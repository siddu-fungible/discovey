from web.fun_test.maintenance_old import *
from lib.system.fun_test import *
from datetime import datetime
from web.fun_test.models_helper import add_jenkins_job_id_map
from dateutil import parser
from django.utils import timezone
from fun_global import PerfUnit

if __name__ == "__main_s1_platform__":
    charts = MetricChart.objects.all()
    for chart in charts:
        if chart.internal_chart_name.endswith('_S1'):
            chart.platform = "S1"
            chart.last_build_status = fun_test.PASSED
            data_sets = json.loads(chart.data_sets)
            for data_set in data_sets:
                data_set["output"]["min"] = 0
                data_set["output"]["max"] = -1
                data_set["output"]["expected"] = -1
                data_set["output"]["reference"] = -1
                data_set["output"]["unit"] = chart.visualization_unit
            chart.data_sets = json.dumps(data_sets)
            chart.save()
            print "chart name is: {}".format(chart.chart_name)
            print "peer chart ids: {}".format(json.loads(chart.peer_ids))
        if chart.leaf:
            data_sets = json.loads(chart.data_sets)
            for data_set in data_sets:
                data_set["output"]["unit"] = chart.visualization_unit
            chart.data_sets = json.dumps(data_sets)
            chart.save()

if __name__ == "__main_ipsec__":
    internal_chart_names = ["juniper_ipsec_enc_single_tunnel_output_throughput",
                            "juniper_ipsec_enc_single_tunnel_output_pps",
                            "juniper_ipsec_enc_multi_tunnel_output_throughput",
                            "juniper_ipsec_enc_multi_tunnel_output_pps",
                            "juniper_ipsec_dec_single_tunnel_output_throughput",
                            "juniper_ipsec_dec_single_tunnel_output_pps",
                            "juniper_ipsec_dec_multi_tunnel_output_throughput",
                            "juniper_ipsec_dec_multi_tunnel_output_pps"
                            ]
    input_algorithm = "AES_GCM"
    description = "TBD"
    positive = True
    base_line_date = datetime(year=2019, month=5, day=15, minute=0, hour=0, second=0)
    for internal_chart_name in internal_chart_names:
        if "ipsec_enc_single" in internal_chart_name:
            model_name = "JuniperIpsecEncryptionSingleTunnelPerformance"
        elif "ipsec_enc_multi" in internal_chart_name:
            model_name = "JuniperIpsecEncryptionMultiTunnelPerformance"
        elif "ipsec_dec_single" in internal_chart_name:
            model_name = "JuniperIpsecDecryptionSingleTunnelPerformance"
        else:
            model_name = "JuniperIpsecDecryptionMultiTunnelPerformance"

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
                    source="https://github.com/fungible-inc/FunOS/blob/2c0e5c4b94086b6eae63a8af68ca8d8e1287aa6c/apps/cryptotest/ipsec_perf.c",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False,
                    platform=FunPlatform.F1).save()
    print "created charts for the IPSEC juniper customer teramarks"

if __name__ == "__main_raw_nvmetcp__":
    internal_iops_chart_names = ["rand_read_qd_nvmetcp_output_iops", "read_qd_nvmetcp_output_iops"]
    # internal_latency_chart_names = ["read_qd1_nvmetcp_output_latency", "read_qd8_nvmetcp_output_latency",
    #                              "read_qd16_nvmetcp_output_latency", "read_qd32_nvmetcp_output_latency", "read_qd64_nvmetcp_output_latency",
    #                         "rand_read_qd1_nvmetcp_output_latency", "rand_read_qd8_nvmetcp_output_latency", "rand_read_qd16_nvmetcp_output_latency",
    #                         "rand_read_qd32_nvmetcp_output_latency", "rand_read_qd64_nvmetcp_output_latency"]
    copy_read = "read_qd1_nvmetcp_output_latency"
    copy_rand_read = "rand_read_qd1_nvmetcp_output_latency"
    fio_rand_read_job_names = [
        "fio_tcp_randread_blt_1_1_scaling", "fio_tcp_randread_blt_8_1_scaling", "fio_tcp_randread_blt_16_1_scaling",
        "fio_tcp_randread_blt_16_2_scaling", "fio_tcp_randread_blt_16_4_scaling"]
    fio_read_job_names = ["fio_tcp_read_blt_1_1_scaling",
                          "fio_tcp_read_blt_8_1_scaling", "fio_tcp_read_blt_16_1_scaling",
                          "fio_tcp_read_blt_16_2_scaling",
                          "fio_tcp_read_blt_16_4_scaling"]
    for internal_iops_chart_name in internal_iops_chart_names:
        output_name = "output_read_iops"
        iops_chart = MetricChart.objects.get(internal_chart_name=internal_iops_chart_name)
        data_sets = []
        if "rand_read" in internal_iops_chart_name:
            fio_job_names = fio_rand_read_job_names
            operation = "randread"
        else:
            fio_job_names = fio_read_job_names
            operation = "read"
        for fio_job_name in fio_job_names:
            if "1_1" in fio_job_name:
                name = "qd1"
            elif "8_1" in fio_job_name:
                name = "qd8"
            elif "16_1" in fio_job_name:
                name = "qd16"
            elif "16_2" in fio_job_name:
                name = "qd32"
            else:
                name = "qd64"
            one_data_set = {}
            one_data_set["name"] = name
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_operation"] = operation
            one_data_set["inputs"]["input_platform"] = FunPlatform.F1
            one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1,
                                      "unit": iops_chart.visualization_unit}
            data_sets.append(one_data_set)
        iops_chart.data_sets = json.dumps(data_sets)
        iops_chart.save()

    chart_name = "Latency"
    fio_job_names = fio_read_job_names + fio_rand_read_job_names
    for fio_job_name in fio_job_names:
        if "1_1" in fio_job_name:
            name = "qd1"
        elif "8_1" in fio_job_name:
            name = "qd8"
        elif "16_1" in fio_job_name:
            name = "qd16"
        elif "16_2" in fio_job_name:
            name = "qd32"
        else:
            name = "qd64"
        if "randread" in fio_job_name:
            internal_chart_name = "rand_read_" + name + "_nvmetcp_output_latency"
            copy = copy_rand_read
        else:
            internal_chart_name = "read_" + name + "_nvmetcp_output_latency"
            copy = copy_read
        try:
            latency_chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
            data_sets = json.loads(latency_chart.data_sets)
            for data_set in data_sets:
                data_set["inputs"]["input_fio_job_name"] = fio_job_name
            latency_chart.data_sets = json.dumps(data_sets)
            latency_chart.save()
        except:
            chart = MetricChart.objects.get(internal_chart_name=copy)
            data_sets = json.loads(chart.data_sets)
            for data_set in data_sets:
                data_set["inputs"]["input_fio_job_name"] = fio_job_name
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
                        visualization_unit=chart.y1_axis_title,
                        metric_model_name=chart.metric_model_name,
                        base_line_date=chart.base_line_date,
                        work_in_progress=False,
                        platform=FunPlatform.F1).save()
    print "added new qdepth charts for raw block nvmetcp"

