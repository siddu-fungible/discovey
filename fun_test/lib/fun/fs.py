from lib.system.fun_test import fun_test, FunTimer
from lib.host.dpcsh_client import DpcshClient
from lib.host.storage_controller import StorageController
from lib.host.network_controller import NetworkController
from lib.host.linux import Linux
from fun_settings import TFTP_SERVER_IP, INTEGRATION_DIR
from lib.utilities.netcat import Netcat
from lib.system.utils import ToDictMixin
from lib.host.apc_pdu import ApcPdu
from fun_settings import STASH_DIR
from fun_global import Codes, get_current_epoch_time
from asset.asset_global import AssetType
from lib.utilities.statistics_manager import StatisticsCollector, StatisticsCategory
from lib.utilities.http import fetch_text_file

from threading import Thread, Lock
from datetime import datetime
import re
import os
import socket

DOCHUB_FUNGIBLE_LOCAL = "10.1.20.99"
# ERROR_REGEXES = ["MUD_MCI_NON_FATAL_INTR_STAT", "bug_check", "platform_halt: exit status 1"]
ERROR_REGEXES = ["MUD_MCI_NON_FATAL_INTR_STAT",
                 "bug_check on",
                 "platform_halt: exit status 1",
                 "Assertion failed",
                 "Trap exception",
                 "CSR:FEP_.*_FATAL_INTR"]

DOCHUB_BASE_URL = "http://{}/doc/jenkins".format(DOCHUB_FUNGIBLE_LOCAL)

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
    U_BOOT_SET_NO_AUTOLOAD = "u-boot: setenv autoload no"
    U_BOOT_TRAIN = "u-boot: train"
    U_BOOT_SET_ETH_ADDR = "u-boot: setenv ethaddr"
    U_BOOT_SET_IPADDR = "u-boot: setenv ipaddr"
    U_BOOT_SET_GATEWAY_IP = "u-boot: setenv gatewayip"
    U_BOOT_SET_SERVER_IP = "u-boot: setenv serverip"
    U_BOOT_SET_BOOT_ARGS = "u-boot: setenv boot args"
    U_BOOT_DHCP = "u-boot: dhcp"
    U_BOOT_PING = "u-boot: ping tftp server"
    U_BOOT_TFTP_DOWNLOAD = "u-boot: tftp download"
    U_BOOT_UNCOMPRESS_IMAGE = "u-boot: uncompress image"
    U_BOOT_AUTH = "u-boot: auth"
    U_BOOT_ELF = "u-boot: bootelf"
    U_BOOT_COMPLETE = "u-boot: complete"

    FS_BRING_UP_INIT = "FS_BRING_UP_INIT"
    FS_BRING_UP_INSTALL_BUNDLE = "FS_BRING_UP_INSTALL_BUNDLE"
    FS_BRING_UP_FUNETH_UNLOAD_COME_POWER_CYCLE = "FS_BRING_UP_FUNETH_UNLOAD_COME_POWER_CYCLE"
    FS_BRING_UP_BMC_INITIALIZE = "FS_BRING_UP_BMC_INITIALIZE"
    FS_BRING_UP_FPGA_INITIALIZE = "FS_BRING_UP_FPGA_INITIALIZE"
    FS_BRING_UP_FS_RESET = "FS_BRING_UP_FS_RESET"
    FS_BRING_UP_RESET_F1 = "FS_BRING_UP_RESET_F1"
    FS_BRING_UP_U_BOOT = "FS_BRING_UP_U_BOOT"
    FS_BRING_UP_U_BOOT_COMPLETE = "FS_BRING_UP_U_BOOT_COMPLETE"
    FS_BRING_UP_COME_REBOOT_INITIATE = "FS_BRING_UP_COME_REBOOT_INITIATE"
    FS_BRING_UP_COME_ENSURE_UP = "FS_BRING_UP_COME_ENSURE_UP"
    FS_BRING_UP_CALL_FUNCP_CALLBACK = "FS_BRING_UP_CALL_FUNCP_CALLBACK"
    FS_BRING_UP_COME_INITIALIZE = "FS_BRING_UP_COME_INITIALIZE"
    FS_BRING_UP_COME_INITIALIZE_WORKER_THREAD = "FS_BRING_UP_COME_INITIALIZE_WORKER_THREAD"
    FS_BRING_UP_COME_INITIALIZED = "FS_BRING_UP_COME_INITIALIZED"
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
        # fun_test.sleep(message="FPGA reset", seconds=5, context=self.context)

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

    def switch_to_bmc_console(self, username="sysadmin", password="superuser", time_out=60):
        self.command("./BMC_console.sh {}".format(time_out),
                     custom_prompts={"console": chr(0), "login": username, "Password": password})


