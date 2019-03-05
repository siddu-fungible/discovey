import os
import django
import json
import random, pytz
import re
from fun_global import get_current_time
from datetime import datetime
from web.web_global import PRIMARY_SETTINGS_FILE
from django.apps import apps
from fun_global import get_localized_time
from web.fun_test.settings import COMMON_WEB_LOGGER_NAME
import logging
from fun_settings import MAIN_WEB_APP

logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)
from datetime import datetime, timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", PRIMARY_SETTINGS_FILE)
django.setup()
from web.fun_test.metrics_models import Performance1, PerformanceIkv, PerformanceBlt, VolumePerformance
from web.fun_test.metrics_models import AllocSpeedPerformance
from web.fun_test.site_state import *
from web.fun_test.metrics_models import MetricChart, ShaxPerformance
from web.fun_test.metrics_models import WuLatencyUngated, WuLatencyAllocStack, AllocSpeedPerformance, \
    NuTransitPerformance
from web.fun_test.metrics_models import WuDispatchTestPerformance, WuSendSpeedTestPerformance, HuRawVolumePerformance
from web.fun_test.models import JenkinsJobIdMap
from web.fun_test.metrics_models import VoltestPerformance
from web.fun_test.set_base_line import SetBaseLine

from web.fun_test.analytics_models_helper import MetricChartHelper
from web.fun_test.metrics_models import MetricChartStatus, TeraMarkJpegPerformance
from web.fun_test.metrics_models import LastMetricId, MileStoneMarkers


class MetricHelper(object):
    def __init__(self, model):
        self.model = model

    def delete(self, key):
        entries = self.model.objects.filter(key=key)
        entries.delete()
        '''
        for entry in entries:
            entry.delete()
            entry.save()
        '''

    def clear(self):
        self.model.objects.all().delete()


"""
if __name__ == "__main__":
    h = MetricHelper(AllocSpeedPerformance)
    h.delete(key="2202")
    h.delete(key="2184")
    h.delete(key="2194")

"""


def get_rounded_time(dt):
    rounded_d = datetime(year=dt.year, month=dt.month, day=dt.day, hour=23, minute=59, second=59)
    rounded_d = get_localized_time(rounded_d)
    return rounded_d


def software_date_to_datetime(software_date):
    m = re.search(r'(\d{4})(\d{2})(\d{2})', str(software_date))
    if m:
        year = int(m.group(1))
        month = int(m.group(2))
        day = int(m.group(3))
        s = "{}-{}-{} {}:{}".format(year, month, day, "00", "01")
        return datetime.strptime(s, "%Y-%m-%d %H:%M")


if __name__ == "__main33__":
    for model in [WuLatencyUngated, WuLatencyAllocStack, AllocSpeedPerformance]:
        entries = model.objects.all()
        for entry in entries:
            key = entry.key
            # print key
            entries = JenkinsJobIdMap.objects.filter(fun_sdk_branch="refs/tags/bld_" + key)
            if entries:
                j_entry = entries[0]
                dt = get_localized_time(software_date_to_datetime(j_entry.software_date))
                entry.input_date_time = dt
                print dt
                entry.save()

    jm_entries = JenkinsJobIdMap.objects.all()
    for jm_entry in jm_entries:
        # if jm_entry.completion_date == "":
        if jm_entry.software_date:
            dt = get_localized_time(software_date_to_datetime(jm_entry.software_date))
            jm_entry.completion_date = dt.strftime("%Y-%m-%d %H:%M")
            jm_entry.save()

if __name__ == "__main2__":
    for model in ["WuLatencyUngated", "WuLatencyAllocStack", "AllocSpeedPerformance", "BcopyFloodDmaPerformance",
                  "BcopyPerformance",
                  "EcVolPerformance", "EcPerformance"]:
        charts = MetricChartHelper.get_charts_by_model_name(metric_model_name=model)
        for chart in charts:
            chart.last_build_status = "FAILED"
            chart.save()

if __name__ == "__main2__":
    entries = ShaxPerformance.objects.all().delete()
    for entry in entries:
        entry.interpolation_allowed = True
        entry.save()

if __name__ == "__main4__":
    entries = ShaxPerformance.objects.all()
    for entry in entries:
        entry.interpolation_allowed = True
        entry.save()

if __name__ == "__main2__":
    entries = HuRawVolumePerformance.objects.all()
    for entry in entries:
        dt = entry.input_date_time
        dt = dt.replace(day=dt.day - 1)
        entry.input_date_time = dt
        entry.save()

if __name__ == "__main44__":
    chart_name = "LSV: Op Bandwidth"
    entries = MetricChart.objects.filter(chart_name=chart_name)
    for entry in entries:
        print entry
    newentry = entries[0]
    print newentry
    newentry.chart_name += "_01"
    newentry.metric_id = 10000
    newentry.pk = None
    newentry.save()

