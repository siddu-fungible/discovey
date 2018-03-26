from lib.system.fun_test import *
from asset.asset_manager import AssetManager
from lib.host.linux import Linux
from fun_settings import FUN_TEST_DIR
import re
from lib.templates.system.sbp_template import SbpZynqSetupTemplate


LOCAL_REPOSITORY_DIR = "/SBPFirmware"
SBP_FIRMWARE_REPO_DIR = INTEGRATION_DIR + "/../SBPFirmware"
BIT_STREAM = "SilexBitfiles/esecure_top_fpga_sbppuf_20180307.bit"
ZYNC_BOARD_IP = "10.1.23.106"
TEST_LOG_FILE = "/tmp/test.log"
BOARD_TYPE = "zynq7_zc706"
CPU = "m5150"

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

    def cleanup(self):
        self.docker_host.destroy_container(
            container_name=self.container_name,
            ignore_error=True)


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

        sbp_setup = SbpZynqSetupTemplate(host=linux_obj,
                                         local_repository=LOCAL_REPOSITORY_DIR,
                                         zynq_board_ip=ZYNC_BOARD_IP)

        localhost = Linux(host_ip="127.0.0.1", localhost=True)
        localhost.command("cd {}; git pull".format(SBP_FIRMWARE_REPO_DIR))
        fun_test.test_assert_expected(expected=0, actual=localhost.exit_status(), message="Git pull")
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
        pass


class TestCase2(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="secureboot=on ",
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

        sbp_setup = SbpZynqSetupTemplate(host=linux_obj,
                                         local_repository=LOCAL_REPOSITORY_DIR,
                                         zynq_board_ip=ZYNC_BOARD_IP)

        localhost = Linux(host_ip="127.0.0.1", localhost=True)
        localhost.command("cd {}; git pull".format(SBP_FIRMWARE_REPO_DIR))
        fun_test.test_assert_expected(expected=0, actual=localhost.exit_status(), message="Git pull")
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

        command = 'python ./run_test.py --cpu={} --board_type={} --bitstream={} --board={} -vv --secureboot=on {} &> {}'.format(CPU, BOARD_TYPE, BIT_STREAM, ZYNC_BOARD_IP, stimuli_file, TEST_LOG_FILE)
        output = linux_obj.command(command, timeout=900)

        linux_obj.command('cd {}/software/board_tests'.format(LOCAL_REPOSITORY_DIR))
        for stimuli_file in stimuli_files:
            just_file_name = os.path.basename(stimuli_file["filename"])
            local_log_file = "log/{}".format(just_file_name.replace(".py", ".log"))
            last_line = linux_obj.command("tail {}".format(local_log_file))
            fun_test.test_assert("[EXIT] SUCCESS" in last_line, message="{}: [EXIT] SUCCESS message found".format(just_file_name))

    def cleanup(self):
        pass


if __name__ == "__main__":
    ts = ContainerSetup()
    ts.add_test_case(TestCase1())
    ts.run()
