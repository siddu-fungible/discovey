from fun_settings import WEB_ROOT_DIR
# from web.fun_test.metrics_models import ModelMapping
from django.core.exceptions import ObjectDoesNotExist
from web.fun_test.models import Engineer
from web.fun_test.models import Tag
from web.fun_test.models import TestBed
from web.fun_test.models import Module
from web.fun_test.metrics_models import MetricsGlobalSettings
from django.apps import apps
from web.fun_test.metrics_models import MetricChart, LastMetricId
import json

site_state = None

SITE_BASE_DATA_FILE = WEB_ROOT_DIR + "/site_base_data.json"
METRICS_BASE_DATA_FILE = WEB_ROOT_DIR + "/metrics.json"


class SiteState():
    def __init__(self):
        self.metric_models = {}
        with open(SITE_BASE_DATA_FILE, "r") as f:
            self.site_base_data = json.load(f)

    def register_model_mapping(self, model, model_name):
        self.metric_models[model_name] = model

    def get_metric_model_by_name(self, name):
        result = None
        if name in self.metric_models:
            result = self.metric_models[name]
        return result

    def register_users(self):
        users = self.site_base_data["users"]
        for user in users:
            try:
                Engineer.objects.get(short_name=user["short_name"])
            except ObjectDoesNotExist:
                e = Engineer(short_name=user["short_name"], email=user["email"])
                e.save()

    def register_model_mappings(self):
        for model in apps.get_models():
            self.register_model_mapping(model=model, model_name=model.__name__)

    def register_testbeds(self):
        testbeds = self.site_base_data["testbeds"]
        for testbed in testbeds:
            try:
                TestBed.objects.get(name=testbed)
            except ObjectDoesNotExist:
                t = TestBed(name=testbed)
                t.save()

    def register_tags(self):
        for tag in self.site_base_data["tags"]:
            try:
                Tag.objects.get(tag=tag)
            except ObjectDoesNotExist:
                t = Tag(tag=tag)
                t.save()

    def register_modules(self):
        Module.objects.all().delete()
        for module in self.site_base_data["modules"]:
            try:
                Module.objects.get(name=module["name"])
            except ObjectDoesNotExist:
                m = Module(name=module["name"], verbose_name=module["verbose_name"])
                m.save()

    def _do_register_metric(self, metric):

        all_metrics_chart = None
        try:
            all_metrics_chart = MetricChart.objects.get(metric_model_name="MetricContainer",
                                                        chart_name="All metrics")
        except ObjectDoesNotExist:
            all_metrics_chart = MetricChart(metric_model_name="MetricContainer",
                                            chart_name="All metrics",
                                            leaf=False, metric_id=LastMetricId.get_next_id())
        m = None
        children = []
        if "children" in metric:
            children = metric["children"]
        description = "TBD"

        if "Erasure" in metric["name"]:
            i = 0
        try:
            metric_model_name = "MetricContainer"

            if "metric_model_name" in metric:
                metric_model_name = metric["metric_model_name"]
            if "info" in metric:
                description = metric["info"]
            m = MetricChart.objects.get(metric_model_name=metric_model_name, chart_name=metric["name"])
            m.save()
            if description and not m.description:
                m.description = description
                m.save()
            '''
            if metric_model_name == "MetricContainer":
                m.leaf = False
                m.save()
            else:
                m.leaf = True
                m.save()
            '''

        except ObjectDoesNotExist:
            if len(children):
                m = MetricChart(metric_model_name="MetricContainer",
                                chart_name=metric["name"],
                                leaf=False, metric_id=LastMetricId.get_next_id(),
                                description=description)
                m.save()

        if "reference" in metric and metric["reference"]:
            pass
        else:
            m.children = "[]"
            m.children_weights = "{}"
            m.save()
            for child in children:
                c = self._do_register_metric(metric=child)
                if c:
                    m.add_child(child_id=c.metric_id)
                    child_weight = 0
                    if "weight" in child:
                        child_weight = child["weight"]
                    m.add_child_weight(child_id=c.metric_id, weight=child_weight)
                    if "leaf" in child and child["leaf"]:
                        all_metrics_chart.add_child(child_id=c.metric_id)
                        all_metrics_chart.add_child_weight(child_id=c.metric_id, weight=1)

        return m

    def register_product_metrics(self):
        with open(METRICS_BASE_DATA_FILE, "r") as f:
            metrics = json.load(f)
            all_metrics_metric = {
                "info": "All metrics",
                "metric_model_name": "MetricContainer",
                "leaf": False,
                "name": "All metrics",
                "label": "All metrics",
                "children": [],
                "weight": 0
            }
            self._do_register_metric(metric=all_metrics_metric)
            for metric in metrics:
                self._do_register_metric(metric=metric)

        total_chart = MetricChart.objects.get(metric_model_name="MetricContainer",
                                                            chart_name="Total")
        all_metrics_chart = MetricChart.objects.get(metric_model_name="MetricContainer",
                                                            chart_name="All metrics")
        if total_chart.chart_name == "Total":
            total_chart.add_child(all_metrics_chart.metric_id)

    def set_metrics_settings(self):
        if MetricsGlobalSettings.objects.count() == 0:
            global_settings = MetricsGlobalSettings()
            global_settings.save()

if not site_state:
    site_state = SiteState()


