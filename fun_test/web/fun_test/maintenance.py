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

if __name__ == "__main_channel_parall__":
    internal_chart_names = ["channel_parall_performance_4_8_16", "channel_parall_performance_1000"]
    base_line_date = datetime(year=2019, month=6, day=8, minute=0, hour=0, second=0)
    for internal_chart_name in internal_chart_names:
        chart_name = "Channel Parall Speed"
        if "4_8_16" in internal_chart_name:
            number_channels = [4, 8, 16]
        else:
            number_channels = [1000]
        data_sets = []
        for number_channel in number_channels:
            one_data_set = {}
            one_data_set["name"] = str(number_channel)
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_number_channels"] = number_channel
            one_data_set["output"] = {"name": "output_channel_parall_speed", 'min': 0, "max": -1, "expected": -1,
                                      "reference": -1, "unit": PerfUnit.UNIT_USECS}
            data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="Measures the speed at which channel_parall operates. The forked children are just busy loops (1usecs).",
                    owner_info="Bertrand Serlet (bertrand.serlet@fungible.com)",
                    source="https://github.com/fungible-inc/FunOS/blob/master/apps/channel_parall_speed.c",
                    positive=False,
                    y1_axis_title=PerfUnit.UNIT_USECS,
                    visualization_unit=PerfUnit.UNIT_USECS,
                    metric_model_name="ChannelParallPerformance",
                    base_line_date=base_line_date,
                    work_in_progress=False,
                    platform=FunPlatform.F1).save()
    print "added charts for channel parall speed performance"

if __name__ == "__main_0%_compression__":
    internal_chart_names = ["read_4kb1vol12ssd_durable_volume_ec_output_iops",
                            "read_4kb1vol12ssd_durable_volume_ec_4_output_latency",
                            "rand_read_4kb1vol12ssd_durable_volume_ec_4_output_latency",
                            "rand_read_4kb1vol12ssd_durable_volume_ec_output_iops"]
    for internal_chart_name in internal_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        if "rand_read" in internal_chart_name:
            operation = "randread"
            fio_job_name = "ec_fio_25G_comp_disabled_randread_50"
        else:
            operation = "read"
            fio_job_name = "ec_fio_25G_comp_disabled_read_50"
        if "iops" in internal_chart_name:
            y1_axis_title = PerfUnit.UNIT_KOPS
            output_name = "output_read_iops"
            name = "0%"
        else:
            y1_axis_title = PerfUnit.UNIT_USECS
            output_name = "output_read_avg_latency"
            name = "0%-avg"
        if chart:
            data_sets = json.loads(chart.data_sets)
            one_data_set = {}
            one_data_set["name"] = name
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
            one_data_set["inputs"]["input_operation"] = operation
            one_data_set["inputs"]["input_platform"] = FunPlatform.F1
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1,
                                      "reference": -1, "unit": y1_axis_title}
            data_sets.append(one_data_set)
            chart.data_sets = json.dumps(data_sets)
            chart.save()
    print "added 0 compression dataset for durable volume EC + compression"

if __name__ == "__main_inspur_8k_comp__":
    internal_chart_names = ["inspur_8132_8k_rand_rw_comp_output_latency", "inspur_8132_8k_rand_rw_comp_output_iops"]
    model_name = "BltVolumePerformance"
    base_line_date = datetime(year=2019, month=6, day=10, minute=0, hour=0, second=0)
    fio_job_names = ["inspur_ec_comp_8k_randrw_1pctcomp_8", "inspur_ec_comp_8k_randrw_50pctcomp_8",
                     "inspur_ec_comp_8k_randrw_80pctcomp_8"]
    output_iops_names = ["output_read_iops", "output_write_iops"]
    output_latency_names = ["output_read_avg_latency", "output_write_avg_latency"]
    for internal_chart_name in internal_chart_names:
        if "latency" in internal_chart_name:
            positive = False
            y1_axis_title = PerfUnit.UNIT_USECS
            chart_name = "Latency"
            output_names = output_latency_names
            output_avg_name = "-avg"
        else:
            positive = True
            y1_axis_title = PerfUnit.UNIT_OPS
            chart_name = "IOPS"
            output_names = output_iops_names
            output_avg_name = ""

        data_sets = []
        for output_name in output_names:
            if "read" in output_name:
                operation = "read" + output_avg_name
            else:
                operation = "write" + output_avg_name
            for fio_job_name in fio_job_names:
                if "1pctcomp" in fio_job_name:
                    name = "1%-" + operation
                elif "50pctcomp" in fio_job_name:
                    name = "50%-" + operation
                else:
                    name = "80%-" + operation
                one_data_set = {}
                one_data_set["name"] = name
                one_data_set["inputs"] = {}
                one_data_set["inputs"]["input_platform"] = FunPlatform.F1
                one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
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
                    owner_info="Aamir Shaikh (aamir.shaikh@fungible.com)",
                    source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/inspur_comp_perf.py",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False,
                    platform=FunPlatform.F1).save()
    print "added charts for inspur random read write compression"

if __name__ == "__main_changed_owner__":
    entries = MetricChart.objects.all()
    for entry in entries:
        if "Tahsin" in entry.owner_info:
            print entry.owner_info
            entry.owner_info = "Bertrand Serlet (bertrand.serlet@fungible.com)"
            entry.save()
    print "changed owner to Bertrand"

if __name__ == "__main_rand_write_rawblock_nvmetcp__":
    random_write_qd64 = ["fio_tcp_randwrite_blt_16_4_scaling", "fio_tcp_randwrite_blt_32_2_nvols"]
    random_write_qd128 = ["fio_tcp_randwrite_blt_32_4_nvols"]
    model_name = "BltVolumePerformance"
    base_line_date = datetime(year=2019, month=1, day=26, minute=0, hour=0, second=0)
    internal_chart_names = ["rand_write_qd64_nvmetcp_output_latency", "rand_write_qd128_nvmetcp_output_latency"]
    output_names = ["output_write_avg_latency", "output_write_99_latency", "output_write_99_99_latency"]
    for internal_chart_name in internal_chart_names:
        if "qd64" in internal_chart_name:
            fio_job_names = random_write_qd64
        else:
            fio_job_names = random_write_qd128
        operation = "randwrite"
        chart_name = "Latency"
        data_sets = []
        for fio_job_name in fio_job_names:
            if "scaling" in fio_job_name:
                vol = "(1 vol)"
            else:
                vol = "(N vols)"

            for output_name in output_names:
                if "avg" in output_name:
                    name = "avg" + vol
                elif "99_99" in output_name:
                    name = "99.99%" + vol
                else:
                    name = "99%" + vol
                one_data_set = {}
                one_data_set["name"] = name
                one_data_set["inputs"] = {}
                one_data_set["inputs"]["input_platform"] = FunPlatform.F1
                one_data_set["inputs"]["input_operation"] = operation
                one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
                one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1,
                                          "reference": -1, "unit": PerfUnit.UNIT_USECS}
                data_sets.append(one_data_set)

        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Radhika Naik (radhika.naik@fungible.com)",
                    source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/multiple_blt_tcp_perf.py",
                    positive=False,
                    y1_axis_title=PerfUnit.UNIT_USECS,
                    visualization_unit=PerfUnit.UNIT_USECS,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False,
                    platform=FunPlatform.F1).save()
    print "added charts for random write latency"

