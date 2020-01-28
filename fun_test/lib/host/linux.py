import pexpect
import paramiko
from paramiko_expect import SSHClientInteraction
import re
import collections
import sys
import os
import time
from lib.system.fun_test import fun_test, FunTimer
from fun_global import get_current_time
from lib.system.utils import ToDictMixin
import json
import copy
import traceback

class NoLogger:
    def __init__(self):
        self.trace_enabled = None
        self.trace_id = None
        
    def trace(self, enable, id):
        self.trace_enabled = enable
        self.trace_id = id

    def reset_context(self):
        if hasattr(self, "context"):
            self.context = None

    def write_now(self, message, stdout=True):
        pass
        
    def write(self, message, stdout=True):
        pass

    def flush(self):
        pass

    def log(self, message):
        fun_test.log(message=message, trace_id=self.trace_id)

    def critical(self, message):
        message = "\nCRITICAL: {}".format(message)
        fun_test.log(message=message, trace_id=self.trace_id)


class LinuxLogger:
    def __init__(self, context=None):
        self.trace_enabled = None
        self.trace_id = None
        self.context = context

    def reset_context(self):
        if hasattr(self, "context"):
            self.context = None

    def trace(self, enable, id):
        self.trace_enabled = enable
        self.trace_id = id

    def write_now(self, message, stdout=True):
        fun_test.write(message=message, context=self.context)
        fun_test.flush(trace_id=self.trace_id, stdout=stdout, context=self.context)

    def write(self, message, stdout=True):
        fun_test.write(message=message, context=self.context)

    def flush(self):
        fun_test.flush(trace_id=self.trace_id, context=self.context)

    def log(self, message):
        fun_test.log(message=message, trace_id=self.trace_id, context=self.context)

    def critical(self, message):
        message = "\nCRITICAL: {}".format(message)
        fun_test.log(message=message, trace_id=self.trace_id, context=self.context)


