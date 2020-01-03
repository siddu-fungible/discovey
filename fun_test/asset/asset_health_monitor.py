from lib.system.fun_test import *

am = fun_test.get_asset_manager()
all_test_bed_specs = am.get_all_test_beds_specs()

for test_bed_name, test_bed_spec in all_test_bed_specs.iteritems():
    print test_bed_name