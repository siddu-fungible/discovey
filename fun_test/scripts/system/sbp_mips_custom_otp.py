from lib.system.fun_test import *
import re
from asset.asset_manager import AssetManager
from lib.host.linux import Linux
from lib.templates.system.sbp_template import SbpZynqSetupTemplate

BIT_STREAM = "SilexBitfiles/esecure_top_fpga_sbppuf_20180322.bit"
ZYNC_BOARD_IP = "10.1.23.106"


class ContainerSetup(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Bring up the container
        """)

    def setup(self):
        self.docker_host = AssetManager().get_any_docker_host()
        self.container_asset = SbpZynqSetupTemplate(host=None, zynq_board_ip=None).setup_container(git_pull=False)
        """
        container_asset = {}
        container_asset["host_ip"] = "127.0.0.1"
        container_asset["mgmt_ssh_username"] = "root"
        container_asset["mgmt_ssh_password"] = "fun123"
        container_asset["mgmt_ssh_port"] = 3220
        fun_test.shared_variables["container_asset"] = container_asset
        """

    def cleanup(self):
        container_asset = fun_test.shared_variables["container_asset"]
#         self.docker_host.destroy_container(container_name=container_asset["name"], ignore_error=True)



class TestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Secureboot=on, PUF-ROM A signed by FPK4",
                              steps="""
                              """)

    def setup(self):
        pass

    def run(self):

        container_asset = fun_test.shared_variables["container_asset"]

        linux_obj = Linux(host_ip=container_asset["host_ip"],
                          ssh_username=container_asset["mgmt_ssh_username"],
                          ssh_password=container_asset["mgmt_ssh_password"],
                          ssh_port=container_asset["mgmt_ssh_port"])
        sbp_setup = SbpZynqSetupTemplate(host=linux_obj, zynq_board_ip=ZYNC_BOARD_IP)

        sbp_setup.artifacts_setup(enroll=True, secure_boot=True, otp_settings={"hw_lock_bit": 0, "esec_secureboot": 0})

        config_template_path = fun_test.get_script_parent_directory() + "/flash_config.json"
        with open(config_template_path, "r") as f:
            contents = f.read()
            config = json.loads(contents)
            config["start_certificate"]["key"] = "fpk4"

            sbp_setup.host.create_file(contents=json.dumps(config), file_name="/tmp/flash_config.json")
            sbp_setup.host.read_file(file_name="/tmp/flash_config.json")
            sbp_setup.custom_flash_generator(artifacts_dir=sbp_setup._get_artifacts_dir(secure_boot=True))

            stimuli_dir = "{}/validation/stimuli/short".format(SbpZynqSetupTemplate.LOCAL_REPOSITORY_DIR)
            stimuli_file = "{}/cmd_AES_CTR.py".format(stimuli_dir)

            fun_test.test_assert(not sbp_setup.run_test_py(secure_boot=True,
                                                       stimuli_file=stimuli_file,
                                                       artifacts_dir=sbp_setup._get_artifacts_dir(secure_boot=True)),
                                 "run_test should fail")

            # stimuli_file = "{}/cmd_get_status.py".format(stimuli_dir)
            # fun_test.test_assert(sbp_setup.run_test_py(secure_boot=True,
            #                                               stimuli_file=stimuli_file,
            #                                               artifacts_dir=sbp_setup._get_artifacts_dir()), "cmd_get_status")



    def cleanup(self):
        self.container_asset = fun_test.shared_variables["container_asset"]
        post_fix_name = self.__class__.__name__ + "_test_log.txt"
        artifact_file_name = fun_test.get_test_case_artifact_file_name(post_fix_name=post_fix_name)
        fun_test.scp(source_ip=self.container_asset["host_ip"],
                     source_file_path="{}".format(SbpZynqSetupTemplate.TEST_LOG_FILE),
                     source_username=self.container_asset["mgmt_ssh_username"],
                     source_password=self.container_asset["mgmt_ssh_password"],
                     source_port=self.container_asset["mgmt_ssh_port"],
                     target_file_path=artifact_file_name)
        fun_test.add_auxillary_file(description="{} Log".format(post_fix_name),
                                    filename=artifact_file_name)


class TestCase2(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Secureboot=off, PUF-ROM A signed by FPK4",
                              steps="""
                              """)

    def setup(self):
        pass

    def run(self):

        container_asset = fun_test.shared_variables["container_asset"]

        linux_obj = Linux(host_ip=container_asset["host_ip"],
                          ssh_username=container_asset["mgmt_ssh_username"],
                          ssh_password=container_asset["mgmt_ssh_password"],
                          ssh_port=container_asset["mgmt_ssh_port"])
        sbp_setup = SbpZynqSetupTemplate(host=linux_obj, zynq_board_ip=ZYNC_BOARD_IP)

        sbp_setup.artifacts_setup(enroll=True, secure_boot=True, otp_settings={"hw_lock_bit": 0, "esec_secureboot": 0})


        config_template_path = fun_test.get_script_parent_directory() + "/flash_config.json"
        with open(config_template_path, "r") as f:
            contents = f.read()
            config = json.loads(contents)
            config["start_certificate"]["key"] = "fpk4"

            sbp_setup.host.create_file(contents=json.dumps(config), file_name="/tmp/flash_config.json")
            sbp_setup.host.read_file(file_name="/tmp/flash_config.json")
            sbp_setup.custom_flash_generator(artifacts_dir=sbp_setup._get_artifacts_dir(secure_boot=False))

            stimuli_dir = "{}/validation/stimuli/short".format(SbpZynqSetupTemplate.LOCAL_REPOSITORY_DIR)
            stimuli_file = "{}/cmd_AES_CTR.py".format(stimuli_dir)

            fun_test.test_assert(sbp_setup.run_test_py(secure_boot=False,
                                                       stimuli_file=stimuli_file,
                                                       artifacts_dir=sbp_setup._get_artifacts_dir(secure_boot=False)),
                                 "run_test not should fail")

            # stimuli_file = "{}/cmd_get_status.py".format(stimuli_dir)
            # fun_test.test_assert(sbp_setup.run_test_py(secure_boot=True,
            #                                               stimuli_file=stimuli_file,
            #                                               artifacts_dir=sbp_setup._get_artifacts_dir()), "cmd_get_status")



    def cleanup(self):
        self.container_asset = fun_test.shared_variables["container_asset"]
        post_fix_name = self.__class__.__name__ + "_test_log.txt"
        artifact_file_name = fun_test.get_test_case_artifact_file_name(post_fix_name=post_fix_name)
        fun_test.scp(source_ip=self.container_asset["host_ip"],
                     source_file_path="{}".format(SbpZynqSetupTemplate.TEST_LOG_FILE),
                     source_username=self.container_asset["mgmt_ssh_username"],
                     source_password=self.container_asset["mgmt_ssh_password"],
                     source_port=self.container_asset["mgmt_ssh_port"],
                     target_file_path=artifact_file_name)
        fun_test.add_auxillary_file(description="{} Log".format(post_fix_name),
                                    filename=artifact_file_name)


class TestCase3(FunTestCase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Secureboot=on, Illegal serial number",
                              steps="""
                              """)

    def setup(self):
        pass

    def run(self):
        container_asset = fun_test.shared_variables["container_asset"]

        linux_obj = Linux(host_ip=container_asset["host_ip"],
                          ssh_username=container_asset["mgmt_ssh_username"],
                          ssh_password=container_asset["mgmt_ssh_password"],
                          ssh_port=container_asset["mgmt_ssh_port"])
        sbp_setup = SbpZynqSetupTemplate(host=linux_obj, zynq_board_ip=ZYNC_BOARD_IP)

        sbp_setup.artifacts_setup(enroll=True, secure_boot=True, otp_settings={"serial_no": "0x00000000000000000000000000000000"})

        stimuli_dir = "{}/validation/stimuli/short".format(SbpZynqSetupTemplate.LOCAL_REPOSITORY_DIR)
        stimuli_file = "{}/cmd_AES_CTR.py".format(stimuli_dir)

        # sbp_setup.get_status(secure_boot=True)
        test_log = sbp_setup.run_test_py(secure_boot=True,
                                         stimuli_file=stimuli_file,
                                         artifacts_dir=sbp_setup._get_artifacts_dir(secure_boot=True),
                                         get_log=True)

        serial_number_errors = re.findall("Serial number error: is OTP configured", test_log)
        fun_test.test_assert_expected(expected=2, actual=len(serial_number_errors), message="Number of occurences of Serial number error")

    def cleanup(self):
        self.container_asset = fun_test.shared_variables["container_asset"]
        post_fix_name = self.__class__.__name__ + "_test_log.txt"
        artifact_file_name = fun_test.get_test_case_artifact_file_name(post_fix_name=post_fix_name)
        fun_test.scp(source_ip=self.container_asset["host_ip"],
                     source_file_path="{}".format(SbpZynqSetupTemplate.TEST_LOG_FILE),
                     source_username=self.container_asset["mgmt_ssh_username"],
                     source_password=self.container_asset["mgmt_ssh_password"],
                     source_port=self.container_asset["mgmt_ssh_port"],
                     target_file_path=artifact_file_name)
        fun_test.add_auxillary_file(description="{} Log".format(post_fix_name),
                                    filename=artifact_file_name)



class TestCase4(FunTestCase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Secureboot=on, Watchdog=off",
                              steps="""
                              """)

    def setup(self):
        pass

    def run(self):
        container_asset = fun_test.shared_variables["container_asset"]

        linux_obj = Linux(host_ip=container_asset["host_ip"],
                          ssh_username=container_asset["mgmt_ssh_username"],
                          ssh_password=container_asset["mgmt_ssh_password"],
                          ssh_port=container_asset["mgmt_ssh_port"])
        sbp_setup = SbpZynqSetupTemplate(host=linux_obj, zynq_board_ip=ZYNC_BOARD_IP)

        sbp_setup.artifacts_setup(enroll=True, secure_boot=True, otp_settings={"watchdog": 0,
                                                                               "serial_no": "0x00000000000000000000000000000000"})

        stimuli_dir = "{}/validation/stimuli/short".format(SbpZynqSetupTemplate.LOCAL_REPOSITORY_DIR)
        stimuli_file = "{}/cmd_AES_CTR.py".format(stimuli_dir)

        # sbp_setup.get_status(secure_boot=True)
        test_log = sbp_setup.run_test_py(secure_boot=True,
                                         stimuli_file=stimuli_file,
                                         artifacts_dir=sbp_setup._get_artifacts_dir(secure_boot=True),
                                         get_log=True)

        serial_number_errors = re.findall("Serial number error: is OTP configured", test_log)
        fun_test.test_assert_expected(expected=2, actual=len(serial_number_errors), message="Number of occurences of Serial number error")

    def cleanup(self):
        self.container_asset = fun_test.shared_variables["container_asset"]
        post_fix_name = self.__class__.__name__ + "_test_log.txt"
        artifact_file_name = fun_test.get_test_case_artifact_file_name(post_fix_name=post_fix_name)
        fun_test.scp(source_ip=self.container_asset["host_ip"],
                     source_file_path="{}".format(SbpZynqSetupTemplate.TEST_LOG_FILE),
                     source_username=self.container_asset["mgmt_ssh_username"],
                     source_password=self.container_asset["mgmt_ssh_password"],
                     source_port=self.container_asset["mgmt_ssh_port"],
                     target_file_path=artifact_file_name)
        fun_test.add_auxillary_file(description="{} Log".format(post_fix_name),
                                    filename=artifact_file_name)


class TestCase5(FunTestCase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="OTP and start certificate have mismatched serial no",
                              steps="""
                              """)

    def setup(self):
        pass

    def run(self):
        container_asset = fun_test.shared_variables["container_asset"]

        linux_obj = Linux(host_ip=container_asset["host_ip"],
                          ssh_username=container_asset["mgmt_ssh_username"],
                          ssh_password=container_asset["mgmt_ssh_password"],
                          ssh_port=container_asset["mgmt_ssh_port"])
        sbp_setup = SbpZynqSetupTemplate(host=linux_obj, zynq_board_ip=ZYNC_BOARD_IP)


        config_template_path = fun_test.get_script_parent_directory() + "/flash_config.json"
        with open(config_template_path, "r") as f:
            contents = f.read()
            config = json.loads(contents)
            config["start_certificate"]["serial_number"] = "78502fa8f092ca5008b8d8992f642080"
            config["start_certificate"]["serial_number_mask"] = "ffffffffffffffffffffffffffffffff"

            sbp_setup.host.create_file(contents=json.dumps(config), file_name="/tmp/flash_config.json")
            sbp_setup.host.read_file(file_name="/tmp/flash_config.json")

            sbp_setup.artifacts_setup(enroll=True, secure_boot=True)
            sbp_setup.custom_flash_generator(artifacts_dir=sbp_setup._get_artifacts_dir(secure_boot=True))

            stimuli_dir = "{}/validation/stimuli/short".format(SbpZynqSetupTemplate.LOCAL_REPOSITORY_DIR)
            stimuli_file = "{}/cmd_AES_CTR.py".format(stimuli_dir)

            # sbp_setup.get_status(secure_boot=True)
            fun_test.test_assert(not sbp_setup.run_test_py(secure_boot=True,
                                             stimuli_file=stimuli_file,
                                             artifacts_dir=sbp_setup._get_artifacts_dir(secure_boot=True)), "Run test should fail")



    def cleanup(self):
        self.container_asset = fun_test.shared_variables["container_asset"]
        post_fix_name = self.__class__.__name__ + "_test_log.txt"
        artifact_file_name = fun_test.get_test_case_artifact_file_name(post_fix_name=post_fix_name)
        fun_test.scp(source_ip=self.container_asset["host_ip"],
                     source_file_path="{}".format(SbpZynqSetupTemplate.TEST_LOG_FILE),
                     source_username=self.container_asset["mgmt_ssh_username"],
                     source_password=self.container_asset["mgmt_ssh_password"],
                     source_port=self.container_asset["mgmt_ssh_port"],
                     target_file_path=artifact_file_name)
        fun_test.add_auxillary_file(description="{} Log".format(post_fix_name),
                                    filename=artifact_file_name)

class TestCase6(FunTestCase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="OTP and start certificate have mismatched serial no, but mask is permissive",
                              steps="""
                              """)

    def setup(self):
        pass

    def run(self):
        container_asset = fun_test.shared_variables["container_asset"]

        linux_obj = Linux(host_ip=container_asset["host_ip"],
                          ssh_username=container_asset["mgmt_ssh_username"],
                          ssh_password=container_asset["mgmt_ssh_password"],
                          ssh_port=container_asset["mgmt_ssh_port"])
        sbp_setup = SbpZynqSetupTemplate(host=linux_obj, zynq_board_ip=ZYNC_BOARD_IP)


        config_template_path = fun_test.get_script_parent_directory() + "/flash_config.json"
        with open(config_template_path, "r") as f:
            contents = f.read()
            config = json.loads(contents)
            config["start_certificate"]["serial_number"] = "78502fa8f092ca5008b8d8992f642080"
            config["start_certificate"]["serial_number_mask"] = "ffffffffffffffffffffffffffffff00"

            sbp_setup.host.create_file(contents=json.dumps(config), file_name="/tmp/flash_config.json")
            sbp_setup.host.read_file(file_name="/tmp/flash_config.json")

            sbp_setup.artifacts_setup(enroll=True, secure_boot=True)
            sbp_setup.custom_flash_generator(artifacts_dir=sbp_setup._get_artifacts_dir(secure_boot=True))

            stimuli_dir = "{}/validation/stimuli/short".format(SbpZynqSetupTemplate.LOCAL_REPOSITORY_DIR)
            stimuli_file = "{}/cmd_AES_CTR.py".format(stimuli_dir)

            # sbp_setup.get_status(secure_boot=True)
            fun_test.test_assert(sbp_setup.run_test_py(secure_boot=True,
                                             stimuli_file=stimuli_file,
                                             artifacts_dir=sbp_setup._get_artifacts_dir(secure_boot=True)), "Run test should not fail")



    def cleanup(self):
        self.container_asset = fun_test.shared_variables["container_asset"]
        post_fix_name = self.__class__.__name__ + "_test_log.txt"
        artifact_file_name = fun_test.get_test_case_artifact_file_name(post_fix_name=post_fix_name)
        fun_test.scp(source_ip=self.container_asset["host_ip"],
                     source_file_path="{}".format(SbpZynqSetupTemplate.TEST_LOG_FILE),
                     source_username=self.container_asset["mgmt_ssh_username"],
                     source_password=self.container_asset["mgmt_ssh_password"],
                     source_port=self.container_asset["mgmt_ssh_port"],
                     target_file_path=artifact_file_name)
        fun_test.add_auxillary_file(description="{} Log".format(post_fix_name),
                                    filename=artifact_file_name)


if __name__ == "__main__":
    ts = ContainerSetup()
    # ts.add_test_case(TestCase1())
    # ts.add_test_case(TestCase2())
    # ts.add_test_case(TestCase3())
    # ts.add_test_case(TestCase4())
    # ts.add_test_case(TestCase5())
    ts.add_test_case(TestCase6())
    ts.run()
