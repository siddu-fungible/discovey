from django.core.management.base import BaseCommand
from web.fun_test.models import Asset
import os

class Command(BaseCommand):
    help = 'Prepare assets by reading the topology spec'

    def handle(self, *args, **options):
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
                    Asset.objects.get_or_create(type=asset_type, name=asset)
