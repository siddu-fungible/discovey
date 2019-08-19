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

if __name__ == "__main__underlay":
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

if __name__ == "__main__inspur_charts":
    internal_chart_names = OrderedDict([  # read iops
                                        ("pocs_inspur_8111_8k_rand_read_iodepth_1_iops", 1),
                                        ("pocs_inspur_8111_8k_rand_read_iodepth_8_iops", 8),
                                        ("pocs_inspur_8111_8k_rand_read_iodepth_16_iops", 16),
                                        ("pocs_inspur_8111_8k_rand_read_iodepth_32_iops", 32),
                                        ("pocs_inspur_8111_8k_rand_read_iodepth_64_iops", 64),
                                        ("pocs_inspur_8111_8k_rand_read_iodepth_96_iops", 96),
                                        ("pocs_inspur_8111_8k_rand_read_iodepth_128_iops", 128),
                                        # write iops
                                        ("pocs_inspur_8111_8k_rand_write_iodepth_1_iops", 1),
                                        ("pocs_inspur_8111_8k_rand_write_iodepth_8_iops", 8),
                                        ("pocs_inspur_8111_8k_rand_write_iodepth_16_iops", 16),
                                        ("pocs_inspur_8111_8k_rand_write_iodepth_32_iops", 32),
                                        ("pocs_inspur_8111_8k_rand_write_iodepth_64_iops", 64),
                                        ("pocs_inspur_8111_8k_rand_write_iodepth_96_iops", 96),
                                        ("pocs_inspur_8111_8k_rand_write_iodepth_128_iops", 128),
                                        # read latency
                                        ("pocs_inspur_8111_8k_rand_read_iodepth_1_latency", 1),
                                        ("pocs_inspur_8111_8k_rand_read_iodepth_8_latency", 8),
                                        ("pocs_inspur_8111_8k_rand_read_iodepth_16_latency", 16),
                                        ("pocs_inspur_8111_8k_rand_read_iodepth_32_latency", 32),
                                        ("pocs_inspur_8111_8k_rand_read_iodepth_64_latency", 64),
                                        ("pocs_inspur_8111_8k_rand_read_iodepth_96_latency", 96),
                                        ("pocs_inspur_8111_8k_rand_read_iodepth_128_latency", 128),
                                        # write latency
                                        ("pocs_inspur_8111_8k_rand_write_iodepth_1_latency", 1),
                                        ("pocs_inspur_8111_8k_rand_write_iodepth_8_latency", 8),
                                        ("pocs_inspur_8111_8k_rand_write_iodepth_16_latency", 16),
                                        ("pocs_inspur_8111_8k_rand_write_iodepth_32_latency", 32),
                                        ("pocs_inspur_8111_8k_rand_write_iodepth_64_latency", 64),
                                        ("pocs_inspur_8111_8k_rand_write_iodepth_96_latency", 96),
                                        ("pocs_inspur_8111_8k_rand_write_iodepth_128_latency", 128),
                                        ])

    owner_info = "Ravi Hulle (ravi.hulle@fungible.com)"
    source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/" \
             "ec_inspur_fs_teramark_multivolume.py"
    platform = FunPlatform.F1
    model_name = "BltVolumePerformance"
    description = "TBD"

    for internal_chart_name in internal_chart_names:
        iodepth = internal_chart_names[internal_chart_name]
        if "read" in internal_chart_name:
            mode = "read"
        elif "write" in internal_chart_name:
            mode = "write"
        if "iops" in internal_chart_name:
            field = "iops"
            add_name = ""
            y1_axis_title = PerfUnit.UNIT_OPS
            positive = False
            chart_name = "IOPS, QDepth={}".format(iodepth)
        elif "latency" in internal_chart_name:
            field = "avg_latency"
            add_name = "-avg"
            y1_axis_title = PerfUnit.UNIT_USECS
            positive = True
            chart_name = "Latency, QDepth={}".format(iodepth)

        one_data_set = {}
        data_sets = []

        output_name = "output_{}_{}".format(mode, field)

        if iodepth == 1 or iodepth == 8 or iodepth == 16:
            fio_job_name = "inspur_8k_random_{}_{}".format(mode, iodepth)
            naming = "{}{}(1 vol)".format(mode, add_name)
            input_fio_job_names = OrderedDict([(fio_job_name, naming)])
        elif iodepth == 32 or iodepth == 64 or iodepth == 128 or iodepth == 96:
            if iodepth == 96:
                volumes_list = [4, 8]
            else:
                volumes_list = [1, 4, 8]
            input_fio_job_names = OrderedDict()
            for vol in volumes_list:
                if vol == 1:
                    fio_job_name = "inspur_8k_random_{}_{}".format(mode, iodepth)
                else:
                    fio_job_name = "inspur_8k_random_{}_iodepth_{}_vol_{}".format(mode, iodepth, vol)

                input_fio_job_names[fio_job_name] = "{}{}({} vol)".format(mode, add_name, vol)

        for input_fio_job_name in input_fio_job_names:
            inputs = {
                "input_platform": platform,
                "input_fio_job_name": input_fio_job_name
            }

            output = {
                "name": output_name,
                "unit": y1_axis_title,
                "min": 0,
                "max": -1,
                "expected": -1,
                "reference": -1
            }
            one_data_set["name"] = input_fio_job_names[input_fio_job_name]
            one_data_set["inputs"] = inputs
            one_data_set["output"] = output
            data_sets.append(one_data_set.copy())

        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description=description,
                    owner_info=owner_info,
                    source=source,
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    platform=platform,
                    work_in_progress=False).save()
        print ("Metric id: {}".format(metric_id))
        print ("Data sets: {}".format(data_sets))


