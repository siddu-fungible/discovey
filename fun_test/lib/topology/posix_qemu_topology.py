from lib.system.fun_test import fun_test
from lib.fun.f1 import F1
from lib.orchestration.simulation_orchestrator import SimulationOrchestrator
from asset.asset_manager import AssetManager

class PosixQemuTopology:

    @fun_test.log_parameters
    def __init__(self,
                 num_vm_instances,
                 dpcsh_only=False):
        self.num_vm_instances = num_vm_instances
        self.instances = []
        self.orchestrators = []
        self.duts = []
        self.dpcsh_only = dpcsh_only
        self.mode = fun_test.MODE_SIMULATION

    def __repr__(self):
        return str(self.__class__)

    @fun_test.log_parameters
    def deploy(self):
        result = None
        try:
            asset_manager = AssetManager()
            simulation_orchestrator = SimulationOrchestrator.get(asset_manager.get_orchestrator(type=asset_manager.ORCHESTRATOR_TYPE_SIMULATION))
            self.orchestrators.append(simulation_orchestrator)

            f1_obj = F1.get(asset_manager.get_asset(name="ubuntu1"))

            self.duts.append(f1_obj)

            # Start FunOS
            fun_test.test_assert(f1_obj.start(dpcsh=True, dpcsh_only=self.dpcsh_only), "PosixQemuTopology: Start FunOS")

            # Request host to Launch QEMU instances
            for index in range(0, self.num_vm_instances):
                self.instances.append(simulation_orchestrator.launch_host_instance(name="VM_{}".format(index)))

            # self.instances.append(self.f1_obj)
            fun_test.test_assert(True, "Instances deployed")
            result = self
        except Exception as ex:
            fun_test.critical(str(ex))
        return result

    @fun_test.log_parameters
    def get_vms(self):
        return self.instances

    @fun_test.log_parameters
    def get_duts(self):
        return self.duts

    @fun_test.log_parameters
    def get_orchestrators(self):
        return self.orchestrators