class Bmc(Linux):
    # UART_LOG_LISTENER_FILE = "uart_log_listener.py"
    UART_LOG_LISTENER_FILE = "uart_log_listener2.py"

    UART_LOG_LISTENER_PATH = "/tmp/{}".format(UART_LOG_LISTENER_FILE)
    SCRIPT_DIRECTORY = "/mnt/sdmmc0p1/scripts"
    INSTALL_DIRECTORY = "/mnt/sdmmc0p1/_install"
    LOG_DIRECTORY = "/mnt/sdmmc0p1/log"
    SERIAL_PROXY_PORTS = [9990, 9991]
    TFTP_LOAD_ADDRESS = "0xffffffff91000000"
    ELF_ADDRESS = "0xa800000020000000"

    SERIAL_SPEED_DEFAULT = 1000000
    U_BOOT_F1_PROMPT = "f1 #"
    NUM_F1S = 2
    FUNOS_LOGS_SCRIPT = "/mnt/sdmmc0p1/scripts/funos_logs.sh"

    def __init__(self, disable_f1_index=None,
                 disable_uart_logger=False,
                 setup_support_files=True,
                 bundle_upgraded=None,
                 bundle_compatible=None,
                 fs=None,
                 **kwargs):
        super(Bmc, self).__init__(**kwargs)
        self.set_prompt_terminator(r'# $')
        self.disable_f1_index = disable_f1_index
        self.disable_uart_logger = disable_uart_logger
        self.uart_log_listener_process_ids = []
        self.u_boot_logs = ["" for x in range(self.NUM_F1S)]  # for each F1
        self.original_context_description = None
        if self.context:
            self.original_context_description = self.context.description
        self.setup_support_files = setup_support_files
        self.nc = {}  # nc connections to serial proxy indexed by f1_index
        self.hbm_dump_enabled = fun_test.get_job_environment_variable("hbm_dump")
        self.bundle_upgraded = bundle_upgraded
        self.bundle_compatible = bundle_compatible
        self.fs = fs
        if "fs" in kwargs:
            self.fs = kwargs.get("fs", None)

    def _get_fake_mac(self, index):
        this_ip = socket.gethostbyname(self.host_ip)  # so we can resolve full fqdn/ip-string in dot-decimal
        a, b, c, d = this_ip.split('.')
        return ':'.join(['02'] + ['1d', 'ad', "%02x" % int(c), "%02x" % int(d)] + ["%02x" % int(index)])

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
        if self.fs.get_revision() in ["2"]:
            ipmi_details = None
        fun_test.test_assert(expression=come.ensure_host_is_up(max_wait_time=max_wait_time,
                                                               ipmi_details=ipmi_details,
                                                               power_cycle=power_cycle),
                             message="Ensure ComE is reachable before reboot",
                             context=self.context)

        fun_test.log("Rebooting ComE (Graceful)", context=self.context)
        if not come.was_power_cycled:

            if self.fs.get_revision() in ["2"] or self.fs.bundle_compatible:
                come.fs_reset(fast=True)
            else:
                reboot_result = come.reboot(max_wait_time=max_wait_time,
                                            non_blocking=non_blocking,
                                            ipmi_details=ipmi_details)

                reboot_info_string = "initiated" if non_blocking else "complete"
                fun_test.test_assert(expression=reboot_result,
                                     message="ComE reboot {} (Graceful)".format(reboot_info_string),
                                     context=self.context)
        else:
            fun_test.log("Skipping reboot as ComE was power-cycled")
        return True

    def ensure_come_is_up(self, come, max_wait_time=300, power_cycle=True):
        come_up = come.ensure_host_is_up(max_wait_time=max_wait_time, ipmi_details=self._get_ipmi_details(), power_cycle=power_cycle)
        return come_up

    def set_boot_phase(self, index, phase):
        self.boot_phase = phase
        result = fun_test.PASSED
        if phase == BootPhases.FS_BRING_UP_ERROR:
            result = fun_test.FAILED
        fun_test.add_checkpoint(checkpoint="F1_{}: Started boot phase: {}".format(index, phase),
                                context=self.context,
                                result=result,
                                expected=True,
                                actual=False)
        fun_test.log_section(message="F1_{}:{}".format(index, phase), context=self.context)

    def detect_version(self, output):
        try:
            m = re.search(r'FunSDK.*Version=(\S+), ', output)  # Branch=(\S+)', output)
            if m:
                version = m.group(1)
                fun_test.add_checkpoint(checkpoint="SDK Version: {}".format(version), context=self.context)
                fun_test.set_version(version=version.replace("bld_", ""))
        except Exception as ex:
            fun_test.critical(str(ex))

    def u_boot_command(self, f1_index, command, timeout=15, expected=None, write_on_trigger=None, read_buffer=1024, close_on_write_trigger=False):
        nc = self.nc[f1_index]
        nc.write(command + "\n")
        output = nc.read_until(expected_data=expected, timeout=timeout, write_on_trigger=write_on_trigger, read_buffer=read_buffer, close_on_write_trigger=close_on_write_trigger)
        self.detect_version(output)

        fun_test.log(message=output, context=self.context)
        if expected:
            fun_test.simple_assert(expression=expected in output,
                                   message="{} in output".format(expected),
                                   context=self.context)
        self.u_boot_logs[f1_index] += output
        return output

    def kill_serial_proxies(self, f1_index):
        serial_proxy_ids = self.get_process_id_by_pattern("python.*999{}".format(f1_index), multiple=True)
        for serial_proxy_id in serial_proxy_ids:
            try:
                self.kill_process(signal=9, process_id=serial_proxy_id, kill_seconds=2)
            except:
                pass
        serial_proxy_ids = self.get_process_id_by_pattern("python.*999")

    def start_bundle_f1_logs(self):
        if self.bundle_compatible:
            for f1_index in range(2):
                if f1_index == self.disable_f1_index:
                    continue
                self.kill_serial_proxies(f1_index=f1_index)
            self.command("{} start".format(self.FUNOS_LOGS_SCRIPT))

        self.command("ps -ef | grep micro")
        # self.command("{}".format(self.FUNOS_LOGS_SCRIPT))
        self.command("cat /tmp/f1_0_logpid")
        self.command("cat /tmp/f1_1_logpid")


    def stop_bundle_f1_logs(self):
        try:
            for f1_index in range(2):
                if f1_index == self.disable_f1_index:
                    continue
                # self.kill_serial_proxies(f1_index=f1_index)
            self.command("{} stop".format(self.FUNOS_LOGS_SCRIPT))
        except Exception as ex:
            fun_test.critical(str(ex))
        self.command("ps -ef | grep micro")
        self.command("{}".format(self.FUNOS_LOGS_SCRIPT))
        self.command("cat /tmp/f1_0_logpid")
        self.command("cat /tmp/f1_1_logpid")


    def start_uart_log_listener(self, f1_index, serial_device):
        self.stop_bundle_f1_logs()
        process_ids = self.get_process_id_by_pattern("microcom", multiple=True)
        self.kill_serial_proxies(f1_index=f1_index)
        output_file = self.get_f1_uart_log_file_name(f1_index=f1_index)
        self.command("rm -f /var/lock/LCK..{}".format(os.path.basename(serial_device)))
        command = "microcom -s 1000000 {} >> {}  < /dev/null &".format(serial_device, output_file)
        self.command(command)
        process_ids = self.get_process_id_by_pattern("microcom", multiple=True)

    def _get_boot_args_for_index(self, boot_args, f1_index):
        s = boot_args
        if not self.bundle_compatible and not (self.fs and self.fs.get_revision() in ["2"]):
            s = "sku=SKU_FS1600_{} ".format(f1_index) + boot_args

        if self.hbm_dump_enabled:
            if "cc_huid" not in s:
                huid = 3
                if f1_index == 1:
                    huid = 2
                s += " cc_huid={}".format(huid)
        csi_cache_miss_enabled = fun_test.get_job_environment_variable("csi_cache_miss")
        if csi_cache_miss_enabled:
            if "csi_cache_miss" not in s:
                s += " --csi-cache-miss"
        if self.fs.tftp_image_path:  # do it for rev1 system too and self.fs.get_revision() in ["2"]:
            s += " --disable-syslog-replay"
        return s

    def setup_serial_proxy_connection(self, f1_index, auto_boot=False):
        # self.stop_bundle_f1_logs()
        # self._reset_microcom()
        uart_log_file_name = self.get_f1_uart_log_file_name(f1_index)
        if not self.bundle_compatible:
            self.command("rm -f {}".format(uart_log_file_name))
        fun_test.log("Netcat: open {}:{}".format(self.host_ip, self.SERIAL_PROXY_PORTS[f1_index]))
        self.nc[f1_index] = Netcat(ip=self.host_ip, port=self.SERIAL_PROXY_PORTS[f1_index])
        return True

    def get_preamble(self, f1_index, auto_boot=False):
        nc = self.nc[f1_index]
        write_on_trigger = None
        if not auto_boot:
            write_on_trigger = {"Autoboot in": "noboot\n"}
        output = self.u_boot_command(command="",
                                     timeout=90,
                                     expected=self.U_BOOT_F1_PROMPT,
                                     f1_index=f1_index,
                                     write_on_trigger=write_on_trigger,
                                     read_buffer=512,
                                     close_on_write_trigger=True)
        # nc.stop_reading()
        # output = nc.get_buffer()
        # fun_test.log(message=output, context=self.context)
        return output

    def validate_u_boot_version(self, output, minimum_date):
        result = False
        m = re.search("U-Boot\s+\S+\s+\((.*)\s+-", output)
        # Based on U-Boot 2017.01-00000-bld_6654 (May 29 2019 - 05:38:02 +0000)
        if m:
            try:
                this_date = datetime.strptime(m.group(1), "%b %d %Y")
                fun_test.add_checkpoint("u-boot date: {}".format(this_date), context=self.context)
                fun_test.log("Minimum u-boot build date: {}".format(minimum_date), context=self.context)
                fun_test.test_assert(this_date >= minimum_date, "Valid u-boot build date", context=self.context)
                result = True
            except Exception as ex:
                fun_test.critical("Unable to parse u-boot build date", context=self.context)
        return result

    def _use_i2c_reset(self):
        result = False
        reset_file = "/mnt/sdmmc0p1/scripts/f1_reset.sh"
        if self.list_files(reset_file):
            contents = self.read_file(reset_file)
            result = "i2c-test -w -b 4 -s 0x41" in contents
        return result

    def remove_uart_logs(self, f1_index=0):
        if not self.bundle_compatible:
            self.command("rm {}".format(self.get_f1_uart_log_file_name(f1_index=f1_index)))
        elif self.bundle_compatible:
            self.command("echo 'cleared by fs.py' > {}".format(self.get_f1_uart_log_file_name(f1_index=f1_index)))

    def reset_f1(self, f1_index=0, keep_low=False):
        # Workaround for cases where autoboot is enabled, but we want to do tftpboot
        """
        gpiotool $F1_RESET_0 --set-dir-output &>/dev/null
        gpiotool $F1_RESET_1 --set-dir-output &>/dev/null

        if [ $RESET -eq 0 ]; then
            printf "F1 reset: 0\n"
            gpiotool $F1_RESET_0 --set-data-low &>/dev/null
            gpiotool $F1_RESET_1 --set-data-low &>/dev/null
        fi

        if [ $RESET -eq 1 ]; then
            printf "F1 reset: 1\n"
            gpiotool $F1_RESET_0 --set-data-high &>/dev/null
            sleep 5
            gpiotool $F1_RESET_1 --set-data-high &>/dev/null
        fi

        BMC_F1_RESET="i2c-test -w -b 4 -s 0x41 -d "
        F1_RESET_0="0x00 0xEC 0x5D 0x5C 0x01 0x00"
        F1_RESET_1="0x00 0xEC 0x5C 0x5D 0x01 0x00"

        :param f1_index:
        :return:
        """
        if not self._use_i2c_reset():
            gpio_pin = 149
            if f1_index == 1:
                gpio_pin = 150

            gpio_command = "gpiotool {} --set-dir-output &>/dev/null".format(gpio_pin)
            self.command(gpio_command)
            gpio_command = "gpiotool {} --set-data-low &>/dev/null".format(gpio_pin)
            self.command(gpio_command)
            fun_test.sleep("After F1 reset")
            if not keep_low:
                gpio_command = "gpiotool {} --set-dir-output &>/dev/null".format(gpio_pin)
                self.command(gpio_command)
                gpio_command = "gpiotool {} --set-data-high &>/dev/null".format(gpio_pin)
                self.command(gpio_command)
                fun_test.sleep("After removing F1 reset")
        else:
            bmc_f1_reset = "i2c-test -w -b 4 -s 0x41 -d "
            if f1_index == 0:
                self.command("{} {}".format(bmc_f1_reset, "0x00 0xEC 0x5D 0x5C 0x01 0x00"))
            else:
                self.command("{} {}".format(bmc_f1_reset, "0x00 0xEC 0x5C 0x5D 0x01 0x00"))


    def u_boot_load_image(self,
                          index,
                          boot_args,
                          tftp_load_address=TFTP_LOAD_ADDRESS,
                          tftp_server=TFTP_SERVER_IP,
                          tftp_image_path="funos-f1.stripped.gz",
                          gateway_ip=None,
                          mpg_ips=None):
        result = None

        is_signed_image = True if "signed" in tftp_image_path else False
        self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_INIT)

        self.u_boot_command(command="",
                            timeout=5,
                            expected=self.U_BOOT_F1_PROMPT,
                            f1_index=index)

        if not self.bundle_compatible:
            self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_SET_NO_AUTOLOAD)
            self.u_boot_command(command="setenv autoload no",
                                timeout=15,
                                expected=self.U_BOOT_F1_PROMPT,
                                f1_index=index)

        self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_SET_ETH_ADDR)
        fake_mac = self._get_fake_mac(index=index)
        self.u_boot_command(command="setenv ethaddr {}".format(fake_mac),
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
        final_boot_args = self._get_boot_args_for_index(boot_args=boot_args, f1_index=index)
        self.u_boot_command(command="setenv bootargs {}".format(final_boot_args), timeout=5, f1_index=index, expected=self.U_BOOT_F1_PROMPT)
        fun_test.add_checkpoint("BOOTARGS: {}".format(final_boot_args), context=self.context)

        if mpg_ips:
            self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_SET_IPADDR)
            self.u_boot_command(command="setenv ipaddr {}".format(mpg_ips[index]),
                                timeout=15,
                                expected=self.U_BOOT_F1_PROMPT,
                                f1_index=index)
            self.u_boot_command(command="setenv netmask 255.255.255.0",
                                timeout=15,
                                expected=self.U_BOOT_F1_PROMPT,
                                f1_index=index)
        else:
            self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_DHCP)
            self.u_boot_command(command="dhcp", timeout=15, expected=self.U_BOOT_F1_PROMPT, f1_index=index)

        self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_PING)
        self.u_boot_command(command="ping {}".format(tftp_server), timeout=15, expected=self.U_BOOT_F1_PROMPT, f1_index=index)

        self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_TFTP_DOWNLOAD)
        output = self.u_boot_command(
            command="tftpboot {} {}:{}".format(tftp_load_address, tftp_server, tftp_image_path), timeout=60,
            f1_index=index, expected=self.U_BOOT_F1_PROMPT)
        m = re.search(r'Bytes transferred = (\d+)', output)
        bytes_transferred = 0
        if m:
            bytes_transferred = int(m.group(1))

        fun_test.test_assert(bytes_transferred > 1000, "FunOS download size: {}".format(bytes_transferred), context=self.context)

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

        if is_signed_image:
            self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_AUTH)
            self.u_boot_command(command="auth {};".format(self.ELF_ADDRESS), timeout=10, f1_index=index, expected=self.U_BOOT_F1_PROMPT)

        self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_ELF)
        rich_input_boot_args = False
        rich_inputs = fun_test.get_rich_inputs()
        if rich_inputs:
            if "boot_args" in rich_inputs:
                rich_input_boot_args = True

        load_address = self.ELF_ADDRESS
        if is_signed_image:
            load_address = "${loadaddr}"

        # self.u_boot_command(command="setenv loadaddr {}".format(self.ELF_ADDRESS), timeout=80, f1_index=index,
        #                    expected=self.U_BOOT_F1_PROMPT)

        if not rich_input_boot_args:
            if "load_mods" in boot_args and "hw_hsu_test" not in boot_args:
                output = self.u_boot_command(command="bootelf -p {}".format(load_address), timeout=80, f1_index=index, expected="FUNOS_INITIALIZED")
            else:
                output = self.u_boot_command(command="bootelf -p {}".format(load_address), timeout=80, f1_index=index, expected="\"this space intentionally left blank.\"")

        else:
            output = self.u_boot_command(command="bootelf -p {}".format(load_address), timeout=80, f1_index=index, expected="sending a HOST_BOOTED message")
        """
        m = re.search(r'FunSDK Version=(\S+), ', output) # Branch=(\S+)', output)
        if m:
            version = m.group(1)
            # branch = m.group(2)
            fun_test.add_checkpoint(checkpoint="SDK Version: {}".format(version), context=self.context)
            fun_test.set_version(version=version.replace("bld_", ""))
        """

        if not rich_input_boot_args:
            sections = ['Welcome to FunOS', 'NETWORK_START', 'DPC_SERVER_STARTED', 'PCI_STARTED']
            for section in sections:
                fun_test.test_assert(expression=section in output,
                                     message="{} seen".format(section),
                                     context=self.context)
        else:
            fun_test.sleep("Waiting for custom apps to finish", seconds=120)
        self.set_boot_phase(index=index, phase=BootPhases.U_BOOT_COMPLETE)

        result = True
        try:
            self.nc[index].close()
            fun_test.log("Disconnected nc")
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def _reset_microcom(self):
        fun_test.log("Resetting microcom and minicom", context=self.context)
        process_ids = self.get_process_id_by_pattern("microcom", multiple=True)
        for process_id in process_ids:
            self.kill_process(signal=9, process_id=process_id, kill_seconds=2)
        process_ids = self.get_process_id_by_pattern("microcom", multiple=True)
        self.command("rm -f /var/lock/LCK..tty*")
        process_ids = self.get_process_id_by_pattern("minicom", multiple=True)
        for process_id in process_ids:
            self.kill_process(signal=9, process_id=process_id, kill_seconds=2)

    def position_support_scripts(self, auto_boot=False):
        try:
            self.stop_bundle_f1_logs()
        except Exception as ex:
            fun_test.critical(str(ex))

        if not self.bundle_compatible or not auto_boot:
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
        fun_test.sleep("Wait for serial proxies to be operational", seconds=15)
        '''
        uart_listener_script = FUN_TEST_LIB_UTILITIES_DIR + "/{}".format(self.UART_LOG_LISTENER_FILE)

        fun_test.scp(source_file_path=uart_listener_script,
                     target_ip=self.host_ip,
                     target_username=self.ssh_username,
                     target_password=self.ssh_password,
                     target_file_path=self.UART_LOG_LISTENER_PATH)
        fun_test.simple_assert(expression=self.list_files(self.UART_LOG_LISTENER_PATH),
                                   message="UART log listener copied",
                                   context=self.context)


        log_listener_processes = self.get_process_id_by_pattern("uart_log_listener.py", multiple=True)
        for log_listener_process in log_listener_processes:
            self.kill_process(signal=9, process_id=log_listener_process, kill_seconds=2)

        log_listener_processes = self.get_process_id_by_pattern(self.UART_LOG_LISTENER_FILE, multiple=True)
        for log_listener_process in log_listener_processes:
            self.kill_process(signal=9, process_id=log_listener_process, kill_seconds=2)
        '''

    def restart_serial_proxy(self):
        fun_test.log("Restoring serial proxy")
        self.command("cd {}".format(self.INSTALL_DIRECTORY))

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

    def initialize(self, reset=False):
        self.command("mkdir -p {}".format("{}".format(self.LOG_DIRECTORY)))
        self.command("cd {}".format(self.SCRIPT_DIRECTORY))
        self.command('gpiotool 8 --get-data | grep High >/dev/null 2>&1 && echo FS1600_REV2 || echo FS1600_REV1')

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

    def get_uart_log_file(self, f1_index, post_fix=None):
        if post_fix is not None:
            post_fix = "_pf_{}_".format(post_fix)
        artifact_file_name = fun_test.get_test_case_artifact_file_name(
            self._get_context_prefix("f1_{}{}_uart_log.txt".format(f1_index, post_fix)))
        fun_test.scp(source_ip=self.host_ip,
                     source_file_path=self.get_f1_uart_log_file_name(f1_index=f1_index),
                     source_username=self.ssh_username,
                     source_password=self.ssh_password,
                     target_file_path=artifact_file_name)
        with open(artifact_file_name, "r+") as f:
            content = f.read()
            f.seek(0, 0)
            f.write(self.u_boot_logs[f1_index] + '\n' + content)
        return artifact_file_name

    def cleanup(self):
        asset_id = "FS"
        asset_type = AssetType.DUT
        if self.fs:
            asset_type = self.fs.get_asset_type()
            asset_id = self.fs.get_asset_name()

        fun_test.sleep(message="Allowing time to generate full report", seconds=30, context=self.context)
        post_processing_error_found = False
        for f1_index in range(self.NUM_F1S):
            if self.disable_f1_index is not None and f1_index == self.disable_f1_index:
                continue

            artifact_file_name = fun_test.get_test_case_artifact_file_name(self._get_context_prefix("f1_{}_uart_log.txt".format(f1_index)))
            fun_test.scp(source_ip=self.host_ip,
                         source_file_path=self.get_f1_uart_log_file_name(f1_index=f1_index),
                         source_username=self.ssh_username,
                         source_password=self.ssh_password,
                         target_file_path=artifact_file_name,
                         timeout=240)

            if self.fs.tftp_image_path:
                u_boot_artifact_file_name = fun_test.get_test_case_artifact_file_name(
                    self._get_context_prefix("f1_{}_tftpboot_u_boot_log.txt".format(f1_index)))
                mode = "r+"
                if not os.path.exists(u_boot_artifact_file_name):
                    mode = "a+"
                with open(u_boot_artifact_file_name, mode) as f:
                    content = f.read()
                    f.seek(0, 0)
                    f.write(self.u_boot_logs[f1_index] + '\n' + content)
                fun_test.add_auxillary_file(description=self._get_context_prefix("F1_{} tftpboot u-boot log").format(f1_index),
                                            filename=u_boot_artifact_file_name,
                                            asset_type=asset_type,
                                            asset_id=asset_id,
                                            artifact_category=self.fs.ArtifactCategory.BRING_UP,
                                            artifact_sub_category=self.fs.ArtifactSubCategory.BMC)

            fun_test.add_auxillary_file(description=self._get_context_prefix("F1_{} UART log").format(f1_index),
                                        filename=artifact_file_name,
                                        asset_type=asset_type,
                                        asset_id=asset_id,
                                        artifact_category=self.fs.ArtifactCategory.POST_BRING_UP,
                                        artifact_sub_category=self.fs.ArtifactSubCategory.BMC)
            try:
                fun_test.log("Looking for rotated files")
                rotated_log_files = self.list_files(self.LOG_DIRECTORY + "/funos_f1_{}*gz".format(f1_index))
                for rotated_index, rotated_log_file in enumerate(rotated_log_files):
                    rotated_log_filename = rotated_log_file["filename"]
                    rotated_artifact_file_name = fun_test.get_test_case_artifact_file_name(
                        self._get_context_prefix("{}_{}".format(f1_index, os.path.basename(rotated_log_filename))))

                    fun_test.scp(source_ip=self.host_ip,
                                 source_file_path=rotated_log_filename,
                                 source_username=self.ssh_username,
                                 source_password=self.ssh_password,
                                 target_file_path=rotated_artifact_file_name,
                                 timeout=60)

                    fun_test.add_auxillary_file(description=self._get_context_prefix("F1_{} UART rotated log compressed {} {}").format(f1_index, rotated_index, os.path.basename(rotated_log_filename)),
                                                filename=rotated_artifact_file_name,
                                                asset_type=asset_type,
                                                asset_id=asset_id,
                                                artifact_category=self.fs.ArtifactCategory.POST_BRING_UP,
                                                artifact_sub_category=self.fs.ArtifactSubCategory.BMC)
            except Exception as ex:
                fun_test.critical(str(ex))
            try:
                self.post_process_uart_log(f1_index=f1_index, file_name=artifact_file_name)
            except Exception as ex:
                post_processing_error_found = True
                fun_test.critical("Error in post-processing:" + str(ex))

        if self.context:
            fun_test.add_auxillary_file(description=self._get_context_prefix("bringup"),
                                        filename=self.context.output_file_path,
                                        asset_type=asset_type,
                                        asset_id=asset_id,
                                        artifact_category=self.fs.ArtifactCategory.BRING_UP,
                                        artifact_sub_category=self.fs.ArtifactSubCategory.BMC)

        try:
            if not self.bundle_compatible:
                self._reset_microcom()
            else:
                self.start_bundle_f1_logs()
        except Exception as ex:
            fun_test.critical(str(ex))

    def post_process_uart_log(self, f1_index, file_name):
        regex_found = None
        try:
            fun_test.log("Post-processing UART log F1: {}".format(f1_index))
            regex = ""
            for error_regex in ERROR_REGEXES:
                regex += "{}|".format(error_regex)
            regex = regex.rstrip("|")
            with open(file_name, "r") as f:
                content = f.read()
                m = re.search(regex, content)
                if m:
                    full_match = m.group(0)
                    critical_message = "ERROR Regex matched: {}".format(full_match)
                    regex_found = critical_message
                    fun_test.critical(critical_message)
                    error_message = "Regression: ERROR REGEX Matched: {} Job-ID: {} F1_{} Context: {}".format(full_match, fun_test.get_suite_execution_id(), f1_index, self._get_context_prefix(data="error"))
                    fun_test.send_mail(subject=error_message, content=error_message, to_addresses=["team-regression@fungible.com"])

        except Exception as ex:
            fun_test.critical(ex)
        if regex_found and self.fs:
            self.fs.errors_detected.append("UART log contains: {}".format(regex_found))
        # fun_test.simple_assert(not regex_found, "UART log contains: {}".format(regex_found))

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

    def get_f1_uart_log_file_name(self, f1_index):
        file_name = "{}/f1_{}_uart_log.txt".format(self.LOG_DIRECTORY, f1_index)
        if self.bundle_compatible:
            file_name = "{}/funos_f1_{}.log".format(self.LOG_DIRECTORY, f1_index)
        return file_name

    def clear_bundle_f1_logs(self):
        for f1_index in range(2):
            if f1_index == self.disable_f1_index:
                continue
            if self.bundle_compatible:
                self.stop_bundle_f1_logs()
                # self.start_bundle_f1_logs()
                file_name = "{}/funos_f1_{}.log".format(self.LOG_DIRECTORY, f1_index)
                self.command("echo 'Cleared' > {}".format(file_name))
                try:
                    rotated_log_files = self.list_files(self.LOG_DIRECTORY + "/funos_f1_{}*gz".format(f1_index))
                    for rotated_index, rotated_log_file in enumerate(rotated_log_files):
                        rotated_log_filename = rotated_log_file["filename"]
                        self.command('rm {}'.format(rotated_log_filename))
                except Exception as ex:
                    fun_test.critical(str(ex))