if __name__ == "__main_rand_read_rawblock_nvmetcp__":
    internal_chart_names = ["rand_read_qd1_nvmetcp_output_latency",
                            "rand_read_qd128_nvmetcp_output_latency",
                            "rand_read_qd256_nvmetcp_output_latency"]
    model_name = "BltVolumePerformance"
    base_line_date = datetime(year=2019, month=1, day=26, minute=0, hour=0, second=0)
    for internal_chart_name in internal_chart_names:
        try:
            chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
            data_sets = json.loads(chart.data_sets)
            for data_set in data_sets:
                data_set["name"] = str(data_set["name"]) + "(1 vol)"
            chart.data_sets = json.dumps(data_sets)
            chart.owner_info = "Radhika Naik (radhika.naik@fungible.com)"
            chart.source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/multiple_blt_tcp_perf.py"
            chart.save()
            if "qd128" in internal_chart_name:
                new_data_sets = json.loads(chart.data_sets)
                for data_set in new_data_sets:
                    data_set["name"] = data_set["name"].replace("1 vol", "N vols")
                    data_set["inputs"]["input_fio_job_name"] = "fio_tcp_randread_blt_32_4_nvols"
                    data_set["output"]["reference"] = -1
                    data_sets.append(data_set)
                chart.data_sets = json.dumps(data_sets)
                chart.save()
        except ObjectDoesNotExist:
            chart_name = "Latency"
            chart = MetricChart.objects.get(internal_chart_name="rand_read_qd1_nvmetcp_output_latency")
            data_sets = json.loads(chart.data_sets)
            for data_set in data_sets:
                data_set["name"] = data_set["name"].replace("1 vol", "N vols")
                data_set["inputs"]["input_fio_job_name"] = "fio_tcp_randread_blt_32_8_nvols"
                data_set["output"]["reference"] = -1
            metric_id = LastMetricId.get_next_id()
            MetricChart(chart_name=chart_name,
                        metric_id=metric_id,
                        internal_chart_name=internal_chart_name,
                        data_sets=json.dumps(data_sets),
                        leaf=True,
                        description="TBD",
                        owner_info="Radhika Naik (radhika.naik@fungible.com)",
                        source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/multiple_blt_tcp_perf.py",
                        positive=False,
                        y1_axis_title=PerfUnit.UNIT_USECS,
                        visualization_unit=PerfUnit.UNIT_USECS,
                        metric_model_name=model_name,
                        base_line_date=base_line_date,
                        work_in_progress=False,
                        platform=FunPlatform.F1).save()
    print "added charts for random read latency"

if __name__ == "__main_nvols_to_8vols__":
    internal_chart_names = ["inspur_single_f1_host", "inspur_single_f1_host_6"]
    for internal_chart_name in internal_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        children = json.loads(chart.children)
        print json.dumps(children)
        for child in children:
            child_chart = MetricChart.objects.get(metric_id=child)
            data_sets = json.loads(child_chart.data_sets)
            for data_set in data_sets:
                if "(N vols)" in data_set["name"]:
                    print data_set["name"]
                    data_set["name"] = data_set["name"].replace("(N vols)", "(8 vols)")
            child_chart.data_sets = json.dumps(data_sets)
            child_chart.save()

if __name__ == "__main_multi_host_nvmetcp__":
    model_name = "BltVolumePerformance"
    base_line_date = datetime(year=2019, month=6, day=20, minute=0, hour=0, second=0)
    internal_iops_chart_names = ["rand_read_qd_multi_host_nvmetcp_output_iops",
                                 "rand_write_qd_multi_host_nvmetcp_output_iops"]
    internal_latency_chart_names = [
        "rand_read_qd1_multi_host_nvmetcp_output_latency",
        "rand_read_qd32_multi_host_nvmetcp_output_latency",
        "rand_read_qd64_multi_host_nvmetcp_output_latency",
        "rand_write_qd1_multi_host_nvmetcp_output_latency",
        "rand_write_qd32_multi_host_nvmetcp_output_latency",
        "rand_write_qd64_multi_host_nvmetcp_output_latency"]
    fio_read_job_names = ["fio_tcp_randread_blt_1_1_nhosts",
                          "fio_tcp_randread_blt_32_1_nhosts",
                          "fio_tcp_randread_blt_32_2_nhosts"]
    fio_write_job_names = ["fio_tcp_randwrite_blt_1_1_nhosts",
                           "fio_tcp_randwrite_blt_32_1_nhosts",
                           "fio_tcp_randwrite_blt_32_2_nhosts"]
    output_read_names = ["output_read_avg_latency", "output_read_99_latency", "output_read_99_99_latency"]
    output_write_names = ["output_write_avg_latency", "output_write_99_latency", "output_write_99_99_latency"]
    for internal_iops_chart_name in internal_iops_chart_names:
        chart_name = "IOPS"
        if "rand_read" in internal_iops_chart_name:
            fio_job_names = fio_read_job_names
            output_name = "output_read_iops"
        else:
            fio_job_names = fio_write_job_names
            output_name = "output_write_iops"
        data_sets = []
        for fio_job_name in fio_job_names:
            if "1_1" in fio_job_name:
                name = "qd1"
            elif "32_1" in fio_job_name:
                name = "qd32"
            else:
                name = "qd64"
            one_data_set = {}
            one_data_set["name"] = name
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
            one_data_set["inputs"]["input_platform"] = FunPlatform.F1
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1,
                                      "reference": -1, "unit": PerfUnit.UNIT_OPS}
            data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_iops_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Radhika Naik (radhika.naik@fungible.com)",
                    source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/multi_host_blt_tcp_perf.py",
                    positive=True,
                    y1_axis_title=PerfUnit.UNIT_OPS,
                    visualization_unit=PerfUnit.UNIT_OPS,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False,
                    platform=FunPlatform.F1).save()
    print "added iops chart"
    for internal_latency_chart_name in internal_latency_chart_names:
        if "rand_read" in internal_latency_chart_name:
            fio_job_names = fio_read_job_names
            output_names = output_read_names
            if "qd1" in internal_latency_chart_name:
                fio_job_name = "fio_tcp_randread_blt_1_1_nhosts"
            elif "qd32" in internal_latency_chart_name:
                fio_job_name = "fio_tcp_randread_blt_32_1_nhosts"
            else:
                fio_job_name = "fio_tcp_randread_blt_32_2_nhosts"
        else:
            fio_job_names = fio_write_job_names
            output_names = output_write_names
            if "qd1" in internal_latency_chart_name:
                fio_job_name = "fio_tcp_randwrite_blt_1_1_nhosts"
            elif "qd32" in internal_latency_chart_name:
                fio_job_name = "fio_tcp_randwrite_blt_32_1_nhosts"
            else:
                fio_job_name = "fio_tcp_randwrite_blt_32_2_nhosts"
        data_sets = []
        for output_name in output_names:
            if "avg" in output_name:
                name = "avg"
            elif "99_99" in output_name:
                name = "99.99%"
            else:
                name = "99%"
            one_data_set = {}
            one_data_set["name"] = name
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
            one_data_set["inputs"]["input_platform"] = FunPlatform.F1
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1,
                                      "reference": -1, "unit": PerfUnit.UNIT_USECS}
            data_sets.append(one_data_set)
        chart_name = "Latency"
        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_latency_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Radhika Naik (radhika.naik@fungible.com)",
                    source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/multi_host_blt_tcp_perf.py",
                    positive=False,
                    y1_axis_title=PerfUnit.UNIT_USECS,
                    visualization_unit=PerfUnit.UNIT_USECS,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False,
                    platform=FunPlatform.F1).save()
    print "added latency charts"

if __name__ == "__main__lsv_charts_update":
    metric_id_list = [795, 796, 797, 798]
    for metric_id in metric_id_list:
        chart = MetricChart.objects.get(metric_id=metric_id)
        chart.owner_info = "Sunil Subramanya (sunil.subramanya@fungible.com)"
        data_sets_uni = chart.data_sets
        data_sets = json.loads(data_sets_uni)[0]
        output_name = data_sets["output"]['name']
        data_sets['name'] = 'read_write'
        data_sets['output']['reference'] = -1
        if 'iops' in output_name:
            data_sets["output"]['name'] = 'output_read_write_iops'
        else:
            data_sets['output']['name'] = 'output_read_write_bandwidth'

        data_sets_json = json.dumps([data_sets])
        chart.data_sets = data_sets_json
        chart.save()

