from lib.system.fun_test import fun_test

class SbpZynqSetupTemplate:
    ZYNQ_SETUP_DIR = "/zynq_setup"
    REPOSITORY_DIR = "/repository"

    def __init__(self, host, local_repository, zynq_board_ip):
        self.host = host
        self.local_repository = local_repository
        self.zynq_board_ip = zynq_board_ip
        self.host.command("echo $MIPS_ELF_ROOT")
        self.host.command("ls -l {}".format(self.ZYNQ_SETUP_DIR))

    def setup(self):
        fun_test.test_assert(self.setup_local_repository(),
                             message="Setup local repository")
        fun_test.test_assert(self.setup_hsm(), "HSM install")
        fun_test.test_assert(self.setup_build(), "Build")
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
