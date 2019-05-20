from lib.system.fun_test import *
from scripts.networking.nu_config_manager import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.utilities.funcp_config import *

fs = "fs-11"
image = "funos-f1.stripped.gz.gliang"
boot_args = "app=hw_hsu_test retimer=0,1 --dpc-uart --dpc-server --csr-replay --all_100g"
boot_args_f1_0 = "app=hw_hsu_test cc_huid=3 sku=SKU_FS1600_0 retimer=0,1 --csr-replay --all_100g --dpc-server --dpc-uart "
boot_args_f1_1 = "app=hw_hsu_test cc_huid=2 sku=SKU_FS1600_1 retimer=0,1 --csr-replay --all_100g --dpc-server --dpc-uart "

class ScriptSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="1. Make sure correct FS system is selected")

    def setup(self):

        pass

    def cleanup(self):
        pass


class BringupFS(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Bringup FS-11",
                              steps="""
                              1. BringUP both F1s
                              """)

    def setup(self):
        pass

    def run(self):
        funcp_obj = FunControlPlaneBringup(fs_name=fs,
                                           boot_image_f1_0=image,
                                           boot_image_f1_1=image,
                                           boot_args_f1_0=boot_args_f1_0,
                                           boot_args_f1_1=boot_args_f1_1)
        funcp_obj.boot_both_f1(power_cycle_come=True)
        #funcp_obj.bringup_funcp()
        #funcp_obj.assign_mpg_ips()
        #abstract_json_file = fun_test.get_script_parent_directory() + '/abstract_configs.json'
        #funcp_obj.funcp_abstract_config(abstract_config_file=abstract_json_file)

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(BringupFS())
    ts.run()