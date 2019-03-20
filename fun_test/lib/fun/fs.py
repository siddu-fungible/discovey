from lib.system.fun_test import fun_test, FunTimer
from lib.system.utils import parse_file_to_json
from lib.host.linux import Linux
from fun_settings import TFTP_SERVER, ASSET_DIR
import re
import pexpect



class BootPhases:
    U_BOOT_INIT = "u-boot: init"
    U_BOOT_MICROCOM_STARTED = "u-boot: microcom started"
    U_BOOT_TRAIN = "u-boot: train"
    U_BOOT_SET_BOOT_ARGS = "u-boot: set boot args"
    U_BOOT_DHCP = "u-boot: dhcp"
    U_BOOT_TFTP_DOWNLOAD = "u-boot: tftp download"
    U_BOOT_UNCOMPRESS_IMAGE = "u-boot: uncompress image"
    U_BOOT_ELF = "u-boot: bootelf"

    F1_BOOT_NETWORK_STARTED = "f1: network started"
    F1_BOOT_PCI_STARTED = "f1: pci started"
    F1_BOOT_READY = "f1: ready"
    F1_DPC_SERVER_STARTED = "f1: dpc server started"
    F1_BOOT_EP_CONTROLLER_READY = "f1: ep controller ready"


class F1InFs:
    SERIAL_SPEED_DEFAULT = 1000000
    ELF_ADDRESS = "0xffffffff99000000"

    def __init__(self, index, bmc, serial_device_path, serial_sbp_device_path):
        self.index = index
        self.bmc = bmc.clone()
        self.bmc._connect()
        self.serial_device_path = serial_device_path
        self.serial_sbp_device_path = serial_sbp_device_path

    def bootup(self):
        fun_test.test_assert(self.u_boot_load_image(), "u-boot load image")
        return True

    def set_boot_phase(self, phase):
        self.boot_phase = phase
        fun_test.add_checkpoint("Started boot phase: {}".format(phase))
        fun_test.log_section("F1_{}:{}".format(self.index, phase))

    def u_boot_command(self, command, timeout=15, expected=None):
        output = self.bmc.command("python /tmp/u_boot_interface.py --device_path={} --speed {} --command='{}' --timeout={}".format(self.serial_device_path,
                                                                                           self.SERIAL_SPEED_DEFAULT,
                                                                                                          command, timeout), timeout=timeout + 5)
        if expected:
            fun_test.simple_assert(expected in output, "{} not in output: {}".format(expected, output))
        return output

    def receive_serial(self, handle, expect=None, timeout=60):
        buffer = ""
        handle.sendline("cat {}".format(self.serial_device_path))
        if expect:
            handle.timeout = timeout
            handle.expect(expect)
            buffer += handle.before
        return buffer

    def u_boot_load_image(self,
                          tftp_load_address="0xa800000080000000",
                          tftp_server=TFTP_SERVER):
        result = None
        handle = self.bmc.handle
        self.set_boot_phase(BootPhases.U_BOOT_INIT)

        self.u_boot_command(command="lfw; lmpg; ltrain; lstatus", timeout=15, expected='Fifo Out of Reset')
        self.set_boot_phase(BootPhases.U_BOOT_TRAIN)

        self.u_boot_command(command="setenv bootargs app=hw_hsu_test sku=SKU_FS1600_{} --dis-stats --disable-wu-watchdog --dpc-server --dpc-uart --csr-replay --serdesinit".format(self.index), timeout=5)
        self.set_boot_phase(BootPhases.U_BOOT_SET_BOOT_ARGS)

        self.u_boot_command(command="dhcp", timeout=15, expected="our IP address is")
        self.set_boot_phase(BootPhases.U_BOOT_DHCP)

        output = self.u_boot_command(command="tftpboot {} {}:funos-f1.stripped.gz".format(tftp_load_address, tftp_server), timeout=15)
        m = re.search(r'Bytes transferred = (\d+)', output)
        if m:
            bytes_transferred = int(m.group(1))
            fun_test.test_assert(bytes_transferred > 1000, "FunOs download size: {}".format(bytes_transferred))
            self.set_boot_phase(BootPhases.U_BOOT_TFTP_DOWNLOAD)


        output = self.u_boot_command(command="unzip {} {};".format(tftp_load_address, self.ELF_ADDRESS), timeout=10)
        m = re.search(r'Uncompressed size: (\d+) =', output)
        if m:
            uncompressed_size = int(m.group(1))
            fun_test.test_assert(uncompressed_size > 1000, "FunOs uncompressed size: {}".format(uncompressed_size))
            self.set_boot_phase(BootPhases.U_BOOT_UNCOMPRESS_IMAGE)

        output = self.u_boot_command(command="bootelf -p {}".format(self.ELF_ADDRESS), timeout=60, expected="Welcome to FunOS")
        m = re.search(r'Version=(\S+), Branch=(\S+)', output)
        if m:
            version = m.group(1)
            branch = m.group(2)
            fun_test.add_checkpoint("Version: {}, branch: {}".format(version, branch))
        self.set_boot_phase(BootPhases.U_BOOT_ELF)

        sections = ['NETWORK_START', 'DPC_SERVER_STARTED', 'PCI_STARTED']
        for section in sections:
            fun_test.test_assert(section in output, "{} seen".format(section))

        '''
        handle.timeout = 60
        i = handle.expect(r'EP: controller is ready')
        self.set_boot_phase(BootPhases.F1_BOOT_EP_CONTROLLER_READY)
        '''
        result = True
        return result


