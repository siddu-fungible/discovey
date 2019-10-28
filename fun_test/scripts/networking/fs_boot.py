from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_rfc2544_template import *
from scripts.networking.nu_config_manager import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.host.linux import *
from lib.fun.fs import *


class ScriptSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="1. Make sure correct FS system is selected")

    def setup(self):

        fun_test.test_assert_expected(expected="fs-7", actual=fun_test.get_job_environment_variable('test_bed_type'),
                                      message="Correct FS was selected")

    def cleanup(self):
        pass


class BootFS(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary=" Boot FS",
                              steps="""
                              1. Get FS system : %s credentials, image and bootargs
                              2. Boot up FS system
                              """ % fun_test.get_job_environment_variable('test_bed_type'))

    def setup(self):
        pass

    def run(self):
        
        if fun_test.get_job_environment_variable('test_bed_type') == 'fs-7':
            fs = Fs.get(boot_args="app=load_mods cc_huid=3 --fec sku=SKU_FS1600_0 --dis-stats --disable-wu-watchdog --dpc-server --dpc-uart --serdesinit")
        fun_test.simple_assert(fs, "Succesfully fetched image, credentials and bootargs")
        fun_test.test_assert(fs.bootup(reboot_bmc=False), 'FS bootup')

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(BootFS())
    ts.run()
