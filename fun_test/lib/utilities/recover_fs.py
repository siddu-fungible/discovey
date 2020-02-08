from lib.system.fun_test import *
from lib.fun.fs import Fs

if __name__ == "__main__":
    #fs_name = "fs-116"
    #fs_name = "fs-116"
    fs_names = ["fs-104", "fs-116", "fs-117", "fs-121", "fs-122", "fs-123"]
    fs_names = ["fs-121"]

    for fs_name in fs_names:
        try:
            stable_image_gz = "s_57904_funos-f1.stripped.signed.gz"
            stable_image_gz = "s_57928_funos-f1.stripped.signed.gz"  # 198 good
            stable_image_gz = "s_57984_funos-f1.stripped.signed.gz"  # Felix
            boot_args = "app=mdt_test,load_mods workload=storage --serial --memvol --dpc-server --dpc-uart --csr-replay --all_100g --useddr --disable-syslog-replay"
            fs = Fs.get(fun_test.get_asset_manager().get_fs_spec(name=fs_name))
            bmc = fs.get_bmc()
            bmc.initialize()
            bmc.position_support_scripts(auto_boot=False)
            bmc.stop_bundle_f1_logs()
            for f1_index in range(2):
                bmc.setup_serial_proxy_connection(f1_index=f1_index)
                bmc.reset_f1(f1_index=f1_index)
                preamble = bmc.get_preamble(f1_index=f1_index)
                bmc.validate_u_boot_version(output=preamble, minimum_date=Fs.MIN_U_BOOT_DATE)
                bmc.u_boot_load_image(index=f1_index, tftp_image_path=stable_image_gz, boot_args=boot_args)# mpg_ips=["10.1.105.156", "10.1.105.159"], gateway_ip="10.1.105.1")

            bmc.start_bundle_f1_logs()
            bmc.come_power_cycle()
        except Exception as ex:
            fun_test.critical(str(ex))


# TBD: Fs-121, FS-116, FS-122
# Done: FS-117

# FS-123