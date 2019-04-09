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
from web.fun_test.site_state import *
from web.fun_test.metrics_models import MetricChart, MileStoneMarkers, LastMetricId


class MetricLib():
    def add_data_set(self, metric_id, data_set):
        try:
            chart = MetricChart.objects.get(metric_id=metric_id)
            if chart:
                data_sets = json.loads(chart.data_sets)
                data_sets.append(data_set)
                self.save_data_sets(data_sets=data_sets, chart=chart)
                return True
            else:
                return False
        except:
            return False

    def delete_data_set(self, metric_id, data_set):
        try:
            chart = MetricChart.objects.get(metric_id=metric_id)
            if chart:
                data_sets = json.loads(chart.data_sets)
                for set in data_sets:
                    if set["name"] == data_set["name"]:
                        data_sets.remove(set)
                self.save_data_sets(data_sets=data_sets, chart=chart)
                return True
            else:
                return False
        except:
            return False

    def save_data_sets(self, data_sets, chart):
        chart.data_sets = json.dumps(data_sets)
        chart.save()

    def replace_data_Set(self, data_sets, metric_id):
        try:
            chart = MetricChart.objects.get(metric_id=metric_id)
            if chart:
                self.save_data_sets(data_sets=data_sets, chart=chart)
                return True
            else:
                return False
        except:
            return False

    def get_data_sets(self, metric_id):
        try:
            chart = MetricChart.objects.get(metric_id=metric_id)
            return json.loads(chart.data_sets)
        except:
            return []

    def get_data_set(self, metric_id, **kwargs):
        try:
            chart = MetricChart.objects.get(metric_id=metric_id)
            if "name" in kwargs:
                name = kwargs["name"]
                data_sets = json.loads(chart.data_sets)
                for data_set in data_sets:
                    if data_set["name"] == name:
                        for key, value in kwargs.iteritems():
                            if not key.startswith("name"):
                                if not value == data_set["inputs"][key]:
                                    return []
                        return data_set
                return []
        except:
            return []

    def set_attributes_to_data_set(self, metric_id, **kwargs):
        try:
            chart = MetricChart.objects.get(metric_id=metric_id)
            if "name" in kwargs:
                name = kwargs["name"]
                data_sets = json.loads(chart.data_sets)
                for data_set in data_sets:
                    if data_set["name"] == name:
                        for key, value in kwargs.iteritems():
                            if not key.startswith("name"):
                                if data_set["inputs"][key]:
                                    data_set["inputs"][key] = value
                        break
                self.save_data_sets(data_sets=data_sets, chart=chart)
                return True
            else:
                return False
        except:
            return False

    def add_attributes_to_data_set(self, metric_id, **kwargs):
        try:
            chart = MetricChart.objects.get(metric_id=metric_id)
            if "name" in kwargs:
                name = kwargs["name"]
                data_sets = json.loads(chart.data_sets)
                for data_set in data_sets:
                    if data_set["name"] == name:
                        for key, value in kwargs.iteritems():
                            if not key.startswith("name"):
                                data_set["inputs"][key] = value
                        break
                self.save_data_sets(data_sets=data_sets, chart=chart)
                return True
            else:
                return False
        except:
            return False

    def add_attributes_to_data_sets(self, metric_id, **kwargs):
        try:
            chart = MetricChart.objects.get(metric_id=metric_id)
            data_sets = json.loads(chart.data_sets)
            for data_set in data_sets:
                for key, value in kwargs.iteritems():
                    data_set["inputs"][key] = value
            self.save_data_sets(data_sets=data_sets, chart=chart)
            return True
        except:
            return False

    def set_work_in_progress(self, chart, in_progress):
        chart.work_in_progress = in_progress
        chart.save()

    def create_chart(self, **kwargs):
        metric_id = LastMetricId.get_next_id()
        MetricChart(chart_name=kwargs["chart_name"],
                    metric_id=metric_id,
                    internal_chart_name=kwargs["internal_chart_name"],
                    data_sets=json.dumps(kwargs["data_sets"]),
                    leaf=True,
                    description=kwargs["description"],
                    owner_info=kwargs["owner_info"],
                    source=kwargs["source"],
                    positive=kwargs["positive"],
                    y1_axis_title=kwargs["y1_axis_title"],
                    visualization_unit=kwargs["visualization_unit"],
                    metric_model_name=kwargs["metric_model_name"],
                    base_line_date=kwargs["base_line_date"]).save()
        MileStoneMarkers(metric_id=metric_id,
                         milestone_date=datetime(year=2018, month=9, day=16),
                         milestone_name="Tape-out").save()