class BootupWorker(Thread):
    def __init__(self, fs, power_cycle_come=True, non_blocking=False, context=None):
        super(BootupWorker, self).__init__()
        self.fs = fs
        self.power_cycle_come = power_cycle_come
        self.non_blocking = non_blocking
        self.context = context
        self.worker = None

    def run(self):
        fs = self.fs
        bmc = self.fs.get_bmc()
        fpga = self.fs.get_fpga()
        try:
            fs.set_boot_phase(BootPhases.FS_BRING_UP_BMC_INITIALIZE)
            fun_test.test_assert(expression=fs.bmc_initialize(), message="BMC initialize", context=self.context)

            if fs.retimer_workround:
                fs._apply_retimer_workaround()

            fun_test.test_assert(expression=fs.set_f1s(), message="Set F1s", context=self.context)

            if not fs.skip_funeth_come_power_cycle and not fs.bundle_image_parameters:
                fs.set_boot_phase(BootPhases.FS_BRING_UP_FUNETH_UNLOAD_COME_POWER_CYCLE)
                fun_test.test_assert(expression=fs.funeth_reset(), message="Funeth ComE power-cycle ref: IN-373")

            if self.fs.get_revision() in ["2"] and self.fs.bundle_compatible:
                come = fs.get_come()
                come_initialized = False
                fs_health = False
                expected_containers_running = False
                # try:
                #    come_initialized = come.initialize()
                #    try:
                #        fs_health = self.fs.health()
                #        expected_containers_running = come.ensure_expected_containers_running()
                #    except Exception as ex:
                #        fun_test.critical(str(ex))
                # except Exception as ex:
                #    fun_test.critical(str(ex))

                # if not come_initialized or not fs_health or not expected_containers_running:
                if True:
                    come.fs_reset()
                    fs.come = None
                    fs.bmc = None
                    fs.ensure_is_up(validate_uptime=True)
                    come = fs.get_come()
                    come.initialize()
                    try:
                        fs_health = self.fs.health()
                    except:
                        pass

                    fun_test.test_assert(come.ensure_expected_containers_running(), "Expected containers running")
                    self.fs.renew_device_handles()

            if fs.bundle_image_parameters:
                fs.set_boot_phase(BootPhases.FS_BRING_UP_INSTALL_BUNDLE)
                build_number = fs.bundle_image_parameters.get("build_number", 70)  # TODO: Is there a latest?
                release_train = fs.bundle_image_parameters.get("release_train", "1.0a_aa")
                fun_test.set_suite_run_time_environment_variable("bundle_image_parameters",
                                                                 {"release_train": release_train,
                                                                  "build_number": build_number})
                fun_test.set_version(version="{}/{}".format(release_train, build_number))
                come = fs.get_come()
                # try:
                #    come.detect_pfs()
                #    # fun_test.test_assert(self.fs.health(), "FS is healthy")
                # except Exception as ex:
                #    fun_test.add_checkpoint("PFs were not detected or FS is unhealthy. Doing a full power-cycle now")
                #    fun_test.test_assert(self.fs.reset(hard=False), "FS reset complete. Devices are up")
                #    fs.come = None
                #    fs.bmc = None
                #    come = fs.get_come()
                #    come.initialize()
                #    come.detect_pfs()
                #    bmc = fs.get_bmc()

                bmc = fs.get_bmc()
                come = fs.get_come()
                for f1_index in range(2):
                    if f1_index == self.fs.disable_f1_index:
                        continue

                    bmc.remove_uart_logs(f1_index=f1_index)
                fun_test.test_assert(expression=come.install_build_setup_script(build_number=build_number, release_train=release_train),
                                     message="Bundle image installed",
                                     context=self.context)
                fs.bundle_upgraded = True
                bmc.bundle_upgraded = True

                come.cleanup_databases()

                fs.set_boot_phase(BootPhases.FS_BRING_UP_FS_RESET)
                try:
                    come.fs_reset()
                except Exception as ex:
                    pass

                fs.bmc = None
                fs.come = None
                come = None

                # Wait for BMC to come up
                bmc = self.fs.get_bmc()
                fun_test.test_assert(expression=bmc.ensure_host_is_up(), message="BMC is up", context=self.context)

            if not fs.bundle_image_parameters:
                bmc = fs.get_bmc()
                fs.set_boot_phase(BootPhases.FS_BRING_UP_U_BOOT)
                if fs.tftp_image_path:
                    bmc.position_support_scripts(auto_boot=fs.is_auto_boot())
                    self.fs.get_come().pre_reboot_cleanup(for_bundle_installation=False)
                if not fs.bundle_compatible and fs.tftp_image_path:
                    bmc.stop_bundle_f1_logs()
                    bmc._reset_microcom()

                for f1_index, f1 in fs.f1s.iteritems():
                    if f1_index == fs.disable_f1_index:
                        continue
                    boot_args = fs.boot_args
                    fun_test.log("Auto-boot: {}".format(fs.is_auto_boot()), context=self.context)
                    if fs.tftp_image_path:
                        fun_test.test_assert(expression=bmc.setup_serial_proxy_connection(f1_index=f1_index, auto_boot=fs.is_auto_boot()),
                                             message="Setup nc serial proxy connection",
                                             context=self.context)

                    if fs.f1_parameters:
                        if f1_index in fs.f1_parameters:
                            if "boot_args" in fs.f1_parameters[f1_index]:
                                boot_args = fs.f1_parameters[f1_index]["boot_args"]

                    if fs.tftp_image_path:
                        if fs.get_bmc()._use_i2c_reset():
                            fs.get_bmc().reset_f1(f1_index=f1_index)
                        elif fpga and not fs.bundle_compatible:
                            fpga.reset_f1(f1_index=f1_index)
                        elif fpga and not fs.get_bmc()._use_i2c_reset():
                            fpga.reset_f1(f1_index=f1_index)
                        else:
                            fs.get_bmc().reset_f1(f1_index=f1_index)
                        preamble = bmc.get_preamble(f1_index=f1_index, auto_boot=fs.is_auto_boot())
                        # if fs.validate_u_boot_version:
                        #    fun_test.log("Preamble: {}".format(preamble))
                        fun_test.test_assert(
                            expression=bmc.u_boot_load_image(index=f1_index,
                                                             tftp_image_path=fs.tftp_image_path,
                                                             boot_args=boot_args, gateway_ip=fs.gateway_ip,
                                                             mpg_ips=fs.mpg_ips),
                            message="U-Bootup f1: {} complete".format(f1_index),

                            context=self.context)


                        fun_test.update_job_environment_variable("tftp_image_path", fs.tftp_image_path)
                    if not fs.bundle_compatible:
                        bmc.start_uart_log_listener(f1_index=f1_index, serial_device=fs.f1s.get(f1_index).serial_device_path)
                    # else:
                    #    bmc.start_bundle_f1_logs()

                fs.set_boot_phase(BootPhases.FS_BRING_UP_U_BOOT_COMPLETE)
                fs.u_boot_complete = True
                fs.get_bmc().clear_bundle_f1_logs()
                fs.get_bmc().start_bundle_f1_logs()

                come = fs.get_come()
                fs.set_boot_phase(BootPhases.FS_BRING_UP_COME_REBOOT_INITIATE)
                if fs.get_revision() not in ["2"]:
                    fun_test.test_assert(expression=fs.come_reset(power_cycle=self.power_cycle_come, non_blocking=self.non_blocking),
                                         message="ComE rebooted successfully. Non-blocking: {}".format(self.non_blocking),
                                         context=self.context)
                else:
                    try:
                        fun_test.test_assert(expression=fs.come_reset(power_cycle=False, non_blocking=self.non_blocking),
                                             message="ComE rebooted successfully. Non-blocking: {}".format(self.non_blocking),
                                             context=self.context)

                    except Exception as ex:
                        fun_test.critical(str(ex))
                        fs.reset(hard=False)
                        raise ex

            self.worker = ComEInitializationWorker(fs=self.fs)
            self.worker.run()
            come = fs.get_come()
            for f1_index, f1 in fs.f1s.iteritems():
                f1.set_dpc_port(come.get_dpc_port(f1_index))
            self.fs.set_boot_phase(BootPhases.FS_BRING_UP_COME_INITIALIZED)
            try:
                fs.get_bmc().disconnect()
                fun_test.log(message="BMC disconnect", context=self.context)
                if fpga:
                    fpga.disconnect()
                fs.get_come().disconnect()
            except:
                pass

            come = self.fs.get_come()
            bmc = self.fs.get_bmc()

            if self.fs.fun_cp_callback:
                fs.set_boot_phase(BootPhases.FS_BRING_UP_CALL_FUNCP_CALLBACK)
                fun_test.log("Calling fun CP callback from Fs")
                self.fs.fun_cp_callback(self)
            self.fs.set_boot_phase(BootPhases.FS_BRING_UP_COMPLETE)

        except Exception as ex:
            fun_test.critical(str(ex) + " FS: {}".format(fs), context=fs.context)
            fs.set_boot_phase(BootPhases.FS_BRING_UP_ERROR)
            fun_test.add_checkpoint(result=fun_test.FAILED,
                                    expected=False,
                                    actual=True,
                                    checkpoint="Bringup error",
                                    context=fs.context)
            raise ex


