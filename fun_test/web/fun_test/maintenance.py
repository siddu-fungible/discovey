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

if __name__ == "__main_juniper_networking__":
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

if __name__ == "__main_juniper_networking__":
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

if __name__ == "__main_memset_BM__":
    entries = MetricChart.objects.all()
    ml = MetricLib()
    for entry in entries:
        if "memset" in entry.chart_name:
            print entry.chart_name
            data_sets = json.loads(entry.data_sets)
            input = {}
            input["input_buffer_memory"] = False
            data_sets = ml.set_inputs_data_sets(data_sets=data_sets, **input)
            ml.save_data_sets(data_sets=data_sets, chart=entry)
            print "added buffer memory"

    internal_chart_names = {"memset_buffer_memory_output_bandwidth_below_4k": "DMA soak memset BM (Below 4K)",
                            "memset_buffer_memory_output_bandwidth_4k_1mb": "DMA soak memset BM (4K-1MB)"}
    internal_frame_sizes = {
        "memset_buffer_memory_output_bandwidth_below_4k": ["64B", "128B", "256B", "512B", "1024B", "2048B"],
        "memset_buffer_memory_output_bandwidth_4k_1mb": ["4096B", "8192B", "16KB"]}
    for internal_chart_name in internal_chart_names:
        chart_name = internal_chart_names[internal_chart_name]
        model_name = "SoakDmaMemsetPerformance"
        metric_id = LastMetricId.get_next_id()
        y1_axis_title = "Gbps"
        positive = True
        base_line_date = datetime(year=2019, month=4, day=11, minute=0, hour=0, second=0)
        data_sets = []
        frame_sizes = internal_frame_sizes[internal_chart_name]
        output = "output_bandwidth"
        for frame_size in frame_sizes:
            one_data_set = {}
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_buffer_memory"] = True
            one_data_set["inputs"]["input_size"] = frame_size
            one_data_set["inputs"]["input_operation"] = "memset"
            one_data_set["name"] = frame_size
            one_data_set["output"] = {"name": output, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Bertrand Serlet (bertrand.serlet@fungible.com)",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    source="https://github.com/fungible-inc/FunOS/blob/4ed61d76485feb65fa6f801d994622737ec6dc9a/apps/soak_dma_memset.c",
                    metric_model_name=model_name,
                    base_line_date=base_line_date).save()
        mmt = MileStoneMarkers(metric_id=metric_id,
                               milestone_date=datetime(year=2018, month=9, day=16),
                               milestone_name="Tape-out")
        mmt.save()
    print "chart creation for BM DMA memset is done"

if __name__ == "__main_delete_network_model__":
    entries = NuTransitPerformance.objects.all().delete()
    print "Deletion Complete"

if __name__ == "__main_work_in_progress__":
    internal_chart_names = ["Networking", "Regex", "teramarks_customer_juniper"]
    ml = MetricLib()
    for internal_chart_name in internal_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        ml.set_work_in_progress(chart=chart, in_progress=True)

