from lib.system.fun_test import *
from lib.host.lsf_status_server import LsfStatusServer
import json
import re
from web.fun_test.analytics_models_helper import MetricChartHelper
from web.fun_test.analytics_models_helper import AllocSpeedPerformanceHelper, MetricHelper
from web.fun_test.metrics_models import BcopyPerformance, BcopyFloodDmaPerformance

from datetime import datetime

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


def validate():
    pass


class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="bcopy performance",
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

            stats_found = False
            for line in lines:

                m = re.search(
                    r'bcopy \((?P<coherent>\S+),\s+(?P<plain>\S+)\) (?P<size>\S+) (?P<iterations>\d+) times;\s+latency\s+\((?P<latency_units>\S+)\):\s+(?P<latency_json>{.*})\s+\[(?P<latency_perf_name>.*)\];\s+average bandwidth: (?P<average_bandwidth>\S+) \[(?P<average_bandwidth_perf_name>.*)\]',
                    line)

                if m:
                    stats_found = True
                    coherent = "Coherent"
                    if m.group("coherent") != "coherent":
                        coherent = "Non-coherent"
                    plain = "Plain"
                    if  m.group("plain") != "plain":
                        plain = "DMA"
                    size = m.group("size")
                    fun_test.test_assert(size.endswith("KB"), "Size should be in KB")
                    size = int(size.replace("KB", ""))

                    iterations = int(m.group("iterations"))
                    latency_units = m.group("latency_units")
                    try:
                        fun_test.test_assert_expected(expected="nsecs", actual=latency_units,
                                                      message="Latency in nsecs")
                    except:
                        pass
                    latency_json_raw = m.group("latency_json")
                    latency_json = json.loads(latency_json_raw)
                    latency_min = latency_json["min"]
                    latency_max = latency_json["max"]
                    latency_avg = latency_json["avg"]
                    latency_perf_name = m.group("latency_perf_name")
                    average_bandwidth = m.group("average_bandwidth")
                    try:
                        fun_test.test_assert(average_bandwidth.endswith("MBs"), "Avg bw should be MBs")
                        average_bandwidth = int(average_bandwidth.replace("MBs", ""))
                    except:
                        if average_bandwidth.endswith("GBs"):
                            average_bandwidth = int(average_bandwidth.replace("GBs", "")) * 1000

                    average_bandwidth_perf_name = m.group("average_bandwidth_perf_name")

                    if stats_found:
                        MetricHelper(model=BcopyPerformance).add_entry(input_date_time=dt,
                                                                       input_plain=plain,
                                                                       input_coherent=coherent,
                                                                       input_size=size,
                                                                       input_iterations=iterations,
                                                                       output_latency_units=latency_units,
                                                                       output_latency_min=latency_min,
                                                                       output_latency_max=latency_max,
                                                                       output_latency_avg=latency_avg,
                                                                       input_latency_perf_name=latency_perf_name,
                                                                       output_average_bandwith=average_bandwidth,
                                                                       input_average_bandwith_perf_name=average_bandwidth_perf_name
                                                                       )
                    '''
                chart_name = "EC 8:4 Latency"
                metric_model_name = "EcPerformance"
                model = EcPerformance

                chart_helper = MetricChartHelper(chart_name=chart_name,
                                                 metric_model_name=metric_model_name)
                entry = MetricHelper(model=model).get_recent_entry()

                if entry:
                    values_to_check = ["output_encode_latency_min",
                                       "output_encode_latency_max",
                                       "output_encode_latency_avg", 
                                       "output_recovery_latency_min",
                                       "output_recovery_latency_max",
                                       "output_recovery_latency_avg"]
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

                '''
        fun_test.test_assert_expected(expected=0, actual=issues_found, message="Number of issues found")




class FunTestCase2(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="bcopy flood performance",
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

            stats_found = False
            for line in lines:

                m = re.search(
                    r'bcopy flood with dma \((?P<N>\d+)\)\s+(?P<size>\S+);\s+latency\s+\((?P<latency_units>\S+)\):\s+(?P<latency_json>{.*})\s+\[(?P<latency_perf_name>\S+)\];\s+average bandwidth: (?P<average_bandwidth>\S+) \[(?P<average_bandwidth_perf_name>\S+)\]', line)

                if m:
                    stats_found = True
                    n = m.group("N")
                    size = m.group("size")
                    fun_test.test_assert(size.endswith("KB"), "Size should be in KB")
                    size = int(size.replace("KB", ""))
                    latency_units = m.group("latency_units")
                    try:
                        fun_test.test_assert_expected(expected="nsecs", actual=latency_units,
                                                      message="Latency in nsecs")
                    except:
                        pass
                    latency_json_raw = m.group("latency_json")
                    latency_json = json.loads(latency_json_raw)
                    latency_min = latency_json["min"]
                    latency_max = latency_json["max"]
                    latency_avg = latency_json["avg"]
                    latency_perf_name = m.group("latency_perf_name")
                    average_bandwidth = m.group("average_bandwidth")
                    try:
                        fun_test.test_assert(average_bandwidth.endswith("MBs"), "Avg bw should be MBs")
                        average_bandwidth = int(average_bandwidth.replace("MBs", ""))
                    except:
                        if average_bandwidth.endswith("GBs"):
                            average_bandwidth = int(average_bandwidth.replace("GBs", "")) * 1000

                    average_bandwidth_perf_name = m.group("average_bandwidth_perf_name")

                    if stats_found:
                        MetricHelper(model=BcopyFloodDmaPerformance).add_entry(input_date_time=dt,
                                                                        input_n=n,
                                                                       input_size=size,
                                                                       output_latency_units=latency_units,
                                                                       output_latency_min=latency_min,
                                                                       output_latency_max=latency_max,
                                                                       output_latency_avg=latency_avg,
                                                                       input_latency_perf_name=latency_perf_name,
                                                                       output_average_bandwith=average_bandwidth,
                                                                       input_average_bandwith_perf_name=average_bandwidth_perf_name
                                                                       )
                    '''
                chart_name = "EC 8:4 Latency"
                metric_model_name = "EcPerformance"
                model = EcPerformance

                chart_helper = MetricChartHelper(chart_name=chart_name,
                                                 metric_model_name=metric_model_name)
                entry = MetricHelper(model=model).get_recent_entry()

                if entry:
                    values_to_check = ["output_encode_latency_min",
                                       "output_encode_latency_max",
                                       "output_encode_latency_avg", 
                                       "output_recovery_latency_min",
                                       "output_recovery_latency_max",
                                       "output_recovery_latency_avg"]
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

                '''
        fun_test.test_assert_expected(expected=0, actual=issues_found, message="Number of issues found")
if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.add_test_case(FunTestCase2())
    myscript.run()