if __name__ == "__main55__":
    entries = MetricChartStatus.objects.filter(metric_id=108)
    # entries = MetricChartStatus.objects.all()

    for entry in entries:
        print entry

if __name__ == "__main2__":
    # clone charts
    chart_name = "Best time for 1 malloc/free (WU)"
    entry = MetricChart.objects.get(chart_name=chart_name)

    chart_id_range = range(10000, 10100)
    for i in chart_id_range:
        entry.metric_id = i
        entry.chart_name = "TestChart{}".format(i)
        entry.pk = None
        try:
            entry.save()
        except:
            pass

if __name__ == "__main66__":
    chart_name = "Nucleus"
    entry = MetricChart.objects.get(chart_name=chart_name)
    chart_id_range = range(10000, 10100)
    for i in chart_id_range:
        test_chart_name = "TestChart{}".format(i)
        test_chart = MetricChart.objects.get(chart_name=test_chart_name)
        entry.add_child(test_chart.metric_id)

if __name__ == "__main5__":
    from django.apps import apps

    for entry in site_state.metric_models.keys():
        print entry
'''
    try:
        entry = django.apps.apps.get_model(app_label='fun_test', model_name='FunMagentPerformanceTest')
        print entry
    except:
        logger.critical("No data found Model")
    #for model_name in apps.get_models():
        #print model_name.objects.filter()'''

if __name__ == "__main1__":
    today = get_current_time()
    from_date = datetime(year=2018, month=8, day=10, minute=0, hour=0, second=0)

    yesterday = today + timedelta(days=1)
    yesterday = get_rounded_time(yesterday)
    to_date = yesterday
    date_range = [from_date, to_date]
    chart_name = "BLK_LSV: Bandwidth"
    chart_name = "WU Latency: Alloc Stack"
    mcs_entries = MetricChartStatus.objects.filter(chart_name=chart_name, date_time__range=[from_date, to_date])
    # mcs_entries = MetricChartStatus.objects.filter(chart_name=chart_name)

    for mcs_entry in mcs_entries:
        print mcs_entry.score, mcs_entry.date_time

    mcs_entries = MetricChartStatus.objects.filter(chart_name=chart_name)

    for mcs_entry in mcs_entries:
        print mcs_entry.score, mcs_entry.date_time


def get_day_bounds(dt):
    d = get_rounded_time(dt)
    start = d.replace(hour=0, minute=0, second=0)
    end = d.replace(hour=23, minute=59, second=59)
    return start, end


def get_entries_for_day(model, day, data_set):
    bounds = get_day_bounds(day)
    d = {}
    d["input_date_time__range"] = bounds
    inputs = data_set["inputs"]
    for input_name, input_value in inputs.iteritems():
        if d == "input_date_time":
            continue
        d[input_name] = input_value
    result = model.objects.filter(**d)
    return result


def get_possible_values(model_name):
    metric_model = app_config.get_metric_models()[model_name]
    fields = metric_model._meta.get_fields()
    field_choices = {}
    for field in fields:
        choices = None
        if hasattr(field, "choices"):
            if field.column.startswith("input_") and (not field.column.startswith("input_date_time")):
                all_values = metric_model.objects.values(field.column).distinct()
                choices = []
                for index, value in enumerate(all_values):
                    choices.append(value[field.column])

                field_choices[field.column] = choices
    return field_choices


if __name__ == "__main2__":
    today = datetime.now()

    from_date = datetime(year=today.year, month=8, day=8, minute=0, hour=0, second=0)

    yesterday = today - timedelta(days=1)
    yesterday = get_rounded_time(yesterday)
    to_date = yesterday
    current_date = get_rounded_time(from_date)

    from_date = get_localized_time(datetime(year=2018, month=8, day=9, minute=0, hour=0, second=0))

    yesterday = today - timedelta(days=1)
    yesterday = get_rounded_time(yesterday)
    to_date = yesterday
    date_range = [from_date, to_date]
    chart_name = "BLK_LSV: Bandwidth"
    chart = MetricChart.objects.get(chart_name=chart_name)
    data_sets = chart.data_sets
    data_sets = json.loads(data_sets)

    for data_set in data_sets:
        while current_date <= to_date:
            entries = get_entries_for_day(model=VoltestPerformance, day=current_date, data_set=data_set)
            for entry in entries:
                print entry

            current_date = current_date + timedelta(days=1)

if __name__ == "__main250__":
    entries = JenkinsJobIdMap.objects.all()
    for entry in entries:
        if entry.completion_date:
            dt = get_localized_time(datetime.strptime(entry.completion_date, "%Y-%m-%d %H:%M"))
            dt = dt - timedelta(hours=7)
            # print dt
            key = str(dt)
            key = re.sub(r':\d{2}-.*', '', key)
            print key
            entry.completion_date = key
            entry.save()

