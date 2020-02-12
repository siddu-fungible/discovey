from lib.system.fun_test import *
from lib.utilities.funcp_config import *
from scripts.networking.funcp.helper import *
from scripts.networking.funeth.sanity import Funeth
from lib.topology.topology_helper import TopologyHelper
from lib.templates.networking.rdma_tools import Rocetools
from asset.asset_manager import *


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
            enable_fcp = True
            fun_test.shared_variables["enable_fcp"] = enable_fcp
        if "qp_list" in job_inputs:
            fun_test.shared_variables["qp_list"] = job_inputs["qp_list"]
        else:
            fun_test.shared_variables["qp_list"] = [512]
        if "funos_branch" in job_inputs:
            fun_test.shared_variables["funos_branch"] = job_inputs["funos_branch"]
        else:
            fun_test.shared_variables["funos_branch"] = None
        if "funsdk_branch" in job_inputs:
            fun_test.shared_variables["funsdk_branch"] = job_inputs["funsdk_branch"]
        else:
            fun_test.shared_variables["funsdk_branch"] = None
        if "funsdk_commit" in job_inputs:
            fun_test.shared_variables["funsdk_commit"] = job_inputs["funsdk_commit"]
        else:
            fun_test.shared_variables["funsdk_commit"] = None
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
        if "ping_debug" in job_inputs:
            if job_inputs["ping_debug"] == 0:
                fun_test.shared_variables["ping_debug"] = False
            else:
                fun_test.shared_variables["ping_debug"] = True
        else:
            fun_test.shared_variables["ping_debug"] = True
        if "update_funcp" in job_inputs:
            update_funcp = job_inputs["update_funcp"]
        else:
            update_funcp = False
        if "disable_large_io" in job_inputs:
            fun_test.shared_variables["disable_large_io"] = job_inputs["disable_large_io"]
        else:
            fun_test.shared_variables["disable_large_io"] = 0

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
            f10_instance = fs.get_f1(index=0)
            f11_instance = fs.get_f1(index=1)
            fun_test.shared_variables["f10_storage_controller"] = f10_instance.get_dpc_storage_controller()
            fun_test.shared_variables["f11_storage_controller"] = f11_instance.get_dpc_storage_controller()
            come_obj = fs.get_come()
            come_obj.sudo_command("netplan apply")
            come_obj.sudo_command("dmesg -c > /dev/null")
            if "fs-45" in fs_name:
                come_obj.command("/home/fun/mks/restart_docker_service.sh")

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
                linux_obj = Linux(host_ip=server, ssh_username="localadmin", ssh_password="Precious1*")
                linux_obj.sudo_command("netplan apply")

                if result == "2":
                    fun_test.add_checkpoint("<b><font color='red'><PCIE link did not come up in %s mode</font></b>"
                                            % servers_mode[server])
            # Bringup FunCP
            fun_test.test_assert(expression=funcp_obj.bringup_funcp(prepare_docker=update_funcp),
                                 message="Bringup FunCP")
            # Assign MPG IPs from dhcp
            funcp_obj.assign_mpg_ips(static=self.server_key["fs"][fs_name]["mpg_ips"]["static"],
                                     f1_1_mpg=self.server_key["fs"][fs_name]["mpg_ips"]["mpg1"],
                                     f1_0_mpg=self.server_key["fs"][fs_name]["mpg_ips"]["mpg0"])
        else:
            # Get COMe object
            am = AssetManager()
            th = TopologyHelper(spec=am.get_test_bed_spec(name=fs_name))
            topology = th.get_expanded_topology()
            dut = topology.get_dut(index=0)
            dut_name = dut.get_name()
            fs_spec = fun_test.get_asset_manager().get_fs_spec(name=dut_name)
            fs_obj = Fs.get(fs_spec=fs_spec, already_deployed=True)
            come_obj = fs_obj.get_come()
            f10_instance = fs_obj.get_f1(index=0)
            f11_instance = fs_obj.get_f1(index=1)
            fun_test.shared_variables["f10_storage_controller"] = f10_instance.get_dpc_storage_controller()
            fun_test.shared_variables["f11_storage_controller"] = f11_instance.get_dpc_storage_controller()
            fun_test.shared_variables["come_obj"] = come_obj

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
                                fundrv_commit=fun_test.shared_variables["fundrv_commit"],
                                funsdk_branch=fun_test.shared_variables["funsdk_branch"],
                                funsdk_commit=fun_test.shared_variables["funsdk_commit"],
                                funos_branch=fun_test.shared_variables["funos_branch"])
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

            # Clear dmesg on hosts before starting test
            for objs in host_objs:
                for handle in host_objs[objs]:
                    handle.sudo_command("dmesg -c > /dev/null")

        # Create a dict containing F1_0 & F1_1 details
        f10_hosts = []
        f11_hosts = []

        for objs in host_objs:
            for handle in host_objs[objs]:
                handle.sudo_command("rm -rf /tmp/*bw* && rm -rf /tmp/*rping* /tmp/*lat*")
                hostname = handle.command("hostname").strip()
                if handle.lsmod("funeth"):
                    iface_name = handle.command(
                        "ip link ls up | awk '{print $2}' | grep -e '00:f1:1d' -e '00:de:ad' -B 1 | head -1 | tr -d :"). \
                        strip()
                    iface_addr = handle.command(
                        "ip addr list {} | grep \"inet \" | cut -d\' \' -f6 | cut -d/ -f1".format(
                            iface_name)).strip()
                else:
                    fun_test.test_assert(False, "Funeth is not loaded on {}".format(hostname))
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

        build_rdma_threadid = {}
        thread_count = 0
        for x in range(0, 1):
            fun_test.log("Sarting build_rdma_repo on F1_0 for host: {}".format(f10_hosts[x]["name"]))
            build_rdma_threadid[thread_count] = fun_test.execute_thread_after(
                func=f10_host_roce.build_rdma_repo,
                time_in_seconds=5,
                rdmacore_branch=fun_test.shared_variables["rdmacore_branch"],
                rdmacore_commit=fun_test.shared_variables["rdmacore_commit"],
                perftest_branch=fun_test.shared_variables["perftest_branch"],
                perftest_commit=fun_test.shared_variables["perftest_commit"],
                threaded=True)
            thread_count += 1
        for x in range(0, 1):
            fun_test.log("Sarting build_rdma_repo on F1_1 for host: {}".format(f11_hosts[x]["name"]))
            build_rdma_threadid[thread_count] = fun_test.execute_thread_after(
                func=f11_host_roce.build_rdma_repo,
                time_in_seconds=5,
                rdmacore_branch=fun_test.shared_variables["rdmacore_branch"],
                rdmacore_commit=fun_test.shared_variables["rdmacore_commit"],
                perftest_branch=fun_test.shared_variables["perftest_branch"],
                perftest_commit=fun_test.shared_variables["perftest_commit"],
                threaded=True)
            thread_count += 1
        for thread_id in range(thread_count):
            fun_test.join_thread(build_rdma_threadid[thread_id])
            fun_test.log("Joined thread: {}".format(build_rdma_threadid[thread_id]))
        fun_test.log("Config done")

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
        tool_debug = fun_test.shared_variables["ping_debug"]

        # Load RDMA modules
        f10_host_roce.rdma_setup()
        f11_host_roce.rdma_setup()

        # Kill all RDMA tools
        f10_host_roce.cleanup()
        f11_host_roce.cleanup()

        # Check if ping works before running tests
        command_result = f10_hosts[0]["handle"].ping(dst=f11_hosts[0]["ipaddr"])
        fun_test.simple_assert(command_result, "F10 HU -> F11 HU ping")
        command_result = f11_hosts[0]["handle"].ping(dst=f10_hosts[0]["ipaddr"])
        fun_test.simple_assert(command_result, "F11 HU -> F10 HU ping")

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

        fun_test.log("Running tests for size {}".format(io_list))

        for size in io_list:
            f10_host_server = f10_host_roce.srping_test(size=size, count=test_count, debug=tool_debug, timeout=120)
            fun_test.sleep("Started srping server for size {}".format(size), seconds=1)
            f10_host_client = f10_host_roce.srping_test(size=size, count=test_count, debug=tool_debug,
                                                        server_ip=f10_hosts[0]["ipaddr"], timeout=120)

            # Kill client process then server process
            f10_client_pid = 0
            while f10_hosts[0]["handle"].process_exists(process_id=f10_host_client["cmd_pid"]):
                fun_test.sleep("Srping client on f10_host", 2)
                f10_client_pid += 1  # Counter to check before initiating kill
                if f10_client_pid == 60:
                    f10_hosts[0]["handle"].kill_process(process_id=f10_host_client["cmd_pid"])
                    f10_host_roce.dump_debug()
                    break
            f10_server_pid = 0
            while f10_hosts[0]["handle"].process_exists(process_id=f10_host_server["cmd_pid"]):
                fun_test.sleep("Srping server on f10_host", 2)
                f10_server_pid += 1  # Counter to check before initiating kill
                if f10_server_pid == 10:  # Reduce this time as client should have exited by now
                    f10_hosts[0]["handle"].kill_process(process_id=f10_host_server["cmd_pid"])
                    f10_host_roce.dump_debug()
                    break
            f10_server_result = f10_host_roce.parse_test_log(f10_host_server["output_file"], tool="srping",
                                                             debug=tool_debug)
            f10_client_result = f10_host_roce.parse_test_log(f10_host_client["output_file"], tool="srping",
                                                             debug=tool_debug,
                                                             client_cmd=True)
            fun_test.simple_assert(f10_server_result, "F10_host server result for size {}".format(size))
            fun_test.simple_assert(f10_client_result, "F10_host client result for size {}".format(size))

        for size in io_list:
            f11_host_server = f11_host_roce.srping_test(size=size, count=test_count, debug=tool_debug, timeout=120)
            fun_test.sleep("Started srping server for size {}".format(size), seconds=1)
            f11_host_client = f11_host_roce.srping_test(size=size, count=test_count, debug=tool_debug,
                                                        server_ip=f11_hosts[0]["ipaddr"], timeout=120)

            f11_client_pid = 0
            while f11_hosts[0]["handle"].process_exists(process_id=f11_host_client["cmd_pid"]):
                fun_test.sleep("Srping client on f11_host", 2)
                f11_client_pid += 1  # Counter to check before initiating kill
                if f11_client_pid == 60:
                    f11_hosts[0]["handle"].kill_process(process_id=f11_host_client["cmd_pid"])
                    f11_host_roce.dump_debug()
                    break

            f11_server_pid = 0
            while f11_hosts[0]["handle"].process_exists(process_id=f11_host_server["cmd_pid"]):
                fun_test.sleep("Srping server on f11_host", 2)
                f11_server_pid += 1  # Counter to check before initiating kill
                if f11_server_pid == 10:
                    f11_hosts[0]["handle"].kill_process(process_id=f11_host_server["cmd_pid"])
                    f11_host_roce.dump_debug()
                    break

            f11_server_result = f11_host_roce.parse_test_log(f11_host_server["output_file"], tool="srping",
                                                             debug=tool_debug)
            f11_client_result = f11_host_roce.parse_test_log(f11_host_client["output_file"], tool="srping",
                                                             debug=tool_debug, client_cmd=True)
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
        tool_debug = fun_test.shared_variables["ping_debug"]

        # Load RDMA modules
        f10_host_roce.rdma_setup()
        f11_host_roce.rdma_setup()

        # Kill all RDMA tools
        f10_host_roce.cleanup()
        f11_host_roce.cleanup()

        # Check if ping works before running tests
        command_result = f10_hosts[0]["handle"].ping(dst=f11_hosts[0]["ipaddr"])
        fun_test.simple_assert(command_result, "F10 HU -> F11 HU ping")
        command_result = f11_hosts[0]["handle"].ping(dst=f10_hosts[0]["ipaddr"])
        fun_test.simple_assert(command_result, "F11 HU -> F10 HU ping")

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

        fun_test.log("Running tests for size {}".format(io_list))

        for size in io_list:
            f10_host_server = f10_host_roce.rping_test(size=size, count=test_count, debug=tool_debug, timeout=120)
            fun_test.sleep("Started Rping server for size {}".format(size), seconds=1)
            f10_host_client = f10_host_roce.rping_test(size=size, count=test_count, debug=tool_debug,
                                                       server_ip=f10_hosts[0]["ipaddr"], timeout=120)

            f10_client_pid = 0
            while f10_hosts[0]["handle"].process_exists(process_id=f10_host_client["cmd_pid"]):
                fun_test.sleep("Rping client on f10_host", 2)
                f10_client_pid += 1  # Counter to check before initiating kill
                if f10_client_pid == 60:
                    f10_hosts[0]["handle"].kill_process(process_id=f10_host_client["cmd_pid"])
                    f10_host_roce.dump_debug()
                    break

            f10_server_pid = 0
            while f10_hosts[0]["handle"].process_exists(process_id=f10_host_server["cmd_pid"]):
                fun_test.sleep("Rping server on f10_host", 2)
                f10_server_pid += 1  # Counter to check before initiating kill
                if f10_server_pid == 10:
                    f10_hosts[0]["handle"].kill_process(process_id=f10_host_server["cmd_pid"])
                    f10_host_roce.dump_debug()
                    break

            f10_server_result = f10_host_roce.parse_test_log(f10_host_server["output_file"], tool="rping",
                                                             debug=tool_debug)
            f10_client_result = f10_host_roce.parse_test_log(f10_host_client["output_file"], tool="rping",
                                                             debug=tool_debug, client_cmd=True)
            fun_test.simple_assert(f10_server_result, "F10_host server result for size {}".format(size))
            fun_test.simple_assert(f10_client_result, "F10_host client result for size {}".format(size))

        for size in io_list:
            f11_host_server = f11_host_roce.rping_test(size=size, count=test_count, debug=tool_debug, timeout=120)
            fun_test.sleep("Started rping server for size {}".format(size), seconds=1)
            f11_host_client = f11_host_roce.rping_test(size=size, count=test_count, debug=tool_debug,
                                                       server_ip=f11_hosts[0]["ipaddr"], timeout=120)
            f11_client_pid = 0
            while f11_hosts[0]["handle"].process_exists(process_id=f11_host_client["cmd_pid"]):
                fun_test.sleep("Rping client on f11_host", 2)
                f11_client_pid += 1  # Counter to check before initiating kill
                if f11_client_pid == 60:
                    f11_hosts[0]["handle"].kill_process(process_id=f11_host_client["cmd_pid"])
                    f11_host_roce.dump_debug()
                    break
            f11_server_pid = 0
            while f11_hosts[0]["handle"].process_exists(process_id=f11_host_server["cmd_pid"]):
                fun_test.sleep("Rping server on f11_host", 2)
                f11_server_pid += 1  # Counter to check before initiating kill
                if f11_server_pid == 10:
                    f11_hosts[0]["handle"].kill_process(process_id=f11_host_server["cmd_pid"])
                    f11_host_roce.dump_debug()
                    break

            f11_server_result = f11_host_roce.parse_test_log(f11_host_server["output_file"], tool="rping",
                                                             debug=tool_debug,)
            f11_client_result = f11_host_roce.parse_test_log(f11_host_client["output_file"], tool="rping",
                                                             debug=tool_debug, client_cmd=True)
            fun_test.simple_assert(f11_server_result, "f11_host server result for size {}".format(size))
            fun_test.simple_assert(f11_client_result, "f11_host client result for size {}".format(size))

        fun_test.test_assert(True, "Rping loop back test")

    def cleanup(self):
        fun_test.shared_variables["f10_host_roce"].cleanup()
        fun_test.shared_variables["f10_host_roce"].cleanup()


