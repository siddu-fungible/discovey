from lib.system.fun_test import *
from lib.host.dpcsh_client import DpcshClient
from lib.topology.topology_helper import TopologyHelper
from lib.topology.end_points import *

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
        topology_helper.set_dut_parameters(disable_f1_index=1, dut_index=0, custom_boot_args="app=load_mods --dpc-uart --dpc-server --csr-replay --all_100g")

        topology = topology_helper.deploy()
        fun_test.test_assert(topology, "Topology deployed")
        fs = topology.get_dut_instance(index=0)
        fun_test.shared_variables["topology"] = topology

        fun_test.log("Dut: spec")
        fun_test.log(topology.get_dut(index=0).spec)

        fun_test.log("FPG interfaces:")
        fpg_interfaces = topology.get_dut(index=0).get_fpg_interfaces(f1_index=0)
        for fpg_interface_index, fpg_interface in fpg_interfaces.items():
            peer_end_point = fpg_interface.get_peer_instance()
            fun_test.log("F1 index: {} FPG Interface: {} IP: {}".format(fpg_interface.f1_index, fpg_interface_index, fpg_interface.ip))
            if peer_end_point.type == EndPoint.END_POINT_TYPE_SWITCH:
                switch_name = peer_end_point.name
                fun_test.log("Name: {}".format(switch_name))
                switch = topology.get_switch(name=switch_name)
                fun_test.log("Switch spec: {}".format(json.dumps(switch.spec, indent=4)))
                fun_test.log("Port: {}".format(peer_end_point.port))

        fun_test.log("Bond Interfaces:")
        bond_interfaces = topology.get_dut(index=0).get_bond_interfaces(f1_index=0)
        for bond_interface_index, bond_interface in bond_interfaces.items():
            fun_test.log("Bond interface index: {}".format(bond_interface_index))
            fun_test.log("IP: {}".format(bond_interface.ip))
            fpg_slaves = bond_interface.fpg_slaves
            fun_test.log("FPG slaves: {}".format(fpg_slaves))

            for fpg_slave_index in fpg_slaves:
                fpg_interface = topology.get_dut(index=0).get_fpg_interface(f1_index=0, interface_index=fpg_slave_index)
                peer_end_point = fpg_interface.get_peer_instance()
                if peer_end_point.type == EndPoint.END_POINT_TYPE_SWITCH:
                    switch_name = peer_end_point.name
                    fun_test.log("Name: {}".format(switch_name))
                    switch = topology.get_switch(name=switch_name)
                    fun_test.log("Switch spec: {}".format(json.dumps(switch.spec, indent=4)))
                    fun_test.log("Port: {}".format(peer_end_point.port))

        fun_test.log("Hosts")
        hosts = topology.get_hosts()
        for host_name, host in hosts.items():
            test_interfaces = host.get_test_interfaces()
            test_interface_0 = host.get_test_interface(index=0)

            fun_test.log("Host-IP: {}".format(test_interface_0.ip))
            fun_test.log("Peer-info: {}".format(test_interface_0.peer_info))
            fun_test.log("Switch-name: {}".format(test_interface_0.peer_info["name"]))
            fun_test.log("Switch-port: {}".format(test_interface_0.peer_info["port"]))

            host_instance = host.get_instance()
            # host_instance.command("date")





if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