if __name__ == "__main24335__":
    # import pytz
    # chart_name = "WU Latency: Alloc Stack"
    # model_name = "WuLatencyAllocStack"

    # mcs_entries = WuLatencyAllocStack.objects.all()
    # x = datetime(year=2018, month=6, day=01, minute=0, hour=0, second=0)
    # tz = pytz.timezone("UTC")
    # localized = tz.localize(x, is_dst=None)
    # # dt = get_localized_time(x)
    #
    # for mcs_entry in mcs_entries:
    #     if mcs_entry.input_date_time < localized:
    #         mcs_entry.delete()
    entries = MetricChart.objects.all()
    # print(len(entries))
    for entry in entries:
        if entry.data_sets:
            jsonData = json.loads(entry.data_sets)
            for data in jsonData:
                d = {}
                for input_name, input_value in data["inputs"].iteritems():
                    if d == "input_date_time":
                        continue
                    d[input_name] = input_value
                if "expected" in data["output"]:
                    if entry.metric_model_name:
                        outputName = data["output"]["name"]
                        print(entry.metric_model_name, outputName, data["output"]["expected"])
                        model = apps.get_model(app_label='fun_test', model_name=entry.metric_model_name)
                        mcs_entries = model.objects.filter(**d).order_by('input_date_time')
                        for m in mcs_entries:
                            print getattr(m, outputName)
                        i = len(mcs_entries) - 2
                        while i >= 0:
                            lastData = mcs_entries[i]
                            newExpectedOutput = getattr(lastData, outputName)
                            if newExpectedOutput < 0:
                                i = i - 1
                                print "Decrementing: {}".format(outputName)
                            else:
                                break
                        print newExpectedOutput
                        data["output"]["expected"] = newExpectedOutput
                        print(data["output"]["expected"])
            entry.data_sets = json.dumps(jsonData)
            entry.save()

if __name__ == "__main_owner__":
    models = {
        "AllocSpeedPerformance": "Bertrand Serlet (bertrand.serlet@fungible.com)",
        "WuLatencyUngated": "Bertrand Serlet (bertrand.serlet@fungible.com)",
        "WuLatencyAllocStack": "Bertrand Serlet (bertrand.serlet@fungible.com)",
        "BcopyPerformance": "Bertrand Serlet (bertrand.serlet@fungible.com)",
        "BcopyFloodDmaPerformance": "Bertrand Serlet (bertrand.serlet@fungible.com)",
        "EcPerformance": "Alagarswamy Devaraj (alagarswamy.devaraj@fungible.com)",
        "EcVolPerformance": "Alagarswamy Devaraj (alagarswamy.devaraj@fungible.com)",
        "VoltestPerformance": "Jaspal Kohli (jaspal.kohli@fungible.com)",
        "WuDispatchTestPerformance": "Tahsin Erdogan (tahsin.erdogan@fungible.com)",
        "WuSendSpeedTestPerformance": "Tahsin Erdogan (tahsin.erdogan@fungible.com)",
        "FunMagentPerformanceTest": "Bertrand Serlet (bertrand.serlet@fungible.com)",
        "WuStackSpeedTestPerformance": "Tahsin Erdogan (tahsin.erdogan@fungible.com)",
        "SoakFunMallocPerformance": "Bertrand Serlet (bertrand.serlet@fungible.com)",
        "SoakClassicMallocPerformance": "Bertrand Serlet (bertrand.serlet@fungible.com)",
        "BootTimePerformance": "Michael Boksanyi (michael.boksanyi@fungible.com)",
        "TeraMarkPkeRsaPerformance": "Michael Boksanyi (michael.boksanyi@fungible.com)",
        "TeraMarkPkeRsa4kPerformance": "Michael Boksanyi (michael.boksanyi@fungible.com)",
        "TeraMarkPkeEcdh256Performance": "Michael Boksanyi (michael.boksanyi@fungible.com)",
        "TeraMarkPkeEcdh25519Performance": "Michael Boksanyi (michael.boksanyi@fungible.com)",
        "TeraMarkCryptoPerformance": "Suren Madineni (suren.madineni@fungible.com)"
    }
    for model_name, owner in models.iteritems():
        entries = MetricChart.objects.filter(metric_model_name=model_name)
        for entry in entries:
            entry.owner_info = owner
            entry.save()

if __name__ == "__main_delete__":
    chart_names = ['Lookup-engine', 'HT HBM non-coherent - FP HBM non-coherent', 'HT HBM coherent - FP HBM coherent',
                   'HT DDR non-coherent - FP DDR non-coherent', 'HT DDR coherent - FP DDR coherent', 'TCAM', 'Total',
                   'All metrics', 'TeraMarks', 'Networking']
    for chart_name in chart_names:
        entries = MetricChartStatus.objects.filter(chart_name=chart_name).order_by('-date_time')[:2]
        for entry in entries:
            entry.delete()

