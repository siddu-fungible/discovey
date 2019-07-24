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
    ml = MetricLib()
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
        if "children" in metrics:
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

if __name__ == "__main_3264raw__":
    # fio_pcie_read_blt_32_iod_scaling
    # fio_pcie_read_blt_64_iod_scaling
    # fio_pcie_randread_blt_32_iod_scaling
    # fio_pcie_randread_blt_64_iod_scaling
    copy_from_pcie_read = ["read_4kb1vol1ssd_4_output_latency", "read_4kb1vol1ssd_output_iops"]
    copy_from_pcie_randread = ["rand_read_4kb1vol1ssd_4_output_latency", "rand_read_4kb1vol1ssd_output_iops"]
    output_names = ["output_latency", "output_iops"]
    operations = ["read", "rand_read"]
    names = ["pcie"]
    qdepths = ["qd32", "qd64"]
    model_name = "BltVolumePerformance"
    base_line_date = datetime(year=2019, month=5, day=10, minute=0, hour=0, second=0)
    for name in names:
        for operation in operations:
            for output_name in output_names:
                source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/blt_pcie_io_depth.py"
                if operation == "rand_read":
                    job_names = ["fio_pcie_randread_blt_", "_iod_scaling"]
                    copy = copy_from_pcie_randread
                else:
                    job_names = ["fio_pcie_read_blt_", "_iod_scaling"]
                    copy = copy_from_pcie_read

                if "iops" in output_name:
                    internal_chart_name = operation + "_" + "qd" + "_" + name + "_" + output_name
                    chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
                    data_sets = json.loads(chart.data_sets)
                    for qdepth in qdepths:
                        if "32" in qdepth:
                            fio_job_name = job_names[0] + "32" + job_names[1]
                        else:
                            fio_job_name = job_names[0] + "64" + job_names[1]

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

                    ml.save_data_sets(data_sets=data_sets, chart=chart)
                else:
                    for qdepth in qdepths:
                        if "32" in qdepth:
                            fio_job_name = job_names[0] + "32" + job_names[1]
                        else:
                            fio_job_name = job_names[0] + "64" + job_names[1]
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
    print "added charts for raw block read and random read different io depths"

