from lib.system.fun_test import fun_test
from lib.system.utils import ToDictMixin
from lib.host.linux import Linux
import re
import json


class F1(Linux, ToDictMixin):
    '''START_MODE_DPCSH_ONLY
    F1 class encapsulating ways to start the funos-posix simulator
    '''
    SIMULATION_FUNOS_BUILD_PATH = "/home/jabraham/FunOS/build"
    DPCSH_PATH = "/home/jabraham/FunTools/dpcsh/dpcsh"
    FUN_OS_SIMULATION_PROCESS_NAME = "funos-posix"
    DPCSH_PROCESS_NAME = "dpcsh"

    INTERNAL_DPCSH_PORT = 5000

    # Default log path when run in the background
    F1_LOG = "/tmp/f1.log.txt"
    DPCSH_PROXY_LOG = "/tmp/dpcsh_proxy.log.txt"

    START_MODE_NORMAL = "START_MODE_NORMAL"  # How do we define NORMAL ? #TODO
    START_MODE_DPCSH_ONLY = "START_MODE_DPCSH_ONLY"  # Start with dpcsh only
    START_MODE_QEMU_PLUS_DPCSH = "START_MODE_QEMU_PLUS_DPCSH"  # Start with dpcsh server for the prem_test app also
    START_MODE_CUSTOM_APP = "START_MODE_CUSTOM_APP"  # the user will start it from the script by specifying the app

    CONNECT_RETRY_TIMEOUT_DEFAULT = 90

    def __init__(self,
                 host_ip,
                 ssh_username,
                 ssh_password,
                 ssh_port,
                 external_dpcsh_port,
                 boot_args=None):
        super(F1, self).__init__(host_ip=host_ip,
                                 ssh_username=ssh_username,
                                 ssh_password=ssh_password,
                                 ssh_port=ssh_port)
        self.external_dpcsh_port = external_dpcsh_port
        self.dpcsh_tcp_proxy_process_id = None
        self.fun_os_process_id = None
        self.last_start_parameters = {}
        self.connect_retry_timeout_max = self.CONNECT_RETRY_TIMEOUT_DEFAULT
        self.boot_args = boot_args

    @staticmethod
    def get(asset_properties):
        prop = asset_properties
        f1 = F1(host_ip=prop["host_ip"],
                ssh_username=prop["mgmt_ssh_username"],
                ssh_password=prop["mgmt_ssh_password"],
                ssh_port=prop["mgmt_ssh_port"],
                external_dpcsh_port=prop["external_dpcsh_port"])
        return f1

    def post_init(self):
        self.fun_os_process_id = None
        self.external_dpcsh_port = None
        self.TO_DICT_VARS.extend(["fun_os_process_id", "external_dpcsh_port"])

    def run_app(self, boot_args, foreground=False, timeout=20, run_to_completion=False):
        rich_inputs = fun_test.get_rich_inputs()
        if rich_inputs:
            if "boot_args" in rich_inputs:
                rich_input_boot_args = rich_inputs.get("boot_args", None)
                if rich_input_boot_args:
                    if "0" in rich_input_boot_args:
                        boot_args = rich_input_boot_args["0"]
        return self.start(start_mode=self.START_MODE_CUSTOM_APP,
                          boot_args=boot_args,
                          foreground=foreground,
                          timeout=timeout,
                          get_output=True,
                          run_to_completion=run_to_completion)

    def start(self, start_mode=None,
              boot_args=None,
              foreground=False,
              timeout=20,
              get_output=False,
              run_to_completion=False,
              mdt_rebuild=True):
        result = None
        self.last_start_parameters = {
            "boot_args": boot_args,
            "foreground": foreground,
            "timeout": timeout,
            "get_output": get_output,
            "run_to_completion": run_to_completion,
            "start_mode": start_mode
        }
        if boot_args:
            self.boot_args = boot_args
        # Detect if it is in Simulation mode #TODO
        simulation_mode = True  # for now
        if not start_mode:
            start_mode = self.START_MODE_NORMAL

        if simulation_mode:
            if start_mode == self.START_MODE_NORMAL:
                try:
                    process_id = self.get_process_id(process_name=self.FUN_OS_SIMULATION_PROCESS_NAME)
                    if process_id:
                        self.kill_process(process_id=process_id, signal=9)

                    self.command("cd {}".format(self.SIMULATION_FUNOS_BUILD_PATH))
                    self.command("ulimit -Sc unlimited")
                    self.command(r'export ASAN_OPTIONS="disable_coredump=0:unmap_shadow_on_exit=1:abort_on_error=true"')
                    self.command("./{} app=mdt_test nvfile=nvfile &> {}".format(self.FUN_OS_SIMULATION_PROCESS_NAME,
                                                                                self.F1_LOG))
                    # adding --wustack-stale to find the root cause for the bug SWOS-4219 and SWOS-4423
                    new_process_id = self.start_bg_process(
                        command="./{} --wustack-stale app=prem_test nvfile=nvfile".format(
                            self.FUN_OS_SIMULATION_PROCESS_NAME), output_file=self.F1_LOG)
                    fun_test.sleep("Ensure FunOS is started", seconds=10)
                    fun_test.test_assert(new_process_id, "Started FunOs")
                    result = True
                except Exception as ex:
                    fun_test.critical(str(ex))
            if start_mode == self.START_MODE_QEMU_PLUS_DPCSH:
                try:
                    self.command("ps -ef")
                    process_id = self.get_process_id(process_name=self.FUN_OS_SIMULATION_PROCESS_NAME)
                    if process_id:
                        self.kill_process(process_id=process_id, signal=9)

                    self.command("cd {}".format(self.SIMULATION_FUNOS_BUILD_PATH))
                    # Creating the metadata file needed for the funos-posix
                    # self.command("dd if=/dev/zero of=nvfile bs=4096 count=256")
                    self.command("ulimit -Sc unlimited")
                    self.command(r'export ASAN_OPTIONS="disable_coredump=0:unmap_shadow_on_exit=1:abort_on_error=true"')
                    # self.command("./funos-posix app=mdt_test nvfile=nvfile")
                    # self.interactive_command("./funos-posix app=prem_test sim_id=nvme_test nvfile=nvfile",
                    #                          expected_prompt="Remote PCIe EP NVME Test")

                    # Formatting the drive
                    mdt_command = "./{} app=mdt_test nvfile=nvfile &> {}".format(self.FUN_OS_SIMULATION_PROCESS_NAME,
                                                                                 self.F1_LOG)
                    self.command(command=mdt_command, timeout=32)

                    # Starting the funos-poix to run the prem_test app along with the dpc-server
                    # adding --wustack-stale to find the root cause for the bug SWOS-4219 and SWOS-4423
                    funos_command = "./{} --dpc-server --wustack-stale app=prem_test nvfile=nvfile".format(
                        self.FUN_OS_SIMULATION_PROCESS_NAME)
                    self.fun_os_process_id = self.start_bg_process(command=funos_command, output_file=self.F1_LOG)
                    fun_test.sleep("Ensure FunOS is started", seconds=10)
                    fun_test.test_assert(self.fun_os_process_id, "Started FunOs")

                    # Starting the dpcsh tcp proxy
                    dpcsh_tcp_proxy_cmd = "{}/{} --tcp_proxy={}".format(self.DPCSH_PATH, self.DPCSH_PROCESS_NAME,
                                                                        self.INTERNAL_DPCSH_PORT)
                    self.dpcsh_tcp_proxy_process_id = self.start_bg_process(command=dpcsh_tcp_proxy_cmd,
                                                                            output_file=self.DPCSH_PROXY_LOG)
                    fun_test.test_assert(self.dpcsh_tcp_proxy_process_id, "Start dpcsh tcp proxy")
                    result = True
                except Exception as ex:
                    fun_test.critical(str(ex))
            elif start_mode == self.START_MODE_DPCSH_ONLY:
                try:
                    process_id = self.get_process_id(process_name=self.FUN_OS_SIMULATION_PROCESS_NAME)
                    if process_id:
                        self.kill_process(process_id=process_id, signal=9)

                    self.command("cd {}".format(self.SIMULATION_FUNOS_BUILD_PATH))
                    if mdt_rebuild:
                        self.command("dd if=/dev/zero of=nvfile bs=4096 count=256")
                    self.command("ulimit -Sc unlimited")
                    self.command(r'export ASAN_OPTIONS="disable_coredump=0:unmap_shadow_on_exit=1:abort_on_error=true"')
                    if mdt_rebuild:
                        self.command("{}/{} app=mdt_test nvfile=nvfile &> {}".format(
                            self.SIMULATION_FUNOS_BUILD_PATH, self.FUN_OS_SIMULATION_PROCESS_NAME, self.F1_LOG))
                    '''
                    if not dpcsh_only:

                    '''

                    if True:
                        new_process_id = self.start_bg_process(
                            command="{}/{} --dpc-server --dpc-early-init app=load_mods".format(
                                self.SIMULATION_FUNOS_BUILD_PATH, self.FUN_OS_SIMULATION_PROCESS_NAME),
                            output_file=self.F1_LOG)
                        fun_test.sleep("Ensure FunOS is started", seconds=10)
                        self.dpcsh_tcp_proxy_process_id = self.start_bg_process("{}/{} --tcp_proxy={}".format(self.DPCSH_PATH,
                                                                            self.DPCSH_PROCESS_NAME,
                                                                            self.INTERNAL_DPCSH_PORT),
                                                                            output_file=self.DPCSH_PROXY_LOG)
                        fun_test.test_assert(self.dpcsh_tcp_proxy_process_id, "Start dpcsh tcp proxy")

                        fun_test.test_assert(new_process_id, "Started FunOs")
                        self.fun_os_process_id = new_process_id
                    result = True
                except:
                    pass  #TODO
            elif start_mode == self.START_MODE_CUSTOM_APP:
                # new_process_id = self.start_bg_process(command="{}/{} app=prem_test sim_id=nvme_test nvfile=nvfile --dpc-server".format(self.SIMULATION_FUNOS_BUILD_PATH,
                #                                                                           self.FUN_OS_SIMULATION_PROCESS_NAME))


                command = "{}/{} {}".format(
                        self.SIMULATION_FUNOS_BUILD_PATH,
                        self.FUN_OS_SIMULATION_PROCESS_NAME,
                        self.boot_args)
                if not foreground:
                    new_process_id = self.start_bg_process(command=command,
                                                           output_file=self.F1_LOG)
                    fun_test.sleep("Ensure FunOS is started", seconds=10)
                    fun_test.test_assert(new_process_id, "Started FunOs")
                    self.fun_os_process_id = new_process_id
                    result = True
                else:
                    result = self.command(command=command, timeout=timeout, run_to_completion=run_to_completion)
            # if not get_output:
            #    result = True
        return result

    def dpcsh_command(self, line):
        result = {}
        output = self.command("{}/{} --nocli {}".format(self.DPCSH_PATH, self.DPCSH_PROCESS_NAME, line))
        for line in output.splitlines():
            if "output =>" in line:
                try:
                    m = re.search(r'output => (.*})', line)
                    if m:
                        result = json.loads(m.group(1))
                    m = re.search(r'output => \d+', line)
                    if m:
                        result = json.loads(m.group(1))
                except:
                    result = line
                    break
        return result

    def disconnect(self):
        if self.fun_os_process_id:
            self.kill_process(process_id=self.fun_os_process_id, signal=9)
        super(F1, self).disconnect()

    def stop(self):
        fun_test.debug("Stopping dpcsh {}".format(self))
        self.kill_process(self.dpcsh_tcp_proxy_process_id, signal=9)
        fun_test.sleep("Kill dpcsh")
        fun_test.debug("Stopping F1: {}".format(self))
        self.kill_process(self.fun_os_process_id, signal=9)
        fun_test.sleep("Kill FunOs")
        self.cleanup()
        self.fun_os_process_id = None
        self.dpcsh_tcp_proxy_process_id = None

    @fun_test.safe
    def restart(self, mdt_rebuild=True):
        self.stop()
        if self.last_start_parameters:
            result = self.start(boot_args=self.boot_args,
                                timeout=self.last_start_parameters["timeout"],
                                get_output=self.last_start_parameters["get_output"],
                                foreground=self.last_start_parameters["foreground"],
                                run_to_completion=self.last_start_parameters["run_to_completion"],
                                mdt_rebuild=mdt_rebuild,
                                start_mode=self.last_start_parameters["start_mode"])
        else:
            result = self.start()
        return result


class DockerF1(F1, ToDictMixin):
    SIMULATION_FUNOS_BUILD_PATH = "/"
    DPCSH_PATH = "/"
    data_plane_ip = None

    def __init__(self, host_ip,
                 ssh_username,
                 ssh_password,
                 ssh_port,
                 external_dpcsh_port,
                 spec=None):
        super(DockerF1, self).__init__(host_ip=host_ip,
                                       ssh_username=ssh_username,
                                       ssh_port=ssh_port,
                                       ssh_password=ssh_password,
                                       external_dpcsh_port=external_dpcsh_port)

    def set_data_plane_ip(self, data_plane_ip):
        self.data_plane_ip = data_plane_ip
        self.TO_DICT_VARS.append("data_plane_ip")

