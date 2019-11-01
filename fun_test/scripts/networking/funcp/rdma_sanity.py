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
        f10_hosts = fun_test.shared_variables["f10_hosts"]
        f11_hosts = fun_test.shared_variables["f11_hosts"]
        f10_host_count = fun_test.shared_variables["host_len_f10"]
        f11_host_count = fun_test.shared_variables["host_len_f11"]
        for x in xrange(0, f10_host_count):
            f10_hosts[x]["handle"].disconnect()
        for x in xrange(0, f11_host_count):
            f11_hosts[x]["handle"].disconnect()

        # Check if funeth is loaded or else bail out
        # for obj in host_obj:
        #     host_obj[obj][0].sudo_command("rmmod funrdma")
        # fun_test.log("Unload funrdma drivers")
        # pass
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
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        fun_test.log("Provided job inputs: {}".format(job_inputs))
        if "f10_retimer" in job_inputs:
            f10_retimer = str(job_inputs["f10_retimer"]).strip("[]").replace(" ", "")
        else:
            f10_retimer = 0
        if "f11_retimer" in job_inputs:
            f11_retimer = str(job_inputs["f11_retimer"]).strip("[]").replace(" ", "")
        else:
            f11_retimer = 0

        f1_0_boot_args = "app=mdt_test,load_mods cc_huid=3 --dpc-server --all_100g --serial --dpc-uart " \
                         "retimer={} --mgmt".format(f10_retimer)
        f1_1_boot_args = "app=mdt_test,load_mods cc_huid=2 --dpc-server --all_100g --serial --dpc-uart " \
                         "retimer={} --mgmt".format(f11_retimer)

        topology_helper = TopologyHelper()
        if "deploy_setup" in job_inputs:
            deploy_setup = job_inputs["deploy_setup"]
            fun_test.shared_variables["deploy_setup"] = deploy_setup
        else:
            deploy_setup = True
            fun_test.shared_variables["deploy_setup"] = deploy_setup
        if "quick_sanity" in job_inputs:
            if job_inputs["quick_sanity"]:
                fun_test.shared_variables["test_count"] = 30
            else:
                fun_test.shared_variables["test_count"] = 200
        else:
            fun_test.shared_variables["test_count"] = 200
        ib_bw_tests = []
        if "test_type" in job_inputs:
            ib_bw_tests.append(job_inputs["test_type"])
            fun_test.shared_variables["test_type"] = ib_bw_tests
        else:
            ib_bw_tests = ["write", "read"]
            fun_test.shared_variables["test_type"] = ib_bw_tests
        if "enable_fcp" in job_inputs:
            enable_fcp = job_inputs["enable_fcp"]
            fun_test.shared_variables["enable_fcp"] = enable_fcp
        else:
            enable_fcp = False
            fun_test.shared_variables["enable_fcp"] = enable_fcp
        if "qp_list" in job_inputs:
            fun_test.shared_variables["qp_list"] = job_inputs["qp_list"]
        else:
            fun_test.shared_variables["qp_list"] = [512]
        if "fundrv_branch" in job_inputs:
            fun_test.shared_variables["fundrv_branch"] = job_inputs["fundrv_branch"]
        else:
            fun_test.shared_variables["fundrv_branch"] = None
        if "fundrv_commit" in job_inputs:
            fun_test.shared_variables["fundrv_commit"] = job_inputs["fundrv_commit"]
        else:
            fun_test.shared_variables["fundrv_commit"] = None
        if "rdmacore_branch" in job_inputs:
            fun_test.shared_variables["rdmacore_branch"] = job_inputs["rdmacore_branch"]
        else:
            fun_test.shared_variables["rdmacore_branch"] = None
        if "rdmacore_commit" in job_inputs:
            fun_test.shared_variables["rdmacore_commit"] = job_inputs["rdmacore_commit"]
        else:
            fun_test.shared_variables["rdmacore_commit"] = None
        if "perftest_branch" in job_inputs:
            fun_test.shared_variables["perftest_branch"] = job_inputs["perftest_branch"]
        else:
            fun_test.shared_variables["perftest_branch"] = None
        if "perftest_commit" in job_inputs:
            fun_test.shared_variables["perftest_commit"] = job_inputs["perftest_commit"]
        else:
            fun_test.shared_variables["perftest_commit"] = None

        if deploy_setup:
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
        enable_fcp = fun_test.shared_variables["enable_fcp"]
        abstract_key = ""
        if enable_fcp:
            abstract_key = "abstract_configs_bgp"
        else:
            abstract_key = "abstract_configs"

        if fun_test.shared_variables["deploy_setup"]:
            fun_test.log("Using abstract_key {}".format(abstract_key))
            # execute abstract Configs
            abstract_json_file0 = fun_test.get_script_parent_directory() + '/abstract_config/' + \
                                  self.server_key["fs"][fs_name][abstract_key]["F1-0"]
            abstract_json_file1 = fun_test.get_script_parent_directory() + '/abstract_config/' + \
                                  self.server_key["fs"][fs_name][abstract_key]["F1-1"]

            funcp_obj.funcp_abstract_config(abstract_config_f1_0=abstract_json_file0,
                                            abstract_config_f1_1=abstract_json_file1, workspace="/scratch")

            # Add static routes on Containers
            if not enable_fcp:
                funcp_obj.add_routes_on_f1(routes_dict=self.server_key["fs"][fs_name]["static_routes"])
                fun_test.sleep(message="Waiting before ping tests", seconds=10)

            # Ping QFX from both F1s
            ping_dict = self.server_key["fs"][fs_name]["cc_pings"]
            if enable_fcp:
                ping_dict = self.server_key["fs"][fs_name]["cc_pings_bgp"]

            for container in ping_dict:
                funcp_obj.test_cc_pings_remote_fs(dest_ips=ping_dict[container], docker_name=container)

            # Ping vlan to vlan
            funcp_obj.test_cc_pings_fs()

            # install drivers on PCIE connected servers
            tb_config_obj = tb_configs.TBConfigs(str(fs_name))
            funeth_obj = Funeth(tb_config_obj, fundrv_branch=fun_test.shared_variables["fundrv_branch"],
                                fundrv_commit=fun_test.shared_variables["fundrv_commit"])
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

        # # Update RDMA Core & perftest on hosts
        # bg_proc_id = {}
        # for obj in host_objs:
        #     if obj == "f1_0":
        #         host_count = fun_test.shared_variables["host_len_f10"]
        #         bg_proc_id[obj] = []
        #     elif obj == "f1_1":
        #         host_count = fun_test.shared_variables["host_len_f11"]
        #         bg_proc_id[obj] = []
        #     for x in xrange(0, host_count):
        #         update_path = host_objs[obj][x].command("echo $HOME")
        #         update_script = update_path.strip() + "/mks/update_rdma.sh"
        #         print update_script
        #         bg_proc_id[obj].append(host_objs[obj][x].
        #                                start_bg_process("{} build build".format(update_script),
        #                                                 timeout=1200))
        # # fun_test.sleep("Building rdma_perf & core", seconds=120)
        # for obj in host_objs:
        #     if obj == "f1_0":
        #         host_count = fun_test.shared_variables["host_len_f10"]
        #     elif obj == "f1_1":
        #         host_count = fun_test.shared_variables["host_len_f11"]
        #     for x in xrange(0, host_count):
        #         for pid in bg_proc_id[obj]:
        #             while host_objs[obj][x].process_exists(process_id=pid):
        #                 fun_test.sleep(message="Still building RDMA repo...", seconds=5)
        #         host_objs[obj][x].disconnect()

        # Create a dict containing F1_0 & F1_1 details
        f10_hosts = []
        f11_hosts = []

        for objs in host_objs:
            for handle in host_objs[objs]:
                handle.sudo_command("rm -rf /tmp/*bw* && rm -rf /tmp/*rping* /tmp/*lat*")
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

        f10_host_roce.build_rdma_repo(rdmacore_branch=fun_test.shared_variables["rdmacore_branch"],
                                      rdmacore_commit=fun_test.shared_variables["rdmacore_commit"],
                                      perftest_branch=fun_test.shared_variables["perftest_branch"],
                                      perftest_commit=fun_test.shared_variables["perftest_commit"])
        f11_host_roce.build_rdma_repo(rdmacore_branch=fun_test.shared_variables["rdmacore_branch"],
                                      rdmacore_commit=fun_test.shared_variables["rdmacore_commit"],
                                      perftest_branch=fun_test.shared_variables["perftest_branch"],
                                      perftest_commit=fun_test.shared_variables["perftest_commit"])

    def cleanup(self):
        pass


