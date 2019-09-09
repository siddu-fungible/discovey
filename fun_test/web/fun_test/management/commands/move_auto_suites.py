from web.fun_test.django_interactive import *
from web.fun_test.models import Suite, SuiteExecution
from fun_settings import SUITES_DIR
from glob import glob
import json

suite_executions = SuiteExecution.objects.filter(is_auto_scheduled_job=True)
for suite_execution in suite_executions:
    if suite_execution.suite_path:
        print suite_execution.suite_path
        try:
            suite = Suite.objects.get(name=suite_execution.suite_path)
            suite_execution.suite_id = suite.id
            suite_execution.save()
        except:
            i = 0

    else:
        print suite_execution.script_path