if __name__ == "__main_jenkins__":
    model_name = "JenkinsJobIdMap"
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    metric_model = app_config.get_metric_models()[model_name]
    entries = metric_model.objects.all()
    for entry in entries:
        print entry.build_date
        if entry.completion_date != "":
            dt = parser.parse(entry.completion_date)
            entry.build_date = dt
            entry.save()
            print "string date {}, date object {}".format(entry.completion_date, entry.build_date)

if __name__ == "__main_converted_old_storge_versions__":
    model_name = "BltVolumePerformance"
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    metric_model = app_config.get_metric_models()[model_name]
    entries = metric_model.objects.all()
    for entry in entries:
        if entry.input_version != "":
            completion_date = timezone.localtime(entry.input_date_time)
            # completion_date = timezone.localtime(date_time)
            completion_date = str(completion_date).split(":")
            completion_date = completion_date[0] + ":" + completion_date[1]
            build_date = parser.parse(completion_date)
            print completion_date
            print entry.input_version
            add_jenkins_job_id_map(jenkins_job_id=0,
                                   fun_sdk_branch="",
                                   git_commit="",
                                   software_date=0,
                                   hardware_version="",
                                   completion_date=completion_date,
                                   build_properties="", lsf_job_id="",
                                   sdk_version=entry.input_version,
                                   build_date=build_date)

if __name__ == "__main_128_tcp__":
    internal_iops_chart_names = ["rand_read_qd_nvmetcp_output_iops", "read_qd_nvmetcp_output_iops"]
    # internal_latency_chart_names = ["read_qd1_nvmetcp_output_latency", "read_qd8_nvmetcp_output_latency",
    #                              "read_qd16_nvmetcp_output_latency", "read_qd32_nvmetcp_output_latency", "read_qd64_nvmetcp_output_latency",
    #                         "rand_read_qd1_nvmetcp_output_latency", "rand_read_qd8_nvmetcp_output_latency", "rand_read_qd16_nvmetcp_output_latency",
    #                         "rand_read_qd32_nvmetcp_output_latency", "rand_read_qd64_nvmetcp_output_latency"]
    copy_read = "read_qd1_nvmetcp_output_latency"
    copy_rand_read = "rand_read_qd1_nvmetcp_output_latency"
    fio_rand_read_job_names = [
        "fio_tcp_randread_blt_1_1_scaling", "fio_tcp_randread_blt_16_1_scaling",
        "fio_tcp_randread_blt_16_2_scaling", "fio_tcp_randread_blt_16_4_scaling", "fio_tcp_randread_blt_16_8_scaling"]
    fio_read_job_names = ["fio_tcp_read_blt_1_1_scaling",
                          "fio_tcp_read_blt_16_1_scaling",
                          "fio_tcp_read_blt_16_2_scaling",
                          "fio_tcp_read_blt_16_4_scaling", "fio_tcp_read_blt_16_8_scaling"]
    for internal_iops_chart_name in internal_iops_chart_names:
        output_name = "output_read_iops"
        iops_chart = MetricChart.objects.get(internal_chart_name=internal_iops_chart_name)
        data_sets = []
        if "rand_read" in internal_iops_chart_name:
            fio_job_names = fio_rand_read_job_names
            operation = "randread"
        else:
            fio_job_names = fio_read_job_names
            operation = "read"
        for fio_job_name in fio_job_names:
            if "1_1" in fio_job_name:
                name = "qd1"
            elif "16_1" in fio_job_name:
                name = "qd16"
            elif "16_2" in fio_job_name:
                name = "qd32"
            elif "16_4" in fio_job_name:
                name = "qd64"
            else:
                name = "qd128"

            one_data_set = {}
            one_data_set["name"] = name
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_operation"] = operation
            one_data_set["inputs"]["input_platform"] = FunPlatform.F1
            one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1,
                                      "unit": iops_chart.visualization_unit}
            data_sets.append(one_data_set)
        iops_chart.data_sets = json.dumps(data_sets)
        iops_chart.save()

    chart_name = "Latency"
    fio_job_names = fio_read_job_names + fio_rand_read_job_names
    for fio_job_name in fio_job_names:
        if "1_1" in fio_job_name:
            name = "qd1"
        elif "16_1" in fio_job_name:
            name = "qd16"
        elif "16_2" in fio_job_name:
            name = "qd32"
        elif "16_4" in fio_job_name:
            name = "qd64"
        else:
            name = "qd128"

        if "randread" in fio_job_name:
            internal_chart_name = "rand_read_" + name + "_nvmetcp_output_latency"
            copy = copy_rand_read
        else:
            internal_chart_name = "read_" + name + "_nvmetcp_output_latency"
            copy = copy_read
        try:
            latency_chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
            data_sets = json.loads(latency_chart.data_sets)
            for data_set in data_sets:
                data_set["inputs"]["input_fio_job_name"] = fio_job_name
            latency_chart.data_sets = json.dumps(data_sets)
            latency_chart.save()
        except:
            chart = MetricChart.objects.get(internal_chart_name=copy)
            data_sets = json.loads(chart.data_sets)
            for data_set in data_sets:
                data_set["inputs"]["input_fio_job_name"] = fio_job_name
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
                        visualization_unit=chart.y1_axis_title,
                        metric_model_name=chart.metric_model_name,
                        base_line_date=chart.base_line_date,
                        work_in_progress=False,
                        platform=FunPlatform.F1).save()
    print "added 128 qdepth charts for raw block nvmetcp"

