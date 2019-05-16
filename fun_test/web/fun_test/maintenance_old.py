import os
import django
import json
import random, pytz
from dateutil.parser import parse
import re
from fun_global import *
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

from web.fun_test.analytics_models_helper import MetricChartHelper, BltVolumePerformanceHelper
from web.fun_test.metrics_models import MetricChartStatus, TeraMarkJpegPerformance
from web.fun_test.metrics_models import LastMetricId, MileStoneMarkers, BltVolumePerformance
from web.fun_test.metrics_lib import MetricLib


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
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
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


def get_possible_output_values(model_name):
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    metric_model = app_config.get_metric_models()[model_name]
    fields = metric_model._meta.get_fields()
    field_choices = []
    for field in fields:
        if field.column.startswith("output_"):
            field_choices.append(field.column)
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

if __name__ == "__main_crypto_raw__":
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
    global_setting = MetricsGlobalSettings.objects.first()
    global_setting.cache_valid = False
    global_setting.save()
    print "cache valid is false"

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

if __name__ == "__main_reference__":
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
                    data["output"]["expected"] = -1
                    print (count, ". old ", data["output"]["expected"])
            entry.data_sets = json.dumps(jsonData)
            entry.save()
    print "created reference values"

if __name__ == "__main_change_max__":
    entries = MetricChart.objects.all()
    count = 0
    for entry in entries:
        if entry.leaf:
            count += 1
            data_set = json.loads(entry.data_sets)
            for data in data_set:
                if "max" in data["output"]:
                    maximum = data["output"]["max"]
                    print (count, maximum)
                    if str(maximum).startswith('99'):
                        data["output"]["max"] = -1
                        print (count, data["output"]["max"])
            entry.data_sets = json.dumps(data_set)
            entry.save()
    print "maximum values for all data sets set to -1"

if __name__ == "__main_create_pps__":
    flow_types = ["HU_HU_NFCP", "HU_NU_NFCP", "NU_HU_NFCP"]
    model_name = "NuTransitPerformance"
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    input_choices = get_possible_values(model_name=model_name)
    frame_size = 1500
    name = "1500B"
    output = "output_pps"
    chart_name = "Extrapolated Packets per sec"
    for flow_type in flow_types:
        data_sets = []
        internal_name = flow_type + '_' + output
        one_data_set = {}
        one_data_set["inputs"] = {}
        one_data_set["inputs"]["input_flow_type"] = flow_type
        one_data_set["inputs"]["input_frame_size"] = frame_size
        one_data_set["name"] = name
        one_data_set["output"] = {"name": "output_pps", 'min': 0, "max": -1, "expected": -1, "reference": -1}
        data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        positive = True
        y1_axis_title = "Mpps"
        base_line_date = datetime(year=2019, month=1, day=22, minute=0, hour=0, second=0)
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_name,
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
    print "create pps charts for 3 nw flow type metrics"

if __name__ == "__main_compression__":
    entries = MetricChart.objects.all()
    for entry in entries:
        if entry.base_line_date:
            if str(entry.base_line_date).startswith('2019-04-01'):
                print (entry.chart_name, str(entry.base_line_date))
                if entry.chart_name == "Compression":
                    base_line_date = datetime(year=2019, month=1, day=30, minute=0, hour=0, second=0)
                else:
                    base_line_date = datetime(year=2019, month=2, day=7, minute=0, hour=0, second=0)
                entry.base_line_date = base_line_date
                entry.save()
                print (entry.chart_name, str(entry.base_line_date))

if __name__ == "__main_EC_Perf__":
    entries = MetricChart.objects.all()
    for entry in entries:
        if entry.chart_name == "EC 8:4 Throughput":
            entry.y1_axis_title = "Gbps"
            entry.save()
    model = apps.get_model(app_label='fun_test', model_name='EcPerformance')
    mcs_entries = model.objects.all()
    base_line_date = datetime(year=2019, month=3, day=14, minute=0, hour=0, second=0)
    for entry in mcs_entries:
        if entry.input_date_time.day >= base_line_date.day and entry.input_date_time.month >= base_line_date.month and entry.input_date_time.year >= base_line_date.year:
            print entry.input_date_time
            entry.output_encode_throughput_min = entry.output_encode_throughput_min / 1000
            entry.output_encode_throughput_max = entry.output_encode_throughput_max / 1000
            entry.output_encode_throughput_avg = entry.output_encode_throughput_avg / 1000
            entry.output_recovery_throughput_min = entry.output_recovery_throughput_min / 1000
            entry.output_recovery_throughput_max = entry.output_recovery_throughput_max / 1000
            entry.output_recovery_throughput_avg = entry.output_recovery_throughput_avg / 1000
            entry.save()
            print "updated"