class SrpingSeqIoTest(FunTestCase):
    server_key = {}
    random_io = False
    mtu = 0

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
        tool_debug = fun_test.shared_variables["ping_debug"]
        f10_storage_controller = fun_test.shared_variables["f10_storage_controller"]
        f11_storage_controller = fun_test.shared_variables["f11_storage_controller"]
        self.fcp = fun_test.shared_variables["enable_fcp"]

        # Load RDMA modules
        f10_host_roce.rdma_setup()
        f11_host_roce.rdma_setup()

        # Kill all RDMA tools
        f10_host_roce.cleanup()
        f11_host_roce.cleanup()

        # Check if ping works before running tests
        command_result = f10_hosts[0]["handle"].ping(dst=f11_hosts[0]["ipaddr"])
        fun_test.simple_assert(command_result, "F10 HU -> F11 HU ping")
        command_result = f11_hosts[0]["handle"].ping(dst=f10_hosts[0]["ipaddr"])
        fun_test.simple_assert(command_result, "F11 HU -> F10 HU ping")

        if self.mtu != 0:
            f10_hosts[0]["handle"].sudo_command("ifconfig {} mtu {}".format(f10_hosts[0]["iface_name"],
                                                                            self.mtu))
            f11_hosts[0]["handle"].sudo_command("ifconfig {} mtu {}".format(f11_hosts[0]["iface_name"],
                                                                            self.mtu))

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

        fun_test.log("Running tests for size {}".format(io_list))

        for size in io_list:
            # FCP stats before test on F10 & F11
            f10_fcp_stats_before = f10_storage_controller.peek("stats/fcp/nu/global")
            f11_fcp_stats_before = f11_storage_controller.peek("stats/fcp/nu/global")

            f10_host_test = f10_host_roce.srping_test(size=size, count=test_count, debug=tool_debug)
            fun_test.sleep("Started srping server for size {}".format(size), seconds=1)
            f11_host_test = f11_host_roce.srping_test(size=size, count=test_count, debug=tool_debug,
                                                      server_ip=f10_hosts[0]["ipaddr"])
            f10_pid_there = 0
            f11_pid_there = 0
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
            f10_host_result = f10_host_roce.parse_test_log(f10_host_test["output_file"], tool="srping",
                                                           debug=tool_debug)
            f11_host_result = f11_host_roce.parse_test_log(f11_host_test["output_file"], tool="srping",
                                                           debug=tool_debug, client_cmd=True)
            fun_test.simple_assert(f10_host_result, "F10_host result for size {}".format(size))
            fun_test.simple_assert(f11_host_result, "F11_host result for size {}".format(size))

            # FCP stats after test on F10 & F11
            f10_fcp_stats_after = f10_storage_controller.peek("stats/fcp/nu/global")
            f11_fcp_stats_after = f11_storage_controller.peek("stats/fcp/nu/global")

            if self.fcp:
                f10_fcb_dst_fcp_pkt_rcvd = f10_fcp_stats_after["data"]["FCB_DST_FCP_PKT_RCVD"]
                f11_fcb_src_fcp_pkt_xmtd = f11_fcp_stats_after["data"]["FCB_SRC_FCP_PKT_XMTD"]
                if f10_fcb_dst_fcp_pkt_rcvd == f11_fcb_src_fcp_pkt_xmtd and f10_fcb_dst_fcp_pkt_rcvd != 0:
                    fun_test.log("FCP rcvd & xmtd stat : {}".format(f10_fcb_dst_fcp_pkt_rcvd))
                counter_diff = f10_fcp_stats_after["data"]["FCB_DST_FCP_PKT_RCVD"] - \
                               f10_fcp_stats_before["data"]["FCB_DST_FCP_PKT_RCVD"]
                fun_test.log("FCP : F10 FCP_PKT_RCVD diff count : {}".format(counter_diff))
                fun_test.simple_assert(expression=(counter_diff != 0), message="F10 : Traffic is not FCP")

                counter_diff = f11_fcp_stats_after["data"]["FCB_SRC_FCP_PKT_XMTD"] - \
                               f11_fcp_stats_before["data"]["FCB_SRC_FCP_PKT_XMTD"]
                fun_test.log("FCP : F11 FCP_PKT_XMTD diff count : {}".format(counter_diff))
                fun_test.simple_assert(expression=(counter_diff != 0), message="F11 : Traffic is not FCP")

                # NFCP counters check
                counter_names = ["tdp0_nonfcp", "tdp1_nonfcp", "tdp2_nonfcp"]
                for cname in counter_names:
                    try:
                        counter_diff = f10_fcp_stats_after["data"][cname] - \
                                       f10_fcp_stats_before["data"][cname]
                        if counter_diff != 0 and counter_diff > 2000:
                            fun_test.simple_assert(False, "F10 {} counter diff : {}".format(cname, counter_diff))
                        counter_diff = f11_fcp_stats_after["data"][cname] - \
                                       f11_fcp_stats_before["data"][cname]
                        if counter_diff != 0 and counter_diff > 2000:
                            fun_test.simple_assert(False, "F11 {} counter diff : {}".format(cname, counter_diff))
                    except:
                        fun_test.critical("NFCP counter issue")
            else:
                counter_diff = f10_fcp_stats_after["data"]["FCB_DST_FCP_PKT_RCVD"] - \
                               f10_fcp_stats_before["data"]["FCB_DST_FCP_PKT_RCVD"]
                fun_test.log("NFCP : F10 FCP_PKT_RCVD diff count : {}".format(counter_diff))
                fun_test.simple_assert(expression=(counter_diff == 0),
                                       message="F10: Traffic is using FCP")
                counter_diff = f11_fcp_stats_after["data"]["FCB_SRC_FCP_PKT_XMTD"] - \
                               f11_fcp_stats_before["data"]["FCB_SRC_FCP_PKT_XMTD"]
                fun_test.log("NFCP : F11 FCP_PKT_XMTD diff count : {}".format(counter_diff))
                fun_test.simple_assert(expression=(counter_diff == 0),
                                       message="F11: Traffic is using FCP")
                counter_diff = f10_fcp_stats_after["data"]["FCB_SRC_NFCP_PKT_XMTD"] - \
                               f10_fcp_stats_before["data"]["FCB_SRC_NFCP_PKT_XMTD"]
                fun_test.simple_assert(expression=(counter_diff != 0),
                                       message="F10 : NFCP counters not incrementing")
                counter_diff = f11_fcp_stats_after["data"]["FCB_SRC_NFCP_PKT_XMTD"] - \
                               f11_fcp_stats_before["data"]["FCB_SRC_NFCP_PKT_XMTD"]
                fun_test.simple_assert(expression=(counter_diff != 0),
                                       message="F11 : NFCP counters not incrementing")

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
    mtu = 0

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
        tool_debug = fun_test.shared_variables["ping_debug"]
        f10_storage_controller = fun_test.shared_variables["f10_storage_controller"]
        f11_storage_controller = fun_test.shared_variables["f11_storage_controller"]
        self.fcp = fun_test.shared_variables["enable_fcp"]

        # Load RDMA modules
        f10_host_roce.rdma_setup()
        f11_host_roce.rdma_setup()

        # Kill all RDMA tools
        f10_host_roce.cleanup()
        f11_host_roce.cleanup()

        # Check if ping works before running tests
        command_result = f10_hosts[0]["handle"].ping(dst=f11_hosts[0]["ipaddr"])
        fun_test.simple_assert(command_result, "F10 HU -> F11 HU ping")
        command_result = f11_hosts[0]["handle"].ping(dst=f10_hosts[0]["ipaddr"])
        fun_test.simple_assert(command_result, "F11 HU -> F10 HU ping")

        if self.mtu != 0:
            f10_hosts[0]["handle"].sudo_command("ifconfig {} mtu {}".format(f10_hosts[0]["iface_name"],
                                                                            self.mtu))
            f11_hosts[0]["handle"].sudo_command("ifconfig {} mtu {}".format(f11_hosts[0]["iface_name"],
                                                                            self.mtu))

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

        fun_test.log("Running tests for size {}".format(io_list))

        for size in io_list:
            # FCP stats before test on F10 & F11
            f10_fcp_stats_before = f10_storage_controller.peek("stats/fcp/nu/global")
            f11_fcp_stats_before = f11_storage_controller.peek("stats/fcp/nu/global")

            f10_host_test = f10_host_roce.rping_test(size=size, count=test_count, debug=tool_debug)
            fun_test.sleep("Started rping server for size {}".format(size), seconds=1)
            f11_host_test = f11_host_roce.rping_test(size=size, count=test_count, debug=tool_debug,
                                                     server_ip=f10_hosts[0]["ipaddr"])
            f10_pid_there = 0
            f11_pid_there = 0
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
            f10_host_result = f10_host_roce.parse_test_log(f10_host_test["output_file"], tool="rping",
                                                           debug=tool_debug)
            f11_host_result = f11_host_roce.parse_test_log(f11_host_test["output_file"], tool="rping",
                                                           debug=tool_debug, client_cmd=True)
            fun_test.simple_assert(f10_host_result, "F10_host result for size {}".format(size))
            fun_test.simple_assert(f11_host_result, "F11_host result for size {}".format(size))

            # FCP stats after test on F10 & F11
            f10_fcp_stats_after = f10_storage_controller.peek("stats/fcp/nu/global")
            f11_fcp_stats_after = f11_storage_controller.peek("stats/fcp/nu/global")

            if self.fcp:
                f10_fcb_dst_fcp_pkt_rcvd = f10_fcp_stats_after["data"]["FCB_DST_FCP_PKT_RCVD"]
                f11_fcb_src_fcp_pkt_xmtd = f11_fcp_stats_after["data"]["FCB_SRC_FCP_PKT_XMTD"]
                if f10_fcb_dst_fcp_pkt_rcvd == f11_fcb_src_fcp_pkt_xmtd and f10_fcb_dst_fcp_pkt_rcvd != 0:
                    fun_test.log("FCP rcvd & xmtd stat : {}".format(f10_fcb_dst_fcp_pkt_rcvd))
                counter_diff = f10_fcp_stats_after["data"]["FCB_DST_FCP_PKT_RCVD"] - \
                               f10_fcp_stats_before["data"]["FCB_DST_FCP_PKT_RCVD"]
                fun_test.log("FCP : F10 FCP_PKT_RCVD diff count : {}".format(counter_diff))
                fun_test.simple_assert(expression=(counter_diff != 0), message="F10 : Traffic is not FCP")

                counter_diff = f11_fcp_stats_after["data"]["FCB_SRC_FCP_PKT_XMTD"] - \
                               f11_fcp_stats_before["data"]["FCB_SRC_FCP_PKT_XMTD"]
                fun_test.log("FCP : F11 FCP_PKT_XMTD diff count : {}".format(counter_diff))
                fun_test.simple_assert(expression=(counter_diff != 0), message="F11 : Traffic is not FCP")

                # NFCP counters check
                counter_names = ["tdp0_nonfcp", "tdp1_nonfcp", "tdp2_nonfcp"]
                for cname in counter_names:
                    try:
                        counter_diff = f10_fcp_stats_after["data"][cname] - \
                                       f10_fcp_stats_before["data"][cname]
                        if counter_diff != 0 and counter_diff > 2000:
                            fun_test.simple_assert(False, "F10 {} counter diff : {}".format(cname, counter_diff))
                        counter_diff = f11_fcp_stats_after["data"][cname] - \
                                       f11_fcp_stats_before["data"][cname]
                        if counter_diff != 0 and counter_diff > 2000:
                            fun_test.simple_assert(False, "F11 {} counter diff : {}".format(cname, counter_diff))
                    except:
                        fun_test.critical("NFCP counter issue")
            else:
                counter_diff = f10_fcp_stats_after["data"]["FCB_DST_FCP_PKT_RCVD"] - \
                               f10_fcp_stats_before["data"]["FCB_DST_FCP_PKT_RCVD"]
                fun_test.log("NFCP : F10 FCP_PKT_RCVD diff count : {}".format(counter_diff))
                fun_test.simple_assert(expression=(counter_diff == 0),
                                       message="F10: Traffic is using FCP")
                counter_diff = f11_fcp_stats_after["data"]["FCB_SRC_FCP_PKT_XMTD"] - \
                               f11_fcp_stats_before["data"]["FCB_SRC_FCP_PKT_XMTD"]
                fun_test.log("NFCP : F11 FCP_PKT_XMTD diff count : {}".format(counter_diff))
                fun_test.simple_assert(expression=(counter_diff == 0),
                                       message="F11: Traffic is using FCP")
                counter_diff = f10_fcp_stats_after["data"]["FCB_SRC_NFCP_PKT_XMTD"] - \
                               f10_fcp_stats_before["data"]["FCB_SRC_NFCP_PKT_XMTD"]
                fun_test.simple_assert(expression=(counter_diff != 0),
                                       message="F10 : NFCP counters not incrementing")
                counter_diff = f11_fcp_stats_after["data"]["FCB_SRC_NFCP_PKT_XMTD"] - \
                               f11_fcp_stats_before["data"]["FCB_SRC_NFCP_PKT_XMTD"]
                fun_test.simple_assert(expression=(counter_diff != 0),
                                       message="F11 : NFCP counters not incrementing")

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
    mtu = 0

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
        f10_storage_controller = fun_test.shared_variables["f10_storage_controller"]
        f11_storage_controller = fun_test.shared_variables["f11_storage_controller"]
        self.fcp = fun_test.shared_variables["enable_fcp"]

        # Check if ping works before running tests
        command_result = f10_hosts[0]["handle"].ping(dst=f11_hosts[0]["ipaddr"])
        fun_test.simple_assert(command_result, "F10 HU -> F11 HU ping")
        command_result = f11_hosts[0]["handle"].ping(dst=f10_hosts[0]["ipaddr"])
        fun_test.simple_assert(command_result, "F11 HU -> F10 HU ping")

        # Load RDMA modules
        f10_host_roce.rdma_setup()
        f11_host_roce.rdma_setup()

        # Kill all RDMA tools
        f10_host_roce.cleanup()
        f11_host_roce.cleanup()

        if self.mtu != 0:
            f10_hosts[0]["handle"].sudo_command("ifconfig {} mtu {}".format(f10_hosts[0]["iface_name"],
                                                                            self.mtu))
            f11_hosts[0]["handle"].sudo_command("ifconfig {} mtu {}".format(f11_hosts[0]["iface_name"],
                                                                            self.mtu))

        if self.use_rdmacm:
            rdmacm = True
        else:
            rdmacm = False

        if self.random_io:
            if not fun_test.shared_variables["disable_large_io"]:
                max_io = 2097152
            else:
                max_io = 524288
            io_type = "Random"
            io_list = []
            while True:
                rand_num = random.randint(1, max_io)
                if rand_num not in io_list:
                    io_list.append(rand_num)
                if len(io_list) == 16:
                    break
        else:
            io_type = "Sequential"
            io_list = []
            size = 32
            while size <= 65536:
                if size == 65536:
                    io_list.append(65534)
                else:
                    io_list.append(size)
                size = size * 2

        fun_test.log("Running tests for size {}".format(io_list))

        for test in test_type_list:
            for size in io_list:
                # FCP stats before test on F10 & F11
                f10_fcp_stats_before = f10_storage_controller.peek("stats/fcp/nu/global")
                f11_fcp_stats_before = f11_storage_controller.peek("stats/fcp/nu/global")

                f10_host_test = f10_host_roce.ib_bw_test(test_type=test, size=size, rdma_cm=rdmacm)
                f11_host_test = f11_host_roce.ib_bw_test(test_type=test, size=size, rdma_cm=rdmacm,
                                                         server_ip=f10_hosts[0]["ipaddr"])
                f10_pid_there = 0
                f11_pid_there = 0
                while f10_hosts[0]["handle"].process_exists(process_id=f10_host_test["cmd_pid"]):
                    # sleep for 5 seconds as it takes longer time to run for larger IO
                    fun_test.sleep("ib_bw test on f10_host", 5)
                    f10_pid_there += 1
                    if f10_pid_there == 60:
                        f10_hosts[0]["handle"].kill_process(process_id=f10_host_test["cmd_pid"])
                while f11_hosts[0]["handle"].process_exists(process_id=f11_host_test["cmd_pid"]):
                    fun_test.sleep("ib_bw test on f11_host", 5)
                    f11_pid_there += 1
                    if f11_pid_there == 60:
                        f11_hosts[0]["handle"].kill_process(process_id=f11_host_test["cmd_pid"])
                f10_host_result = f10_host_roce.parse_test_log(f10_host_test["output_file"], tool="ib_bw")
                f11_host_result = f11_host_roce.parse_test_log(f11_host_test["output_file"], tool="ib_bw",
                                                               client_cmd=True)
                fun_test.simple_assert(f10_host_result, "F10_host {} result of size {}".format(test, size))
                fun_test.simple_assert(f11_host_result, "F11_host {} result of size {}".format(test, size))

                # FCP stats after test on F10 & F11
                f10_fcp_stats_after = f10_storage_controller.peek("stats/fcp/nu/global")
                f11_fcp_stats_after = f11_storage_controller.peek("stats/fcp/nu/global")

                if self.fcp:
                    f10_fcb_dst_fcp_pkt_rcvd = f10_fcp_stats_after["data"]["FCB_DST_FCP_PKT_RCVD"]
                    f11_fcb_src_fcp_pkt_xmtd = f11_fcp_stats_after["data"]["FCB_SRC_FCP_PKT_XMTD"]
                    if f10_fcb_dst_fcp_pkt_rcvd == f11_fcb_src_fcp_pkt_xmtd and f10_fcb_dst_fcp_pkt_rcvd != 0:
                        fun_test.log("FCP rcvd & xmtd stat : {}".format(f10_fcb_dst_fcp_pkt_rcvd))
                    counter_diff = f10_fcp_stats_after["data"]["FCB_DST_FCP_PKT_RCVD"] - \
                                   f10_fcp_stats_before["data"]["FCB_DST_FCP_PKT_RCVD"]
                    fun_test.log("FCP : F10 FCP_PKT_RCVD diff count : {}".format(counter_diff))
                    fun_test.simple_assert(expression=(counter_diff != 0), message="F10 : Traffic is not FCP")

                    counter_diff = f11_fcp_stats_after["data"]["FCB_SRC_FCP_PKT_XMTD"] - \
                                   f11_fcp_stats_before["data"]["FCB_SRC_FCP_PKT_XMTD"]
                    fun_test.log("FCP : F11 FCP_PKT_XMTD diff count : {}".format(counter_diff))
                    fun_test.simple_assert(expression=(counter_diff != 0), message="F11 : Traffic is not FCP")

                    # NFCP counters check
                    counter_names = ["tdp0_nonfcp", "tdp1_nonfcp", "tdp2_nonfcp"]
                    for cname in counter_names:
                        try:
                            counter_diff = f10_fcp_stats_after["data"][cname] - \
                                           f10_fcp_stats_before["data"][cname]
                            if counter_diff != 0 and counter_diff > 2000:
                                fun_test.simple_assert(False, "F10 {} counter diff : {}".format(cname, counter_diff))
                            counter_diff = f11_fcp_stats_after["data"][cname] - \
                                           f11_fcp_stats_before["data"][cname]
                            if counter_diff != 0 and counter_diff > 2000:
                                fun_test.simple_assert(False, "F11 {} counter diff : {}".format(cname, counter_diff))
                        except:
                            fun_test.critical("NFCP counter issue")
                else:
                    counter_diff = f10_fcp_stats_after["data"]["FCB_DST_FCP_PKT_RCVD"] - \
                                   f10_fcp_stats_before["data"]["FCB_DST_FCP_PKT_RCVD"]
                    fun_test.log("NFCP : F10 FCP_PKT_RCVD diff count : {}".format(counter_diff))
                    fun_test.simple_assert(expression=(counter_diff == 0),
                                           message="F10: Traffic is using FCP")
                    counter_diff = f11_fcp_stats_after["data"]["FCB_SRC_FCP_PKT_XMTD"] - \
                                   f11_fcp_stats_before["data"]["FCB_SRC_FCP_PKT_XMTD"]
                    fun_test.log("NFCP : F11 FCP_PKT_XMTD diff count : {}".format(counter_diff))
                    fun_test.simple_assert(expression=(counter_diff == 0),
                                           message="F11: Traffic is using FCP")
                    counter_diff = f10_fcp_stats_after["data"]["FCB_SRC_NFCP_PKT_XMTD"] - \
                                   f10_fcp_stats_before["data"]["FCB_SRC_NFCP_PKT_XMTD"]
                    fun_test.simple_assert(expression=(counter_diff != 0),
                                           message="F10 : NFCP counters not incrementing")
                    counter_diff = f11_fcp_stats_after["data"]["FCB_SRC_NFCP_PKT_XMTD"] - \
                                   f11_fcp_stats_before["data"]["FCB_SRC_NFCP_PKT_XMTD"]
                    fun_test.simple_assert(expression=(counter_diff != 0),
                                           message="F11 : NFCP counters not incrementing")

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
    mtu = 0

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

        f10_storage_controller = fun_test.shared_variables["f10_storage_controller"]
        f11_storage_controller = fun_test.shared_variables["f11_storage_controller"]
        self.fcp = fun_test.shared_variables["enable_fcp"]

        # Check if ping works before running tests
        command_result = f10_hosts[0]["handle"].ping(dst=f11_hosts[0]["ipaddr"])
        fun_test.simple_assert(command_result, "F10 HU -> F11 HU ping")
        command_result = f11_hosts[0]["handle"].ping(dst=f10_hosts[0]["ipaddr"])
        fun_test.simple_assert(command_result, "F11 HU -> F10 HU ping")

        # Load RDMA modules
        f10_host_roce.rdma_setup()
        f11_host_roce.rdma_setup()

        # Kill all RDMA tools
        f10_host_roce.cleanup()
        f11_host_roce.cleanup()

        if self.mtu != 0:
            f10_hosts[0]["handle"].sudo_command("ifconfig {} mtu {}".format(f10_hosts[0]["iface_name"],
                                                                            self.mtu))
            f11_hosts[0]["handle"].sudo_command("ifconfig {} mtu {}".format(f11_hosts[0]["iface_name"],
                                                                            self.mtu))

        if self.use_rdmacm:
            rdmacm = True
        else:
            rdmacm = False

        if self.random_io:
            if not fun_test.shared_variables["disable_large_io"]:
                max_io = 2097152
            else:
                max_io = 524288
            io_type = "Random"
            io_list = []
            while True:
                rand_num = random.randint(1, max_io)
                if rand_num not in io_list:
                    io_list.append(rand_num)
                if len(io_list) == 16:
                    break
        else:
            io_type = "Sequential"
            io_list = []
            size = 32
            while size <= 65536:
                if size == 65536:
                    io_list.append(65534)
                else:
                    io_list.append(size)
                size = size * 2

        for test in test_type_list:
            for size in io_list:
                # FCP stats before test on F10 & F11
                f10_fcp_stats_before = f10_storage_controller.peek("stats/fcp/nu/global")
                f11_fcp_stats_before = f11_storage_controller.peek("stats/fcp/nu/global")

                f10_host_test = f10_host_roce.ib_lat_test(test_type=test, size=size, rdma_cm=rdmacm)
                f11_host_test = f11_host_roce.ib_lat_test(test_type=test, size=size, rdma_cm=rdmacm,
                                                          server_ip=f10_hosts[0]["ipaddr"])
                f10_pid_there = 0
                f11_pid_there = 0
                while f10_hosts[0]["handle"].process_exists(process_id=f10_host_test["cmd_pid"]):
                    # sleep for 5 seconds as ib_write_lat takes longer time to run for larger IO
                    fun_test.sleep("ib_lat test on f10_host", 5)
                    f10_pid_there += 1
                    if f10_pid_there == 60:
                        f10_hosts[0]["handle"].kill_process(process_id=f10_host_test["cmd_pid"])
                while f11_hosts[0]["handle"].process_exists(process_id=f11_host_test["cmd_pid"]):
                    fun_test.sleep("ib_lat test on f11_host", 5)
                    f11_pid_there += 1
                    if f11_pid_there == 60:
                        f11_hosts[0]["handle"].kill_process(process_id=f11_host_test["cmd_pid"])
                f10_host_result = f10_host_roce.parse_test_log(f10_host_test["output_file"], tool="ib_lat")
                f11_host_result = f11_host_roce.parse_test_log(f11_host_test["output_file"], tool="ib_lat",
                                                               client_cmd=True)
                fun_test.simple_assert(f10_host_result, "F10_host {} result of size {}".format(test, size))
                fun_test.simple_assert(f11_host_result, "F11_host {} result of size {}".format(test, size))

                # FCP stats after test on F10 & F11
                f10_fcp_stats_after = f10_storage_controller.peek("stats/fcp/nu/global")
                f11_fcp_stats_after = f11_storage_controller.peek("stats/fcp/nu/global")

                if self.fcp:
                    f10_fcb_dst_fcp_pkt_rcvd = f10_fcp_stats_after["data"]["FCB_DST_FCP_PKT_RCVD"]
                    f11_fcb_src_fcp_pkt_xmtd = f11_fcp_stats_after["data"]["FCB_SRC_FCP_PKT_XMTD"]
                    if f10_fcb_dst_fcp_pkt_rcvd == f11_fcb_src_fcp_pkt_xmtd and f10_fcb_dst_fcp_pkt_rcvd != 0:
                        fun_test.log("FCP rcvd & xmtd stat : {}".format(f10_fcb_dst_fcp_pkt_rcvd))
                    counter_diff = f10_fcp_stats_after["data"]["FCB_DST_FCP_PKT_RCVD"] - \
                                   f10_fcp_stats_before["data"]["FCB_DST_FCP_PKT_RCVD"]
                    fun_test.log("FCP : F10 FCP_PKT_RCVD diff count : {}".format(counter_diff))
                    fun_test.simple_assert(expression=(counter_diff != 0), message="F10 : Traffic is not FCP")

                    counter_diff = f11_fcp_stats_after["data"]["FCB_SRC_FCP_PKT_XMTD"] - \
                                   f11_fcp_stats_before["data"]["FCB_SRC_FCP_PKT_XMTD"]
                    fun_test.log("FCP : F11 FCP_PKT_XMTD diff count : {}".format(counter_diff))
                    fun_test.simple_assert(expression=(counter_diff != 0), message="F11 : Traffic is not FCP")

                    # NFCP counters check
                    counter_names = ["tdp0_nonfcp", "tdp1_nonfcp", "tdp2_nonfcp"]
                    for cname in counter_names:
                        try:
                            counter_diff = f10_fcp_stats_after["data"][cname] - \
                                           f10_fcp_stats_before["data"][cname]
                            if counter_diff != 0 and counter_diff > 2000:
                                fun_test.simple_assert(False, "F10 {} counter diff : {}".format(cname, counter_diff))
                            counter_diff = f11_fcp_stats_after["data"][cname] - \
                                           f11_fcp_stats_before["data"][cname]
                            if counter_diff != 0 and counter_diff > 2000:
                                fun_test.simple_assert(False, "F11 {} counter diff : {}".format(cname, counter_diff))
                        except:
                            fun_test.critical("NFCP counter issue")
                else:
                    counter_diff = f10_fcp_stats_after["data"]["FCB_DST_FCP_PKT_RCVD"] - \
                                   f10_fcp_stats_before["data"]["FCB_DST_FCP_PKT_RCVD"]
                    fun_test.log("NFCP : F10 FCP_PKT_RCVD diff count : {}".format(counter_diff))
                    fun_test.simple_assert(expression=(counter_diff == 0),
                                           message="F10: Traffic is using FCP")
                    counter_diff = f11_fcp_stats_after["data"]["FCB_SRC_FCP_PKT_XMTD"] - \
                                   f11_fcp_stats_before["data"]["FCB_SRC_FCP_PKT_XMTD"]
                    fun_test.log("NFCP : F11 FCP_PKT_XMTD diff count : {}".format(counter_diff))
                    fun_test.simple_assert(expression=(counter_diff == 0),
                                           message="F11: Traffic is using FCP")
                    counter_diff = f10_fcp_stats_after["data"]["FCB_SRC_NFCP_PKT_XMTD"] - \
                                   f10_fcp_stats_before["data"]["FCB_SRC_NFCP_PKT_XMTD"]
                    fun_test.simple_assert(expression=(counter_diff != 0),
                                           message="F10 : NFCP counters not incrementing")
                    counter_diff = f11_fcp_stats_after["data"]["FCB_SRC_NFCP_PKT_XMTD"] - \
                                   f11_fcp_stats_before["data"]["FCB_SRC_NFCP_PKT_XMTD"]
                    fun_test.simple_assert(expression=(counter_diff != 0),
                                           message="F11 : NFCP counters not incrementing")

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
        f10_storage_controller = fun_test.shared_variables["f10_storage_controller"]
        f11_storage_controller = fun_test.shared_variables["f11_storage_controller"]
        self.fcp = fun_test.shared_variables["enable_fcp"]

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
            if not fun_test.shared_variables["disable_large_io"]:
                max_io = 2097152
            else:
                max_io = 524288
            io_type = "Random"
            io_list = []
            while True:
                rand_num = random.randint(1, max_io)
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
        f10_max_cqe = int(f10_device_info["max_cqe"])
        f11_max_cqe = int(f11_device_info["max_cqe"])
        if f10_max_cqe != f11_max_cqe:
            max_cqe_in_test = min(f10_max_cqe, f11_max_cqe)
            fun_test.critical("Max CQE on F10 : {} & F11 : {}".format(f10_max_cqe, f11_max_cqe))
            fun_test.add_checkpoint("Max CQE mismatch", "FAILED", f10_max_cqe, f11_max_cqe)
        else:
            max_cqe_in_test = f10_max_cqe
        fun_test.log("The max_cqe is {}".format(max_cqe_in_test))
        size = 1
        for test in test_type_list:
            for qp in qp_list:
                # FCP stats before test on F10 & F11
                f10_fcp_stats_before = f10_storage_controller.peek("stats/fcp/nu/global")
                f11_fcp_stats_before = f11_storage_controller.peek("stats/fcp/nu/global")

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
                check_num_qp = True
                while f10_hosts[0]["handle"].process_exists(process_id=f10_host_test["cmd_pid"]):
                    fun_test.sleep("ib_bw test on f10_host", 2)
                    f10_pid_there += 1
                    if f10_pid_there == 10:
                        current_qp = f10_host_roce.qp_check()
                        if current_qp > 1 and check_num_qp:
                            if current_qp != qp:
                                fun_test.critical("Current QP count {} doesn't match test QP count of {}".
                                                  format(current_qp, qp))
                                check_num_qp = False
                                fun_test.add_checkpoint("QP mismatch in test", "FAILED", expected=qp, actual=current_qp)
                            else:
                                fun_test.log_section("Num of QP : {}".format(current_qp))
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

                # FCP stats after test on F10 & F11
                f10_fcp_stats_after = f10_storage_controller.peek("stats/fcp/nu/global")
                f11_fcp_stats_after = f11_storage_controller.peek("stats/fcp/nu/global")

                if self.fcp:
                    f10_fcb_dst_fcp_pkt_rcvd = f10_fcp_stats_after["data"]["FCB_DST_FCP_PKT_RCVD"]
                    f11_fcb_src_fcp_pkt_xmtd = f11_fcp_stats_after["data"]["FCB_SRC_FCP_PKT_XMTD"]
                    if f10_fcb_dst_fcp_pkt_rcvd == f11_fcb_src_fcp_pkt_xmtd and f10_fcb_dst_fcp_pkt_rcvd != 0:
                        fun_test.log("FCP rcvd & xmtd stat : {}".format(f10_fcb_dst_fcp_pkt_rcvd))
                    counter_diff = f10_fcp_stats_after["data"]["FCB_DST_FCP_PKT_RCVD"] - \
                                   f10_fcp_stats_before["data"]["FCB_DST_FCP_PKT_RCVD"]
                    fun_test.log("FCP : F10 FCP_PKT_RCVD diff count : {}".format(counter_diff))
                    fun_test.simple_assert(expression=(counter_diff != 0), message="F10 : Traffic is not FCP")

                    counter_diff = f11_fcp_stats_after["data"]["FCB_SRC_FCP_PKT_XMTD"] - \
                                   f11_fcp_stats_before["data"]["FCB_SRC_FCP_PKT_XMTD"]
                    fun_test.log("FCP : F11 FCP_PKT_XMTD diff count : {}".format(counter_diff))
                    fun_test.simple_assert(expression=(counter_diff != 0), message="F11 : Traffic is not FCP")

                    # NFCP counters check
                    counter_names = ["tdp0_nonfcp", "tdp1_nonfcp", "tdp2_nonfcp"]
                    for cname in counter_names:
                        try:
                            counter_diff = f10_fcp_stats_after["data"][cname] - \
                                           f10_fcp_stats_before["data"][cname]
                            if counter_diff != 0 and counter_diff > 2000:
                                fun_test.simple_assert(False, "F10 {} counter diff : {}".format(cname, counter_diff))
                            counter_diff = f11_fcp_stats_after["data"][cname] - \
                                           f11_fcp_stats_before["data"][cname]
                            if counter_diff != 0 and counter_diff > 2000:
                                fun_test.simple_assert(False, "F11 {} counter diff : {}".format(cname, counter_diff))
                        except:
                            fun_test.critical("NFCP counter issue")
                else:
                    counter_diff = f10_fcp_stats_after["data"]["FCB_DST_FCP_PKT_RCVD"] - \
                                   f10_fcp_stats_before["data"]["FCB_DST_FCP_PKT_RCVD"]
                    fun_test.log("NFCP : F10 FCP_PKT_RCVD diff count : {}".format(counter_diff))
                    fun_test.simple_assert(expression=(counter_diff == 0),
                                           message="F10: Traffic is using FCP")
                    counter_diff = f11_fcp_stats_after["data"]["FCB_SRC_FCP_PKT_XMTD"] - \
                                   f11_fcp_stats_before["data"]["FCB_SRC_FCP_PKT_XMTD"]
                    fun_test.log("NFCP : F11 FCP_PKT_XMTD diff count : {}".format(counter_diff))
                    fun_test.simple_assert(expression=(counter_diff == 0),
                                           message="F11: Traffic is using FCP")
                    counter_diff = f10_fcp_stats_after["data"]["FCB_SRC_NFCP_PKT_XMTD"] - \
                                   f10_fcp_stats_before["data"]["FCB_SRC_NFCP_PKT_XMTD"]
                    fun_test.simple_assert(expression=(counter_diff != 0),
                                           message="F10 : NFCP counters not incrementing")
                    counter_diff = f11_fcp_stats_after["data"]["FCB_SRC_NFCP_PKT_XMTD"] - \
                                   f11_fcp_stats_before["data"]["FCB_SRC_NFCP_PKT_XMTD"]
                    fun_test.simple_assert(expression=(counter_diff != 0),
                                           message="F11 : NFCP counters not incrementing")

            fun_test.test_assert(True, "IB_BW {} test with {} IO".format(test, io_type))

    def cleanup(self):
        fun_test.shared_variables["f10_host_roce"].cleanup()
        fun_test.shared_variables["f10_host_roce"].cleanup()