if __name__ == "__mainBootTimePerformance__":
    model = apps.get_model(app_label='fun_test', model_name='BootTimePerformance')
    mcs_entries = model.objects.all()
    for entry in mcs_entries:
        entry.output_firmware_boot_time = entry.output_firmware_boot_time / 1000.0
        entry.output_flash_type_boot_time = entry.output_flash_type_boot_time / 1000.0
        entry.output_eeprom_boot_time = entry.output_eeprom_boot_time / 1000.0
        entry.output_sbus_boot_time = entry.output_sbus_boot_time / 1000.0
        entry.output_host_boot_time = entry.output_host_boot_time / 1000.0
        entry.output_main_loop_boot_time = entry.output_main_loop_boot_time / 1000.0
        entry.output_boot_success_boot_time = entry.output_boot_success_boot_time / 1000.0
        entry.save()
        print entry

if __name__ == "__mainappend_internal_chart_name__":
    # Set internal name
    charts = MetricChart.objects.all()
    for chart in charts:
        chart.internal_chart_name = chart.chart_name
        chart.save()

if __name__ == "__jpegmain__":
    display_name_map = {"output_average_bandwidth": "Bandwidth",
                        "output_iops": "IOPS",
                        "output_average_latency": "Latency"}
    yaxis_title_map = {"output_average_bandwidth": "kbps",
                       "output_iops": "ops/sec",
                       "output_average_latency": "ns"}
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)

    outputs = ["output_average_bandwidth", "output_iops", "output_average_latency"]
    # for operation in operations:
    #    for input_image in input_images:
    #        one_data_set = [operation, image, ]
    model_name = "TeraMarkJpegPerformance"
    input_choices = get_possible_values(model_name=model_name)
    for key, value in input_choices.iteritems():
        print key, value

    d = {"info": "JPEG",
         "metric_model_name": "MetricContainer",
         "leaf": False,
         "name": "JPEG",
         "label": "JPEG",
         "weight": 1, "children": []}
    jpeg_children = d["children"]
    for input_operation_choice in input_choices["input_operation"]:
        if input_operation_choice == "JPEG Compression":
            continue
        new_operation_entry = {"info": input_operation_choice,
                               "metric_model_name": "MetricContainer",
                               "leaf": False,
                               "name": input_operation_choice,
                               "label": input_operation_choice,
                               "weight": 1, "children": []}
        jpeg_children.append(new_operation_entry)
        operation_children = new_operation_entry["children"]
        for output_choice in outputs:
            data_sets = []
            positive = True

            chart_internal_name = "{}_{}".format(input_operation_choice, output_choice)
            chart_display_name = display_name_map[output_choice]
            new_output_entry = {"info": chart_internal_name,
                                "metric_model_name": model_name,
                                "leaf": True,
                                "name": chart_internal_name,
                                "label": chart_internal_name,
                                "weight": 1}
            operation_children.append(new_output_entry)
            print "This chart: {}, {}".format(chart_display_name, chart_internal_name)
            for input_image_choice in input_choices["input_image"]:
                one_data_set = {}
                one_data_set["inputs"] = {}
                one_data_set["inputs"]["input_operation"] = input_operation_choice
                one_data_set["inputs"]["input_image"] = input_image_choice
                one_data_set["output"] = {"name": output_choice, 'min': 0, "max": 9999999}
                one_data_set["name"] = input_image_choice
                data_sets.append(one_data_set)
            print data_sets
            if "latency" in output_choice.lower():
                positive = False

            MetricChart(chart_name=chart_display_name,
                        metric_id=LastMetricId.get_next_id(),
                        internal_chart_name=chart_internal_name,
                        data_sets=json.dumps(data_sets),
                        leaf=True,
                        description="TBD",
                        owner_info='aamir.shaikh@fungible.com',
                        positive=positive,
                        y1_axis_title=yaxis_title_map[output_choice],
                        metric_model_name=model_name).save()

    # for input_operation_choice in input_choices["input_operation"]:

    print json.dumps(d)

    '''
    a = [
        {"inputs": {"input_type": "LZMA", "input_effort": "8", "input_operation": "Decompress"}, 
         "name": "All Efforts",
         "output": {"expected": 182179, "max": 99999, "name": "output_latency_avg", "min": 0}}
    ]
    '''

