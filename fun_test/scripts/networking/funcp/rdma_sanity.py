from lib.system.fun_test import *
from lib.utilities.funcp_config import *
from scripts.networking.funcp.helper import *
from scripts.networking.funeth.sanity import Funeth
from lib.topology.topology_helper import TopologyHelper
from lib.templates.networking.rdma_tools import Rocetools


class ScriptSetup(FunTestScript):
    server_key = {}

    def describe(self):
        self.set_test_details(steps="1. Make sure correct FS system is selected")

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def cleanup(self):
        # host_obj = fun_test.shared_variables["hosts_obj"]

        # Check if funeth is loaded or else bail out
        # for obj in host_obj:
        #     host_obj[obj][0].sudo_command("rmmod funrdma")
        # fun_test.log("Unload funrdma drivers")
        pass
        # funcp_obj.cleanup_funcp()
        # for server in servers_mode:
        #     critical_log(expression=rmmod_funeth_host(hostname=server), message="rmmod funeth on host")


class BringupSetup(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=1,
                              summary="Bringup FS with control plane",
                              steps="""
                              1. BringUP both F1s
                              2. Bringup FunCP
                              3. Create MPG Interfaces and assign static IPs
                              """)

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):
        # Last working parameter:
        # --environment={\"test_bed_type\":\"fs-alibaba_demo\",\"tftp_image_path\":\"divya_funos-f1.stripped_june5.gz\"}

        global funcp_obj, servers_mode, servers_list, fs_name
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        f1_0_boot_args = "app=mdt_test,load_mods,hw_hsu_test cc_huid=3 --dpc-server --all_100g --serial --dpc-uart " \
                         "retimer=0 --mgmt --disable-wu-watchdog syslog=2"
        f1_1_boot_args = "app=mdt_test,load_mods,hw_hsu_test cc_huid=2 --dpc-server --all_100g --serial --dpc-uart " \
                         "retimer=0 --mgmt --disable-wu-watchdog syslog=2"

        topology_helper = TopologyHelper()
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        fun_test.log("Provided job inputs: {}".format(job_inputs))
        if "deploy_status" in job_inputs:
            deploy_status = job_inputs["deploy_status"]
            fun_test.shared_variables["deploy_status"] = deploy_status
        else:
            deploy_status = True
            fun_test.shared_variables["deploy_status"] = deploy_status
        if "quick_sanity" in job_inputs:
            quick_sanity = job_inputs["quick_sanity"]
            fun_test.shared_variables["quick_sanity"] = quick_sanity
        ib_bw_tests = []
        if "test_type" in job_inputs:
            ib_bw_tests.append(job_inputs["test_type"])
            fun_test.shared_variables["test_type"] = ib_bw_tests
        else:
            ib_bw_tests = ["write", "read"]
            fun_test.shared_variables["test_type"] = ib_bw_tests

        if deploy_status:
            funcp_obj = FunControlPlaneBringup(fs_name=self.server_key["fs"][fs_name]["fs-name"])
            funcp_obj.cleanup_funcp()
            servers_mode = self.server_key["fs"][fs_name]["hosts"]
            servers_list = []

            for server in servers_mode:
                critical_log(expression=rmmod_funeth_host(hostname=server), message="rmmod funeth on host")
                servers_list.append(server)

            topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                              1: {"boot_args": f1_1_boot_args}}
                                               )
            topology = topology_helper.deploy()
            fun_test.shared_variables["topology"] = topology
            fun_test.test_assert(topology, "Topology deployed")
            fs = topology.get_dut_instance(index=0)
            come_obj = fs.get_come()
            come_obj.sudo_command("netplan apply")
            come_obj.sudo_command("dmesg -c > /dev/null")

            fun_test.log("Getting host details")
            host_dict = {"f1_0": [], "f1_1": []}
            for i in range(0, 23):
                if i <= 11:
                    if topology.get_host_instance(dut_index=0, host_index=0, ssd_interface_index=i):
                        if topology.get_host_instance(dut_index=0, host_index=0, ssd_interface_index=i) not in \
                                host_dict["f1_0"]:
                            host_dict["f1_0"].append(
                                topology.get_host_instance(dut_index=0, host_index=0, ssd_interface_index=i))
                elif i > 11 <= 23:
                    if topology.get_host_instance(dut_index=0, host_index=0, ssd_interface_index=i):
                        if topology.get_host_instance(dut_index=0, host_index=0, ssd_interface_index=i) not in \
                                host_dict["f1_1"]:
                            host_dict["f1_1"].append(
                                topology.get_host_instance(dut_index=0, host_index=0, ssd_interface_index=i))
            fun_test.shared_variables["hosts_obj"] = host_dict

            # Check PICe Link on host
            servers_mode = self.server_key["fs"][fs_name]["hosts"]
            for server in servers_mode:
                result = verify_host_pcie_link(hostname=server, mode=servers_mode[server], reboot=False)
                fun_test.test_assert(expression=(result != "0"), message="Make sure that PCIe links on host %s went up"
                                                                         % server)
                if result == "2":
                    fun_test.add_checkpoint("<b><font color='red'><PCIE link did not come up in %s mode</font></b>"
                                            % servers_mode[server])

            # Bringup FunCP
            fun_test.test_assert(expression=funcp_obj.bringup_funcp(prepare_docker=False), message="Bringup FunCP")
            # Assign MPG IPs from dhcp
            funcp_obj.assign_mpg_ips(static=self.server_key["fs"][fs_name]["mpg_ips"]["static"],
                                     f1_1_mpg=self.server_key["fs"][fs_name]["mpg_ips"]["mpg1"],
                                     f1_0_mpg=self.server_key["fs"][fs_name]["mpg_ips"]["mpg0"])
        else:
            fun_test.log("Getting host info")
            host_dict = {"f1_0": [], "f1_1": []}
            temp_host_list = []
            temp_host_list1 = []
            expanded_topology = topology_helper.get_expanded_topology()
            pcie_hosts = expanded_topology.get_pcie_hosts_on_interfaces(dut_index=0)
            for pcie_interface_index, host_info in pcie_hosts.iteritems():
                host_instance = fun_test.get_asset_manager().get_linux_host(host_info["name"])
                # if host_info["name"] not in temp_host_list:
                # temp_host_list.append(host_info["name"])
                if pcie_interface_index <= 11:
                    if host_info["name"] not in temp_host_list:
                        host_dict["f1_0"].append(host_instance)
                        temp_host_list.append(host_info["name"])
                elif pcie_interface_index > 11 <= 23:
                    if host_info["name"] not in temp_host_list1:
                        host_dict["f1_1"].append(host_instance)
                        temp_host_list1.append(host_info["name"])
            fun_test.shared_variables["hosts_obj"] = host_dict

        fun_test.shared_variables["host_len_f10"] = len(host_dict["f1_0"])
        fun_test.shared_variables["host_len_f11"] = len(host_dict["f1_1"])

        fun_test.log("SETUP Done")

    def cleanup(self):
        pass


