from lib.system.fun_test import fun_test, FunTimer
from lib.host.dpcsh_client import DpcshClient
from lib.host.storage_controller import StorageController
from lib.host.network_controller import NetworkController
from lib.host.linux import Linux
from fun_settings import TFTP_SERVER_IP, FUN_TEST_LIB_UTILITIES_DIR, INTEGRATION_DIR
from lib.utilities.netcat import Netcat
from lib.system.utils import ToDictMixin
from lib.host.apc_pdu import ApcPdu

from threading import Thread
from datetime import datetime
import re
import os

"""
Possible workarounds:
    "workarounds": {
      "disable_u_boot_version_validation": true,
      "retimer_workaround": true,
      "skip_funeth_come_power_cycle": true
    }
"""


class BootPhases:
    U_BOOT_INIT = "u-boot: init"
    U_BOOT_MICROCOM_STARTED = "u-boot: microcom started"
    U_BOOT_TRAIN = "u-boot: train"
    U_BOOT_SET_ETH_ADDR = "u-boot: set ethaddr"
    U_BOOT_SET_GATEWAY_IP = "u-boot: set gatewayip"
    U_BOOT_SET_SERVER_IP = "u-boot: set serverip"
    U_BOOT_SET_BOOT_ARGS = "u-boot: set boot args"
    U_BOOT_DHCP = "u-boot: dhcp"
    U_BOOT_TFTP_DOWNLOAD = "u-boot: tftp download"
    U_BOOT_UNCOMPRESS_IMAGE = "u-boot: uncompress image"
    U_BOOT_ELF = "u-boot: bootelf"
    U_BOOT_COMPLETE = "u-boot: complete"

    FS_BRING_UP_INIT = "FS_BRING_UP_INIT"
    FS_BRING_UP_FUNETH_UNLOAD_COME_POWER_CYCLE = "FS_BRING_UP_FUNETH_UNLOAD_COME_POWER_CYCLE"
    FS_BRING_UP_BMC_INITIALIZE = "FS_BRING_UP_BMC_INITIALIZE"
    FS_BRING_UP_FPGA_INITIALIZE = "FS_BRING_UP_FPGA_INITIALIZE"
    FS_BRING_UP_U_BOOT = "FS_BRING_UP_U_BOOT"
    FS_BRING_UP_U_BOOT_COMPLETE = "FS_BRING_UP_U_BOOT_COMPLETE"
    FS_BRING_UP_COME_REBOOT_INITIATE = "FS_BRING_UP_COME_REBOOT_INITIATE"
    FS_BRING_UP_COME_ENSURE_UP = "FS_BRING_UP_COME_ENSURE_UP"
    FS_BRING_UP_CALL_FUNCP_CALLBACK = "FS_BRING_UP_CALL_FUNCP_CALLBACK"
    FS_BRING_UP_COME_INITIALIZE = "FS_BRING_UP_COME_INITIALIZE"
    FS_BRING_UP_COME_INITIALIZE_WORKER_THREAD = "FS_BRING_UP_COME_INITIALIZE_WORKER_THREAD"
    FS_BRING_UP_COMPLETE = "FS_BRING_UP_COMPLETE"
    FS_BRING_UP_ERROR = "FS_BRING_UP_ERROR"



class Fpga(Linux):
    NUM_F1S = 2

    def __init__(self, disable_f1_index=None, **kwargs):
        super(Fpga, self).__init__(**kwargs)
        self.disable_f1_index = disable_f1_index

    def initialize(self):
        fun_test.add_checkpoint(checkpoint="FPGA initialize", context=self.context)
        for f1_index in range(self.NUM_F1S):
            if f1_index == self.disable_f1_index:
                continue
            self.reset_f1(f1_index=f1_index)
        fun_test.sleep(message="FPGA reset", seconds=5, context=self.context)

        result = True
        return result

    def reset_f1(self, f1_index, keep_low=False):
        self.command("./f1reset -s {0} 0; sleep 2;".format(f1_index))
        if not keep_low:
            self.command("./f1reset -s {0} 1".format(f1_index))
        output = self.command("./f1reset -g")
        if not keep_low:
            fun_test.simple_assert(expression="F1_{} is out of reset".format(f1_index) in output,
                                   message="F1 {} out of reset".format(f1_index),
                                   context=self.context)

    def _set_term_settings(self):
        self.command("stty cols %d" % 1024)
        self.sendline(chr(0))
        self.handle.expect(self.prompt_terminator, timeout=1)
        return True


