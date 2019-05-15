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
from web.fun_test.models_helper import add_jenkins_job_id_map
from django.utils import timezone
from fun_global import PerfUnit

ml = MetricLib()


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

if __name__ == "__main__network_revamped__":
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

if __name__ == "__main_removed_offloads__":
    internal_chart_names = ["HU_NU_NFCP_1TCP_offloads_disabled_output_throughput",
                            "HU_NU_NFCP_1TCP_offloads_disabled_output_pps",
                            "HU_NU_NFCP_8TCP_offloads_disabled_output_throughput",
                            "HU_NU_NFCP_8TCP_offloads_disabled_output_pps",
                            "NU_HU_NFCP_1TCP_offloads_disabled_output_throughput",
                            "NU_HU_NFCP_1TCP_offloads_disabled_output_pps",
                            "NU_HU_NFCP_8TCP_offloads_disabled_output_throughput",
                            "NU_HU_NFCP_8TCP_offloads_disabled_output_pps"]
    ml = MetricLib()
    for internal_chart_name in internal_chart_names:
        entry = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        ml.remove_attribute_from_data_sets(chart=entry, key="input_offloads")
    print "removed the input offloads from datasets"

if __name__ == "__main_fun_tcp__":
    internal_chart_names = ["funtcp_server_throughput_1tcp", "funtcp_server_throughput_4tcp"]
    frame_size = 1500
    flow_type = "FunTCP_Server_Throughput"
    for internal_chart_name in internal_chart_names:
        positive = True
        base_line_date = datetime(year=2019, month=4, day=18, minute=0, hour=0, second=0)
        model_name = "TeraMarkFunTcpThroughputPerformance"
        y1_axis_title = "Gbps"
        output_name = "output_throughput"
        if "1tcp" in internal_chart_name:
            chart_name = "1 TCP Flow(s)"
            num_flows = 1
        else:
            chart_name = "4 TCP Flow(s)"
            num_flows = 4

        description = "TBD"
        data_sets = []
        name = str(frame_size) + "B"
        # if chart_name == "Latency":
        #     name = name + "-avg"
        one_data_set = {}
        one_data_set["name"] = name
        one_data_set["inputs"] = {}
        one_data_set["inputs"]["input_flow_type"] = flow_type
        one_data_set["inputs"]["input_num_flows"] = num_flows
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
                    owner_info="Onkar Sarmalkar (onkar.sarmalkar@fungible.com)",
                    source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/networking/tcp/performance.py",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
    print "created charts for the FunTCP networking teramarks"

if __name__ == "__main_ipsec_tunnel__":
    internal_chart_names = ["juniper_crypto_single_tunnel_output_throughput", "juniper_crypto_single_tunnel_output_pps",
                            "juniper_crypto_multi_tunnel_output_throughput", "juniper_crypto_multi_tunnel_output_pps"]
    model_name = "JuniperCryptoTunnelPerformance"
    input_algorithm = "AES_GCM"
    description = "TBD"
    positive = True
    base_line_date = datetime(year=2019, month=1, day=26, minute=0, hour=0, second=0)
    for internal_chart_name in internal_chart_names:
        if "throughput" in internal_chart_name:
            chart_name = "Throughput"
            output_name = "output_throughput"
            y1_axis_title = "Gbps"
        else:
            chart_name = "Packets per sec"
            output_name = "output_packets_per_sec"
            y1_axis_title = "Mpps"

        if "single_tunnel" in internal_chart_name:
            num_tunnels = 1
        else:
            num_tunnels = 64

        data_sets = []
        name = "GCM-" + str(num_tunnels) + "tunnel(s)"
        one_data_set = {}
        one_data_set["name"] = name
        one_data_set["inputs"] = {}
        one_data_set["inputs"]["input_num_tunnels"] = num_tunnels
        one_data_set["inputs"]["input_algorithm"] = input_algorithm
        one_data_set["inputs"]["input_pkt_size"] = 354
        one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
        data_sets.append(one_data_set)

        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description=description,
                    owner_info="Suren Madineni (suren.madineni@fungible.com)",
                    source="https://github.com/fungible-inc/FunOS/blob/5c090e8bbe9f6826c9bb1467f5e4642dadbd9d82/apps/cryptotest/crypto_dp_tunnel_perf.c",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
    print "created charts for the IPSEC juniper customer teramarks"

if __name__ == "__main_version_addition__":
    networking_models = ["HuThroughputPerformance", "HuLatencyPerformance", "TeraMarkFunTcpThroughputPerformance",
                         "NuTransitPerformance"]
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    for model in networking_models:
        metric_model = app_config.get_metric_models()[model]
        entries = metric_model.objects.all()
        for entry in entries:
            date_time = timezone.localtime(entry.input_date_time)
            date_time = str(date_time).split(":")
            completion_date = date_time[0] + ":" + date_time[1]
            version = entry.input_version
            add_jenkins_job_id_map(jenkins_job_id=0,
                                   fun_sdk_branch="",
                                   git_commit="",
                                   software_date=0,
                                   hardware_version="",
                                   completion_date=completion_date,
                                   build_properties="", lsf_job_id="",
                                   sdk_version=version)

if __name__ == "__main_add_half_load_latency__":
    internal_chart_names = ["juniper_NU_VP_NU_FWD_NFCP_output_throughput", "juniper_NU_VP_NU_FWD_NFCP_output_pps",
                            "juniper_NU_VP_NU_FWD_NFCP_output_latency_avg"]
    ml = MetricLib()
    for internal_chart_name in internal_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        if chart:
            data_sets = json.loads(chart.data_sets)
            input = {}
            input["input_half_load_latency"] = False
            data_sets = ml.set_inputs_data_sets(data_sets=data_sets, **input)
            ml.save_data_sets(data_sets=data_sets, chart=chart)
            print "added half load latency"

if __name__ == "__main_delete_27th data__":
    model = "TeraMarkJuniperNetworkingPerformance"
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    metric_model = app_config.get_metric_models()[model]
    entries = metric_model.objects.all()
    for entry in entries:
        # date_time = get_localized_time(entry.input_date_time)
        if entry.input_date_time.day >= 27:
            entry.delete()

if __name__ == "__main_changed_num_flows__":
    model_names = ["TeraMarkJuniperNetworkingPerformance", "NuTransitPerformance"]
    entries = MetricChart.objects.all()
    ml = MetricLib()
    for entry in entries:
        if entry.metric_model_name in model_names:
            print json.loads(entry.data_sets)
            data_sets = json.loads(entry.data_sets)
            for data_set in data_sets:
                if "input_number_flows" in data_set["inputs"]:
                    data_set["inputs"]["input_num_flows"] = data_set["inputs"].pop("input_number_flows")
            ml.save_data_sets(data_sets=data_sets, chart=entry)

