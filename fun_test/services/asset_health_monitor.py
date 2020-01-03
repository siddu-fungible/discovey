from lib.system.fun_test import *
from web.fun_test.models import TestBed
from web.fun_test.django_interactive import *
from threading import Thread
import time
from services.daemon_service import Service


class TestBedWorker(Thread):
    def __init__(self, test_bed_name, test_bed_spec, logger):
        super(TestBedWorker, self).__init__()
        self.test_bed_name = test_bed_name
        self.test_bed_spec = test_bed_spec
        self.logger = logger
        self.terminated = False

    def run(self):
        while not self.terminated:
            time.sleep(5)
            if TestBed.objects.filter(name=self.test_bed_name).exists():
                print "Test-bed worker: {}".format(self.test_bed_name)
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
    service = AssetHealthMonitor()
    service.run()

