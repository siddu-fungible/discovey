from web.fun_test.maintenance_old import *
from dateutil import parser
from web.fun_test.metrics_lib import MetricLib
from web.fun_test.models import *
from django.forms.models import model_to_dict
from web.fun_test.models_helper import add_metrics_data_run_time

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
                        teramark_metrics = f1_metric
                        break

        tera_marks = teramark_metrics["children"]
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
                                     source=source, base_line_date=base_line_date, workspace_ids=[1480])
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
                iops_chart = ml.create_leaf(chart_name="IOPS", internal_chart_name=host + operation, data_sets=[],
                                            leaf=True,
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
                    chart_name = host + operation + "Latency, QDepth=" + str(qdepth)
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
    internal_chart_names = ["apple_rand_read_mrsw_tcp_output_bandwidth", "apple_rand_read_mrsw_tcp_output_latency",
                            "apple_rand_read_mrsw_tcp_output_iops"]
    for internal_chart_name in internal_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        mmt = MileStoneMarkers(metric_id=chart.metric_id, milestone_date=datetime(year=2019, month=9, day=8),
                               milestone_name="Moved to new host")
        mmt.save()

if __name__ == "__main_inspur_iodepth_96__":
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
        new_data_sets = []
        for each_data in data_sets:
            for vol in [4, 8]:
                inputs = each_data['inputs'].copy()
                output = each_data['output'].copy()
                name = each_data['name']
                new_each_data = {}

                input_fio_job_name = inputs['input_fio_job_name']
                iodepth = re.search(r'write_(\d+)', input_fio_job_name).group(1)
                inputs['input_fio_job_name'] = input_fio_job_name.replace('write_{}'.format(iodepth),
                                                                          "write_iodepth_{}_vol_{}".format(iodepth,
                                                                                                           vol))
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

if __name__ == "__main__trailingrst":
    metric_ids = [273, 287, 279, 1126, 1127, 1128]
    for metric_id in metric_ids:
        chart = MetricChart.objects.get(metric_id=metric_id)
        data_sets = chart.get_data_sets()
        data_set = data_sets[0]
        data_set["name"] = "trailingrst_jpg"
        data_set["inputs"]["input_image"] = "trailingrst_jpg"
        data_set["output"]["expected"] = -1
        data_set["output"]["reference"] = -1
        data_sets = chart.get_data_sets()
        data_sets.append(data_set)
        chart.data_sets = json.dumps(data_sets)
        chart.save()
    print "set trailingrst dataset for jpeg metrics"

if __name__ == "__main__pke_tls":
    with open(METRICS_BASE_DATA_FILE, "r") as f:
        metrics = json.load(f)
        for metric in metrics:
            if metric["label"] == "F1":
                f1_metrics = metric["children"]
                for f1_metric in f1_metrics:
                    if f1_metric["label"] == "TeraMarks":
                        teramark_metrics = f1_metric
                    if f1_metric["label"] == "Security":
                        security_metrics = f1_metric

    tera_marks = teramark_metrics["children"]
    for tera_mark in tera_marks:
        if tera_mark["name"] == "TeraMark Security":
            for children in tera_mark["children"]:
                if children["name"] == "TeraMark PKE":
                    result = set_internal_name(children)
                    print json.dumps(result, indent=4)

    security_childrens = security_metrics["children"]
    for security_children in security_childrens:
        if security_children["name"] == "PKE TLS":
            result = set_internal_name(security_children)
            print json.dumps(result, indent=4)

if __name__ == "__main_dfa_regex__":
    with open(METRICS_BASE_DATA_FILE, "r") as f:
        metrics = json.load(f)
        for metric in metrics:
            if metric["label"] == "F1":
                f1_metrics = metric["children"]
                for f1_metric in f1_metrics:
                    if f1_metric["label"] == "TeraMarks":
                        teramark_metrics = f1_metric

    tera_mark_childrens = teramark_metrics["children"]
    for tera_mark_children in tera_mark_childrens:
        if tera_mark_children["name"] == "Regex":
            result = set_internal_name(tera_mark_children)
            print json.dumps(result, indent=4)

if __name__ == "__main_remove_milestones__":
    mmt = MileStoneMarkers.objects.all()
    for mm in mmt:
        if "Tape-out" in mm.milestone_name or "F1" in mm.milestone_name:
            mm.delete()

if __name__ == "__main__alibaba":
    metric_ids = [900, 901]
    for metric_id in metric_ids:
        chart = MetricChart.objects.get(metric_id=metric_id)
        children = chart.get_children()
        for child in children:
            child_chart = MetricChart.objects.get(metric_id=int(child))
            data_sets = child_chart.get_data_sets()
            for data_set in data_sets:
                data_set["inputs"]["input_num_ssd"] = 1
            child_chart.data_sets = json.dumps(data_sets)
            child_chart.save()

    read_copy_chart = MetricChart.objects.get(metric_id=890)
    write_copy_chart = MetricChart.objects.get(metric_id=895)
    read_iops_chart = MetricChart.objects.get(metric_id=888)
    write_iops_chart = MetricChart.objects.get(metric_id=889)
    operations = ["Random Read", "Random Write"]
    qdepths = OrderedDict([(1, [1, 1]), (32, [1, 32]), (64, [1, 64]), (128, [2, 64]), (256, [4, 64]), (1024, [16, 64])])
    owner_info = "Divya Krishnankutty (divya.krishnankutty@fungible.com)"
    source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/pocs/alibaba/alibaba_raw_multi_vol_pcie_via_vm.py"
    base_line_date = datetime(year=2019, month=9, day=25, minute=0, hour=0, second=0)
    for operation in operations:
        internal_chart_name = "alibaba_bmv_storage_local_ssd_4_" + operation.replace(" ", "_").lower()
        root_chart = ml.create_container(chart_name=operation, internal_chart_name=internal_chart_name,
                                         platform=FunPlatform.F1,
                                         owner_info=owner_info,
                                         source=source, base_line_date=base_line_date, workspace_ids=[])
        iops_data_sets = []
        if "Read" in operation:
            iops_internal_chart_name = read_iops_chart.internal_chart_name.replace("ssd", "ssd_4")
            iops_description = read_iops_chart.description
            op = "randread"
            output = "output_read_iops"
        else:
            iops_internal_chart_name = write_iops_chart.internal_chart_name.replace("ssd", "ssd_4")
            iops_description = write_iops_chart.description
            op = "randwrite"
            output = "output_write_iops"

        for qdepth in qdepths:
            one_data_set = {}
            one_data_set["name"] = str(qdepth)
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_num_ssd"] = 4
            one_data_set["inputs"]["input_platform"] = FunPlatform.F1
            one_data_set["inputs"]["input_test"] = op
            one_data_set["inputs"]["input_num_threads"] = qdepths[qdepth][0]
            one_data_set["inputs"]["input_io_depth"] = qdepths[qdepth][1]
            one_data_set["output"] = {"name": output, "min": 0, "max": -1, "expected": -1, "reference": -1,
                                      "unit": PerfUnit.UNIT_OPS}
            iops_data_sets.append(one_data_set)
        iops_chart = ml.create_leaf(chart_name="IOPS", internal_chart_name=iops_internal_chart_name,
                                    data_sets=iops_data_sets, leaf=True,
                                    description=iops_description,
                                    owner_info=owner_info, source=source,
                                    positive=True, y1_axis_title=PerfUnit.UNIT_OPS,
                                    visualization_unit=PerfUnit.UNIT_OPS,
                                    metric_model_name="AlibabaPerformance",
                                    base_line_date=base_line_date,
                                    work_in_progress=False, children=[], jira_ids=[], platform=FunPlatform.F1,
                                    peer_ids=[], creator=TEAM_REGRESSION_EMAIL,
                                    workspace_ids=[])
        iops_chart.fix_children_weights()
        root_chart.add_child(child_id=iops_chart.metric_id)
        for qdepth in qdepths:
            chart_name = "Latency, Qdepth=" + str(qdepth)
            internal_chart_name = "bmv_storage_local_ssd_4_" + operation.replace(" ", "_").lower() + "_qd" + str(
                qdepth) + "_latency"
            if "read" in internal_chart_name:
                data_sets = read_copy_chart.get_data_sets()
                description = read_copy_chart.description
                y1_axis_title = read_copy_chart.y1_axis_title
            else:
                data_sets = write_copy_chart.get_data_sets()
                description = write_copy_chart.description
                y1_axis_title = write_copy_chart.y1_axis_title
            for data_set in data_sets:
                data_set["inputs"]["input_num_ssd"] = 4
                data_set["inputs"]["input_num_threads"] = qdepths[qdepth][0]
                data_set["inputs"]["input_io_depth"] = qdepths[qdepth][1]
                data_set["output"]["expected"] = -1
                data_set["output"]["reference"] = -1
            latency_chart = ml.create_leaf(chart_name=chart_name, internal_chart_name=internal_chart_name,
                                           data_sets=data_sets, leaf=True,
                                           description=description,
                                           owner_info=owner_info, source=source,
                                           positive=False, y1_axis_title=y1_axis_title,
                                           visualization_unit=y1_axis_title,
                                           metric_model_name="AlibabaPerformance",
                                           base_line_date=base_line_date,
                                           work_in_progress=False, children=[], jira_ids=[], platform=FunPlatform.F1,
                                           peer_ids=[], creator=TEAM_REGRESSION_EMAIL,
                                           workspace_ids=[])
            latency_chart.fix_children_weights()
            root_chart.add_child(child_id=latency_chart.metric_id)
        root_chart.fix_children_weights()
        final_dict = ml.get_dict(chart=root_chart)
        print json.dumps(final_dict)

if __name__ == "__main_crypto_s1__":
    with open(METRICS_BASE_DATA_FILE, "r") as f:
        metrics = json.load(f)
        for metric in metrics:
            if metric["label"] == "F1":
                f1_metrics = metric["children"]
                for f1_metric in f1_metrics:
                    if f1_metric["label"] == "TeraMarks":
                        teramark_metrics = f1_metric

    tera_mark_childrens = teramark_metrics["children"]
    for tera_mark_children in tera_mark_childrens:
        if tera_mark_children["label"] == "Security":
            security_childrens = tera_mark_children["children"]
            for security_children in security_childrens:
                if security_children["name"] == "Crypto raw throughput":
                    result = set_internal_name(security_children)
                    print json.dumps(result, indent=4)

if __name__ == "__main_rebasing__":
    global_setting = MetricsGlobalSettings.objects.first()
    global_setting.cache_valid = False
    global_setting.save()
    entries = MetricChart.objects.all()
    for entry in entries:
        if entry.leaf and entry.platform == FunPlatform.F1:
            to_edit = True
            data_sets = entry.get_data_sets()
            print "checking {} {}".format(entry.chart_name, entry.metric_id)
            for data_set in data_sets:
                if "expected" in data_set["output"] and data_set["output"]["expected"] != -1:
                    to_edit = False
                    break
            if to_edit:
                for data_set in data_sets:
                    if "reference" in data_set["output"]:
                        metric_model = app_config.get_metric_models()[entry.metric_model_name]
                        model_data_all = metric_model.objects.filter(**data_set["inputs"]).order_by(
                            "-input_date_time")[:1]
                        if len(model_data_all):
                            for model_data in model_data_all:
                                output_name = data_set["output"]["name"]
                                if hasattr(model_data, output_name) and hasattr(model_data, output_name + "_unit"):
                                    output_unit = getattr(model_data, output_name + "_unit")
                                    output_value = getattr(model_data, output_name)
                                    data_set_unit = data_set["output"]["unit"]
                                    data_set["output"]["reference"] = output_value
                                    data_set["output"]["unit"] = output_unit
                entry.data_sets = json.dumps(data_sets)
                entry.save()
                print "edited the datasets for {} with metric id {}".format(entry.chart_name, entry.metric_id)

if __name__ == "__main_inspur_12_volumes__":
    metric_ids = {1207: "read", 754: "read_write", 1208: "write", 1209: "read", 755: "read_write", 1210: "write"}
    fio_job_names = ["inspur_8k_random_", "_iodepth_", "_f1_6_vol_12"]
    for key in metric_ids:
        value = metric_ids[key]
        chart = MetricChart.objects.get(metric_id=int(key))
        children = chart.get_children()
        for child in children:
            child_chart = MetricChart.objects.get(metric_id=int(child))
            if "32" in child_chart.internal_chart_name:
                fio_job_name = fio_job_names[0] + value + fio_job_names[1] + "32" + fio_job_names[2]
            elif "64" in child_chart.internal_chart_name:
                fio_job_name = fio_job_names[0] + value + fio_job_names[1] + "64" + fio_job_names[2]
            elif "96" in child_chart.internal_chart_name:
                fio_job_name = fio_job_names[0] + value + fio_job_names[1] + "96" + fio_job_names[2]
            elif "128" in child_chart.internal_chart_name:
                fio_job_name = fio_job_names[0] + value + fio_job_names[1] + "128" + fio_job_names[2]
            else:
                fio_job_name = None
                continue

            if fio_job_name:
                if child_chart.positive:
                    name = value
                    output_names = ["output_read_iops", "output_write_iops"]
                else:
                    name = value + "-avg"
                    output_names = ["output_read_avg_latency", "output_write_avg_latency"]
                data_sets = child_chart.get_data_sets()
                if value == "read_write":
                    for output_name in output_names:
                        if "read" in output_name:
                            rw_name = "read"
                        else:
                            rw_name = "write"
                        one_data_set = {}
                        if "-avg" in name:
                            one_data_set["name"] = rw_name + "-avg(12 vols)"
                            unit = PerfUnit.UNIT_USECS
                        else:
                            one_data_set["name"] = rw_name + "(12 vols)"
                            unit = PerfUnit.UNIT_OPS
                        one_data_set["inputs"] = {}
                        one_data_set["inputs"]["input_platform"] = FunPlatform.F1
                        one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
                        one_data_set["output"] = {"name": output_name, "min": 0, "max": -1, "expected": -1,
                                                  "reference": -1, "unit": unit}
                        data_sets.append(one_data_set)
                else:
                    one_data_set = data_sets[0]
                    one_data_set["name"] = name + "(12 vols)"
                    one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
                    one_data_set["output"]["expected"] = -1
                    one_data_set["output"]["reference"] = -1
                    data_sets = child_chart.get_data_sets()
                    data_sets.append(one_data_set)
                child_chart.data_sets = json.dumps(data_sets)
                child_chart.save()
    print "added 12 volume datasets for 32, 64, 96 and 128 qdepths for Inspur"

if __name__ == "__main_power_perf__":
    metric_model_name = "PowerPerformance"
    description = "TBD"
    owner_info = "Ranganatha Gowda (ranga.gowda@fungible.com)"
    source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/system/frs/start_traffic.py"
    positive = False
    visualization_unit = PerfUnit.UNIT_WATT
    y1_axis_title = PerfUnit.UNIT_WATT
    platform = FunPlatform.F1
    internal_chart_name = "system_power_f1"
    chart_name = "Power"

    data_sets = []
    one_data_set = {}

    inputs = {
        "input_platform": platform,
    }
    output_names = OrderedDict([("output_fs_power", "FS"), ("output_f1_0_power", "F1_0"),
                                ("output_f1_1_power", "F1_1")])
    for output_name in output_names:
        output = {
            "name": output_name,
            "unit": visualization_unit,
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
    base_line_date = datetime(year=2019, month=10, day=13, minute=0, hour=0, second=0)
    power_chart = ml.create_leaf(chart_name=chart_name,
                                 internal_chart_name=internal_chart_name,
                                 data_sets=data_sets,
                                 leaf=True,
                                 description=description,
                                 owner_info=owner_info,
                                 source=source,
                                 positive=positive,
                                 y1_axis_title=y1_axis_title,
                                 visualization_unit=visualization_unit,
                                 metric_model_name=metric_model_name,
                                 base_line_date=base_line_date,
                                 work_in_progress=False,
                                 children=[],
                                 jira_ids=[],
                                 platform=platform,
                                 peer_ids=[],
                                 creator=TEAM_REGRESSION_EMAIL,
                                 workspace_ids=[])

    final_dict = ml.get_dict(chart=power_chart)
    print json.dumps(final_dict, indent=4)

if __name__ == "__main__backup":
    ml.backup_dags()

if __name__ == "__main_rds_client__":
    metric_model_name = "RdsClientPerformance"
    description = "TBD"
    owner_info = "Nazir Ahamed (nazir.ahamed@fungible.com)"
    source = ""
    positive = False
    visualization_unit = PerfUnit.UNIT_MBITS_PER_SEC
    y1_axis_title = PerfUnit.UNIT_MBITS_PER_SEC
    platform = FunPlatform.F1
    internal_chart_name = "rds_client_test_2_hosts_aggbw"
    chart_name = "Aggregate Bandwidth"
    num_hosts = 2
    output_name = "output_aggregate_bandwidth"

    data_sets = []
    one_data_set = {}

    output = {
        "name": output_name,
        "unit": y1_axis_title,
        "min": 0,
        "max": -1,
        "expected": -1,
        "reference": -1
    }
    for msg_rate in [1, 8, 16]:
        for no_of_con in [1, 8, 16]:
            inputs = {
                "input_platform": platform,
                "input_num_hosts": num_hosts,
                "input_msg_rate": msg_rate,
                "input_num_connection": no_of_con
            }
            display_name = "MR {}, TC {}".format(msg_rate, no_of_con)
            one_data_set["name"] = display_name
            one_data_set["inputs"] = inputs
            one_data_set["output"] = output
            data_sets.append(one_data_set.copy())

    metric_id = LastMetricId.get_next_id()
    base_line_date = datetime(year=2019, month=10, day=20, minute=0, hour=0, second=0)
    iops_chart = ml.create_leaf(chart_name=chart_name,
                                internal_chart_name=internal_chart_name,
                                data_sets=data_sets,
                                leaf=True,
                                description=description,
                                owner_info=owner_info,
                                source=source,
                                positive=positive,
                                y1_axis_title=y1_axis_title,
                                visualization_unit=visualization_unit,
                                metric_model_name=metric_model_name,
                                base_line_date=base_line_date,
                                work_in_progress=False,
                                children=[],
                                jira_ids=[],
                                platform=platform,
                                peer_ids=[],
                                creator=TEAM_REGRESSION_EMAIL,
                                workspace_ids=[])

    final_dict = ml.get_dict(chart=iops_chart)
    print json.dumps(final_dict, indent=4)

if __name__ == "__main_inspur_datasets__":
    metric_ids = [1207, 754, 1208, 1209, 755, 1210]
    for metric_id in metric_ids:
        chart = MetricChart.objects.get(metric_id=metric_id)
        children = chart.get_children()
        for child in children:
            child_chart = MetricChart.objects.get(metric_id=int(child))
            data_sets = child_chart.get_data_sets()
            for data_set in data_sets:
                name = data_set["name"]
                if "6 F1" not in name:
                    if "(" in name:
                        index = name.find('(') + 1
                        name = name[:index] + "6 F1s, " + name[index:]
                        data_set["name"] = name
            child_chart.data_sets = json.dumps(data_sets)
            child_chart.save()
    print "changed the name of datasets for 6F1s inspur charts"

if __name__ == "__main_best_value__":
    entries = MetricChart.objects.all()
    for entry in entries:
        if entry.leaf:
            model = app_config.get_metric_models()[entry.metric_model_name]
            data_sets = entry.get_data_sets()
            for data_set in data_sets:
                inputs = data_set["inputs"]
                d = {}
                for input_name, input_value in inputs.iteritems():
                    if input_name == "input_date_time":
                        continue
                    d[input_name] = input_value
                order_by = "-input_date_time"
                result = model.objects.filter(**d).order_by(order_by)[:1]
                result = result.first() if len(result) else None
                output_name = data_set["output"]["name"]
                best_value = getattr(result, output_name) if result else -1
                data_set["output"]["best"] = best_value
            entry.data_sets = json.dumps(data_sets)
            entry.save()
    print "added best value for all datasets"

if __name__ == "__main_FCP__":
    root = "FCP"
    categories = ["NVMe", "NVMe/TCP", "NVMe/FunTCP"]
    leaves = ["IOPS", "Throughput", "Latency"]
    latency_ds = ["avg", "50%", "90%", "95%", "99%", "99.5%", "99.99%"]
    owner_info = "Manu K S (manu.ks@fungible.com)"
    source = "Unknown"
    base_line_date = datetime(year=2019, month=10, day=29, minute=0, hour=0, second=0)
    description = "TBD"
    model_name = "NvmeFcpPerformance"
    internal_name = "teramarks_storage_fcp"
    root_chart = ml.create_container(chart_name=root, internal_chart_name=internal_name,
                                     platform=FunPlatform.F1,
                                     owner_info=owner_info,
                                     source=source, base_line_date=base_line_date, workspace_ids=[])
    for category in categories:
        internal_chart_name = internal_name + "_" + category.replace("/", "_").lower()
        category_chart = ml.create_container(chart_name=category, internal_chart_name=internal_chart_name,
                                             platform=FunPlatform.F1,
                                             owner_info=owner_info,
                                             source=source, base_line_date=base_line_date, workspace_ids=[])
        inputs = {"input_platform": FunPlatform.F1,
                  "input_block_size": 4096,
                  "input_operation": "read",
                  "input_test_case": category}
        if category != "NVMe":
            for leaf in leaves:
                data_sets = []
                if "Latency" in leaf:
                    positive = False
                    y1_axis_title = PerfUnit.UNIT_USECS
                    output = "output_read_latency_"
                    for ds in latency_ds:
                        if "avg" in ds:
                            output_name = output + "avg"
                        elif "99.99%" in ds:
                            output_name = output + "9999"
                        elif "99.5%" in ds:
                            output_name = output + "9950"
                        elif "99%" in ds:
                            output_name = output + "99"
                        elif "95%" in ds:
                            output_name = output + "95"
                        elif "90%" in ds:
                            output_name = output + "90"
                        elif "50%" in ds:
                            output_name = output + "50"
                        one_data_set = {}
                        one_data_set["name"] = ds
                        one_data_set["inputs"] = inputs
                        one_data_set["output"] = {"name": output_name,
                                                  "min": 0,
                                                  "max": -1,
                                                  "expected": -1,
                                                  "reference": -1,
                                                  "best": -1,
                                                  "unit": y1_axis_title}
                        data_sets.append(one_data_set)
                else:
                    positive = True
                    name = "read"
                    if "IOPS" in leaf:
                        y1_axis_title = PerfUnit.UNIT_OPS
                        output_name = "output_read_iops"
                    else:
                        y1_axis_title = PerfUnit.UNIT_GBITS_PER_SEC
                        output_name = "output_read_bw"
                    one_data_set = {}
                    one_data_set["name"] = name
                    one_data_set["inputs"] = inputs
                    one_data_set["output"] = {"name": output_name,
                                              "min": 0,
                                              "max": -1,
                                              "expected": -1,
                                              "reference": -1,
                                              "best": -1,
                                              "unit": y1_axis_title}
                    data_sets.append(one_data_set)

                internal_chart_name = internal_chart_name + "_" + leaf.lower()
                chart = ml.create_leaf(chart_name=leaf, internal_chart_name=internal_chart_name,
                                       data_sets=data_sets, leaf=True,
                                       description=description,
                                       owner_info=owner_info, source=source,
                                       positive=positive, y1_axis_title=y1_axis_title,
                                       visualization_unit=y1_axis_title,
                                       metric_model_name=model_name,
                                       base_line_date=base_line_date,
                                       work_in_progress=False, children=[], jira_ids=[], platform=FunPlatform.F1,
                                       peer_ids=[], creator=TEAM_REGRESSION_EMAIL,
                                       workspace_ids=[])
                chart.fix_children_weights()
                category_chart.add_child(chart.metric_id)
        category_chart.fix_children_weights()
        root_chart.add_child(child_id=category_chart.metric_id)
    root_chart.fix_children_weights()
    final_dict = ml.get_dict(chart=root_chart)
    print json.dumps(final_dict)

if __name__ == "__main_FCP_NVMe__":
    internal_chart_name = "teramarks_storage_fcp_nvme"
    leaves = ["IOPS", "Throughput", "Latency - 1 Vol(s)", "Latency - 2 Vol(s)", "Latency - 4 Vol(s)", "Latency - 8 "
                                                                                                      "Vol(s)",
              "Latency - 12 Vol(s)"]
    volumes = [1, 2, 4, 8, 12]
    latency_ds = ["avg", "50%", "90%", "95%", "99%", "99.5%", "99.99%"]
    owner_info = "Manu K S (manu.ks@fungible.com)"
    source = "Unknown"
    base_line_date = datetime(year=2019, month=10, day=29, minute=0, hour=0, second=0)
    description = "TBD"
    model_name = "NvmeFcpPerformance"
    inputs = {"input_platform": FunPlatform.F1,
              "input_block_size": 4096,
              "input_operation": "read",
              "input_test_case": "NVMe",
              "input_volumes": 1}
    chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
    for leaf in leaves:
        internal_chart_name = "teramarks_storage_fcp_nvme"
        data_sets = []
        if "Latency" in leaf:
            if "1 Vol" in leaf:
                volume = 1
                internal_name = "latency_" + "1vol"
            elif "- 2 Vol" in leaf:
                volume = 2
                internal_name = "latency_" + "2vol"
            elif "4 Vol" in leaf:
                volume = 4
                internal_name = "latency_" + "4vol"
            elif "8 Vol" in leaf:
                volume = 8
                internal_name = "latency_" + "8vol"
            elif "12 Vol" in leaf:
                volume = 12
                internal_name = "latency_" + "12vol"
            positive = False
            y1_axis_title = PerfUnit.UNIT_USECS
            output = "output_read_latency_"
            for ds in latency_ds:
                if "avg" in ds:
                    output_name = output + "avg"
                elif "99.99%" in ds:
                    output_name = output + "9999"
                elif "99.5%" in ds:
                    output_name = output + "9950"
                elif "99%" in ds:
                    output_name = output + "99"
                elif "95%" in ds:
                    output_name = output + "95"
                elif "90%" in ds:
                    output_name = output + "90"
                elif "50%" in ds:
                    output_name = output + "50"
                one_data_set = {}
                one_data_set["name"] = ds
                inputs["input_volumes"] = volume
                one_data_set["inputs"] = inputs
                one_data_set["output"] = {"name": output_name,
                                          "min": 0,
                                          "max": -1,
                                          "expected": -1,
                                          "reference": -1,
                                          "best": -1,
                                          "unit": y1_axis_title}
                data_sets.append(one_data_set)
        else:
            internal_name = leaf.lower()
            positive = True
            name = "read-"
            if "IOPS" in leaf:
                y1_axis_title = PerfUnit.UNIT_OPS
                output_name = "output_read_iops"
            else:
                y1_axis_title = PerfUnit.UNIT_GBITS_PER_SEC
                output_name = "output_read_bw"
            for volume in volumes:
                one_data_set = {}
                one_data_set["name"] = name + str(volume) + " Vol(s)"
                inputs["input_volumes"] = volume
                one_data_set["inputs"] = inputs
                one_data_set["output"] = {"name": output_name,
                                          "min": 0,
                                          "max": -1,
                                          "expected": -1,
                                          "reference": -1,
                                          "best": -1,
                                          "unit": y1_axis_title}
                data_sets.append(one_data_set)

        internal_chart_name = internal_chart_name + "_" + internal_name
        child_chart = ml.create_leaf(chart_name=leaf, internal_chart_name=internal_chart_name,
                                     data_sets=data_sets, leaf=True,
                                     description=description,
                                     owner_info=owner_info, source=source,
                                     positive=positive, y1_axis_title=y1_axis_title,
                                     visualization_unit=y1_axis_title,
                                     metric_model_name=model_name,
                                     base_line_date=base_line_date,
                                     work_in_progress=False, children=[], jira_ids=[], platform=FunPlatform.F1,
                                     peer_ids=[], creator=TEAM_REGRESSION_EMAIL,
                                     workspace_ids=[])
        child_chart.fix_children_weights()
        chart.add_child(child_chart.metric_id)
    chart.fix_children_weights()
    final_dict = ml.get_dict(chart=chart)
    print json.dumps(final_dict)
    internal_chart_names = ["teramarks_storage_fcp_nvme_tcp_iops_throughput",
                            "teramarks_storage_fcp_nvme_tcp_iops_throughput_latency",
                            "teramarks_storage_fcp_nvme_funtcp_iops_throughput",
                            "teramarks_storage_fcp_nvme_funtcp_iops_throughput_latency"]
    for ic in internal_chart_names:
        change_chart = MetricChart.objects.get(internal_chart_name=ic)
        index = ic.find('_iops')
        if "iops_throughput_latency" in ic:
            internal_name = ic[:index] + "_latency"
        else:
            internal_name = ic[:index] + "_throughput"
        change_chart.internal_chart_name = internal_name
        change_chart.save()

if __name__ == "__main_FCP_nvme__":
    io_depths = OrderedDict([(1, [1, 1]), (8, [1, 8]), (16, [1, 16]), (32, [2, 16]), (64, [4, 16]), (128, [8, 16]),
                             (256, [16, 16])])
    base_line_date = datetime(year=2019, month=10, day=28, minute=0, hour=0, second=0)
    internal_iops_chart_names = ["bmv_storage_local_ssd_4_random_read_iops",
                                 "bmv_storage_local_ssd_4_random_write_iops"]
    for internal_chart_name in internal_iops_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        if "random_read" in internal_chart_name:
            operation = "randread"
            output_name = "output_read_iops"
        else:
            operation = "randwrite"
            output_name = "output_write_iops"
        data_sets = []
        for key, value in io_depths.items():
            one_data_set = {}
            one_data_set["name"] = key
            one_data_set["inputs"] = {"input_test": operation, "input_num_threads": value[1], "input_io_depth":
                value[0], "input_platform": "F1", "input_num_ssd": 4}
            one_data_set["output"] = {"name": output_name, "reference": -1, "min": 0, "max": -1, "unit": "ops",
                                      "expected": -1, "best": -1}
            data_sets.append(one_data_set)
        chart.base_line_date = base_line_date
        chart.data_sets = json.dumps(data_sets)
        chart.save()
    i_names = ["bmv_storage_local_ssd_4_random_read_qd", "bmv_storage_local_ssd_4_random_write_qd"]
    copy_chart = MetricChart.objects.get(internal_chart_name="bmv_storage_local_ssd_4_random_read_qd1_latency")
    for i_name in i_names:
        for key, value in io_depths.items():
            if key == 1:
                internal_name = i_name + "1_latency"
            elif key == 8:
                internal_name = i_name + "8_latency"
            elif key == 16:
                internal_name = i_name + "16_latency"
            elif key == 32:
                internal_name = i_name + "32_latency"
            elif key == 64:
                internal_name = i_name + "64_latency"
            elif key == 128:
                internal_name = i_name + "128_latency"
            elif key == 256:
                internal_name = i_name + "256_latency"

            try:
                chart = MetricChart.objects.get(internal_chart_name=internal_name)
                if chart:
                    chart.base_line_date = base_line_date
                    data_sets = chart.get_data_sets()
                    for data_set in data_sets:
                        data_set["inputs"]["input_io_depth"] = value[0]
                        data_set["inputs"]["input_num_threads"] = value[1]
                        data_set["output"]["reference"] = -1
                        data_set["output"]["min"] = 0
                        data_set["output"]["max"] = -1
                        data_set["output"]["expected"] = -1
                        data_set["output"]["best"] = -1
                    chart.data_sets = json.dumps(data_sets)
                    chart.save()
            except ObjectDoesNotExist:
                data_sets = copy_chart.get_data_sets()
                for data_set in data_sets:
                    data_set["inputs"]["input_io_depth"] = value[0]
                    data_set["inputs"]["input_num_threads"] = value[1]
                    data_set["output"]["reference"] = -1
                    data_set["output"]["min"] = 0
                    data_set["output"]["max"] = -1
                    data_set["output"]["expected"] = -1
                    data_set["output"]["best"] = -1
                ml.create_leaf(chart_name="Latency", internal_chart_name=internal_name,
                               data_sets=data_sets, leaf=True,
                               description=copy_chart.description,
                               owner_info=copy_chart.owner_info, source=copy_chart.source,
                               positive=copy_chart.positive, y1_axis_title=copy_chart.y1_axis_title,
                               visualization_unit=copy_chart.y1_axis_title,
                               metric_model_name=copy_chart.metric_model_name,
                               base_line_date=base_line_date,
                               work_in_progress=False, children=[], jira_ids=[], platform=FunPlatform.F1,
                               peer_ids=[], creator=TEAM_REGRESSION_EMAIL,
                               workspace_ids=[])
    print "edited all the charts for 4 ssd loacl alibaba bmv storage"

if __name__ == "__main_funos_s1__":
    with open(METRICS_BASE_DATA_FILE, "r") as f:
        metrics = json.load(f)
        for metric in metrics:
            if metric["label"] == "F1":
                f1_metrics = metric["children"]
                for f1_metric in f1_metrics:
                    if f1_metric["label"] == "FunOS":
                        fun_os_metrics = f1_metric
                    if f1_metric["label"] == "System":
                        system_metrics = f1_metric

        children_fun_os = fun_os_metrics["children"]
        for child in children_fun_os:
            child_name = child["name"]
            if child_name == "Nucleus" or child_name == "MovingBits":
                result = set_internal_name(child)
                print json.dumps(result)
        result = set_internal_name(system_metrics)
        print json.dumps(result)


if __name__ == "__main_crypto_fastpath__":
    model_name = "CryptoFastPathPerformance"
    algorithms = ["AES_GCM", "AES_XTS", "AES_CBC", "SHA_256"]
    packet_sizes = [64, 354, 1500, 4096]
    y1_axis_title = PerfUnit.UNIT_GBITS_PER_SEC
    base_line_date = datetime(year=2019, month=11, day=1, minute=0, hour=0, second=0)
    for algorithm in algorithms:
        internal_chart_name = algorithm.lower() + "_crypto_fastpath_throughput"
        data_sets = []
        for packet_size in packet_sizes:
            one_data_set = {}
            one_data_set["name"] = str(packet_size) + "B"
            one_data_set["inputs"] = {"input_platform": FunPlatform.F1, "input_algorithm": algorithm,
                                      "input_operation": "Encrypt", "input_pkt_size": packet_size, "input_key_size":
                                          16}
            one_data_set["output"] = {"name": "output_throughput", "min": 0, "max": -1, "expected": -1, "reference":
                -1, "best": -1, "unit": y1_axis_title}
            data_sets.append(one_data_set)
        ml.create_leaf(chart_name=algorithm, internal_chart_name=internal_chart_name,
                       data_sets=data_sets, leaf=True,
                       description="TBD",
                       owner_info="Suren Madineni (suren.madineni@fungible.com)",
                       source="https://github.com/fungible-inc/FunOS/blob/e0f67f6ac777f948117ca1dabb16c511ebd88d7f/apps/cryptotest/crypto_dp_perf.c",
                       positive=True, y1_axis_title=y1_axis_title,
                       visualization_unit=y1_axis_title,
                       metric_model_name=model_name,
                       base_line_date=base_line_date,
                       work_in_progress=False, children=[], jira_ids=[], platform=FunPlatform.F1,
                       peer_ids=[], creator=TEAM_REGRESSION_EMAIL,
                       workspace_ids=[])
    print "created charts for crypto fastpath"

if __name__ == "__main_random_rw_comp__":
    internal_names = "inspur_8141_8k_rand_rw_comp_qd"
    owner_info = "Alagarswamy Devaraj (alagarswamy.devaraj@fungible.com)"
    source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/pocs/inspur/ec_inspur_fs_teramark_multivolume_comp.py"
    model_name = "BltVolumePerformance"
    base_line_date = datetime(year=2019, month=11, day=1, minute=0, hour=0, second=0)
    qdepths = [32, 64, 96, 128]
    fio_job_names = ["inspur_8k_random_read_write_50pctcomp_iodepth_", "_vol_8"]
    output_names = ["Latency", "IOPS"]
    operations = ["read", "write"]
    for qdepth in qdepths:
        for name in output_names:
            internal_chart_name = internal_names + str(qdepth) + "_output_" + name.lower()
            if name == "Latency":
                positive = False
                y1_axis_title = PerfUnit.UNIT_USECS
            else:
                positive = True
                y1_axis_title = PerfUnit.UNIT_OPS
            data_sets = []
            for operation in operations:
                if positive:
                    data_set_name = operation + "(8 vols)"
                    if operation == "read":
                        output_name = "output_read_iops"
                    else:
                        output_name = "output_write_iops"
                else:
                    data_set_name = operation + "-avg(8 vols)"
                    if operation == "read":
                        output_name = "output_read_avg_latency"
                    else:
                        output_name = "output_write_avg_latency"

                one_data_set = {}
                one_data_set["name"] = data_set_name
                one_data_set["inputs"] = {"input_platform": FunPlatform.F1, "input_fio_job_name": fio_job_names[0] +
                                                                                                  str(qdepth) +
                                                                                                  fio_job_names[1]}
                one_data_set["output"] = {"name": output_name, "min": 0, "max": -1, "expected": -1, "best": -1, "reference":
                    -1, "unit": y1_axis_title}
                data_sets.append(one_data_set)
            ml.create_leaf(chart_name=name, internal_chart_name=internal_chart_name,
                           data_sets=data_sets, leaf=True,
                           description="TBD",
                           owner_info=owner_info, source=source,
                           positive=positive, y1_axis_title=y1_axis_title,
                           visualization_unit=y1_axis_title,
                           metric_model_name=model_name,
                           base_line_date=base_line_date,
                           work_in_progress=False, children=[], jira_ids=[], platform=FunPlatform.F1,
                           peer_ids=[], creator=TEAM_REGRESSION_EMAIL,
                           workspace_ids=[])
    print "created charts for inspur random read write compression"

if __name__ == "__main_random_read_write_inspur_comp___":
    owner_info = "Alagarswamy Devaraj (alagarswamy.devaraj@fungible.com)"
    source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/pocs/inspur/ec_inspur_fs_teramark_multivolume_comp.py"
    base_line_date = datetime(year=2019, month=11, day=4, minute=0, hour=0, second=0)
    model_name = "BltVolumePerformance"
    qdepths = [32, 64, 96, 128]
    categories = ["Latency", "IOPS"]
    fio_job_names = ["inspur_8k_random_", "_50pctcomp_iodepth_", "_vol_8"]
    internal_names = ["inspur_8141_8k_rand_rd_comp", "inspur_8141_8k_rand_wr_comp"]
    for internal_name in internal_names:
        root_chart = ml.create_container(chart_name=internal_name, internal_chart_name=internal_name,
                        platform=FunPlatform.F1,
                        owner_info=owner_info,
                        source=source, base_line_date=base_line_date, workspace_ids=[])
        for category in categories:
            if internal_name == "inspur_8141_8k_rand_rd_comp":
                operation = "read"
                output_name = "output_read_"
            else:
                operation = "write"
                output_name = "output_write_"
            if category == "Latency":
                positive = False
                y1_axis_title = PerfUnit.UNIT_USECS
                output_name += "avg_latency"
                name = operation + "-avg(8 vols)"
            else:
                positive = True
                y1_axis_title = PerfUnit.UNIT_OPS
                output_name += "iops"
                name = operation + "(8 vols)"
            for qdepth in qdepths:
                internal_chart_name = internal_name + "_qd" + str(qdepth) + "_output_" + category.lower()
                data_sets = []
                fio_job_name = fio_job_names[0] + operation + fio_job_names[1] + str(qdepth) + fio_job_names[2]
                one_data_set = {}
                one_data_set["name"] = name
                one_data_set["inputs"] = {"input_platform": FunPlatform.F1,
                                          "input_fio_job_name": fio_job_name}
                one_data_set["output"] = {"name": output_name, "min": 0, "max": -1, "expected": -1, "reference": -1,
                                          "best": -1, "unit": y1_axis_title}
                data_sets.append(one_data_set)
                leaf_chart = ml.create_leaf(chart_name=category, internal_chart_name=internal_chart_name,
                               data_sets=data_sets, leaf=True,
                               description="TBD",
                               owner_info=owner_info, source=source,
                               positive=positive, y1_axis_title=y1_axis_title,
                               visualization_unit=y1_axis_title,
                               metric_model_name=model_name,
                               base_line_date=base_line_date,
                               work_in_progress=False, children=[], jira_ids=[], platform=FunPlatform.F1,
                               peer_ids=[], creator=TEAM_REGRESSION_EMAIL,
                               workspace_ids=[])
                leaf_chart.fix_children_weights()
                root_chart.add_child(leaf_chart.metric_id)
        root_chart.fix_children_weights()
        final_dict = ml.get_dict(chart=root_chart)
        print json.dumps(final_dict)
    print "added charts for random read and random write compression charts for inspur"

def create_container(internal_name, chart_name):
    owner_info = "Divya Krishnankutty (divya.krishnankutty@fungible.com)"
    source = "unknown"
    base_line_date = datetime(year=2019, month=11, day=5, minute=0, hour=0, second=0)
    root_chart = ml.create_container(chart_name=chart_name, internal_chart_name=internal_name,
                                     platform=FunPlatform.F1,
                                     owner_info=owner_info,
                                     source=source, base_line_date=base_line_date, workspace_ids=[])
    return root_chart

def encryption_helper(children, root_chart):
    owner_info = "Divya Krishnankutty (divya.krishnankutty@fungible.com)"
    source = "unknown"
    base_line_date = datetime(year=2019, month=11, day=5, minute=0, hour=0, second=0)
    for child in children:
        child_chart = MetricChart.objects.get(metric_id=int(child))
        if child_chart.leaf:
            data_sets = child_chart.get_data_sets()
            for data_set in data_sets:
                data_set["inputs"]["input_encryption"] = False
            child_chart.data_sets = json.dumps(data_sets)
            child_chart.save()
            data_sets = child_chart.get_data_sets()
            for data_set in data_sets:
                data_set["inputs"]["input_encryption"] = True
                data_set["output"]["reference"] = -1
                data_set["output"]["expected"] = -1
                data_set["output"]["best"] = -1
            leaf_chart = ml.create_leaf(chart_name=child_chart.chart_name,
                                        internal_chart_name=child_chart.internal_chart_name + "_encryption_on",
                                        data_sets=data_sets, leaf=True,
                                        description=child_chart.description,
                                        owner_info=owner_info, source=source,
                                        positive=child_chart.positive, y1_axis_title=child_chart.y1_axis_title,
                                        visualization_unit=child_chart.visualization_unit,
                                        metric_model_name=child_chart.metric_model_name,
                                        base_line_date=base_line_date,
                                        work_in_progress=False, children=[], jira_ids=[], platform=FunPlatform.F1,
                                        peer_ids=[], creator=TEAM_REGRESSION_EMAIL,
                                        workspace_ids=[])
            leaf_chart.fix_children_weights()
        else:
            chart_name = child_chart.chart_name
            leaf_chart = create_container(child_chart.internal_chart_name + "_encryption_on", chart_name)
            new_children = child_chart.get_children()
            encryption_helper(new_children, leaf_chart)
        root_chart.add_child(leaf_chart.metric_id)
    root_chart.fix_children_weights()


if __name__ == "__main_encryption_on_local_ssd__":
    internal_names = ["alibaba_bmv_storage_local_ssd_1", "alibaba_bmv_storage_local_ssd_4"]
    for internal_name in internal_names:
        if "ssd_1" in internal_name:
            chart_name = "1 SSD (encryption on)"
        else:
            chart_name = "4 SSD (encryption on)"
        root_chart = create_container(internal_name + "_encryption_on", chart_name)
        chart = MetricChart.objects.get(internal_chart_name=internal_name)
        children = chart.get_children()
        encryption_helper(children, root_chart)
        final_dict = ml.get_dict(chart=root_chart)
        print json.dumps(final_dict)
    print "created encryption on charts for 1SSD and 4SSD"

if __name__ == "__main_other_tree__":
    owner_info = "Bertrand Serlet (bertrand.serlet@fungible.com)"
    source = "Unknown"
    base_line_date = datetime(year=2019, month=11, day=5, minute=0, hour=0, second=0)
    other_node = ml.create_container(chart_name="Other", internal_chart_name="other_tree",
                        platform=FunPlatform.F1,
                        owner_info=owner_info,
                        source=source, base_line_date=base_line_date, workspace_ids=[])
    data_sets = []
    one_data_set = {}
    one_data_set["name"] = "load_mods"
    one_data_set["inputs"] = {}
    one_data_set["output"] = {"name": "output_total_time", "min": 0, "max": -1, "expected": -1, "reference": -1,
                              "best": -1, "unit": PerfUnit.UNIT_SECS}
    chart = ml.create_leaf(chart_name="Time taken on F1 (app=load_mods)", internal_chart_name="load_mods_time_taken",
                   data_sets=data_sets, leaf=True,
                   description="TBD",
                   owner_info=owner_info, source=source,
                   positive=False, y1_axis_title=PerfUnit.UNIT_SECS,
                   visualization_unit=PerfUnit.UNIT_SECS,
                   metric_model_name="FunOnDemandTotalTimePerformance",
                   base_line_date=base_line_date,
                   work_in_progress=False, children=[], jira_ids=[], platform=FunPlatform.F1,
                   peer_ids=[], creator=TEAM_REGRESSION_EMAIL,
                   workspace_ids=[])
    chart.fix_children_weights()
    other_node.add_child(chart.metric_id)
    other_node.fix_children_weights()
    print "added other node as a root"

if __name__ == "__main_backed_up_dag__":
    internal_name = "load_mods_time_taken"
    chart = MetricChart.objects.get(internal_chart_name="load_mods_time_taken")
    data_sets = chart.get_data_sets()
    one_data_set = {}
    one_data_set["name"] = "load_mods"
    one_data_set["inputs"] = {}
    one_data_set["output"] = {"name": "output_total_time", "min": 0, "max": -1, "expected": -1, "reference": -1,
                              "best": -1, "unit": PerfUnit.UNIT_SECS}
    data_sets.append(one_data_set)
    chart.data_sets = json.dumps(data_sets)
    chart.save()
    ml.backup_dags()

if __name__ == "__main_load_mods__":
    internal_name = "load_mods_time_taken"
    chart = MetricChart.objects.get(internal_chart_name=internal_name)
    internal_chart_name = "job_execution_time_fun_on_demand"
    chart.internal_chart_name = internal_chart_name
    data_sets = chart.get_data_sets()
    for data_set in data_sets:
        data_set["name"] = "app=load_mods,target=F1"
    chart.data_sets = json.dumps(data_sets)
    chart.save()

if __name__ == "__main_fs1600__":
    chart = MetricChart.objects.get(internal_chart_name="f1_fs1600")
    chart.internal_chart_name = "fs1600"
    chart.save()
    inspur_chart = MetricChart.objects.get(metric_id=464)
    result = []
    children = inspur_chart.get_children()
    for child in children:
        child_chart = MetricChart.objects.get(metric_id=int(child))
        one_dict = {}
        one_dict["metric_model_name"] = child_chart.metric_model_name
        one_dict["name"] = child_chart.internal_chart_name
        one_dict["label"] = child_chart.chart_name
        one_dict["reference"] = True
        result.append(one_dict)
    print json.dumps(result)

    apple_chart = MetricChart.objects.get(metric_id=431)
    result = []
    children = apple_chart.get_children()
    for child in children:
        child_chart = MetricChart.objects.get(metric_id=int(child))
        one_dict = {}
        one_dict["metric_model_name"] = child_chart.metric_model_name
        one_dict["name"] = child_chart.internal_chart_name
        one_dict["label"] = child_chart.chart_name
        one_dict["reference"] = True
        result.append(one_dict)
    print json.dumps(result)

if __name__ == "__main_fs1600_backup__":
    ml.backup_dags()
    ml.set_global_cache(cache_valid=True)

if __name__ == "__main_48_vols__":
    metric_ids = [743, 744, 746, 745, 750, 751, 753, 752]
    operations = ["read", "write"]
    fio_job_names = ["inspur_8k_random_read_write_iodepth_", "_f1_6_vol_48"]
    for metric_id in metric_ids:
        chart = MetricChart.objects.get(metric_id=metric_id)

        if "QDepth=32" in chart.chart_name:
            fio_job_name = fio_job_names[0] + str(32) + fio_job_names[1]
        elif "QDepth=64" in chart.chart_name:
            fio_job_name = fio_job_names[0] + str(64) + fio_job_names[1]
        elif "QDepth=96" in chart.chart_name:
            fio_job_name = fio_job_names[0] + str(96) + fio_job_names[1]
        elif "QDepth=128" in chart.chart_name:
            fio_job_name = fio_job_names[0] + str(128) + fio_job_names[1]

        read_data_set = {}
        if chart.positive:
            read_data_set["name"] = "read(6 F1s, 48 vols)"
            output_name = "output_read_iops"
            unit = PerfUnit.UNIT_OPS
        else:
            read_data_set["name"] = "read-avg(6 F1s, 48 vols)"
            output_name = "output_read_avg_latency"
            unit = PerfUnit.UNIT_USECS
        read_data_set["inputs"] = {"input_platform": FunPlatform.F1,
                                   "input_fio_job_name": fio_job_name}
        read_data_set["output"] = {"name": output_name, "min": 0, "max": -1, "expected": -1, "best": -1, "reference":
            -1, "unit": unit}

        write_data_set = {}
        if chart.positive:
            write_data_set["name"] = "write(6 F1s, 48 vols)"
            output_name = "output_write_iops"
            unit = PerfUnit.UNIT_OPS
        else:
            write_data_set["name"] = "write-avg(6 F1s, 48 vols)"
            output_name = "output_write_avg_latency"
            unit = PerfUnit.UNIT_USECS
        write_data_set["inputs"] = {"input_platform": FunPlatform.F1,
                                    "input_fio_job_name": fio_job_name}
        write_data_set["output"] = {"name": output_name, "min": 0, "max": -1, "expected": -1, "best": -1, "reference":
            -1, "unit": unit}
        data_sets = chart.get_data_sets()
        data_sets.append(read_data_set)
        data_sets.append(write_data_set)
        chart.data_sets = json.dumps(data_sets)
        chart.save()
    print "added 48 vol datasets for random read write"

if __name__ == "__main_build_props__":
    entries = MetricsDataRunTime.objects.all()
    for entry in entries:
        entry.delete()
    from django.db import transaction
    transaction.set_autocommit(False)
    metric_models = app_config.get_metric_models()
    end_date = get_current_time()
    start_date = end_date - timedelta(days=60)
    date_range = [start_date, end_date]
    jenkins_entries = JenkinsJobIdMap.objects.filter(build_date__range=date_range).order_by("-build_date")
    jenkins_job_id_map = {}
    for entry in jenkins_entries:
        epoch = get_epoch_time_from_datetime(entry.build_date)
        jenkins_job_id_map[epoch] = entry
    print "created the jenkins job id map"
    for metric_model in metric_models:
        print "updating the model {}".format(metric_model)
        try:
            model_entries = metric_models[metric_model].objects.filter(input_date_time__range=date_range).order_by(
                "-input_date_time")
            for model_entry in model_entries:
                model_entry_epoch = get_epoch_time_from_datetime(model_entry.input_date_time)
                if model_entry_epoch in jenkins_job_id_map:
                    entry = jenkins_job_id_map[model_entry_epoch]
                    build_date = entry.build_date
                    result = {}
                    result["lsf_job_id"] = None
                    if entry.lsf_job_id != "" and entry.lsf_job_id != -1:
                        result["lsf_job_id"] = int(entry.lsf_job_id)

                    result["suite_execution_id"] = entry.suite_execution_id if entry.suite_execution_id != -1 else None
                    result["jenkins_build_number"] = entry.jenkins_job_id if entry.jenkins_job_id != -1 else None

                    build_properties = None
                    if entry.build_properties != "":
                        build_properties = json.loads(entry.build_properties)
                    result["build_properties"] = build_properties

                    result["version"] = None
                    if entry.sdk_version != "" and entry.sdk_version != -1:
                        result["version"] = entry.sdk_version
                    result["associated_suites"] = entry.associated_suites if len(entry.associated_suites) else None
                    try:
                        run_time_id = add_metrics_data_run_time(date_time=build_date, run_time=result)
                        model_entry.run_time_id = run_time_id
                        model_entry.save()
                    except Exception as ex:
                        print str(ex)
        except Exception as ex:
            pass
    transaction.commit()
    transaction.set_autocommit(True)

if __name__ == "__main__pr_build_time__":
    owner_info = "Vijay Varkhedi (vijay.varkhedi@fungible.com)"
    source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/system/build_time_performance.py"
    base_line_date = datetime(year=2019, month=11, day=20, minute=0, hour=0, second=0)
    data_sets = []
    one_data_set = {}
    one_data_set["name"] = "pr build"
    one_data_set["inputs"] = {}
    one_data_set["output"] = {"name": "output_total_time", "min": 0, "max": -1, "expected": -1, "reference": -1,
                              "best": -1, "unit": PerfUnit.UNIT_SECS}
    ml.create_leaf(chart_name="PR build time", internal_chart_name="pr_build_time",
                           data_sets=data_sets, leaf=True,
                           description="TBD",
                           owner_info=owner_info, source=source,
                           positive=False, y1_axis_title=PerfUnit.UNIT_SECS,
                           visualization_unit=PerfUnit.UNIT_SECS,
                           metric_model_name="PrBuildTotalTimePerformance",
                           base_line_date=base_line_date,
                           work_in_progress=False, children=[], jira_ids=[], platform=FunPlatform.F1,
                           peer_ids=[], creator=TEAM_REGRESSION_EMAIL,
                           workspace_ids=[])
    print "created pr build chart"

if __name__ == "__main_blt_volume__":
    owner_info = "Saravanan Selvam (saravanan.selvam@fungible.com )"
    source = "TBD"
    base_line_date = datetime(year=2019, month=11, day=20, minute=0, hour=0, second=0)
    model_name = "BltVolumePerformance"
    qdepths = [32, 64, 96, 128]
    categories = ["Latency", "IOPS"]
    container_names = ["8_15_1:4k_RAND_RW_ENCRYPTION,F1(s)=1",
                       "8_15_1:4k_RAND_RD_ENCRYPTION,F1(s)=1",
                       "8_15_1:4k_RAND_WR_ENCRYPTION,F1(s)=1"]
    container_charts = []
    for container_name in container_names:
        container_chart = ml.create_container(chart_name=container_name,
                                              internal_chart_name=container_name,
                                              platform=FunPlatform.F1,
                                              owner_info=owner_info,
                                              source=source,
                                              base_line_date=base_line_date, workspace_ids=[])

        for qdepth in qdepths:
            operation = "read"
            if "RW" in container_name:
                operation = "read_write"
            if "WR" in container_name:
                operation = "write"
            fio_job_name = "inspur_8k_random_{}_encryption_keysize_32_iodepth_{}_vol_8".format(operation, qdepth)

            output_names = ["output_read_iops"]
            if "read_write" in operation:
                output_names = ["output_read_iops", "output_write_iops"]
            if operation == "write":
                output_names = ["output_write_iops"]

            data_sets = []

            y1_axis_title = PerfUnit.UNIT_OPS
            positive = True

            for output_name in output_names:
                one_data_set = {}
                data_set_name = "{}(8 vols)".format("read")
                if output_name == "output_write_iops":
                    data_set_name = "{}(8 vols)".format("write")

                one_data_set["name"] = data_set_name
                one_data_set["inputs"] = {"input_platform": FunPlatform.F1,
                                          "input_fio_job_name": fio_job_name}


                one_data_set["output"] = {"name": output_name,
                                          "min": 0,
                                          "max": -1,
                                          "expected": -1,
                                          "reference": -1,
                                          "best": -1,
                                          "unit": y1_axis_title}
                data_sets.append(one_data_set)

            leaf_chart = ml.create_leaf(chart_name="IOPS, QDepth={}".format(qdepth),
                                        internal_chart_name=internal_chart_name,
                                        data_sets=data_sets,
                                        leaf=True,
                                        description="TBD",
                                        owner_info=owner_info,
                                        source=source,
                                        positive=positive, y1_axis_title=y1_axis_title,
                                        visualization_unit=y1_axis_title,
                                        metric_model_name=model_name,
                                        base_line_date=base_line_date,
                                        work_in_progress=False, children=[], jira_ids=[], platform=FunPlatform.F1,
                                        peer_ids=[], creator=TEAM_REGRESSION_EMAIL,
                                        workspace_ids=[])
            container_chart.fix_children_weights()
            container_chart.add_child(leaf_chart.metric_id)

        container_charts.append(ml.get_dict(chart=container_chart))

    print json.dumps(container_charts, indent=4)

if __name__ == "__main_integration_job__":
    owner_info = "Ashwin S (ashwin.s@fungible.com)"
    source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/system/build_time_performance.py"
    base_line_date = datetime(year=2019, month=11, day=26, minute=0, hour=0, second=0)
    data_sets = []
    one_data_set = {}
    one_data_set["name"] = "integration job"
    one_data_set["inputs"] = {}
    one_data_set["output"] = {"name": "output_total_time", "min": 0, "max": -1, "expected": -1, "reference": -1,
                              "best": -1, "unit": PerfUnit.UNIT_SECS}
    data_sets.append(one_data_set)
    ml.create_leaf(chart_name="Integration job run time", internal_chart_name="integration_job_run_time",
                           data_sets=data_sets, leaf=True,
                           description="TBD",
                           owner_info=owner_info, source=source,
                           positive=False, y1_axis_title=PerfUnit.UNIT_SECS,
                           visualization_unit=PerfUnit.UNIT_SECS,
                           metric_model_name="IntegrationJobBuildTimePerformance",
                           base_line_date=base_line_date,
                           work_in_progress=False, children=[], jira_ids=[], platform=FunPlatform.F1,
                           peer_ids=[], creator=TEAM_REGRESSION_EMAIL,
                           workspace_ids=[])
    print "created Integration job run time chart"

if __name__ == "__main__inspur_qdepth":
    metric_ids = [1141, 1142]
    vols = [4, 8]
    for metric_id in metric_ids:
        chart = MetricChart.objects.get(metric_id=metric_id)
        data_sets = chart.get_data_sets()
        if "iodepth_8" in chart.internal_chart_name:
            fio_job_name = "inspur_8k_random_write_iodepth_8_vol_"
        else:
            fio_job_name = "inspur_8k_random_write_iodepth_16_vol_"
        for vol in vols:
            temp_data_sets = chart.get_data_sets()
            one_data_set = temp_data_sets[0]
            one_data_set["inputs"]["input_fio_job_name"] = fio_job_name + str(vol)
            one_data_set["name"] = "write(" + str(vol) + " vols)"
            one_data_set["output"]["reference"] = -1
            one_data_set["output"]["best"] = -1
            one_data_set["output"]["expected"] = -1
            data_sets.append(one_data_set)
        chart.data_sets = json.dumps(data_sets)
        chart.save()
    print "added filters for qdepth 8 and qdepth 16"

def leaf_recursion(present_dataset, root_chart):
    if type(present_dataset) == list:
        for i in present_dataset:
            leaf_recursion(i, root_chart)

    try:
        base_line_date = datetime(year=2019, month=7, day=15, minute=0, hour=0, second=0)
        internal_chart_name = present_dataset["name"]
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
    except:
        return

    if chart.leaf:
        new_internal_chart_name = chart.internal_chart_name + "_hosts_4"
        data_sets = json.loads(chart.data_sets)
        for each_data_set in data_sets:
            inputs = each_data_set["inputs"]
            inputs["input_hosts"] = 4
        leaf_chart = ml.create_leaf(chart_name=chart.chart_name, internal_chart_name=new_internal_chart_name,
                                    data_sets=data_sets, leaf=True,
                                    description="TBD",
                                    owner_info=chart.owner_info, source=chart.source,
                                    positive=chart.positive, y1_axis_title=chart.y1_axis_title,
                                    visualization_unit=chart.y1_axis_title,
                                    metric_model_name=chart.metric_model_name,
                                    base_line_date=chart.base_line_date,
                                    work_in_progress=False, children=[], jira_ids=[], platform=chart.platform,
                                    peer_ids=[], creator=TEAM_REGRESSION_EMAIL,
                                    workspace_ids=[])
        root_chart.add_child(leaf_chart.metric_id)
        return
    else:
        internal_chart_name = internal_chart_name.replace("host", "4host")
        container = ml.create_container(chart_name=chart.chart_name,
                                        internal_chart_name=internal_chart_name,
                                        platform=FunPlatform.F1,
                                        owner_info=chart.owner_info,
                                        source=chart.source, base_line_date=base_line_date, workspace_ids=[])
        root_chart.add_child(container.metric_id)
        childrens = present_dataset["children"]
        # final_dict = ml.get_dict(chart=main_chart)
        # print json.dumps(final_dict, indent=4)
        leaf_recursion(childrens, container)


if __name__ == "__main__num_hosts_2":
    alirdma_charts = MetricChart.objects.filter(metric_model_name="AlibabaRdmaPerformance")
    for chart in alirdma_charts:
        data_sets = json.loads(chart.data_sets)
        for each_data_set in data_sets:
            inputs = each_data_set["inputs"]
            inputs["input_hosts"] = 2
        chart.data_sets = json.dumps(data_sets)
        chart.save()
    print ("Added num hosts 2 as the filter for the Allibaba RDMA charts")

    with open(METRICS_BASE_DATA_FILE, "r") as f:
        metrics = json.load(f)
        for metric in metrics:
            if metric["label"] == "F1":
                f1_metrics = metric["children"]
                for f1_metric in f1_metrics:
                    if f1_metric["label"] == "PoCs":
                        pocs = f1_metric["children"]
                        for poc in pocs:
                            if poc["label"] == "Alibaba":
                                alibaba_childrens = poc["children"]
                                for alibaba_children in alibaba_childrens:
                                    if alibaba_children["label"] == "RDMA":
                                        rdma_childrens = alibaba_children["children"]
                                        for rdma_children in rdma_childrens:
                                            if rdma_children["name"] == "alibaba_rdma_host_fcp_2f1":
                                                fcp_children = rdma_children["children"]

    base_line_date = datetime(year=2019, month=6, day=1, minute=0, hour=0, second=0)
    main_chart = ml.create_container(chart_name="4 host(s)",
                                     internal_chart_name="alibaba_rdma_host_fcp_2f1_hosts_4", platform=FunPlatform.F1,
                                     owner_info="manu.ks@fungible.com",
                                     source="", base_line_date=base_line_date, workspace_ids=[3523])
    leaf_recursion(fcp_children, main_chart)
    final_dict = ml.get_dict(chart=main_chart)
    print json.dumps(final_dict, indent=4)

    allibaba_data = AlibabaRdmaPerformance.objects.all()
    for each_data in allibaba_data:
        each_data.input_hosts = 2
        each_data.save()
    print("Initialized num hosts as 2 in the db")

if __name__ == "__main__8_14_1:4K_RAND_WR_COMP":
    owner_info = "Alagarswamy Devaraj (alagarswamy.devaraj@fungible.com)"
    source = "TBD"
    base_line_date = datetime(year=2019, month=12, day=03, minute=0, hour=0, second=1)
    model_name = "BltVolumePerformance"
    qdepths = [8, 16]
    categories = ["IOPS"]

    new_charts = []

    for qdepth in qdepths:
        output_names = ["output_write_iops"]
        data_sets = []
        y1_axis_title = PerfUnit.UNIT_OPS
        chart_name = "IOPS, QDepth={}".format(qdepth)
        for output_name in output_names:
            one_data_set = {}
            data_set_name = "{}(8 vols)".format("write")
            one_data_set["name"] = data_set_name
            fio_job_name = "inspur_8k_random_write_50pctcomp_iodepth_{}_vol_8".format(qdepth)
            one_data_set["inputs"] = {"input_platform": FunPlatform.F1,
                                      "input_fio_job_name": fio_job_name}

            one_data_set["output"] = {"name": output_name,
                                      "min": 0,
                                      "max": -1,
                                      "expected": -1,
                                      "reference": -1,
                                      "best": -1,
                                      "unit": y1_axis_title}
            data_sets.append(one_data_set)
        internal_chart_name = "8_14_1:4K_RAND_WR_COMP," + chart_name + fio_job_name + data_sets[0]["name"]
        positive = True
        leaf_chart = ml.create_leaf(chart_name=chart_name,
                                    internal_chart_name=internal_chart_name,
                                    data_sets=data_sets,
                                    leaf=True,
                                    description="TBD",
                                    owner_info=owner_info,
                                    source=source,
                                    positive=positive, y1_axis_title=y1_axis_title,
                                    visualization_unit=y1_axis_title,
                                    metric_model_name=model_name,
                                    base_line_date=base_line_date,
                                    work_in_progress=False, children=[], jira_ids=[], platform=FunPlatform.F1,
                                    peer_ids=[], creator=TEAM_REGRESSION_EMAIL,
                                    workspace_ids=[])
        new_charts.append(leaf_chart.get_metrics_json_blob())

    print json.dumps(new_charts, indent=4)


if __name__ == "__main_bltvolume__":
    owner_info = "Alagarswamy Devaraj (alagarswamy.devaraj@fungible.com)"
    source = "TBD"
    base_line_date = datetime(year=2019, month=12, day=03, minute=0, hour=0, second=1)
    model_name = "BltVolumePerformance"
    qdepths = [8, 16]
    categories = ["IOPS"]

    new_charts = []

    for qdepth in qdepths:
        output_names = ["output_write_iops"]
        data_sets = []
        y1_axis_title = PerfUnit.UNIT_OPS
        chart_name = "IOPS, QDepth={}".format(qdepth)
        for output_name in output_names:
            one_data_set = {}
            data_set_name = "{}(8 vols)".format("write")
            one_data_set["name"] = data_set_name
            fio_job_name = "inspur_8k_random_write_encryption_keysize_32_iodepth_{}_vol_8".format(qdepth)
            one_data_set["inputs"] = {"input_platform": FunPlatform.F1,
                                      "input_fio_job_name": fio_job_name}

            one_data_set["output"] = {"name": output_name,
                                      "min": 0,
                                      "max": -1,
                                      "expected": -1,
                                      "reference": -1,
                                      "best": -1,
                                      "unit": y1_axis_title}
            data_sets.append(one_data_set)
        internal_chart_name = "8_15_1:4k_RAND_WR_ENCRYPTION,F1(s)=1 " + chart_name + fio_job_name + data_sets[0]["name"]
        positive = True
        leaf_chart = ml.create_leaf(chart_name=chart_name,
                                    internal_chart_name=internal_chart_name,
                                    data_sets=data_sets,
                                    leaf=True,
                                    description="TBD",
                                    owner_info=owner_info,
                                    source=source,
                                    positive=positive, y1_axis_title=y1_axis_title,
                                    visualization_unit=y1_axis_title,
                                    metric_model_name=model_name,
                                    base_line_date=base_line_date,
                                    work_in_progress=False, children=[], jira_ids=[], platform=FunPlatform.F1,
                                    peer_ids=[], creator=TEAM_REGRESSION_EMAIL,
                                    workspace_ids=[])
        new_charts.append(leaf_chart.get_metrics_json_blob())

    print json.dumps(new_charts, indent=4)

if __name__ == "__main_alibaba_rdma__":
    metric_model_name = "AlibabaRdmaPerformance"
    charts = MetricChart.objects.filter(metric_model_name=metric_model_name)
    for chart in charts:
        if "latency" in chart.internal_chart_name:
            chart.positive = False
        else:
            chart.positive = True
        chart.save()
    print "edited all the rdma charts positive flag"

    internal_1500_2_hosts_chart_names = ["alibaba_rdma_fcp_f1_2_mtu_1500_write_bandwidth_size_1",
                            "alibaba_rdma_fcp_f1_2_mtu_1500_write_packet_rate_size_1",
                            "alibaba_rdma_fcp_f1_2_mtu_1500_write_latency_size_1"]

    internal_9000_2_hosts_chart_names = ["alibaba_rdma_fcp_f1_2_mtu_9000_write_bandwidth_size_4096",
                                         "alibaba_rdma_fcp_f1_2_mtu_9000_write_packet_rate_size_4096",
                                         "alibaba_rdma_fcp_f1_2_mtu_9000_write_latency_size_4096"]

    internal_1500_4_hosts_chart_names = ["alibaba_rdma_fcp_f1_2_mtu_1500_write_bandwidth_size_1_hosts_4",
                                         "alibaba_rdma_fcp_f1_2_mtu_1500_write_packet_rate_size_1_hosts_4",
                                         "alibaba_rdma_fcp_f1_2_mtu_1500_write_latency_size_1_hosts_4"]

    internal_9000_4_hosts_chart_names = ["alibaba_rdma_fcp_f1_2_mtu_9000_write_bandwidth_size_4096_hosts_4",
                                         "alibaba_rdma_fcp_f1_2_mtu_9000_write_packet_rate_size_4096_hosts_4",
                                         "alibaba_rdma_fcp_f1_2_mtu_9000_write_latency_size_4096_hosts_4"]

    sizes = {8192: "8192", 16384: "16K", 32768: "32K", 65536: "64K", 131072: "128K"}
    internal_chart_names = [internal_1500_2_hosts_chart_names, internal_1500_4_hosts_chart_names,
                            internal_9000_2_hosts_chart_names, internal_9000_4_hosts_chart_names]
    base_line_date = datetime(year=2020, month=01, day=15, minute=0, hour=0, second=1)
    for internal_names in internal_chart_names:
        for internal_name in internal_names:
            new_charts = []
            chart = MetricChart.objects.get(internal_chart_name=internal_name)
            positive = chart.positive
            for size in sizes:
                chart_name = "Size " + sizes[size]
                index = internal_name.find('size_') + 5
                internal_chart_name = internal_name[:index] + sizes[size]
                if "hosts" in internal_name:
                    internal_chart_name = internal_name[:index] + sizes[size] + "_hosts_4"
                data_sets = chart.get_data_sets()
                for data_set in data_sets:
                    data_set["output"]["reference"] = -1
                    data_set["output"]["min"] = 0
                    data_set["output"]["max"] = -1
                    data_set["output"]["expected"] = -1
                    data_set["output"]["best"] = -1
                    if positive:
                        data_set["inputs"]["input_size_bandwidth"] = size
                    else:
                        data_set["inputs"]["input_size_latency"] = size
                # print json.dumps(data_sets)
                leaf_chart = ml.create_leaf(chart_name=chart_name,
                                            internal_chart_name=internal_chart_name,
                                            data_sets=data_sets,
                                            leaf=True,
                                            description=chart.description,
                                            owner_info=chart.owner_info,
                                            source=chart.source,
                                            positive=chart.positive, y1_axis_title=chart.y1_axis_title,
                                            visualization_unit=chart.y1_axis_title,
                                            metric_model_name=chart.metric_model_name,
                                            base_line_date=base_line_date,
                                            work_in_progress=False, children=[], jira_ids=[], platform=FunPlatform.F1,
                                            peer_ids=[], creator=TEAM_REGRESSION_EMAIL,
                                            workspace_ids=[])
                new_charts.append(leaf_chart.get_metrics_json_blob())
            # print json.dumps(new_charts, indent=4)
    print "added new charts for different sizes"

if __name__ == "__main_failure_ratio__":
    owner_info = "Ashwin S (ashwin.s@fungible.com)"
    source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/system/build_time_performance.py"
    base_line_date = datetime(year=2020, month=2, day=10, minute=0, hour=0, second=0)
    data_sets = []
    one_data_set = {}
    one_data_set["name"] = "failure percentage"
    one_data_set["inputs"] = {}
    one_data_set["output"] = {"name": "output_failure_percentage", "min": 0, "max": -1, "expected": -1, "reference": -1,
                              "best": -1, "unit": PerfUnit.UNIT_NUMBER}
    data_sets.append(one_data_set)
    ml.create_leaf(chart_name="Flaky tests failure ratio", internal_chart_name="flaky_tests_failure_ratio",
                           data_sets=data_sets, leaf=True,
                           description="TBD",
                           owner_info=owner_info, source=source,
                           positive=False, y1_axis_title=PerfUnit.UNIT_NUMBER,
                           visualization_unit=PerfUnit.UNIT_NUMBER,
                           metric_model_name="FlakyTestsFailurePerformance",
                           base_line_date=base_line_date,
                           work_in_progress=False, children=[], jira_ids=[], platform=FunPlatform.F1,
                           peer_ids=[], creator=TEAM_REGRESSION_EMAIL,
                           workspace_ids=[])
    print "created flaky tests failure ratio chart"

if __name__ == "__main_qdepth512__":
    iops_chart_ids = [843, 1075, 1076, 1077]
    fio_job_name = "fio_tcp_randread_blt_32_16_vol_"
    for id in iops_chart_ids:
        chart = MetricChart.objects.get(metric_id=id)
        if chart:
            data_sets = chart.get_data_sets()
            new_data_set = chart.get_data_sets()[0]
            old_fio_job_name = new_data_set["inputs"]["input_fio_job_name"]
            if "vol_12" in old_fio_job_name:
                new_data_set["inputs"]["input_fio_job_name"] = fio_job_name + "12"
            elif "vol_8" in old_fio_job_name:
                new_data_set["inputs"]["input_fio_job_name"] = fio_job_name + "8"
            elif "vol_4" in old_fio_job_name:
                new_data_set["inputs"]["input_fio_job_name"] = fio_job_name + "4"
            elif "vol_2" in old_fio_job_name:
                new_data_set["inputs"]["input_fio_job_name"] = fio_job_name + "2"
            new_data_set["name"] = "qd512"
            new_data_set["output"]["min"] = 0
            new_data_set["output"]["max"] = -1
            new_data_set["output"]["expected"] = -1
            new_data_set["output"]["reference"] = -1
            new_data_set["output"]["best"] = -1

            data_sets.append(new_data_set)
            chart.data_sets = json.dumps(data_sets)
            chart.save()
    print "created 512 qdepth iops dataset for all volumes"
    copy_latency_charts = ["rand_read_qd1_multi_host_nvmetcp_2_vols_output_latency",
                           "rand_read_qd1_multi_host_nvmetcp_4_vols_output_latency",
                           "rand_read_qd1_multi_host_nvmetcp_8_vols_output_latency",
                           "rand_read_qd1_multi_host_nvmetcp_output_latency"]
    base_line_date = datetime(year=2020, month=1, day=30, minute=0, hour=0, second=0)
    for latency_chart in copy_latency_charts:
        chart = MetricChart.objects.get(internal_chart_name=latency_chart)
        if chart:
            internal_chart_name = latency_chart.replace("qd1", "qd512")
            data_sets = chart.get_data_sets()
            for data_set in data_sets:
                data_set["output"]["min"] = 0
                data_set["output"]["max"] = -1
                data_set["output"]["expected"] = -1
                data_set["output"]["reference"] = -1
                data_set["output"]["best"] = -1
                data_set["inputs"]["input_fio_job_name"] = data_set["inputs"]["input_fio_job_name"].replace("1_1",
                                                                                                            "32_16")
            ml.create_leaf(chart_name="Latency, QDepth=512", internal_chart_name=internal_chart_name,
                           data_sets=data_sets, leaf=True,
                           description=chart.description,
                           owner_info=chart.owner_info, source=chart.source,
                           positive=False, y1_axis_title=chart.y1_axis_title,
                           visualization_unit=chart.visualization_unit,
                           metric_model_name=chart.metric_model_name,
                           base_line_date=base_line_date,
                           work_in_progress=False, children=[], jira_ids=[], platform=FunPlatform.F1,
                           peer_ids=[], creator=TEAM_REGRESSION_EMAIL,
                           workspace_ids=[])
    print "created latency charts for all volumes random read"

if __name__ == "__main_data_plane_operations__":
    operations = ["attach_volume", "create_volume", "delete_volume", "detach_volume"]
    concurrent = [True, False]
    base_line_date = datetime(year=2020, month=2, day=18, minute=0, hour=0, second=0)
    for operation in operations:
        for c in concurrent:
            chart_name = "Average time per volume - " + "serial"
            internal_chart_name = "fungible_controller_api_" + operation[:6] + "_avg_time_" + "serial"
            if c:
                chart_name = "Average time per volume - " +  "concurrent"
                internal_chart_name = "fungible_controller_api_" + operation[:6] + "_avg_time_" + "concurrent"
            data_sets = []
            one_data_set = {}
            one_data_set["name"] = "avg_time"
            one_data_set["inputs"] = {"input_platform": FunPlatform.F1, "input_action_type": operation,
                                      "input_volume_type": "raw", "input_volume_size": 1800,
                                      "input_volume_size_unit": "MB", "input_total_volumes": 5, "input_concurrent": c}
            one_data_set["output"] = {"name": "output_avg_time", "min": 0, "max": -1, "expected": -1, "reference":
                -1, "best": -1, "unit": PerfUnit.UNIT_SECS}
            data_sets.append(one_data_set)
            ml.create_leaf(chart_name=chart_name, internal_chart_name=internal_chart_name,
                           data_sets=data_sets, leaf=True,
                           description="TBD",
                           owner_info="Ashwin S (ashwin.s@fungible.com)", source="Unknown",
                           positive=False, y1_axis_title=PerfUnit.UNIT_SECS,
                           visualization_unit=PerfUnit.UNIT_SECS,
                           metric_model_name="DataPlaneOperationsPerformance",
                           base_line_date=base_line_date,
                           work_in_progress=False, children=[], jira_ids=[], platform=FunPlatform.F1,
                           peer_ids=[], creator=TEAM_REGRESSION_EMAIL,
                           workspace_ids=[])
    print "added charts for concurrent and serial chart for all operations"

if __name__ == "__main_pooled_test_beds__":
    names = ["fs-functional-1", "fs-inspur", "fs-regression1", "fs-regression2", "fs-storage-test-cab04"]
    for name in names:
        test_bed = TestBed.objects.get(name=name)
        test_bed.pooled = True
        test_bed.save()
    print "set the pooled boolean to be true for few test beds"

if __name__ == "__main__":
    internal_chart_name = "multi_host_raw_block_nvmetcp_12_vols"
    chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
    model_name = "RawVolumeNvmeTcpMultiHostPerformance"
    block_size = "12_vols_block_8k_"
    iops_charts = ["rand_read_qd_multi_host_nvmetcp_output_iops", "rand_write_qd_multi_host_nvmetcp_output_iops"]
    latency_charts = [""]