if __name__ == "__main_12ssd_blt__":
    fio_job_names = ["fio_read_12blt", "fio_randread_12blt"]
    internal_chart_names = ["read_4kb12vol12ssd_nvmetcp_output_bandwidth",
                            "read_4kb12vol12ssd_nvmetcp_output_iops",
                            "rand_read_4kb12vol12ssd_nvmetcp_output_bandwidth",
                            "rand_read_4kb12vol12ssd_nvmetcp_output_iops"]
    model_name = "BltVolumePerformance"
    positive = True
    base_line_date = datetime(year=2019, month=4, day=29, minute=0, hour=0, second=0)
    owner = "Manu KS (manu.ks@fungible.com)"
    source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/12blt_fs_perf.py"

    for internal_chart_name in internal_chart_names:
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

        if "rand_read" in internal_chart_name:
            operation = "randread"
            fio_job_name = "fio_randread_12blt"
        else:
            operation = "read"
            fio_job_name = "fio_read_12blt"

        data_sets = []
        name = "Samsung PM1725b"
        one_data_set = {}
        one_data_set["inputs"] = {}
        one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
        one_data_set["inputs"]["input_operation"] = operation
        one_data_set["name"] = name
        one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
        data_sets.append(one_data_set)

        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info=owner,
                    source=source,
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
    print "created throughput charts for blt volume with 12 ssds"

    internal_chart_names = ["read_4kb12vol12ssd_4_nvmetcp_output_latency",
                            "rand_read_4kb12vol12ssd_4_nvmetcp_output_latency"]
    y1_axis_title = "usecs"
    output_read_names = ["output_read_avg_latency", "output_read_99_latency", "output_read_99_99_latency"]
    chart_name = "Latency"
    positive = False

    for internal_chart_name in internal_chart_names:
        if "rand_read" in internal_chart_name:
            operation = "randread"
            fio_job_name = "fio_randread_12blt"
        else:
            operation = "read"
            fio_job_name = "fio_read_12blt"

        data_sets = []
        for output_name in output_read_names:
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
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info=owner,
                    source=source,
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
    print "created latency charts for blt volume 12 ssds"

if __name__ == "__main_memvol__":
    fio_job_names = ["fio_read_memvol_seq_read", "fio_randread_memvol_rand_read", "fio_write_memvol_seq_write",
                     "fio_randwrite_memvol_rand_write", "fio_readwrite_memvol_seq_read_write",
                     "fio_randrw_memvol_rand_read_write"]
    internal_chart_names = ["memvol_sequential_read_output_bandwidth",
                            "memvol_sequential_read_output_iops",
                            "memvol_random_read_output_bandwidth",
                            "memvol_random_read_output_iops", "memvol_sequential_write_output_bandwidth",
                            "memvol_sequential_write_output_iops", "memvol_random_write_output_bandwidth",
                            "memvol_random_write_output_iops", "memvol_seq_read_write_output_bandwidth",
                            "memvol_seq_read_write_output_iops",
                            "memvol_random_read_write_output_bandwidth", "memvol_random_read_write_output_iops"]
    model_name = "BltVolumePerformance"
    positive = True
    base_line_date = datetime(year=2019, month=4, day=27, minute=0, hour=0, second=0)
    owner = "Radhika Naik (radhika.naik@fungible.com)"
    source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/memvol_fs_perf_updated.py"

    for internal_chart_name in internal_chart_names:
        if "bandwidth" in internal_chart_name:
            chart_name = "Throughput"
            y1_axis_title = "MBps"
            if "seq_read_write" in internal_chart_name:
                operation = "readwrite"
                fio_job_name = "fio_readwrite_memvol_seq_read_write"
                output_names = ["output_read_throughput", "output_write_throughput"]
            elif "random_read_write" in internal_chart_name:
                operation = "randrw"
                fio_job_name = "fio_randrw_memvol_rand_read_write"
                output_names = ["output_read_throughput", "output_write_throughput"]
            elif "sequential_read" in internal_chart_name:
                operation = "read"
                fio_job_name = "fio_read_memvol_seq_read"
                output_names = ["output_read_throughput"]
            elif "random_read" in internal_chart_name:
                operation = "randread"
                fio_job_name = "fio_randread_memvol_rand_read"
                output_names = ["output_read_throughput"]
            elif "sequential_write" in internal_chart_name:
                operation = "write"
                fio_job_name = "fio_write_memvol_seq_write"
                output_names = ["output_write_throughput"]
            elif "random_write" in internal_chart_name:
                operation = "randwrite"
                fio_job_name = "fio_randwrite_memvol_rand_write"
                output_names = ["output_write_throughput"]
        else:
            chart_name = "IOPS"
            y1_axis_title = "ops"
            if "seq_read_write" in internal_chart_name:
                operation = "readwrite"
                fio_job_name = "fio_readwrite_memvol_seq_read_write"
                output_names = ["output_read_iops", "output_write_iops"]
            elif "random_read_write" in internal_chart_name:
                operation = "randrw"
                fio_job_name = "fio_randrw_memvol_rand_read_write"
                output_names = ["output_read_iops", "output_write_iops"]
            elif "sequential_read" in internal_chart_name:
                operation = "read"
                fio_job_name = "fio_read_memvol_seq_read"
                output_names = ["output_read_iops"]
            elif "random_read" in internal_chart_name:
                operation = "randread"
                fio_job_name = "fio_randread_memvol_rand_read"
                output_names = ["output_read_iops"]
            elif "sequential_write" in internal_chart_name:
                operation = "write"
                fio_job_name = "fio_write_memvol_seq_write"
                output_names = ["output_write_iops"]
            elif "random_write" in internal_chart_name:
                operation = "randwrite"
                fio_job_name = "fio_randwrite_memvol_rand_write"
                output_names = ["output_write_iops"]

        data_sets = []
        for output_name in output_names:
            if operation == "randrw":
                if "read" in output_name:
                    name = "randread"
                else:
                    name = "randwrite"
            elif operation == "readwrite":
                if "read" in output_name:
                    name = "read"
                else:
                    name = "write"
            else:
                name = operation
            one_data_set = {}
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
            one_data_set["inputs"]["input_operation"] = operation
            one_data_set["name"] = name
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)

        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info=owner,
                    source=source,
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
    print "created throughput and iops charts for memvol"

    internal_chart_names = ["memvol_sequential_read_output_latency_avg",
                            "memvol_random_read_output_latency_avg", "memvol_sequential_write_output_latency_avg",
                            "memvol_random_write_output_latency_avg",
                            "memvol_seq_read_write_output_latency_avg", "memvol_random_read_write_output_latency_avg"]
    y1_axis_title = "usecs"
    output_read_names = ["output_read_avg_latency", "output_read_99_latency", "output_read_99_99_latency"]
    output_write_names = ["output_write_avg_latency", "output_write_99_latency", "output_write_99_99_latency"]
    chart_name = "Latency"
    positive = False

    for internal_chart_name in internal_chart_names:
        if "seq_read_write" in internal_chart_name:
            operation = "readwrite"
            fio_job_name = "fio_readwrite_memvol_seq_read_write"
            output_names = output_read_names + output_write_names
        elif "random_read_write" in internal_chart_name:
            operation = "randrw"
            fio_job_name = "fio_randrw_memvol_rand_read_write"
            output_names = output_read_names + output_write_names
        elif "sequential_read" in internal_chart_name:
            operation = "read"
            fio_job_name = "fio_read_memvol_seq_read"
            output_names = output_read_names
        elif "random_read" in internal_chart_name:
            operation = "randread"
            fio_job_name = "fio_randread_memvol_rand_read"
            output_names = output_read_names
        elif "sequential_write" in internal_chart_name:
            operation = "write"
            fio_job_name = "fio_write_memvol_seq_write"
            output_names = output_write_names
        elif "random_write" in internal_chart_name:
            operation = "randwrite"
            fio_job_name = "fio_randwrite_memvol_rand_write"
            output_names = output_write_names

        data_sets = []
        for output_name in output_names:
            if "_avg_" in output_name:
                name = "avg"
            elif "_99_99_" in output_name:
                name = "99.99%"
            else:
                name = "99%"

            if operation == "randrw":
                if "read" in output_name:
                    name = "randread-" + name
                else:
                    name = "randwrite-" + name
            elif operation == "readwrite":
                if "read" in output_name:
                    name = "read-" + name
                else:
                    name = "write-" + name

            one_data_set = {}
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
            one_data_set["inputs"]["input_operation"] = operation
            one_data_set["name"] = name
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)

        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info=owner,
                    source=source,
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
    print "created latency charts for memvol"

