from lib.system.fun_test import *
from scripts.networking.nu_config_manager import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.utilities.funcp_config import *
from scripts.networking.funeth.funeth import Funeth
from scripts.networking.tb_configs import tb_configs
import pprint

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
        fs_name="fs-45"
        funcp_obj = FunControlPlaneBringup(fs_name=fs_name, boot_image_f1_0="ysingh/funos-f1.stripped_18may_pcie_test.gz",
                                           boot_image_f1_1="ysingh/funos-f1.stripped_18may_pcie_test.gz",
                                           boot_args_f1_0="app=mdt_test,hw_hsu_test cc_huid=3 --all_100g --dpc-server "
                                                          "--serial --dpc-uart --dis-stats retimer=0 --mgmt",
                                           boot_args_f1_1="app=mdt_test,hw_hsu_test cc_huid=2 --all_100g --dpc-server "
                                                          "--serial --dpc-uart --dis-stats retimer=3 --mgmt")
        t_end = time.time() + 60 * 120

        server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() + '/fs_connected_servers.json')
        servers_mode = server_key["fs"][fs_name]
        final_result = {}
        for server in servers_mode:
            final_result[server] = {"success": 0, "incomplete": 0, "failure": 0}
        while time.time() < t_end:
            fun_test.test_assert(expression=funcp_obj.boot_both_f1(power_cycle_come=False, reboot_come=False),
                                 message="Boot F1s")
            for server in servers_mode:
                print server
                result = self.verify_host_pcie_link(hostname=server, mode=servers_mode[server])
                if result == "1":
                    final_result[server]["success"] += 1
                if result == "0":
                    final_result[server]["failure"] += 1
                if result == "2":
                    final_result[server]["incomplete"] += 1

            print("#####################################################################################")
            fun_test.log(final_result)
            pprint.pprint(final_result)
            print("#####################################################################################")

    def cleanup(self):

        pass

    def verify_host_pcie_link(self, hostname, username="localadmin", password="Precious1*", mode="x16", reboot=True):
        linux_obj = Linux(host_ip=hostname, ssh_username=username, ssh_password=password)
        if reboot:
            linux_obj.reboot()
            count = 0
            while not linux_obj.check_ssh():
                fun_test.sleep(message="waiting for server to come back up", seconds=15)
                count += 1
                if count == 5:
                    fun_test.test_assert(expression=False, message="Cant reboot server %s" % hostname)
        else:
            count = 0
            while not linux_obj.check_ssh():
                fun_test.sleep(message="waiting for server to come back up", seconds=30)
                count += 1
                if count == 5:
                    fun_test.test_assert(expression=False, message="Cant reach server %s" % hostname)

        lspci_out = linux_obj.sudo_command(command="sudo lspci -d 1dad: -vv | grep LnkSta")
        result = "1"
        if mode not in lspci_out:
            if "LnkSta" not in lspci_out:
                fun_test.critical("PCIE link did not come up")
                result = "0"
            else:
                fun_test.critical("PCIE link did not come up in %s mode" % mode)
                result = "2"
        return result


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(VerifySetup())
    ts.run()
