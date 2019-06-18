from lib.system.fun_test import *
from scripts.networking.nu_config_manager import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.utilities.funcp_config import *
from scripts.networking.funcp.helper import *
from lib.topology.topology_helper import TopologyHelper


class ScriptSetup(FunTestScript):
    server_key = {}

    def describe(self):
        self.set_test_details(steps="""
        Verify FS-name
        """)

    def setup(self):
        global funcp_obj, fs_name
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        funcp_obj = FunControlPlaneBringup(fs_name=fs_name)
        funcp_obj.cleanup_funcp()

    def cleanup(self):
        funcp_obj.cleanup_funcp()


class BootF1(FunTestCase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Bringup both F1s and Reboot COMe",
                              steps="""
                              1. BringUP both F1s
                              2. Reboot COMe
                              """)

    def setup(self):
        pass

    def run(self):

        f1_0_boot_args = "app=hw_hsu_test cc_huid=3 --dpc-server --all_100g --dpc-uart --dis-stats --disable-wu-watchdog"
        f1_1_boot_args = "app=hw_hsu_test cc_huid=2 --dpc-server --all_100g --dpc-uart --dis-stats --disable-wu-watchdog"

        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                          1: {"boot_args": f1_1_boot_args}}
                                           )
        topology = topology_helper.deploy()
        fun_test.shared_variables["topology"] = topology
        fun_test.test_assert(topology, "Topology deployed")

        # Bringup FunCP


    def cleanup(self):
        pass


class BringupControlPlane(FunTestCase):
    server_key = {}

    def describe(self):
        self.set_test_details(id=2,
                              summary="Bringup Control Plane",
                              steps="""
                                  1. Prepare Docker
                                  2. Setup Docker
                                  """)


    def setup(self):
        self.server_key = fun_test.parse_file_to_json(fun_test.get_script_parent_directory() +
                                                      '/fs_connected_servers.json')


    def run(self):

        fun_test.test_assert(expression=funcp_obj.bringup_funcp(prepare_docker=True), message="Bringup FunCP")
        funcp_obj.assign_mpg_ips(static=self.server_key["fs"][fs_name]["mpg_ips"]["static"],
                                 f1_1_mpg=self.server_key["fs"][fs_name]["mpg_ips"]["mpg1"],
                                 f1_0_mpg=self.server_key["fs"][fs_name]["mpg_ips"]["mpg0"])
        abstract_json_file0 = fun_test.get_script_parent_directory() + '/abstract_config/' + \
                              self.server_key["fs"][fs_name]["abstract_configs"]["F1-0"]
        abstract_json_file1 = fun_test.get_script_parent_directory() + '/abstract_config/' + \
                              self.server_key["fs"][fs_name]["abstract_configs"]["F1-1"]
        funcp_obj.funcp_abstract_config(abstract_config_f1_0=abstract_json_file0,
                                        abstract_config_f1_1=abstract_json_file1, workspace="/scratch")
        ping_dict = self.server_key["fs"][fs_name]["cc_pings"]
        for container in ping_dict:
            funcp_obj.test_cc_pings_remote_fs(dest_ips=ping_dict[container], docker_name=container)


    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(BootF1())
    ts.add_test_case(BringupControlPlane())
    # T1 : NIC emulation : ifconfig, Ethtool - move Host configs here, do a ping, netperf, tcpdump
    # T2 : Local SSD from FIO
    # T3 : Remote SSD FIO
    ts.run()