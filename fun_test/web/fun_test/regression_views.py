import json
import os
from web.fun_test.settings import COMMON_WEB_LOGGER_NAME
from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers, paginator
from fun_global import RESULTS
from fun_settings import LOGS_RELATIVE_DIR, SUITES_DIR, LOGS_DIR
from scheduler.scheduler_helper import LOG_DIR_PREFIX, queue_job, re_queue_job
import scheduler.scheduler_helper
from models_helper import _get_suite_executions, _get_suite_execution_attributes, SUITE_EXECUTION_FILTERS
from web.fun_test.models import SuiteExecution, TestCaseExecution, Tag, Engineer, CatalogTestCaseExecution
from web.fun_test.models import CatalogSuiteExecution, Module
from web.fun_test.models import JenkinsJobIdMap, JenkinsJobIdMapSerializer
from web.web_global import initialize_result, api_safe_json_response
import glob, collections
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from fun_global import get_localized_time
from datetime import datetime, timedelta
import logging
import dateutil.parser
import re

logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)

def index(request):
    filter_string = SUITE_EXECUTION_FILTERS["ALL"]
    return render(request, 'qa_dashboard/regression.html', locals())

def sampler(request):
    return render(request, 'qa_dashboard/tree_view.html', locals())

def sampler2(request):
    return render(request, 'qa_dashboard/table_view.html', locals())

def completed_jobs(request):
    filter_string = SUITE_EXECUTION_FILTERS["COMPLETED"]
    return render(request, 'qa_dashboard/regression.html', locals())

def pending_jobs(request):
    filter_string = SUITE_EXECUTION_FILTERS["PENDING"]
    return render(request, 'qa_dashboard/regression.html', locals())

def jenkins_jobs(request):
    filter_string = SUITE_EXECUTION_FILTERS["ALL"]
    tags = json.dumps(["jenkins-hourly", "jenkins-nightly"])
    # tags = json.dumps(["none"])
    return render(request, 'qa_dashboard/regression.html', locals())

def jobs_by_tag(request, tag):
    filter_string = SUITE_EXECUTION_FILTERS["ALL"]
    tags = json.dumps([tag])
    # tags = json.dumps(["none"])
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
        tags = request_json["tags"]
        email_list = None
        email_on_fail_only = None
        if "email_list" in request_json:
            email_list = request_json["email_list"]
        if "email_on_fail_only" in request_json:
            email_on_fail_only = request_json["email_on_fail_only"]

        if "schedule_at" in request_json and request_json["schedule_at"]:
            schedule_at_value = request_json["schedule_at"]
            schedule_at_value = str(timezone.localtime(dateutil.parser.parse(schedule_at_value)))
            schedule_at_repeat = False
            if "schedule_at_repeat" in request_json:
                schedule_at_repeat = request_json["schedule_at_repeat"]
            job_id = queue_job(suite_path=suite_path,
                               build_url=build_url,
                               schedule_at=schedule_at_value,
                               repeat=schedule_at_repeat,
                               email_list=email_list,
                               email_on_fail_only=email_on_fail_only)

        elif "schedule_in_minutes" in request_json and request_json["schedule_in_minutes"]:
            schedule_in_minutes_value = request_json["schedule_in_minutes"]
            schedule_in_minutes_repeat = None
            if "schedule_in_minutes_repeat" in request_json:
                schedule_in_minutes_repeat = request_json["schedule_in_minutes_repeat"]
            job_id = queue_job(suite_path=suite_path,
                               build_url=build_url,
                               schedule_in_minutes=schedule_in_minutes_value,
                               repeat_in_minutes=schedule_in_minutes_repeat,
                               tags=tags,
                               email_list=email_list,
                               email_on_fail_only=email_on_fail_only)
        else:
            job_id = queue_job(suite_path=suite_path,
                               build_url=build_url,
                               tags=tags,
                               email_list=email_list,
                               email_on_fail_only=email_on_fail_only)
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

def tags(request):
    return HttpResponse(serializers.serialize('json', Tag.objects.all()))

def engineers(request):
    result = initialize_result(failed=True)
    s = serializers.serialize('json', Engineer.objects.all())
    s = json.loads(s)  #TODO
    result["data"] = s
    result["status"] = True
    return HttpResponse(json.dumps(result))

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


@csrf_exempt
def suite_executions_count(request, filter_string):
    tags = None
    if request.method == 'POST':
        if request.body:
            request_json = json.loads(request.body)
            if "tags" in request_json:
                tags = request_json["tags"]
                tags = json.loads(tags)
    count = _get_suite_executions(get_count=True, filter_string=filter_string, tags=tags)
    return HttpResponse(count)

@csrf_exempt
def suite_executions(request, records_per_page=10, page=None, filter_string="ALL"):
    tags = None
    if request.method == 'POST':
        if request.body:
            request_json = json.loads(request.body)
            if "tags" in request_json:
                tags = request_json["tags"]
                tags = json.loads(tags)
    all_objects_dict = _get_suite_executions(execution_id=None,
                                             page=page,
                                             records_per_page=records_per_page,
                                             filter_string=filter_string,
                                             tags=tags)
    return HttpResponse(json.dumps(all_objects_dict))

def suite_execution(request, execution_id):
    all_objects_dict = _get_suite_executions(execution_id=int(execution_id))
    return HttpResponse(json.dumps(all_objects_dict[0])) #TODO: Validate