if __name__ == "__networking_main__":
    display_name_map = {"output_throughput": "Bandwidth",
                        "output_latency_avg": "Latency",
                        "output_jitter_avg": "Jitter",
                        "output_pps": "PPS"}
    yaxis_title_map = {"output_throughput": "Mbps",
                       "output_latency_avg": "us",
                       "output_jitter_avg": "us",
                       "output_pps": "packets per second"}
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)

    outputs = ["output_throughput", "output_latency_avg", "output_jitter_avg", "output_pps"]
    # for operation in operations:
    #    for input_image in input_images:
    #        one_data_set = [operation, image, ]
    model_name = "NuTransitPerformance"
    input_choices = get_possible_values(model_name=model_name)
    for key, value in input_choices.iteritems():
        print key, value

    d = {"info": "Networking",
         "metric_model_name": "MetricContainer",
         "leaf": False,
         "name": "Networking_Teramarks",
         "label": "Networking",
         "weight": 1, "children": []}
    networking_children = d["children"]
    for input_flow_type in input_choices["input_flow_type"]:
        if input_flow_type:
            if "FCP_" in input_flow_type:
                input_flow_type = input_flow_type.replace("FCP_", "")
                input_flow_type = input_flow_type + "_FCP"
            new_operation_entry = {"info": input_flow_type,
                                   "metric_model_name": "MetricContainer",
                                   "leaf": False,
                                   "name": input_flow_type,
                                   "label": input_flow_type,
                                   "weight": 1, "children": []}
            networking_children.append(new_operation_entry)
            operation_children = new_operation_entry["children"]
            for output_choice in outputs:
                data_sets = []
                positive = True

                chart_internal_name = "{}_{}".format(input_flow_type, output_choice)
                chart_display_name = display_name_map[output_choice]
                new_output_entry = {"info": chart_internal_name,
                                    "metric_model_name": model_name,
                                    "leaf": True,
                                    "name": chart_internal_name,
                                    "label": chart_internal_name,
                                    "weight": 1}
                operation_children.append(new_output_entry)
                print "This chart: {}, {}".format(chart_display_name, chart_internal_name)
                for input_frame_size in input_choices["input_frame_size"]:
                    for input_mode in input_choices["input_mode"]:
                        one_data_set = {}
                        one_data_set["inputs"] = {}
                        one_data_set["inputs"]["input_flow_type"] = input_flow_type
                        one_data_set["inputs"]["input_frame_size"] = input_frame_size
                        one_data_set["inputs"]["input_mode"] = input_mode
                        one_data_set["output"] = {"name": output_choice, 'min': 0, "max": 9999999}
                        one_data_set["name"] = input_frame_size
                        data_sets.append(one_data_set)
                print data_sets
                if "latency" in output_choice.lower():
                    positive = False
                # mcs = MetricChart.objects.get(internal_chart_name=chart_internal_name)
                # if not mcs:
                MetricChart(chart_name=chart_display_name,
                            metric_id=LastMetricId.get_next_id(),
                            internal_chart_name=chart_internal_name,
                            data_sets=json.dumps(data_sets),
                            leaf=True,
                            description="TBD",
                            owner_info='amit.surana@fungible.com',
                            positive=positive,
                            y1_axis_title=yaxis_title_map[output_choice],
                            metric_model_name=model_name).save()

    # for input_operation_choice in input_choices["input_operation"]:

    print json.dumps(d)

if __name__ == "__main_delete_nutransit__":
    entries = NuTransitPerformance.objects.all().delete()
    print "Deletion Complete"

if __name__ == "__baseline_main__":
    entries = MetricChart.objects.all()
    sbl = SetBaseLine()
    base_line_date = datetime(year=2018, month=4, day=1, minute=59, hour=23, second=59)
    model_names = ["TeraMarkZipDeflatePerformance", "TeraMarkZipLzmaPerformance", "TeraMarkCryptoPerformance"]
    y1_axis_title = None
    for entry in entries:
        if entry.metric_model_name in model_names:
            base_line_date = datetime(year=2019, month=1, day=30, minute=0, hour=0, second=0)
            if "Latency" in entry.chart_name:
                y1_axis_title = "ns"
            else:
                y1_axis_title = "Gbps"
        else:
            base_line_date = datetime(year=2018, month=4, day=1, minute=59, hour=23, second=59)
        sbl.set_base_line(metric_id=entry.metric_id, base_line_date=base_line_date, y1_axis_title=y1_axis_title)
    print "Setting Complete"

if __name__ == "__main_zip__":
    entries = MetricChart.objects.all()
    sbl = SetBaseLine()
    model_names = ["TeraMarkZipDeflatePerformance", "TeraMarkZipLzmaPerformance"]
    for entry in entries:
        if entry.metric_model_name in model_names:
            if "Latency" in entry.chart_name:
                base_line_date = datetime(year=2018, month=4, day=1, minute=59, hour=23, second=59)
            else:
                base_line_date = entry.base_line_date + timedelta(days=1)
            sbl.set_base_line(metric_id=entry.metric_id, base_line_date=base_line_date, y1_axis_title=None)
    print "Setting Complete"

if __name__ == "__main_milestone__":
    entries = MetricChart.objects.all()
    for entry in entries:
        if entry.metric_id:
            mmt = MileStoneMarkers(metric_id=entry.metric_id, milestone_date=datetime(year=2018, month=9, day=16),
                                   milestone_name="Tape-out")
            mmt.save()
            mmf = MileStoneMarkers(metric_id=entry.metric_id, milestone_date=datetime(year=2019, month=1, day=24),
                                   milestone_name="F1")
            mmf.save()
    print "MileStone Complete"

