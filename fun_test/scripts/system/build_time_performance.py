from lib.system.fun_test import *
from django.apps import apps
from fun_global import PerfUnit, FunPlatform
from lib.utilities.jenkins_manager import JenkinsManager
from lib.host.lsf_status_server import LsfStatusServer
from web.fun_test.analytics_models_helper import ModelHelper, get_data_collection_time
from web.fun_test.metrics_models import MetricChart
from web.fun_test.models import Suite
from web.fun_test.metrics_lib import MetricLib
from web.fun_test.models_helper import get_suite_execution
import time, psycopg2

app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
ml = MetricLib()

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
        result = True
        try:
            generic_helper = ModelHelper(model_name=model_name)
            generic_helper.set_units(validate=True, **unit_dict)
            generic_helper.add_entry(**value_dict)
            generic_helper.set_status(status)
        except Exception as ex:
            result = False
            fun_test.critical(str(ex))
        return result

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
            status = fun_test.FAILED
            if self.build_success == fun_test.PASSED and self.lsf_success == fun_test.PASSED:
                status = fun_test.PASSED
            else:
                self.total_time_taken = -1

            value_dict = {"date_time": get_data_collection_time(),
                          "total_time": self.total_time_taken}

            unit_dict = {"total_time_unit": PerfUnit.UNIT_SECS}
            db_success = self.add_to_db(model_name=model_name, value_dict=value_dict, unit_dict=unit_dict,
                                        status=status)
            fun_test.test_assert_expected(expected=True, actual=db_success, message="Db entry successful")
            fun_test.test_assert_expected(expected=fun_test.PASSED, actual=status, message="Fun On Demand build time status")

class PrBuildTimeTc(PalladiumTc):
    since_time = round(time.time()) - 86400
    status = fun_test.FAILED
    total_time_taken = -1
    FUN_ON_DEMAND_DATABASE = {'host': 'grafana.fungible.local',
                              'database': 'buildData',
                              'user': 'builddata_reader',
                              'password': 'pico80@Lhasa'}

    def describe(self):
        self.set_test_details(id=2,
                              summary="Poll Jenkins to get time taken for a PR build",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def run(self):
        try:
            conn = psycopg2.connect(**self.FUN_ON_DEMAND_DATABASE)
            cur = conn.cursor()
            cur.execute(
                "SELECT ROUND(AVG(duration_secs)) FROM \"buildTimes\" WHERE (job = 'funsdk/master' OR job LIKE "
                "'funsdk/pull_request%') AND start_time > " + str(
                    self.since_time) + " AND step = 'TotalTime' AND build_status LIKE 'Success'")
            average_time = int(cur.fetchone()[0])
            self.total_time_taken = average_time
            self.status = fun_test.PASSED
        except Exception as ex:
            fun_test.critical(str(ex))
        finally:
            model_name = "PrBuildTotalTimePerformance"

            value_dict = {"date_time": get_data_collection_time(),
                          "total_time": self.total_time_taken}

            unit_dict = {"total_time_unit": PerfUnit.UNIT_SECS}
            db_success = self.add_to_db(model_name=model_name, value_dict=value_dict, unit_dict=unit_dict,
                                   status=self.status)
            fun_test.test_assert_expected(expected=True, actual=db_success, message="Db entry successful")
            fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.status,
                                          message="Pr build time status")