if __name__ == "__main_create_hu_fcp__":
    flow_types = ["HU_HU_FCP"]
    model_name = "NuTransitPerformance"
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    input_choices = get_possible_values(model_name=model_name)
    frame_size = 800
    name = "800B"
    outputs = ["output_throughput", "output_pps", "output_latency_avg"]
    chart_names = ["Throughput", "Packets per sec", "Latency"]
    for flow_type in flow_types:
        for output in outputs:
            data_sets = []
            internal_name = flow_type + '_' + output
            one_data_set = {}
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_flow_type"] = flow_type
            one_data_set["inputs"]["input_frame_size"] = frame_size
            one_data_set["name"] = name
            one_data_set["output"] = {"name": output, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)
            metric_id = LastMetricId.get_next_id()
            positive = True
            if "throughput" in output:
                y1_axis_title = "Gbps"
                chart_name = "Throughput"
            elif "pps" in output:
                y1_axis_title = "Mpps"
                chart_name = "Packets per sec"
            else:
                y1_axis_title = "usecs"
                chart_name = "Latency"
                positive = False
            base_line_date = datetime(year=2019, month=3, day=19, minute=0, hour=0, second=0)
            MetricChart(chart_name=chart_name,
                        metric_id=metric_id,
                        internal_chart_name=internal_name,
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
    print "chart creation for HU_HU_FCP is done"
    entries = MetricChart.objects.all()
    for entry in entries:
        if not entry.leaf:
            if "Host" in entry.chart_name:
                base_line_date = datetime(year=2019, month=3, day=19, minute=0, hour=0, second=0)
                entry.base_line_date = base_line_date
                entry.save()
                print entry.chart_name

if __name__ == "__main_unit_change__":
    entries = MetricChart.objects.all()
    for entry in entries:
        if entry.leaf:
            if entry.y1_axis_title == "ns":
                entry.y1_axis_title = "nsecs"
            elif entry.y1_axis_title == "ops/sec":
                entry.y1_axis_title = "ops"
            elif entry.y1_axis_title == "ms":
                entry.y1_axis_title = "msecs"
            elif entry.y1_axis_title == "us":
                entry.y1_axis_title = "usecs"
            elif entry.y1_axis_title == "seconds":
                entry.y1_axis_title = "secs"
            elif entry.y1_axis_title == "IOPS":
                entry.y1_axis_title = "ops"
            elif entry.y1_axis_title == "Cycles":
                entry.y1_axis_title = "cycles"
            elif entry.y1_axis_title == "mbps":
                entry.y1_axis_title = "Mbps"
            elif entry.y1_axis_title == "Kops/sec":
                entry.y1_axis_title = "Kops"
            entry.save()
            entry.visualization_unit = entry.y1_axis_title
            entry.save()
    print "setting y1axis title, score and viz unit complete"

if __name__ == "__main_flowtest__":
    chart_name = "Flowtest on F1"
    internal_chart_name = "flow_test_f1"
    model_name = "F1FlowTestPerformance"
    data_sets = []
    one_data_set = {}
    one_data_set["inputs"] = {}
    one_data_set["inputs"]["input_app"] = "hw_hsu_test"
    one_data_set["inputs"]["input_iterations"] = 100000000
    one_data_set["name"] = "100M iterations"
    one_data_set["output"] = {"name": "output_time", 'min': 0, "max": -1, "expected": -1, "reference": None}
    data_sets.append(one_data_set)
    metric_id = LastMetricId.get_next_id()
    positive = False
    y1_axis_title = "secs"
    base_line_date = datetime(year=2019, month=3, day=24, minute=0, hour=0, second=0)
    MetricChart(chart_name=chart_name,
                metric_id=metric_id,
                internal_chart_name=internal_chart_name,
                data_sets=json.dumps(data_sets),
                leaf=True,
                description="TBD",
                owner_info="Divya Krishnankutty (divya.krishnankutty@fungible.com)",
                positive=positive,
                y1_axis_title=y1_axis_title,
                visualization_unit=y1_axis_title,
                metric_model_name=model_name,
                base_line_date=base_line_date).save()
    mmt = MileStoneMarkers(metric_id=metric_id,
                           milestone_date=datetime(year=2018, month=9, day=16),
                           milestone_name="Tape-out")
    mmt.save()

if __name__ == "__main_DFA__":
    chart_names = ["DFA Throughput", "NFA Throughput"]

    for chart_name in chart_names:
        if "DFA" in chart_name:
            model_name = "TeraMarkDfaPerformance"
            internal_chart_name = "dfa_teramark_output_bandwidth"
            name = "dfa"
        else:
            model_name = "TeraMarkNfaPerformance"
            internal_chart_name = "nfa_teramark_output_bandwidth"
            name = "nfa"
        data_sets = []
        one_data_set = {}
        one_data_set["inputs"] = {}
        one_data_set["name"] = name
        one_data_set["output"] = {"name": "output_bandwidth", 'min': 0, "max": -1, "expected": -1, "reference": -1}
        data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        positive = True
        y1_axis_title = "Gbps"
        base_line_date = datetime(year=2019, month=3, day=25, minute=0, hour=0, second=0)
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Lakshmi Billa (lakshmi.billa@fungible.com), Mahesh Kumar (mahesh.kumar@fungible.com)",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date).save()
        mmt = MileStoneMarkers(metric_id=metric_id,
                               milestone_date=datetime(year=2018, month=9, day=16),
                               milestone_name="Tape-out")
        mmt.save()
    print "created charts for DFA and NFA"

if __name__ == "__main_container_unit_removal__":
    print "started unit removal for containers"
    entries = MetricChart.objects.all()
    for entry in entries:
        if not entry.leaf:
            print entry.chart_name
            entry.y1_axis_title = ""
            entry.visualization_unit = ""
            entry.save()
    print "finished removing units from containers"

if __name__ == "__main_adding_db_blt__":
    print "started adding entry into blt performance"
    blt = BltVolumePerformanceHelper()
    blt.add_entry(date_time=datetime.now(), volume="BLT", test="FioSeqWriteSeqReadOnly", block_size="4k", io_depth=20,
                  size="20g", operation="read", num_ssd=1, num_volume=1, fio_job_name="job_name", write_iops=1678,
                  read_iops=1780,
                  write_throughput=237, read_throughput=279, write_avg_latency=1789, read_avg_latency=1890,
                  write_90_latency=-1,
                  write_95_latency=-1, write_99_latency=-1, read_90_latency=-1, read_95_latency=-1, read_99_latency=-1,
                  write_iops_unit="ops", read_iops_unit="ops", write_throughput_unit="Mbps",
                  read_throughput_unit="Mbps", write_avg_latency_unit="usecs", read_avg_latency_unit="usecs",
                  write_90_latency_unit="usecs", write_95_latency_unit="usecs",
                  write_99_latency_unit="usecs", read_90_latency_unit="usecs", read_95_latency_unit="usecs",
                  read_99_latency_unit="usecs")
    print "added an entry into the DB"

if __name__ == "__main_read_throughput__":
    internal_chart_names = ["read_4kb1vol1ssd_output_bandwidth", "write_4kb1vol1ssd_output_bandwidth",
                            "read_4kb1vol1ssd_output_iops", "write_4kb1vol1ssd_output_iops"]
    model_name = "BltVolumePerformance"
    fio_read_job_names = ["fio_read_4gbps"]
    fio_write_job_names = ["fio_write_4gbps"]

    for internal_chart_name in internal_chart_names:
        fio_job_names = []
        if "bandwidth" in internal_chart_name:
            chart_name = "Throughput"
            y1_axis_title = "MBps"
        else:
            chart_name = "IOPS"
            y1_axis_title = "ops"
        if "read_" in internal_chart_name:
            if chart_name == "Throughput":
                output_name = "output_read_throughput"
            else:
                output_name = "output_read_iops"
            fio_job_names = fio_read_job_names
            operation = "read"
        else:
            if chart_name == "Throughput":
                output_name = "output_write_throughput"
            else:
                output_name = "output_write_iops"
            fio_job_names = fio_write_job_names
            operation = "write"

        data_sets = []
        name = "Samsung PM1725b (MZWLL1T6HAJQ)"
        for job_name in fio_job_names:
            one_data_set = {}
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_fio_job_name"] = job_name
            one_data_set["inputs"]["input_operation"] = operation
            one_data_set["name"] = name
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        positive = True
        base_line_date = datetime(year=2019, month=4, day=1, minute=0, hour=0, second=0)
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Ravi Hulle (ravi.hulle@fungible.com)",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date).save()
        mmt = MileStoneMarkers(metric_id=metric_id,
                               milestone_date=datetime(year=2018, month=9, day=16),
                               milestone_name="Tape-out")
        mmt.save()
    print "created throughput charts for storage"

if __name__ == "__main_read_latency__":
    internal_chart_names_dict = {"read_4kb1vol1ssd_4_output_latency": "Latency - 4Gbps",
                                 "read_4kb1vol1ssd_8_output_latency": "Latency - 8Gbps",
                                 "write_4kb1vol1ssd_4_output_latency": "Latency - 4Gbps",
                                 "write_4kb1vol1ssd_8_output_latency": "Latency - 8Gbps"}
    model_name = "BltVolumePerformance"
    fio_read_job_names = ["fio_read_4gbps", "fio_read_8gbps"]
    fio_write_job_names = ["fio_write_4gbps", "fio_write_8gbps"]
    y1_axis_title = "usecs"
    output_write_names = ["output_write_avg_latency", "output_write_90_latency", "output_write_95_latency",
                          "output_write_99_latency"]
    output_read_names = ["output_read_avg_latency", "output_read_90_latency", "output_read_95_latency",
                         "output_read_99_latency"]

    for internal_chart_name in internal_chart_names_dict:
        output_names = []
        chart_name = internal_chart_names_dict[internal_chart_name]
        if "read_" in internal_chart_name:
            if "4Gbps" in chart_name:
                fio_job_name = "fio_read_4gbps"
            else:
                fio_job_name = "fio_read_8gbps"
            output_names = output_read_names
            operation = "read"
        else:
            if "4Gbps" in chart_name:
                fio_job_name = "fio_write_4gbps"
            else:
                fio_job_name = "fio_write_8gbps"
            output_names = output_write_names
            operation = "write"

        data_sets = []
        for output_name in output_names:
            if "avg_" in output_name:
                name = "avg"
            elif "90_" in output_name:
                name = "90%"
            elif "95_" in output_name:
                name = "95%"
            else:
                name = "99.99%"

            one_data_set = {}
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
            one_data_set["inputs"]["input_operation"] = operation
            one_data_set["name"] = name
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        positive = False
        base_line_date = datetime(year=2019, month=4, day=1, minute=0, hour=0, second=0)
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Ravi Hulle (ravi.hulle@fungible.com)",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date).save()
        mmt = MileStoneMarkers(metric_id=metric_id,
                               milestone_date=datetime(year=2018, month=9, day=16),
                               milestone_name="Tape-out")
        mmt.save()
    print "created latency charts for storage"

if __name__ == "__main__rand_read_throughput__":
    internal_chart_names = ["rand_read_4kb1vol1ssd_output_bandwidth",
                            "rand_read_4kb1vol1ssd_output_iops"]
    model_name = "BltVolumePerformance"
    fio_read_job_names = ["fio_randread_4gbps"]

    for internal_chart_name in internal_chart_names:
        fio_job_names = []
        if "bandwidth" in internal_chart_name:
            chart_name = "Throughput"
            y1_axis_title = "MBps"
        else:
            chart_name = "IOPS"
            y1_axis_title = "ops"
        if chart_name == "Throughput":
            output_name = "output_read_throughput"
        else:
            output_name = "output_read_iops"
        fio_job_names = fio_read_job_names
        operation = "randread"

        data_sets = []
        name = "Samsung PM1725b (MZWLL1T6HAJQ)"
        for job_name in fio_job_names:
            one_data_set = {}
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_fio_job_name"] = job_name
            one_data_set["inputs"]["input_operation"] = operation
            one_data_set["name"] = name
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        positive = True
        base_line_date = datetime(year=2019, month=4, day=1, minute=0, hour=0, second=0)
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Ravi Hulle (ravi.hulle@fungible.com)",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date).save()
        mmt = MileStoneMarkers(metric_id=metric_id,
                               milestone_date=datetime(year=2018, month=9, day=16),
                               milestone_name="Tape-out")
        mmt.save()
    print "created throughput charts for random read storage"

if __name__ == "__main__random_read_latency__":
    internal_chart_names_dict = {"rand_read_4kb1vol1ssd_4_output_latency": "Latency"}
    model_name = "BltVolumePerformance"
    fio_read_job_names = ["fio_randread_4gbps"]
    y1_axis_title = "usecs"
    output_read_names = ["output_read_avg_latency", "output_read_90_latency", "output_read_95_latency",
                         "output_read_99_latency"]

    for internal_chart_name in internal_chart_names_dict:
        chart_name = internal_chart_names_dict[internal_chart_name]
        fio_job_name = "fio_randread_4gbps"
        output_names = output_read_names
        operation = "randread"

        data_sets = []
        for output_name in output_names:
            if "avg_" in output_name:
                name = "avg"
            elif "90_" in output_name:
                name = "90%"
            elif "95_" in output_name:
                name = "95%"
            else:
                name = "99.99%"

            one_data_set = {}
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
            one_data_set["inputs"]["input_operation"] = operation
            one_data_set["name"] = name
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        positive = False
        base_line_date = datetime(year=2019, month=4, day=1, minute=0, hour=0, second=0)
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Ravi Hulle (ravi.hulle@fungible.com)",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date).save()
        mmt = MileStoneMarkers(metric_id=metric_id,
                               milestone_date=datetime(year=2018, month=9, day=16),
                               milestone_name="Tape-out")
        mmt.save()
    print "created latency charts for random read storage"

if __name__ == "__main_memset_non_coh__":
    entries = MetricChart.objects.all()
    ml = MetricLib()
    for entry in entries:
        d = {}
        if entry.metric_model_name == "SoakDmaMemsetPerformance":
            d["input_coherent"] = True
            status = ml.add_attributes_to_data_sets(metric_id=entry.metric_id, **d)
            if not status:
                print "not successful - error"
            print "added attribute for {}".format(entry.chart_name)
    print "successfully added attribute to the memset data sets"
    for entry in entries:
        if entry.metric_model_name == "SoakDmaMemsetPerformance":
            d = {}
            data_sets = ml.get_data_sets(metric_id=entry.metric_id)
            for data_set in data_sets:
                data_set["inputs"]["input_coherent"] = False
            chart_name = entry.chart_name.replace("memset", "memset non coherent")
            internal_chart_name = entry.internal_chart_name.replace("memset", "memset_non_coherent")
            base_line_date = datetime(year=2019, month=4, day=3, minute=0, hour=0, second=0)
            d["chart_name"] = chart_name
            d["internal_chart_name"] = internal_chart_name
            d["data_sets"] = data_sets
            d["leaf"] = True
            d["description"] = "TBD"
            d["owner_info"] = entry.owner_info
            d["source"] = entry.source
            d["positive"] = entry.positive
            d["y1_axis_title"] = entry.y1_axis_title
            d["visualization_unit"] = entry.y1_axis_title
            d["metric_model_name"] = entry.metric_model_name
            d["base_line_date"] = base_line_date
            ml.create_chart(**d)
            print "created chart for {}".format(chart_name)
    print "created charts for memset non coherent"

if __name__ == "__main_blt_99__":
    model_name = "BltVolumePerformance"
    model = BltVolumePerformance
    data = model.objects.all()
    for d in data:
        if d.output_read_99_latency:
            d.output_read_99_99_latency = d.output_read_99_latency
            d.save()
            d.output_read_99_latency = -1
            d.save()
    entries = MetricChart.objects.all()
    ml = MetricLib()
    for entry in entries:
        if entry.metric_model_name == model_name:
            if entry.chart_name == "Latency":
                data_sets = json.loads(entry.data_sets)
                print json.dumps(data_sets)
                for data_set in data_sets:
                    if "99_latency" in data_set["output"]["name"]:
                        data_set["output"]["name"] = data_set["output"]["name"].replace("99", "99_99")
                print json.dumps(data_sets)
                ml.save_data_sets(data_sets=data_sets, chart=entry)

if __name__ == "__main_new_base_line__":
    entries = MetricChart.objects.all()
    new_base_line = datetime(year=2019, month=1, day=26, minute=0, hour=0, second=0)
    new_base_line = get_localized_time(new_base_line)
    for entry in entries:
        if entry.base_line_date < new_base_line:
            print entry.chart_name
            entry.base_line_date = new_base_line
            entry.save()

if __name__ == "__main_read_iops_ec__":
    internal_chart_names = ["rand_read_4kb1vol1ssd_durable_volume_ec_output_bandwidth",
                            "rand_read_4kb1vol1ssd_durable_volume_ec_output_iops",
                            "read_4kb1vol1ssd_durable_volume_ec_output_bandwidth",
                            "read_4kb1vol1ssd_durable_volume_ec_output_iops"]
    model_name = "BltVolumePerformance"
    fio_read_job_names = ["fio_ec_read_4gbps"]
    fio_rand_read_job_names = ["fio_ec_randread_4gbps"]

    for internal_chart_name in internal_chart_names:
        fio_job_names = []
        if "bandwidth" in internal_chart_name:
            chart_name = "Throughput"
            y1_axis_title = "MBps"
        else:
            chart_name = "IOPS"
            y1_axis_title = "ops"
        if chart_name == "Throughput":
            output_name = "output_read_throughput"
        else:
            output_name = "output_read_iops"
        if "rand_read" in internal_chart_name:
            fio_job_names = fio_rand_read_job_names
            operation = "randread"
        else:
            fio_job_names = fio_read_job_names
            operation = "read"

        data_sets = []
        name = "Samsung PM1725b (MZWLL1T6HAJQ)"
        for job_name in fio_job_names:
            one_data_set = {}
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_fio_job_name"] = job_name
            one_data_set["inputs"]["input_operation"] = operation
            one_data_set["name"] = name
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        positive = True
        base_line_date = datetime(year=2019, month=4, day=7, minute=0, hour=0, second=0)
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Ravi Hulle (ravi.hulle@fungible.com)",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date).save()
        mmt = MileStoneMarkers(metric_id=metric_id,
                               milestone_date=datetime(year=2018, month=9, day=16),
                               milestone_name="Tape-out")
        mmt.save()
    print "created throughput and iops charts for read and random read durable volume ec storage"

if __name__ == "__main_read_latency_ec__":
    internal_chart_names_dict = {"read_4kb1vol1ssd_durable_volume_ec_4_output_latency": "Latency",
                                 "rand_read_4kb1vol1ssd_durable_volume_ec_4_output_latency": "Latency"}
    model_name = "BltVolumePerformance"
    fio_read_job_names = ["fio_ec_read_4gbps"]
    fio_rand_read_job_names = ["fio_ec_randread_4gbps"]
    y1_axis_title = "usecs"
    output_read_names = ["output_read_avg_latency",
                         "output_read_99_latency", "output_read_99_99_latency"]

    for internal_chart_name in internal_chart_names_dict:
        chart_name = internal_chart_names_dict[internal_chart_name]
        if "rand_read" in internal_chart_name:
            fio_job_name = "fio_ec_randread_4gbps"
            operation = "randread"
        else:
            fio_job_name = "fio_ec_read_4gbps"
            operation = "read"
        output_names = output_read_names

        data_sets = []
        for output_name in output_names:
            if "avg_" in output_name:
                name = "avg"
            elif "99_99" in output_name:
                name = "99.99%"
            else:
                name = "99%"

            one_data_set = {}
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
            one_data_set["inputs"]["input_operation"] = operation
            one_data_set["name"] = name
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        positive = False
        base_line_date = datetime(year=2019, month=4, day=7, minute=0, hour=0, second=0)
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Ravi Hulle (ravi.hulle@fungible.com)",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date).save()
        mmt = MileStoneMarkers(metric_id=metric_id,
                               milestone_date=datetime(year=2018, month=9, day=16),
                               milestone_name="Tape-out")
        mmt.save()
    print "created latency charts for read and random read durable volume ec storage"

if __name__ == "__main_memset_datasets__":
    entries = MetricChart.objects.all()
    ml = MetricLib()
    input = {}
    input["input_operation"] = "memset"
    output = {}
    output["reference"] = -1
    output["expected"] = -1
    for entry in entries:
        if entry.chart_name == "DMA soak memcpy coherent (Below 4K)":
            below_4k_data_sets = json.loads(entry.data_sets)
        if entry.chart_name == "DMA soak memcpy coherent (4K-1MB)":
            k_1mb_data_sets = json.loads(entry.data_sets)
        if entry.chart_name == "DMA soak memcpy coherent (Above 1MB)":
            above_1mb_data_sets = json.loads(entry.data_sets)
    for entry in entries:
        if entry.chart_name == "DMA soak memset coherent (Below 4K)" or entry.chart_name == "DMA soak memset non coherent (Below 4K)":
            if "non coherent" in entry.chart_name:
                input["input_coherent"] = False
            else:
                input["input_coherent"] = True
            below_4k_data_sets = ml.set_inputs_data_sets(data_sets=below_4k_data_sets, **input)
            below_4k_data_sets = ml.set_outputs_data_sets(data_sets=below_4k_data_sets, **output)
            print json.dumps(below_4k_data_sets)
            ml.save_data_sets(data_sets=below_4k_data_sets, chart=entry)
        if entry.chart_name == "DMA soak memset coherent (4K-1MB)" or entry.chart_name == "DMA soak memset non coherent (4K-1MB)":
            if "non coherent" in entry.chart_name:
                input["input_coherent"] = False
            else:
                input["input_coherent"] = True
            k_1mb_data_sets = ml.set_inputs_data_sets(data_sets=k_1mb_data_sets, **input)
            k_1mb_data_sets = ml.set_outputs_data_sets(data_sets=k_1mb_data_sets, **output)
            print json.dumps(k_1mb_data_sets)
            ml.save_data_sets(data_sets=k_1mb_data_sets, chart=entry)
        if entry.chart_name == "DMA soak memset coherent (Above 1MB)" or entry.chart_name == "DMA soak memset non coherent (Above 1MB)":
            if "non coherent" in entry.chart_name:
                input["input_coherent"] = False
            else:
                input["input_coherent"] = True
            above_1mb_data_sets = ml.set_inputs_data_sets(data_sets=above_1mb_data_sets, **input)
            above_1mb_data_sets = ml.set_outputs_data_sets(data_sets=above_1mb_data_sets, **output)
            print json.dumps(above_1mb_data_sets)
            ml.save_data_sets(data_sets=above_1mb_data_sets, chart=entry)
            data_sets = json.loads(entry.data_sets)
            for data_set in data_sets:
                if data_set["name"] == "2048KB" or data_set["name"] == "4096KB":
                    ml.delete_data_set(metric_id=entry.metric_id, data_set=data_set)

if __name__ == "__main_juniper_networking__":
    flow_types = ["NU_VP_NU_FWD_NFCP", "NU_LE_VP_NU_FW"]
    model_name = "TeraMarkJuniperNetworkingPerformance"
    frame_size_names = {
        64: "64B",
        1500: "1500B",
        362.94: "IMIX"
    }
    outputs = ["output_throughput", "output_pps"]
    chart_names = ["Throughput", "Packets per sec"]
    for flow_type in flow_types:
        for output in outputs:
            data_sets = []
            for frame_size in frame_size_names:
                one_data_set = {}
                one_data_set["inputs"] = {}
                one_data_set["inputs"]["input_flow_type"] = flow_type
                one_data_set["inputs"]["input_number_flows"] = 128000000
                one_data_set["inputs"]["input_offloads"] = False
                one_data_set["inputs"]["input_protocol"] = "UDP"
                one_data_set["inputs"]["input_frame_size"] = frame_size
                one_data_set["name"] = frame_size_names[frame_size]
                one_data_set["output"] = {"name": output, 'min': 0, "max": -1, "expected": -1, "reference": -1}
                data_sets.append(one_data_set)
            metric_id = LastMetricId.get_next_id()
            positive = True
            internal_name = "juniper_" + flow_type + '_' + output
            if "throughput" in output:
                y1_axis_title = "Gbps"
                chart_name = "Throughput"
            else:
                y1_axis_title = "Mpps"
                chart_name = "Packets per sec"
            base_line_date = datetime(year=2019, month=4, day=10, minute=0, hour=0, second=0)
            MetricChart(chart_name=chart_name,
                        metric_id=metric_id,
                        internal_chart_name=internal_name,
                        data_sets=json.dumps(data_sets),
                        leaf=True,
                        description="TBD",
                        owner_info="Amit Surana (amit.surana@fungible.com)",
                        positive=positive,
                        y1_axis_title=y1_axis_title,
                        visualization_unit=y1_axis_title,
                        source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/networking/performance/test_performance_fwd_benchmark.py",
                        metric_model_name=model_name,
                        base_line_date=base_line_date).save()
            mmt = MileStoneMarkers(metric_id=metric_id,
                                   milestone_date=datetime(year=2018, month=9, day=16),
                                   milestone_name="Tape-out")
            mmt.save()
    print "chart creation for NU_VP_NU_FWD_NFCP throughput and pps is done"

if __name__ == "__main_juniper_networking__":
    flow_types = ["NU_VP_NU_FWD_NFCP", "NU_LE_VP_NU_FW"]
    model_name = "TeraMarkJuniperNetworkingPerformance"
    frame_size_names = {
        64: "64B",
        1500: "1500B",
        362.94: "IMIX"
    }
    outputs = ["output_latency_avg", "output_latency_min", "output_latency_max"]
    chart_names = ["Latency"]
    for flow_type in flow_types:
        data_sets = []
        for output in outputs:
            if "avg" in output:
                name = "avg"
            elif "min" in output:
                name = "min"
            else:
                name = "max"
            for frame_size in frame_size_names:
                one_data_set = {}
                one_data_set["inputs"] = {}
                one_data_set["inputs"]["input_flow_type"] = flow_type
                one_data_set["inputs"]["input_number_flows"] = 128000000
                one_data_set["inputs"]["input_offloads"] = False
                one_data_set["inputs"]["input_protocol"] = "UDP"
                one_data_set["inputs"]["input_frame_size"] = frame_size
                one_data_set["name"] = frame_size_names[frame_size] + "-" + name
                one_data_set["output"] = {"name": output, 'min': 0, "max": -1, "expected": -1, "reference": -1}
                data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        y1_axis_title = "usecs"
        chart_name = "Latency"
        positive = False
        internal_name = "juniper_" + flow_type + '_' + "output_latency_avg"
        base_line_date = datetime(year=2019, month=4, day=10, minute=0, hour=0, second=0)
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Amit Surana (amit.surana@fungible.com)",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/networking/performance/test_performance_fwd_benchmark.py",
                    metric_model_name=model_name,
                    base_line_date=base_line_date).save()
        mmt = MileStoneMarkers(metric_id=metric_id,
                               milestone_date=datetime(year=2018, month=9, day=16),
                               milestone_name="Tape-out")
        mmt.save()
    print "chart creation for NU_VP_NU_FWD_NFCP latency is done"

