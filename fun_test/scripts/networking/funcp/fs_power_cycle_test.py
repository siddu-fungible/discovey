from lib.system.fun_test import *
from scripts.networking.nu_config_manager import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.utilities.funcp_config import *
from scripts.networking.tb_configs import tb_configs
from scripts.networking.funcp.helper import *
from scripts.networking.funeth.sanity import Funeth
from lib.host.storage_controller import StorageController
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
import json
from scripts.networking.funcp.ali_bmv_storage_sanity import *


class SetupBringup(FunTestScript):
    server_key = {}

    def describe(self):
        self.set_test_details(steps="""
                    
                              """)

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                 '/ali_bmv_storage_sanity.json')
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        fs_spec = fun_test.get_asset_manager().get_fs_by_name(str(self.server_key["fs"][fs_name]["fs-name"]))
        servers_mode = self.server_key["fs"][fs_name]["hosts"]
        servers_list = []

        for server in servers_mode:
            print server
            critical_log(expression=rmmod_funeth_host(hostname=server), message="rmmod funeth on host")
            servers_list.append(server)
        print(servers_list)

        self.reboot_fpga(fs_spec['fpga']['mgmt_ip'])

        come_linux = Linux(host_ip=fs_spec['come']['mgmt_ip'], ssh_username='fun', ssh_password="123")
        come_linux.ensure_host_is_up(max_wait_time=300, power_cycle=False)

        retry_count = 0
        while True:
            fpga_linux = Linux(host_ip=fs_spec['fpga']['mgmt_ip'], ssh_username='root', ssh_password="root")
            if fpga_linux.check_ssh():
                fpga_linux.disconnect()
                linux_home = Linux(host_ip="qa-ubuntu-02", ssh_username="auto_admin", ssh_password="fun123")
                if linux_home.ping(dst=fs_spec['bmc']['mgmt_ip']):
                    if come_linux.check_ssh():
                        come_linux.disconnect()
                        break
            retry_count += 1
            fun_test.sleep(message="Waiting for FS reboot", seconds=30)
            if retry_count > 20:
                fun_test.test_assert(message="Can't reach FS components", expression=False)

    def cleanup(self):
        pass

    def reboot_fpga(self, fpga_ip):
        linux_obj = Linux(host_ip=fpga_ip, ssh_username='root', ssh_password='root')
        linux_obj.reboot(max_wait_time=240)