if __name__ == "__main__half_load_charts__":
    internal_chart_names = ["juniper_NU_LE_VP_NU_FW_output_throughput", "juniper_NU_LE_VP_NU_FW_output_pps",
                            "juniper_NU_LE_VP_NU_FW_output_latency_avg"]
    ml = MetricLib()
    for internal_chart_name in internal_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        if chart:
            data_sets = json.loads(chart.data_sets)
            input = {}
            input["input_half_load_latency"] = False
            data_sets = ml.set_inputs_data_sets(data_sets=data_sets, **input)
            ml.save_data_sets(data_sets=data_sets, chart=chart)
            print "added half load latency"

    entry = MetricChart.objects.get(internal_chart_name="juniper_NU_LE_VP_NU_FW_output_latency_avg")
    if entry:
        data_sets = json.loads(entry.data_sets)
        input = {}
        input["input_half_load_latency"] = True
        data_sets = ml.set_inputs_data_sets(data_sets=data_sets, **input)
        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name='Latency - Half Load',
                    metric_id=metric_id,
                    internal_chart_name="juniper_NU_LE_VP_NU_FW_output_half_load_latency_avg",
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description=entry.description,
                    owner_info=entry.owner_info,
                    source=entry.source,
                    positive=False,
                    y1_axis_title='usecs',
                    visualization_unit='usecs',
                    metric_model_name=entry.metric_model_name,
                    base_line_date=entry.base_line_date,
                    work_in_progress=False).save()

    entry = MetricChart.objects.get(internal_chart_name="juniper_NU_VP_NU_FWD_NFCP_output_latency_avg")
    if entry:
        data_sets = json.loads(entry.data_sets)
        input = {}
        input["input_half_load_latency"] = True
        data_sets = ml.set_inputs_data_sets(data_sets=data_sets, **input)
        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name='Latency - Half Load',
                    metric_id=metric_id,
                    internal_chart_name="juniper_NU_VP_NU_FWD_NFCP_output_half_load_latency_avg",
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description=entry.description,
                    owner_info=entry.owner_info,
                    source=entry.source,
                    positive=False,
                    y1_axis_title='usecs',
                    visualization_unit='usecs',
                    metric_model_name=entry.metric_model_name,
                    base_line_date=entry.base_line_date,
                    work_in_progress=False).save()

if __name__ == "__main_us_to_usecs__":
    model = "TeraMarkJuniperNetworkingPerformance"
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    metric_model = app_config.get_metric_models()[model]
    entries = metric_model.objects.all()
    for entry in entries:
        if entry.output_latency_avg_unit == "us":
            print entry
            entry.output_latency_avg_unit = "usecs"
            entry.output_latency_max_unit = "usecs"
            entry.output_latency_min_unit = "usecs"
            entry.output_jitter_min_unit = "usecs"
            entry.output_jitter_max_unit = "usecs"
            entry.output_jitter_avg_unit = "usecs"
            entry.save()

if __name__ == "__main_fix_units__":
    model = "TeraMarkJuniperNetworkingPerformance"
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    metric_model = app_config.get_metric_models()[model]
    entries = metric_model.objects.all()
    for entry in entries:
        if entry.input_flow_type == "NU_VP_NU_FWD_NFCP" and entry.input_date_time.day == 2 and entry.input_date_time.month == 5 and entry.input_date_time.year == 2019:
            print entry
            entry.output_throughput_unit = "Gbps"
            entry.output_pps_unit = "Mpps"
            entry.save()

if __name__ == "__main_rcnvme_12drives__":
    operations = ["sequential_read", "sequential_write", "random_read", "random_write"]
    outputs = ["output_bandwidth", "output_iops", "output_latency_avg"]
    for operation in operations:
        for output in outputs:
            data_sets = []
            positive = True
            if "bandwidth" in output:
                y1_axis_title = "Mbps"
                chart_name = "Throughput"
                name = "throughput"
            elif "iops" in output:
                y1_axis_title = "ops"
                chart_name = "IOPS"
                name = "iops"
            else:
                y1_axis_title = "nsecs"
                chart_name = "Latency"
                positive = False
                name = "avg"
            internal_name = "rcnvme_12_" + operation + '_' + output
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
            model_name = "TeraMarkRcnvmeReadWriteAllPerformance"
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
    print "chart creation for RCNVME 12 drives is done"

if __name__ == "__main_inspur_charts__":
    model_name = "BltVolumePerformance"
    base_line_date = datetime(year=2019, month=5, day=2, minute=0, hour=0, second=0)
    owner = "Ravi Hulle (ravi.hulle@fungible.com)"
    source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/ec_inspur_fs_teramark.py"
    outputs = ["output_bandwidth", "output_iops", "output_latency"]
    internal_chart_names = ["inspur_rand_read_write_8k_block_output_bandwidth",
                            "inspur_rand_read_write_8k_block_output_latency",
                            "inspur_rand_read_write_8k_block_output_iops"]
    fio_job_name = "inspur_8k_random_read_write_vdbench"
    for internal_chart_name in internal_chart_names:
        data_sets = []
        positive = True
        if "bandwidth" in internal_chart_name:
            y1_axis_title = "MBps"
            chart_name = "Throughput"
            output_names = ["output_read_throughput", "output_write_throughput"]
        elif "iops" in internal_chart_name:
            y1_axis_title = "ops"
            chart_name = "IOPS"
            output_names = ["output_read_iops", "output_write_iops"]
        else:
            y1_axis_title = "usecs"
            chart_name = "Latency"
            positive = False
            output_names = ["output_read_avg_latency", "output_write_avg_latency"]
        for output_name in output_names:
            if "read" in output_name:
                name = "read"
            else:
                name = "write"
            if "latency" in output_name:
                name += "-avg"
            one_data_set = {}
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
            one_data_set["name"] = name
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info=owner,
                    source=source,
                    work_in_progress=False,
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date).save()
    print "chart creation for inspur single f1 is done"

