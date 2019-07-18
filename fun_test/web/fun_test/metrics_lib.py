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

    def replace_data_sets(self, data_sets, metric_id):
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
        result = []
        try:
            chart = MetricChart.objects.get(metric_id=metric_id)
            result = json.loads(chart.data_sets)
        except Exception as ex:
            print str(ex)
        return result

    def get_peer_ids(self, metric_id):
        result = []
        try:
            chart = MetricChart.objects.get(metric_id=metric_id)
            result = json.loads(chart.peer_ids)
        except Exception as ex:
            print str(ex)
        return result

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
                    base_line_date=kwargs["base_line_date"],
                    work_in_progress=False).save()
        MileStoneMarkers(metric_id=metric_id,
                         milestone_date=datetime(year=2018, month=9, day=16),
                         milestone_name="Tape-out").save()

    def set_inputs_data_sets(self, data_sets, **kwargs):
        for data_set in data_sets:
            for key, value in kwargs.iteritems():
                data_set["inputs"][key] = value
        return data_sets

    def set_outputs_data_sets(self, data_sets, **kwargs):
        for data_set in data_sets:
            for key, value in kwargs.iteritems():
                data_set["output"][key] = value
        return data_sets

    def remove_attribute_from_data_sets(self, chart, key):
        data_sets = json.loads(chart.data_sets)
        for data_set in data_sets:
            data_set["inputs"].pop(key, None)
        self.save_data_sets(data_sets=data_sets, chart=chart)

    def clone_chart(self, old_chart, internal_chart_name, data_sets):
        try:
            chart = MetricChart.objects.filter(internal_chart_name=internal_chart_name)
        except ObjectDoesNotExist:
            metric_id = LastMetricId.get_next_id()
            peer_id = []
            peer_id.append(old_chart.metric_id)
            MetricChart(chart_name=old_chart.chart_name,
                        metric_id=metric_id,
                        internal_chart_name=internal_chart_name,
                        data_sets=json.dumps(data_sets),
                        leaf=old_chart.leaf,
                        description=old_chart.description,
                        owner_info=old_chart.owner_info,
                        source=old_chart.source,
                        positive=old_chart.positive,
                        y1_axis_title=old_chart.y1_axis_title,
                        visualization_unit=old_chart.visualization_unit,
                        metric_model_name=old_chart.metric_model_name,
                        base_line_date=old_chart.base_line_date,
                        work_in_progress=False,
                        peer_ids=json.dumps(peer_id)).save()
            old_chart.peer_ids = json.dumps([metric_id])
            old_chart.save()

    def update_weights_for_wip(self):
        charts = MetricChart.objects.filter(metric_model_name="MetricContainer")
        for container in charts:
            children = json.loads(container.children)
            for child in children:
                chart = MetricChart.objects.get(metric_id=child)
                if chart and chart.work_in_progress:
                    container.add_child_weight(child_id=child, weight=0)

    def reset_reference_value(self, chart):
        data_sets = json.loads(chart.data_sets)
        for data_set in data_sets:
            data_set["output"]["reference"] = -1
            data_set["output"]["expected"] = -1
            data_set["output"]["min"] = 0
            data_set["output"]["max"] = -1
        chart.data_sets = json.dumps(data_sets)
        chart.save()

if __name__ == "__main__":
    ml = MetricLib()
    ml.update_weights_for_wip()


