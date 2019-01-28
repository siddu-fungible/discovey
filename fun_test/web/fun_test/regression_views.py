import json
import os
from web.fun_test.settings import COMMON_WEB_LOGGER_NAME
from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers, paginator
from fun_global import RESULTS, get_datetime_from_epoch_time, get_epoch_time_from_datetime
from fun_settings import LOGS_RELATIVE_DIR, SUITES_DIR, LOGS_DIR, MAIN_WEB_APP
from scheduler.scheduler_helper import LOG_DIR_PREFIX, queue_job, re_queue_job, queue_job2, queue_suite_container
import scheduler.scheduler_helper
from models_helper import _get_suite_executions, _get_suite_execution_attributes, SUITE_EXECUTION_FILTERS, get_test_case_details, get_all_test_cases
from web.fun_test.models import SuiteExecution, TestCaseExecution, Tag, Engineer, CatalogTestCaseExecution
from django.core.exceptions import ObjectDoesNotExist
from web.fun_test.models import CatalogSuiteExecution, Module
from web.fun_test.models import JenkinsJobIdMap, JenkinsJobIdMapSerializer
from web.web_global import initialize_result, api_safe_json_response, string_to_json
import glob, collections
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from fun_global import get_localized_time
from datetime import datetime, timedelta
from web.fun_test.models import RegresssionScripts, RegresssionScriptsSerializer, SuiteExecutionSerializer
from web.fun_test.models import ScriptInfo
from web.fun_test.models import TestCaseExecutionSerializer
import logging
import dateutil.parser
import re
from django.apps import apps
import time
from django.db import transaction
from django.db.models import Q



logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)
app_config = apps.get_app_config(app_label=MAIN_WEB_APP)

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
    return render(request, 'qa_dashboard/angular_home.html', locals())

def submit_job_page(request):
    return render(request, 'qa_dashboard/submit_job_page.html')


@csrf_exempt
@api_safe_json_response
def suite_re_run(request, suite_execution_id):
    return re_queue_job(suite_execution_id=suite_execution_id)

@csrf_exempt
@api_safe_json_response
def test_case_re_run(request):
    request_json = json.loads(request.body)
    suite_execution_id = request_json["suite_execution_id"]
    test_case_execution_id = request_json["test_case_execution_id"]
    script_path = request_json["script_path"]

    return re_queue_job(suite_execution_id=suite_execution_id,
                                     test_case_execution_id=test_case_execution_id,
                                     script_path=script_path)

@csrf_exempt
@api_safe_json_response
def submit_job(request):
    job_id = 0
    if request.method == 'POST':
        request_json = json.loads(request.body)
        suite_path = request_json["suite_path"]
        build_url = request_json["build_url"]
        tags = None
        if "tags" in request_json:
            tags = request_json["tags"]
        email_list = None
        email_on_fail_only = None
        environment = None
        if "environment" in request_json:
            environment = request_json["environment"]
        if "email_list" in request_json:
            email_list = request_json["email_list"]
        if "email_on_fail_only" in request_json:
            email_on_fail_only = request_json["email_on_fail_only"]

        scheduling_type = "asap"
        if "scheduling_type" in request_json:
            scheduling_type = request_json["scheduling_type"]
        tz = "PST"
        if "timezone" in request_json:
            tz = request_json["timezone"]
        requested_days = []
        requested_hour = None
        requested_minute = None
        repeat_in_minutes = -1

        if "requested_days" in request_json:
            requested_days = request_json["requested_days"]
            requested_days = [x.lower() for x in requested_days]
        if "requested_hour" in request_json:
            requested_hour = request_json["requested_hour"]
        if "requested_minute" in request_json:
            requested_minute = request_json["requested_minute"]
        if "repeat_in_minutes" in request_json:
            repeat_in_minutes = request_json["repeat_in_minutes"]

        if suite_path.replace(".json", "").endswith("_container"):
            job_id = queue_suite_container(suite_path=suite_path,
                       build_url=build_url,
                       tags=tags,
                       email_list=email_list,
                       email_on_fail_only=email_on_fail_only,
                       environment=environment,
                       scheduling_type=scheduling_type,
                       tz_string=tz,
                       requested_hour=requested_hour,
                       requested_minute=requested_minute,
                       requested_days=requested_days,
                                repeat_in_minutes=repeat_in_minutes)
        else:
            job_id = queue_job2(suite_path=suite_path,
                       build_url=build_url,
                       tags=tags,
                       email_list=email_list,
                       email_on_fail_only=email_on_fail_only,
                       environment=environment,
                       scheduling_type=scheduling_type,
                       tz_string=tz,
                       requested_hour=requested_hour,
                       requested_minute=requested_minute,
                       requested_days=requested_days,
                                repeat_in_minutes=repeat_in_minutes)
        '''
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
                               email_on_fail_only=email_on_fail_only,
                               environment=environment)

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
                               email_on_fail_only=email_on_fail_only,
                               environment=environment)
        else:
            job_id = queue_job(suite_path=suite_path,
                               build_url=build_url,
                               tags=tags,
                               email_list=email_list,
                               email_on_fail_only=email_on_fail_only, environment=environment)
        '''
    return job_id

