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

METRICS_BASE_DATA_FILE = WEB_ROOT_DIR + "/metrics.json"

if __name__ == "__main__kk":
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


if __name__ == "__main__":

    # S1 EC 8:4 latency, throughput charts
    internal_chart_names = ["s1_ec_8_eachto_4_latency", "s1_ec_8_eachto_4_throughput"]
    model_name = "EcPerformance"
    owner_info = "Mohit Saxena (mohit.saxena@fungible.com)"
    source = "https://github.com/fungible-inc/FunOS/blob/master/apps/integration_apps/ec/qa_ec_test.c"
    positive = True
    platform = FunPlatform.S1

    for internal_chart_name in internal_chart_names:
        one_data_set = {}
        data_sets = []
        if internal_chart_name == "s1_ec_8_eachto_4_latency":
            chart_name = "EC 8:4 Latency"
            y1_axis_title = PerfUnit.UNIT_NSECS
            description = 'Encode and Recovery latency of the EC accelerator with Reed-Solomon algorithm' \
                          ' for one Processor Cluster(PC) of S1. ' \
                          '<br><br>' \
                          '<u>Job details</u><br>' \
                          '<li> Number of data blocks - 8' \
                          '<li> Number of parity blocks - 4' \
                          '<li> Stride Length - 4k' \
                          '<li> Data block content type - random data' \
                          '<li> Request send from 1 VP to the the EC accelerator' \
                          '<li> Scatter & Gather Memory: HBM to HBM' \
                          '<li> Latency is calculated for both encode and recovery operation over 256 iterations' \
                          '<br><br>'
            output_names = OrderedDict([("output_encode_latency_avg", "Encode-avg"),
                                        ("output_recovery_latency_avg", "Recovery-avg")])

        elif internal_chart_name == "s1_ec_8_eachto_4_throughput":
            chart_name = "EC 8:4 Throughput"
            y1_axis_title = PerfUnit.UNIT_GBITS_PER_SEC
            description = 'Encode and Recovery throughput of the EC accelerator with Reed-Solomon algorithm' \
                          ' for multi-cluster of S1. ' \
                          '<br><br>' \
                          '<u>Job details</u><br>' \
                          '<li> Number of data blocks - 8' \
                          '<li> Number of parity blocks - 4' \
                          '<li> Stride Length - 4k' \
                          '<li> Data block content type - random data' \
                          '<li> Request send from 1 VP to the the EC accelerator' \
                          '<li> Scatter & Gather Memory: HBM to HBM' \
                          '<li> Latency is calculated for both encode and recovery operation over 256 iterations' \
                          '<br><br>'
            output_names = OrderedDict([("output_encode_throughput_avg", "Encode-avg"),
                                        ("output_recovery_throughput_avg", "Recovery-avg")])

        inputs = {
            "input_platform": platform
        }

        for output_name in output_names:
            output = {
                "name": output_name,
                "unit": y1_axis_title,
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

    # S1 JPEG compression_throughput, decompression_throughput, compression_ratio charts

    internal_chart_names = ["s1_compression_throughput", "s1_decompression_throughput", "s1_compression_ratio"]
    model_name = "TeraMarkJpegPerformance"
    owner_info = "Harinadh Saladi (harinadh.saladi@fungible.com)"
    source = "https://github.com/fungible-inc/FunOS/blob/master/apps/integration_apps/zip/jpeg_perf_test.c"
    positive = True
    platform = FunPlatform.S1

    for internal_chart_name in internal_chart_names:
        one_data_set = {}
        data_sets = []

        if internal_chart_name == "s1_compression_throughput":
            chart_name = "JPEG compression throughput"
            input_operation = "Compression throughput with Driver"
            output_name = "output_average_bandwidth"
            y1_axis_title = PerfUnit.UNIT_GBITS_PER_SEC
            description = 'Compression throughput measured using 1 PC (Processing Cluster); this measurement does not' \
                          ' includes the time spent in driver.' \
                          '<br><b>' \
                          '<u>Images used</u>' \
                          '</b></p><table>' \
                          '<tr>' \
                          '<td><b>Name&nbsp&nbsp&nbsp</b></td><td><b>Size</b></td>' \
                          '</tr>' \
                          '<tr>' \
                          '<td>kodim13_jpg</td>    <td>197KB</td>' \
                          '</tr>' \
                          '<tr>' \
                          '<td>kodim18_jpg</td>    <td>150KB</td>' \
                          '</tr>' \
                          '<tr>' \
                          '<td>kodim20_jpg</td>    <td>84KB</td>' \
                          '</tr>' \
                          '</table>' \
                          '<br><b><u>Job Details</u></b><br>' \
                          '<u>Test Inputs located at</u>:  <code>/project/users/ashaikh/qa_test_inputs/</code><br>' \
                          '<hr>' \
                          'Test owner: Aamir Shaikh (<a href="mailto:aamir.shaikh@fungible.com">' \
                          'aamir.shaikh@fungible.com</a>)<br>' \
                          '<hr>' \
                          '<b>Details</b><br>' \
                          '<u>Platform</u>: S1<br>' \
                          '<u>Boot args</u>: <code>app=jpeg_perf_test num_iter=20 --disable-wu-watchdog</code><br>' \
                          '<u>Test code</u>: <code> apps/integration_apps/zip/jpeg_perf_test.c</code><br>' \
                          '<u>See jobs:</u> <a href="http://palladium-jobs.fungible.local:8080/?tag=jpeg_teramark">' \
                          'here</a>'

        elif internal_chart_name == "s1_decompression_throughput":
            chart_name = "JPEG decompression throughput"
            input_operation = "JPEG Decompress"
            output_name = "output_average_bandwidth"
            y1_axis_title = PerfUnit.UNIT_GBITS_PER_SEC
            description = 'Data compression ratio is defined as the ratio between the uncompressed size and compressed' \
                          ' size.<br>Compression Ratio = Uncompressed Size / Compressed Size<br>' \
                          'A representation that compresses a 10 MB file to 2 MB has a compression ratio of 10/2 = 5,' \
                          ' often notated as an ' \
                          'explicit ratio,5:1 (read "five" to "one"), or as an implicit ratio, 5/1.' \
                          '<br><b>' \
                          '<u>Images used</u>' \
                          '</b></p><table>' \
                          '<tr>' \
                          '<td><b>Name&nbsp&nbsp&nbsp</b></td><td><b>Size</b></td>' \
                          '</tr>' \
                          '<tr>' \
                          '<td>kodim13_jpg</td>    <td>197KB</td>' \
                          '</tr>' \
                          '<tr>' \
                          '<td>kodim18_jpg</td>    <td>150KB</td>' \
                          '</tr>' \
                          '<tr>' \
                          '<td>kodim20_jpg</td>    <td>84KB</td>' \
                          '</tr>' \
                          '</table>' \
                          '<br><b><u>Job Details</u></b><br>' \
                          '<u>Test Inputs located at</u>:  <code>/project/users/ashaikh/qa_test_inputs/</code><br>' \
                          '<hr>' \
                          'Test owner: Aamir Shaikh (<a href="mailto:aamir.shaikh@fungible.com">' \
                          'aamir.shaikh@fungible.com</a>)<br>' \
                          '<hr>' \
                          '<b>Details</b><br>' \
                          '<u>Platform</u>: S1<br>' \
                          '<u>Boot args</u>: <code>app=jpeg_perf_test num_iter=20 --disable-wu-watchdog</code><br>' \
                          '<u>Test code</u>: <code> apps/integration_apps/zip/jpeg_perf_test.c</code><br>' \
                          '<u>See jobs:</u> <a href="http://palladium-jobs.fungible.local:8080/?tag=jpeg_teramark">' \
                          'here</a>'

        elif internal_chart_name == "s1_compression_ratio":
            chart_name = "JPEG Compression-ratio"
            input_operation = "JPEG Compression"
            output_name = "output_compression_ratio"
            y1_axis_title = PerfUnit.UNIT_NUMBER
            description = 'Decompression throughput measured using one PC. It measures the time taken by the' \
                          ' accelerator to decompress the image.The time spent by the driver is ignored in this' \
                          ' calculation as the driver adds an overhead of ~10%.' \
                          '<br><b>' \
                          '<u>Images used</u>' \
                          '</b></p><table>' \
                          '<tr>' \
                          '<td><b>Name&nbsp&nbsp&nbsp</b></td><td><b>Size</b></td>' \
                          '</tr>' \
                          '<tr>' \
                          '<td>kodim13_jpg</td>    <td>197KB</td>' \
                          '</tr>' \
                          '<tr>' \
                          '<td>kodim18_jpg</td>    <td>150KB</td>' \
                          '</tr>' \
                          '<tr>' \
                          '<td>kodim20_jpg</td>    <td>84KB</td>' \
                          '</tr>' \
                          '</table>' \
                          '<br><b><u>Job Details</u></b><br>' \
                          '<u>Test Inputs located at</u>:  <code>/project/users/ashaikh/qa_test_inputs/</code><br>' \
                          '<hr>' \
                          'Test owner: Aamir Shaikh (<a href="mailto:aamir.shaikh@fungible.com">' \
                          'aamir.shaikh@fungible.com</a>)<br>' \
                          '<hr>' \
                          '<b>Details</b><br>' \
                          '<u>Platform</u>: S1<br>' \
                          '<u>Boot args</u>: <code>app=jpeg_perf_test num_iter=20 --disable-wu-watchdog</code><br>' \
                          '<u>Test code</u>: <code> apps/integration_apps/zip/jpeg_perf_test.c</code><br>' \
                          '<u>See jobs:</u> <a href="http://palladium-jobs.fungible.local:8080/?tag=jpeg_teramark">' \
                          'here</a>'

        inputs = {
            "input_platform": platform,
            "input_operation": input_operation
        }

        output = {
            "name": output_name,
            "unit": y1_axis_title,
            "min": 0,
            "max": -1,
            "expected": -1,
            "reference": -1
        }

        image_names_list = ['kodim13_jpg', 'kodim18_jpg', 'kodim20_jpg']

        for image in image_names_list:
            inputs["input_image"] = image
            one_data_set["name"] = image
            one_data_set["inputs"] = inputs.copy()
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