class NicEmulation(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=2,
                              summary="Bringup PCIe Connected Hosts and test traffic",
                              steps="""
                              1. Reboot connected hosts
                              2. Verify for PICe Link
                              3. Install Funeth Driver
                              4. Configure HU interface
                              5. Configure FunCP according to HU interfaces
                              6. Add routes on FunCP Container
                              7. Ping NU host from HU host
                              8. Do netperf
                              """)

    def setup(self):

        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):
        host_objs = fun_test.shared_variables["hosts_obj"]

        if fun_test.shared_variables["deploy_status"]:
            # execute abstract Configs
            abstract_json_file0 = fun_test.get_script_parent_directory() + '/abstract_config/' + \
                                  self.server_key["fs"][fs_name]["abstract_configs"]["F1-0"]
            abstract_json_file1 = fun_test.get_script_parent_directory() + '/abstract_config/' + \
                                  self.server_key["fs"][fs_name]["abstract_configs"]["F1-1"]

            funcp_obj.funcp_abstract_config(abstract_config_f1_0=abstract_json_file0,
                                            abstract_config_f1_1=abstract_json_file1, workspace="/scratch")

            # Add static routes on Containers
            funcp_obj.add_routes_on_f1(routes_dict=self.server_key["fs"][fs_name]["static_routes"])
            fun_test.sleep(message="Waiting before ping tests", seconds=10)

            # Ping QFX from both F1s
            ping_dict = self.server_key["fs"][fs_name]["cc_pings"]
            for container in ping_dict:
                funcp_obj.test_cc_pings_remote_fs(dest_ips=ping_dict[container], docker_name=container)

            # Ping vlan to vlan
            funcp_obj.test_cc_pings_fs()

            # install drivers on PCIE connected servers
            tb_config_obj = tb_configs.TBConfigs(str(fs_name))
            funeth_obj = Funeth(tb_config_obj)
            fun_test.shared_variables['funeth_obj'] = funeth_obj
            setup_hu_host(funeth_obj, update_driver=True, sriov=4, num_queues=1)

            # get ethtool output
            get_ethtool_on_hu_host(funeth_obj)

            # Ping hosts
            ping_dict = self.server_key["fs"][fs_name]["host_pings"]
            for host in ping_dict:
                test_host_pings(host=host, ips=ping_dict[host])
            fun_test.sleep(message="Wait for host to check ping again", seconds=30)
            # Ping hosts
            ping_dict = self.server_key["fs"][fs_name]["host_pings"]
            for host in ping_dict:
                test_host_pings(host=host, ips=ping_dict[host], strict=False)

        # Update RDMA Core & perftest on hosts
        # for obj in host_objs:
        #     if obj == "f1_0":
        #         host_count = fun_test.shared_variables["host_len_f10"]
        #     elif obj == "f1_1":
        #         host_count = fun_test.shared_variables["host_len_f11"]
        #     for x in xrange(0, host_count):
        #         host_objs[obj][x].start_bg_process("/home/localadmin/mks/update_rdma.sh update update", timeout=1200)
        #         # host_objs[obj][x].command("hostname")
        # fun_test.sleep("Building rdma_perf & core", seconds=120)

        # Create a dict containing F1_0 & F1_1 details
        f10_hosts = []
        f11_hosts = []

        for objs in host_objs:
            for handle in host_objs[objs]:
                handle.sudo_command("rm -rf /tmp/*bw*")
                hostname = handle.command("hostname").strip()
                iface_name = handle.command(
                    "ip link ls up | awk '{print $2}' | grep -e '00:f1:1d' -e '00:de:ad' -B 1 | head -1 | tr -d :"). \
                    strip()
                iface_addr = handle.command(
                    "ip addr list {} | grep \"inet \" | cut -d\' \' -f6 | cut -d/ -f1".format(iface_name)).strip()
                if objs == "f1_0":
                    f10_host_dict = {"name": hostname, "iface_name": iface_name, "ipaddr": iface_addr,
                                     "handle": handle}
                    f10_hosts.append(f10_host_dict)
                elif objs == "f1_1":
                    f11_host_dict = {"name": hostname, "iface_name": iface_name, "ipaddr": iface_addr,
                                     "handle": handle}
                    f11_hosts.append(f11_host_dict)

        # Use first host of F1_0 & F1_1 for RoCE tests
        f10_host_roce = Rocetools(f10_hosts[0]["handle"])
        f11_host_roce = Rocetools(f11_hosts[0]["handle"])

        fun_test.shared_variables["f10_hosts"] = f10_hosts
        fun_test.shared_variables["f11_hosts"] = f11_hosts
        fun_test.shared_variables["f10_host_roce"] = f10_host_roce
        fun_test.shared_variables["f11_host_roce"] = f11_host_roce

    def cleanup(self):
        pass