if __name__ == "__main_write_raw__":
    # fio_pcie_write_blt_1_iod_scaling
    # fio_pcie_write_blt_8_iod_scaling
    # fio_pcie_randwrite_blt_1_iod_scaling
    # fio_pcie_randwrite_blt_8_iod_scaling
    copy_from_pcie_read = ["read_4kb1vol1ssd_4_output_latency", "read_4kb1vol1ssd_output_iops"]
    copy_from_pcie_randread = ["rand_read_4kb1vol1ssd_4_output_latency", "rand_read_4kb1vol1ssd_output_iops"]
    output_names = ["output_latency", "output_iops"]
    operations = ["write", "rand_write"]
    names = ["pcie"]
    qdepths = ["qd1", "qd8"]
    model_name = "BltVolumePerformance"
    base_line_date = datetime(year=2019, month=5, day=10, minute=0, hour=0, second=0)
    for name in names:
        for operation in operations:
            for output_name in output_names:
                source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/blt_pcie_io_depth.py"
                if operation == "rand_write":
                    job_names = ["fio_pcie_randwrite_blt_", "_iod_scaling"]
                    copy = copy_from_pcie_randread
                    data_set_operation = "randwrite"
                else:
                    job_names = ["fio_pcie_write_blt_", "_iod_scaling"]
                    copy = copy_from_pcie_read
                    data_set_operation = "write"

                if "iops" in output_name:
                    internal_chart_name = operation + "_" + "qd" + "_" + name + "_" + output_name
                    chart_name = "IOPS"
                    positive = True
                    y1_axis_title = "ops"
                    data_sets = []
                    for qdepth in qdepths:
                        if "8" in qdepth:
                            fio_job_name = job_names[0] + "8" + job_names[1]
                        else:
                            fio_job_name = job_names[0] + "1" + job_names[1]

                        one_data_set = {}
                        one_data_set["name"] = qdepth
                        one_data_set["inputs"] = {}
                        one_data_set["inputs"]["input_platform"] = "F1"
                        one_data_set["inputs"]["input_operation"] = data_set_operation
                        one_data_set["inputs"]["input_fio_job_name"] = fio_job_name
                        one_data_set["output"] = {"name": "output_write_iops", 'min': 0, "max": -1, "expected": -1,
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
                        if "8" in qdepth:
                            fio_job_name = job_names[0] + "8" + job_names[1]
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
                            data_set["inputs"]["input_operation"] = data_set_operation
                            data_set["output"]["name"] = data_set["output"]["name"].replace("read", "write")
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
    print "added charts for raw block write and random write different io depths"

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
    internal_chart_names_compression = ["read_4kb1vol12ssd_durable_volume_ec_4_output_latency",
                                        "read_4kb1vol12ssd_durable_volume_ec_output_iops",
                                        "rand_read_4kb1vol12ssd_durable_volume_ec_4_output_latency",
                                        "rand_read_4kb1vol12ssd_durable_volume_ec_output_iops"]
    fio_job_names_randread = ["ec_nvme_tcp_comp_randread_1pctcomp_8", "ec_nvme_tcp_comp_randread_50pctcomp_8",
                              "ec_nvme_tcp_comp_randread_80pctcomp_8"]
    fio_job_names_read = ["ec_nvme_tcp_comp_read_1pctcomp_8", "ec_nvme_tcp_comp_read_50pctcomp_8",
                          "ec_nvme_tcp_comp_read_80pctcomp_8"]
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
                internal_chart_name = "HU_HU_FCP_" + str(num_flow) + "TCP_" + str(
                    num_host) + "H_offloads_enabled_" + output_name
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
                    one_data_set["output"] = {"name": data_set_output + output + "_h2h", 'min': 0, "max": -1,
                                              "expected": -1,
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

if __name__ == "__main_raw_block_nvmetcp__":
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
    internal_chart_names = ["voltest_lsv_1instances_blt_iops", "voltest_lsv_1instances_blt_bandwidth",
                            "voltest_lsv_4instances_blt_iops", "voltest_lsv_4instances_blt_bandwidth"]
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

if __name__ == "__main_inspur__":
    internal_chart_names = ["inspur_", "_read_write_", "_output_iops"]
    names = ["seq", "mixed", "oltp", "olap"]
    qdepths = ["qd1", "qd8", "qd16", "qd32", "qd64"]
    chart_name = "Latency"
    model_name = "BltVolumePerformance"
    base_line_date = datetime(year=2019, month=6, day=1, minute=0, hour=0, second=0)
    y1_axis_title = PerfUnit.UNIT_OPS
    fio_seq_job_names = ["inspur_1024k_sequential_read_write_1", "inspur_1024k_sequential_read_write_8",
                         "inspur_1024k_sequential_read_write_16", "inspur_1024k_sequential_read_write_32",
                         "inspur_1024k_sequential_read_write_64"]
    fio_mixed_job_names = ["inspur_mixed_random_read_write_1", "inspur_mixed_random_read_write_8",
                           "inspur_mixed_random_read_write_16", "inspur_mixed_random_read_write_32",
                           "inspur_mixed_random_read_write_64"]
    fio_oltp_job_names = ["inspur_oltp_model_read_write_2", "inspur_oltp_model_read_write_8",
                          "inspur_oltp_model_read_write_16", "inspur_oltp_model_read_write_32",
                          "inspur_oltp_model_read_write_64"]
    fio_olap_job_names = ["inspur_olap_model_read_write_2", "inspur_olap_model_read_write_8",
                          "inspur_olap_model_read_write_16", "inspur_olap_model_read_write_32",
                          "inspur_olap_model_read_write_64"]
    output_names = ["output_read_iops", "output_write_iops"]
    for name in names:
        if name == "seq":
            fio_job_names = fio_seq_job_names
        elif name == "mixed":
            fio_job_names = fio_mixed_job_names
        elif name == "oltp":
            fio_job_names = fio_oltp_job_names
        else:
            fio_job_names = fio_olap_job_names
        for fio_job_name in fio_job_names:
            if "_64" in fio_job_name:
                qdepth = "qd64"
            elif "_32" in fio_job_name:
                qdepth = "qd32"
            elif "_16" in fio_job_name:
                qdepth = "qd16"
            elif "_8" in fio_job_name:
                qdepth = "qd8"
            else:
                qdepth = "qd1"

            internal_chart_name = internal_chart_names[0] + name + internal_chart_names[1] + qdepth + internal_chart_names[2]
            data_sets = []
            for output_name in output_names:
                if "read" in output_name:
                    data_set_name = "read(1 vol)"
                else:
                    data_set_name = "write(1 vol)"
                one_data_set = {}
                one_data_set["name"] = data_set_name
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
                        owner_info="Ravi Hulle (ravi.hulle@fungible.com)",
                        source="https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/ec_inspur_fs_teramark.py",
                        positive=True,
                        y1_axis_title=y1_axis_title,
                        visualization_unit=y1_axis_title,
                        metric_model_name=model_name,
                        base_line_date=base_line_date,
                        work_in_progress=False,
                        platform=FunPlatform.F1).save()
    print "added charts for inspur containers"

if __name__ == "__main_latency_under_load__":
    model_name = "HuLatencyUnderLoadPerformance"
    entries = MetricChart.objects.all()
    for entry in entries:
        if entry.metric_model_name == "HuLatencyPerformance":
            print "adding clone for {}".format(entry.internal_chart_name)
            internal_chart_name = entry.internal_chart_name + "_under_load"
            data_sets = json.loads(entry.data_sets)
            for data_set in data_sets:
                index = data_set["output"]["name"].rfind('_')
                output_name = data_set["output"]["name"][:index] + '_uload' + data_set["output"]["name"][index:]
                data_set["output"] = {"name": output_name, 'min': 0, "max": -1, "expected": -1,
                                      "reference": -1, "unit": PerfUnit.UNIT_USECS}
            metric_id = LastMetricId.get_next_id()
            MetricChart(chart_name=entry.chart_name,
                        metric_id=metric_id,
                        internal_chart_name=internal_chart_name,
                        data_sets=json.dumps(data_sets),
                        leaf=True,
                        description=entry.description,
                        owner_info=entry.owner_info,
                        source=entry.source,
                        positive=entry.positive,
                        y1_axis_title=entry.y1_axis_title,
                        visualization_unit=entry.y1_axis_title,
                        metric_model_name=model_name,
                        base_line_date=entry.base_line_date,
                        work_in_progress=False,
                        platform=FunPlatform.F1).save()
    print "added charts for latency under load"

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

if __name__ == "__main__bmv_storage_local_ssd":
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

if __name__ == "__main_fio_job_name_fix__":
    fio_job_names = ["inspur_8k_random_read_write_iodepth_32_f1_6_vol_1",
                     "inspur_8k_random_read_write_iodepth_2_f1_6_vol_1",
                     "inspur_8k_random_read_write_iodepth_3_f1_6_vol_1", "inspur_8k_random_read_write_iodepth_4_f1_6_vol_1"]
    for fio_job_name in fio_job_names:
        entries = BltVolumePerformance.objects.filter(input_fio_job_name=fio_job_name)
        for entry in entries:
            print entry
            print fio_job_name
            if "_1_f1" in fio_job_name:
                entry.input_fio_job_name = entry.input_fio_job_name.replace("_1_f1", "_32_f1")
            elif "_2_f1" in fio_job_name:
                entry.input_fio_job_name = entry.input_fio_job_name.replace("_2_f1", "_64_f1")
            elif "_3_f1" in fio_job_name:
                entry.input_fio_job_name = entry.input_fio_job_name.replace("_3_f1", "_96_f1")
            elif "_4_f1" in fio_job_name:
                entry.input_fio_job_name = entry.input_fio_job_name.replace("_4_f1", "_128_f1")
            entry.save()
    print "changed fio job names for inpur 6 f1s"
    internal_chart_names = ["inspur_rand_read_write_qd1_6f1_8k_block_output_iops",
                            "inspur_rand_read_write_qd8_6f1_8k_block_output_iops",
                            "inspur_rand_read_write_qd16_6f1_8k_block_output_iops",
                            "inspur_rand_read_write_qd32_6f1_8k_block_output_iops",
                            "inspur_rand_read_write_qd64_6f1_8k_block_output_iops",
                            "inspur_rand_read_write_qd96_6f1_8k_block_output_iops",
                            "inspur_rand_read_write_qd128_6f1_8k_block_output_iops",
                            "inspur_rand_read_write_qd1_6f1_8k_block_output_latency",
                            "inspur_rand_read_write_qd8_6f1_8k_block_output_latency",
                            "inspur_rand_read_write_qd16_6f1_8k_block_output_latency",
                            "inspur_rand_read_write_qd32_6f1_8k_block_output_latency",
                            "inspur_rand_read_write_qd64_6f1_8k_block_output_latency",
                            "inspur_rand_read_write_qd96_6f1_8k_block_output_latency",
                            "inspur_rand_read_write_qd128_6f1_8k_block_output_latency"]
    for internal_chart_name in internal_chart_names:
        chart = MetricChart.objects.get(internal_chart_name=internal_chart_name)
        if chart:
            data_sets = json.loads(chart.data_sets)
            for data_set in data_sets:
                data_set["inputs"].pop("input_operation", None)
            if "qd32" in internal_chart_name or "qd64" in internal_chart_name or "qd96" in internal_chart_name or \
                    "qd128" in internal_chart_name:
                data_sets[:] = [data_set for data_set in data_sets if "6 F1s" in data_set["name"]]
            chart.data_sets = json.dumps(data_sets)
            chart.save()
    print "removed input operation from the filter"

if __name__ == "__main__inspur":
    entries = BltVolumePerformance.objects.filter(input_fio_job_name="inspur_8k_random_read_write_iodepth_1_f1_6_vol_1")
    for entry in entries:
        print entry
        entry.input_fio_job_name = entry.input_fio_job_name.replace("_1_f1", "_32_f1")
        entry.save()
    print "fixed missed 32 iodepth"


if __name__ == "__main__":

    # charts for inspur functional 871 time_taken
    internal_chart_name = "inspur_functional_871_single_disk_failure_time_taken"
    owner_info = "Ravi Hulle (ravi.hulle@fungible.com) "
    source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/review/review_ec_inspur" \
             "_single_drive_failure_with_rebuild.py"
    positive = False
    y1_axis_title = PerfUnit.UNIT_SECS
    platform = FunPlatform.F1
    model_name = "InspurSingleDiskFailurePerformance"
    description = "Copy a file, when there is no disk failure. Base file copy. Measure time to copy file<br>" \
                  "Copy file during disk/volume failure, Measure time to copy file<br>" \
                  "Copy file during failed disk/volume rebuild, Measure time to copy file<br>"
    chart_name = "Single disk failure with rebuild"
    one_data_set = {}
    data_sets = []

    inputs = {
        "input_platform": platform,
        "input_num_hosts": 1,
        "input_num_f1s": 1
    }

    output_names = OrderedDict([("output_base_file_copy_time", "base file copy time"),
                                ("output_copy_time_during_plex_fail", "time taken during plex fail"),
                                ("output_file_copy_time_during_rebuild", "time taken during rebuild"),
                                ("output_plex_rebuild_time", "plex rebuild time")])

    for output_name in output_names:
        output = {
            "name": output_name,
            "unit": PerfUnit.UNIT_SECS,
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

    # charts for inspur functional 875 (iops, latency, plex rebuild time)
    internal_chart_names = ["inspur_functional_875_iops", "inspur_functional_875_plex_rebuild_time",
                            "inspur_functional_875_latency"]
    owner_info = "Ravi Hulle (ravi.hulle@fungible.com)"
    source = "https://github.com/fungible-inc/Integration/blob/master/fun_test/scripts/storage/review/review_ec_inspur" \
             "_single_drive_failure_with_rebuild.py"
    platform = FunPlatform.F1
    model_name = "InspurDataReconstructionPerformance"

    for internal_chart_name in internal_chart_names:
        one_data_set = {}
        data_sets = []
        inputs = {
            "input_platform": platform,
            "input_num_hosts": 1,
            "input_block_size": "Mixed",
            "input_operation": "Combined"
        }
        if internal_chart_name == "inspur_functional_875_iops":
            chart_name = "Inspur functional 875 IOPS"
            y1_axis_title = PerfUnit.UNIT_OPS
            description = "TBD"
            output_names = OrderedDict([("output_write_iops", "write(1 vol)"),
                                        ("output_read_iops", "read(1 vol)")])
            positive = False
        elif internal_chart_name == "inspur_functional_875_plex_rebuild_time":
            chart_name = "Inspur functional 875 Plex rebuild time"
            y1_axis_title = PerfUnit.UNIT_SECS
            description = "TBD"
            output_names = OrderedDict([("output_plex_rebuild_time", "Plex rebuild time")])
            positive = False
        elif internal_chart_name == "inspur_functional_875_latency":
            chart_name = "Inspur functional 875 latency"
            y1_axis_title = PerfUnit.UNIT_USECS
            description = "TBD"
            output_names = OrderedDict([("output_write_avg_latency", "write-avg(1 vol)"),
                                        ("output_read_avg_latency", "read-avg(1 vol)")])
            positive = True

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