from lib.system.fun_test import *
from lib.topology.topology_helper import TopologyHelper

class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. Step 1
        2. Step 2
        3. Step 3""")

    def setup(self):
        fun_test.log("Script-level setup")

    def cleanup(self):
        fun_test.log("Script-level cleanup")


class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Setup FS1600",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        fun_test.log("Testcase setup")
        fun_test.sleep("demo", seconds=1)

    def cleanup(self):
        fun_test.log("Testcase cleanup")
        fun_test.shared_variables["topology"].cleanup()

    def run(self):
        # fs = Fs.get(disable_f1_index=1)
        topology_helper = TopologyHelper()
        available_dut_indexes = topology_helper.get_available_duts().keys()

        for available_dut_index in available_dut_indexes:
            topology_helper.set_dut_parameters(dut_index=available_dut_index, custom_boot_args="app=load_mods --dpc-uart --dpc-server --csr-replay --all_100g")

        topology = topology_helper.deploy()
        fun_test.test_assert(topology, "Topology deployed")

        for available_dut_index in available_dut_indexes:
            fs_instance = topology.get_dut_instance(index=available_dut_index)
            storage_controller = fs_instance.get_f1(0).get_dpc_storage_controller()
            storage_controller.json_execute(verb="peek", data="stats/vppkts", command_duration=4)

        available_host_names = topology_helper.get_available_hosts().keys()
        for available_host_name in available_host_names:
            host = topology.get_host_instance(dut_index=available_dut_indexes[0], name=available_host_name)  #For example just use DUT index 0
            host.lspci()

        fun_test.log("Num Hosts: {}, hosts: {}".format(len(available_host_names), str(available_host_names)))
        fun_test.shared_variables["topology"] = topology




if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