class SrpingSqIo512MtuTest(SrpingSeqIoTest):
    mtu = 512

    def describe(self):
        self.set_test_details(id=18,
                              summary="SRPING Seq IO Test with 512 MTU",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Set MTU to 512
                                  3. Start srping test for different sizes
                                  """)


class SrpingSqIo1024MtuTest(SrpingSeqIoTest):
    mtu = 1024

    def describe(self):
        self.set_test_details(id=19,
                              summary="SRPING Seq IO Test with 1024 MTU",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Set MTU to 1024
                                  3. Start srping test for different sizes
                                  """)


class SrpingSqIo2048MtuTest(SrpingSeqIoTest):
    mtu = 2048

    def describe(self):
        self.set_test_details(id=20,
                              summary="SRPING Seq IO Test with 2048 MTU",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Set MTU to 2048
                                  3. Start srping test for different sizes
                                  """)


class SrpingSqIo4096MtuTest(SrpingSeqIoTest):
    mtu = 4096

    def describe(self):
        self.set_test_details(id=21,
                              summary="SRPING Seq IO Test with 4096 MTU",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Set MTU to 4096
                                  3. Start srping test for different sizes
                                  """)


class SrpingSqIo9000MtuTest(SrpingSeqIoTest):
    mtu = 9000

    def describe(self):
        self.set_test_details(id=22,
                              summary="SRPING Seq IO Test with 9000 MTU",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Set MTU to 9000
                                  3. Start srping test for different sizes
                                  """)


class SrpingRandIo512MtuTest(SrpingSeqIoTest):
    mtu = 512
    random_io = True

    def describe(self):
        self.set_test_details(id=23,
                              summary="SRPING Rand IO Test with 512 MTU",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Set MTU to 512
                                  3. Start srping test for different sizes
                                  """)


