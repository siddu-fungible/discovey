from web.fun_test.django_interactive import *
from web.fun_test.models import Suite, SuiteExecution
from fun_settings import SUITES_DIR
from glob import glob
import json

from django.db.models import Q
q = Q(is_auto_scheduled_job=True)
q = q & Q(execution_id=26979)

def fixup(environment, suite_execution):
    print "Fixing: {}".format(suite_execution.execution_id)
    environment["with_stable_master"] = {"debug": False, "stripped": True}
    if "with_jenkins_build" in environment:
        del environment["with_jenkins_build"]
    if "build_parameters" in environment:
        del environment["build_parameters"]
    suite_execution.environment = json.dumps(environment)
    suite_execution.save()


suite_executions = SuiteExecution.objects.filter(q)
for suite_execution in suite_executions:
    # print suite_execution.suite_id
    environment = suite_execution.get_environment()
    if environment and "with_jenkins_build" in environment and environment["with_jenkins_build"]:
        fixup(environment, suite_execution)

        scheduled_jobs = SuiteExecution.objects.filter(auto_scheduled_execution_id=suite_execution.execution_id)
        for scheduled_job in scheduled_jobs:
            fixup(scheduled_job.get_environment(), scheduled_job)

        """
        if environment:
            try:
                s = Suite.objects.get(id=suite_execution.suite_id)
                print s.entries
            except Exception as ex:
                print ex
                
        """
