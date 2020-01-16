from lib.system.fun_test import *
from web.fun_test.models import TestBed
from web.fun_test.django_interactive import *
from lib.fun.fs import Fs
from threading import Thread
import time
from services.daemon_service import Service
from asset.asset_global import AssetHealthStates, AssetType
from jinja2 import Environment, FileSystemLoader, Template
from web.web_global import JINJA_TEMPLATE_DIR


UNHEALTHY_VERDICT_TIME = 10 * 60  # 10 mins
# start service by: nohup python asset_health_monitor.py >/dev/null 2>&1 &

class ReportWorker(Thread):
    def run(self):
        while True:
            test_bed_reports = []
            asset_reports = []

            test_beds = TestBed.objects.all()
            for test_bed in test_beds:
                if not test_bed.disabled and test_bed.health_check_enabled and (test_bed.health_status == AssetHealthStates.UNHEALTHY):
                    test_bed_reports.append({"test_bed_name": test_bed.name,
                                             "health_status": test_bed.health_status,
                                             "health_check_message": test_bed.health_check_message})

            assets = Asset.objects.all()
            for asset in assets:
                if asset.health_check_enabled and (asset.health_status == AssetHealthStates.UNHEALTHY):
                    asset_reports.append({"asset_name": asset.name,
                                          "health_status": asset.health_status,
                                          "health_check_message": asset.health_check_message})

            if test_bed_reports or asset_reports:
                file_loader = FileSystemLoader(JINJA_TEMPLATE_DIR)
                env = Environment(loader=file_loader)
                template = env.get_template('asset_health_monitor.html')
                content = template.render(test_bed_reports=test_bed_reports, asset_reports=asset_reports)
                data = send_mail(to_addresses=[TEAM_REGRESSION_EMAIL],
                                 subject="ALERT: Asset health monitor",
                                 content=content)

            time.sleep(60 * 15)

