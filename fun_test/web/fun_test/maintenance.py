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
ml = MetricLib()

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
                one_data_set["inputs"] = {"input_platform": FunPlatform.F1,
                                          "input_fio_job_name": "fio_tcp_randread_blt_32_4_vol_12"}
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
                            "l4_firewall_flow_128m_flows_latency_full_load",
                            "l4_firewall_flow_128m_flows_latency_half_load"]
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

if __name__ == "__main_inspur__":
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

if __name__ == "__main_crypto_s1__":
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

if __name__ == "__main_6vol_6f1_inspur__":
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

if __name__ == "__main_alibaba_remote_ssd__":
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

if __name__ == "__main__channel_parall_performance":
    internal_chart_name = "channel_parall_performance_1000"
    chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
    internal_name = internal_chart_name.replace("1000", "100")
    chart_name = chart.chart_name.replace("1000", "100")
    data_sets = json.loads(chart.data_sets)
    for data_set in data_sets:
        data_set["name"] = "100"
        data_set["inputs"]["input_number_channels"] = 100
        data_set["inputs"]["input_platform"] = FunPlatform.F1
        data_set["output"]["expected"] = -1
        data_set["output"]["reference"] = -1
    metric_id = LastMetricId.get_next_id()
    MetricChart(chart_name=chart_name,
                metric_id=metric_id,
                internal_chart_name=internal_name,
                data_sets=json.dumps(data_sets),
                leaf=True,
                description=chart.description,
                owner_info=chart.owner_info,
                source=chart.source,
                positive=chart.positive,
                y1_axis_title=chart.y1_axis_title,
                visualization_unit=chart.visualization_unit,
                metric_model_name=chart.metric_model_name,
                base_line_date=chart.base_line_date,
                work_in_progress=False,
                platform=FunPlatform.F1).save()
    internal_chart_names = ["channel_parall_performance_1000", "channel_parall_performance_4_8_16"]
    for internal_chart_name in internal_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        data_sets = json.loads(chart.data_sets)
        for data_set in data_sets:
            data_set["inputs"]["input_platform"] = FunPlatform.F1
        chart.data_sets = json.dumps(data_sets)
        chart.save()
    print "added channel parall chart for n=100"

if __name__ == "__main__durable_ec_vol":
    internal_chart_names = OrderedDict([("durable_vol_ec_comp_nvme_tcp_write_iops", "nvme iops"),
                                        ("durable_vol_ec_comp_pcie_write_iops", "pcie iops"),
                                        ("durable_vol_ec_comp_nvme_tcp_write_latency", "nvme latency"),
                                        ("durable_vol_ec_comp_pcie_write_latency", "pcie latency")
                                        ])
    owner_info = "Aamir Shaikh (aamir.shaikh@fungible.com)"
    platform = FunPlatform.F1
    model_name = "BltVolumePerformance"
    description = "TBD"
    base_line_date = datetime(year=2019, month=8, day=20, minute=0, hour=0, second=0)

    for internal_chart_name in internal_chart_names:
        one_data_set = {}
        data_sets = []
        field = internal_chart_names[internal_chart_name]

        if "nvme" in field:
            inputs_list = OrderedDict([("ec_nvme_tcp_write_1pctcomp_128", "1%"),
                                       ("ec_nvme_tcp_write_50pctcomp_128", "50%"),
                                       ("ec_nvme_tcp_write_80pctcomp_128", "80%")])
            source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/" \
                     "ec_nvme_tcp_comp_perf.py"
            if "iops" in field:
                y1_axis_title = PerfUnit.UNIT_OPS
                chart_name = "Write IOPS NVME/TCP"
                output_name = "output_write_iops"
                positive = False
            else:
                y1_axis_title = PerfUnit.UNIT_USECS
                chart_name = "Write Latency NVME/TCP"
                output_name = "output_write_avg_latency"
                positive = True

        elif "pcie" in field:
            inputs_list = OrderedDict([("ec_fio_25G_write_1", "1%"),
                                       ("ec_fio_25G_write_50", "50%"),
                                       ("ec_fio_25G_write_80", "80%")])

            source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/" \
                     "ec_volume_fs_comp_perf.py"
            if "iops" in field:
                y1_axis_title = PerfUnit.UNIT_KOPS
                chart_name = "Write IOPS PCIe"
                output_name = "output_write_iops"
                positive = False
            else:
                y1_axis_title = PerfUnit.UNIT_USECS
                chart_name = "Write Latency PCIe"
                output_name = "output_write_avg_latency"
                positive = True

        output = {
            "name": output_name,
            "unit": y1_axis_title,
            "min": 0,
            "max": -1,
            "expected": -1,
            "reference": -1
        }
        for input_fio_job_name in inputs_list:
            inputs = {
                "input_platform": platform,
                "input_fio_job_name": input_fio_job_name
            }

            one_data_set["name"] = inputs_list[input_fio_job_name]
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
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
        print ("Metric id: {}".format(metric_id))
        print ("Data sets: {}".format(data_sets))
        for i in data_sets:
            print i

