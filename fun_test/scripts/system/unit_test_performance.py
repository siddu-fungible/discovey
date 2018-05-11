from lib.system.fun_test import *
from lib.host.lsf_status_server import LsfStatusServer
import json
import re
from datetime import datetime
from web.fun_test.analytics_models_helper import MetricHelper
from web.fun_test.metrics_models import UnitTestPerformance
from fun_global import get_localized_time

LSF_WEB_SERVER_BASE_URL = "http://10.1.20.73:8080"
ALLOC_SPEED_TEST_TAG = "alloc_speed_test"
TOLERANCE_PERCENTAGE = 5
BLACK_LIST = [2184, 2194, 2202]


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. Step 1
        2. Step 2""")

    def setup(self):
        pass

    def cleanup(self):
        pass


class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Alloc speed test performance",
                              steps="Steps 1")

    def setup(self):
        print("Testcase setup")

    def cleanup(self):
        print("Testcase cleanup")

    def run(self):
        job_info = {}
        lsf_status_server = LsfStatusServer()
        past_jobs = lsf_status_server.get_past_jobs_by_tag(tag="nightly")

        issues_found = 0
        for past_job in past_jobs:
            return_code = -1
            job_id = past_job["job_id"]

            jenkins_build_number = past_job["jenkins_build_number"]
            branch_funsdk = past_job["branch_funsdk"]
            git_commit = past_job["git_commit"]
            software_date = past_job["software_date"]
            completion_date = "20" + past_job["completion_date"]
            hardware_version = "---"
            if "hardware_version" in past_job:
                hardware_version = past_job["hardware_version"]

            fun_test.log("Return code: {}".format(return_code))
            fun_test.log("Job id: {}".format(job_id))
            fun_test.log("Branch Fun SDK: {}".format(branch_funsdk))
            fun_test.log("Jenkins build number: {}".format(jenkins_build_number))
            fun_test.log("Git commit: {}".format(git_commit))
            fun_test.log("Software date: {}".format(software_date))
            dt = get_localized_time(datetime.strptime(completion_date, "%Y-%m-%d %H:%M"))
            models_helper.add_jenkins_job_id_map(jenkins_job_id=jenkins_build_number,
                                                 fun_sdk_branch=branch_funsdk,
                                                 git_commit=git_commit,
                                                 software_date=software_date,
                                                 hardware_version=hardware_version,
                                                 completion_date=completion_date)
            response = lsf_status_server.get_job_by_id(job_id=job_id)
            fun_test.test_assert(response, "Fetch job info for {}".format(job_id))
            response_dict = json.loads(response)
            fun_test.log(json.dumps(response_dict, indent=4))
            output_text = response_dict["output_text"]

            try:
                return_code = int(response_dict["job_dict"]["return_code"])
            except Exception as ex:
                fun_test.critical(str(ex))

            lines = output_text.split("\n")

            num_passed = 0
            num_failed = 0
            num_disabled = 0


            mh = MetricHelper(model=UnitTestPerformance)
            for line in lines:
                m = re.search(r'\[\s+PASSED\s+]\s+(\d+)\s+tests', line)
                if m:
                    num_passed = int(m.group(1))
                m = re.search(r'\[\s+FAILED\s+]\s+(\d+)\s+tests', line)
                if m:
                    num_failed = int(m.group(1))
                m = re.search(r'\[\s+FAILED\s+]\s+(\d+)\s+tests', line)
                if m:
                    num_disabled = int(m.group(1))
            '''
            date_time = models.DateTimeField(verbose_name="Datetime")
            input_app = "unit_tests"
            num_passed = models.IntegerField(verbose_name="Passed")
            num_failed = models.IntegerField(verbose_name="Failed")
            num_disabled = models.IntegerField(verbose_name="Disabled")
            hardware_version = models.CharField(max_length=50, default="")
            software_date = models.CharField(max_length=50, default="")
            git_commit = models.CharField(max_length=100, default="")
            branch_funsdk = models.CharField(max_length=100, default="")
            '''
            mh.add_entry(input_date_time=get_localized_time(dt),
                         output_num_passed=num_passed,
                         output_num_failed=num_failed,
                         output_num_disabled=num_disabled,
                         input_hardware_version=hardware_version,
                         input_software_date=software_date,
                         input_git_commit=git_commit,
                         input_branch_funsdk=branch_funsdk)
        fun_test.test_assert_expected(expected=0, actual=issues_found, message="Number of issues found")


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
