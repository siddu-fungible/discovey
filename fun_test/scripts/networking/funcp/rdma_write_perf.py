from lib.system.fun_test import *
from lib.utilities.funcp_config import *
from scripts.networking.funcp.helper import *
from scripts.networking.funeth.sanity import Funeth
from lib.topology.topology_helper import TopologyHelper
from web.fun_test.analytics_models_helper import ModelHelper, get_data_collection_time
from fun_global import PerfUnit, FunPlatform


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
        fun_test.log("pass")
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

        # fs_name = "fs-45"
        funcp_obj = FunControlPlaneBringup(fs_name=self.server_key["fs"][fs_name]["fs-name"])
        funcp_obj.cleanup_funcp()
        servers_mode = self.server_key["fs"][fs_name]["hosts"]
        servers_list = []

        for server in servers_mode:
            print server
            critical_log(expression=rmmod_funeth_host(hostname=server), message="rmmod funeth on host")
            servers_list.append(server)

        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                          1: {"boot_args": f1_1_boot_args}}
                                           )
        topology = topology_helper.deploy()
        fun_test.shared_variables["topology"] = topology
        fun_test.test_assert(topology, "Topology deployed")
        fs = topology.get_dut_instance(index=0)
        come_obj = fs.get_come()
        come_obj.sudo_command("netplan apply")

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

        # funcp_obj.fetch_mpg_ips() #Only if not running the full script

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
        # ping_dict = self.server_key["fs"][fs_name]["cc_pings"]
        # for container in ping_dict:
        #     funcp_obj.test_cc_pings_remote_fs(dest_ips=ping_dict[container], docker_name=container)

        # Ping vlan to vlan
        funcp_obj.test_cc_pings_fs()
        # Check PICe Link on host
        servers_mode = self.server_key["fs"][fs_name]["hosts"]
        for server in servers_mode:
            result = verify_host_pcie_link(hostname=server, mode=servers_mode[server], reboot=False)
            fun_test.test_assert(expression=(result != "0"), message="Make sure that PCIe links on host %s went up"
                                                                     % server)
            if result == "2":
                fun_test.add_checkpoint("<b><font color='red'><PCIE link did not come up in %s mode</font></b>"
                                        % servers_mode[server])
        # install drivers on PCIE connected servers
        tb_config_obj = tb_configs.TBConfigs(str(fs_name))
        funeth_obj = Funeth(tb_config_obj)
        fun_test.shared_variables['funeth_obj'] = funeth_obj
        setup_hu_host(funeth_obj, update_driver=False, sriov=4, num_queues=1)

        # host_objs = fun_test.shared_variables["hosts_obj"]
        # for obj in host_objs:
        #     host_objs[obj][0].command("/home/localadmin/mks/update_rdma.sh update update")

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

    def cleanup(self):
        pass


