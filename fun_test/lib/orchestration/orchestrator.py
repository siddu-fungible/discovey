class OrchestratorType:
    """
    An orchestrator should be capable of launching DUT instances, host instances
    """
    ORCHESTRATOR_TYPE_SIMULATION = "SimulationOrchestrator" # Default Simulation Orchestrator
    ORCHESTRATOR_TYPE_DOCKER_CONTAINER = "DockerContainerOrchestrator" # Container that is capable of spinning an F1 and multiple Qemu instances, all within one container
    ORCHESTRATOR_TYPE_DOCKER_HOST = "DockerHostOrchestrator" # A Docker Linux Host capable of launching docker container instances