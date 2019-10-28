from lib.system.fun_test import *
from scripts.networking.nu_config_manager import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.utilities.funcp_config import *
from scripts.networking.funeth.funeth import Funeth
from scripts.networking.tb_configs import tb_configs
from scripts.networking.funcp.helper import *
from lib.host.linux import Linux
from lib.topology.topology_helper import TopologyHelper
import time
import datetime

CHECK_HPING3_ON_HOSTS = True


def clean_testbed(fs_name, hu_host_list):
    funcp_obj = FunControlPlaneBringup(fs_name=fs_name)
    funcp_obj.cleanup_funcp()
    for server in hu_host_list:
        critical_log(expression=rmmod_funeth_host(hostname=server), message="rmmod funeth on host")


class FunCPSetup:

    def __init__(self, f1_0_mpg, f1_1_mpg, test_bed_type, abstract_config_f1_0, abstract_config_f1_1,
                 update_funcp=False):
        self.funcp_obj = FunControlPlaneBringup(fs_name=test_bed_type)
        self.update_funcp = update_funcp
        self.f1_0_mpg = f1_0_mpg
        self.f1_1_mpg = f1_1_mpg
        self.abstract_config_f1_0 = abstract_config_f1_0
        self.abstract_config_f1_1 = abstract_config_f1_1

    def bringup(self, fs):
        self.funcp_obj.bringup_funcp(prepare_docker=self.update_funcp)
        self.funcp_obj.assign_mpg_ips(static=True, f1_1_mpg=self.f1_1_mpg, f1_0_mpg=self.f1_0_mpg,
                                      f1_0_mpg_netmask="255.255.255.0",
                                      f1_1_mpg_netmask="255.255.255.0"
                                      )
        self.funcp_obj.funcp_abstract_config(abstract_config_f1_0=self.abstract_config_f1_0,
                                             abstract_config_f1_1=self.abstract_config_f1_1)


class ScriptSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
                              1. BringUP both F1s
                              2. Bringup FunCP
                              3. Create MPG Interfacfes and get IPs using DHCP
                              4. Get MPG IPs
                              5. execute abstract config for both F1
                              """)

    def setup(self):
        global funcp_obj, servers_list, test_bed_type
        testbed_info = fun_test.parse_file_to_json(
            fun_test.get_script_parent_directory() + '/testbed_inputs.json')
        test_bed_type = fun_test.get_job_environment_variable('test_bed_type')
        fun_test.shared_variables["test_bed_type"] = test_bed_type
        fun_test.shared_variables['testbed_info'] = testbed_info
        fun_test.shared_variables["pcie_host_result"] = True

        tb_config_obj = tb_configs.TBConfigs(test_bed_type)
        funeth_obj = Funeth(tb_config_obj)
        fun_test.shared_variables['funeth_obj'] = funeth_obj
        setup_hu_host(funeth_obj, update_driver=True, num_queues=4)

    def cleanup(self):
        fun_test.log("Cleanup")
        fun_test.shared_variables["topology"].cleanup()


class TestHostPCIeLanes(FunTestCase):
    def describe(self):
        self.set_test_details(id=6, summary="Test PCIe speeds for HU servers",
                              steps="""
                                      1. SSH into each host
                                      2. Check PCIe link
                                      3. Make sure PCIe link speed is correct
                                      """)

    def setup(self):
        pass

    def check_pcie_link_speed(self, hostname, link_speed, username="localadmin", password="Precious1*"):
        try:
            result = True
            linux_obj = Linux(host_ip=hostname, ssh_username=username, ssh_password=password)
            lspci_out = linux_obj.sudo_command(command="sudo lspci -d 1dad: -vv | grep LnkSta")
            output = linux_obj.command('lspci -d 1dad:')
            link_check = re.search(r'Ethernet controller: (?:Device 1dad:00f1|Fungible Device 00f1)', output)
            fun_test.test_assert(expression=link_check, message="Fungible Ethernet PFs on host %s" % hostname)
            result &= bool(link_check)
            if link_speed not in lspci_out:
                if "LnkSta" not in lspci_out:
                    fun_test.test_assert(expression=False, message="PCIE link did not come up on Host %s" % hostname)
                else:
                    fun_test.test_assert(expression=False,
                                         message="PCIE link did not come up in %s mode on Host %s" % (link_speed,
                                                                                                      hostname))
                result &= False
            result &= fun_test.shared_variables["pcie_host_result"]
            fun_test.shared_variables["pcie_host_result"] = result
        except Exception as e:
            fun_test.log("==================")
            fun_test.log("Exception occurred")
            fun_test.log("==================")
            fun_test.critical(e)
            fun_test.shared_variables["pcie_host_result"] &= False

    def run(self):

        pass

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(TestHostPCIeLanes())
    ts.run()