if __name__ == "__main_128_tcp__":
    fio_job_names = ["fio_tcp_randwrite_blt_1_1_scaling",
                     "fio_tcp_randwrite_blt_8_1_scaling",
                     "fio_tcp_randwrite_blt_16_1_scaling",
                     "fio_tcp_randwrite_blt_16_2_scaling"]
    internal_iops_chart_name = "rand_write_qd_nvmetcp_output_iops"
    copy = "rand_read_qd_nvmetcp_output_iops"
    chart = MetricChart.objects.get(internal_chart_name=copy)
    chart_name = "IOPS"
    data_sets = []
    for fio_job_name in fio_job_names:
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
        one_data_set["inputs"] = {}
        one_data_set["inputs"]["input_operation"] = "randwrite"
        one_data_set["inputs"]["input_platform"] = FunPlatform.F1
        one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
        one_data_set["output"] = {"name": "output_write_iops", 'min': 0, "max": -1, "expected": -1, "reference": -1,
                                  "unit": chart.visualization_unit}
        data_sets.append(one_data_set)

    metric_id = LastMetricId.get_next_id()
    MetricChart(chart_name=chart_name,
                metric_id=metric_id,
                internal_chart_name=internal_iops_chart_name,
                data_sets=json.dumps(data_sets),
                leaf=True,
                description=chart.description,
                owner_info=chart.owner_info,
                source=chart.source,
                positive=chart.positive,
                y1_axis_title=chart.y1_axis_title,
                visualization_unit=chart.y1_axis_title,
                metric_model_name=chart.metric_model_name,
                base_line_date=chart.base_line_date,
                work_in_progress=False,
                platform=FunPlatform.F1).save()

    internal_chart_names = ["rand_write_", "_nvmetcp_output_latency"]
    chart_name = "Latency"
    copy = "rand_read_qd1_nvmetcp_output_latency"
    chart = MetricChart.objects.get(internal_chart_name=copy)
    output_names = ["output_write_avg_latency", "output_write_99_latency", "output_write_99_99_latency"]
    for fio_job_name in fio_job_names:
        if "1_1" in fio_job_name:
            name = "qd1"
        elif "8_1" in fio_job_name:
            name = "qd8"
        elif "16_1" in fio_job_name:
            name = "qd16"
        else:
            name = "qd32"
        internal_chart_name = internal_chart_names[0] + name + internal_chart_names[1]
        data_sets = []
        for output_name in output_names:
            if "_avg_" in output_name:
                name = "avg"
            elif "_99_99_" in output_name:
                name = "99.99%"
            else:
                name = "99%"
            one_data_set = {}
            one_data_set["name"] = name
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_operation"] = "randwrite"
            one_data_set["inputs"]["input_platform"] = FunPlatform.F1
            one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1,
                                      "unit": chart.visualization_unit}
            data_sets.append(one_data_set)
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
                    visualization_unit=chart.y1_axis_title,
                    metric_model_name=chart.metric_model_name,
                    base_line_date=chart.base_line_date,
                    work_in_progress=False,
                    platform=FunPlatform.F1).save()
    print "added random write raw block nvmetcp"

if __name__ == "__main_128_pcie__":
    internal_chart_names = ["read_qd128_pcie_output_latency", "rand_read_qd128_pcie_output_latency"]
    chart_name = "Latency, QDepth=128"
    for internal_chart_name in internal_chart_names:
        if "rand_read" in internal_chart_name:
            chart = MetricChart.objects.get(internal_chart_name="rand_read_qd64_pcie_output_latency")
            fio_job_name = "fio_pcie_randread_blt_128_iod_scaling"
        else:
            chart = MetricChart.objects.get(internal_chart_name="read_qd64_pcie_output_latency")
            fio_job_name = "fio_pcie_read_blt_128_iod_scaling"
        data_sets = json.loads(chart.data_sets)
        for data_set in data_sets:
            data_set["inputs"]["input_fio_job_name"] = fio_job_name

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
                    visualization_unit=chart.y1_axis_title,
                    metric_model_name=chart.metric_model_name,
                    base_line_date=chart.base_line_date,
                    work_in_progress=False,
                    platform=FunPlatform.F1).save()

    iops_charts = ["read_qd_pcie_output_iops", "rand_read_qd_pcie_output_iops"]
    for iops_chart in iops_charts:
        chart = MetricChart.objects.get(internal_chart_name=iops_chart)
        if "rand_read" in iops_chart:
            operation = "randread"
            fio_job_name = "fio_pcie_randread_blt_128_iod_scaling"
        else:
            operation = "read"
            fio_job_name = "fio_pcie_read_blt_128_iod_scaling"
        data_sets = json.loads(chart.data_sets)
        one_data_set = {}
        one_data_set["name"] = "qd128"
        one_data_set["inputs"] = {}
        one_data_set["inputs"]["input_operation"] = operation
        one_data_set["inputs"]["input_platform"] = FunPlatform.F1
        one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
        one_data_set["output"] = {"name": "output_read_iops", 'min': 0, "max": -1, "expected": -1, "reference": -1,
                                  "unit": chart.visualization_unit}
        data_sets.append(one_data_set)
        chart.data_sets = json.dumps(data_sets)
        chart.save()
    print "added charts for qd128 raw block pcie"

if __name__ == "__main_s1_fix__":
    model_names = ["WuDispatchTestPerformance", "WuSendSpeedTestPerformance", "FunMagentPerformanceTest",
                   "WuStackSpeedTestPerformance", "SoakFunMallocPerformance", "SoakClassicMallocPerformance",
                   "BcopyFloodDmaPerformance", "BcopyPerformance", "AllocSpeedPerformance", "WuLatencyUngated",
                   "WuLatencyAllocStack"]
    for model_name in model_names:
        app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
        metric_model = app_config.get_metric_models()[model_name]
        entries = metric_model.objects.filter(input_platform=FunPlatform.S1)
        print len(entries), model_name
        entries.delete()
        print len(entries), model_name
    charts = MetricChart.objects.all()
    for chart in charts:
        if chart.internal_chart_name.endswith('_S1'):
            data_sets = json.loads(chart.data_sets)
            for data_set in data_sets:
                data_set["output"]["min"] = 0
                data_set["output"]["max"] = -1
                data_set["output"]["expected"] = -1
                data_set["output"]["reference"] = -1
                data_set["output"]["unit"] = chart.visualization_unit
            chart.data_sets = json.dumps(data_sets)
            chart.save()
            print "chart name is: {}".format(chart.chart_name)

if __name__ == "__main_funtcp_16flows__":
    internal_chart_name = "funtcp_server_throughput_16tcp"
    chart = MetricChart.objects.get(internal_chart_name="funtcp_server_throughput_8tcp")
    data_sets = json.loads(chart.data_sets)
    for data_set in data_sets:
        data_set["inputs"]["input_num_flows"] = 16
    metric_id = LastMetricId.get_next_id()
    MetricChart(chart_name="16 TCP Flow(s)",
                metric_id=metric_id,
                internal_chart_name=internal_chart_name,
                data_sets=json.dumps(data_sets),
                leaf=True,
                description=chart.description,
                owner_info=chart.owner_info,
                source=chart.source,
                positive=chart.positive,
                y1_axis_title=chart.y1_axis_title,
                visualization_unit=chart.y1_axis_title,
                metric_model_name=chart.metric_model_name,
                base_line_date=chart.base_line_date,
                work_in_progress=False,
                platform=FunPlatform.F1).save()

