from lib.system.fun_test import *
import requests
import json
import re
from web.fun_test.analytics_models_helper import MetricChartHelper
from web.fun_test.analytics_models_helper import AllocSpeedPerformanceHelper

LSF_WEB_SERVER_BASE_URL = "http://10.1.20.73:8080"
ALLOC_SPEED_TEST_TAG = "alloc_speed_test"
TOLERANCE_PERCENTAGE = 5


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
        url = "{}/?tag={}&format=json".format(LSF_WEB_SERVER_BASE_URL, ALLOC_SPEED_TEST_TAG)
        response = requests.get(url=url)
        fun_test.test_assert(response.status_code == 200, "Fetched jobs by tag")
        response_dict = json.loads(response.text)
        fun_test.log(json.dumps(response_dict, indent=4))
        past_jobs = response_dict["past_jobs"]
        job_info = {}
        for past_job in past_jobs:
            return_code = -1
            job_id = past_job["job_id"]

            jenkins_build_number = past_job["jenkins_build_number"]
            branch_fun_sdk = past_job["branch_funsdk"]
            git_commit = past_job["git_commit"]
            software_date = past_job["software_date"]
            hardware_version = "---"
            if "hardware_version" in past_job:
                hardware_version = past_job["hardware_version"]

            fun_test.log("Return code: {}".format(return_code))
            fun_test.log("Job id: {}".format(job_id))
            fun_test.log("Branch Fun SDK: {}".format(branch_fun_sdk))
            fun_test.log("Jenkins build number: {}".format(jenkins_build_number))
            fun_test.log("Git commit: {}".format(git_commit))
            fun_test.log("Software date: {}".format(software_date))
            models_helper.add_jenkins_job_id_map(jenkins_job_id=jenkins_build_number,
                                                 fun_sdk_branch=branch_fun_sdk,
                                                 git_commit=git_commit, software_date=software_date, hardware_version=hardware_version)
            job_info_url = "{}/job/{}?format=json".format(LSF_WEB_SERVER_BASE_URL, job_id)
            fun_test.log("URL: {}".format(job_info_url))
            response = requests.get(job_info_url)
            fun_test.test_assert(response.status_code == 200, "Fetch job info for {}".format(job_id))
            response_dict = json.loads(response.text)
            fun_test.log(json.dumps(response_dict, indent=4))
            output_text = response_dict["output_text"]

            return_code = int(response_dict["job_dict"]["return_code"])

            lines = output_text.split("\n")
            lines = [x for x in lines if "Best time" in x]
            output_one_malloc_free_wu = 0
            output_one_malloc_free_threaded = 0
            for line in lines:
                m = re.search(r'Best time for one malloc/free \(WU\): (\d+)ns', line)
                if m:
                    output_one_malloc_free_wu = int(m.group(1))
                m = re.search(r'Best time for one malloc/free \(threaded\): (\d+)ns', line)
                if m:
                    output_one_malloc_free_threaded = int(m.group(1))
            try:
                if not int(return_code) == 0:
                    continue
            except Exception as ex:
                fun_test.critical(str(ex))
            # fun_test.test_assert_expected(actual=return_code, expected=0, message="Return code in test: {}".format(ALLOC_SPEED_TEST_TAG))
            fun_test.log("Malloc Free threaded: {}".format(output_one_malloc_free_threaded))
            fun_test.log("Malloc Free WU: {}".format(output_one_malloc_free_wu))
            key = branch_fun_sdk
            m = re.search(r'refs/tags/bld_(\d+)', branch_fun_sdk)
            if m:
                key = int(m.group(1))
            AllocSpeedPerformanceHelper().add_entry(key=key, input_app="alloc_speed_test",
                                                    output_one_malloc_free_wu=output_one_malloc_free_wu,
                                                    output_one_malloc_free_threaded=output_one_malloc_free_threaded)

            job_info[int(key)] = {"output_one_malloc_free_wu": output_one_malloc_free_wu,
                                  "output_one_malloc_free_threaded": output_one_malloc_free_threaded}

        newest_build_number = max(job_info.keys())
        expected_values = {}

        metric_model_name = "AllocSpeedPerformance"
        chart_map = {}
        chart_map["output_one_malloc_free_wu"] = "Best time for 1 malloc/free (WU)"
        chart_map["output_one_malloc_free_threaded"] = "Best time for 1 malloc/free (Threaded)"
        values_to_check = ["output_one_malloc_free_wu", "output_one_malloc_free_threaded"]

        for value_to_check in values_to_check:
            chart_helper = MetricChartHelper(chart_name=chart_map[value_to_check], metric_model_name=metric_model_name)
            expected_values[value_to_check] = {"min": chart_helper.get_output_data_set(output_name=value_to_check)["min"],
                                               "max": chart_helper.get_output_data_set(output_name=value_to_check)["max"]}

        # expected_values["output_one_malloc_free_wu"] = {"expected": 660, "min": 1}
        # expected_values["output_one_malloc_free_threaded"] = {"expected": 402, "min": 1}

        # for value_to_check in values_to_check:
        #    expected_values[value_to_check]["max"] = expected_values[value_to_check]["expected"] * (1 + (TOLERANCE_PERCENTAGE / 100))

        for value_to_check in values_to_check:
            min_value, max_value = expected_values[value_to_check]["min"], expected_values[value_to_check]["max"]
            actual = job_info[newest_build_number][value_to_check]
            fun_test.test_assert(actual >= min_value, "Build: {} Attr: {} Min: {} Actual: {}".format(newest_build_number, value_to_check, min_value, actual))
            fun_test.test_assert(actual <= max_value, "Build: {} Attr: {} Max: {} Actual: {}".format(newest_build_number, value_to_check, max_value, actual))


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
