from lib.system.fun_test import *
from web.fun_test.models import TestBed
from web.fun_test.django_interactive import *
from lib.fun.fs import Fs
from threading import Thread
import time
from services.daemon_service import Service
from asset.asset_global import AssetHealthStates, AssetType

UNHEALTHY_VERDICT_TIME = 4 * 60  # 10 mins


class TestBedWorker(Thread):
    def __init__(self, test_bed_name, test_bed_spec, logger):
        super(TestBedWorker, self).__init__()
        self.test_bed_name = test_bed_name
        self.test_bed_spec = test_bed_spec
        self.logger = logger
        self.terminated = False

    def run(self):
        while not self.terminated:
            health_status = AssetHealthStates.HEALTHY
            time.sleep(5)
            test_bed_objects = TestBed.objects.filter(name=self.test_bed_name)
            if test_bed_objects.exists():
                # print "Test-bed worker: {}".format(self.test_bed_name)
                test_bed_object = test_bed_objects[0]
                if test_bed_object.disabled:
                    health_status = AssetHealthStates.DISABLED
                elif test_bed_object.health_check_enabled:
                    self.check_health()
                elif not test_bed_object.health_check_enabled:
                    health_status = AssetHealthStates.HEALTHY
                test_bed_object.set_health(status=health_status)
            else:
                self.logger.exception("Test-bed entry for {} not found".format(self.test_bed_name))
                self.terminated = True

    def check_health(self):
        am = fun_test.get_asset_manager()
        assets = am.get_assets_required(test_bed_name=self.test_bed_name)

        for asset_type, asset_list in assets.iteritems():
            issue_found = False
            health_result, error_message = True, ""
            only_reachability = False
            if asset_type == AssetType.DUT:
                only_reachability = True

            for asset_name in asset_list:
                asset_objects = Asset.objects.filter(name=asset_name, type=asset_type)
                asset_object = None

                if asset_objects.exists():
                    asset_object = asset_objects.first()
                else:
                    pass  #TODO
                instance = am.get_asset_instance(asset=asset_object)
                if not instance:
                    pass  # TODO
                else:
                    health_result, error_message = instance.health(only_reachability=only_reachability)
                self.set_health_status(asset_object=asset_object,
                                       health_result=health_result,
                                       error_message=error_message)

                if not health_result:
                    issue_found = True
                    break
            if issue_found:
                self.logger.exception("Issue found: {}, {}".format(health_result, error_message))
                break


    def set_health_status(self, asset_object, health_result, error_message):
        health_status = AssetHealthStates.HEALTHY
        if asset_object.disabled:
            health_status = AssetHealthStates.DISABLED
        else:
            if not asset_object.health_check_enabled:
                health_status = AssetHealthStates.HEALTHY
            elif asset_object.health_check_enabled:
                if health_result:
                    health_status = AssetHealthStates.HEALTHY
                elif not health_result:

                    current_health_status = asset_object.health_status
                    if current_health_status == AssetHealthStates.DEGRADING:
                        time_in_degrading_state = (get_current_time() - asset_object.state_change_time).total_seconds()

                        if time_in_degrading_state > UNHEALTHY_VERDICT_TIME:
                            health_status = AssetHealthStates.UNHEALTHY
                            self.logger.exception("Setting {} to unhealthy".format(asset_object.name))
                    else:
                        health_status = AssetHealthStates.DEGRADING
                        self.logger.exception("Setting {} to degrading".format(asset_object.name))

        asset_object.set_health(status=health_status, message=error_message)

    def terminate(self):
        self.terminated = True


class AssetHealthMonitor(Service):
    service_name = "asset_health_monitor"
    workers = {}

    def run(self, filter_test_bed_name=None):
        am = fun_test.get_asset_manager()

        while True:
            all_test_bed_specs = am.get_all_test_beds_specs()
            self.beat()
            for test_bed_name, test_bed_spec in all_test_bed_specs.iteritems():
                if filter_test_bed_name and test_bed_name != filter_test_bed_name:
                    continue
                if test_bed_name not in am.PSEUDO_TEST_BEDS:
                    if test_bed_name not in self.workers:
                        worker_thread = TestBedWorker(test_bed_name=test_bed_name,
                                                      test_bed_spec=test_bed_spec,
                                                      logger=self.get_logger())
                        self.workers[test_bed_name] = worker_thread
                        worker_thread.start()
                        self.get_logger().info("Started worker for {}".format(test_bed_name))
            self.remove_stale_test_beds(all_test_bed_specs=all_test_bed_specs)
            time.sleep(10)

    def remove_stale_test_beds(self, all_test_bed_specs):
        test_beds_marked_for_deletion = []
        for worker_test_bed_name, worker_thread in self.workers.iteritems():
            if worker_test_bed_name not in all_test_bed_specs:
                worker_thread.terminate()
                test_beds_marked_for_deletion.append(worker_test_bed_name)

        for test_bed_marked_for_deletion in test_beds_marked_for_deletion:
            del self.workers[test_bed_marked_for_deletion]
            self.logger.info("Stale test-bed {} removed".format(test_bed_marked_for_deletion))


if __name__ == "__main__":
    service = AssetHealthMonitor()
    service.run(filter_test_bed_name="fs-118")
