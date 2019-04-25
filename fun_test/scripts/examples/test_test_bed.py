from lib.system.fun_test import *
from lib.host.dpcsh_client import DpcshClient
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
        topology_helper.set_dut_parameters(dut_index=0, custom_boot_args="app=hw_hsu_test --disable-wu-watchdog --dpc-uart --dpc-server --csr-replay --retimer --all_100g")
        topology = topology_helper.deploy()
        fun_test.test_assert(topology, "Topology deployed")
        fs = topology.get_dut_instance(index=0)
        fun_test.shared_variables["topology"] = topology

        host_instance1 = topology.get_host_instance(dut_index=0, host_index=0, interface_index=4)
        host_instance2 = topology.get_host_instance(dut_index=0, host_index=0, interface_index=5)
        print host_instance1, host_instance2
        dpcsh_client = DpcshClient(target_ip=host_instance1.host_ip, target_port=fs.get_come().get_dpc_port(0))
        dpcsh_client.json_execute(verb="peek", data="stats/vppkts", command_duration=4)



if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
