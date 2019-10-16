from lib.system.fun_test import *
from lib.utilities.funcp_config import *
from scripts.networking.funcp.helper import *
from scripts.networking.funeth.sanity import Funeth
from lib.topology.topology_helper import TopologyHelper
from web.fun_test.analytics_models_helper import ModelHelper, get_data_collection_time
from fun_global import PerfUnit, FunPlatform
from lib.templates.networking.rdma_tools import Rocetools
import re
from asset.asset_manager import *
import math


def add_to_data_base(value_dict):
    unit_dict = {
        "read_avg_latency_unit": PerfUnit.UNIT_USECS,
        "write_avg_latency_unit": PerfUnit.UNIT_USECS,
        "read_min_latency_unit": PerfUnit.UNIT_USECS,
        "write_min_latency_unit": PerfUnit.UNIT_USECS,
        "read_max_latency_unit": PerfUnit.UNIT_USECS,
        "write_max_latency_unit": PerfUnit.UNIT_USECS,
        "read_99_latency_unit": PerfUnit.UNIT_USECS,
        "write_99_latency_unit": PerfUnit.UNIT_USECS,
        "read_99_99_latency_unit": PerfUnit.UNIT_USECS,
        "write_99_99_latency_unit": PerfUnit.UNIT_USECS,
        "read_bandwidth_unit": PerfUnit.UNIT_GBITS_PER_SEC,
        "write_bandwidth_unit": PerfUnit.UNIT_GBITS_PER_SEC,
        "read_msg_rate_unit": PerfUnit.UNIT_MPPS,
        "write_msg_rate_unit": PerfUnit.UNIT_MPPS,
    }
    
    value_dict["date_time"] = get_data_collection_time()
    value_dict["version"] = fun_test.get_version()
    value_dict["platform"] = FunPlatform.F1
    model_name = "AlibabaRdmaPerformance"
    status = fun_test.PASSED
    try:
        generic_helper = ModelHelper(model_name=model_name)
        generic_helper.set_units(validate=True, **unit_dict)
        generic_helper.add_entry(**value_dict)
        generic_helper.set_status(status)
        print "used generic helper to add an entry"
    except Exception as ex:
        fun_test.critical(str(ex))


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

        f1_0_boot_args = "app=load_mods,hw_hsu_test cc_huid=3 --dpc-server --serial --all_100g --dpc-uart " \
                         "retimer={} --mgmt syslog=3".format(f10_retimer)
        f1_1_boot_args = "app=load_mods,hw_hsu_test cc_huid=2 --dpc-server --serial --all_100g --dpc-uart " \
                         "retimer={} --mgmt syslog=3".format(f11_retimer)

        topology_helper = TopologyHelper()

        if "deploy_setup" in job_inputs:
            deploy_setup = job_inputs["deploy_setup"]
            fun_test.shared_variables["deploy_setup"] = deploy_setup
        else:
            deploy_setup = True
            fun_test.shared_variables["deploy_setup"] = deploy_setup
        if "test_speed" in job_inputs:
            roce_speed = job_inputs["test_speed"]
            fun_test.shared_variables["test_speed"] = roce_speed
        else:
            roce_speed = "all"
            fun_test.shared_variables["test_speed"] = roce_speed
        if "enable_fcp" in job_inputs:
            enable_fcp = job_inputs["enable_fcp"]
            fun_test.shared_variables["enable_fcp"] = enable_fcp
        else:
            enable_fcp = True
            fun_test.shared_variables["enable_fcp"] = enable_fcp
        qp_list = []
        if "qp_list" in job_inputs:
            qp_list = job_inputs["qp_list"]
            fun_test.shared_variables["qp_list"] = qp_list
        else:
            qp_list = [1, 2, 4, 8, 16, 32]
            fun_test.shared_variables["qp_list"] = qp_list

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
            fun_test.shared_variables["come_obj"] = come_obj
            come_obj.sudo_command("netplan apply")
            come_obj.sudo_command("iptables -F")
            come_obj.sudo_command("ip6tables -F")
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

            # Bringup FunCP
            fun_test.test_assert(expression=funcp_obj.bringup_funcp(prepare_docker=False), message="Bringup FunCP")
            # Assign MPG IPs from dhcp
            funcp_obj.assign_mpg_ips(static=self.server_key["fs"][fs_name]["mpg_ips"]["static"],
                                     f1_1_mpg=self.server_key["fs"][fs_name]["mpg_ips"]["mpg1"],
                                     f1_0_mpg=self.server_key["fs"][fs_name]["mpg_ips"]["mpg0"])

            # Check PICe Link on host
            servers_mode = self.server_key["fs"][fs_name]["hosts"]
            for server in servers_mode:
                result = verify_host_pcie_link(hostname=server, mode=servers_mode[server], reboot=False)
                fun_test.test_assert(expression=(result != "0"), message="Make sure that PCIe links on host %s went up"
                                                                         % server)
                if result == "2":
                    fun_test.add_checkpoint("<b><font color='red'><PCIE link did not come up in %s mode</font></b>"
                                            % servers_mode[server])
        else:
            # Get COMe object
            am = AssetManager()
            th = TopologyHelper(spec=am.get_test_bed_spec(name=fs_name))
            topology = th.get_expanded_topology()
            dut = topology.get_dut(index=0)
            dut_name = dut.get_name()
            fs_spec = fun_test.get_asset_manager().get_fs_by_name(name=dut_name)
            fs_obj = Fs.get(fs_spec=fs_spec, already_deployed=True)
            come_obj = fs_obj.get_come()
            fun_test.shared_variables["come_obj"] = come_obj

            fun_test.log("Getting host info")
            host_dict = {"f1_0": [], "f1_1": []}
            temp_host_list = []
            temp_host_list1 = []
            expanded_topology = topology_helper.get_expanded_topology()
            pcie_hosts = expanded_topology.get_pcie_hosts_on_interfaces(dut_index=0)
            for pcie_interface_index, host_info in pcie_hosts.iteritems():
                host_instance = fun_test.get_asset_manager().get_linux_host(host_info["name"])
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

            if not enable_fcp:
                # Add static routes on Containers
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
            funeth_obj = Funeth(tb_config_obj)
            fun_test.shared_variables['funeth_obj'] = funeth_obj
            setup_hu_host(funeth_obj, update_driver=True, sriov=0, num_queues=1)

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
        bg_proc_id = {}
        for obj in host_objs:
            if obj == "f1_0":
                host_count = fun_test.shared_variables["host_len_f10"]
                bg_proc_id[obj] = []
            elif obj == "f1_1":
                host_count = fun_test.shared_variables["host_len_f11"]
                bg_proc_id[obj] = []
            for x in xrange(0, host_count):
                update_path = host_objs[obj][x].command("echo $HOME")
                update_script = update_path.strip() + "/mks/update_rdma.sh"
                print update_script
                bg_proc_id[obj].append(host_objs[obj][x].
                                       start_bg_process("{} build build".format(update_script),
                                                        timeout=1200))
        # fun_test.sleep("Building rdma_perf & core", seconds=120)
        for obj in host_objs:
            if obj == "f1_0":
                host_count = fun_test.shared_variables["host_len_f10"]
            elif obj == "f1_1":
                host_count = fun_test.shared_variables["host_len_f11"]
            for x in xrange(0, host_count):
                for pid in bg_proc_id[obj]:
                    while host_objs[obj][x].process_exists(process_id=pid):
                        fun_test.sleep(message="Still building RDMA repo...", seconds=5)
                host_objs[obj][x].disconnect()

        # Create a dict containing F1_0 & F1_1 details
        f10_hosts = []
        f11_hosts = []
        for objs in host_objs:
            for handle in host_objs[objs]:
                handle.sudo_command("rm -rf /tmp/*bw* && rm -rf /tmp/*rping* /tmp/*lat*")
                handle.sudo_command("dmesg -c > /dev/null")
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
                                     "handle": handle, "roce_handle": Rocetools(handle)}
                    f10_hosts.append(f10_host_dict)
                elif objs == "f1_1":
                    f11_host_dict = {"name": hostname, "iface_name": iface_name, "ipaddr": iface_addr,
                                     "handle": handle, "roce_handle": Rocetools(handle)}
                    f11_hosts.append(f11_host_dict)
        fun_test.shared_variables["f10_hosts"] = f10_hosts
        fun_test.shared_variables["f11_hosts"] = f11_hosts

    def cleanup(self):
        pass