if __name__ == "__main_HBM__":
    internal_chart_names = ["juniper_NU_VP_NU_FWD_NFCP_output_throughput", "juniper_NU_VP_NU_FWD_NFCP_output_pps",
                            "juniper_NU_VP_NU_FWD_NFCP_output_latency_avg",
                            "juniper_NU_VP_NU_FWD_NFCP_output_half_load_latency_avg",
                            "juniper_NU_LE_VP_NU_FW_output_throughput", "juniper_NU_LE_VP_NU_FW_output_pps",
                            "juniper_NU_LE_VP_NU_FW_output_latency_avg",
                            "juniper_NU_LE_VP_NU_FW_output_half_load_latency_avg"]
    ml = MetricLib()
    for internal_chart_name in internal_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        if chart:
            data_sets = json.loads(chart.data_sets)
            input = {}
            input["input_memory"] = "HBM"
            data_sets = ml.set_inputs_data_sets(data_sets=data_sets, **input)
            ml.save_data_sets(data_sets=data_sets, chart=chart)
            print "added HBM memory {}".format(chart.chart_name)

if __name__ == "__main_opeartion_lookups__":
    internal_chart_names = ["HT HBM non-coherent - FP HBM non-coherent", "HT HBM coherent - FP HBM coherent",
                            "HT DDR non-coherent - FP DDR non-coherent", "HT DDR coherent - FP DDR coherent",
                            "TCAM"]
    ml = MetricLib()
    for internal_chart_name in internal_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        if chart:
            data_sets = json.loads(chart.data_sets)
            input = {}
            input["input_operation"] = "lookups"
            data_sets = ml.set_inputs_data_sets(data_sets=data_sets, **input)
            ml.save_data_sets(data_sets=data_sets, chart=chart)
            print "added lookups operation {}".format(chart.chart_name)

if __name__ == "__main_unit_fix__":
    model = "TeraMarkJuniperNetworkingPerformance"
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    metric_model = app_config.get_metric_models()[model]
    entries = metric_model.objects.all()
    for entry in entries:
        # date_time = get_localized_time(entry.input_date_time)
        if entry.input_date_time.day == 5 and entry.input_date_time.year == 2019 and entry.input_date_time.month == 5:
            print entry
            entry.output_throughput_unit = "Mbps"
            entry.output_pps_unit = "pps"
            entry.save()

if __name__ == "__main_created_DDR_FW__":
    model = "TeraMarkJuniperNetworkingPerformance"
    ml = MetricLib()
    entries = MetricChart.objects.filter(metric_model_name=model)
    for entry in entries:
        if "NU_LE_VP_NU_FW" in entry.internal_chart_name:
            print entry
            data_sets = json.loads(entry.data_sets)
            input = {}
            input["input_memory"] = "DDR"
            data_sets = ml.set_inputs_data_sets(data_sets=data_sets, **input)
            base_line_date = datetime(year=2019, month=5, day=5, minute=0, hour=0, second=0)
            metric_id = LastMetricId.get_next_id()
            index = entry.internal_chart_name.find('output')
            internal_name = entry.internal_chart_name[:index] + 'DDR_' + entry.internal_chart_name[index:]
            MetricChart(chart_name=entry.chart_name,
                        metric_id=metric_id,
                        internal_chart_name=internal_name,
                        data_sets=json.dumps(data_sets),
                        leaf=True,
                        description=entry.description,
                        owner_info=entry.owner_info,
                        positive=entry.positive,
                        y1_axis_title=entry.y1_axis_title,
                        visualization_unit=entry.visualization_unit,
                        source=entry.source,
                        metric_model_name=entry.metric_model_name,
                        base_line_date=base_line_date).save()
    print "added charts for DDR flow based firewall"

if __name__ == "__main_num_hosts__":
    model_name = "HuThroughputPerformance"
    charts = MetricChart.objects.filter(metric_model_name=model_name)
    ml = MetricLib()
    for chart in charts:
        data_sets = json.loads(chart.data_sets)
        input = {}
        input["input_num_hosts"] = 1
        data_sets = ml.set_inputs_data_sets(data_sets=data_sets, **input)
        ml.save_data_sets(data_sets=data_sets, chart=chart)
        print "added number of hosts field for {}".format(chart.chart_name)

if __name__ == "__main__durable_ec_comp__":
    internal_chart_names = ["read_4kb1vol12ssd_durable_volume_ec_output_bandwidth",
                            "read_4kb1vol12ssd_durable_volume_ec_output_iops",
                            "read_4kb1vol12ssd_durable_volume_ec_4_output_latency",
                            "rand_read_4kb1vol12ssd_durable_volume_ec_output_bandwidth",
                            "rand_read_4kb1vol12ssd_durable_volume_ec_output_iops",
                            "rand_read_4kb1vol12ssd_durable_volume_ec_4_output_latency"]
    model_name = "BltVolumePerformance"
    fio_read_job_names = ["ec_fio_25G_read_1", "ec_fio_25G_read_50", "ec_fio_25G_read_80"]
    fio_rand_read_job_names = ["ec_fio_25G_randread_1", "ec_fio_25G_randread_50", "ec_fio_25G_randread_80"]

    for internal_chart_name in internal_chart_names:
        fio_job_names = []
        positive = True
        if "bandwidth" in internal_chart_name:
            chart_name = "Throughput"
            y1_axis_title = "MBps"
        elif "iops" in internal_chart_name:
            chart_name = "IOPS"
            y1_axis_title = "ops"
        else:
            chart_name = "Latency"
            y1_axis_title = "usecs"

        if chart_name == "Throughput":
            output_name = "output_read_throughput"
        elif chart_name == "IOPS":
            output_name = "output_read_iops"
        else:
            output_name = "output_read_avg_latency"
            positive = False
        if "rand_read" in internal_chart_name:
            fio_job_names = fio_rand_read_job_names
            operation = "randread"
        else:
            fio_job_names = fio_read_job_names
            operation = "read"

        data_sets = []
        for job_name in fio_job_names:
            if "80" in job_name:
                name = "80%"
            elif "50" in job_name:
                name = "50%"
            else:
                name = "1%"
            if chart_name == "Latency":
                name += "-avg"
            one_data_set = {}
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_fio_job_name"] = job_name
            one_data_set["inputs"]["input_operation"] = operation
            one_data_set["name"] = name
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        base_line_date = datetime(year=2019, month=5, day=5, minute=0, hour=0, second=0)
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Aamir Shaikh (aamir.shaikh@fungible.com)",
                    source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/ec_volume_fs_comp_perf.py",
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
    print "created throughput, iops and latency charts for 12 ssd read and random read durable volume ec storage"