class BootF1(FunTestCase):
    server_key = {}

    def describe(self):

        self.set_test_details(id=1,
                              summary="Boot FunOS and reboot Hosts, bringup FunCP and bringup hosts with Funeth",
                              steps="""
                                   """)

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/ali_bmv_storage_sanity.json')

    def cleanup(self):
        pass

    def run(self):
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        f1_0_boot_args = "app=mdt_test,load_mods,hw_hsu_test cc_huid=3 --dpc-server --all_100g --serial --dpc-uart " \
                         "retimer=0,1 --mgmt --disable-wu-watchdog syslog=6 workload=storage"
        f1_1_boot_args = "app=mdt_test,load_mods,hw_hsu_test cc_huid=2 --dpc-server --all_100g --serial --dpc-uart " \
                         "retimer=0,1 --mgmt --disable-wu-watchdog syslog=6 workload=storage"

        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                          1: {"boot_args": f1_1_boot_args}}
                                           )
        topology = topology_helper.deploy()
        fun_test.shared_variables["topology"] = topology
        fun_test.test_assert(topology, "Topology deployed")

        # Check SSD link & count
        match_strings = "Gen3x4|Gen3x2|backend: 4 devices up"
        for f1index in 0, 1:
            uart_path = topology.get_dut_instance(index=0).get_uart_log_file(f1_index=f1index)
            uart_content = os.popen("cat %s" % uart_path).read()
            match_str_list = re.findall(r'{}'.format(match_strings), uart_content, re.IGNORECASE)
            gen3x4_count = match_str_list.count("Gen3x4")
            gen3x2_count = match_str_list.count("Gen3x2")
            backend_vol = match_str_list.count("backend: 4 devices up")
            fun_test.log_section("SSD Details on F1_{}".format(f1index))
            fun_test.log("SSD in Gen3x4 : {}".format(gen3x4_count))
            fun_test.log("SSD in Gen3x2 : {}".format(gen3x2_count))
            if backend_vol != 1:
                fun_test.critical("Error in volume count detected by FunOS")
            for line in uart_content.split("\n"):
                if "INFO volume_manager \"backend:" in line:
                    if "devices up" in line:
                        backend_dev = line.split("backend:", 1)[1]
                        count = re.findall("\d+", backend_dev)
                        # count = re.search(r'backend:\s+(?P<count>\d+)', line)
                        fun_test.add_checkpoint(checkpoint="Backend devices up", expected=4, actual=int(count[0]))
                    elif "devices are already up" in line:
                        backend_dev = line.split("backend:", 1)[1]
                        count = re.findall("\d+", backend_dev)
                        fun_test.add_checkpoint(checkpoint="Backend devices already up",
                                                expected=4, actual=int(count[0]))
            if gen3x4_count == 8:
                fun_test.add_checkpoint("Gen3x4 SSD count on F1_{}".format(f1index),
                                        "PASSED", expected=8, actual=gen3x4_count)
            else:
                fun_test.add_checkpoint("Gen3x4 SSD count on F1_{}".format(f1index),
                                        "FAILED", expected=8, actual=gen3x4_count)
            if gen3x2_count == 0:
                fun_test.add_checkpoint("Gen3x2 SSD count on F1_{}".format(f1index),
                                        "PASSED", expected=0, actual=gen3x2_count)
            else:
                fun_test.add_checkpoint("Gen3x2 SSD count on F1_{}".format(f1index),
                                        "FAILED", expected=0, actual=gen3x2_count)

        funcp_obj = FunControlPlaneBringup(fs_name=self.server_key["fs"][fs_name]["fs-name"])
        fun_test.test_assert(expression=funcp_obj.bringup_funcp(prepare_docker=False), message="Bringup FunCP")
        funcp_obj.assign_mpg_ips(static=self.server_key["fs"][fs_name]["mpg_ips"]["static"],
                                 f1_1_mpg=self.server_key["fs"][fs_name]["mpg_ips"]["mpg1"],
                                 f1_0_mpg=self.server_key["fs"][fs_name]["mpg_ips"]["mpg0"])
        abstract_json_file0 = fun_test.get_script_parent_directory() + '/abstract_config/' + \
                              self.server_key["fs"][fs_name]["abstract_configs"]["F1-0"]
        abstract_json_file1 = fun_test.get_script_parent_directory() + '/abstract_config/' + \
                              self.server_key["fs"][fs_name]["abstract_configs"]["F1-1"]

        funcp_obj.funcp_abstract_config(abstract_config_f1_0=abstract_json_file0,
                                        abstract_config_f1_1=abstract_json_file1, workspace="/scratch")
        funcp_obj.add_routes_on_f1(routes_dict=self.server_key["fs"][fs_name]["static_routes"])
        fun_test.sleep(message="Waiting before ping tests", seconds=10)
        funcp_obj.test_cc_pings_fs()
        
        tb_file = str(fs_name)
        if fs_name == "fs-alibaba-demo":
            tb_file = "FS45"
        tb_config_obj = tb_configs.TBConfigs(tb_file)
        funeth_obj = Funeth(tb_config_obj)
        fun_test.shared_variables['funeth_obj'] = funeth_obj
        setup_hu_host(funeth_obj, update_driver=True, sriov=4, num_queues=1)


class PingTest(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=4, summary="Test PCIe speeds for HU servers",
                              steps="""
                                      1. SSH into each host
                                      2. Check PCIe link
                                      3. Make sure PCIe link speed is correct
                                      """)

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/ali_bmv_storage_sanity.json')

    def run(self):
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        topology = fun_test.shared_variables["topology"]
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        fs_spec = fun_test.get_asset_manager().get_fs_by_name(str(self.server_key["fs"][fs_name]["fs-name"]))
        print("\n================================")
        print("F1_0 DPC Stats")
        print("================================\n")
        network_controller_obj = NetworkController(dpc_server_ip=fs_spec['come']['mgmt_ip'],
                                                   dpc_server_port=40220)
        network_controller_obj.peek_fpg_port_stats(port_num=0)
        network_controller_obj.peek_fpg_port_stats(port_num=4)
        network_controller_obj.port_link_status()
        network_controller_obj.disconnect()
        print("\n================================")
        print("F1_1 DPC Stats")
        print("================================\n")

        network_controller_obj = NetworkController(dpc_server_ip=fs_spec['come']['mgmt_ip'],
                                                   dpc_server_port=40221)
        network_controller_obj.peek_fpg_port_stats(port_num=0)
        network_controller_obj.peek_fpg_port_stats(port_num=4)
        network_controller_obj.port_link_status()
        network_controller_obj.disconnect()
        # Ping hosts
        ping_dict = self.server_key["fs"][fs_name]["host_pings"]
        for host in ping_dict:
            test_host_pings(host=host, ips=ping_dict[host], ping_count=1000, ping_interval=0.1, strict=True)
        fun_test.sleep(message="Wait for host to check ping again", seconds=30)


    def cleanup(self):
        pass


