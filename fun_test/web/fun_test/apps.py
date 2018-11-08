from django.apps import AppConfig
from django.contrib import admin
from lib.utilities.jira_manager import JiraManager
from apscheduler.schedulers.background import BackgroundScheduler


class ListAdminMixin(object):
    def __init__(self, model, admin_site):
        self.list_display = [field.name for field in model._meta.fields if field.name != "id"]
        super(ListAdminMixin, self).__init__(model, admin_site)



class FunTestConfig(AppConfig):

    name = "web.fun_test"

    def __init__(self, *args, **kwargs):
        super(FunTestConfig, self).__init__(*args, **kwargs)
        self.metric_models = {}

    def ready(self):
        self.set_metric_models()

        ''' Auto-register models for admin '''
        models = self.get_models()
        for model in models:
            admin_class = type('AdminClass', (ListAdminMixin, admin.ModelAdmin), {})
            try:
                admin.site.register(model, admin_class)
            except admin.sites.AlreadyRegistered:
                pass


    def get_jira_manager(self):
        if not hasattr(self, "jira_manager"):
            self.jira_manager = JiraManager()
        return self.jira_manager

    def get_background_scheduler(self):
        if not hasattr(self, "background_scheduler"):
            self.background_scheduler = BackgroundScheduler()
            self.background_scheduler.start()
        return self.background_scheduler

    def set_metric_models(self):
        for model in self.get_models():
            self.metric_models[model.__name__] = model

    def get_metric_models(self):
        return self.metric_models