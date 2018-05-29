from lib.system.fun_test import fun_test
from fun_settings import FUN_TEST_DIR, INTEGRATION_DIR
from asset.asset_manager import AssetManager
from lib.host.linux import Linux
import os
import re





class OtpTemplateGenerator():
    OTP_TEMPLATE_STRING = """HW_LOCK_BIT {hw_lock_bit}
ESEC_SECUREBOOT {esec_secureboot}
WATCHDOG {watchdog}
CUSTOMER_KEY_BIT {customer_key_bit}
I2C_CHAL_BIT {i2c_chal_bit}
TAMPERFILTERPERIOD {tamper_filter_period}
TAMPERFILTERTHRESHOLD {tamper_filter_threshold}
DEBUGPROTEN {debug_protection}
SERIAL_INFO {serial_info}
SERIALNO {serial_no}
TAMP00_CM {tamp00_cm}
TAMP01_CM {tamp01_cm}
TAMP02_CM {tamp02_cm}
TAMP03_CM {tamp03_cm}
TAMP04_CM {tamp04_cm}
TAMP05_CM {tamp05_cm}
TAMP06_CM {tamp06_cm}
TAMP07_CM {tamp07_cm}
TAMP08_CM {tamp08_cm}
TAMP09_CM {tamp09_cm}
TAMP10_CM {tamp10_cm}
TAMP11_CM {tamp11_cm}
TAMP12_CM {tamp12_cm}
TAMP13_CM {tamp13_cm}
TAMP14_CM {tamp14_cm}
TAMP15_CM {tamp15_cm}
TAMP16_CM {tamp16_cm}
TAMP17_CM {tamp17_cm}
TAMP18_CM {tamp18_cm}
TAMP19_CM {tamp19_cm}
TAMP20_CM {tamp20_cm}
TAMP21_CM {tamp21_cm}
TAMP22_CM {tamp22_cm}
TAMP23_CM {tamp23_cm}
TAMP24_CM {tamp24_cm}
TAMP25_CM {tamp25_cm}
TAMP26_CM {tamp26_cm}
TAMP27_CM {tamp27_cm}
TAMP28_CM {tamp28_cm}
TAMP29_CM {tamp29_cm}
TAMP30_CM {tamp30_cm}
TAMP31_CM {tamp31_cm}"""
    def __init__(self):
        self.hw_lock_bit = 1
        self.esec_secureboot = 0
        self.watchdog = 1
        self.customer_key_bit = 0
        self.i2c_chal_bit = 0
        self.tamper_filter_period = "0x1f"
        self.tamper_filter_threshold = "0x05"
        self.debug_protection = "0xFC00FF"
        self.serial_info = 0
        self.serial_no = "0x78502fa8f092ca5008b8d8992f64208d"
        self.tamp00_cm = 1
        self.tamp01_cm = 1
        self.tamp02_cm = 4
        self.tamp03_cm = 4
        self.tamp04_cm = 4
        self.tamp05_cm = 4
        self.tamp06_cm = 1
        self.tamp07_cm = 4
        self.tamp08_cm = 4
        self.tamp09_cm = 4
        self.tamp10_cm = 1
        self.tamp11_cm = 1
        self.tamp12_cm = 4
        self.tamp13_cm = 4
        self.tamp14_cm = 4
        self.tamp15_cm = 1
        self.tamp16_cm = 0
        self.tamp17_cm = 0
        self.tamp18_cm = 0
        self.tamp19_cm = 0
        self.tamp20_cm = 0
        self.tamp21_cm = 0
        self.tamp22_cm = 0
        self.tamp23_cm = 0
        self.tamp24_cm = 1
        self.tamp25_cm = 0
        self.tamp26_cm = 0
        self.tamp27_cm = 0
        self.tamp28_cm = 0
        self.tamp29_cm = 0
        self.tamp30_cm = 0
        self.tamp31_cm = 4

    def set(self, **kwargs):
        for key, value in kwargs.iteritems():
            if hasattr(self, key):
                setattr(self, key, value)

    def generate(self):
        template = self.OTP_TEMPLATE_STRING.format(hw_lock_bit=self.hw_lock_bit,
                                          esec_secureboot=self.esec_secureboot,
                                          watchdog=self.watchdog,
                                          customer_key_bit=self.customer_key_bit,
                                          i2c_chal_bit=self.i2c_chal_bit,
                                          tamper_filter_period=self.tamper_filter_period,
                                          tamper_filter_threshold=self.tamper_filter_threshold,
                                          debug_protection=self.debug_protection,
                                          serial_info=self.serial_info,
                                          serial_no=self.serial_no,
                                          tamp00_cm=self.tamp00_cm,
                                          tamp01_cm=self.tamp01_cm,
                                          tamp02_cm=self.tamp02_cm,
                                          tamp03_cm=self.tamp03_cm,
                                          tamp04_cm=self.tamp04_cm,
                                          tamp05_cm=self.tamp05_cm,
                                          tamp06_cm=self.tamp06_cm,
                                          tamp07_cm=self.tamp07_cm,
                                          tamp08_cm=self.tamp08_cm,
                                          tamp09_cm=self.tamp09_cm,
                                          tamp10_cm=self.tamp10_cm,
                                          tamp11_cm=self.tamp11_cm,
                                          tamp12_cm=self.tamp12_cm,
                                          tamp13_cm=self.tamp13_cm,
                                          tamp14_cm=self.tamp14_cm,
                                          tamp15_cm=self.tamp15_cm,
                                          tamp16_cm=self.tamp16_cm,
                                          tamp17_cm=self.tamp17_cm,
                                          tamp18_cm=self.tamp18_cm,
                                          tamp19_cm=self.tamp19_cm,
                                          tamp20_cm=self.tamp20_cm,
                                          tamp21_cm=self.tamp21_cm,
                                          tamp22_cm=self.tamp22_cm,
                                          tamp23_cm=self.tamp23_cm,
                                          tamp24_cm=self.tamp24_cm,
                                          tamp25_cm=self.tamp25_cm,
                                          tamp26_cm=self.tamp26_cm,
                                          tamp27_cm=self.tamp27_cm,
                                          tamp28_cm=self.tamp28_cm,
                                          tamp29_cm=self.tamp29_cm,
                                          tamp30_cm=self.tamp30_cm,
                                          tamp31_cm=self.tamp31_cm)
        return template


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
    DEFAULT_SBP_PUF_BIT_STREAM = "SilexBitfiles/esecure_top_fpga_sbppuf_20180523.bit"

    def __init__(self, host, zynq_board_ip, bit_stream=None):
        self.host = host
        self.local_repository = self.LOCAL_REPOSITORY_DIR
        self.zynq_board_ip = zynq_board_ip
        if host:
            self.host.command("echo $MIPS_ELF_ROOT")
            self.host.command("ls -l {}".format(self.ZYNQ_SETUP_DIR))
        if not bit_stream:
            bit_stream = self.DEFAULT_SBP_PUF_BIT_STREAM
        self.bit_stream = bit_stream

    def set_otp_template(self, **kwargs):
        otp_template = OtpTemplateGenerator()
        otp_template.set(**kwargs)
        template = otp_template.generate()
        fun_test.log("OTP Template:\n{}".format(template))
        target_file_name = self.get_otp_templates_dir() + "/OTP_content_CM.txt.in"
        self.host.create_file(contents=template, file_name=target_file_name)

    def setup_container(self, git_pull=True):
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
        if git_pull:
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

    def _get_artifacts_dir(self, party="fungible", platform="zync6"):
        s = "artifacts_{}_eeprom_{}".format(party, platform)
        return os.path.join(self.LOCAL_REPOSITORY_DIR, s)

    def artifacts_setup(self, enroll=True, otp_settings=None, secure_boot=True):
        fun_test.test_assert(self.setup_local_repository(), message="Setup local repository")
        if otp_settings:
            self.set_otp_template(**otp_settings)
        fun_test.test_assert(self.setup_hsm(), "HSM install")
        fun_test.test_assert(self.run_test_software(), "Run test_software")
        fun_test.test_assert(self.setup_build(make=False), "Cmake")
        fun_test.test_assert(self.host.list_files(self._get_artifacts_dir()), "List artifacts")
        if enroll:
            fun_test.test_assert(self.enroll(artifacts_dir=self._get_artifacts_dir()), "Enroll")
            fun_test.test_assert(self.run_test_software(enroll_tbs=os.path.join(self.LOCAL_REPOSITORY_DIR,
                                                                                self.ENROLLMENT_TBS_BIN)),
                                 "Run test_software with enrollment TBS")

    def run_test_software(self, enroll_tbs=None, ram="128K", num_pkes=1):
        self.host.command("cd {}".format(self.LOCAL_REPOSITORY_DIR))
        command = "./test_software.sh -r {} -b {}".format(ram, num_pkes)
        if enroll_tbs:
            command += " -e {}".format(enroll_tbs)
        return self.host.command(command, timeout=120)

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

    def setup_build(self, make=True):
        self.host.command("cd {}".format(self.local_repository))
        self.host.command("mkdir ../build-sbp")
        self.host.command("cd ../build-sbp")
        self.host.command('cmake {} -DBUILD_ESECURE_UNITTESTS=0 -DBOARD_ADDRESS={}'.format(self.local_repository,
                                                                                           self.zynq_board_ip))
        if make:
            output = self.host.command("make")
            fun_test.test_assert("[100%] Built target eSecure_platform_tests" in output,
                                 "[100%] Built target eSecure_platform_tests")
        return True

    def custom_flash_generator(self, artifacts_dir, spec="/tmp/flash_config.json", output_dir=None):
        fun_test.add_checkpoint("Custom Flash generator")
        self.host.command("cd {}".format(self.get_board_tests_dir()))
        if not artifacts_dir:
            artifacts_dir = self._get_artifacts_dir()
        if not output_dir:
            output_dir = artifacts_dir
        command = "python custom_flash_generator.py --spec {} --artifacts_dir {} --output_dir {}".format(spec,
                                                                                                         artifacts_dir,
                                                                                                         output_dir)
        return self.host.command(command)

    def get_board_tests_dir(self):
        return "{}/{}".format(self.local_repository, self.RELATIVE_BOARD_TESTS_DIR)

    def get_otp_templates_dir(self):
        s = self.DEVTOOLS_FIRMWARE_DIR + "/otp_templates"
        return s

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
                    timeout=900,
                    artifacts_dir=None,
                    get_log=None):
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
            # if no_host_boot:
            #    no_host_boot_str = "--nohostboot"

            artifacts_dir_str = ""
            if artifacts_dir:
                artifacts_dir_str = " --artifacts_dir={}".format(artifacts_dir)
            test_log_file_str = ""
            if test_log_file:
                test_log_file_str = " &> {}".format(test_log_file)

            command = 'python ./run_test.py --cpu={} {} --board_type={} --bitstream={} --board={} -vv {} --secureboot={} {} {}'.format(
                cpu,
                artifacts_dir_str,
                board_type,
                self.bit_stream,
                self.zynq_board_ip,
                no_host_boot_str,
                secure_boot_str,
                stimuli_file,
                test_log_file_str)
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
        if get_log:
            result = self.host.read_file(file_name=test_log_file)
        return result

    def get_stimuli_log_filename(self, stimuli_file, secure_boot=False):
        self.host.command('cd {}'.format(self.get_board_tests_dir()))
        just_file_name = os.path.basename(stimuli_file)

        replacement = ".log"
        if secure_boot:
            replacement = "_secboot" + replacement
        local_log_file = "log/{}".format(just_file_name.replace(".py", replacement))
        return local_log_file

    def enroll(self, artifacts_dir=None):
        fun_test.add_checkpoint("Enrolling")
        stimuli_dir = "{}/validation/stimuli/enroll".format(self.local_repository)
        stimuli_file = "{}/cmd_enroll_puf_chal.py".format(stimuli_dir)

        fun_test.test_assert(self.run_test_py(secure_boot=True,
                                              stimuli_file=stimuli_file,
                                              no_host_boot=True,
                                              artifacts_dir=artifacts_dir),
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

        tbs_bin_base_file = "enroll_tbs.bin"
        tbs_hex_file = "/tmp/tbs.hex"
        tbs_bin_file = "/tmp/{}".format(tbs_bin_base_file)
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
        self.host.command("cp ./{} {}/".format(tbs_bin_base_file, self.LOCAL_REPOSITORY_DIR))
        fun_test.test_assert(self.host.list_files(self.LOCAL_REPOSITORY_DIR + "/" + tbs_bin_base_file),
                             "Ensure TBS bin is copied")
        return True

    def get_status(self, secure_boot=True):
        stimuli_dir = "{}/validation/stimuli/short".format(SbpZynqSetupTemplate.LOCAL_REPOSITORY_DIR)
        stimuli_file = "{}/cmd_get_status.py".format(stimuli_dir)
        logs = self.run_test_py(secure_boot=False, stimuli_file=stimuli_file,
                         artifacts_dir=self._get_artifacts_dir(), get_log=True)
