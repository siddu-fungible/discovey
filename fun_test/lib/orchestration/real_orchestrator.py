from lib.system.fun_test import fun_test
from lib.orchestration.orchestrator import Orchestrator
from lib.system.utils import ToDictMixin
from lib.fun.fs import Fs


class RealOrchestrator(Orchestrator, ToDictMixin):
    def __init__(self, id):
        super(RealOrchestrator, self).__init__(id=id)
        self.dut_instance = None

    @staticmethod
    def get(id):
        s = RealOrchestrator(id=id)
        s.TO_DICT_VARS.append("ORCHESTRATOR_TYPE")
        return s

    def launch_dut_instance(self, dut_index, dut_obj):
        fs_spec = None
        disable_f1_index = None
        boot_args = None
        if "dut" in dut_obj.spec:
            dut_name = dut_obj.spec["dut"]
            fs_spec = fun_test.get_asset_manager().get_fs_by_name(dut_name)
            if "disable_f1_index" in dut_obj.spec:
                disable_f1_index = dut_obj.spec["disable_f1_index"]
            boot_args = dut_obj.spec.get("custom_boot_args", None)
        fs_obj = Fs.get(fs_spec=fs_spec, disable_f1_index=disable_f1_index, boot_args=boot_args)

        # Start Fs
        fun_test.test_assert(fs_obj.bootup(non_blocking=True), "Fs bootup")

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

    def cleanup(self):
        dut_instance = self.get_dut_instance()
        if dut_instance:
            self.dut_instance.cleanup()
        return True