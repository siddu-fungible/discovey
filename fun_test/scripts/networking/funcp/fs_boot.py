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
        pass

    def cleanup(self):
        pass


class BringupSetup(FunTestCase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Bringup FS",
                              steps="""
                              1. BringUP both F1s
                              2. Reboot COMe
                              """)

    def setup(self):
        pass

    def run(self):
       
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        f1_0_boot_args = "app=load_mods cc_huid=3 --dpc-uart --dpc-server " \
                         "--all_100g --disable-wu-watchdog"
        f1_1_boot_args = "app=load_mods cc_huid=2 --dpc-uart --dpc-server " \
                         "--all_100g --disable-wu-watchdog"

        topology_helper = TopologyHelper()
        topology_helper.set_dut_parameters(f1_parameters={0: {"boot_args": f1_0_boot_args},
                                                          1: {"boot_args": f1_1_boot_args}}, disable_f1_index=1
                                           )

        topology = topology_helper.deploy()
        fun_test.shared_variables["topology"] = topology
        fun_test.test_assert(topology, "Topology deployed")
  

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(BringupSetup())

    ts.run()