class ComEInitializationWorker(Thread):
    EXPECTED_CONTAINERS = ["run_sc"]# , "F1-1", "F1-0"]
    CONTAINERS_BRING_UP_TIME_MAX = 120


    def __init__(self, fs):
        super(ComEInitializationWorker, self).__init__()
        self.fs = fs
        for f1_index in range(self.fs.NUM_F1S):
            if f1_index == self.fs.disable_f1_index:
                continue
            self.EXPECTED_CONTAINERS.append("F1-{}".format(f1_index))

    def run(self):
        try:
            self.fs.set_boot_phase(BootPhases.FS_BRING_UP_COME_INITIALIZE_WORKER_THREAD)
            come = self.fs.get_come(clone=True)
            bmc = self.fs.get_bmc()
            if not self.fs.get_boot_phase() == BootPhases.FS_BRING_UP_ERROR:
                self.fs.set_boot_phase(BootPhases.FS_BRING_UP_COME_ENSURE_UP)
                fun_test.test_assert(expression=bmc.ensure_come_is_up(come=come, max_wait_time=300, power_cycle=True),
                                     message="Ensure ComE is up",
                                     context=self.fs.context)

            if not self.fs.get_boot_phase() == BootPhases.FS_BRING_UP_ERROR:
                self.fs.set_boot_phase(BootPhases.FS_BRING_UP_COME_INITIALIZE)
                fun_test.test_assert(expression=come.initialize(disable_f1_index=self.fs.disable_f1_index),
                                     message="ComE initialized",
                                     context=self.fs.context)
                if (self.fs.bundle_compatible):  # and not self.fs.tftp_image_path): # or (come.list_files(ComE.BOOT_UP_LOG)):
                    fun_test.sleep(seconds=10, message="Waiting for expected containers", context=self.fs.context)
                    expected_containers_running = self.is_expected_containers_running(come)
                    expected_containers_running_timer = FunTimer(max_time=self.CONTAINERS_BRING_UP_TIME_MAX)

                    while not expected_containers_running and not expected_containers_running_timer.is_expired(print_remaining_time=True):
                        fun_test.sleep(seconds=10, message="Waiting for expected containers", context=self.fs.context)
                        expected_containers_running = self.is_expected_containers_running(come)

                    fun_test.test_assert(expected_containers_running, "Expected containers running", context=self.fs.context)

                self.fs.come_initialized = True
        except Exception as ex:
            fun_test.critical(str(ex) + " FS: {}".format(self.fs), context=self.fs.context)
            self.fs.set_boot_phase(BootPhases.FS_BRING_UP_ERROR)
            raise ex

    def is_expected_containers_running(self, come):

        result = True
        containers = come.docker(sudo=True)
        for expected_container in self.EXPECTED_CONTAINERS:
            found = False
            if containers:
                for container in containers:
                    container_name = container["Names"]
                    if container_name == expected_container:
                        found = True
                        container_is_up = "Up" in container["Status"]
                        if not container_is_up:
                            result = False
                            fun_test.critical("Container {} is not up".format(container_name), context=self.fs.context)
                            break
                if not found:
                    fun_test.critical("Container {} was not found".format(expected_container), context=self.fs.context)
                    result = False
                break
            else:
                fun_test.critical("No containers are running")
                result = False
        return result

