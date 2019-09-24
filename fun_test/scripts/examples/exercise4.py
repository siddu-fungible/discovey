from lib.system.fun_test import *
from asset.asset_manager import AssetManager
from lib.host.linux import Linux


import os


class Setup(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Bring up the container
        """)

    def setup(self):
        os.environ["DOCKER_HOSTS_SPEC_FILE"] = fun_test.get_script_parent_directory() + "/local_docker_host.json"
        self.docker_host = AssetManager().get_any_docker_host()

        image_name = "ubuntu_template:latest"

        container_assets = []
        for i in xrange(2):
            container_name = "this_container_{}".format(i)
            container_asset = self.docker_host.setup_container(image_name=image_name,
                                                                    container_name=container_name,
                                                                    pool0_internal_ports=[22],
                                                                    auto_remove=True)
            fun_test.test_assert(container_asset, "Container launched")
            container_assets.append(container_asset)
            fun_test.test_assert(self.docker_host.ensure_container_idling(container_name=container_name), "Container {} UP".format(container_name))
        fun_test.shared_variables["container_assets"] = container_assets

    def cleanup(self):
        container_assets = fun_test.shared_variables["container_assets"]
        for container_asset in container_assets:
            self.docker_host.destroy_container(
                container_name=container_asset["name"],
                ignore_error=True)


class TestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Connect to a container",
                              steps="""
        1. Do something on the container.
                              """)

    def setup(self):
        pass

    def run(self):
        container_assets = fun_test.shared_variables["container_assets"]
        for container_asset in container_assets:
            linux_obj = Linux(host_ip=container_asset["host_ip"],
                              ssh_username=container_asset["mgmt_ssh_username"],
                              ssh_password=container_asset["mgmt_ssh_password"],
                              ssh_port=container_asset["mgmt_ssh_port"])

            linux_obj.command("ifconfig")
            fun_test.test_assert(True, "Done")

    def cleanup(self):
        pass


if __name__ == "__main__":
    ts = Setup()
    ts.add_test_case(TestCase1())
    ts.run()
