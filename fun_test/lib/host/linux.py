import pexpect, paramiko
from paramiko_expect import SSHClientInteraction
import re
import collections
import sys
import os
import time
from lib.system.fun_test import fun_test


class NoLogger:
    def __init__(self):
        self.trace_enabled = None
        self.trace_id = None
        
    def trace(self, enable, id):
        self.trace_enabled = enable
        self.trace_id = id

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
    def __init__(self):
        self.trace_enabled = None
        self.trace_id = None

    def trace(self, enable, id):
        self.trace_enabled = enable
        self.trace_id = id

    def write_now(self, message, stdout=True):
        fun_test.write(message=message)
        fun_test.flush(trace_id=self.trace_id, stdout=stdout)

    def write(self, message, stdout=True):
        fun_test.write(message=message)

    def flush(self):
        fun_test.flush(trace_id=self.trace_id)

    def log(self, message):
        fun_test.log(message=message, trace_id=self.trace_id)

    def critical(self, message):
        message = "\nCRITICAL: {}".format(message)
        fun_test.log(message=message, trace_id=self.trace_id)


class Linux(object):
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



    def __init__(self,
                 host_ip,
                 ssh_username="jabraham",
                 ssh_password="fun123",
                 ssh_port=SSH_PORT_DEFAULT,
                 telnet_username="root",
                 telnet_password="zebra",
                 telnet_port=TELNET_PORT_DEFAULT,
                 connect_retry_timeout_max=20,
                 use_paramiko=False):

        self.host_ip = host_ip
        self.ssh_username = ssh_username
        self.ssh_password = ssh_password
        self.ssh_port = ssh_port
        self.connect_retry_timeout_max = connect_retry_timeout_max
        self.handle = None

        self.use_paramiko = use_paramiko
        self.paramiko_handle = None
        self.logger = LinuxLogger()
        self.trace_enabled = None
        self.trace_id = None
        self.tmp_dir = None
        self.prompt_terminator = None
        self.buffer = None
        self.saved_prompt_terminator = None
        self._set_defaults()
        self.use_telnet = False
        self.telnet_port = telnet_port
        self.telnet_username = telnet_username
        self.telnet_password = telnet_password
        self.post_init()

    @staticmethod
    def get(asset_properties):
        """

        :rtype: object
        """
        prop = asset_properties
        return Linux(host_ip=prop["host_ip"],
                     ssh_username=prop["mgmt_ssh_username"],
                     ssh_password=prop["mgmt_ssh_password"],
                     ssh_port=prop["mgmt_ssh_port"])

    def enable_logs(self, enable=True):
        if enable:
            self.logger = LinuxLogger()
        else:
            self.logger = NoLogger()

    def post_init(self):
        pass

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

    def trace(self, enable, id):
        self.logger.trace(enable=enable, id=id)

    def ip_route_add(self, network, gateway, outbound_interface):
        # "ip route add 10.1.0.0/16  via 172.17.0.1 dev eth0"
        command = "ip route add {} via {} dev {}".format(network, gateway, outbound_interface)
        return self.sudo_command(command)

    def _debug_expect_buffer(self):
        fun_test.debug("Expect Buffer Before:%s" % self.handle.before)
        fun_test.debug("Expect Buffer After:%s" % self.handle.after)
        fun_test.debug("Expect Buffer:%s" % self.handle.buffer)

    @fun_test.log_parameters
    def _paramiko_connect(self):
        client = paramiko.SSHClient()

        # Set SSH key parameters to auto accept unknown hosts
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to the host
        client.connect(hostname=self.host_ip, username=self.ssh_username, password=self.ssh_password)

        self.paramiko_handle = SSHClientInteraction(client, timeout=10, display=True)

    @fun_test.log_parameters
    def _connect(self):

        if self.use_paramiko:
            return self._paramiko_connect()
        result = None
        connected = False

        try:


            expects = collections.OrderedDict()
            expects[0] = '[pP]assword'
            expects[1] = '\(yes/no\)?'
            expects[2] = self.prompt_terminator + r'$'

            attempt = 0
            loop_count_max = 10
            start_time = time.time()
            elapsed_time = 0
            while elapsed_time < self.connect_retry_timeout_max:
                if attempt:
                    fun_test.log("Attempting connect: %d" % (attempt))
                if not self.use_telnet:
                    fun_test.debug(
                        "Attempting SSH connect to %s username: %s password: %s" % (self.host_ip,
                                                                                    self.ssh_username,
                                                                                    self.ssh_password))
                    fun_test.debug("Prompt terminator:%s" % self.prompt_terminator)
                    ssh_command = 'ssh -o UserKnownHostsFile=/dev/null %s@%s -p %d' % (self.ssh_username,
                                                                                       self.host_ip,
                                                                                       int(self.ssh_port))
                    self.logger.log(ssh_command)
                    self.handle = pexpect.spawn(ssh_command,
                                                env={"TERM": "dumb"},
                                                maxread=4096)
                else:
                    fun_test.debug(
                        "Attempting Telnet connect to %s username: %s password: %s" % (self.host_ip,
                                                                                    self.ssh_username,
                                                                                    self.ssh_password))
                    fun_test.debug("Prompt terminator:%s" % self.prompt_terminator)
                    telnet_command = 'telnet -l {} {} {}'.format(self.telnet_username, self.host_ip, self.telnet_port)
                    self.logger.log(telnet_command)
                    self.handle = pexpect.spawn(telnet_command,
                                                env={"TERM": "dumb"},
                                                maxread=4096)

                self.handle.logfile_read = sys.stdout
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
            if not self._set_term_settings():
                raise Exception("Unable to set term settings")
            if not self._set_paths():
                raise Exception("Unable to set paths")
            result = True
        return result

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

    @fun_test.log_parameters
    def command(self, command, sync=False, timeout=60, sync_timeout=0.3, custom_prompts=None, wait_until=None,
                wait_until_timeout=60, include_last_line=False, include_first_line=False):
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
                    self.disconnect()
                    return self.command(command=command,
                                        sync=sync, timeout=timeout,
                                        custom_prompts=custom_prompts,
                                        wait_until=wait_until,
                                        wait_until_timeout=wait_until_timeout,
                                        include_last_line=include_last_line)
                except (pexpect.EOF, pexpect.TIMEOUT):
                    pass  # We are expecting an intentional timeout
            command_lines = command.split('\n')
            for c in command_lines:
                self.sendline(c)
                if wait_until and (len(command_lines) == 1):
                    try:
                        self.handle.expect(wait_until, timeout=wait_until_timeout)
                    except (pexpect.EOF):
                        self.disconnect()
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
                    all_prompts_list = custom_prompts.keys()
                    all_prompts_list.append(self.prompt_terminator)
                    i = self.handle.expect(all_prompts_list, timeout=timeout)
                    if i == (len(all_prompts_list) - 1):
                        break
                    else:
                        self.sendline(custom_prompts[custom_prompts.keys()[i]])
                try:
                    self.handle.expect(self.prompt_terminator + r'$', timeout=timeout)
                except pexpect.EOF:
                    self.disconnect()
                    return self.command(command=command,
                                        sync=sync, timeout=timeout,
                                        custom_prompts=custom_prompts,
                                        wait_until=wait_until,
                                        wait_until_timeout=wait_until_timeout,
                                        include_last_line=include_last_line)
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
            critical_str = str(ex)
            fun_test.critical(critical_str)
            self.logger.critical(critical_str)
            raise ex
        return buf

    @fun_test.log_parameters
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

    @fun_test.log_parameters
    def ping(self,
             dst,
             count=5,
             max_percentage_loss=50,
             timeout=30):
        result = False
        percentage_loss = 100
        try:
            command = 'ping %s -c %d' % (str(dst), count)
            output = self.command(command, timeout=timeout)
            m = re.search(r'(\d+)%\s+packet\s+loss', output)
            if m:
                percentage_loss = int(m.group(1))
        except Exception as ex:
            critical_str = str(ex)
            fun_test.critical(critical_str)
            self.logger.critical(critical_str)
        if percentage_loss < max_percentage_loss:
            result = True
        return result

    @fun_test.log_parameters
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

    @fun_test.log_parameters
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

    @fun_test.log_parameters
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

    @fun_test.log_parameters
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

    @fun_test.log_parameters
    def create_file(self, file_name, contents):
        self.command("touch %s" % file_name)
        lines = contents.split('\n')
        if len(lines):
            processed_line = lines[0].replace(r'"', r'\"')
            self.command("echo \"%s\" > %s" % (processed_line, file_name))

        if len(lines) > 1:
            for line in lines[1:]:
                processed_line = line.replace(r'"', r'\"')
                self.command("echo \"%s\" >> %s" % (processed_line, file_name))
        return file_name

    @fun_test.log_parameters
    def create_temp_file(self, file_name, contents):
        return self.create_file(file_name=self.get_temp_file_path(file_name=file_name),
                                contents=contents)

    def remove_file(self, file_name):
        self.command("rm -f %s" % file_name)
        return True

    def remove_directory_contents(self, directory):
        self.command("rm -rf %s/" % (directory.strip("/")))
        return True

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

    @fun_test.log_parameters
    def list_files(self, path):
        o = self.command("ls -ltr " + path)
        lines = o.split('\n')
        files = []
        for line in lines:
            if line.startswith("-"):
                reg = re.compile(r'(.*) (\S+)')
                m = reg.search(line)
                if m:
                    files.append((m.group(1), m.group(2)))
            if line.startswith("d"):
                reg = re.compile(r'(.*) (\S+)')
                m = reg.search(line)
                if m:
                    files.append((m.group(1), m.group(2)))
        return files

    @fun_test.log_parameters
    def start_bg_process(self,
                         command,
                         get_job_id=False,
                         output_file='/dev/null',
                         timeout=3):
        command = command.rstrip()
        if output_file != "":
            command += r' &>' + output_file + " "
        command += r'&'
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

    @fun_test.log_parameters
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

    @fun_test.log_parameters
    def kill_process(self,
                     process_id=None,
                     job_id=None,
                     signal=15,
                     override=False,
                     kill_seconds=5,
                     minimum_process_id=50):
        if not process_id and not job_id:
            fun_test.critical(message="Please provide a valid process-id or job-id")
            return
        if ((process_id < minimum_process_id) and not override) and (not job_id):
            fun_test.critical(
                message="This API won't kill processes with PID < %d. Use the override switch" % minimum_process_id)
            return
        job_str = ""
        if job_id:
            job_str = "%"
        command = "kill -%s %s%s" % (str(signal), str(job_str), str(process_id))
        try:
            self.sudo_command(command=command)
        except pexpect.ExceptionPexpect:
            pass
        fun_test.sleep("Waiting for kill to complete", seconds=kill_seconds)

    def tshark_capture_start(self):
        pass

    def tshark_capture_stop(self, process_id):
        return self.kill_process(process_id=process_id)

    def tcpdump_capture_start(self):
        pass

    def tcpdump_capture_stop(self, process_id):
        pass

    def tshark_parse(self, file_name, read_filter, fields=None, decode_as=None):
        pass

    @fun_test.log_parameters
    def enter_sudo(self):
        result = False
        if not self.handle:
            self._connect()
        self.saved_prompt_terminator = self.prompt_terminator
        self.set_prompt_terminator(prompt_terminator=r'# ')
        prompt = r'assword\s+for\s+%s: ' % self.ssh_username
        output = self.command("sudo bash", custom_prompts={prompt: self.ssh_password})
        if "command not found" in output:
            result = False
        return result

    @fun_test.log_parameters
    def set_prompt_terminator(self, prompt_terminator):
        self.prompt_terminator = prompt_terminator

    @fun_test.log_parameters
    def exit_sudo(self):
        if hasattr(self, 'saved_prompt_terminator'):
            self.set_prompt_terminator(prompt_terminator=self.saved_prompt_terminator)
        self.command("exit")

    @fun_test.log_parameters
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

    @fun_test.log_parameters
    def disconnect(self):
        if self.handle:
            self.handle.close()
        self.handle = None
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

    @fun_test.log_parameters
    def clean(self):
        self.send_control_c()
        try:
            self.handle.expect(self.UNEXPECTED_EXPECT, timeout="0.1")
        except pexpect.ExceptionPexpect:
            pass
        try:
            self.handle.expect(self.prompt_terminator, timeout="0.1")
        except pexpect.ExceptionPexpect:
            pass

    @fun_test.log_parameters
    def sendline(self, c):
        self.handle.sendline(c)

    @fun_test.log_parameters
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

    @fun_test.log_parameters
    def sudo_command(self, command, timeout=60):
        sudoed = self.enter_sudo()
        output = self.command(command, timeout=timeout)
        if sudoed:
            self.exit_sudo()
        return output

    @fun_test.log_parameters
    def copy(self, source_file_name, destination_file_name):
        command = "yes | cp %s %s" % (source_file_name, destination_file_name)
        return self.command(command)

    @fun_test.log_parameters
    def backup_file(self, source_file_name):
        destination_file_name = self.tmp_dir + "/" + os.path.basename(source_file_name) + ".backup"
        self.copy(source_file_name=source_file_name, destination_file_name=destination_file_name)
        backup_obj = LinuxBackup(linux_obj=self,
                                 source_file_name=source_file_name,
                                 backedup_file_name=destination_file_name)
        return backup_obj

    @fun_test.log_parameters
    def read_file(self, file_name, include_last_line=False):
        output = self.command("cat %s" % file_name, include_last_line=include_last_line)
        lines = output.split('\n')
        processed_output = output
        if len(lines) > 1:
            processed_output = '\n'.join(lines[1:])
        return processed_output

    @fun_test.log_parameters
    def tail(self, file_name, line_count=5):
        output = self.command("tail -%d %s" % (line_count, file_name))
        lines = output.split('\n')
        # processed_output = output
        '''
        if len(lines) > 1:
            processed_output = '\n'.join(lines[1:])
        '''
        return lines

    @fun_test.log_parameters
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

    @fun_test.log_parameters
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

    @fun_test.log_parameters
    def exit_status(self):
        output = self.command("echo $?")
        output = output.rstrip()
        exit_code = None
        try:
            exit_code = int(output[-1])
        except ValueError:
            pass
        return exit_code

    @fun_test.log_parameters
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

    @fun_test.log_parameters
    def scp(self, source_file_path, target_ip, target_file_path, target_username, target_password, timeout=60):
        transfer_complete = False
        scp_command = "scp %s %s@%s:%s" % (source_file_path, target_username, target_ip, target_file_path)

        handle = self.handle
        handle.sendline(scp_command)
        handle.logfile_read = fun_test

        expects = collections.OrderedDict()
        expects[0] = '[pP]assword:'
        expects[1] = self.prompt_terminator + r'$'
        expects[2] = '\(yes/no\)?'

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
                    except pexpect.exceptions.EOF:
                        transfer_complete = True
                        break
        except Exception as ex:
            critical_str = str(ex)
            fun_test.critical(critical_str)
            self.logger.critical(critical_str)

        return transfer_complete

    @fun_test.log_parameters
    def md5sum(self, file_name):
        result = None
        command = "md5sum " + file_name + " | cut -d ' ' -f 1"
        try:
            output = self.sudo_command(command)
            output_lines = output.split('\n')
            result = output_lines[1].strip()
        except Exception as ex:
            critical_str = str(ex)
            fun_test.critical(critical_str)
            self.logger.critical(critical_str)
        return result

    @fun_test.log_parameters
    def command_exists(self, command):
        self.command("which " + command)
        exit_status = self.get_exit_status()  #TODO
        return exit_status == 0

    @fun_test.log_parameters
    def initialize(self, reset=False):
        if reset:
            self.reset()
        self.iptables(flush=True)
        return True

    @fun_test.log_parameters
    def reset(self):
        self.sudo_command("rm -rf /tmp/*")

    @fun_test.log_parameters
    def nslookup(self, dns_name):
        result = {}
        try:
            self.logger.log("Fetching ip address")
            command = "nslookup  %s | grep -A2 Name | grep Address " % dns_name
            output = self.sudo_command(command=command)
            output_lines = output.split('\n')
            obj = re.match('(.*):(.*)', output_lines[1])
            result['ip_address'] = obj.group(2).strip()
        except Exception as ex:
            critical_str = str(ex)
            fun_test.critical(critical_str)
            self.logger.critical(critical_str)
        return result

    def __repr__(self):
        return "{}: {}".format(self.__class__.__name__, self.host_ip)

    @fun_test.log_parameters
    def insmod(self, module):
        self.sudo_command("insmod {}".format(module))

    @fun_test.log_parameters
    def nvme_setup(self):
        self.command("cd .") #TODO
        modules = ["nvme-core.ko", "nvme.ko"]
        for module in modules:
            self.insmod(module=module)
            fun_test.sleep("Insmod wait", seconds=2)
        return True

    @fun_test.log_parameters
    def nvme_create_namespace(self, size, capacity, device):
        command = "{} create-ns --nsze={} --ncap={} {}".format(self.NVME_PATH, size, capacity, device)
        return self.sudo_command(command)

    @fun_test.log_parameters
    def nvme_attach_namespace(self, namespace_id, controllers, device):
        command = "{} attach-ns --namespace-id={} --controllers={} {}".format(self.NVME_PATH,
                                                                             namespace_id,
                                                                             controllers,
                                                                             device)
        return self.sudo_command(command)

    @fun_test.log_parameters
    def nvme_restart(self):
        command = "rmmod nvme"
        self.sudo_command(command)
        self.insmod(module="nvme.ko")
        return True

    @fun_test.log_parameters
    def lsblk(self):
        result = collections.OrderedDict()
        output = self.command("lsblk")
        lines = output.split("\n")
        for line in lines:

            """NAME    MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
               sr0      11:0    1 1024M  0 rom  """
            m = re.search(r'(.*\S+)\s+(\S+)\s+(\d+)\s+(\S+)\s+(\d+)\s+(\S+)\s+(\S+)?', line)
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
        linux_obj.copy(source_file_name=self.backedup_file_name, destination_file_name=self.source_file_name)
