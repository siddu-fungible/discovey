from web.fun_test.maintenance_old import *
from lib.system.fun_test import *
from datetime import datetime

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

if __name__ == "__main__":
    internal_chart_names = ["juniper_ipsec_enc_single_tunnel_output_throughput", "juniper_ipsec_enc_single_tunnel_output_pps",
                            "juniper_ipsec_enc_multi_tunnel_output_throughput", "juniper_ipsec_enc_multi_tunnel_output_pps",
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
