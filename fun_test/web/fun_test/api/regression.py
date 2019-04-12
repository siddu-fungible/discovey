from fun_global import get_current_time
from web.web_global import api_safe_json_response
from django.views.decorators.csrf import csrf_exempt
from web.fun_test.models import TestBed
from django.db.models import Q
from web.fun_test.models import SuiteExecution
import json
from datetime import datetime, timedelta

@csrf_exempt
@api_safe_json_response
def test_beds(request, id):
    result = None
    if request.method == "GET":
        all_test_beds = TestBed.objects.all().order_by('name')
        result = []
        for test_bed in all_test_beds:
            t = {"name": test_bed.name,
                 "description": test_bed.description,
                 "id": test_bed.id,
                 "manual_lock": test_bed.manual_lock,
                 "manual_lock_expiry_time": str(test_bed.manual_lock_expiry_time),
                 "manual_lock_submitter": test_bed.manual_lock_submitter}
            result.append(t)
    if request.method == "PUT":
        test_bed = TestBed.objects.get(id=int(id))
        request_json = json.loads(request.body)
        extension_hour = request_json["manual_lock_extension_hour"]
        extension_minute = request_json["manual_lock_extension_minute"]
        submitter_email = request_json["manual_lock_submitter_email"]

        future_time = get_current_time() + timedelta(hours=int(extension_hour),
                                                     minutes=int(extension_minute))
        test_bed.manual_lock_expiry_time = future_time
        test_bed.manual_lock_submitter = submitter_email
        test_bed.manual_lock = True
        test_bed.save()
        pass
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