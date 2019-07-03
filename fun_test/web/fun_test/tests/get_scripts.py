from fun_settings import LOGS_DIR
from web.fun_test.django_interactive import *
import os
import glob
from web.fun_test.models import SuiteExecution, TestCaseExecution


def get_scripts_by_suite_execution(suite_execution_id):
    test_case_executions = TestCaseExecution.objects.filter(suite_execution_id=suite_execution_id)
    scripts = set()
    for test_case_execution in test_case_executions:
        scripts.add(test_case_execution.script_path)
    return scripts


suite_execution_id = 16308
suite_log_directory = LOGS_DIR + "/s_" + str(suite_execution_id)
scripts = get_scripts_by_suite_execution(suite_execution_id=suite_execution_id)
for script in scripts:
    base_name = os.path.basename(script)
    print base_name
    print "Associated files:"
    glob_pattern = suite_log_directory + "/*" + base_name + "*"
    associated_files = glob.glob(glob_pattern)
    for associated_file in associated_files:
        print associated_file


