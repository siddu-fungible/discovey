from lib.system.fun_test import *
from asset.asset_manager import AssetManager
from lib.host.linux import Linux
from fun_settings import REGRESSION_USER, REGRESSION_USER_PASSWORD, FUN_TEST_DIR
import re


class FunControlPlaneSanity(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Bring up FunControlPlane (running in QEMU) and PSIM inside docker container
        2. Perform L3 NH tests
        3. Execute Parser (FPG, ERP, ETP, FAE) tests
        """)

    def setup(self):
        self.docker_host = AssetManager().get_any_docker_host()
        user = REGRESSION_USER
        user_passwd = REGRESSION_USER_PASSWORD
        workspace = dirname(abspath(dirname(abspath(FUN_TEST_DIR))))
        self.container_name = "parser"
        f1_hostname = "parser"
        f1_image_name = "reg-nw-user:v1"
        self.target_workspace = "/workspace"
        entry_point = "{}/Integration/tools/docker/funcp/user/fungible/scripts/parser-test.sh".format(self.target_workspace)
        environment_variables = {"DOCKER": True,
                                 "WORKSPACE": workspace}
        home_mount = "/home/{0}:/home/{0}".format(user)
        workspace_mount = "{}:{}".format(workspace, self.target_workspace)

        self.container_asset = self.docker_host.setup_container(image_name=f1_image_name,
                                                                container_name=self.container_name,
                                                                command=entry_point,
                                                                pool0_internal_ports=[22],
                                                                mounts=[home_mount, workspace_mount],
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
        for log_file in ["psim.log", "nutest.txt", "ptf.log"]:
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


class NwSanitySimpleL3Integration(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Sanity L3 Integration Test",
                              steps="""
        1. Launch Qemu + PSIM.
        2. Copy prebuilt bins/libs from dochub.
        3. Copy FunCP bins/libs into qemu that is being run as CC-linux
        4. Push configs (in json) to FunOS->model
        5. Test by sending traffic from PTF 
                              """)

    def setup(self):
        pass

    def run(self):

        qemu_status = "qemux86-64 login:"
        sanity_status = "PASSED"
        escape_seq = "grep"

        container_asset = fun_test.shared_variables["container_asset"]
        target_workspace = fun_test.shared_variables["target_workspace"]

        linux_obj = Linux(host_ip=container_asset["host_ip"],
                          ssh_username=container_asset["mgmt_ssh_username"],
                          ssh_password=container_asset["mgmt_ssh_password"],
                          ssh_port=container_asset["mgmt_ssh_port"])

        output = linux_obj.command("bash")
        output = linux_obj.command("cd {}/FunControlPlane".format(target_workspace))
        output = linux_obj.command("make venv")
        output = linux_obj.command(
            command="sudo -E python -u {}/FunControlPlane/scripts/nutest/test_l3_traffic.py -p -b -s > {}/nutest.txt 2>&1"
            .format(target_workspace, target_workspace), timeout=300)

        timer = FunTimer(max_time=180)
        status = False
        while not timer.is_expired():
            output = linux_obj.command(command="grep '{}' {}/psim.log".format(qemu_status, target_workspace),
                                       include_last_line=True)
            if re.search(qemu_status, output) and not re.search(escape_seq, output): 
                fun_test.log("PSIM + QEMU up")
                status = True
                break
            fun_test.sleep("Waiting for QEMU/PSIM to come up", seconds=10)
        fun_test.test_assert(status, "QEMU/PSIM UP")

        timer = FunTimer(max_time=120)
        status = False
        while not timer.is_expired():
            output = linux_obj.command(command="grep '{}' {}/nutest.txt".format(sanity_status, target_workspace),
                                       include_last_line=True)
            if re.search(sanity_status, output) and not re.search(escape_seq, output):
                fun_test.log("NwSanitySimpleL3Integration Success")
                status = True
                break
            fun_test.sleep("Waiting for NwSanitySimpleL3Integration test to finish", seconds=10)
        fun_test.test_assert(status, "NwSanitySimpleL3Integration Completed")

    def cleanup(self):
        pass


class NwSanityPRV(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="NU Parser Test",
                              steps="""
        1. Needs environment setup in previous test.
        2. Send traffic from PTF to verify Parser logic.
                              """)

    def setup(self):
        pass

    def run(self):
        prv_completed = "TEST RUN END"
        prv_status = "ATTENTION|FAIL|ERROR|RuntimeError"
        escape_seq = "grep"

        container_asset = fun_test.shared_variables["container_asset"]
        target_workspace = fun_test.shared_variables["target_workspace"]

        linux_obj = Linux(host_ip=container_asset["host_ip"],
                          ssh_username=container_asset["mgmt_ssh_username"],
                          ssh_password=container_asset["mgmt_ssh_password"],
                          ssh_port=container_asset["mgmt_ssh_port"])

        output = linux_obj.command("bash")
        output = linux_obj.command("cd {}/FunControlPlane".format(target_workspace))
        output = linux_obj.command("make venv")
        output = linux_obj.command(
            command="sudo -E python -u {}/FunControlPlane/scripts/nutest/test_l3_traffic.py --traffic --testcase prv >> {}/nutest.txt 2>&1"
                        .format(target_workspace, target_workspace), timeout=600)

        timer = FunTimer(max_time=600)
        status = False
        while not timer.is_expired():
            output = linux_obj.command(command="grep '{}' {}/ptf.log".format(prv_completed, target_workspace),
                                       include_last_line=True)
            if re.search(prv_completed, output) and not re.search(escape_seq, output):
                status = True
                break
            fun_test.sleep("Waiting for NwSanityPRV to complete", seconds=60)
        fun_test.test_assert(status, "NwSanityPRV Completed")

        status = True
        output = linux_obj.command(command="grep -E '{}' {}/nutest.txt".format(prv_status, target_workspace))
        for res in prv_status.split('|'):
            if re.search(res, output) and not re.search(escape_seq, output):
                status = False
        fun_test.test_assert(status, "NwSanityPRV Result")


    def cleanup(self):
        pass


if __name__ == "__main__":
    ts = FunControlPlaneSanity()
    for tc in (NwSanitySimpleL3Integration,
               NwSanityPRV
               ):
        ts.add_test_case(tc())
    ts.run()
