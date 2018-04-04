from lib.system.fun_test import fun_test
from fun_settings import FUN_TEST_DIR, INTEGRATION_DIR
from asset.asset_manager import AssetManager
from lib.host.linux import Linux
import os
import re


class SbpZynqSetupTemplate:
    ZYNQ_SETUP_DIR = "/zynq_setup"
    REPOSITORY_DIR = "/repository"
    RELATIVE_BOARD_TESTS_DIR = "software/board_tests"
    RELATIVE_BOARD_TESTS_LOG_DIR = "log"
    LOCAL_REPOSITORY_DIR = "/SBPFirmware"
    BOARD_TYPE = "zynq7_zc706"
    CPU = "m5150"
    TEST_LOG_FILE = "/tmp/test.log"
    ENROLLMENT_MAGIC_NUMBER = "1E5C00B1"
    DEVTOOLS_FIRMWARE_DIR = LOCAL_REPOSITORY_DIR + "/software/devtools/firmware"
    ENROLLMENT_CERT_BIN = "enroll_cert.bin"
    ENROLLMENT_TBS_BIN = "enroll_tbs.bin"
    SBP_FIRMWARE_REPO_DIR = INTEGRATION_DIR + "/../SBPFirmware"

    def __init__(self, host, zynq_board_ip, bit_stream=None):
        self.host = host
        self.local_repository = self.LOCAL_REPOSITORY_DIR
        self.zynq_board_ip = zynq_board_ip
        if host:
            self.host.command("echo $MIPS_ELF_ROOT")
            self.host.command("ls -l {}".format(self.ZYNQ_SETUP_DIR))
        self.bit_stream = bit_stream

    def setup_container(self):
        self.docker_host = AssetManager().get_any_docker_host()
        workspace = os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(FUN_TEST_DIR))))
        self.container_name = "this_container"
        image_name = "sbp_basic:latest"
        self.target_workspace = "/workspace"
        environment_variables = {"DOCKER": True,
                                 "WORKSPACE": workspace}
        repository_mount = "{}:/repository".format(self.SBP_FIRMWARE_REPO_DIR)

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

        fun_test.test_assert(self.docker_host.wait_for_handoff(container_name=self.container_name,
                                                               handoff_string="Idling"), message="Container handoff")

        localhost = Linux(host_ip="127.0.0.1", localhost=True)
        localhost.command("cd {}; git pull".format(self.SBP_FIRMWARE_REPO_DIR))
        fun_test.test_assert_expected(expected=0, actual=localhost.exit_status(), message="Git pull")
        return self.container_asset

    def setup(self):
        fun_test.test_assert(self.setup_local_repository(),
                             message="Setup local repository")
        fun_test.test_assert(self.setup_hsm(), "HSM install")
        fun_test.test_assert(self.setup_build(), "Cmake Build")
        fun_test.test_assert(self.clear_board_tests_logs(), "Clear board-tests logs")
        self.clear_enrollment_bin()

        return True

    def setup_local_repository(self):
        self.host.command("ls -l {}".format(self.REPOSITORY_DIR))
        self.host.command("cp -r {} {}".format(self.REPOSITORY_DIR, self.local_repository))
        self.host.command("ls -l {}".format(self.local_repository))
        return True

    def setup_hsm(self):
        self.host.command("cd {}/tools".format(self.local_repository))
        output = self.host.command("./hsm_install.sh")
        fun_test.test_assert("The token has been initialized" in output, "Initialize token")
        return True

    def setup_build(self):
        self.host.command("cd {}".format(self.local_repository))
        self.host.command("mkdir ../build-sbp")
        self.host.command("cd ../build-sbp")
        self.host.command('cmake {} -DBUILD_ESECURE_UNITTESTS=0 -DBOARD_ADDRESS={}'.format(self.local_repository,
                                                                                           self.zynq_board_ip))
        output = self.host.command("make")
        fun_test.test_assert("[100%] Built target eSecure_platform_tests" in output,
                             "[100%] Built target eSecure_platform_tests")
        return True

    def get_board_tests_dir(self):
        return "{}/{}".format(self.local_repository, self.RELATIVE_BOARD_TESTS_DIR)

    def get_board_tests_log_dir(self):
        return "{}/{}".format(self.get_board_tests_dir(), self.RELATIVE_BOARD_TESTS_LOG_DIR)

    def clear_board_tests_logs(self):
        self.host.command("rm -rf {}/*".format(self.get_board_tests_log_dir()))
        return True

    def clear_enrollment_bin(self):
        self.host.command("rm {}/{}".format(self.get_board_tests_dir(), self.ENROLLMENT_TBS_BIN))

    def run_test_py(self,
                    secure_boot,
                    stimuli_file,
                    cpu=CPU,
                    board_type=BOARD_TYPE,
                    test_log_file=TEST_LOG_FILE,
                    no_host_boot=False,
                    clear_all_logs=True,
                    timeout=900):
        result = False
        try:
            self.host.command('cd {}'.format(self.get_board_tests_dir()))
            if clear_all_logs:
                self.clear_board_tests_logs()
            self.host.command("ls -l")
            secure_boot_str = ""
            if secure_boot:
                secure_boot_str = "on"
            else:
                secure_boot_str = "off"
            no_host_boot_str = ""
            if no_host_boot:
                no_host_boot_str = "--nohostboot"

            command = 'python ./run_test.py --cpu={} --board_type={} --bitstream={} --board={} -vv {} --secureboot={} {} &> {}'.format(
                cpu,
                board_type,
                self.bit_stream,
                self.zynq_board_ip,
                no_host_boot_str,
                secure_boot_str,
                stimuli_file,
                test_log_file)
            fun_test.debug("run_test_py command: {}".format(command))
            output = self.host.command(command, timeout=timeout)
            stimuli_files = self.host.list_files(stimuli_file)
            fun_test.simple_assert(stimuli_files, "Atleast one stimuli file")

            error_found = False

            for stimuli_file in stimuli_files:
                log_file_name = self.get_stimuli_log_filename(stimuli_file=stimuli_file["filename"],
                                                              secure_boot=secure_boot)
                last_line = self.host.command("tail {}".format(log_file_name))
                try:
                    fun_test.test_assert("[EXIT] SUCCESS" in last_line,
                                         message="{}: [EXIT] SUCCESS message found".format(log_file_name))
                except Exception as ex:
                    error_found = True
                    fun_test.critical(str(ex))

            # Check test log too

            output = self.host.command("grep -c {} {}".format("'ERROR:run_test.py:Tests completed with .* errors'", self.TEST_LOG_FILE))
            fun_test.test_assert(not int(output.strip()), message="Completed with errors found in log")
            result = True and not error_found

        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def get_stimuli_log_filename(self, stimuli_file, secure_boot=False):
        self.host.command('cd {}'.format(self.get_board_tests_dir()))
        just_file_name = os.path.basename(stimuli_file)

        replacement = ".log"
        if secure_boot:
            replacement = "_secboot" + replacement
        local_log_file = "log/{}".format(just_file_name.replace(".py", replacement))
        return local_log_file

    def enroll(self):
        stimuli_dir = "{}/validation/stimuli/enroll".format(self.local_repository)
        stimuli_file = "{}/cmd_enroll_puf_chal.py".format(stimuli_dir)

        fun_test.test_assert(self.run_test_py(secure_boot=True, stimuli_file=stimuli_file, no_host_boot=True),
                             message="Run test py enrollment challenge")

        output = self.host.command("cat {}".format(self.get_stimuli_log_filename(stimuli_file=stimuli_file,
                                                                                 secure_boot=True)))
        certificate_contents = ""
        m = re.search(
            r'TBS Certificate log start.*memory\s+read.*bytes:(.*)\[INFO\].*Step 1-4: TBS Certificate log end', output,
            re.MULTILINE | re.DOTALL)
        fun_test.test_assert(m, message="Find TBS certificate section in log")
        if m:
            certificate_contents = m.group(1).strip()
        fun_test.test_assert(certificate_contents.startswith(self.ENROLLMENT_MAGIC_NUMBER),
                             message="Find magic in enrollment cert")
        fun_test.log("TBS cert: {}".format(certificate_contents))

        tbs_hex_file = "/tmp/tbs.hex"
        tbs_bin_file = "/tmp/enroll_tbs.bin"
        self.host.create_file(tbs_hex_file, contents=certificate_contents)

        self.host.command("xxd -r -p {} {}".format(tbs_hex_file, tbs_bin_file))

        self.host.command("cd {}".format(self.DEVTOOLS_FIRMWARE_DIR))
        enrollment_bin_file = "/tmp/enroll_cert.bin"
        # self.host.command("python3 ./generate_firmware_image.py sign -k fpk4 -f {} -o {}".format(tbs_bin_file,
        #                                                                                         enrollment_bin_file))
        # fun_test.test_assert(self.host.list_files(enrollment_bin_file),
        #                     message="Signed enrollment bin file")
        self.host.command('cd {}'.format(self.get_board_tests_dir()))
        self.host.command("mv {} .".format(tbs_bin_file))
        return True