from lib.system.fun_test import fun_test, FunTimer
from lib.host.dpcsh_client import DpcshClient
from lib.host.storage_controller import StorageController
from lib.host.network_controller import NetworkController
from lib.host.linux import Linux
from fun_settings import TFTP_SERVER_IP, FUN_TEST_LIB_UTILITIES_DIR, INTEGRATION_DIR
from lib.utilities.netcat import Netcat
from lib.system.utils import ToDictMixin

from threading import Thread
import re
import os


class UartLogger(Thread):
    def __init__(self, ip, port):
        super(UartLogger, self).__init__()
        self.ip = ip
        self.port = port
        self.stopped = False
        self.buf = ""
        self.nc = None

    def run(self):
        self.nc = Netcat(ip=self.ip, port=self.port)
        try:
            while not self.stopped and not fun_test.closed:
                self.buf += self.nc.read_until(expected_data="PUlsAr", timeout=5)
        except Exception as ex:
            pass

    def get_log(self):
        return self.buf

    def close(self):
        self.stopped = True
        if self.nc:
            self.buf += self.nc.close()


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


class Fpga(Linux):
    NUM_F1S = 2

    def __init__(self, disable_f1_index=None, **kwargs):
        super(Fpga, self).__init__(**kwargs)
        self.disable_f1_index = disable_f1_index

    def initialize(self):
        fun_test.add_checkpoint("FPGA initialize")
        for f1_index in range(self.NUM_F1S):
            if f1_index == self.disable_f1_index:
                continue
            self.reset_f1(f1_index=f1_index)
        fun_test.sleep("FPGA reset", seconds=10)

        result = True
        return result

    def reset_f1(self, f1_index):
        self.command("./f1reset -s {0} 0; sleep 2; ./f1reset -s {0} 1".format(f1_index))
        output = self.command("./f1reset -g")
        fun_test.simple_assert("F1_{} is out of reset".format(f1_index) in output,
                               "F1 {} out of reset".format(f1_index))

    def _set_term_settings(self):
        self.command("stty cols %d" % 1024)
        self.sendline(chr(0))
        self.handle.expect(self.prompt_terminator, timeout=1)
        return True

