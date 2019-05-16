from lib.system.fun_test import *
from scripts.networking.nu_config_manager import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.utilities.funcp_config import *


class ScriptSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="1. Make sure correct FS system is selected")

    def setup(self):

        pass

    def cleanup(self):
        pass


class BringupBgp(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Bringup BGP on FS-45",
                              steps="""
                              1. BringUP both F1s
                              2. Bringup FunCP
                              3. Create MPG Interfacfes and get IPs using DHCP
                              4. Get MPG IPs
                              5. execute abstract config
                              """)

    def setup(self):

        pass

    def run(self):

        funcp_obj = FunControlPlaneBringup(fs_name="fs-7", boot_image_f1_0="funos-f1.stripped_15may_chhandak.gz",
                                           boot_image_f1_1="funos-f1.stripped_15may_chhandak.gz")
        funcp_obj.boot_both_f1(power_cycle_come=True)
        funcp_obj.bringup_funcp()
        funcp_obj.assign_mpg_ips()
        abstract_json_file = fun_test.get_script_parent_directory() + '/abstract_configs.json'
        funcp_obj.funcp_abstract_config(abstract_config_file=abstract_json_file)

    def cleanup(self):

        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(BringupBgp())
    ts.run()