if __name__ == "__main_memset_BM__":
    entries = MetricChart.objects.all()
    ml = MetricLib()
    for entry in entries:
        if "memset" in entry.chart_name:
            print entry.chart_name
            data_sets = json.loads(entry.data_sets)
            input = {}
            input["input_buffer_memory"] = False
            data_sets = ml.set_inputs_data_sets(data_sets=data_sets, **input)
            ml.save_data_sets(data_sets=data_sets, chart=entry)
            print "added buffer memory"

    internal_chart_names = {"memset_buffer_memory_output_bandwidth_below_4k": "DMA soak memset BM (Below 4K)",
                            "memset_buffer_memory_output_bandwidth_4k_1mb": "DMA soak memset BM (4K-1MB)"}
    internal_frame_sizes = {
        "memset_buffer_memory_output_bandwidth_below_4k": ["64B", "128B", "256B", "512B", "1024B", "2048B"],
        "memset_buffer_memory_output_bandwidth_4k_1mb": ["4096B", "8192B", "16KB"]}
    for internal_chart_name in internal_chart_names:
        chart_name = internal_chart_names[internal_chart_name]
        model_name = "SoakDmaMemsetPerformance"
        metric_id = LastMetricId.get_next_id()
        y1_axis_title = "Gbps"
        positive = True
        base_line_date = datetime(year=2019, month=4, day=11, minute=0, hour=0, second=0)
        data_sets = []
        frame_sizes = internal_frame_sizes[internal_chart_name]
        output = "output_bandwidth"
        for frame_size in frame_sizes:
            one_data_set = {}
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_buffer_memory"] = True
            one_data_set["inputs"]["input_size"] = frame_size
            one_data_set["inputs"]["input_operation"] = "memset"
            one_data_set["name"] = frame_size
            one_data_set["output"] = {"name": output, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Bertrand Serlet (bertrand.serlet@fungible.com)",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    source="https://github.com/fungible-inc/FunOS/blob/4ed61d76485feb65fa6f801d994622737ec6dc9a/apps/soak_dma_memset.c",
                    metric_model_name=model_name,
                    base_line_date=base_line_date).save()
        mmt = MileStoneMarkers(metric_id=metric_id,
                               milestone_date=datetime(year=2018, month=9, day=16),
                               milestone_name="Tape-out")
        mmt.save()
    print "chart creation for BM DMA memset is done"

if __name__ == "__main_delete_network_model__":
    entries = NuTransitPerformance.objects.all().delete()
    print "Deletion Complete"

if __name__ == "__main_work_in_progress__":
    internal_chart_names = ["Networking", "Regex", "teramarks_customer_juniper"]
    ml = MetricLib()
    for internal_chart_name in internal_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        ml.set_work_in_progress(chart=chart, in_progress=True)

if __name__ == "__main_RCNVME__":
    operations = ["sequential_read", "sequential_write", "random_read", "random_write"]
    outputs = ["output_bandwidth", "output_iops", "output_latency_avg"]
    for operation in operations:
        for output in outputs:
            data_sets = []
            positive = True
            name = "SAMSUNG MZQLB1T9HAJR"
            if "bandwidth" in output:
                y1_axis_title = "Mbps"
                chart_name = "Throughput"
            elif "iops" in output:
                y1_axis_title = "ops"
                chart_name = "IOPS"
            else:
                y1_axis_title = "nsecs"
                chart_name = "Latency"
                positive = False
                name = "avg"
            internal_name = "rcnvme_" + operation + '_' + output
            if "sequential" in operation:
                dev_access = "sequential"
            else:
                dev_access = "random"
            if "read" in operation:
                io_type = "RCNVME_TEST_TYPE_RO"
            else:
                io_type = "RCNVME_TEST_TYPE_WO"
            base_line_date = datetime(year=2019, month=4, day=14, minute=0, hour=0, second=0)
            one_data_set = {}
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_io_type"] = io_type
            one_data_set["inputs"]["input_dev_access"] = dev_access
            one_data_set["name"] = name
            one_data_set["output"] = {"name": output, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)
            metric_id = LastMetricId.get_next_id()
            model_name = "TeraMarkRcnvmeReadWritePerformance"
            MetricChart(chart_name=chart_name,
                        metric_id=metric_id,
                        internal_chart_name=internal_name,
                        data_sets=json.dumps(data_sets),
                        leaf=True,
                        description="TBD",
                        owner_info="Raju Vasudevan (raju.vasudevan@fungible.com)",
                        source="https://github.com/fungible-inc/FunOS/blob/ad5f77ba0db25525eed4a3ac4822562b7ccf5d9c/apps/rcnvme_test.c",
                        work_in_progress=False,
                        positive=positive,
                        y1_axis_title=y1_axis_title,
                        visualization_unit=y1_axis_title,
                        metric_model_name=model_name,
                        base_line_date=base_line_date).save()
            mmt = MileStoneMarkers(metric_id=metric_id,
                                   milestone_date=datetime(year=2018, month=9, day=16),
                                   milestone_name="Tape-out")
            mmt.save()
    print "chart creation for RCNVME is done"