if __name__ == "__main_PKE__":
    entries = MetricChart.objects.all()
    sbl = SetBaseLine()
    model_names = ["PkeX25519TlsSoakPerformance", "PkeP256TlsSoakPerformance"]
    for entry in entries:
        if entry.metric_model_name in model_names:
            base_line_date = datetime(year=2019, month=2, day=8, minute=0, hour=0, second=0)
            mmt = MileStoneMarkers(metric_id=entry.metric_id, milestone_date=datetime(year=2018, month=9, day=16),
                                   milestone_name="Tape-out")
            mmt.save()
            mmf = MileStoneMarkers(metric_id=entry.metric_id, milestone_date=datetime(year=2019, month=1, day=24),
                                   milestone_name="F1")
            mmf.save()
            sbl.set_base_line(metric_id=entry.metric_id, base_line_date=base_line_date, y1_axis_title=None)
    print "Milestone and Baseline Setting Complete"

if __name__ == "__main_HU_NU__":
    entries = MetricChart.objects.all()
    sbl = SetBaseLine()
    chart_names = ["HU_NU_NFCP_output_latency_avg", "HU_NU_NFCP_output_throughput", "HU_NU_NFCP", "TeraMark PKE",
                   "PKE soak"]
    for entry in entries:
        if entry.internal_chart_name in chart_names:
            base_line_date = datetime(year=2019, month=2, day=8, minute=0, hour=0, second=0)
            mmt = MileStoneMarkers(metric_id=entry.metric_id, milestone_date=datetime(year=2018, month=9, day=16),
                                   milestone_name="Tape-out")
            mmt.save()
            mmf = MileStoneMarkers(metric_id=entry.metric_id, milestone_date=datetime(year=2019, month=1, day=24),
                                   milestone_name="F1")
            mmf.save()
            sbl.set_base_line(metric_id=entry.metric_id, base_line_date=base_line_date, y1_axis_title=None)
    print "Milestone and Baseline Setting Complete"

if __name__ == "__main_JPEG_gbps__":
    entries = MetricChart.objects.all()
    sbl = SetBaseLine()
    model_names = ["TeraMarkJpegPerformance"]
    for entry in entries:
        if entry.metric_model_name in model_names:
            base_line_date = datetime(year=2019, month=2, day=12, minute=0, hour=0, second=0)
            mmt = MileStoneMarkers(metric_id=entry.metric_id, milestone_date=datetime(year=2018, month=9, day=16),
                                   milestone_name="Tape-out")
            mmt.save()
            mmf = MileStoneMarkers(metric_id=entry.metric_id, milestone_date=datetime(year=2019, month=1, day=24),
                                   milestone_name="F1")
            mmf.save()
            if entry.chart_name == "Bandwidth":
                print entry.chart_name
                y1_axis_title = "Gbps"
            elif entry.chart_name == "Latency":
                print entry.chart_name
                y1_axis_title = "ns"
            elif entry.chart_name == "IOPS":
                print entry.chart_name
                y1_axis_title = "ops/sec"
            elif entry.chart_name == "Compression-ratio":
                print entry.chart_name
                y1_axis_title = "number"
            else:
                y1_axis_title = None

            sbl.set_base_line(metric_id=entry.metric_id, base_line_date=base_line_date, y1_axis_title=y1_axis_title)
    print "Milestone and Baseline Setting Complete"

if __name__ == "__main_rebasing__":
    entries = MetricChart.objects.all()
    sbl = SetBaseLine()
    internal_chart_names_zip = ["Deflate", "Lzma", "Zip"]
    internal_chart_names_jpeg = ["JPEG", "Decompression Accelerator throughput", "JPEG Decompress",
                                 "Compression Accelerator throughput", "Compression throughput with Driver",
                                 "Compression-ratio"]
    internal_chart_names_crypto = ["Crypto", "Crypto Accelerator"]
    for entry in entries:
        if entry.internal_chart_name in internal_chart_names_zip:
            base_line_date = datetime(year=2019, month=1, day=31, minute=0, hour=0, second=0)
            sbl.set_base_line(metric_id=entry.metric_id, base_line_date=base_line_date, y1_axis_title=None)
        if entry.internal_chart_name in internal_chart_names_jpeg:
            base_line_date = datetime(year=2019, month=2, day=13, minute=0, hour=0, second=0)
            sbl.set_base_line(metric_id=entry.metric_id, base_line_date=base_line_date, y1_axis_title=None)
        if entry.internal_chart_name in internal_chart_names_crypto:
            base_line_date = datetime(year=2019, month=1, day=30, minute=0, hour=0, second=0)
            sbl.set_base_line(metric_id=entry.metric_id, base_line_date=base_line_date, y1_axis_title=None)
    print "Milestone and Baseline Setting Complete"