if __name__ == "__main__inspur_random_read_write_iodepth_vol":
    internal_chart_names = ["inspur_single_f1_host", "inspur_single_f1_host_6"]
    fio_job_names = ["inspur_8k_random_read_write_iodepth_8_vol_4", "inspur_8k_random_read_write_iodepth_16_vol_4",
                     "inspur_8k_random_read_write_iodepth_32_vol_4", "inspur_8k_random_read_write_iodepth_64_vol_4",
                     "inspur_8k_random_read_write_iodepth_128_vol_4", "inspur_8k_random_read_write_iodepth_256_vol_4"]
    for internal_chart_name in internal_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        if chart:
            children = json.loads(chart.children)
            for child in children:
                child_chart = MetricChart.objects.get(metric_id=child)
                if "_qd1_" not in child_chart.internal_chart_name:
                    if "latency" in child_chart.internal_chart_name:
                        output_names = ["output_read_avg_latency", "output_write_avg_latency"]
                        name = "-avg(4 vols)"
                        unit = PerfUnit.UNIT_USECS
                    else:
                        output_names = ["output_read_iops", "output_write_iops"]
                        name = "(4 vols)"
                        unit = PerfUnit.UNIT_OPS
                    if "_qd8_" in child_chart.internal_chart_name:
                        fio_job_name = "inspur_8k_random_read_write_iodepth_8_vol_4"
                    elif "_qd16_" in child_chart.internal_chart_name:
                        fio_job_name = "inspur_8k_random_read_write_iodepth_16_vol_4"
                    elif "_qd32_" in child_chart.internal_chart_name:
                        fio_job_name = "inspur_8k_random_read_write_iodepth_32_vol_4"
                    elif "_qd64_" in child_chart.internal_chart_name:
                        fio_job_name = "inspur_8k_random_read_write_iodepth_64_vol_4"
                    elif "_qd128_" in child_chart.internal_chart_name:
                        fio_job_name = "inspur_8k_random_read_write_iodepth_128_vol_4"
                    else:
                        fio_job_name = "inspur_8k_random_read_write_iodepth_256_vol_4"
                    data_sets = json.loads(child_chart.data_sets)
                    for output_name in output_names:
                        if "read" in output_name:
                            operation = "read"
                        else:
                            operation = "write"
                        one_data_set = {}
                        one_data_set["name"] = operation + name
                        one_data_set["inputs"] = {}
                        one_data_set["inputs"]["input_platform"] = FunPlatform.F1
                        one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
                        one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1,
                                                  "reference": -1, "unit": unit}
                        data_sets.append(one_data_set)
                    child_chart.data_sets = json.dumps(data_sets)
                    child_chart.save()
                    print "added datasets for {}".format(child_chart.chart_name)
    print "added datasets for inspur containers"

if __name__ == "__main_durable_volume_ec__":
    # __main_1_change_from_0 % _to_no_compression_(aamir)
    metric_id_list = [535, 536, 538, 539]
    for metric_id in metric_id_list:
        chart = MetricChart.objects.get(metric_id=metric_id)
        data_set_uni = chart.data_sets
        data_sets_list = json.loads(data_set_uni)
        for one_data_set in data_sets_list:
            name = one_data_set['name']
            match_zero = re.search(r'\d+', name)
            if match_zero:
                if match_zero.group() == '0':
                    one_data_set['name'] = name.replace("0%", "No Compression")
                    print ("Metric id : {} name : {} changed to {}".format(metric_id, name, one_data_set['name']))

        data_sets = json.dumps(data_sets_list)
        chart.data_sets = data_sets
        chart.save()

    # __main__2_change_input_fio_job_name_and_remove_8_add_128_(aamir)

    metric_id_list = [757, 758, 759, 760]
    for metric_id in metric_id_list:
        chart = MetricChart.objects.get(metric_id=metric_id)
        data_set_uni = chart.data_sets
        data_sets_list = json.loads(data_set_uni)
        for one_data_set in data_sets_list:
            input_fio_job_name = one_data_set['inputs']['input_fio_job_name']
            input_fio_job_name = input_fio_job_name.replace('_comp_', '_').replace('p_8', 'p_128')
            one_data_set['inputs']['input_fio_job_name'] = input_fio_job_name
        data_sets = json.dumps(data_sets_list)
        chart.data_sets = data_sets
        chart.save()

    # __main__3_iops_remove_8_add_128_(aamir)

    metric_id_list = [766, 772]
    for metric_id in metric_id_list:
        chart = MetricChart.objects.get(metric_id=metric_id)
        data_set_uni = chart.data_sets
        data_sets_list = json.loads(data_set_uni)
        for one_data_set in data_sets_list:
            if one_data_set['name'] == '8':
                data_sets_list.remove(one_data_set)
                one_data_set['name'] = '128'
                one_data_set['inputs']['input_fio_job_name'] = \
                    one_data_set['inputs']['input_fio_job_name'].replace('8', '128')
                data_sets_list.append(one_data_set)
                break

        data_sets = json.dumps(data_sets_list)
        chart.data_sets = data_sets
        chart.save()

    # __main__4_latency_change_8_to_128_(aamir)

    metric_id_list = [762, 768]
    for metric_id in metric_id_list:
        chart = MetricChart.objects.get(metric_id=metric_id)
        chart.chart_name = chart.chart_name.replace('=8', '=128')
        chart.internal_chart_name = chart.internal_chart_name.replace('d8', 'd128')
        data_set_uni = chart.data_sets
        data_sets_list = json.loads(data_set_uni)
        for one_data_set in data_sets_list:
            one_data_set['inputs']['input_fio_job_name'] = \
                one_data_set['inputs']['input_fio_job_name'].replace('_8', '_128')
        data_sets = json.dumps(data_sets_list)
        chart.data_sets = data_sets
        chart.save()

if __name__ == "__main_container_data_sets__":
    entries = MetricChart.objects.all()
    leafCount = 0
    modelCount = 0
    for entry in entries:
        if not entry.leaf and entry.metric_model_name == "MetricContainer":
            data_sets = []
            one_data_set = {}
            one_data_set["name"] = "Scores"
            one_data_set["output"] = {"min": 0, "max": 200}
            data_sets.append(one_data_set)
            entry.data_sets = json.dumps(data_sets)
            entry.save()
    print "Added datasets for containers"

if __name__ == "__main_companion_charts__":
    charts = ["iops", "latency"]
    xaxis_title = "log2(qDepth)"
    chart_type = ChartType.REGULAR
    fun_chart_type = FunChartType.LINE_CHART
    for chart in charts:
        if "iops" in chart:
            names = ["read(8 vols)", "write(8 vols)"]
            chart_name = "inspur_single_f1_host"
            yaxis_title = "log10(" + PerfUnit.UNIT_OPS + ")"
            title = "qdepth vs ops"
        else:
            names = ["read-avg(8 vols)", "write-avg(8 vols)"]
            chart_name = "inspur_single_f1_host_6"
            yaxis_title = "log10(" + PerfUnit.UNIT_USECS + ")"
            title = "qdepth vs usecs"
        data_sets = []
        for name in names:
            if "iops" in chart:
                if "read" in name:
                    output_name = "output_read_iops"
                else:
                    output_name = "output_write_iops"
            else:
                if "read" in name:
                    output_name = "output_read_avg_latency"
                else:
                    output_name = "output_write_avg_latency"
            one_data_set = {}
            one_data_set["name"] = name
            one_data_set["filters"] = {}
            one_data_set["filters"] = [{"name": 1, "model_name": "BltVolumePerformance", "filter": {
                "input_fio_job_name": "inspur_8k_random_read_write_iodepth_1_vol_8",
                "input_platform": FunPlatform.F1}},
                                       {"name": 8, "model_name": "BltVolumePerformance", "filter": {
                                           "input_fio_job_name": "inspur_8k_random_read_write_iodepth_8_vol_8",
                                           "input_platform": FunPlatform.F1}},
                                       {"name": 16, "model_name": "BltVolumePerformance", "filter": {
                                           "input_fio_job_name": "inspur_8k_random_read_write_iodepth_16_vol_8",
                                           "input_platform": FunPlatform.F1}},
                                       {"name": 32, "model_name": "BltVolumePerformance", "filter": {
                                           "input_fio_job_name": "inspur_8k_random_read_write_iodepth_32_vol_8",
                                           "input_platform": FunPlatform.F1}},
                                       {"name": 64, "model_name": "BltVolumePerformance", "filter": {
                                           "input_fio_job_name": "inspur_8k_random_read_write_iodepth_64_vol_8",
                                           "input_platform": FunPlatform.F1}},
                                       {"name": 128, "model_name": "BltVolumePerformance", "filter": {
                                           "input_fio_job_name": "inspur_8k_random_read_write_iodepth_128_vol_8",
                                           "input_platform": FunPlatform.F1}},
                                       {"name": 256, "model_name": "BltVolumePerformance", "filter": {
                                           "input_fio_job_name": "inspur_8k_random_read_write_iodepth_256_vol_8",
                                           "input_platform": FunPlatform.F1}}]
            one_data_set["output_field"] = output_name
            data_sets.append(one_data_set)
        print json.dumps(data_sets)
        chart_id = LastChartId.get_next_id()
        Chart(chart_id=chart_id, title=title, x_axis_title=xaxis_title, y_axis_title=yaxis_title,
              chart_type=chart_type, fun_chart_type=fun_chart_type, series_filters=data_sets, x_scale="log2",
              y_scale="log10").save()
        chart = MetricChart.objects.get(internal_chart_name=chart_name)
        if chart:
            chart.companion_charts = [chart_id]
            chart.save()
        print "added chart id: {}", format(chart_id)
    print "added companion charts"

