from lib.system.fun_test import *
from lib.utilities.funcp_config import *
from scripts.networking.funcp.helper import *
from scripts.networking.funeth.sanity import Funeth
from lib.topology.topology_helper import TopologyHelper
from web.fun_test.analytics_models_helper import ModelHelper, get_data_collection_time
from fun_global import PerfUnit, FunPlatform
import re


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
        "write_msg_rate_unit": PerfUnit.UNIT_MPPS
    }
    # This dictionary is just for reference
    default_value_dict = {
        "date_time": get_data_collection_time(),
        "platform": FunPlatform.F1,
        "version": fun_test.get_version(),
        "test": "RDMA_test",
        "operation": "read",

        "size_latency": 128,
        "size_bandwidth": 128,
        "read_avg_latency": 100,
        "write_avg_latency": 100,
        "read_min_latency": 100,
        "write_min_latency": 100,
        "read_max_latency": 100,
        "write_max_latency": 100,
        "read_99_latency": 100,
        "write_99_latency": 100,
        "read_99_99_latency": 100,
        "write_99_99_latency": 100,
        "read_bandwidth": 100,
        "write_bandwidth": 100,
        "read_msg_rate": 100,
        "write_msg_rate": 100
    }
    
    value_dict["date_time"] = get_data_collection_time()
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
        roce_tests = []
        if "test_type" in job_inputs:
            roce_tests.append(job_inputs["test_type"])
            fun_test.shared_variables["test_type"] = roce_tests
        else:
            roce_tests = ["write", "read"]
            fun_test.shared_variables["test_type"] = roce_tests
        if "test_speed" in job_inputs:
            roce_speed = job_inputs["test_speed"]
            fun_test.shared_variables["test_speed"] = roce_speed
        else:
            roce_speed = "all"
            fun_test.shared_variables["test_speed"] = roce_speed

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

            # Bringup FunCP
            fun_test.test_assert(expression=funcp_obj.bringup_funcp(prepare_docker=True), message="Bringup FunCP")
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
                #if host_info["name"] not in temp_host_list:
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

        # Check PICe Link on host
        servers_mode = self.server_key["fs"][fs_name]["hosts"]
        for server in servers_mode:
            result = verify_host_pcie_link(hostname=server, mode=servers_mode[server], reboot=False)
            fun_test.test_assert(expression=(result != "0"), message="Make sure that PCIe links on host %s went up"
                                                                     % server)
            if result == "2":
                fun_test.add_checkpoint("<b><font color='red'><PCIE link did not come up in %s mode</font></b>"
                                        % servers_mode[server])

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
        for obj in host_objs:
            if obj == "f1_0":
                host_count = fun_test.shared_variables["host_len_f10"]
            elif obj == "f1_1":
                host_count = fun_test.shared_variables["host_len_f11"]
            for x in xrange(0, host_count):
                host_objs[obj][x].start_bg_process("/home/localadmin/mks/update_rdma.sh update update", timeout=1200)
                # host_objs[obj][x].command("hostname")
        fun_test.sleep("Building rdma_perf & core", seconds=120)

    def cleanup(self):
        pass


