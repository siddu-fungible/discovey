from web.fun_test.maintenance_old import *
from lib.system.fun_test import *
from datetime import datetime
from web.fun_test.models_helper import add_jenkins_job_id_map
from dateutil import parser
from django.utils import timezone
from fun_global import PerfUnit
from fun_global import ChartType, FunChartType
from web.fun_test.metrics_models import *

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
        
if __name__=="__main__inspur_random_read_write_iodepth_vol":
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
                one_data_set['inputs']['input_fio_job_name'] =\
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

if __name__=="__main_container_data_sets__":
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
