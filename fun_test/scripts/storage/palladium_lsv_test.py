from lib.system.fun_test import *
from lib.host.lsf_status_server import LsfStatusServer
import json
import re
from web.fun_test.analytics_models_helper import MetricChartHelper
from web.fun_test.analytics_models_helper import MetricHelper
from web.fun_test.metrics_models import LsvZipCryptoPerformance

from datetime import datetime

LSF_WEB_SERVER_BASE_URL = "http://10.1.20.73:8080"
STORAGE_PERFORMANCE_TEST_TAG = "storage_performance"
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
        past_jobs = lsf_status_server.get_past_jobs_by_tag(tag=STORAGE_PERFORMANCE_TEST_TAG)
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
            metrics = collections.OrderedDict()

            stats_found = False
            for line in lines:

                m = re.search(
                    r'\S\s+(?P<metric_type>\S+):\s+(?P<value>.*)\s+(?P<units>\S+)\s+\[(?P<metric_name>\S+)\]', line)
                if m:
                    metric_type = m.group("metric_type")
                    value = m.group("value")
                    units = m.group("units")
                    metric_name = m.group("metric_name").lower()
                    allowed_prefixes = ["FILTER_TYPE_XTS", "FILTER_TYPE_INFLATE", "FILTER_TYPE_DEFLATE", "lsv_read",
                                        "lsv_write"]
                    allowed_prefixes = [x[: 5].lower() for x in allowed_prefixes]
                    if metric_name[: 5] not in allowed_prefixes:
                        continue
                    try:  # Either a raw value or json value
                        j = json.loads(value)
                        for key, value in j.iteritems():
                            metrics["output_" + metric_name + "_" + key] = value
                    except:
                        metrics["output_" + metric_name] = value
                    try:
                        # if units not in ["mbps", "nsecs", "iops"]:
                        fun_test.simple_assert(units in ["mbps", "nsecs", "iops"], "Unexpected unit {} in line: {}".format(units, line))
                    except Exception as ex:
                        issues_found += 1
                        pass
                    stats_found = True

            i = 0
            print "----"

            for key, _ in metrics.iteritems():
                print key

            d = {}
            d["input_date_time"] = dt
            for key, value in metrics.iteritems():
                d[key] = value

            if stats_found:
                MetricHelper(model=LsvZipCryptoPerformance).add_entry(**d)
            '''
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

        fun_test.test_assert_expected(expected=0, actual=issues_found, message="Number of issues found")

if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