if __name__ == "__main_apple_rr_throughput__":
    internal_chart_names = ["apple_rand_read_4kb6vol6ssd_output_bandwidth",
                            "apple_rand_read_4kb6vol6ssd_output_iops"]
    model_name = "BltVolumePerformance"
    fio_read_job_names = ["fio_randread_stripe12"]

    for internal_chart_name in internal_chart_names:
        fio_job_names = []
        if "bandwidth" in internal_chart_name:
            chart_name = "Throughput"
            y1_axis_title = "MBps"
        else:
            chart_name = "IOPS"
            y1_axis_title = "ops"
        if chart_name == "Throughput":
            output_name = "output_read_throughput"
        else:
            output_name = "output_read_iops"
        fio_job_names = fio_read_job_names
        operation = "randread"

        data_sets = []
        name = "Samsung PM1725b"
        for job_name in fio_job_names:
            one_data_set = {}
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_fio_job_name"] = job_name
            one_data_set["inputs"]["input_operation"] = operation
            one_data_set["name"] = name
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        positive = True
        base_line_date = datetime(year=2019, month=4, day=14, minute=0, hour=0, second=0)
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Manu KS (manu.ks@fungible.com)",
                    source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/stripe_vol_fs_perf.py",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
        mmt = MileStoneMarkers(metric_id=metric_id,
                               milestone_date=datetime(year=2018, month=9, day=16),
                               milestone_name="Tape-out")
        mmt.save()
    print "created throughput charts for random read stripe volume"

if __name__ == "__main_apple_rr_latency__":
    internal_chart_names_dict = {"apple_rand_read_4kb6vol6ssd_output_latency": "Latency"}
    model_name = "BltVolumePerformance"
    fio_read_job_names = ["fio_randread_stripe12"]
    y1_axis_title = "usecs"
    output_read_names = ["output_read_avg_latency", "output_read_99_latency", "output_read_99_99_latency"]

    for internal_chart_name in internal_chart_names_dict:
        chart_name = internal_chart_names_dict[internal_chart_name]
        fio_job_name = "fio_randread_stripe12"
        output_names = output_read_names
        operation = "randread"

        data_sets = []
        for output_name in output_names:
            if "_avg_" in output_name:
                name = "avg"
            elif "_99_99_" in output_name:
                name = "99.99%"
            else:
                name = "99%"

            one_data_set = {}
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
            one_data_set["inputs"]["input_operation"] = operation
            one_data_set["name"] = name
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        positive = False
        base_line_date = datetime(year=2019, month=4, day=14, minute=0, hour=0, second=0)
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Manu KS (manu.ks@fungible.com)",
                    source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/stripe_vol_fs_perf.py",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
        mmt = MileStoneMarkers(metric_id=metric_id,
                               milestone_date=datetime(year=2018, month=9, day=16),
                               milestone_name="Tape-out")
        mmt.save()
    print "created latency charts for random read stripe volume"

if __name__ == "__main__network_revamped__":
    old_internal_names = ["HU_NU_NFCP_output_throughput", "HU_NU_NFCP_output_pps", "NU_HU_NFCP_output_throughput",
                          "NU_HU_NFCP_output_pps"]
    for old_name in old_internal_names:
        entry = MetricChart.objects.get(internal_chart_name=old_name)
        if "HU_NU" in old_name:
            if "throughput" in old_name:
                HU_NU_throughput_description = entry.description
            else:
                HU_NU_pps_description = entry.description
        else:
            if "throughput" in old_name:
                NU_HU_throughput_description = entry.description
            else:
                NU_HU_pps_description = entry.description

    internal_chart_names = ["HU_NU_NFCP_1TCP_offloads_disabled_output_throughput",
                            "HU_NU_NFCP_1TCP_offloads_disabled_output_pps",
                            "HU_NU_NFCP_8TCP_offloads_disabled_output_throughput",
                            "HU_NU_NFCP_8TCP_offloads_disabled_output_pps",
                            "NU_HU_NFCP_1TCP_offloads_disabled_output_throughput",
                            "NU_HU_NFCP_1TCP_offloads_disabled_output_pps",
                            "NU_HU_NFCP_8TCP_offloads_disabled_output_throughput",
                            "NU_HU_NFCP_8TCP_offloads_disabled_output_pps"]
    frame_sizes = [800, 1500]
    flow_types = ["HU_NU_NFCP", "NU_HU_NFCP"]
    for internal_chart_name in internal_chart_names:
        positive = True
        base_line_date = datetime(year=2019, month=1, day=26, minute=0, hour=0, second=0)
        model_name = "HuThroughputPerformance"
        if "throughput" in internal_chart_name:
            chart_name = "Throughput"
            y1_axis_title = "Gbps"
            output_name = "output_throughput"
        else:
            chart_name = "Packets per sec"
            y1_axis_title = "Mpps"
            output_name = "output_pps"
        # else:
        #     chart_name = "Latency"
        #     positive = False
        #     y1_axis_title = "usecs"
        #     output_name = "output_latency_avg"
        #     model_name = "HuLatencyPerformance"

        if "1TCP" in internal_chart_name:
            num_flows = 1
        else:
            num_flows = 8

        if "HU_NU_NFCP" in internal_chart_name:
            flow_type = "HU_NU_NFCP"
            output_name = output_name + "_h2n"
        else:
            flow_type = "NU_HU_NFCP"
            output_name = output_name + "_n2h"

        description = "TBD"
        if internal_chart_name == "HU_NU_NFCP_1TCP_offloads_disabled_output_throughput":
            description = HU_NU_throughput_description
        elif internal_chart_name == "HU_NU_NFCP_1TCP_offloads_disabled_output_pps":
            description = HU_NU_pps_description
        elif internal_chart_name == "NU_HU_NFCP_1TCP_offloads_disabled_output_throughput":
            description = NU_HU_throughput_description
        elif internal_chart_name == "NU_HU_NFCP_1TCP_offloads_disabled_output_pps":
            description = NU_HU_pps_description
        data_sets = []
        for frame_size in frame_sizes:
            name = str(frame_size) + "B"
            # if chart_name == "Latency":
            #     name = name + "-avg"
            one_data_set = {}
            one_data_set["name"] = name
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_flow_type"] = flow_type
            one_data_set["inputs"]["input_number_flows"] = num_flows
            one_data_set["inputs"]["input_protocol"] = "TCP"
            one_data_set["inputs"]["input_offloads"] = False
            one_data_set["inputs"]["input_frame_size"] = frame_size
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)

        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description=description,
                    owner_info="Zhuo (George) Liang (george.liang@fungible.com)",
                    source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/networking/funeth/performance.py",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
    print "created charts for the new networking teramarks"

if __name__ == "__main_removed_offloads__":
    internal_chart_names = ["HU_NU_NFCP_1TCP_offloads_disabled_output_throughput",
                            "HU_NU_NFCP_1TCP_offloads_disabled_output_pps",
                            "HU_NU_NFCP_8TCP_offloads_disabled_output_throughput",
                            "HU_NU_NFCP_8TCP_offloads_disabled_output_pps",
                            "NU_HU_NFCP_1TCP_offloads_disabled_output_throughput",
                            "NU_HU_NFCP_1TCP_offloads_disabled_output_pps",
                            "NU_HU_NFCP_8TCP_offloads_disabled_output_throughput",
                            "NU_HU_NFCP_8TCP_offloads_disabled_output_pps"]
    ml = MetricLib()
    for internal_chart_name in internal_chart_names:
        entry = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        ml.remove_attribute_from_data_sets(chart=entry, key="input_offloads")
    print "removed the input offloads from datasets"

if __name__ == "__main_fun_tcp__":
    internal_chart_names = ["funtcp_server_throughput_1tcp", "funtcp_server_throughput_4tcp"]
    frame_size = 1500
    flow_type = "FunTCP_Server_Throughput"
    for internal_chart_name in internal_chart_names:
        positive = True
        base_line_date = datetime(year=2019, month=4, day=18, minute=0, hour=0, second=0)
        model_name = "TeraMarkFunTcpThroughputPerformance"
        y1_axis_title = "Gbps"
        output_name = "output_throughput"
        if "1tcp" in internal_chart_name:
            chart_name = "1 TCP Flow(s)"
            num_flows = 1
        else:
            chart_name = "4 TCP Flow(s)"
            num_flows = 4

        description = "TBD"
        data_sets = []
        name = str(frame_size) + "B"
        # if chart_name == "Latency":
        #     name = name + "-avg"
        one_data_set = {}
        one_data_set["name"] = name
        one_data_set["inputs"] = {}
        one_data_set["inputs"]["input_flow_type"] = flow_type
        one_data_set["inputs"]["input_num_flows"] = num_flows
        one_data_set["inputs"]["input_frame_size"] = frame_size
        one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
        data_sets.append(one_data_set)

        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description=description,
                    owner_info="Onkar Sarmalkar (onkar.sarmalkar@fungible.com)",
                    source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/networking/tcp/performance.py",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
    print "created charts for the FunTCP networking teramarks"

if __name__ == "__main_ipsec_tunnel__":
    internal_chart_names = ["juniper_crypto_single_tunnel_output_throughput", "juniper_crypto_single_tunnel_output_pps",
                            "juniper_crypto_multi_tunnel_output_throughput", "juniper_crypto_multi_tunnel_output_pps"]
    model_name = "JuniperCryptoTunnelPerformance"
    input_algorithm = "AES_GCM"
    description = "TBD"
    positive = True
    base_line_date = datetime(year=2019, month=1, day=26, minute=0, hour=0, second=0)
    for internal_chart_name in internal_chart_names:
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
                    source="https://github.com/fungible-inc/FunOS/blob/5c090e8bbe9f6826c9bb1467f5e4642dadbd9d82/apps/cryptotest/crypto_dp_tunnel_perf.c",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
    print "created charts for the IPSEC juniper customer teramarks"

if __name__ == "__main_version_addition__":
    networking_models = ["HuThroughputPerformance", "HuLatencyPerformance", "TeraMarkFunTcpThroughputPerformance",
                         "NuTransitPerformance"]
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    for model in networking_models:
        metric_model = app_config.get_metric_models()[model]
        entries = metric_model.objects.all()
        for entry in entries:
            date_time = timezone.localtime(entry.input_date_time)
            date_time = str(date_time).split(":")
            completion_date = date_time[0] + ":" + date_time[1]
            version = entry.input_version
            add_jenkins_job_id_map(jenkins_job_id=0,
                                   fun_sdk_branch="",
                                   git_commit="",
                                   software_date=0,
                                   hardware_version="",
                                   completion_date=completion_date,
                                   build_properties="", lsf_job_id="",
                                   sdk_version=version)

if __name__ == "__main_add_half_load_latency__":
    internal_chart_names = ["juniper_NU_VP_NU_FWD_NFCP_output_throughput", "juniper_NU_VP_NU_FWD_NFCP_output_pps",
                            "juniper_NU_VP_NU_FWD_NFCP_output_latency_avg"]
    ml = MetricLib()
    for internal_chart_name in internal_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        if chart:
            data_sets = json.loads(chart.data_sets)
            input = {}
            input["input_half_load_latency"] = False
            data_sets = ml.set_inputs_data_sets(data_sets=data_sets, **input)
            ml.save_data_sets(data_sets=data_sets, chart=chart)
            print "added half load latency"

if __name__ == "__main_delete_27th data__":
    model = "TeraMarkJuniperNetworkingPerformance"
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    metric_model = app_config.get_metric_models()[model]
    entries = metric_model.objects.all()
    for entry in entries:
        # date_time = get_localized_time(entry.input_date_time)
        if entry.input_date_time.day >= 27:
            entry.delete()

if __name__ == "__main_changed_num_flows__":
    model_names = ["TeraMarkJuniperNetworkingPerformance", "NuTransitPerformance"]
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

