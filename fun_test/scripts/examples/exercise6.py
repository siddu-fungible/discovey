from lib.system.fun_test import *
from lib.topology.topology_helper import TopologyHelper


import os
# os.environ["DOCKER_HOSTS_SPEC_FILE"] = fun_test.get_script_parent_directory() + "/local_docker_host_with_storage.json"


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Setup one F1 container
        2. Start QEMU within the container
        """)

    def setup(self):
        os.environ[
            "DOCKER_HOSTS_SPEC_FILE"] = fun_test.get_script_parent_directory() + "/remote_docker_host_with_storage.json"

        # topology_obj_helper = TopologyHelper(spec=topology_dict) use locally defined dictionary variable
        topology_obj_helper = TopologyHelper(spec_file="./single_f1_with_qemu_yocto.json")
        topology = topology_obj_helper.deploy()
        fun_test.test_assert(topology, "Ensure deploy is successful")
        fun_test.shared_variables["topology"] = topology

    def cleanup(self):
        if "topology" in fun_test.shared_variables:
            fun_test.shared_variables["topology"].cleanup()
        pass


class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Do some operation on QEMU",
                              steps="""
    1. Connect to QEMU
    2. Execute the date command
                              """)

    def setup(self):
        self.topology = fun_test.shared_variables["topology"]

    def cleanup(self):
        pass

    def run(self):
        topology = fun_test.shared_variables["topology"]
        dut_instance0 = topology.get_dut_instance(index=0)
        fun_test.test_assert(dut_instance0, "Retrieved dut instance 0")

        qemu_host = self.topology.get_host_instance(dut_index=0, interface_index=0, host_index=0)
        qemu_host.command("date")

if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