class SrpingTest(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=3,
                              summary="SRPING Test",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start srping test for different sizes
                                  """)

    def setup(self):

        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):
        global funcp_obj, servers_mode, servers_list, fs_name
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        f10_hosts = fun_test.shared_variables["f10_hosts"]
        f11_hosts = fun_test.shared_variables["f11_hosts"]

        f10_host_roce = fun_test.shared_variables["f10_host_roce"]
        f11_host_roce = fun_test.shared_variables["f11_host_roce"]

        # Load RDMA modules
        f10_host_roce.rdma_setup()
        f11_host_roce.rdma_setup()

        # Kill all RDMA tools
        f10_host_roce.cleanup()
        f11_host_roce.cleanup()

        size = 32
        while (size <= 65536):
            if size == 65536:
                size = 65534
            f10_host_test = f10_host_roce.srping_test(size=size, count=10, debug=True)
            fun_test.sleep("Started srping server for size {}".format(size), seconds=1)
            f11_host_test = f11_host_roce.srping_test(size=size, count=10, debug=True, server_ip=f10_hosts[0]["ipaddr"])
            while f10_hosts[0]["handle"].process_exists(process_id=f10_host_test["cmd_pid"]):
                fun_test.sleep("Srping on f10_host", 2)
            while f11_hosts[0]["handle"].process_exists(process_id=f11_host_test["cmd_pid"]):
                fun_test.sleep("Srping on f11_host", 2)
            f10_host_result = f10_host_roce.parse_test_log(f10_host_test["output_file"], tool="srping")
            f11_host_result = f11_host_roce.parse_test_log(f11_host_test["output_file"], tool="srping", client_cmd=True)
            f10_hosts[0]["handle"].disconnect()
            f11_hosts[0]["handle"].disconnect()
            fun_test.simple_assert(f10_host_result, "F10_host result for size {}".format(size))
            fun_test.simple_assert(f11_host_result, "F11_host result for size {}".format(size))
            size = size * 2

        fun_test.test_assert(True, "Srping test passed")

        fun_test.sleep("sleep", 3)

    def cleanup(self):
        fun_test.shared_variables["f10_host_roce"].cleanup()
        fun_test.shared_variables["f10_host_roce"].cleanup()


class RpingTest(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=4,
                              summary="RPING Test",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start rping test for different sizes
                                  """)

    def setup(self):

        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):
        global funcp_obj, servers_mode, servers_list, fs_name
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        f10_hosts = fun_test.shared_variables["f10_hosts"]
        f11_hosts = fun_test.shared_variables["f11_hosts"]

        f10_host_roce = fun_test.shared_variables["f10_host_roce"]
        f11_host_roce = fun_test.shared_variables["f11_host_roce"]

        # Load RDMA modules
        f10_host_roce.rdma_setup()
        f11_host_roce.rdma_setup()

        # Kill all RDMA tools
        f10_host_roce.cleanup()
        f11_host_roce.cleanup()

        size = 32
        while (size<=65536):
            if size == 65536:
                size = 65534
            f10_host_test = f10_host_roce.rping_test(size=size, count=10, debug=True)
            fun_test.sleep("Started rping server for size {}".format(size), seconds=1)
            f11_host_test = f11_host_roce.rping_test(size=size, count=10, debug=True, server_ip=f10_hosts[0]["ipaddr"])
            while f10_hosts[0]["handle"].process_exists(process_id=f10_host_test["cmd_pid"]):
                fun_test.sleep("Rping on f10_host", 2)
            while f11_hosts[0]["handle"].process_exists(process_id=f11_host_test["cmd_pid"]):
                fun_test.sleep("Rping on f11_host", 2)
            f10_host_result = f10_host_roce.parse_test_log(f10_host_test["output_file"], tool="rping")
            f11_host_result = f11_host_roce.parse_test_log(f11_host_test["output_file"], tool="rping", client_cmd=True)
            f10_hosts[0]["handle"].disconnect()
            f11_hosts[0]["handle"].disconnect()
            fun_test.simple_assert(f10_host_result, "F10_host result for size {}".format(size))
            fun_test.simple_assert(f11_host_result, "F11_host result for size {}".format(size))
            size = size * 2

        fun_test.test_assert(True, "Rping test passed")

        fun_test.sleep("sleep", 3)

    def cleanup(self):
        fun_test.shared_variables["f10_host_roce"].cleanup()
        fun_test.shared_variables["f10_host_roce"].cleanup()