if __name__ == "__main_RCNVME__":
    operations = ["sequential_read", "sequential_write", "random_read", "random_write"]
    outputs = ["output_bandwidth", "output_iops", "output_latency_avg"]
    for operation in operations:
        for output in outputs:
            data_sets = []
            positive = True
            name = "SAMSUNG MZQLB1T9HAJR"
            if "bandwidth" in output:
                y1_axis_title = "Mbps"
                chart_name = "Throughput"
            elif "iops" in output:
                y1_axis_title = "ops"
                chart_name = "IOPS"
            else:
                y1_axis_title = "nsecs"
                chart_name = "Latency"
                positive = False
                name = "avg"
            internal_name = "rcnvme_" + operation + '_' + output
            if "sequential" in operation:
                dev_access = "sequential"
            else:
                dev_access = "random"
            if "read" in operation:
                io_type = "RCNVME_TEST_TYPE_RO"
            else:
                io_type = "RCNVME_TEST_TYPE_WO"
            base_line_date = datetime(year=2019, month=4, day=14, minute=0, hour=0, second=0)
            one_data_set = {}
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_io_type"] = io_type
            one_data_set["inputs"]["input_dev_access"] = dev_access
            one_data_set["name"] = name
            one_data_set["output"] = {"name": output, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)
            metric_id = LastMetricId.get_next_id()
            model_name = "TeraMarkRcnvmeReadWritePerformance"
            MetricChart(chart_name=chart_name,
                        metric_id=metric_id,
                        internal_chart_name=internal_name,
                        data_sets=json.dumps(data_sets),
                        leaf=True,
                        description="TBD",
                        owner_info="Raju Vasudevan (raju.vasudevan@fungible.com)",
                        source="https://github.com/fungible-inc/FunOS/blob/ad5f77ba0db25525eed4a3ac4822562b7ccf5d9c/apps/rcnvme_test.c",
                        work_in_progress=False,
                        positive=positive,
                        y1_axis_title=y1_axis_title,
                        visualization_unit=y1_axis_title,
                        metric_model_name=model_name,
                        base_line_date=base_line_date).save()
            mmt = MileStoneMarkers(metric_id=metric_id,
                                   milestone_date=datetime(year=2018, month=9, day=16),
                                   milestone_name="Tape-out")
            mmt.save()
    print "chart creation for RCNVME is done"

if __name__ == "__main_apple_rr_throughput__":
    internal_chart_names = ["apple_rand_read_4kb6vol6ssd_output_bandwidth",
                            "apple_rand_read_4kb6vol6ssd_output_iops"]
    model_name = "BltVolumePerformance"
    fio_read_job_names = ["fio_randread_stripe12"]

    for internal_chart_name in internal_chart_names:
        fio_job_names = []
        if "bandwidth" in internal_chart_name:
            chart_name = "Throughput"
            y1_axis_title = "MBps"
        else:
            chart_name = "IOPS"
            y1_axis_title = "ops"
        if chart_name == "Throughput":
            output_name = "output_read_throughput"
        else:
            output_name = "output_read_iops"
        fio_job_names = fio_read_job_names
        operation = "randread"

        data_sets = []
        name = "Samsung PM1725b"
        for job_name in fio_job_names:
            one_data_set = {}
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_fio_job_name"] = job_name
            one_data_set["inputs"]["input_operation"] = operation
            one_data_set["name"] = name
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        positive = True
        base_line_date = datetime(year=2019, month=4, day=14, minute=0, hour=0, second=0)
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Manu KS (manu.ks@fungible.com)",
                    source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/stripe_vol_fs_perf.py",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
        mmt = MileStoneMarkers(metric_id=metric_id,
                               milestone_date=datetime(year=2018, month=9, day=16),
                               milestone_name="Tape-out")
        mmt.save()
    print "created throughput charts for random read stripe volume"

if __name__ == "__main_apple_rr_latency__":
    internal_chart_names_dict = {"apple_rand_read_4kb6vol6ssd_output_latency": "Latency"}
    model_name = "BltVolumePerformance"
    fio_read_job_names = ["fio_randread_stripe12"]
    y1_axis_title = "usecs"
    output_read_names = ["output_read_avg_latency", "output_read_99_latency", "output_read_99_99_latency"]

    for internal_chart_name in internal_chart_names_dict:
        chart_name = internal_chart_names_dict[internal_chart_name]
        fio_job_name = "fio_randread_stripe12"
        output_names = output_read_names
        operation = "randread"

        data_sets = []
        for output_name in output_names:
            if "_avg_" in output_name:
                name = "avg"
            elif "_99_99_" in output_name:
                name = "99.99%"
            else:
                name = "99%"

            one_data_set = {}
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
            one_data_set["inputs"]["input_operation"] = operation
            one_data_set["name"] = name
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        positive = False
        base_line_date = datetime(year=2019, month=4, day=14, minute=0, hour=0, second=0)
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Manu KS (manu.ks@fungible.com)",
                    source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/stripe_vol_fs_perf.py",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
        mmt = MileStoneMarkers(metric_id=metric_id,
                               milestone_date=datetime(year=2018, month=9, day=16),
                               milestone_name="Tape-out")
        mmt.save()
    print "created latency charts for random read stripe volume"

