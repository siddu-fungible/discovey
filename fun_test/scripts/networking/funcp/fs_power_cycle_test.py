from lib.system.fun_test import *
from lib.host import netperf_manager as nm
from scripts.networking.funcp.helper import *
from lib.topology.topology_helper import TopologyHelper
import json


class SetupBringup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
                    
                              """)

    def setup(self):
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        fs_spec = fun_test.get_asset_manager().get_fs_by_name(fs_name)
        # self.reboot_fpga(fs_spec['fpga']['mgmt_ip'])
        fun_test.sleep(message="Waiting for FS reboot", seconds=400)
        retry_count = 0
        while True:
            fpga_linux = Linux(host_ip=fs_spec['fpga']['mgmt_ip'], ssh_username='root', ssh_password="root")
            if fpga_linux.check_ssh():
                fpga_linux.disconnect()
                bmc_linux = Linux(host_ip=fs_spec['bmc']['mgmt_ip'], ssh_username='sysadmin', ssh_password="superuser")
                if bmc_linux.check_ssh():
                    bmc_linux.disconnect()
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
    def describe(self):
        self.set_test_details(id=1,
                              summary="Boot FunOS and reboot Hosts",
                              steps="""
                                   """)

    def setup(self):
        pass

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
