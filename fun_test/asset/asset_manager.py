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
from scheduler.scheduler_global import JobStatusType
from asset.asset_global import AssetType
from lib.topology.topology_helper import TopologyHelper, ExpandedTopology

PSEUDO_TEST_BEDS = ["emulation", "simulation", "tasks"]

class AssetManager:
    SIMPLE_HOSTS_ASSET_SPEC = ASSET_DIR + "/simple_hosts.json"
    DOCKER_HOSTS_ASSET_SPEC = ASSET_DIR + "/docker_hosts.json"
    DOCKER_HOSTS_DEVELOPMENT_ASSET_SPEC = ASSET_DIR + "/docker_hosts_development.json"
    TEST_BED_SPEC = ASSET_DIR + "/test_beds.json"
    FS_SPEC = ASSET_DIR + "/fs.json"
    HOSTS_SPEC = ASSET_DIR + "/hosts.json"

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
                    self.real_orchestrator = RealOrchestrator.get(id=dut_index)
                orchestrator = self.real_orchestrator
        except Exception as ex:
            fun_test.critical(str(ex))
        self.orchestrators.append(orchestrator)
        return orchestrator


    @fun_test.safe
    def get_fs_by_name(self, name):
        result = None
        fs_json = self.FS_SPEC
        json_spec = parse_file_to_json(file_name=fs_json)
        for fs in json_spec:
            if fs["name"] == name:
                result = fs
        return result

    @fun_test.safe
    def check_assets_in_use(self, test_bed_type, assets_required):
        from web.fun_test.models import Asset
        from django.core.exceptions import ObjectDoesNotExist
        from web.fun_test.models_helper import is_suite_in_progress
        used_by_suite_id = None
        in_use = False
        error_message = ""
        duts_required = assets_required.get(AssetType.DUT, None)
        asset_in_use = None
        print("Assets required for {}, : {}".format(test_bed_type, duts_required))
        if duts_required:
            for dut_required in duts_required:
                try:
                    this_asset = Asset.objects.get(type=AssetType.DUT, name=dut_required)
                    job_ids = this_asset.job_ids
                    print "Asset job-ids: {}, TB: {}".format(job_ids, test_bed_type)
                    if job_ids:
                        for job_id in job_ids:
                            print("Check if suite in progress: {}: {}: {}".format(test_bed_type, job_id, duts_required))
                            in_progress = is_suite_in_progress(job_id, test_bed_type)
                            if in_progress:
                                in_use, error_message = True, "{} used by Suite: {}".format(dut_required, job_id)
                                used_by_suite_id = job_id
                                asset_in_use = dut_required
                                break
                except ObjectDoesNotExist:
                    print "ObjectDoesnotExist, {}".format(test_bed_type)
                except Exception as ex:
                    print("Some other exception: {}".format(ex))
        if not in_use:
            # Check Hosts
            pass
        return in_use, error_message, used_by_suite_id, asset_in_use

    @fun_test.safe
    def get_test_bed_availability(self, test_bed_type):
        from web.fun_test.models_helper import get_suite_executions_by_filter, is_test_bed_with_manual_lock
        from scheduler.scheduler_global import JobStatusType
        result = {}
        result["test_bed"] = test_bed_type
        result["status"] = False
        result["message"] = None
        result["resources"] = None
        result["internal_resource_in_use"] = False  # set this if any DUT or Host within the test-bed is locked (shared asset)
        in_progress_suites = get_suite_executions_by_filter(test_bed_type=test_bed_type, state=JobStatusType.IN_PROGRESS).exclude(suite_path__endswith="_container.json")

        in_use, error_message, used_by_suite_id, asset_in_use = False, "", -1, None
        assets_required_for_test_bed = None
        if test_bed_type not in PSEUDO_TEST_BEDS:
            assets_required_for_test_bed = self.get_assets_required(test_bed_name=test_bed_type)
            if "fs-42" in test_bed_type:
                print ("TB: {}".format(test_bed_type))
            in_use, error_message, used_by_suite_id, asset_in_use = self.check_assets_in_use(test_bed_type=test_bed_type, assets_required=assets_required_for_test_bed)

        credits = 0
        if test_bed_type.lower().startswith("fs-"):
            credits = 1  # TODO: why are these hard-coded?
        elif test_bed_type.lower().startswith("simulation"):
            credits = 3
        elif test_bed_type.lower().startswith("emulation"):
            credits = 3
        elif test_bed_type.lower().startswith("task"):
            credits = 10
        else:
            credits = 1
        in_progress_count = in_progress_suites.count()

        manual_lock_info = is_test_bed_with_manual_lock(test_bed_name=test_bed_type)

        if manual_lock_info:
            result["status"] = False
            result["message"] = "Test-bed: {} manual locked by: {}".format(test_bed_type, manual_lock_info["manual_lock_submitter"])
        elif in_progress_count >= credits:
            result["status"] = False
            result["message"] = "Test-bed: {} In-progress count: {}, Credit: {}".format(test_bed_type, in_progress_count, credits)
            result["used_by_suite_id"] = in_progress_suites[0].execution_id
        elif in_use:  # Check if the required internal resources are used by another run
            result["status"] = False
            result["message"] = error_message
            result["internal_asset_in_use"] = True
            result["internal_asset_in_use_suite_id"] = used_by_suite_id
            result["internal_asset"] = asset_in_use
        else:
            result["status"] = True
            result["assets_required"] = assets_required_for_test_bed
        return result

    @fun_test.safe
    def get_test_bed_spec(self, name):
        all_test_bed_specs = parse_file_to_json(file_name=self.TEST_BED_SPEC)
        result = all_test_bed_specs[name] if name in all_test_bed_specs else None
        return result

    @fun_test.safe
    def get_host_spec(self, name):
        all_hosts_specs = parse_file_to_json(file_name=self.HOSTS_SPEC)
        result = all_hosts_specs.get(name, None)
        return result

    @fun_test.safe
    def get_regression_service_host_spec(self):
        host_spec = self.get_host_spec(name=REGRESSION_SERVICE_HOST)
        return host_spec

    @fun_test.safe
    def get_assets_required(self, test_bed_name):
        assets_required = {}
        test_bed_spec = self.get_test_bed_spec(name=test_bed_name)
        fun_test.simple_assert(test_bed_spec, "Test-bed spec for: {}".format(test_bed_name))

        th = TopologyHelper(spec=test_bed_spec)
        topology = th.get_expanded_topology()
        duts = topology.get_duts()
        dut_names = [duts[x].name for x in duts]
        assets_required[AssetType.DUT] = dut_names

        hosts = topology.get_hosts()
        host_names = [host_obj.name for name, host_obj in hosts.iteritems()]
        assets_required[AssetType.HOST] = host_names
        return assets_required

    @fun_test.safe
    def lock_assets(self, manual_lock_user, assets):
        from web.fun_test.models import Asset
        if assets:
            for asset_type, assets in assets.items():
                for asset in assets:
                    Asset.add_update(name=asset, type=asset_type)
                    Asset.add_job_id(name=asset, type=asset_type, manual_lock_user=manual_lock_user)

    def un_lock_assets(self, assets, user_email):
        assets = Asset.objects.filter(job_ids__contains=[job_id])
        for asset in assets:
            asset.job_ids = asset.remove_job_id(job_id=job_id)


asset_manager = AssetManager()

if __name__ == "__main__":
    spec = asset_manager.get_test_bed_spec(name="fs-inspur")
    from lib.topology.topology_helper import TopologyHelper
    th = TopologyHelper(spec=spec)
    topology = th.get_expanded_topology()
    duts = topology.get_duts()
    dut_names = [duts[x].name for x in duts]
    print dut_names

    hosts = topology.get_hosts()
    host_names = [host_obj.name for name, host_obj in hosts.iteritems()]
    print host_names