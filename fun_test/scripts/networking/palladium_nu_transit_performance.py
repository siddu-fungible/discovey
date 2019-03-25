from lib.system.fun_test import *
from django.utils.dateparse import parse_datetime
import json
import re
from web.fun_test.analytics_models_helper import MetricHelper
from web.fun_test.metrics_models import NuTransitPerformance
from datetime import datetime

NU_PERF_JSON = LOGS_DIR + "/nu_transit_performance_data.json"


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
        with open(NU_PERF_JSON, "r") as f:
            contents = f.read()
            data = json.loads(contents)
            print json.dumps(json.loads(contents), indent=4)

            for data_entry in data:
                metrics = collections.OrderedDict()

                # dt = data_entry["timestamp"]
                # s = "2018-05-07 23:52:39.562324-07:00"
                # s = "2018-05-07 23:52:39.562324"

                dt = parse_datetime(data_entry["timestamp"])
                dt = datetime(year=dt.year, month=dt.month, day=dt.day, hour=dt.hour, minute=dt.minute)
                # dt.replace()
                metrics["input_frame_size"] = data_entry["frame_size"]
                metrics["output_latency_avg"] = data_entry["latency_avg"]
                metrics["output_latency_min"] = data_entry["latency_min"]
                metrics["output_latency_max"] = data_entry["latency_max"]
                metrics["output_pps"] = data_entry["pps"]
                metrics["output_throughput"] = float(data_entry["throughput"])
                # metrics["input_throughput"] = float(data_entry["throughput"].replace("Mbps", "").strip())
                metrics["input_mode"] = data_entry["mode"].upper()
                metrics["output_jitter_min"] = data_entry.get("jitter_min", 0)
                metrics["output_jitter_max"] = data_entry.get("jitter_max", 0)
                metrics["output_jitter_avg"] = data_entry.get("jitter_avg", 0)

                for key, _ in metrics.iteritems():
                    print key

                d = {}
                d["input_date_time"] = dt
                for key, value in metrics.iteritems():
                    d[key] = value

                fun_test.log('Addinng Metrics for Date: {}'.format(dt))
                MetricHelper(model=NuTransitPerformance).add_entry(**d)

        # fun_test.test_assert_expected(expected=0, actual=issues_found, message="Number of issues found")

if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