if __name__ == "__main_qd128_pcie__":
    internal_chart_names = ["read_iod128_durable_volume_ec_output_latency",
                            "rand_read_iod128_durable_volume_ec_output_latency"]
    chart_name = "Latency, QDepth=128"
    for internal_chart_name in internal_chart_names:
        if "rand_read" in internal_chart_name:
            chart = MetricChart.objects.get(internal_chart_name="rand_read_iod64_durable_volume_ec_output_latency")
            fio_job_name = "ec_randread_iodepth_128"
        else:
            chart = MetricChart.objects.get(internal_chart_name="read_iod64_durable_volume_ec_output_latency")
            fio_job_name = "ec_read_iodepth_128"
        data_sets = json.loads(chart.data_sets)
        for data_set in data_sets:
            data_set["inputs"]["input_fio_job_name"] = fio_job_name

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
                    visualization_unit=chart.y1_axis_title,
                    metric_model_name=chart.metric_model_name,
                    base_line_date=chart.base_line_date,
                    work_in_progress=False,
                    platform=FunPlatform.F1).save()

    iops_charts = ["rand_read_iod_durable_volume_ec_output_iops", "read_iod_durable_volume_ec_output_iops"]
    for iops_chart in iops_charts:
        chart = MetricChart.objects.get(internal_chart_name=iops_chart)
        if "rand_read" in iops_chart:
            operation = "randread"
            fio_job_name = "ec_randread_iodepth_128"
        else:
            operation = "read"
            fio_job_name = "ec_read_iodepth_128"
        data_sets = json.loads(chart.data_sets)
        one_data_set = {}
        one_data_set["name"] = "qd128"
        one_data_set["inputs"] = {}
        one_data_set["inputs"]["input_operation"] = operation
        one_data_set["inputs"]["input_platform"] = FunPlatform.F1
        one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
        one_data_set["output"] = {"name": "output_read_iops", 'min': 0, "max": -1, "expected": -1, "reference": -1,
                                  "unit": chart.visualization_unit}
        data_sets.append(one_data_set)
        chart.data_sets = json.dumps(data_sets)
        chart.save()
    print "added charts for qd128 durable volume pcie"

if __name__ == "__main_pcie_write__":
    output_names = ["output_latency", "output_iops"]
    operations = ["write", "rand_write"]
    names = ["pcie"]
    qdepths = ["qd1", "qd4", "qd8", "qd16", "qd32", "qd64"]
    model_name = "BltVolumePerformance"
    base_line_date = datetime(year=2019, month=5, day=20, minute=0, hour=0, second=0)
    for name in names:
        for operation in operations:
            for output_name in output_names:
                source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/blt_pcie_io_depth.py"
                if operation == "rand_write":
                    job_names = ["fio_pcie_randwrite_blt_", "_iod_scaling"]
                    data_set_operation = "randwrite"
                    copy = "rand_write_qd1_pcie_output_latency"
                else:
                    job_names = ["fio_pcie_write_blt_", "_iod_scaling"]
                    data_set_operation = "write"
                    copy = "write_qd1_pcie_output_latency"

                if "iops" in output_name:
                    internal_chart_name = operation + "_" + "qd" + "_" + name + "_" + output_name
                    chart_name = "IOPS"
                    positive = True
                    y1_axis_title = "ops"
                    data_sets = []
                    for qdepth in qdepths:
                        if qdepth == "qd1":
                            fio_job_name = job_names[0] + "1_1" + job_names[1]
                        elif qdepth == "qd4":
                            fio_job_name = job_names[0] + "4_1" + job_names[1]
                        elif qdepth == "qd8":
                            fio_job_name = job_names[0] + "8_1" + job_names[1]
                        elif qdepth == "qd16":
                            fio_job_name = job_names[0] + "8_2" + job_names[1]
                        elif qdepth == "qd32":
                            fio_job_name = job_names[0] + "8_4" + job_names[1]
                        else:
                            fio_job_name = job_names[0] + "8_8" + job_names[1]

                        one_data_set = {}
                        one_data_set["name"] = qdepth
                        one_data_set["inputs"] = {}
                        one_data_set["inputs"]["input_platform"] = FunPlatform.F1
                        one_data_set["inputs"]["input_operation"] = data_set_operation
                        one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
                        one_data_set["output"] = {"name": "output_write_iops", 'min': 0, "max": -1, "expected": -1,
                                                  "reference": -1, "unit": y1_axis_title}
                        data_sets.append(one_data_set)

                    try:
                        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
                        chart.data_sets = json.dumps(data_sets)
                        chart.save()
                    except ObjectDoesNotExist:
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
                                    work_in_progress=False,
                                    platform=FunPlatform.F1).save()
                else:
                    for qdepth in qdepths:
                        if qdepth == "qd1":
                            fio_job_name = job_names[0] + "1_1" + job_names[1]
                        elif qdepth == "qd4":
                            fio_job_name = job_names[0] + "4_1" + job_names[1]
                        elif qdepth == "qd8":
                            fio_job_name = job_names[0] + "8_1" + job_names[1]
                        elif qdepth == "qd16":
                            fio_job_name = job_names[0] + "8_2" + job_names[1]
                        elif qdepth == "qd32":
                            fio_job_name = job_names[0] + "8_4" + job_names[1]
                        else:
                            fio_job_name = job_names[0] + "8_8" + job_names[1]
                        chart_name = "Latency"
                        internal_chart_name = operation + "_" + qdepth + "_" + name + "_" + output_name
                        positive = False
                        y1_axis_title = "usecs"

                        copy_chart = MetricChart.objects.get(internal_chart_name=copy)
                        data_sets = json.loads(copy_chart.data_sets)
                        for data_set in data_sets:
                            data_set["inputs"]["input_fio_job_name"] = fio_job_name
                            data_set["inputs"]["input_operation"] = data_set_operation
                            data_set["inputs"]["input_platform"] = FunPlatform.F1
                            data_set["output"]["expected"] = -1
                            data_set["output"]["min"] = 0
                            data_set["output"]["max"] = -1
                            data_set["output"]["reference"] = -1
                            data_set["output"]["unit"] = y1_axis_title

                        try:
                            chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
                            chart.data_sets = json.dumps(data_sets)
                            chart.save()
                        except ObjectDoesNotExist:
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
                                        work_in_progress=False,
                                        platform=FunPlatform.F1).save()
    print "added charts for raw block write and random write different io depths"

if __name__ == "__main_funtcp_cps__":
    internal_chart_names = ["funtcp_server_cps_close_reset", "funtcp_server_cps_close_fin"]
    for internal_chart_name in internal_chart_names:
        if "close_reset" in internal_chart_name:
            name = "close reset"
            chart_name = "Close Reset"
            type = "close_reset_cps"
        else:
            name = "close fin"
            chart_name = "Close Fin"
            type = "close_fin_cps"
        base_line_date = datetime(year=2019, month=5, day=20, minute=0, hour=0, second=0)

        data_sets = []
        one_data_set = {}
        one_data_set["name"] = name
        one_data_set["inputs"] = {}
        one_data_set["inputs"]["input_platform"] = FunPlatform.F1
        one_data_set["inputs"]["input_frame_size"] = 1500
        one_data_set["inputs"]["input_flow_type"] = "FunTCP_Server_CPS"
        one_data_set["inputs"]["input_cps_type"] = type
        one_data_set["output"] = {"name": "output_max_cps", 'min': 0, "max": -1, "expected": -1,
                                  "reference": -1, "unit": "cps"}
        data_sets.append(one_data_set)

        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Rushikesh Pendse (rushikesh.pendse@fungible.com)",
                    source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/networking/tcp/cps_performance.py",
                    positive=True,
                    y1_axis_title="cps",
                    visualization_unit="cps",
                    metric_model_name="TeraMarkFunTcpConnectionsPerSecondPerformance",
                    base_line_date=base_line_date,
                    work_in_progress=False,
                    platform=FunPlatform.F1).save()
    print "added cps charts for funtcp"

