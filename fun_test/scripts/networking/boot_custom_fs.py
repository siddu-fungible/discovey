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

        pass

    def cleanup(self):
        pass


class BootFS(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary=" Boot FS",
                              steps="""
                              1. Get FS system credentials, image and bootargs
                              2. Boot up FS system
                              """)

    def setup(self):
        pass

    def run(self):

        bootargs = "app=load_mods cc_huid=3 --fec sku=SKU_FS1600_0 --dis-stats --csr-replay --dpc-server --dpc-uart --serdesinit"
        test_bed_spec = fun_test.get_asset_manager().get_fs_spec("fs-7")
        img_path = "funos-f1.stripped_24apr_funcp.gz"
        fs = Fs.get(fs_spec=test_bed_spec, tftp_image_path=img_path, boot_args=bootargs)
        fun_test.simple_assert(fs, "Succesfully fetched image, credentials and bootargs")
        fun_test.test_assert(fs.bootup(reboot_bmc=False), 'FS bootup')

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(BootFS())
    ts.run()
