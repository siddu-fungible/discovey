from lib.system.fun_test import fun_test
from lib.system.utils import ToDictMixin
from lib.host.linux import Linux
import re, json

class F1(Linux, ToDictMixin):
    '''
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
    START_MODE_DPCSH_ONLY = "START_MODE_DPCSH_ONLY"   # Start with dpcsh only
    START_MODE_CUSTOM_APP = "START_MODE_CUSTOM_APP" # the user will start it from the script by specifying the app

    @staticmethod
    def get(asset_properties):
        prop = asset_properties
        f1 = F1(host_ip=prop["host_ip"],
                ssh_username=prop["mgmt_ssh_username"],
                ssh_password=prop["mgmt_ssh_password"],
                ssh_port=prop["mgmt_ssh_port"])
        return f1

    def post_init(self):
        self.fun_os_process_id = None
        self.external_dpcsh_port = None
        self.TO_DICT_VARS.extend(["fun_os_process_id", "external_dpcsh_port"])

    def start(self, start_mode,
              external_dpcsh_port=None,
              app="prem_test",
              args=""):
        if external_dpcsh_port:
            self.external_dpcsh_port = external_dpcsh_port
        started = False
        # Detect if it is in Simulation mode #TODO
        simulation_mode = True  # for now
        if simulation_mode:
            if start_mode == self.START_MODE_NORMAL:

                try:
                    process_id = self.get_process_id(process_name=self.FUN_OS_SIMULATION_PROCESS_NAME)
                    if process_id:
                        self.kill_process(process_id=process_id[0], signal=9)

                    self.command("cd {}".format(self.SIMULATION_FUNOS_BUILD_PATH))
                    self.command("ulimit -Sc unlimited")
                    self.command(r'export ASAN_OPTIONS="disable_coredump=0:unmap_shadow_on_exit=1:abort_on_error=true"')
                    self.command("./funos-posix app=mdt_test nvfile=nvfile")
                    self.interactive_command("./funos-posix app=prem_test sim_id=nvme_test nvfile=nvfile",
                                             expected_prompt="Remote PCIe EP NVME Test")
                except:
                    pass  #TODO
            elif start_mode == self.START_MODE_DPCSH_ONLY:
                try:
                    process_id = self.get_process_id(process_name=self.FUN_OS_SIMULATION_PROCESS_NAME)
                    if process_id:
                        self.kill_process(process_id=process_id, signal=9)

                    self.command("cd {}".format(self.SIMULATION_FUNOS_BUILD_PATH))
                    self.command("dd if=/dev/zero of=nvfile bs=4096 count=256")
                    self.command("ulimit -Sc unlimited")
                    self.command(r'export ASAN_OPTIONS="disable_coredump=0:unmap_shadow_on_exit=1:abort_on_error=true"')
                    self.command("{}/{} app=mdt_test nvfile=nvfile &> {}".format(self.SIMULATION_FUNOS_BUILD_PATH,
                                                                                 self.FUN_OS_SIMULATION_PROCESS_NAME,
                                                                                 self.F1_LOG))
                    '''
                    if not dpcsh_only:

                    '''

                    if True:
                        new_process_id = self.start_bg_process(
                            command="{}/{} --dpc-server app=load_mods".format(self.SIMULATION_FUNOS_BUILD_PATH,
                                                                self.FUN_OS_SIMULATION_PROCESS_NAME),
                            output_file=self.F1_LOG)
                        fun_test.sleep("Ensure FunOS is started", seconds=10)
                        dpcsh_tcp_proxy_process_id = self.start_bg_process("{}/{} --tcp_proxy {}".format(self.DPCSH_PATH,
                                                                            self.DPCSH_PROCESS_NAME,
                                                                            self.INTERNAL_DPCSH_PORT),
                                                                            output_file=self.DPCSH_PROXY_LOG)
                        fun_test.test_assert(dpcsh_tcp_proxy_process_id, "Start dpcsh tcp proxy")

                        fun_test.test_assert(new_process_id, "Started FunOs")
                        self.fun_os_process_id = new_process_id
                except:
                    pass  #TODO
            elif start_mode == self.START_MODE_CUSTOM_APP:
                # new_process_id = self.start_bg_process(command="{}/{} app=prem_test sim_id=nvme_test nvfile=nvfile --dpc-server".format(self.SIMULATION_FUNOS_BUILD_PATH,
                #                                                                           self.FUN_OS_SIMULATION_PROCESS_NAME))

                new_process_id = self.start_bg_process(
                    command="{}/{} app={} {} nvfile=nvfile".format(
                        self.SIMULATION_FUNOS_BUILD_PATH,
                        self.FUN_OS_SIMULATION_PROCESS_NAME,
                        app, args),
                    output_file=self.F1_LOG)
                fun_test.sleep("Ensure FunOS is started", seconds=10)
                fun_test.test_assert(new_process_id, "Started FunOs")
                self.fun_os_process_id = new_process_id

            started = True
        return started

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


class DockerF1(F1, ToDictMixin):
    SIMULATION_FUNOS_BUILD_PATH = "/"
    DPCSH_PATH = "/"
    data_plane_ip = None

    def set_data_plane_ip(self, data_plane_ip):
        self.data_plane_ip = data_plane_ip
        self.TO_DICT_VARS.append("data_plane_ip")

    def __getstate__(self):
        d = dict(self.__dict__)
        del d['handle']
        del d['logger']
        return d