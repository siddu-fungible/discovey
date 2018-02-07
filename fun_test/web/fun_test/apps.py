from django.apps import AppConfig
from web.web_global import is_performance_server


class FunTestConfig(AppConfig):
    name = "web.fun_test"

    def ready(self):
        pass