class IntegrationJobBuildTimePerformanceTc(PalladiumTc):
    total_time_taken = -1
    status = fun_test.FAILED

    def describe(self):
        self.set_test_details(id=3,
                              summary="Calculate the time taken for integration job submission",
                              steps="Steps 1")

    def run(self):
        try:
            self.result = fun_test.FAILED
            self.timer1 = None
            self.timer2 = None
            test_bed_type = ["fs-118"]
            time_zone = "PST"
            build_parameters = {"RELEASE_BUILD": True,
                                "SKIP_DASM_C": True,
                                "BRANCH_FunHW": None,
                                "FUNOS_MAKEFLAGS": None,
                                "BRANCH_FunSDK": None,
                                "BRANCH_FunControlPlane": None,
                                "BRANCH_FunTools": None,
                                "BRANCH_FunOS": None}
            environment = {"test_bed_type": test_bed_type,
                           "with_jenkins_build": True,
                           "build_parameters": build_parameters}
            suites = Suite.objects.filter(name="test_fs1600.json") #199-test_fs1600.json
            fun_test.simple_assert(expression=len(suites) > 0, message="No suites with the given name")
            if len(suites):
                suite_id = suites.first().id
                emails = ["ashwin.s@fungible.com", "john.abraham@fungible.com"]
                submitter_email = "ashwin.s@fungible.com"
                suite_execution_id = queue_job3(suite_id=suite_id,
                                    build_url=None,
                                    tags=None,
                                    emails=emails,
                                    test_bed_type=test_bed_type,
                                    email_on_fail_only=False,
                                    environment=environment,
                                    scheduling_type=SchedulingType.ASAP,
                                    timezone_string=time_zone,
                                    requested_hour=None,
                                    requested_minute=None,
                                    requested_days=None,
                                    repeat_in_minutes=None,
                                    submitter_email=submitter_email,
                                    inputs=None,
                                    description="",
                                    suite_type=SuiteType.STATIC,
                                    rich_inputs=None)
                fun_test.log("The returned suite_execution id is {}".format(suite_execution_id))
                self.timer1 = FunTimer(max_time=4000)
                while not self.timer1.is_expired():
                    suite_execution = get_suite_execution(suite_execution_id=suite_execution_id)
                    fun_test.simple_assert(suite_execution, "Suite execution")
                    if suite_execution:
                        if self.timer2 and suite_execution.state <= JobStatusType.COMPLETED:
                            self.total_time_taken = self.timer2.elapsed_time()
                            self.result = suite_execution.result
                            fun_test.log("time taken is {}".format(self.total_time_taken))
                            break
                        elif not self.timer2 and suite_execution.state == JobStatusType.IN_PROGRESS:
                            self.timer2 = FunTimer(max_time=2000)
                        elif not self.timer2 and suite_execution.state <= JobStatusType.COMPLETED:
                            fun_test.log("The job completed too quickly and exited even before the timer could start")
                            break
                    else:
                        fun_test.log("suite execution object does not exist for the id {}".format(suite_execution_id))
                        break
                    fun_test.sleep(message="Waiting to poll suite status", seconds=20)
                fun_test.test_assert_expected(expected=True, actual=not self.timer1.is_expired(), message="Checking if "
                                                                                                       "the time expired")
                if self.total_time_taken != -1 and self.result == fun_test.PASSED:
                    self.status = fun_test.PASSED
                else:
                    self.total_time_taken = -1

        except Exception as ex:
            self.status = fun_test.FAILED
            fun_test.critical(str(ex))
        finally:
            model_name = "IntegrationJobBuildTimePerformance"

            value_dict = {"date_time": get_data_collection_time(),
                          "total_time": self.total_time_taken}

            unit_dict = {"total_time_unit": PerfUnit.UNIT_SECS}
            db_success = self.add_to_db(model_name=model_name, value_dict=value_dict, unit_dict=unit_dict,
                                        status=self.status)
            fun_test.test_assert_expected(expected=True, actual=db_success, message="Db entry successful")
            fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.status,
                                          message="Integration job submission status")


class SetBuildTimeChartStatusTc(PalladiumTc):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Set build failure details for build time performance",
                              steps="Steps 1")

    def run(self):
        try:
            self.result = fun_test.FAILED
            models = ["FunOnDemandTotalTimePerformance", "PrBuildTotalTimePerformance", "IntegrationJobBuildTimePerformance"]
            ml._set_chart_status(models=models, suite_execution_id=fun_test.get_suite_execution_id())
            self.result = fun_test.PASSED
        except Exception as ex:
            self.result = fun_test.FAILED
            fun_test.critical(str(ex))

        fun_test.test_assert_expected(expected=fun_test.PASSED, actual=self.result, message="Test result")


if __name__ == "__main__":
    myscript = MyScript()

    myscript.add_test_case(FunOnDemandBuildTimeTc())
    myscript.add_test_case(PrBuildTimeTc())
    myscript.add_test_case(IntegrationJobBuildTimePerformanceTc())
    myscript.add_test_case(SetBuildTimeChartStatusTc())

    myscript.run()
