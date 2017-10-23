import json, os
from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers, paginator
from fun_global import RESULTS
from fun_settings import LOGS_RELATIVE_DIR, SUITES_DIR
from scheduler.scheduler_helper import LOG_DIR_PREFIX, queue_job, re_queue_job
from web.fun_test.models import SuiteExecution, TestCaseExecution
import glob, collections
from django.views.decorators.csrf import csrf_exempt
import logging

logger = logging.getLogger(__name__)

def index(request):
    return render(request, 'qa_dashboard/regression.html', locals())

def submit_job_page(request):
    return render(request, 'qa_dashboard/submit_job_page.html')

def suite_re_run(request, suite_execution_id):
    return HttpResponse(re_queue_job(suite_execution_id=suite_execution_id))

@csrf_exempt
def test_case_re_run(request):
    request_json = json.loads(request.body)
    suite_execution_id = request_json["suite_execution_id"]
    test_case_execution_id = request_json["test_case_execution_id"]
    script_path = request_json["script_path"]

    return HttpResponse(re_queue_job(suite_execution_id=suite_execution_id,
                                     test_case_execution_id=test_case_execution_id,
                                     script_path=script_path))

@csrf_exempt
def submit_job(request):
    job_id = 0
    if request.method == 'POST':
        request_json = json.loads(request.body)
        suite_path = request_json["suite_path"]
        job_id = queue_job(suite_path=suite_path)
    return HttpResponse(job_id)

def suites(request):
    suites_info = collections.OrderedDict()
    suite_files = glob.glob(SUITES_DIR + "/*.json")
    for suite_file in suite_files:
        try:
            with open(suite_file, "r") as infile:
                contents = infile.read()
                result = json.loads(contents)
                suites_info[os.path.basename(suite_file)] = result

        except Exception as ex:
            pass
    return HttpResponse(json.dumps(suites_info))


def _get_suite_executions(execution_id, page=None, records_per_page=10):
    all_objects = None
    if not execution_id:
        all_objects = SuiteExecution.objects.all().order_by('-id')
    else:
        all_objects = SuiteExecution.objects.filter(execution_id=execution_id).order_by('-id')
    if page:
        p = paginator.Paginator(all_objects, records_per_page)
        all_objects = p.page(page)

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
        if num_in_progress:
            suite_result = RESULTS["IN_PROGRESS"]
        suite_execution["suite_result"] = suite_result
        suite_execution["num_passed"] = num_passed
        suite_execution["num_failed"] = num_failed
        suite_execution["num_skipped"] = num_skipped
        suite_execution["num_not_run"] = num_not_run
        suite_execution["num_in_progress"] = num_in_progress
    return all_objects_dict

def suite_executions_count(request):
    return HttpResponse(SuiteExecution.objects.count())

def suite_executions(request, records_per_page=10, page=None):
    all_objects_dict = _get_suite_executions(execution_id=None, page=page, records_per_page=records_per_page)
    return HttpResponse(json.dumps(all_objects_dict))

def suite_execution(request, execution_id):
    all_objects_dict = _get_suite_executions(execution_id=int(execution_id))
    return HttpResponse(json.dumps(all_objects_dict[0])) #TODO: Validate

def suite_detail(request, execution_id):
    all_objects_dict = _get_suite_executions(execution_id=execution_id)
    suite_execution = all_objects_dict[0]
    suite_execution_attributes = []
    suite_execution_attributes.append({"name": "Result", "value": suite_execution["suite_result"]})
    suite_execution_attributes.append({"name": "Scheduled Time", "value": str(suite_execution["fields"]["scheduled_time"])})
    suite_execution_attributes.append({"name": "Completed Time", "value": str(suite_execution["fields"]["completed_time"])})
    suite_execution_attributes.append({"name": "Path", "value": str(suite_execution["fields"]["suite_path"])})
    suite_execution_attributes.append({"name": "Passed", "value": suite_execution["num_passed"]})
    suite_execution_attributes.append({"name": "Failed", "value": suite_execution["num_failed"]})
    suite_execution_attributes.append({"name": "Not Run", "value": suite_execution["num_not_run"]})
    suite_execution_attributes.append({"name": "In Progress", "value": suite_execution["num_in_progress"]})
    suite_execution_attributes.append({"name": "Skipped", "value": suite_execution["num_skipped"]})

    return render(request, 'qa_dashboard/suite_detail.html', locals())

def test_case_execution(request, suite_execution_id, test_case_execution_id):
    test_case_execution_obj = TestCaseExecution.objects.get(suite_execution_id=suite_execution_id,
                                                        execution_id=test_case_execution_id)
    data = serializers.serialize('json', [test_case_execution_obj])
    return HttpResponse(data)

def log_path(request):
    return HttpResponse(LOGS_RELATIVE_DIR + "/" + LOG_DIR_PREFIX)