class BwTest(FunTestCase):
    server_key = {}
    mtu = 0
    fcp = True
    rt = None
    io_size = [1, 128, 256, 512, 1024, 4096]

    def describe(self):
        pass

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):
        global funcp_obj, servers_mode, servers_list, fs_name
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        f10_hosts = fun_test.shared_variables["f10_hosts"]
        f11_hosts = fun_test.shared_variables["f11_hosts"]
        qp_list = fun_test.shared_variables["qp_list"]
        come_obj = fun_test.shared_variables["come_obj"]
        kill_time = 30
        test_case_failure_time = 20

        # Using hosts based on minimum host length
        total_link_bw = min(fun_test.shared_variables["host_len_f10"], fun_test.shared_variables["host_len_f11"])
        if total_link_bw > 1:
            link_capacity = "200G"
        else:
            link_capacity = "100G"
        for index in range(total_link_bw):
            rdma_setup = f10_hosts[index]["roce_handle"].rdma_setup()
            fun_test.simple_assert(rdma_setup, "RDMA setup on {}".format(f10_hosts[index]["name"]))
            rdma_setup = f11_hosts[index]["roce_handle"].rdma_setup()
            fun_test.simple_assert(rdma_setup, "RDMA setup on {}".format(f11_hosts[index]["name"]))

        table_data_headers = ["Size in bytes", "QP count", "BW in Gbps", "Msg Rate in Mpps"]
        table_data_cols = ["size_bandwidth", "qp_count", "avg_bandwidth", "msg_rate"]
        table_data_rows = []
        row_data_dict = {}

        # Set MTU n hosts
        if self.mtu != 0:
            for index in range(total_link_bw):
                f10_hosts[index]["handle"].sudo_command("ifconfig {} mtu {}".format(f10_hosts[index]["iface_name"],
                                                                                    self.mtu))
                f11_hosts[index]["handle"].sudo_command("ifconfig {} mtu {}".format(f11_hosts[index]["iface_name"],
                                                                                    self.mtu))
        if not self.fcp:
            come_obj.command(
                "echo SELECT 1 > /scratch/opt/fungible/f10_del")
            come_obj.command(
                "echo DEL \\\"openconfig-fcp:fcp-tunnel[ftep=\\\'4.4.4.4\\\']\\\" >> /scratch/opt/fungible/f10_del")
            come_obj.command(
                "echo SELECT 1 > /scratch/opt/fungible/f11_del")
            come_obj.command(
                "echo DEL \\\"openconfig-fcp:fcp-tunnel[ftep=\\\'3.3.3.3\\\']\\\" >> /scratch/opt/fungible/f11_del")
            come_obj.command("docker exec F1-0 bash -c \"redis-cli < f10_del\"")
            come_obj.command("docker exec F1-1 bash -c \"redis-cli < f11_del\"")
            fun_test.sleep("Removed FTEP", seconds=5)

        for size in self.io_size:
            for qp in qp_list:
                f10_pid_list = []
                f11_pid_list = []
                # Start servers on F1_0
                for index in range(total_link_bw):
                    f10_server = f10_hosts[index]["roce_handle"].ib_bw_test(test_type=self.rt, perf=True, size=size,
                                                                            qpair=qp,
                                                                            timeout=300)
                    pid_dict = {f10_hosts[index]["roce_handle"]: f10_server}
                    f10_pid_list.append(pid_dict)
                fun_test.sleep("Servers started for {} BW test with size={} & qp={}".format(self.rt, size, qp),
                               seconds=5)
                # Start servers on F1_1
                for index in range(total_link_bw):
                    f11_client = f11_hosts[index]["roce_handle"].ib_bw_test(test_type=self.rt, perf=True, size=size,
                                                                            qpair=qp,
                                                                            server_ip=f10_hosts[index]["ipaddr"],
                                                                            timeout=300)
                    pid_dict = {f11_hosts[index]["roce_handle"]: f11_client}
                    f11_pid_list.append(pid_dict)
                fun_test.sleep("Clients started for {} BW test with size={} & qp={}".format(self.rt, size, qp),
                               seconds=5)
                # fun_test.sleep("Clients started for {} BW test, size {}".format(rt, size), seconds=20)
                fun_test.sleep("Waiting for {} seconds before killing tests".format(kill_time), seconds=kill_time)
                # First kill client & then kill server
                parsed_result = []
                for handle in f11_pid_list:
                    for key, value in handle.items():
                        key.kill_pid(pid=value["cmd_pid"])
                        while key.process_check(pid=value["cmd_pid"]):
                            fun_test.sleep(message="Client process still there", seconds=2)
                        wait_time = test_case_failure_time
                        while key.qp_check() > 1:
                            fun_test.sleep("Client : QP count {}".format(key.qp_check()), seconds=5)
                            wait_time -= 1
                            if wait_time == 0:
                                print "******** QP didn't clear on client *****************"
                                fun_test.test_assert(False, "QP is not clearing on client, aborting test case")
                        parsed_result.append(key.parse_test_log(filepath=value["output_file"], tool="ib_bw",
                                                                perf=True))
                for handle in f10_pid_list:
                    for key, value in handle.items():
                        key.kill_pid(pid=value["cmd_pid"])
                        while key.process_check(pid=value["cmd_pid"]):
                            fun_test.sleep(message="Server process still there", seconds=2)
                        wait_time = test_case_failure_time
                        while key.qp_check() > 1:
                            fun_test.sleep("Server : QP count {}".format(key.qp_check()), seconds=5)
                            wait_time -= 1
                            if wait_time == 0:
                                print "******** QP didn't clear on server *****************"
                                fun_test.test_assert(False, "QP is not clearing on server, aborting test case")
                avg_bandwidth = 0
                msg_rate = 0
                bw_peak_gbps = 0
                qp_count = qp
                row_data_list = []
                total_values = len(parsed_result)
                for results in parsed_result:
                    size_bandwidth = float(results[0])
                    iterations = float(results[1])
                    bw_peak_gbps += float(results[2])
                    avg_bandwidth += float(results[3])
                    msg_rate += float(results[4])
                for item in table_data_cols:
                    row_data_list.append(eval(item))
                table_data_rows.append(row_data_list)

                value_dict = {
                    "operation": "{}".format(self.rt),
                    "size_bandwidth": size_bandwidth,
                    "{}_bandwidth".format(self.rt): avg_bandwidth,
                    "{}_msg_rate".format(self.rt): msg_rate,
                    "fcp": self.fcp,
                    "qp": qp_count,
                    "mtu": self.mtu
                }
                add_to_data_base(value_dict)

                table_data = {"headers": table_data_headers, "rows": table_data_rows}

        fun_test.add_table(panel_header="{} BW Test, MTU : {}, FCP : {}, LnkCap : {}".
                           format(self.rt, self.mtu, self.fcp, link_capacity).upper(),
                           table_name=self.summary,
                           table_data=table_data)

        fun_test.log("Test done")

    def cleanup(self):
        pass


