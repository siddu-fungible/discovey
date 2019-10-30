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
                              summary="Check of FS66",
                              steps="""
                              1. BringUP both F1s
                              2. reboot COMe and hosts
                              3. Verify PICe link
                              """)

    def setup(self):

        pass

    def run(self):
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        if not fs_name:
            fs_name = "fs-66"
        f1_0_boot_args = "app=mdt_test,load_mods cc_huid=3 --dpc-server --all_100g --serial --dpc-uart " \
                         "--dis-stats retimer=0 --mgmt --disable-wu-watchdog"
        f1_1_boot_args = "app=mdt_test,load_mods cc_huid=2 --dpc-server --all_100g --serial --dpc-uart " \
                         "--dis-stats retimer=3 --mgmt --disable-wu-watchdog"
        server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                 '/fs_connected_servers.json')
        servers_mode = server_key["fs"][fs_name]["hosts"]
        final_result = {}
        t_end = time.time() + 60 * 120
        for server in servers_mode:
            final_result[server] = {"success": 0, "incomplete": 0, "failure": 0}
        while time.time() < t_end:
            topology_helper = TopologyHelper()
            topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                              1: {"boot_args": f1_1_boot_args}}
                                               )
            topology = topology_helper.deploy()
            fun_test.shared_variables["topology"] = topology
            fun_test.test_assert(topology, "Topology deployed")

            for server in servers_mode:
                result = verify_host_pcie_link(hostname=server, mode=servers_mode[server], reboot=False)
                critical_log(expression=(result != "0"), message="Make sure that PCIe links on host %s went up"
                                                                         % server)
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
            fun_test.add_checkpoint(checkpoint="final_result")
            
    def cleanup(self):

        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(VerifySetup())
    ts.run()