if __name__ == "__main__soak_flows_apps":
    internal_chart_names = ['soak_flows_busy_loop_10usecs', 'soak_flows_dma_memcpy_test_1MB']
    for internal_chart_name in internal_chart_names:
        one_data_set = {}
        data_sets = []
        if internal_chart_name == "soak_flows_busy_loop_10usecs":
            chart_name = "Busy Loops 10usecs"
            input_name = "busy_loop_10usecs"
            one_data_set["name"] = "10usecs busy loop on a VP"
            model_name = "SoakFlowsBusyLoop10usecs"
            description = "Maximum number of ops across the entire chip, an op being a 10usecs busy loop on a VP." \
                          " Ideally, with 200 VPs, one would expect 20Kops. The real number is much lower though," \
                          " because not all VP participate, and because of overhead, so a reasonable expected number" \
                          " is 7Kops"
            output_field = "output_busy_loops_value"
        else:
            chart_name = "Soak Flows Busy Loop 10usecs"
            input_name = internal_chart_name
            one_data_set["name"] = "1MB non-coherent DMA memcpy"
            model_name = "SoakFlowsMemcpy1MBNonCoh"
            description = "Maximum number of ops across the entire chip, an op being a 1MB non-coherent DMA memcpy." \
                          " Ideally, the HBM bandwidth is 4Tb/s, but we are doing a read and a write, so one would" \
                          " expect 2Tb/8Mb = 250Kops. There may be other limiting factors though."
            output_field = "output_dma_memcpy_value"

        metric_id = LastMetricId.get_next_id()
        positive = True
        y1_axis_title = PerfUnit.UNIT_OPS
        owner_info = "Bertrand Serlet (bertrand.serlet@fungible.com)"
        source = 'https://github.com/fungible-inc/FunOS/blob/79f82e7a330220295afbaf5b3b28bf9296915131/tests/soak_flows_test.c'
        platform = FunPlatform.F1

        inputs = {"input_name": input_name,
                  "input_platform": "F1"}
        output = {"name": output_field,
                  "unit": PerfUnit.UNIT_OPS,
                  "min": 0,
                  "max": -1,
                  "expected": -1,
                  "reference": -1}

        one_data_set["inputs"] = inputs
        one_data_set['output'] = output

        data_sets.append(one_data_set)

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
        print data_sets
        print ("Metric id: {}".format(metric_id))

if __name__ == "__main_rdma__":

    internal_chart_names = OrderedDict([("ib_write_latency_size_1b", 1), ("ib_write_latency_size_128b", 128),
                                        ("ib_write_latency_size_256b", 256), ("ib_write_latency_size_512b", 512),
                                        ("ib_write_latency_size_1024b", 1024), ("ib_write_latency_size_4096b", 4096)])

    model_name = "AlibabaRdmaPerformance"
    description = "TBD"
    owner_info = "Manu K S  (manu.ks@fungible.com)"
    source = "https://github.com/fungible-inc/Integration/blob/93cbceb27e5be0dfb3b79325c813d36789c5fe3d/fun_test" \
             "/scripts/networking/funcp/rdma_write_perf.py"
    positive = False
    y1_axis_title = PerfUnit.UNIT_USECS
    platform = FunPlatform.F1

    for internal_chart_name in internal_chart_names:
        size = internal_chart_names[internal_chart_name]
        one_data_set = {}
        data_sets = []

        chart_name = "IB write latency, size {}B".format(size)
        inputs = {
            "input_size_latency": size,
            "input_platform": platform,
            "input_operation": "write",
            "input_size_bandwidth": -1
        }
        output_names = OrderedDict([("output_write_min_latency", "min"), ("output_write_max_latency", "max"),
                                    ("output_write_avg_latency", "avg"), ("output_write_99_latency", "99%"),
                                    ("output_write_99_99_latency", "99.99%")])
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

        print ("Data sets: {}".format(data_sets))
        print ("Metric id: {}".format(metric_id))

    # Charts for RDMA bandwidth

    internal_chart_name = "rdma_ib_write_bw"
    model_name = "AlibabaRdmaPerformance"
    description = "TBD"
    owner_info = "Manu K S  (manu.ks@fungible.com)"
    source = "https://github.com/fungible-inc/Integration/blob/93cbceb27e5be0dfb3b79325c813d36789c5fe3d/fun_test/" \
             "scripts/networking/funcp/rdma_write_perf.py"
    positive = True
    y1_axis_title = PerfUnit.UNIT_GBITS_PER_SEC
    platform = FunPlatform.F1
    chart_name = "IB write BW"

    one_data_set = {}
    data_sets = []
    output_name = "output_write_bandwidth"
    bw_size_list = [1, 128, 256, 512, 1024, 4096]

    for bw_size in bw_size_list:
        one_data_set = {}
        inputs = {
            "input_size_bandwidth": bw_size,
            "input_platform": platform,
            "input_operation": "write",
            "input_size_latency": -1,
        }

        output = {
            "name": output_name,
            "unit": PerfUnit.UNIT_GBITS_PER_SEC,
            "min": 0,
            "max": -1,
            "expected": -1,
            "reference": -1
        }

        one_data_set["name"] = bw_size
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

    print ("Data sets: {}".format(data_sets))
    print ("Metric id: {}".format(metric_id))

    # Chart for message rate

    internal_chart_name = "rdma_ib_msg_rate"
    model_name = "AlibabaRdmaPerformance"
    description = "TBD"
    owner_info = "Manu K S  (manu.ks@fungible.com)"
    source = "https://github.com/fungible-inc/Integration/blob/93cbceb27e5be0dfb3b79325c813d36789c5fe3d/fun_test/" \
             "scripts/networking/funcp/rdma_write_perf.py"
    positive = True
    y1_axis_title = PerfUnit.UNIT_MPPS
    platform = FunPlatform.F1
    chart_name = "IB write message rate"

    one_data_set = {}
    data_sets = []
    output_name = "output_write_msg_rate"
    bw_size_list = [1, 128, 256, 512, 1024, 4096]
    for bw_size in bw_size_list:
        one_data_set = {}
        inputs = {
            "input_size_bandwidth": bw_size,
            "input_platform": platform,
            "input_operation": "write",
        }
        output = {
            "name": output_name,
            "unit": PerfUnit.UNIT_MPPS,
            "min": 0,
            "max": -1,
            "expected": -1,
            "reference": -1
        }
        one_data_set["name"] = bw_size
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

    print ("Data sets: {}".format(data_sets))
    print ("Metric id: {}".format(metric_id))