class Bmc(Linux):
    UART_LOG_LISTENER_FILE = "uart_log_listener.py"
    UART_LOG_LISTENER_PATH = "/tmp/{}".format(UART_LOG_LISTENER_FILE)
    SCRIPT_DIRECTORY = "/mnt/sdmmc0p1/scripts"
    INSTALL_DIRECTORY = "/mnt/sdmmc0p1/_install"
    SERIAL_PROXY_PORTS = [9990, 9991]
    ELF_ADDRESS = "0xffffffff99000000"
    SERIAL_SPEED_DEFAULT = 1000000
    U_BOOT_F1_PROMPT = "f1 #"
    NUM_F1S = 2

    def __init__(self, disable_f1_index=None, disable_uart_logger=False, setup_support_files=None, **kwargs):
        super(Bmc, self).__init__(**kwargs)
        self.uart_log_threads = {}
        self.disable_f1_index = disable_f1_index
        self.disable_uart_logger = disable_uart_logger
        self.uart_log_listener_process_ids = []
        self.u_boot_logs = ["" for x in range(self.NUM_F1S)]  # for each F1
        self.original_context_description = None
        if self.context:
            self.original_context_description = self.context.description
        self.setup_support_files = setup_support_files
        self.nc = {}  # nc connections to serial proxy indexed by f1_index

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
            fun_test.critical(message=critical_str, context=self.context)
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

    def come_power_cycle(self):
        ipmi_details = self._get_ipmi_details()
        ipmi_host_ip = ipmi_details["host_ip"]
        ipmi_username = ipmi_details["username"]
        ipmi_password = ipmi_details["password"]
        service_host_spec = fun_test.get_asset_manager().get_regression_service_host_spec()
        service_host = None
        power_on_result = False
        if service_host_spec:
            service_host = Linux(**service_host_spec)
        else:
            fun_test.log("Regression service host could not be instantiated. Trying BMC")
            service_host = self

        try:
            service_host.ipmi_power_off(host=ipmi_host_ip, user=ipmi_username, passwd=ipmi_password, chassis=True)
            fun_test.log("IPMI power-cycle off complete")
        except Exception as ex:
            fun_test.critical(str(ex))
        try:
            power_on_result = service_host.ipmi_power_on(host=ipmi_host_ip, user=ipmi_username, passwd=ipmi_password, chassis=True)
            fun_test.log("IPMI power-cycle on complete")
        except Exception as ex:
            fun_test.critical(str(ex))
        fun_test.simple_assert(power_on_result, "IPMI power on")
        return True

    def come_reset(self, come, max_wait_time=180, power_cycle=True, non_blocking=None):
        self.command("cd {}".format(self.SCRIPT_DIRECTORY))
        ipmi_details = self._get_ipmi_details()
        fun_test.test_assert(expression=come.ensure_host_is_up(max_wait_time=max_wait_time,
                                                               ipmi_details=ipmi_details,
                                                               power_cycle=power_cycle),
                             message="Ensure ComE is reachable before reboot",
                             context=self.context)

        fun_test.log("Rebooting ComE (Graceful)")
        reboot_result = come.reboot(max_wait_time=max_wait_time, non_blocking=non_blocking, ipmi_details=ipmi_details)
        reboot_info_string = "initiated" if non_blocking else "complete"
        fun_test.test_assert(expression=reboot_result,
                             message="ComE reboot {} (Graceful)".format(reboot_info_string),
                             context=self.context)
        return True

    def ensure_come_is_up(self, come, max_wait_time=300, power_cycle=True):
        come_up = come.ensure_host_is_up(max_wait_time=max_wait_time, ipmi_details=self._get_ipmi_details(), power_cycle=power_cycle)
        return come_up

    def set_boot_phase(self, index, phase):
        self.boot_phase = phase
        fun_test.add_checkpoint(checkpoint="F1_{}: Started boot phase: {}".format(index, phase), context=self.context)
        fun_test.log_section(message="F1_{}:{}".format(index, phase), context=self.context)

    def u_boot_command(self, f1_index, command, timeout=15, expected=None):
        # nc = Netcat(ip=self.host_ip, port=self.SERIAL_PROXY_PORTS[f1_index])
        nc = self.nc[f1_index]
        nc.write(command + "\n")
        output = nc.read_until(expected_data=expected, timeout=timeout)
        fun_test.log(message=output, context=self.context)
        if expected:
            fun_test.simple_assert(expression=expected in output,
                                   message="{} in output".format(expected),
                                   context=self.context)
        # output = nc.close()
        self.u_boot_logs[f1_index] += output
        return output

    def start_uart_log_listener(self, f1_index, serial_device):
        output_file = self.get_f1_uart_log_filename(f1_index=f1_index)
        process_id = self.start_bg_process("python {} --proxy_port={} --output_file={}".format(self.UART_LOG_LISTENER_PATH,
                                                                                                self.SERIAL_PROXY_PORTS[f1_index],
                                                                                                output_file), nohup=False)
        self.uart_log_listener_process_ids.append(process_id)

    def _get_boot_args_for_index(self, boot_args, f1_index):
        return "sku=SKU_FS1600_{} ".format(f1_index) + boot_args

    def setup_serial_proxy_connection(self, f1_index):
        self.nc[f1_index] = Netcat(ip=self.host_ip, port=self.SERIAL_PROXY_PORTS[f1_index])
        nc = self.nc[f1_index]
        fun_test.execute_thread_after(0, nc.read_until, expected_data=self.U_BOOT_F1_PROMPT, timeout=20)
        # output = nc.read_until(expected_data=self.U_BOOT_F1_PROMPT, timeout=2)
        # fun_test.log(message=output, context=self.context)

        return True

    def validate_u_boot_version(self, f1_index, minimum_date):
        result = False
        nc = self.nc[f1_index]
        nc.stop_reading()
        fun_test.sleep("Reading preamble")
        output = nc.get_buffer()
        fun_test.log(message=output, context=self.context)

        m = re.search("U-Boot\s+\S+\s+\((.*)\s+-", output)  # Based on U-Boot 2017.01-00000-bld_6654 (May 29 2019 - 05:38:02 +0000)
        if m:
            try:
                this_date = datetime.strptime(m.group(1), "%b %d %Y")
                fun_test.add_checkpoint("u-boot date: {}".format(this_date))
                fun_test.log("Mininum u-boot build date: {}".format(minimum_date))
                fun_test.test_assert(this_date >= minimum_date, "Valid u-boot build date")
                result = True
            except Exception as ex:
                fun_test.critical("Unable to parse u-boot build date")
        return result

    def u_boot_load_image(self,
                          index,
                          boot_args,
                          tftp_load_address="0xa800000080000000",
                          tftp_server=TFTP_SERVER_IP,
                          tftp_image_path="funos-f1.stripped.gz",
                          gateway_ip=None):
        result = None

        self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_INIT)

        self.u_boot_command(command="setenv autoload no",
                            timeout=15,
                            expected=self.U_BOOT_F1_PROMPT,
                            f1_index=index)

        self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_TRAIN)
        self.u_boot_command(command="lfw; lmpg; ltrain; lstatus",
                            timeout=15,
                            expected=self.U_BOOT_F1_PROMPT,
                            f1_index=index)

        if gateway_ip:
            self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_SET_GATEWAY_IP)
            self.u_boot_command(command="setenv gatewayip {}".format(gateway_ip), timeout=10, expected=self.U_BOOT_F1_PROMPT,
                                f1_index=index)

        self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_SET_SERVER_IP)
        self.u_boot_command(command="setenv serverip {}".format(TFTP_SERVER_IP), timeout=10, expected=self.U_BOOT_F1_PROMPT,
                            f1_index=index)

        self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_SET_BOOT_ARGS)
        self.u_boot_command(
            command="setenv bootargs {}".format(
                self._get_boot_args_for_index(boot_args=boot_args, f1_index=index)), timeout=5, f1_index=index, expected=self.U_BOOT_F1_PROMPT)

        fun_test.add_checkpoint("BOOTARGS: {}".format(boot_args), context=self.context)
        self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_DHCP)
        self.u_boot_command(command="dhcp", timeout=15, expected=self.U_BOOT_F1_PROMPT, f1_index=index)

        self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_TFTP_DOWNLOAD)
        output = self.u_boot_command(
            command="tftpboot {} {}:{}".format(tftp_load_address, tftp_server, tftp_image_path), timeout=15,
            f1_index=index, expected=self.U_BOOT_F1_PROMPT)
        m = re.search(r'Bytes transferred = (\d+)', output)
        bytes_transferred = 0
        if m:
            bytes_transferred = int(m.group(1))

        fun_test.test_assert(bytes_transferred > 1000, "FunOs download size: {}".format(bytes_transferred))

        self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_UNCOMPRESS_IMAGE)
        output = self.u_boot_command(command="unzip {} {};".format(tftp_load_address, self.ELF_ADDRESS), timeout=10,
                                     f1_index=index, expected=self.U_BOOT_F1_PROMPT)
        m = re.search(r'Uncompressed size: (\d+) =', output)
        uncompressed_size = 0
        if m:
            uncompressed_size = int(m.group(1))
        fun_test.test_assert(expression=uncompressed_size > 1000,
                             message="FunOs uncompressed size: {}".format(uncompressed_size),
                             context=self.context)

        self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_ELF)
        output = self.u_boot_command(command="bootelf -p {}".format(self.ELF_ADDRESS), timeout=80, f1_index=index, expected="CRIT hw_hsu_test \"this space intentionally left blank.\"")
        m = re.search(r'Version=(\S+), Branch=(\S+)', output)
        if m:
            version = m.group(1)
            branch = m.group(2)
            fun_test.add_checkpoint(checkpoint="Version: {}, branch: {}".format(version, branch), context=self.context)
            fun_test.set_version(version=version.replace("bld_", ""))

        sections = ['Welcome to FunOS', 'NETWORK_START', 'DPC_SERVER_STARTED', 'PCI_STARTED']
        for section in sections:
            fun_test.test_assert(expression=section in output,
                                 message="{} seen".format(section),
                                 context=self.context)
        self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_COMPLETE)
        result = True
        try:
            self.nc[index].close()
            fun_test.log("Disconnected nc")
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def _reset_microcom(self):
        fun_test.log("Resetting microcom and minicom")
        process_ids = self.get_process_id_by_pattern("microcom", multiple=True)
        for process_id in process_ids:
            self.kill_process(signal=9, process_id=process_id, kill_seconds=2)
        process_ids = self.get_process_id_by_pattern("minicom", multiple=True)
        for process_id in process_ids:
            self.kill_process(signal=9, process_id=process_id, kill_seconds=2)

    def position_support_scripts(self):
        self._reset_microcom()
        pyserial_filename = "pyserial-install.tar"
        pyserial_dir = INTEGRATION_DIR + "/tools/platform/bmc/{}".format(pyserial_filename)
        if self.setup_support_files:
            fun_test.scp(source_file_path=pyserial_dir, target_ip=self.host_ip, target_username=self.ssh_username, target_password=self.ssh_password, target_file_path=self.INSTALL_DIRECTORY)
            fun_test.simple_assert(expression=self.list_files("{}/{}".format(self.INSTALL_DIRECTORY, pyserial_filename)),
                                   message="pyserial copied",
                                   context=self.context)

        self.command("cd {}".format(self.INSTALL_DIRECTORY))
        if self.setup_support_files:
            self.command("tar -xvf {}".format(pyserial_filename))

        serial_proxy_ids = self.get_process_id_by_pattern("python.*999", multiple=True)
        for serial_proxy_id in serial_proxy_ids:
            self.kill_process(signal=9, process_id=serial_proxy_id, kill_seconds=2)
        serial_proxy_ids = self.get_process_id_by_pattern("python.*999")
        fun_test.simple_assert(expression=not serial_proxy_ids,
                               message="old serial proxies are alive",
                               context=self.context)

        self.command("bash web/fungible/RUN_TCP_PYSERIAL.sh")
        serial_proxy_ids = self.get_process_id_by_pattern("python.*999", multiple=True)
        fun_test.simple_assert(expression=len(serial_proxy_ids) == 2,
                               message="2 serial proxies are alive",
                               context=self.context)

        uart_listener_script = FUN_TEST_LIB_UTILITIES_DIR + "/{}".format(self.UART_LOG_LISTENER_FILE)

        fun_test.scp(source_file_path=uart_listener_script,
                     target_ip=self.host_ip,
                     target_username=self.ssh_username,
                     target_password=self.ssh_password,
                     target_file_path=self.UART_LOG_LISTENER_PATH)
        fun_test.simple_assert(expression=self.list_files(self.UART_LOG_LISTENER_PATH),
                                   message="UART log listener copied",
                                   context=self.context)
        log_listener_processes = self.get_process_id_by_pattern(self.UART_LOG_LISTENER_FILE, multiple=True)
        for log_listener_process in log_listener_processes:
            self.kill_process(signal=9, process_id=log_listener_process, kill_seconds=2)

    def initialize(self, reset=False):
        self.command("cd {}".format(self.SCRIPT_DIRECTORY))
        self.position_support_scripts()
        return True

    def reset_come(self):
        self.command("cd {}".format(self.SCRIPT_DIRECTORY))
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
            fun_test.sleep(message="host {}: power up".format(host_ip), context=self.context)
        if not max_timer.is_expired() and ping_result:
            result = True
        return result

    def _get_context_prefix(self, data):
        s = "{}".format(data)
        if self.original_context_description:
            s = "{}_{}".format(self.original_context_description.replace(":", "_"), data)
        return s

    def cleanup(self):
        fun_test.sleep(message="Allowing time to generate full report", seconds=45, context=self.context)

        for f1_index in range(self.NUM_F1S):
            if self.disable_f1_index is not None and f1_index == self.disable_f1_index:
                continue
            log_listener_processes = self.get_process_id_by_pattern(self.UART_LOG_LISTENER_FILE + ".*_{}.*txt".format(f1_index), multiple=True)
            for log_listener_process in log_listener_processes:
                self.kill_process(signal=15, process_id=int(log_listener_process))
                self.kill_process(signal=9, process_id=log_listener_process)

                artifact_file_name = fun_test.get_test_case_artifact_file_name(self._get_context_prefix("f1_{}_uart_log.txt".format(f1_index)))
                fun_test.scp(source_ip=self.host_ip,
                             source_file_path=self.get_f1_uart_log_filename(f1_index=f1_index),
                             source_username=self.ssh_username,
                             source_password=self.ssh_password,
                             target_file_path=artifact_file_name)
                with open(artifact_file_name, "r+") as f:
                    content = f.read()
                    f.seek(0, 0)
                    f.write(self.u_boot_logs[f1_index] + '\n' + content)

                fun_test.add_auxillary_file(description=self._get_context_prefix("F1_{} UART log").format(f1_index),
                                            filename=artifact_file_name)
        if self.context:
            fun_test.add_auxillary_file(description=self._get_context_prefix("bringup"),
                                        filename=self.context.output_file_path)


    def get_f1_device_paths(self):
        self.command("cd {}".format(self.SCRIPT_DIRECTORY))
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
                    fun_test.log(message="Disabling F1_{} for this run".format(f1_index), context=self.context)
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


