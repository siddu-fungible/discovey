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

        # self.reboot_fpga(fs_spec['fpga']['mgmt_ip'])

        # fun_test.sleep(message="Waiting for FS reboot", seconds=400)
        retry_count = 0
        while True:
            fpga_linux = Linux(host_ip=fs_spec['fpga']['mgmt_ip'], ssh_username='root', ssh_password="root")
            if fpga_linux.check_ssh():
                fpga_linux.disconnect()
                linux_home = Linux(host_ip="qa-ubuntu-02", ssh_username="auto_admin", ssh_password="fun123")
                if linux_home.ping(dst=fs_spec['bmc']['mgmt_ip']):
                    come_linux = Linux(host_ip=fs_spec['come']['mgmt_ip'], ssh_username='fun', ssh_password="123")
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
        linux_obj.command(command="ifconfig")


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
                         "retimer=0,1 --mgmt --disable-wu-watchdog syslog=2 workload=storage"
        f1_1_boot_args = "app=mdt_test,load_mods,hw_hsu_test cc_huid=2 --dpc-server --all_100g --serial --dpc-uart " \
                         "retimer=0,1 --mgmt --disable-wu-watchdog syslog=2 workload=storage"

        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                          1: {"boot_args": f1_1_boot_args}}
                                           )
        topology = topology_helper.deploy()
        fun_test.shared_variables["topology"] = topology
        fun_test.test_assert(topology, "Topology deployed")
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

        ping_dict = self.server_key["fs"][fs_name]["host_pings"]
        for host in ping_dict:
            test_host_pings(host=host, ips=ping_dict[host])
        fun_test.sleep(message="Wait for host to check ping again", seconds=30)
        # Ping hosts
        ping_dict = self.server_key["fs"][fs_name]["host_pings"]
        for host in ping_dict:
            test_host_pings(host=host, ips=ping_dict[host], strict=True)


class TestHostPCIeLanes(FunTestCase):
    def describe(self):
        self.set_test_details(id=2, summary="Test PCIe speeds for HU servers",
                              steps="""
                                      1. SSH into each host
                                      2. Check PCIe link
                                      3. Make sure PCIe link speed is correct
                                      """)

    def setup(self):
        pass

    def run(self):
        testbed_info = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() + '/testbed_inputs.json')
        test_bed_type = fun_test.get_job_environment_variable('test_bed_type')
        for fs_name in testbed_info['fs'][test_bed_type]["fs_list"]:
            server_key = fun_test.parse_file_to_json(
                fun_test.get_script_parent_directory() + '/fs_connected_servers.json')
            servers_mode = server_key["fs"][fs_name]
            for server in servers_mode:
                result = verify_host_pcie_link(hostname=server, mode=servers_mode[server], reboot=False)
                fun_test.test_assert(expression=(result == "1"), message="Make sure that PCIe links on host %s went up"
                                                                         % server)

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = SetupBringup()
    ts.add_test_case(BootF1())
    ts.add_test_case(TestHostPCIeLanes())
    ts.run()
