import json
from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers
from fun_global import RESULTS
from web.fun_test.models import SuiteExecution, TestCaseExecution

def index(request):
    return render(request, 'qa_dashboard/regression.html', locals())


def suite_executions(request):
    all_objects = SuiteExecution.objects.all()
    data = serializers.serialize("json", all_objects)
    all_objects_dict = json.loads(data)

    for suite_execution in all_objects_dict:
        test_case_execution_ids = json.loads(suite_execution["fields"]["test_case_execution_ids"])
        suite_result = RESULTS["UNKNOWN"]
        num_passed = 0
        num_failed = 0
        num_skipped = 0
        num_not_run = 0
        num_in_progress = 0

        for test_case_execution_id in test_case_execution_ids:
            test_case_execution = TestCaseExecution.objects.get(execution_id=test_case_execution_id)
            te_result = test_case_execution.result.upper()  #TODO: Upper?
            if te_result == RESULTS["FAILED"]:
                num_failed += 1
            elif te_result == RESULTS["PASSED"]:
                num_passed += 1
            elif te_result == RESULTS["NOT_RUN"]:
                num_not_run += 1
            elif te_result == RESULTS["SKIPPED"]:
                num_skipped += 1
            elif te_result == RESULTS["IN_PROGRESS"]:
                num_in_progress += 1

        if (num_passed == len(test_case_execution_ids)) and test_case_execution_ids:
            suite_result = RESULTS["PASSED"]
        if num_failed:
            suite_result = RESULTS["FAILED"]
        suite_execution["suite_result"] = suite_result
        suite_execution["num_passed"] = num_passed
        suite_execution["num_failed"] = num_failed
        suite_execution["num_skipped"] = num_skipped
        suite_execution["num_not_run"] = num_not_run
        suite_execution["num_in_progress"] = num_in_progress

    return HttpResponse(json.dumps(all_objects_dict))

def suite_detail(request, execution_id):
    # suite_execution = SuiteExecution.objects.get(execution_id=execution_id)
    # data = serializers.serialize("json", suite_execution)
    # return HttpResponse(data)
    return render(request, 'qa_dashboard/suite_detail.html', locals())