if __name__ == "__main__inspur_charts":
    internal_chart_names = OrderedDict([  # read iops
        ("pocs_inspur_8111_8k_rand_read_iodepth_32_iops_f1_6", 32),
        ("pocs_inspur_8111_8k_rand_read_iodepth_64_iops_f1_6", 64),
        ("pocs_inspur_8111_8k_rand_read_iodepth_96_iops_f1_6", 96),
        ("pocs_inspur_8111_8k_rand_read_iodepth_128_iops_f1_6", 128),
        # write iops
        ("pocs_inspur_8111_8k_rand_write_iodepth_32_iops_f1_6", 32),
        ("pocs_inspur_8111_8k_rand_write_iodepth_64_iops_f1_6", 64),
        ("pocs_inspur_8111_8k_rand_write_iodepth_96_iops_f1_6", 96),
        ("pocs_inspur_8111_8k_rand_write_iodepth_128_iops_f1_6", 128),
        # read latency
        ("pocs_inspur_8111_8k_rand_read_iodepth_32_latency_f1_6", 32),
        ("pocs_inspur_8111_8k_rand_read_iodepth_64_latency_f1_6", 64),
        ("pocs_inspur_8111_8k_rand_read_iodepth_96_latency_f1_6", 96),
        ("pocs_inspur_8111_8k_rand_read_iodepth_128_latency_f1_6", 128),
        # write latency
        ("pocs_inspur_8111_8k_rand_write_iodepth_32_latency_f1_6", 32),
        ("pocs_inspur_8111_8k_rand_write_iodepth_64_latency_f1_6", 64),
        ("pocs_inspur_8111_8k_rand_write_iodepth_96_latency_f1_6", 96),
        ("pocs_inspur_8111_8k_rand_write_iodepth_128_latency_f1_6", 128),
    ])

    owner_info = "Ravi Hulle (ravi.hulle@fungible.com)"
    source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/" \
             "ec_inspur_fs_teramark_multivolume.py"
    platform = FunPlatform.F1
    model_name = "BltVolumePerformance"
    description = "TBD"
    base_line_date = datetime(year=2019, month=8, day=20, minute=0, hour=0, second=0)

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

        if iodepth == 32 or iodepth == 64 or iodepth == 128 or iodepth == 96:
            volumes_list = [6]
            input_fio_job_names = OrderedDict()
            for vol in volumes_list:
                fio_job_name = "inspur_8k_random_{}_iodepth_{}_f1_6_vol_{}".format(mode, iodepth, vol)
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
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
        print ("Metric id: {}".format(metric_id))
        print ("Data sets: {}".format(data_sets))

