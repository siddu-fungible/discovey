from lib.system.fun_test import *
from lib.host.dpcsh_client import DpcshClient
from lib.topology.topology_helper import TopologyHelper


class SomeClass():
    def some_callback(self, come):
        fun_test.log("inside callback")
        fun_test.log("ComE: callback: {}".format(come.command("date")))

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
        # topology_helper.set_dut_parameters(dut_index=0, custom_boot_args="app=load_mods --dpc-uart --dpc-server --csr-replay --retimer --all_100g")
        # topology_helper.set_dut_parameters(dut_index=0, custom_boot_args="app=load_mods --dpc-uart --dpc-server --csr-replay retimer=0,1 --all_100g")
        topology_helper.set_dut_parameters(dut_index=0, custom_boot_args="app=load_mods --dpc-uart --dpc-server --csr-replay --all_100g")

        """ For FunCP callback only"""
        # s = SomeClass()
        # topology_helper.set_dut_parameters(dut_index=0, fun_cp_callback=s.some_callback)


        topology = topology_helper.deploy()
        fun_test.test_assert(topology, "Topology deployed")
        fs = topology.get_dut_instance(index=0)
        fun_test.shared_variables["topology"] = topology

        come = fs.get_come()
        fun_test.test_assert(come, "ComE ready: {}".format(str(come)))
        lspci_output = come.lspci(device="1dad:", verbose=True)
        fun_test.log(json.dumps(lspci_output, indent=4))

        host_instance_0 = topology.get_host_instance(dut_index=0, host_index=0, ssd_interface_index=0)
        if host_instance_0:
            fun_test.test_assert(host_instance_0, "Host instance on ssd interface 1: {}".format(str(host_instance_0)))
            lspci_output = host_instance_0.lspci(device="1dad:", verbose=True)
            fun_test.log(json.dumps(lspci_output, indent=4))

        host_instance_4 = topology.get_host_instance(dut_index=0, host_index=0, ssd_interface_index=4)
        if host_instance_4:
            fun_test.test_assert(host_instance_4, "Host instance on ssd interface 4: {}".format(str(host_instance_4)))
            lspci_output = host_instance_4.lspci(device="1dad:", verbose=True)
            fun_test.log(json.dumps(lspci_output, indent=4))

        host_intance_fpg_0 = topology.get_host_instance(dut_index=0, host_index=0, fpg_interface_index=0, f1_index=0)

        # dpcsh_client0 = DpcshClient(target_ip=come.host_ip, target_port=come.get_dpc_port(0))
        # dpcsh_client0.json_execute(verb="peek", data="stats/vppkts", command_duration=4)

        # dpcsh_client1 = DpcshClient(target_ip=come.host_ip, target_port=come.get_dpc_port(1))
        # dpcsh_client1.json_execute(verb="peek", data="stats/vppkts", command_duration=4)

        # Some more helpers
        ssd_connected_hosts = topology.get_host_instances_on_ssd_interfaces(dut_index=0)
        for host_ip, host_info in ssd_connected_hosts.iteritems():
            fun_test.log("SSD: Host-IP: {}: host: {} Interfaces: {}".format(host_ip, str(host_info["host_obj"]), str(host_info["interfaces"])))

        fpg_connected_hosts = topology.get_host_instances_on_fpg_interfaces(dut_index=0, f1_index=0)
        for host_ip, host_info in fpg_connected_hosts.iteritems():
            fun_test.log("FPG: Host-IP: {}: host: {} Interfaces: {}".format(host_ip, str(host_info["host_obj"]), str(host_info["interfaces"])))

        fpg_connected_duts = topology.get_dut_instances_on_fpg_interfaces(dut_index=0, f1_index=0)
        for fpg_connected_dut in fpg_connected_duts:
            dut_obj = fpg_connected_dut["dut_obj"]
            come = dut_obj.get_come()
            try:
                dpcsh_client = DpcshClient(target_ip=come.host_ip, target_port=come.get_dpc_port(0))
                dpcsh_client.json_execute(verb="peek", data="stats/vppkts", command_duration=4)
            except:
                pass
            interface_obj = fpg_connected_dut["interface_obj"]
            fun_test.log("F1: {} FPG Interface: {}".format(interface_obj.f1_index, interface_obj.index))





if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
