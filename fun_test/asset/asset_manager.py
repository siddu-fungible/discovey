from fun_settings import *
from lib.host.docker_host import DockerHost
from lib.fun.f1 import F1
from lib.orchestration.simulation_orchestrator import SimulationOrchestrator, DockerContainerOrchestrator
from lib.system.fun_test import fun_test
from lib.orchestration.orchestrator import OrchestratorType

SPEC_FILE = ASSET_DIR + "/" + "docker_hosts.json"


class AssetManager:
    ASSET_SPEC = ASSET_DIR + "/assets.json"
    ORCHESTRATOR_SPEC = ASSET_DIR + "/orchestrators.json"


    def __init__(self):
        self.docker_host = None  #TODO
        self.orchestrators = []

    def describe(self):
        fun_test.log_section("Printing assets")
        # for orchestrator in self.orchestrators:
        #    orchestrator.describe()
        self.docker_host.describe()

    @fun_test.log_parameters
    def get_asset(self, name):
        asset = None
        try:
            all_assets = fun_test.parse_file_to_json(file_name=self.ASSET_SPEC)
            fun_test.test_assert(all_assets, "Retrieve at least one asset")
            if name in all_assets:
                asset = all_assets[name]
                fun_test.debug("Found asset {}".format(name))
        except Exception as ex:
            fun_test.critical(str(ex))
        return asset


    @fun_test.safe
    def get_any_docker_host(self):
        docker_hosts = fun_test.parse_file_to_json(SPEC_FILE)
        fun_test.simple_assert(docker_hosts, "At least one docker host")
        asset = DockerHost.get(docker_hosts[0])
        return asset

    @fun_test.safe
    def get_orchestrator(self, type=OrchestratorType.ORCHESTRATOR_TYPE_DOCKER_CONTAINER, index=0):
        fun_test.debug("Getting orchestrator")
        orchestrator = None
        try:
            all_assets = fun_test.parse_file_to_json(file_name=self.ORCHESTRATOR_SPEC)
            fun_test.simple_assert(all_assets, "Retrieve at least one orchestrator")
            for one_asset in all_assets:
                if one_asset['type'] == type:
                    fun_test.debug("Found asset {}".format(one_asset['name']))
                    if type == OrchestratorType.ORCHESTRATOR_TYPE_SIMULATION:
                        orchestrator = SimulationOrchestrator.get(one_asset)
                    elif type == OrchestratorType.ORCHESTRATOR_TYPE_DOCKER_CONTAINER:
                        # Ensure a docker container is running
                        if not fun_test.build_url:
                            build_url = DEFAULT_BUILD_URL
                        else:
                            build_url = fun_test.build_url
                        if not self.docker_host:
                            self.docker_host = self.get_any_docker_host()
                        fun_test.simple_assert(self.docker_host.health()["result"], "Health of the docker host")
                        fun_test.simple_assert(self.docker_host, "Docker host available")
                        fun_test.log("Setting up the integration container for index: {} url: {}".format(index, build_url))
                        id = index + fun_test.get_suite_execution_id()
                        container_name = "{}_{}".format("integration_basic", id)

                        container_asset = self.docker_host.setup_storage_container(build_url=build_url,
                                                                                   container_name=container_name,
                                                                                   ssh_internal_ports=[22],
                                                                                   qemu_internal_ports=[50001, 50002,
                                                                                                        50003, 50004],
                                                                                   dpcsh_internal_ports=[
                                                                                       F1.INTERNAL_DPCSH_PORT])

                        fun_test.test_assert(container_asset, "Setup storage basic container: {}".format(id))
                        orchestrator = DockerContainerOrchestrator.get(container_asset)
                    else:
                        orchestrator = DockerHost.get(one_asset)
                    break
        except Exception as ex:
            fun_test.critical(str(ex))
        self.orchestrators.append(orchestrator)
        return orchestrator





asset_manager = AssetManager()