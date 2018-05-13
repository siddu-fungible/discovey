from lib.system.fun_test import *
from lib.host.lsf_status_server import LsfStatusServer
import json
import re
from web.fun_test.analytics_models_helper import MetricChartHelper
from web.fun_test.analytics_models_helper import AllocSpeedPerformanceHelper, MetricHelper
from web.fun_test.metrics_models import EcPerformance

from datetime import datetime

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
                              summary="EC performance",
                              steps="Steps 1")

    def setup(self):
        print("Testcase setup")

    def cleanup(self):
        print("Testcase cleanup")

    def run(self):
        lsf_status_server = LsfStatusServer()
        past_jobs = lsf_status_server.get_past_jobs_by_tag(tag=ALLOC_SPEED_TEST_TAG)
        issues_found = 0
        for past_job in past_jobs:

            ##########################################################
            job_id = past_job["job_id"]
            job_info = lsf_status_server.add_palladium_job_info(job_info=past_job)
            try:
                fun_test.test_assert(job_info, "Valid job info for {}".format(job_id))
            except:
                continue

            dt = job_info["date_time"]
            ############################################################

            lines = job_info["output_text"].split("\n")
            ec_encode_latency_min = ec_encode_latency_max = ec_encode_latency_avg = -1
            ec_encode_throughput_min = ec_encode_throughput_max = ec_encode_throughput_avg = -1
            ec_recovery_latency_min = ec_recovery_latency_max = ec_recovery_latency_avg = -1
            ec_recovery_throughput_min = ec_recovery_throughput_max = ec_recovery_throughput_avg = -1

            stats_found = False
            for line in lines:

                m = re.search(r'({.*})\s+(\S+)\s+\[perf_ec_encode_latency\]', line)
                if m:
                    stats_found = True
                    d = json.loads(m.group(1))
                    ec_encode_latency_min = int(d["min"])
                    ec_encode_latency_max = int(d["max"])
                    ec_encode_latency_avg = int(d["avg"])

                    unit = m.group(2)
                    fun_test.test_assert_expected(actual=unit, expected="nsecs", message="perf_ec_encode_latency unit")

                m = re.search(r'({.*})\s+(\S+)\s+\[perf_ec_encode_throughput\]', line)
                if m:
                    d = json.loads(m.group(1))
                    ec_encode_throughput_min = int(d["min"])
                    ec_encode_throughput_max = int(d["max"])
                    ec_encode_throughput_avg = int(d["avg"])

                    unit = m.group(2)
                    fun_test.test_assert_expected(actual=unit, expected="MBps",
                                                  message="perf_ec_encode_throughput unit")

                m = re.search(r'({.*})\s+(\S+)\s+\[perf_ec_recovery_latency\]', line)
                if m:
                    d = json.loads(m.group(1))
                    ec_recovery_latency_min = int(d["min"])
                    ec_recovery_latency_max = int(d["max"])
                    ec_recovery_latency_avg = int(d["avg"])

                    unit = m.group(2)
                    fun_test.test_assert_expected(actual=unit, expected="nsecs",
                                                  message="perf_ec_recovery_latency unit")

                m = re.search(r'({.*})\s+(\S+)\s+\[perf_ec_recovery_throughput\]', line)
                if m:
                    d = json.loads(m.group(1))
                    ec_recovery_throughput_min = int(d["min"])
                    ec_recovery_throughput_max = int(d["max"])
                    ec_recovery_throughput_avg = int(d["avg"])

                    unit = m.group(2)
                    fun_test.test_assert_expected(actual=unit, expected="MBps",
                                                  message="perf_ec_encode_throughput unit")

            if stats_found:
                MetricHelper(model=EcPerformance).add_entry(input_date_time=dt,
                                                            output_encode_latency_min=ec_encode_latency_min,
                                                            output_encode_latency_max=ec_encode_latency_max,
                                                            output_encode_latency_avg=ec_encode_latency_avg,
                                                            output_encode_throughput_min=ec_encode_throughput_min,
                                                            output_encode_throughput_max=ec_encode_throughput_max,
                                                            output_encode_throughput_avg=ec_encode_throughput_avg,
                                                            output_recovery_latency_min=ec_recovery_latency_min,
                                                            output_recovery_latency_max=ec_recovery_latency_max,
                                                            output_recovery_latency_avg=ec_recovery_latency_avg,
                                                            output_recovery_throughput_min=ec_recovery_throughput_min,
                                                            output_recovery_throughput_max=ec_recovery_throughput_max,
                                                            output_recovery_throughput_avg=ec_recovery_throughput_avg
                                                            )
                chart_name = "EC 8:4 Encode Latency"
                metric_model_name = "EcPerformance"
                model = EcPerformance

                chart_helper = MetricChartHelper(chart_name=chart_name,
                                                 metric_model_name=metric_model_name)
                entry = MetricHelper(model=model).get_recent_entry()

                if entry:
                    '''
                    values_to_check = ["output_encode_latency_min",
                                       "output_encode_latency_max",
                                       "output_encode_latency_avg",
                                       "output_encode_throughput_min",
                                       "output_encode_throughput_max",
                                       "output_encode_throughput_avg",
                                       "output_recovery_latency_min",
                                       "output_recovery_latency_max",
                                       "output_recovery_latency_avg",
                                       "output_recovery_throughput_min",
                                       "output_recovery_throughput_max",
                                       "output_recovery_throughput_avg"]
                    '''
                    values_to_check = ["output_encode_latency_min",
                                       "output_encode_latency_max",
                                       "output_encode_latency_avg"]
                    for value_to_check in values_to_check:
                        output_data_set = chart_helper.get_output_data_set(output_name=value_to_check)
                        expected_min_value, expected_max_value = output_data_set["min"], output_data_set["max"]

                        try:
                            actual = getattr(entry, value_to_check)
                            fun_test.test_assert(actual >= expected_min_value,
                                                 "Build: {} Chart: {} Attr: {} Min: {} Actual: {}".format(job_id,
                                                                                                          chart_name,
                                                                                                          value_to_check,
                                                                                                          expected_min_value,
                                                                                                          actual))
                            fun_test.test_assert(actual <= expected_max_value,
                                                 "Build: {} Chart: {} Attr: {} Max: {} Actual: {}".format(job_id,
                                                                                                          chart_name,
                                                                                                          value_to_check,
                                                                                                          expected_min_value,
                                                                                                          actual))


                        except:
                            issues_found += 1

        fun_test.test_assert_expected(expected=0, actual=issues_found, message="Number of issues found")


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
