from django.apps import AppConfig
from lib.utilities.jira_manager import JiraManager


class FunTestConfig(AppConfig):
    name = "web.fun_test"

    def ready(self):
        pass

    def get_jira_manager(self):
        if not hasattr(self, "jira_manager"):
            self.jira_manager = JiraManager()
        return self.jira_manager
