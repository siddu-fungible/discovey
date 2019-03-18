from lib.system.fun_test import fun_test
from lib.system.utils import parse_file_to_json
from lib.host.linux import Linux
from fun_settings import TFTP_SERVER, ASSET_DIR
import re


# BMC_IP = "10.1.20.149"
# BMC_USERNAME = "sysadmin"
# BMC_PASSWORD = "superuser"
# l = Linux(host_ip=BMC_IP, ssh_username=BMC_USERNAME, ssh_password=BMC_PASSWORD)
# l.set_prompt_terminator(r'# $')
# l.command("cd {}".format(SCRIPT_DIRECTORY))
# l.command("./f1_uartmux.sh 1")
# l.command("./f1_console.sh 1")
# process_id = l.get_process_id_by_pattern("microcom ")
# if process_id:
#    l.kill_process(process_id)
# process_id = l.get_process_id_by_pattern("microcom ")

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


class F1InFs:
    SERIAL_SPEED_DEFAULT = 1000000
    ELF_ADDRESS = "0xffffffff99000000"
    def __init__(self, bmc, serial_device_path, serial_sbp_device_path):
        self.bmc = bmc.clone()
        self.bmc._connect()
        self.serial_device_path = serial_device_path
        self.serial_sbp_device_path = serial_sbp_device_path

    def bootup(self):
        fun_test.test_assert(self.u_boot_load_image(), "u-boot load image")
        return True

    def set_boot_phase(self, phase):
        self.boot_phase = phase
        fun_test.log_section(phase)

    def u_boot_load_image(self,
                          tftp_load_address="0xa800000080000000",
                          tftp_server=TFTP_SERVER):
        result = None
        handle = self.bmc.handle
        self.set_boot_phase(BootPhases.U_BOOT_INIT)
        handle.sendline("microcom -s {} {}".format(self.SERIAL_SPEED_DEFAULT, self.serial_device_path))
        handle.sendline("\n")
        i = handle.expect('f1 # ', timeout=20)
        self.set_boot_phase(BootPhases.U_BOOT_MICROCOM_STARTED)

        handle.sendline("lfw; lmpg; ltrain; lstatus")
        i = handle.expect('Fifo Out of Reset')
        i = handle.expect("f1 # ")
        self.set_boot_phase(BootPhases.U_BOOT_TRAIN)

        handle.sendline("setenv bootargs app=hw_hsu_test sku=SKU_FS1600_0")
        i = handle.expect("f1 # ")
        self.set_boot_phase(BootPhases.U_BOOT_SET_BOOT_ARGS)

        handle.sendline("dhcp")
        i = handle.expect("f1 # ")
        self.set_boot_phase(BootPhases.U_BOOT_DHCP)

        handle.sendline("tftpboot {} {}:funos-f1.stripped.gz".format(tftp_load_address, tftp_server))
        i = handle.expect(r'Bytes transferred = (\d+)')
        bytes_transferred = handle.match.group(1)
        self.set_boot_phase(BootPhases.U_BOOT_TFTP_DOWNLOAD)

        handle.sendline("unzip {} {};".format(tftp_load_address, self.ELF_ADDRESS))
        i = handle.expect(r'Uncompressed size: (\d+) =')
        uncompressed_size = handle.match.group(1)
        self.set_boot_phase(BootPhases.U_BOOT_UNCOMPRESS_IMAGE)

        handle.sendline("bootelf -p {}".format(self.ELF_ADDRESS))
        i = handle.expect(r'Welcome to FunOS')
        i = handle.expect(r'Version=(\S+), Branch=(\S+)')
        version = handle.match.group(1)
        branch = handle.match.group(2)
        self.set_boot_phase(BootPhases.U_BOOT_ELF)

        i = handle.expect(r'NETWORK_STARTED')
        self.set_boot_phase(BootPhases.F1_BOOT_NETWORK_STARTED)

        i = handle.expect(r'PCI_STARTED')
        self.set_boot_phase(BootPhases.F1_BOOT_PCI_STARTED)

        result = True
        return result


class Fs():
    BMC_SCRIPT_DIRECTORY = "/mnt/sdmmc0p1/scripts"

    def __init__(self, bmc_mgmt_ip, bmc_mgmt_ssh_username, bmc_mgmt_ssh_password):
        self.bmc_mgmt_ip = bmc_mgmt_ip
        self.bmc_mgmt_ssh_username = bmc_mgmt_ssh_username
        self.bmc_mgmt_ssh_password = bmc_mgmt_ssh_password
        self.bmc = None
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
        return Fs(bmc_mgmt_ip=bmc_spec["mgmt_ip"],
                  bmc_mgmt_ssh_username=bmc_spec["mgmt_ssh_username"],
                  bmc_mgmt_ssh_password=bmc_spec["mgmt_ssh_password"])

    def bootup(self):
        fun_test.simple_assert(self.bmc_initialize(), "BMC initialize")
        for f1_index, f1 in self.f1s.iteritems():
            fun_test.add_checkpoint("Booting up f1: {}".format(f1_index))
            fun_test.test_assert(f1.bootup(), "Bootup f1: {} complete".format(f1_index))

        # fun_test.

    def get_bmc(self):
        if not self.bmc:
            self.bmc_initialize()
        return self.bmc

    def bmc_initialize(self):
        self.bmc = Linux(host_ip=self.bmc_mgmt_ip,
                         ssh_username=self.bmc_mgmt_ssh_username,
                         ssh_password=self.bmc_mgmt_ssh_password)
        self.bmc.set_prompt_terminator(r'# $')
        fun_test.simple_assert(self.bmc._connect(), "BMC connected")
        self.bmc.command("cd {}".format(self.BMC_SCRIPT_DIRECTORY))
        self.bmc.command("./f1_console.sh 1")
        self._set_f1s()
        return self.bmc

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
                if f1_index not in f1_info:
                    f1_info[f1_index] = {}
                if console_or_sbp == "console":
                    f1_info[f1_index]["f1_device_path"] = device_path
                if console_or_sbp == "SBP":
                    f1_info[f1_index]["sbp_device_path"] = device_path
        # F1InFs()
        # flatten
        for f1_index in sorted(f1_info.keys()):
            self.f1s[f1_index] = F1InFs(bmc=self.bmc,
                                        serial_device_path=f1_info[f1_index]["f1_device_path"],
                                        serial_sbp_device_path=f1_info[f1_index]["sbp_device_path"])

        fun_test.simple_assert(len(self.f1s.keys()), "Both F1 device paths found")
        return result




fs_json = ASSET_DIR + "/fs.json"
json_spec = parse_file_to_json(file_name=fs_json)

fs = Fs.get(spec=json_spec[0])
fs.bootup()
# fs.u_boot_load_image(fs.)
