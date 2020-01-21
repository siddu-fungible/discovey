from web.fun_test.django_interactive import *
from web.fun_test.models import SuiteExecution, Suite

import sys

filter_test_bed = None
if len(sys.argv) > 1:
    filter_test_bed = sys.argv[1]

s = SuiteExecution.objects.filter(test_bed_type="suite-based").order_by("-started_time")
for job in s:
    duts_used = []
    run_time = job.run_time
    if "custom_test_bed_spec" in run_time:
        ct = run_time["custom_test_bed_spec"]
        if "dut_info" in ct:
            for dut_index, dut_info in ct["dut_info"].iteritems():
                if "disabled" in dut_info:
                    if not dut_info["disabled"]:
                        duts_used.append(dut_info["dut"])
                else:
                    duts_used.append(dut_info["dut"])

    # for dut_used in duts_used:
    #    print dut_used
    print_it = True
    if filter_test_bed:
        if filter_test_bed not in duts_used:
            print_it = False

    suite_name = ""
    try:
        suite = Suite.objects.get(id=job.suite_id)
        suite_name = suite.name
    except:
        pass

    if print_it:
        print "http://integration.fungible.local/regression/suite_detail/{} {}".format(job.execution_id, suite_name)