class Bmc(Linux):
    U_BOOT_INTERFACE_PATH = "/tmp/u_boot_interface.py"
    UART_LOG_LISTENER_FILE = "uart_log_listener.py"
    BMC_UART_LOG_LISTENER_PATH = "/tmp/{}".format(UART_LOG_LISTENER_FILE)
    BMC_SCRIPT_DIRECTORY = "/mnt/sdmmc0p1/scripts"
    BMC_INSTALL_DIRECTORY = "/mnt/sdmmc0p1/_install"
    SERIAL_PROXY_PORTS = [9990, 9991]
    ELF_ADDRESS = "0xffffffff99000000"
    SERIAL_SPEED_DEFAULT = 1000000
    U_BOOT_F1_PROMPT = "f1 #"
    NUM_F1S = 2

    def __init__(self, disable_f1_index=None, disable_uart_logger=False, **kwargs):
        super(Bmc, self).__init__(**kwargs)
        self.uart_log_threads = {}
        self.disable_f1_index = disable_f1_index
        self.disable_uart_logger = disable_uart_logger
        self.uart_log_listener_process_ids = []
        self.u_boot_logs = ["" for x in range(self.NUM_F1S)]  # for each F1

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

    def get_uart_log(self):
        for f1_index in range(self.NUM_F1S):
            if f1_index == self.disable_f1_index:
                continue
            self.uart_log_threads[f1_index].close()

    def _get_ipmi_details(self):
        ipmi_details = {
            "username": "admin",
            "password": "admin",
            "host_ip": self.host_ip
        }
        return ipmi_details

    def come_reset(self, come, max_wait_time=180, power_cycle=True, non_blocking=None):
        self.command("cd {}".format(self.BMC_SCRIPT_DIRECTORY))
        ipmi_details = self._get_ipmi_details()
        fun_test.test_assert(come.ensure_host_is_up(max_wait_time=max_wait_time, ipmi_details=ipmi_details),
                             "Ensure ComE is reachable before reboot")

        fun_test.log("Rebooting ComE")
        reboot_result = come.reboot(max_wait_time=max_wait_time, non_blocking=non_blocking, ipmi_details=ipmi_details)
        reboot_info_string = "initiated" if non_blocking else "complete"
        fun_test.test_assert(reboot_result, "ComE reboot {}".format(reboot_info_string))
        # if not non_blocking:
        #    fun_test.test_assert(self.ensure_come_is_up(come=come, max_wait_time=max_wait_time, power_cycle=power_cycle), "Ensure ComE is up")

        return True

    def ensure_come_is_up(self, come, max_wait_time=240, power_cycle=True):
        come_up = False
        come_up = come.ensure_host_is_up(max_wait_time=max_wait_time, ipmi_details=self._get_ipmi_details())
        return come_up

    def set_boot_phase(self, index, phase):
        self.boot_phase = phase
        fun_test.add_checkpoint("F1_{}: Started boot phase: {}".format(index, phase))
        fun_test.log_section("F1_{}:{}".format(index, phase))

    def u_boot_command(self, f1_index, command, timeout=15, expected=None):
        nc = Netcat(ip=self.host_ip, port=self.SERIAL_PROXY_PORTS[f1_index])
        nc.write(command + "\n")
        output = nc.read_until(expected_data=expected, timeout=timeout)
        fun_test.log(output)
        if expected:
            fun_test.simple_assert(expected in output, "{} not in output".format(expected))
        output = nc.close()
        self.u_boot_logs[f1_index] += output
        return output

    def start_uart_log_listener(self, f1_index, serial_device):

        """
        t = UartLogger(ip=self.host_ip, port=self.SERIAL_PROXY_PORTS[f1_index])
        self.uart_log_threads[f1_index] = t
        if not self.disable_uart_logger:
            t.start()
        """
        output_file = self.get_f1_uart_log_filename(f1_index=f1_index)
        process_id = self.start_bg_process("python {} --proxy_port={} --output_file={}".format(self.BMC_UART_LOG_LISTENER_PATH,
                                                                                                self.SERIAL_PROXY_PORTS[f1_index],
                                                                                                output_file), nohup=False)
        self.uart_log_listener_process_ids.append(process_id)

    def _get_boot_args_for_index(self, boot_args, f1_index):
        return "sku=SKU_FS1600_{} ".format(f1_index) + boot_args

    def u_boot_load_image(self,
                          index,
                          boot_args,
                          tftp_load_address="0xa800000080000000",
                          tftp_server=TFTP_SERVER_IP,
                          tftp_image_path="funos-f1.stripped.gz",
                          gateway_ip=None):
        result = None
        self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_INIT)

        # self.u_boot_command(command="lfw; lmpg; ltrain; lstatus", timeout=15, expected='Fifo Out of Reset',
        self.u_boot_command(command="lfw; lmpg; ltrain; lstatus", timeout=15, expected=self.U_BOOT_F1_PROMPT,

                            f1_index=index)
        self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_TRAIN)

        if gateway_ip:
            self.u_boot_command(command="setenv gatewayip {}".format(gateway_ip), timeout=10, expected=self.U_BOOT_F1_PROMPT,
                                f1_index=index)

        self.u_boot_command(command="setenv serverip {}".format(TFTP_SERVER_IP), timeout=10, expected=self.U_BOOT_F1_PROMPT,
                            f1_index=index)
        self.u_boot_command(
            command="setenv bootargs {}".format(
                self._get_boot_args_for_index(boot_args=boot_args, f1_index=index)), timeout=5, f1_index=index, expected=self.U_BOOT_F1_PROMPT)
        self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_SET_BOOT_ARGS)


        self.u_boot_command(command="dhcp", timeout=15, expected=self.U_BOOT_F1_PROMPT, f1_index=index)
        self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_DHCP)

        output = self.u_boot_command(
            command="tftpboot {} {}:{}".format(tftp_load_address, tftp_server, tftp_image_path), timeout=15,
            f1_index=index, expected=self.U_BOOT_F1_PROMPT)
        m = re.search(r'Bytes transferred = (\d+)', output)
        bytes_transferred = 0
        if m:
            bytes_transferred = int(m.group(1))
            self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_TFTP_DOWNLOAD)
        fun_test.test_assert(bytes_transferred > 1000, "FunOs download size: {}".format(bytes_transferred))

        output = self.u_boot_command(command="unzip {} {};".format(tftp_load_address, self.ELF_ADDRESS), timeout=10,
                                     f1_index=index, expected=self.U_BOOT_F1_PROMPT)
        m = re.search(r'Uncompressed size: (\d+) =', output)
        uncompressed_size = 0
        if m:
            uncompressed_size = int(m.group(1))
            self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_UNCOMPRESS_IMAGE)
        fun_test.test_assert(uncompressed_size > 1000, "FunOs uncompressed size: {}".format(uncompressed_size))

        fun_test.sleep("Uncompress image")

        output = self.u_boot_command(command="bootelf -p {}".format(self.ELF_ADDRESS), timeout=80, f1_index=index, expected="CRIT hw_hsu_test \"this space intentionally left blank.\"")
        m = re.search(r'Version=(\S+), Branch=(\S+)', output)
        if m:
            version = m.group(1)
            branch = m.group(2)
            fun_test.add_checkpoint("Version: {}, branch: {}".format(version, branch))
            fun_test.set_version(version=version.replace("bld_", ""))
        self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_ELF)

        sections = ['Welcome to FunOS', 'NETWORK_START', 'DPC_SERVER_STARTED', 'PCI_STARTED']
        for section in sections:
            fun_test.test_assert(section in output, "{} seen".format(section))

        result = True
        return result

    def _reset_microcom(self):
        fun_test.log("Resetting microcom and minicom")
        process_ids = self.get_process_id_by_pattern("microcom", multiple=True)
        for process_id in process_ids:
            self.kill_process(signal=9, process_id=process_id)
        process_ids = self.get_process_id_by_pattern("minicom", multiple=True)
        for process_id in process_ids:
            self.kill_process(signal=9, process_id=process_id)

    def position_support_scripts(self):
        self._reset_microcom()
        pyserial_filename = "pyserial-install.tar"
        pyserial_dir = INTEGRATION_DIR + "/tools/platform/bmc/{}".format(pyserial_filename)
        fun_test.scp(source_file_path=pyserial_dir, target_ip=self.host_ip, target_username=self.ssh_username, target_password=self.ssh_password, target_file_path=self.BMC_INSTALL_DIRECTORY)
        fun_test.simple_assert(self.list_files("{}/{}".format(self.BMC_INSTALL_DIRECTORY, pyserial_filename)), "pyserial copied")

        self.command("cd {}".format(self.BMC_INSTALL_DIRECTORY))
        self.command("tar -xvf {}".format(pyserial_filename))

        serial_proxy_ids = self.get_process_id_by_pattern("python.*999", multiple=True)
        for serial_proxy_id in serial_proxy_ids:
            self.kill_process(signal=9, process_id=serial_proxy_id)
        serial_proxy_ids = self.get_process_id_by_pattern("python.*999")
        fun_test.simple_assert(not serial_proxy_ids, "old serial proxies are alive")

        self.command("bash web/fungible/RUN_TCP_PYSERIAL.sh")
        serial_proxy_ids = self.get_process_id_by_pattern("python.*999", multiple=True)
        fun_test.simple_assert(len(serial_proxy_ids) == 2, "2 serial proxies are alive")


        uart_listener_script = FUN_TEST_LIB_UTILITIES_DIR + "/{}".format(self.UART_LOG_LISTENER_FILE)
        fun_test.scp(source_file_path=uart_listener_script,
                     target_ip=self.host_ip,
                     target_username=self.ssh_username,
                     target_password=self.ssh_password,
                     target_file_path=self.BMC_UART_LOG_LISTENER_PATH)
        fun_test.simple_assert(self.list_files(self.BMC_UART_LOG_LISTENER_PATH), "UART log listener copied")
        log_listener_processes = self.get_process_id_by_pattern(self.UART_LOG_LISTENER_FILE, multiple=True)
        for log_listener_process in log_listener_processes:
            self.kill_process(signal=9, process_id=log_listener_process)



    def initialize(self, reset=False):
        self.command("cd {}".format(self.BMC_SCRIPT_DIRECTORY))
        self.command("./f1_console.sh 1")
        self.position_support_scripts()
        return True

    def reset_come(self):
        self.command("cd {}".format(self.BMC_SCRIPT_DIRECTORY))
        bmc_files = self.command(command='ls')
        if "come.sh" in bmc_files:
            self.command(command="./come.sh 2")
        elif "come-power.sh" in bmc_files:
            self.command(command="./come-power.sh")
        return True

    def host_power_cycle(self):
        return self.ipmi_power_cycle(host=self.host_ip, user="admin", passwd="admin", chassis=False)  #TODO: What are these credentials

    def is_host_pingable(self, host_ip, max_time):
        result = False
        # Ensure come restarted
        max_timer = FunTimer(max_time=max_time)
        ping_result = False
        while not max_timer.is_expired():
            ping_result = self.ping(host_ip)
            if ping_result:
                break
            fun_test.sleep("host {}: power up".format(host_ip))
        if not max_timer.is_expired() and ping_result:
            result = True
        return result


    def cleanup(self):
        fun_test.sleep("Allowing time to generate full report", seconds=45)

        # fun_test.log("U-boot logs: {}: END".format(self.u_boot_logs))
        """
        for f1_index, uart_log_thread in self.uart_log_threads.iteritems():
            artifact_file_name = fun_test.get_test_case_artifact_file_name("f1_{}_uart_log.txt".format(f1_index))
            uart_log_thread.close()
            log = uart_log_thread.get_log()
            with open(artifact_file_name, "w") as f:
                f.write(log)
            fun_test.add_auxillary_file(description="F1_{} UART Log".format(f1_index),
                                        filename=artifact_file_name)
        """

        for f1_index in range(self.NUM_F1S):
            if self.disable_f1_index is not None and f1_index == self.disable_f1_index:
                continue
            log_listener_processes = self.get_process_id_by_pattern(self.UART_LOG_LISTENER_FILE + ".*_{}.*txt".format(f1_index), multiple=True)
            for log_listener_process in log_listener_processes:
                self.kill_process(signal=15, process_id=int(log_listener_process))
                self.kill_process(signal=9, process_id=log_listener_process)

                artifact_file_name = fun_test.get_test_case_artifact_file_name("f1_{}_uart_log.txt".format(f1_index))
                fun_test.scp(source_ip=self.host_ip,
                             source_file_path=self.get_f1_uart_log_filename(f1_index=f1_index),
                             source_username=self.ssh_username,
                             source_password=self.ssh_password,
                             target_file_path=artifact_file_name)
                with open(artifact_file_name, "r+") as f:
                    content = f.read()
                    f.seek(0, 0)
                    f.write(self.u_boot_logs[f1_index] + '\n' + content)

                fun_test.add_auxillary_file(description="F1_{} UART Log".format(f1_index),
                                            filename=artifact_file_name)


    def get_f1_device_paths(self):
        self.command("cd {}".format(self.BMC_SCRIPT_DIRECTORY))
        output = self.command("./f1_uartmux.sh 1")
        lines = output.split("\n")
        f1_info = {}
        for line in lines:
            m = re.search(r'F1\[(\d+)\]\s+(\S+)\s+(\S+)', line)
            if m:
                f1_index = int(m.group(1))
                console_or_sbp = m.group(2)
                device_path = m.group(3)
                if f1_index == self.disable_f1_index:
                    fun_test.log("Disabling F1_{} for this run".format(f1_index))
                    continue
                if f1_index not in f1_info:
                    f1_info[f1_index] = {}
                if console_or_sbp == "console":
                    f1_info[f1_index]["f1_device_path"] = device_path
                if console_or_sbp == "SBP":
                    f1_info[f1_index]["sbp_device_path"] = device_path
        return f1_info

    def get_f1_uart_log_filename(self, f1_index):
        return "/tmp/f1_{}_uart_log.txt".format(f1_index)