if __name__ == "__main_12ssd_blt__":
    fio_job_names = ["fio_read_12blt", "fio_randread_12blt"]
    internal_chart_names = ["read_4kb12vol12ssd_nvmetcp_output_bandwidth",
                            "read_4kb12vol12ssd_nvmetcp_output_iops",
                            "rand_read_4kb12vol12ssd_nvmetcp_output_bandwidth",
                            "rand_read_4kb12vol12ssd_nvmetcp_output_iops"]
    model_name = "BltVolumePerformance"
    positive = True
    base_line_date = datetime(year=2019, month=4, day=29, minute=0, hour=0, second=0)
    owner = "Manu KS (manu.ks@fungible.com)"
    source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/12blt_fs_perf.py"

    for internal_chart_name in internal_chart_names:
        if "bandwidth" in internal_chart_name:
            chart_name = "Throughput"
            y1_axis_title = "MBps"
        else:
            chart_name = "IOPS"
            y1_axis_title = "ops"
        if chart_name == "Throughput":
            output_name = "output_read_throughput"
        else:
            output_name = "output_read_iops"

        if "rand_read" in internal_chart_name:
            operation = "randread"
            fio_job_name = "fio_randread_12blt"
        else:
            operation = "read"
            fio_job_name = "fio_read_12blt"

        data_sets = []
        name = "Samsung PM1725b"
        one_data_set = {}
        one_data_set["inputs"] = {}
        one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
        one_data_set["inputs"]["input_operation"] = operation
        one_data_set["name"] = name
        one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
        data_sets.append(one_data_set)

        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info=owner,
                    source=source,
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
    print "created throughput charts for blt volume with 12 ssds"

    internal_chart_names = ["read_4kb12vol12ssd_4_nvmetcp_output_latency",
                            "rand_read_4kb12vol12ssd_4_nvmetcp_output_latency"]
    y1_axis_title = "usecs"
    output_read_names = ["output_read_avg_latency", "output_read_99_latency", "output_read_99_99_latency"]
    chart_name = "Latency"
    positive = False

    for internal_chart_name in internal_chart_names:
        if "rand_read" in internal_chart_name:
            operation = "randread"
            fio_job_name = "fio_randread_12blt"
        else:
            operation = "read"
            fio_job_name = "fio_read_12blt"

        data_sets = []
        for output_name in output_read_names:
            if "_avg_" in output_name:
                name = "avg"
            elif "_99_99_" in output_name:
                name = "99.99%"
            else:
                name = "99%"

            one_data_set = {}
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
            one_data_set["inputs"]["input_operation"] = operation
            one_data_set["name"] = name
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)

        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info=owner,
                    source=source,
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
    print "created latency charts for blt volume 12 ssds"

if __name__ == "__main_memvol__":
    fio_job_names = ["fio_read_memvol_seq_read", "fio_randread_memvol_rand_read", "fio_write_memvol_seq_write",
                     "fio_randwrite_memvol_rand_write", "fio_readwrite_memvol_seq_read_write",
                     "fio_randrw_memvol_rand_read_write"]
    internal_chart_names = ["memvol_sequential_read_output_bandwidth",
                            "memvol_sequential_read_output_iops",
                            "memvol_random_read_output_bandwidth",
                            "memvol_random_read_output_iops", "memvol_sequential_write_output_bandwidth",
                            "memvol_sequential_write_output_iops", "memvol_random_write_output_bandwidth",
                            "memvol_random_write_output_iops", "memvol_seq_read_write_output_bandwidth",
                            "memvol_seq_read_write_output_iops",
                            "memvol_random_read_write_output_bandwidth", "memvol_random_read_write_output_iops"]
    model_name = "BltVolumePerformance"
    positive = True
    base_line_date = datetime(year=2019, month=4, day=27, minute=0, hour=0, second=0)
    owner = "Radhika Naik (radhika.naik@fungible.com)"
    source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/memvol_fs_perf_updated.py"

    for internal_chart_name in internal_chart_names:
        if "bandwidth" in internal_chart_name:
            chart_name = "Throughput"
            y1_axis_title = "MBps"
            if "seq_read_write" in internal_chart_name:
                operation = "readwrite"
                fio_job_name = "fio_readwrite_memvol_seq_read_write"
                output_names = ["output_read_throughput", "output_write_throughput"]
            elif "random_read_write" in internal_chart_name:
                operation = "randrw"
                fio_job_name = "fio_randrw_memvol_rand_read_write"
                output_names = ["output_read_throughput", "output_write_throughput"]
            elif "sequential_read" in internal_chart_name:
                operation = "read"
                fio_job_name = "fio_read_memvol_seq_read"
                output_names = ["output_read_throughput"]
            elif "random_read" in internal_chart_name:
                operation = "randread"
                fio_job_name = "fio_randread_memvol_rand_read"
                output_names = ["output_read_throughput"]
            elif "sequential_write" in internal_chart_name:
                operation = "write"
                fio_job_name = "fio_write_memvol_seq_write"
                output_names = ["output_write_throughput"]
            elif "random_write" in internal_chart_name:
                operation = "randwrite"
                fio_job_name = "fio_randwrite_memvol_rand_write"
                output_names = ["output_write_throughput"]
        else:
            chart_name = "IOPS"
            y1_axis_title = "ops"
            if "seq_read_write" in internal_chart_name:
                operation = "readwrite"
                fio_job_name = "fio_readwrite_memvol_seq_read_write"
                output_names = ["output_read_iops", "output_write_iops"]
            elif "random_read_write" in internal_chart_name:
                operation = "randrw"
                fio_job_name = "fio_randrw_memvol_rand_read_write"
                output_names = ["output_read_iops", "output_write_iops"]
            elif "sequential_read" in internal_chart_name:
                operation = "read"
                fio_job_name = "fio_read_memvol_seq_read"
                output_names = ["output_read_iops"]
            elif "random_read" in internal_chart_name:
                operation = "randread"
                fio_job_name = "fio_randread_memvol_rand_read"
                output_names = ["output_read_iops"]
            elif "sequential_write" in internal_chart_name:
                operation = "write"
                fio_job_name = "fio_write_memvol_seq_write"
                output_names = ["output_write_iops"]
            elif "random_write" in internal_chart_name:
                operation = "randwrite"
                fio_job_name = "fio_randwrite_memvol_rand_write"
                output_names = ["output_write_iops"]

        data_sets = []
        for output_name in output_names:
            if operation == "randrw":
                if "read" in output_name:
                    name = "randread"
                else:
                    name = "randwrite"
            elif operation == "readwrite":
                if "read" in output_name:
                    name = "read"
                else:
                    name = "write"
            else:
                name = operation
            one_data_set = {}
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
            one_data_set["inputs"]["input_operation"] = operation
            one_data_set["name"] = name
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)

        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info=owner,
                    source=source,
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
    print "created throughput and iops charts for memvol"

    internal_chart_names = ["memvol_sequential_read_output_latency_avg",
                            "memvol_random_read_output_latency_avg", "memvol_sequential_write_output_latency_avg",
                            "memvol_random_write_output_latency_avg",
                            "memvol_seq_read_write_output_latency_avg", "memvol_random_read_write_output_latency_avg"]
    y1_axis_title = "usecs"
    output_read_names = ["output_read_avg_latency", "output_read_99_latency", "output_read_99_99_latency"]
    output_write_names = ["output_write_avg_latency", "output_write_99_latency", "output_write_99_99_latency"]
    chart_name = "Latency"
    positive = False

    for internal_chart_name in internal_chart_names:
        if "seq_read_write" in internal_chart_name:
            operation = "readwrite"
            fio_job_name = "fio_readwrite_memvol_seq_read_write"
            output_names = output_read_names + output_write_names
        elif "random_read_write" in internal_chart_name:
            operation = "randrw"
            fio_job_name = "fio_randrw_memvol_rand_read_write"
            output_names = output_read_names + output_write_names
        elif "sequential_read" in internal_chart_name:
            operation = "read"
            fio_job_name = "fio_read_memvol_seq_read"
            output_names = output_read_names
        elif "random_read" in internal_chart_name:
            operation = "randread"
            fio_job_name = "fio_randread_memvol_rand_read"
            output_names = output_read_names
        elif "sequential_write" in internal_chart_name:
            operation = "write"
            fio_job_name = "fio_write_memvol_seq_write"
            output_names = output_write_names
        elif "random_write" in internal_chart_name:
            operation = "randwrite"
            fio_job_name = "fio_randwrite_memvol_rand_write"
            output_names = output_write_names

        data_sets = []
        for output_name in output_names:
            if "_avg_" in output_name:
                name = "avg"
            elif "_99_99_" in output_name:
                name = "99.99%"
            else:
                name = "99%"

            if operation == "randrw":
                if "read" in output_name:
                    name = "randread-" + name
                else:
                    name = "randwrite-" + name
            elif operation == "readwrite":
                if "read" in output_name:
                    name = "read-" + name
                else:
                    name = "write-" + name

            one_data_set = {}
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
            one_data_set["inputs"]["input_operation"] = operation
            one_data_set["name"] = name
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)

        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info=owner,
                    source=source,
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
    print "created latency charts for memvol"

if __name__ == "__main__half_load_charts__":
    internal_chart_names = ["juniper_NU_LE_VP_NU_FW_output_throughput", "juniper_NU_LE_VP_NU_FW_output_pps",
                            "juniper_NU_LE_VP_NU_FW_output_latency_avg"]
    ml = MetricLib()
    for internal_chart_name in internal_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        if chart:
            data_sets = json.loads(chart.data_sets)
            input = {}
            input["input_half_load_latency"] = False
            data_sets = ml.set_inputs_data_sets(data_sets=data_sets, **input)
            ml.save_data_sets(data_sets=data_sets, chart=chart)
            print "added half load latency"

    entry = MetricChart.objects.get(internal_chart_name="juniper_NU_LE_VP_NU_FW_output_latency_avg")
    if entry:
        data_sets = json.loads(entry.data_sets)
        input = {}
        input["input_half_load_latency"] = True
        data_sets = ml.set_inputs_data_sets(data_sets=data_sets, **input)
        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name='Latency - Half Load',
                    metric_id=metric_id,
                    internal_chart_name="juniper_NU_LE_VP_NU_FW_output_half_load_latency_avg",
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description=entry.description,
                    owner_info=entry.owner_info,
                    source=entry.source,
                    positive=False,
                    y1_axis_title='usecs',
                    visualization_unit='usecs',
                    metric_model_name=entry.metric_model_name,
                    base_line_date=entry.base_line_date,
                    work_in_progress=False).save()

    entry = MetricChart.objects.get(internal_chart_name="juniper_NU_VP_NU_FWD_NFCP_output_latency_avg")
    if entry:
        data_sets = json.loads(entry.data_sets)
        input = {}
        input["input_half_load_latency"] = True
        data_sets = ml.set_inputs_data_sets(data_sets=data_sets, **input)
        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name='Latency - Half Load',
                    metric_id=metric_id,
                    internal_chart_name="juniper_NU_VP_NU_FWD_NFCP_output_half_load_latency_avg",
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description=entry.description,
                    owner_info=entry.owner_info,
                    source=entry.source,
                    positive=False,
                    y1_axis_title='usecs',
                    visualization_unit='usecs',
                    metric_model_name=entry.metric_model_name,
                    base_line_date=entry.base_line_date,
                    work_in_progress=False).save()

if __name__ == "__main_us_to_usecs__":
    model = "TeraMarkJuniperNetworkingPerformance"
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    metric_model = app_config.get_metric_models()[model]
    entries = metric_model.objects.all()
    for entry in entries:
        if entry.output_latency_avg_unit == "us":
            print entry
            entry.output_latency_avg_unit = "usecs"
            entry.output_latency_max_unit = "usecs"
            entry.output_latency_min_unit = "usecs"
            entry.output_jitter_min_unit = "usecs"
            entry.output_jitter_max_unit = "usecs"
            entry.output_jitter_avg_unit = "usecs"
            entry.save()

if __name__ == "__main_fix_units__":
    model = "TeraMarkJuniperNetworkingPerformance"
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    metric_model = app_config.get_metric_models()[model]
    entries = metric_model.objects.all()
    for entry in entries:
        if entry.input_flow_type == "NU_VP_NU_FWD_NFCP" and entry.input_date_time.day == 2 and entry.input_date_time.month == 5 and entry.input_date_time.year == 2019:
            print entry
            entry.output_throughput_unit = "Gbps"
            entry.output_pps_unit = "Mpps"
            entry.save()