if __name__ == "__main_juniper_tls__":
    internal_chart_names = ["juniper_tls_output_throughput", "juniper_tls_output_pps"]
    chart_name = "Throughput"
    model_name = "JuniperTlsTunnelPerformance"
    num_tunnels = [1, 32, 64]
    base_line_date = datetime(year=2019, month=5, day=5, minute=0, hour=0, second=0)
    for internal_chart_name in internal_chart_names:
        if "throughput" in internal_chart_name:
            chart_name = "Throughput"
            output_name = "output_throughput"
            y1_axis_title = "Gbps"
        else:
            chart_name = "Packets per sec"
            output_name = "output_packets_per_sec"
            y1_axis_title = "Mpps"

        data_sets = []
        for num_tunnel in num_tunnels:
            name = str(num_tunnel) + "tunnel(s)"
            one_data_set = {}
            one_data_set["name"] = name
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_num_tunnels"] = num_tunnel
            one_data_set["inputs"]["input_algorithm"] = "AES_GCM"
            one_data_set["inputs"]["input_pkt_size"] = 356
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)

        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Fabrice Ferino (fabrice.ferino@fungible.com)",
                    source="https://github.com/fungible-inc/FunOS/blob/master/apps/tls_dp_tunnel_perf.c",
                    positive=True,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
    print "created charts for the TLS juniper customer teramarks"

if __name__ == "__main_memcpy_threshold__":
    internal_chart_name = "memcpy_threshold"
    model_name = "SoakDmaMemcpyThresholdPerformance"
    chart_name = "DMA memcpy vs. VP memcpy"
    y1_axis_title = "KB"
    base_line_date = datetime(year=2019, month=5, day=5, minute=0, hour=0, second=0)
    data_sets = []
    one_data_set = {}
    one_data_set["name"] = "threshold"
    one_data_set["inputs"] = {}
    one_data_set["output"] = {"name": "output_threshold", 'min': 0, "max": -1, "expected": 4, "reference": -1}
    data_sets.append(one_data_set)
    metric_id = LastMetricId.get_next_id()
    MetricChart(chart_name=chart_name,
                metric_id=metric_id,
                internal_chart_name=internal_chart_name,
                data_sets=json.dumps(data_sets),
                leaf=True,
                description="VP-based memcpy is faster for small sizes and DMA-based memcpy wins for large sizes. This metric defines the threshold above which DMA memcpy always wins.",
                owner_info="Bertrand Serlet (bertrand.serlet@fungible.com)",
                source="https://github.com/fungible-inc/FunOS/blob/master/apps/misc_app.c",
                positive=False,
                y1_axis_title=y1_axis_title,
                visualization_unit=y1_axis_title,
                metric_model_name=model_name,
                base_line_date=base_line_date,
                work_in_progress=False).save()

if __name__ == "__main_2hosts__":
    internal_chart_names = ["HU_NU_NFCP_8TCP_offloads_disabled_output_throughput",
                            "HU_NU_NFCP_8TCP_offloads_disabled_output_pps",
                            "NU_HU_NFCP_8TCP_offloads_disabled_output_throughput",
                            "NU_HU_NFCP_8TCP_offloads_disabled_output_pps"]
    for internal_chart_name in internal_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        if chart:
            index = chart.internal_chart_name.find('output')
            internal_name = chart.internal_chart_name[:index] + '2hosts_' + chart.internal_chart_name[index:]
            if "HU_NU" in internal_chart_name:
                flow_type = "HU_NU_NFCP"
                output_name = chart.internal_chart_name[index:] + '_h2n'
            else:
                flow_type = "NU_HU_NFCP"
                output_name = chart.internal_chart_name[index:] + '_n2h'
            data_sets = []
            one_data_set = {}
            one_data_set["name"] = "1500B"
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_number_flows"] = 8
            one_data_set["inputs"]["input_flow_type"] = flow_type
            one_data_set["inputs"]["input_frame_size"] = 1500
            one_data_set["inputs"]["input_protocol"] = "TCP"
            one_data_set["inputs"]["input_num_hosts"] = 2
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)

            metric_id = LastMetricId.get_next_id()
            MetricChart(chart_name=chart.chart_name,
                        metric_id=metric_id,
                        internal_chart_name=internal_name,
                        data_sets=json.dumps(data_sets),
                        leaf=True,
                        description=chart.description,
                        owner_info=chart.owner_info,
                        source=chart.source,
                        positive=True,
                        y1_axis_title=chart.y1_axis_title,
                        visualization_unit=chart.y1_axis_title,
                        metric_model_name=chart.metric_model_name,
                        base_line_date=chart.base_line_date,
                        work_in_progress=False).save()
    print "added 2hosts charts"


def set_internal_name(metrics):
    chart = MetricChart.objects.get(internal_chart_name=metrics["name"])
    metrics["name"] += "_S1"
    if chart.leaf:
        data_sets = json.loads(chart.data_sets)
        input = {}
        input["input_platform"] = FunPlatform.S1
        data_sets = ml.set_inputs_data_sets(data_sets=data_sets, **input)
        ml.clone_chart(old_chart=chart, internal_chart_name=metrics["name"], data_sets=data_sets)
    else:
        ml.clone_chart(old_chart=chart, internal_chart_name=metrics["name"], data_sets=json.loads(chart.data_sets))
        for child in metrics["children"]:
            set_internal_name(child)
    return metrics


if __name__ == "__main_S1__":
    charts = MetricChart.objects.all()
    for chart in charts:
        if chart.leaf:
            data_sets = json.loads(chart.data_sets)
            input = {}
            input["input_platform"] = FunPlatform.F1
            data_sets = ml.set_inputs_data_sets(data_sets=data_sets, **input)
            ml.save_data_sets(data_sets=data_sets, chart=chart)
            print "added platform for {}".format(chart.chart_name)
    with open(METRICS_BASE_DATA_FILE, "r") as f:
        metrics = json.load(f)
        for metric in metrics:
            if metric["label"] == "F1":
                f1_metrics = metric["children"]
                for f1_metric in f1_metrics:
                    if f1_metric["label"] == "FunOS":
                        funos_metrics = f1_metric
                        break
        result = set_internal_name(funos_metrics)
        print json.dumps(result)

