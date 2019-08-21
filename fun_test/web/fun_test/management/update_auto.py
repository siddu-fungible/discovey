from web.fun_test.django_interactive import *
from web.fun_test.models import SuiteExecution
from scheduler.scheduler_global import SchedulingType, SchedulerStates, JobStatusType
import json

suite_executions = SuiteExecution.objects.all()

for suite_execution in suite_executions:
    if suite_execution.state == JobStatusType.AUTO_SCHEDULED:
        environment = suite_execution.environment
        environment = json.loads(environment)
        if "build_parameters" in environment:
            build_parameters = environment["build_parameters"]
            if "DISABLE_ASSERTIONS" in build_parameters:
                if build_parameters["DISABLE_ASSERTIONS"]:
                    print suite_execution.execution_id, suite_execution.suite_path, suite_execution.environment
                    build_parameters["DISABLE_ASSERTIONS"] = False
                    build_parameters["RELEASE_BUILD"] = True
                    suite_execution.environment = json.dumps(environment)
                    suite_execution.save()
                else:
                    print False