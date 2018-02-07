from fun_settings import WEB_ROOT_DIR
from web.fun_test.metrics_models import ModelMapping, REGISTRANTS
from django.core.exceptions import ObjectDoesNotExist
from web.fun_test.models import Engineer
from web.fun_test.models import Tag
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
        for registrant in REGISTRANTS:
            self.register_metric(model=registrant["model"],
                                 model_name=registrant["model_name"],
                                 module=registrant["module"],
                                 component=registrant["component"])

    def register_tags(self):
        for tag in self.site_base_data["tags"]:
            try:
                Tag.objects.get(tag=tag)
            except ObjectDoesNotExist:
                t = Tag(tag=tag)
                t.save()

if not site_state:
    site_state = SiteState()