class Fs():
    BMC_SCRIPT_DIRECTORY = "/mnt/sdmmc0p1/scripts"

    def __init__(self,
                 bmc_mgmt_ip,
                 bmc_mgmt_ssh_username,
                 bmc_mgmt_ssh_password,
                 fpga_mgmt_ip,
                 fpga_mgmt_ssh_username,
                 fpga_mgmt_ssh_password,
                 come_mgmt_ip,
                 come_mgmt_ssh_username,
                 come_mgmt_ssh_password):
        self.bmc_mgmt_ip = bmc_mgmt_ip
        self.bmc_mgmt_ssh_username = bmc_mgmt_ssh_username
        self.bmc_mgmt_ssh_password = bmc_mgmt_ssh_password
        self.fpga_mgmt_ip = fpga_mgmt_ip
        self.fpga_mgmt_ssh_username = fpga_mgmt_ssh_username
        self.fpga_mgmt_ssh_password = fpga_mgmt_ssh_password
        self.come_mgmt_ip = come_mgmt_ip
        self.come_mgmt_ssh_username = come_mgmt_ssh_username
        self.come_mgmt_ssh_password = come_mgmt_ssh_password
        self.bmc = None
        self.fpga = None
        self.come = None
        self.f1s = {}

    def get_f1_0(self):
        return self.get_f1(index=0)

    def get_f1_1(self):
        return self.get_f1(index=1)

    def get_f1(self, index):
        pass

    @staticmethod
    def get(spec):
        bmc_spec = spec["bmc"]
        fpga_spec = spec["fpga"]
        come_spec = spec["come"]
        return Fs(bmc_mgmt_ip=bmc_spec["mgmt_ip"],
                  bmc_mgmt_ssh_username=bmc_spec["mgmt_ssh_username"],
                  bmc_mgmt_ssh_password=bmc_spec["mgmt_ssh_password"],
                  fpga_mgmt_ip=fpga_spec["mgmt_ip"],
                  fpga_mgmt_ssh_username=fpga_spec["mgmt_ssh_username"],
                  fpga_mgmt_ssh_password=fpga_spec["mgmt_ssh_password"],
                  come_mgmt_ip=come_spec["mgmt_ip"],
                  come_mgmt_ssh_username=come_spec["mgmt_ssh_username"],
                  come_mgmt_ssh_password=come_spec["mgmt_ssh_password"])

    def bootup(self, reboot_bmc=False):
        if reboot_bmc:
            fun_test.test_assert(self.reboot_bmc(), "Reboot BMC")
        fun_test.test_assert(self.bmc_initialize(), "BMC initialize")
        fun_test.test_assert(self.fpga_initialize(), "FPGA initiaize")

        for f1_index, f1 in self.f1s.iteritems():
            fun_test.test_assert(f1.bootup(), "Bootup f1: {} complete".format(f1_index))
        return True

    def get_bmc(self):
        if not self.bmc:
            self.bmc_initialize()
        return self.bmc

    def get_fpga(self):
        if not self.fpga:
            self.fpga_initialize()
        return self.fpga

    def get_come(self):
        if not self.come:
            self.come_initialize()
        return self.come

    def come_initialize(self):
        self.come = Linux(host_ip=self.come_mgmt_ip,
                          ssh_username=self.come_mgmt_ssh_username,
                          ssh_password=self.come_mgmt_ssh_password, set_term_settings=True)
        working_directory = "/tmp"
        self.come.command("cd {}".format(working_directory))
        self.come.command("mkdir workspace; cd workspace")
        self.come.command("export WORKSPACE=$PWD")
        self.come.command("wget http://dochub.fungible.local/doc/jenkins/funcontrolplane/latest/functrlp_palladium.tgz")
        files = self.come.list_files("functrlp_palladium.tgz")
        fun_test.test_assert(len(files), "functrlp_palladium.tgz downloaded")
        return True


    def bmc_initialize(self):
        self.bmc = Linux(host_ip=self.bmc_mgmt_ip,
                         ssh_username=self.bmc_mgmt_ssh_username,
                         ssh_password=self.bmc_mgmt_ssh_password, set_term_settings=True)
        self.bmc.set_prompt_terminator(r'# $')
        fun_test.simple_assert(self.bmc._connect(), "BMC connected")
        self.bmc.command("cd {}".format(self.BMC_SCRIPT_DIRECTORY))
        self.bmc.command("./f1_console.sh 1")
        self._set_f1s()
        return self.bmc

    def fpga_initialize(self):
        result = None
        fun_test.add_checkpoint("FPGA initialize")
        self.fpga = Linux(host_ip=self.fpga_mgmt_ip,
                          ssh_username=self.fpga_mgmt_ssh_username,
                          ssh_password=self.fpga_mgmt_ssh_password, set_term_settings=True)

        for f1_index, f1 in self.f1s.iteritems():
            self.fpga.command("./f1reset -s {0} 0; sleep 2; ./f1reset -s {0} 1".format(f1_index))
            output = self.fpga.command("./f1reset -g")
            fun_test.simple_assert("F1_{} is out of reset".format(f1_index) in output, "F1 {} out of reset".format(f1_index))

        fun_test.sleep("FPGA reset", seconds=10)

        result = True
        return result

    def _set_f1s(self):
        result = None
        output = self.bmc.command("./f1_uartmux.sh 1")
        lines = output.split("\n")
        f1_info = {}
        for line in lines:
            m = re.search(r'F1\[(\d+)\]\s+(\S+)\s+(\S+)', line)
            if m:
                f1_index = int(m.group(1))
                console_or_sbp = m.group(2)
                device_path = m.group(3)
                if f1_index > 0:
                    fun_test.critical("Disabling F1_1 for now")
                    continue
                if f1_index not in f1_info:
                    f1_info[f1_index] = {}
                if console_or_sbp == "console":
                    f1_info[f1_index]["f1_device_path"] = device_path
                if console_or_sbp == "SBP":
                    f1_info[f1_index]["sbp_device_path"] = device_path
        # F1InFs()
        # flatten
        for f1_index in sorted(f1_info.keys()):
            self.f1s[f1_index] = F1InFs(index=f1_index,
                                        bmc=self.bmc,
                                        serial_device_path=f1_info[f1_index]["f1_device_path"],
                                        serial_sbp_device_path=f1_info[f1_index]["sbp_device_path"])

            if f1_index > 0:
                fun_test.critical("Disabling F1_1 for now")
                continue

        fun_test.simple_assert(len(self.f1s.keys()), "Both F1 device paths found")
        return result


    def reboot_bmc(self):
        result = None
        fun_test.add_checkpoint("Rebooting BMC")
        bmc = self.get_bmc().clone()
        bmc.command("reboot")
        powered_down = False
        power_down_timer = FunTimer(max_time=60)
        while not power_down_timer.is_expired():
            try:
                bmc.command("date")
                fun_test.sleep("Powering down BMC")
            except:
                powered_down = True
                bmc.disconnect()
                break
        bmc.disconnect()
        self.bmc = None
        fun_test.simple_assert(not power_down_timer.is_expired(), "Power down timer is not expired")
        fun_test.simple_assert(powered_down, "Power down detected")
        power_up_timer = FunTimer(max_time=180)
        while not power_up_timer.is_expired():
            try:
                bmc.command("date")
                break
            except:
                fun_test.sleep("Rebooting BMC", seconds=10)
        fun_test.simple_assert(not power_up_timer.is_expired(), "Power up timer is not expired")

        fun_test.add_checkpoint("Reboot procedure completed")
        result = True
        return result

if __name__ == "__main__":
    fs_json = ASSET_DIR + "/fs.json"
    json_spec = parse_file_to_json(file_name=fs_json)
    fs = Fs.get(spec=json_spec[0])
    #fs.bootup(reboot_bmc=True)
    fs.come_initialize()