if __name__ == "__main_rcnvme_12drives__":
    operations = ["sequential_read", "sequential_write", "random_read", "random_write"]
    outputs = ["output_bandwidth", "output_iops", "output_latency_avg"]
    for operation in operations:
        for output in outputs:
            data_sets = []
            positive = True
            if "bandwidth" in output:
                y1_axis_title = "Mbps"
                chart_name = "Throughput"
                name = "throughput"
            elif "iops" in output:
                y1_axis_title = "ops"
                chart_name = "IOPS"
                name = "iops"
            else:
                y1_axis_title = "nsecs"
                chart_name = "Latency"
                positive = False
                name = "avg"
            internal_name = "rcnvme_12_" + operation + '_' + output
            if "sequential" in operation:
                dev_access = "sequential"
            else:
                dev_access = "random"
            if "read" in operation:
                io_type = "RCNVME_TEST_TYPE_RO"
            else:
                io_type = "RCNVME_TEST_TYPE_WO"
            base_line_date = datetime(year=2019, month=4, day=14, minute=0, hour=0, second=0)
            one_data_set = {}
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_io_type"] = io_type
            one_data_set["inputs"]["input_dev_access"] = dev_access
            one_data_set["name"] = name
            one_data_set["output"] = {"name": output, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)
            metric_id = LastMetricId.get_next_id()
            model_name = "TeraMarkRcnvmeReadWriteAllPerformance"
            MetricChart(chart_name=chart_name,
                        metric_id=metric_id,
                        internal_chart_name=internal_name,
                        data_sets=json.dumps(data_sets),
                        leaf=True,
                        description="TBD",
                        owner_info="Raju Vasudevan (raju.vasudevan@fungible.com)",
                        source="https://github.com/fungible-inc/FunOS/blob/ad5f77ba0db25525eed4a3ac4822562b7ccf5d9c/apps/rcnvme_test.c",
                        work_in_progress=False,
                        positive=positive,
                        y1_axis_title=y1_axis_title,
                        visualization_unit=y1_axis_title,
                        metric_model_name=model_name,
                        base_line_date=base_line_date).save()
    print "chart creation for RCNVME 12 drives is done"

if __name__ == "__main_inspur_charts__":
    model_name = "BltVolumePerformance"
    base_line_date = datetime(year=2019, month=5, day=2, minute=0, hour=0, second=0)
    owner = "Ravi Hulle (ravi.hulle@fungible.com)"
    source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/ec_inspur_fs_teramark.py"
    outputs = ["output_bandwidth", "output_iops", "output_latency"]
    internal_chart_names = ["inspur_rand_read_write_8k_block_output_bandwidth",
                            "inspur_rand_read_write_8k_block_output_latency",
                            "inspur_rand_read_write_8k_block_output_iops"]
    fio_job_name = "inspur_8k_random_read_write_vdbench"
    for internal_chart_name in internal_chart_names:
        data_sets = []
        positive = True
        if "bandwidth" in internal_chart_name:
            y1_axis_title = "MBps"
            chart_name = "Throughput"
            output_names = ["output_read_throughput", "output_write_throughput"]
        elif "iops" in internal_chart_name:
            y1_axis_title = "ops"
            chart_name = "IOPS"
            output_names = ["output_read_iops", "output_write_iops"]
        else:
            y1_axis_title = "usecs"
            chart_name = "Latency"
            positive = False
            output_names = ["output_read_avg_latency", "output_write_avg_latency"]
        for output_name in output_names:
            if "read" in output_name:
                name = "read"
            else:
                name = "write"
            if "latency" in output_name:
                name += "-avg"
            one_data_set = {}
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
            one_data_set["name"] = name
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info=owner,
                    source=source,
                    work_in_progress=False,
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date).save()
    print "chart creation for inspur single f1 is done"

if __name__ == "__main_HBM__":
    internal_chart_names = ["juniper_NU_VP_NU_FWD_NFCP_output_throughput", "juniper_NU_VP_NU_FWD_NFCP_output_pps",
                            "juniper_NU_VP_NU_FWD_NFCP_output_latency_avg",
                            "juniper_NU_VP_NU_FWD_NFCP_output_half_load_latency_avg",
                            "juniper_NU_LE_VP_NU_FW_output_throughput", "juniper_NU_LE_VP_NU_FW_output_pps",
                            "juniper_NU_LE_VP_NU_FW_output_latency_avg",
                            "juniper_NU_LE_VP_NU_FW_output_half_load_latency_avg"]
    ml = MetricLib()
    for internal_chart_name in internal_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        if chart:
            data_sets = json.loads(chart.data_sets)
            input = {}
            input["input_memory"] = "HBM"
            data_sets = ml.set_inputs_data_sets(data_sets=data_sets, **input)
            ml.save_data_sets(data_sets=data_sets, chart=chart)
            print "added HBM memory {}".format(chart.chart_name)

if __name__ == "__main_opeartion_lookups__":
    internal_chart_names = ["HT HBM non-coherent - FP HBM non-coherent", "HT HBM coherent - FP HBM coherent",
                            "HT DDR non-coherent - FP DDR non-coherent", "HT DDR coherent - FP DDR coherent",
                            "TCAM"]
    ml = MetricLib()
    for internal_chart_name in internal_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        if chart:
            data_sets = json.loads(chart.data_sets)
            input = {}
            input["input_operation"] = "lookups"
            data_sets = ml.set_inputs_data_sets(data_sets=data_sets, **input)
            ml.save_data_sets(data_sets=data_sets, chart=chart)
            print "added lookups operation {}".format(chart.chart_name)

if __name__ == "__main_unit_fix__":
    model = "TeraMarkJuniperNetworkingPerformance"
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    metric_model = app_config.get_metric_models()[model]
    entries = metric_model.objects.all()
    for entry in entries:
        # date_time = get_localized_time(entry.input_date_time)
        if entry.input_date_time.day == 5 and entry.input_date_time.year == 2019 and entry.input_date_time.month == 5:
            print entry
            entry.output_throughput_unit = "Mbps"
            entry.output_pps_unit = "pps"
            entry.save()

if __name__ == "__main_created_DDR_FW__":
    model = "TeraMarkJuniperNetworkingPerformance"
    ml = MetricLib()
    entries = MetricChart.objects.filter(metric_model_name=model)
    for entry in entries:
        if "NU_LE_VP_NU_FW" in entry.internal_chart_name:
            print entry
            data_sets = json.loads(entry.data_sets)
            input = {}
            input["input_memory"] = "DDR"
            data_sets = ml.set_inputs_data_sets(data_sets=data_sets, **input)
            base_line_date = datetime(year=2019, month=5, day=5, minute=0, hour=0, second=0)
            metric_id = LastMetricId.get_next_id()
            index = entry.internal_chart_name.find('output')
            internal_name = entry.internal_chart_name[:index] + 'DDR_' + entry.internal_chart_name[index:]
            MetricChart(chart_name=entry.chart_name,
                        metric_id=metric_id,
                        internal_chart_name=internal_name,
                        data_sets=json.dumps(data_sets),
                        leaf=True,
                        description=entry.description,
                        owner_info=entry.owner_info,
                        positive=entry.positive,
                        y1_axis_title=entry.y1_axis_title,
                        visualization_unit=entry.visualization_unit,
                        source=entry.source,
                        metric_model_name=entry.metric_model_name,
                        base_line_date=base_line_date).save()
    print "added charts for DDR flow based firewall"

if __name__ == "__main_num_hosts__":
    model_name = "HuThroughputPerformance"
    charts = MetricChart.objects.filter(metric_model_name=model_name)
    ml = MetricLib()
    for chart in charts:
        data_sets = json.loads(chart.data_sets)
        input = {}
        input["input_num_hosts"] = 1
        data_sets = ml.set_inputs_data_sets(data_sets=data_sets, **input)
        ml.save_data_sets(data_sets=data_sets, chart=chart)
        print "added number of hosts field for {}".format(chart.chart_name)

if __name__ == "__main__durable_ec_comp__":
    internal_chart_names = ["read_4kb1vol12ssd_durable_volume_ec_output_bandwidth",
                            "read_4kb1vol12ssd_durable_volume_ec_output_iops",
                            "read_4kb1vol12ssd_durable_volume_ec_4_output_latency",
                            "rand_read_4kb1vol12ssd_durable_volume_ec_output_bandwidth",
                            "rand_read_4kb1vol12ssd_durable_volume_ec_output_iops",
                            "rand_read_4kb1vol12ssd_durable_volume_ec_4_output_latency"]
    model_name = "BltVolumePerformance"
    fio_read_job_names = ["ec_fio_25G_read_1", "ec_fio_25G_read_50", "ec_fio_25G_read_80"]
    fio_rand_read_job_names = ["ec_fio_25G_randread_1", "ec_fio_25G_randread_50", "ec_fio_25G_randread_80"]

    for internal_chart_name in internal_chart_names:
        fio_job_names = []
        positive = True
        if "bandwidth" in internal_chart_name:
            chart_name = "Throughput"
            y1_axis_title = "MBps"
        elif "iops" in internal_chart_name:
            chart_name = "IOPS"
            y1_axis_title = "ops"
        else:
            chart_name = "Latency"
            y1_axis_title = "usecs"

        if chart_name == "Throughput":
            output_name = "output_read_throughput"
        elif chart_name == "IOPS":
            output_name = "output_read_iops"
        else:
            output_name = "output_read_avg_latency"
            positive = False
        if "rand_read" in internal_chart_name:
            fio_job_names = fio_rand_read_job_names
            operation = "randread"
        else:
            fio_job_names = fio_read_job_names
            operation = "read"

        data_sets = []
        for job_name in fio_job_names:
            if "80" in job_name:
                name = "80%"
            elif "50" in job_name:
                name = "50%"
            else:
                name = "1%"
            if chart_name == "Latency":
                name += "-avg"
            one_data_set = {}
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_fio_job_name"] = job_name
            one_data_set["inputs"]["input_operation"] = operation
            one_data_set["name"] = name
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        base_line_date = datetime(year=2019, month=5, day=5, minute=0, hour=0, second=0)
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Aamir Shaikh (aamir.shaikh@fungible.com)",
                    source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/ec_volume_fs_comp_perf.py",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
        mmt = MileStoneMarkers(metric_id=metric_id,
                               milestone_date=datetime(year=2018, month=9, day=16),
                               milestone_name="Tape-out")
        mmt.save()
    print "created throughput, iops and latency charts for 12 ssd read and random read durable volume ec storage"

if __name__ == "__main_juniper_tls__":
    internal_chart_names = ["juniper_tls_output_throughput", "juniper_tls_output_pps"]
    chart_name = "Throughput"
    model_name = "JuniperTlsTunnelPerformance"
    num_tunnels = [1, 32, 64]
    base_line_date = datetime(year=2019, month=5, day=5, minute=0, hour=0, second=0)
    for internal_chart_name in internal_chart_names:
        if "throughput" in internal_chart_name:
            chart_name = "Throughput"
            output_name = "output_throughput"
            y1_axis_title = "Gbps"
        else:
            chart_name = "Packets per sec"
            output_name = "output_packets_per_sec"
            y1_axis_title = "Mpps"

        data_sets = []
        for num_tunnel in num_tunnels:
            name = str(num_tunnel) + "tunnel(s)"
            one_data_set = {}
            one_data_set["name"] = name
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_num_tunnels"] = num_tunnel
            one_data_set["inputs"]["input_algorithm"] = "AES_GCM"
            one_data_set["inputs"]["input_pkt_size"] = 356
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)

        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Fabrice Ferino (fabrice.ferino@fungible.com)",
                    source="https://github.com/fungible-inc/FunOS/blob/master/apps/tls_dp_tunnel_perf.c",
                    positive=True,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
    print "created charts for the TLS juniper customer teramarks"

