from lib.system.fun_test import *
from lib.utilities.funcp_config import *
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


class FunCPBringUp(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Bringup FS",
                              steps="""
                              1. BringUP both F1s
                              2. Reboot COMe
                              """)

    def setup(self):
        pass

    def run(self):
        fs_name = "fs-7"
        f1_0_boot_args = "app=load_mods cc_huid=3 --dpc-uart --dpc-server " \
                         "--all_100g --disable-wu-watchdog"
        f1_1_boot_args = "app=load_mods cc_huid=2 --dpc-uart --dpc-server " \
                         "--all_100g --disable-wu-watchdog"

        boot_image = "s_29708_funos-f1.stripped.gz"
        funcp_obj = FunControlPlaneBringup(fs_name=fs_name, boot_image_f1_0=boot_image, boot_image_f1_1=boot_image,
                                           boot_args_f1_0=f1_0_boot_args, boot_args_f1_1=f1_1_boot_args)
        funcp_obj.boot_both_f1()
        funcp_obj.bringup_funcp(prepare_docker=False)

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(FunCPBringUp())

    ts.run()