class SrpingRandIo1024MtuTest(SrpingSeqIoTest):
    mtu = 1024
    random_io = True

    def describe(self):
        self.set_test_details(id=24,
                              summary="SRPING Rand IO Test with 1024 MTU",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Set MTU to 1024
                                  3. Start srping test for different sizes
                                  """)


class SrpingRandIo2048MtuTest(SrpingSeqIoTest):
    mtu = 2048
    random_io = True

    def describe(self):
        self.set_test_details(id=25,
                              summary="SRPING Rand IO Test with 2048 MTU",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Set MTU to 2048
                                  3. Start srping test for different sizes
                                  """)


class SrpingRandIo4096MtuTest(SrpingSeqIoTest):
    mtu = 4096
    random_io = True

    def describe(self):
        self.set_test_details(id=26,
                              summary="SRPING Rand IO Test with 4096 MTU",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Set MTU to 4096
                                  3. Start srping test for different sizes
                                  """)


class SrpingRandIo9000MtuTest(SrpingSeqIoTest):
    mtu = 9000
    random_io = True

    def describe(self):
        self.set_test_details(id=27,
                              summary="SRPING Rand IO Test with 9000 MTU",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Set MTU to 9000
                                  3. Start srping test for different sizes
                                  """)


class IbBwSeqIo512MtuTest(IbBwSeqIoTest):
    server_key = {}
    mtu = 512

    def describe(self):
        self.set_test_details(id=28,
                              summary="IB_Bw* Seq IO with 512 MTU",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start ib_bw test for random sizes
                                  """)


class IbBwSeqIo1024MtuTest(IbBwSeqIoTest):
    server_key = {}
    mtu = 1024

    def describe(self):
        self.set_test_details(id=29,
                              summary="IB_Bw* Seq IO with 1024 MTU",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start ib_bw test for random sizes
                                  """)


