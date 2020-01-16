from fun_settings import *
from lib.system.fun_test import fun_test
from lib.system.utils import parse_file_to_json
from lib.host.docker_host import DockerHost
from lib.fun.f1 import F1
from lib.orchestration.simulation_orchestrator import DockerContainerOrchestrator
from lib.orchestration.simulation_orchestrator import DockerHostOrchestrator
from lib.orchestration.real_orchestrator import RealOrchestrator
from lib.orchestration.orchestrator import OrchestratorType
from lib.topology.dut import Dut
from fun_global import *
from scheduler.scheduler_global import JobStatusType
from asset.asset_global import AssetType, AssetHealthStates
import json





class AssetManager:
    SIMPLE_HOSTS_ASSET_SPEC = ASSET_DIR + "/simple_hosts.json"
    DOCKER_HOSTS_ASSET_SPEC = ASSET_DIR + "/docker_hosts.json"
    DOCKER_HOSTS_DEVELOPMENT_ASSET_SPEC = ASSET_DIR + "/docker_hosts_development.json"
    TEST_BED_SPEC = ASSET_DIR + "/test_beds.json"
    FS_SPEC = ASSET_DIR + "/fs.json"
    HOSTS_SPEC = ASSET_DIR + "/hosts.json"
    PSEUDO_TEST_BEDS = ["emulation", "simulation", "tasks", "suite-based"]


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
                # if not self.real_orchestrator:
                orchestrator = RealOrchestrator.get(id=dut_index)
        except Exception as ex:
            fun_test.critical(str(ex))
        self.orchestrators.append(orchestrator)
        return orchestrator


    @fun_test.safe
    def get_fs_spec(self, name):
        result = None
        fs_json = self.FS_SPEC
        json_spec = parse_file_to_json(file_name=fs_json)
        for fs in json_spec:
            if fs["name"] == name:
                result = fs
        return result

    @fun_test.safe
    def get_all_fs_spec(self):
        fs_json = self.FS_SPEC
        json_spec = parse_file_to_json(file_name=fs_json)
        result = []
        for fs_spec in json_spec:
            result.append(fs_spec)
        return result


    @fun_test.safe
    def check_test_bed_manual_locked(self, test_bed_name, all_test_bed_specs=None):
        assets_required = self.get_assets_required(test_bed_name=test_bed_name, all_test_bed_specs=all_test_bed_specs)
        return self.check_assets_are_manual_locked(assets_required=assets_required)


    @fun_test.safe
    def check_if_any_asset_is_disabled(self, assets_required):
        one_asset_disabled = False
        one_asset_unhealthy = False
        unhealthy_asset = ""
        disabled_asset = ""
        from django.core.exceptions import ObjectDoesNotExist
        from web.fun_test.models import Asset
        for asset_type, assets_for_type in assets_required.iteritems():
            if one_asset_disabled:
                break
            for asset_for_type in assets_for_type:
                try:
                    this_asset = Asset.objects.get(name=asset_for_type, type=asset_type)
                    if this_asset.disabled:
                        one_asset_disabled = True
                        disabled_asset = asset_for_type
                        break
                    if this_asset.health_check_enabled and this_asset.health_status != AssetHealthStates.HEALTHY:
                        one_asset_unhealthy = True
                        unhealthy_asset = this_asset.name
                except ObjectDoesNotExist:
                    pass
                    #print "ObjectDoesnotExist, {}".format(asset_for_type)
                except Exception as ex:
                    print("Some other exception: {}".format(ex))

        return one_asset_disabled, disabled_asset, one_asset_unhealthy, unhealthy_asset

    @fun_test.safe
    def check_assets_are_manual_locked(self, assets_required):
        from django.core.exceptions import ObjectDoesNotExist
        from web.fun_test.models import Asset

        asset_level_manual_locked, error_message, manual_lock_user = False, "", None

        for asset_type, assets_for_type in assets_required.iteritems():
            for asset_for_type in assets_for_type:
                try:
                    this_asset = Asset.objects.get(name=asset_for_type, type=asset_type)
                    if this_asset.manual_lock_user:
                        asset_level_manual_locked, error_message, manual_lock_user = True, "Asset: {} manual locked by: {}".format(asset_for_type, this_asset.manual_lock_user), this_asset.manual_lock_user
                except ObjectDoesNotExist:
                    pass
                    #print "ObjectDoesnotExist, {}".format(asset_for_type)
                except Exception as ex:
                    print("Some other exception: {}".format(ex))
        return asset_level_manual_locked, error_message, manual_lock_user, assets_required

    @fun_test.safe
    def check_assets_in_use(self, test_bed_type, assets_required):
        from web.fun_test.models import Asset
        from django.core.exceptions import ObjectDoesNotExist
        from web.fun_test.models_helper import is_suite_in_progress
        used_by_suite_id = None
        in_use = False
        error_message = ""
        asset_in_use = None
        # print("Assets required for {}, : {}".format(test_bed_type, assets_required))
        for asset_type, assets_for_type in assets_required.iteritems():
            for asset_for_type in assets_for_type:
                try:
                    this_asset = Asset.objects.get(name=asset_for_type, type=asset_type)
                    job_ids = this_asset.job_ids
                    # print "Asset job-ids: {}, TB: {}".format(job_ids, test_bed_type)
                    if job_ids:
                        marked_for_deletion = []
                        for job_id in job_ids:
                            # print("Check if suite in progress: {}: {}: {}".format(test_bed_type, job_id, duts_required))
                            in_progress = is_suite_in_progress(job_id, test_bed_type)
                            if in_progress:
                                in_use, error_message = True, "{} used by Suite: {}".format(asset_for_type, job_id)
                                used_by_suite_id = job_id
                                asset_in_use = asset_for_type
                                break
                            else:
                                marked_for_deletion.append(job_id)
                        job_ids = [x for x in job_ids if x not in marked_for_deletion]
                        this_asset.job_ids = job_ids
                        this_asset.save()
                except ObjectDoesNotExist:
                    pass # print "ObjectDoesnotExist, {}".format(test_bed_type)
                except Exception as ex:
                    print("Some other exception: {}".format(ex))
        if not in_use:
            # Check Hosts
            pass
        return in_use, error_message, used_by_suite_id, asset_in_use

    @fun_test.safe
    def get_test_bed_availability(self, test_bed_type, suite_base_test_bed_spec=None, all_test_bed_specs=None):
        from web.fun_test.models_helper import get_suite_executions_by_filter, is_test_bed_with_manual_lock
        from scheduler.scheduler_global import JobStatusType
        from web.fun_test.models import TestBed
        result = {}
        result["test_bed"] = test_bed_type
        result["status"] = False
        result["message"] = ""
        result["resources"] = None
        result["internal_resource_in_use"] = False  # set this if any DUT or Host within the test-bed is locked (shared asset)


        test_bed_name = test_bed_type
        if test_bed_type == "suite-based":
            if suite_base_test_bed_spec:
                test_bed_name = suite_base_test_bed_spec.get("base_test_bed", None)

        if test_bed_name != "suite-based":
            test_bed_objects = TestBed.objects.filter(name=test_bed_name)
            if test_bed_objects.exists():
                test_bed_object = test_bed_objects.first()
                if test_bed_object and test_bed_object.disabled:
                    result["status"] = False
                    result["message"] = "TB: {} is disabled".format(test_bed_name)
                    # return result

        test_bed_unhealthy = False
        if test_bed_name != "suite-based":
            test_bed_objects = TestBed.objects.filter(name=test_bed_name)
            if test_bed_objects.exists():
                test_bed_object = test_bed_objects.first()
                if test_bed_object.health_check_enabled and (test_bed_object.health_status != AssetHealthStates.HEALTHY):
                    test_bed_unhealthy = True
                    result["status"] = False
                    result["message"] = "TB: {} is not healthy".format(test_bed_name)
                    if test_bed_object.health_status == AssetHealthStates.DISABLED:
                        result["message"] = "TB: {} is disabled".format(test_bed_name)

                    # return result

        if test_bed_type == "fs-122":
            i = 0

        if suite_base_test_bed_spec:
            return self.check_custom_test_bed_availability(custom_spec=suite_base_test_bed_spec)

        in_progress_suites = get_suite_executions_by_filter(test_bed_type=test_bed_type, state__gte=JobStatusType.IN_PROGRESS).exclude(suite_path__endswith="_container.json")

        in_use, error_message, used_by_suite_id, asset_in_use = False, "", -1, None
        assets_required_for_test_bed = None
        if test_bed_type not in self.PSEUDO_TEST_BEDS:
            assets_required_for_test_bed = self.get_assets_required(test_bed_name=test_bed_type, all_test_bed_specs=all_test_bed_specs)
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
        asset_level_manual_locked, asset_level_error_message, manual_lock_user, assets_required = False, "", None, None

        # check if any asset is disabled
        one_asset_disabled, disabled_asset_name = False, ""
        one_asset_unhealthy, unhealthy_asset_name = False, ""
        if assets_required_for_test_bed:
            one_asset_disabled, disabled_asset_name, one_asset_unhealthy, unhealthy_asset_name = self.check_if_any_asset_is_disabled(assets_required=assets_required_for_test_bed)
            if one_asset_disabled:
                result["status"] = False
                result["message"] = result["message"] + ":" + "Asset: {} is disabled".format(disabled_asset_name)
            if one_asset_unhealthy:
                result["status"] = False
                result["message"] = result["message"] + ":" + "Asset: {} is unhealthy".format(unhealthy_asset_name)

        if assets_required_for_test_bed:
            asset_level_manual_locked, asset_level_error_message, manual_lock_user, assets_required = self.check_assets_are_manual_locked(assets_required=assets_required_for_test_bed)

        result["suite_info"] = None
        if in_progress_count > 0:  # TODO: Duplicate check below
            result["suite_info"] = {"suite_execution_id": in_progress_suites[0].execution_id}
        if manual_lock_info:
            result["status"] = False
            result["message"] = result["message"] + ":" + "Test-bed: {} manual locked by: {}".format(test_bed_type, manual_lock_info["manual_lock_submitter"])
            if in_use:  # Check if the required internal resources are used by another run
                result["internal_asset_in_use"] = True
                result["internal_asset_in_use_suite_id"] = used_by_suite_id
                result["internal_asset"] = asset_in_use
        elif asset_level_manual_locked:
            result["status"] = False
            result["message"] = result["message"] + ":" + asset_level_error_message
            if in_use:  # Check if the required internal resources are used by another run
                result["internal_asset_in_use"] = True
                result["internal_asset_in_use_suite_id"] = used_by_suite_id
                result["internal_asset"] = asset_in_use
        elif in_progress_count >= credits:
            result["status"] = False
            result["message"] = result["message"] + ":" + "Test-bed: {0} locked by Suite: <a href='/regression/suite_detail/{1}'>{1}</a>".format(test_bed_type, in_progress_suites[0].execution_id)
            result["used_by_suite_id"] = in_progress_suites[0].execution_id
        elif in_use:  # Check if the required internal resources are used by another run
            result["status"] = False
            result["message"] = result["message"] + ":" + error_message
            result["internal_asset_in_use"] = True
            result["internal_asset_in_use_suite_id"] = used_by_suite_id
            result["internal_asset"] = asset_in_use
        elif test_bed_unhealthy:
            result["status"] = False
        elif one_asset_disabled:
            result["status"] = False
        elif one_asset_unhealthy:
            result["status"] = False
        else:
            result["status"] = True
            result["assets_required"] = assets_required_for_test_bed
        result["message"] = result["message"].lstrip(":")
        return result

    @fun_test.safe
    def get_test_bed_spec(self, name, all_test_bed_specs=None):
        if not all_test_bed_specs:
            all_test_bed_specs = self.get_all_test_beds_specs()
        result = all_test_bed_specs[name] if name in all_test_bed_specs else None
        return result

    @fun_test.safe
    def get_all_test_beds_specs(self):
        all_test_bed_specs = parse_file_to_json(file_name=self.TEST_BED_SPEC)
        return all_test_bed_specs

    @fun_test.safe
    def get_host_spec(self, name):
        all_hosts_specs = parse_file_to_json(file_name=self.HOSTS_SPEC)
        result = all_hosts_specs.get(name, None)
        return result

    @fun_test.safe
    def get_linux_host(self, name):
        from lib.host.linux import Linux
        host_spec = self.get_host_spec(name=name)
        host = None
        if host_spec:
            host = Linux(**host_spec)
        return host

    @fun_test.safe
    def get_fs(self, name):
        from lib.fun.fs import Fs
        fs_spec = self.get_fs_spec(name=name)
        fs = None
        if fs_spec:
            fs = Fs.get(fs_spec=fs_spec)
        return fs

    @fun_test.safe
    def get_asset_instance(self, asset):
        instance = None
        if asset.type in [AssetType.HOST, AssetType.PCIE_HOST, AssetType.PERFORMANCE_LISTENER_HOST]:
            instance = self.get_linux_host(name=asset.name)
        elif asset.type in AssetType.DUT:
            instance = self.get_fs(name=asset.name)
        return instance

    @fun_test.safe
    def get_asset_instance_by_name(self, asset_type, asset_name):
        instance = None
        if asset_type in [AssetType.HOST, AssetType.PCIE_HOST, AssetType.PERFORMANCE_LISTENER_HOST]:
            instance = self.get_linux_host(name=asset_name)
        elif asset_type in AssetType.DUT:
            instance = self.get_fs(name=asset_name)
        return instance

    @fun_test.safe
    def get_asset_db_entry(self, asset_type, asset_name):
        from web.fun_test.models import Asset
        from django.core.exceptions import ObjectDoesNotExist
        result = None
        try:
            asset_object = Asset(name=asset_name, type=asset_type)
            result = asset_object
        except ObjectDoesNotExist:
            pass
        return result


    @fun_test.safe
    def get_regression_service_host_spec(self):
        host_spec = self.get_host_spec(name=REGRESSION_SERVICE_HOST)
        return host_spec

    @fun_test.safe
    def manual_lock_assets(self, user, assets, expiration_time=None):
        from web.fun_test.models import Asset
        for asset_type, assets_for_type in assets.items():
            for asset in assets_for_type:
                try:
                    Asset.add_update(name=asset, type=asset_type)
                    a = Asset.objects.get(name=asset, type=asset_type)
                    a.manual_lock_user = user
                    if expiration_time is not None:
                        a.manual_lock_expiry_time = expiration_time
                    a.save()
                except Exception as ex:   #TODO
                    print(str(ex))

    @fun_test.safe
    def manual_un_lock_assets_by_test_bed(self, test_bed_name, user):
        test_bed_spec = self.get_test_bed_spec(name=test_bed_name)
        if test_bed_name not in self.PSEUDO_TEST_BEDS:
            fun_test.simple_assert(test_bed_spec, "Test-bed spec for: {}".format(test_bed_name))
        assets_required = self.get_assets_required(test_bed_name=test_bed_name)
        return self.manual_un_lock_assets(user=user, assets=assets_required)

    @fun_test.safe
    def manual_un_lock_assets(self, user, assets):
        from web.fun_test.models import Asset
        for asset_type, assets_for_type in assets.items():
            for asset in assets_for_type:
                try:
                    a = Asset.objects.get(name=asset, manual_lock_user=user, type=asset_type)
                    a.manual_lock_user = None
                    a.save()
                except Exception as ex:   #TODO
                    print(str(ex))


    @fun_test.safe
    def is_asset_in_test_bed(self, asset_name, asset_type, test_bed_name):
        found = False
        from lib.topology.topology_helper import TopologyHelper
        if test_bed_name not in self.PSEUDO_TEST_BEDS:
            test_bed_spec = self.get_test_bed_spec(name=test_bed_name)
            th = TopologyHelper(spec=test_bed_spec)
            topology = th.get_expanded_topology()
            if asset_type == AssetType.DUT:
                duts = topology.get_duts()
                for dut_index, dut in duts.iteritems():
                    if dut.spec["dut"] == asset_name:
                        found = True
                        break
            if asset_type == AssetType.HOST:
                hosts = topology.get_hosts()
                for host_index, host in hosts.iteritems():
                    if host.name == asset_name:
                        found = True
                        break
            if asset_type == AssetType.PERFORMANCE_LISTENER_HOST:
                hosts = topology.get_perf_listener_hosts()
                for host_index, host in hosts.iteritems():
                    if host.name == asset_name:
                        found = True
                        break
            if asset_type == AssetType.PCIE_HOST:
                hosts = topology.get_pcie_hosts()
                for host_index, host in hosts.iteritems():
                    if host.name == asset_name:
                        found = True
                        break
        return found


    @fun_test.safe
    def is_asset_valid(self, asset_name, asset_type):
        valid_test_beds = self.get_valid_test_beds()
        found = False
        for test_bed_name in valid_test_beds:
            found = self.is_asset_in_test_bed(test_bed_name=test_bed_name, asset_name=asset_name, asset_type=asset_type)
            if found:
                break
        return found

    @fun_test.safe
    def get_assets_required(self, test_bed_name, with_pool_member_type_options=False, all_test_bed_specs=None):
        from lib.topology.topology_helper import TopologyHelper
        assets_required = {}
        if test_bed_name not in self.PSEUDO_TEST_BEDS:
            test_bed_spec = self.get_test_bed_spec(name=test_bed_name, all_test_bed_specs=all_test_bed_specs)
            fun_test.simple_assert(test_bed_spec, "Test-bed spec for: {}".format(test_bed_name))

            th = TopologyHelper(spec=test_bed_spec)
            topology = th.get_expanded_topology()
            duts = topology.get_duts()
            if with_pool_member_type_options:
                dut_objs = [duts[x] for x in duts]
            else:
                dut_objs = [duts[x].name for x in duts]
            assets_required[AssetType.DUT] = dut_objs

            hosts = topology.get_hosts()
            host_names = [host_obj.name for name, host_obj in hosts.iteritems()]
            assets_required[AssetType.HOST] = host_names

            perf_listener_hosts = topology.get_perf_listener_hosts()
            host_names = [host_obj.name for name, host_obj in perf_listener_hosts.iteritems()]
            assets_required[AssetType.PERFORMANCE_LISTENER_HOST] = host_names

            pcie_hosts = topology.get_pcie_hosts()
            host_names = [host_obj.name for name, host_obj in pcie_hosts.iteritems()]
            assets_required[AssetType.PCIE_HOST] = host_names

        return assets_required

    @fun_test.safe
    def is_asset_available(self, asset):
        pass

    @fun_test.safe
    def _disable_assets_in_test_bed_spec(self,
                                         test_bed_spec,
                                         asset_type,
                                         to_disable=None,
                                         to_enable=None):
        if asset_type in [AssetType.DUT]:
            if "dut_info" in test_bed_spec:
                dut_info = test_bed_spec["dut_info"]
                for dut_index, dut_spec in dut_info.iteritems():
                    if "dut" in dut_spec:
                        if to_enable and dut_spec["dut"] not in to_enable:
                            dut_spec["disabled"] = True
                        if to_disable and dut_spec["dut"] in to_disable:
                            dut_spec["disabled"] = True

        if asset_type == AssetType.HOST:
            disabled_hosts = []
            if "host_info" in test_bed_spec:
                for host in test_bed_spec["host_info"]:
                    if to_disable and host in to_disable:
                        disabled_hosts.append(host)
                    if to_enable and host not in to_enable:
                        disabled_hosts.append(host)
            test_bed_spec["disabled_hosts"] = disabled_hosts

        if asset_type == AssetType.PERFORMANCE_LISTENER_HOST:
            disabled_perf_listener_hosts = []
            if "perf_listener_host_info" in test_bed_spec:
                for host in test_bed_spec["perf_listener_host_info"]:
                    if to_disable and host in to_disable:
                        disabled_perf_listener_hosts.append(host)
                    if to_enable and host not in to_enable:
                        disabled_perf_listener_hosts.append(host)
            test_bed_spec["disabled_perf_listener_hosts"] = disabled_perf_listener_hosts

        return test_bed_spec

    @fun_test.safe
    def check_custom_test_bed_availability(self, custom_spec):
        result = {"status": True,
                  "message": "",
                  "custom_test_bed_spec": None,
                  "assets_required": {AssetType.DUT: [],
                                      AssetType.HOST: [],
                                      AssetType.PERFORMANCE_LISTENER_HOST: []}}
        from web.fun_test.models import Asset
        from web.fun_test.models_helper import is_suite_in_progress
        from django.core.exceptions import ObjectDoesNotExist
        base_test_bed_name = custom_spec.get("base_test_bed", None)
        fun_test.simple_assert(base_test_bed_name, "Base test-bed available in custom-spec")

        test_bed_spec = self.get_test_bed_spec(name=base_test_bed_name)
        fun_test.simple_assert(test_bed_spec, "Test-bed spec for: {}".format(base_test_bed_name))

        asset_request = custom_spec.get("asset_request", None)
        fun_test.simple_assert(asset_request, "asset_request in custom_spec")

        assets_required_config = {AssetType.DUT: {},
                                  AssetType.HOST: {},
                                  AssetType.PERFORMANCE_LISTENER_HOST: {}}

        all_asset_types = [AssetType.DUT,
                           AssetType.HOST,
                           AssetType.PERFORMANCE_LISTENER_HOST]
        for asset_type in all_asset_types:
            if asset_type in asset_request:
                info = asset_request[asset_type]
                num_required = info.get("num", 0)
                specifics = info.get("names", None)
                pool_member_type_options = info.get("pool_member_type_options", None)
                if pool_member_type_options:
                    for pool_member_type, pool_member_type_value in pool_member_type_options.iteritems():
                        if "num" in pool_member_type_value:
                            num_required += pool_member_type_value["num"]

                if specifics:
                    num_required = len(specifics)
                assets_required_config[asset_type] = {"num_required": num_required,
                                                      "specific": specifics,
                                                      "pool_member_type_options": pool_member_type_options}

        asset_category_unavailable = False
        error_message = ""

        matches_for_pool_member_type = []

        for asset_type in all_asset_types:
            if asset_category_unavailable:
                break
            num_assets_available = 0
            num_assets_required = assets_required_config[asset_type].get("num_required", None)

            if num_assets_required is not None:

                assets_in_test_bed = self.get_assets_required(test_bed_name=base_test_bed_name, with_pool_member_type_options=True)

                assets_in_test_bed = assets_in_test_bed.get(asset_type)
                unavailable_assets = []
                available_assets = []
                for asset_in_test_bed in assets_in_test_bed:
                    asset_name = asset_in_test_bed
                    if isinstance(asset_in_test_bed, Dut):
                        asset_name = asset_in_test_bed.name

                    specific_assets = assets_required_config[asset_type].get("specific", None)
                    if specific_assets and asset_name not in specific_assets:
                        fun_test.log("Specific Assets set: {}, so skipping {}".format(specific_assets, asset_in_test_bed))
                        continue
                    asset = None
                    try:
                        asset = Asset.objects.get(name=asset_name, type=asset_type)
                    except ObjectDoesNotExist:
                        pass

                    in_progress = False
                    is_manual_locked = False
                    is_disabled = False
                    is_unhealthy = False
                    if asset:
                        is_manual_locked = asset.manual_lock_user
                        is_disabled = asset.disabled
                        job_ids = asset.job_ids
                        is_unhealthy = asset.health_status != AssetHealthStates.HEALTHY
                        if job_ids:
                            for job_id in job_ids:
                                in_progress = is_suite_in_progress(job_id=job_id, test_bed_type="")
                                if in_progress:
                                    unavailable_assets.append(asset_name)
                        elif (is_manual_locked or is_disabled or is_unhealthy):
                            unavailable_assets.append(asset_name)

                    pool_member_type_options = assets_required_config[asset_type].get("pool_member_type_options", None)
                    if pool_member_type_options:
                        this_asset_pool_member_type = asset_in_test_bed.get_pool_member_type()
                        pool_member_required_count = pool_member_type_options[str(this_asset_pool_member_type)]["num"]
                        current_match_count = matches_for_pool_member_type.count(this_asset_pool_member_type)
                        if current_match_count >= pool_member_required_count:
                            continue
                        if not is_manual_locked and not in_progress and not is_disabled and not is_unhealthy:
                            matches_for_pool_member_type.append(this_asset_pool_member_type)
                    if not is_manual_locked and not in_progress and not is_disabled and not is_unhealthy:
                        num_assets_available += 1
                        available_assets.append(asset_name)
                    if num_assets_required == num_assets_available:
                        break

                if num_assets_required > num_assets_available:
                    error_message = "Assets: {} required: {}, available: {}".format(asset_type,
                                                                                    num_assets_required,
                                                                                    num_assets_available)
                    asset_category_unavailable = True
                    break
                elif num_assets_required <= num_assets_available:
                    self._disable_assets_in_test_bed_spec(test_bed_spec=test_bed_spec,
                                                          asset_type=asset_type,
                                                          to_disable=unavailable_assets,
                                                          to_enable=available_assets)
                    result["assets_required"][asset_type].extend(available_assets)

        if asset_category_unavailable:
            result["status"] = False
            result["message"] = error_message
        else:
            result["custom_test_bed_spec"] = test_bed_spec
        return result

    @fun_test.safe
    def get_valid_test_beds(self):
        all_test_beds = self.get_all_test_beds_specs()
        all_test_bed_names = all_test_beds.keys()
        all_test_bed_names.extend(self.PSEUDO_TEST_BEDS)
        return all_test_bed_names


    """
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
    """

    def add_or_replace_fs_spec(self, fs_name, spec):
        json_spec = parse_file_to_json(file_name=self.FS_SPEC)
        new_spec = []
        replaced = False
        for fs in json_spec:
            if fs["name"] == fs_name:
                new_spec.append(spec)
                replaced = True
            else:
                new_spec.append(fs)
        if not replaced:
            new_spec.append(spec)
        # sorted_fs = sorted(new_spec, key=lambda x: x["name"])
        with open(self.FS_SPEC, "w") as f:
            f.write(json.dumps(new_spec, indent=4))
            f.close()

    def add_test_bed_spec(self, test_bed_name, spec):
        json_spec = parse_file_to_json(file_name=self.TEST_BED_SPEC)
        if test_bed_name not in json_spec:
            json_spec[test_bed_name] = spec
        with open(self.TEST_BED_SPEC, "w") as f:
            f.write(json.dumps(json_spec, indent=4))
            f.close()