class SrpingLoopBack(FunTestCase):
    server_key = {}
    random_io = False

    def describe(self):
        self.set_test_details(id=3,
                              summary="SRPING Loopback Test",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start srping test in loop back
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
        test_count = fun_test.shared_variables["test_count"]

        # Load RDMA modules
        f10_host_roce.rdma_setup()
        f11_host_roce.rdma_setup()

        # Kill all RDMA tools
        f10_host_roce.cleanup()
        f11_host_roce.cleanup()

        if self.random_io:
            io_list = []
            while True:
                rand_num = random.randint(23, 65534)
                if rand_num not in io_list:
                    io_list.append(rand_num)
                if len(io_list) == 16:
                    break
        else:
            io_list = []
            size = 32
            while size <= 65536:
                if size == 65536:
                    io_list.append(65534)
                else:
                    io_list.append(size)
                size = size * 2

        for size in io_list:
            f10_host_server = f10_host_roce.srping_test(size=size, count=test_count, debug=True, timeout=120)
            fun_test.sleep("Started srping server for size {}".format(size), seconds=1)
            f10_host_client = f10_host_roce.srping_test(size=size, count=test_count, debug=True,
                                                        server_ip=f10_hosts[0]["ipaddr"], timeout=120)
            while f10_hosts[0]["handle"].process_exists(process_id=f10_host_server["cmd_pid"]):
                fun_test.sleep("Srping server on f10_host", 2)
            while f10_hosts[0]["handle"].process_exists(process_id=f10_host_client["cmd_pid"]):
                fun_test.sleep("Srping client on f10_host", 2)
            f10_server_result = f10_host_roce.parse_test_log(f10_host_server["output_file"], tool="srping")
            f10_client_result = f10_host_roce.parse_test_log(f10_host_client["output_file"], tool="srping",
                                                             client_cmd=True)

            fun_test.simple_assert(f10_server_result, "F10_host server result for size {}".format(size))
            fun_test.simple_assert(f10_client_result, "F10_host client result for size {}".format(size))

        for size in io_list:
            f11_host_server = f11_host_roce.srping_test(size=size, count=test_count, debug=True, timeout=120)
            fun_test.sleep("Started srping server for size {}".format(size), seconds=1)
            f11_host_client = f11_host_roce.srping_test(size=size, count=test_count, debug=True,
                                                        server_ip=f11_hosts[0]["ipaddr"], timeout=120)
            while f11_hosts[0]["handle"].process_exists(process_id=f11_host_server["cmd_pid"]):
                fun_test.sleep("Srping server on f11_host", 2)
            while f11_hosts[0]["handle"].process_exists(process_id=f11_host_client["cmd_pid"]):
                fun_test.sleep("Srping client on f11_host", 2)
            f11_server_result = f11_host_roce.parse_test_log(f11_host_server["output_file"], tool="srping")
            f11_client_result = f11_host_roce.parse_test_log(f11_host_client["output_file"], tool="srping",
                                                             client_cmd=True)
            fun_test.simple_assert(f11_server_result, "f11_host server result for size {}".format(size))
            fun_test.simple_assert(f11_client_result, "f11_host client result for size {}".format(size))

        fun_test.test_assert(True, "Srping loop back test")

    def cleanup(self):
        fun_test.shared_variables["f10_host_roce"].cleanup()
        fun_test.shared_variables["f10_host_roce"].cleanup()


class RpingLoopBack(FunTestCase):
    server_key = {}
    random_io = False

    def describe(self):
        self.set_test_details(id=4,
                              summary="RPING Loopback Test",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start rping test in loop back
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
        test_count = fun_test.shared_variables["test_count"]

        # Load RDMA modules
        f10_host_roce.rdma_setup()
        f11_host_roce.rdma_setup()

        # Kill all RDMA tools
        f10_host_roce.cleanup()
        f11_host_roce.cleanup()

        if self.random_io:
            io_list = []
            while True:
                rand_num = random.randint(23, 65534)
                if rand_num not in io_list:
                    io_list.append(rand_num)
                if len(io_list) == 16:
                    break
        else:
            io_list = []
            size = 32
            while size <= 65536:
                if size == 65536:
                    io_list.append(65534)
                else:
                    io_list.append(size)
                size = size * 2

        for size in io_list:
            f10_host_server = f10_host_roce.rping_test(size=size, count=test_count, debug=True, timeout=120)
            fun_test.sleep("Started Rping server for size {}".format(size), seconds=1)
            f10_host_client = f10_host_roce.rping_test(size=size, count=test_count, debug=True,
                                                       server_ip=f10_hosts[0]["ipaddr"], timeout=120)
            while f10_hosts[0]["handle"].process_exists(process_id=f10_host_server["cmd_pid"]):
                fun_test.sleep("Rping server on f10_host", 2)
            while f10_hosts[0]["handle"].process_exists(process_id=f10_host_client["cmd_pid"]):
                fun_test.sleep("Rping client on f10_host", 2)
            f10_server_result = f10_host_roce.parse_test_log(f10_host_server["output_file"], tool="rping")
            f10_client_result = f10_host_roce.parse_test_log(f10_host_client["output_file"], tool="rping",
                                                             client_cmd=True)
            fun_test.simple_assert(f10_server_result, "F10_host server result for size {}".format(size))
            fun_test.simple_assert(f10_client_result, "F10_host client result for size {}".format(size))

        for size in io_list:
            f11_host_server = f11_host_roce.rping_test(size=size, count=test_count, debug=True, timeout=120)
            fun_test.sleep("Started rping server for size {}".format(size), seconds=1)
            f11_host_client = f11_host_roce.rping_test(size=size, count=test_count, debug=True,
                                                       server_ip=f11_hosts[0]["ipaddr"], timeout=120)
            while f11_hosts[0]["handle"].process_exists(process_id=f11_host_server["cmd_pid"]):
                fun_test.sleep("Rping server on f11_host", 2)
            while f11_hosts[0]["handle"].process_exists(process_id=f11_host_client["cmd_pid"]):
                fun_test.sleep("Rping client on f11_host", 2)
            f11_server_result = f11_host_roce.parse_test_log(f11_host_server["output_file"], tool="rping")
            f11_client_result = f11_host_roce.parse_test_log(f11_host_client["output_file"], tool="rping",
                                                             client_cmd=True)
            fun_test.simple_assert(f11_server_result, "f11_host server result for size {}".format(size))
            fun_test.simple_assert(f11_client_result, "f11_host client result for size {}".format(size))

        fun_test.test_assert(True, "Rping loop back test")

    def cleanup(self):
        fun_test.shared_variables["f10_host_roce"].cleanup()
        fun_test.shared_variables["f10_host_roce"].cleanup()


class SrpingSeqIoTest(FunTestCase):
    server_key = {}
    random_io = False

    def describe(self):
        self.set_test_details(id=5,
                              summary="SRPING Seq IO Test",
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
        test_count = fun_test.shared_variables["test_count"]

        # Load RDMA modules
        f10_host_roce.rdma_setup()
        f11_host_roce.rdma_setup()

        # Kill all RDMA tools
        f10_host_roce.cleanup()
        f11_host_roce.cleanup()

        if self.random_io:
            test = "Random"
            io_list = []
            while True:
                rand_num = random.randint(23, 65534)
                if rand_num not in io_list:
                    io_list.append(rand_num)
                if len(io_list) == 16:
                    break
        else:
            test = "Sequential"
            io_list = []
            size = 32
            while size <= 65536:
                if size == 65536:
                    io_list.append(65534)
                else:
                    io_list.append(size)
                size = size * 2
        f10_pid_there = 0
        f11_pid_there = 0
        for size in io_list:
            f10_host_test = f10_host_roce.srping_test(size=size, count=test_count, debug=True)
            fun_test.sleep("Started srping server for size {}".format(size), seconds=1)
            f11_host_test = f11_host_roce.srping_test(size=size, count=test_count, debug=True,
                                                      server_ip=f10_hosts[0]["ipaddr"])
            while f10_hosts[0]["handle"].process_exists(process_id=f10_host_test["cmd_pid"]):
                fun_test.sleep("Srping test on f10_host", 2)
                f10_pid_there += 1  # Counter to check before initiating kill
                if f10_pid_there == 60:
                    f10_hosts[0]["handle"].kill_process(process_id=f10_host_test["cmd_pid"])
            while f11_hosts[0]["handle"].process_exists(process_id=f11_host_test["cmd_pid"]):
                fun_test.sleep("Srping test on f11_host", 2)
                f11_pid_there += 1
                if f11_pid_there == 60:
                    f11_hosts[0]["handle"].kill_process(process_id=f11_host_test["cmd_pid"])
            f10_host_result = f10_host_roce.parse_test_log(f10_host_test["output_file"], tool="srping")
            f11_host_result = f11_host_roce.parse_test_log(f11_host_test["output_file"], tool="srping",
                                                           client_cmd=True)
            fun_test.simple_assert(f10_host_result, "F10_host result for size {}".format(size))
            fun_test.simple_assert(f11_host_result, "F11_host result for size {}".format(size))

        fun_test.test_assert(True, "Srping {} IO test".format(test))

    def cleanup(self):
        fun_test.shared_variables["f10_host_roce"].cleanup()
        fun_test.shared_variables["f10_host_roce"].cleanup()


class SrpingRandIoTest(SrpingSeqIoTest):
    random_io = True

    def describe(self):
        self.set_test_details(id=6,
                              summary="SRPING Random IO Test",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start srping test for different sizes
                                  """)


class RpingSeqIoTest(FunTestCase):
    server_key = {}
    random_io = False

    def describe(self):
        self.set_test_details(id=7,
                              summary="RPING Seq IO Test",
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
        test_count = fun_test.shared_variables["test_count"]

        # Load RDMA modules
        f10_host_roce.rdma_setup()
        f11_host_roce.rdma_setup()

        # Kill all RDMA tools
        f10_host_roce.cleanup()
        f11_host_roce.cleanup()

        if self.random_io:
            test = "Random"
            io_list = []
            while True:
                rand_num = random.randint(23, 65534)
                if rand_num not in io_list:
                    io_list.append(rand_num)
                if len(io_list) == 16:
                    break
        else:
            test = "Sequential"
            io_list = []
            size = 32
            while size <= 65536:
                if size == 65536:
                    io_list.append(65534)
                else:
                    io_list.append(size)
                size = size * 2
        f10_pid_there = 0
        f11_pid_there = 0
        for size in io_list:
            f10_host_test = f10_host_roce.rping_test(size=size, count=test_count, debug=True)
            fun_test.sleep("Started rping server for size {}".format(size), seconds=1)
            f11_host_test = f11_host_roce.rping_test(size=size, count=test_count, debug=True,
                                                     server_ip=f10_hosts[0]["ipaddr"])
            while f10_hosts[0]["handle"].process_exists(process_id=f10_host_test["cmd_pid"]):
                fun_test.sleep("Rping test on f10_host", 2)
                f10_pid_there += 1
                if f10_pid_there == 60:
                    f10_hosts[0]["handle"].kill_process(process_id=f10_host_test["cmd_pid"])
            while f11_hosts[0]["handle"].process_exists(process_id=f11_host_test["cmd_pid"]):
                fun_test.sleep("Rping test on f11_host", 2)
                f11_pid_there += 1
                if f11_pid_there == 60:
                    f11_hosts[0]["handle"].kill_process(process_id=f11_host_test["cmd_pid"])
            f10_host_result = f10_host_roce.parse_test_log(f10_host_test["output_file"], tool="rping")
            f11_host_result = f11_host_roce.parse_test_log(f11_host_test["output_file"], tool="rping", client_cmd=True)
            fun_test.simple_assert(f10_host_result, "F10_host result for size {}".format(size))
            fun_test.simple_assert(f11_host_result, "F11_host result for size {}".format(size))

        fun_test.test_assert(True, "Rping {} IO test".format(test))

    def cleanup(self):
        fun_test.shared_variables["f10_host_roce"].cleanup()
        fun_test.shared_variables["f10_host_roce"].cleanup()


class RpingRandIoTest(RpingSeqIoTest):
    server_key = {}
    random_io = True

    def describe(self):
        self.set_test_details(id=8,
                              summary="RPING Random IO Test",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start rping test for different sizes
                                  """)


class IbBwSeqIoTest(FunTestCase):
    server_key = {}
    random_io = False
    use_rdmacm = False

    def describe(self):
        self.set_test_details(id=9,
                              summary="IB_BW* Seq IO Test",
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

        if self.use_rdmacm:
            rdmacm = True
        else:
            rdmacm = False

        if self.random_io:
            io_type = "Random"
            io_list = []
            while True:
                rand_num = random.randint(1, 524288)
                if rand_num not in io_list:
                    io_list.append(rand_num)
                if len(io_list) == 16:
                    break
        else:
            io_type = "Sequential"
            io_list = ["1", "128", "256", "512", "1024", "2048", "4096"]
        f10_pid_there = 0
        f11_pid_there = 0
        for test in test_type_list:
            for size in io_list:
                f10_host_test = f10_host_roce.ib_bw_test(test_type=test, size=size, rdma_cm=rdmacm)
                f11_host_test = f11_host_roce.ib_bw_test(test_type=test, size=size, rdma_cm=rdmacm,
                                                         server_ip=f10_hosts[0]["ipaddr"])
                while f10_hosts[0]["handle"].process_exists(process_id=f10_host_test["cmd_pid"]):
                    fun_test.sleep("ib_bw test on f10_host", 2)
                    f10_pid_there += 1
                    if f10_pid_there == 60:
                        f10_hosts[0]["handle"].kill_process(process_id=f10_host_test["cmd_pid"])
                while f11_hosts[0]["handle"].process_exists(process_id=f11_host_test["cmd_pid"]):
                    fun_test.sleep("ib_bw test on f11_host", 2)
                    f11_pid_there += 1
                    if f11_pid_there == 60:
                        f11_hosts[0]["handle"].kill_process(process_id=f11_host_test["cmd_pid"])
                f10_host_result = f10_host_roce.parse_test_log(f10_host_test["output_file"], tool="ib_bw")
                f11_host_result = f11_host_roce.parse_test_log(f11_host_test["output_file"], tool="ib_bw",
                                                               client_cmd=True)
                fun_test.simple_assert(f10_host_result, "F10_host {} result of size {}".format(test, size))
                fun_test.simple_assert(f11_host_result, "F11_host {} result of size {}".format(test, size))

            fun_test.test_assert(True, "IB_BW {} test with {} IO".format(test, io_type))

    def cleanup(self):
        fun_test.shared_variables["f10_host_roce"].cleanup()
        fun_test.shared_variables["f10_host_roce"].cleanup()


class IbBwRandIoTest(IbBwSeqIoTest):
    server_key = {}
    random_io = True

    def describe(self):
        self.set_test_details(id=10,
                              summary="IB_BW* Random IO Test",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start ib_bw test for different sizes
                                  """)


class IbBwSeqIoRdmaCm(IbBwSeqIoTest):
    server_key = {}
    random_io = False
    use_rdmacm = True

    def describe(self):
        self.set_test_details(id=11,
                              summary="IB_BW* Seq IO & RDMA_CM",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start ib_bw test for different sizes
                                  """)


class IbBwRandIoRdmaCm(IbBwSeqIoTest):
    server_key = {}
    random_io = True
    use_rdmacm = True

    def describe(self):
        self.set_test_details(id=12,
                              summary="IB_BW* Random IO & RDMA_CM",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start ib_bw test for different sizes
                                  """)


class IbLatSeqIoTest(FunTestCase):
    server_key = {}
    random_io = False
    use_rdmacm = False

    def describe(self):
        self.set_test_details(id=13,
                              summary="IB_LAT* Seq IO Test",
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

        if self.use_rdmacm:
            rdmacm = True
        else:
            rdmacm = False

        if self.random_io:
            io_type = "Random"
            io_list = []
            while True:
                rand_num = random.randint(1, 524288)
                if rand_num not in io_list:
                    io_list.append(rand_num)
                if len(io_list) == 16:
                    break
        else:
            io_type = "Sequential"
            io_list = ["1", "128", "256", "512", "1024", "2048", "4096"]

        f10_pid_there = 0
        f11_pid_there = 0
        for test in test_type_list:
            for size in io_list:
                f10_host_test = f10_host_roce.ib_lat_test(test_type=test, size=size, rdma_cm=rdmacm)
                f11_host_test = f11_host_roce.ib_lat_test(test_type=test, size=size, rdma_cm=rdmacm,
                                                          server_ip=f10_hosts[0]["ipaddr"])
                while f10_hosts[0]["handle"].process_exists(process_id=f10_host_test["cmd_pid"]):
                    fun_test.sleep("ib_lat test on f10_host", 2)
                    f10_pid_there += 1
                    if f10_pid_there == 60:
                        f10_hosts[0]["handle"].kill_process(process_id=f10_host_test["cmd_pid"])
                while f11_hosts[0]["handle"].process_exists(process_id=f11_host_test["cmd_pid"]):
                    fun_test.sleep("ib_lat test on f11_host", 2)
                    f11_pid_there += 1
                    if f11_pid_there == 60:
                        f11_hosts[0]["handle"].kill_process(process_id=f11_host_test["cmd_pid"])
                f10_host_result = f10_host_roce.parse_test_log(f10_host_test["output_file"], tool="ib_lat")
                f11_host_result = f11_host_roce.parse_test_log(f11_host_test["output_file"], tool="ib_lat",
                                                               client_cmd=True)
                fun_test.simple_assert(f10_host_result, "F10_host {} result of size {}".format(test, size))
                fun_test.simple_assert(f11_host_result, "F11_host {} result of size {}".format(test, size))

            fun_test.test_assert(True, "IB_LAT {} test for {} IO".format(test, io_type))

    def cleanup(self):
        fun_test.shared_variables["f10_host_roce"].cleanup()
        fun_test.shared_variables["f10_host_roce"].cleanup()


class IbLatRandIoTest(IbLatSeqIoTest):
    server_key = {}
    random_io = True

    def describe(self):
        self.set_test_details(id=14,
                              summary="IB_Lat* Random IO Test",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start ib_bw test for random sizes
                                  """)


class IbLatSeqIoRdmaCm(IbLatSeqIoTest):
    server_key = {}
    random_io = False
    use_rdmacm = True

    def describe(self):
        self.set_test_details(id=15,
                              summary="IB_Lat* Seq IO & RDMA_CM Test",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start ib_bw test for random sizes
                                  """)


class IbLatRandIoRdmaCm(IbLatSeqIoTest):
    server_key = {}
    random_io = True
    use_rdmacm = True

    def describe(self):
        self.set_test_details(id=16,
                              summary="IB_Lat* Rand IO & RDMA_CM Test",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start ib_bw test for random sizes
                                  """)


class IbWriteScale(FunTestCase):
    server_key = {}
    random_io = False
    use_rdmacm = False

    def describe(self):
        self.set_test_details(id=17,
                              summary="IB_BW* QP scale test",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start IB_BW write/read test for different QP's with size=1
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

        if self.use_rdmacm:
            rdmacm = True
        else:
            rdmacm = False

        if self.random_io:
            io_type = "Random"
            io_list = []
            while True:
                rand_num = random.randint(1, 524288)
                if rand_num not in io_list:
                    io_list.append(rand_num)
                if len(io_list) == 16:
                    break
        else:
            io_type = "Sequential"

        qp_list = fun_test.shared_variables["qp_list"]

        # Get max_cqe to compute tx_depth required for scaling
        f10_device_info = f10_host_roce.ibv_devinfo()
        f11_device_info = f11_host_roce.ibv_devinfo()
        for devinfo in f10_device_info:
            if "max_cqe" in devinfo:
                f10_max_cqe = int(devinfo.split(":")[1])
        for devinfo in f11_device_info:
            if "max_cqe" in devinfo:
                f11_max_cqe = int(devinfo.split(":")[1])
        if f10_max_cqe != f11_max_cqe:
            max_cqe_in_test = min(f10_max_cqe, f11_max_cqe)
            fun_test.critical("Max CQE on F10 : {} & F11 : {}".format(f10_max_cqe, f11_max_cqe))
            fun_test.add_checkpoint("Max CQE mismatch", "FAILED", f10_max_cqe, f11_max_cqe)
        else:
            max_cqe_in_test = f10_max_cqe
        print "The max_cqe is {}".format(max_cqe_in_test)
        size = 1
        for test in test_type_list:
            for qp in qp_list:
                f10_pid_there = 0
                f11_pid_there = 0
                # Compute the tx_depth required for scaling.
                # Default tx_depth = 128 from ib_write_bw
                tx_depth_default = 128
                cq_depth_required = 128 * qp

                # Reduce the tx_depth for scaling and avoid CQ allocation failure
                if cq_depth_required > max_cqe_in_test:
                    tx_depth_in_test = max_cqe_in_test / qp
                else:
                    tx_depth_in_test = tx_depth_default
                fun_test.log("Running test with tx_depth {}".format(tx_depth_in_test))

                f10_host_test = f10_host_roce.ib_bw_test(test_type=test, size=size, rdma_cm=rdmacm, qpair=qp,
                                                         tx_depth=tx_depth_in_test, duration=30)
                f11_host_test = f11_host_roce.ib_bw_test(test_type=test, size=size, rdma_cm=rdmacm, qpair=qp,
                                                         tx_depth=tx_depth_in_test, server_ip=f10_hosts[0]["ipaddr"],
                                                         duration=30)
                while f10_hosts[0]["handle"].process_exists(process_id=f10_host_test["cmd_pid"]):
                    fun_test.sleep("ib_bw test on f10_host", 2)
                    f10_pid_there += 1
                    if f10_pid_there == 60:
                        f10_hosts[0]["handle"].kill_process(process_id=f10_host_test["cmd_pid"])
                while f11_hosts[0]["handle"].process_exists(process_id=f11_host_test["cmd_pid"]):
                    fun_test.sleep("ib_bw test on f11_host", 2)
                    f11_pid_there += 1
                    if f11_pid_there == 60:
                        f11_hosts[0]["handle"].kill_process(process_id=f11_host_test["cmd_pid"])
                f10_host_result = f10_host_roce.parse_test_log(f10_host_test["output_file"], tool="ib_bw")
                f11_host_result = f11_host_roce.parse_test_log(f11_host_test["output_file"], tool="ib_bw",
                                                               client_cmd=True)
                fun_test.simple_assert(f10_host_result, "F10_host {} result of size {}".format(test, size))
                fun_test.simple_assert(f11_host_result, "F11_host {} result of size {}".format(test, size))

            fun_test.test_assert(True, "IB_BW {} test with {} IO".format(test, io_type))

    def cleanup(self):
        fun_test.shared_variables["f10_host_roce"].cleanup()
        fun_test.shared_variables["f10_host_roce"].cleanup()


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(BringupSetup())
    ts.add_test_case(NicEmulation())
    ts.add_test_case(SrpingLoopBack())
    ts.add_test_case(RpingLoopBack())
    ts.add_test_case(SrpingSeqIoTest())
    ts.add_test_case(SrpingRandIoTest())
    ts.add_test_case(RpingSeqIoTest())
    ts.add_test_case(RpingRandIoTest())
    ts.add_test_case(IbBwSeqIoTest())
    ts.add_test_case(IbBwRandIoTest())
    ts.add_test_case(IbBwSeqIoRdmaCm())
    ts.add_test_case(IbBwRandIoRdmaCm())
    ts.add_test_case(IbLatSeqIoTest())
    ts.add_test_case(IbLatRandIoTest())
    ts.add_test_case(IbLatSeqIoRdmaCm())
    ts.add_test_case(IbLatRandIoRdmaCm())
    ts.add_test_case(IbWriteScale())
    ts.run()
