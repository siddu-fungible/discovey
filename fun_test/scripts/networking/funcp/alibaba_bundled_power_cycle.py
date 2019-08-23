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
import json
from scripts.networking.funcp.ali_bmv_storage_sanity import *


class SetupBringup(FunTestScript):
    server_key = {}

    def describe(self):
        self.set_test_details(steps="""

                              """)

    def setup(self):

        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        fs_spec = fun_test.get_asset_manager().get_fs_by_name(fs_name)

        self.reboot_fpga(fs_spec['fpga']['mgmt_ip'])

        come_linux = Linux(host_ip=fs_spec['come']['mgmt_ip'], ssh_username='fun', ssh_password="123")
        come_linux.ensure_host_is_up(max_wait_time=300, power_cycle=False)

        retry_count = 0
        while True:
            fpga_linux = Linux(host_ip=fs_spec['fpga']['mgmt_ip'], ssh_username='root', ssh_password="root")
            if fpga_linux.check_ssh():
                fpga_linux.disconnect()
                linux_home = Linux(host_ip="qa-ubuntu-02", ssh_username="auto_admin", ssh_password="fun123")
                if linux_home.ping(dst=fs_spec['bmc']['mgmt_ip']):
                    if come_linux.check_ssh():
                        come_linux.disconnect()
                        break
            retry_count += 1
            fun_test.sleep(message="Waiting for FS reboot", seconds=30)
            if retry_count > 20:
                fun_test.test_assert(message="Can't reach FS components", expression=False)

    def cleanup(self):
        pass

    def reboot_fpga(self, fpga_ip):
        linux_obj = Linux(host_ip=fpga_ip, ssh_username='root', ssh_password='root')
        linux_obj.reboot(max_wait_time=240)


class CheckCOMe(FunTestCase):
    come_linux = None

    def describe(self):
        self.set_test_details(id=2, summary="Reboot COMe and CHeck Fungible PFs",
                              steps="""

                                      """)

    def setup(self):

        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        fs_spec = fun_test.get_asset_manager().get_fs_by_name(str(fs_name))
        self.come_linux = Linux(host_ip=fs_spec['come']['mgmt_ip'], ssh_username='fun', ssh_password="123")
        self.come_linux.reboot(max_wait_time=300)

    def run(self):
        output = self.come_linux.command('lspci -d 1dad:')
        fun_test.test_assert(re.search(r'Ethernet controller: (?:Device 1dad:00f1|Fungible Device 00f1)', output),
                             message="Check ethernet device")

    def cleanup(self):
        pass


class CheckSSDSpeed(FunTestCase):

    def describe(self):
        self.set_test_details(id=1, summary="Check SSD Linkspeed and count",
                              steps="""

                                      """)

    def setup(self):

        # TODO: FS33 F1_1 takes longer time to boot
        fun_test.sleep("Waiting for FunOS Boot to complete", seconds=180)

    def run(self):
        # Check SSD link & count
        fs_0 = fun_test.shared_variables['fs_object']
        ssd_up_count_fail = False
        ssd_already_up_count_fail = False
        gen3x2_fail = False
        gen3x4_fail = False
        f1_0_ssd_count = 4
        f1_1_ssd_count = 4

        match_strings = "Gen3x4|Gen3x2"
        for f1index in 0, 1:
            uart_path = fs_0.get_uart_log_file(f1_index=f1index)
            uart_content = os.popen("cat %s" % uart_path).read()
            match_str_list = re.findall(r'{}'.format(match_strings), uart_content, re.IGNORECASE)
            gen3x4_count = match_str_list.count("Gen3x4")
            gen3x2_count = match_str_list.count("Gen3x2")
            fun_test.log_section("SSD Details on F1_{}".format(f1index))
            fun_test.log("SSD in Gen3x4 : {}".format(gen3x4_count))
            fun_test.log("SSD in Gen3x2 : {}".format(gen3x2_count))

            counter_name = "f1_{}_ssd_count".format(f1index)
            ssd_count = eval(counter_name)

            for line in uart_content.split("\n"):
                if "INFO volume_manager \"backend:" in line:
                    if "devices up" in line:
                        match_count = re.search(r'backend:\s+(?P<count>\d+)', line)
                        if match_count:
                            actual_ssd_count = int(match_count.group('count'))
                            fun_test.add_checkpoint(checkpoint="F1_{} backend devices up".format(f1index),
                                                    expected=ssd_count, actual=actual_ssd_count)
                            if actual_ssd_count != ssd_count:
                                ssd_up_count_fail = True
                    elif "devices are already up" in line:
                        match_count = re.search(r'backend:\s+(?P<count>\d+)', line)
                        if match_count:
                            actual_ssd_up_count = int(match_count.group('count'))
                            fun_test.add_checkpoint(checkpoint="F1_{} backend devices already up".format(f1index),
                                                    expected=ssd_count, actual=actual_ssd_up_count)
                            if actual_ssd_up_count != ssd_count:
                                ssd_already_up_count_fail = True

            if gen3x4_count / 2 == 4:
                fun_test.add_checkpoint("Gen3x4 SSD count on F1_{}".format(f1index),
                                        "PASSED", expected=ssd_count, actual=gen3x4_count)
            else:
                fun_test.add_checkpoint("Gen3x4 SSD count on F1_{}".format(f1index),
                                        "FAILED", expected=ssd_count, actual=gen3x4_count)
                gen3x4_fail = True
            if gen3x2_count == 0:
                fun_test.add_checkpoint("Gen3x2 SSD count on F1_{}".format(f1index),
                                        "PASSED", expected=0, actual=gen3x2_count)
            else:
                fun_test.add_checkpoint("Gen3x2 SSD count on F1_{}".format(f1index),
                                        "FAILED", expected=0, actual=gen3x2_count)

                gen3x2_fail = True

        if ssd_already_up_count_fail or ssd_up_count_fail or gen3x4_fail or gen3x2_fail:
            fun_test.test_assert(False, "SSD checks failed")

    def cleanup(self):
        pass

class F1reset(FunTestScript):
    come_linux = None

    def describe(self):
        self.set_test_details(
                              steps="""

                                      """)

    def setup(self):
        boot_image = "demo.gz"
        fs_name = fun_test.get_job_environment_variable('test_bed_type')
        fs_spec = fun_test.get_asset_manager().get_fs_by_name(str(fs_name))
        fs_0 = Fs.get(fs_spec=fs_spec, tftp_image_path=boot_image, boot_args="abc")
        fun_test.test_assert(fs_0.bmc_initialize(), "BMC initialize") # starts netcat
        fun_test.test_assert(fs_0.set_f1s(), "Set F1s")
        fun_test.shared_variables['fs_object'] = fs_0
        for f1index in 0, 1:
            fs_0.bmc.start_uart_log_listener(f1_index=f1index, serial_device=None)

        fun_test.test_assert(fs_0.fpga_initialize(), "FPGA initiaize")

    def cleanup(self):
        pass


if __name__ == '__main__':

    job_inputs = fun_test.get_job_inputs()
    f1_reset=None
    if not job_inputs:
        job_inputs = {}
    fun_test.log("Provided job inputs: {}".format(job_inputs))
    if "f1_reset" in job_inputs:
        f1_reset = job_inputs["f1_reset"]
        fun_test.shared_variables["f1_reset"] = f1_reset
    if f1_reset:
        ts = F1reset()
        ts.add_test_case(CheckSSDSpeed())
        print "F1 reset"
    else:
        ts = SetupBringup()

    ts.add_test_case(CheckCOMe())
    ts.run()
