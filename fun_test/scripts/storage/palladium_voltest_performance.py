from lib.system.fun_test import *
from lib.host.lsf_status_server import LsfStatusServer
import json
import re
from web.fun_test.analytics_models_helper import MetricHelper
from web.fun_test.metrics_models import VoltestPerformance

from datetime import datetime

LSF_WEB_SERVER_BASE_URL = "http://10.1.20.73:8080"
STORAGE_PERFORMANCE_TEST_TAG = "voltest_performance"
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
                              summary="voltest performance",
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
                    r'"(?P<metric_name>\S+)\s+(?P<metric_type>\S+):\s+(?P<value>.*)\s+(?P<units>\S+)\s+\[(?P<metric_id>\S+)\]',
                    line)
                if m:
                    stats_found = True
                    metric_name = m.group("metric_name")
                    metric_type = m.group("metric_type")
                    value = m.group("value")
                    units = m.group("units")
                    metric_id = m.group("metric_id").lower()
                    allowed_metric_names = ["VOL_TYPE_BLK_LSV_write",
                                            "VOL_TYPE_BLK_LSV_read",
                                            "FILTER_TYPE_XTS_ENCRYPT",
                                            "FILTER_TYPE_XTS_DECRYPT",
                                            "FILTER_TYPE_DEFLATE",
                                            "FILTER_TYPE_INFLATE",
                                            "VOL_TYPE_BLK_EC_write",
                                            "VOL_TYPE_BLK_EC_read"]
                    if metric_name not in allowed_metric_names:
                        continue

                    if "andwidth" in metric_type.lower():
                        if "avg_op_bw_mbps" in line:
                            metric_type += "_avg"
                        elif "total_op_bw_mbps":
                            metric_type += "_total"

                    try:  # Either a raw value or json value
                        j = json.loads(value)
                        for key, value in j.iteritems():
                            metrics["output_" + metric_name + "_" + metric_type + "_" + key] = value
                    except Exception as ex:
                        metrics["output_" + metric_name + "_" + metric_type] = value

                    try:
                        fun_test.simple_assert(units in ["mbps", "nsecs", "iops"],
                                               "Unexpected unit {} in line: {}".format(units, line))
                    except Exception as ex:
                        issues_found += 1
                        pass
                    stats_found = True
            print "----"

            for key, _ in metrics.iteritems():
                print key

            d = {}
            d["input_date_time"] = dt
            for key, value in metrics.iteritems():
                d[key] = value

            if stats_found:
                fun_test.log('Addinng Metrics for job-id: {}'.format(job_id))
                MetricHelper(model=VoltestPerformance).add_entry(**d)

        fun_test.test_assert_expected(expected=0, actual=issues_found, message="Number of issues found")

if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
