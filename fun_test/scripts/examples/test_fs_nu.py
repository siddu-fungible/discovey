from lib.system.fun_test import *
from lib.host.dpcsh_client import DpcshClient
from lib.topology.topology_helper import TopologyHelper
from lib.templates.csi_perf.csi_perf_template import CsiPerfTemplate


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


def configure_endhost_interface(end_host, test_network, interface_name, timeout=30):
    interface_ip_unconfig = "ip addr del {} dev {}".format(test_network["test_interface_ip"],
                                                           interface_name)
    interface_ip_config = "ip addr add {} dev {}".format(test_network["test_interface_ip"],
                                                         interface_name)
    interface_mac_config = "ip link set {} address {}".format(interface_name,
                                                              test_network["test_interface_mac"])
    link_up_cmd = "ip link set {} up".format(interface_name)
    static_arp_cmd = "arp -s {} {}".format(test_network["test_net_route"]["gw"],
                                           test_network["test_net_route"]["arp"])

    end_host.sudo_command(command=interface_ip_unconfig, timeout=timeout)
    end_host.sudo_command(command=interface_ip_config, timeout=timeout)
    fun_test.test_assert_expected(expected=0,
                                  actual=end_host.exit_status(),
                                  message="Configuring test interface IP address")

    end_host.sudo_command(command=interface_mac_config)
    fun_test.test_assert_expected(expected=0,
                                  actual=end_host.exit_status(),
                                  message="Assigning MAC to test interface")

    end_host.sudo_command(command=link_up_cmd,
                          timeout=timeout)
    fun_test.test_assert_expected(expected=0,
                                  actual=end_host.exit_status(),
                                  message="Bringing up test link")

    fun_test.test_assert(end_host.ifconfig_up_down(interface=interface_name,
                                                   action="up"), "Bringing up test interface")

    end_host.ip_route_add(network=test_network["test_net_route"]["net"],
                          gateway=test_network["test_net_route"]["gw"],
                          outbound_interface=interface_name,
                          timeout=timeout)
    fun_test.test_assert_expected(expected=0,
                                  actual=end_host.exit_status(),
                                  message="Adding route to F1")

    end_host.sudo_command(command=static_arp_cmd,
                          timeout=timeout)
    fun_test.test_assert_expected(expected=0,
                                  actual=end_host.exit_status(),
                                  message="Adding static ARP to F1 route")


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
        f1_parameters = {0: {"boot_args": "app=mdt_test,load_mods,hw_hsu_test workload=storage --serial --memvol --dpc-server --dpc-uart --csr-replay --all_100g --nofreeze --useddr"},
                         1: {"boot_args": "app=mdt_test,load_mods,hw_hsu_test workload=storage --serial --memvol --dpc-server --dpc-uart --csr-replay --all_100g --nofreeze --useddr"}}

        perf_listener_host_name = "poc-server-04"  # figure this out from the topology spec
        perf_listener_ip = "20.1.1.1"              # figure this out from the topology spec
        csi_perf_enabled = fun_test.get_job_environment_variable("csi_perf")
        if csi_perf_enabled:
            f1_parameters[0]["boot_args"] = f1_parameters[0]["boot_args"] + " --perf csi-local-ip=29.1.1.2 csi-remote-ip={} pdtrace-hbm-size-kb=204800".format(perf_listener_ip)
            # f1_parameters[1]["boot_args"] = f1_parameters[1]["boot_args"] + " --perf csi-local-ip=29.1.1.2 csi-remote-ip={} pdtrace-hbm-size-kb=204800".format(perf_listener_ip)

        topology_helper.set_dut_parameters(dut_index=0, f1_parameters=f1_parameters)

        # s = SomeClass()
        # topology_helper.set_dut_parameters(dut_index=0, fun_cp_callback=s.some_callback)

        topology = topology_helper.deploy()
        fun_test.test_assert(topology, "Topology deployed")
        fs = topology.get_dut_instance(index=0)
        fun_test.shared_variables["topology"] = topology

        fpg_connected_hosts = topology.get_host_instances_on_fpg_interfaces(dut_index=0, f1_index=0)
        end_host = None
        for host_ip, host_info in fpg_connected_hosts.iteritems():
            fun_test.log("FPG: Host-IP: {}: host: {} Interfaces: {}".format(host_ip, str(host_info["host_obj"]), str(host_info["interfaces"])))
            end_host = host_info["host_obj"]
            break

        csr_network = {
            "0": {
                "test_interface_ip": "20.1.1.1/24",
                "test_interface_mac": "fe:dc:ba:44:66:30",
                "test_net_route": {
                    "net": "29.1.1.0/24",
                    "gw": "20.1.1.2",
                    "arp": "00:de:ad:be:ef:00"
                },
                "f1_loopback_ip": "29.1.1.1"
            },
            "4": {
                "test_interface_ip": "21.1.1.1/24",
                "test_interface_mac": "fe:dc:ba:44:66:31",
                "test_net_route": {
                    "net": "29.1.1.0/24",
                    "gw": "21.1.1.2",
                    "arp": "00:de:ad:be:ef:00"
                },
                "f1_loopback_ip": "29.1.1.1"
            }
        }

        configure_endhost_interface(end_host=end_host, test_network=csr_network["0"], interface_name=end_host.extra_attributes["test_interface_name"])

        if csi_perf_enabled:
            p = CsiPerfTemplate(perf_collector_host_name=perf_listener_host_name, listener_ip=perf_listener_ip, fs=fs)
            p.prepare(f1_index=0)
            p.start(f1_index=0)
            for i in range(1):
                try:
                    dpcsh_client = fs.get_dpc_client(f1_index=0, auto_disconnect=True)
                    # do some activity
                    # dpcsh_client.json_execute(verb="peek", data="stats/vppkts", command_duration=10)
                    dpcsh_client.json_execute(verb="echo", command_duration=10)

                except Exception as ex:
                    fun_test.critical(str(ex))
            p.stop(f1_index=0)




if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