class ComE(Linux):
    EXPECTED_FUNQ_DEVICE_ID = ["04:00.1", "06:00.1"]
    DEFAULT_DPC_PORT = [42220, 42221]
    DEFAULT_STATISTICS_DPC_PORT = [45220, 45221]
    DEFAULT_CSI_PERF_DPC_PORT = [46220, 46221]
    DPC_LOG_PATH = "/tmp/f1_{}_dpc.txt"
    DPC_STATISTICS_LOG_PATH = "/tmp/f1_{}_dpc_statistics.txt"
    DPC_CSI_PERF_LOG_PATH = "/tmp/f1_{}_dpc_csi_perf.txt"
    NUM_F1S = 2
    NVME_CMD_TIMEOUT = 600000

    HBM_DUMP_DIRECTORY = "/home/fun/hbm_dumps"
    HBM_TOOL_DIRECTORY = "/home/fun/hbm_dump_tool"
    HBM_TOOL = "hbm_dump_pcie"

    MAX_HBM_DUMPS = 200
    BUILD_SCRIPT_DOWNLOAD_DIRECTORY = "/tmp/remove_me_build_script"
    BOOT_UP_LOG = "/var/log/COMe-boot-up.log"
    FUN_ROOT = "/opt/fungible"
    HEALTH_MONITOR = "/opt/fungible/etc/DpuHealthMonitor.sh"

    DPCSH_DIRECTORY = "/tmp/workspace/FunSDK/bin/Linux"  #TODO
    SC_LOG_PATH = "/var/log/sc"
    REDIS_LOG_PATH = "/var/log/redis"

    FS_RESET_COMMAND = "/opt/fungible/etc/ResetFs1600.sh"
    EXPECTED_CONTAINERS = ["run_sc"]# , "F1-1", "F1-0"]
    CONTAINERS_BRING_UP_TIME_MAX = 3 * 60

    CORES_DIRECTORY = "/opt/fungible/cores"

    class FunCpDockerContainer(Linux):
        CUSTOM_PROMPT_TERMINATOR = r'# '

        def __init__(self, name, **kwargs):
            super(ComE.FunCpDockerContainer, self).__init__(**kwargs)
            self.name = name

        def _connect(self):
            result = False
            if (super(ComE.FunCpDockerContainer, self)._connect()):

                # the below set_prompt_terminator is the temporary workaround of the recent FunCP docker container change
                # Recently while logging into the docker container it gets logged in as root user
                self.set_prompt_terminator(self.CUSTOM_PROMPT_TERMINATOR)
                sudo_entered = self.enter_sudo()
                output = self.command("docker exec -it {} bash".format(self.name))
                if "No such container" not in output:
                    # self.clean()
                    self.set_prompt_terminator(self.CUSTOM_PROMPT_TERMINATOR)
                    self.command("export TERM=xterm-mono; export PS1='{}'".format(self.CUSTOM_PROMPT_TERMINATOR), wait_until_timeout=3,
                                 wait_until=self.CUSTOM_PROMPT_TERMINATOR)
                    result = True
            fun_test.simple_assert(result, "SSH connection to docker host: {}".format(self))
            return result

    def __init__(self, **kwargs):
        super(ComE, self).__init__(**kwargs)
        self.original_context_description = None
        if self.context:
            self.original_context_description = self.context.description
        self.fs = kwargs.get("fs", None)
        self.hbm_dump_enabled = False
        self.funq_bind_device = {}
        self.starting_dpc_for_statistics = False # Just temporarily while statistics manager is being developed TODO

    def ensure_expected_containers_running(self, max_time=CONTAINERS_BRING_UP_TIME_MAX):
        fun_test.sleep(seconds=10, message="Waiting for expected containers", context=self.fs.context)
        expected_containers_running = self.is_expected_containers_running()
        expected_containers_running_timer = FunTimer(max_time=max_time)

        while not expected_containers_running and not expected_containers_running_timer.is_expired(print_remaining_time=True):
            fun_test.sleep(seconds=10, message="Waiting for expected containers", context=self.fs.context)
            expected_containers_running = self.is_expected_containers_running()
        return expected_containers_running

    def is_expected_containers_running(self):

        result = True
        containers = self.docker(sudo=True)
        for expected_container in self.EXPECTED_CONTAINERS:
            found = False
            if containers:
                for container in containers:
                    container_name = container["Names"]
                    if container_name == expected_container:
                        found = True
                        container_is_up = "Up" in container["Status"]
                        if not container_is_up:
                            result = False
                            fun_test.critical("Container {} is not up".format(container_name), context=self.fs.context)
                            break
                if not found:
                    fun_test.critical("Container {} was not found".format(expected_container), context=self.fs.context)
                    result = False
                break
            else:
                fun_test.critical("No containers are running")
                result = False
        return result

    def get_funcp_container(self, f1_index):
        container_name = "F1-{}".format(f1_index)
        return ComE.FunCpDockerContainer(host_ip=self.host_ip,
                                         ssh_username=self.ssh_username,
                                         ssh_password=self.ssh_password,
                                         ssh_port=self.ssh_port,
                                         name=container_name)

    def cleanup_redis(self):
        for f1_index in range(2):
            try:
                """
                # self.command("sudo docker exec -it F1-{} /bin/bash -c 'redis-cli hdel config node_id'".format(f1_index))
                """
                clone = self.clone()
                container = clone.get_funcp_container(f1_index=f1_index)
                container.command("pwd")
                container.handle.sendline("redis-cli\r\n")
                container.handle.expect(r'> $')
                container.handle.sendline("hdel config node_id\r\n")
                container.handle.expect(r'> $')
                container.handle.sendline("exit\r\n")
                container.handle.expect("# ")
                container.disconnect()

            except:
                pass

    def fs_reset(self, clone=False, fast=False):
        fun_test.add_checkpoint(checkpoint="Resetting FS")
        handle = self
        if clone:
            handle = self.clone()
        try:
            reset_command = "{}".format(self.FS_RESET_COMMAND)
            if fast:
                reset_command += " -f"

            handle.sudo_command(reset_command, timeout=120)
        except Exception as ex:
            fun_test.critical(str(ex))

    def stop_health_monitors(self):
        health_monitor_processes = self.get_process_id_by_pattern(self.HEALTH_MONITOR, multiple=True)
        for health_monitor_process in health_monitor_processes:
            self.kill_process(process_id=health_monitor_process, signal=9)
        health_monitor_processes = self.get_process_id_by_pattern(self.HEALTH_MONITOR, multiple=True)


    def restart_storage_controller(self):
        fun_test.add_checkpoint("Restart storage controller", context=self.context)
        try:
            self.stop_cc_health_check()
        except Exception as ex:
            fun_test.critical(str(ex))
            self.diags()
            self.fs_reset(clone=True)
        self.sudo_command("{}/StorageController/etc/start_sc.sh -c restart".format(self.FUN_ROOT))


    def pre_reboot_cleanup(self, skip_cc_cleanup=False, for_bundle_installation=True):
        fun_test.log("Cleaning up storage controller containers", context=self.context)
        self.stop_health_monitors()

        try:
            self.restart_storage_controller()
        except:
            pass

        if self.fs.bundle_compatible:
            fun_test.test_assert(self.ensure_expected_containers_running(max_time=60 * 10), "Expected containers running")
            fun_test.sleep("After expected containers running")

        try:
            # self.cleanup_redis()
            pass
        except:
            pass

        try:
            if not skip_cc_cleanup:
                self.stop_cclinux_service()
        except:
            pass
        # try:
        #    self.sudo_command("service docker stop")
        # except:
        #    pass
        try:
            self.sudo_command("{}/StorageController/etc/start_sc.sh stop".format(self.FUN_ROOT))
        except:
            pass

        containers = self.docker(sudo=True)
        try:
            for container in containers:
                if 'cclinux' in container['Names'] or 'run_sc' in container['Names']:
                    self.docker(sudo=True, kill_container_id=container['ID'], timeout=120)
            self.sudo_command("service docker stop")
        except:
            pass

        try:
            self.sudo_command("rmmod funeth fun_core")
        except:
            pass


    def initialize(self, reset=False, disable_f1_index=None):
        self.disable_f1_index = disable_f1_index
        self.dpc_ready = None
        fun_test.simple_assert(expression=self.setup_workspace(), message="ComE workspace setup", context=self.context)
        fun_test.simple_assert(expression=self.cleanup_dpc(), message="Cleanup dpc", context=self.context)
        for f1_index in range(self.NUM_F1S):
            self.sudo_command("rm -f {}".format(self.get_dpc_log_path(f1_index=f1_index)))

        fun_test.test_assert(expression=self.detect_pfs(), message="Fungible PFs detected", context=self.context)
        fun_test.test_assert(expression=self.setup_dpc(), message="Setup DPC", context=self.context)
        fun_test.test_assert(expression=self.is_dpc_ready(), message="DPC ready", context=self.context)
        if self.fs.statistics_enabled:
            fun_test.test_assert(expression=self.setup_dpc(statistics=True), message="Setup DPC for statistics", context=self.context)
            self.fs.dpc_for_statistics_ready = True
        self.hbm_dump_enabled = fun_test.get_job_environment_variable("hbm_dump")
        if self.hbm_dump_enabled:
            fun_test.test_assert(self.setup_hbm_tools(), "HBM tools and dump directory ready")

        if not self.fs.already_deployed:
            self.command("rm -f {}/*core*".format(self.CORES_DIRECTORY))
        return True

    def upload_sc_logs(self):
        result = None
        tar_timeout = 120
        try:
            if self.list_files(self.SC_LOG_PATH):
                sc_tar_file_path = "/tmp/{}_sc.tgz".format(fun_test.get_suite_execution_id())
                self.command("tar -cvzf {} {}".format(sc_tar_file_path, self.SC_LOG_PATH),
                             timeout=tar_timeout)
                self.list_files(sc_tar_file_path)
                result = sc_tar_file_path
        except Exception as ex:
            fun_test.critical(str(ex))
        return result


    def _get_build_script_url(self, build_number, release_train, script_file_name):
        """
        convert build number and release train to a url on dochub that refers to the bundle script
        :param build_number: example 68
        :param release_train: example apple_fs1600
        :param script_file_name: example setup_fs1600-68.sh
        :return: returns the dochub url with the given build number and release train
                example: http://dochub.fungible.local/doc/jenkins/apple_fs1600/68/setup_fs1600-68.sh
        """
        release_prefix = ""
        if "master" not in release_train:
            release_prefix = "rel_"

        url = "{}/{}/fs1600/{}/{}".format(DOCHUB_BASE_URL,
                                          release_prefix + release_train.replace(".", "_"),
                                          build_number,
                                          script_file_name)

        return url

    def _get_build_number_for_latest(self, release_train):
        release_prefix = ""
        if "master" not in release_train:
            release_prefix = "rel_"
        latest_url = "{}/{}/fs1600/latest/build_info.txt".format(DOCHUB_BASE_URL,
                                                                 release_prefix + release_train.replace(".", "_"))

        result = None
        build_info_file_contents = fetch_text_file(url=latest_url)
        if build_info_file_contents:
            try:
                result = int(build_info_file_contents)
            except Exception as ex:
                fun_test.critical(str(ex))
        return result

    def diags(self):
        fun_test.add_checkpoint(checkpoint="Trying to fetch diags")
        clone = self.clone()
        clone.command("dmesg")
        clone.command("cat /var/log/syslog")

    def stop_cc_health_check(self):
        system_health_check_script = "system_health_check.py"
        health_check_processes = self.get_process_id_by_pattern(system_health_check_script, multiple=True)
        for health_check_process in health_check_processes:
            self.kill_process(process_id=health_check_process, signal=9)
        self.get_process_id_by_pattern(system_health_check_script, multiple=True)


    def stop_cclinux_service(self):
        try:
            self.sudo_command("/opt/fungible/cclinux/cclinux_service.sh --stop", timeout=120)
        except Exception as ex:
            fun_test.critical(str(ex))
            self.diags()
            self.fs_reset(clone=True)

    def _setup_build_script_directory(self):
        """
        Sets up the directory location where the build script such as setup_fs1600-68.sh will be saved for the installation
        process. Remove the directory and Create the directory
        :return:
        """
        path = self.BUILD_SCRIPT_DOWNLOAD_DIRECTORY
        self.command("rm -rf {}".format(path))
        self.command("mkdir -p {}".format(path))
        return path

    def _transform_build_number(self):
        pass

    def install_build_setup_script(self, build_number, release_train="1.0a_aa"):
        """
        install the build setup script downloaded from dochub
        :param build_number: build number
        :param release_train: example apple_fs1600
        :return: True if the installation succeeded with exit status == 0, else raise an assert
        """

        self.stop_cclinux_service()
        # self.stop_cc_health_check()
        self.stop_health_monitors()

        if type(build_number) == str or type(build_number) == unicode and "latest" in build_number:
            build_number = self._get_build_number_for_latest(release_train=release_train)
            fun_test.simple_assert(build_number, "Getting latest build number")
        if "master" not in release_train:
            parts = release_train.split("_")
            temp = "{}-{}_{}".format(parts[0], build_number, parts[1])
        else:
            temp = "bld-{}".format(build_number)
        script_file_name = "setup_fs1600-{}.sh".format(temp)

        script_url = self._get_build_script_url(build_number=build_number,
                                                release_train=release_train,
                                                script_file_name=script_file_name)
        target_directory = self._setup_build_script_directory()
        target_file_name = "{}/{}".format(target_directory, script_file_name)
        self.curl(output_file=target_file_name, url=script_url, timeout=180)
        fun_test.simple_assert(self.list_files(target_file_name), "Install script downloaded")
        self.sudo_command("chmod 777 {}".format(target_file_name))
        self.sudo_command("{} install".format(target_file_name), timeout=720)
        exit_status = self.exit_status()
        fun_test.test_assert(exit_status == 0, "Bundle install complete. Exit status valid", context=self.context)


        ### Workaround for bond

        self.sudo_command("mkdir -p /opt/fungible/etc/funcontrolplane.d")
        self.sudo_command("touch /opt/fungible/etc/funcontrolplane.d/configure_bond")
        fun_test.set_version(version="{}/{}".format(release_train, build_number))

        return True

    def cleanup_databases(self):
        self.stop_cc_health_check()
        self.stop_health_monitors()

        try:
            self.restart_storage_controller()
        except Exception as ex:
            fun_test.critical(str(ex))
        # fun_test.test_assert(self.ensure_expected_containers_running(), "Expected containers running")


    def _get_bus_number(self, pcie_device_id):
        bus_number = None
        parts = pcie_device_id.split(":")
        if parts:
            bus_number = int(parts[0])
        return bus_number

    def get_dpc_port(self, f1_index, statistics=None, csi_perf=None):
        port = self.DEFAULT_DPC_PORT[f1_index]
        if statistics:
            port = self.DEFAULT_STATISTICS_DPC_PORT[f1_index]
        if csi_perf:
            port = self.DEFAULT_CSI_PERF_DPC_PORT[f1_index]
        return port

    def setup_workspace(self):
        working_directory = "/tmp"
        fun_test.log("Context: {}".format(self.context))
        self.command("cd {}".format(working_directory))
        self.command("mkdir -p workspace; cd workspace")
        self.command("export WORKSPACE=$PWD")
        self.command("wget http://10.1.20.99/doc/jenkins/funsdk/latest/Linux/dpcsh.tgz")
        fun_test.test_assert(expression=self.list_files("dpcsh.tgz"),
                             message="dpcsh.tgz downloaded",
                             context=self.context)
        self.command("mkdir -p FunSDK")
        self.command("tar -zxvf dpcsh.tgz -C ../workspace/FunSDK")

        return True

    def hbm_dump(self, f1_index):
        funq_bind_device = self.funq_bind_device.get(f1_index, None)
        fun_test.simple_assert(funq_bind_device, "funq_bind_device found for {}".format(f1_index))
        bus_number = self._get_bus_number(pcie_device_id=funq_bind_device)

        artifact_file_name = fun_test.get_test_case_artifact_file_name(post_fix_name="hbm_dump_f1_{}.bin".format(f1_index))
        artifact_file_name = "{}/{}".format(self.HBM_DUMP_DIRECTORY, self._get_context_prefix(os.path.basename(artifact_file_name)))
        if funq_bind_device:
            pass
        resource_path = "/sys/bus/pci/devices/0000:0{}:00.2/resource2".format(bus_number)
        self.sudo_command("ls -ltr {}".format(resource_path))
        command = "{}/{} -a 0x100000 -s 0x40000000 -b {} -f -o {}".format(self.HBM_TOOL_DIRECTORY, self.HBM_TOOL, resource_path, artifact_file_name)
        self.sudo_command(command, timeout=10 * 60)
        fun_test.test_assert(self.list_files(artifact_file_name), "HBM dump file created")
        tar_artifact_file_name = artifact_file_name + ".tgz"
        command = "tar -cvzf {} {} --remove-files".format(tar_artifact_file_name, artifact_file_name)
        self.sudo_command(command, timeout=120)
        fun_test.test_assert(self.list_files(tar_artifact_file_name), "HBM dump file tgz created")
        fun_test.log("HBM dump tgz file: {}".format(tar_artifact_file_name))
        self.list_files(path="{}".format(self.HBM_DUMP_DIRECTORY))
        fun_test.report_message("ComE IP: {}, username: {} password: {}".format(self.host_ip, self.ssh_username, self.ssh_password))
        fun_test.report_message("HBM dump for F1_{} available at {}".format(f1_index, tar_artifact_file_name))

    def setup_hbm_tools(self):
        tool_path = "{}/{}".format(STASH_DIR, self.HBM_TOOL)
        fun_test.simple_assert(os.path.exists(tool_path), "Ensure HBM tool exists at {} (locally)".format(tool_path))
        self.command("mkdir -p {}".format(self.HBM_TOOL_DIRECTORY))
        target_file_path = "{}/{}".format(self.HBM_TOOL_DIRECTORY, self.HBM_TOOL)
        fun_test.scp(source_file_path=tool_path, target_ip=self.host_ip, target_username=self.ssh_username, target_password=self.ssh_password, target_file_path=target_file_path)
        fun_test.simple_assert(self.list_files(target_file_path), "HBM tool copied")
        self.command("mkdir -p {}".format(self.HBM_DUMP_DIRECTORY))
        tgzs = "{}/*tgz".format(self.HBM_DUMP_DIRECTORY)
        tgz_paths = self.list_files(tgzs)
        num_tgzs = len(tgz_paths)
        try:
            fun_test.simple_assert(num_tgzs < self.MAX_HBM_DUMPS, "Only {} dump tgzs are allowed. Please delete a few old ones".format(self.MAX_HBM_DUMPS))
        except Exception as ex:
            fun_test.log("Clearing old dumps")
            for tgz_path in tgz_paths[:100]:
                self.remove_file(tgz_path["filename"])
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

    def setup_dpc(self, statistics=None, csi_perf=None):
        if statistics and self.starting_dpc_for_statistics:
            return True  #TODO: testing only
        if statistics:   #TODO: testing only
            self.starting_dpc_for_statistics = True
        self.modprobe("nvme")
        fun_test.sleep(message="After modprobe", seconds=5, context=self.context)
        nvme_devices = self.list_files("/dev/nvme*")
        fun_test.test_assert(expression=nvme_devices, message="At least one NVME device detected", context=self.context)

        self.command("cd {}".format(self.DPCSH_DIRECTORY))
        for f1_index in range(self.NUM_F1S):
            if f1_index == self.disable_f1_index:
                continue

            # self.command("cd $WORKSPACE/FunSDK/bin/Linux")
            nvme_device_index = f1_index
            if len(nvme_devices) == 1:  # if only one nvme device was detected
                nvme_device_index = 0
            command = "./dpcsh --pcie_nvme_sock=/dev/nvme{} --nvme_cmd_timeout={} --tcp_proxy={} &> {} &".format(nvme_device_index,
                                                                                                                 self.NVME_CMD_TIMEOUT,
                                                                                                                 self.get_dpc_port(f1_index=f1_index, statistics=statistics, csi_perf=csi_perf),
                                                                                                                 self.get_dpc_log_path(f1_index=f1_index, statistics=statistics, csi_perf=csi_perf))
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

    def get_dpc_log_path(self, f1_index, statistics=None, csi_perf=None):
        path = self.DPC_LOG_PATH.format(f1_index)
        if statistics:
            path = self.DPC_STATISTICS_LOG_PATH.format(f1_index)
        if csi_perf:
            path = self.DPC_CSI_PERF_LOG_PATH.format(f1_index)
        return path

    def _get_context_prefix(self, data):
        s = "{}".format(data)
        if self.original_context_description:
            s = "{}_{}".format(self.original_context_description.replace(":", "_"), data)
        return s

    def cleanup(self):
        asset_type = "unknown"
        asset_id = "unknown"
        if self.fs:
            asset_type = self.fs.get_asset_type()
            asset_id = self.fs.get_asset_name()
        try:
            fungible_root = self.command("echo $FUNGIBLE_ROOT")
            fungible_root = fungible_root.strip()

            try:
                if self.fs and self.fs.get_revision() in ["2"]:
                    fungible_root = "/opt/fungible"
            except Exception as ex:
                fun_test.critical(str(ex))

            if fungible_root:
                logs_path = "{}/logs/*".format(fungible_root)
                files = self.list_files(logs_path)
                for file in files:
                    file_name = file["filename"]
                    base_name = os.path.basename(file_name)
                    artifact_file_name = fun_test.get_test_case_artifact_file_name(
                        self._get_context_prefix(base_name))

                    #if not fun_test.is_at_least_one_failed():
                    if "openr" in file_name.lower():
                        continue
                    fun_test.scp(source_ip=self.host_ip,
                                 source_file_path=file_name,
                                 source_username=self.ssh_username,
                                 source_password=self.ssh_password,
                                 target_file_path=artifact_file_name)


                    fun_test.add_auxillary_file(description=self._get_context_prefix(base_name),
                                                filename=artifact_file_name,
                                                asset_type=asset_type,
                                                asset_id=asset_id,
                                                artifact_category=self.fs.ArtifactCategory.POST_BRING_UP,
                                                artifact_sub_category=self.fs.ArtifactSubCategory.COME)


        except Exception as ex:
            fun_test.critical(str(ex))

        try:
            come_boot_up_log_file = "/var/log/COMe-boot-up.log"
            base_name = os.path.basename(come_boot_up_log_file)
            artifact_file_name = fun_test.get_test_case_artifact_file_name(self._get_context_prefix(base_name))
            fun_test.scp(source_ip=self.host_ip,
                         source_file_path=come_boot_up_log_file,
                         source_username=self.ssh_username,
                         source_password=self.ssh_password,
                         target_file_path=artifact_file_name)
            fun_test.add_auxillary_file(description=self._get_context_prefix(base_name),
                                        filename=artifact_file_name,
                                        asset_type=asset_type,
                                        asset_id=asset_id,
                                        artifact_category=self.fs.ArtifactCategory.BRING_UP,
                                        artifact_sub_category=self.fs.ArtifactSubCategory.COME)
        except Exception as ex:
            fun_test.critical(str(ex))

        for f1_index in range(self.NUM_F1S):
            if f1_index == self.disable_f1_index:
                continue

            # try:
            #    if self.hbm_dump_enabled:
            #        self.hbm_dump(f1_index=f1_index)

            # except Exception as ex:
            #    fun_test.critical(str(ex))
            artifact_file_name = fun_test.get_test_case_artifact_file_name(self._get_context_prefix("f1_{}_dpc_log.txt".format(f1_index)))
            fun_test.scp(source_file_path=self.get_dpc_log_path(f1_index=f1_index), source_ip=self.host_ip, source_password=self.ssh_password, source_username=self.ssh_username, target_file_path=artifact_file_name)
            fun_test.add_auxillary_file(description=self._get_context_prefix("F1_{} DPC Log").format(f1_index),
                                        filename=artifact_file_name,
                                        asset_type=asset_type,
                                        asset_id=asset_id,
                                        artifact_category=self.fs.ArtifactCategory.BRING_UP,
                                        artifact_sub_category=self.fs.ArtifactSubCategory.COME)

        # Fetch sc logs if they exist
        sc_logs_path = self.upload_sc_logs()
        if sc_logs_path:
            uploaded_path = fun_test.upload_artifact(local_file_name_post_fix="sc_log.tgz",
                                                     linux_obj=self,
                                                     source_file_path=sc_logs_path,
                                                     display_name="sc logs tgz",
                                                     asset_type=asset_type,
                                                     asset_id=asset_id,
                                                     artifact_category=self.fs.ArtifactCategory.POST_BRING_UP,
                                                     artifact_sub_category=self.fs.ArtifactSubCategory.COME,
                                                     is_large_file=True,
                                                     timeout=240)
            if uploaded_path:
                fun_test.log("sc log uploaded to {}".format(uploaded_path))
            self.command("rm {}".format(sc_logs_path))

        # Fetch redis logs if they exist
        try:
            redis_target_path = "/tmp/redis_logs.tgz"
            self.sudo_command("tar -cvzf {} {}".format(redis_target_path, self.REDIS_LOG_PATH))
            redis_uploaded_path = fun_test.upload_artifact(local_file_name_post_fix="redis_logs.tgz",
                                                           linux_obj=self,
                                                           source_file_path=redis_target_path,
                                                           display_name="redis_logs",
                                                           asset_type=asset_type,
                                                           asset_id=asset_id,
                                                           artifact_category=self.fs.ArtifactCategory.POST_BRING_UP,
                                                           artifact_sub_category=self.fs.ArtifactSubCategory.COME,
                                                           is_large_file=False,
                                                           timeout=60)
        except:
            pass
        else:
            self.sudo_command("rm {}".format(redis_target_path))
        fun_test.simple_assert(not self.list_files("{}/*core*".format(self.CORES_DIRECTORY)), "Core files detected")