class BootupWorker(Thread):
    def __init__(self, fs, power_cycle_come=True, non_blocking=False, context=None):
        super(BootupWorker, self).__init__()
        self.fs = fs
        self.power_cycle_come = power_cycle_come
        self.non_blocking = non_blocking
        self.context = context

    def run(self):
        fs = self.fs
        bmc = self.fs.get_bmc()
        try:
            fs.set_boot_phase(BootPhases.FS_BRING_UP_BMC_INITIALIZE)
            fun_test.test_assert(expression=fs.bmc_initialize(), message="BMC initialize", context=self.context)

            if fs.retimer_workround:
                fs._apply_retimer_workaround()

            fun_test.test_assert(expression=fs.set_f1s(), message="Set F1s", context=self.context)

            if not fs.skip_funeth_come_power_cycle:
                fs.set_boot_phase(BootPhases.FS_BRING_UP_FUNETH_UNLOAD_COME_POWER_CYCLE)
                fun_test.test_assert(expression=fs.funeth_reset(), message="Funeth ComE power-cycle ref: IN-373")

            for f1_index, f1 in fs.f1s.iteritems():
                fun_test.test_assert(bmc.setup_serial_proxy_connection(f1_index=f1_index),
                                     "Setup nc serial proxy connection")

            fs.set_boot_phase(BootPhases.FS_BRING_UP_FPGA_INITIALIZE)
            fun_test.test_assert(expression=fs.fpga_initialize(), message="FPGA initiaize", context=self.context)

            fs.set_boot_phase(BootPhases.FS_BRING_UP_U_BOOT)
            for f1_index, f1 in fs.f1s.iteritems():
                if f1_index == fs.disable_f1_index:
                    continue
                boot_args = fs.boot_args
                if fs.f1_parameters:
                    if f1_index in fs.f1_parameters:
                        if "boot_args" in fs.f1_parameters[f1_index]:
                            boot_args = fs.f1_parameters[f1_index]["boot_args"]
                if fs.validate_u_boot_version:
                    fun_test.test_assert(
                        bmc.validate_u_boot_version(f1_index=f1_index, minimum_date=fs.MIN_U_BOOT_DATE),
                        "Validate preamble")
                fun_test.test_assert(
                    expression=bmc.u_boot_load_image(index=f1_index, tftp_image_path=fs.tftp_image_path,
                                                          boot_args=boot_args, gateway_ip=fs.gateway_ip),
                    message="U-Bootup f1: {} complete".format(f1_index),
                    context=self.context)
                fun_test.update_job_environment_variable("tftp_image_path", fs.tftp_image_path)
                bmc.start_uart_log_listener(f1_index=f1_index, serial_device=fs.f1s.get(f1_index).serial_device_path)

            fs.set_boot_phase(BootPhases.FS_BRING_UP_U_BOOT_COMPLETE)
            fs.u_boot_complete = True

            come = fs.get_come()
            fs.set_boot_phase(BootPhases.FS_BRING_UP_COME_REBOOT_INITIATE)
            fun_test.test_assert(expression=fs.come_reset(power_cycle=self.power_cycle_come, non_blocking=self.non_blocking),
                                 message="ComE rebooted successfully. Non-blocking: {}".format(self.non_blocking),
                                 context=self.context)

            self.worker = ComEInitializationWorker(fs=self.fs)
            self.worker.run()
            for f1_index, f1 in fs.f1s.iteritems():
                f1.set_dpc_port(come.get_dpc_port(f1_index))
            try:
                fs.get_bmc().disconnect()
                fun_test.log(message="BMC disconnect", context=self.context)
                fs.get_fpga().disconnect()
                fs.get_come().disconnect()
            except:
                pass

            come = self.fs.get_come()
            bmc = self.fs.get_bmc()
            """
            fun_test.test_assert(expression=bmc.ensure_come_is_up(come=come, max_wait_time=300, power_cycle=True),
                                 message="Ensure ComE is up",
                                 context=self.fs.context)

            self.fs.set_boot_phase(BootPhases.FS_BRING_UP_COME_INITIALIZE)
            fun_test.test_assert(expression=self.fs.come.initialize(disable_f1_index=self.fs.disable_f1_index),
                                 message="ComE initialized",
                                 context=self.fs.context)
            """

            if self.fs.fun_cp_callback:
                fs.set_boot_phase(BootPhases.FS_BRING_UP_CALL_FUNCP_CALLBACK)
                fun_test.log("Calling fun CP callback from Fs")
                self.fs.fun_cp_callback(self.fs.get_come())
            self.fs.come_initialized = True
            self.fs.set_boot_phase(BootPhases.FS_BRING_UP_COMPLETE)

        except Exception as ex:
            fs.set_boot_phase(BootPhases.FS_BRING_UP_ERROR)
            raise ex