def static_serve_log_directory(request, suite_execution_id):
    path = LOGS_DIR + "/" + LOG_DIR_PREFIX + str(suite_execution_id) + "/*"
    files = glob.glob(path)
    files = [os.path.basename(f) for f in files]
    return render(request, 'qa_dashboard/list_directory.html', locals())


@csrf_exempt
@api_safe_json_response
def kill_job(request, suite_execution_id):
    scheduler.scheduler_helper.kill_job(job_id=suite_execution_id)
    suite_execution = SuiteExecution.objects.get(execution_id=suite_execution_id)
    suite_execution.result = RESULTS["KILLED"]
    suite_execution.save()
    return "OK"

@csrf_exempt
@api_safe_json_response
def tags(request):
    return serializers.serialize('json', Tag.objects.all())

def engineers(request):
    result = initialize_result(failed=True)
    s = serializers.serialize('json', Engineer.objects.all())
    s = json.loads(s)  #TODO
    result["data"] = s
    result["status"] = True
    return HttpResponse(json.dumps(result))

def parse_suite(suite_file):
    with open(suite_file, "r") as infile:
        contents = infile.read()
        items = json.loads(contents)
        return items

@csrf_exempt
@api_safe_json_response
def suites(request):

    suites_info = collections.OrderedDict()
    suite_files = glob.glob(SUITES_DIR + "/*.json")
    for suite_file in suite_files:
        try:
            if suite_file.endswith("container.json"):
                suites_info[os.path.basename(suite_file)] = []
                inner_suites = parse_suite(suite_file=suite_file)
                for inner_suite in inner_suites:
                    items = parse_suite(suite_file=SUITES_DIR + "/" + inner_suite)
                    # suites_info.extend(items)
                    suites_info[os.path.basename(suite_file)].extend(items)
            else:
                items = parse_suite(suite_file=suite_file)
                suites_info[os.path.basename(suite_file)] = items
                # suites_info.extend(items)

        except Exception as ex:
            pass
    return suites_info

@csrf_exempt
@api_safe_json_response
def suite_executions_count(request, filter_string):
    tags = None
    if request.method == 'POST':
        if request.body:
            request_json = json.loads(request.body)
            if "tags" in request_json:
                tags = request_json["tags"]
                tags = json.loads(tags)
    count = _get_suite_executions(get_count=True, filter_string=filter_string, tags=tags)
    return count

@csrf_exempt
@api_safe_json_response
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
    return json.dumps(all_objects_dict)
    # return all_objects_dict

@csrf_exempt
@api_safe_json_response
def suite_execution(request, execution_id):
    all_objects_dict = _get_suite_executions(execution_id=int(execution_id))
    # return json.dumps(all_objects_dict[0]) #TODO: Validate
    return all_objects_dict[0]

@csrf_exempt
@api_safe_json_response
def last_jenkins_hourly_execution_status(request):
    result = RESULTS["UNKNOWN"]
    suite_executions = _get_suite_executions(tags=["jenkins-hourly"],
                                             filter_string=SUITE_EXECUTION_FILTERS["COMPLETED"],
                                             page=1, records_per_page=10)
    if suite_executions:
        result = suite_executions[0]["suite_result"]
    return result

def suite_detail(request, execution_id):
    all_objects_dict = _get_suite_executions(execution_id=execution_id)
    suite_execution = all_objects_dict[0]
    suite_execution_attributes = _get_suite_execution_attributes(suite_execution=suite_execution)
    return render(request, 'qa_dashboard/angular_home.html', locals())

@csrf_exempt
@api_safe_json_response
def suite_execution_attributes(request, execution_id):
    all_objects_dict = _get_suite_executions(execution_id=execution_id)
    suite_execution = all_objects_dict[0]
    suite_execution_attributes = _get_suite_execution_attributes(suite_execution=suite_execution)
    return suite_execution_attributes