if __name__ == "__main__crypto":
    internal_chart_names = OrderedDict([("crypto_dp_tunnel_perf_S1", "pktsize: 354B"),
                                        ("crypto_ipsec_perf_S1", "pktsize: 354B")])
    owner_info = "Jitendra Lulla (jitendra.lulla@fungible.com)"
    source = ""
    platform = FunPlatform.S1
    model_name = "TeraMarkCryptoPerformance"
    description = "TBD"
    y1_axis_title = PerfUnit.UNIT_GBITS_PER_SEC
    positive = False
    output_name = "output_throughput"

    for internal_chart_name in internal_chart_names:
        if "dp_tunnel_perf" in internal_chart_name:
            input_app = "crypto_dp_tunnel_throughput"
            chart_name = "Dp tunnel perf"
        elif "ipsec_perf" in internal_chart_name:
            input_app = "ipsec_tunnel_throughput"
            chart_name = "Ipsec perf"
        one_data_set = {}
        data_sets = []

        inputs = {
            "input_platform": platform,
            "input_app": input_app
        }
        output = {
            "name": output_name,
            "unit": y1_axis_title,
            "min": 0,
            "max": -1,
            "expected": -1,
            "reference": -1
        }
        one_data_set["name"] = internal_chart_names[internal_chart_name]
        one_data_set["inputs"] = inputs
        one_data_set["output"] = output
        data_sets.append(one_data_set.copy())

        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description=description,
                    owner_info=owner_info,
                    source=source,
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    platform=platform,
                    work_in_progress=False).save()
        print ("Metric id: {}".format(metric_id))
        print ("Data sets: {}".format(data_sets))


if __name__ == "__main_added_6vol__":
    # Add the 6 vol field for inspur 8_11 F1s = 6 charts
    metric_ids = [743, 744, 746, 745, 750, 751, 753, 752]
    for metric_id in metric_ids:
        chart = MetricChart.objects.get(metric_id=metric_id)
        data_sets = json.loads(chart.data_sets)
        copy_data_sets = data_sets[:]
        for one_data_set in copy_data_sets:
            input_fio_job_name = one_data_set['inputs']['input_fio_job_name']
            name = one_data_set['name']
            output = one_data_set['output']

            one_data_set["inputs"]["input_fio_job_name"] = re.sub(r'vol_1', 'vol_6', input_fio_job_name)
            one_data_set["name"] = re.sub(r'1 vol', '6 vol', name)
            output["reference"] = -1
            output["min"] = 0
            output["max"] = -1

        data_sets = json.loads(chart.data_sets)
        data_sets += copy_data_sets
        chart.data_sets = json.dumps(data_sets)
        chart.save()

if __name__ == "__main__":
    names = ["alibaba_bmv_storage_local_ssd_random_write", "alibaba_bmv_storage_local_ssd_random_read"]
    base_line_date = datetime(year=2019, month=8, day=11, minute=0, hour=0, second=0)
    for internal_chart_name in names:
        container_chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        container_chart.base_line_data = base_line_date
        container_chart.save()
        children = json.loads(container_chart.children)
        for child in children:
            chart = MetricChart.objects.get(metric_id=int(child))
            chart.base_line_date = base_line_date
            chart.save()
            internal_chart_name = chart.internal_chart_name
            internal_name = internal_chart_name.replace("local", "remote")
            data_sets = json.loads(chart.data_sets)
            for data_set in data_sets:
                data_set["output"]["expected"] = -1
                data_set["output"]["reference"] = -1
            metric_id = LastMetricId.get_next_id()
            MetricChart(chart_name=chart.chart_name,
                        metric_id=metric_id,
                        internal_chart_name=internal_name,
                        data_sets=json.dumps(data_sets),
                        leaf=True,
                        description=chart.description,
                        owner_info="Divya Krishnankutty (divya.krishnankutty@fungible.com)",
                        source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/pocs/alibaba/alibaba_raw_vol_rds_via_vm.py",
                        positive=chart.positive,
                        y1_axis_title=chart.y1_axis_title,
                        visualization_unit=chart.visualization_unit,
                        metric_model_name="AlibabaBmvRemoteSsdPerformance",
                        base_line_date=base_line_date,
                        work_in_progress=False,
                        platform=FunPlatform.F1).save()
    print "added charts for remote ssd and reset the baseline for local ssd charts"