if __name__ == "__main_multiple_apple__":
    # [{"inputs": {"input_operation": "randread", "input_platform": "F1",
    #              "input_fio_job_name": "fio_randread_apple_single_tcp"}, "name": "iops",
    #   "output": {"name": "output_read_iops", "reference": 88.134, "min": 0, "max": -1, "expected": 101.3,
    #              "unit": "Kops"}}]
    internal_chart_names = ["apple_rand_read_mrsw_tcp_output_bandwidth", "apple_rand_read_mrsw_tcp_output_latency",
                            "apple_rand_read_mrsw_tcp_output_iops"]
    base_line_date = datetime(year=2019, month=5, day=24, minute=0, hour=0, second=0)
    for internal_chart_name in internal_chart_names:
        if "bandwidth" in internal_chart_name:
            y1_axis_title = PerfUnit.UNIT_MBYTES_PER_SEC
        elif "latency" in internal_chart_name:
            y1_axis_title = PerfUnit.UNIT_USECS
        else:
            y1_axis_title = PerfUnit.UNIT_OPS
        copy_chart_name = internal_chart_name.replace("mrsw", "srsw")
        copy_chart = MetricChart.objects.get(internal_chart_name=copy_chart_name)
        data_sets = json.loads(copy_chart.data_sets)
        for data_set in data_sets:
            data_set["inputs"]["input_fio_job_name"] = data_set["inputs"]["input_fio_job_name"].replace("single",
                                                                                                        "multiple")
            data_set["output"]["reference"] = -1
            data_set["output"]["expected"] = -1
            data_set["output"]["unit"] = y1_axis_title
        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=copy_chart.chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description=copy_chart.description,
                    owner_info=copy_chart.owner_info,
                    source=copy_chart.source,
                    positive=copy_chart.positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=copy_chart.metric_model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False,
                    platform=FunPlatform.F1).save()
    print "added multiple reader tcp charts for apple"

if __name__ == "__main_inspur__":
    iops_names = ["inspur_rand_read_write_", "_8k_block_"]
    fio_job_names = ["inspur_8k_random_read_write_iodepth_", "_vol_8"]
    qdepths = ["qd1", "qd8", "qd16", "qd32", "qd64", "qd128", "qd256"]
    output_names = ["output_iops", "output_latency"]
    output_iops_names = ["output_read_iops", "output_write_iops"]
    output_latency_names = ["output_read_avg_latency", "output_write_avg_latency"]
    for output_name in output_names:
        for qdepth in qdepths:
            if qdepth == "qd1":
                fio_job_name = fio_job_names[0] + "1" + fio_job_names[1]
            elif qdepth == "qd8":
                fio_job_name = fio_job_names[0] + "8" + fio_job_names[1]
            elif qdepth == "qd16":
                fio_job_name = fio_job_names[0] + "16" + fio_job_names[1]
            elif qdepth == "qd32":
                fio_job_name = fio_job_names[0] + "32" + fio_job_names[1]
            elif qdepth == "qd64":
                fio_job_name = fio_job_names[0] + "64" + fio_job_names[1]
            elif qdepth == "qd128":
                fio_job_name = fio_job_names[0] + "128" + fio_job_names[1]
            else:
                fio_job_name = fio_job_names[0] + "256" + fio_job_names[1]
            if "iops" in output_name:
                positive = True
                chart_name = "IOPS"
                copy = "inspur_rand_read_write_qd1_8k_block_output_iops"
                data_output_names = output_iops_names
                y1_axis_title = "ops"
            else:
                positive = False
                chart_name = "Latency"
                copy = "inspur_rand_read_write_qd1_8k_block_output_latency"
                data_output_names = output_latency_names
                y1_axis_title = "usecs"
            internal_chart_name = iops_names[0] + qdepth + iops_names[1] + output_name
            try:
                chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
                data_sets = json.loads(chart.data_sets)
                for data_set in data_sets:
                    data_set["name"] = data_set["name"] + "(1 vol)"
                for names in data_output_names:
                    if "iops" in names:
                        if "read" in names:
                            name = "read(N vols)"
                        else:
                            name = "write(N vols)"
                    else:
                        if "read" in names:
                            name = "read-avg(N vols)"
                        else:
                            name = "write-avg(N vols)"
                    one_data_set = {}
                    one_data_set["name"] = name
                    one_data_set["inputs"] = {}
                    one_data_set["inputs"]["input_platform"] = FunPlatform.F1
                    one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
                    one_data_set["output"] = {"name": names, 'min': 0, "max": -1, "expected": -1,
                                              "reference": -1, "unit": chart.y1_axis_title}
                    data_sets.append(one_data_set)
                chart.data_sets = json.dumps(data_sets)
                chart.save()
            except ObjectDoesNotExist:
                copy_chart = MetricChart.objects.get(internal_chart_name=copy)
                data_sets = []
                for names in data_output_names:
                    if "iops" in names:
                        if "read" in names:
                            name = "read(N vols)"
                        else:
                            name = "write(N vols)"
                    else:
                        if "read" in names:
                            name = "read-avg(N vols)"
                        else:
                            name = "write-avg(N vols)"
                    one_data_set = {}
                    one_data_set["name"] = name
                    one_data_set["inputs"] = {}
                    one_data_set["inputs"]["input_platform"] = FunPlatform.F1
                    one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
                    one_data_set["output"] = {"name": names, 'min': 0, "max": -1, "expected": -1,
                                              "reference": -1, "unit": "ops"}
                    data_sets.append(one_data_set)
                metric_id = LastMetricId.get_next_id()
                MetricChart(chart_name=chart_name,
                            metric_id=metric_id,
                            internal_chart_name=internal_chart_name,
                            data_sets=json.dumps(data_sets),
                            leaf=True,
                            description=copy_chart.description,
                            owner_info=copy_chart.owner_info,
                            source=copy_chart.source,
                            positive=positive,
                            y1_axis_title=y1_axis_title,
                            visualization_unit=y1_axis_title,
                            metric_model_name=copy_chart.metric_model_name,
                            base_line_date=copy_chart.base_line_date,
                            work_in_progress=False,
                            platform=FunPlatform.F1).save()
    print "added datasets for inspur read write multiple volumes"