if __name__ == "__main_memcpy_threshold__":
    internal_chart_name = "memcpy_threshold"
    model_name = "SoakDmaMemcpyThresholdPerformance"
    chart_name = "DMA memcpy vs. VP memcpy"
    y1_axis_title = "KB"
    base_line_date = datetime(year=2019, month=5, day=5, minute=0, hour=0, second=0)
    data_sets = []
    one_data_set = {}
    one_data_set["name"] = "threshold"
    one_data_set["inputs"] = {}
    one_data_set["output"] = {"name": "output_threshold", 'min': 0, "max": -1, "expected": 4, "reference": -1}
    data_sets.append(one_data_set)
    metric_id = LastMetricId.get_next_id()
    MetricChart(chart_name=chart_name,
                metric_id=metric_id,
                internal_chart_name=internal_chart_name,
                data_sets=json.dumps(data_sets),
                leaf=True,
                description="VP-based memcpy is faster for small sizes and DMA-based memcpy wins for large sizes. This metric defines the threshold above which DMA memcpy always wins.",
                owner_info="Bertrand Serlet (bertrand.serlet@fungible.com)",
                source="https://github.com/fungible-inc/FunOS/blob/master/apps/misc_app.c",
                positive=False,
                y1_axis_title=y1_axis_title,
                visualization_unit=y1_axis_title,
                metric_model_name=model_name,
                base_line_date=base_line_date,
                work_in_progress=False).save()

if __name__ == "__main_2hosts__":
    internal_chart_names = ["HU_NU_NFCP_8TCP_offloads_disabled_output_throughput",
                            "HU_NU_NFCP_8TCP_offloads_disabled_output_pps",
                            "NU_HU_NFCP_8TCP_offloads_disabled_output_throughput",
                            "NU_HU_NFCP_8TCP_offloads_disabled_output_pps"]
    for internal_chart_name in internal_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        if chart:
            index = chart.internal_chart_name.find('output')
            internal_name = chart.internal_chart_name[:index] + '2hosts_' + chart.internal_chart_name[index:]
            if "HU_NU" in internal_chart_name:
                flow_type = "HU_NU_NFCP"
                output_name = chart.internal_chart_name[index:] + '_h2n'
            else:
                flow_type = "NU_HU_NFCP"
                output_name = chart.internal_chart_name[index:] + '_n2h'
            data_sets = []
            one_data_set = {}
            one_data_set["name"] = "1500B"
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_number_flows"] = 8
            one_data_set["inputs"]["input_flow_type"] = flow_type
            one_data_set["inputs"]["input_frame_size"] = 1500
            one_data_set["inputs"]["input_protocol"] = "TCP"
            one_data_set["inputs"]["input_num_hosts"] = 2
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)

            metric_id = LastMetricId.get_next_id()
            MetricChart(chart_name=chart.chart_name,
                        metric_id=metric_id,
                        internal_chart_name=internal_name,
                        data_sets=json.dumps(data_sets),
                        leaf=True,
                        description=chart.description,
                        owner_info=chart.owner_info,
                        source=chart.source,
                        positive=True,
                        y1_axis_title=chart.y1_axis_title,
                        visualization_unit=chart.y1_axis_title,
                        metric_model_name=chart.metric_model_name,
                        base_line_date=chart.base_line_date,
                        work_in_progress=False).save()
    print "added 2hosts charts"


def set_internal_name(metrics):
    chart = MetricChart.objects.get(internal_chart_name=metrics["name"])
    metrics["name"] += "_S1"
    if chart.leaf:
        data_sets = json.loads(chart.data_sets)
        input = {}
        input["input_platform"] = FunPlatform.S1
        data_sets = ml.set_inputs_data_sets(data_sets=data_sets, **input)
        ml.clone_chart(old_chart=chart, internal_chart_name=metrics["name"], data_sets=data_sets)
    else:
        ml.clone_chart(old_chart=chart, internal_chart_name=metrics["name"], data_sets=json.loads(chart.data_sets))
        for child in metrics["children"]:
            set_internal_name(child)
    return metrics


if __name__ == "__main_S1__":
    charts = MetricChart.objects.all()
    for chart in charts:
        if chart.leaf:
            data_sets = json.loads(chart.data_sets)
            input = {}
            input["input_platform"] = FunPlatform.F1
            data_sets = ml.set_inputs_data_sets(data_sets=data_sets, **input)
            ml.save_data_sets(data_sets=data_sets, chart=chart)
            print "added platform for {}".format(chart.chart_name)
    with open(METRICS_BASE_DATA_FILE, "r") as f:
        metrics = json.load(f)
        for metric in metrics:
            if metric["label"] == "F1":
                f1_metrics = metric["children"]
                for f1_metric in f1_metrics:
                    if f1_metric["label"] == "FunOS":
                        funos_metrics = f1_metric
                        break
        result = set_internal_name(funos_metrics)
        print json.dumps(result)

if __name__ == "__main_delete__":
    model = "HuThroughputPerformance"
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    metric_model = app_config.get_metric_models()[model]
    entries = metric_model.objects.filter(input_flow_type="HU_HU_NFCP")
    print len(entries)
    entries.delete()
    model = "HuLatencyPerformance"
    app_config = apps.get_app_config(app_label=MAIN_WEB_APP)
    metric_model = app_config.get_metric_models()[model]
    entries = metric_model.objects.filter(input_flow_type="HU_HU_NFCP")
    print len(entries)
    entries.delete()
    print "got entries"

if __name__ == "__main_HU_HU__":
    internal_chart_names = ["HU_HU_NFCP_8TCP_offloads_disabled_output_throughput",
                            "HU_HU_NFCP_8TCP_offloads_disabled_output_pps",
                            "HU_HU_NFCP_1TCP_offloads_disabled_output_throughput",
                            "HU_HU_NFCP_1TCP_offloads_disabled_output_pps"]
    copy_from = ["NU_HU_NFCP_8TCP_offloads_disabled_2hosts_output_throughput",
                 "NU_HU_NFCP_8TCP_offloads_disabled_2hosts_output_pps"]
    flow_type = "HU_HU_NFCP"
    frame_size = 1500

    for internal_chart_name in internal_chart_names:
        if "throughput" in internal_chart_name:
            output_name = "output_throughput_h2h"
            chart_name = "Throughput"
            copy_from = "NU_HU_NFCP_8TCP_offloads_disabled_2hosts_output_throughput"
        else:
            output_name = "output_pps_h2h"
            chart_name = "Packets per sec"
            copy_from = "NU_HU_NFCP_8TCP_offloads_disabled_2hosts_output_pps"
        chart = MetricChart.objects.get(internal_chart_name=copy_from)

        if "8TCP" in internal_chart_name:
            num_flows = 8
        else:
            num_flows = 1

        data_sets = json.loads(chart.data_sets)
        input = {}
        input["input_flow_type"] = "HU_HU_NFCP"
        input["input_number_flows"] = num_flows
        input["input_num_hosts"] = 1
        data_sets = ml.set_inputs_data_sets(data_sets=data_sets, **input)
        data_sets[0]["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart.chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description=chart.description,
                    owner_info=chart.owner_info,
                    source=chart.source,
                    positive=True,
                    y1_axis_title=chart.y1_axis_title,
                    visualization_unit=chart.y1_axis_title,
                    metric_model_name=chart.metric_model_name,
                    base_line_date=chart.base_line_date,
                    work_in_progress=False).save()
    print "Added new HU HU NFCP charts"

if __name__ == "__main_apple__":
    internal_chart_names = ["apple_rand_read_srsw_tcp_output_bandwidth",
                            "apple_rand_read_srsw_tcp_output_iops"]
    model_name = "BltVolumePerformance"
    base_line_date = datetime(year=2019, month=5, day=10, minute=0, hour=0, second=0)

    for internal_chart_name in internal_chart_names:
        if "bandwidth" in internal_chart_name:
            chart_name = "Throughput"
            y1_axis_title = "MBps"
            output_name = "output_read_throughput"
            name = "throughput"
        else:
            chart_name = "IOPS"
            y1_axis_title = "ops"
            output_name = "output_read_iops"
            name = "iops"
        operation = "randread"

        data_sets = []
        one_data_set = {}
        one_data_set["inputs"] = {}
        one_data_set["inputs"]["input_fio_job_name"] = "fio_randread_apple_single_tcp"
        one_data_set["inputs"]["input_platform"] = "F1"
        one_data_set["inputs"]["input_operation"] = operation
        one_data_set["name"] = name
        one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
        data_sets.append(one_data_set)
        metric_id = LastMetricId.get_next_id()
        positive = True
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Manu KS (manu.ks@fungible.com)",
                    source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/apple_tcp_fs_perf.py",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
    print "added apple charts"
    internal_name = "apple_rand_read_4kb6vol6ssd_output_latency"
    chart = MetricChart.objects.get(internal_chart_name=internal_name)
    data_sets = json.loads(chart.data_sets)
    for data_set in data_sets:
        data_set["inputs"]["input_fio_job_name"] = "fio_randread_apple_single_tcp"
        data_set["output"]["min"] = 0
        data_set["output"]["max"] = -1
        data_set["output"]["expected"] = -1
        data_set["output"]["reference"] = -1
    metric_id = LastMetricId.get_next_id()
    MetricChart(chart_name=chart.chart_name,
                metric_id=metric_id,
                internal_chart_name="apple_rand_read_srsw_tcp_output_latency",
                data_sets=json.dumps(data_sets),
                leaf=True,
                description="TBD",
                owner_info="Manu KS (manu.ks@fungible.com)",
                source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/apple_tcp_fs_perf.py",
                positive=False,
                y1_axis_title=chart.y1_axis_title,
                visualization_unit=chart.y1_axis_title,
                metric_model_name=model_name,
                base_line_date=base_line_date,
                work_in_progress=False).save()

if __name__ == "__main_tls_3264__":
    internal_chart_names = ["juniper_tls_32_output_throughput", "juniper_tls_32_output_pps",
                            "juniper_tls_64_output_throughput", "juniper_tls_64_output_pps"]
    model_name = "JuniperTlsTunnelPerformance"
    base_line_date = datetime(year=2019, month=5, day=5, minute=0, hour=0, second=0)
    for internal_chart_name in internal_chart_names:
        if "throughput" in internal_chart_name:
            chart_name = "Throughput"
            output_name = "output_throughput"
            y1_axis_title = "Gbps"
        else:
            chart_name = "Packets per sec"
            output_name = "output_packets_per_sec"
            y1_axis_title = "Mpps"
        if "32" in internal_chart_name:
            num_tunnel = 32
        else:
            num_tunnel = 64

        data_sets = []
        name = str(num_tunnel) + "tunnel(s)"
        one_data_set = {}
        one_data_set["name"] = name
        one_data_set["inputs"] = {}
        one_data_set["inputs"]["input_num_tunnels"] = num_tunnel
        one_data_set["inputs"]["input_algorithm"] = "AES_GCM"
        one_data_set["inputs"]["input_platform"] = "F1"
        one_data_set["inputs"]["input_pkt_size"] = 354
        one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
        data_sets.append(one_data_set)

        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description="TBD",
                    owner_info="Fabrice Ferino (fabrice.ferino@fungible.com)",
                    source="https://github.com/fungible-inc/FunOS/blob/master/apps/tls_dp_tunnel_perf.c",
                    positive=True,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
    print "created charts for the TLS 32 nad 64 tunnel juniper customer teramarks"