class TestBedWorker(Thread):
    def __init__(self, test_bed_name, test_bed_spec, logger, service):
        super(TestBedWorker, self).__init__()
        self.test_bed_name = test_bed_name
        self.test_bed_spec = test_bed_spec
        self.logger = logger
        self.terminated = False
        self.service = service

    def _get_base_log(self):
        s = "{}: ".format(self.test_bed_name)
        return s

    def info(self, log):
        self.service.info(message="{}: {}".format(self._get_base_log(), log))

    def alert(self, log):
        self.service.alert(message="{}: {}".format(self._get_base_log(), log))

    def report_exception(self, exception_log):
        self.service.report_exception(exception_log="{}: {}".format(self._get_base_log(), exception_log))

    def run(self):
        try:
            while not self.terminated:
                health_status, health_check_error_message = AssetHealthStates.HEALTHY, ""
                time.sleep(5)
                test_bed_objects = TestBed.objects.filter(name=self.test_bed_name)
                if not test_bed_objects.exists():
                    self.terminated = True
                self.service.service_assert(test_bed_objects.exists(), "Test-bed entry for {} not found".format(self.test_bed_name))
                test_bed_object = test_bed_objects.first()

                if test_bed_object.disabled:
                    health_status = AssetHealthStates.DISABLED
                else:
                    if test_bed_object.health_check_enabled:
                        health_status, health_check_error_message = self.check_health()
                    else:
                        if test_bed_object.health_check_enabled:
                            health_status = AssetHealthStates.HEALTHY

                if test_bed_object.health_status != health_status:
                    self.info("Test-bed status set to {}".format(health_status))
                if health_status == AssetHealthStates.UNHEALTHY:
                    self.alert("Status set to unhealthy")
                if health_status == AssetHealthStates.DEGRADING:
                    self.alert("Test-bed status set to degrading")

                test_bed_object.set_health(status=health_status, message=health_check_error_message)
                time.sleep(60)
        except Exception as ex:
            self.report_exception(str(ex))
            time.sleep(60)

    def check_health(self):
        am = fun_test.get_asset_manager()
        assets = am.get_assets_required(test_bed_name=self.test_bed_name)

        issue_found = False
        health_result_for_test_bed, error_message_for_test_bed = AssetHealthStates.HEALTHY, ""
        at_least_one_unhealthy = False
        at_least_one_degrading = False
        at_least_one_disabled = False
        for asset_type, asset_list in assets.iteritems():

            health_result, error_message = True, ""
            only_reachability = False
            if asset_type == AssetType.DUT:
                only_reachability = True

            for asset_name in asset_list:
                asset_objects = Asset.objects.filter(name=asset_name, type=asset_type)

                exception_message = "Asset object for {}: {} not found".format(asset_type, asset_name)
                self.service.service_assert(asset_objects.exists(), exception_message)
                asset_object = asset_objects.first()

                instance = am.get_asset_instance(asset=asset_object)
                self.service.service_assert(instance, "Unable to retrieve asset instance for {}: {}".format(asset_type,
                                                                                                            asset_name))
                health_result, error_message = instance.health(only_reachability=only_reachability)
                if asset_type in [AssetType.HOST, AssetType.PCIE_HOST, AssetType.PERFORMANCE_LISTENER_HOST]:
                    try:
                        instance.disconnect()
                    except:
                        pass
                final_health_status = self.set_health_status(asset_object=asset_object,
                                                             health_result=health_result,
                                                             error_message=error_message)
                if final_health_status == AssetHealthStates.DEGRADING:
                    at_least_one_degrading = True
                if final_health_status == AssetHealthStates.UNHEALTHY:
                    at_least_one_unhealthy = True
                if final_health_status == AssetHealthStates.DISABLED:
                    at_least_one_disabled = True

                if not health_result:
                    issue_found = True
                    error_message_for_test_bed = error_message

                    break
            if issue_found:
                self.report_exception("Issue found: {}, {}".format(health_result, error_message))
                break

        if issue_found:
            if at_least_one_degrading:
                health_result_for_test_bed = AssetHealthStates.DEGRADING
                self.alert("Setting Test-bed to degrading")

            if at_least_one_unhealthy:
                health_result_for_test_bed = AssetHealthStates.UNHEALTHY
                self.alert("Setting Test-bed to unhealthy")

            if at_least_one_disabled:
                health_result_for_test_bed = AssetHealthStates.UNHEALTHY
                self.alert("Setting Test-bed to unhealthy, one asset disabled")


        return health_result_for_test_bed, error_message_for_test_bed

    def set_health_status(self, asset_object, health_result, error_message):
        health_status = AssetHealthStates.HEALTHY
        if not asset_object.health_check_enabled:
            health_status = AssetHealthStates.HEALTHY
        elif asset_object.health_check_enabled:
            if health_result:
                health_status = AssetHealthStates.HEALTHY
            elif not health_result:

                current_health_status = asset_object.health_status
                health_status = current_health_status
                if current_health_status == AssetHealthStates.DEGRADING:

                    time_in_degrading_state = (get_current_time() - asset_object.state_change_time).total_seconds()
                    health_status = AssetHealthStates.DEGRADING
                    if time_in_degrading_state > UNHEALTHY_VERDICT_TIME:
                        health_status = AssetHealthStates.UNHEALTHY
                        self.alert("Setting {} to unhealthy".format(asset_object.name))
                else:
                    if not current_health_status == AssetHealthStates.UNHEALTHY:
                        health_status = AssetHealthStates.DEGRADING
                        self.alert("Setting {} to degrading".format(asset_object.name))

        asset_object.set_health(status=health_status, message=error_message)
        return health_status

    def terminate(self):
        self.terminated = True


class AssetHealthMonitor(Service):
    service_name = "asset_health_monitor"
    workers = {}
    report_worker = None

    def __init__(self):
        super(AssetHealthMonitor, self).__init__()
        self.report_worker = ReportWorker()
        self.report_worker.start()

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
                                                      logger=self.get_logger(),
                                                      service=self)
                        self.workers[test_bed_name] = worker_thread
                        worker_thread.start()
                        self.get_logger().info("Started worker for {}".format(test_bed_name))
            self.remove_stale_test_beds(all_test_bed_specs=all_test_bed_specs)
            time.sleep(30)

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
    # service.run(filter_test_bed_name="fs-118")
    service.run()
