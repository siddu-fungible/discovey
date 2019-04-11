import os
import django
import json
import random, pytz
from dateutil.parser import parse
import re
from fun_global import *
from datetime import datetime
from web.web_global import PRIMARY_SETTINGS_FILE
from django.apps import apps
from fun_global import get_localized_time
from web.fun_test.settings import COMMON_WEB_LOGGER_NAME
import logging
from fun_settings import MAIN_WEB_APP

logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)
from datetime import datetime, timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", PRIMARY_SETTINGS_FILE)
django.setup()
from web.fun_test.metrics_models import Performance1, PerformanceIkv, PerformanceBlt, VolumePerformance
from web.fun_test.metrics_models import AllocSpeedPerformance
from web.fun_test.site_state import *
from web.fun_test.metrics_models import MetricChart, ShaxPerformance
from web.fun_test.metrics_models import WuLatencyUngated, WuLatencyAllocStack, AllocSpeedPerformance, \
    NuTransitPerformance
from web.fun_test.metrics_models import WuDispatchTestPerformance, WuSendSpeedTestPerformance, HuRawVolumePerformance
from web.fun_test.models import JenkinsJobIdMap
from web.fun_test.metrics_models import VoltestPerformance
from web.fun_test.set_base_line import SetBaseLine

from web.fun_test.analytics_models_helper import MetricChartHelper, BltVolumePerformanceHelper
from web.fun_test.metrics_models import MetricChartStatus, TeraMarkJpegPerformance
from web.fun_test.metrics_models import LastMetricId, MileStoneMarkers, BltVolumePerformance
from web.fun_test.metrics_lib import MetricLib


class MetricHelper(object):
    def __init__(self, model):
        self.model = model

    def delete(self, key):
        entries = self.model.objects.filter(key=key)
        entries.delete()
        '''
        for entry in entries:
            entry.delete()
            entry.save()
        '''

    def clear(self):
        self.model.objects.all().delete()


def get_rounded_time(dt):
    rounded_d = datetime(year=dt.year, month=dt.month, day=dt.day, hour=23, minute=59, second=59)
    rounded_d = get_localized_time(rounded_d)
    return rounded_d


def software_date_to_datetime(software_date):
    m = re.search(r'(\d{4})(\d{2})(\d{2})', str(software_date))
    if m:
        year = int(m.group(1))
        month = int(m.group(2))
        day = int(m.group(3))
        s = "{}-{}-{} {}:{}".format(year, month, day, "00", "01")
        return datetime.strptime(s, "%Y-%m-%d %H:%M")


def get_day_bounds(dt):
    d = get_rounded_time(dt)
    start = d.replace(hour=0, minute=0, second=0)
    end = d.replace(hour=23, minute=59, second=59)
    return start, end


def get_entries_for_day(model, day, data_set):
    bounds = get_day_bounds(day)
    d = {}
    d["input_date_time__range"] = bounds
    inputs = data_set["inputs"]
    for input_name, input_value in inputs.iteritems():
        if d == "input_date_time":
            continue
        d[input_name] = input_value
    result = model.objects.filter(**d)
    return result


def get_possible_values(model_name):
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    metric_model = app_config.get_metric_models()[model_name]
    fields = metric_model._meta.get_fields()
    field_choices = {}
    for field in fields:
        choices = None
        if hasattr(field, "choices"):
            if field.column.startswith("input_") and (not field.column.startswith("input_date_time")):
                all_values = metric_model.objects.values(field.column).distinct()
                choices = []
                for index, value in enumerate(all_values):
                    choices.append(value[field.column])

                field_choices[field.column] = choices
    return field_choices


def get_possible_output_values(model_name):
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    metric_model = app_config.get_metric_models()[model_name]
    fields = metric_model._meta.get_fields()
    field_choices = []
    for field in fields:
        if field.column.startswith("output_"):
            field_choices.append(field.column)
    return field_choices


if __name__ == "__main_memset_datasets__":
    entries = MetricChart.objects.all()
    ml = MetricLib()
    input = {}
    input["input_operation"] = "memset"
    output = {}
    output["reference"] = -1
    output["expected"] = -1
    for entry in entries:
        if entry.chart_name == "DMA soak memcpy coherent (Below 4K)":
            below_4k_data_sets = json.loads(entry.data_sets)
        if entry.chart_name == "DMA soak memcpy coherent (4K-1MB)":
            k_1mb_data_sets = json.loads(entry.data_sets)
        if entry.chart_name == "DMA soak memcpy coherent (Above 1MB)":
            above_1mb_data_sets = json.loads(entry.data_sets)
    for entry in entries:
        if entry.chart_name == "DMA soak memset coherent (Below 4K)" or entry.chart_name == "DMA soak memset non coherent (Below 4K)":
            if "non coherent" in entry.chart_name:
                input["input_coherent"] = False
            else:
                input["input_coherent"] = True
            below_4k_data_sets = ml.set_inputs_data_sets(data_sets=below_4k_data_sets, **input)
            below_4k_data_sets = ml.set_outputs_data_sets(data_sets=below_4k_data_sets, **output)
            print json.dumps(below_4k_data_sets)
            ml.save_data_sets(data_sets=below_4k_data_sets, chart=entry)
        if entry.chart_name == "DMA soak memset coherent (4K-1MB)" or entry.chart_name == "DMA soak memset non coherent (4K-1MB)":
            if "non coherent" in entry.chart_name:
                input["input_coherent"] = False
            else:
                input["input_coherent"] = True
            k_1mb_data_sets = ml.set_inputs_data_sets(data_sets=k_1mb_data_sets, **input)
            k_1mb_data_sets = ml.set_outputs_data_sets(data_sets=k_1mb_data_sets, **output)
            print json.dumps(k_1mb_data_sets)
            ml.save_data_sets(data_sets=k_1mb_data_sets, chart=entry)
        if entry.chart_name == "DMA soak memset coherent (Above 1MB)" or entry.chart_name == "DMA soak memset non coherent (Above 1MB)":
            if "non coherent" in entry.chart_name:
                input["input_coherent"] = False
            else:
                input["input_coherent"] = True
            above_1mb_data_sets = ml.set_inputs_data_sets(data_sets=above_1mb_data_sets, **input)
            above_1mb_data_sets = ml.set_outputs_data_sets(data_sets=above_1mb_data_sets, **output)
            print json.dumps(above_1mb_data_sets)
            ml.save_data_sets(data_sets=above_1mb_data_sets, chart=entry)
            data_sets = json.loads(entry.data_sets)
            for data_set in data_sets:
                if data_set["name"] == "2048KB" or data_set["name"] == "4096KB":
                    ml.delete_data_set(metric_id=entry.metric_id, data_set=data_set)

