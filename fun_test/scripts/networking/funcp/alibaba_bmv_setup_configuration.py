from lib.system.fun_test import *
from scripts.networking.nu_config_manager import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.utilities.funcp_config import *
from scripts.networking.tb_configs import tb_configs
from scripts.networking.funcp.helper import *
from scripts.networking.funeth.sanity import Funeth


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
                              summary="Bringup FS-45 with control plane",
                              steps="""
                              1. BringUP both F1s
                              2. Bringup FunCP
                              3. Create MPG Interfaces and assign static IPs
                              """)

    def setup(self):

        pass

    def run(self):
        fs_name = "fs-45"
        global funcp_obj, servers_mode
        funcp_obj = FunControlPlaneBringup(fs_name=fs_name, boot_image_f1_0="ysingh/funos-f1.stripped_28may_retimer.gz",
                                           boot_image_f1_1="ysingh/funos-f1.stripped_28may_retimer.gz",
                                           boot_args_f1_0="app=mdt_test,load_mods,hw_hsu_test cc_huid=3 --dpc-server "
                                                          "--all_100g --serial --dpc-uart --dis-stats retimer=0 --mgmt",
                                           boot_args_f1_1="app=mdt_test,load_mods,hw_hsu_test cc_huid=2 --dpc-server "
                                                          "--all_100g --serial --dpc-uart --dis-stats retimer=3 --mgmt")


        server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() + '/fs_connected_servers.json')
        servers_mode = server_key["fs"][fs_name]

        for server in servers_mode:
            print server
            fun_test.test_assert(expression=rmmod_funeth_host(hostname=server), message="rmmod funeth on host")

        # Boot both F1s and reboot COMe
        fun_test.test_assert(expression=funcp_obj.boot_both_f1(power_cycle_come=True, gatewayip="10.1.105.1",
                                                               funcp_cleanup=True), message="Boot F1s")
        # Bringup FunCP

        fun_test.test_assert(expression=funcp_obj.bringup_funcp(prepare_docker=False), message="Bringup FunCP")
        # Assign MPG IPs from dhcp

        funcp_obj.assign_mpg_ips(static=True, f1_1_mpg="10.1.105.172", f1_0_mpg="10.1.105.173")

    def cleanup(self):

        pass


class NicEmulation(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Bringup PCIe Connceted Hosts and test traffic",
                              steps="""
                              1. Reboot connected hosts
                              2. Verify for PICe Link
                              3. Install Funeth Driver
                              4. Configure HU interface
                              5. Configure FunCP according to HU interfaces
                              6. Add routes on FunCP Container
                              7. Ping NU host from HU host
                              8. Do netperf
                              """)

    def setup(self):

        pass

    def run(self):
        # reboot PCIe connected servers and verify PCIe connections
        for server in servers_mode:
            print server
            result = verify_host_pcie_link(hostname=server, mode=servers_mode[server], reboot=True)
            fun_test.test_assert(expression=(result != "0"), message="Make sure that PCIe links on host %s went up"
                                                                     % server)

        # install drivers on PCIE connected servers
        tb_config_obj = tb_configs.TBConfigs("FS45")
        funeth_obj = Funeth(tb_config_obj)
        fun_test.shared_variables['funeth_obj'] = funeth_obj
        setup_hu_host(funeth_obj, update_driver=True)
        # TODO : add ethtool output
        # funcp_obj.fetch_mpg_ips() #Only if not running the full script
        # execute abstract file

        abstract_json_file0 = fun_test.get_script_parent_directory() + '/alibaba_bmv_configs_f1_0.json'
        abstract_json_file1 = fun_test.get_script_parent_directory() + '/alibaba_bmv_configs_f1_1.json'
        funcp_obj.funcp_abstract_config(abstract_config_f1_0=abstract_json_file0,
                                        abstract_config_f1_1=abstract_json_file1, workspace="/scratch")

        funcp_obj.add_routes_on_f1(f1_0_outgoing=["fpg0", "1.1.1.1"], f1_0=["19.1.1.0/24", "30.1.1.0/24"],
                                   f1_1_outgoing=["fpg0", "1.1.2.1"], f1_1=["18.1.1.0/24", "30.1.1.0/24"])

        # test_hu_host_pings(hostnames=servers_mode)
        funcp_obj.test_cc_pings_fs() # TODO : check ping: -I, -L, -T flags cannot be used with unicast destination
        # funcp_obj.test_cc_pings_remote_fs(dest_ips=["", ""])

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(BringupSetup())
    ts.add_test_case(NicEmulation())
    # T1 : NIC emulation : ifconfig, Ethtool - move Host configs here, do a ping, netperf, tcpdump
    # T2 : Local SSD from FIO
    # T3 : Remote SSD FIO
    ts.run()
