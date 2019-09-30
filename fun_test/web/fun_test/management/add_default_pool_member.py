from web.fun_test.django_interactive import *
from web.fun_test.models import Suite, SuiteExecution


all_suites = Suite.objects.all()

for suite in all_suites:
    if suite.custom_test_bed_spec:
        if "asset_request" in suite.custom_test_bed_spec:
            asset_request = suite.custom_test_bed_spec["asset_request"]

            if "DUT" in asset_request:
                dut = asset_request["DUT"]
                if "num" in dut:
                    print asset_request
                    dut["pool_member_type_options"] = {0: {"num": dut["num"]}}
                    del dut["num"]
                    suite.save()
                    """
                    if "pool_member_type" not in dut:
                        dut["pool_member_type"] = 0
                        suite.save()
                    """