if __name__ == "__main_bmv_local_storage__":
    internal_iops_chart_names = ["bmv_storage_local_ssd_random_read_iops", "bmv_storage_local_ssd_random_write_iops"]
    num_threads = [1, 4, 16, 64, 256]
    for internal_chart_name in internal_iops_chart_names:
        if "random_read" in internal_chart_name:
            test = "randread"
            output_name = "output_read_iops"
        else:
            test = "randwrite"
            output_name = "output_write_iops"
        chart_name = "IOPS"
        positive = True
        model_name = "AlibabaPerformance"
        data_sets = []
        for thread in num_threads:
            one_data_set = {}
            one_data_set["name"] = str(thread)
            one_data_set["inputs"] = {"input_test": test, "input_num_threads": thread, "input_platform":
                FunPlatform.F1, "input_io_depth": 1}
            one_data_set["output"] = {"name": output_name, "min": 0, "max": -1, "expected": -1, "reference": -1,
                                      "unit": PerfUnit.UNIT_OPS}
            data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Radhika Naik (radhika.naik@fungible.com)",
                    source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/POCs/Alibaba/raw_vol_pcie_perf.py",
                    positive=positive,
                    y1_axis_title=PerfUnit.UNIT_OPS,
                    visualization_unit=PerfUnit.UNIT_OPS,
                    metric_model_name=model_name,
                    platform=FunPlatform.F1,
                    work_in_progress=False).save()
    print "added iops charts"
    internal_latency_chart_names = ["bmv_storage_local_ssd_random_read_qd1_latency",
                                    "bmv_storage_local_ssd_random_read_qd4_latency",
                                    "bmv_storage_local_ssd_random_read_qd16_latency",
                                    "bmv_storage_local_ssd_random_read_qd64_latency",
                                    "bmv_storage_local_ssd_random_read_qd256_latency",
                                    "bmv_storage_local_ssd_random_write_qd1_latency",
                                    "bmv_storage_local_ssd_random_write_qd4_latency",
                                    "bmv_storage_local_ssd_random_write_qd16_latency",
                                    "bmv_storage_local_ssd_random_write_qd64_latency",
                                    "bmv_storage_local_ssd_random_write_qd256_latency"]
    for internal_chart_name in internal_latency_chart_names:
        if "random_read" in internal_chart_name:
            test = "randread"
            output_names = ["output_read_avg_latency", "output_read_99_latency", "output_read_99_99_latency"]
        else:
            test = "randwrite"
            output_names = ["output_write_avg_latency", "output_write_99_latency", "output_write_99_99_latency"]
        chart_name = "Latency"
        positive = False
        model_name = "AlibabaPerformance"
        if "qd256" in internal_chart_name:
            thread = 256
        elif "qd64" in internal_chart_name:
            thread = 64
        elif "qd16" in internal_chart_name:
            thread = 16
        elif "qd4" in internal_chart_name:
            thread = 4
        else:
            thread = 1
        data_sets = []
        for output_name in output_names:
            if "avg" in output_name:
                name = "avg"
            elif "99_99" in output_name:
                name = "99.99%"
            else:
                name = "99%"
            one_data_set = {}
            one_data_set["name"] = name
            one_data_set["inputs"] = {"input_test": test, "input_num_threads": thread, "input_platform":
                FunPlatform.F1, "input_io_depth": 1}
            one_data_set["output"] = {"name": output_name, "min": 0, "max": -1, "expected": -1, "reference": -1,
                                      "unit": PerfUnit.UNIT_USECS}
            data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Radhika Naik (radhika.naik@fungible.com)",
                    source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/POCs/Alibaba/raw_vol_pcie_perf.py",
                    positive=positive,
                    y1_axis_title=PerfUnit.UNIT_USECS,
                    visualization_unit=PerfUnit.UNIT_USECS,
                    metric_model_name=model_name,
                    platform=FunPlatform.F1,
                    work_in_progress=False).save()
    print "added latency charts"

if __name__ == "__main_bmv_datasets__":
    internal_iops_chart_names = ["bmv_storage_local_ssd_random_read_iops", "bmv_storage_local_ssd_random_write_iops"]
    num_threads = [1, 16, 32, 64, 128]
    for internal_chart_name in internal_iops_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        if "random_read" in internal_chart_name:
            test = "randread"
            output_name = "output_read_iops"
        else:
            test = "randwrite"
            output_name = "output_write_iops"
        data_sets = []
        for thread in num_threads:
            one_data_set = {}
            one_data_set["name"] = str(thread)
            one_data_set["inputs"] = {"input_test": test, "input_num_threads": thread, "input_platform":
                FunPlatform.F1, "input_io_depth": 1}
            one_data_set["output"] = {"name": output_name, "min": 0, "max": -1, "expected": -1, "reference": -1,
                                      "unit": PerfUnit.UNIT_OPS}
            data_sets.append(one_data_set)
        chart.data_sets = json.dumps(data_sets)
        chart.save()
    internal_latency_chart_names = [
        "bmv_storage_local_ssd_random_read_qd4_latency",
        "bmv_storage_local_ssd_random_read_qd256_latency",
        "bmv_storage_local_ssd_random_write_qd4_latency",
        "bmv_storage_local_ssd_random_write_qd256_latency"]
    for internal_chart_name in internal_latency_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        if "qd4" in internal_chart_name:
            internal_chart_name = internal_chart_name.replace("qd4", "qd32")
            thread = 32
        else:
            internal_chart_name = internal_chart_name.replace("qd256", "qd128")
            thread = 128
        chart.internal_chart_name = internal_chart_name
        data_sets = json.loads(chart.data_sets)
        for data_set in data_sets:
            data_set["inputs"]["input_num_threads"] = thread
            data_set["output"]["reference"] = -1
        chart.data_sets = json.dumps(data_sets)
        chart.save()
    print "changed datasets and charts to show different qdepths"

