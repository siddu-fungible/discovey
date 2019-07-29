from web.fun_test.maintenance_old import *
from lib.system.fun_test import *
from datetime import datetime
from web.fun_test.models_helper import add_jenkins_job_id_map
from dateutil import parser
from django.utils import timezone
from fun_global import PerfUnit
from fun_global import ChartType, FunChartType
from web.fun_test.metrics_models import *
from collections import OrderedDict
from web.fun_test.metrics_lib import MetricLib
from web.fun_test.models import *

METRICS_BASE_DATA_FILE = WEB_ROOT_DIR + "/metrics.json"

if __name__ == "__main__rand_read_qd_multi_host":
    internal_read_chart_names = ["rand_read_qd_multi_host_nvmetcp_output_iops",
                                 "rand_read_qd1_multi_host_nvmetcp_output_latency",
                                 "rand_read_qd32_multi_host_nvmetcp_output_latency",
                                 "rand_read_qd64_multi_host_nvmetcp_output_latency",
                                 "rand_read_qd128_multi_host_nvmetcp_output_latency"]
    internal_write_chart_names = ["rand_write_qd_multi_host_nvmetcp_output_iops",
                                  "rand_write_qd1_multi_host_nvmetcp_output_latency",
                                  "rand_write_qd8_multi_host_nvmetcp_output_latency",
                                  "rand_write_qd16_multi_host_nvmetcp_output_latency",
                                  "rand_write_qd32_multi_host_nvmetcp_output_latency"]
    base_line_date = datetime(year=2019, month=7, day=15, minute=0, hour=0, second=0)
    for internal_chart_name in internal_read_chart_names:
        try:
            chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
            if "iops" in internal_chart_name:
                data_sets = json.loads(chart.data_sets)
                for data_set in data_sets:
                    data_set["inputs"]["input_fio_job_name"] = data_set["inputs"]["input_fio_job_name"].replace(
                        "nhosts", "vol_12")
                one_data_set = {}
                one_data_set["name"] = "qd128"
                one_data_set["inputs"] = {"input_platform": FunPlatform.F1, "input_fio_job_name": "fio_tcp_randread_blt_32_4_vol_12"}
                one_data_set["output"] = {"name": "output_read_iops", "min": 0, "max": -1, "expected": -1,
                                          "reference": -1,
                                          "unit": PerfUnit.UNIT_OPS}
                data_sets.append(one_data_set)
                chart.data_sets = json.dumps(data_sets)
                chart.save()
            else:
                data_sets = json.loads(chart.data_sets)
                for data_set in data_sets:
                    data_set["inputs"]["input_fio_job_name"] = data_set["inputs"]["input_fio_job_name"].replace(
                        "nhosts", "vol_12")
                chart.data_sets = json.dumps(data_sets)
                chart.save()
        except ObjectDoesNotExist:
            copy_chart = MetricChart.objects.get(internal_chart_name="rand_read_qd1_multi_host_nvmetcp_output_latency")
            data_sets = json.loads(copy_chart.data_sets)
            for data_set in data_sets:
                data_set["inputs"]["input_fio_job_name"] = "fio_tcp_randread_blt_32_4_vol_12"
                data_set["output"]["expected"] = -1
                data_set["output"]["reference"] = -1
            metric_id = LastMetricId.get_next_id()
            MetricChart(chart_name="temp",
                        metric_id=metric_id,
                        internal_chart_name=internal_chart_name,
                        data_sets=json.dumps(data_sets),
                        leaf=True,
                        description=copy_chart.description,
                        owner_info=copy_chart.owner_info,
                        source=copy_chart.source,
                        positive=copy_chart.positive,
                        y1_axis_title=copy_chart.y1_axis_title,
                        visualization_unit=copy_chart.visualization_unit,
                        metric_model_name=copy_chart.metric_model_name,
                        base_line_date=copy_chart.base_line_date,
                        work_in_progress=False,
                        platform=FunPlatform.F1).save()
    print "fixed 12 volume random read charts"
    write_fio_job_names = ["fio_tcp_randwrite_blt_1_1_vol_12", "fio_tcp_randwrite_blt_8_1_vol_12",
                           "fio_tcp_randwrite_blt_16_1_vol_12", "fio_tcp_randwrite_blt_32_1_vol_12"]
    for internal_chart_name in internal_write_chart_names:
        try:
            chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
            if "iops" in internal_chart_name:
                data_sets = []
                for fio_job_name in write_fio_job_names:
                    if "1_1" in fio_job_name:
                        name = "qd1"
                    elif "8_1" in fio_job_name:
                        name = "qd8"
                    elif "16_1" in fio_job_name:
                        name = "qd16"
                    else:
                        name = "qd32"
                    one_data_set = {}
                    one_data_set["name"] = name
                    one_data_set["inputs"] = {"input_platform": FunPlatform.F1, "input_fio_job_name": fio_job_name}
                    one_data_set["output"] = {"name": "output_write_iops", "min": 0, "max": -1, "expected": -1,
                                              "reference": -1, "unit": PerfUnit.UNIT_OPS}
                    data_sets.append(one_data_set)
                chart.data_sets = json.dumps(data_sets)
                chart.save()
            else:
                data_sets = json.loads(chart.data_sets)
                for data_set in data_sets:
                    data_set["inputs"]["input_fio_job_name"] = data_set["inputs"]["input_fio_job_name"].replace(
                        "nhosts", "vol_12")
                chart.data_sets = json.dumps(data_sets)
                chart.save()
        except ObjectDoesNotExist:
            copy_chart = MetricChart.objects.get(internal_chart_name="rand_write_qd1_multi_host_nvmetcp_output_latency")
            data_sets = json.loads(copy_chart.data_sets)
            if "qd8" in internal_chart_name:
                fio_job_name = "fio_tcp_randwrite_blt_8_1_vol_12"
            elif "qd16" in internal_chart_name:
                fio_job_name = "fio_tcp_randwrite_blt_16_1_vol_12"
            for data_set in data_sets:
                data_set["inputs"]["input_fio_job_name"] = fio_job_name
                data_set["output"]["expected"] = -1
                data_set["output"]["reference"] = -1
            metric_id = LastMetricId.get_next_id()
            MetricChart(chart_name="temp",
                        metric_id=metric_id,
                        internal_chart_name=internal_chart_name,
                        data_sets=json.dumps(data_sets),
                        leaf=True,
                        description=copy_chart.description,
                        owner_info=copy_chart.owner_info,
                        source=copy_chart.source,
                        positive=copy_chart.positive,
                        y1_axis_title=copy_chart.y1_axis_title,
                        visualization_unit=copy_chart.visualization_unit,
                        metric_model_name=copy_chart.metric_model_name,
                        base_line_date=copy_chart.base_line_date,
                        work_in_progress=False,
                        platform=FunPlatform.F1).save()
    print "fixed 12 volumes random write charts"
    num_volumes = [2, 4, 8]
    for internal_chart_name in (internal_read_chart_names + internal_write_chart_names):
        copy_chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        index = internal_chart_name.find('output')
        for volume in num_volumes:
            internal_name = internal_chart_name[:index] + str(volume) + '_vols_' + internal_chart_name[index:]
            data_sets = json.loads(copy_chart.data_sets)
            vol_string = "vol_" + str(volume)
            for data_set in data_sets:
                data_set["inputs"]["input_fio_job_name"] = data_set["inputs"]["input_fio_job_name"].replace("vol_12",
                                                                                                            vol_string)
                data_set["output"]["expected"] = -1
                data_set["output"]["reference"] = -1
            metric_id = LastMetricId.get_next_id()
            MetricChart(chart_name="temp",
                        metric_id=metric_id,
                        internal_chart_name=internal_name,
                        data_sets=json.dumps(data_sets),
                        leaf=True,
                        description=copy_chart.description,
                        owner_info=copy_chart.owner_info,
                        source=copy_chart.source,
                        positive=copy_chart.positive,
                        y1_axis_title=copy_chart.y1_axis_title,
                        visualization_unit=copy_chart.visualization_unit,
                        metric_model_name=copy_chart.metric_model_name,
                        base_line_date=copy_chart.base_line_date,
                        work_in_progress=False,
                        platform=FunPlatform.F1).save()
    print "added charts f0r 2,4,8 volumes"