if __name__ == "__main__":
    flow_types = ["NU_VP_NU_FWD_NFCP", "NU_LE_VP_NU_FW"]
    model_name = "TeraMarkJuniperNetworkingPerformance"
    frame_size_names = {
        64: "64B",
        1500: "1500B",
        362.94: "IMIX"
    }
    outputs = ["output_throughput", "output_pps"]
    chart_names = ["Throughput", "Packets per sec"]
    for flow_type in flow_types:
        for output in outputs:
            data_sets = []
            for frame_size in frame_size_names:
                one_data_set = {}
                one_data_set["inputs"] = {}
                one_data_set["inputs"]["input_flow_type"] = flow_type
                one_data_set["inputs"]["input_number_flows"] = 128000000
                one_data_set["inputs"]["input_offloads"] = False
                one_data_set["inputs"]["input_protocol"] = "UDP"
                one_data_set["inputs"]["input_frame_size"] = frame_size
                one_data_set["name"] = frame_size_names[frame_size]
                one_data_set["output"] = {"name": output, 'min': 0, "max": -1, "expected": -1, "reference": -1}
                data_sets.append(one_data_set)
            metric_id = LastMetricId.get_next_id()
            positive = True
            internal_name = "juniper_" + flow_type + '_' + output
            if "throughput" in output:
                y1_axis_title = "Gbps"
                chart_name = "Throughput"
            else:
                y1_axis_title = "Mpps"
                chart_name = "Packets per sec"
            base_line_date = datetime(year=2019, month=4, day=10, minute=0, hour=0, second=0)
            MetricChart(chart_name=chart_name,
                        metric_id=metric_id,
                        internal_chart_name=internal_name,
                        data_sets=json.dumps(data_sets),
                        leaf=True,
                        description="TBD",
                        owner_info="Amit Surana (amit.surana@fungible.com)",
                        positive=positive,
                        y1_axis_title=y1_axis_title,
                        visualization_unit=y1_axis_title,
                        source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/networking/performance/test_performance_fwd_benchmark.py",
                        metric_model_name=model_name,
                        base_line_date=base_line_date).save()
            mmt = MileStoneMarkers(metric_id=metric_id,
                                   milestone_date=datetime(year=2018, month=9, day=16),
                                   milestone_name="Tape-out")
            mmt.save()
    print "chart creation for NU_VP_NU_FWD_NFCP throughput and pps is done"

if __name__ == "__main__":
    flow_types = ["NU_VP_NU_FWD_NFCP", "NU_LE_VP_NU_FW"]
    model_name = "TeraMarkJuniperNetworkingPerformance"
    frame_size_names = {
        64: "64B",
        1500: "1500B",
        362.94: "IMIX"
    }
    outputs = ["output_latency_avg", "output_latency_min", "output_latency_max"]
    chart_names = ["Latency"]
    for flow_type in flow_types:
        data_sets = []
        for output in outputs:
            if "avg" in output:
                name = "avg"
            elif "min" in output:
                name = "min"
            else:
                name = "max"
            for frame_size in frame_size_names:
                one_data_set = {}
                one_data_set["inputs"] = {}
                one_data_set["inputs"]["input_flow_type"] = flow_type
                one_data_set["inputs"]["input_number_flows"] = 128000000
                one_data_set["inputs"]["input_offloads"] = False
                one_data_set["inputs"]["input_protocol"] = "UDP"
                one_data_set["inputs"]["input_frame_size"] = frame_size
                one_data_set["name"] = frame_size_names[frame_size] + "-" + name
                one_data_set["output"] = {"name": output, 'min': 0, "max": -1, "expected": -1, "reference": -1}
                data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        y1_axis_title = "usecs"
        chart_name = "Latency"
        positive = False
        internal_name = "juniper_" + flow_type + '_' + "output_latency_avg"
        base_line_date = datetime(year=2019, month=4, day=10, minute=0, hour=0, second=0)
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Amit Surana (amit.surana@fungible.com)",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/networking/performance/test_performance_fwd_benchmark.py",
                    metric_model_name=model_name,
                    base_line_date=base_line_date).save()
        mmt = MileStoneMarkers(metric_id=metric_id,
                               milestone_date=datetime(year=2018, month=9, day=16),
                               milestone_name="Tape-out")
        mmt.save()
    print "chart creation for NU_VP_NU_FWD_NFCP latency is done"
