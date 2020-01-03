from lib.system.fun_test import *

am = fun_test.get_asset_manager()
all_test_bed_specs = am.get_all_test_beds_specs()

for test_bed_name, test_bed_spec in all_test_bed_specs.iteritems():
    print test_bed_name
    print "------------"
    if test_bed_name not in am.PSEUDO_TEST_BEDS:
        assets_in_test_bed = am.get_assets_required(test_bed_name=test_bed_name)
        for asset_type, asset_name in assets_in_test_bed.iteritems():
            print asset_type, asset_name

    print "------------"
