from fun_settings import *
from lib.system.fun_test import FunTestSystemException
from lib.system.utils import parse_file_to_json
from lib.host.docker_host import DockerHost
from lib.fun.f1 import F1
from lib.orchestration.simulation_orchestrator import SimulationOrchestrator, DockerContainerOrchestrator
from lib.orchestration.simulation_orchestrator import DockerHostOrchestrator
from lib.system.fun_test import fun_test
from lib.orchestration.orchestrator import OrchestratorType
from fun_global import *


class AssetManager:
    SIMPLE_HOSTS_ASSET_SPEC = ASSET_DIR + "/simple_hosts.json"
    DOCKER_HOSTS_ASSET_SPEC = ASSET_DIR + "/docker_hosts.json"
    DOCKER_HOSTS_DEVELOPMENT_ASSET_SPEC = ASSET_DIR + "/docker_hosts_development.json"


    def __init__(self):
        self.docker_host = None  #TODO
        self.orchestrators = []

    @fun_test.safe
    def cleanup(self):
        for orchestrator in self.orchestrators:
            if orchestrator.ORCHESTRATOR_TYPE == OrchestratorType.ORCHESTRATOR_TYPE_DOCKER_CONTAINER:
                # TODO: We need to map container to the container type
                # if it is an F1 container we should retrieve F1 logs,
                # if it is a Tg container we should retrieve tg logs

                artifact_file_name = fun_test.get_test_case_artifact_file_name(post_fix_name="f1.log.txt")
                container_asset = self.docker_host.get_container_asset(name=orchestrator.container_name)
                if container_asset:
                    fun_test.scp(source_ip=container_asset["host_ip"],
                                 source_file_path=F1.F1_LOG,
                                 source_username=container_asset["mgmt_ssh_username"],
                                 source_password=container_asset["mgmt_ssh_password"],
                                 source_port=container_asset["mgmt_ssh_port"],
                                 target_file_path=artifact_file_name)
                    fun_test.add_auxillary_file(description="F1 Log", filename=artifact_file_name)
                    if hasattr(orchestrator, "QEMU_LOG"):
                        artifact_file_name = fun_test.get_test_case_artifact_file_name(post_fix_name="qemu.log.txt")
                        fun_test.scp(source_ip=container_asset["host_ip"],
                                     source_file_path=orchestrator.QEMU_LOG,
                                     source_username=container_asset["mgmt_ssh_username"],
                                     source_password=container_asset["mgmt_ssh_password"],
                                     source_port=container_asset["mgmt_ssh_port"],
                                     target_file_path=artifact_file_name)
                        fun_test.add_auxillary_file(description="QEMU Log", filename=artifact_file_name)

                self.docker_host.stop_container(orchestrator.container_name)
                fun_test.sleep("Stopping container: {}".format(orchestrator.container_name))
                self.docker_host.remove_container(orchestrator.container_name)

            elif orchestrator.ORCHESTRATOR_TYPE == OrchestratorType.ORCHESTRATOR_TYPE_DOCKER_HOST:
                container_assets = orchestrator.container_assets
                for container_name in container_assets:
                    fun_test.log("Destroying container: {}".format(container_name))
                    self.docker_host.destroy_container(container_name=container_name)


    def describe(self):
        fun_test.log_section("Printing assets")
        # for orchestrator in self.orchestrators:
        #    orchestrator.describe()
        if self.docker_host:
            self.docker_host.describe()

    @fun_test.safe
    def get_any_simple_host(self, name):
        asset = None
        try:
            all_assets = parse_file_to_json(file_name=self.SIMPLE_HOSTS_ASSET_SPEC)
            fun_test.test_assert(all_assets, "Retrieve at least one asset")
            if name in all_assets:
                asset = all_assets[name]
                fun_test.debug("Found asset {}".format(name))
        except Exception as ex:
            fun_test.critical(str(ex))
        return asset


    @fun_test.safe
    def get_any_docker_host(self):
        docker_hosts_spec_file = self.DOCKER_HOSTS_ASSET_SPEC
        if (not is_regression_server()) and (not is_performance_server()):
            docker_hosts_spec_file = fun_test.get_environment_variable("DOCKER_HOSTS_SPEC_FILE")
            if not docker_hosts_spec_file:
                # This is probably for script development
                docker_hosts_spec_file = self.DOCKER_HOSTS_DEVELOPMENT_ASSET_SPEC
        if is_regression_server():
            docker_hosts_spec_file = self.DOCKER_HOSTS_DEVELOPMENT_ASSET_SPEC
                # raise FunTestSystemException("Please set the environment variable:\nDOCKER_HOSTS_SPEC_FILE=<my-docker.hosts.json>")
        local_setting_docker_host_spec_file = fun_test.get_local_setting(setting="DOCKER_HOSTS_SPEC_FILE")
        if local_setting_docker_host_spec_file:
            docker_hosts_spec_file = local_setting_docker_host_spec_file

        docker_hosts = parse_file_to_json(docker_hosts_spec_file)
        fun_test.simple_assert(docker_hosts, "At least one docker host")
        index = 0
        if (is_performance_server()):
            index = 1
        asset = DockerHost.get(docker_hosts[index])
        return asset

    @fun_test.safe
    def get_orchestrator(self, type=OrchestratorType.ORCHESTRATOR_TYPE_DOCKER_CONTAINER, index=0, dut_obj=None):
        fun_test.debug("Getting orchestrator")
        orchestrator = None
        try:
            if type == OrchestratorType.ORCHESTRATOR_TYPE_SIMULATION:
                orchestrator = SimulationOrchestrator.get(self.get_any_simple_host())
            elif type == OrchestratorType.ORCHESTRATOR_TYPE_DOCKER_CONTAINER:
                # Ensure a docker container is running
                if not self.docker_host:
                    self.docker_host = self.get_any_docker_host()
                fun_test.simple_assert(self.docker_host, "Docker host available")
                if not fun_test.get_environment_variable("DOCKER_URL"):
                    fun_test.simple_assert(self.docker_host.health()["result"], "Health of the docker host")
                fun_test.log("Setting up the integration container for index: {}".format(index))
                container_name = "{}_{}_{}".format("integration_basic", fun_test.get_suite_execution_id(), index)

                vm_host_os = None   # TODO: Hack needed until asset_manager is implemented
                if dut_obj.interfaces:
                    peer_info = dut_obj.interfaces[0].peer_info
                    if hasattr(peer_info, "vm_host_os"):
                        vm_host_os = peer_info.vm_host_os

                container_asset = self.docker_host.setup_storage_container(container_name=container_name,
                                                                           ssh_internal_ports=[22],
                                                                           qemu_internal_ports=[50001, 50002,
                                                                                                50003, 50004],
                                                                           dpcsh_internal_ports=[
                                                                               F1.INTERNAL_DPCSH_PORT],
                                                                           vm_host_os=vm_host_os)
                container_asset["host_type"] = self.docker_host.type # DESKTOP, BARE_METAL

                fun_test.test_assert(container_asset, "Setup storage basic container: {}".format(container_name))
                orchestrator = DockerContainerOrchestrator.get(container_asset)
            elif type == OrchestratorType.ORCHESTRATOR_TYPE_DOCKER_HOST:
                if not self.docker_host:
                    self.docker_host = self.get_any_docker_host()
                    fun_test.simple_assert(self.docker_host, "Docker host available")
                    fun_test.simple_assert(self.docker_host.health()["result"], "Health of the docker host")
                orchestrator = self.docker_host
                orchestrator.__class__ = DockerHostOrchestrator

        except Exception as ex:
            fun_test.critical(str(ex))
        self.orchestrators.append(orchestrator)
        return orchestrator





asset_manager = AssetManager()
