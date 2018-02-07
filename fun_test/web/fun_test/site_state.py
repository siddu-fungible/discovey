from fun_settings import WEB_ROOT_DIR
from web.fun_test.metrics_models import ModelMapping, ANALYTICS_MAP
from django.core.exceptions import ObjectDoesNotExist
from web.fun_test.models import Engineer
from web.fun_test.models import Tag
from web.fun_test.models import TestBed
from web.fun_test.models import Module
import json

site_state = None

SITE_BASE_DATA_FILE = WEB_ROOT_DIR + "/site_base_data.json"


class SiteState():
    def __init__(self):
        self.metric_models = {}
        with open(SITE_BASE_DATA_FILE, "r") as f:
            self.site_base_data = json.load(f)


    def register_metric(self, model, model_name, module, component):
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

    def register_metrics(self):
        for model_name, model_info in ANALYTICS_MAP:
            self.register_metric(model=model_info["model"],
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


if not site_state:
    site_state = SiteState()

