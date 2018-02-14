from lib.system.fun_test import *
from asset.asset_manager import AssetManager
from lib.host.docker_host import DockerHost
from lib.host.linux import Linux
from fun_settings import REGRESSION_USER, FUN_TEST_DIR


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. Step 1
        2. Step 2
        3. Step 3""")

    def setup(self):
        fun_test.log("Script-level setup")
        fun_test.shared_variables["some_variable"] = 123

    def cleanup(self):
        fun_test.log("Script-level cleanup")


class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Sanity Test 1",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        pass

    def cleanup(self):
        if "container_asset" in fun_test.shared_variables:
            fun_test.shared_variables["docker_host"].destroy_container(container_name=fun_test.shared_variables["container_asset"]["name"],
                                                                       ignore_error=True)


    def run(self):
        docker_host = AssetManager().get_any_docker_host()
        fun_test.shared_variables["docker_host"] = docker_host
        user = REGRESSION_USER
        workspace = dirname(abspath(dirname(abspath(FUN_TEST_DIR))))
        name = "parser"
        host_name = "parser"
        image_name = "reg-nw-full-build:v1"
        target_workspace = "/workspace"
        entry_point = "{}/Integration/tools/docker/funcp/user/fungible/scripts/parser-test.sh".format(target_workspace)
        environment_variables = {}
        environment_variables["DOCKER"] = True
        environment_variables["WORKSPACE"] = workspace
        user_mount = "/home/{0}:/home/{0}".format(user)
        workspace_mount = "{}:{}".format(workspace, target_workspace)
        container_name = "johns_parser"

        container_asset = docker_host.setup_container(image_name=image_name,
                                                      container_name=container_name,
                                                      command=entry_point,
                                                      pool0_internal_ports=[22],
                                                      mounts=[user_mount, workspace_mount],
                                                      user=user,
                                                      host_name=host_name,
                                                      working_dir=target_workspace,
                                                      auto_remove=True)
        fun_test.test_assert(container_asset, "Container launched")
        fun_test.shared_variables["container_asset"] = container_asset
        linux_obj = Linux(host_ip=container_asset["host_ip"],
                          ssh_username=container_asset["mgmt_ssh_username"],
                          ssh_password=container_asset["mgmt_ssh_password"],
                          ssh_port=container_asset["mgmt_ssh_port"])
        timer = FunTimer(max_time=180)
        passed_found = False
        while not timer.is_expired():
            output = linux_obj.command("cat {}/nutest.log".format(target_workspace))
            if "PASSED" in output:
                fun_test.log("Success")
                passed_found = True
                break
            fun_test.sleep("Nutest", seconds=10)
        fun_test.test_assert(passed_found, "NuTest")
        docker_host.destroy_container(container_name=container_name, ignore_error=True)


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