@csrf_exempt
@api_safe_json_response
def log_path(request):
    return LOGS_RELATIVE_DIR + "/" + LOG_DIR_PREFIX

@csrf_exempt
@api_safe_json_response
def test_case_execution(request, suite_execution_id, test_case_execution_id):
    test_case_execution_obj = TestCaseExecution.objects.get(suite_execution_id=suite_execution_id,
                                                        execution_id=test_case_execution_id)
    test_case_execution_obj.started_time = timezone.localtime(test_case_execution_obj.started_time)
    test_case_execution_obj.end_time = timezone.localtime(test_case_execution_obj.end_time)

    # lock = app_config.get_site_lock()
    # lock.acquire()
    # print "Ac"
    details = get_test_case_details(script_path=test_case_execution_obj.script_path, test_case_id=test_case_execution_obj.test_case_id)
    # print "Rel"
    # lock.release()
    # test_case_execution_obj.summary = details["summary"]
    # data = serializers.serialize('json', [test_case_execution_obj])
    serializer = TestCaseExecutionSerializer(test_case_execution_obj)
    # setattr(serializer.data, "summary", details["summary"])
    return {"execution_obj": serializer.data, "more_info": {"summary": details["summary"]}}

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
def script_history(request):
    request_json = json.loads(request.body)
    script_path = request_json["script_path"]

@csrf_exempt
@api_safe_json_response
def scripts_by_module(request, module):
    matched_scripts = []
    regression_scripts = RegresssionScripts.objects.all()
    for regression_script in regression_scripts:
        modules = regression_script.modules
        modules = json.loads(modules)
        if module in modules:
            serializer = RegresssionScriptsSerializer(regression_script)
            matched_scripts.append(serializer.data)
    return matched_scripts

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

            if (dt.year == 2018 and ((dt.month == 11 and dt.day >= 4) or dt.month > 11)) or (dt.year == 2019 and ((dt.month < 3) or (dt.month == 3 and dt.day < 10))):
                dt = dt + timedelta(hours=8)  #TODO: hardcoded
            else:
                dt = dt + timedelta(hours=7)  # TODO: hardcoded
            key = str(dt)
            key = re.sub(r':\d{2}-.*', '', key)
            build_info[key] = {"software_date": entry.software_date,
                                                 "hardware_version": entry.hardware_version,
                                                 "fun_sdk_branch": entry.fun_sdk_branch,
                                                 "git_commit": entry.git_commit,
                                                 "build_properties": entry.build_properties}
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

def suite_execution_properties(suite_execution_id, properties):
    result = {}
    try:
        suite_execution = SuiteExecution.objects.get(execution_id=suite_execution_id)
        for property in properties:
            result[property] = getattr(suite_execution, property)
    except ObjectDoesNotExist:
        pass
    return result

@csrf_exempt
@api_safe_json_response
def get_suite_execution_properties(request):
    request_json = string_to_json(request.body)
    suite_execution_id = request_json["suite_execution_id"]
    properties = request_json["properties"]
    return suite_execution_properties(suite_execution_id=suite_execution_id, properties=properties)

@csrf_exempt
@api_safe_json_response
def get_all_versions(request):
    ses = SuiteExecution.objects.values('version', 'execution_id', 'scheduled_time')
    result = []
    for se in ses:
        scheduled_time_in_epoch = get_epoch_time_from_datetime(se['scheduled_time'])
        new_entry = {"version": se["version"], "execution_id": se["execution_id"], "scheduled_time": scheduled_time_in_epoch}
        result.append(new_entry)
    return result

@csrf_exempt
@api_safe_json_response
def get_script_history(request):
    history = []
    request_json = json.loads(request.body)
    script_path = request_json["script_path"]
    tes = TestCaseExecution.objects.filter(script_path=script_path).order_by("-suite_execution_id")[:100]
    start = time.time()

    for te in tes:
        # version = suite_execution_properties(te.suite_execution_id, "version")
        new_entry = {"suite_execution_id": te.suite_execution_id,
                     "execution_id": te.execution_id,
                     "result": te.result}
        #serializer = TestCaseExecutionSerializer(te)
        #history.append(serializer.data)
        history.append(new_entry)
    return history

@csrf_exempt
@api_safe_json_response
def get_suite_executions_by_time(request):
    request_json = json.loads(request.body)
    from_time = int(request_json["from_time"])
    to_time = request_json["to_time"]
    from_time = get_datetime_from_epoch_time(from_time)
    to_time = get_datetime_from_epoch_time(to_time)
    suite_executions = SuiteExecution.objects.filter(scheduled_time__gte=from_time, scheduled_time__lte=to_time)
    suite_executions = SuiteExecutionSerializer(suite_executions, many=True)
    return suite_executions.data

