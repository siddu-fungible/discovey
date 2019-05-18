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
                              summary="Bringup BGP on FS-45",
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
        funcp_obj = FunControlPlaneBringup(fs_name="fs-15", boot_image_f1_0="funos-f1.stripped_vdd_en2.gz",
                                           boot_image_f1_1="funos-f1.stripped_vdd_en2.gz",
                                           boot_args_f1_0="app=mdt_test,hw_hsu_test cc_huid=3 --all_100g --dpc-server "
                                                          "--serial --dpc-uart --dis-stats",#retimer=0,1,2 --mgmt
                                           boot_args_f1_1="app=mdt_test,hw_hsu_test cc_huid=2 --all_100g --dpc-server "
                                                          "--serial --dpc-uart --dis-stats")#retimer=0 --mgmt
        fun_test.test_assert(expression=funcp_obj.boot_both_f1(power_cycle_come=True), message="Boot F1s")
        # funcp_obj.prepare_come_for_control_plane()
        fun_test.test_assert(expression=funcp_obj.bringup_funcp(prepare_docker=False), message="Bringup FunCP")
        funcp_obj.assign_mpg_ips()
        abstract_json_file0 = fun_test.get_script_parent_directory() + '/alibaba_bmv_configs_f1_0.json'
        abstract_json_file1 = fun_test.get_script_parent_directory() + '/alibaba_bmv_configs_f1_1.json'
        funcp_obj.funcp_abstract_config(abstract_config_f1_0=abstract_json_file0,
                                        abstract_config_f1_1=abstract_json_file1)

        tb_config_obj = tb_configs.TBConfigs("FS45")
        funeth_obj = Funeth(tb_config_obj)
        fun_test.shared_variables['funeth_obj'] = funeth_obj

        # HU host
        setup_hu_host(funeth_obj, update_driver=True)

    def cleanup(self):

        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(BringupSetup())
    # ts.add_test_case(SetupVMs)
    ts.run()