if __name__ == "__main_s1_teramarks__":
    with open(METRICS_BASE_DATA_FILE, "r") as f:
        metrics = json.load(f)
        for metric in metrics:
            if metric["label"] == "F1":
                f1_metrics = metric["children"]
                for f1_metric in f1_metrics:
                    if f1_metric["label"] == "TeraMarks":
                        funos_metrics = f1_metric
                        break

        tera_marks = funos_metrics["children"]
        for tera_mark in tera_marks:
            tera_mark_child_name = tera_mark["name"]
            print(tera_mark_child_name)
            if tera_mark_child_name == "TeraMark Compression" or tera_mark_child_name == "Erasure-coding":
                print("tera_mark :{}".format(tera_mark))
                result = set_internal_name(tera_mark)
                print json.dumps(result)


if __name__ == "__main_l4_firewall__":
    internal_chart_names = ["l4_firewall_flow_128m_flows_throughput", "l4_firewall_flow_128m_flows_pps",
                            "l4_firewall_flow_128m_flows_latency_full_load", "l4_firewall_flow_128m_flows_latency_half_load"]
    for internal_chart_name in internal_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        temp_data_sets = json.loads(chart.data_sets)
        if "throughput" in internal_chart_name or "pps" in internal_chart_name:
            for temp_data_set in temp_data_sets:
                if temp_data_set["name"] == "64B":
                    one_data_set = temp_data_set
            one_data_set["name"] = "1500B"
            one_data_set["inputs"]["input_frame_size"] = 1500
            one_data_set["output"]["expected"] = -1
            one_data_set["output"]["reference"] = -1
            data_sets = json.loads(chart.data_sets)
            data_sets.append(one_data_set)
            chart.data_sets = json.dumps(data_sets)
            chart.save()
        else:
            data_sets = json.loads(chart.data_sets)
            for temp_data_set in temp_data_sets:
                if "64B" in temp_data_set["name"]:
                    one_data_set = temp_data_set
                    one_data_set["name"] = one_data_set["name"].replace("64B", "1500B")
                    one_data_set["inputs"]["input_frame_size"] = 1500
                    one_data_set["output"]["expected"] = -1
                    one_data_set["output"]["reference"] = -1
                    data_sets.append(one_data_set)
            chart.data_sets = json.dumps(data_sets)
            chart.save()
    print "added 1500B datasets for 124M flows"

