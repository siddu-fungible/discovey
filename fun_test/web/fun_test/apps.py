from django.apps import AppConfig
from lib.utilities.jira_manager import JiraManager

class FunTestConfig(AppConfig):

    name = "web.fun_test"

    def __init__(self, *args, **kwargs):
        super(FunTestConfig, self).__init__(*args, **kwargs)
        self.metric_models = {}

    def ready(self):
        self.set_metric_models()

    def get_jira_manager(self):
        if not hasattr(self, "jira_manager"):
            self.jira_manager = JiraManager()
        return self.jira_manager

    def set_metric_models(self):
        for model in self.get_models():
            self.metric_models[model.__name__] = model

    def get_metric_models(self):
        return self.metric_models