class LatencyTest(FunTestCase):
    server_key = {}
    mtu = 0
    fcp = True
    rt = None
    io_size = [1, 128, 256, 512, 1024, 4096]

    def describe(self):
        pass

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):
        global funcp_obj, servers_mode, servers_list, fs_name
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        f10_hosts = fun_test.shared_variables["f10_hosts"]
        f11_hosts = fun_test.shared_variables["f11_hosts"]
        qp_list = fun_test.shared_variables["qp_list"]
        kill_time = 20
        test_case_failure_time = 20

        # Using hosts based on minimum host length
        total_link_bw = min(fun_test.shared_variables["host_len_f10"], fun_test.shared_variables["host_len_f11"])
        if total_link_bw > 1:
            link_capacity = "200G"
        else:
            link_capacity = "100G"
        for index in range(total_link_bw):
            rdma_setup = f10_hosts[index]["roce_handle"].rdma_setup()
            fun_test.simple_assert(rdma_setup, "RDMA setup on {}".format(f10_hosts[index]["name"]))
            rdma_setup = f11_hosts[index]["roce_handle"].rdma_setup()
            fun_test.simple_assert(rdma_setup, "RDMA setup on {}".format(f11_hosts[index]["name"]))

        table_data_headers = ["Size in bytes", "Iterations", "t_min[usec]", "t_max[usec]", "t_avg[usec]",
                              "99%[usec]", "99.9%[usec]"]
        table_data_cols = ["size_latency", "iterations", "min_latency", "max_latency",
                           "avg_latency", "latency_99", "latency_99_99"]

        table_data_rows = []
        row_data_dict = {}

        # Set MTU n hosts
        if self.mtu != 0:
            for index in range(total_link_bw):
                f10_hosts[index]["handle"].sudo_command("ifconfig {} mtu {}".format(f10_hosts[index]["iface_name"],
                                                                                    self.mtu))
                f11_hosts[index]["handle"].sudo_command("ifconfig {} mtu {}".format(f11_hosts[index]["iface_name"],
                                                                                    self.mtu))
        if not self.fcp:
            come_obj = Linux(host_ip="fs66-come", ssh_username="fun", ssh_password="123")
            come_obj.command(
                "echo SELECT 1 > /scratch/opt/fungible/f10_del")
            come_obj.command(
                "echo DEL \\\"openconfig-fcp:fcp-tunnel[ftep=\\\'4.4.4.4\\\']\\\" >> /scratch/opt/fungible/f10_del")
            come_obj.command(
                "echo SELECT 1 > /scratch/opt/fungible/f11_del")
            come_obj.command(
                "echo DEL \\\"openconfig-fcp:fcp-tunnel[ftep=\\\'3.3.3.3\\\']\\\" >> /scratch/opt/fungible/f11_del")
            come_obj.command("docker exec F1-0 bash -c \"redis-cli < f10_del\"")
            come_obj.command("docker exec F1-1 bash -c \"redis-cli < f11_del\"")

        for size in self.io_size:
            f10_pid_list = []
            f11_pid_list = []
            # Start servers on F1_0
            for index in range(total_link_bw):
                f10_server = f10_hosts[index]["roce_handle"].ib_lat_test(test_type=self.rt, perf=True, size=size,
                                                                         iteration=10000,
                                                                         timeout=300)
                pid_dict = {f10_hosts[index]["roce_handle"]: f10_server}
                f10_pid_list.append(pid_dict)
            fun_test.sleep("Servers started for {} Latency test with size={}".format(self.rt, size),
                           seconds=5)
            # Start servers on F1_1
            for index in range(total_link_bw):
                f11_client = f11_hosts[index]["roce_handle"].ib_lat_test(test_type=self.rt, perf=True, size=size,
                                                                         iteration=10000,
                                                                         server_ip=f10_hosts[index]["ipaddr"],
                                                                         timeout=300)
                pid_dict = {f11_hosts[index]["roce_handle"]: f11_client}
                f11_pid_list.append(pid_dict)
            fun_test.sleep("Clients started for {} Latency test with size={}".format(self.rt, size),
                           seconds=5)
            fun_test.sleep("Waiting for {} seconds before killing tests".format(kill_time), seconds=kill_time)
            # First kill client & then kill server
            parsed_result = []
            for handle in f11_pid_list:
                for key, value in handle.items():
                    key.kill_pid(pid=value["cmd_pid"])
                    while key.process_check(pid=value["cmd_pid"]):
                        fun_test.sleep(message="Client process still there", seconds=2)
                    wait_time = test_case_failure_time
                    while key.qp_check() > 1:
                        fun_test.sleep("Client : QP count {}".format(key.qp_check()), seconds=5)
                        wait_time -= 1
                        if wait_time == 0:
                            print "******** QP didn't clear on client *****************"
                            fun_test.test_assert(False, "QP is not clearing on client, aborting test case")
                    parsed_result.append(key.parse_test_log(filepath=value["output_file"], tool="ib_lat",
                                                            perf=True))
            for handle in f10_pid_list:
                for key, value in handle.items():
                    key.kill_pid(pid=value["cmd_pid"])
                    while key.process_check(pid=value["cmd_pid"]):
                        fun_test.sleep(message="Server process still there", seconds=2)
                    wait_time = test_case_failure_time
                    while key.qp_check() > 1:
                        fun_test.sleep("Server : QP count {}".format(key.qp_check()), seconds=5)
                        wait_time -= 1
                        if wait_time == 0:
                            print "******** QP didn't clear on server *****************"
                            fun_test.test_assert(False, "QP is not clearing on server, aborting test case")
            min_latency = 0
            max_latency = 0
            avg_latency = 0
            latency_99 = 0
            latency_99_99 = 0
            iterations = 0
            row_data_list = []
            total_values = len(parsed_result)
            for results in parsed_result:
                size_latency = float(results[0])
                iterations = float(results[4])
                min_latency = float(results[5])
                max_latency = float(results[6])
                avg_latency = float(results[8])
                latency_99 = float(results[10])
                latency_99_99 = float(results[11])
            for item in table_data_cols:
                row_data_list.append(eval(item))
            table_data_rows.append(row_data_list)

            value_dict = {
                "operation": "{}".format(self.rt),
                "size_latency": size_latency,
                "{}_avg_latency".format(self.rt): avg_latency,
                "{}_min_latency".format(self.rt): min_latency,
                "{}_max_latency".format(self.rt): max_latency,
                "{}_99_latency".format(self.rt): latency_99,
                "{}_99_99_latency".format(self.rt): latency_99_99,
                "mtu": self.mtu,
                "fcp": self.fcp
            }
            add_to_data_base(value_dict)
            table_data = {"headers": table_data_headers, "rows": table_data_rows}

        fun_test.add_table(panel_header="{} Latency Test, MTU : {}, FCP : {}".
                           format(self.rt, self.mtu, self.fcp).upper(),
                           table_name=self.summary,
                           table_data=table_data)

        fun_test.log("Test done")

    def cleanup(self):
        pass