def last_jenkins_hourly_execution_status(request):
    result = RESULTS["UNKNOWN"]
    suite_executions = _get_suite_executions(tags=["jenkins-hourly"],
                                             filter_string=SUITE_EXECUTION_FILTERS["COMPLETED"],
                                             page=1, records_per_page=10)
    if suite_executions:
        result = suite_executions[0]["suite_result"]
    return HttpResponse(result)

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

def get_catalog_test_case_execution_summary_result_multiple_jiras(suite_execution_id, jira_ids):
    summary_result = {}
    for jira_id in jira_ids:
        summary_result[jira_id] = get_catalog_test_case_execution_summary_result(suite_execution_id=suite_execution_id,
                                                                                 jira_id=jira_id)
    return summary_result

def get_catalog_test_case_execution_summary_result(suite_execution_id, jira_id):
    ctes = CatalogTestCaseExecution.objects.filter(catalog_suite_execution_id=suite_execution_id, jira_id=jira_id)
    summary_result = RESULTS["UNKNOWN"]
    te_count = ctes.count()
    num_passed = 0
    num_failed = 0
    num_blocked = 0
    for cte in ctes:
        te = TestCaseExecution.objects.using('regression').get(execution_id=cte.execution_id)
        if te.result == RESULTS["PASSED"]:
            num_passed += 1
        if te.result == RESULTS["FAILED"]:
            num_failed += 1
        if te.result == RESULTS["BLOCKED"]:
            num_blocked += 1

    if num_failed:
        summary_result = RESULTS["FAILED"]
    if num_passed == te_count:
        summary_result = RESULTS["PASSED"]
    if num_blocked:
        summary_result = RESULTS["BLOCKED"]

    # if num_passed == 0:
    #    summary_result = RESULTS["FAILED"]
    return summary_result

@csrf_exempt
def catalog_test_case_execution_summary_result(request, suite_execution_id, jira_id):
    result = initialize_result(failed=True)
    try:
        result["status"] = True
        result["data"] = get_catalog_test_case_execution_summary_result(suite_execution_id=suite_execution_id,
                                                                        jira_id=jira_id)
    except Exception as ex:
        result["error_message"] = str(ex)
    return HttpResponse(json.dumps(result))


@csrf_exempt
@api_safe_json_response
def modules(request):
    return [{"name": x.name, "verbose_name": x.verbose_name} for x in Module.objects.all()]

@csrf_exempt
@api_safe_json_response
def jenkins_job_id_map(request):
    all_entries = JenkinsJobIdMap.objects.all()
    s = JenkinsJobIdMapSerializer(all_entries, many=True)
    s = s.data
    # print s
    s = sorted(s, key=lambda x: x["fun_sdk_branch"], reverse=True)
    return s

@csrf_exempt
@api_safe_json_response
def build_to_date_map(request):
    all_entries = JenkinsJobIdMap.objects.all()
    build_info = {}
    for entry in all_entries:
        sdk_branch = entry.fun_sdk_branch
        m = re.search(r'refs/tags/bld_(\d+)', sdk_branch)
        key = 0
        if m:
            key = int(m.group(1))
        # print "Completion date:" + entry.completion_date
        try:
            key = entry.completion_date
            dt = get_localized_time(datetime.strptime(entry.completion_date, "%Y-%m-%d %H:%M"))
            dt = dt + timedelta(hours=7)  #TODO: hardcoded
            key = str(dt)
            key = re.sub(r':\d{2}-.*', '', key)
            build_info[key] = {"software_date": entry.software_date,
                                                 "hardware_version": entry.hardware_version,
                                                 "fun_sdk_branch": entry.fun_sdk_branch,
                                                 "git_commit": entry.git_commit}
            # print str(dt)
        except Exception as ex:
            print ex
            # pass
    return build_info


@csrf_exempt
def catalog_test_case_execution_summary_result_multiple_jiras(request):
    result = initialize_result(failed=True)
    try:
        request_json = json.loads(request.body)
        suite_execution_id = request_json["suite_execution_id"]
        jira_ids = request_json["jira_ids"]
        result["status"] = True
        result["data"] = get_catalog_test_case_execution_summary_result_multiple_jiras(suite_execution_id=suite_execution_id,
                                                                        jira_ids=jira_ids)
    except Exception as ex:
        result["error_message"] = str(ex)
    return HttpResponse(json.dumps(result))

@csrf_exempt
def update_test_case_execution(request):
    result = initialize_result(failed=True)
    request_json = json.loads(request.body)
    override_result = None
    bugs = None
    owner_email = None
    if "override_result" in request_json:
        override_result = request_json["override_result"]
    if "bugs" in request_json:
        bugs = request_json["bugs"]

    if "owner_email" in request_json:
        owner_email = request_json["owner_email"]
    execution_id = int(request_json["execution_id"])
    try:
        te = TestCaseExecution.objects.get(execution_id=execution_id)
        if override_result:
            te.result = override_result
            te.overridden_result = True
        if bugs:
            te.bugs = bugs
        if owner_email:
            cte = CatalogTestCaseExecution.objects.get(execution_id=execution_id)
            cte.engineer = Engineer.objects.get(email=owner_email)
            cte.save()
        te.save()
        suite_execution_id = te.suite_execution_id
        summary_result = get_catalog_test_case_execution_summary_result(suite_execution_id=suite_execution_id, jira_id=te.test_case_id)
        result["status"] = True
        result["data"] = summary_result
    except Exception as ex:
        logger.critical(str(ex))

    return HttpResponse(json.dumps(result))


def test(request):
    return render(request, 'qa_dashboard/test.html', locals())