if __name__ == "__main_DMA__":
    entries = MetricChart.objects.all()
    sbl = SetBaseLine()
    chart_names = ["DMA", "MovingBits"]
    for entry in entries:
        if "memcpy" in entry.internal_chart_name or "memset" in entry.internal_chart_name:
            base_line_date = datetime(year=2019, month=2, day=17, minute=0, hour=0, second=0)
            if entry.leaf:
                y1_axis_title = "GBps"
            else:
                y1_axis_title = None
            sbl.set_base_line(metric_id=entry.metric_id, base_line_date=base_line_date, y1_axis_title=y1_axis_title)
            mmt = MileStoneMarkers(metric_id=entry.metric_id, milestone_date=datetime(year=2018, month=9, day=16),
                                   milestone_name="Tape-out")
            mmt.save()
        if entry.chart_name in chart_names:
            base_line_date = datetime(year=2019, month=2, day=17, minute=0, hour=0, second=0)
            sbl.set_base_line(metric_id=entry.metric_id, base_line_date=base_line_date, y1_axis_title=None)
            mmt = MileStoneMarkers(metric_id=entry.metric_id, milestone_date=datetime(year=2018, month=9, day=16),
                                   milestone_name="Tape-out")
            mmt.save()
    print "Milestone and Baseline Setting Complete"

if __name__ == "__main_crypto_baseline__":
    entries = MetricChart.objects.all()
    sbl = SetBaseLine()
    internal_chart_names = ["Crypto raw throughput", "Crypto api throughput"]
    for entry in entries:
        if entry.internal_chart_name in internal_chart_names:
            base_line_date = datetime(year=2019, month=2, day=18, minute=0, hour=0, second=0)
            mmt = MileStoneMarkers(metric_id=entry.metric_id, milestone_date=datetime(year=2018, month=9, day=16),
                                   milestone_name="Tape-out")
            mmt.save()
            sbl.set_base_line(metric_id=entry.metric_id, base_line_date=base_line_date, y1_axis_title=None)
    print "Milestone and Baseline Setting Complete"

if __name__ == "__main_crypto_charts__":
    internal_name_map = {"AES_GCM": "AES_GCM Encryption Raw Throughput",
                         "AES_XTS": "AES_XTS Encryption Raw Throughput",
                         "SHA_256": "SHA_256 Raw Throughput",
                         "SHA3_256": "SHA3_256 Raw Throughput"}
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    sbl = SetBaseLine()
    base_line_date = datetime(year=2019, month=2, day=19, minute=0, hour=0, second=0)
    model_name = "TeraMarkMultiClusterCryptoPerformance"
    input_choices = get_possible_values(model_name=model_name)
    for key, value in input_choices.iteritems():
        print key, value

    for input_algorithm in input_choices["input_algorithm"]:
        if input_algorithm:
            data_sets = []
            for packet_size in input_choices["input_pkt_size"]:
                if "SHA" in input_algorithm:
                    input_operation = "Hash"
                    input_key_size = 0
                    name = packet_size
                    one_data_set = {}
                    one_data_set["inputs"] = {}
                    one_data_set["inputs"]["input_algorithm"] = input_algorithm
                    one_data_set["inputs"]["input_operation"] = input_operation
                    one_data_set["inputs"]["input_key_size"] = input_key_size
                    one_data_set["inputs"]["input_pkt_size"] = packet_size
                    one_data_set["output"] = {"name": "output_throughput", 'min': 0, "max": 9999999}
                    one_data_set["name"] = name
                    data_sets.append(one_data_set)
                else:
                    input_operation = "Encrypt"
                    for key_size in input_choices["input_key_size"]:
                        if key_size != 0:
                            name = str(packet_size) + "-" + str(key_size)
                            one_data_set = {}
                            one_data_set["inputs"] = {}
                            one_data_set["inputs"]["input_algorithm"] = input_algorithm
                            one_data_set["inputs"]["input_operation"] = input_operation
                            one_data_set["inputs"]["input_key_size"] = key_size
                            one_data_set["inputs"]["input_pkt_size"] = packet_size
                            one_data_set["output"] = {"name": "output_throughput", 'min': 0, "max": 9999999}
                            one_data_set["name"] = name
                            data_sets.append(one_data_set)

            metric_id = LastMetricId.get_next_id()
            positive = True
            MetricChart(chart_name=input_algorithm,
                        metric_id=metric_id,
                        internal_chart_name=internal_name_map[input_algorithm],
                        data_sets=json.dumps(data_sets),
                        leaf=True,
                        description="TBD",
                        owner_info="Suren Madineni (suren.madineni@fungible.com)",
                        positive=positive,
                        y1_axis_title="Gbps",
                        metric_model_name=model_name,
                        base_line_date=base_line_date).save()
            mmt = MileStoneMarkers(metric_id=metric_id,
                                   milestone_date=datetime(year=2018, month=9, day=16),
                                   milestone_name="Tape-out")
            mmt.save()
    print "Creating charts and setting baseline is done programatically"