if __name__ == "__main_zip_compression__":
    model_name = "InspurZipCompressionRatiosPerformance"
    internal_name = "inspur_8131_compression_ratio_benchmarking_"
    efforts = ["ZIP_EFFORT_2Gbps", "ZIP_EFFORT_64Gbps", "ZIP_EFFORT_AUTO"]
    corpus_names = ["artificl", "cantrbry", "calgary", "large", "silesia", "misc", "enwik8"]
    chart_name = "Effort"
    base_line_date = datetime(year=2019, month=5, day=26, minute=0, hour=0, second=0)
    for effort in efforts:
        if "AUTO" in effort:
            internal_chart_name = internal_name + "auto"
        elif "64" in effort:
            internal_chart_name = internal_name + "64Gbps"
        else:
            internal_chart_name = internal_name + "2Gbps"

        data_sets = []
        for corpus in corpus_names:
            one_data_set = {}
            one_data_set["name"] = corpus
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_platform"] = FunPlatform.F1
            one_data_set["inputs"]["input_effort_name"] = effort
            one_data_set["inputs"]["input_corpus_name"] = corpus
            one_data_set["output"] = {"name": "output_f1_compression_ratio", 'min': 0, "max": -1, "expected": -1,
                                      "reference": -1, "unit": PerfUnit.UNIT_NUMBER}
            data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Aamir Shaikh (aamir.shaikh@fungible.com)",
                    source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/ec_comp_ratio_benchmark.py",
                    positive=True,
                    y1_axis_title=PerfUnit.UNIT_NUMBER,
                    visualization_unit=PerfUnit.UNIT_NUMBER,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False,
                    platform=FunPlatform.F1).save()
    print "added charts for inspur compression benchmark"

if __name__ == "__main_num_flows__":
    model_names = ["HuThroughputPerformance", "HuLatencyPerformance"]
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
            print data_sets

if __name__ == "__main_inspur_multiplef1s__":
    iops_names = ["inspur_rand_read_write_", "_2f1_8k_block_"]
    fio_job_names = ["inspur_8k_random_read_write_iodepth_", "_f1_2_vol_1"]
    qdepths = ["qd1", "qd8", "qd16", "qd32", "qd64", "qd128", "qd256"]
    output_names = ["output_iops", "output_latency"]
    output_iops_names = ["output_read_iops", "output_write_iops"]
    output_latency_names = ["output_read_avg_latency", "output_write_avg_latency"]
    base_line_date = datetime(year=2019, month=5, day=27, minute=0, hour=0, second=0)
    for output_name in output_names:
        for qdepth in qdepths:
            if qdepth == "qd1":
                fio_job_name = fio_job_names[0] + "1" + fio_job_names[1]
            elif qdepth == "qd8":
                fio_job_name = fio_job_names[0] + "8" + fio_job_names[1]
            elif qdepth == "qd16":
                fio_job_name = fio_job_names[0] + "16" + fio_job_names[1]
            elif qdepth == "qd32":
                fio_job_name = fio_job_names[0] + "32" + fio_job_names[1]
            elif qdepth == "qd64":
                fio_job_name = fio_job_names[0] + "64" + fio_job_names[1]
            elif qdepth == "qd128":
                fio_job_name = fio_job_names[0] + "128" + fio_job_names[1]
            else:
                fio_job_name = fio_job_names[0] + "256" + fio_job_names[1]
            internal_chart_name = iops_names[0] + qdepth + iops_names[1] + output_name
            if "iops" in output_name:
                data_output_names = output_iops_names
                y1_axis_title = PerfUnit.UNIT_OPS
            else:
                data_output_names = output_latency_names
                y1_axis_title = PerfUnit.UNIT_USECS
            copy = internal_chart_name.replace("_2f1", "")

            copy_chart = MetricChart.objects.get(internal_chart_name=copy)
            data_sets = []
            for names in data_output_names:
                if "iops" in names:
                    if "read" in names:
                        name = "read(1 vol)"
                    else:
                        name = "write(1 vol)"
                else:
                    if "read" in names:
                        name = "read-avg(1 vol)"
                    else:
                        name = "write-avg(1 vol)"
                one_data_set = {}
                one_data_set["name"] = name
                one_data_set["inputs"] = {}
                one_data_set["inputs"]["input_platform"] = FunPlatform.F1
                one_data_set["inputs"]["input_operation"] = "randrw"
                one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
                one_data_set["output"] = {"name": names, 'min': 0, "max": -1, "expected": -1,
                                          "reference": -1, "unit": y1_axis_title}
                data_sets.append(one_data_set)
            metric_id = LastMetricId.get_next_id()
            MetricChart(chart_name=copy_chart.chart_name,
                        metric_id=metric_id,
                        internal_chart_name=internal_chart_name,
                        data_sets=json.dumps(data_sets),
                        leaf=True,
                        description=copy_chart.description,
                        owner_info=copy_chart.owner_info,
                        source=copy_chart.source,
                        positive=copy_chart.positive,
                        y1_axis_title=y1_axis_title,
                        visualization_unit=y1_axis_title,
                        metric_model_name=copy_chart.metric_model_name,
                        base_line_date=base_line_date,
                        work_in_progress=False,
                        platform=FunPlatform.F1).save()
    print "added datasets for inspur read write multiple F1 single volume"

if __name__ == "__main_changed_zipeffort__":
    internal_chart_name = "inspur_8131_compression_ratio_benchmarking_auto"
    chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
    data_sets = json.loads(chart.data_sets)
    for data_set in data_sets:
        data_set["inputs"]["input_effort_name"] = "ZIP_EFFORT_7Gbps"
        data_set["output"]["reference"] = -1
    chart.data_sets = json.dumps(data_sets)
    chart.save()
    print "effort name changed for auto"

if __name__ == "__main_boot_timings__":
    output_names = ["output_parsing_config", "output_parsing_config_end", "output_all_vps_online",
                    "output_sending_host_booted_message"]
    base_line_date = datetime(year=2019, month=5, day=27, minute=0, hour=0, second=0)
    data_sets = []
    for output_name in output_names:
        if "parsing_config_end" in output_name:
            name = "parsing config end"
            y1_axis_title = PerfUnit.UNIT_SECS
        elif "parsing_config" in output_name:
            name = "parsing config time"
            y1_axis_title = PerfUnit.UNIT_USECS
        elif "online" in output_name:
            name = "all VPs online"
            y1_axis_title = PerfUnit.UNIT_SECS
        else:
            name = "sending HOST_BOOTED message"
            y1_axis_title = PerfUnit.UNIT_SECS
        one_data_set = {}
        one_data_set["name"] = name
        one_data_set["inputs"] = {}
        one_data_set["inputs"]["input_platform"] = FunPlatform.F1
        one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1,
                                  "reference": -1, "unit": y1_axis_title}
        data_sets.append(one_data_set)
    metric_id = LastMetricId.get_next_id()
    MetricChart(chart_name="F1 Timings",
                metric_id=metric_id,
                internal_chart_name="f1_timings",
                data_sets=json.dumps(data_sets),
                leaf=True,
                description="TBD",
                owner_info="Michael Boksanyi (michael.boksanyi@fungible.com)",
                source="https://github.com/fungible-inc/FunOS/blob/f1cf84392b353200317449de77f3ea0a11d8cf2a/tests/wutest_test.c",
                positive=False,
                y1_axis_title=PerfUnit.UNIT_MSECS,
                visualization_unit=PerfUnit.UNIT_MSECS,
                metric_model_name="BootTimePerformance",
                base_line_date=base_line_date,
                work_in_progress=False,
                platform=FunPlatform.F1).save()
    print "added charts for extra boot timings"

