from web.fun_test.models import Engineer
from web.fun_test.models import CatalogSuite, CatalogSuiteExecution, CatalogTestCaseExecution, TestCaseExecution, Module
from web.fun_test.models import ModelMapping
from web.fun_test.metrics_models import MetricChart, VolumePerformance

class UsersRouter(object):
    def db_for_read(self, model, **hints):
        if model == Engineer:
            return 'users'
        if hasattr(model, "tag"):
            if model.tag == "analytics":
                return "performance"
        if model in [CatalogSuite, CatalogSuiteExecution, CatalogTestCaseExecution]:
            return "regression"
        elif model in [MetricChart, VolumePerformance, Module, Mo]:
            return "performance"
        else:
            i = 0
        return 'default'

    def db_for_write(self, model, **hints):
        if model == Engineer:
            return 'users'
        if hasattr(model, "tag"):
            if model.tag == "analytics":
                return "performance"
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return True