if __name__ == "__main_HU_latency__":
    internal_chart_names = ["NU_HU_NFCP_8TCP_offloads_disabled_output_latency",
                            "HU_NU_NFCP_8TCP_offloads_disabled_output_latency",
                            "HU_NU_NFCP_1TCP_offloads_disabled_output_latency",
                            "NU_HU_NFCP_1TCP_offloads_disabled_output_latency",
                            "HU_NU_NFCP_8TCP_offloads_disabled_2hosts_output_latency",
                            "NU_HU_NFCP_8TCP_offloads_disabled_2hosts_output_latency",
                            "HU_HU_NFCP_1TCP_offloads_disabled_output_latency",
                            "HU_HU_NFCP_8TCP_offloads_disabled_output_latency"]
    frame_size = 1500
    flow_types = ["HU_NU_NFCP", "NU_HU_NFCP"]
    base_line_date = datetime(year=2019, month=1, day=26, minute=0, hour=0, second=0)
    model_name = "HuLatencyPerformance"
    chart_name = "Latency"
    positive = False
    description = "TBD"
    y1_axis_title = "usecs"
    output_names = ["output_latency_min", "output_latency_P50", "output_latency_P90", "output_latency_P99"]
    for internal_chart_name in internal_chart_names:
        if "1TCP" in internal_chart_name:
            num_flows = 1
        else:
            num_flows = 8

        if "2hosts" in internal_chart_name:
            num_hosts = 2
        else:
            num_hosts = 1

        data_sets = []
        for output_name in output_names:
            if "HU_NU_NFCP" in internal_chart_name:
                flow_type = "HU_NU_NFCP"
                output_name = output_name + "_h2n"
            elif "NU_HU_NFCP" in internal_chart_name:
                flow_type = "NU_HU_NFCP"
                output_name = output_name + "_n2h"
            else:
                flow_type = "HU_HU_NFCP"
                output_name = output_name + "_h2h"
            name = str(frame_size) + "B"
            if "99" in output_name:
                name += '-99%'
            elif "90" in output_name:
                name += '-90%'
            elif "50" in output_name:
                name += '-50%'
            else:
                name += '-min'
            one_data_set = {}
            one_data_set["name"] = name
            one_data_set["inputs"] = {}
            one_data_set["inputs"]["input_flow_type"] = flow_type
            one_data_set["inputs"]["input_number_flows"] = num_flows
            one_data_set["inputs"]["input_num_hosts"] = num_hosts
            one_data_set["inputs"]["input_protocol"] = "TCP"
            one_data_set["inputs"]["input_platform"] = "F1"
            one_data_set["inputs"]["input_frame_size"] = frame_size
            one_data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1, "reference": -1}
            data_sets.append(one_data_set)

        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=chart_name,
                    metric_id=metric_id,
                    internal_chart_name=internal_chart_name,
                    data_sets=json.dumps(data_sets),
                    leaf=True,
                    description=description,
                    owner_info="Zhuo (George) Liang (george.liang@fungible.com)",
                    source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/networking/funeth/performance.py",
                    positive=positive,
                    y1_axis_title=y1_axis_title,
                    visualization_unit=y1_axis_title,
                    metric_model_name=model_name,
                    base_line_date=base_line_date,
                    work_in_progress=False).save()
    print "created latency charts for the networking teramarks"

if __name__ == "__main_raw_block_iod__":
    # fio_pcie_read_blt_1_iod_scaling,
    # fio_pcie_read_blt_4_iod_scaling,
    # fio_pcie_read_blt_8_iod_scaling,
    # fio_pcie_read_blt_16_iod_scaling,
    # fio_pcie_randread_blt_1_iod_scaling,
    # fio_pcie_randread_blt_4_iod_scaling,
    # fio_pcie_randread_blt_8_iod_scaling,
    # fio_pcie_randread_blt_16_iod_scaling,
    # fio_read_blt_1_iod_scaling,
    # fio_read_blt_4_iod_scaling,
    # fio_read_blt_8_iod_scaling,
    # fio_read_blt_16_iod_scaling,
    # fio_randread_blt_1_iod_scaling,
    # fio_randread_blt_4_iod_scaling,
    # fio_randread_blt_8_iod_scaling,
    # fio_randread_blt_16_iod_scaling,
    copy_from_pcie_read = ["read_4kb1vol1ssd_4_output_latency", "read_4kb1vol1ssd_output_iops"]
    copy_from_pcie_randread = ["rand_read_4kb1vol1ssd_4_output_latency", "rand_read_4kb1vol1ssd_output_iops"]
    copy_from_nvmetcp_read = ["read_4kb12vol12ssd_4_nvmetcp_output_latency", "read_4kb12vol12ssd_nvmetcp_output_iops"]
    copy_from_nvmetcp_randread = ["rand_read_4kb12vol12ssd_4_nvmetcp_output_latency",
                                  "rand_read_4kb12vol12ssd_nvmetcp_output_iops"]
    output_names = ["output_latency", "output_iops"]
    operations = ["read", "rand_read"]
    names = ["nvmetcp", "pcie"]
    qdepths = ["qd1", "qd4", "qd8", "qd16"]
    model_name = "BltVolumePerformance"
    base_line_date = datetime(year=2019, month=5, day=10, minute=0, hour=0, second=0)
    for name in names:
        for operation in operations:
            for output_name in output_names:
                if name == "nvmetcp":
                    source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/blt_fs_iodepth_scaling.py"
                    if operation == "rand_read":
                        job_names = ["fio_randread_blt_", "_iod_scaling"]
                        copy = copy_from_nvmetcp_randread
                    else:
                        job_names = ["fio_read_blt_", "_iod_scaling"]
                        copy = copy_from_nvmetcp_read
                else:
                    source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/blt_pcie_io_depth.py"
                    if operation == "rand_read":
                        job_names = ["fio_pcie_randread_blt_", "_iod_scaling"]
                        copy = copy_from_pcie_randread
                    else:
                        job_names = ["fio_pcie_read_blt_", "_iod_scaling"]
                        copy = copy_from_pcie_read

                if "iops" in output_name:
                    internal_chart_name = operation + "_" + "qd" + "_" + name + "_" + output_name
                    chart_name = "IOPS"
                    positive = True
                    y1_axis_title = "ops"
                    data_sets = []
                    for qdepth in qdepths:
                        if "16" in qdepth:
                            fio_job_name = job_names[0] + "16" + job_names[1]
                        elif "8" in qdepth:
                            fio_job_name = job_names[0] + "8" + job_names[1]
                        elif "4" in qdepth:
                            fio_job_name = job_names[0] + "4" + job_names[1]
                        else:
                            fio_job_name = job_names[0] + "1" + job_names[1]

                        if operation == "rand_read":
                            data_set_operation = "randread"
                        else:
                            data_set_operation = "read"

                        one_data_set = {}
                        one_data_set["name"] = qdepth
                        one_data_set["inputs"] = {}
                        one_data_set["inputs"]["input_platform"] = "F1"
                        one_data_set["inputs"]["input_operation"] = data_set_operation
                        one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
                        one_data_set["output"] = {"name": "output_read_iops", 'min': 0, "max": -1, "expected": -1,
                                                  "reference": -1}
                        data_sets.append(one_data_set)

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
                                work_in_progress=False).save()
                else:
                    for qdepth in qdepths:
                        if "16" in qdepth:
                            fio_job_name = job_names[0] + "16" + job_names[1]
                        elif "8" in qdepth:
                            fio_job_name = job_names[0] + "8" + job_names[1]
                        elif "4" in qdepth:
                            fio_job_name = job_names[0] + "4" + job_names[1]
                        else:
                            fio_job_name = job_names[0] + "1" + job_names[1]
                        chart_name = "Latency"
                        internal_chart_name = operation + "_" + qdepth + "_" + name + "_" + output_name
                        positive = False
                        y1_axis_title = "usecs"
                        for c in copy:
                            if "latency" in c:
                                copy_from = c

                        chart = MetricChart.objects.get(internal_chart_name=copy_from)
                        data_sets = json.loads(chart.data_sets)
                        for data_set in data_sets:
                            data_set["inputs"]["input_fio_job_name"] = fio_job_name
                            data_set["output"]["expected"] = -1
                            data_set["output"]["min"] = 0
                            data_set["output"]["max"] = -1
                            data_set["output"]["reference"] = -1

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
                                    work_in_progress=False).save()
    print "added charts for raw block different io depths"

if __name__ == "__main_durable_volume__":
    copy_rand_read = "rand_read_4kb1vol1ssd_durable_volume_ec_4_output_latency"
    copy_read = "read_4kb1vol1ssd_durable_volume_ec_4_output_latency"
    output_names = ["output_latency", "output_iops"]
    operations = ["read", "rand_read"]
    iodepths = [1, 8, 16, 32, 64]
    model_name = "BltVolumePerformance"
    base_line_date = datetime(year=2019, month=5, day=10, minute=0, hour=0, second=0)
    for operation in operations:
        for output_name in output_names:
            source = ""
            if operation == "rand_read":
                job_names = "ec_randread_iodepth_"
                copy = copy_rand_read
            else:
                job_names = "ec_read_iodepth_"
                copy = copy_read

            if "iops" in output_name:
                internal_chart_name = operation + "_iod_durable_volume_ec_" + output_name
                chart_name = "IOPS"
                positive = True
                y1_axis_title = "ops"
                data_sets = []
                for iodepth in iodepths:
                    fio_job_name = job_names + str(iodepth)
                    if operation == "rand_read":
                        data_set_operation = "randread"
                    else:
                        data_set_operation = "read"

                    one_data_set = {}
                    one_data_set["name"] = iodepth
                    one_data_set["inputs"] = {}
                    one_data_set["inputs"]["input_platform"] = "F1"
                    one_data_set["inputs"]["input_operation"] = data_set_operation
                    one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
                    one_data_set["output"] = {"name": "output_read_iops", 'min': 0, "max": -1, "expected": -1,
                                              "reference": -1}
                    data_sets.append(one_data_set)

                metric_id = LastMetricId.get_next_id()
                MetricChart(chart_name=chart_name,
                            metric_id=metric_id,
                            internal_chart_name=internal_chart_name,
                            data_sets=json.dumps(data_sets),
                            leaf=True,
                            description="TBD",
                            owner_info="Aamir Shaikh (aamir.shaikh@fungible.com)",
                            source=source,
                            positive=positive,
                            y1_axis_title=y1_axis_title,
                            visualization_unit=y1_axis_title,
                            metric_model_name=model_name,
                            base_line_date=base_line_date,
                            work_in_progress=False).save()
            else:
                for iodepth in iodepths:
                    fio_job_name = job_names + str(iodepth)
                    chart_name = "Latency"
                    internal_chart_name = operation + "_iod" + str(iodepth) + "_durable_volume_ec_" + output_name
                    positive = False
                    y1_axis_title = "usecs"

                    chart = MetricChart.objects.get(internal_chart_name=copy)
                    data_sets = json.loads(chart.data_sets)
                    for data_set in data_sets:
                        data_set["inputs"]["input_fio_job_name"] = fio_job_name
                        data_set["output"]["expected"] = -1
                        data_set["output"]["min"] = 0
                        data_set["output"]["max"] = -1
                        data_set["output"]["reference"] = -1

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
                                work_in_progress=False).save()
    print "added charts for durable volume different io depths"

if __name__ == "__main_inspur__":
    iops_chart = MetricChart.objects.get(internal_chart_name="inspur_rand_read_write_8k_block_output_iops")
    latency_chart = MetricChart.objects.get(internal_chart_name="inspur_rand_read_write_8k_block_output_latency")
    iodepths = [1, 8, 16, 32, 64]
    model_name = "BltVolumePerformance"
    job_name = "inspur_8k_random_read_write_"
    internal_names = ["inspur_rand_read_write_qd", "_8k_block_output_"]
    base_line_date = datetime(year=2019, month=5, day=10, minute=0, hour=0, second=0)
    names = ["iops", "latency"]
    for name in names:
        if name == "iops":
            chart = iops_chart
            chart_name = "IOPS"
        else:
            chart = latency_chart
            chart_name = "Latency"
        for iodepth in iodepths:
            internal_chart_name = internal_names[0] + str(iodepth) + internal_names[1] + name
            data_sets = json.loads(chart.data_sets)
            for data_set in data_sets:
                data_set["inputs"]["input_fio_job_name"] = job_name + str(iodepth)
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
                        visualization_unit=chart.visualization_unit,
                        metric_model_name=model_name,
                        base_line_date=base_line_date,
                        work_in_progress=False).save()
    print "added charts for Inspur different io depths"

if __name__ == "__main_8TCP__":
    chart = MetricChart.objects.get(internal_chart_name="funtcp_server_throughput_4tcp")
    data_sets = json.loads(chart.data_sets)
    internal_chart_name = "funtcp_server_throughput_8tcp"
    for data_set in data_sets:
        data_set["inputs"]["input_num_flows"] = 8
        data_set["output"]["expected"] = -1
        data_set["output"]["reference"] = -1
    chart_name = "8 TCP Flow(s)"
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
                visualization_unit=chart.visualization_unit,
                metric_model_name=chart.metric_model_name,
                base_line_date=chart.base_line_date,
                work_in_progress=False).save()
    print "added chart for 8 TCP Flow"