class ComE(Linux):
    EXPECTED_FUNQ_DEVICE_ID = ["04:00.1", "06:00.1"]
    DEFAULT_DPC_PORT = [40220, 40221]
    DPC_LOG_PATH = "/tmp/f1_{}_dpc.txt"
    NUM_F1S = 2
    NVME_CMD_TIMEOUT = 600000

    def initialize(self, reset=False, disable_f1_index=None):
        self.disable_f1_index = disable_f1_index
        self.funq_bind_device = {}
        self.dpc_ready = None
        fun_test.simple_assert(self.setup_workspace(), "ComE workspace setup")
        fun_test.simple_assert(self.cleanup_dpc(), "Cleanup dpc")
        for f1_index in range(self.NUM_F1S):
            self.command("rm -f {}".format(self.get_dpc_log_path(f1_index=f1_index)))

        fun_test.test_assert(self.detect_pfs(), "Fungible PFs detected")
        fun_test.test_assert(self.setup_dpc(), "Setup DPC")
        fun_test.test_assert(self.is_dpc_ready(), "DPC ready")
        return True

    def get_dpc_port(self, f1_index):
        return self.DEFAULT_DPC_PORT[f1_index]

    def setup_workspace(self):
        working_directory = "/tmp"
        self.command("cd {}".format(working_directory))
        self.command("mkdir -p workspace; cd workspace")
        self.command("export WORKSPACE=$PWD")
        self.command(
            "wget http://10.1.20.99/doc/jenkins/funcontrolplane/latest/functrlp_palladium.tgz")
        files = self.list_files("functrlp_palladium.tgz")
        fun_test.test_assert(len(files), "functrlp_palladium.tgz downloaded")
        self.command("wget http://10.1.20.99/doc/jenkins/funsdk/latest/Linux/dpcsh.tgz")
        fun_test.test_assert(self.list_files("dpcsh.tgz"), "functrlp_palladium.tgz downloaded")
        self.command("mkdir -p FunControlPlane FunSDK")
        self.command("tar -zxvf functrlp_palladium.tgz -C ../workspace/FunControlPlane")
        self.command("tar -zxvf dpcsh.tgz -C ../workspace/FunSDK")
        return True

    def cleanup_dpc(self):
        self.command("cd $WORKSPACE/FunControlPlane")
        self.sudo_command("pkill dpc")
        self.sudo_command("pkill dpcsh")
        self.sudo_command("build/posix/bin/funq-setup unbind")
        return True

    def setup_dpc(self):

        self.command("cd $WORKSPACE/FunControlPlane")
        output = self.sudo_command("build/posix/bin/funq-setup bind")
        for f1_index in range(self.NUM_F1S):
            if f1_index == self.disable_f1_index:
                continue
            fun_test.test_assert("Binding {}".format(self.funq_bind_device[f1_index]) in output,
                                 "Bound to {}".format(self.funq_bind_device[f1_index]))
        for f1_index in range(self.NUM_F1S):
            if f1_index == self.disable_f1_index:
                continue
            # command = "LD_LIBRARY_PATH=$PWD/build/posix/lib build/posix/bin/dpc -j -d {} &> {} &".format(
            #    self.funq_bind_device[f1_index], self.get_dpc_log_path(f1_index=f1_index))

            self.command("cd $WORKSPACE/FunSDK/bin/Linux")
            self.modprobe("nvme")
            fun_test.sleep("After modprobe", seconds=5)

            nvme_devices = self.list_files("/dev/nvme*")
            fun_test.test_assert(nvme_devices, "At least one nvme device detected")
            # self.command("ls /dev/nvm*")
            nvme_device_index = f1_index
            if len(nvme_devices) == 1:  # if only one nvme device was detected
                nvme_device_index = 0
            command = "./dpcsh --pcie_nvme_sock=/dev/nvme{} --nvme_cmd_timeout={} --tcp_proxy={} &> {} &".format(nvme_device_index, self.NVME_CMD_TIMEOUT, self.get_dpc_port(f1_index=f1_index), self.get_dpc_log_path(f1_index=f1_index))
            self.sudo_command(command)
            fun_test.sleep("dpc socket creation")
            # output = self.command("cat {}".format(self.get_dpc_log_path(f1_index=f1_index)))
            # fun_test.test_assert("socket creation: Success" in output, "DPC Socket creation success")
        self.dpc_ready = True
        return True

    def is_dpc_running(self):
        pass

    def expected_funq_device_id(self):
        pass

    def detect_pfs(self):
        devices = self.lspci(grep_filter="1dad")
        fun_test.test_assert(devices, "PCI devices detected")

        f1_index = 0
        num_pfs_detected = 0
        if self.disable_f1_index is not None:
            f1_index = filter(lambda x: x != self.disable_f1_index, range(self.NUM_F1S))[0]

        for device in devices:
            if "Unassigned class" in device["device_class"]:
                device_id = device["id"]
                if num_pfs_detected:
                    f1_index += 1
                # fun_test.simple_assert(device_id in self.EXPECTED_FUNQ_DEVICE_ID, "Device-Id: {} not in expected list: {}".format(device_id, self.EXPECTED_FUNQ_DEVICE_ID))
                self.funq_bind_device[f1_index] = device_id


                num_pfs_detected += 1

        '''
        for f1_index in range(self.NUM_F1S):
            if f1_index == self.disable_f1_index:
                continue
            fun_test.test_assert_expected(actual=self.funq_bind_device[f1_index],
                                          expected=self.EXPECTED_FUNQ_DEVICE_ID[f1_index],
                                          message="F1_{} funq bind device found".format(f1_index))
        '''
        fun_test.test_assert(num_pfs_detected, "At least one PF detected")
        return True

    def ensure_dpc_running(self):
        result = None
        process_id = self.get_process_id_by_pattern("dpc")
        fun_test.log("Dpc process id: {}".format(process_id))
        if not process_id:
            self.setup_dpc()
        self.dpc_ready = True
        result = True
        return result

    def is_dpc_ready(self):
        return self.dpc_ready

    def get_dpc_log_path(self, f1_index):
        return self.DPC_LOG_PATH.format(f1_index)

    def cleanup(self):
        for f1_index in range(self.NUM_F1S):
            if f1_index == self.disable_f1_index:
                continue
            artifact_file_name = fun_test.get_test_case_artifact_file_name("f1_{}_dpc_log.txt".format(f1_index))
            fun_test.scp(source_file_path=self.get_dpc_log_path(f1_index=f1_index), source_ip=self.host_ip, source_password=self.ssh_password, source_username=self.ssh_username, target_file_path=artifact_file_name)
            fun_test.add_auxillary_file(description="F1_{} DPC Log".format(f1_index),
                                        filename=artifact_file_name)

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

    def get_dpc_storage_controller(self):
        come = self.fs.get_come()
        return StorageController(target_ip=come.host_ip, target_port=come.get_dpc_port(self.index))

    def get_dpc_network_controller(self):
        come = self.fs.get_come()
        return NetworkController(dpc_server_ip=come.host_ip, dpc_server_port=come.get_dpc_port(self.index))

    def set_dpc_port(self, port):
        self.dpc_port = port