class BwWriteFcp1500(BwTest):
    rt = "write"
    mtu = 1500
    fcp = True

    def describe(self):
        self.set_test_details(id=3,
                              summary="Write BW with MTU=1500 & FCP",
                              steps="""
                                      1. Load funrdma & rdma_ucm driver
                                      2. Start ib_write_bw test for different sizes
                                      """)


class LatWriteFcp1500(LatencyTest):
    rt = "write"
    mtu = 1500
    fcp = True

    def describe(self):
        self.set_test_details(id=4,
                              summary="Write Latency with MTU=1500 & FCP",
                              steps="""
                                      1. Load funrdma & rdma_ucm driver
                                      2. Start ib_write_lat test for different sizes
                                      """)


class BwWriteFcp9000(BwTest):
    rt = "write"
    fcp = True
    mtu = 9000
    io_size = [4096]

    def describe(self):
        self.set_test_details(id=5,
                              summary="Write BW with MTU=9000 & FCP",
                              steps="""
                                      1. Load funrdma & rdma_ucm driver
                                      2. Start ib_write_bw test for different sizes
                                      """)


class LatWriteFcp9000(LatencyTest):
    rt = "write"
    mtu = 9000
    fcp = True
    io_size = [4096]

    def describe(self):
        self.set_test_details(id=6,
                              summary="Write Latency with MTU=9000 & FCP",
                              steps="""
                                      1. Load funrdma & rdma_ucm driver
                                      2. Start ib_write_lat test for IO_Size = 4096
                                      """)


