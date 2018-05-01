from lib.system.fun_test import *
from lib.host.lsf_status_server import LsfStatusServer
import requests
import json
import re
from web.fun_test.analytics_models_helper import MetricChartHelper
from web.fun_test.analytics_models_helper import AllocSpeedPerformanceHelper, MetricHelper
from web.fun_test.metrics_models import WuLatencyAllocStack, WuLatencyUngated

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
        past_jobs = lsf_status_server.get_past_jobs_by_tag(tag=ALLOC_SPEED_TEST_TAG)

        issues_found = 0
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
                                                 git_commit=git_commit,
                                                 software_date=software_date,
                                                 hardware_version=hardware_version)
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
            lines = [x for x in lines if "Best time" in x or "wu_latency_test" in x]

            alloc_speed_test_found = False
            output_one_malloc_free_wu = 0
            output_one_malloc_free_threaded = 0

            wu_latency_test_found = False
            wu_alloc_stack_ns_min = wu_alloc_stack_ns_max = wu_alloc_stack_ns_avg = None
            wu_ungated_ns_min = wu_ungated_ns_max = wu_ungated_ns_avg = None

            for line in lines:
                m = re.search(r'Best time for one malloc/free \(WU\):\s+(.*)\s+nsecs\s+\[perf_malloc_free_wu_ns\]', line)
                if m:
                    alloc_speed_test_found = True
                    d = json.loads(m.group(1))
                    output_one_malloc_free_wu = int(d["avg"])
                m = re.search(r'Best time for one malloc/free \(threaded\):\s+(.*)\s+nsecs\s+\[perf_malloc_free_wu_ns\]', line)
                if m:
                    d = json.loads(m.group(1))
                    output_one_malloc_free_threaded = int(d['avg'])

                # wu_latency_test
                m = re.search(r' wu_latency_test.*({.*}).*perf_wu_alloc_stack_ns', line)
                if m:
                    d = json.loads(m.group(1))
                    wu_latency_test_found = True
                    wu_alloc_stack_ns_min = int(d["min"])
                    wu_alloc_stack_ns_avg = int(d["avg"])
                    wu_alloc_stack_ns_max = int(d["max"])
                m = re.search(r' wu_latency_test.*({.*}).*perf_wu_ungated_ns', line)
                if m:
                    d = json.loads(m.group(1))
                    wu_latency_test_found = True
                    wu_ungated_ns_min = int(d["min"])
                    wu_ungated_ns_avg = int(d["avg"])
                    wu_ungated_ns_max = int(d["max"])

            try:
                if not int(return_code) == 0:
                    continue
            except Exception as ex:
                fun_test.critical(str(ex))

            fun_test.log("Malloc Free threaded: {}".format(output_one_malloc_free_threaded))
            fun_test.log("Malloc Free WU: {}".format(output_one_malloc_free_wu))
            fun_test.log("wu_latency_test: wu_alloc_stack_ns: min: {}, avg: {}, max: {}".format(wu_alloc_stack_ns_min,
                                                                                                wu_alloc_stack_ns_avg,
                                                                                                wu_alloc_stack_ns_max))
            fun_test.log("wu_latency_test: wu_ungated_ns: min: {}, avg: {}, max: {}".format(wu_ungated_ns_min,
                                                                                            wu_ungated_ns_avg,
                                                                                            wu_ungated_ns_max))

            key = branch_fun_sdk
            m = re.search(r'refs/tags/bld_(\d+)', branch_fun_sdk)
            if m:
                key = int(m.group(1))
            if key in BLACK_LIST:
                continue

            if wu_latency_test_found:

                for chart_name, metric_model_name, model in [
                    ("WU Latency: Ungated", "WuLatencyUngated", WuLatencyUngated),
                    ("WU Latency: Alloc Stack", "WuLatencyAllocStack",
                     WuLatencyAllocStack)]:
                    if metric_model_name == "WuLatencyUngated":
                        MetricHelper(model=model).add_entry(key=key,
                                                            input_app="wu_latency_test",
                                                            output_min=wu_ungated_ns_min,
                                                            output_max=wu_ungated_ns_max,
                                                            output_avg=wu_ungated_ns_avg)
                    elif metric_model_name == "WuLatencyAllocStack":
                        MetricHelper(model=model).add_entry(key=key,
                                                            input_app="wu_latency_test",
                                                            output_min=wu_alloc_stack_ns_min,
                                                            output_max=wu_alloc_stack_ns_max,
                                                            output_avg=wu_alloc_stack_ns_avg)
     

                    chart_helper = MetricChartHelper(chart_name=chart_name,
                                                     metric_model_name=metric_model_name)
                    entry = MetricHelper(model=model).get_recent_entry()

                    if entry:
                        values_to_check = ["output_min", "output_max", "output_avg"]
                        for value_to_check in values_to_check:
                            output_data_set = chart_helper.get_output_data_set(output_name=value_to_check)
                            expected_min_value, expected_max_value = output_data_set["min"], output_data_set["max"]

                            try:
                                actual = getattr(entry, value_to_check)
                                fun_test.test_assert(actual >= expected_min_value,
                                                     "Build: {} Chart: {} Attr: {} Min: {} Actual: {}".format(key,
                                                                                                              chart_name,
                                                                                                              value_to_check,
                                                                                                              expected_min_value,
                                                                                                              actual))
                                fun_test.test_assert(actual <= expected_max_value,
                                                     "Build: {} Chart: {} Attr: {} Max: {} Actual: {}".format(key,
                                                                                                              chart_name,
                                                                                                              value_to_check,
                                                                                                              expected_max_value,
                                                                                                              actual))
                            except:
                                issues_found += 1

            if alloc_speed_test_found:
                AllocSpeedPerformanceHelper().add_entry(key=key, input_app="alloc_speed_test",
                                                        output_one_malloc_free_wu=output_one_malloc_free_wu,
                                                        output_one_malloc_free_threaded=output_one_malloc_free_threaded)

                job_info[int(key)] = {"output_one_malloc_free_wu": output_one_malloc_free_wu,
                                      "output_one_malloc_free_threaded": output_one_malloc_free_threaded}

                newest_build_number = max(job_info.keys())

                metric_model_name = "AllocSpeedPerformance"
                chart_map = {}
                chart_map["output_one_malloc_free_wu"] = "Best time for 1 malloc/free (WU)"
                chart_map["output_one_malloc_free_threaded"] = "Best time for 1 malloc/free (Threaded)"
                values_to_check = ["output_one_malloc_free_wu", "output_one_malloc_free_threaded"]

                for value_to_check in values_to_check:
                    chart_helper = MetricChartHelper(chart_name=chart_map[value_to_check],
                                                     metric_model_name=metric_model_name)
                    output_data_set = chart_helper.get_output_data_set(output_name=value_to_check)
                    min_value, max_value = output_data_set["min"], output_data_set["max"]
                    actual = job_info[newest_build_number][value_to_check]
                    try:
                        fun_test.test_assert(actual >= min_value,
                                             "Build: {} Attr: {} Min: {} Actual: {}".format(newest_build_number,
                                                                                            value_to_check, min_value,
                                                                                            actual))
                        fun_test.test_assert(actual <= max_value,
                                             "Build: {} Attr: {} Max: {} Actual: {}".format(newest_build_number,
                                                                                            value_to_check, max_value,
                                                                                            actual))
                    except:
                        issues_found += 1
        fun_test.test_assert_expected(expected=0, actual=issues_found, message="Number of issues found")


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