if __name__ == "__main__":
    old_internal_names = ["HU_NU_NFCP_output_throughput", "HU_NU_NFCP_output_pps", "NU_HU_NFCP_output_throughput",
                          "NU_HU_NFCP_output_pps"]
    for old_name in old_internal_names:
        entry = MetricChart.objects.get(internal_chart_name=old_name)
        if "HU_NU" in old_name:
            if "throughput" in old_name:
                HU_NU_throughput_description = entry.description
            else:
                HU_NU_pps_description = entry.description
        else:
            if "throughput" in old_name:
                NU_HU_throughput_description = entry.description
            else:
                NU_HU_pps_description = entry.description

    internal_chart_names = ["HU_NU_NFCP_1TCP_offloads_disabled_output_throughput",
                            "HU_NU_NFCP_1TCP_offloads_disabled_output_pps",
                            "HU_NU_NFCP_8TCP_offloads_disabled_output_throughput",
                            "HU_NU_NFCP_8TCP_offloads_disabled_output_pps",
                            "NU_HU_NFCP_1TCP_offloads_disabled_output_throughput",
                            "NU_HU_NFCP_1TCP_offloads_disabled_output_pps",
                            "NU_HU_NFCP_8TCP_offloads_disabled_output_throughput",
                            "NU_HU_NFCP_8TCP_offloads_disabled_output_pps"]
    frame_sizes = [800, 1500]
    flow_types = ["HU_NU_NFCP", "NU_HU_NFCP"]
    for internal_chart_name in internal_chart_names:
        positive = True
        base_line_date = datetime(year=2019, month=1, day=26, minute=0, hour=0, second=0)
        model_name = "HuThroughputPerformance"
        if "throughput" in internal_chart_name:
            chart_name = "Throughput"
            y1_axis_title = "Gbps"
            output_name = "output_throughput"
        else:
            chart_name = "Packets per sec"
            y1_axis_title = "Mpps"
            output_name = "output_pps"
        # else:
        #     chart_name = "Latency"
        #     positive = False
        #     y1_axis_title = "usecs"
        #     output_name = "output_latency_avg"
        #     model_name = "HuLatencyPerformance"

        if "1TCP" in internal_chart_name:
            num_flows = 1
        else:
            num_flows = 8

        if "HU_NU_NFCP" in internal_chart_name:
            flow_type = "HU_NU_NFCP"
            output_name = output_name + "_h2n"
        else:
            flow_type = "NU_HU_NFCP"
            output_name = output_name + "_n2h"

        description = "TBD"
        if internal_chart_name == "HU_NU_NFCP_1TCP_offloads_disabled_output_throughput":
            description = HU_NU_throughput_description
        elif internal_chart_name == "HU_NU_NFCP_1TCP_offloads_disabled_output_pps":
            description = HU_NU_pps_description
        elif internal_chart_name == "NU_HU_NFCP_1TCP_offloads_disabled_output_throughput":
            description = NU_HU_throughput_description
        elif internal_chart_name == "NU_HU_NFCP_1TCP_offloads_disabled_output_pps":
            description = NU_HU_pps_description
        data_sets = []
        for frame_size in frame_sizes:
            name = str(frame_size) + "B"
            # if chart_name == "Latency":
            #     name = name + "-avg"
            one_data_set = {}
            one_data_set["name"] = name
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_flow_type"] = flow_type
            one_data_set["inputs"]["input_number_flows"] = num_flows
            one_data_set["inputs"]["input_protocol"] = "TCP"
            one_data_set["inputs"]["input_offloads"] = False
            one_data_set["inputs"]["input_frame_size"] = frame_size
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)

        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description=description,
                    owner_info="Zhuo (George) Liang (george.liang@fungible.com)",
                    source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/networking/funeth/performance.py",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
    print "created charts for the new networking teramarks"
