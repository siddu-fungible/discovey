from fun_settings import *
from lib.system.fun_test import fun_test
from lib.system.utils import parse_file_to_json
from lib.host.docker_host import DockerHost
from lib.fun.f1 import F1
from lib.orchestration.simulation_orchestrator import DockerContainerOrchestrator
from lib.orchestration.simulation_orchestrator import DockerHostOrchestrator
from lib.orchestration.real_orchestrator import RealOrchestrator
from lib.orchestration.orchestrator import OrchestratorType
from fun_global import *


class AssetManager:
    SIMPLE_HOSTS_ASSET_SPEC = ASSET_DIR + "/simple_hosts.json"
    DOCKER_HOSTS_ASSET_SPEC = ASSET_DIR + "/docker_hosts.json"
    DOCKER_HOSTS_DEVELOPMENT_ASSET_SPEC = ASSET_DIR + "/docker_hosts_development.json"

    def __init__(self):
        self.docker_host = None  # TODO
        self.orchestrators = []
        self.real_orchestrator = None
        self.docker_host_orchestrator = None

    @fun_test.safe
    def cleanup(self):
        for orchestrator_index, orchestrator in enumerate(self.orchestrators):
            orchestrator.cleanup()
            # TODO: We need to map container to the container type
            # if it is an F1 container we should retrieve F1 logs,
            # if it is a Tg container we should retrieve tg logs

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
    def get_any_docker_host(self, spec_only=False):
        docker_hosts_spec_file = self.DOCKER_HOSTS_ASSET_SPEC
        if is_lite_mode():
            docker_hosts_spec_file = fun_test.get_environment_variable("DOCKER_HOSTS_SPEC_FILE")
            if not docker_hosts_spec_file:
                # This is probably for script development, let try development spec
                docker_hosts_spec_file = self.DOCKER_HOSTS_DEVELOPMENT_ASSET_SPEC
        if is_development_mode():
            docker_hosts_spec_file = self.DOCKER_HOSTS_DEVELOPMENT_ASSET_SPEC
        local_setting_docker_host_spec_file = fun_test.get_local_setting(setting="DOCKER_HOSTS_SPEC_FILE")
        if local_setting_docker_host_spec_file:
            docker_hosts_spec_file = local_setting_docker_host_spec_file

        docker_hosts = parse_file_to_json(docker_hosts_spec_file)
        fun_test.simple_assert(docker_hosts, "At least one docker host")
        index = 0
        if (is_production_mode()):
            index = 1  #TODO: this should go away when we have asset management
        if spec_only:
            asset = docker_hosts[index]
        else:
            asset = DockerHost.get(docker_hosts[index])
        return asset

    @fun_test.safe
    def get_orchestrator(self, is_simulation, type=OrchestratorType.ORCHESTRATOR_TYPE_DOCKER_CONTAINER, dut_index=0):
        orchestrator = None
        if not is_simulation:
            type = OrchestratorType.ORCHESTRATOR_TYPE_REAL
        try:
            if type == OrchestratorType.ORCHESTRATOR_TYPE_DOCKER_CONTAINER:
                self.docker_host = self.get_any_docker_host()
                orchestrator = DockerContainerOrchestrator(docker_host=self.docker_host, id=dut_index)
            elif type == OrchestratorType.ORCHESTRATOR_TYPE_DOCKER_HOST:
                if not self.docker_host_orchestrator:
                    docker_host_spec = self.get_any_docker_host(spec_only=True)
                    self.docker_host_orchestrator = DockerHostOrchestrator(id=dut_index, spec=docker_host_spec)
                orchestrator = self.docker_host_orchestrator
            elif type == OrchestratorType.ORCHESTRATOR_TYPE_REAL:
                if not self.real_orchestrator:
                    self.real_orchestrator = RealOrchestrator.get()
                orchestrator = self.real_orchestrator
        except Exception as ex:
            fun_test.critical(str(ex))
        self.orchestrators.append(orchestrator)
        return orchestrator


    @fun_test.safe
    def get_fs_by_name(self, name):
        result = None
        fs_json = ASSET_DIR + "/fs.json"
        json_spec = parse_file_to_json(file_name=fs_json)
        for fs in json_spec:
            if fs["name"] == name:
                result = fs
        return result

asset_manager = AssetManager()
