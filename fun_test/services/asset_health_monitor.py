from lib.system.fun_test import *
from web.fun_test.models import TestBed
from web.fun_test.django_interactive import *
from threading import Thread
import time
from services.daemon_service import Service
from asset.asset_global import AssetHealthStates, AssetType


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
                    pass
                elif not test_bed_object.health_check_enabled:
                    health_status = AssetHealthStates.HEALTHY
                test_bed_object.set_health(status=health_status)
            else:
                self.logger.exception("Test-bed entry for {} not found".format(self.test_bed_name))
                self.terminated = True

    def terminate(self):
        self.terminated = True


class AssetHealthMonitor(Service):
    service_name = "asset_health_monitor"
    workers = {}

    def run(self):
        am = fun_test.get_asset_manager()

        while True:
            all_test_bed_specs = am.get_all_test_beds_specs()
            self.beat()
            for test_bed_name, test_bed_spec in all_test_bed_specs.iteritems():
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
    am = fun_test.get_asset_manager()
    assets = am.get_assets_required(test_bed_name="fs-11")
    for asset_type, asset_list in assets.iteritems():
        if asset_type in [AssetType.HOST, AssetType.PCIE_HOST]:
            for asset_name in asset_list:
                print asset_name
                linux_object = am.get_linux_host(name=asset_name)
                if not linux_object:
                    pass #TODO
                else:
                    health_result, error_message = linux_object.health()
    i = 0
    #service = AssetHealthMonitor()
    #service.run()