class IbBwTest(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=5,
                              summary="IB_BW* Test",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start IB_BW write/read test for different sizes
                                  """)

    def setup(self):

        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):
        global funcp_obj, servers_mode, servers_list, fs_name
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        f10_hosts = fun_test.shared_variables["f10_hosts"]
        f11_hosts = fun_test.shared_variables["f11_hosts"]

        f10_host_roce = fun_test.shared_variables["f10_host_roce"]
        f11_host_roce = fun_test.shared_variables["f11_host_roce"]
        test_type_list = fun_test.shared_variables["test_type"]

        # Load RDMA modules
        f10_host_roce.rdma_setup()
        f11_host_roce.rdma_setup()

        # Kill all RDMA tools
        f10_host_roce.cleanup()
        f11_host_roce.cleanup()

        for test in test_type_list:
            print test
            packet_size = ["1", "128", "256", "512", "1024", "2048", "4096"]
            for size in packet_size:
                f10_host_test = f10_host_roce.ib_bw_test(test_type=test, size=size)
                f11_host_test = f11_host_roce.ib_bw_test(test_type=test, size=size, server_ip=f10_hosts[0]["ipaddr"])
                while f10_hosts[0]["handle"].process_exists(process_id=f10_host_test["cmd_pid"]):
                    fun_test.sleep("ib_bw test on f10_host", 2)
                while f11_hosts[0]["handle"].process_exists(process_id=f11_host_test["cmd_pid"]):
                    fun_test.sleep("ib_bw test on f11_host", 2)
                f10_host_result = f10_host_roce.parse_test_log(f10_host_test["output_file"], tool="ib_bw")
                f11_host_result = f11_host_roce.parse_test_log(f11_host_test["output_file"], tool="ib_bw", client_cmd=True)
                fun_test.simple_assert(f10_host_result, "F10_host {} result of size {}".format(test, size))
                fun_test.simple_assert(f11_host_result, "F11_host {} result of size {}".format(test, size))

        fun_test.sleep("sleep", 3)

    def cleanup(self):
        fun_test.shared_variables["f10_host_roce"].cleanup()
        fun_test.shared_variables["f10_host_roce"].cleanup()


class IbLatTest(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=6,
                              summary="IB_LAT* Test",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start IB_BW write/read test for different sizes
                                  """)

    def setup(self):

        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):
        global funcp_obj, servers_mode, servers_list, fs_name
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        f10_hosts = fun_test.shared_variables["f10_hosts"]
        f11_hosts = fun_test.shared_variables["f11_hosts"]

        f10_host_roce = fun_test.shared_variables["f10_host_roce"]
        f11_host_roce = fun_test.shared_variables["f11_host_roce"]
        test_type_list = fun_test.shared_variables["test_type"]

        # Load RDMA modules
        f10_host_roce.rdma_setup()
        f11_host_roce.rdma_setup()

        # Kill all RDMA tools
        f10_host_roce.cleanup()
        f11_host_roce.cleanup()

        for test in test_type_list:
            print test
            packet_size = ["1", "128", "256", "512", "1024", "2048", "4096"]
            for size in packet_size:
                f10_host_test = f10_host_roce.ib_lat_test(test_type=test, size=size)
                f11_host_test = f11_host_roce.ib_lat_test(test_type=test, size=size, server_ip=f10_hosts[0]["ipaddr"])
                while f10_hosts[0]["handle"].process_exists(process_id=f10_host_test["cmd_pid"]):
                    fun_test.sleep("ib_bw test on f10_host", 2)
                while f11_hosts[0]["handle"].process_exists(process_id=f11_host_test["cmd_pid"]):
                    fun_test.sleep("ib_bw test on f11_host", 2)
                f10_host_result = f10_host_roce.parse_test_log(f10_host_test["output_file"], tool="ib_lat")
                f11_host_result = f11_host_roce.parse_test_log(f11_host_test["output_file"], tool="ib_lat", client_cmd=True)
                fun_test.simple_assert(f10_host_result, "F10_host {} result of size {}".format(test, size))
                fun_test.simple_assert(f11_host_result, "F11_host {} result of size {}".format(test, size))

        fun_test.sleep("sleep", 3)

    def cleanup(self):
        fun_test.shared_variables["f10_host_roce"].cleanup()
        fun_test.shared_variables["f10_host_roce"].cleanup()

if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(BringupSetup())
    ts.add_test_case(NicEmulation())
    ts.add_test_case(SrpingTest())
    ts.add_test_case(RpingTest())
    ts.add_test_case(IbBwTest())
    ts.add_test_case(IbLatTest())

    ts.run()