class IbBwSeqIo2048MtuTest(IbBwSeqIoTest):
    server_key = {}
    mtu = 2048

    def describe(self):
        self.set_test_details(id=30,
                              summary="IB_Bw* Seq IO with 2048 MTU",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start ib_bw test for random sizes
                                  """)


class IbBwSeqIo4096MtuTest(IbBwSeqIoTest):
    server_key = {}
    mtu = 4096

    def describe(self):
        self.set_test_details(id=31,
                              summary="IB_Bw* Seq IO with 4096 MTU",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start ib_bw test for random sizes
                                  """)


class IbBwSeqIo9000MtuTest(IbBwSeqIoTest):
    server_key = {}
    mtu = 9000

    def describe(self):
        self.set_test_details(id=32,
                              summary="IB_Bw* Seq IO with 9000 MTU",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start ib_bw test for random sizes
                                  """)


class IbBwRandIo512MtuTest(IbBwSeqIoTest):
    server_key = {}
    random_io = True
    mtu = 512

    def describe(self):
        self.set_test_details(id=33,
                              summary="IB_BW* Random IO with 512 MTU",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start ib_bw test for different sizes
                                  """)


class IbBwRandIo1024MtuTest(IbBwSeqIoTest):
    server_key = {}
    random_io = True
    mtu = 1024

    def describe(self):
        self.set_test_details(id=34,
                              summary="IB_BW* Random IO with 1024 MTU",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start ib_bw test for different sizes
                                  """)


class IbBwRandIo2048MtuTest(IbBwSeqIoTest):
    server_key = {}
    random_io = True
    mtu = 2048

    def describe(self):
        self.set_test_details(id=35,
                              summary="IB_BW* Random IO with 2048 MTU",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start ib_bw test for different sizes
                                  """)