if __name__ == "__main_delete__":
    model = "HuThroughputPerformance"
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    metric_model = app_config.get_metric_models()[model]
    entries = metric_model.objects.filter(input_flow_type="HU_HU_NFCP")
    print len(entries)
    entries.delete()
    model = "HuLatencyPerformance"
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    metric_model = app_config.get_metric_models()[model]
    entries = metric_model.objects.filter(input_flow_type="HU_HU_NFCP")
    print len(entries)
    entries.delete()
    print "got entries"

if __name__ == "__main_HU_HU__":
    internal_chart_names = ["HU_HU_NFCP_8TCP_offloads_disabled_output_throughput",
                            "HU_HU_NFCP_8TCP_offloads_disabled_output_pps",
                            "HU_HU_NFCP_1TCP_offloads_disabled_output_throughput",
                            "HU_HU_NFCP_1TCP_offloads_disabled_output_pps"]
    copy_from = ["NU_HU_NFCP_8TCP_offloads_disabled_2hosts_output_throughput",
                 "NU_HU_NFCP_8TCP_offloads_disabled_2hosts_output_pps"]
    flow_type = "HU_HU_NFCP"
    frame_size = 1500

    for internal_chart_name in internal_chart_names:
        if "throughput" in internal_chart_name:
            output_name = "output_throughput_h2h"
            chart_name = "Throughput"
            copy_from = "NU_HU_NFCP_8TCP_offloads_disabled_2hosts_output_throughput"
        else:
            output_name = "output_pps_h2h"
            chart_name = "Packets per sec"
            copy_from = "NU_HU_NFCP_8TCP_offloads_disabled_2hosts_output_pps"
        chart = MetricChart.objects.get(internal_chart_name=copy_from)

        if "8TCP" in internal_chart_name:
            num_flows = 8
        else:
            num_flows = 1

        data_sets = json.loads(chart.data_sets)
        input = {}
        input["input_flow_type"] = "HU_HU_NFCP"
        input["input_number_flows"] = num_flows
        input["input_num_hosts"] = 1
        data_sets = ml.set_inputs_data_sets(data_sets=data_sets, **input)
        data_sets[0]["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart.chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description=chart.description,
                    owner_info=chart.owner_info,
                    source=chart.source,
                    positive=True,
                    y1_axis_title=chart.y1_axis_title,
                    visualization_unit=chart.y1_axis_title,
                    metric_model_name=chart.metric_model_name,
                    base_line_date=chart.base_line_date,
                    work_in_progress=False).save()
    print "Added new HU HU NFCP charts"

if __name__ == "__main_apple__":
    internal_chart_names = ["apple_rand_read_srsw_tcp_output_bandwidth",
                            "apple_rand_read_srsw_tcp_output_iops"]
    model_name = "BltVolumePerformance"
    base_line_date = datetime(year=2019, month=5, day=10, minute=0, hour=0, second=0)

    for internal_chart_name in internal_chart_names:
        if "bandwidth" in internal_chart_name:
            chart_name = "Throughput"
            y1_axis_title = "MBps"
            output_name = "output_read_throughput"
            name = "throughput"
        else:
            chart_name = "IOPS"
            y1_axis_title = "ops"
            output_name = "output_read_iops"
            name = "iops"
        operation = "randread"

        data_sets = []
        one_data_set = {}
        one_data_set["inputs"] = {}
        one_data_set["inputs"]["input_fio_job_name"] = "fio_randread_apple_single_tcp"
        one_data_set["inputs"]["input_platform"] = "F1"
        one_data_set["inputs"]["input_operation"] = operation
        one_data_set["name"] = name
        one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
        data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        positive = True
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Manu KS (manu.ks@fungible.com)",
                    source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/apple_tcp_fs_perf.py",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
    print "added apple charts"
    internal_name = "apple_rand_read_4kb6vol6ssd_output_latency"
    chart = MetricChart.objects.get(internal_chart_name=internal_name)
    data_sets = json.loads(chart.data_sets)
    for data_set in data_sets:
        data_set["inputs"]["input_fio_job_name"] = "fio_randread_apple_single_tcp"
        data_set["output"]["min"] = 0
        data_set["output"]["max"] = -1
        data_set["output"]["expected"] = -1
        data_set["output"]["reference"] = -1
    metric_id = LastMetricId.get_next_id()
    MetricChart(chart_name=chart.chart_name,
                metric_id=metric_id,
                internal_chart_name="apple_rand_read_srsw_tcp_output_latency",
                data_sets=json.dumps(data_sets),
                leaf=True,
                description="TBD",
                owner_info="Manu KS (manu.ks@fungible.com)",
                source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/apple_tcp_fs_perf.py",
                positive=False,
                y1_axis_title=chart.y1_axis_title,
                visualization_unit=chart.y1_axis_title,
                metric_model_name=model_name,
                base_line_date=base_line_date,
                work_in_progress=False).save()

if __name__ == "__main_tls_3264__":
    internal_chart_names = ["juniper_tls_32_output_throughput", "juniper_tls_32_output_pps",
                            "juniper_tls_64_output_throughput", "juniper_tls_64_output_pps"]
    model_name = "JuniperTlsTunnelPerformance"
    base_line_date = datetime(year=2019, month=5, day=5, minute=0, hour=0, second=0)
    for internal_chart_name in internal_chart_names:
        if "throughput" in internal_chart_name:
            chart_name = "Throughput"
            output_name = "output_throughput"
            y1_axis_title = "Gbps"
        else:
            chart_name = "Packets per sec"
            output_name = "output_packets_per_sec"
            y1_axis_title = "Mpps"
        if "32" in internal_chart_name:
            num_tunnel = 32
        else:
            num_tunnel = 64

        data_sets = []
        name = str(num_tunnel) + "tunnel(s)"
        one_data_set = {}
        one_data_set["name"] = name
        one_data_set["inputs"] = {}
        one_data_set["inputs"]["input_num_tunnels"] = num_tunnel
        one_data_set["inputs"]["input_algorithm"] = "AES_GCM"
        one_data_set["inputs"]["input_platform"] = "F1"
        one_data_set["inputs"]["input_pkt_size"] = 354
        one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
        data_sets.append(one_data_set)

        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Fabrice Ferino (fabrice.ferino@fungible.com)",
                    source="https://github.com/fungible-inc/FunOS/blob/master/apps/tls_dp_tunnel_perf.c",
                    positive=True,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
    print "created charts for the TLS 32 nad 64 tunnel juniper customer teramarks"