class F1InFs:
    def __init__(self, index, fs, serial_device_path, serial_sbp_device_path):
        self.index = index
        self.fs = fs
        self.serial_device_path = serial_device_path
        self.serial_sbp_device_path = serial_sbp_device_path
        self.dpc_port = None
        self.hbm_dump_complete = False


    def get_dpc_client(self, auto_disconnect=False, statistics=None, csi_perf=None):
        come = self.fs.get_come()
        if statistics or csi_perf:
            come = self.fs.get_come(clone=True)
        host_ip = come.host_ip
        if statistics and not self.fs.dpc_for_statistics_ready:
            come.setup_dpc(statistics=True)
            self.fs.dpc_for_statistics_ready = True
            come.disconnect()
        if csi_perf and not self.fs.dpc_for_csi_perf_ready:
            come.setup_dpc(csi_perf=True)
            self.fs.dpc_for_csi_perf_ready = True
        dpc_port = come.get_dpc_port(self.index, statistics=statistics, csi_perf=csi_perf)
        dpcsh_client = DpcshClient(target_ip=host_ip, target_port=dpc_port, auto_disconnect=auto_disconnect)
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

    class ArtifactCategory:
        BRING_UP = "Bring-up"
        POST_BRING_UP = "Post bring-up"

    class ArtifactSubCategory:
        COME = "COME"
        BMC = "BMC"


    DEFAULT_BOOT_ARGS = "app=load_mods --dpc-server --dpc-uart --csr-replay --serdesinit --all_100g"
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

    class StatisticsType(Codes):
        BAM = 1000
        DEBUG_VP_UTIL = 1050



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
                 setup_bmc_support_files=True,
                 apc_info=None,
                 fun_cp_callback=None,
                 skip_funeth_come_power_cycle=None,
                 bundle_image_parameters=None,
                 spec=None,
                 already_deployed=None,
                 revision=None,
                 fs_parameters=None,
                 fpga_telnet_ip=None,
                 fpga_telnet_port=None,
                 fpga_telnet_username=None,
                 fpga_telnet_password=None):
        self.spec = spec
        self.bmc_mgmt_ip = bmc_mgmt_ip
        self.bmc_mgmt_ssh_username = bmc_mgmt_ssh_username
        self.bmc_mgmt_ssh_password = bmc_mgmt_ssh_password
        self.fpga_mgmt_ip = fpga_mgmt_ip
        self.fpga_mgmt_ssh_username = fpga_mgmt_ssh_username
        self.fpga_mgmt_ssh_password = fpga_mgmt_ssh_password

        self.fpga_telnet_ip = fpga_telnet_ip
        self.fpga_telnet_port = fpga_telnet_port
        self.fpga_telnet_username = fpga_telnet_username
        self.fpga_telnet_password = fpga_telnet_password

        self.come_mgmt_ip = come_mgmt_ip
        self.come_mgmt_ssh_username = come_mgmt_ssh_username
        self.come_mgmt_ssh_password = come_mgmt_ssh_password
        self.bmc = None
        self.fpga = None
        self.come = None
        self.tftp_image_path = tftp_image_path
        self.bundle_image_parameters = bundle_image_parameters
        self.fs_parameters = fs_parameters
        if self.bundle_image_parameters:
            bundle_build_number = self.bundle_image_parameters["build_number"]
            is_number = False
            try:
                bundle_build_number = int(bundle_build_number)
                is_number = True
            except:
                pass
            if is_number and bundle_build_number < 0:
                fun_test.log("Build number set to -1 so resetting bundle image parameters. Received bundle number: {}".format(bundle_build_number))
                self.bundle_image_parameters = None
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

        self.asset_name = "FS"
        if self.spec:
            self.asset_name = self.spec.get("name", "FS")
        self.asset_type = AssetType.DUT

        if self.context:
            self.original_context_description = self.context.description
        self.setup_bmc_support_files = setup_bmc_support_files
        self.validate_u_boot_version = True
        disable_u_boot_version_validation = self.get_workaround("disable_u_boot_version_validation")
        self.revision = self.get_revision()

        if disable_u_boot_version_validation is not None:
            self.validate_u_boot_version = not disable_u_boot_version_validation
        self.bootup_worker = None
        self.u_boot_complete = False
        self.come_initialized = False

        self.csi_perf_templates = {}
        self.bundle_upgraded = False   # is the bundle upgrade complete?
        self.bundle_compatible = False   # Set this, if we are trying to boot a device with bundle installed already
        if ("bundle_compatible" in spec and spec["bundle_compatible"]) or (self.bundle_image_parameters) or (self.get_revision() in ["2"]):
            self.bundle_compatible = True
            self.skip_funeth_come_power_cycle = True
        self.mpg_ips = spec.get("mpg_ips", [])
        # self.auto_boot = auto_boot
        self.bmc_maintenance_threads = []
        self.cleanup_attempted = False
        self.already_deployed = already_deployed
        if self.fs_parameters:
            if "already_deployed" in self.fs_parameters:
                self.already_deployed = self.fs_parameters["already_deployed"]

        self.statistics_collectors = {}
        self.dpc_statistics_lock = Lock()
        self.statistics_enabled = True

        if self.fs_parameters:
            if "statistics_enabled" in self.fs_parameters:
                self.statistics_enabled = self.fs_parameters["statistics_enabled"]
        self.register_all_statistics()
        self.dpc_for_statistics_ready = False
        self.dpc_for_csi_perf_ready = False

        self.errors_detected = []
        fun_test.register_fs(self)

    def enable_statistics(self, enable):
        self.statistics_enabled = enable

    def register_all_statistics(self):
        self.register_statistics(statistics_type=Fs.StatisticsType.BAM)
        self.register_statistics(statistics_type=Fs.StatisticsType.DEBUG_VP_UTIL)

    def renew_device_handles(self):
        self.reset_device_handles()
        self.bmc = self.get_bmc()
        self.come = self.get_come()
        self.fpga = self.get_fpga()

    def reset_device_handles(self):
        try:
            if self.bmc:
                self.bmc.destroy()
                self.bmc = None
        except:
            pass
        finally:
            self.bmc = None
        try:
            if self.come:
                self.come.destroy()
                self.come = None
        except:
            pass
        finally:
            self.come = None
        try:
            if self.fpga:
                self.fpga.destroy()
                self.fpga = None
        except:
            pass
        finally:
            self.fpga = None

    def get_asset_type(self):
        return self.asset_type

    def get_asset_name(self):
        return self.asset_name

    def start_statistics_collection(self, statistics_type=None):
        statistics_manager = fun_test.get_statistics_manager()
        for st, collector_id in self.statistics_collectors.iteritems():
            if st is not None and st is not statistics_type:
                continue
            statistics_manager.start(collector_id=collector_id)

    def stop_statistics_collection(self, statistics_type=None):
        statistics_manager = fun_test.get_statistics_manager()
        for st, collector_id in self.statistics_collectors.iteritems():
            if st is not None and st is not statistics_type:
                continue
            statistics_manager.stop(collector_id=collector_id)

    def register_statistics(self, statistics_type):
        statistics_manager = fun_test.get_statistics_manager()
        collector = StatisticsCollector(collector=self,
                                        category=StatisticsCategory.FS_SYSTEM,
                                        type=statistics_type,
                                        asset_id=self.get_asset_name())
        self.statistics_collectors[statistics_type] = statistics_manager.register_collector(collector=collector)

    def get_context(self):
        return self.context

    def is_auto_boot(self):
        return False if self.tftp_image_path else True

    def get_tftp_image_path(self):
        return self.tftp_image_path

    def __str__(self):
        name = self.spec.get("name", None)
        if not name:
            name = "FS"
        return name

    def is_u_boot_complete(self):
        return self.u_boot_complete

    def get_revision(self):
        value = None
        if self.spec:
            value = self.spec.get("revision", None)
        return value

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
        fpga = self.get_fpga()
        if fpga:
            fpga.reset_context()
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
        self.cleanup_attempted = True
        self.get_come().cleanup()
        self.get_bmc().cleanup()

        if self.errors_detected:
            for f1_index, f1 in self.f1s.iteritems():
                try:
                    if self.disable_f1_index is not None and f1_index == self.disable_f1_index:
                        continue
                    if f1.hbm_dump_complete:
                        continue
                    fun_test.log("Errors were detected. Starting HBM dump")
                    f1.hbm_dump_complete = True
                    self.get_come().setup_hbm_tools()
                    self.get_come().hbm_dump(f1_index=f1_index)
                except Exception as ex:
                    fun_test.critical(str(ex))
        try:
            for maintenance_thread in self.bmc_maintenance_threads:
                maintenance_thread.stop()
        except Exception as ex:
            fun_test.critical(str(ex))

        try:
            self.get_bmc().disconnect()
            fun_test.log(message="BMC disconnect", context=self.context)
            fpga = self.get_fpga()
            if fpga:
                fpga.disconnect()
                fun_test.log(message="FPGA disconnect", context=self.context)
            self.get_come().disconnect()
            fun_test.log(message="ComE disconnect", context=self.context)
        except:
            pass
        finally:
            if self.errors_detected:
                for error_detected in self.errors_detected:
                    fun_test.critical("Error detected: {}".format(error_detected))
                    fun_test.add_checkpoint(checkpoint="Error detected: {}".format(error_detected), expected=False, actual=True, result=fun_test.FAILED)
                    try:
                        if self.errors_detected \
                                and self.get_revision() in ["2"] \
                                and any("bug_check" in error_detected for error_detected in self.errors_detected):
                            fun_test.add_checkpoint("Crash detected, so doing a full power-cycle")
                            fun_test.test_assert(self.reset(), "FS reset complete. Devices are up")
                    except Exception as ex:
                        fun_test.critical(str(ex))
            fun_test.simple_assert(not self.errors_detected, "Errors detected")
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
            setup_bmc_support_files=True,
            fun_cp_callback=None,
            power_cycle_come=False,
            already_deployed=False,
            skip_funeth_come_power_cycle=None,
            bundle_image_parameters=None,
            fs_parameters=None):  #TODO
        if not fs_spec:
            am = fun_test.get_asset_manager()
            test_bed_type = fun_test.get_job_environment_variable("test_bed_type")
            fun_test.log("Testbed-type: {}".format(test_bed_type), context=context)
            test_bed_spec = am.get_test_bed_spec(name=test_bed_type)
            fun_test.simple_assert(test_bed_spec, "Test-bed spec for {}".format(test_bed_spec), context=context)
            dut_name = test_bed_spec["dut_info"]["0"]["dut"]
            fs_spec = am.get_fs_spec(dut_name)
            fun_test.simple_assert(fs_spec, "FS spec for {}".format(dut_name), context=context)

        if fs_parameters:
            if not already_deployed:
                already_deployed = fs_parameters.get("already_deployed", None)
        if not already_deployed:
            if not tftp_image_path:
                tftp_image_path = fun_test.get_build_parameter("tftp_image_path")
            if not tftp_image_path:
                bundle_image_parameters = fun_test.get_build_parameter("bundle_image_parameters")
                if bundle_image_parameters:

                    is_number = False   # redundant
                    try:
                        bundle_build_number = int(bundle_image_parameters["build_number"])
                        is_number = True
                    except:
                        pass
                    if is_number and int(bundle_image_parameters["build_number"]) < 0:
                        fun_test.log("Build number set to -1 so resetting bundle image parameters. Received: {}".format(bundle_image_parameters["build_number"]))
                        bundle_image_parameters = None
            # fun_test.test_assert(tftp_image_path, "TFTP image path: {}".format(tftp_image_path), context=context)

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
        skip_funeth_come_power_cycle = skip_funeth_come_power_cycle or workarounds.get("skip_funeth_come_power_cycle", None)

        apc_info = fs_spec.get("apc_info", None)  # Used for power-cycling the entire FS
        fs_obj = Fs(bmc_mgmt_ip=bmc_spec["mgmt_ip"],
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
                  spec=fs_spec,
                  bundle_image_parameters=bundle_image_parameters,
                  already_deployed=already_deployed,
                  fs_parameters=fs_parameters)

        if "telnet_ip" in fpga_spec:
            fs_obj.fpga_telnet_ip = fpga_spec["telnet_ip"]
            fs_obj.fpga_telnet_port = fpga_spec.get("telnet_port", None)
            fs_obj.fpga_telnet_username = fpga_spec.get("telnet_username", None)
            fs_obj.fpga_telnet_password = fpga_spec.get("telnet_password", None)
        if already_deployed:
            fs_obj.re_initialize()
        return fs_obj

    def bootup(self, reboot_bmc=False, power_cycle_come=True, non_blocking=False, threaded=False):
        fpga = self.get_fpga()
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

            self.set_boot_phase(BootPhases.FS_BRING_UP_U_BOOT)
            self.get_bmc()
            self.get_bmc().position_support_scripts()
            for f1_index, f1 in self.f1s.iteritems():
                if f1_index == self.disable_f1_index:
                    continue
                boot_args = self.boot_args
                if self.f1_parameters:
                    if f1_index in self.f1_parameters:
                        if "boot_args" in self.f1_parameters[f1_index]:
                            boot_args = self.f1_parameters[f1_index]["boot_args"]

                fun_test.test_assert(self.get_bmc().setup_serial_proxy_connection(f1_index=f1_index, auto_boot=self.is_auto_boot()),
                                     "Setup nc serial proxy connection")

                self.set_boot_phase(BootPhases.FS_BRING_UP_RESET_F1)
                if self.get_bmc()._use_i2c_reset():
                    self.get_bmc().reset_f1(f1_index=f1_index)
                elif fpga and not self.bundle_compatible:
                    fpga.reset_f1(f1_index=f1_index)
                else:
                    bmc = self.get_bmc()
                    bmc.reset_f1(f1_index=f1_index)
                    bmc.remove_uart_logs(f1_index=f1_index)

                preamble = self.get_bmc().get_preamble(f1_index=f1_index)
                if self.validate_u_boot_version:
                    fun_test.test_assert(self.bmc.validate_u_boot_version(output=preamble, minimum_date=self.MIN_U_BOOT_DATE), "Validate preamble")

                if self.tftp_image_path:
                    fun_test.test_assert(expression=self.bmc.u_boot_load_image(index=f1_index,
                                                                               tftp_image_path=self.tftp_image_path,
                                                                               boot_args=boot_args,
                                                                               gateway_ip=self.gateway_ip,
                                                                               mpg_ips=self.mpg_ips),
                                         message="U-Bootup f1: {} complete".format(f1_index),
                                         context=self.context)
                    fun_test.update_job_environment_variable("tftp_image_path", self.tftp_image_path)
                self.bmc.start_uart_log_listener(f1_index=f1_index, serial_device=self.f1s.get(f1_index).serial_device_path)

            self.get_come()
            if not self.bundle_upgraded:
                self.set_boot_phase(BootPhases.FS_BRING_UP_COME_REBOOT_INITIATE)
                fun_test.test_assert(expression=self.come_reset(power_cycle=self.power_cycle_come or power_cycle_come,
                                                                non_blocking=non_blocking),
                                     message="ComE rebooted successfully. Non-blocking: {}".format(non_blocking),
                                     context=self.context)
            self.come = self.get_come()
            if not non_blocking:
                # self.come = self.fs.get_come()
                self.set_boot_phase(BootPhases.FS_BRING_UP_COME_INITIALIZE)
                fun_test.test_assert(expression=self.come.initialize(disable_f1_index=self.disable_f1_index),
                                     message="ComE initialized",
                                     context=self.context)

                if self.fun_cp_callback:
                    fun_test.log("Calling FunCP callback from FS")
                #    self.fs.fun_cp_callback(self.fs.get_come())
                self.come_initialized = True
                self.set_boot_phase(BootPhases.FS_BRING_UP_COMPLETE)
                        # bmc_maintenance_thread.start()
                        # self.bmc_maintenance_threads.append(bmc_maintenance_thread)
            else:
                # Start thread
                self.worker = ComEInitializationWorker(fs=self)
                self.worker.start()
            for f1_index, f1 in self.f1s.iteritems():
                f1.set_dpc_port(self.come.get_dpc_port(f1_index))
    
    
            try:
                self.get_bmc().disconnect()
                fun_test.log(message="BMC disconnect", context=self.context)
                if fpga:
                    fpga.disconnect()
                self.get_come().disconnect()
            except:
                pass

        else:
            if not self.already_deployed:
                self.bootup_worker = BootupWorker(fs=self, power_cycle_come=power_cycle_come, non_blocking=non_blocking, context=self.context)
                self.bootup_worker.start()
                fun_test.sleep("Bootup worker start", seconds=3)
            else:
                self.boot_phase = BootPhases.FS_BRING_UP_COMPLETE
                self.come_initialized = True

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

        ready = self.boot_phase == BootPhases.FS_BRING_UP_COMPLETE
        return ready

    def is_come_ready(self):
        return self.come_initialized

    def come_reset(self, power_cycle=None, non_blocking=None, max_wait_time=300):
        result = self.bmc.come_reset(come=self.get_come(),
                                     power_cycle=power_cycle,
                                     non_blocking=non_blocking,
                                     max_wait_time=max_wait_time)
        self.come = None
        return result

    def re_initialize(self):
        self.get_bmc(disable_f1_index=self.disable_f1_index)
        if not self.already_deployed:
            self.bmc.position_support_scripts()
        self.get_fpga()
        self.get_come()
        self.set_f1s()
        self.come.initialize(disable_f1_index=self.disable_f1_index)
        self.come.setup_dpc()


        self.come.detect_pfs()
        fun_test.test_assert(expression=self.come.ensure_dpc_running(),
                             message="Ensure dpc is running",
                             context=self.context)
        if self.statistics_enabled:
            if not self.dpc_for_statistics_ready:
                self.come.setup_dpc(statistics=True)
                self.dpc_for_statistics_ready = True
        return True

    def funeth_reset(self):
        fpga = self.get_fpga()
        bmc = self.get_bmc()
        for f1_index, f1 in self.f1s.iteritems():
            if bmc._use_i2c_reset():
                bmc.reset_f1(f1_index=f1_index, keep_low=True)
            elif fpga and not self.bundle_compatible:
                fpga.reset_f1(f1_index=f1_index, keep_low=True)
            else:
                bmc.reset_f1(f1_index=f1_index, keep_low=True)
        fun_test.add_checkpoint("Reset and hold F1")

        fun_test.test_assert(bmc.come_power_cycle(), "Trigger ComE power-cycle")
        come = self.get_come()
        fun_test.test_assert(come.ensure_host_is_up(max_wait_time=300), "Ensure ComE is up")
        return True

    def get_bmc(self, disable_f1_index=None):
        if disable_f1_index is None:
            disable_f1_index = self.disable_f1_index

        if not self.bmc:
            self.bmc = Bmc(disable_f1_index=disable_f1_index, host_ip=self.bmc_mgmt_ip,
                           ssh_username=self.bmc_mgmt_ssh_username,
                           ssh_password=self.bmc_mgmt_ssh_password,
                           set_term_settings=True,
                           disable_uart_logger=self.disable_uart_logger,
                           context=self.context,
                           setup_support_files=self.setup_bmc_support_files,
                           fs=self)
        if self.bundle_upgraded:
            self.bmc.bundle_upgraded = self.bundle_upgraded
        self.bmc.bundle_compatible = self.bundle_compatible
        return self.bmc

    def get_terminal(self):
        return self.get_fpga(terminal=True)

    def get_fpga(self, terminal=False):
        result = None
        if not terminal:
            if not self.fpga:
                if self.fpga_mgmt_ip:
                    self.fpga = Fpga(host_ip=self.fpga_mgmt_ip,
                                     ssh_username=self.fpga_mgmt_ssh_username,
                                     ssh_password=self.fpga_mgmt_ssh_password,
                                     set_term_settings=True,
                                     disable_f1_index=self.disable_f1_index,
                                     context=self.context)
            result = self.fpga
        else:
            telnet_object = Fpga(host_ip=self.fpga_telnet_ip,
                                 ssh_username=self.fpga_mgmt_ssh_username,
                                 ssh_password=self.fpga_mgmt_ssh_password,
                                 set_term_settings=True,
                                 disable_f1_index=self.disable_f1_index,
                                 context=self.context,
                                 telnet_username=self.fpga_telnet_username,
                                 telnet_password=self.fpga_telnet_password,
                                 telnet_ip=self.fpga_telnet_ip,
                                 telnet_port=self.fpga_telnet_port,
                                 use_telnet=True)
            telnet_object.set_prompt_terminator('# ')
            result = telnet_object
        return result

    def get_come(self, clone=False):
        if not self.come:
            self.come = ComE(host_ip=self.come_mgmt_ip,
                             ssh_username=self.come_mgmt_ssh_username,
                             ssh_password=self.come_mgmt_ssh_password,
                             set_term_settings=True,
                             context=self.context,
                             ipmi_info=self.get_bmc()._get_ipmi_details(),
                             fs=self)
            self.come.disable_f1_index = self.disable_f1_index
        come = self.come
        if clone:
            come = come.clone()
        return come

    def come_initialize(self):
        self.get_come()
        self.come.initialize(disable_f1_index=self.disable_f1_index)
        return True

    def health(self, only_reachability=False):
        result = None
        if not only_reachability:
            bam_result = self.bam()
            if bam_result["status"]:
                result = True
        else:
            try:
                bmc = self.get_bmc()
                health_result, health_error_message = bmc.is_host_up(max_wait_time=60, with_error_details=True)
                if health_result:
                    try:
                        come = self.get_come()
                        health_result, health_error_message = come.is_host_up(max_wait_time=60, with_error_details=True)
                    except Exception as ex:
                        fun_test.critical(str(ex))
                    else:
                        come.disconnect()
                    if health_result:
                        try:
                            fpga = self.get_fpga()
                            if fpga:
                                health_result, health_error_message = fpga.is_host_up(max_wait_time=60, with_error_details=True)
                        except Exception as ex:
                            fun_test.critical(str(ex))
                        else:
                            if fpga:
                                fpga.disconnect()
                result = health_result, health_error_message

            except Exception as ex:
                fun_test.critical(str(ex))
            else:
                bmc.disconnect()



        return result

    def bam(self, command_duration=2):
        result = {"status": False}
        f1_level_result = {}
        for f1_index in range(self.NUM_F1S):
            if f1_index == self.disable_f1_index:
                continue
            dpc_client = self.get_dpc_client(f1_index=f1_index, auto_disconnect=True, statistics=True)
            cmd = "stats/resource/bam"
            dpc_result = dpc_client.json_execute(verb="peek", data=cmd, command_duration=command_duration)
            if dpc_result["status"]:
                f1_level_result[f1_index] = dpc_result["data"]
        result["data"] = f1_level_result
        if f1_level_result:
            result["status"] = True
        # fun_test.log("BAM result: {} {}".format(result, f1_level_result))
        return result

    def debug_vp_util(self, command_duration=2):
        result = {"status": False}
        f1_level_result = {}
        for f1_index in range(self.NUM_F1S):
            if f1_index == self.disable_f1_index:
                continue
            dpc_client = self.get_dpc_client(f1_index=f1_index, auto_disconnect=True, statistics=True)
            cmd = "vp_util"
            dpc_result = dpc_client.json_execute(verb="debug", data=cmd, command_duration=command_duration)
            if dpc_result["status"]:
                raw_data = dpc_result["data"]
                fixed_data = {key.replace(".", "_"): value for key, value in raw_data.iteritems()}
                f1_level_result[f1_index] = fixed_data

        result["data"] = f1_level_result
        if f1_level_result:
            result["status"] = True

        return result

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

    def reset(self, hard=False):
        if hard:
            fun_test.simple_assert(expression=self.apc_info, context=self.context, message="APC info is missing")
            apc_pdu = ApcPdu(context=self.context, **self.apc_info)
            power_cycle_result = apc_pdu.power_cycle(self.apc_info["outlet_number"])
            fun_test.simple_assert(expression=power_cycle_result,
                                   context=self.context,
                                   message="APC power-cycle result")
            try:
                apc_pdu.disconnect()
            except:
                pass

            self.reset_device_handles()
        else:
            come = self.get_come()
            come.fs_reset()
            self.reset_device_handles()
        fun_test.test_assert(self.ensure_is_up(validate_uptime=True), "Validate FS components are up")
        return True

    def ensure_is_up(self, validate_uptime=False):
        worst_case_uptime = 60 * 10
        fpga = self.get_fpga()
        """
        if fpga:
            fun_test.test_assert(expression=fpga.ensure_host_is_up(max_wait_time=120),
                                 context=self.context, message="FPGA reachable after reset")
            if validate_uptime:
                fun_test.simple_assert(fpga.uptime() < worst_case_uptime, "FPGA uptime is less than 10 minutes")
        """
        bmc = self.get_bmc()
        fun_test.test_assert(expression=bmc.ensure_host_is_up(max_wait_time=120),
                             context=self.context, message="BMC reachable after reset")
        """
        if validate_uptime:
            fun_test.simple_assert(bmc.uptime() < worst_case_uptime, "BMC uptime is less than 10 minutes")
        """
        
        come = self.get_come().clone()
        fun_test.test_assert(expression=come.ensure_host_is_up(max_wait_time=180 * 2,
                                                               power_cycle=False), message="ComE reachable after reset")
        if validate_uptime:
            fun_test.simple_assert(come.uptime() < worst_case_uptime, "ComE uptime is less than 10 minutes")


        return True

    def get_dpc_client(self, f1_index, auto_disconnect=False, statistics=None, csi_perf=None):
        f1 = self.get_f1(index=f1_index)
        dpc_client = f1.get_dpc_client(auto_disconnect=auto_disconnect, statistics=statistics, csi_perf=csi_perf)
        return dpc_client

    def _get_context_prefix(self, data):
        s = "{}".format(data)
        if self.original_context_description:
            s = "{}_{}".format(self.original_context_description.replace(":", "_"), data)
        return s

    def get_uart_log_file(self, f1_index, post_fix=None):
        return self.get_bmc().get_uart_log_file(f1_index=f1_index, post_fix=post_fix)

    def statistics_dispatcher(self, statistics_type, **kwargs):
        result = {"status": False, "data": None, "epoch_time": get_current_epoch_time()}
        if self.statistics_enabled:
            try:
                self.dpc_statistics_lock.acquire()
                if statistics_type == self.StatisticsType.BAM:
                    bam_result = self.bam(**kwargs)
                    if bam_result["status"]:
                        result["data"] = bam_result["data"]
                        result["status"] = True
                if statistics_type == self.StatisticsType.DEBUG_VP_UTIL:
                    debug_vp_result = self.debug_vp_util(**kwargs)
                    if debug_vp_result["status"]:
                        result["data"] = debug_vp_result["data"]
                        result["status"] = True
            finally:
                self.dpc_statistics_lock.release()
        return result

if __name__ == "__main__":
    fs = Fs.get(fun_test.get_asset_manager().get_fs_spec(name="fs-121"))
    come = fs.get_come()
    come.cleanup_redis()


    i = 0
    #terminal = fs.get_terminal()
    #terminal.command("pwd")
    #terminal.command("ifconfig")
    # fs.get_bmc().position_support_scripts()
    # fs.bootup(reboot_bmc=False)
    # fs.come_initialize()
    # fs.come_reset()
    # come = fs.get_come()
    # come.detect_pfs()
    # come.setup_dpc()
    # come = fs.get_come()
    # come.command("ls -ltr")
    # fs.re_initialize()
    # i = fs.bam()


if __name__ == "__main2__":
    come = ComE(host_ip="fs118-come.fungible.local", ssh_username="fun", ssh_password="123")
    output = come.pre_reboot_cleanup()
    i = 0
    #come.setup_hbm_tools()
    #print come.setup_tools()
