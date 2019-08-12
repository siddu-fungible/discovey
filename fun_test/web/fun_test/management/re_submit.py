from web.fun_test.django_interactive import *
from web.fun_test.models import SuiteExecution
from scheduler.scheduler_global import SchedulingType, SchedulerStates, JobStatusType
import json

suite_executions = SuiteExecution.objects.all()

for suite_execution in suite_executions:
    if suite_execution.execution_id in [22180, 22181, 21716]: 
        suite_execution.state = JobStatusType.SUBMITTED
        suite_execution.result = "UNKNOWN"
        suite_execution.save()
         