if __name__ == "__main_delete_nw__":
    model = NuTransitPerformance
    entries = model.objects.all()
    entries.delete()
    print "deleted nu transit model"

if __name__ == "__main_remove_mm__":
    model = MetricChart
    model_name = "NuTransitPerformance"
    internal_chart_names = ["Networking", "Networking_Teramarks", "NU_HNU", "HNU_HNU_FCP", "HNU_HNU", "NU_NU", "HNU_NU",
                            "HU_NU_NFCP"]
    entries = model.objects.all()
    for entry in entries:
        if entry.metric_model_name == model_name or entry.internal_chart_name in internal_chart_names:
            mm = MileStoneMarkers.objects.filter(metric_id=entry.metric_id)
            for milestone in mm:
                if milestone.milestone_name == "F1":
                    milestone.delete()
    print "removed milestones for networking"

if __name__ == "__main_create_nw__":
    internal_name_map = {"HU_HU_Throughput": "HU_HU_NFCP_output_throughput",
                         "HU_HU_Latency": "HU_HU_NFCP_output_latency_avg",
                         "NU_HU_Throughput": "NU_HU_NFCP_output_throughput",
                         "NU_HU_Latency": "NU_HU_NFCP_output_latency_avg"}
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    sbl = SetBaseLine()
    base_line_date = datetime(year=2019, month=1, day=22, minute=0, hour=0, second=0)
    model_name = "NuTransitPerformance"
    input_choices = get_possible_values(model_name=model_name)
    for key, value in input_choices.iteritems():
        print key, value

    flow_types = ["HU_HU_NFCP", "NU_HU_NFCP"]
    flow_type_map = {"HU_HU_Throughput": "HU_HU_NFCP",
                     "HU_HU_Latency": "HU_HU_NFCP",
                     "NU_HU_Throughput": "NU_HU_NFCP",
                     "NU_HU_Latency": "NU_HU_NFCP"}
    frame_sizes = [64, 1500]

    for internal_name in internal_name_map:
        internal_flow_type = flow_type_map[internal_name]
        for input_flow_type in input_choices["input_flow_type"]:
            if input_flow_type in flow_types and input_flow_type == internal_flow_type:
                data_sets = []
                for input_frame_size in input_choices["input_frame_size"]:
                    if input_frame_size in frame_sizes:
                        chart_name = internal_name.split('_')[-1]
                        one_data_set = {}
                        one_data_set["inputs"] = {}
                        one_data_set["inputs"]["input_flow_type"] = input_flow_type
                        one_data_set["inputs"]["input_frame_size"] = input_frame_size
                        one_data_set["name"] = str(input_frame_size) + 'B'
                        if chart_name == "Throughput":
                            one_data_set["output"] = {"name": "output_throughput", 'min': 0, "max": 9999999}
                        else:
                            one_data_set["output"] = {"name": "output_latency_avg", 'min': 0, "max": 9999999}
                        data_sets.append(one_data_set)
                internal_chart_name = internal_name_map[internal_name]
                chart_name = internal_name.split('_')[-1]
                metric_id = LastMetricId.get_next_id()
                if chart_name == "Throughput":
                    positive = True
                    y1_axis_title = "Mbps"
                else:
                    positive = False
                    y1_axis_title = "ns"
                MetricChart(chart_name=chart_name,
                            metric_id=metric_id,
                            internal_chart_name=internal_chart_name,
                            data_sets=json.dumps(data_sets),
                            leaf=True,
                            description="TBD",
                            owner_info="Zhuo (George) Liang (george.liang@fungible.com)",
                            positive=positive,
                            y1_axis_title=y1_axis_title,
                            metric_model_name=model_name,
                            base_line_date=base_line_date).save()
                mmt = MileStoneMarkers(metric_id=metric_id,
                                       milestone_date=datetime(year=2018, month=9, day=16),
                                       milestone_name="Tape-out")
                mmt.save()
    print "Creating charts and setting baseline for networking flow types is completed programatically"

if __name__ == "__main__":
    entries = MetricChart.objects.all()
    count = 0
    for entry in entries:
        if entry.leaf and entry.data_sets:
            count += 1
            print entry.chart_name
            jsonData = json.loads(entry.data_sets)
            for data in jsonData:
                if "expected" in data["output"]:
                    expected = data["output"]["expected"]
                    print (count, ". old ", expected)
                    data["output"]["reference"] = expected
                    reference = data["output"]["reference"]
                    print (count, ". new ", reference)
                    data["output"]["expected"] = 0
                    print (count, ". old ", data["output"]["expected"])
            entry.data_sets = json.dumps(jsonData)
            entry.save()
    print "created reference values"
