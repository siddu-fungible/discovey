from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_rfc2544_template import *
from scripts.networking.nu_config_manager import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.host.linux import *
from lib.fun.fs import *
import os
import time
bmc_reach = False
fpga_reach = False
server_reach = False
server_ip = ""


class ScriptSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="1. Make sure BMC and FPGA are reachable")

    def setup(self):
        global server_ip, bmc_reach, fpga_reach, server_reach, test_bed_spec
        test_bed_spec = fun_test.get_asset_manager().get_fs_spec("fs-11")
        bmc_reach = False
        fpga_reach = False
        server_reach = False
        server_ip = "poc-server-05"


    def cleanup(self):
        pass


class BootFS(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary=" Boot FS, reboot Server",
                              steps="""
                              1. Get FS system credentials, image and bootargs
                              2. Boot up FS system
                              """)

    def setup(self):
        pass

    def run(self):
        run_count = 1
        success_count = 0
        fail_count = 0
        t_end = time.time() + 60 * 120
        while time.time() < t_end:
            reach = self.check_reachability()
            fun_test.test_assert(reach, message="Reachable test passed for run %s" % run_count)
            print ""
            print "Run %s" % run_count
            run_count += 1
            print "===================================================================================================="
            bootargs = "app=load_mods cc_huid=3 --fec sku=SKU_FS1600_0 --dis-stats --disable-wu-watchdog --dpc-server --dpc-uart --serdesinit --retimer"
            img_path = "funos-f1.stripped_28apr_pcie_extn_test.gz"
            fs = Fs.get(fs_spec=test_bed_spec, tftp_image_path=img_path, boot_args=bootargs)
            fun_test.test_assert(expression=fs, message="Succesfully fetched image, credentials and bootargs")
            fun_test.test_assert(fs.bmc_initialize(), "BMC initialize")

            fun_test.test_assert(fs.set_f1s(), "Set F1s")
            fun_test.test_assert(fs.fpga_initialize(), "FPGA initiaize")
            for f1_index, f1 in fs.f1s.iteritems():
                if f1_index == fs.disable_f1_index:
                    continue
                fun_test.test_assert(fs.bmc.u_boot_load_image(index=f1_index, tftp_image_path=fs.tftp_image_path,
                                                              boot_args=fs.boot_args),
                                     "U-Bootup f1: {} complete".format(f1_index))
                fs.bmc.start_uart_log_listener(f1_index=f1_index)
                break
            # fun_test.test_assert(fs.bootup(reboot_bmc=False, power_cycle_come=False), 'FS bootup')
            fun_test.sleep(message="Waiting for FS", seconds=30)
            linux_obj = Linux(host_ip=server_ip, ssh_username="localadmin", ssh_password="Precious1*")
            linux_obj.reboot()
            lspci_output = linux_obj.command(command="lspci -d 1dad:")
            sections = ['Ethernet controller', 'Non-Volatile', 'Unassigned class', 'encryption device']
            lspci_err = False
            for section in sections:
                if section not in lspci_output:
                    lspci_err = True
                    fun_test.critical("Under LSPCI {} not found".format(section))
            if lspci_err:
                fail_count += 1
                fun_test.critical("This is a failed run %s" % run_count)
            else:
                success_count += 1
            fun_test.log("Success Count = %s" % success_count)
            fun_test.log("Fail Count = %s" % fail_count)

    def cleanup(self):
        pass

    def check_reachability(self):
        result = False
        for i in range(5):
            response = os.system("ping -c 1 " + test_bed_spec['bmc']['mgmt_ip'])
            if response == 0:
                bmc_reach = True
                break
        fun_test.test_assert(expression=bmc_reach, message="Make sure BMC is reachable")
        for i in range(5):
            response = os.system("ping -c 1 " + test_bed_spec['fpga']['mgmt_ip'])
            if response == 0:
                fpga_reach = True
                break
        fun_test.test_assert(expression=fpga_reach, message="Make sure FPGA is reachable")
        for i in range(5):
            response = os.system("ping -c 1 " + server_ip)
            if response == 0:
                server_reach = True
                break
        fun_test.test_assert(expression=server_reach, message="Make sure %s is reachable" % server_ip)

        if bmc_reach and fpga_reach and server_reach:
            result = True
        return result


if __name__ == '__main__':
        ts = ScriptSetup()
        ts.add_test_case(BootFS())
        ts.run()