class Rocebwtest(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=3,
                              summary="Run ib_* bw Test",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start ib_write_bw test for different sizes
                                  """)

    def setup(self):

        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):
        global funcp_obj, servers_mode, servers_list, fs_name
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        roce_tests = fun_test.shared_variables["test_type"]
        host_obj = fun_test.shared_variables["hosts_obj"]

        # Load drivers on host
        for obj in host_obj:
            if obj == "f1_0":
                host_count = fun_test.shared_variables["host_len_f10"]
            elif obj == "f1_1":
                host_count = fun_test.shared_variables["host_len_f11"]
            for x in xrange(0, host_count):
                # Check if funeth is loaded or else bail out
                check_funeth = host_obj[obj][x].lsmod("funeth")
                fun_test.test_assert(check_funeth, "Check funeth load status")
                host_obj[obj][x].sudo_command("dmesg -c > /dev/null")
                host_obj[obj][x].sudo_command("killall -g ib_write_lat ib_write_bw ib_read_lat ib_read_bw")
                check_module = host_obj[obj][x].lsmod("funrdma")
                if not check_module:
                    host_obj[obj][x].sudo_command("insmod /mnt/ws/fungible-host-drivers/linux/kernel/funrdma.ko")
                    host_obj[obj][x].modprobe("rdma_ucm")
                    check_load_module = host_obj[obj][x].lsmod("funrdma")
                    fun_test.test_assert(check_load_module, "Funrdma load")
                    # host_obj[obj][x].sudo_command("/etc/init.d/irqbalance stop")
                    # host_obj[obj][x].sudo_command("tuned-adm profile network-throughput")

        # Create a dict containing F1_0 & F1_1 details
        f10_hosts = []
        f11_hosts = []

        for objs in host_obj:
            for handle in host_obj[objs]:
                handle.sudo_command("rm -rf /tmp/*bw*")
                hostname = handle.command("hostname").strip()
                iface_name = handle.command(
                    "ip link ls up | awk '{print $2}' | grep -e '00:f1:1d' -e '00:de:ad' -B 1 | head -1 | tr -d :").\
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

        fun_test.shared_variables["f10_hosts"] = f10_hosts
        fun_test.shared_variables["f11_hosts"] = f11_hosts

        # Using hosts based on minimum host length
        total_link_bw = min(fun_test.shared_variables["host_len_f10"], fun_test.shared_variables["host_len_f11"])

        table_data_headers = ["Server", "Client", "Size in bytes", "BW in Gbps", "Msg Rate in Mpps"]
        table_data_cols = ["server_name", "client_name", "size_bandwidth", "avg_bandwidth", "msg_rate"]
        table_data_rows = []
        row_data_dict = {}

        # List to hold dict of test results
        all_result_dict = []

        for rt in roce_tests:
            if rt == "write":
                ib_test = "ib_write_bw"
            elif rt == "read":
                ib_test = "ib_read_bw"
            for size in ["1", "128", "256", "512", "1024", "4096"]:
                f10_pid_list = []
                f11_pid_list = []
                # Start servers on F1_0
                for index in range(total_link_bw):
                    f10_hosts[index]["handle"].command(
                        "export PATH=$PATH:/mnt/ws/fungible-rdma-core/build/bin/:/mnt/ws/fungible-perftest/ && "
                        "export LD_LIBRARY_PATH=/mnt/ws/fungible-rdma-core/build/lib/")
                    pid = f10_hosts[index]["handle"].start_bg_process(command="{} -d funrdma0 -s {} --report_gbits -F".
                                                                      format(ib_test, size),
                                                                      nohup=False, timeout=300)
                    pid_dict = {"handle": f10_hosts[index]["handle"], "pid": pid}
                    f10_pid_list.append(pid_dict)
                fun_test.sleep("Servers started for {} BW test".format(rt), seconds=5)

                # Start clients on F1_1
                for index in range(total_link_bw):
                    f11_hosts[index]["handle"].command(
                        "export PATH=$PATH:/mnt/ws/fungible-rdma-core/build/bin/:/mnt/ws/fungible-perftest/ && "
                        "export LD_LIBRARY_PATH=/mnt/ws/fungible-rdma-core/build/lib/")
                    file_name = f11_hosts[index]["name"].replace("-", "_") + "_" + ib_test + "_" + size + "_client"
                    pid = f11_hosts[index]["handle"].start_bg_process(
                        command="{} -d funrdma0 -s {} {} --report_gbits -F --run_infinitely -D 5".
                        format(ib_test, size, f10_hosts[index]["ipaddr"]), nohup=False,
                        output_file="/tmp/{}".format(file_name), timeout=300)
                    pid_dict = {"handle": f11_hosts[index]["handle"], "pid": pid}
                    f11_pid_list.append(pid_dict)
                    fun_test.log("Starting {} BW test, Server:{} <------> Client:{}".
                                 format(rt, f10_hosts[index]["name"], f11_hosts[index]["name"]))
                fun_test.sleep("Clients started for {} BW test, size {}".format(rt, size), seconds=20)

                # First kill client then server
                for ids in f11_pid_list:
                    ids["handle"].kill_process(ids["pid"])
                    test_result = ids["handle"].command("sed 'x;$!d' < /tmp/{}".format(file_name))
                    result_line = re.findall(r'[\d.]+', test_result)
                    row_data_list = []
                    server_name = f10_hosts[index]["name"].replace("-", "_")
                    client_name = f11_hosts[index]["name"].replace("-", "_")
                    size_bandwidth = result_line[0]
                    iterations = result_line[1]
                    bw_peak_gbps = result_line[2]
                    avg_bandwidth = result_line[3]
                    msg_rate = result_line[4]
                    for item in table_data_cols:
                        row_data_list.append(eval(item))
                    table_data_rows.append(row_data_list)

                    value_dict = {
                        "version": fun_test.get_version(),
                        "test": "IB_Write_BW_Test",
                        "operation": "{}".format(rt),
                        "size_bandwidth": size_bandwidth,
                        "{}_bandwidth".format(rt): avg_bandwidth,
                        "{}_msg_rate".format(rt): msg_rate
                    }
                    add_to_data_base(value_dict)
                    table_data = {"headers": table_data_headers, "rows": table_data_rows}
                for ids in f10_pid_list:
                    ids["handle"].kill_process(ids["pid"])
            fun_test.add_table(panel_header="{} Table".format(ib_test), table_name=self.summary,
                               table_data=table_data)

        fun_test.log("Test done")

    def cleanup(self):
        pass


class Rocelattest(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=4,
                              summary="Run ib_* lat Test",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start ib_write/read_lat test for different sizes
                                  """)

    def setup(self):

        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):
        global funcp_obj, servers_mode, servers_list, fs_name
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        roce_tests = fun_test.shared_variables["test_type"]

        f10_hosts = fun_test.shared_variables["f10_hosts"]
        f11_hosts = fun_test.shared_variables["f11_hosts"]

        # Using hosts based on minimum host length
        total_link_bw = min(fun_test.shared_variables["host_len_f10"], fun_test.shared_variables["host_len_f11"])

        table_data_headers = ["Server", "Client", "Size in bytes", "t_min[usec]", "t_max[usec]", "t_avg[usec]",
                              "99%[usec]", "99.9%[usec]"]
        table_data_cols = ["server_name", "client_name", "size_latency", "min_latency", "max_latency",
                           "avg_latency", "latency_99", "latency_99_99"]
        table_data_rows = []

        # List to hold dict of test results
        all_result_dict = []

        for rt in roce_tests:
            if rt == "write":
                ib_test = "ib_write_lat"
            elif rt == "read":
                ib_test = "ib_read_lat"
            for size in ["1", "128", "256", "512", "1024", "4096"]:
                f10_pid_list = []
                f11_pid_list = []
                # Start servers on F1_0
                for index in range(total_link_bw):
                    f10_hosts[index]["handle"].command(
                        "export PATH=$PATH:/mnt/ws/fungible-rdma-core/build/bin/:/mnt/ws/fungible-perftest/ && "
                        "export LD_LIBRARY_PATH=/mnt/ws/fungible-rdma-core/build/lib/")
                    pid = f10_hosts[index]["handle"].start_bg_process(command="{} -d funrdma0 -s {} -F -n 10000".
                                                                      format(ib_test, size),
                                                                      nohup=False, timeout=120)
                    pid_dict = {"handle": f10_hosts[index]["handle"], "pid": pid}
                    f10_pid_list.append(pid_dict)
                fun_test.sleep("Servers started for {} LAT test".format(rt), seconds=5)

                # Start clients on F1_1
                for index in range(total_link_bw):
                    f11_hosts[index]["handle"].command(
                        "export PATH=$PATH:/mnt/ws/fungible-rdma-core/build/bin/:/mnt/ws/fungible-perftest/ && "
                        "export LD_LIBRARY_PATH=/mnt/ws/fungible-rdma-core/build/lib/")
                    file_name = f11_hosts[index]["name"].replace("-", "_") + "_" + ib_test + "_" + size + "_client"
                    pid = f11_hosts[index]["handle"].start_bg_process(
                        command="{} -d funrdma0 -s {} {} -F -n 10000".
                        format(ib_test, size, f10_hosts[index]["ipaddr"]), nohup=False,
                        output_file="/tmp/{}".format(file_name), timeout=120)
                    pid_dict = {"handle": f11_hosts[index]["handle"], "pid": pid}
                    f11_pid_list.append(pid_dict)
                    fun_test.log("Starting {} LAT test, Server:{} <------> Client:{}".
                                 format(rt, f10_hosts[index]["name"], f11_hosts[index]["name"]))
                fun_test.sleep("Clients started for {} LAT test, size {}".format(rt, size), seconds=5)

                # First kill client then server
                for ids in f11_pid_list:
                    ids["handle"].kill_process(ids["pid"])
                    test_result = ids["handle"].command("sed 'x;$!d' < /tmp/{}".format(file_name))
                    result_line = re.findall(r'[\d.]+', test_result)
                    row_data_list = []
                    server_name = f10_hosts[index]["name"].replace("-", "_")
                    client_name = f11_hosts[index]["name"].replace("-", "_")
                    size_latency = result_line[0]
                    min_latency = result_line[2]
                    max_latency = result_line[3]
                    avg_latency = result_line[5]
                    latency_99 = result_line[7]
                    latency_99_99 = result_line[8]
                    for item in table_data_cols:
                        row_data_list.append(eval(item))
                    table_data_rows.append(row_data_list)

                    value_dict = {
                        "version": fun_test.get_version(),
                        "test": "IB_Write_Lat_Test",
                        "operation": "write",
                        "size_latency": size_latency,
                        "{}_avg_latency".format(rt): avg_latency,
                        "{}_min_latency".format(rt): min_latency,
                        "{}_max_latency".format(rt): max_latency,
                        "{}_99_latency".format(rt): latency_99,
                        "{}_99_99_latency".format(rt): latency_99_99,
                    }
                    add_to_data_base(value_dict)
                    table_data = {"headers": table_data_headers, "rows": table_data_rows}
                for ids in f10_pid_list:
                    ids["handle"].kill_process(ids["pid"])
            fun_test.add_table(panel_header="{} Table".format(ib_test), table_name=self.summary,
                               table_data=table_data)

        fun_test.log("Test done")

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(BringupSetup())
    ts.add_test_case(NicEmulation())
    ts.add_test_case(Rocebwtest())
    ts.add_test_case(Rocelattest())

    ts.run()
