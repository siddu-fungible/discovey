from lib.system.fun_test import *
from asset.asset_manager import AssetManager
from lib.host.linux import Linux
from fun_settings import FUN_TEST_DIR
import re
from lib.templates.system.sbp_template import SbpZynqSetupTemplate

# SBP_FIRMWARE_REPO_DIR = INTEGRATION_DIR + "/../SBPFirmware"
SBP_FIRMWARE_REPO_DIR = "/Users/johnabraham/temp2/SBPFirmware"
BIT_STREAM = "SilexBitfiles/esecure_top_fpga_sbppuf_20180307.bit"
ZYNC_BOARD_IP = "10.1.23.106"


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
        # localhost.command("git checkout drop_0_5_0+silex")
        fun_test.test_assert_expected(expected=0, actual=localhost.exit_status(), message="Git pull")

    def cleanup(self):
        self.docker_host.destroy_container(container_name=self.container_name, ignore_error=True)
        fun_test.log(fun_test.get_wall_clock_time())


class TestCase2(FunTestCase):
    secure_boot = True
    enroll = True

    def describe(self):
        self.set_test_details(id=2,
                              summary="secureboot=on, with enrollment certificate",
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
        self.linux_obj = linux_obj
        sbp_setup = SbpZynqSetupTemplate(host=linux_obj, zynq_board_ip=ZYNC_BOARD_IP, bit_stream=BIT_STREAM)
        fun_test.test_assert(sbp_setup.setup(), "Setup")
        if self.enroll:
            fun_test.test_assert(sbp_setup.enroll(), "Enrollment")

        stimuli_dir = "{}/validation/stimuli/short".format(SbpZynqSetupTemplate.LOCAL_REPOSITORY_DIR)
        # stimuli_file = "{}/test_stack_protection.py".format(stimuli_dir)
        stimuli_file = "{}/test_tamper.py".format(stimuli_dir)

        if self.enroll:
            fun_test.test_assert(sbp_setup.run_test_py(secure_boot=self.secure_boot,
                                                       stimuli_file=stimuli_file, timeout=900),
                                 message="Run test py")
        else:
            fun_test.test_assert(not sbp_setup.run_test_py(secure_boot=self.secure_boot,
                                                           stimuli_file=stimuli_file),
                                 message="Run test py should fail without enrollment")

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
    ts.add_test_case(TestCase2())
    ts.run()