class BwWriteNfcp1500(BwTest):
    rt = "write"
    mtu = 1500
    fcp = False

    def describe(self):
        self.set_test_details(id=7,
                              summary="Write BW with MTU=1500 & NFCP",
                              steps="""
                                      1. Load funrdma & rdma_ucm driver
                                      2. Start ib_write_bw test for different sizes
                                      """)


class LatWriteNfcp1500(LatencyTest):
    rt = "write"
    mtu = 1500
    fcp = False

    def describe(self):
        self.set_test_details(id=8,
                              summary="Write Latency with MTU=1500 & NFCP",
                              steps="""
                                      1. Load funrdma & rdma_ucm driver
                                      2. Start ib_write_lat test for different sizes
                                      """)


class BwWriteNfcp9000(BwTest):
    rt = "write"
    mtu = 9000
    fcp = False
    io_size = [4096]

    def describe(self):
        self.set_test_details(id=9,
                              summary="Write BW with MTU=9000 & NFCP",
                              steps="""
                                      1. Load funrdma & rdma_ucm driver
                                      2. Start ib_write_bw test for different sizes
                                      """)


class LatWriteNfcp9000(LatencyTest):
    rt = "write"
    mtu = 9000
    fcp = False
    io_size = [4096]

    def describe(self):
        self.set_test_details(id=10,
                              summary="Write Latency with MTU=9000 & NFCP",
                              steps="""
                                      1. Load funrdma & rdma_ucm driver
                                      2. Start ib_write_lat test for IO_Size = 4096
                                      """)


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(BringupSetup())
    ts.add_test_case(NicEmulation())
    ts.add_test_case(BwWriteFcp1500())
    ts.add_test_case(LatWriteFcp1500())
    ts.add_test_case(BwWriteFcp9000())
    ts.add_test_case(LatWriteFcp9000())
    ts.add_test_case(BwWriteNfcp1500())
    ts.add_test_case(LatWriteNfcp1500())
    ts.add_test_case(BwWriteNfcp9000())
    ts.add_test_case(LatWriteNfcp9000())

    ts.run()
