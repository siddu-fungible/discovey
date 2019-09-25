from fun_settings import WEB_ROOT_DIR, TEAM_REGRESSION_EMAIL
# from web.fun_test.metrics_models import ModelMapping
from django.core.exceptions import ObjectDoesNotExist
from web.fun_test.models import Engineer
from web.fun_test.models import Tag
from web.fun_test.models import TestBed, TestbedNotificationEmails
from web.fun_test.models import Module
from web.fun_test.metrics_models import MetricsGlobalSettings
from web.fun_test.models import Asset
from django.apps import apps
from web.fun_test.metrics_models import MetricChart, LastMetricId
from web.fun_test.metrics_lib import *
import json
import os
import traceback

site_state = None
ml = MetricLib()

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

    def register_test_bed_interest_emails(self):
        try:
            TestbedNotificationEmails.objects.get(email=TEAM_REGRESSION_EMAIL)
        except ObjectDoesNotExist:
            TestbedNotificationEmails(email=TEAM_REGRESSION_EMAIL).save()

    def register_model_mappings(self):
        for model in apps.get_models():
            self.register_model_mapping(model=model, model_name=model.__name__)

    def register_test_beds(self):
        testbeds = self.site_base_data["testbeds"]
        for testbed in testbeds:
            try:
                TestBed.objects.get(name=testbed)
            except ObjectDoesNotExist:
                t = TestBed(name=testbed)
                t.save()

    def register_assets(self):
        fun_test_was_disabled = False
        if "DISABLE_FUN_TEST" in os.environ:
            fun_test_was_disabled = True
            del os.environ["DISABLE_FUN_TEST"]
        from asset.asset_manager import AssetManager

        am = AssetManager()
        valid_test_beds = am.get_valid_test_beds()
        for test_bed_name in valid_test_beds:
            # print test_bed_name
            assets_required = am.get_assets_required(test_bed_name=test_bed_name)
            for asset_type, assets in assets_required.iteritems():
                print asset_type, assets
                for asset in assets:
                    try:
                        (o, created) = Asset.objects.get_or_create(type=asset_type,
                                                                   name=asset)
                        if not created:
                            o.test_beds = []
                        if test_bed_name not in o.test_beds:
                            o.test_beds.append(test_bed_name)
                        o.save()
                    except Exception as ex:
                        print "Exception: {} {}".format(str(ex), traceback.format_exc())
        if fun_test_was_disabled:
            os.environ["DISABLE_FUN_TEST"] = "1"

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
                                                        internal_chart_name="All metrics")
        except ObjectDoesNotExist:
            all_metrics_chart = MetricChart(metric_model_name="MetricContainer",
                                            chart_name="All metrics",
                                            internal_chart_name="All metrics",
                                            leaf=False, metric_id=LastMetricId.get_next_id())
        m = None
        disable = False
        if "disable" in metric:
            disable = metric["disable"]
        if not disable:
            children = []
            if "children" in metric:
                children = metric["children"]

            description = "TBD"
            try:
                metric_model_name = "MetricContainer"

                if "metric_model_name" in metric:
                    metric_model_name = metric["metric_model_name"]
                m = MetricChart.objects.get(metric_model_name=metric_model_name, internal_chart_name=metric["name"])
                m.chart_name = metric["label"]
                m.save()
                if description and not m.description:
                    m.description = description
                    m.save()

            except ObjectDoesNotExist:
                data_sets = []
                one_data_set = {}
                one_data_set["name"] = "Scores"
                one_data_set["output"] = {"min": 0, "max": 200}
                data_sets.append(one_data_set)
                m = MetricChart(metric_model_name="MetricContainer",
                                    internal_chart_name=metric["name"],
                                    chart_name=metric["label"],
                                    leaf=False, metric_id=LastMetricId.get_next_id(),
                                    description=description, data_sets=json.dumps(data_sets))
                m.save()
            if "reference" in metric and metric["reference"]:
                pass
            else:
                try:
                    m.children = "[]"
                except Exception as ex:
                    pass
                # m.children_weights = "{}"
                m.save()
                for child in children:
                    c = self._do_register_metric(metric=child)
                    if c:
                        m.add_child(child_id=c.metric_id)
                        if "metric_model_name" in child and child["metric_model_name"] != "MetricContainer":
                            all_metrics_chart.add_child(child_id=c.metric_id)
                            all_metrics_chart.add_child_weight(child_id=c.metric_id, weight=1)
                m.save()
            if "extensible_references" in metric:
                references = metric["extensible_references"]
                if len(references):
                    for reference in references:
                        try:
                            reference_chart = MetricChart.objects.get(metric_model_name="MetricContainer", internal_chart_name=reference)
                            reference_children = json.loads(reference_chart.children)
                            for child in reference_children:
                                m.add_child(child_id=child)
                            m.save()
                        except Exception as ex:
                            pass
            m.fix_children_weights()

        return m

    def register_product_metrics(self):
        with open(METRICS_BASE_DATA_FILE, "r") as f:
            metrics = json.load(f)
            all_metrics_metric = {
                "metric_model_name": "MetricContainer",
                "name": "All metrics",
                "label": "All metrics",
                "children": [],
                "weight": 0
            }
            self._do_register_metric(metric=all_metrics_metric)
            for metric in metrics:
                self._do_register_metric(metric=metric)
                ml.set_global_cache(cache_valid=False)
            ml.update_weights_for_wip()

    def set_metrics_settings(self):
        if MetricsGlobalSettings.objects.count() == 0:
            global_settings = MetricsGlobalSettings()
            global_settings.save()

if not site_state:
    site_state = SiteState()