class IBWriteBW(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=3,
                              summary="IB_Write_BW Test",
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
        host_obj = fun_test.shared_variables["hosts_obj"]

        # Load drivers on host
        for obj in host_obj:
            host_obj[obj][0].sudo_command("dmesg -c > /dev/null")
            check_module = host_obj[obj][0].lsmod("funrdma")
            if not check_module:
                host_obj[obj][0].sudo_command("insmod /mnt/ws/fungible-host-drivers/linux/kernel/funrdma.ko "
                                              "&& modprobe rdma_ucm")
                check_load_module = host_obj[obj][0].lsmod("funrdma")
                fun_test.test_assert(check_load_module, "Funrdma load")
                host_obj[obj][0].sudo_command("/etc/init.d/irqbalance stop")
                host_obj[obj][0].sudo_command("tuned-adm profile network-throughput")

        # Start ib_write_bw server on F1_0
        host_obj["f1_0"][0].command("export PATH=$PATH:/mnt/ws/fungible-rdma-core/build/bin/:/mnt/ws/fungible-perftest/"
                                    " && export LD_LIBRARY_PATH=/mnt/ws/fungible-rdma-core/build/lib/")
        host_obj["f1_0"][0].start_bg_process(command="sh -c 'for size in 1 128 256 512 1024 4096; "
                                                     "do ib_write_bw --report_gbits -F -d funrdma0 -s $size -D 180 -R;"
                                                     "sleep 2;done'",
                                             timeout=1400)
        server_interface_name = \
            host_obj["f1_0"][0].command("ip link ls up | awk '{print $2}' | grep -i \"00:f1:1d\" -B 1 |head -1|tr -d :")

        server_ip_address = \
            host_obj["f1_0"][0].command("ip addr list {} |grep \"inet \" |cut -d\' \' -f6|cut -d/ -f1".
                                        format(server_interface_name.rstrip()))

        # Start ib_write_bw client on F1_1
        host_obj["f1_1"][0].sudo_command("sudo rm -rf /tmp/*")
        host_obj["f1_1"][0].command(
            "export PATH=$PATH:/mnt/ws/fungible-rdma-core/build/bin/:/mnt/ws/fungible-perftest/ && "
            "export LD_LIBRARY_PATH=/mnt/ws/fungible-rdma-core/build/lib/")
        host_obj["f1_1"][0].command(
            "for size in 1 128 256 512 1024 4096;"
            "do ib_write_bw --report_gbits -F -d funrdma0 -s $size -D 180 -R {} >> /tmp/ib_bw_$size.txt;sleep 5;done".
            format(server_ip_address.rstrip()),
            timeout=1400)

        # host_obj["f1_1"][0].sudo_command("rmmod funrdma")
        # host_obj["f1_0"][0].sudo_command("rmmod funrdma")
        fun_test.sleep("Write BW test complete", 5)

        table_data_headers = ["Size in bytes", "Write_BW in Gbps", "Msg Rate in Mpps"]
        table_data_cols = ["size_bandwidth", "write_bandwidth", "write_msg_rate"]
        table_data_rows = []
        row_data_dict = {}

        test_results = \
            host_obj["f1_1"][0].command("for size in 1 128 256 512 1024 4096;"
                                        "do cat /tmp/ib_bw_$size.txt | grep -A2 -i bytes | sed 1d | sed '$d';done")

        for lines in test_results.rsplit("\n"):
            row_data_list = []
            line = lines.rsplit()
            size_bandwidth = line[0]
            iterations = line[1]
            bw_peak_gbps = line[2]
            write_bandwidth = line[3]
            write_msg_rate = line[4]
            for item in table_data_cols:
                row_data_list.append(eval(item))
            table_data_rows.append(row_data_list)

            value_dict = {
                "version": fun_test.get_version(),
                "test": "IB_Write_BW_Test",
                "operation": "write",
                "size_bandwidth": size_bandwidth,
                "write_bandwidth": write_bandwidth,
                "write_msg_rate": write_msg_rate
            }
            add_to_data_base(value_dict)

        # for i in table_data_cols:
        #     row_data_list.append(row_data_dict[i])

        table_data = {"headers": table_data_headers, "rows": table_data_rows}
        fun_test.add_table(panel_header="IB_Write_BW Table", table_name=self.summary,
                           table_data=table_data)

        table_data_rows.append(row_data_list)
        host_obj["f1_0"][0].disconnect()
        host_obj["f1_1"][0].disconnect()

        fun_test.log("Test done")

    def cleanup(self):
        pass


class IBWriteLat(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=4,
                              summary="IB_Write_Lat Test",
                              steps="""
                                  1. Load funrdma & rdma_ucm driver
                                  2. Start ib_write_lat test for different sizes
                                  """)

    def setup(self):

        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')

    def run(self):
        host_obj = fun_test.shared_variables["hosts_obj"]
        # Load drivers on host
        for obj in host_obj:
            host_obj[obj][0].sudo_command("dmesg -c > /dev/null")
            check_module = host_obj[obj][0].lsmod("funrdma")
            if not check_module:
                host_obj[obj][0].sudo_command("insmod /mnt/ws/fungible-host-drivers/linux/kernel/funrdma.ko "
                                              "&& modprobe rdma_ucm")
                host_obj[obj][0].sudo_command("tuned-adm profile network-throughput")

        # Start ib_write_bw server on F1_0 host
        host_obj["f1_0"][0].command("export PATH=$PATH:/mnt/ws/fungible-rdma-core/build/bin/:/mnt/ws/fungible-perftest/"
                                    " && export LD_LIBRARY_PATH=/mnt/ws/fungible-rdma-core/build/lib/")
        host_obj["f1_0"][0].start_bg_process(command="sh -c 'for size in 1 128 256 512 1024 4096;"
                                                     "do ib_write_lat -I 64 -F -d funrdma0 -s $size -n 100000 -R;"
                                                     "sleep 2;done'",
                                             timeout=500)
        server_interface_name = host_obj["f1_0"][0].command(
            "ip link ls up | awk '{print $2}' | grep -i \"00:f1:1d\" -B 1 |head -1|tr -d :")

        server_ip_address = host_obj["f1_0"][0].command(
            "ip addr list {} |grep \"inet \" |cut -d\' \' -f6|cut -d/ -f1".format(server_interface_name.rstrip()))

        # Start ib_write_bw client on F1_1 host
        host_obj["f1_1"][0].sudo_command("sudo rm -rf /tmp/*")
        host_obj["f1_1"][0].command(
            "export PATH=$PATH:/mnt/ws/fungible-rdma-core/build/bin/:/mnt/ws/fungible-perftest/ && "
            "export LD_LIBRARY_PATH=/mnt/ws/fungible-rdma-core/build/lib/")
        host_obj["f1_1"][0].command(
            "for size in 1 128 256 512 1024 4096;"
            "do ib_write_lat -I 64 -F -d funrdma0 -s $size -n 100000 -R {} >> /tmp/ib_lat_$size.txt;sleep 5;done".
            format(server_ip_address.rstrip()),
            timeout=500)

        host_obj["f1_1"][0].sudo_command("rmmod funrdma")
        host_obj["f1_0"][0].sudo_command("rmmod funrdma")
        fun_test.sleep("Write BW test complete", 5)

        table_data_headers = ["Size in bytes", "t_min[usec]", "t_max[usec]", "t_avg[usec]", "99%[usec]", "99.9%[usec]"]
        table_data_cols = ["size_latency", "write_min_latency", "write_max_latency", "write_avg_latency",
                           "write_99_latency", "write_99_99_latency"]
        table_data_rows = []
        row_data_dict = {}

        test_results = \
            host_obj["f1_1"][0].command("for size in 1 128 256 512 1024 4096;"
                                        "do cat /tmp/ib_lat_$size.txt | grep -A2 -i bytes | sed 1d | sed '$d';done")

        for lines in test_results.rsplit("\n"):
            row_data_list = []
            line = lines.rsplit()
            size_latency = line[0]
            write_min_latency = line[2]
            write_max_latency = line[3]
            write_avg_latency = line[5]
            write_99_latency = line[7]
            write_99_99_latency = line[8]
            for item in table_data_cols:
                row_data_list.append(eval(item))
            table_data_rows.append(row_data_list)

            value_dict = {
                "version": fun_test.get_version(),
                "test": "IB_Write_Lat_Test",
                "operation": "write",
                "size_latency": size_latency,
                "write_avg_latency": write_avg_latency,
                "write_min_latency": write_min_latency,
                "write_max_latency": write_max_latency,
                "write_99_latency": write_99_latency,
                "write_99_99_latency": write_99_99_latency,
            }
            add_to_data_base(value_dict)

        # for i in table_data_cols:
        #     row_data_list.append(row_data_dict[i])

        table_data = {"headers": table_data_headers, "rows": table_data_rows}
        fun_test.add_table(panel_header="IB_Write_Lat Table", table_name=self.summary,
                           table_data=table_data)

        table_data_rows.append(row_data_list)
        host_obj["f1_0"][0].disconnect()
        host_obj["f1_1"][0].disconnect()

        fun_test.log("Test done")

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(BringupSetup())
    ts.add_test_case(NicEmulation())
    ts.add_test_case(IBWriteBW())
    ts.add_test_case(IBWriteLat())

    ts.run()
