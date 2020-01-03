from lib.system.fun_test import *
from threading import Thread


class TestBedWorker(Thread):
    def __init__(self, test_bed_name, spec):
        super(TestBedWorker, self).__init__()
        self.test_bed_name = test_bed_name
        self.spec = spec

    def run(self):
        pass


if __name__ == "__main__":
    am = fun_test.get_asset_manager()
    all_test_bed_specs = am.get_all_test_beds_specs()

    for test_bed_name, test_bed_spec in all_test_bed_specs.iteritems():
        if test_bed_name not in am.PSEUDO_TEST_BEDS:
            assets_in_test_bed = am.get_assets_required(test_bed_name=test_bed_name)
            for asset_type, asset_name in assets_in_test_bed.iteritems():
                print asset_type, asset_name

        print "------------"



# What does each thread do?
# Each thread is associated with one test-bed
# Terminating conditions
# a. daemon terminated
# b. test-bed no longer exists

# What daemon main does
# Create threads indexed by test-bed name
# if thread for test-bed does not exist start one