if __name__ == "__main_underlay_overlay__":
    internal_chart_names = ["HU_HU_FCP_8TCP_1H_offloads_enabled_output_throughput",
                            "HU_HU_FCP_8TCP_1H_offloads_enabled_output_pps",
                            "HU_HU_FCP_8TCP_1H_offloads_enabled_output_latency",
                            "HU_HU_FCP_8TCP_1H_offloads_enabled_output_latency_under_load",
                            "HU_HU_FCP_8TCP_2H_offloads_enabled_output_throughput",
                            "HU_HU_FCP_8TCP_2H_offloads_enabled_output_pps",
                            "HU_HU_FCP_8TCP_2H_offloads_enabled_output_latency",
                            "HU_HU_FCP_8TCP_2H_offloads_enabled_output_latency_under_load",
                            "HU_HU_FCP_1TCP_1H_offloads_enabled_output_throughput",
                            "HU_HU_FCP_1TCP_1H_offloads_enabled_output_pps",
                            "HU_HU_FCP_1TCP_1H_offloads_enabled_output_latency", "HU_HU_FCP_1TCP_1H_offloads_enabled_output_latency_under_load"]
    for internal_chart_name in internal_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        internal_chart_name = internal_chart_name.replace("FCP", "NFCP_2f1")
        data_sets = json.loads(chart.data_sets)
        for data_set in data_sets:
            data_set["inputs"]["input_flow_type"] = data_set["inputs"]["input_flow_type"].replace("FCP", "NFCP_2F1")
            data_set["output"]["reference"] = -1
            data_set["output"]["expected"] = -1
        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name="temp",
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
                    metric_model_name=chart.metric_model_name,
                    base_line_date=chart.base_line_date,
                    work_in_progress=False,
                    platform=FunPlatform.F1).save()
    print "added Host to host 2f1s"
    model_names = ["HuThroughputPerformance", "HuLatencyPerformance", "HuLatencyUnderLoadPerformance"]
    for model_name in model_names:
        charts = MetricChart.objects.filter(metric_model_name=model_name)
        for chart in charts:
            internal_chart_name = chart.internal_chart_name + "_underlay"
            data_sets = json.loads(chart.data_sets)
            for data_set in data_sets:
                data_set["inputs"]["input_flow_type"] = data_set["inputs"]["input_flow_type"] + "_UL_VM"
                data_set["output"]["reference"] = -1
                data_set["output"]["expected"] = -1
            metric_id = LastMetricId.get_next_id()
            MetricChart(chart_name="temp",
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
                        metric_model_name=chart.metric_model_name,
                        base_line_date=chart.base_line_date,
                        work_in_progress=False,
                        platform=FunPlatform.F1).save()
    print "added underlay charts"
    internal_chart_names = ["HU_HU_FCP_8TCP_1H_offloads_enabled_output_throughput_underlay",
                            "HU_HU_FCP_8TCP_1H_offloads_enabled_output_pps_underlay",
                            "HU_HU_FCP_8TCP_1H_offloads_enabled_output_latency_underlay",
                            "HU_HU_FCP_8TCP_1H_offloads_enabled_output_latency_under_load_underlay",
                            "HU_HU_FCP_8TCP_2H_offloads_enabled_output_throughput_underlay",
                            "HU_HU_FCP_8TCP_2H_offloads_enabled_output_pps_underlay",
                            "HU_HU_FCP_8TCP_2H_offloads_enabled_output_latency_underlay",
                            "HU_HU_FCP_8TCP_2H_offloads_enabled_output_latency_under_load_underlay",
                            "HU_HU_FCP_1TCP_1H_offloads_enabled_output_throughput_underlay",
                            "HU_HU_FCP_1TCP_1H_offloads_enabled_output_pps_underlay",
                            "HU_HU_FCP_1TCP_1H_offloads_enabled_output_latency_underlay",
                            "HU_HU_FCP_1TCP_1H_offloads_enabled_output_latency_under_load_underlay",
                            "HU_HU_NFCP_2f1_8TCP_1H_offloads_enabled_output_throughput_underlay",
                            "HU_HU_NFCP_2f1_8TCP_1H_offloads_enabled_output_pps_underlay",
                            "HU_HU_NFCP_2f1_8TCP_1H_offloads_enabled_output_latency_underlay",
                            "HU_HU_NFCP_2f1_8TCP_1H_offloads_enabled_output_latency_under_load_underlay",
                            "HU_HU_NFCP_2f1_8TCP_2H_offloads_enabled_output_throughput_underlay",
                            "HU_HU_NFCP_2f1_8TCP_2H_offloads_enabled_output_pps_underlay",
                            "HU_HU_NFCP_2f1_8TCP_2H_offloads_enabled_output_latency_underlay",
                            "HU_HU_NFCP_2f1_8TCP_2H_offloads_enabled_output_latency_under_load_underlay",
                            "HU_HU_NFCP_2f1_1TCP_1H_offloads_enabled_output_throughput_underlay",
                            "HU_HU_NFCP_2f1_1TCP_1H_offloads_enabled_output_pps_underlay",
                            "HU_HU_NFCP_2f1_1TCP_1H_offloads_enabled_output_latency_underlay",
                            "HU_HU_NFCP_2f1_1TCP_1H_offloads_enabled_output_latency_under_load_underlay"]
    for internal_chart_name in internal_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        internal_chart_name = internal_chart_name.replace("underlay", "overlay")
        if "NFCP" in internal_chart_name:
            flow_type = "HU_HU_NFCP_OL_VM"
        else:
            flow_type = "HU_HU_FCP_OL_VM"
        data_sets = json.loads(chart.data_sets)
        for data_set in data_sets:
            data_set["inputs"]["input_flow_type"] = flow_type
            data_set["output"]["reference"] = -1
            data_set["output"]["expected"] = -1
        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name="temp",
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
                    metric_model_name=chart.metric_model_name,
                    base_line_date=chart.base_line_date,
                    work_in_progress=False,
                    platform=FunPlatform.F1).save()
    print "added overlay charts"

if __name__ == "__main_l4_firewall__":
    model_name = "TeraMarkJuniperNetworkingPerformance"
    chart_name = "temp"
    internal_throughput_chart_names = ["l4_firewall_flow_4m_flows_throughput", "l4_firewall_flow_4m_flows_pps",
                            "l4_firewall_flow_128m_flows_throughput", "l4_firewall_flow_128m_flows_pps"]
    internal_latency_chart_names = ["l4_firewall_flow_4m_flows_latency_full_load",
                                    "l4_firewall_flow_4m_flows_latency_half_load",
                                    "l4_firewall_flow_128m_flows_latency_full_load", "l4_firewall_flow_128m_flows_latency_half_load"]
    flow_type = "NU_LE_VP_NU_L4_FW"
    offloads = False
    base_line_date = datetime(year=2019, month=7, day=15, minute=0, hour=0, second=0)
    for internal_chart_name in internal_throughput_chart_names:
        if "throughput" in internal_chart_name:
            y1_axis_title = PerfUnit.UNIT_GBITS_PER_SEC
            visualization_unit = PerfUnit.UNIT_GBITS_PER_SEC
            data_set_unit = PerfUnit.UNIT_MBITS_PER_SEC
            output_name = "output_throughput"
        else:
            y1_axis_title = PerfUnit.UNIT_MPPS
            visualization_unit = PerfUnit.UNIT_MPPS
            data_set_unit = PerfUnit.UNIT_PPS
            output_name = "output_pps"
        if "128m" in internal_chart_name:
            num_flows = 128000000
            frame_sizes = [64]
        else:
            num_flows = 4000000
            frame_sizes = [64, 1500, 362.94]
        half_load_latency = False
        data_sets = []
        for frame_size in frame_sizes:
            if frame_size == 362.94:
                name = "IMIX"
            else:
                name = str(frame_size) + 'B'
            one_data_set = {}
            one_data_set["inputs"] = {}
            one_data_set["name"] = name
            one_data_set["inputs"] = {"input_platform": FunPlatform.F1, "input_flow_type": flow_type,
                                      "input_frame_size": frame_size, "input_offloads": offloads, "input_num_flows":
                                          num_flows, "input_protocol": "UDP", "input_half_load_latency": half_load_latency}
            one_data_set["output"] = {"name": output_name, "reference": -1, "min": 0, "max": -1, "expected": -1,
                                      "unit": data_set_unit}
            data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name="temp",
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Amit Surana (amit.surana@fungible.com)",
                    source="",
                    positive=True,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=visualization_unit,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False,
                    platform=FunPlatform.F1).save()
    print "added throughput and pps charts for l4 firewall"
    for internal_chart_name in internal_latency_chart_names:
        y1_axis_title = PerfUnit.UNIT_USECS
        visualization_unit = PerfUnit.UNIT_USECS
        data_set_unit = PerfUnit.UNIT_USECS
        if "full_load" in internal_chart_name:
            half_load_latency = False
        else:
            half_load_latency = True
        if "128m" in internal_chart_name:
            num_flows = 128000000
            frame_sizes = [64]
        else:
            num_flows = 4000000
            frame_sizes = [64, 1500, 362.94]
        positive = False
        latency_names = ["min", "avg", "max"]
        data_sets = []
        for frame_size in frame_sizes:
            for latency_name in latency_names:
                if frame_size == 362.94:
                    name = "IMIX" + "-" + latency_name
                else:
                    name = str(frame_size) + 'B' + "-" + latency_name
                output_name = "output_latency_" + latency_name
                one_data_set = {}
                one_data_set["name"] = name
                one_data_set["inputs"] = {}
                one_data_set["inputs"] = {"input_platform": FunPlatform.F1, "input_flow_type": flow_type,
                                          "input_frame_size": frame_size, "input_offloads": offloads, "input_num_flows":
                                              num_flows, "input_protocol": "UDP",
                                          "input_half_load_latency": half_load_latency}
                one_data_set["output"] = {"name": output_name, "reference": -1, "min": 0, "max": -1, "expected": -1,
                                          "unit": data_set_unit}
                data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name="temp",
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Amit Surana (amit.surana@fungible.com)",
                    source="",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=visualization_unit,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False,
                    platform=FunPlatform.F1).save()
    print "added latency charts for juniper l4 firewall"

