from lib.system.fun_test import fun_test
from lib.host.linux import Linux
import re, json

class F1(Linux):
    SIMULATION_FUNOS_BUILD_PATH = "/home/jabraham/FunOS/build"
    DPCSH_PATH = "/home/jabraham/FunTools/dpcsh/dpcsh"
    FUN_OS_SIMULATION_PROCESS = "funos-posix"
    DPCSH_PROCESS = "dpcsh"

    @staticmethod
    def get(asset_properties):
        prop = asset_properties
        return F1(host_ip=prop["host_ip"],
                     ssh_username=prop["mgmt_ssh_username"],
                     ssh_password=prop["mgmt_ssh_password"],
                     ssh_port=prop["mgmt_ssh_port"])

    def post_init(self):
        self.fun_os_process_id = None

    def start(self, dpcsh=False, dpcsh_only=False):
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
                    pass
            else:
                try:
                    process_id = self.get_process_id(process_name=self.FUN_OS_SIMULATION_PROCESS)
                    if process_id:
                        self.kill_process(process_id=process_id, signal=9)

                    self.command("cd {}".format(self.SIMULATION_FUNOS_BUILD_PATH))
                    self.command("dd if=/dev/zero of=nvfile bs=4096 count=256")
                    self.command("ulimit -Sc unlimited")
                    self.command(r'export ASAN_OPTIONS="disable_coredump=0:unmap_shadow_on_exit=1:abort_on_error=true"')
                    self.command("./funos-posix app=mdt_test nvfile=nvfile")
                    if not dpcsh_only:
                        #new_process_id = self.start_bg_process(command="{}/{} app=prem_test sim_id=nvme_test nvfile=nvfile --dpc-server".format(self.SIMULATION_FUNOS_BUILD_PATH,
                        #                                                                           self.FUN_OS_SIMULATION_PROCESS))

                        new_process_id = self.start_bg_process(
                            command="{}/{} app=prem_test nvfile=nvfile".format(
                                self.SIMULATION_FUNOS_BUILD_PATH,
                                self.FUN_OS_SIMULATION_PROCESS))
                    else:
                        new_process_id = self.start_bg_process(
                            command="{}/{} --dpc-server".format(self.SIMULATION_FUNOS_BUILD_PATH,
                                                                self.FUN_OS_SIMULATION_PROCESS))

                    fun_test.test_assert(new_process_id, "Started FunOs")
                    self.fun_os_process_id = new_process_id
                except:
                    pass

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


class DockerF1(F1):
    SIMULATION_FUNOS_BUILD_PATH = "/"
    DPCSH_PATH = "/"