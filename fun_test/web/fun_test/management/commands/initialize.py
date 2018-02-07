from django.core.management.base import BaseCommand, CommandError
from web.fun_test.site_state import site_state
from web.web_global import is_performance_server, is_regression_server


class Command(BaseCommand):
    help = 'Initialize'

    def handle(self, *args, **options):
        site_state.register_users()
        site_state.register_tags()
        if is_performance_server():
            site_state.register_metrics()
        if is_regression_server():
            site_state.register_testbeds()