class TestHostPCIeLanes(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=2, summary="Test PCIe speeds for HU servers",
                              steps="""
                                      1. SSH into each host
                                      2. Check PCIe link
                                      3. Make sure PCIe link speed is correct
                                      """)

    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/ali_bmv_storage_sanity.json')

    def run(self):
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        servers_mode = self.server_key["fs"][fs_name]["hosts"]
        for server in servers_mode:
            result = verify_host_pcie_link(hostname=server, mode=servers_mode[server], reboot=False)
            fun_test.test_assert(expression=(result == "1"), message="Make sure that PCIe links on host %s went up"
                                                                         % server)

    def cleanup(self):
        pass


class LocalSSDTest(StorageConfiguration):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Run fio traffic on locally attached SSD",
                              steps="""
                                      1. Create BLT volume
                                      2. Create PCI controller
                                      3. Attach volume to the controller
                                      4. Check if nvme device is present on host
                                      5. Run fio write
                                      6. Run fio read
                                      """)

    def setup(self):
        config = "LocalSSDTest"
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        if fs_name == 'fs-66':
            config = "LocalSSDTestFS66"
            self.__class__.__name__ = "LocalSSDTestFS66"
        super(LocalSSDTest, self).setup(config)

    def run(self):
        self.vol_type = "PCI"
        self.ctrl_type = "PCI"
        self.vol_attach_type = "local"
        self.storage_controller = StorageController(target_ip=self.come_ip, target_port=self.dpc_p0)
        # Revert syslog to 3
        command_result = self.storage_controller.poke("params/syslog/level 3")
        fun_test.test_assert(command_result["status"], "Setting syslog level to 3")
        self.dpu = 0
        super(LocalSSDTest, self).run()
        server = self.storage_config['server']
        i = 0
        for host in server:
            self.host = Linux(host_ip=server[i], ssh_username=self.uname, ssh_password=self.pwd)
            self.host.command("sudo nvme list")
            device = self.host.command("sudo nvme list | grep nvme | sed -n 1p | awk {'print $1'}").strip()
            fun_test.test_assert(device, message="nvme device visible on host")
            i += 1

        self.storage_controller = StorageController(target_ip=self.come_ip, target_port=self.dpc_p1)
        # Revert syslog to 3
        command_result = self.storage_controller.poke("params/syslog/level 3")
        fun_test.test_assert(command_result["status"], "Setting syslog level to 3")
        self.dpu = 1
        super(LocalSSDTest, self).run()
        server = self.storage_config['server_f1']
        i = 0
        for host in server:
            self.host = Linux(host_ip=server[i], ssh_username=self.uname, ssh_password=self.pwd)
            self.host.command("sudo nvme list")
            device = self.host.command("sudo nvme list | grep nvme | sed -n 1p | awk {'print $1'}").strip()
            fun_test.test_assert(device, message="nvme device visible on host")
            i += 1

        def runfio(arg1, device):
            for rw_mode in self.mode:
                op = arg1.command(command="cd ~; pwd").strip()
                job_file = op+"/mks/fio_{}_jf.txt".format(rw_mode)
                result = arg1.sudo_command("fio {}".format(job_file), timeout=30000)
                if "bad bits" in result.lower() or "verify failed" in result.lower():
                    fun_test.critical(False, "Data verification failed for {} test".format(rw_mode))
            arg1.disconnect()
        # def runfio(arg1, device):
        #     for rw_mode in self.mode:
        #         hostname = arg1.command("hostname")
        #         fio_result = arg1.pcie_fio(filename=device, rw=rw_mode,
        #                                    numjobs=self.num_jobs,
        #                                    iodepth=self.iodepth,
        #                                    name="fio_" + str(rw_mode),
        #                                    runtime=300,
        #                                    prio=0,
        #                                    direct=1,
        #                                    timeout=460)
        #         fun_test.test_assert(fio_result, "Fio {} test on {}".format(rw_mode, hostname))
        #         arg1.disconnect()

        threads_list = []
        hosts = self.storage_config['io_servers']
        print(hosts)
        for servers in hosts:
            self.host = Linux(host_ip=servers, ssh_username=self.uname, ssh_password=self.pwd)
            device = self.host.command("sudo nvme list -o normal | awk -F ' ' '{print $1}' | grep -i nvme0").\
                replace("\r", '')
            device_list = device.replace("\n", ":").rstrip(":")
            thread_id = fun_test.execute_thread_after(time_in_seconds=2, func=runfio,
                                                      arg1=self.host, device=device_list)
            fun_test.sleep("Threadzz started", 2)
            threads_list.append(thread_id)

        fun_test.sleep("Sleeping between thread join...", seconds=10)
        for thread_id in threads_list:
            fun_test.join_thread(fun_test_thread_id=thread_id, sleep_time=1)

        # self.storage_controller.disconnect()

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = SetupBringup()
    ts.add_test_case(BootF1())
    ts.add_test_case(TestHostPCIeLanes())
    ts.add_test_case(LocalSSDTest())
    ts.add_test_case(PingTest())
    ts.run()