if __name__ == "__main_companion2__":
    charts = ["iops", "latency"]
    xaxis_title = "log2(qDepth)"
    chart_type = ChartType.REGULAR
    fun_chart_type = FunChartType.LINE_CHART
    for chart in charts:
        if "iops" in chart:
            names = ["read(1 vol)", "write(1 vol)"]
            chart_name = "inspur_8111_8k_rand_rw_2f1"
            yaxis_title = "log10(" + PerfUnit.UNIT_OPS + ")"
            title = "qdepth vs IOPS (1 vol)"
        else:
            names = ["read-avg(1 vol)", "write-avg(1 vol)"]
            chart_name = "inspur_8116_8k_rand_rw_2f1"
            yaxis_title = "log10(" + PerfUnit.UNIT_USECS + ")"
            title = "qdepth vs latency (1 vol)"
        data_sets = []
        for name in names:
            if "iops" in chart:
                if "read" in name:
                    output_name = "output_read_iops"
                else:
                    output_name = "output_write_iops"
            else:
                if "read" in name:
                    output_name = "output_read_avg_latency"
                else:
                    output_name = "output_write_avg_latency"
            one_data_set = {}
            one_data_set["name"] = name
            one_data_set["filters"] = {}
            one_data_set["filters"] = [{"name": 1, "model_name": "BltVolumePerformance", "filter": {
                "input_fio_job_name": "inspur_8k_random_read_write_iodepth_1_f1_2_vol_1",
                "input_platform": FunPlatform.F1}},
                                       {"name": 8, "model_name": "BltVolumePerformance", "filter": {
                                           "input_fio_job_name": "inspur_8k_random_read_write_iodepth_8_f1_2_vol_1",
                                           "input_platform": FunPlatform.F1}},
                                       {"name": 16, "model_name": "BltVolumePerformance", "filter": {
                                           "input_fio_job_name": "inspur_8k_random_read_write_iodepth_16_f1_2_vol_1",
                                           "input_platform": FunPlatform.F1}},
                                       {"name": 32, "model_name": "BltVolumePerformance", "filter": {
                                           "input_fio_job_name": "inspur_8k_random_read_write_iodepth_32_f1_2_vol_1",
                                           "input_platform": FunPlatform.F1}},
                                       {"name": 64, "model_name": "BltVolumePerformance", "filter": {
                                           "input_fio_job_name": "inspur_8k_random_read_write_iodepth_64_f1_2_vol_1",
                                           "input_platform": FunPlatform.F1}},
                                       {"name": 128, "model_name": "BltVolumePerformance", "filter": {
                                           "input_fio_job_name": "inspur_8k_random_read_write_iodepth_128_f1_2_vol_1",
                                           "input_platform": FunPlatform.F1}},
                                       {"name": 256, "model_name": "BltVolumePerformance", "filter": {
                                           "input_fio_job_name": "inspur_8k_random_read_write_iodepth_256_f1_2_vol_1",
                                           "input_platform": FunPlatform.F1}}]
            one_data_set["output_field"] = output_name
            data_sets.append(one_data_set)
        print json.dumps(data_sets)
        chart_id = LastChartId.get_next_id()
        Chart(chart_id=chart_id, title=title, x_axis_title=xaxis_title, y_axis_title=yaxis_title,
              chart_type=chart_type, fun_chart_type=fun_chart_type, series_filters=data_sets, x_scale="log2",
              y_scale="log10").save()
        chart = MetricChart.objects.get(internal_chart_name=chart_name)
        if chart:
            chart.companion_charts = [chart_id]
            chart.save()
        print "added chart id: {}", format(chart_id)
    print "added companion charts"

if __name__ == "__main_associated_suites__":
    entries = JenkinsJobIdMap.objects.all()
    for entry in entries:
        if len(entry.associated_suites) > 0:
            print entry.associated_suites
            entry.associated_suites = list(set(entry.associated_suites))
            entry.save()

if __name__ == "__main_voltest_blt__":

    # Latency charts for various instances
    internal_chart_names = OrderedDict([('voltest_blt_1_instance_latency', 1), ('voltest_blt_8_instance_latency', 8),
                                        ('voltest_blt_12_instance_latency', 12)])

    owner_info = "Sunil Subramanya (sunil.subramanya@fungible.com)"
    source = "https://github.com/fungible-inc/FunOS/blob/5d979f094bc34c0425f8d27d0e5bcaeb4aa80954/apps/md_table_test.c"
    positive = False
    y1_axis_title = PerfUnit.UNIT_NSECS
    platform = FunPlatform.F1

    for internal_chart_name in internal_chart_names:
        blt_instance = internal_chart_names[internal_chart_name]
        model_name = 'VoltestBlt{}Performance'.format(blt_instance)
        description = "TBD"
        chart_name = "voltest blt {} instance latency".format(blt_instance)
        one_data_set = {}
        data_sets = []

        inputs = {
            "input_platform": platform,
            "input_blt_instance": blt_instance
        }
        output_names = OrderedDict([('output_min_latency', 'min'), ('output_max_latency', 'max'),
                                    ('output_avg_latency', 'avg')])
        for output_name in output_names:
            output = {
                "name": output_name,
                "unit": PerfUnit.UNIT_NSECS,
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
        print ("Data sets: {}".format(data_sets))
        print ("Metric id: {}".format(metric_id))

    # IOPS and Bandwidht charts for various instances

    internal_chart_names = OrderedDict([('voltest_blt_1_instance_iops', 1), ('voltest_blt_8_instance_iops', 8),
                                        ('voltest_blt_12_instance_iops', 12), ('voltest_blt_1_instance_bandwidth', 1),
                                        ('voltest_blt_8_instance_bandwidth', 8),
                                        ('voltest_blt_12_instance_bandwidth', 12)])

    owner_info = "Sunil Subramanya (sunil.subramanya@fungible.com)"
    source = "https://github.com/fungible-inc/FunOS/blob/5d979f094bc34c0425f8d27d0e5bcaeb4aa80954/apps/md_table_test.c"
    positive = True
    platform = FunPlatform.F1

    for internal_chart_name in internal_chart_names:
        blt_instance = internal_chart_names[internal_chart_name]
        model_name = 'VoltestBlt{}Performance'.format(blt_instance)
        one_data_set = {}
        data_sets = []

        if "iops" in internal_chart_name:
            chart_name = "voltest blt {} instance(s) IOPS".format(blt_instance)
            output_name = "output_iops"
            y1_axis_title = PerfUnit.UNIT_OPS
            name = "iops"
            description = "TBD"
        elif "bandwidth" in internal_chart_name:
            chart_name = "voltest blt {} instance(s) Bandwidth".format(blt_instance)
            output_name = "output_bandwidth"
            y1_axis_title = PerfUnit.UNIT_MBITS_PER_SEC
            name = "bandwidth"
            description = "TBD"

        inputs = {
            "input_platform": platform,
            "input_blt_instance": blt_instance
        }

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

if __name__ == "__main_ipsec_new__":
    internal_chart_names = ["juniper_new_ipsec_enc_single_tunnel_output_throughput",
                            "juniper_new_ipsec_enc_single_tunnel_output_pps",
                            "juniper_new_ipsec_enc_multi_tunnel_output_throughput",
                            "juniper_new_ipsec_enc_multi_tunnel_output_pps",
                            "juniper_new_ipsec_dec_single_tunnel_output_throughput",
                            "juniper_new_ipsec_dec_single_tunnel_output_pps",
                            "juniper_new_ipsec_dec_multi_tunnel_output_throughput",
                            "juniper_new_ipsec_dec_multi_tunnel_output_pps"]
    chart_name = "temp"
    positive = True
    model_name = "TeraMarkJuniperNetworkingPerformance"
    base_line_date = datetime(year=2019, month=7, day=15, minute=0, hour=0, second=0)
    frame_sizes = [64, 362.94]
    for internal_chart_name in internal_chart_names:
        if "throughput" in internal_chart_name:
            y1_axis_title = PerfUnit.UNIT_GBITS_PER_SEC
            visualization_unit = PerfUnit.UNIT_GBITS_PER_SEC
            output_name = "output_throughput"
            data_set_unit = PerfUnit.UNIT_MBITS_PER_SEC
        else:
            y1_axis_title = PerfUnit.UNIT_MPPS
            visualization_unit = PerfUnit.UNIT_MPPS
            output_name = "output_pps"
            data_set_unit = PerfUnit.UNIT_PPS
        data_sets = []
        if "enc_single_tunnel" in internal_chart_name:
            flow_type = "IPSEC_ENCRYPT_SINGLE_TUNNEL"
        elif "enc_multi_tunnel" in internal_chart_name:
            flow_type = "IPSEC_ENCRYPT_MULTI_TUNNEL"
        elif "dec_single_tunnel" in internal_chart_name:
            flow_type = "IPSEC_DECRYPT_SINGLE_TUNNEL"
        else:
            flow_type = "IPSEC_DECRYPT_MULTI_TUNNEL"
        for frame_size in frame_sizes:
            name = str(frame_size) + 'B'
            one_data_set = {}
            one_data_set["name"] = name
            one_data_set["inputs"] = {"input_platform": FunPlatform.F1, "input_offloads": False,
                                      "input_half_load_latency": False, "input_flow_type": flow_type,
                                      "input_frame_size": frame_size, "input_protocol": "UDP"}
            one_data_set["output"] = {"name": output_name, "min": 0, "max": -1, "expected": -1, "reference": -1,
                                      "unit": data_set_unit}
            data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name="temp",
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Amit Surana (amit.surana@fungible.com), Onkar Sarmalkar (onkar.sarmalkar@fungible.com)",
                    source="",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=visualization_unit,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False,
                    platform=FunPlatform.F1).save()
    print "added charts for ipsec encryption and decryption"