if __name__ == "__main_qd256__":
    internal_iops_chart_names = ["read_qd_pcie_output_iops", "rand_read_qd_pcie_output_iops"]
    for internal_chart_name in internal_iops_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        data_sets = json.loads(chart.data_sets)
        for data_set in data_sets:
            if data_set["name"] == "qd128":
                one_data_set = data_set
                one_data_set["name"] = "qd256"
                one_data_set["inputs"]["input_fio_job_name"] = one_data_set["inputs"]["input_fio_job_name"].replace(
                    "128", "256")
                one_data_set["output"]["expected"] = -1
                one_data_set["output"]["reference"] = -1
        data_sets = json.loads(chart.data_sets)
        data_sets.append(one_data_set)
        chart.data_sets = json.dumps(data_sets)
        chart.save()
    print "added 256 for random/sequentail read iops"
    internal_latency_chart_names = ["read_qd256_pcie_output_latency", "rand_read_qd256_pcie_output_latency"]
    for internal_chart_name in internal_latency_chart_names:
        copy_chart = MetricChart.objects.get(internal_chart_name=internal_chart_name.replace("256", "128"))
        if copy_chart:
            data_sets = json.loads(copy_chart.data_sets)
            for data_set in data_sets:
                data_set["inputs"]["input_fio_job_name"] = data_set["inputs"]["input_fio_job_name"].replace("128",
                                                                                                            "256")
                data_set["output"]["expected"] = -1
                data_set["output"]["reference"] = -1
            metric_id = LastMetricId.get_next_id()
            MetricChart(chart_name="temp",
                        metric_id=metric_id,
                        internal_chart_name=internal_chart_name,
                        data_sets=json.dumps(data_sets),
                        leaf=True,
                        description=copy_chart.description,
                        owner_info=copy_chart.owner_info,
                        source=copy_chart.source,
                        positive=copy_chart.positive,
                        y1_axis_title=copy_chart.y1_axis_title,
                        visualization_unit=copy_chart.visualization_unit,
                        metric_model_name=copy_chart.metric_model_name,
                        base_line_date=copy_chart.base_line_date,
                        work_in_progress=False,
                        platform=FunPlatform.F1).save()
    print "added charts for 256 qdepth latency"

if __name__ == "__main_setting_expected__":
    entries = MetricChart.objects.filter(leaf=True)
    for entry in entries:
        if ("underlay" in entry.internal_chart_name or "overlay" in entry.internal_chart_name) and \
                "latency" not in entry.internal_chart_name:
            # print "overlay or underlay chart is {}".format(entry.internal_chart_name)
            if "overlay" in entry.internal_chart_name:
                index = entry.internal_chart_name.find('_overlay')
            else:
                index = entry.internal_chart_name.find('_underlay')
            internal_chart_name = entry.internal_chart_name[:index]
            # print "original chart is {}".format(internal_chart_name)
            overlay_underlay_data_sets = json.loads(entry.data_sets)
            chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
            data_sets = json.loads(chart.data_sets)
            for data_set in data_sets:
                for ou_data_set in overlay_underlay_data_sets:
                    if data_set["name"] == ou_data_set["name"]:
                        if data_set["output"]["unit"] == ou_data_set["output"]["unit"]:
                            ou_data_set["output"]["expected"] = data_set["output"]["expected"]
                        else:
                            print entry.internal_chart_name, data_set["name"]

            entry.data_sets = json.dumps(overlay_underlay_data_sets)
            entry.save()

if __name__ == "__main__":
    users = User.objects.all()
    for user in users:
        PerformanceUserProfile(email=user.email).save()
    print "added users for performance profile"

