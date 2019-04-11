from web.web_global import api_safe_json_response
from django.views.decorators.csrf import csrf_exempt
from web.fun_test.models import TestBed
from django.db.models import Q
from web.fun_test.models import SuiteExecution

@csrf_exempt
@api_safe_json_response
def test_beds(request, id):
    result = None
    if request.method == "GET":
        all_test_beds = TestBed.objects.all().order_by('name')
        result = []
        for test_bed in all_test_beds:
            t = {"name": test_bed.name, "description": test_bed.description}
            result.append(t)
    return result

@csrf_exempt
@api_safe_json_response
def suite_executions(request, id):
    result = None
    q = Q()
    if request.method == "GET":
        test_bed_type = request.GET.get('test_bed_type', None)
        if test_bed_type:
            q = q & Q(test_bed_type=test_bed_type)
        state = request.GET.get('state', None)
        if state:
            q = q & Q(state=int(state))

        records = []
        suite_executions = SuiteExecution.objects.filter(q).order_by('submitted_time')
        for suite_execution in suite_executions:
            one_record = {"execution_id": suite_execution.execution_id,
                          "state": suite_execution.state}
            records.append(one_record)
        result = records if len(records) else None
    return result