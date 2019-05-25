from lib.system.fun_test import *
from scripts.networking.nu_config_manager import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.utilities.funcp_config import *
from scripts.networking.funeth.funeth import Funeth
from scripts.networking.tb_configs import tb_configs
from scripts.networking.funcp.helper import *

class ScriptSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="1. Make sure correct FS system is selected")

    def setup(self):

        pass

    def cleanup(self):
        pass


class BringupSetup(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Bringup FCP Setup",
                              steps="""
                              1. BringUP both F1s
                              2. Bringup FunCP
                              3. Create MPG Interfacfes and get IPs using DHCP
                              4. Get MPG IPs
                              5. execute abstract config for both F1
                              """)

    def setup(self):

        pass

    def run(self):
        #funos-f1.stripped_vdd_en2.gz
        #cmukherjee/funos-f1.stripped.gz
        # Working FunCP - cmukherjee/funos-f1.stripped.gz
        testbed_info=fun_test.parse_file_to_json(fun_test.get_script_parent_directory() + '/alibaba_fcp_testbed.json')
        for fs_name  in testbed_info['fs']:
            funcp_obj = FunControlPlaneBringup(fs_name=fs_name, boot_image_f1_0=testbed_info['fs'][fs_name]['boot_image_f1_0'],
                                               boot_image_f1_1=testbed_info['fs'][fs_name]['boot_image_f1_1'],
                                               boot_args_f1_0="app=mdt_test,hw_hsu_test cc_huid=3 --all_100g --dpc-server "
                                                              "--serial --dpc-uart --dis-stats retimer=0,1,2 --mgmt",
                                               boot_args_f1_1="app=mdt_test,hw_hsu_test cc_huid=2 --all_100g --dpc-server "
                                                              "--serial --dpc-uart --dis-stats retimer=0 --mgmt")
            #Boot both F1s and reboot COMe

            fun_test.test_assert(expression=funcp_obj.boot_both_f1(power_cycle_come=True, gatewayip=testbed_info['fs'][fs_name]['gatewayip']),
                                 message="Boot F1s")

            # Bringup FunCP
            fun_test.test_assert(expression=funcp_obj.bringup_funcp(prepare_docker=testbed_info['fs'][fs_name]['prepare_docker']), message="Bringup FunCP")

            #reboot PCIe connected servers and verify PCIe connections

            server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() + '/fs_connected_servers.json')
            servers_mode = server_key["fs"][fs_name]
            for server in servers_mode:
                print server
                result = verify_host_pcie_link(hostname=server, mode=servers_mode[server], reboot=False)
                # fun_test.test_assert(expression=(result != "0"), message="Make sure that PCIe links on host %s went up"
                #                                                          % server)

            # install drivers on PCIE connected servers
            tb_config_obj = tb_configs.TBConfigs(str('FS'+ item.split('-')[1]))
            funeth_obj = Funeth(tb_config_obj)
            fun_test.shared_variables['funeth_obj'] = funeth_obj
            setup_hu_host(funeth_obj, update_driver=True)
            # funcp_obj.prepare_come_for_control_plane()

            # Assign MPG IPs from dhcp
            funcp_obj.assign_mpg_ips_dhcp()
            # funcp_obj.fetch_mpg_ips() #Only if not running the full script
            #execute abstract file

            abstract_json_file0 = fun_test.get_script_parent_directory() + testbed_info['fs'][fs_name]['abtract_config_f1_0']
            abstract_json_file1 = fun_test.get_script_parent_directory() + testbed_info['fs'][fs_name]['abtract_config_f1_0']
            funcp_obj.funcp_abstract_config(abstract_config_f1_0=abstract_json_file0,
                                            abstract_config_f1_1=abstract_json_file1)


        


    def cleanup(self):

        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(BringupSetup())
    # ts.add_test_case(SetupVMs)
    ts.run()