class Linux(object, ToDictMixin):
    ROOT_PROMPT_TERMINATOR_DEFAULT = "# "
    NON_ROOT_PROMPT_TERMINATOR_DEFAULT = r'\$ '
    SSH_PORT_DEFAULT = 22
    TELNET_PORT_DEFAULT = 23
    TMP_DIR_DEFAULT = "/tmp"
    PATHS_DEFAULT = []
    UNEXPECTED_EXPECT = "Bilee000ns"
    NVME_PATH = "/usr/local/sbin/nvme"

    # IPTABLES
    IPTABLES_TABLE_NAT = "nat"
    IPTABLES_CHAIN_RULE_DOCKER = "DOCKER"
    IPTABLES_CHAIN_RULE_INPUT = "INPUT"
    IPTABLES_CHAIN_RULE_POSTROUTING = "POSTROUTING"
    IPTABLES_ACTION_ACCEPT = "ACCEPT"
    IPTABLES_ACTION_DNAT = "DNAT"
    IPTABLES_ACTION_MASQUERADE = "MASQUERADE"
    IPTABLES_PROTOCOL_TCP = "tcp"

    TO_DICT_VARS = ["host_ip", "ssh_username", "ssh_password", "ssh_port"]
    DEBUG_LOG_FILE = "/tmp/linux_debug.txt"

    def __init__(self,
                 host_ip=None,
                 ssh_username="jabraham",
                 ssh_password="fun123",
                 ssh_port=SSH_PORT_DEFAULT,
                 telnet_username="root",
                 telnet_password="zebra",
                 telnet_port=TELNET_PORT_DEFAULT,
                 connect_retry_timeout_max=20,
                 use_paramiko=False,
                 localhost=None,
                 set_term_settings=True,
                 context=None,
                 ipmi_info=None,
                 use_telnet=None,
                 **kwargs):

        self.host_ip = host_ip
        self.ssh_username = ssh_username
        self.ssh_password = ssh_password
        self.ssh_port = ssh_port
        self.connect_retry_timeout_max = connect_retry_timeout_max
        self.handle = None
        self.set_term_settings = set_term_settings
        self.localhost = localhost
        self.use_paramiko = use_paramiko
        self.paramiko_handle = None
        self.logger = LinuxLogger(context=context)
        self.trace_enabled = None
        self.trace_id = None
        self.tmp_dir = None
        self.prompt_terminator = None
        self.root_prompt_terminator = Linux.ROOT_PROMPT_TERMINATOR_DEFAULT
        self.buffer = None
        self._set_defaults()
        self.use_telnet = False
        self.telnet_port = telnet_port
        self.telnet_username = telnet_username
        self.telnet_password = telnet_password
        self.extra_attributes = kwargs
        self.context = context
        self.ipmi_info = ipmi_info
        self.use_telnet = use_telnet
        if self.extra_attributes:
            if "ipmi_info" in self.extra_attributes:
                self.ipmi_info = self.extra_attributes["ipmi_info"]
        fun_test.register_hosts(host=self)
        self.was_power_cycled = False
        self.spawn_pid = None
        self.post_init()

    @staticmethod
    def get(asset_properties):
        """

        :rtype: object
        """
        prop = asset_properties
        ssh_username = prop.get("mgmt_ssh_username", prop.get("ssh_username"))
        ssh_password = prop.get("mgmt_ssh_password", prop.get("ssh_password"))
        ssh_port = prop.get("mgmt_ssh_port", 22)

        return Linux(host_ip=prop["host_ip"], ssh_username=ssh_username,
                     ssh_password=ssh_password, ssh_port=ssh_port)

    def reset_context(self):
        self.logger.reset_context()

    def enable_logs(self, enable=True):
        if enable:
            self.logger = LinuxLogger()
        else:
            self.logger = NoLogger()

    def post_init(self):
        pass

    def __getstate__(self):
        d = dict(self.__dict__)
        if 'handle' in d:
            del d['handle']
        if 'logger' in d:
            del d['logger']
        return d

    def __setstate__(self, state):
        state["logger"] = self.logger = LinuxLogger()  # TODO? What is the current logger?
        state["handle"] = None
        self.__dict__.update(state)

    def _set_defaults(self):
        self.tmp_dir = self.TMP_DIR_DEFAULT
        if self.ssh_username == 'root':
            if self.use_paramiko:
                self.prompt_terminator = '.*' + self.ROOT_PROMPT_TERMINATOR_DEFAULT
            else:
                self.prompt_terminator = self.ROOT_PROMPT_TERMINATOR_DEFAULT
        else:
            if self.use_paramiko:
                self.prompt_terminator = ".*" + self.NON_ROOT_PROMPT_TERMINATOR_DEFAULT
            else:
                self.prompt_terminator = self.NON_ROOT_PROMPT_TERMINATOR_DEFAULT
        self.saved_prompt_terminator = self.prompt_terminator


    def trace(self, enable, id):
        self.logger.trace(enable=enable, id=id)

    def ip_route_add(self, network, gateway, outbound_interface, timeout=30):
        # "ip route add 10.1.0.0/16  via 172.17.0.1 dev eth0"
        command = "ip route add {} via {} dev {}".format(network, gateway, outbound_interface)
        return self.sudo_command(command, timeout=timeout)

    def _debug_expect_buffer(self):
        fun_test.debug("Expect Buffer Before:%s" % self.handle.before)
        fun_test.debug("Expect Buffer After:%s" % self.handle.after)
        fun_test.debug("Expect Buffer:%s" % self.handle.buffer)

    @fun_test.safe
    def _paramiko_connect(self):
        client = paramiko.SSHClient()

        # Set SSH key parameters to auto accept unknown hosts
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to the host
        client.connect(hostname=self.host_ip, username=self.ssh_username, password=self.ssh_password)

        self.paramiko_handle = SSHClientInteraction(client, timeout=10, display=True)

    @fun_test.safe
    def _connect(self):
        if self.use_paramiko:
            return self._paramiko_connect()
        result = None
        connected = False

        try:
            expects = collections.OrderedDict()
            expects[0] = '[pP]assword'
            expects[1] = '\(yes/no\)?'
            if self.ssh_username == 'root':
                self.prompt_terminator = self.root_prompt_terminator
            expects[2] = self.prompt_terminator + r'$'
            expects[3] = 'Escape character is'
            if self.use_telnet:
                expects[4] = 'login:'


            attempt = 0
            loop_count_max = 10
            start_time = time.time()
            elapsed_time = 0
            while elapsed_time < self.connect_retry_timeout_max:
                if attempt:
                    fun_test.log("Attempting connect: {}, Remaining time: {}".format(attempt, self.connect_retry_timeout_max - elapsed_time))
                if not self.use_telnet:
                    fun_test.debug(
                        "Attempting SSH connect to %s username: %s password: %s" % (self.host_ip,
                                                                                    self.ssh_username,
                                                                                    self.ssh_password))
                    fun_test.debug("Prompt terminator:%s " % self.prompt_terminator)
                    if self.ssh_port:
                        ssh_command = 'ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null %s@%s -p %d' % (self.ssh_username,
                                                                                           self.host_ip,
                                                                                           int(self.ssh_port))
                    else:
                        ssh_command = 'ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null %s@%s' % (self.ssh_username,
                                                                                     self.host_ip)
                    if not self.localhost:
                        self.logger.log(ssh_command)

                        self.handle = pexpect.spawn(ssh_command,
                                                    env={"TERM": "dumb"},
                                                    maxread=4096)
                    else:
                        self.prompt_terminator = r'(\$ |# )'
                        expects[2] = self.prompt_terminator + r'$'
                        self.handle = pexpect.spawn("bash",
                                                    env={"TERM": "dumb"},
                                                    maxread=4096)
                    self.spawn_pid = self.handle.pid
                else:
                    fun_test.debug(
                        "Attempting Telnet connect to %s username: %s password: %s" % (self.host_ip,
                                                                                    self.ssh_username,
                                                                                    self.ssh_password))
                    fun_test.debug("Prompt terminator:{} Root prompt terminator: {}".format(self.prompt_terminator, self.root_prompt_terminator))
                    telnet_command = 'telnet -l {} {} {}'.format(self.telnet_username, self.host_ip, self.telnet_port)
                    self.logger.log(telnet_command)
                    self.handle = pexpect.spawn(telnet_command,
                                                env={"TERM": "dumb", "PATH": "$PATH:/usr/local/bin:/usr/bin"},
                                                maxread=4096)

                # self.handle.logfile_read = sys.stdout
                self.handle.logfile_read = self.logger

                current_loop_count = 0
                while current_loop_count < loop_count_max:
                    try:
                        i = self.handle.expect(expects.values(), timeout=20)
                        if i == 0:
                            self._debug_expect_buffer()
                            if not self.use_telnet:
                                self.logger.log("Sending Password: %s" % self.ssh_password)
                                self.sendline(self.ssh_password)
                            else:
                                self.logger.log("Sending Password: %s" % self.telnet_password)
                                self.sendline(self.telnet_password)
                            current_loop_count += 1
                        elif i == 1:
                            self._debug_expect_buffer()
                            fun_test.debug("Sending: %s" % "yes")
                            self.sendline("yes")
                            current_loop_count += 1
                        elif i == 2:
                            self._debug_expect_buffer()
                            self.logger.log("Connected to %s Using %s:%s" % (self.host_ip,
                                                                             self.ssh_username,
                                                                             self.ssh_password))
                            connected = True
                            self.command("")

                            break
                        elif i == 3:
                            self.sendline("")
                        elif i == 4:
                            self.sendline("{}".format(self.telnet_username))
                    except Exception as ex:
                        attempt += 1
                        retry_sleep = 1
                        self.logger.log("Sleeping {} seconds for next attempt".format(retry_sleep))
                        time.sleep(retry_sleep)
                        break
                if connected:
                    break
                elapsed_time = time.time() - start_time

            if elapsed_time > self.connect_retry_timeout_max:
                critical_str = "Unable to connect to %s. Exceed max time: %d" % (self.host_ip,
                                                                                 self.connect_retry_timeout_max)
                fun_test.critical(critical_str)
                self.logger.critical(critical_str)
        except Exception as ex:
            critical_str = ex.message
            fun_test.critical(critical_str)
            self.logger.critical(critical_str)
        if connected:
            if self.set_term_settings and not self._set_term_settings():
                raise Exception("Unable to set term settings")
            if not self._set_paths():
                raise Exception("Unable to set paths")
            result = True
            self._add_to_debug_log()
        else:
            self.handle = None
        return result

    def _add_to_debug_log(self):
        # IN-478
        try:
            s = "{} {}\n".format(get_current_time(), traceback.format_stack())
            f = open(self.DEBUG_LOG_FILE, "a+")
            f.write(s)
            f.close()
        except:
            pass

    def _set_term_settings(self):
        self.command("shopt -s checkwinsize")
        self.command("setterm -linewrap off")
        self.command("stty cols %d" % 1024)
        self.sendline(chr(0))
        self.handle.expect(self.prompt_terminator, timeout=1)
        return True

    def send_control(self, c):
        self.handle.sendcontrol(char=c)

    def send_control_c(self, timeout=1):
        self.send_control(c='c')
        try:
            self.handle.expect(self.prompt_terminator, timeout=timeout)
        except (pexpect.EOF, pexpect.TIMEOUT):
            pass

    def send_control_z(self, timeout=1):
        self.send_control(c='z')
        try:
            self.handle.expect(self.prompt_terminator, timeout=timeout)
        except (pexpect.EOF, pexpect.TIMEOUT):
            pass

    def add_path(self, additional_path):
        c = "export PATH=$PATH:{}".format(additional_path)
        self.command(c)

    def _paramiko_command(self, command, timeout):
        if not self.paramiko_handle:
            self._paramiko_connect()
        self.paramiko_handle.send(command)
        self.logger.write_now(message=self.paramiko_handle.current_send_string, stdout=False)
        self.paramiko_handle.expect(self.prompt_terminator, timeout=timeout)
        clean_output = self.paramiko_handle.current_output_clean
        self.logger.write_now(message=self.paramiko_handle.current_output_clean, stdout=False)
        return clean_output

    @fun_test.safe
    def command(self, command, sync=False, timeout=60, sync_timeout=0.3, custom_prompts=None, wait_until=None,
                wait_until_timeout=60, include_last_line=False, include_first_line=False, run_to_completion=None):

        if run_to_completion:
            fun_test.critical("run_to_completion is not recommended")
            timeout = 9999
        if self.use_paramiko:
            return self._paramiko_command(command=command, timeout=timeout)
        buf = ''
        try:
            if not custom_prompts:
                custom_prompts = {}
            if not self.handle:
                if not self._connect():
                    raise Exception("Unable to connect to %s, username: %s, password: %s" % (self.host_ip,
                                                                                             self.ssh_username,
                                                                                             self.ssh_password))
                self.sendline(chr(0))
                try:
                    self.handle.expect(self.prompt_terminator, timeout=1)
                except (pexpect.EOF, pexpect.TIMEOUT):
                    pass  # We are expecting an intentional timeout

            if sync:
                self.sendline(chr(0))
                try:
                    self.handle.expect(self.prompt_terminator, timeout=sync_timeout)
                except (pexpect.EOF):
                    self.disconnect(self)
                    return self.command(command=command,
                                        sync=sync, timeout=timeout,
                                        custom_prompts=custom_prompts,
                                        wait_until=wait_until,
                                        wait_until_timeout=wait_until_timeout,
                                        include_last_line=include_last_line)
                except (pexpect.EOF, pexpect.TIMEOUT):
                    pass  # We are expecting an intentional timeout
            command_lines = command.split('\n')
            prompt_terminator_processed = False
            for c in command_lines:
                self.sendline(c)
                if wait_until and (len(command_lines) == 1):
                    try:
                        self.handle.timeout = wait_until_timeout  # Pexpect does not honor timeouts
                        self.handle.expect(wait_until, timeout=wait_until_timeout)
                    except (pexpect.EOF):
                        Linux.disconnect(self)
                        return self.command(command=command,
                                            sync=sync, timeout=timeout,
                                            custom_prompts=custom_prompts,
                                            wait_until=wait_until,
                                            wait_until_timeout=wait_until_timeout,
                                            include_last_line=include_last_line)
                    except (pexpect.TIMEOUT):
                        # self._clean_buffer()
                        pass
                    buf += self.handle.before.lstrip() + str(self.handle.after).lstrip()
                elif custom_prompts:
                    done = False
                    max_custom_prompt_timer = FunTimer(max_time=timeout)
                    while not max_custom_prompt_timer.is_expired():
                        all_prompts_list = custom_prompts.keys()
                        all_prompts_list.append(self.prompt_terminator)
                        self.handle.timeout = timeout  # Pexpect does not honor timeouts
                        i = self.handle.expect(all_prompts_list, timeout=timeout)
                        if i == (len(all_prompts_list) - 1):
                            buf = buf + self.handle.before.lstrip()
                            prompt_terminator_processed = True
                            break
                        else:
                            self.sendline(custom_prompts[custom_prompts.keys()[i]])
                try:
                    if not prompt_terminator_processed:
                        self.handle.expect(self.prompt_terminator + r'$', timeout=timeout)
                except pexpect.EOF:
                    Linux.disconnect(self)
                    # return self.command(command=command,
                    #                    sync=sync, timeout=timeout,
                    #                    custom_prompts=custom_prompts,
                    #                    wait_until=wait_until,
                    #                    wait_until_timeout=wait_until_timeout,
                    #                    include_last_line=include_last_line)
                except Exception as ex:
                    self.clean()
                    raise ex
                finally:
                    buf = buf + self.handle.before.lstrip()
            buf_lines = buf.split('\n')
            self.buffer = buf
            start_line = 0
            if not include_first_line:
                start_line = 1
            if not include_last_line:
                buf = '\n'.join(buf_lines[start_line:-1])
        except Exception as ex:
            critical_str = str(ex) + " Command: {}".format(command)
            fun_test.critical(critical_str, context=self.context)
            self.logger.critical(critical_str)
            raise ex
        return buf

    @fun_test.safe
    def interactive_command(self, command, timeout=0.5, expected_prompt=None):
        if expected_prompt and (timeout == 0.5):
            timeout = 5
        if not self.handle:
            self._connect()
        buf = ''
        try:
            self.sendline(command)
            if not expected_prompt:
                self.handle.expect(r'\\S*$', timeout=timeout)
            else:
                self.handle.expect(expected_prompt, timeout=timeout)
            buf += self.handle.before + self.handle.after
        except (pexpect.EOF, pexpect.TIMEOUT):
            buf += self.handle.before
        self.buffer = buf
        buf_lines = buf.split('\n')
        buf = '\n'.join(buf_lines[1:-1])  # Ignore the command itself start from 1
        return buf

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
            command = 'ping %s -c %d -i %s -s %s' % (str(dst), count, interval, size)
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

    @fun_test.safe
    def hping(self, dst, count=5, mode='faster', protocol_mode='icmp', max_percentage_loss=50, timeout=10,
              data_bytes=80):
        result = False
        percentage_loss = 100
        try:
            cmd = "hping3 %s --%s -d %d --%s -c %d" % (dst, protocol_mode, data_bytes, mode, count)
            output = self.sudo_command(command=cmd, timeout=timeout)
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

    @fun_test.safe
    def check_disk(self, threshold=75):
        result = False
        try:
            command = 'df -hl -xtmpfs --total'
            output = self.command(command)
            """
            total                  38G  8.9G   27G  26%
            """
            m = re.search(r'^total\s+\S+\s+\S+\s+\S+\s+(\d+)%', output, re.M | re.DOTALL)
            if m:
                result = int(m.group(1)) < threshold
        except Exception as ex:
            critical_str = str(ex)
            fun_test.critical(critical_str)
            self.logger.critical(critical_str)
        fun_test.debug("Disk utilization below %d limit: " % threshold + str(result) + "\n")
        return result

    @fun_test.safe
    def check_ssh(self):
        result = False
        try:
            result = self._connect()
        except Exception as ex:
            critical_str = str(ex)
            fun_test.critical(critical_str)
            self.logger.critical(critical_str)

        fun_test.debug("ssh status: " + str(result) + "\n")
        return result

    @fun_test.safe
    def service(self,
                service_name,
                action="restart"):
        result = None
        command = "service %s %s" % (service_name, action)
        try:
            output = self.sudo_command(command)
            m = re.search('FAIL', output, re.IGNORECASE)
            if m:
                fun_test.debug("command: %s failed" % command)
                result = False
            else:
                m1 = re.search('OK', output)
                m2 = re.search('Done', output)
                m3 = re.search('SUCCESS', output)
                if not m1 and not m2 and not m3:
                    fun_test.debug("command: %s failed. Expected OK, Done or SUCCESS statement" % command)
                else:
                    result = True
        except Exception as ex:
            critical_str = str(ex)
            fun_test.critical(critical_str)
            self.logger.critical(critical_str)
        return result

    @fun_test.safe
    def systemctl(self,
                  service_name,
                  action="restart"):

        result = False
        start_action = ["start", "restart", "reload"]
        stop_action  = ["stop"]
        start_status = "active"
        stop_status  = "inactive"

        # Applying the requested action on the desired service
        command = "systemctl %s %s --no-pager" % (action, service_name)
        try:
            output = self.sudo_command(command)
        except Exception as ex:
            critical_str = str(ex)
            fun_test.critical(critical_str)
            self.logger.critical(critical_str)
            return result
        # Checking whether the requested action applied correctly on the desired service
        command = "systemctl is-active %s" % (service_name)
        try:
            output = self.sudo_command(command)
            if action in start_action:
                if output.find(start_status) != -1:
                    result = True
                    fun_test.debug("{}ing of service {}: Passed".format(action.capitalize(), service_name))
                else:
                    result = False
                    fun_test.debug("{}ing of service {}: Failed".format(action.capitalize(), service_name))
            elif action in stop_action:
                if output.find(stop_status) != -1:
                    result = True
                    fun_test.debug("{}ing of service {}: Passed".format(action.capitalize(), service_name))
                else:
                    result = False
                    fun_test.debug("{}ing of service {}: Failed".format(action.capitalize(), service_name))
        except Exception as ex:
            critical_str = str(ex)
            fun_test.critical(critical_str)
            self.logger.critical(critical_str)
        return result

    @fun_test.safe
    def get_process_id(self, process_name):
        pid = None
        command = "pidof -x " + process_name
        try:
            output = self.command(command)
            m = re.search(r'(\d+)$', output.strip())
            if m:
                pid = int(m.group(1))
        except Exception as ex:
            critical_str = str(ex)
            fun_test.critical(critical_str)
            self.logger.critical(critical_str)

        return pid

    @fun_test.safe
    def get_process_id_by_pattern(self, process_pat, multiple=False):
        result = None
        pid = None
        pids = []
        command = "ps -ef | grep '" + process_pat + "'| grep -v grep"
        try:
            output = self.command(command)
            if output:
                # Converting the multi line output into list of lines
                output = output.split('\n')
                # If the output contains 2 lines, then the process matching the given pattern exists
                if len(output) >= 1:
                    if not multiple:
                        # Extracting the pid of the process matched the given pattern
                        pid = output[0].split()[1]
                        result = pid
                    else:
                        pids = [x.split()[1] for x in output]
                        result = pids
            else:
                if multiple:
                    result = []
        except Exception as ex:
            critical_str = str(ex)
            fun_test.critical(critical_str)
            self.logger.critical(critical_str)

        return result

    @fun_test.safe
    def process_exists(self, process_id, sudo=False):
        """
        Check if a process id exists
        :param process_id:
        :param sudo: set to True if the ps command needs to be executed with sudo
        :return: None/False if process_id does not exist, True otherwise
        """
        result = None
        if process_id is not None:
            process_id = int(process_id)
        command = "ps -ef | grep {}".format(process_id)
        if sudo:
            output = self.sudo_command(command)
        else:
            output = self.command(command)
        if output:
            m = re.search(r'(\S+)\s+(\d+)\s+(\d+).*', output)
            if m:
                pid = int(m.group(2))
                if pid:
                    result = pid == process_id
        return result

    @fun_test.safe
    def dd(self, input_file, output_file, block_size, count, timeout=60, sudo=False, **kwargs):

        result = 0
        dd_cmd = "dd if={} of={} bs={} count={}".format(input_file, output_file, block_size, count)
        if kwargs:
            for key, value in kwargs.items():
                arg = key + "=" + str(value)
                dd_cmd += " " + arg

        if not sudo:
            output = self.command(command=dd_cmd, timeout=timeout)
        else:
            output = self.sudo_command(command=dd_cmd, timeout=timeout)
        match = re.search(r'(\d+) bytes', output)
        if match:
            result = match.group(1)
        return result

    @fun_test.safe
    def create_file(self, file_name, contents):
        self.command("touch %s" % file_name)
        lines = contents.split('\n')
        if len(lines):
            processed_line = lines[0].replace(r'"', r'\"')
            self.command("printf \"%s\\n\" > %s" % (processed_line, file_name))

        if len(lines) > 1:
            for line in lines[1:]:
                processed_line = line.replace(r'"', r'\"')
                self.command("printf \"%s\\n\" >> %s" % (processed_line, file_name))
        return file_name

    @fun_test.safe
    def create_temp_file(self, file_name, contents):
        return self.create_file(file_name=self.get_temp_file_path(file_name=file_name),
                                contents=contents)

    def remove_file(self, file_name):
        self.command("rm -f %s" % file_name)
        return True

    def remove_directory_contents(self, directory):
        self.command("rm -rf %s/" % (directory.strip("/")))
        return True

    def remove_directory(self, directory, sudo=False):
        result = False
        if directory in ["/", "/root"]:
            fun_test.critical("Removing {} is not permitted".format(directory))
            result = True
        else:
            cmd = "rm -rf {}".format(directory)
            if not sudo:
                self.command(cmd)
            else:
                self.sudo_command(cmd)
        return result

    def remove_temp_file(self, file_name):
        return self.remove_file(file_name=self.get_temp_file_path(file_name=file_name))

    def get_temp_file_path(self, file_name):
        full_path = self.tmp_dir + "/" + file_name
        return full_path

    def get_bash_user_name(self):
        user_name = None
        result = re.search(pattern="(.*)$", string=self.command("echo $USER"))
        if result:
            user_name = result.group(0).strip()
        return user_name

    @fun_test.safe
    def list_files(self, path):
        o = self.command("ls -ltrd " + path)
        lines = o.split('\n')
        files = []
        for line in lines:
            if line and "No such" not in line :
                reg = re.compile(r'(.*) (\S+)')
                m = reg.search(line)
                if m:
                    files.append({"info": m.group(1), "filename": m.group(2)})
            if "No such" in line:
                files = []
                break
        return files

    @fun_test.safe
    def start_bg_process(self,
                         command,
                         get_job_id=False,
                         output_file='/dev/null',
                         timeout=3,
                         nohup=True):
        command = command.rstrip()
        if output_file != "":
            command += r' >&' + output_file + " "
        command += r'&'
        if nohup:
            command = "nohup " + command
        job_id = None
        process_id = None
        try:
            o = self.command(command=command, timeout=timeout)
            for line in o.split('\n'):
                line = line.strip()
                m = re.search(r'\[(\d+)\]\s+(\d+)$', line)
                if m:
                    job_id = m.group(1)
                    process_id = m.group(2)
                    break
            pass
        except pexpect.ExceptionPexpect:
            self.send_control_c()

        result = process_id
        if get_job_id:
            result = job_id
        if process_id:
            fun_test.sleep("Waiting for bg process to start", seconds=1)
        return result

    @fun_test.safe
    def fg_process(self,
                   job_id=None,
                   process_id=None):
        command = ""
        if job_id:
            command = "fg " + str(job_id)
        elif process_id:
            output = self.command(command="jobs -l")
            m = re.search(r'\[(\d+)\]\S?\s+' + str(process_id) + r'\s+', output)
            if m:
                command = "fg " + m.group(1)
        try:
            self.command(command=command)
        except pexpect.ExceptionPexpect:
            pass

    @fun_test.safe
    def kill_process(self,
                     process_id=None,
                     job_id=None,
                     signal=15,
                     override=False,
                     kill_seconds=5,
                     minimum_process_id=50,
                     sudo=True):
        if process_id is not None:
            process_id = int(process_id)
        if job_id is not None:
            job_id = int(job_id)
        if not process_id and not job_id:
            fun_test.critical(message="Please provide a valid process-id or job-id", context=self.context)
            return
        if ((process_id < minimum_process_id) and not override) and (not job_id):
            fun_test.critical(
                message="This API won't kill processes with PID < %d. Use the override switch" % minimum_process_id,
            context=self.context)
            return
        job_str = ""
        if job_id:
            job_str = "%"
        command = "kill -%s %s%s" % (str(signal), str(job_str), str(process_id))
        try:
            if sudo:
                self.sudo_command(command=command)
            else:
                self.command(command=command)
        except pexpect.ExceptionPexpect:
            pass
        self.command("")  # This is to ensure that back-ground tasks Exit message is processed before leaving this function
        fun_test.sleep("Waiting for kill to complete", seconds=kill_seconds, context=self.context)

    def tshark_capture_start(self):
        pass

    def tshark_capture_stop(self, process_id):
        return self.kill_process(process_id=process_id)

    def tcpdump_capture_start(self, interface, tcpdump_filename="/tmp/tcpdump_capture.pcap", snaplen=96, filecount=1,
                              packet_count=2000000, file_size=None, rotate_seconds=None, sudo=True):
        result = None
        try:
            if not file_size and not rotate_seconds:
                cmd = "sudo tcpdump -nni {} -s {} -c {} -W {} -w {}".format(interface, snaplen, packet_count, filecount,
                                                                            tcpdump_filename)
            elif file_size and rotate_seconds:
                cmd = "sudo tcpdump -nni {} -s {} -C {} -G {} -W {} -w {}".format(interface, snaplen, file_size,
                                                                                  rotate_seconds, filecount,
                                                                                  tcpdump_filename)
            elif file_size:
                cmd = "sudo tcpdump -nni {} -s {} -C {} -W {} -w {}".format(interface, snaplen, file_size, filecount,
                                                                            tcpdump_filename)
            elif rotate_seconds:
                cmd = "sudo tcpdump -nni {} -s {} -G {} -W {} -w {}".format(interface, snaplen, rotate_seconds,
                                                                            filecount, tcpdump_filename)

            fun_test.log("executing command: {}".format(cmd))
            if sudo:
                cmd = "nohup {} >/dev/null 2>&1 &".format(cmd)
                self.sudo_command(command=cmd)
                process_id = self.get_process_id_by_pattern(process_pat="tcpdump")
            else:
                process_id = self.start_bg_process(command=cmd)
            fun_test.log("tcpdump is started, process id: {}".format(process_id))
            if process_id:
                result = process_id
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    def tcpdump_capture_stop(self, process_id, wait_after_stop=0):
        return self.kill_process(process_id=process_id, kill_seconds=wait_after_stop)

    def tshark_parse(self, file_name, read_filter, fields=None, decode_as=None):
        pass

    def stat(self, file_name):
        result = {}
        command = "stat {}".format(file_name)
        output = self.command(command)
        for line in output.split("\n"):
            m = re.search("Size:\s+(\d+)", line)
            if m:
                result["size"] = int(m.group(1))
        return result

    @fun_test.safe
    def enter_sudo(self, preserve_environment=None):
        result = False
        if not self.handle:
            self._connect()
        self.saved_prompt_terminator = self.prompt_terminator
        self.set_prompt_terminator(prompt_terminator=self.root_prompt_terminator)
        prompt = r'assword\s+for\s+%s: ' % self.ssh_username
        mac_prompt = r'Password:.*'
        options_str = ""
        if preserve_environment:
            options_str += "-E "
        cmd = 'sudo {}bash'.format(options_str)
        output = self.command(cmd, custom_prompts={prompt: self.ssh_password, mac_prompt: self.ssh_password})
        result = True
        if "not found" in output:
            result = False
        return result

    @fun_test.safe
    def set_prompt_terminator(self, prompt_terminator):
        self.prompt_terminator = prompt_terminator

    @fun_test.safe
    def set_root_prompt_terminator(self, root_prompt_terminator):
        self.root_prompt_terminator = root_prompt_terminator

    @fun_test.safe
    def exit_sudo(self):
        if hasattr(self, 'saved_prompt_terminator'):
            self.set_prompt_terminator(prompt_terminator=self.saved_prompt_terminator)
        self.command("exit")

    @fun_test.safe
    def netstat(self, grep_filters=None):
        result = []
        command = "netstat -anpt"
        self.enter_sudo()
        if grep_filters:
            for grep_filter in grep_filters:
                command += " | grep %s" % (str(grep_filter))
        output = self.command(command)
        output_lines = output.split('\n')
        for output_line in output_lines:
            if output_line.startswith('Active') or (output_line.startswith('Proto')):
                continue
            parts = re.findall(r'\S+', output_line)
            if len(parts) == 7:
                d = dict()
                d["protocol"] = parts[0]
                d["recv_q"] = parts[1]
                d["send_q"] = parts[2]
                d["local_address"] = parts[3]
                if d["local_address"].count(':') == 1:
                    d["local_ip"], d["local_port"] = d["local_address"].split(":")
                else:
                    temp_parts = d["local_address"].split(":")  # must be ipv6
                    d["local_ip"], d["local_port"] = ":".join(temp_parts[0:-1]), temp_parts[-1]
                d["foreign_address"] = parts[4]
                if d["foreign_address"].count(':') == 1:
                    d["foreign_ip"], d["foreign_port"] = d["foreign_address"].split(":")
                else:
                    temp_parts = d["foreign_address"].split(":")  # must be ipv6
                    d["foreign_ip"], d["foreign_port"] = ":".join(temp_parts[0:-1]), temp_parts[-1]
                d["state"] = parts[5]
                d["pid_program_name"] = parts[6]
                result.append(d)
            else:
                pass  # TODO
        self.exit_sudo()
        return result

    @fun_test.safe
    def disconnect(self):
        if self.handle:
            self.handle.close()
        self.handle = None
        fun_test.log(message="Disconnecting: {}".format(self.spawn_pid), context=self.context)
        return True

    def _set_paths(self):
        pathstr = ""
        for path in self.PATHS_DEFAULT:
            pathstr += ":" + str(path)
        pathstr = "$PATH" + pathstr
        self.command("export PATH=%s" % pathstr)
        return True

    def _clean_buffer(self):
        try:
            self.handle.expect(r'.*$', timeout=0.3)
        except pexpect.ExceptionPexpect:
            pass

    @fun_test.safe
    def clean(self):
        self.send_control_c()
        try:
            self.handle.expect(self.UNEXPECTED_EXPECT, timeout=0.1)
        except pexpect.ExceptionPexpect:
            pass
        try:
            self.handle.expect(self.prompt_terminator, timeout=0.1)
        except pexpect.ExceptionPexpect:
            pass

    @fun_test.safe
    def cleanup(self):
        self.command("rm -rf {}/*".format(self.tmp_dir))

    @fun_test.safe
    def sendline(self, c):
        self.handle.sendline(c)

    @fun_test.safe
    def iptables(self,
                 flush=None,
                 append_chain_rule="INPUT",
                 action="DROP",
                 source_ip=None,
                 destination_ip=None,
                 interface=None,
                 protocol="all",
                 destination_port=None,
                 table=None,
                 nat_to_destination=None):
        """
        docker_host.iptables(table=Linux.IPTABLES_TABLE_NAT,
                             append_chain_rule=Linux.IPTABLES_CHAIN_RULE_DOCKER,
                             protocol=Linux.IPTABLES_PROTOCOL_TCP,
                             destination_port=port,
                             action=Linux.IPTABLES_ACTION_DNAT, nat_to_destination="{}:{}".format(internal_ip, port))

        # docker_host.command("iptables -t nat -A DOCKER -p tcp --dport 2220 -j DNAT --to-destination 172.17.0.2:2220")
        #docker_host.command(
        #    "iptables -t nat -A POSTROUTING -j MASQUERADE -p tcp --source 172.17.0.2 --destination 172.17.0.2 --dport 2220")

        docker_host.iptables(table=Linux.IPTABLES_TABLE_NAT,
                             append_chain_rule=Linux.IPTABLES_CHAIN_RULE_POSTROUTING,
                             protocol=Linux.IPTABLES_PROTOCOL_TCP,
                             source_ip=internal_ip,
                             action=Linux.IPTABLES_ACTION_MASQUERADE,
                             destination_ip=internal_ip,
                             destination_port=port)

        docker_host.iptables(action=Linux.IPTABLES_ACTION_ACCEPT,
                             protocol=Linux.IPTABLES_PROTOCOL_TCP,
                             destination_ip=internal_ip,
                             destination_port=port,
                             append_chain_rule=Linux.IPTABLES_CHAIN_RULE_DOCKER
                             )
        """
        result = True
        iptables_command = "iptables "
        try:
            if flush:
                self.sudo_command(iptables_command + "-F")
            else:
                interface_str = ""
                if interface:
                    interface_str = " -i {}".format(interface)

                table_str = ""
                if table:
                    table_str = " -t {}".format(table)

                nat_to_destination_str = ""
                if nat_to_destination:
                    nat_to_destination_str = " --to-destination {}".format(nat_to_destination)
                command = iptables_command + "-A %s %s %s -j %s -p %s %s" % (append_chain_rule,
                                                                          interface_str,
                                                                          table_str,
                                                                          action,
                                                                          protocol,
                                                                          nat_to_destination_str)
                if append_chain_rule == "OUTPUT":
                    command = iptables_command + "-A %s -j %s -p %s" % (append_chain_rule,
                                                                        action,
                                                                        protocol)
                if source_ip:
                    command += " -s \"%s\"" % source_ip
                if destination_ip:
                    command += " -d \"%s\"" % destination_ip
                if destination_port:
                    command += " --dport %d" % destination_port
                self.sudo_command(command=command)
        except Exception as ex:
            critical_str = str(ex)
            fun_test.critical(critical_str)
            self.logger.critical(critical_str)
        return result

    @fun_test.safe
    def sudo_command(self, command, timeout=60, preserve_environment=None):
        sudoed = self.enter_sudo(preserve_environment=preserve_environment)
        output = self.command(command, timeout=timeout)
        if sudoed:
            self.exit_sudo()
        return output

    @fun_test.safe
    def cp(self, source_file_name, destination_file_name, recursive=False, sudo=False):
        command = "yes | cp {0} {1} {2}".format("-r" if recursive else "", source_file_name, destination_file_name)
        response = self.sudo_command(command) if sudo else self.command(command)
        return response

    @fun_test.safe
    def backup_file(self, source_file_name):
        destination_file_name = self.tmp_dir + "/" + os.path.basename(source_file_name) + ".backup"
        self.cp(source_file_name=source_file_name, destination_file_name=destination_file_name)
        backup_obj = LinuxBackup(linux_obj=self,
                                 source_file_name=source_file_name,
                                 backedup_file_name=destination_file_name)
        return backup_obj

    @fun_test.safe
    def read_file(self, file_name, include_last_line=False):
        output = self.command("cat %s" % file_name, include_last_line=include_last_line)
        lines = output.split('\n')
        processed_output = output
        if len(lines) > 1:
            processed_output = '\n'.join(lines[1:])
        return processed_output

    @fun_test.safe
    def tail(self, file_name, line_count=5):
        output = self.command("tail -%d %s" % (line_count, file_name))
        lines = output.split('\n')
        # processed_output = output
        '''
        if len(lines) > 1:
            processed_output = '\n'.join(lines[1:])
        '''
        return lines

    @fun_test.safe
    def replace_line(self, file_name, search_line_regex, desired_line):
        file_contents = self.read_file(file_name=file_name)
        processed_lines = []
        lines = file_contents.split('\n')
        for line in lines:
            if re.search(search_line_regex, line):
                processed_lines.append(desired_line)
            else:
                processed_lines.append(line.strip())
        processed_output = '\n'.join(processed_lines)
        return self.create_file(file_name=file_name, contents=processed_output)

    @fun_test.safe
    def check_file_directory_exists(self,
                                    path):
        result = False
        try:
            command = 'if [ -f ' + path + ' ] || [ -d ' + path + ' ]; then echo "True"; else echo "False"; fi'
            output_command = self.command(command=command, timeout=60)
            if 'True' in output_command:
                output = True
            else:
                output = False
            result = output
        except Exception as ex:
            critical_str = str(ex)
            fun_test.critical(critical_str)
            self.logger.critical(critical_str)

        return result

    @fun_test.safe
    def exit_status(self):
        output = self.command("echo $?")
        output = output.rstrip()
        exit_code = None
        try:
            exit_code = int(output)
        except ValueError:
            pass
        return exit_code

    @fun_test.safe
    def tc(self, target_ip=None, delay_in_ms=None, interface=None, remove=None):
        result = False
        entered_sudo = False
        try:
            if not interface:
                raise Exception("Please provide mgmt_interface of machine")

            if remove:
                command_list = ["tc qdisc del root dev %s" % interface, "modprobe -r ifb"]
                self.enter_sudo()
                for command in command_list:
                    self.command(command=command)
                self.exit_sudo()
                result = True
            else:
                if not target_ip or not delay_in_ms:
                    raise Exception("Please provide target_ip and delay in milliseconds")

                command_list = ["modprobe ifb numifbs=1",
                                "ip link set dev ifb0 up",
                                "tc qdisc add dev %s handle 1:0 root htb" % interface,
                                "tc class add dev %s parent 1:0 classid 1:1 htb rate 100Mbps" % interface,
                                "tc qdisc add dev %s parent 1:1 handle 10: netem delay %dms" % (interface, delay_in_ms),
                                "tc filter add dev %s protocol ip parent 1:0 prio 3 u32 match ip dst %s flowid 1:1" % (
                                    interface, target_ip)]
                self.enter_sudo()
                entered_sudo = True
                m = None
                for command in command_list:
                    output = self.command(command=command)
                    m = re.search(r".*File\sexists.*", output)
                    if m:
                        result = False
                        break
                if m is None:
                    result = True
                self.exit_sudo()
        except Exception as ex:
            critical_str = str(ex)
            fun_test.critical(critical_str)
            self.logger.critical(critical_str)
            if entered_sudo:
                self.exit_sudo()
        return result

    @fun_test.safe
    def scp(self, source_file_path, target_ip, target_file_path, target_username, target_password, target_port=22, timeout=60, sudo=False, sudo_password=None):
        transfer_complete = False
        sudo_string = ""
        if sudo:
            sudo_string = "sudo "
        scp_command = "%sscp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -P %d %s %s@%s:%s" % (sudo_string, target_port, source_file_path, target_username, target_ip, target_file_path)
        if not self.handle:
            self._connect()

        handle = self.handle
        handle.sendline(scp_command)
        handle.logfile_read = fun_test

        expects = collections.OrderedDict()
        expects[0] = '[pP]assword:'
        expects[1] = self.prompt_terminator + r'$'
        expects[2] = '\(yes/no\)?'

        if sudo:
            expects[3] = '{}@.*password'.format(sudo_password)

        max_retry_count = 10
        max_loop_count = 10

        attempt = 0
        try:
            while attempt < max_retry_count and not transfer_complete:
                current_loop_count = 0
                while current_loop_count < max_loop_count:
                    try:
                        i = handle.expect(expects.values(), timeout=timeout)
                        if i == 0:
                            fun_test.debug("Sending: %s" % target_password)
                            handle.sendline(target_password)
                            current_loop_count += 1
                        if i == 2:
                            fun_test.debug("Sending: %s" % "yes")
                            handle.sendline("yes")
                            current_loop_count += 1
                        if i == 1:
                            transfer_complete = True
                            break
                        if i == 3 and sudo and sudo_password:
                            handle.sendline(sudo_password)
                            current_loop_count += 1
                    except pexpect.exceptions.EOF:
                        transfer_complete = True
                        break
        except Exception as ex:
            critical_str = str(ex)
            fun_test.critical(critical_str)
            self.logger.critical(critical_str)

        if self.exit_status():
            transfer_complete = False

        return transfer_complete

    @fun_test.safe
    def md5sum(self, file_name, timeout=60):
        result = None
        command = "md5sum " + file_name + " | cut -d ' ' -f 1"
        try:
            output = self.sudo_command(command, timeout=timeout)
            fun_test.debug(output)
            output_lines = output.split('\n')
            fun_test.debug(output_lines)
            result = output_lines[0].strip()
        except Exception as ex:
            critical_str = str(ex)
            fun_test.critical(critical_str)
            self.logger.critical(critical_str)
        return result

    @fun_test.safe
    def untar(self, file_name, dest, timeout=60, sudo=True):
        result = None
        command = "tar -xvzf " + file_name + " -C " + dest
        try:
            if sudo:
                output = self.sudo_command("tar -xvzf " + file_name + " -C " + dest)
            else:
                output = self.command("tar -xvzf " + file_name + " -C " + dest)
            fun_test.debug(output)
            output_lines = output.split('\n')
            fun_test.debug(output_lines)
            result = True
        except Exception as ex:
            result = False
            critical_str = str(ex)
            fun_test.critical(critical_str)
            self.logger.critical(critical_str)
        return result

    @fun_test.safe
    def command_exists(self, command):
        self.command("which " + command)
        exit_status = self.exit_status()  #TODO
        return exit_status == 0

    @fun_test.safe
    def initialize(self, reset=False):
        if reset:
            self.reset()
        self.iptables(flush=True)
        return True

    @fun_test.safe
    def reset(self):
        self.sudo_command("rm -rf /tmp/*")

    @fun_test.safe
    def nslookup(self, dns_name):
        result = {}
        try:
            self.logger.log("Fetching ip address")
            command = "nslookup  %s | grep -A2 Name | grep Address " % dns_name
            output = self.sudo_command(command=command)
            output_lines = output.split('\n')
            obj = re.match('(.*):(.*)', output_lines[0])
            result['ip_address'] = obj.group(2).strip()
        except Exception as ex:
            critical_str = str(ex)
            fun_test.critical(critical_str)
            self.logger.critical(critical_str)
        return result

    def __repr__(self):
        return "{}: {}".format(self.__class__.__name__, self.host_ip)

    @fun_test.safe
    def insmod(self, module):
        return self.sudo_command("insmod {}".format(module))

    @fun_test.safe
    def modprobe(self, module):
        return self.sudo_command("modprobe {}".format(module))

    @fun_test.safe
    def rmmod(self, module):
        return self.sudo_command("modprobe -r {}".format(module))

    @fun_test.safe
    def lsmod(self, module):
        result = {}
        lsmod_output = self.sudo_command("lsmod | grep {}".format(module))
        re_output = re.search(r'(%s)\s+(\d+)\s+(\d)' % module, lsmod_output)
        if re_output:
            result['name'] = re_output.group(1)
            result['size'] = int(re_output.group(2))
            result['used_by'] = int(re_output.group(3))
        return result

    @fun_test.safe
    def lspci(self, grep_filter=None, verbose=False, device=None, slot=None):
        result = []
        command = "lspci"
        if verbose:
            command += " -vvv"
        if device:
            command += " -d {}".format(device)
        if slot:
            command += " -s {}".format(slot)
        if grep_filter:
            command += " | grep {}".format(grep_filter)
        output = self.sudo_command(command)
        lines = output.split("\n")

        current_record = None
        current_capabilities_record = None
        parsing_capabilty = None
        for line in lines:

            m = re.search(r'(([a-f\d]+):(\d+)\.(\d+))\s+(.*?):', line)
            if m:
                id = m.group(1)
                bus_number = m.group(2)
                device_number = m.group(3)
                function_number = m.group(4)
                device_class = m.group(5)
                record = {"id": id,
                          "bus_number": bus_number,
                          "device_number": device_number,
                          "function_number": function_number,
                          "device_class": device_class,
                          "capabilities": {}}
                current_record = record
                result.append(record)

            if verbose:
                match_numa_node = re.search(r'(?<=NUMA node: )[0-9]+', line)
                if match_numa_node:
                    current_record['numa_node'] = int(match_numa_node.group())
                m2 = re.search(r'\s+Capabilities: \[(\d+)\]', line)  # Capabilities: [80] Express (v2) Endpoint, MSI 00
                if m2:
                    current_record["capabilities"][m2.group(1)] = {}
                    current_capabilities_record = current_record["capabilities"][m2.group(1)]

                    parsing_capabilty = True
                if parsing_capabilty:
                    m3 = re.search("LnkSta:.*Width\s+(x\d+)", line)
                    if m3:
                        if current_capabilities_record is not None:
                            current_capabilities_record["LnkSta"] = {}
                            current_capabilities_record["LnkSta"]["Width"] = m3.group(1)
        return result

    @fun_test.safe
    def nvme_setup(self):
        self.command("cd .") #TODO
        modules = ["nvme-core.ko", "nvme.ko"]
        for module in modules:
            self.insmod(module=module)
            fun_test.sleep("Insmod wait", seconds=2)
        return True

    @fun_test.safe
    def nvme_create_namespace(self, size, capacity, device):
        command = "{} create-ns --nsze={} --ncap={} {}".format(self.NVME_PATH, size, capacity, device)
        return self.sudo_command(command)

    @fun_test.safe
    def nvme_attach_namespace(self, namespace_id, controllers, device):
        command = "{} attach-ns --namespace-id={} --controllers={} {}".format(self.NVME_PATH,
                                                                             namespace_id,
                                                                             controllers,
                                                                             device)
        return self.sudo_command(command)

    @fun_test.safe
    def nvme_restart(self, reload_interval=10):
        result = True
        # Unloading the nvme driver
        unload_status = self.rmmod("nvme")
        if not unload_status:
            fun_test.sleep("Waiting for nvme driver unload to complete", seconds=reload_interval)
            load_status = self.modprobe("nvme")
            # fun_test.sleep("Waiting for nvme driver load to complete", seconds=reload_interval)
            if load_status:
                result = False
        else:
            result = False
        return result

    @fun_test.safe
    def lsblk(self, options=None):
        result = collections.OrderedDict()
        if options:
            cmd = "lsblk " + options
        else:
            cmd = "lsblk"
        output = self.command(cmd)
        lines = output.split("\n")
        for line in lines:

            """NAME    MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
               sr0      11:0    1 1024M  0 rom  """
            m = re.search(r'(.*\S+)\s+(\S+)\s+(\d+)\s+(\S+|\d+)\s+(\d+)\s+(\S+)\s+(\S+)?', line)
            if m:
                name = m.group(1)
                major_min = m.group(2)
                rm = int(m.group(3))
                size = m.group(4)
                ro = int(m.group(5))
                type = m.group(6)
                mount_point = m.group(7)

                name_alpha = name
                m = re.search("([A-Za-z0-9].*)", name_alpha)
                if m:
                    name_alpha = m.group(1)
                result_d = {}
                result_d["name"] = name
                result_d["major_min"] = major_min
                result_d["rm"] = rm
                result_d["size"] = size
                result_d["ro"] = ro
                result_d["type"] = type
                result_d["mount_point"] = mount_point
                result[name_alpha] = result_d
        return result

    @fun_test.safe
    def get_ip_route(self, netns=None):
        """Do 'ip -n <netns> route' to get kernel FIB info

        root@ubuntu:~# ip -n 1-1 route show
        default via 172.17.0.1 dev eth0
        ..
        10.0.0.48/28 via 192.168.0.10 dev p-69  proto 186  metric 20
        10.0.1.0/28  proto 186  metric 20
        	nexthop via 192.96.0.2  dev p-1 weight 1
        	nexthop via 192.96.0.6  dev p-3 weight 1
        192.96.0.0/30 dev p-1  proto kernel  scope link  src 192.96.0.1
        ..

        :return: dict {'0.0.0.0/0': {'172.17.0.1': 'eth0'},
                       '10.0.0.48/28': {'192.168.0.10': 'p-69'},
                       '10.0.1.0/28': {'192.96.0.2': 'p-1', '192.96.0.6': 'p-3'},
                       '192.96.0.0/30': {'directly connected': 'p-1'},
                        ..}
        """
        result = {}
        command = "ip -n %s route show" % netns if netns else 'ip route show'
        output = self.command(command)

        pat_ip_addr = r'(?:\d{1,3}\.){3}\d{1,3}'
        m = re.findall(r'^(%s/\d{1,2}|default|).*?(?:via )?(%s|)\s+dev\s+(\S+)' % (pat_ip_addr, pat_ip_addr), output,
                       re.S | re.M)
        if m:
            for prefix, nhp, interface in m:
                if prefix == 'default':  # format it to match FRR's FIB
                    prefix = '0.0.0.0/0'
                if nhp == '':
                    nhp = 'directly connected'  # format it to match FRR's FIB
                if prefix:
                    prefix_cache = prefix
                else:
                    prefix = prefix_cache
                result.setdefault(prefix, {}).update({nhp: interface})
        return result

    @fun_test.safe
    def old_fio(self, destination_ip, timeout=60, **kwargs):

        fio_command = "fio"
        fio_result = ""
        fio_dict = {}

        fun_test.debug(kwargs)

        # Building the fio command
        if 'name' not in kwargs:
            fio_command += " --name=fun_nvmeof"

        if 'ioengine' not in kwargs:
            fio_command += " --ioengine=fun"

        fio_command += " --dest_ip={}".format(destination_ip)

        if 'source_ip' not in kwargs:
            fio_command += " --source_ip={}".format(self.internal_ip)

        if 'numjobs' not in kwargs:
            fio_command += " --numjobs=1"

        if 'io_queues' not in kwargs:
            fio_command += " --io_queues=2"

        if 'nrfiles' not in kwargs:
            fio_command += " --nrfiles=1"

        if 'nqn' not in kwargs:
            fio_command += " --nqn=nqn.2017-05.com.fungible:nss-uuid1"

        if 'nvme_mode' not in kwargs:
            fio_command += " --nvme_mode=IO_ONLY"

        if kwargs:
            for key in kwargs:
                fio_command += " --" + key + "=" + str(kwargs[key])

        fun_test.debug(fio_command)

        # Executing the fio command
        fio_result = self.command(command=fio_command, timeout=timeout)
        # fio_result += '\n'
        fun_test.debug(fio_result)

        # Checking there is no error occurred during the FIO test
        match = ""
        match = re.search(r'Assertion .* failed', fio_result, re.I)
        if match:
            fun_test.critical("FIO test failed due to an error: {}".format(match.group(0)))
            return fio_dict
        # Extracting the Run status portion of the output and converting it into a dictionary
        match_obj = ""
        match_str = ""
        match_obj = re.compile(r'Run status group *\d+ *\(all jobs\):((?:(?!Disk stats).)*)', re.S)
        match_str = match_obj.search(fio_result)
        fun_test.simple_assert(match_str, "Found FIO Run status output")

        # Splitting the extracted portion into lines and stripping the whitespaces and newline characters from it
        match_list = ""
        match_str = match_str.group(1).strip()
        match_list = match_str.split('\n')
        fun_test.debug(match_list)

        # Extracting the bw, io and run time status for both read & write operation and populating it as dictionary
        # attributes
        for line in match_list:
            mode, stats = line.split(':')
            mode = mode.strip().lower()
            stats = stats.strip()
            fun_test.debug(mode)
            fun_test.debug(stats)
            fio_dict[mode] = {}

            for field, value in dict(x.split('=') for x in stats.split(',') if '=' in x).items():
                field = field.strip()
                value = int(re.sub(r'(\d+)(.*)', r'\1', value))
                fio_dict[mode][field] = value

        match = re.search(r'read: IOPS=(\d+)', fio_result)
        if match:
            fio_dict["read"]["iops"] = int(match.group(1))

        match = re.search(r'write: IOPS=(\d+)', fio_result)
        if match:
            fio_dict["write"]["iops"] = int(match.group(1))

        fun_test.debug(fio_dict)
        return fio_dict

    @fun_test.safe
    def remote_fio(self, destination_ip, timeout=60, **kwargs):

        # List contains the all pattern of all known/possible error from the FIO
        err_pat_list = [r'Assertion .* failed', r'.*err(or)*=.*']

        fio_command = "fio"
        fio_result = ""
        fio_dict = {}

        fun_test.debug(kwargs)

        # Building the fio command
        if 'name' not in kwargs:
            fio_command += " --name=fun_nvmeof"

        if 'ioengine' not in kwargs:
            fio_command += " --ioengine=fun"

        fio_command += " --dest_ip={}".format(destination_ip)

        if 'source_ip' not in kwargs:
            fio_command += " --source_ip={}".format(self.internal_ip)

        if 'numjobs' not in kwargs:
            fio_command += " --numjobs=1"

        if 'io_queues' not in kwargs:
            fio_command += " --io_queues=2"

        if 'nrfiles' not in kwargs:
            fio_command += " --nrfiles=1"

        if 'nqn' not in kwargs:
            fio_command += " --nqn=nqn.2017-05.com.fungible:nss-uuid1"

        if 'nvme_mode' not in kwargs:
            fio_command += " --nvme_mode=IO_ONLY"

        if 'output-format' not in kwargs:
            fio_command += " --output-format=json"

        if kwargs:
            for key in kwargs:
                fio_command += " --" + key + "=" + str(kwargs[key])

        fun_test.debug(fio_command)

        # Executing the fio command
        fio_result = self.command(command=fio_command, timeout=timeout)
        # fio_result += '\n'
        fun_test.debug(fio_result)

        # Trimming initial few lines to convert the output into a valid json format
        before, sep, after = fio_result.partition("{")
        trim_fio_result = sep + after
        fun_test.debug(trim_fio_result)

        # Checking there is no error occurred during the FIO test
        for pattern in err_pat_list:
            match = ""
            match = re.search(pattern, before, re.I)
            if match:
                fun_test.critical("FIO test failed due to an error: {}".format(match.group(0)))
                return fio_dict

        # Converting the json into python dictionary
        fio_result_dict = json.loads(trim_fio_result)
        fun_test.debug(fio_result_dict)

        # Populating the resultant fio_dict dictionary
        for operation in ["write", "read"]:
            fio_dict[operation] = {}
            for stat in ["bw", "iops", "latency"]:
                if stat != "latency":
                    fio_dict[operation][stat] = int(round(fio_result_dict["jobs"][0][operation][stat]))
                else:
                    for key in fio_result_dict["jobs"][0][operation].keys():
                        if key.startswith("lat"):
                            # Extracting the latency unit
                            unit = key[-2:]
                            # Converting the units into microseconds
                            if unit == "ns":
                                value = int(round(fio_result_dict["jobs"][0][operation][key]["mean"]))
                                value /= 1000
                                fio_dict[operation][stat] = value
                            elif unit == "us":
                                fio_dict[operation][stat] = int(round(fio_result_dict["jobs"][0][operation][key]["mean"]))
                            else:
                                value = int(round(fio_result_dict["jobs"][0][operation][key]["mean"]))
                                value *= 1000
                                fio_dict[operation][stat] = value

        fun_test.debug(fio_dict)
        return fio_dict

    @fun_test.safe
    def pcie_fio(self, filename, timeout=60, **kwargs):

        # List contains the all pattern of all known/possible error from the FIO
        err_pat_list = [r'Assertion .* failed', r'.*err(or)*=.*']

        fio_command = "fio"
        fio_result = ""
        fio_dict = {}

        try:
            fun_test.debug(kwargs)

            # Building the fio command

            # Add group reporting option (in case numjobs > 1)
            fio_command += " --group_reporting"

            if 'output-format' not in kwargs:
                fio_command += " --output-format=json"

            if "multiple_jobs" not in kwargs and 'name' not in kwargs:
                fio_command += " --name=nvme_pcie"

            if 'ioengine' not in kwargs:
                fio_command += " --ioengine=libaio"

            fio_command += " --filename={}".format(filename)

            if 'numjobs' not in kwargs:
                fio_command += " --numjobs=1"

            if 'runtime' in kwargs:
                fio_command += " --time_based"

            if kwargs:
                for key, value in kwargs.iteritems():
                    if key == "multiple_jobs":
                        fio_command += " " + str(value)
                        # In case of multiple jobs scenario if global filename exists, removing it
                        if fio_command.count("filename") >= 2:
                            fio_command = re.sub(r"--filename=\S+", "", fio_command, 1)
                    else:
                        if value != "NO_VALUE":
                            fio_command += " --" + key + "=" + str(value)
                        else:
                            fio_command += " --" + key

            fun_test.debug(fio_command)

            # Executing the fio command
            fio_result = self.sudo_command(command=fio_command, timeout=timeout)
            # fio_result += '\n'
            fun_test.debug(fio_result)

            # Trimming initial few lines to convert the output into a valid json format
            before, sep, after = fio_result.partition("{")
            trim_fio_result = sep + after
            fun_test.debug(trim_fio_result)

            # Checking there is no error occurred during the FIO test
            for pattern in err_pat_list:
                match = ""
                match = re.search(pattern, before, re.I)
                if match:
                    fun_test.critical("FIO test failed due to an error: {}".format(match.group(0)))
                    return fio_dict

            # Converting the json into python dictionary
            fio_result_dict = json.loads(trim_fio_result)
            fun_test.debug(fio_result_dict)

            # Populating the resultant fio_dict dictionary
            for operation in ["write", "read"]:
                fio_dict[operation] = {}
                stat_list = ["bw", "iops", "io_bytes", "runtime", "latency", "clatency", "latency50",
                             "latency90", "latency95", "latency99", "latency9950", "latency9999"]
                for stat in stat_list:
                    if stat not in ("latency", "clatency", "latency50", "latency90", "latency95",
                                    "latency99", "latency9950", "latency9999"):
                        fio_dict[operation][stat] = fio_result_dict["jobs"][0][operation][stat]
                    elif stat in ("latency", "clatency"):
                        for key in fio_result_dict["jobs"][0][operation].keys():
                            if key.startswith("lat"):
                                stat = "latency"
                                # Extracting the latency unit
                                unit = key[-2:]
                                # Converting the units into microseconds
                                if unit == "ns":
                                    value = int(round(fio_result_dict["jobs"][0][operation][key]["mean"]))
                                    value /= 1000
                                    fio_dict[operation][stat] = value
                                elif unit == "us":
                                    fio_dict[operation][stat] = int(round(fio_result_dict["jobs"][0][operation][key]["mean"]))
                                else:
                                    value = int(round(fio_result_dict["jobs"][0][operation][key]["mean"]))
                                    value *= 1000
                                    fio_dict[operation][stat] = value
                            if key.startswith("clat"):
                                stat = "clatency"
                                # Extracting the latency unit
                                unit = key[-2:]
                                # Converting the units into microseconds
                                if unit == "ns":
                                    value = int(round(fio_result_dict["jobs"][0][operation][key]["mean"]))
                                    value /= 1000
                                    fio_dict[operation][stat] = value
                                elif unit == "us":
                                    fio_dict[operation][stat] = int(round(fio_result_dict["jobs"][0][operation][key]["mean"]))
                                else:
                                    value = int(round(fio_result_dict["jobs"][0][operation][key]["mean"]))
                                    value *= 1000
                                    fio_dict[operation][stat] = value
                    elif stat in ("latency50", "latency90", "latency95", "latency99", "latency9950", "latency9999"):
                        for key in fio_result_dict["jobs"][0][operation].keys():
                            if key == "clat_ns":
                                for key in fio_result_dict["jobs"][0][operation]["clat_ns"]["percentile"].keys():
                                    if key.startswith("50.00"):
                                        stat = "latency50"
                                        value = int(round(
                                            fio_result_dict["jobs"][0][operation]["clat_ns"]["percentile"]["50.000000"]))
                                        value /= 1000
                                        fio_dict[operation][stat] = value
                                    if key.startswith("90.00"):
                                        stat = "latency90"
                                        value = int(round(
                                            fio_result_dict["jobs"][0][operation]["clat_ns"]["percentile"]["90.000000"]))
                                        value /= 1000
                                        fio_dict[operation][stat] = value
                                    if key.startswith("95.00"):
                                        stat = "latency95"
                                        value = int(round(
                                            fio_result_dict["jobs"][0][operation]["clat_ns"]["percentile"]["95.000000"]))
                                        value /= 1000
                                        fio_dict[operation][stat] = value
                                    if key.startswith("99.00"):
                                        stat = "latency99"
                                        value = int(round(
                                            fio_result_dict["jobs"][0][operation]["clat_ns"]["percentile"]["99.000000"]))
                                        value /= 1000
                                        fio_dict[operation][stat] = value
                                    if key.startswith("99.50"):
                                        stat = "latency9950"
                                        value = int(round(
                                            fio_result_dict["jobs"][0][operation]["clat_ns"]["percentile"]["99.500000"]))
                                        value /= 1000
                                        fio_dict[operation][stat] = value
                                    if key.startswith("99.99"):
                                        stat = "latency9999"
                                        value = int(round(
                                            fio_result_dict["jobs"][0][operation]["clat_ns"]["percentile"]["99.990000"]))
                                        value /= 1000
                                        fio_dict[operation][stat] = value
            fun_test.debug(fio_dict)
        except Exception as ex:
            fun_test.critical(ex.message)

        return fio_dict

    @fun_test.safe
    def fio(self, destination_ip, timeout=60, **kwargs):

        fio_command = "fio"
        fio_result = ""
        fio_dict = {}

        fun_test.debug(kwargs)

        # Building the fio command
        if 'name' not in kwargs:
            fio_command += " --name=fun_nvmeof"

        if 'numjobs' not in kwargs:
            fio_command += " --numjobs=1"

        if 'io_queues' not in kwargs:
            fio_command += " --io_queues=2"

        if 'nrfiles' not in kwargs:
            fio_command += " --nrfiles=1"

        if 'output-format' not in kwargs:
            fio_command += " --output-format=json"

        if kwargs:
            for key in kwargs:
                fio_command += " --" + key + "=" + str(kwargs[key])

        fun_test.debug(fio_command)

        # Executing the fio command
        fio_result = self.command(command=fio_command, timeout=timeout)
        # fio_result += '\n'
        fun_test.debug(fio_result)

        # Checking there is no error occured during the FIO test
        match = ""
        match = re.search(r'Assertion .* failed', fio_result, re.I)
        if match:
            fun_test.critical("FIO test failed due to an error: {}".format(match.group(0)))
            return fio_dict

        # Trimming initial few lines to convert the output into a valid json format
        before, sep, after = fio_result.partition("{")
        trim_fio_result = sep + after
        fun_test.debug(trim_fio_result)

        # Converting the json into python dictionary
        fio_result_dict = json.loads(trim_fio_result)
        fun_test.debug(fio_result_dict)

        # Populating the resultant fio_dict dictionary
        for operation in ["write", "read"]:
            fio_dict[operation] = {}
            for stat in ["bw", "iops", "latency"]:
                if stat != "latency":
                    fio_dict[operation][stat] = int(round(fio_result_dict["jobs"][0][operation][stat]))
                else:
                    for key in fio_result_dict["jobs"][0][operation].keys():
                        if key.startswith("lat"):
                            # Extracting the latency unit
                            unit = key[-2:]
                            # Converting the units into microseconds
                            if unit == "ns":
                                value = int(round(fio_result_dict["jobs"][0][operation][key]["mean"]))
                                value /= 1000
                                fio_dict[operation][stat] = value
                            elif unit == "us":
                                fio_dict[operation][stat] = int(round(fio_result_dict["jobs"][0][operation][key]["mean"]))
                            else:
                                value = int(round(fio_result_dict["jobs"][0][operation][key]["mean"]))
                                value *= 1000
                                fio_dict[operation][stat] = value

        fun_test.debug(fio_dict)
        return fio_dict

    def _ensure_reboot_is_initiated(self, ipmi_details, power_cycled=None, reboot_initiated_wait_time=60):
        reboot_initiated = False
        reboot_initiated_timer = FunTimer(max_time=reboot_initiated_wait_time)

        service_host_spec = fun_test.get_asset_manager().get_regression_service_host_spec()
        service_host = None
        if service_host_spec:
            service_host = Linux(**service_host_spec)
        while not reboot_initiated and not reboot_initiated_timer.is_expired() and not fun_test.closed:
            try:
                if service_host:
                    ping_result = service_host.ping(dst=self.host_ip, count=5)
                    if not ping_result:
                        reboot_initiated = True
                        fun_test.log("Reboot initiated (based on pings)")
                else:
                    self.ping(dst="127.0.0.1")
            except Exception as ex:
                try:
                    self.disconnect()
                    self._set_defaults()
                    reboot_initiated = True
                    fun_test.log("Reboot initiated (based on failing ssh)")
                except:
                    reboot_initiated = True
        if not reboot_initiated and reboot_initiated_timer.is_expired():
            fun_test.critical("Unable to verify reboot was initiated. Wait-time: {}".format(reboot_initiated_wait_time))
            if ipmi_details and not fun_test.closed:
                fun_test.log("Trying IPMI power-cycle".format(self.host_ip))
                ipmi_host_ip = ipmi_details["host_ip"]
                ipmi_username = ipmi_details["username"]
                ipmi_password = ipmi_details["password"]
                try:
                    service_host.ipmi_power_cycle(host=ipmi_host_ip, user=ipmi_username, passwd=ipmi_password, chassis=True)
                    power_cycled = True
                    reboot_initiated = True  # ipmi power-cycle already has a 30 second sleep
                    fun_test.log("IPMI power-cycle complete")
                except Exception as ex:
                    fun_test.critical(str(ex))
                    service_host.ipmi_power_on(host=ipmi_host_ip, user=ipmi_username, passwd=ipmi_password, chassis=True)
                    power_cycled = True
                    return self._ensure_reboot_is_initiated(ipmi_details=None, power_cycled=power_cycled)
        return reboot_initiated, power_cycled


    @fun_test.safe
    def reboot(self, timeout=5,
               retries=6,
               max_wait_time=180,
               non_blocking=None,
               ipmi_details=None,
               wait_time_before_host_check=None,
               reboot_initiated_wait_time=60,
               reboot_initiated_check=True):
        """
        :param timeout: deprecated
        :param retries: deprecated
        :param max_wait_time: Total time to wait before declaring failure
        :param non_blocking: if set to True, return immediately after issuing a reboot. However, this does not impact
               the check for reboot being initiated successfully. i.e, the function will try to confirm if reboot was
               initiated regardless of the non-blocking input
        :param ipmi_details: if ipmi_details are provided we will try power-cycling in case normal bootup did not work
        :param wait_time_before_host_check: wait time before we check if host is up. Might be useful when we know the
                system is prone to crashes
        :param reboot_initiated_wait_time: time to wait until we can confirm that reboot was initiated
        :param reboot_initiated_check: check if reboot was successfully initiated, using a failing ping or ssh test
               This tries to address extreme cases where the system remains alive even after a reboot command was
               executed
        :return:
        """
        result = True

        # Rebooting the host

        try:
            self.sudo_command(command="reboot", timeout=timeout)
        except Exception as ex:
            try:
                self.disconnect()
                self._set_defaults()
            except:
                pass

        reboot_initiated, power_cycled_already = (False, False)
        if not ipmi_details:
            if self.ipmi_info:
                ipmi_details = self.ipmi_info
        if reboot_initiated_check:
            reboot_initiated, power_cycled_already = self._ensure_reboot_is_initiated(ipmi_details=ipmi_details,
                                                                                      reboot_initiated_wait_time=reboot_initiated_wait_time)
        else:
            reboot_initiated = True
            fun_test.log("Reboot initiated check was not enabled. Assuming reboot was properly initiated")

        if not reboot_initiated:
            result = False
            fun_test.log("Reboot was not initiated")
        else:
            result = True
            if not non_blocking:
                if wait_time_before_host_check:
                    fun_test.sleep("Waiting before checking the host is up", seconds=wait_time_before_host_check)
                result = self.ensure_host_is_up(max_wait_time=max_wait_time,
                                                ipmi_details=ipmi_details,
                                                power_cycle=not power_cycled_already)
        return result

    @fun_test.safe
    def ensure_host_is_up(self, max_wait_time=180, ipmi_details=None, power_cycle=None, with_error_details=None):
        """
        Waits until the host is reachable. Typically needed after a reboot
        :param max_wait_time: total time to wait before giving
        :return: True, if the host is pingable and ssh'able, else False
        """
        error_message = ""
        fun_test.log("Ensuring the host is up: ipmi_details={}, power_cycle={}".format(ipmi_details, power_cycle), context=self.context)
        service_host_spec = fun_test.get_asset_manager().get_regression_service_host_spec()
        service_host = None
        if service_host_spec:
            service_host = Linux(context=self.context, **service_host_spec)
        else:
            fun_test.log("Regression service host could not be instantiated", context=self.context)
        host_is_up = False
        max_reboot_timer = FunTimer(max_time=max_wait_time)
        result = False
        ping_result = False
        ssh_result = False
        while not host_is_up and not max_reboot_timer.is_expired() and not fun_test.closed:
            if service_host and not ping_result:
                ping_result = service_host.ping(dst=self.host_ip, count=5)
            if ping_result or not service_host:
                try:
                    fun_test.log("Attempting SSH", context=self.context)
                    self.command("pwd")
                    ssh_result = True
                    host_is_up = True
                    result = host_is_up
                    fun_test.log("Host: {} is up".format(str(self)), context=self.context)
                    break
                except Exception as ex:
                    pass
            fun_test.log("Time remaining: {}".format(max_reboot_timer.remaining_time()))
        if not host_is_up:
            result = False
            error_message = "Host: {} is not up. Ping result: {} SSH result: {}".format(self.host_ip, ping_result, ssh_result)
            fun_test.critical("Host: {} is not reachable. Ping result: {}".format(self.host_ip, ping_result))


        if not host_is_up and service_host:
            result = False

            if not ipmi_details:
                if self.ipmi_info:
                    ipmi_details = self.ipmi_info

            if not result and ipmi_details and power_cycle:
                fun_test.log("Trying IPMI power-cycle".format(self.host_ip))
                ipmi_host_ip = ipmi_details["host_ip"]
                ipmi_username = ipmi_details["username"]
                ipmi_password = ipmi_details["password"]
                try:
                    self.was_power_cycled = False
                    service_host.ipmi_power_cycle(host=ipmi_host_ip, user=ipmi_username, passwd=ipmi_password, chassis=True)
                    fun_test.log("IPMI power-cycle complete")
                    self.was_power_cycled = True

                except Exception as ex:
                    fun_test.critical(str(ex))
                    service_host.ipmi_power_on(host=ipmi_host_ip, user=ipmi_username, passwd=ipmi_password, chassis=True)
                    self.was_power_cycled = True
                finally:
                    return self.ensure_host_is_up(max_wait_time=max_wait_time, power_cycle=False)
        try:
            if service_host:
                service_host.disconnect()
        except:
            pass
        if with_error_details:
            result = result, error_message
        return result

    @fun_test.safe
    def is_host_up(self, timeout=5, retries=6, max_wait_time=180, with_error_details=None):
        """
        deprecated. use ensure_host_is_up
        :param timeout: deprecated
        :param retries: deprecated
        :param max_wait_time: time to wait before giving up
        :param with_error_details: returns an error message along with the result
        :return:
        """
        return self.ensure_host_is_up(max_wait_time=max_wait_time, with_error_details=with_error_details)


    @fun_test.safe
    def ipmi_power_off(self, host, interface="lanplus", user="ADMIN", passwd="ADMIN", chassis=True):
        result = True
        chassis_string = "" if not chassis else " chassis"

        fun_test.log("Host: {}; Interface:{}; User: {}; Passwd: {}".format(host, interface, user, passwd))
        ipmi_cmd = "ipmitool -I {} -H {} -U {} -P {}{} power off".format(interface, host, user, passwd, chassis_string)
        expected_pat = r'Chassis Power Control: Down/Off'
        ipmi_out = self.command(command=ipmi_cmd)
        if ipmi_out:
            match = re.search(expected_pat, ipmi_out, re.I)
            if not match:
                fun_test.critical("IPMI power off: Failed")
                result = False
            else:
                fun_test.log("IPMI power off: Passed")
        else:
            fun_test.critical("IPMI power off: Failed")
            result = False

        return result

    @fun_test.safe
    def ipmi_power_on(self, host, interface="lanplus", user="ADMIN", passwd="ADMIN", chassis=True):
        result = True
        chassis_string = "" if not chassis else " chassis"
        ipmi_cmd = "ipmitool -I {} -H {} -U {} -P {}{} power on".format(interface, host, user, passwd, chassis_string)
        expected_pat = r'Chassis Power Control: Up/On'
        ipmi_out = self.command(command=ipmi_cmd)
        if ipmi_out:
            match = re.search(expected_pat, ipmi_out, re.I)
            if not match:
                fun_test.critical("IPMI power on: Failed")
                result = False
            else:
                fun_test.log("IPMI power on: Passed")
        else:
            fun_test.critical("IPMI power on: Failed")
            result = False

        return result

    @fun_test.safe
    def ipmi_power_cycle(self, host, interface="lanplus", user="ADMIN", passwd="ADMIN", interval=10, chassis=True):
        """
        result = True
        chassis_string = "" if not chassis else " chassis"
        ipmi_cmd = "ipmitool -I {} -H {} -U {} -P {}{} power cycle".format(interface, host, user, passwd, chassis_string)
        self.command(ipmi_cmd)

        return result
        """

        
        result = True
        fun_test.log("Host: {}; Interface:{}; User: {}; Passwd: {}; Interval: {}".format(host, interface, user, passwd,
                                                                                         interval))
        off_status = self.ipmi_power_off(host=host, interface=interface, user=user, passwd=passwd, chassis=chassis)
        if off_status:
            fun_test.sleep("Sleeping for {} seconds for the host to go down".format(interval), interval)
            on_status = self.ipmi_power_on(host=host, interface=interface, user=user, passwd=passwd, chassis=chassis)
            if not on_status:
                result = False
        else:
            result = False

        return result

    @fun_test.safe
    def get_process_cmdline(self, process_name):

        process_cmdline = ""
        process_id = self.get_process_id(process_name)
        if process_id:
            # command = r"echo `cat /proc/{}/cmdline | tr '\0' '\n'`".format(process_id)
            command = r"ps -p {} -o args --no-headers".format(process_id)
            process_cmdline = self.command(command=command)

        return process_cmdline

    @fun_test.safe
    def create_filesystem(self, fs_type, device, sector_size=None, timeout=60):
        result = True

        if fs_type == "ext4":
            fs_command = "mkfs.ext4 -F {}".format(device)
        elif fs_type == "ext3":
            fs_command = "mkfs.ext3 -F {}".format(device)
        elif fs_type == "ext2":
            fs_command = "mkfs.ext2 -F {}".format(device)
        elif fs_type == "xfs":
            fs_command = "mkfs.xfs -f {}".format(device)
        elif fs_type == "ntfs":
            fs_command = "mkfs.ntfs -F {}".format(device)
        elif fs_type == "btrfs":
            fs_command = "mkfs.btrfs {}".format(device)
        elif fs_type == "f2fs":
            fs_command = "mkfs.f2fs {}".format(device)
        else:
            fun_test.critical("Creation of {} filesystem is not yet supported".format(fs_type))
            result = False
            return result

        if sector_size:
            fs_command += " -b {}".format(sector_size)

        try:
            output = self.sudo_command(fs_command, timeout=timeout)
            match = re.findall(r"done", output, re.M)
            if match:
                if fs_type == "ext2":
                    if len(match) != 3:
                        result = False
                elif fs_type == "ext3" or fs_type == "ext4":
                    if len(match) != 4:
                        # In case the size of the volume is too small, then the journal won't be created
                        # In that case the total done will be only 3
                        sub_match = re.search(r'Filesystem too small for a journal', output, re.M|re.I)
                        if not sub_match or len(match) != 3:
                            result = False
            else:
                if fs_type == "xfs":
                    match = re.search(r"bsize=(\d+)\s+blocks=(\d+)", output, re.MULTILINE)
                    if match:
                        result = match.group(2)
                    else:
                        result = False
                elif fs_type == "ntfs":
                    match = re.search(r"mkntfs\scompleted\ssuccessfully", output, re.MULTILINE)
                    if match:
                        result = match.group(0)
                    else:
                        result = False
                elif fs_type == "btrfs":
                    match = re.search(r"Number\sof\sdevices:", output, re.MULTILINE)
                    if match:
                        result = match.group(0)
                    else:
                        result = False
                elif fs_type == "f2fs":
                    match = re.search(r"Info:\sformat\ssuccessful", output, re.MULTILINE)
                    if match:
                        result = match.group(0)
                    else:
                        result = False
                else:
                    result = False
        except Exception as ex:
            result = False
            critical_str = str(ex)
            fun_test.critical(critical_str)
            self.logger.critical(critical_str)

        return result

    @fun_test.safe
    def create_directory(self, dir_name, sudo=True):
        result = True
        # Check if the directory already exists. If so return True
        dir_status = self.check_file_directory_exists(path=dir_name)
        if dir_status:
            return result

        mkdir_cmd = "mkdir -p {}".format(dir_name)
        if sudo:
            self.sudo_command(mkdir_cmd)
        else:
            self.command(mkdir_cmd)

        dir_status = self.check_file_directory_exists(path=dir_name)
        if not dir_status:
            result = False

        return result

    @fun_test.safe
    def mount_volume(self, volume, directory, readonly=False):
        result = True
        try:
            mnt_cmd = "mount {} {}".format(volume, directory)
            if readonly:
                mnt_cmd += " --read-only"
            mnt_out = self.sudo_command(mnt_cmd)
            if not mnt_out:
                pattern = r'.*{}.*'.format(directory)
                mnt_out = self.command("mount")
                match = re.search(pattern, mnt_out, re.M)
                if not match:
                    result = False
            else:
                result = False
        except Exception as ex:
            result = False
            critical_str = str(ex)
            fun_test.critical(critical_str)
            self.logger.critical(critical_str)
        return result

    @fun_test.safe
    def unmount_volume(self, volume=None, directory=None):
        result = True
        if volume:
            mnt_cmd = "umount -f {}".format(volume)
        elif directory:
            mnt_cmd = "umount -f {}".format(directory)
        try:
            mnt_out = self.sudo_command(mnt_cmd)
            if not mnt_out:
                pattern = r'.*{}.*'.format(volume)
                if directory:
                    pattern = r'.*{}.*'.format(directory)
                mnt_out = self.command("mount")
                match = re.search(pattern, mnt_out, re.M)
                if match:
                    result = False
            else:
                result = False
        except Exception as ex:
            result = False
            critical_str = str(ex)
            fun_test.critical(critical_str)
            self.logger.critical(critical_str)
        return result

    @fun_test.safe
    def check_package(self, pkg):
        result = True
        dpkg_cmd = "dpkg -s {}".format(pkg)
        output = self.sudo_command(dpkg_cmd)
        match = re.search(r'Status: install ok installed', output, re.M|re.I)
        if not match:
            result = False
        return result

    @fun_test.safe
    def install_package(self, pkg):
        result = True

        # At first check whether the requested package is already installed or not
        status = self.check_package(pkg)
        # If the package installed, then return True, else proceed to install the same
        if status:
            return result
        install_cmd = "apt-get -yq install {}".format(pkg)
        self.sudo_command(install_cmd)
        # Check whether the package is installed successfully
        status = self.check_package(pkg)
        if not status:
            result = False
        return result

    def clone(self):
        # Do a shallow copy
        c = copy.copy(self)
        try:
            c.handle = None
            c.buffer = None
            c.context = self.context
            c.logger = self.logger
            c.prompt_terminator = self.prompt_terminator
            c.saved_prompt_terminator = self.saved_prompt_terminator
        except:
            pass
        return c

    @fun_test.safe
    def set_mtu(self, interface, mtu, ns=None):
        # Configure
        cmd = "ifconfig {} mtu {}".format(interface, mtu)
        if ns:
            cmd = 'ip netns exec {} {}'.format(ns, cmd)
        self.sudo_command(cmd)

        # Check
        return self.get_mtu(interface, ns=ns) == mtu

    @fun_test.safe
    def get_mtu(self, interface, ns=None):
        cmd = 'ifconfig {}'.format(interface)
        if ns:
            cmd = 'ip netns exec {} {}'.format(ns, cmd)
            output = self.sudo_command(cmd)
        else:
            output = self.command(cmd)
        match = re.search(r'mtu (\d+)', output)
        if match:
            return int(match.group(1))

    @fun_test.safe
    def ifconfig_up_down(self, interface, action, ns=None):
        # Configure
        cmd = "ifconfig {} {}".format(interface, action)
        if ns:
            cmd = 'ip netns exec {} {}'.format(ns, cmd)
        self.sudo_command(cmd)

        # Check
        cmd = 'ifconfig {}'.format(interface)
        if ns:
            cmd = 'ip netns exec {} {}'.format(ns, cmd)
        output = self.sudo_command(cmd)
        match = re.search(r'{}.*UP'.format(interface), output)
        if action == 'up':
            return match is not None
        else:
            return match is None

    def is_mount_ro(self, mnt):
        """
        Method to validate if filesystem mounted is Read-only filesystem
        :param mnt: mount partition
        :return: boolean, if mount filesystem is Read-only filesystem, return True
        """
        result = True
        try:
            cmd = "grep '\sro[\s,]' /proc/mounts"
            output = self.sudo_command(cmd)
            lines = output.split("\n")
            for line in lines:
                if mnt in line:
                    result = True
                else:
                    result = False
        except Exception as ex:
            result = False
            critical_str = str(ex)
            fun_test.critical(critical_str)
            self.logger.critical(critical_str)

        return result

    @fun_test.safe
    def get_mgmt_interface(self):
        """Get mgmt interface name. Below is an example output.

        user@cadence-pc-3:~$ ip address show | grep 10.1.20.246 -A2 -B2
        2: enp10s0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
            link/ether 0c:c4:7a:84:eb:70 brd ff:ff:ff:ff:ff:ff
            inet 10.1.20.246/22 brd 10.1.23.255 scope global enp10s0
                valid_lft forever preferred_lft forever
            inet6 fe80::ec4:7aff:fe84:eb70/64 scope link
        """
        result = None
        if re.search(r'\d+\.\d+\.\d+\.\d+', self.host_ip):
            ip_addr = self.host_ip
        else:
            r = self.nslookup(self.host_ip)
            if r:
                ip_addr = r['ip_address']
        output = self.command('ip address show | grep {} -A2 -B2'.format(ip_addr))
        match = re.search(r'\d+: (\w+):.*?mtu.*?state.*?inet {}'.format(ip_addr), output, re.DOTALL)
        if match:
            result = match.group(1)

        return result

    @fun_test.safe
    def get_interface_to_route(self, ip, ns=None):
        """Get interface name, via which the ip route point to the destination IP. In below example, it returns 'fpg1'.

        root@cadence-pc-5:~# ip route show to match 19.1.1.1
        default via 10.1.20.1 dev eth0 onlink
        19.1.1.0/24 via 53.1.1.1 dev hu3-f0
        root@cadence-pc-5:~#
        """
        cmd = 'ip route show to match {}'.format(ip)
        if ns:
            cmd = 'ip netns exec {} {}'.format(ns, cmd)
            output = self.sudo_command(cmd)
        else:
            output = self.command(cmd)
        match = re.search(r'\d+\.\d+\.\d+\.\d+/\d+ via.*dev (\S+)', output)
        if match:
            return match.group(1)

    @fun_test.safe
    def get_namespaces(self):
        """Get all the namespaces.

        localadmin@hu-lab-01:~$ ip netns list
        n9 (id: 2)
        n8 (id: 1)
        n1 (id: 0)
        localadmin@hu-lab-01:~$
        """
        cmd = 'ip netns list'
        output = self.command(cmd)
        if output:
            return [i.split()[0] for i in output.strip().split('\n')]
        else:
            return []

    @fun_test.safe
    def health(self, only_reachability=False):
        return self.is_host_up(max_wait_time=60, with_error_details=True)

    @fun_test.safe
    def hostname(self):
        """Get hostname."""
        cmd = 'hostname'
        output = self.command(cmd)
        return output.split('.')[0]

    @fun_test.safe
    def pkill(self, process_name):
        """sudo pkill one or multiple processes which match the given name."""
        cmd = 'pkill {}'.format(process_name)
        return self.sudo_command(cmd)

    @fun_test.safe
    def vdbench(self, path="/usr/local/share/vdbench", filename=None, timeout=300):
        vdb_out = ""
        vdb_result = {}
        # Vdbench's column output format
        header_list = ["datetime", "interval", "iops", "throughput", "io_bytes", "read_pct", "resp_time", "read_resp",
                       "write_resp", "read_max", "write_max", "resp_stddev", "queue_depth", "cpu_sys_user", "cpu_sys"]

        # Building the vdbbench command
        if filename:
            vdb_cmd = "{}/vdbench -f {}".format(path, filename)
        else:
            vdb_cmd = "{}/vdbench -t".format(path)

        vdb_out = self.sudo_command(command=vdb_cmd, timeout=timeout)

        # Checking whether the vdbench command got succeeded or not
        if "Vdbench execution completed successfully" in vdb_out:
            fun_test.debug("Vdbench command got completed successfully...Proceeding to parse its output")
        else:
            fun_test.critical("Vdbench command didn't complete successfully...Aborting...")
            return vdb_result

        # Parsing the vdbench output
        # Searching for the line containing the final result using the below pattern
        vdb_out = vdb_out.split('\n')
        result_line = ""
        for line in vdb_out:
            match = re.search(r'.*avg_\d+\-\d+.*', line, re.M)
            if match:
                fun_test.debug("Found final result line: {}".format(match.group(0)))
                result_line = match.group(0)
                result_line = result_line.split()
                fun_test.debug("Parsed final result line: {}".format(result_line))

        if not result_line:
            fun_test.critical("Unable to find the final result line...Aborting...")
            return vdb_result

        for index, header in enumerate(header_list):
            vdb_result[header] = result_line[index]

        return vdb_result

    @fun_test.safe
    def get_number_cpus(self):
        """Get number of CPUs."""
        cmd = 'lscpu'
        output = self.command(cmd)
        match = re.search(r'CPU\(s\):\s+(\d+)', output)
        if match:
            return int(match.group(1))

    @fun_test.safe
    def free(self, memory=None):
        cmd = "free"
        if memory:
            cmd += " -{}".format(memory)
        output = self.command(cmd)
        values_list = re.findall(r'[0-9]+', output)
        values = {}
        if values_list:
            values_list_int = map(int, values_list)
            values = {
                "total": values_list_int[0],
                "used": values_list_int[1],
                "free": values_list_int[2],
                "shared": values_list_int[3],
                "cache": values_list_int[4],
                "available": values_list_int[5],
                "swap_total": values_list_int[6],
                "swap_used": values_list_int[7],
                "swap_free": values_list_int[8]
            }
        return values

    @fun_test.safe
    def lscpu(self, grep_filter=None):
        cmd = "lscpu"
        if grep_filter:
            cmd = cmd + " | grep '{}'".format(grep_filter)
        output = self.command(cmd)
        lines = output.split('\n')
        lscpu_dictionary = {}
        for line in lines:
            match_key_value = re.search(r'(.*):(.*)', line)
            if match_key_value:
                key = match_key_value.group(1)
                value = match_key_value.group(2).strip()
                lscpu_dictionary[key] = value
        return lscpu_dictionary

    def ls(self, file, sudo=False, timeout=10):
        file_info = {}
        header_list = ["permissions", "links", "owner", "group", "size", "month", "day", "time", "name"]

        # Currently the method is going to return the info of the first file from the ls -l output
        ls_cmd = "ls -l {} | head -1".format(file)
        if sudo:
            output = self.sudo_command(command=ls_cmd, timeout=timeout)
        else:
            output = self.command(command=ls_cmd, timeout=timeout)

        if output and "No such file or directory" not in output:
            output = output.split()
            for index, header in enumerate(header_list):
                file_info[header] = output[index]

        return file_info

    @fun_test.safe
    def flush_cache_mem(self, timeout=60):
        flush_cmd = """
        sync; echo 1 > /proc/sys/vm/drop_caches; 
        sync; echo 2 > /proc/sys/vm/drop_caches; 
        sync; echo 3 > /proc/sys/vm/drop_caches"""
        self.sudo_command(flush_cmd, timeout=timeout)

    def mpstat(self, cpu_list=None, numa_node=None, interval=5, count=2, background=True,
               output_file="/tmp/mpstat.out"):

        mpstat_output = None
        timeout = interval * (count + 1)

        cmd = "mpstat"
        if cpu_list:
            cmd += " -P {}".format(str(cpu_list))
        if numa_node:
            cmd += " -N {}".format(str(numa_node))

        cmd += " {} {}".format(str(interval), str(count))

        if background:
            fun_test.log("Starting command {} in background".format(cmd))
            mpstat_output = self.start_bg_process(cmd, output_file=output_file, timeout=timeout)
            if mpstat_output is None:
                fun_test.critical("mpstat process is not started")
            else:
                fun_test.log("mpstat process is started in background, pid is: {}".format(mpstat_output))
        else:
            mpstat_output = self.command(cmd, timeout=timeout)

        return mpstat_output

    def iostat(self, device=None, interval=5, count=2, background=True, extended_stats=False,
               output_file="/tmp/iostat.out", timeout=None):
        iostat_output = None
        if not timeout:
            timeout = interval * (count + 1)

        cmd = "iostat"
        if device:
            cmd += " -p {}".format(str(device))
        if extended_stats:
            cmd += " -x"

        cmd += " {} {}".format(str(interval), str(count))

        if background:
            fun_test.log("Starting iostat command {} in background".format(cmd))
            iostat_output = self.start_bg_process(cmd, output_file=output_file, timeout=timeout)
            if iostat_output is None:
                fun_test.critical("iostat process is not started")
            else:
                fun_test.log("iostat process is started in background, pid is: {}".format(iostat_output))
        else:
            iostat_output = self.command(cmd, timeout=timeout)

        return iostat_output

    def nvme_connect(self, target_ip, nvme_subsystem, port=1099, transport="tcp", nvme_io_queues=None, hostnqn=None,
                     retries=2, timeout=61):
        result = False
        nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {}".format(transport.lower(), target_ip, port,
                                                                         nvme_subsystem)
        if nvme_io_queues:
            nvme_connect_cmd += " -i {}".format(nvme_io_queues)
        if hostnqn:
            nvme_connect_cmd += " -q {}".format(hostnqn)

        for i in range(retries):
            try:
                nvme_connect_output = self.sudo_command(command=nvme_connect_cmd, timeout=timeout)
                nvme_connect_exit_status = self.exit_status()
                # fun_test.log("NVMe connect output: {}".format(nvme_connect_output))
                if not nvme_connect_exit_status:
                    result = True
                    break
            except Exception as ex:
                remaining = retries - i - 1
                if remaining:
                    fun_test.critical("NVMe connect attempt failed...Going to retry {} more time(s)...\n".
                                      format(remaining))
                    fun_test.critical(str(ex))
                    fun_test.sleep("before retrying")
                else:
                    fun_test.critical("Maximum number of retires({}) failed...So bailing out...".format(retries))

        return result

    def nvme_disconnect(self, nvme_subsystem=None, device=None):
        result = False
        cmd = "nvme disconnect"
        try:
            if nvme_subsystem:
                cmd += " -n {}".format(nvme_subsystem)
            if device:
                cmd += " -d {}".format(device)
            output = self.sudo_command(cmd)
            if output:
                if "disconnect" in output:
                    result = True
        except Exception as ex:
            fun_test.critical(ex)
        return result



    @fun_test.safe
    def curl(self, url, output_file=None, timeout=60):
        command = "curl {}".format(url)
        if output_file:
            command += " -o {}".format(output_file)
        output = self.command(command, timeout=timeout)
        result = int(self.exit_status()) == 0
        if not output_file:
            result = output
        return result

    @fun_test.safe
    def destroy(self):
        try:
            Linux.disconnect(self)
        except Exception as ex:
            pass
        try:
            if self.spawn_pid > 1:
                fun_test.log("Killing spawn id: {}".format(self.spawn_pid))
                os.kill(self.spawn_pid, 9)
        except Exception as ex:
            pass

    @fun_test.safe
    def docker(self, ps=True, kill_container_id=None, sudo=False, timeout=60):
        result = None
        command = None
        if ps:
            command = "docker ps --format '{{json .}}'"
        if kill_container_id:
            command = "docker kill {}".format(kill_container_id)
        if sudo:
            output = self.sudo_command(command, timeout=timeout)
        else:
            output = self.command(command, timeout=timeout)
        if output.strip():
            lines = output.split("\n")
            try:
                if lines:
                    result = [json.loads(str(line)) for line in lines]
            except Exception as ex:
                fun_test.critical(str(ex))

        return result


    @fun_test.safe
    def uptime(self, use_proc_uptime=True):
        result = None
        if use_proc_uptime:
            output = self.command("cat /proc/uptime")
            m = re.search(r'(\d+\.\d*)\s', output)
            if m:
                result = float(m.group(1))

        return result

    @fun_test.safe
    def file(self, path, mime_type=None):
        result = None
        command = "file"
        if mime_type:
            command += " --mime-type"
        command += " {}".format(path)
        output = self.command(command)
        if output:
            result = {}
            if mime_type:
                m = re.search(path + ":\s+(\S+)", output)
                if m:
                    result["mime_type"] = m.group(1)
        return result

    @fun_test.safe
    def ifconfig(self, interface="", action=None):

        result = []
        cmd = "ifconfig"
        if interface:
            cmd += " " + interface
            if action:
                cmd += " " + action

        ifconfig_output = self.command(cmd)
        if ifconfig_output:
            interfaces = ifconfig_output.split("\n\r")
            for interface in interfaces:
                one_data_set = {}
                match_interface = re.search(r'(?P<interface>\w+)', interface)
                match_ipv4 = re.search(r'[\s\S]*inet\s+(addr:)?(?P<ipv4>\d+.\d+.\d+.\d+)', interface)
                match_ipv6 = re.search(r'[\s\S]*inet6\s+(addr:)?\s?(?P<ipv6>\w+::\w+:\w+:\w+:\w+)', interface)
                match_ether = re.search(r'[\s\S]*ether\s+(?P<ether>\w+:\w+:\w+:\w+:\w+:\w+)', interface)
                match_hwaddr = re.search(r'[\s\S]*HWaddr\s+(?P<HWaddr>\w+:\w+:\w+:\w+:\w+:\w+)', interface)

                if match_interface and (match_ipv4 or match_ipv6) and (match_ether or match_hwaddr):
                    one_data_set["interface"] = match_interface.group("interface")
                    one_data_set["ipv4"] = match_ipv4.group("ipv4") if match_ipv4 else ""
                    one_data_set["ipv6"] = match_ipv6.group("ipv6") if match_ipv6 else ""
                    one_data_set["ether"] = match_ether.group("ether") if match_ether else ""
                    one_data_set["HWaddr"] = match_hwaddr.group("HWaddr") if match_hwaddr else ""
                    result.append(one_data_set)
        else:
            result = None
        return result

    @fun_test.safe
    def uname(self):
        result = {}
        cmd = "uname -snrmpio"
        uname_output = self.command(cmd)
        match_uname = re.search(r'(?P<kernel_name>\S+)\s+(?P<nodename>\S+)\s+(?P<kernel_release>\S+)\s+'
                                r'(?P<machine>\S+)\s+(?P<processor>\S+)\s+(?P<hardware_platform>\S+)\s+'
                                r'(?P<operating_system>\S+)', uname_output)
        if match_uname:
            result["kernel_name"] = match_uname.group("kernel_name")
            result["nodename"] = match_uname.group("nodename")
            result["kernel_release"] = match_uname.group("kernel_release")
            result["machine"] = match_uname.group("machine")
            result["processor"] = match_uname.group("processor")
            result["hardware_platform"] = match_uname.group("hardware_platform")
            result["operating_system"] = match_uname.group("operating_system")
        return result

    @fun_test.safe
    def ethtool(self, interface):
        result = {}
        cmd = "ethtool {}".format(interface)
        output = self.command(cmd)
        lines = output.split("\n")
        for line in lines:
            match_pattern = re.search(r'(?P<key>[-\w ]+):\s+(?P<value>[\w//]+)', line)
            if match_pattern:
                key = match_pattern.group("key").lower()
                key = key.replace(" ", "_")
                value = match_pattern.group("value")
                result[key] = value
        return result

    def ensure_host_is_down(self, max_wait_time=30):
        service_host_spec = fun_test.get_asset_manager().get_regression_service_host_spec()
        service_host = None
        if service_host_spec:
            service_host = Linux(**service_host_spec)
        else:
            fun_test.log("Regression service host could not be instantiated", context=self.context)

        max_down_timer = FunTimer(max_time=max_wait_time)
        result = False
        ping_result = True
        while ping_result and not max_down_timer.is_expired():
            if service_host and ping_result:
                ping_result = service_host.ping(dst=self.host_ip, count=5)
        if not ping_result:
            result = True
        service_host.disconnect()
        return result


class LinuxBackup:
    def __init__(self, linux_obj, source_file_name, backedup_file_name):
        self.linux_obj = linux_obj
        self.source_file_name = source_file_name
        self.backedup_file_name = backedup_file_name
        self.prompt_terminator = linux_obj.prompt_terminator

    def restore(self):
        linux_obj = Linux(host_ip=self.linux_obj.host_ip,
                          ssh_username=self.linux_obj.ssh_username,
                          ssh_password=self.linux_obj.ssh_password,
                          ssh_port=self.linux_obj.ssh_port)
        linux_obj.prompt_terminator = self.prompt_terminator
        linux_obj.cp(source_file_name=self.backedup_file_name, destination_file_name=self.source_file_name)



if __name__ == "__main__":
    l = Linux(host_ip="qa-ubuntu-02", ssh_username="auto_admin", ssh_password="fun123")
    print l.file(path="/tmp/s_signed", mime_type=True)