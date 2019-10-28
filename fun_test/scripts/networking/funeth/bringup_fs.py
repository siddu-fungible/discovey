from lib.system.fun_test import *
from fun_settings import SCRIPTS_DIR
from scripts.networking.nu_config_manager import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.utilities.funcp_config import *

fs = "fs-11"
image = "funos-f1.stripped.gz.gliang"

# CSR replay
#boot_args_f1_0 = "app=load_mods retimer=0,1 --dpc-uart --dpc-server --csr-replay --all_100g --disable-wu-watchdog"
#boot_args_f1_1 = "app=load_mods retimer=0,1 --dpc-uart --dpc-server --csr-replay --all_100g --disable-wu-watchdog"

#boot_args_f1_0 = "app=load_mods,rdstest --server clients=20 qd=256 msgs=1000 delay=100 --noalternatecheck localip=29.1.1.1 remoteip=20.1.1.1 --disable-wu-watchdog --disable-idle-detection --dpc-uart --dpc-server --csr-replay --all_100g"
# With FunCP
boot_args_f1_0 = "app=load_mods cc_huid=3 sku=SKU_FS1600_0 retimer=0,1 --all_100g --dpc-server --dpc-uart --disable-wu-watchdog"
boot_args_f1_1 = "app=load_mods cc_huid=2 sku=SKU_FS1600_1 retimer=0,1 --all_100g --dpc-server --dpc-uart --disable-wu-watchdog"

# Juniper IPSec
#boot_args_f1_0 = "app=hw_hsu_test --dpc-uart --dpc-server --csr-replay --all_100g --disable-wu-watchdog override={NetworkUnit/VP:[{nu_bm_alloc_clusters:255,}]} hbm-coh-pool-mb=550 hbm-ncoh-pool-mb=3303"
#boot_args_f1_1 = "app=hw_hsu_test --dpc-uart --dpc-server --csr-replay --all_100g --disable-wu-watchdog"


class ScriptSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="1. Make sure correct FS system is selected")

    def setup(self):

        pass

    def cleanup(self):
        pass


class BringupFS(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Bringup FS-11",
                              steps="""
                              1. BringUP both F1s
                              """)

    def setup(self):
        pass

    def run(self):
        funcp_obj = FunControlPlaneBringup(fs_name=fs,
                                           boot_image_f1_0=image,
                                           boot_image_f1_1=image,
                                           boot_args_f1_0=boot_args_f1_0,
                                           boot_args_f1_1=boot_args_f1_1)
        funcp_obj.boot_both_f1(power_cycle_come=True)

        if 'cc_huid' in boot_args_f1_0:
            funcp_obj = FunControlPlaneBringup(fs_name="fs-11")
            funcp_obj.bringup_funcp(prepare_docker=False)
            funcp_obj.assign_mpg_ips(static=True, f1_1_mpg='10.1.20.241', f1_0_mpg='10.1.20.242',
                                     f1_0_mpg_netmask="255.255.252.0",
                                     f1_1_mpg_netmask="255.255.252.0")
            abstract_json_file_f1_0 = '{}/networking/tb_configs/FS11_F1_0.json'.format(SCRIPTS_DIR)
            abstract_json_file_f1_1 = '{}/networking/tb_configs/FS11_F1_1.json'.format(SCRIPTS_DIR)
            funcp_obj.funcp_abstract_config(abstract_config_f1_0=abstract_json_file_f1_0,
                                            abstract_config_f1_1=abstract_json_file_f1_1)
            fun_test.sleep("Sleeping for a while waiting for control plane to converge", seconds=10)

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = ScriptSetup()
    ts.add_test_case(BringupFS())
    ts.run()