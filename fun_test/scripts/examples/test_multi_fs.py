from lib.system.fun_test import *
from lib.host.dpcsh_client import DpcshClient
from lib.topology.topology_helper import TopologyHelper
fun_test.enable_profiling()

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
        topology_helper.set_dut_parameters(dut_index=0, custom_boot_args="app=load_mods --dpc-uart --dpc-server --csr-replay --all_100g")
        fun_test.shared_variables["topology"] = topology_helper.get_topology()
        topology = topology_helper.deploy()
        fun_test.test_assert(topology, "Topology deployed")
        fs = topology.get_dut_instance(index=0)

        fs.get_come().command("lspci")


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
