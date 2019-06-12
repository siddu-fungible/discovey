from django.core.management.base import BaseCommand, CommandError
from web.fun_test.models import SiteConfig
from fun_global import is_lite_mode


class Command(BaseCommand):
    help = 'Bump site version'

    def handle(self, *args, **options):
        if SiteConfig.objects.count() == 0:
            SiteConfig().save()
        site_config = SiteConfig.objects.all()
        site_config[0].bump_version()
