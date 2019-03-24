
class OrchestratorType:
    """
    An orchestrator should be capable of launching DUT instances, host instances
    """
    ORCHESTRATOR_TYPE_SIMULATION = "ORCHESTRATOR_TYPE_SIMULATION" # Default Simulation Orchestrator. Probably will never be used
    ORCHESTRATOR_TYPE_DOCKER_CONTAINER = "ORCHESTRATOR_TYPE_DOCKER_CONTAINER" # Container that is capable of spinning an F1 and multiple Qemu instances, all within one container
    ORCHESTRATOR_TYPE_DOCKER_HOST = "ORCHESTRATOR_TYPE_DOCKER_HOST" # A Docker Linux Host capable of launching docker container instances
    ORCHESTRATOR_TYPE_REAL = "ORCHESTRATOR_TYPE_DOCKER_REAL" # Real Physical devices

class Orchestrator:
    OrchestratorType = OrchestratorType.ORCHESTRATOR_TYPE_DOCKER_CONTAINER