import os
import django
from web.web_global import PRIMARY_SETTINGS_FILE
from web.fun_test.settings import COMMON_WEB_LOGGER_NAME
import logging
from datetime import datetime

logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", PRIMARY_SETTINGS_FILE)
django.setup()

from web.fun_test.metrics_models import MetricChart, MetricChartStatus

class SetBaseLine():
    def set_base_line(self, metric_id, base_line_date, y1_axis_title=None):
        mc = MetricChart.objects.get(metric_id=metric_id)
        print mc.base_line_date
        mc.base_line_date = base_line_date
        if y1_axis_title:
            mc.y1_axis_title = y1_axis_title
        print mc.base_line_date
        mc.save()

if __name__ == "__main__":
    metric_id = 212
    base_line_date = datetime(year=2019, month=1, day=5, minute=0, hour=0, second=0)
    sbl = SetBaseLine()
    sbl.set_base_line(metric_id, base_line_date)
    print "completed"
