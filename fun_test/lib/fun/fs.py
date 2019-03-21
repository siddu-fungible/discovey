from lib.system.fun_test import fun_test, FunTimer
from lib.host.dpcsh_client import DpcshClient
from lib.host.linux import Linux
from asset.asset_manager import AssetManager
from fun_settings import TFTP_SERVER, FUN_TEST_DIR
import re
import os



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


class Bmc(Linux):
    U_BOOT_INTERFACE_PATH = "/tmp/u_boot_interface.py"
    F1_UART_LOG_LISTENER_PATH = "/tmp/uart_log_listener.py"
    BMC_SCRIPT_DIRECTORY = "/mnt/sdmmc0p1/scripts"

    @fun_test.safe
    def ping(self,
             dst,
             count=5,
             max_percentage_loss=50,
             timeout=30,
             interval=1,
             size=56,
             sudo=False):
        result = False
        percentage_loss = 100
        try:
            command = 'ping %s -c %d -s %s' % (str(dst), count, size)
            if sudo:
                output = self.sudo_command(command, timeout=timeout)
            else:
                output = self.command(command, timeout=timeout)
            m = re.search(r'(\d+)%\s+packet\s+loss', output)
            if m:
                percentage_loss = int(m.group(1))
        except Exception as ex:
            critical_str = str(ex)
            fun_test.critical(critical_str)
            self.logger.critical(critical_str)
        if percentage_loss <= max_percentage_loss:
            result = True
        return result

    def _set_term_settings(self):
        self.command("stty cols %d" % 1024)
        self.sendline(chr(0))
        self.handle.expect(self.prompt_terminator, timeout=1)
        return True

    def come_reset(self, come, max_wait_time=180):
        self.command("cd {}".format(self.BMC_SCRIPT_DIRECTORY))
        fun_test.test_assert(self.ping(come.host_ip), "ComE reachable before reset")
        self.command("./come-power.sh")
        fun_test.sleep("ComE powering down", seconds=15)
        fun_test.test_assert(not self.ping(come.host_ip), "ComE should be unreachable")

        # Ensure come restarted
        come_restart_timer = FunTimer(max_time=max_wait_time)
        ping_result = False
        while not come_restart_timer.is_expired():
            ping_result = self.ping(come.host_ip)
            if ping_result:
                break
            fun_test.sleep("ComE power up")
        fun_test.test_assert(not come_restart_timer.is_expired() and ping_result, "ComE reachable")
        return True

    def position_support_scripts(self):
        utilities_dir = FUN_TEST_DIR + "/lib/utilities"

        files_to_position = ["u_boot_interface.py", "uart_log_listener.py"]
        target_directory = "/tmp"
        for file_to_position in files_to_position:
            fun_test.scp(source_file_path=utilities_dir + "/" + file_to_position,
                         target_file_path=target_directory, target_ip=self.host_ip,
                         target_username=self.ssh_username, target_password=self.ssh_password)

    def initialize(self, reset=False):
        self.command("cd {}".format(self.BMC_SCRIPT_DIRECTORY))
        self.command("./f1_console.sh 1")
        self.position_support_scripts()
        return True

    def get_f1_device_paths(self):
        output = self.command("./f1_uartmux.sh 1")
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
        return f1_info

class ComE(Linux):
    EXPECTED_FUNQ_DEVICE_ID = "04:00.1"
    DEFAULT_DPC_PORT = 40220

    def initialize(self, reset=False):
        self.funq_bind_device = None
        self.dpc_ready = None
        fun_test.simple_assert(self.setup_workspace(), "ComE workspace setup")
        fun_test.simple_assert(self.cleanup_dpc(), "Cleanup dpc")
        return True

    def get_dpc_port(self, f1_index):
        return self.DEFAULT_DPC_PORT

    def setup_workspace(self):
        working_directory = "/tmp"
        self.command("cd {}".format(working_directory))
        self.command("mkdir -p workspace; cd workspace")
        self.command("export WORKSPACE=$PWD")
        self.command(
            "wget http://dochub.fungible.local/doc/jenkins/funcontrolplane/latest/functrlp_palladium.tgz")
        files = self.list_files("functrlp_palladium.tgz")
        fun_test.test_assert(len(files), "functrlp_palladium.tgz downloaded")
        self.command("wget http://dochub.fungible.local/doc/jenkins/funsdk/latest/Linux/dpcsh.tgz")
        fun_test.test_assert(self.list_files("dpcsh.tgz"), "functrlp_palladium.tgz downloaded")
        self.command("mkdir -p FunControlPlane FunSDK")
        self.command("tar -zxvf functrlp_palladium.tgz -C ../workspace/FunControlPlane")
        self.command("tar -zxvf dpcsh.tgz -C ../workspace/FunSDK")
        return True


    def cleanup_dpc(self):
        self.command("cd $WORKSPACE/FunControlPlane")
        self.sudo_command("pkill dpc")
        self.sudo_command("build/posix/bin/funq-setup unbind")
        return True

    def setup_dpc(self):
        dpc_log = "/tmp/dpc.txt"
        self.command("cd $WORKSPACE/FunControlPlane")
        output = self.sudo_command("build/posix/bin/funq-setup bind")
        fun_test.test_assert("Binding {}".format(self.funq_bind_device) in output, "Bound to {}".format(self.funq_bind_device))
        command = "LD_LIBRARY_PATH=$PWD/build/posix/lib build/posix/bin/dpc -j -d {} &> {} &".format(self.funq_bind_device, dpc_log)
        self.sudo_command(command)
        fun_test.sleep("dpc socket creation")
        output = self.command("cat {}".format(dpc_log))
        fun_test.test_assert("socket creation: Success" in output, "DPC Socket creation success")
        self.dpc_ready = True
        return True

    def detect_pfs(self):
        devices = self.lspci(grep_filter="dad")
        fun_test.test_assert(devices, "PCI devices detected")
        for device in devices:
            if "Unassigned class" in device["device_class"]:
                self.funq_bind_device = device["id"]
        fun_test.test_assert_expected(actual=self.funq_bind_device,
                                      expected=self.EXPECTED_FUNQ_DEVICE_ID,
                                      message="funq bind device found")
        return True

    def is_dpc_ready(self):
        return self.dpc_ready