if __name__ == "__main_HU_latency__":
    internal_chart_names = ["NU_HU_NFCP_8TCP_offloads_disabled_output_latency",
                            "HU_NU_NFCP_8TCP_offloads_disabled_output_latency",
                            "HU_NU_NFCP_1TCP_offloads_disabled_output_latency",
                            "NU_HU_NFCP_1TCP_offloads_disabled_output_latency",
                            "HU_NU_NFCP_8TCP_offloads_disabled_2hosts_output_latency",
                            "NU_HU_NFCP_8TCP_offloads_disabled_2hosts_output_latency",
                            "HU_HU_NFCP_1TCP_offloads_disabled_output_latency",
                            "HU_HU_NFCP_8TCP_offloads_disabled_output_latency"]
    frame_size = 1500
    flow_types = ["HU_NU_NFCP", "NU_HU_NFCP"]
    base_line_date = datetime(year=2019, month=1, day=26, minute=0, hour=0, second=0)
    model_name = "HuLatencyPerformance"
    chart_name = "Latency"
    positive = False
    description = "TBD"
    y1_axis_title = "usecs"
    output_names = ["output_latency_min", "output_latency_P50", "output_latency_P90", "output_latency_P99"]
    for internal_chart_name in internal_chart_names:
        if "1TCP" in internal_chart_name:
            num_flows = 1
        else:
            num_flows = 8

        if "2hosts" in internal_chart_name:
            num_hosts = 2
        else:
            num_hosts = 1

        data_sets = []
        for output_name in output_names:
            if "HU_NU_NFCP" in internal_chart_name:
                flow_type = "HU_NU_NFCP"
                output_name = output_name + "_h2n"
            elif "NU_HU_NFCP" in internal_chart_name:
                flow_type = "NU_HU_NFCP"
                output_name = output_name + "_n2h"
            else:
                flow_type = "HU_HU_NFCP"
                output_name = output_name + "_h2h"
            name = str(frame_size) + "B"
            if "99" in output_name:
                name += '-99%'
            elif "90" in output_name:
                name += '-90%'
            elif "50" in output_name:
                name += '-50%'
            else:
                name += '-min'
            one_data_set = {}
            one_data_set["name"] = name
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_flow_type"] = flow_type
            one_data_set["inputs"]["input_number_flows"] = num_flows
            one_data_set["inputs"]["input_num_hosts"] = num_hosts
            one_data_set["inputs"]["input_protocol"] = "TCP"
            one_data_set["inputs"]["input_platform"] = "F1"
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
    print "created latency charts for the networking teramarks"

if __name__ == "__main_raw_block_iod__":
    # fio_pcie_read_blt_1_iod_scaling,
    # fio_pcie_read_blt_4_iod_scaling,
    # fio_pcie_read_blt_8_iod_scaling,
    # fio_pcie_read_blt_16_iod_scaling,
    # fio_pcie_randread_blt_1_iod_scaling,
    # fio_pcie_randread_blt_4_iod_scaling,
    # fio_pcie_randread_blt_8_iod_scaling,
    # fio_pcie_randread_blt_16_iod_scaling,
    # fio_read_blt_1_iod_scaling,
    # fio_read_blt_4_iod_scaling,
    # fio_read_blt_8_iod_scaling,
    # fio_read_blt_16_iod_scaling,
    # fio_randread_blt_1_iod_scaling,
    # fio_randread_blt_4_iod_scaling,
    # fio_randread_blt_8_iod_scaling,
    # fio_randread_blt_16_iod_scaling,
    copy_from_pcie_read = ["read_4kb1vol1ssd_4_output_latency", "read_4kb1vol1ssd_output_iops"]
    copy_from_pcie_randread = ["rand_read_4kb1vol1ssd_4_output_latency", "rand_read_4kb1vol1ssd_output_iops"]
    copy_from_nvmetcp_read = ["read_4kb12vol12ssd_4_nvmetcp_output_latency", "read_4kb12vol12ssd_nvmetcp_output_iops"]
    copy_from_nvmetcp_randread = ["rand_read_4kb12vol12ssd_4_nvmetcp_output_latency",
                                  "rand_read_4kb12vol12ssd_nvmetcp_output_iops"]
    output_names = ["output_latency", "output_iops"]
    operations = ["read", "rand_read"]
    names = ["nvmetcp", "pcie"]
    qdepths = ["qd1", "qd4", "qd8", "qd16"]
    model_name = "BltVolumePerformance"
    base_line_date = datetime(year=2019, month=5, day=10, minute=0, hour=0, second=0)
    for name in names:
        for operation in operations:
            for output_name in output_names:
                if name == "nvmetcp":
                    source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/blt_fs_iodepth_scaling.py"
                    if operation == "rand_read":
                        job_names = ["fio_randread_blt_", "_iod_scaling"]
                        copy = copy_from_nvmetcp_randread
                    else:
                        job_names = ["fio_read_blt_", "_iod_scaling"]
                        copy = copy_from_nvmetcp_read
                else:
                    source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/blt_pcie_io_depth.py"
                    if operation == "rand_read":
                        job_names = ["fio_pcie_randread_blt_", "_iod_scaling"]
                        copy = copy_from_pcie_randread
                    else:
                        job_names = ["fio_pcie_read_blt_", "_iod_scaling"]
                        copy = copy_from_pcie_read

                if "iops" in output_name:
                    internal_chart_name = operation + "_" + "qd" + "_" + name + "_" + output_name
                    chart_name = "IOPS"
                    positive = True
                    y1_axis_title = "ops"
                    data_sets = []
                    for qdepth in qdepths:
                        if "16" in qdepth:
                            fio_job_name = job_names[0] + "16" + job_names[1]
                        elif "8" in qdepth:
                            fio_job_name = job_names[0] + "8" + job_names[1]
                        elif "4" in qdepth:
                            fio_job_name = job_names[0] + "4" + job_names[1]
                        else:
                            fio_job_name = job_names[0] + "1" + job_names[1]

                        if operation == "rand_read":
                            data_set_operation = "randread"
                        else:
                            data_set_operation = "read"

                        one_data_set = {}
                        one_data_set["name"] = qdepth
                        one_data_set["inputs"] = {}
                        one_data_set["inputs"]["input_platform"] = "F1"
                        one_data_set["inputs"]["input_operation"] = data_set_operation
                        one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
                        one_data_set["output"] = {"name": "output_read_iops", 'min': 0, "max": -1, "expected": -1,
                                                  "reference": -1}
                        data_sets.append(one_data_set)

                    metric_id = LastMetricId.get_next_id()
                    MetricChart(chart_name=chart_name,
                                metric_id=metric_id,
                                internal_chart_name=internal_chart_name,
                                data_sets=json.dumps(data_sets),
                                leaf=True,
                                description="TBD",
                                owner_info="Manu KS (manu.ks@fungible.com)",
                                source=source,
                                positive=positive,
                                y1_axis_title=y1_axis_title,
                                visualization_unit=y1_axis_title,
                                metric_model_name=model_name,
                                base_line_date=base_line_date,
                                work_in_progress=False).save()
                else:
                    for qdepth in qdepths:
                        if "16" in qdepth:
                            fio_job_name = job_names[0] + "16" + job_names[1]
                        elif "8" in qdepth:
                            fio_job_name = job_names[0] + "8" + job_names[1]
                        elif "4" in qdepth:
                            fio_job_name = job_names[0] + "4" + job_names[1]
                        else:
                            fio_job_name = job_names[0] + "1" + job_names[1]
                        chart_name = "Latency"
                        internal_chart_name = operation + "_" + qdepth + "_" + name + "_" + output_name
                        positive = False
                        y1_axis_title = "usecs"
                        for c in copy:
                            if "latency" in c:
                                copy_from = c

                        chart = MetricChart.objects.get(internal_chart_name=copy_from)
                        data_sets = json.loads(chart.data_sets)
                        for data_set in data_sets:
                            data_set["inputs"]["input_fio_job_name"] = fio_job_name
                            data_set["output"]["expected"] = -1
                            data_set["output"]["min"] = 0
                            data_set["output"]["max"] = -1
                            data_set["output"]["reference"] = -1

                        metric_id = LastMetricId.get_next_id()
                        MetricChart(chart_name=chart_name,
                                    metric_id=metric_id,
                                    internal_chart_name=internal_chart_name,
                                    data_sets=json.dumps(data_sets),
                                    leaf=True,
                                    description="TBD",
                                    owner_info="Manu KS (manu.ks@fungible.com)",
                                    source=source,
                                    positive=positive,
                                    y1_axis_title=y1_axis_title,
                                    visualization_unit=y1_axis_title,
                                    metric_model_name=model_name,
                                    base_line_date=base_line_date,
                                    work_in_progress=False).save()
    print "added charts for raw block different io depths"

