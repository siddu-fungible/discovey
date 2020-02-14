from django.core.management.base import BaseCommand, CommandError
from web.fun_test.site_state import site_state
from fun_global import is_lite_mode


class Command(BaseCommand):
    help = 'Initialize'

    def handle(self, *args, **options):
        site_state.register_users()
        site_state.register_test_bed_interest_emails()
        site_state.register_tags()
        site_state.register_modules()
        site_state.register_test_beds()
        site_state.cleanup_test_beds()
        site_state.register_assets()
        site_state.cleanup_assets()

        if not is_lite_mode():
            site_state.register_product_metrics()
            site_state.set_metrics_settings()