class ComEInitializationWorker(Thread):
    def __init__(self, fs):
        super(ComEInitializationWorker, self).__init__()
        self.fs = fs

    def run(self):
        try:
            self.fs.set_boot_phase(BootPhases.FS_BRING_UP_COME_INITIALIZE_WORKER_THREAD)
            come = self.fs.get_come()
            bmc = self.fs.get_bmc()
            self.fs.set_boot_phase(BootPhases.FS_BRING_UP_COME_ENSURE_UP)
            fun_test.test_assert(expression=bmc.ensure_come_is_up(come=come, max_wait_time=300, power_cycle=True),
                                 message="Ensure ComE is up",
                                 context=self.fs.context)

            self.fs.set_boot_phase(BootPhases.FS_BRING_UP_COME_INITIALIZE)
            fun_test.test_assert(expression=self.fs.come.initialize(disable_f1_index=self.fs.disable_f1_index),
                                 message="ComE initialized",
                                 context=self.fs.context)

            # if self.fs.fun_cp_callback:
            #    fun_test.log("Calling fun CP callback from Fs")
            #    self.fs.fun_cp_callback(self.fs.get_come())
            self.fs.come_initialized = True
            # self.fs.set_boot_phase(BootPhases.FS_BRING_UP_COMPLETE)
        except Exception as ex:
            self.fs.set_boot_phase(BootPhases.FS_BRING_UP_ERROR)
            raise ex


