from lib.system.fun_test import *
from asset.asset_manager import AssetManager
from lib.host.linux import Linux
from lib.templates.system.sbp_template import SbpZynqSetupTemplate
from lib.templates.system.sbp_challenge_template import SbpChallengeTemplate
import random

ZYNC_BOARD_IP = "10.1.23.106"
PROBE_IP = "10.1.23.108"
PROBE_NAME = "sp218"



class ContainerSetup(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Bring up the container
        """)

    def setup(self):
        pass
        # self.docker_host = AssetManager().get_any_docker_host()
        # self.container_asset = SbpZynqSetupTemplate(host=None, zynq_board_ip=None).setup_container(git_pull=False)

    def cleanup(self):
        container_asset = fun_test.shared_variables["container_asset"]
        self.docker_host.destroy_container(container_name=container_asset["name"], ignore_error=True)

class TestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="secureboot=off",
                              steps="""
        1. Do something on the container.
                              """)

    def setup(self):
        pass

    def run(self):

        # container_asset = fun_test.shared_variables["container_asset"]
        '''
        linux_obj = Linux(host_ip=container_asset["host_ip"],
                          ssh_username=container_asset["mgmt_ssh_username"],
                          ssh_password=container_asset["mgmt_ssh_password"],
                          ssh_port=container_asset["mgmt_ssh_port"])
        '''
        linux_obj = Linux(host_ip="127.0.0.1", ssh_username="root", ssh_password="fun123", ssh_port=3220,)
        sbp_setup = SbpZynqSetupTemplate(host=linux_obj, zynq_board_ip=ZYNC_BOARD_IP)
        # fun_test.test_assert(sbp_setup.setup(), "Setup")
        developer_cert = SbpZynqSetupTemplate.DEVELOPER_CERT_FILE
        developer_private_key = SbpZynqSetupTemplate.DEVELOPER_PRIVATE_KEY_FILE


        # i = 0

        # fun_test.test_assert(sbp_setup.enroll(), "Enrollment")
        stimuli_dir = "{}/validation/stimuli/short".format(SbpZynqSetupTemplate.LOCAL_REPOSITORY_DIR)
        stimuli_file = "{}/cmd_AES_CBC.py".format(stimuli_dir)
        sbp_setup.get_start_certificate()
        sbp_setup.setup_developer_cert(cert_filename=developer_cert, private_key_filename=developer_private_key)

        # sbp_setup.run_test_py(secure_boot=True, stimuli_file=stimuli_file),

        sbp_challenge_template = SbpChallengeTemplate(board_ip=ZYNC_BOARD_IP, probe_ip=PROBE_IP, probe_name=PROBE_NAME)
        sbp_challenge_template.setup_board()
        sbp_challenge_template.test()
        # sbp_challenge_template.disable_tamper(tamper=0xFFFFFFFF)
        l = 0xFD000000
        # sbp_challenge_template.write_command(command=0xFFFFFFFF)
        for i in range(100):
            sbp_challenge_template.write_command(command=l)
            # l = l + random.randint(0, 0xFFFFFFFF)
            l = l + i


        # for i in range(50):
        #    sbp_challenge_template.test2(0x0000C000)
            # sbp_challenge_template.test2(0xFFFFFFFF)
            # sbp_challenge_template.test2(0x0000FF00)



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
    ts.add_test_case(TestCase1())
    ts.run()
