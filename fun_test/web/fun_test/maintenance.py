import os
import django
import json
import random
import re
from datetime import datetime
from web.web_global import PRIMARY_SETTINGS_FILE
from fun_global import get_localized_time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", PRIMARY_SETTINGS_FILE)
django.setup()
from web.fun_test.metrics_models import Performance1, PerformanceIkv, PerformanceBlt, VolumePerformance
from web.fun_test.metrics_models import AllocSpeedPerformance
from web.fun_test.site_state import *
from web.fun_test.metrics_models import MetricChart, ShaxPerformance
from web.fun_test.metrics_models import WuLatencyUngated, WuLatencyAllocStack, AllocSpeedPerformance
from web.fun_test.metrics_models import WuDispatchTestPerformance, WuSendSpeedTestPerformance
from web.fun_test.models import JenkinsJobIdMap
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

if __name__ == "__main5__":
    entries = WuDispatchTestPerformance.objects.all()
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

if __name__ == "__main__":
    entries = MetricChartStatus.objects.filter(metric_id=108)
    # entries = MetricChartStatus.objects.all()

    for entry in entries:
        print entry