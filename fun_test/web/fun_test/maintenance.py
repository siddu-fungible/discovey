import os
import django
import json
import random
import re
from fun_global import get_current_time
from datetime import datetime
from web.web_global import PRIMARY_SETTINGS_FILE
from fun_global import get_localized_time
from web.fun_test.settings import COMMON_WEB_LOGGER_NAME
import logging
logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)
from datetime import datetime, timedelta

os.environ.setdefault("DJANGO_SETTINGS_MODULE", PRIMARY_SETTINGS_FILE)
django.setup()
from web.fun_test.metrics_models import Performance1, PerformanceIkv, PerformanceBlt, VolumePerformance
from web.fun_test.metrics_models import AllocSpeedPerformance
from web.fun_test.site_state import *
from web.fun_test.metrics_models import MetricChart, ShaxPerformance
from web.fun_test.metrics_models import WuLatencyUngated, WuLatencyAllocStack, AllocSpeedPerformance
from web.fun_test.metrics_models import WuDispatchTestPerformance, WuSendSpeedTestPerformance, HuRawVolumePerformance
from web.fun_test.models import JenkinsJobIdMap
from web.fun_test.metrics_models import VoltestPerformance

from web.fun_test.analytics_models_helper import MetricChartHelper
from web.fun_test.metrics_models import MetricChartStatus

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
    for model in ["WuLatencyUngated", "WuLatencyAllocStack", "AllocSpeedPerformance", "BcopyFloodDmaPerformance", "BcopyPerformance",
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
        dt = dt.replace(day = dt.day - 1)
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

if __name__ == "__main__":
    import pytz
    chart_name = "WU Latency: Alloc Stack"
    model_name = "WuLatencyAllocStack"

    mcs_entries = WuLatencyAllocStack.objects.all()
    x = datetime(year=2018, month=6, day=01, minute=0, hour=0, second=0)
    tz = pytz.timezone("UTC")
    localized = tz.localize(x, is_dst=None)
    # dt = get_localized_time(x)

    for mcs_entry in mcs_entries:
        if mcs_entry.input_date_time < localized:
            mcs_entry.delete()