if __name__ == "__main_nw_fix__":
    model_names = ["HuThroughputPerformance", "HuLatencyPerformance"]
    for model_name in model_names:
        app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
        metric_model = app_config.get_metric_models()[model_name]
        entries = metric_model.objects.all()
        print len(entries), model_name
        for entry in entries:
            if entry.input_date_time.day >= 3 and entry.input_date_time.month >= 6 and entry.input_date_time.year >= 2019:
                print entry.input_date_time
                entry.delete()
    print "1st and 2nd june entries deleted for networking"

if __name__ == "__main_durable_tcp__":
    internal_chart_names_compression = ["read_4kb1vol12ssd_durable_volume_ec_4_output_latency", "read_4kb1vol12ssd_durable_volume_ec_output_iops", "rand_read_4kb1vol12ssd_durable_volume_ec_4_output_latency", "rand_read_4kb1vol12ssd_durable_volume_ec_output_iops"]
    fio_job_names_randread = ["ec_nvme_tcp_comp_randread_1pctcomp_8", "ec_nvme_tcp_comp_randread_50pctcomp_8", "ec_nvme_tcp_comp_randread_80pctcomp_8"]
    fio_job_names_read = ["ec_nvme_tcp_comp_read_1pctcomp_8", "ec_nvme_tcp_comp_read_50pctcomp_8", "ec_nvme_tcp_comp_read_80pctcomp_8"]
    for internal_chart_name in internal_chart_names_compression:
        copy_chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        if "rand_read" in internal_chart_name:
            fio_job_names = fio_job_names_randread
        else:
            fio_job_names = fio_job_names_read
        index = internal_chart_name.find('output')
        internal_name = internal_chart_name[:index] + 'nvmetcp_' + internal_chart_name[index:]
        if "iops" in internal_name:
            output_name = "output_read_iops"
            unit = PerfUnit.UNIT_OPS
        else:
            output_name = "output_read_avg_latency"
            unit = PerfUnit.UNIT_USECS
        data_sets = []
        for fio_job_name in fio_job_names:
            if "1pct" in fio_job_name:
                name = "1%"
            elif "50pct" in fio_job_name:
                name = "50%"
            else:
                name = "80%"
            one_data_set = {}
            one_data_set["name"] = name
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_platform"] = FunPlatform.F1
            one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1,
                                      "reference": -1, "unit": unit}
            data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=copy_chart.chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description=copy_chart.description,
                    owner_info=copy_chart.owner_info,
                    source=copy_chart.source,
                    positive=copy_chart.positive,
                    y1_axis_title=copy_chart.y1_axis_title,
                    visualization_unit=copy_chart.y1_axis_title,
                    metric_model_name=copy_chart.metric_model_name,
                    base_line_date=copy_chart.base_line_date,
                    work_in_progress=False,
                    platform=FunPlatform.F1).save()
    print "added charts for durable volume + compression nvmetcp"
    internal = "read_iod1_durable_volume_ec_nvmetcp_output_latency"
    operations = ["read", "rand_read"]
    qdepths = ["iod1", "iod8", "iod16", "iod32", "iod64"]
    outputs = ["output_latency", "output_iops"]
    for operation in operations:
        for output in outputs:
            if "iops" in output:
                internal_chart_name = operation + "_iod_durable_volume_ec_nvmetcp_" + output
                copy_chart_name = operation + "_iod_durable_volume_ec_" + output
                copy_chart = MetricChart.objects.get(internal_chart_name=copy_chart_name)
                data_sets = []
                for qdepth in qdepths:
                    if qdepth == "iod1":
                        qd = 1
                    elif qdepth == "iod8":
                        qd = 8
                    elif qdepth == "iod16":
                        qd = 16
                    elif qdepth == "iod32":
                        qd = 32
                    else:
                        qd = 64

                    if "rand_read" in operation:
                        fio_job_name = "ec_nvme_tcp_randread_" + str(qd)
                    else:
                        fio_job_name = "ec_nvme_tcp_read_" + str(qd)

                    one_data_set = {}
                    one_data_set["name"] = str(qd)
                    one_data_set["inputs"] = {}
                    one_data_set["inputs"]["input_platform"] = FunPlatform.F1
                    one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
                    one_data_set["output"] = {"name": "output_read_iops", 'min': 0, "max": -1, "expected": -1,
                                              "reference": -1, "unit": PerfUnit.UNIT_OPS}
                    data_sets.append(one_data_set)
                metric_id = LastMetricId.get_next_id()
                MetricChart(chart_name=copy_chart.chart_name,
                            metric_id=metric_id,
                            internal_chart_name=internal_chart_name,
                            data_sets=json.dumps(data_sets),
                            leaf=True,
                            description=copy_chart.description,
                            owner_info=copy_chart.owner_info,
                            source=copy_chart.source,
                            positive=copy_chart.positive,
                            y1_axis_title=copy_chart.y1_axis_title,
                            visualization_unit=copy_chart.y1_axis_title,
                            metric_model_name=copy_chart.metric_model_name,
                            base_line_date=copy_chart.base_line_date,
                            work_in_progress=False,
                            platform=FunPlatform.F1).save()
            else:
                for qdepth in qdepths:
                    internal_chart_name = operation + "_" + qdepth + "_durable_volume_ec_nvmetcp_" + output
                    copy_chart_name = operation + "_" + qdepth + "_durable_volume_ec_" + output
                    copy_chart = MetricChart.objects.get(internal_chart_name=copy_chart_name)
                    if qdepth == "iod1":
                        qd = 1
                    elif qdepth == "iod8":
                        qd = 8
                    elif qdepth == "iod16":
                        qd = 16
                    elif qdepth == "iod32":
                        qd = 32
                    else:
                        qd = 64

                    if "rand_read" in operation:
                        fio_job_name = "ec_nvme_tcp_randread_" + str(qd)
                    else:
                        fio_job_name = "ec_nvme_tcp_read_" + str(qd)

                    data_sets = json.loads(copy_chart.data_sets)
                    for data_set in data_sets:
                        data_set["inputs"]["input_fio_job_name"] = fio_job_name
                        data_set["output"]["max"] = -1
                        data_set["output"]["expected"] = -1
                        data_set["output"]["reference"] = -1
                        data_set["output"]["unit"] = PerfUnit.UNIT_USECS

                    metric_id = LastMetricId.get_next_id()
                    MetricChart(chart_name=copy_chart.chart_name,
                                metric_id=metric_id,
                                internal_chart_name=internal_chart_name,
                                data_sets=json.dumps(data_sets),
                                leaf=True,
                                description=copy_chart.description,
                                owner_info=copy_chart.owner_info,
                                source=copy_chart.source,
                                positive=copy_chart.positive,
                                y1_axis_title=copy_chart.y1_axis_title,
                                visualization_unit=copy_chart.y1_axis_title,
                                metric_model_name=copy_chart.metric_model_name,
                                base_line_date=copy_chart.base_line_date,
                                work_in_progress=False,
                                platform=FunPlatform.F1).save()
    print "added charts for durable volume ec nvmetcp"

