from web.fun_test.maintenance_old import *
from lib.system.fun_test import *
from datetime import datetime
from web.fun_test.models_helper import add_jenkins_job_id_map
from dateutil import parser
from django.utils import timezone
from fun_global import PerfUnit

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
            
if __name__ == "__main__rand_qd_multi_host_nvmetcp_output_iops":
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

if __name__ == "__main__":
    metric_id_list = [795, 796, 797, 798]
    for metric_id in metric_id_list:
        chart = MetricChart.objects.get(metric_id=metric_id)
        chart.owner_info = "Sunil Vettukalppurathu (sunil.v@fungible.com)"
        print chart.chart_name
        data_sets_uni = chart.data_sets
        print data_sets_uni
        data_sets = json.loads(data_sets_uni)[0]
        print data_sets
        output_name = data_sets["output"]['name']
        data_sets['name'] = 'read_write'
        if 'iops' in output_name:
            data_sets["output"]['name'] = 'output_read_write_iops'
        else:
            data_sets['output']['name'] = 'output_read_write_bandwidth'

        print data_sets

        data_sets_json = json.dumps([data_sets])
        chart.data_sets = data_sets_json
        chart.save()