if __name__ == "__main_alibaba_rdma__":
    # Alibaba rdma latency charts

    internal_chart_names = OrderedDict([
        ("alibaba_rdma_nfcp_f1_2_mtu_1500_write_latency", {"fcp": False, "mtu": 1500, "mode": "write"}),
        ("alibaba_rdma_nfcp_f1_2_mtu_1500_read_latency", {"fcp": False, "mtu": 1500, "mode": "read"}),
        ("alibaba_rdma_nfcp_f1_2_mtu_9000_write_latency", {"fcp": False, "mtu": 9000, "mode": "write"}),
        ("alibaba_rdma_nfcp_f1_2_mtu_9000_read_latency", {"fcp": False, "mtu": 9000, "mode": "read"}),
        ("alibaba_rdma_fcp_f1_2_mtu_1500_write_latency", {"fcp": True, "mtu": 1500, "mode": "write"}),
        ("alibaba_rdma_fcp_f1_2_mtu_1500_read_latency", {"fcp": True, "mtu": 1500, "mode": "read"}),
        ("alibaba_rdma_fcp_f1_2_mtu_9000_write_latency", {"fcp": True, "mtu": 9000, "mode": "write"}),
        ("alibaba_rdma_fcp_f1_2_mtu_9000_read_latency", {"fcp": True, "mtu": 9000, "mode": "read"}),
    ])

    model_name = "AlibabaRdmaPerformance"
    description = "TBD"
    owner_info = "Manu K S  (manu.ks@fungible.com)"
    source = "https://github.com/fungible-inc/Integration/blob/93cbceb27e5be0dfb3b79325c813d36789c5fe3d/fun_test" \
             "/scripts/networking/funcp/rdma_write_perf.py"
    positive = True
    y1_axis_title = PerfUnit.UNIT_USECS
    platform = FunPlatform.F1

    for internal_chart_name in internal_chart_names:
        dict_data = internal_chart_names[internal_chart_name]
        fcp = dict_data['fcp']
        mtu = dict_data['mtu']
        mode = dict_data['mode']
        if mtu == 1500:
            size_list = [1, 128, 256, 512, 1024, 4096]
        else:
            size_list = [4096]
        for size in size_list:
            one_data_set = {}
            data_sets = []
            modified_internal_chart_name = internal_chart_name + "_size_{}".format(size)
            chart_name = "IB {} latency, size {}B".format(mode, size)
            inputs = {
                "input_size_latency": size,
                "input_platform": platform,
                "input_operation": mode,
                "input_fcp": fcp,
                "input_mtu": mtu,
                "input_size_bandwidth": -1
            }
            output_names = OrderedDict([("output_{}_min_latency".format(mode), "min"),
                                        ("output_{}_max_latency".format(mode), "max"),
                                        ("output_{}_avg_latency".format(mode), "avg"),
                                        ("output_{}_99_latency".format(mode), "99%"),
                                        ("output_{}_99_99_latency".format(mode), "99.99%")])
            for output_name in output_names:
                output = {
                    "name": output_name,
                    "unit": PerfUnit.UNIT_USECS,
                    "min": 0,
                    "max": -1,
                    "expected": -1,
                    "reference": -1
                }

                one_data_set["name"] = output_names[output_name]
                one_data_set["inputs"] = inputs
                one_data_set["output"] = output
                data_sets.append(one_data_set.copy())

            metric_id = LastMetricId.get_next_id()
            MetricChart(chart_name=chart_name,
                        metric_id=metric_id,
                        internal_chart_name=modified_internal_chart_name,
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
            for i in data_sets:
                print i

    # Alibaba rdma Bandwidth and packet rates charts

    internal_chart_names = OrderedDict([
        ("alibaba_rdma_nfcp_f1_2_mtu_1500_write_bandwidth",
         {"fcp": False, "mtu": 1500, "mode": "write", "field": "bandwidth"}),
        ("alibaba_rdma_nfcp_f1_2_mtu_1500_read_bandwidth",
         {"fcp": False, "mtu": 1500, "mode": "read", "field": "bandwidth"},),
        ("alibaba_rdma_nfcp_f1_2_mtu_9000_write_bandwidth",
         {"fcp": False, "mtu": 9000, "mode": "write", "field": "bandwidth"}),
        ("alibaba_rdma_nfcp_f1_2_mtu_9000_read_bandwidth",
         {"fcp": False, "mtu": 9000, "mode": "read", "field": "bandwidth"}),
        ("alibaba_rdma_fcp_f1_2_mtu_1500_write_bandwidth",
         {"fcp": True, "mtu": 1500, "mode": "write", "field": "bandwidth"}),
        ("alibaba_rdma_fcp_f1_2_mtu_1500_read_bandwidth",
         {"fcp": True, "mtu": 1500, "mode": "read", "field": "bandwidth"}),
        ("alibaba_rdma_fcp_f1_2_mtu_9000_write_bandwidth",
         {"fcp": True, "mtu": 9000, "mode": "write", "field": "bandwidth"}),
        ("alibaba_rdma_fcp_f1_2_mtu_9000_read_bandwidth",
         {"fcp": True, "mtu": 9000, "mode": "read", "field": "bandwidth"}),
        ("alibaba_rdma_nfcp_f1_2_mtu_1500_write_packet_rate",
         {"fcp": False, "mtu": 1500, "mode": "write", "field": "packet_size"}),
        ("alibaba_rdma_nfcp_f1_2_mtu_1500_read_packet_rate",
         {"fcp": False, "mtu": 1500, "mode": "read", "field": "packet_size"}),
        ("alibaba_rdma_nfcp_f1_2_mtu_9000_write_packet_rate",
         {"fcp": False, "mtu": 9000, "mode": "write", "field": "packet_size"}),
        ("alibaba_rdma_nfcp_f1_2_mtu_9000_read_packet_rate",
         {"fcp": False, "mtu": 9000, "mode": "read", "field": "packet_size"}),
        ("alibaba_rdma_fcp_f1_2_mtu_1500_write_packet_rate",
         {"fcp": True, "mtu": 1500, "mode": "write", "field": "packet_size"}),
        ("alibaba_rdma_fcp_f1_2_mtu_1500_read_packet_rate",
         {"fcp": True, "mtu": 1500, "mode": "read", "field": "packet_size"}),
        ("alibaba_rdma_fcp_f1_2_mtu_9000_write_packet_rate",
         {"fcp": True, "mtu": 9000, "mode": "write", "field": "packet_size"}),
        ("alibaba_rdma_fcp_f1_2_mtu_9000_read_packet_rate",
         {"fcp": True, "mtu": 9000, "mode": "read", "field": "packet_size"})
    ])
    model_name = "AlibabaRdmaPerformance"
    description = "TBD"
    owner_info = "Manu K S  (manu.ks@fungible.com)"
    positive = False
    platform = FunPlatform.F1

    for internal_chart_name in internal_chart_names:
        dict_data = internal_chart_names[internal_chart_name]
        fcp = dict_data['fcp']
        mtu = dict_data['mtu']
        mode = dict_data['mode']
        field = dict_data['field']
        if field == "bandwidth":
            y1_axis_title = PerfUnit.UNIT_GBITS_PER_SEC
            output_name = "output_{}_bandwidth".format(mode)
            chart_name = "IB {} {} {} bandwidth".format(mode, fcp, mtu)

        elif field == "packet_size":
            y1_axis_title = PerfUnit.UNIT_MPPS
            output_name = "output_{}_msg_rate".format(mode)
            chart_name = "IB {} {} {} message rate".format(mode, fcp, mtu)

        if mtu == 1500:
            bw_size_list = [1, 128, 256, 512, 1024, 4096]
        elif mtu == 9000:
            bw_size_list = [4096]

        if mode == 'write':
            source = "https://github.com/fungible-inc/Integration/blob/93cbceb27e5be0dfb3b79325c813d36789c5fe3d/fun_test/" \
                     "scripts/networking/funcp/rdma_write_perf.py"
        else:
            source = ""

        qp_list = [1, 2, 4, 8, 16, 32]
        for bw_size in bw_size_list:
            data_sets = []
            internal_chart_name_size = internal_chart_name + "_size_{}".format(bw_size)
            chart_name_size = chart_name + " size{}".format(bw_size)
            for qp in qp_list:
                one_data_set = {}
                inputs = {
                    "input_size_bandwidth": bw_size,
                    "input_platform": platform,
                    "input_operation": mode,
                    "input_size_latency": -1,
                    "input_fcp": fcp,
                    "input_qp": qp,
                    "input_mtu": mtu
                }

                output = {
                    "name": output_name,
                    "unit": y1_axis_title,
                    "min": 0,
                    "max": -1,
                    "expected": -1,
                    "reference": -1
                }
                name = "qp {}".format(qp)
                one_data_set["name"] = name
                one_data_set["inputs"] = inputs
                one_data_set["output"] = output
                data_sets.append(one_data_set.copy())

            metric_id = LastMetricId.get_next_id()
            MetricChart(chart_name=chart_name_size,
                        metric_id=metric_id,
                        internal_chart_name=internal_chart_name_size,
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
            for i in data_sets:
                print i

if __name__ == "__main_manual_db_entry__":
    date_time = parser.parse("2019-08-27 04:45:25.582587-07:00")
    volume = "Multi_host_TCP"
    block_size = "4k"
    size = "128GB"
    num_ssd = 12
    num_volume = 12

    test = "tiHostFioRandRead"
    operation = "randread"
    read_values = [[1, 103321.475198, 413281, 106, 118, 118, 120, 146, "fio_tcp_randread_blt_1_1_vol_12"],
                   [32, 2728469.774469, 10913873, 133, 170, 189, 234, 387, "fio_tcp_randread_blt_32_1_vol_12"],
                   [64, 4541224.44247, 18164891, 161, 218, 248, 328, 593, "fio_tcp_randread_blt_32_2_vol_12"],
                   [128, 5257247.213338999, 21028982, 285, 397, 475, 780, 1513, "fio_tcp_randread_blt_32_4_vol_12"]]

    for value in read_values:
        one_entry = BltVolumePerformance(input_date_time=date_time,
                                         input_volume_type=volume,
                                         input_test=test,
                                         input_block_size=block_size,
                                         input_io_depth=value[0],
                                         input_io_size=size,
                                         input_operation=operation,
                                         input_num_ssd=num_ssd,
                                         input_num_volume=num_volume,
                                         input_fio_job_name=value[8],
                                         input_version=-1,
                                         output_write_iops=-1,
                                         output_read_iops=value[1],
                                         output_write_throughput=-1,
                                         output_read_throughput=value[2],
                                         output_write_avg_latency=-1,
                                         output_read_avg_latency=value[3],
                                         output_write_90_latency=-1,
                                         output_write_95_latency=-1,
                                         output_write_99_latency=-1,
                                         output_write_99_99_latency=-1,
                                         output_read_90_latency=value[4],
                                         output_read_95_latency=value[5],
                                         output_read_99_latency=value[6],
                                         output_read_99_99_latency=value[7],
                                         output_write_iops_unit=PerfUnit.UNIT_OPS,
                                         output_read_iops_unit=PerfUnit.UNIT_OPS,
                                         output_write_throughput_unit=PerfUnit.UNIT_MBYTES_PER_SEC,
                                         output_read_throughput_unit=PerfUnit.UNIT_MBYTES_PER_SEC,
                                         output_write_avg_latency_unit=PerfUnit.UNIT_USECS,
                                         output_read_avg_latency_unit=PerfUnit.UNIT_USECS,
                                         output_write_90_latency_unit=PerfUnit.UNIT_USECS,
                                         output_write_95_latency_unit=PerfUnit.UNIT_USECS,
                                         output_write_99_latency_unit=PerfUnit.UNIT_USECS,
                                         output_write_99_99_latency_unit=PerfUnit.UNIT_USECS,
                                         output_read_90_latency_unit=PerfUnit.UNIT_USECS,
                                         output_read_95_latency_unit=PerfUnit.UNIT_USECS,
                                         output_read_99_latency_unit=PerfUnit.UNIT_USECS,
                                         output_read_99_99_latency_unit=PerfUnit.UNIT_USECS).save()

    test = "tiHostFioRandWrite"
    operation = "randwrite"
    write_values = [[1, 228194.69089600001, 912772, 43, 43, 44, 60, 189, "fio_tcp_randwrite_blt_1_1_vol_12"],
                    [8, 1343489.0677180002, 5373950, 61, 100, 122, 163, 468, "fio_tcp_randwrite_blt_8_1_vol_12"],
                    [16, 2076670.642782, 8306677, 82, 137, 157, 211, 630, "fio_tcp_randwrite_blt_16_1_vol_12"],
                    [32, 2917874.290518, 11671490, 124, 179, 206, 308, 1792, "fio_tcp_randwrite_blt_32_1_vol_12"]]

    for value in write_values:
        one_entry = BltVolumePerformance(input_date_time=date_time,
                                         input_volume_type=volume,
                                         input_test=test,
                                         input_block_size=block_size,
                                         input_io_depth=value[0],
                                         input_io_size=size,
                                         input_operation=operation,
                                         input_num_ssd=num_ssd,
                                         input_num_volume=num_volume,
                                         input_fio_job_name=value[8],
                                         input_version=-1,
                                         output_write_iops=value[1],
                                         output_read_iops=-1,
                                         output_write_throughput=value[2],
                                         output_read_throughput=-1,
                                         output_write_avg_latency=value[3],
                                         output_read_avg_latency=-1,
                                         output_write_90_latency=value[4],
                                         output_write_95_latency=value[5],
                                         output_write_99_latency=value[6],
                                         output_write_99_99_latency=value[7],
                                         output_read_90_latency=-1,
                                         output_read_95_latency=-1,
                                         output_read_99_latency=-1,
                                         output_read_99_99_latency=-1,
                                         output_write_iops_unit=PerfUnit.UNIT_OPS,
                                         output_read_iops_unit=PerfUnit.UNIT_OPS,
                                         output_write_throughput_unit=PerfUnit.UNIT_MBYTES_PER_SEC,
                                         output_read_throughput_unit=PerfUnit.UNIT_MBYTES_PER_SEC,
                                         output_write_avg_latency_unit=PerfUnit.UNIT_USECS,
                                         output_read_avg_latency_unit=PerfUnit.UNIT_USECS,
                                         output_write_90_latency_unit=PerfUnit.UNIT_USECS,
                                         output_write_95_latency_unit=PerfUnit.UNIT_USECS,
                                         output_write_99_latency_unit=PerfUnit.UNIT_USECS,
                                         output_write_99_99_latency_unit=PerfUnit.UNIT_USECS,
                                         output_read_90_latency_unit=PerfUnit.UNIT_USECS,
                                         output_read_95_latency_unit=PerfUnit.UNIT_USECS,
                                         output_read_99_latency_unit=PerfUnit.UNIT_USECS,
                                         output_read_99_99_latency_unit=PerfUnit.UNIT_USECS).save()

    print "added data for 12 hosts 12 volumes manually"


def set_offloads_hu(chart):
    base_line_date = datetime(year=2019, month=8, day=20, minute=0, hour=0, second=0)
    if chart:
        if chart.leaf:
            internal_chart_name = chart.internal_chart_name + "_non_lso"
            data_sets = json.loads(chart.data_sets)
            for data_set in data_sets:
                data_set["inputs"]["input_offloads"] = True
            chart.data_sets = json.dumps(data_sets)
            chart.save()
            for data_set in data_sets:
                data_set["inputs"]["input_offloads"] = False
                data_set["output"]["reference"] = -1
            ml.create_leaf(chart_name=chart.chart_name, internal_chart_name=internal_chart_name, data_sets=data_sets,
                           leaf=True, description=chart.description,
                           owner_info=chart.owner_info, source=chart.source,
                           positive=chart.positive, y1_axis_title=chart.y1_axis_title,
                           visualization_unit=chart.visualization_unit,
                           metric_model_name=chart.metric_model_name,
                           base_line_date=base_line_date,
                           work_in_progress=False, children=[], jira_ids=[], platform=FunPlatform.F1,
                           peer_ids=[], creator=TEAM_REGRESSION_EMAIL,
                           workspace_ids=[])
        else:
            internal_chart_name = chart.internal_chart_name + "_non_lso"
            ml.create_container(chart_name=chart.chart_name, internal_chart_name=internal_chart_name,
                                platform=FunPlatform.F1,
                                owner_info=chart.owner_info,
                                source=chart.source, base_line_date=base_line_date, workspace_ids=[])
            children = json.loads(chart.children)
            for child in children:
                child_chart = MetricChart.objects.get(metric_id=int(child))
                set_offloads_hu(chart=child_chart)


if __name__ == "__main__set_offloads":
    metric_id = 1055
    chart = MetricChart.objects.get(metric_id=metric_id)
    set_offloads_hu(chart=chart)
    print "added hu_nu_nfcp non lso"

if __name__ == "__main_qdepth256__":
    # IOPS charts
    iops_metric_ids = [1075, 1076, 1077, 843]
    for metric_id in iops_metric_ids:
        chart = MetricChart.objects.get(metric_id=metric_id)
        print(chart.chart_name)
        data_sets = json.loads(chart.data_sets)
        one_data_set = data_sets[0].copy()
        inputs = one_data_set["inputs"].copy()
        input_fio_job_name = inputs["input_fio_job_name"]
        inputs["input_fio_job_name"] = input_fio_job_name.replace("1_1", "32_8")
        one_data_set["inputs"] = inputs
        one_data_set["name"] = "qd256"
        one_data_set["output"] = {'name': 'output_read_iops',
                                  'reference': -1,
                                  'min': 0,
                                  'max': -1,
                                  'expected': -1,
                                  'unit': PerfUnit.UNIT_OPS}
        data_sets.append(one_data_set)
        print(data_sets)
        chart.data_sets = json.dumps(data_sets)
        chart.save()

    # Latency charts

    latency_metric_ids = [1078, 1079, 1080, 845]
    for metric_id in latency_metric_ids:
        chart = MetricChart.objects.get(metric_id=metric_id)
        data_sets = json.loads(chart.data_sets)
        for each_data_set in data_sets:
            input_fio_job_name = each_data_set["inputs"]["input_fio_job_name"]
            each_data_set["inputs"]["input_fio_job_name"] = input_fio_job_name.replace("1_1", "32_8")
            each_data_set["output"]["reference"] = -1
        internal_chart_name = chart.internal_chart_name.replace("qd1", "qd256")
        chart_name = "Latency, QDepth=256"
        latency_charts = ml.create_leaf(chart_name=chart_name,
                                        internal_chart_name=internal_chart_name,
                                        data_sets=data_sets,
                                        leaf=True,
                                        description=chart.description,
                                        owner_info=chart.owner_info,
                                        source=chart.source,
                                        positive=chart.positive,
                                        y1_axis_title=chart.visualization_unit,
                                        visualization_unit=chart.visualization_unit,
                                        metric_model_name=chart.metric_model_name,
                                        base_line_date=chart.base_line_date,
                                        work_in_progress=False,
                                        children=[],
                                        jira_ids=[],
                                        platform=chart.platform,
                                        peer_ids=[],
                                        creator=TEAM_REGRESSION_EMAIL,
                                        workspace_ids=[])

        final_dict = ml.get_dict(chart=latency_charts)
        print json.dumps(final_dict, indent=4)

if __name__ == "__main_attach_dag__":
    dag = {}
    owner_info = "Radhika Naik (radhika.naik@fungible.com)"
    source = "Unknown"
    root_node = "Stripe Volume"
    types = ["NVMe/TCP"]
    hosts = ["Multi Host"]
    operations = ["Random Read", "Random Write"]
    qdepths = [16, 32, 64, 128, 256]
    base_line_date = datetime(year=2019, month=8, day=20, minute=0, hour=0, second=0)
    root_chart = ml.create_container(chart_name=root_node, internal_chart_name=root_node, platform=FunPlatform.F1,
                                     owner_info=owner_info,
                                     source=source, base_line_date=base_line_date, workspace_ids=[1891])
    for type in types:
        type_chart = ml.create_container(chart_name=type, internal_chart_name=type,
                                         platform=FunPlatform.F1,
                                         owner_info=owner_info,
                                         source=source, base_line_date=base_line_date, workspace_ids=[])
        root_chart.add_child(child_id=type_chart.metric_id)
        for host in hosts:
            host_chart = ml.create_container(chart_name=host, internal_chart_name=host, platform=FunPlatform.F1,
                                             owner_info=owner_info,
                                             source=source, base_line_date=base_line_date, workspace_ids=[])
            type_chart.add_child(child_id=host_chart.metric_id)
            for operation in operations:
                operation_chart = ml.create_container(chart_name=operation, internal_chart_name=operation,
                                                      platform=FunPlatform.F1,
                                                      owner_info=owner_info,
                                                      source=source, base_line_date=base_line_date, workspace_ids=[])
                host_chart.add_child(child_id=operation_chart.metric_id)
                iops_chart = ml.create_leaf(chart_name="IOPS", internal_chart_name="IOPS", data_sets=[], leaf=True,
                                            description="TBD",
                                            owner_info=owner_info, source=source,
                                            positive=True, y1_axis_title=PerfUnit.UNIT_OPS,
                                            visualization_unit=PerfUnit.UNIT_OPS,
                                            metric_model_name="AlibabaPerformance",
                                            base_line_date=base_line_date,
                                            work_in_progress=False, children=[], jira_ids=[], platform=FunPlatform.F1,
                                            peer_ids=[], creator=TEAM_REGRESSION_EMAIL,
                                            workspace_ids=[])
                iops_chart.fix_children_weights()
                operation_chart.add_child(child_id=iops_chart.metric_id)
                for qdepth in qdepths:
                    chart_name = "Latency, QDepth=" + str(qdepth)
                    latency_chart = ml.create_leaf(chart_name=chart_name, internal_chart_name=chart_name, data_sets=[],
                                                   leaf=True, description="TBD",
                                                   owner_info=owner_info, source=source,
                                                   positive=False, y1_axis_title=PerfUnit.UNIT_USECS,
                                                   visualization_unit=PerfUnit.UNIT_USECS,
                                                   metric_model_name="AlibabaPerformance",
                                                   base_line_date=base_line_date,
                                                   work_in_progress=False, children=[], jira_ids=[],
                                                   platform=FunPlatform.F1,
                                                   peer_ids=[], creator=TEAM_REGRESSION_EMAIL,
                                                   workspace_ids=[])
                    latency_chart.fix_children_weights()
                    operation_chart.add_child(child_id=latency_chart.metric_id)
                operation_chart.fix_children_weights()
            host_chart.fix_children_weights()
        type_chart.fix_children_weights()
    root_chart.fix_children_weights()
    final_dict = ml.get_dict(chart=root_chart)
    print json.dumps(final_dict)

if __name__ == "__main_inspur_fix__":
    charts = MetricChart.objects.all()
    for chart in charts:
        if "inspur" in chart.internal_chart_name and chart.leaf:
            if "latency" in chart.internal_chart_name:
                chart.positive = False
            elif "iops" in chart.internal_chart_name:
                chart.positive = True
            elif "ratio" in chart.internal_chart_name:
                chart.positive = True
            elif "time" in chart.internal_chart_name:
                chart.positive = False
            chart.save()
            print "fixed the chart: {}, {}".format(chart.chart_name, chart.internal_chart_name)

if __name__ == "__main__apple":
    internal_chart_names = ["apple_rand_read_mrsw_tcp_output_bandwidth", "apple_rand_read_mrsw_tcp_output_latency", "apple_rand_read_mrsw_tcp_output_iops"]
    for internal_chart_name in internal_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        mmt = MileStoneMarkers(metric_id=chart.metric_id, milestone_date=datetime(year=2019, month=9, day=8),
                               milestone_name="Moved to new host")
        mmt.save()


if __name__ == "__main__":
    # underscore problem
    metric_ids = [318, 319]
    for metric_id in metric_ids:
        # changing the input_metric_name in the filter
        chart = MetricChart.objects.get(metric_id=metric_id)
        data_sets = json.loads(chart.data_sets)
        metric_name = data_sets[0]['inputs']['input_metric_name']
        data_sets[0]['inputs']['input_metric_name'] = metric_name.replace(' ', '_')
        print(data_sets)
        chart.data_sets = json.dumps(data_sets)
        chart.save()

        # changing the input_metric_name in the data base
        metric_model_name = chart.metric_model_name
        print (metric_model_name)
        model_data = eval(metric_model_name).objects.all()
        for each_data in model_data:
            input_metric_name = each_data.input_metric_name
            each_data.input_metric_name = input_metric_name.replace(' ', '_')
            each_data.save()


    # Inspur charts added vol 4,8

    metric_ids = [803, 804, 805, 806, 807, 808, 809, 810, 811, 812]
    for metric_id in metric_ids:
        chart = MetricChart.objects.get(metric_id=metric_id)
        data_sets = json.loads(chart.data_sets)
        new_data_sets=[]
        for each_data in data_sets:
            for vol in [4, 8]:
                inputs = each_data['inputs'].copy()
                output = each_data['output'].copy()
                name = each_data['name']
                new_each_data = {}

                input_fio_job_name = inputs['input_fio_job_name']
                iodepth = re.search(r'write_(\d+)', input_fio_job_name).group(1)
                inputs['input_fio_job_name'] = input_fio_job_name.replace('write_{}'.format(iodepth),
                                                                          "write_iodepth_{}_vol_{}".format(iodepth, vol))
                new_name = re.sub(r'\d+ vol', "{} vol".format(vol), name)
                output["reference"] = -1
                new_each_data['inputs'] = inputs
                new_each_data['name'] = new_name
                new_each_data['output'] = output
                # print (new_each_data)
                new_data_sets.append(new_each_data.copy())
        new_data_sets[2], new_data_sets[1] = new_data_sets[1], new_data_sets[2]
        data_sets += new_data_sets
        for i in data_sets:
            print i
        print ("next")
        chart.data_sets = json.dumps(data_sets)
        chart.save()

    # Inspur charts iodepth 96

    internal_chart_name = "inspur_rand_read_write_qd96_8k_block_output_iops"
    metric_model_name = "BltVolumePerformance"
    description = "TBD"
    owner_info = "Ravi Hulle (ravi.hulle@fungible.com)"
    source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/" \
             "ec_inspur_fs_teramark_multivolume.py"
    positive = True
    y1_axis_title = PerfUnit.UNIT_OPS
    platform = FunPlatform.F1
    base_line_date = datetime(year=2019, month=5, day=15, minute=0, hour=0, second=0)
    chart_name = 'IOPS, QDepth=96'
    data_sets = []
    for vol in [4, 8]:
        input_fio_job_name = "inspur_8k_random_read_write_iodepth_96_vol_{}".format(vol)
        inputs = {
            "input_platform": platform,
            "input_fio_job_name": input_fio_job_name
        }
        for operation in ["read", "write"]:
            one_data_set = {}
            name = "{}({} vols)".format(operation, vol)
            output_name = "output_{}_iops".format(operation)
            output = {
                "name": output_name,
                "unit": y1_axis_title,
                "min": 0,
                "max": -1,
                "expected": -1,
                "reference": -1
            }
            one_data_set["name"] = name
            one_data_set["inputs"] = inputs
            one_data_set["output"] = output
            data_sets.append(one_data_set.copy())

    iops_charts = ml.create_leaf(chart_name=chart_name,
                                 internal_chart_name=internal_chart_name,
                                 data_sets=data_sets,
                                 leaf=True,
                                 description=description,
                                 owner_info=owner_info,
                                 source=source,
                                 positive=positive,
                                 y1_axis_title=y1_axis_title,
                                 visualization_unit=y1_axis_title,
                                 metric_model_name=metric_model_name,
                                 base_line_date=base_line_date,
                                 work_in_progress=False,
                                 children=[],
                                 jira_ids=[],
                                 platform=platform,
                                 peer_ids=[],
                                 creator=TEAM_REGRESSION_EMAIL,
                                 workspace_ids=[])

    final_dict = ml.get_dict(chart=iops_charts)
    print json.dumps(final_dict, indent=4)