if __name__ == "__main_inspur_6f1s__":
    internal_chart_names = ["inspur_8111_8k_rand_rw_2f1", "inspur_8116_8k_rand_rw_2f1",
                            "inspur_rand_read_write_qd1_2f1_8k_block_output_iops",
                            "inspur_rand_read_write_qd8_2f1_8k_block_output_iops",
                            "inspur_rand_read_write_qd16_2f1_8k_block_output_iops",
                            "inspur_rand_read_write_qd32_2f1_8k_block_output_iops",
                            "inspur_rand_read_write_qd64_2f1_8k_block_output_iops",
                            "inspur_rand_read_write_qd128_2f1_8k_block_output_iops",
                            "inspur_rand_read_write_qd256_2f1_8k_block_output_iops",
                            "inspur_rand_read_write_qd1_2f1_8k_block_output_latency",
                            "inspur_rand_read_write_qd8_2f1_8k_block_output_latency",
                            "inspur_rand_read_write_qd16_2f1_8k_block_output_latency",
                            "inspur_rand_read_write_qd32_2f1_8k_block_output_latency",
                            "inspur_rand_read_write_qd64_2f1_8k_block_output_latency",
                            "inspur_rand_read_write_qd128_2f1_8k_block_output_latency",
                            "inspur_rand_read_write_qd256_2f1_8k_block_output_latency"]
    for internal_chart_name in internal_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        if chart:
            internal_chart_name = internal_chart_name.replace('2f1', '6f1')
            if "qd256" in internal_chart_name:
                internal_chart_name = internal_chart_name.replace('qd256','qd96')
            chart.internal_chart_name = internal_chart_name
            chart.save()
            if chart.leaf:
                if "qd32" in internal_chart_name:
                    fio_job_name = "inspur_8k_random_read_write_iodepth_32_f1_6_vol_1"
                elif "qd64" in internal_chart_name:
                    fio_job_name = "inspur_8k_random_read_write_iodepth_64_f1_6_vol_1"
                elif "qd96" in internal_chart_name:
                    fio_job_name = "inspur_8k_random_read_write_iodepth_96_f1_6_vol_1"
                elif "qd128" in internal_chart_name:
                    fio_job_name = "inspur_8k_random_read_write_iodepth_128_f1_6_vol_1"
                else:
                    fio_job_name = None
                if fio_job_name:
                    data_sets1 = json.loads(chart.data_sets)
                    for data_set in data_sets1:
                        if "read" in data_set["name"]:
                            data_set["name"] = "read(2 F1s, 1 vol)"
                        else:
                            data_set["name"] = "write(2 F1s, 1 vol)"
                    chart.data_sets = json.dumps(data_sets1)
                    chart.save()
                    data_sets = json.loads(chart.data_sets)
                    for data_set in data_sets1:
                        one_data_set = data_set
                        if "read" in one_data_set["name"]:
                            one_data_set["name"] = "read(6 F1s, 1 vol)"
                        else:
                            one_data_set["name"] = "write(6 F1s, 1 vol)"
                        one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
                        one_data_set["output"]["reference"] = -1
                        one_data_set["output"]["expected"] = -1
                        data_sets.append(one_data_set)
                    chart.data_sets = json.dumps(data_sets)
                    chart.save()
    print "added new datasets for 6 F1"

if __name__ == "__main_l4_IMIX__":
    internal_chart_names = ["l4_firewall_flow_128m_flows_throughput", "l4_firewall_flow_128m_flows_pps",
                            "l4_firewall_flow_128m_flows_latency_full_load", "l4_firewall_flow_128m_flows_latency_half_load"]
    for internal_chart_name in internal_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        if chart:
            data_sets1 = json.loads(chart.data_sets)
            data_sets = json.loads(chart.data_sets)
            for data_set in data_sets1:
                data_set["name"] = data_set["name"].replace("64B", "IMIX")
                data_set["inputs"]["input_frame_size"] = 362.94
                data_set["output"]["reference"] = -1
                data_set["output"]["expected"] = -1
                data_sets.append(data_set)
            chart.data_sets = json.dumps(data_sets)
            chart.save()
    print "added l4 firewall datasets for IMIX 128M flows"

if __name__ == "__main__":
    internal_chart_names = ["bmv_storage_local_ssd_random_read_iops", "bmv_storage_local_ssd_random_write_iops",
                            "bmv_storage_local_ssd_random_read_qd128_latency", "bmv_storage_local_ssd_random_write_qd128_latency"]
    for internal_chart_name in internal_chart_names:
        if "latency" in internal_chart_name:
            chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
            internal_chart_name = internal_chart_name.replace("qd128", "qd256")
            data_sets = json.loads(chart.data_sets)
            for data_set in data_sets:
                data_set["inputs"]["input_num_threads"] = 256
                data_set["output"]["reference"] = -1
                data_set["output"]["expected"] = -1
            metric_id = LastMetricId.get_next_id()
            MetricChart(chart_name="temp",
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
                        metric_model_name=chart.metric_model_name,
                        base_line_date=chart.base_line_date,
                        work_in_progress=False,
                        platform=FunPlatform.F1).save()
        else:
            chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
            if "random_read" in internal_chart_name:
                output_name = "output_read_iops"
            else:
                output_name = "output_write_iops"
            data_sets = json.loads(chart.data_sets)
            one_data_set = {}
            one_data_set["name"] = "256"
            one_data_set["inputs"] = {"input_test": "randread", "input_num_threads": 256, "input_io_depth": 1,
                                      "input_platform": "F1"}
            one_data_set["output"] = {"name": output_name, "reference": -1, "min": 0, "max": -1,
                                      "expected": -1, "unit": "ops"}
            data_sets.append(one_data_set)
            chart.data_sets = json.dumps(data_sets)
            chart.save()
    print "added 256 iodepth to local ssd"