asset_manager = AssetManager()

if __name__ == "__main2__":
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


if __name__ == "__main__":
    print "Hi"
    # get base test-bed
    # custom_spec = {"base_test_bed": "fs-inspur-test", "asset_request": {"DUT with servers": {"num": 1}}}
    # custom_spec = {"base_test_bed": "fs-inspur-test", "asset_request": {"DUT": {"num": 1, "pool_member_type": 1}}}
    # custom_spec = {"base_test_bed": "fs-inspur-test", "asset_request": {"DUT": {"num": 1, "pool_member_type": 2}}}
    custom_spec = {"base_test_bed": "fs-inspur-test", "asset_request": {"DUT": {"pool_member_type_options": {0: {"num": 1}, 2: {"num": 1}}}}}
    """
    Default: 1, With
    servers: 0, With
    SSDs: 0
    """
    custom_spec = {"base_test_bed": "fs-inspur", "asset_request": {"DUT": {"pool_member_type_options": {"0": {"num": 1}}}}}

    # custom_spec = {"base_test_bed": "fs-inspur-test", "asset_request": {"DUT": {"pool_member_type_options": {1: {"num": 1}}}}}
    # custom_spec = {"base_test_bed": "fs-inspur-test", "asset_request": {"DUT": {"pool_member_type_options": {2: {"num": 1}}}}}

    """
    custom_spec = {"base_test_bed": "fs-inspur",
                   "asset_request":
                       {
                           "DUT": {"names": ["fs-42", "fs-41"]},

                   "Host": {"names": ["mktg-server-01"]}}}
    """
    spec = asset_manager.check_custom_test_bed_availability(custom_spec=custom_spec)

    i = 0
    # get requested DUT count
    # get requested host count
    # if num DUTs matches, gather DUTs allotted
    # if num Hosts matched, gather Hosts allotted

    # pass TopologyHelper with pool selection