from lib.system.fun_test import *
from django.apps import apps
from lib.host.lsf_status_server import LsfStatusServer
from web.fun_test.metrics_models import AllocSpeedPerformance, BcopyPerformance, LAST_ANALYTICS_DB_STATUS_UPDATE
from web.fun_test.metrics_models import BcopyFloodDmaPerformance, PkeX25519TlsSoakPerformance, PkeP256TlsSoakPerformance
from web.fun_test.metrics_models import EcPerformance, EcVolPerformance, VoltestPerformance
from web.fun_test.metrics_models import WuSendSpeedTestPerformance, WuDispatchTestPerformance, FunMagentPerformanceTest
from web.fun_test.metrics_models import WuStackSpeedTestPerformance, SoakFunMallocPerformance, \
    SoakClassicMallocPerformance, TeraMarkMultiClusterCryptoPerformance
from web.fun_test.metrics_models import WuLatencyAllocStack, WuLatencyUngated, BootTimePerformance, NuTransitPerformance
from web.fun_test.metrics_models import TeraMarkPkeEcdh256Performance, TeraMarkPkeEcdh25519Performance
from web.fun_test.metrics_models import TeraMarkPkeRsa4kPerformance, TeraMarkPkeRsaPerformance, \
    TeraMarkCryptoPerformance, SoakDmaMemcpyCoherentPerformance, SoakDmaMemcpyNonCoherentPerformance, \
    SoakDmaMemsetPerformance, MetricChart, F1FlowTestPerformance
from web.fun_test.metrics_models import TeraMarkLookupEnginePerformance, FlowTestPerformance, \
    TeraMarkZipDeflatePerformance, TeraMarkZipLzmaPerformance, TeraMarkDfaPerformance, TeraMarkJpegPerformance
from web.fun_test.analytics_models_helper import MetricHelper, invalidate_goodness_cache, MetricChartHelper
from web.fun_test.analytics_models_helper import prepare_status_db
from web.fun_test.models import TimeKeeper
import re
from datetime import datetime
from dateutil.parser import parse

app_config = apps.get_app_config(app_label=MAIN_WEB_APP)

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
                for entry in result["data"]:
                    entry.save()
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
        try:
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
                        self.status = fun_test.PASSED
                        input_iterations = int(match.group("iterations"))
                        input_app = "hw_hsu_test"
                        output_time = int(match.group("seconds"))
                        fun_test.log("iterations: {}, time taken: {}".format(input_iterations, output_time))
                        metrics["input_iterations"] = input_iterations
                        metrics["output_time"] = output_time
                        metrics["output_time_unit"] = "secs"
                        metrics["input_app"] = input_app
                        d = self.metrics_to_dict(metrics=metrics, result=self.status, date_time=date_time)
                        metric_model = app_config.get_metric_models()[model_name]
                        model_obj = MetricHelper(model=metric_model).get_model_obj(**d)
                        result["data"].append(model_obj)
                        match = None

            result["match"] = match_found
            result["passed"] = self.status

        except Exception as ex:
            fun_test.critical(str(ex))

        return result