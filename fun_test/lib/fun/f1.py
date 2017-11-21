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
    FUN_OS_SIMULATION_PROCESS = "funos-posix"
    DPCSH_PROCESS = "dpcsh"

    INTERNAL_DPCSH_PORT = 5000

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

    def start(self, dpcsh=False, dpcsh_only=False, external_dpcsh_port=None):
        if external_dpcsh_port:
            self.external_dpcsh_port = external_dpcsh_port
        started = False
        # Detect if it is in Simulation mode #TODO
        simulation_mode = True  # for now
        if simulation_mode:
            if not dpcsh:

                try:
                    process_id = self.get_process_id(process_name=self.FUN_OS_SIMULATION_PROCESS)
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
            else:
                try:
                    process_id = self.get_process_id(process_name=self.FUN_OS_SIMULATION_PROCESS)
                    if process_id:
                        self.kill_process(process_id=process_id, signal=9)

                    self.command("cd {}".format(self.SIMULATION_FUNOS_BUILD_PATH))
                    self.command("dd if=/dev/zero of=nvfile bs=4096 count=256")
                    self.command("ulimit -Sc unlimited")
                    self.command(r'export ASAN_OPTIONS="disable_coredump=0:unmap_shadow_on_exit=1:abort_on_error=true"')
                    # self.command("./funos-posix app=mdt_test nvfile=nvfile &> /tmp/funos.log")
                    self.command("{}/{} app=mdt_test nvfile=nvfile &> /tmp/funos.log".format(self.SIMULATION_FUNOS_BUILD_PATH,
                                                                                    self.FUN_OS_SIMULATION_PROCESS))
                    if not dpcsh_only:
                        #new_process_id = self.start_bg_process(command="{}/{} app=prem_test sim_id=nvme_test nvfile=nvfile --dpc-server".format(self.SIMULATION_FUNOS_BUILD_PATH,
                        #                                                                           self.FUN_OS_SIMULATION_PROCESS))

                        new_process_id = self.start_bg_process(
                            command="{}/{} app=prem_test nvfile=nvfile".format(
                                self.SIMULATION_FUNOS_BUILD_PATH,
                                self.FUN_OS_SIMULATION_PROCESS),
                            output_file="/tmp/f1_no_dpcsh.log")
                        fun_test.sleep("Ensure FunOS is started", seconds=10)

                    else:
                        new_process_id = self.start_bg_process(
                            command="{}/{} --dpc-server app=load_mods".format(self.SIMULATION_FUNOS_BUILD_PATH,
                                                                self.FUN_OS_SIMULATION_PROCESS),
                        output_file="/tmp/f1_dpc_server.log")
                        fun_test.sleep("Ensure FunOS is started", seconds=10)
                        dpcsh_tcp_proxy_process_id = self.start_bg_process("{}/{} --tcp_proxy {}".format(self.DPCSH_PATH,
                                                                            self.DPCSH_PROCESS,
                                                                            self.INTERNAL_DPCSH_PORT),
                                                                           output_file="/tmp/dpcsh.bg.log")
                        fun_test.test_assert(dpcsh_tcp_proxy_process_id, "Start dpcsh tcp proxy")

                    fun_test.test_assert(new_process_id, "Started FunOs")
                    self.fun_os_process_id = new_process_id
                except:
                    pass  #TODO

            started = True
        return started

    def dpcsh_command(self, line):
        result = {}
        output = self.command("{}/{} --nocli {}".format(self.DPCSH_PATH, self.DPCSH_PROCESS, line))
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