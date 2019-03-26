from django.apps import apps
from web.fun_test.metrics_models import MetricChart
from web.fun_test.analytics_models_helper import MetricHelper
import re
import collections
from fun_global import RESULTS

app_config = apps.get_app_config(app_label='fun_test')


class MetricParser():
    def parse_it(self, logs, metric_id=None, model_name=None, auto_add_to_db=False, date_time=None):
        result = {}
        if model_name:
            result = self.regex_by_model(model_name=model_name, logs=logs, date_time=date_time)
        else:
            if metric_id:
                chart = MetricChart.objects.get(metric_id=metric_id)
                model_name = chart.metric_model_name
                result = self.regex_by_model(model_name=model_name, logs=logs, date_time=date_time)

        if auto_add_to_db:
            if result["data"]:
                metric_model = app_config.get_metric_models()[model_name]
                for entry in result["data"]:
                    MetricHelper(model=metric_model).add_entry(**entry)
        return result

    def regex_by_model(self, model_name, logs, date_time):
        if "FlowTest" in model_name:
            return self.flow_test(logs=logs, date_time=date_time, model_name=model_name)
        else:
            return {}

    def metrics_to_dict(self, metrics, result, date_time):
        d = {}
        d["input_date_time"] = date_time
        d["status"] = result
        for key, value in metrics.iteritems():
            d[key] = value
        return d

    def flow_test(self, logs, date_time, model_name):
        match_found = False
        result = {}
        result["data"] = []
        d = {}
        metrics = collections.OrderedDict()
        flow_test_passed = False
        match = None
        self.status = RESULTS["FAILED"]
        for line in logs:
            if "PASS libfunq testflow_test" in line:
                flow_test_passed = True
            m = re.search(
                r'Testflow:\s+(?P<iterations>\d+)\s+iterations\s+took\s+(?P<seconds>\d+)\s+seconds',
                line)
            if m:
                match = m
                match_found = True

            if flow_test_passed:
                if match:
                    self.status = RESULTS["PASSED"]
                    input_iterations = int(match.group("iterations"))
                    input_app = "hw_hsu_test"
                    output_time = int(match.group("seconds"))
                    metrics["input_iterations"] = input_iterations
                    metrics["output_time"] = output_time
                    metrics["output_time_unit"] = "secs"
                    metrics["input_app"] = input_app
                    d = self.metrics_to_dict(metrics=metrics, result=self.status, date_time=date_time)
                    result["data"].append(d)
                    match = None

        result["match_found"] = match_found
        result["status"] = self.status == RESULTS["PASSED"]

        return result
