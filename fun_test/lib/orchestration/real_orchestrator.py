from lib.system.fun_test import fun_test
from lib.orchestration.orchestrator import Orchestrator
from lib.system.utils import ToDictMixin
from lib.fun.fs import Fs


class RealOrchestrator(Orchestrator, ToDictMixin):
    def __init__(self):
        super(RealOrchestrator, self).__init__()
        self.dut_instance = None

    @staticmethod
    def get():
        s = RealOrchestrator()
        s.TO_DICT_VARS.append("ORCHESTRATOR_TYPE")
        return s

    def launch_dut_instance(self, spec):
        fs_obj = Fs.get()

        # Start Fs
        fun_test.test_assert(fs_obj.bootup(), "Fs bootup")

        # TODO: Just for backward compatibility with simulation scripts
        come = fs_obj.get_come()
        host_ip = come.host_ip
        dpc_port = come.get_dpc_port(0)
        fs_obj.host_ip = host_ip
        fs_obj.external_dpcsh_port = dpc_port
        self.dut_instance = fs_obj
        return fs_obj

    def launch_linux_instance(self, index):
        return True

    def get_dut_instance(self):
        return self.dut_instance