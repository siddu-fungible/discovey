from lib.system.fun_test import *
from asset.asset_manager import AssetManager
from lib.host.linux import Linux
from fun_settings import REGRESSION_USER, REGRESSION_USER_PASSWORD, FUN_TEST_DIR
import re, os


class FunCPContainerInit(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Launch container that pulls FunCP, FunOS and FunSDK sources
        """)

    def setup(self):
        self.docker_host = AssetManager().get_any_docker_host()
        user = REGRESSION_USER
        user_passwd = REGRESSION_USER_PASSWORD
        workspace = dirname(abspath(dirname(abspath(FUN_TEST_DIR))))
        self.container_name = "funcp"
        f1_hostname = "funcp"
        f1_image_name = "nw-reg-user:v1"
        self.target_workspace = "/workspace"
        arguments = '-f master -o master -n /workspace/nutest.json'
        entry_point = "{}/Integration/tools/docker/funcp/user/fungible/scripts/parser-test.sh {}".format(self.target_workspace, arguments)
        environment_variables = {"DOCKER": True,
                                 "WORKSPACE": workspace}
        home_mount = "/home/{0}:/home/{0}".format(user)
        workspace_mount = "{}:{}".format(workspace, self.target_workspace)
        csr_mount = "{}:{}".format('/tmp', '/tmp')
        mips_mount = "{}:{}".format('/opt/cross', '/opt/cross')

        self.container_asset = self.docker_host.setup_container(image_name=f1_image_name,
                                                                container_name=self.container_name,
                                                                command=entry_point,
                                                                pool0_internal_ports=[22],
                                                                mounts=[home_mount, workspace_mount, csr_mount, mips_mount],
                                                                user=user,
                                                                host_name=f1_hostname,
                                                                working_dir=self.target_workspace,
                                                                auto_remove=True,
                                                                environment_variables=environment_variables)

        fun_test.test_assert(self.container_asset, "Container launched")
        fun_test.shared_variables["container_asset"] = self.container_asset
        fun_test.shared_variables["target_workspace"] = self.target_workspace

        linux_obj = Linux(host_ip=self.docker_host.host_ip,
                          ssh_username=self.docker_host.ssh_username,
                          ssh_password=self.docker_host.ssh_password)

        timer = FunTimer(max_time=300)
        container_up = False
        while not timer.is_expired():
            output = linux_obj.command(command="docker logs {}".format(self.container_name), include_last_line=True)
            if re.search('Idling', output):
                container_up = True
                break
            fun_test.sleep("Waiting for container to come up", seconds=10)
        fun_test.test_assert(container_up, "Container UP")

    def cleanup(self):
        for log_file in ["psim.log", "nutest.txt"]:
            artifact_file_name = fun_test.get_test_case_artifact_file_name(post_fix_name=log_file)
            fun_test.scp(source_ip=self.container_asset["host_ip"],
                 source_file_path="{}/{}".format(self.target_workspace, log_file),
                 source_username=self.container_asset["mgmt_ssh_username"],
                 source_password=self.container_asset["mgmt_ssh_password"],
                 source_port=self.container_asset["mgmt_ssh_port"],
                 target_file_path=artifact_file_name)
            fun_test.add_auxillary_file(description="{} Log".format(log_file.split('.')[0]), filename=artifact_file_name)

        self.docker_host.destroy_container(
            container_name=self.container_name,
            ignore_error=True)


class FunCPFunOSBuilder(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Build FunCP/FunOS",
                              steps="""
        1. Build FunCP
        2. Build FunOS
                              """)

    def setup(self):
        pass

    def run(self):

        container_asset = fun_test.shared_variables["container_asset"]
        target_workspace = fun_test.shared_variables["target_workspace"]
        BUILD_STATUS = "No such file or directory"
        TEST_STATUS = True

        linux_obj = Linux(host_ip=container_asset["host_ip"],
                          ssh_username=container_asset["mgmt_ssh_username"],
                          ssh_password=container_asset["mgmt_ssh_password"],
                          ssh_port=container_asset["mgmt_ssh_port"])

        cmd_list = ["bash", "cd {}/FunControlPlane".format(target_workspace), "make -j8"]
        for cmd in cmd_list:
            linux_obj.command(cmd, timeout=600)
        output = linux_obj.command(command="ls -ll {}/FunControlPlane/build".format(target_workspace))
        if re.search(BUILD_STATUS, output):
            TEST_STATUS = False
        fun_test.test_assert(TEST_STATUS, "Build FunCP")

        cmd_list = ["bash", "cd {}/FunOS".format(target_workspace), "make -j8 MACHINE=posix"]
        for cmd in cmd_list:
            linux_obj.command(cmd, timeout=600)
        output = linux_obj.command(command="ls -al {}/FunOS/build".format(target_workspace))
        if re.search(BUILD_STATUS, output):
            TEST_STATUS = False
        fun_test.test_assert(TEST_STATUS, "Build FunOS")

    def cleanup(self):
        pass


class GenerateCSR(FunTestCase):


    def describe(self):
        self.set_test_details(id=2,
                              summary="Generate CSR Override File",
                              steps="""
        1. Generate CSR override file that will be used to replay CSRs onto Palladium
                              """)

    def setup(self):
        pass

    def run(self):

        container_asset = fun_test.shared_variables["container_asset"]
        target_workspace = fun_test.shared_variables["target_workspace"]

        TEST_STATUS = True
        CSR_CFG = '/tmp/csr_override.cfg'
        CSR_FUNOS = '{}/FunOS/Configfiles/configs/csr_override.cfg'.format(target_workspace)

        linux_obj = Linux(host_ip=container_asset["host_ip"],
                          ssh_username=container_asset["mgmt_ssh_username"],
                          ssh_password=container_asset["mgmt_ssh_password"],
                          ssh_port=container_asset["mgmt_ssh_port"])

        cmd_list = ['bash', 'sudo rm -rf {}'.format(CSR_CFG),
                    'sudo -E {}/FunControlPlane/scripts/nutest/test_l3_traffic.py -s -d'.format(target_workspace)]
        try:
            for cmd in cmd_list:
                linux_obj.command(cmd, timeout=240)
        except Exception as ex:
            TEST_STATUS = False
            fun_test.critical(str(ex))

        cmd_list = ["reset", "ls -lrt {}".format(CSR_CFG)]
        for cmd in cmd_list:
            output = linux_obj.command(cmd)
        if re.search('No such file', output):
            TEST_STATUS = False
        else:
            cmd_list = ["echo ']}' >> /tmp/csr_override.cfg",
                        'cp {} {}'.format(CSR_CFG, CSR_FUNOS),
                        'sudo pkill funos-posix',
                        'sudo pkill qemu']
            try:
                for cmd in cmd_list:
                    linux_obj.command(cmd)
            except Exception as ex:
                TEST_STATUS = False
                fun_test.critical(str(ex))

        fun_test.test_assert(TEST_STATUS, "Generate CSR")

    def cleanup(self):
        pass


class BuildPalladiumImage(FunTestCase):

    def describe(self):
        self.set_test_details(id=3,
                              summary="Build Palladium Image",
                              steps="""
        1. Build Palladium Image.
        2. Place un-compressed image on server101.
                              """)

    def setup(self):
        pass


    def run(self):

        container_asset = fun_test.shared_variables["container_asset"]
        target_workspace = fun_test.shared_variables["target_workspace"]
        TEST_STATUS = True
        BUILD_STATUS = "No such file or directory"
        PALLADIUM_IMG = 'funos-f1-palladium.install.bz2'
        PALLADIUM_IMG_UNZIP = 'funos-f1-palladium.install'
        PALLADIUM_IMG_PATH = '{}/FunOS/build/{}'.format(target_workspace, PALLADIUM_IMG)
        PALLADIUM_IMG_UNZIP_PATH = '{}/FunOS/build/{}'.format(target_workspace, PALLADIUM_IMG_UNZIP) 
        HOST = 'server101'
        DEBUG = ''
        DPC_UART = '--dpc-uart'
        MAKE_CMD = 'make MACHINE=f1-palladium BOOTARGS="app=port_test ' \
                   '--hwdebug {} {} --csr-replay --no-halt" install > ' \
                   '{}/palladium_build.log'.format(DEBUG, DPC_UART, target_workspace)

        linux_obj = Linux(host_ip=container_asset["host_ip"],
                          ssh_username=container_asset["mgmt_ssh_username"],
                          ssh_password=container_asset["mgmt_ssh_password"],
                          ssh_port=container_asset["mgmt_ssh_port"])

        cmd_list = ['cd {}/FunOS'.format(target_workspace), MAKE_CMD]
        try:
            for cmd in cmd_list:
                linux_obj.command(cmd, timeout=1200)
        except Exception as ex:
            TEST_STATUS = False
            fun_test.critical(str(ex))

        output = linux_obj.command(
            command="ls -al {}".format(PALLADIUM_IMG_PATH))
        if re.search(BUILD_STATUS, output):
            TEST_STATUS = False
        else:
            cmd_list = ['bzip2 -d {}'.format(PALLADIUM_IMG_PATH),
                        'scp {} {}@{}://home/{}/image/'.format(PALLADIUM_IMG_UNZIP_PATH, REGRESSION_USER, HOST, REGRESSION_USER)]
            try:
                for cmd in cmd_list:
                    linux_obj.command(cmd, timeout=60)
            except Exception as ex:
                TEST_STATUS = False
                fun_test.critical(str(ex))

        fun_test.test_assert(TEST_STATUS, "Build Palladium Image")


    def cleanup(self):
        pass


if __name__ == "__main__":
    ts = FunCPContainerInit() 
     
    for tc in (FunCPFunOSBuilder,
               GenerateCSR,
               BuildPalladiumImage,
               ):
        ts.add_test_case(tc())
    '''
    for tc in (GenerateCSR,
               BuildPalladiumImage,
               ):
        ts.add_test_case(tc())
    '''
    ts.run()