class F1InFs:
    def __init__(self, index, fs, serial_device_path, serial_sbp_device_path):
        self.index = index
        self.fs = fs
        self.serial_device_path = serial_device_path
        self.serial_sbp_device_path = serial_sbp_device_path
        self.dpc_port = None

    def get_dpc_client(self):
        come = self.fs.get_come()
        host_ip = come.host_ip
        dpc_port = come.get_dpc_port(self.index)
        dpcsh_client = DpcshClient(target_ip=host_ip, target_port=dpc_port)
        return dpcsh_client

    def set_dpc_port(self, port):
        self.dpc_port = port

    #def bootup(self):
    #    fun_test.test_assert(self.u_boot_load_image(), "u-boot load image")
    #    return True




class Fs():
    SERIAL_SPEED_DEFAULT = 1000000
    ELF_ADDRESS = "0xffffffff99000000"

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
        self.f1_uart_log_process_ids = {}  # stores process id for f1 uart log listener started in background

    def reachability_check(self):
        # TODO
        pass

    def cleanup(self):
        for f1_index, f1 in self.f1s.iteritems():
            uart_log_filename = self.get_f1_uart_log_filename(f1_index)
            artifact_file_name = fun_test.get_test_case_artifact_file_name("f1_{}_uart_log.txt".format(f1_index))

            fun_test.scp(source_ip=self.bmc.host_ip,
                         source_file_path=uart_log_filename,
                         source_username=self.bmc.ssh_username,
                         source_password=self.bmc.ssh_password,
                         source_port=22,
                         target_file_path=artifact_file_name)
            fun_test.add_auxillary_file(description="F1_{} UART Log".format(f1_index),
                                        filename=artifact_file_name)
    def get_f1_0(self):
        return self.get_f1(index=0)

    def get_f1_1(self):
        return self.get_f1(index=1)

    def get_f1(self, index):
        return self.f1s[index]

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
        fun_test.test_assert(self.set_f1s(), "Set F1s")
        fun_test.test_assert(self.fpga_initialize(), "FPGA initiaize")

        for f1_index, f1 in self.f1s.iteritems():
            fun_test.test_assert(self.u_boot_load_image(index=f1_index), "U-Bootup f1: {} complete".format(f1_index))

        for f1_index, f1 in self.f1s.iteritems():
            self.kill_f1_uart_log_listener(f1_index=f1_index)

        for f1_index, f1 in self.f1s.iteritems():
            self.setup_f1_uart_log_listener(f1_index=f1_index)

        fun_test.test_assert(self.come_reset(), "ComE rebooted successfully")
        fun_test.test_assert(self.come_initialize(), "ComE initialized")
        fun_test.test_assert(self.come.detect_pfs(), "Fungible PFs detected")
        fun_test.test_assert(self.come.setup_dpc(), "Setup DPC")
        fun_test.test_assert(self.come.is_dpc_ready(), "DPC ready")


        for f1_index, f1 in self.f1s.iteritems():
            f1.set_dpc_port(self.come.get_dpc_port(f1_index))

        return True

    def come_reset(self):
        return self.bmc.come_reset(self.get_come())

    def get_f1_uart_log_filename(self, f1_index):
        return "/tmp/f1_{}_uart_log.txt".format(f1_index)

    def kill_f1_uart_log_listener(self, f1_index):
        process_ids = self.bmc.get_process_id_by_pattern("{}".format(os.path.basename(self.bmc.F1_UART_LOG_LISTENER_PATH)), multiple=True)
        if process_ids:
            for process_id in process_ids:
                self.bmc.kill_process(process_id=process_id)

    def setup_f1_uart_log_listener(self, f1_index):
        f1 = self.get_f1(index=f1_index)
        command = "python {} --device_path={} --speed={} --log_filename={}".format(self.bmc.F1_UART_LOG_LISTENER_PATH,
                                            f1.serial_device_path,
                                                                            self.SERIAL_SPEED_DEFAULT,
                                                                            self.get_f1_uart_log_filename(f1_index=f1_index))
        process_id = self.bmc.start_bg_process(command, nohup=False)
        self.set_uart_log_process_id(f1_index=f1_index, process_id=process_id)

    def set_uart_log_process_id(self, f1_index, process_id):
        pass

    def set_boot_phase(self, index, phase):
        self.boot_phase = phase
        fun_test.add_checkpoint("Started boot phase: {}".format(phase))
        fun_test.log_section("F1_{}:{}".format(index, phase))

    def u_boot_command(self, f1_index, command, timeout=15, expected=None):
        output = self.bmc.command("python {} --device_path={} --speed {} --command='{}' --timeout={}".format(self.bmc.U_BOOT_INTERFACE_PATH, self.f1s[f1_index].serial_device_path,
                                                                                           self.SERIAL_SPEED_DEFAULT,
                                                                                                          command, timeout), timeout=timeout + 5)
        if expected:
            fun_test.simple_assert(expected in output, "{} not in output: {}".format(expected, output))
        return output

    def u_boot_load_image(self,
                          index,
                          tftp_load_address="0xa800000080000000",
                          tftp_server=TFTP_SERVER):
        result = None
        handle = self.bmc.handle
        self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_INIT)

        self.u_boot_command(command="lfw; lmpg; ltrain; lstatus", timeout=15, expected='Fifo Out of Reset', f1_index=index)
        self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_TRAIN)

        self.u_boot_command(command="setenv bootargs app=hw_hsu_test sku=SKU_FS1600_{} --dis-stats --disable-wu-watchdog --dpc-server --dpc-uart --csr-replay --serdesinit".format(index), timeout=5, f1_index=index)
        self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_SET_BOOT_ARGS)

        self.u_boot_command(command="dhcp", timeout=15, expected="our IP address is", f1_index=index)
        self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_DHCP)

        output = self.u_boot_command(command="tftpboot {} {}:funos-f1.stripped.gz".format(tftp_load_address, tftp_server), timeout=15, f1_index=index)
        m = re.search(r'Bytes transferred = (\d+)', output)
        if m:
            bytes_transferred = int(m.group(1))
            fun_test.test_assert(bytes_transferred > 1000, "FunOs download size: {}".format(bytes_transferred))
            self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_TFTP_DOWNLOAD)

        output = self.u_boot_command(command="unzip {} {};".format(tftp_load_address, self.ELF_ADDRESS), timeout=10, f1_index=index)
        m = re.search(r'Uncompressed size: (\d+) =', output)
        if m:
            uncompressed_size = int(m.group(1))
            fun_test.test_assert(uncompressed_size > 1000, "FunOs uncompressed size: {}".format(uncompressed_size))
            self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_UNCOMPRESS_IMAGE)

        output = self.u_boot_command(command="bootelf -p {}".format(self.ELF_ADDRESS), timeout=60, f1_index=index)
        m = re.search(r'Version=(\S+), Branch=(\S+)', output)
        if m:
            version = m.group(1)
            branch = m.group(2)
            fun_test.add_checkpoint("Version: {}, branch: {}".format(version, branch))
        self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_ELF)

        sections = ['Welcome to FunOS', 'NETWORK_START', 'DPC_SERVER_STARTED', 'PCI_STARTED']
        for section in sections:
            fun_test.test_assert(section in output, "{} seen".format(section))

        result = True
        return result


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
            self.come = ComE(host_ip=self.come_mgmt_ip,
                             ssh_username=self.come_mgmt_ssh_username,
                             ssh_password=self.come_mgmt_ssh_password, set_term_settings=True)
        return self.come

    def come_initialize(self):
        self.come.initialize()
        return True


    def bmc_initialize(self):
        self.bmc = Bmc(host_ip=self.bmc_mgmt_ip,
                         ssh_username=self.bmc_mgmt_ssh_username,
                         ssh_password=self.bmc_mgmt_ssh_password, set_term_settings=True)
        self.bmc.set_prompt_terminator(r'# $')
        fun_test.simple_assert(self.bmc._connect(), "BMC connected")
        fun_test.simple_assert(self.bmc.initialize(), "BMC initialize")

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

    def set_f1s(self):
        result = None
        f1_info = self.bmc.get_f1_device_paths()
        for f1_index in sorted(f1_info.keys()):
            self.f1s[f1_index] = F1InFs(index=f1_index,
                                        fs=self,
                                        serial_device_path=f1_info[f1_index]["f1_device_path"],
                                        serial_sbp_device_path=f1_info[f1_index]["sbp_device_path"])

            if f1_index > 0:
                fun_test.critical("Disabling F1_1 for now")
                continue

        fun_test.simple_assert(len(self.f1s.keys()), "Both F1 device paths found")
        result = True
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
    fs = Fs.get(AssetManager().get_fs_by_name(name="fs-9"))
    #fs.bootup(reboot_bmc=False)
    #fs.come_initialize()
    #fs.come_reset()
    come = fs.get_come()
    come.detect_pfs()
    come.setup_dpc()