@csrf_exempt
@api_safe_json_response
def get_test_case_executions_by_time(request):
    request_json = json.loads(request.body)
    from_time = 1541030400 * 1000
    # from_time = int(request_json["from_time"])
    # to_time = request_json["to_time"]
    from_time = get_datetime_from_epoch_time(from_time)
    # to_time = get_datetime_from_epoch_time(to_time)
    test_case_execution_tags = None
    if "test_case_execution_tags" in request_json:
        test_case_execution_tags = request_json["test_case_execution_tags"]
    module = None
    scripts_for_module = None
    q = None
    if "module" in request_json:
        module = request_json["module"]
        module_str = '"{}"'.format(module)
        q = Q(modules__contains=module_str)
        scripts_for_module = RegresssionScripts.objects.filter(q)
        scripts_for_module = [x.script_path for x in scripts_for_module]

    tes = []
    q = Q(started_time__gte=from_time)

    if test_case_execution_tags:
        for tag in test_case_execution_tags:
            tag_str = '"{}"'.format(tag)
            q = q & Q(tags__contains=tag_str)
    if "script_path" in request_json:
        q = q & Q(script_path=request_json["script_path"])

    test_case_executions = TestCaseExecution.objects.filter(q)

    for te in test_case_executions:
        if scripts_for_module:
            if te.script_path not in scripts_for_module:
                continue
        one_entry = {"execution_id": te.execution_id,
                     "suite_execution_id": te.suite_execution_id,
                     "script_path": te.script_path,
                     "test_case_id": te.test_case_id,
                     "result": te.result,
                     "started_time": te.started_time}
        tes.append(one_entry)

    return tes


@csrf_exempt
@api_safe_json_response
def scripts(request):
    all_regression_scripts = RegresssionScripts.objects.all()
    # regression_serializer = RegresssionScriptsSerializer(all_regression_scripts, many=True)
    regression_scripts = []
    for regression_script in all_regression_scripts:
        new_entry = {"script_path": regression_script.script_path,
                     "modules": json.loads(regression_script.modules),
                     "components": json.loads(regression_script.components),
                     "tags": json.loads(regression_script.tags),
                     "pk": regression_script.pk,
                     "bugs": [],
                     "test_cases": get_all_test_cases(regression_script.script_path),
                     "baseline_suite_execution_id": regression_script.baseline_suite_execution_id}
        script_infos = ScriptInfo.objects.filter(script_id=regression_script.pk)
        for script_info in script_infos:
            new_entry["bugs"].append(script_info.bug)
        regression_scripts.append(new_entry)
    # regression_scripts = regression_serializer.data
    return regression_scripts

@csrf_exempt
@api_safe_json_response
def script(request):
    result = None
    request_json = json.loads(request.body)
    script_path = None
    pk = None
    if "script_path" in request_json:
        script_path = request_json["script_path"]
    if "pk" in request_json:
        pk = request_json["pk"]
    module_names = None

    if "modules" in request_json:
        modules = request_json["modules"]
        module_names = [x["name"] for x in modules]
    if module_names:
        try:
            r = RegresssionScripts.objects.get(script_path=script_path)
            r.modules = json.dumps(module_names)
            r.save()
        except ObjectDoesNotExist:
            r = RegresssionScripts(script_path=script_path, modules=json.dumps(module_names))
            r.save()
    else:
        try:
            r = None
            if script_path:
                r = RegresssionScripts.objects.get(script_path=script_path)
            elif pk:
                r = RegresssionScripts.objects.get(pk=pk)
            result = {"pk": r.pk, "script_path": r.script_path}
        except ObjectDoesNotExist as ex:
            logging.error("Script: {} does not exist. {}".format(script_path, str(ex)))
    return result

@csrf_exempt
@api_safe_json_response
def script_update(request, pk):
    result = None
    request_json = json.loads(request.body)
    q = Q(pk=pk)
    script = RegresssionScripts.objects.get(q)
    if script:
        if "baseline_suite_execution_id" in request_json:
            script.baseline_suite_execution_id = request_json["baseline_suite_execution_id"]
        script.save()
    else:
        logging.error("Could not find script with pk: {}".format(pk))

    return result


