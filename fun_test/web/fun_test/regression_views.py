import json, os
from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers, paginator
from fun_global import RESULTS
from fun_settings import LOGS_RELATIVE_DIR, SUITES_DIR, LOGS_DIR
from scheduler.scheduler_helper import LOG_DIR_PREFIX, queue_job, re_queue_job
import scheduler.scheduler_helper
from models_helper import _get_suite_executions, _get_suite_execution_attributes
from web.fun_test.models import SuiteExecution, TestCaseExecution
import glob, collections
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

def index(request):
    filter_string = "ALL"
    return render(request, 'qa_dashboard/regression.html', locals())

def completed_jobs(request):
    filter_string = "COMPLETED"
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
        build_url = request_json["build_url"]
        job_id = queue_job(suite_path=suite_path, build_url=build_url)
    return HttpResponse(job_id)

def static_serve_log_directory(request, suite_execution_id):
    path = LOGS_DIR + "/" + LOG_DIR_PREFIX + str(suite_execution_id) + "/*"
    files = glob.glob(path)
    files = [os.path.basename(f) for f in files]
    return render(request, 'qa_dashboard/list_directory.html', locals())

def kill_job(request, suite_execution_id):
    scheduler.scheduler_helper.kill_job(job_id=suite_execution_id)
    suite_execution = SuiteExecution.objects.get(execution_id=suite_execution_id)
    suite_execution.result = RESULTS["KILLED"]
    suite_execution.save()
    return HttpResponse("OK")

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
    suite_execution_attributes = _get_suite_execution_attributes(suite_execution=suite_execution)

    return render(request, 'qa_dashboard/suite_detail.html', locals())

def test_case_execution(request, suite_execution_id, test_case_execution_id):
    test_case_execution_obj = TestCaseExecution.objects.get(suite_execution_id=suite_execution_id,
                                                        execution_id=test_case_execution_id)
    test_case_execution_obj.started_time = timezone.localtime(test_case_execution_obj.started_time)
    test_case_execution_obj.end_time = timezone.localtime(test_case_execution_obj.end_time)

    data = serializers.serialize('json', [test_case_execution_obj])
    return HttpResponse(data)

def log_path(request):
    return HttpResponse(LOGS_RELATIVE_DIR + "/" + LOG_DIR_PREFIX)