from lib.system.fun_test import fun_test
from lib.orchestration.orchestrator import Orchestrator
from lib.system.utils import ToDictMixin
from lib.fun.fs import Fs

class RealOrchestrator(Orchestrator, ToDictMixin):
    @staticmethod
    def get():
        s = RealOrchestrator()
        s.TO_DICT_VARS.append("ORCHESTRATOR_TYPE")
        return s

    def launch_dut_instance(self, spec):
        fs_obj = Fs.get()

        # Start Fs
        fun_test.test_assert(fs_obj.bootup(), "Fs bootup")
        return fs_obj