class ComE(Linux):
    EXPECTED_FUNQ_DEVICE_ID = ["04:00.1", "06:00.1"]
    DEFAULT_DPC_PORT = [40220, 40221]
    DPC_LOG_PATH = "/tmp/f1_{}_dpc.txt"
    NUM_F1S = 2
    NVME_CMD_TIMEOUT = 600000

    def __init__(self, **kwargs):
        super(ComE, self).__init__(**kwargs)
        self.original_context_description = None
        if self.context:
            self.original_context_description = self.context.description

    def initialize(self, reset=False, disable_f1_index=None):
        self.disable_f1_index = disable_f1_index
        self.funq_bind_device = {}
        self.dpc_ready = None
        fun_test.simple_assert(expression=self.setup_workspace(), message="ComE workspace setup", context=self.context)
        fun_test.simple_assert(expression=self.cleanup_dpc(), message="Cleanup dpc", context=self.context)
        for f1_index in range(self.NUM_F1S):
            self.command("rm -f {}".format(self.get_dpc_log_path(f1_index=f1_index)))

        fun_test.test_assert(expression=self.detect_pfs(), message="Fungible PFs detected", context=self.context)
        fun_test.test_assert(expression=self.setup_dpc(), message="Setup DPC", context=self.context)
        fun_test.test_assert(expression=self.is_dpc_ready(), message="DPC ready", context=self.context)
        return True

    def get_dpc_port(self, f1_index):
        return self.DEFAULT_DPC_PORT[f1_index]

    def setup_workspace(self):
        working_directory = "/tmp"
        self.command("cd {}".format(working_directory))
        self.command("mkdir -p workspace; cd workspace")
        self.command("export WORKSPACE=$PWD")
        # self.command(
        #     "wget http://10.1.20.99/doc/jenkins/funcontrolplane/latest/functrlp_palladium.tgz")
        # files = self.list_files("functrlp_palladium.tgz")
        # fun_test.test_assert(len(files), "functrlp_palladium.tgz downloaded")
        self.command("wget http://10.1.20.99/doc/jenkins/funsdk/latest/Linux/dpcsh.tgz")
        fun_test.test_assert(expression=self.list_files("dpcsh.tgz"),
                             message="dpcsh.tgz downloaded",
                             context=self.context)
        # self.command("mkdir -p FunControlPlane FunSDK")
        self.command("mkdir -p FunSDK")
        # self.command("tar -zxvf functrlp_palladium.tgz -C ../workspace/FunControlPlane")
        self.command("tar -zxvf dpcsh.tgz -C ../workspace/FunSDK")
        return True

    def setup_tools(self):
        if not self.command_exists("fio"):
            self.sudo_command("apt install -y fio")

    def cleanup_dpc(self):
        # self.command("cd $WORKSPACE/FunControlPlane")
        self.sudo_command("pkill dpc")
        self.sudo_command("pkill dpcsh")
        # self.sudo_command("build/posix/bin/funq-setup unbind")
        return True

    def setup_dpc(self):

        # self.command("cd $WORKSPACE/FunControlPlane")
        """
        output = self.sudo_command("build/posix/bin/funq-setup bind")
        for f1_index in range(self.NUM_F1S):
            if f1_index == self.disable_f1_index:
                continue
            fun_test.test_assert("Binding {}".format(self.funq_bind_device[f1_index]) in output,
                                 "Bound to {}".format(self.funq_bind_device[f1_index]))
        """
        self.modprobe("nvme")
        fun_test.sleep(message="After modprobe", seconds=5, context=self.context)
        nvme_devices = self.list_files("/dev/nvme*")
        fun_test.test_assert(expression=nvme_devices, message="At least one NVME device detected", context=self.context)

        for f1_index in range(self.NUM_F1S):
            if f1_index == self.disable_f1_index:
                continue

            self.command("cd $WORKSPACE/FunSDK/bin/Linux")
            nvme_device_index = f1_index
            if len(nvme_devices) == 1:  # if only one nvme device was detected
                nvme_device_index = 0
            command = "./dpcsh --pcie_nvme_sock=/dev/nvme{} --nvme_cmd_timeout={} --tcp_proxy={} &> {} &".format(nvme_device_index, self.NVME_CMD_TIMEOUT, self.get_dpc_port(f1_index=f1_index), self.get_dpc_log_path(f1_index=f1_index))
            self.sudo_command(command)

        fun_test.sleep(message="DPC socket creation", context=self.context)
        self.dpc_ready = True
        return True

    def is_dpc_running(self):
        pass

    def expected_funq_device_id(self):
        pass

    def detect_pfs(self):
        devices = self.lspci(grep_filter="1dad")
        fun_test.test_assert(expression=devices, message="PCI devices detected", context=self.context)

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
        fun_test.test_assert(expression=num_pfs_detected, message="At least one PF detected", context=self.context)
        if self.disable_f1_index is None:
            fun_test.test_assert_expected(actual=num_pfs_detected,
                                          expected=self.NUM_F1S,
                                          message="Number of PFs (Unassigned class)",
                                          context=self.context)
        return True

    def ensure_dpc_running(self):
        result = None
        process_id = self.get_process_id_by_pattern("dpc")
        fun_test.log(message="DPC process id: {}".format(process_id), context=self.context)
        if not process_id:
            self.setup_dpc()
        self.dpc_ready = True
        result = True
        return result

    def is_dpc_ready(self):
        return self.dpc_ready

    def get_dpc_log_path(self, f1_index):
        return self.DPC_LOG_PATH.format(f1_index)

    def _get_context_prefix(self, data):
        s = "{}".format(data)
        if self.original_context_description:
            s = "{}_{}".format(self.original_context_description.replace(":", "_"), data)
        return s

    def cleanup(self):
        for f1_index in range(self.NUM_F1S):
            if f1_index == self.disable_f1_index:
                continue
            artifact_file_name = fun_test.get_test_case_artifact_file_name(self._get_context_prefix("f1_{}_dpc_log.txt".format(f1_index)))
            fun_test.scp(source_file_path=self.get_dpc_log_path(f1_index=f1_index), source_ip=self.host_ip, source_password=self.ssh_password, source_username=self.ssh_username, target_file_path=artifact_file_name)
            fun_test.add_auxillary_file(description=self._get_context_prefix("F1_{} DPC Log").format(f1_index),
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
    DEFAULT_BOOT_ARGS = "app=hw_hsu_test --dpc-server --dpc-uart --csr-replay --serdesinit --all_100g"
    MIN_U_BOOT_DATE = datetime(year=2019, month=5, day=29)


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
                 retimer_workaround=None,
                 non_blocking=None,
                 context=None,
                 setup_bmc_support_files=None,
                 apc_info=None,
                 fun_cp_callback=None,
                 skip_funeth_come_power_cycle=None,
                 spec=None):
        self.spec = spec
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
        self.skip_funeth_come_power_cycle = skip_funeth_come_power_cycle
        self.non_blocking = non_blocking
        self.context = context
        self.set_boot_phase(BootPhases.FS_BRING_UP_INIT)
        self.apc_info = apc_info
        self.original_context_description = None
        self.fun_cp_callback = fun_cp_callback
        if self.context:
            self.original_context_description = self.context.description
        self.setup_bmc_support_files = setup_bmc_support_files
        self.validate_u_boot_version = True
        disable_u_boot_version_validation = self.get_workaround("disable_u_boot_version_validation")
        if disable_u_boot_version_validation is not None:
            self.validate_u_boot_version = not disable_u_boot_version_validation
        self.bootup_worker = None
        self.u_boot_complete = False
        self.come_initialized = False

    def __str__(self):
        name = self.spec.get("name", None)
        if not name:
            name = "FS"
        return name

    def is_u_boot_complete(self):
        return self.u_boot_complete

    def get_workaround(self, variable):
        value = None
        if self.spec:
            workarounds = self.spec.get("workarounds", None)
            if workarounds:
                value = workarounds.get(variable, None)
        return value

    def post_bootup(self):
        self.get_bmc().reset_context()
        self.get_come().reset_context()
        self.get_fpga().reset_context()
        self.reset_context()

    def reset_context(self):
        self.context = None

    def set_boot_phase(self, boot_phase):
        self.boot_phase = boot_phase
        fun_test.add_checkpoint(checkpoint="FS boot-phase: {}".format(self.boot_phase), context=self.context)
        fun_test.log_section(message="FS boot-phase: {}".format(self.boot_phase), context=self.context)

    def get_boot_phase(self):
        return self.boot_phase

    def reachability_check(self):
        # TODO
        pass

    def cleanup(self):
        self.get_bmc().cleanup()
        self.get_come().cleanup()

        try:
            self.get_bmc().disconnect()
            fun_test.log(message="BMC disconnect", context=self.context)
            self.get_fpga().disconnect()
            fun_test.log(message="FPGA disconnect", context=self.context)
            self.get_come().disconnect()
            fun_test.log(message="ComE disconnect", context=self.context)
        except:
            pass
        return True

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
            non_blocking=None,
            context=None,
            setup_bmc_support_files=None,
            fun_cp_callback=None,
            power_cycle_come=False,
            already_deployed=False):  #TODO
        if not fs_spec:
            am = fun_test.get_asset_manager()
            test_bed_type = fun_test.get_job_environment_variable("test_bed_type")
            fun_test.log("Testbed-type: {}".format(test_bed_type), context=context)
            test_bed_spec = am.get_test_bed_spec(name=test_bed_type)
            fun_test.simple_assert(test_bed_spec, "Test-bed spec for {}".format(test_bed_spec), context=context)
            dut_name = test_bed_spec["dut_info"]["0"]["dut"]
            fs_spec = am.get_fs_by_name(dut_name)
            fun_test.simple_assert(fs_spec, "FS spec for {}".format(dut_name), context=context)

        if not already_deployed:
            if not tftp_image_path:
                tftp_image_path = fun_test.get_build_parameter("tftp_image_path")
            fun_test.test_assert(tftp_image_path, "TFTP image path: {}".format(tftp_image_path), context=context)

        if not boot_args:
            boot_args = fun_test.get_build_parameter("BOOTARGS")
            if not boot_args:
                boot_args = Fs.DEFAULT_BOOT_ARGS
        fun_test.simple_assert(fs_spec, "Test-bed spec available", context=context)
        bmc_spec = fs_spec["bmc"]
        fpga_spec = fs_spec["fpga"]
        come_spec = fs_spec["come"]
        gateway_ip = fs_spec.get("gateway_ip", None)
        workarounds = fs_spec.get("workarounds", {})
        retimer_workaround = workarounds.get("retimer_workaround", None)
        skip_funeth_come_power_cycle = workarounds.get("skip_funeth_come_power_cycle", None)
        apc_info = fs_spec.get("apc_info", None)  # Used for power-cycling the entire FS
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
                  retimer_workaround=retimer_workaround,
                  non_blocking=non_blocking,
                  context=context,
                  setup_bmc_support_files=setup_bmc_support_files,
                  apc_info=apc_info,
                  fun_cp_callback=fun_cp_callback,
                  power_cycle_come=power_cycle_come,
                  skip_funeth_come_power_cycle=skip_funeth_come_power_cycle,
                  spec=fs_spec)

    def bootup(self, reboot_bmc=False, power_cycle_come=True, non_blocking=False, threaded=False):
        if not threaded:

            self.set_boot_phase(BootPhases.FS_BRING_UP_BMC_INITIALIZE)
            if reboot_bmc:
                fun_test.test_assert(expression=self.reboot_bmc(), message="Reboot BMC", context=self.context)
            fun_test.test_assert(expression=self.bmc_initialize(), message="BMC initialize", context=self.context)
    
            if self.retimer_workround:
                self._apply_retimer_workaround()
    
            fun_test.test_assert(expression=self.set_f1s(), message="Set F1s", context=self.context)
    
            if not self.skip_funeth_come_power_cycle:
                self.set_boot_phase(BootPhases.FS_BRING_UP_FUNETH_UNLOAD_COME_POWER_CYCLE)
                fun_test.test_assert(expression=self.funeth_reset(), message="Funeth ComE power-cycle ref: IN-373")
    
            for f1_index, f1 in self.f1s.iteritems():
                fun_test.test_assert(self.bmc.setup_serial_proxy_connection(f1_index=f1_index),
                                     "Setup nc serial proxy connection")
    
            self.set_boot_phase(BootPhases.FS_BRING_UP_FPGA_INITIALIZE)
            fun_test.test_assert(expression=self.fpga_initialize(), message="FPGA initiaize", context=self.context)
    
            self.set_boot_phase(BootPhases.FS_BRING_UP_U_BOOT)
            for f1_index, f1 in self.f1s.iteritems():
                if f1_index == self.disable_f1_index:
                    continue
                boot_args = self.boot_args
                if self.f1_parameters:
                    if f1_index in self.f1_parameters:
                        if "boot_args" in self.f1_parameters[f1_index]:
                            boot_args = self.f1_parameters[f1_index]["boot_args"]
                if self.validate_u_boot_version:
                    fun_test.test_assert(self.bmc.validate_u_boot_version(f1_index=f1_index, minimum_date=self.MIN_U_BOOT_DATE), "Validate preamble")
                fun_test.test_assert(expression=self.bmc.u_boot_load_image(index=f1_index, tftp_image_path=self.tftp_image_path, boot_args=boot_args, gateway_ip=self.gateway_ip),
                                     message="U-Bootup f1: {} complete".format(f1_index),
                                     context=self.context)
                fun_test.update_job_environment_variable("tftp_image_path", self.tftp_image_path)
                self.bmc.start_uart_log_listener(f1_index=f1_index, serial_device=self.f1s.get(f1_index).serial_device_path)
    
            self.get_come()
            self.set_boot_phase(BootPhases.FS_BRING_UP_COME_REBOOT_INITIATE)
            fun_test.test_assert(expression=self.come_reset(power_cycle=self.power_cycle_come or power_cycle_come,
                                                            non_blocking=non_blocking),
                                 message="ComE rebooted successfully. Non-blocking: {}".format(non_blocking),
                                 context=self.context)
    
            if not non_blocking:
                self.set_boot_phase(BootPhases.FS_BRING_UP_COME_INITIALIZE)
                fun_test.test_assert(expression=self.come.initialize(disable_f1_index=self.disable_f1_index),
                                     message="ComE initialized",
                                     context=self.context)

                if self.fun_cp_callback:
                    fun_test.log("Calling fun CP callback from Fs")
                #    self.fs.fun_cp_callback(self.fs.get_come())
                self.come_initialized = True
                self.set_boot_phase(BootPhases.FS_BRING_UP_COMPLETE)
            else:
                # Start thread
                self.worker = ComEInitializationWorker(fs=self)
                self.worker.start()
            for f1_index, f1 in self.f1s.iteritems():
                f1.set_dpc_port(self.come.get_dpc_port(f1_index))
    
    
            try:
                self.get_bmc().disconnect()
                fun_test.log(message="BMC disconnect", context=self.context)
                self.get_fpga().disconnect()
                self.get_come().disconnect()
            except:
                pass

        else:
            self.bootup_worker = BootupWorker(fs=self, power_cycle_come=power_cycle_come, non_blocking=non_blocking, context=self.context)
            self.bootup_worker.start()
            fun_test.sleep("Bootup worker start", seconds=3)
        return True

    def _apply_retimer_workaround(self): #TODO:
        bmc = self.get_bmc()
        bmc.command("gpiotool 57 --get-data")
        bmc.command("gpiotool 57 --set-data-low")
        bmc.command("sleep 2")
        bmc.command("gpiotool 57 --set-data-high")
        bmc.command("sleep 2")
        fun_test.add_checkpoint(checkpoint="Retimer workarounds applied", context=self.context)

    def is_boot_up_error(self):
        return self.boot_phase == BootPhases.FS_BRING_UP_ERROR

    def is_ready(self):
        fun_test.log(message="Boot-phase: {}".format(self.get_boot_phase()), context=self.context)
        return self.boot_phase == BootPhases.FS_BRING_UP_COMPLETE

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
        fun_test.test_assert(expression=self.come.ensure_dpc_running(),
                             message="Ensure dpc is running",
                             context=self.context)
        for f1_index, f1 in self.f1s.iteritems():
            self.bmc.start_uart_log_listener(f1_index=f1_index)
        return True

    def funeth_reset(self):
        fpga = self.get_fpga()

        for f1_index, f1 in self.f1s.iteritems():
            fpga.reset_f1(f1_index=f1_index, keep_low=True)
        fun_test.add_checkpoint("Reset and hold F1")

        bmc = self.get_bmc()
        fun_test.test_assert(bmc.come_power_cycle(), "Trigger ComE power-cycle")
        come = self.get_come()
        fun_test.test_assert(come.ensure_host_is_up(max_wait_time=300), "Ensure ComE is up")
        return True


    def get_bmc(self, disable_f1_index=None):
        if not self.bmc:
            self.bmc = Bmc(disable_f1_index=disable_f1_index, host_ip=self.bmc_mgmt_ip,
                           ssh_username=self.bmc_mgmt_ssh_username,
                           ssh_password=self.bmc_mgmt_ssh_password,
                           set_term_settings=True,
                           disable_uart_logger=self.disable_uart_logger,
                           context=self.context,
                           setup_support_files=self.setup_bmc_support_files)
            self.bmc.set_prompt_terminator(r'# $')
        return self.bmc

    def get_fpga(self):
        if not self.fpga:
            self.fpga = Fpga(host_ip=self.fpga_mgmt_ip,
                             ssh_username=self.fpga_mgmt_ssh_username,
                             ssh_password=self.fpga_mgmt_ssh_password,
                             set_term_settings=True,
                             disable_f1_index=self.disable_f1_index,
                             context=self.context)
        return self.fpga

    def get_come(self):
        if not self.come:
            self.come = ComE(host_ip=self.come_mgmt_ip,
                             ssh_username=self.come_mgmt_ssh_username,
                             ssh_password=self.come_mgmt_ssh_password,
                             set_term_settings=True,
                             context=self.context,
                             ipmi_info=self.get_bmc()._get_ipmi_details())
            self.come.disable_f1_index = self.disable_f1_index
        return self.come

    def come_initialize(self):
        self.get_come()
        self.come.initialize(disable_f1_index=self.disable_f1_index)
        return True

    def bmc_initialize(self):
        bmc = self.get_bmc(disable_f1_index=self.disable_f1_index)
        fun_test.simple_assert(expression=bmc._connect(), message="BMC connected", context=self.context)
        fun_test.simple_assert(expression=bmc.initialize(), message="BMC initialize", context=self.context)

        return bmc

    def from_bmc_reset_come(self):
        bmc = self.get_bmc(disable_f1_index=self.disable_f1_index)
        fun_test.simple_assert(expression=bmc._connect(), message="BMC connected", context=self.context)
        fun_test.simple_assert(expression=bmc.reset_come(), message="BMC reset COMe", context=self.context)

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

        fun_test.simple_assert(expression=len(self.f1s.keys()), message="Both F1 device paths found", context=self.context)
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
        fun_test.simple_assert(expression=not power_down_timer.is_expired(),
                               message="Power down timer is not expired",
                               context=self.context)
        fun_test.simple_assert(expression=powered_down, message="Power down detected", context=self.context)
        power_up_timer = FunTimer(max_time=180)
        while not power_up_timer.is_expired():
            try:
                bmc.command("date")
                break
            except:
                fun_test.sleep(message="Rebooting BMC", seconds=10, context=self.context)
        fun_test.simple_assert(expression=not power_up_timer.is_expired(),
                               message="Power up timer is not expired",
                               context=self.context)

        fun_test.add_checkpoint("Reboot procedure completed")
        result = True
        return result

    def apc_power_cycle(self):
        fun_test.simple_assert(expression=self.apc_info, context=self.context)
        apc_pdu = ApcPdu(context=self.context, **self.apc_info)
        power_cycle_result = apc_pdu.power_cycle(self.apc_info["outlet_number"])
        fun_test.simple_assert(expression=power_cycle_result,
                               context=self.context,
                               message="APC power-cycle result")
        try:
            apc_pdu.disconnect()
        except:
            pass
        fun_test.test_assert(expression=self.get_fpga().ensure_host_is_up(max_wait_time=120),
                             context=self.context, message="FPGA reachable after APC power-cycle")
        fun_test.test_assert(expression=self.get_bmc().ensure_host_is_up(max_wait_time=120),
                             context=self.context, message="BMC reachable after APC power-cycle")
        fun_test.test_assert(expression=self.get_come().ensure_host_is_up(max_wait_time=120,
                                                                          power_cycle=True),
                                                                          message="ComE reachable after APC power-cycle")
        return True


if __name__ == "__main2__":
    fs = Fs.get(AssetManager().get_fs_by_name(name="fs-9"), "funos-f1.stripped.gz")
    fs.get_bmc().position_support_scripts()
    # fs.bootup(reboot_bmc=False)
    # fs.come_initialize()
    # fs.come_reset()
    # come = fs.get_come()
    # come.detect_pfs()
    # come.setup_dpc()


if __name__ == "__main__":
    come = ComE(host_ip="fs21-come.fungible.local", ssh_username="fun", ssh_password="123")
    print come.setup_tools()
