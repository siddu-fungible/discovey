from web.fun_test.django_interactive import *
import json
from web.fun_test.models import SuiteExecution


s = SuiteExecution.objects.get(execution_id=36564)
print json.dumps(s.run_time, indent=4)