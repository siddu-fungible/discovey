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


class VerifySetup(FunTestCase):
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
        funcp_obj = FunControlPlaneBringup(fs_name="fs-48", boot_image_f1_0="funos-f1.stripped_vdd_en2.gz",
                                           boot_image_f1_1="funos-f1.stripped_vdd_en2.gz",
                                           boot_args_f1_0="app=mdt_test,hw_hsu_test cc_huid=3 --all_100g --dpc-server "
                                                          "--serial --dpc-uart --dis-stats retimer=0,1,2 --mgmt",
                                           boot_args_f1_1="app=mdt_test,hw_hsu_test cc_huid=2 --all_100g --dpc-server "
                                                          "--serial --dpc-uart --dis-stats retimer=0 --mgmt")
        t_end = time.time() + 60 * 120
        server05 = 0
        server05_fails = 0
        server05_incorrect = 0
        server06 = 0
        server06_fails = 0
        server06_incorrect = 0
        server07 = 0
        server07_fails = 0
        server07_incorrect = 0
        server08 = 0
        server08_fails = 0
        server08_incorrect = 0

        while time.time() < t_end:

            fun_test.test_assert(expression=funcp_obj.boot_both_f1(power_cycle_come=True, reboot_come=False), message="Boot F1s")
            s05 = verify_host_pcie_link(hostname="cab03-qa-05")
            if s05 == "1":
                server05 += 1
            elif s05 == "0":
                server05_fails += 1
            elif s05 == "2":
                server05_incorrect += 1
            s06 = verify_host_pcie_link(hostname="cab03-qa-06")
            if s06 == "1":
                server06 += 1
            elif s06 == "0":
                server06_fails += 1
            elif s06 == "2":
                server06_incorrect += 1
            s07 = verify_host_pcie_link(hostname="cab03-qa-07", username="localadmin", password="Precious1*", mode="x8")
            if s07 == "1":
                server07 += 1
            elif s07 == "0":
                server07_fails += 1
            elif s07 == "2":
                server07_incorrect += 1
            s08 = verify_host_pcie_link(hostname="cab03-qa-08")
            if s08 == "1":
                server08 += 1
            elif s07 == "0":
                server08_fails += 1
            elif s07 == "2":
                server08_incorrect += 1
            fun_test.log("Server 05 success : %s | Incomplete : %s | Failures : %s"
                         % (server05, server05_incorrect, server05_fails))
            fun_test.log("Server 06 success : %s | Incomplete : %s | Failures : %s"
                         % (server06, server06_incorrect, server06_fails))
            fun_test.log("Server 07 success : %s | Incomplete : %s | Failures : %s"
                         % (server07, server07_incorrect, server07_fails))
            fun_test.log("Server 08 success : %s | Incomplete : %s | Failures : %s"
                         % (server08, server08_incorrect, server08_fails))

    def cleanup(self):

        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(VerifySetup())
    ts.run()