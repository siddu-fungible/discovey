from web.fun_test.maintenance_old import *
from lib.system.fun_test import *
from datetime import datetime
from web.fun_test.models_helper import add_jenkins_job_id_map
from dateutil import parser
from django.utils import timezone

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

if __name__ == "__main__":
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

if __name__ == "__main__":
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