if __name__ == "__main_hu_hu_fcp__":
    num_hosts = [1, 2]
    num_flows = [1, 8]
    flow_type = "HU_HU_FCP"
    frame_size = 1500
    offloads = True
    output_names = ["output_throughput", "output_pps", "output_latency"]
    base_line_date = datetime(year=2019, month=5, day=30, minute=0, hour=0, second=0)
    for num_flow in num_flows:
        for num_host in num_hosts:
            if num_flow == 1 and num_host == 2:
                break
            for output_name in output_names:
                internal_chart_name = "HU_HU_FCP_" + str(num_flow) + "TCP_" + str(num_host) + "H_offloads_enabled_" + output_name
                if "throughput" in internal_chart_name:
                    chart_name = "Throughput"
                    positive = True
                    model_name = "HuThroughputPerformance"
                    y1_axis_title = PerfUnit.UNIT_GBITS_PER_SEC
                    data_set_unit = PerfUnit.UNIT_MBITS_PER_SEC
                    outputs = [""]
                    name = "1500B"
                    data_set_output = output_name
                elif "pps" in internal_chart_name:
                    chart_name = "Packets per sec"
                    positive = True
                    model_name = "HuThroughputPerformance"
                    y1_axis_title = PerfUnit.UNIT_MPPS
                    data_set_unit = PerfUnit.UNIT_PPS
                    outputs = [""]
                    name = "1500B"
                    data_set_output = output_name
                else:
                    chart_name = "Latency"
                    positive = False
                    model_name = "HuLatencyPerformance"
                    y1_axis_title = PerfUnit.UNIT_USECS
                    data_set_unit = PerfUnit.UNIT_USECS
                    outputs = ["min", "P50", "P90", "P99"]
                    name = "1500B-"
                    data_set_output = output_name + "_"

                data_sets = []
                for output in outputs:
                    one_data_set = {}
                    one_data_set["name"] = name + output
                    one_data_set["inputs"] = {}
                    one_data_set["inputs"]["input_platform"] = FunPlatform.F1
                    one_data_set["inputs"]["input_frame_size"] = frame_size
                    one_data_set["inputs"]["input_flow_type"] = flow_type
                    one_data_set["inputs"]["input_num_hosts"] = num_host
                    one_data_set["inputs"]["input_num_flows"] = num_flow
                    one_data_set["inputs"]["input_protocol"] = "TCP"
                    one_data_set["output"] = {"name": data_set_output + output + "_h2h", 'min': 0, "max": -1, "expected": -1,
                                              "reference": -1, "unit": data_set_unit}
                    data_sets.append(one_data_set)
                metric_id = LastMetricId.get_next_id()
                MetricChart(chart_name=chart_name,
                            metric_id=metric_id,
                            internal_chart_name=internal_chart_name,
                            data_sets=json.dumps(data_sets),
                            leaf=True,
                            description="TBD",
                            owner_info="Zhuo (George) Liang (george.liang@fungible.com)",
                            source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/networking/funeth/performance.py",
                            positive=positive,
                            y1_axis_title=y1_axis_title,
                            visualization_unit=y1_axis_title,
                            metric_model_name=model_name,
                            base_line_date=base_line_date,
                            work_in_progress=False,
                            platform=FunPlatform.F1).save()
    print" added charts for HU_HU_FCP 2 F1s"

<<<<<<< HEAD
if __name__ == "__main_raw_block_nvmetcp__":
=======
if __name__ == "__main_multiple_tcp_raw_block__":
>>>>>>> d8e62381a1a2943c8c37ee6275a9cd48525f816f
    internal_chart_names = ["rand_read_qd_nvmetcp_output_iops", "rand_write_qd_nvmetcp_output_iops"]
    multi_vol = "(N vols)"
    fio_read_job_names = ["fio_tcp_randread_blt_32_4_nvols", "fio_tcp_randread_blt_32_8_nvols"]
    fio_write_job_names = ["fio_tcp_randwrite_blt_32_4_nvols", "fio_tcp_randwrite_blt_32_8_nvols"]
    for internal_chart_name in internal_chart_names:
        if "rand_read" in internal_chart_name:
            output_name = "output_read_iops"
            fio_job_names = fio_read_job_names
        else:
            output_name = "output_write_iops"
            fio_job_names = fio_write_job_names
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        data_sets = json.loads(chart.data_sets)
        for fio_job_name in fio_job_names:
            if "32_4" in fio_job_name:
                name = "qd128"
            else:
                name = "qd256"
            one_data_set = {}
            one_data_set["name"] = name + multi_vol
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_platform"] = FunPlatform.F1
            one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1,
                                      "reference": -1, "unit": PerfUnit.UNIT_OPS}
            data_sets.append(one_data_set)
        chart.data_sets = json.dumps(data_sets)
        chart.save()
    print "added datasets for the raw block nvme tcp charts"

if __name__ == "__main_voltest_lsv__":
    internal_chart_names = ["voltest_lsv_1instances_blt_iops", "voltest_lsv_1instances_blt_bandwidth", "voltest_lsv_4instances_blt_iops", "voltest_lsv_4instances_blt_bandwidth"]
    base_line_date = datetime(year=2019, month=6, day=1, minute=0, hour=0, second=0)
    for internal_chart_name in internal_chart_names:
        if "1instances" in internal_chart_name:
            model_name = "VoltestLsvPerformance"
        else:
            model_name = "VoltestLsv4Performance"
        if "iops" in internal_chart_name:
            chart_name = "BLT: IOPS"
            y1_axis_title = PerfUnit.UNIT_OPS
            output_names = ["output_read_iops", "output_write_iops"]
        else:
            chart_name = "BLT: Bandwidth"
            y1_axis_title = PerfUnit.UNIT_MBITS_PER_SEC
            output_names = ["output_read_bandwidth", "output_write_bandwidth"]
        data_sets = []
        for output_name in output_names:
            if "read" in output_name:
                name = "read"
            else:
                name = "write"
            one_data_set = {}
            one_data_set["name"] = name
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_platform"] = FunPlatform.F1
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1,
                                      "reference": -1, "unit": y1_axis_title}
            data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Xiaoqin Ma (xiaoqin.ma@fungible.com)",
                    source="https://github.com/fungible-inc/FunOS/blob/master/apps/voltest.c",
                    positive=True,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False,
                    platform=FunPlatform.F1).save()
    print "added charts for 1 instance and 4 instance lsv voltest"

if __name__ == "__main__":
    internal_chart_names = ["inspur_", "_write_", "_output_iops"]
    names = ["seq", "mixed_read", ""]
    
    