if __name__ == "__main_durable_volume__":
    copy_rand_read = "rand_read_4kb1vol1ssd_durable_volume_ec_4_output_latency"
    copy_read = "read_4kb1vol1ssd_durable_volume_ec_4_output_latency"
    output_names = ["output_latency", "output_iops"]
    operations = ["read", "rand_read"]
    iodepths = [1, 8, 16, 32, 64]
    model_name = "BltVolumePerformance"
    base_line_date = datetime(year=2019, month=5, day=10, minute=0, hour=0, second=0)
    for operation in operations:
        for output_name in output_names:
            source = ""
            if operation == "rand_read":
                job_names = "ec_randread_iodepth_"
                copy = copy_rand_read
            else:
                job_names = "ec_read_iodepth_"
                copy = copy_read

            if "iops" in output_name:
                internal_chart_name = operation + "_iod_durable_volume_ec_" + output_name
                chart_name = "IOPS"
                positive = True
                y1_axis_title = "ops"
                data_sets = []
                for iodepth in iodepths:
                    fio_job_name = job_names + str(iodepth)
                    if operation == "rand_read":
                        data_set_operation = "randread"
                    else:
                        data_set_operation = "read"

                    one_data_set = {}
                    one_data_set["name"] = iodepth
                    one_data_set["inputs"] = {}
                    one_data_set["inputs"]["input_platform"] = "F1"
                    one_data_set["inputs"]["input_operation"] = data_set_operation
                    one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
                    one_data_set["output"] = {"name": "output_read_iops", 'min': 0, "max": -1, "expected": -1,
                                              "reference": -1}
                    data_sets.append(one_data_set)

                metric_id = LastMetricId.get_next_id()
                MetricChart(chart_name=chart_name,
                            metric_id=metric_id,
                            internal_chart_name=internal_chart_name,
                            data_sets=json.dumps(data_sets),
                            leaf=True,
                            description="TBD",
                            owner_info="Aamir Shaikh (aamir.shaikh@fungible.com)",
                            source=source,
                            positive=positive,
                            y1_axis_title=y1_axis_title,
                            visualization_unit=y1_axis_title,
                            metric_model_name=model_name,
                            base_line_date=base_line_date,
                            work_in_progress=False).save()
            else:
                for iodepth in iodepths:
                    fio_job_name = job_names + str(iodepth)
                    chart_name = "Latency"
                    internal_chart_name = operation + "_iod" + str(iodepth) + "_durable_volume_ec_" + output_name
                    positive = False
                    y1_axis_title = "usecs"

                    chart = MetricChart.objects.get(internal_chart_name=copy)
                    data_sets = json.loads(chart.data_sets)
                    for data_set in data_sets:
                        data_set["inputs"]["input_fio_job_name"] = fio_job_name
                        data_set["output"]["expected"] = -1
                        data_set["output"]["min"] = 0
                        data_set["output"]["max"] = -1
                        data_set["output"]["reference"] = -1

                    metric_id = LastMetricId.get_next_id()
                    MetricChart(chart_name=chart_name,
                                metric_id=metric_id,
                                internal_chart_name=internal_chart_name,
                                data_sets=json.dumps(data_sets),
                                leaf=True,
                                description="TBD",
                                owner_info="Manu KS (manu.ks@fungible.com)",
                                source=source,
                                positive=positive,
                                y1_axis_title=y1_axis_title,
                                visualization_unit=y1_axis_title,
                                metric_model_name=model_name,
                                base_line_date=base_line_date,
                                work_in_progress=False).save()
    print "added charts for durable volume different io depths"

if __name__ == "__main__":
    iops_chart = MetricChart.objects.get(internal_chart_name="inspur_rand_read_write_8k_block_output_iops")
    latency_chart = MetricChart.objects.get(internal_chart_name="inspur_rand_read_write_8k_block_output_latency")
    iodepths = [1, 8, 16, 32, 64]
    model_name = "BltVolumePerformance"
    job_name = "inspur_8k_random_read_write_"
    internal_names = ["inspur_rand_read_write_qd", "_8k_block_output_"]
    base_line_date = datetime(year=2019, month=5, day=10, minute=0, hour=0, second=0)
    names = ["iops", "latency"]
    for name in names:
        if name == "iops":
            chart = iops_chart
            chart_name = "IOPS"
        else:
            chart = latency_chart
            chart_name = "Latency"
        for iodepth in iodepths:
            internal_chart_name = internal_names[0] + str(iodepth) + internal_names[1] + name
            data_sets = json.loads(chart.data_sets)
            for data_set in data_sets:
                data_set["inputs"]["input_fio_job_name"] = job_name + str(iodepth)
            metric_id = LastMetricId.get_next_id()
            MetricChart(chart_name=chart_name,
                        metric_id=metric_id,
                        internal_chart_name=internal_chart_name,
                        data_sets=json.dumps(data_sets),
                        leaf=True,
                        description=chart.description,
                        owner_info=chart.owner_info,
                        source=chart.source,
                        positive=chart.positive,
                        y1_axis_title=chart.y1_axis_title,
                        visualization_unit=chart.visualization_unit,
                        metric_model_name=model_name,
                        base_line_date=base_line_date,
                        work_in_progress=False).save()
    print "added charts for Inspur different io depths"
