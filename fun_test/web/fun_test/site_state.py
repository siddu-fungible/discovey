from fun_settings import WEB_ROOT_DIR
from web.fun_test.metrics_models import ModelMapping, ANALYTICS_MAP
from django.core.exceptions import ObjectDoesNotExist
from web.fun_test.models import Engineer
from web.fun_test.models import Tag
from web.fun_test.models import TestBed
from web.fun_test.models import Module
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

    def register_model_mapping(self, model, model_name, module, component):
        self.metric_models[model_name] = model
        try:
            ModelMapping.objects.get(model_name=model_name)
        except ObjectDoesNotExist:
            mapping = ModelMapping(module=module, component=component, model_name=model_name)
            mapping.save()

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
        for model_name, model_info in ANALYTICS_MAP.iteritems():
            self.register_model_mapping(model=model_info["model"],
                                 model_name=model_name,
                                 module=model_info["module"],
                                 component=model_info["component"])

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
        m = None
        children = []
        if "children" in metric:
            children = metric["children"]
        try:
            metric_model_name = "MetricContainer"
            if "metric_model_name" in metric:
                metric_model_name = metric["metric_model_name"]
            m = MetricChart.objects.get(metric_model_name=metric_model_name, chart_name=metric["name"])
        except ObjectDoesNotExist:
            # if len(children):
            m = MetricChart(metric_model_name="MetricContainer",
                            chart_name=metric["name"],
                            leaf=False, metric_id=LastMetricId.get_next_id())
            m.save()

        m.children = "[]"
        m.save()
        for child in children:
            c = self._do_register_metric(metric=child)
            if c:
                m.add_child(child_id=c.metric_id)
        return m

    def register_product_metrics(self):
        with open(METRICS_BASE_DATA_FILE, "r") as f:
            metrics = json.load(f)
            for metric in metrics:
                self._do_register_metric(metric=metric)

if not site_state:
    site_state = SiteState()