class Fs(object, ToDictMixin):
    #  sku=SKU_FS1600_{}
    DEFAULT_BOOT_ARGS = "app=hw_hsu_test --dis-stats --dpc-server --dpc-uart --csr-replay --serdesinit --all_100g"

    TO_DICT_VARS = ["bmc_mgmt_ip",
                    "bmc_mgmt_ssh_username",
                    "bmc_mgmt_ssh_password",
                    "fpga_mgmt_ip",
                    "fpga_mgmt_ssh_username",
                    "fpga_mgmt_ssh_password",
                    "come_mgmt_ip",
                    "come_mgmt_ssh_username",
                    "come_mgmt_ssh_password"]
    NUM_F1S = 2

    def __init__(self,
                 bmc_mgmt_ip,
                 bmc_mgmt_ssh_username,
                 bmc_mgmt_ssh_password,
                 fpga_mgmt_ip,
                 fpga_mgmt_ssh_username,
                 fpga_mgmt_ssh_password,
                 come_mgmt_ip,
                 come_mgmt_ssh_username,
                 come_mgmt_ssh_password,
                 tftp_image_path="funos-f1.stripped.gz",
                 boot_args=DEFAULT_BOOT_ARGS,
                 power_cycle_come=False,
                 disable_f1_index=None,
                 disable_uart_logger=None,
                 f1_parameters=None,
                 gateway_ip=None,
                 retimer_workaround=None):
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
        self.tftp_image_path = tftp_image_path
        self.disable_f1_index = disable_f1_index
        self.f1s = {}
        self.boot_args = boot_args
        self.power_cycle_come = power_cycle_come
        self.disable_uart_logger = disable_uart_logger
        self.come_initialized = False
        self.f1_parameters = f1_parameters
        self.gateway_ip = gateway_ip
        self.retimer_workround = retimer_workaround

    def reachability_check(self):
        # TODO
        pass

    def cleanup(self):
        self.bmc.cleanup()
        self.come.cleanup()

    def get_f1_0(self):
        return self.get_f1(index=0)

    def get_f1_1(self):
        return self.get_f1(index=1)

    def get_f1(self, index):
        return self.f1s[index]

    @staticmethod
    def get(fs_spec=None,
            tftp_image_path=None,
            boot_args=None,
            disable_f1_index=None,
            disable_uart_logger=None,
            f1_parameters=None,
            retimer_workaround=None):  #TODO
        if not fs_spec:
            am = fun_test.get_asset_manager()
            test_bed_type = fun_test.get_job_environment_variable("test_bed_type")
            fun_test.log("Testbed-type: {}".format(test_bed_type))
            test_bed_spec = am.get_test_bed_spec(name=test_bed_type)
            fun_test.simple_assert(test_bed_spec, "Test-bed spec for {}".format(test_bed_spec))
            dut_name = test_bed_spec["dut_info"]["0"]["dut"]
            fs_spec = am.get_fs_by_name(dut_name)
            fun_test.simple_assert(fs_spec, "Fs spec for {}".format(dut_name))

        if not tftp_image_path:
            tftp_image_path = fun_test.get_build_parameter("tftp_image_path")
        fun_test.test_assert(tftp_image_path, "TFTP image path: {}".format(tftp_image_path))

        if not boot_args:
            boot_args = fun_test.get_build_parameter("BOOTARGS")
            if not boot_args:
                boot_args = Fs.DEFAULT_BOOT_ARGS
        fun_test.simple_assert(fs_spec, "Testbed spec available")
        bmc_spec = fs_spec["bmc"]
        fpga_spec = fs_spec["fpga"]
        come_spec = fs_spec["come"]
        gateway_ip = fs_spec.get("gateway_ip", None)
        workarounds = fs_spec.get("workarounds", {})
        retimer_workaround = workarounds.get("retimer_workaround", None)
        return Fs(bmc_mgmt_ip=bmc_spec["mgmt_ip"],
                  bmc_mgmt_ssh_username=bmc_spec["mgmt_ssh_username"],
                  bmc_mgmt_ssh_password=bmc_spec["mgmt_ssh_password"],
                  fpga_mgmt_ip=fpga_spec["mgmt_ip"],
                  fpga_mgmt_ssh_username=fpga_spec["mgmt_ssh_username"],
                  fpga_mgmt_ssh_password=fpga_spec["mgmt_ssh_password"],
                  come_mgmt_ip=come_spec["mgmt_ip"],
                  come_mgmt_ssh_username=come_spec["mgmt_ssh_username"],
                  come_mgmt_ssh_password=come_spec["mgmt_ssh_password"],
                  tftp_image_path=tftp_image_path,
                  boot_args=boot_args,
                  disable_f1_index=disable_f1_index,
                  disable_uart_logger=disable_uart_logger,
                  gateway_ip=gateway_ip,
                  f1_parameters=f1_parameters,
                  retimer_workaround=retimer_workaround)

    def bootup(self, reboot_bmc=False, power_cycle_come=True, non_blocking=False):

        if reboot_bmc:
            fun_test.test_assert(self.reboot_bmc(), "Reboot BMC")
        fun_test.test_assert(self.bmc_initialize(), "BMC initialize")

        if self.retimer_workround:
            self._apply_retimer_workaround()

        fun_test.test_assert(self.set_f1s(), "Set F1s")
        fun_test.test_assert(self.fpga_initialize(), "FPGA initiaize")

        for f1_index, f1 in self.f1s.iteritems():
            if f1_index == self.disable_f1_index:
                continue
            boot_args = self.boot_args
            if self.f1_parameters:
                if f1_index in self.f1_parameters:
                    if "boot_args" in self.f1_parameters[f1_index]:
                        boot_args = self.f1_parameters[f1_index]["boot_args"]
            fun_test.test_assert(self.bmc.u_boot_load_image(index=f1_index, tftp_image_path=self.tftp_image_path, boot_args=boot_args, gateway_ip=self.gateway_ip), "U-Bootup f1: {} complete".format(f1_index))
            fun_test.update_job_environment_variable("tftp_image_path", self.tftp_image_path)
            self.bmc.start_uart_log_listener(f1_index=f1_index, serial_device=self.f1s.get(f1_index).serial_device_path)

        if True:
            self.get_come()
            fun_test.test_assert(self.come_reset(power_cycle=self.power_cycle_come or power_cycle_come, non_blocking=non_blocking), "ComE rebooted successfully. Non-blocking: {}".format(non_blocking))
            if not non_blocking:
                fun_test.test_assert(self.come.initialize(disable_f1_index=self.disable_f1_index), "ComE initialized")
                self.come_initialized = True
                '''
                fun_test.test_assert(self.come.detect_pfs(), "Fungible PFs detected")
                fun_test.test_assert(self.come.setup_dpc(), "Setup DPC")
                fun_test.test_assert(self.come.is_dpc_ready(), "DPC ready")
                '''
            for f1_index, f1 in self.f1s.iteritems():
                f1.set_dpc_port(self.come.get_dpc_port(f1_index))

        # else:
        #    fun_test.critical("Skipping ComE initialization as retimer was used")
        try:
            self.get_bmc().disconnect()
            self.get_fpga().disconnect()
            self.get_come().disconnect()
        except:
            pass
        return True

    def _apply_retimer_workaround(self): #TODO:
        bmc = self.get_bmc()
        bmc.command("gpiotool 57 --get-data")
        bmc.command("gpiotool 57 --set-data-low")
        bmc.command("sleep 2")
        bmc.command("gpiotool 57 --set-data-high")
        bmc.command("sleep 2")
        fun_test.add_checkpoint("Retimer workarounds applied")

    def is_ready(self):
        if not self.come_initialized:
            come = self.get_come()
            fun_test.test_assert(self.bmc.ensure_come_is_up(come=come, max_wait_time=240, power_cycle=True), "Ensure ComE is up")
            fun_test.test_assert(come.initialize(disable_f1_index=self.disable_f1_index), "ComE initialized")
            self.come_initialized = True
        return True

    def come_reset(self, power_cycle=None, non_blocking=None, max_wait_time=300):
        return self.bmc.come_reset(come=self.get_come(),
                                   power_cycle=power_cycle,
                                   non_blocking=non_blocking,
                                   max_wait_time=max_wait_time)

    def re_initialize(self):
        self.get_bmc(disable_f1_index=self.disable_f1_index)
        self.bmc.position_support_scripts()
        self.get_fpga()
        self.get_come()
        self.set_f1s()
        self.come.detect_pfs()
        fun_test.test_assert(self.come.ensure_dpc_running(), "Ensure dpc is running")
        for f1_index, f1 in self.f1s.iteritems():
            self.bmc.start_uart_log_listener(f1_index=f1_index)
        return True

    def get_bmc(self, disable_f1_index=None):
        if not self.bmc:
            self.bmc = Bmc(disable_f1_index=disable_f1_index, host_ip=self.bmc_mgmt_ip,
                           ssh_username=self.bmc_mgmt_ssh_username,
                           ssh_password=self.bmc_mgmt_ssh_password, set_term_settings=True,
                           disable_uart_logger=self.disable_uart_logger)
            self.bmc.set_prompt_terminator(r'# $')
        return self.bmc

    def get_fpga(self):
        if not self.fpga:
            self.fpga = Fpga(host_ip=self.fpga_mgmt_ip,
                            ssh_username=self.fpga_mgmt_ssh_username,
                            ssh_password=self.fpga_mgmt_ssh_password,
                            set_term_settings=True,
                             disable_f1_index=self.disable_f1_index)
        return self.fpga

    def get_come(self):
        if not self.come:
            self.come = ComE(host_ip=self.come_mgmt_ip,
                             ssh_username=self.come_mgmt_ssh_username,
                             ssh_password=self.come_mgmt_ssh_password,
                             set_term_settings=True)
            self.come.disable_f1_index = self.disable_f1_index
        return self.come

    def come_initialize(self):
        self.get_come()
        self.come.initialize(disable_f1_index=self.disable_f1_index)
        return True

    def bmc_initialize(self):
        bmc = self.get_bmc(disable_f1_index=self.disable_f1_index)
        fun_test.simple_assert(bmc._connect(), "BMC connected")
        fun_test.simple_assert(bmc.initialize(), "BMC initialize")

        return bmc

    def from_bmc_reset_come(self):
        bmc = self.get_bmc(disable_f1_index=self.disable_f1_index)
        fun_test.simple_assert(bmc._connect(), "BMC connected")
        fun_test.simple_assert(bmc.reset_come(), "BMC reset COMe")

        return bmc

    def fpga_initialize(self):
        return self.get_fpga().initialize()

    def set_f1s(self):
        result = None
        f1_info = self.bmc.get_f1_device_paths()
        for f1_index in sorted(f1_info.keys()):
            if f1_index == self.disable_f1_index:
                continue
            self.f1s[f1_index] = F1InFs(index=f1_index,
                                        fs=self,
                                        serial_device_path=f1_info[f1_index]["f1_device_path"],
                                        serial_sbp_device_path=f1_info[f1_index]["sbp_device_path"])

            # if f1_index > 0:
            #    fun_test.critical("Disabling F1_1 for now")
            #    continue

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
    fs = Fs.get(AssetManager().get_fs_by_name(name="fs-9"), "funos-f1.stripped.gz")
    fs.get_bmc().position_support_scripts()
    # fs.bootup(reboot_bmc=False)
    # fs.come_initialize()
    # fs.come_reset()
    # come = fs.get_come()
    # come.detect_pfs()
    # come.setup_dpc()
