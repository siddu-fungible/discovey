from lib.system.fun_test import fun_test
from lib.host.linux import Linux
from fun_settings import TFTP_SERVER

BMC_IP = "10.1.20.149"
BMC_USERNAME = "sysadmin"
BMC_PASSWORD = "superuser"
SCRIPT_DIRECTORY = "/mnt/sdmmc0p1/scripts"
l = Linux(host_ip=BMC_IP, ssh_username=BMC_USERNAME, ssh_password=BMC_PASSWORD)
l.set_prompt_terminator(r'# $')
l.command("cd {}".format(SCRIPT_DIRECTORY))
l.command("./f1_uartmux.sh 1")
l.command("./f1_console.sh 1")
process_id = l.get_process_id_by_pattern("microcom ")
if process_id:
    l.kill_process(process_id)
process_id = l.get_process_id_by_pattern("microcom ")

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

class Fs():
    ELF_ADDRESS = "0xffffffff99000000"

    def __init__(self, bmc_mgmt_ip, bmc_mgmt_ssh_username, bmc_mgmt_ssh_password):
        self.bmc_mgmt_ip = bmc_mgmt_ip
        self.bmc_mgmt_ssh_username = bmc_mgmt_ssh_username
        self.bmc_mgmt_ssh_password = bmc_mgmt_ssh_password

        self.bmc = None

    @staticmethod
    def get(spec):
        bmc_spec = spec["bmc"]
        return Fs(bmc_mgmt_ip=bmc_spec["mgmt_ip"],
                  bmc_mgmt_ssh_username=bmc_spec["mgmt_ssh_username"],
                  bmc_mgmt_ssh_password=bmc_spec["mgmt_ssh_password"])

    def set_boot_phase(self, phase):
        self.boot_phase = phase
        fun_test.log_section(phase)


    def bootup(self):
        fun_test.simple_assert(self.bmc_initialize(), "BMC initialize")
        # fun_test.

    def bmc_initialize(self):
        self.bmc = Linux(host_ip=self.bmc_mgmt_ip,
                         ssh_username=self.bmc_mgmt_ssh_username,
                         ssh_password=self.bmc_mgmt_ssh_password)
        fun_test.simple_assert(self.bmc._connect(), "BMC connected")
        return self.bmc

    def u_boot_load_image(self,
                          handle,
                          tftp_load_address="0xa800000080000000",
                          tftp_server=TFTP_SERVER):
        result = None
        self.set_boot_phase(BootPhases.U_BOOT_INIT)
        handle.sendline("microcom -s 1000000 /dev/ttyS0")
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

fs = Fs(bmc_ip=BMC_IP)
#fs.u_boot_load_image(fs.)
