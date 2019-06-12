from web.fun_test.maintenance_old import *
from lib.system.fun_test import *
from datetime import datetime
from web.fun_test.models_helper import add_jenkins_job_id_map
from dateutil import parser
from django.utils import timezone
from fun_global import PerfUnit


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

if __name__ == "__main__":
    internal_chart_names = ["read_4kb1vol12ssd_durable_volume_ec_output_iops", "read_4kb1vol12ssd_durable_volume_ec_4_output_latency", "rand_read_4kb1vol12ssd_durable_volume_ec_4_output_latency", "rand_read_4kb1vol12ssd_durable_volume_ec_output_iops"]
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