@csrf_exempt
@api_safe_json_response
def unallocated_script(request):
    unallocated_scripts = []
    suites_info = collections.OrderedDict()
    suite_files = glob.glob(SUITES_DIR + "/*.json")
    for suite_file in suite_files:
        try:
            with open(suite_file, "r") as infile:
                contents = infile.read()
                result = json.loads(contents)
                for entry in result:
                    if "path" in entry:
                        path = entry["path"]
                        path = "/" + path
                        try:
                            RegresssionScripts.objects.get(script_path=path)
                        except ObjectDoesNotExist:
                            if path not in unallocated_scripts:
                                unallocated_scripts.append(path)
        except Exception as ex:
            logging.error(str(ex))
    return unallocated_scripts



def test(request):
    return render(request, 'qa_dashboard/test.html', locals())


def validate_jira(jira_id):
    project_name, id = jira_id.split('-')
    jira_obj = app_config.get_jira_manager()
    query = 'project="' + str(project_name) + '" and id="' + str(jira_id) + '"'
    try:
        jira_valid = jira_obj.get_issues_by_jql(jql=query)
        if jira_valid:
            jira_valid = jira_valid[0]
            return jira_valid
    except Exception:
        return None
    return None


@api_safe_json_response
def all_regression_jiras(request):
    result = None
    if request.method == "GET":
        jira_info = {}

        try:
            scripts = ScriptInfo.objects.all()
            if scripts:
                for script in scripts:
                    if script.bug:
                        jira_id = script.bug
                        jira_response = validate_jira(jira_id)
                        jira_data = {}
                        jira_data["id"] = jira_id
                        jira_data["summary"] = jira_response.fields.summary
                        jira_data["status"] = jira_response.fields.status
                        jira_info[jira_id] = jira_data

            result = jira_info
        except ObjectDoesNotExist:
            logger.critical("No data found - fetching jira ids")
    return result

@csrf_exempt
@api_safe_json_response
def jiras(request, script_pk, jira_id=None):
    result = None
    if request.method == "POST":
        try:
            request_json = json.loads(request.body)
            jira_id = request_json["jira_id"]
            c = RegresssionScripts.objects.get(pk=script_pk)

            if jira_id:
                jira_info = validate_jira(jira_id)
                if jira_info:
                    try:
                        script_info = ScriptInfo.objects.get(script_id=script_pk, bug=jira_id)
                    except ObjectDoesNotExist:
                        script_info = ScriptInfo(script_id=script_pk, bug=jira_id)
                        script_info.save()
                else:
                    raise ObjectDoesNotExist
            result = "Ok"
        except ObjectDoesNotExist as obj:
            logger.critical("No data found - updating jira ids for script Id {} jira Id: {}".format(script_pk, jira_id))
    if request.method == "GET":
        jira_info = {}
        try:
            c = RegresssionScripts.objects.get(pk=script_pk)
            try:
                scripts = ScriptInfo.objects.filter(script_id=script_pk)
                if scripts:
                    for script in scripts:
                        if script.bug:
                            jira_id = script.bug
                            jira_response = validate_jira(jira_id)
                            jira_data = {}
                            jira_data["id"] = jira_id
                            jira_data["summary"] = jira_response.fields.summary
                            jira_data["status"] = jira_response.fields.status
                            jira_info[jira_id] = jira_data

            except ObjectDoesNotExist:
                pass
            result = jira_info
        except ObjectDoesNotExist:
            logger.critical("No data found - fetching jira ids for script pk id {}".format(script_pk))
    if request.method == "DELETE":
        try:
            c = RegresssionScripts.objects.get(pk=script_pk)
            if jira_id:
                script_info = ScriptInfo.objects.get(script_id=script_pk, bug=jira_id)
                script_info.delete()
            result = True
        except ObjectDoesNotExist:
            logger.critical("No data found - Deleting jira ids for script pk id {}".format(script_pk))
        return "Ok"
    return result


@csrf_exempt
@api_safe_json_response
def script_execution(request, pk):
    result = None
    try:
        request_json = json.loads(request.body)
        r = RegresssionScripts.objects.get(pk=pk)
        script_path = r.script_path
        q = Q(script_path=script_path)
        if "suite_execution_id" in request_json:
            suite_execution_id = request_json["suite_execution_id"]
            q = q & Q(suite_execution_id=suite_execution_id)
        test_case_executions = TestCaseExecution.objects.filter(q)
        result = {}
        for test_case_execution in test_case_executions:
            result[test_case_execution.test_case_id] = {"execution_id": test_case_execution.execution_id, "result": test_case_execution.result}
    except ObjectDoesNotExist:
        raise Exception("Script with pk: {} does not exist".format(pk))
    return result
