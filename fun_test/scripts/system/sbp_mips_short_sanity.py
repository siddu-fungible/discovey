from lib.system.fun_test import *
from asset.asset_manager import AssetManager
from lib.host.linux import Linux
from fun_settings import FUN_TEST_DIR
import re
from lib.templates.system.sbp_template import SbpZynqSetupTemplate


LOCAL_REPOSITORY_DIR = "/SBPFirmware"
DEVTOOLS_FIRMWARE_DIR = LOCAL_REPOSITORY_DIR + "/software/devtools/firmware"
SBP_FIRMWARE_REPO_DIR = INTEGRATION_DIR + "/../SBPFirmware"
BIT_STREAM = "SilexBitfiles/esecure_top_fpga_sbppuf_20180307.bit"
ZYNC_BOARD_IP = "10.1.23.106"
TEST_LOG_FILE = "/tmp/test.log"
BOARD_TYPE = "zynq7_zc706"
CPU = "m5150"

ENROLLMENT_MAGIC_NUMBER = "1E5C00B1"

class ContainerSetup(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Bring up the container
        """)

    def setup(self):
        self.docker_host = AssetManager().get_any_docker_host()
        workspace = dirname(abspath(dirname(abspath(FUN_TEST_DIR))))
        self.container_name = "this_container"
        image_name = "sbp_basic:latest"
        self.target_workspace = "/workspace"
        environment_variables = {"DOCKER": True,
                                 "WORKSPACE": workspace}
        repository_mount = "{}:/repository".format(SBP_FIRMWARE_REPO_DIR)

        self.container_asset = self.docker_host.setup_container(image_name=image_name,
                                                                container_name=self.container_name,
                                                                command="-b 123",
                                                                pool0_internal_ports=[22],
                                                                mounts=[repository_mount],
                                                                working_dir="/",
                                                                auto_remove=True,
                                                                environment_variables=environment_variables)

        fun_test.test_assert(self.container_asset, "Container launched")
        fun_test.shared_variables["container_asset"] = self.container_asset
        fun_test.shared_variables["target_workspace"] = self.target_workspace

        linux_obj = self.docker_host

        timer = FunTimer(max_time=180)
        container_up = False
        while not timer.is_expired():
            output = linux_obj.command(command="docker logs {}".format(self.container_name), include_last_line=True)
            if re.search('Idling', output):
                container_up = True
                break
            fun_test.sleep("Waiting for container to come up", seconds=10)
        fun_test.test_assert(container_up, "Container UP")

        localhost = Linux(host_ip="127.0.0.1", localhost=True)
        localhost.command("cd {}; git pull".format(SBP_FIRMWARE_REPO_DIR))
        fun_test.test_assert_expected(expected=0, actual=localhost.exit_status(), message="Git pull")

    def cleanup(self):

        self.docker_host.destroy_container(container_name=self.container_name, ignore_error=True)


class TestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="secureboot=off ",
                              steps="""
        1. Do something on the container.
                              """)

    def setup(self):
        pass

    def run(self):

        container_asset = fun_test.shared_variables["container_asset"]

        linux_obj = Linux(host_ip=container_asset["host_ip"],
                          ssh_username=container_asset["mgmt_ssh_username"],
                          ssh_password=container_asset["mgmt_ssh_password"],
                          ssh_port=container_asset["mgmt_ssh_port"])

        linux_obj.command('cd {}/software/board_tests'.format(LOCAL_REPOSITORY_DIR))
        linux_obj.command("rm -rf log/*.log".format(SBP_FIRMWARE_REPO_DIR))
        sbp_setup = SbpZynqSetupTemplate(host=linux_obj,
                                         local_repository=LOCAL_REPOSITORY_DIR,
                                         zynq_board_ip=ZYNC_BOARD_IP)


        fun_test.test_assert(sbp_setup.setup(), "Setup")
        linux_obj.command('cd {}/software/board_tests'.format(LOCAL_REPOSITORY_DIR))
        linux_obj.command("ls -l")
        stimuli_dir = "{}/validation/stimuli/short".format(LOCAL_REPOSITORY_DIR)
        files = linux_obj.list_files(stimuli_dir)


        '''
        for file in files:
            filename = file["filename"]
            if not filename.endswith(".py"):
                continue
            stimuli_file = stimuli_dir + "/" + filename
            fun_test.add_checkpoint(checkpoint="Stimuli file: {}".format(filename))
            command = 'python ./run_test.py --cpu={} --board_type={} --bitstream={} --board={} -vv --secureboot=off {}'.format(
                CPU, BOARD_TYPE, BIT_STREAM, ZYNC_BOARD_IP, stimuli_file)
            output = linux_obj.command(command, timeout=260)
            fun_test.test_assert(not re.search("ERROR:run_test.py:*errors", output),
                                 "Error not found: {}".format(filename))

            # stimuli_file = "{}/cmd_debug_access_chlg.py".format(stimuli_dir)

        '''

        stimuli_file = "{}/cmd_AES*.py".format(stimuli_dir)
        stimuli_files = linux_obj.list_files(stimuli_file)
        fun_test.simple_assert(stimuli_files, "Atleast one stimuli file")

        command = 'python ./run_test.py --cpu={} --board_type={} --bitstream={} --board={} -vv --secureboot=off {} &> {}'.format(CPU, BOARD_TYPE, BIT_STREAM, ZYNC_BOARD_IP, stimuli_file, TEST_LOG_FILE)
        output = linux_obj.command(command, timeout=900)

        linux_obj.command('cd {}/software/board_tests'.format(LOCAL_REPOSITORY_DIR))
        for stimuli_file in stimuli_files:
            just_file_name = os.path.basename(stimuli_file["filename"])
            local_log_file = "log/{}".format(just_file_name.replace(".py", ".log"))
            last_line = linux_obj.command("tail {}".format(local_log_file))
            fun_test.test_assert("[EXIT] SUCCESS" in last_line, message="{}: [EXIT] SUCCESS message found".format(just_file_name))


    def cleanup(self):
        self.container_asset = fun_test.shared_variables["container_asset"]
        post_fix_name = "Test-case1-test-log.txt"
        artifact_file_name = fun_test.get_test_case_artifact_file_name(post_fix_name=post_fix_name)
        fun_test.scp(source_ip=self.container_asset["host_ip"],
                     source_file_path="{}".format(TEST_LOG_FILE),
                     source_username=self.container_asset["mgmt_ssh_username"],
                     source_password=self.container_asset["mgmt_ssh_password"],
                     source_port=self.container_asset["mgmt_ssh_port"],
                     target_file_path=artifact_file_name)
        fun_test.add_auxillary_file(description="{} Log".format(post_fix_name),
                                    filename=artifact_file_name)




class TestCase2(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="secureboot=on ",
                              steps="""
        1. Do something on the container.
                              """)

    def setup(self):
        pass

    def enroll(self):
        self.linux_obj.command('cd {}/software/board_tests'.format(LOCAL_REPOSITORY_DIR))
        linux_obj = self.linux_obj
        stimuli_dir = "{}/validation/stimuli/short".format(LOCAL_REPOSITORY_DIR)
        self.linux_obj.command('rm log/cmd_enroll_puf_chal.log')
        stimuli_file = "{}/cmd_enroll_puf_chal.py".format(stimuli_dir)
        command = 'python ./run_test.py --cpu={} --board_type={} --bitstream={} --board={} -vv --secureboot=on --nohostboot {} &> {}'.format(CPU, BOARD_TYPE, BIT_STREAM, ZYNC_BOARD_IP, stimuli_file, TEST_LOG_FILE)
        output = linux_obj.command(command, timeout=900)
        self.linux_obj.list_files(path="log/")
        output = self.linux_obj.command("cat log/cmd_enroll_puf_chal_secboot.log")
        certificate_contents = ""
        m = re.search(
            r'TBS Certificate log start.*memory\s+read.*bytes:(.*)\[INFO\].*Step 1-4: TBS Certificate log end', output,
            re.MULTILINE | re.DOTALL)
        fun_test.test_assert(m, message="Find TBS certificate section in log")
        if m:
            certificate_contents = m.group(1).strip()
        fun_test.test_assert(certificate_contents.startswith(ENROLLMENT_MAGIC_NUMBER), message="Find magic in enrollment cert")
        fun_test.log("TBS cert: {}".format(certificate_contents))

        tbs_hex_file = "/tmp/tbs.hex"
        tbs_bin_file = "/tmp/tbs.bin"
        self.linux_obj.create_file(tbs_hex_file, contents=certificate_contents)

        self.linux_obj.command("apt-get -y install xxd; xxd -r -p {} {}".format(tbs_hex_file, tbs_bin_file))

        self.linux_obj.command("cd {}".format(DEVTOOLS_FIRMWARE_DIR))
        enrollment_bin_file = "/tmp/enroll_cert.bin"
        self.linux_obj.command("python3 ./generate_firmware_image.py sign -k fpk4 -f {} -o {}".format(tbs_bin_file, enrollment_bin_file))
        fun_test.test_assert(self.linux_obj.list_files(enrollment_bin_file), message="Signed enrollment bin file")
        linux_obj.command('cd {}/software/board_tests'.format(LOCAL_REPOSITORY_DIR))
        linux_obj.command("mv {} .".format(enrollment_bin_file))


    def run(self):

        container_asset = fun_test.shared_variables["container_asset"]

        linux_obj = Linux(host_ip=container_asset["host_ip"],
                          ssh_username=container_asset["mgmt_ssh_username"],
                          ssh_password=container_asset["mgmt_ssh_password"],
                          ssh_port=container_asset["mgmt_ssh_port"])
        self.linux_obj = linux_obj


        linux_obj.command('cd {}/software/board_tests'.format(LOCAL_REPOSITORY_DIR))
        linux_obj.command("rm -rf log/*.log".format(SBP_FIRMWARE_REPO_DIR))
        sbp_setup = SbpZynqSetupTemplate(host=linux_obj,
                                         local_repository=LOCAL_REPOSITORY_DIR,
                                         zynq_board_ip=ZYNC_BOARD_IP)

        localhost = Linux(host_ip="127.0.0.1", localhost=True)
        localhost.command("cd {}; git pull".format(SBP_FIRMWARE_REPO_DIR))
        fun_test.test_assert_expected(expected=0, actual=localhost.exit_status(), message="Git pull")
        fun_test.test_assert(sbp_setup.setup(), "Setup")
        self.enroll()


        linux_obj.command('cd {}/software/board_tests'.format(LOCAL_REPOSITORY_DIR))
        linux_obj.command("ls -l")
        stimuli_dir = "{}/validation/stimuli/short".format(LOCAL_REPOSITORY_DIR)
        files = linux_obj.list_files(stimuli_dir)




        stimuli_file = "{}/cmd_AES*.py".format(stimuli_dir)
        stimuli_files = linux_obj.list_files(stimuli_file)
        fun_test.simple_assert(stimuli_files, "Atleast one stimuli file")

        command = 'python ./run_test.py --cpu={} --board_type={} --bitstream={} --board={} -vv --secureboot=on {} &> {}'.format(CPU, BOARD_TYPE, BIT_STREAM, ZYNC_BOARD_IP, stimuli_file, TEST_LOG_FILE)
        output = linux_obj.command(command, timeout=900)

        linux_obj.command('cd {}/software/board_tests'.format(LOCAL_REPOSITORY_DIR))
        for stimuli_file in stimuli_files:
            just_file_name = os.path.basename(stimuli_file["filename"])
            local_log_file = "log/{}".format(just_file_name.replace(".py", "_secboot.log"))
            linux_obj.command("ls -ltr {}".format("log/*"))
            last_line = linux_obj.command("tail {}".format(local_log_file))
            fun_test.test_assert("[EXIT] SUCCESS" in last_line, message="{}: [EXIT] SUCCESS message found".format(just_file_name))


    def cleanup(self):
        self.container_asset = fun_test.shared_variables["container_asset"]
        post_fix_name = "Test-case2-test-log.txt"
        artifact_file_name = fun_test.get_test_case_artifact_file_name(post_fix_name=post_fix_name)
        fun_test.scp(source_ip=self.container_asset["host_ip"],
                     source_file_path="{}".format(TEST_LOG_FILE),
                     source_username=self.container_asset["mgmt_ssh_username"],
                     source_password=self.container_asset["mgmt_ssh_password"],
                     source_port=self.container_asset["mgmt_ssh_port"],
                     target_file_path=artifact_file_name)
        fun_test.add_auxillary_file(description="{} Log".format(post_fix_name),
                                    filename=artifact_file_name)



if __name__ == "__main__":
    ts = ContainerSetup()
    ts.add_test_case(TestCase1())
    ts.add_test_case(TestCase2())
    ts.run()
