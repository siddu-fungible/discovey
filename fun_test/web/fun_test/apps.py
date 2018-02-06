from django.apps import AppConfig
from web.web_global import is_performance_server


class FunTestConfig(AppConfig):
    name = "web.fun_test"

    def ready(self):
        from web.fun_test.site_state import site_state
        if is_performance_server():
            site_state.register_metrics()
        # site_state.register_users()
