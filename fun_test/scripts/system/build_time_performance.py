from lib.system.fun_test import *
from django.apps import apps
from fun_global import PerfUnit, FunPlatform
from lib.utilities.jenkins_manager import JenkinsManager
from lib.host.lsf_status_server import LsfStatusServer
from web.fun_test.analytics_models_helper import ModelHelper, get_data_collection_time
from web.fun_test.metrics_models import MetricChart

app_config = apps.get_app_config(app_label=MAIN_WEB_APP)

class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""

        1. Step 1
        2. Step 2
        3. Step 3""")

    def setup(self):
        fun_test.log("Script-level setup")
        self.lsf_status_server = LsfStatusServer()
        fun_test.shared_variables["lsf_status_server"] = self.lsf_status_server

    def cleanup(self):
        fun_test.log("Script-level cleanup")


class PalladiumTc(FunTestCase):
    boot_args = ""
    tags = ""
    note = ""
    fun_os_make_flags = ""
    hw_model = "F1"
    max_duration = 5
    release_build = "true"
    hw_version = "Ignored"
    run_target = "F1"
    extra_emails = []

    build_success = fun_test.FAILED
    lsf_success = fun_test.FAILED
    in_jenkins = True
    in_lsf = True
    timer = None
    build_number = -1
    lsf_job_id = -1

    def describe(self):
        self.set_test_details(id=0,
                              summary="",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        if not ("team-regression@fungible.com" in self.extra_emails):
            self.extra_emails.append("team-regression@fungible.com")
        fun_test.log("Testcase setup")

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        fun_test.add_checkpoint("Starting the jenkins build")
        jenkins_manager = JenkinsManager()
        lsf_server = LsfStatusServer()
        params = {"BOOTARGS": self.boot_args,
                  "MAX_DURATION": self.max_duration,
                  "RUN_MODE": "Batch",
                  "TAGS": self.tags,
                  "NOTE": self.note,
                  "RELEASE_BUILD": self.release_build,
                  "FUNOS_MAKEFLAGS": self.fun_os_make_flags,
                  "HW_VERSION": self.hw_version,
                  "RUN_TARGET": self.run_target,
                  "HW_MODEL": self.hw_model}

        try:
            self.build_on_jenkins(jenkins_manager=jenkins_manager, params=params)
            fun_test.log("Jenkins build number is  {} and the status is {}".format(self.build_number, self.build_success))
            fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.build_success,
                                          message="jenkins build successfully completed")
            self.monitor_lsf(lsf_server=lsf_server)
            fun_test.log("Lsf job id is {} and status is {}".format(self.lsf_job_id, self.lsf_success))
            fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.lsf_success, message="lsf job successfully completed")
        except Exception as ex:
            fun_test.critical(str(ex))

    def add_to_db(self, model_name, value_dict, unit_dict, status):
        try:
            generic_helper = ModelHelper(model_name=model_name)
            generic_helper.set_units(validate=True, **unit_dict)
            generic_helper.add_entry(**value_dict)
            generic_helper.set_status(status)
        except Exception as ex:
            fun_test.critical(str(ex))
        print ("used generic helper to add an entry into {}".format(model_name))

    def build_on_jenkins(self, jenkins_manager, params):
        queue_item = jenkins_manager.build(params=params, extra_emails=self.extra_emails)
        self.build_number = jenkins_manager.get_build_number(queue_item=queue_item)
        while self.in_jenkins and not self.timer.is_expired():
            job_info = jenkins_manager.get_job_info(build_number=self.build_number)
            if not job_info["building"]:
                job_result = job_info["result"]
                if job_result.lower() == "success":
                    self.in_jenkins = False
                    self.build_success = fun_test.PASSED
                break
            fun_test.sleep("waiting for jenkins build", seconds=60)

    def monitor_lsf(self, lsf_server):
        if not self.in_jenkins:
            while self.in_lsf and not self.timer.is_expired():
                job_info = lsf_server.get_last_job(tag=self.tags)
                if job_info and "job_id" in job_info:
                    self.lsf_job_id = job_info["job_id"]
                    if "state" in job_info and job_info["state"] == "completed":
                        if "return_code" in job_info:
                            self.in_lsf = False
                            if not job_info["return_code"]:
                                self.lsf_success = fun_test.PASSED
                                break
                        else:
                            break
                fun_test.sleep("waiting for lsf job completion", seconds=60)


class FunOnDemandBuildTimeTc(PalladiumTc):
    boot_args = "app=load_mods"
    tags = "qa_fun_on_demand_build_time"
    max_duration = 5
    note = "Building a trivial job to monitor time taken from start to end"

    def describe(self):
        self.set_test_details(id=1,
                              summary="Schedule a trivial job on Jenkins",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def run(self):
        try:
            self.timer = FunTimer(max_time=3600)
            super(FunOnDemandBuildTimeTc, self).run()
        except Exception as ex:
            fun_test.critical(str(ex))
        finally:
            self.total_time_taken = self.timer.elapsed_time()
            model_name = "FunOnDemandTotalTimePerformance"
            if self.build_success == fun_test.PASSED and self.lsf_success == fun_test.PASSED:
                status = fun_test.PASSED
            else:
                status = fun_test.FAILED

            value_dict = {"date_time": get_data_collection_time(),
                          "version": fun_test.get_version(),
                          "total_time": self.total_time_taken}

            unit_dict = {"total_time_unit": PerfUnit.UNIT_SECS}
            self.add_to_db(model_name=model_name, value_dict=value_dict, unit_dict=unit_dict, status=status)

class SetFunOnDemandBuildTimeChartStatusTc(PalladiumTc):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Set build failure details for fun on demand time taken performance",
                              steps="Steps 1")

    def run(self):
        try:
            self.result = fun_test.FAILED
            model = "FunOnDemandTotalTimePerformance"
            charts = MetricChart.objects.filter(metric_model_name=model)
            metric_model = app_config.get_metric_models()[model]
            for chart in charts:
                status = True
                data_sets = chart.get_data_sets()
                for data_set in data_sets:
                    inputs = data_set["inputs"]
                    entries = metric_model.objects.filter(**inputs).order_by("-input_date_time")[:1]
                    if len(entries):
                        entry = entries.first()
                        if not entry.status == fun_test.PASSED:
                            status = False
                            chart.last_build_status = fun_test.FAILED
                            chart.last_suite_execution_id = fun_test.get_suite_execution_id()
                            chart.last_build_date = get_current_time()
                            chart.last_test_case_id = self.id
                            chart.save()
                            break
                if status:
                    chart.last_build_status = fun_test.PASSED
                    chart.last_suite_execution_id = fun_test.get_suite_execution_id()
                    chart.last_test_case_id = self.id
                    chart.last_build_date = get_current_time()
                    chart.save()
            self.result = fun_test.PASSED
        except Exception as ex:
            self.result = fun_test.FAILED
            fun_test.critical(str(ex))

        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


if __name__ == "__main__":
    myscript = MyScript()

    myscript.add_test_case(FunOnDemandBuildTimeTc())
    myscript.add_test_case(SetFunOnDemandBuildTimeChartStatusTc())

    myscript.run()
