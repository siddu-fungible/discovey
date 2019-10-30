from lib.system.fun_test import *
from scripts.networking.nu_config_manager import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from scripts.networking.tb_configs import tb_configs

from lib.utilities.funcp_config import *
from scripts.networking.funcp.helper import *
from lib.topology.topology_helper import TopologyHelper


class ScriptSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="1. Make sure correct FS system is selected")

    def setup(self):
        fs_name = fun_test.get_job_environment_variable('test_bed_type')

        img = fun_test.get_job_environment_variable('tftp_image_path')
        f1_0_boot_args = "app=load_mods cc_huid=3 --all_100g --dpc-server --dpc-uart --disable-wu-watchdog retimer=0"
        f1_1_boot_args = "app=load_mods cc_huid=2 --all_100g --dpc-server --dpc-uart --disable-wu-watchdog"
        funcp_obj = FunControlPlaneBringup(fs_name=fs_name, boot_args_f1_0=f1_0_boot_args, boot_image_f1_1=img,
                                           boot_args_f1_1=f1_1_boot_args, boot_image_f1_0=img)
        funcp_obj.boot_both_f1(reboot_come=False, gatewayip="10.1.44.1")

    def cleanup(self):
        fun_test.log("Cleanup")


class CheckPCIeWidth(FunTestCase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Check Speed",
                              steps="""
                              1. Reboot Host
                              2. Check Width""")

    def setup(self):
        pass

    def run(self):
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        server_key = fun_test.parse_file_to_json(
            fun_test.get_script_parent_directory() + '/fs_connected_servers.json')
        servers_mode = server_key["fs"][fs_name]
        for server in servers_mode:
            result = verify_host_pcie_link(hostname=server, mode=servers_mode[server], reboot=True)
            fun_test.test_assert(expression=(result == "1"), message="Make sure that PCIe links on host %s went up"
                                                                     % server)

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(CheckPCIeWidth())
    ts.run()