class IbBwRandIo4096MtuTest(IbBwSeqIoTest):
    server_key = {}
    random_io = True
    mtu = 4096

    def describe(self):
        self.set_test_details(id=36,
                              summary="IB_BW* Random IO with 4096 MTU",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start ib_bw test for different sizes
                                  """)


class IbBwRandIo9000MtuTest(IbBwSeqIoTest):
    server_key = {}
    random_io = True
    mtu = 9000

    def describe(self):
        self.set_test_details(id=37,
                              summary="IB_BW* Random IO with 9000 MTU",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start ib_bw test for different sizes
                                  """)


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
    job_input = fun_test.get_job_inputs()
    if job_input:
        if job_input.get("full_suite", False):
            ts.add_test_case(SrpingSqIo512MtuTest())
            ts.add_test_case(SrpingSqIo1024MtuTest())
            ts.add_test_case(SrpingSqIo2048MtuTest())
            ts.add_test_case(SrpingSqIo4096MtuTest())
            ts.add_test_case(SrpingSqIo9000MtuTest())
            ts.add_test_case(SrpingRandIo512MtuTest())
            ts.add_test_case(SrpingRandIo1024MtuTest())
            ts.add_test_case(SrpingRandIo2048MtuTest())
            ts.add_test_case(SrpingRandIo4096MtuTest())
            ts.add_test_case(SrpingRandIo9000MtuTest())
            ts.add_test_case(IbBwSeqIo512MtuTest())
            ts.add_test_case(IbBwSeqIo1024MtuTest())
            ts.add_test_case(IbBwSeqIo2048MtuTest())
            ts.add_test_case(IbBwSeqIo4096MtuTest())
            ts.add_test_case(IbBwSeqIo9000MtuTest())
            ts.add_test_case(IbBwRandIo512MtuTest())
            ts.add_test_case(IbBwRandIo1024MtuTest())
            ts.add_test_case(IbBwRandIo2048MtuTest())
            ts.add_test_case(IbBwRandIo4096MtuTest())
            ts.add_test_case(IbBwRandIo9000MtuTest())
    ts.run()
