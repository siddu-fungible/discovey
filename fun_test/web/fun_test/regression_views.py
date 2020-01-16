import json
import os
from web.fun_test.settings import COMMON_WEB_LOGGER_NAME
from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers, paginator
from fun_global import RESULTS, get_datetime_from_epoch_time, get_epoch_time_from_datetime
from fun_global import is_production_mode, is_triaging_mode, get_current_time
from fun_settings import LOGS_RELATIVE_DIR, SUITES_DIR, LOGS_DIR, MAIN_WEB_APP, DEFAULT_BUILD_URL, SCRIPTS_DIR
from fun_settings import TASKS_DIR
from scheduler.scheduler_helper import queue_dynamic_suite, queue_job3, LOG_DIR_PREFIX
from scheduler.scheduler_helper import move_to_higher_queue, move_to_queue_head, increase_decrease_priority, delete_queued_job
import scheduler.scheduler_helper
from models_helper import _get_suite_executions, _get_suite_execution_attributes, SUITE_EXECUTION_FILTERS, \
    get_test_case_details, get_all_test_cases
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
from web.fun_test.models import SuiteReRunInfo, JobQueue, Suite
from web.fun_test.models import SuiteReRunInfo
from web.fun_test.models import TestBed
from lib.utilities.send_mail import send_mail
from web.fun_test.web_interface import get_suite_detail_url
from web.fun_test.models import User, SiteConfig
from web.fun_test.models import SuiteType
from scheduler.scheduler_global import SchedulingType
import logging
import subprocess
import dateutil.parser
import re
from django.apps import apps
import time
import glob
from django.db import transaction
from django.db.models import Q
from scheduler.scheduler_global import SchedulerJobPriority, QueueOperations
from fun_settings import TEAM_REGRESSION_EMAIL
import datetime
from django.utils import timezone

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
    angular_home = 'qa_dashboard/angular_home_development.html'
    if is_production_mode():
        angular_home = 'qa_dashboard/angular_home_production.html'
    return render(request, angular_home, locals())


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
    submitter_email = None
    if request.method == 'POST':
        request_json = json.loads(request.body)

        # suite path
        suite_path = request_json.get("suite_path", None)

        suite_id = request_json.get("suite_id", None)
        if not suite_id and suite_path:
            suite = Suite.objects.filter(name=suite_path)
            if suite.count():
                suite_id = suite[0].id
        submitter_email = request_json.get("submitter_email", "john.abraham@fungible.com")

        # script path used for script only submission
        script_pk = request_json.get("script_pk", None)

        # dynamic suite spec
        dynamic_suite_spec = request_json.get("dynamic_suite_spec", None)
        original_suite_execution_id = request_json.get("original_suite_execution_id", None)

        build_url = request_json.get("build_url", None)
        version = request_json.get("version", None)
        if not build_url and version:
            clean_version = re.sub("(\d+)(\D.*)", r'\1', request_json["version"])     #TODO:
            build_url = DEFAULT_BUILD_URL.replace("latest", clean_version)

        test_bed_type = request_json.get("test_bed_type", None)
        suite_type = request_json.get("suite_type", SuiteType.STATIC)
        tags = request_json.get("tags", None)
        emails = request_json.get("emails", None)
        email_on_fail_only = request_json.get("email_on_fail_only", None)
        email_list = request_json.get("email_list", None)
        environment = request_json.get("environment", None)
        if email_list:
            emails = request_json["email_list"]                      # TODO:

        scheduling_type = request_json.get("scheduling_type", SchedulingType.ASAP)
        tz = request_json.get("timezone", "PST")

        inputs = request_json.get("job_inputs", None)
        requested_days = request_json.get("requested_days", [])       # TODO:
        if requested_days:
            requested_days = [x.lower() for x in requested_days]

        requested_hour = request_json.get("requested_hour", None)
        requested_minute = request_json.get("requested_minute", None)
        repeat_in_minutes = request_json.get("repeat_in_minutes", -1)  # TODO:
        description = request_json.get("description", None)

        rich_inputs = request_json.get("rich_inputs", None)
        max_run_time = request_json.get("max_run_time", 7 * 24 * 3600)
        pause_on_failure = request_json.get("pause_on_failure", False)

        # if suite_path:
        if suite_id:
            job_id = queue_job3(suite_id=suite_id,
                                build_url=build_url,
                                tags=tags,
                                emails=emails,
                                test_bed_type=test_bed_type,
                                email_on_fail_only=email_on_fail_only,
                                environment=environment,
                                scheduling_type=scheduling_type,
                                timezone_string=tz,
                                requested_hour=requested_hour,
                                requested_minute=requested_minute,
                                requested_days=requested_days,
                                repeat_in_minutes=repeat_in_minutes,
                                submitter_email=submitter_email,
                                inputs=inputs,
                                description=description,
                                suite_type=suite_type,
                                rich_inputs=rich_inputs,
                                max_run_time=max_run_time,
                                pause_on_failure=pause_on_failure)
        elif script_pk:
            script_path = RegresssionScripts.objects.get(pk=script_pk).script_path
            job_id = queue_job3(script_path=script_path,
                                build_url=build_url,
                                tags=tags,
                                emails=emails,
                                test_bed_type=test_bed_type,
                                email_on_fail_only=email_on_fail_only,
                                environment=environment,
                                scheduling_type=scheduling_type,
                                timezone_string=tz,
                                requested_hour=requested_hour,
                                requested_minute=requested_minute,
                                requested_days=requested_days,
                                repeat_in_minutes=repeat_in_minutes,
                                submitter_email=submitter_email,
                                inputs=inputs,
                                description=description,
                                suite_type=suite_type,
                                rich_inputs=rich_inputs,
                                max_run_time=max_run_time,
                                pause_on_failure=pause_on_failure)
        elif dynamic_suite_spec:
            job_id = queue_dynamic_suite(dynamic_suite_spec=dynamic_suite_spec,
                                         emails=emails,
                                         environment=environment,
                                         inputs=inputs,
                                         test_bed_type=test_bed_type,
                                         original_suite_execution_id=original_suite_execution_id,
                                         build_url=build_url,
                                         submitter_email=submitter_email,
                                         max_run_time=max_run_time)
    if job_id > 0 and submitter_email:
        submitter_user_name = ""
        try:
            user = User.objects.get(email=submitter_email)
            submitter_user_name = "{} {}".format(user.first_name, user.last_name)
        except ObjectDoesNotExist:
            pass

        contents = "Hi {}".format(submitter_user_name) + "<br>"
        contents += "Your Integration job's progress can be tracked at {}".format(get_suite_detail_url(suite_execution_id=job_id)) + "<br>"
        contents += "Thank you<br>Regression team<br>"
        send_mail(to_addresses=[submitter_email], subject="Regression: Integration Job: {} submitted".format(job_id), content=contents)
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
    return suite_execution_id


@csrf_exempt
@api_safe_json_response
def tags(request):
    return serializers.serialize('json', Tag.objects.all())


def engineers(request):
    result = initialize_result(failed=True)
    s = serializers.serialize('json', Engineer.objects.all())
    s = json.loads(s)  # TODO
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
    suite_path = None
    suite_type = SuiteType.STATIC
    if request.method == 'POST':
        if request.body:
            request_json = json.loads(request.body)
            suite_path = request_json["suite_path"]
            if not suite_path.endswith(".json"):
                suite_path += ".json"

    suite_type = request.GET.get("suite_type", SuiteType.STATIC)
    suites_info = collections.OrderedDict()
    suite_files = []
    if suite_type == SuiteType.STATIC:
        suite_files = glob.glob(SUITES_DIR + "/*.json")
    elif suite_type == SuiteType.TASK:
        suite_files = glob.glob(TASKS_DIR + "/*.json")

    for suite_file in suite_files:
        if suite_path:
            if not suite_file.endswith("/{}".format(suite_path)):
                continue
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
            logging.error("suites: {}".format(str(ex)))
    return suites_info


@csrf_exempt
@api_safe_json_response
def suite_executions_count(request, state_filter_string):
    tags = None
    count = 0
    if request.method == 'POST':
        if request.body:
            request_json = json.loads(request.body)
            if "tags" in request_json:
                tags = request_json["tags"]
                # tags = json.loads(tags)
            if "tag" in request_json:
                tags = [request_json["tag"]]

            submitter_email = request_json.get('submitter_email', None)
            test_bed_type = request_json.get('test_bed_type', None)
            suite_path = request_json.get('suite_path', None)

            count = _get_suite_executions(get_count=True,
                                          state_filter_string=state_filter_string,
                                          tags=tags,
                                          submitter_email=submitter_email,
                                          test_bed_type=test_bed_type, suite_path=suite_path, save_suite_info=False)
    return count


@csrf_exempt
@api_safe_json_response
def suite_executions(request, records_per_page=10, page=None, state_filter_string="ALL"):
    tags = None
    all_objects_dict = None
    if request.method == 'POST':
        if request.body:
            request_json = json.loads(request.body)
            if "tags" in request_json:
                tags = request_json["tags"]
                tags = json.loads(tags)

            if "tag" in request_json:
                tags = [request_json["tag"]]
            submitter_email = request_json.get('submitter_email', None)
            test_bed_type = request_json.get('test_bed_type', None)
            suite_path = request_json.get('suite_path', None)
            all_objects_dict = _get_suite_executions(execution_id=None,
                                                     page=page,
                                                     records_per_page=records_per_page,
                                                     state_filter_string=state_filter_string,
                                                     tags=tags,
                                                     submitter_email=submitter_email,
                                                     test_bed_type=test_bed_type,
                                                     suite_path=suite_path)
    return all_objects_dict
    # return all_objects_dict


@csrf_exempt
@api_safe_json_response
def suite_execution(request, execution_id):
    all_objects_dict = _get_suite_executions(execution_id=int(execution_id))
    # return json.dumps(all_objects_dict[0]) #TODO: Validate
    return all_objects_dict[0]


def suite_detail(request, execution_id):
    all_objects_dict = _get_suite_executions(execution_id=execution_id)
    suite_execution = all_objects_dict[0]
    suite_execution_attributes = _get_suite_execution_attributes(suite_execution=suite_execution)
    site_version = SiteConfig.get_version()
    angular_home = 'qa_dashboard/angular_home_development.html'
    if is_production_mode() and not is_triaging_mode():
        angular_home = 'qa_dashboard/angular_home_production.html'
    return render(request, angular_home, locals())


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

    details = get_test_case_details(script_path=test_case_execution_obj.script_path,
                                    test_case_id=test_case_execution_obj.test_case_id)

    serializer = TestCaseExecutionSerializer(test_case_execution_obj)
    # setattr(serializer.data, "summary", details["summary"])
    script_id = None
    try:
        regression_script = RegresssionScripts.objects.get(script_path=test_case_execution_obj.script_path)
        script_id = regression_script.id
    except ObjectDoesNotExist:
        pass

    return {"execution_obj": serializer.data, "more_info": {"summary": details["summary"]}, "script_id": script_id}


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
    end_date = get_current_time()
    start_date = end_date - timedelta(days=30)
    date_range = [start_date, end_date]
    filtered_entries = JenkinsJobIdMap.objects.filter(build_date__range=date_range).order_by("build_date")
    build_info = {}
    for entry in filtered_entries:
        try:
            # key = timezone.localtime(entry.build_date)
            key = get_epoch_time_from_datetime(entry.build_date)
            build_info[key] = {"software_date": entry.software_date,
                               "hardware_version": entry.hardware_version,
                               "fun_sdk_branch": entry.fun_sdk_branch,
                               "git_commit": entry.git_commit,
                               "build_properties": entry.build_properties,
                               "lsf_job_id": entry.lsf_job_id,
                               "sdk_version": entry.sdk_version,
                               "suite_execution_id": entry.suite_execution_id,
                               "associated_suites": entry.associated_suites}
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
        result["data"] = get_catalog_test_case_execution_summary_result_multiple_jiras(
            suite_execution_id=suite_execution_id,
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
        summary_result = get_catalog_test_case_execution_summary_result(suite_execution_id=suite_execution_id,
                                                                        jira_id=te.test_case_id)
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
        new_entry = {"version": se["version"], "execution_id": se["execution_id"],
                     "scheduled_time": scheduled_time_in_epoch}
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
        # serializer = TestCaseExecutionSerializer(te)
        # history.append(serializer.data)
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
    days_in_past = int(request.GET.get("days_in_past", 10))
    started_time = get_current_time() - timedelta(days=days_in_past)
    # from_time = 1546581539 * 1000
    # from_time = int(request_json["from_time"])
    # to_time = request_json["to_time"]
    # from_time = get_datetime_from_epoch_time(from_time)
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
    q = Q(started_time__gte=started_time)

    if test_case_execution_tags:
        for tag in test_case_execution_tags:
            tag_str = '"{}"'.format(tag)
            q = q & Q(tags__contains=tag_str)
    if "script_path" in request_json:
        q = q & Q(script_path=request_json["script_path"])

    test_case_executions = TestCaseExecution.objects.filter(q).order_by('started_time')
    re_run_info = {}
    for te in test_case_executions:
        if scripts_for_module:
            if te.script_path not in scripts_for_module:
                continue
        if te.suite_execution_id not in re_run_info:
            if SuiteReRunInfo.objects.filter(re_run_suite_execution_id=te.suite_execution_id).count() > 0:
                re_run_info[te.suite_execution_id] = True
            else:
                re_run_info[te.suite_execution_id] = False

        one_entry = {"execution_id": te.execution_id,
                     "suite_execution_id": te.suite_execution_id,
                     "script_path": te.script_path,
                     "test_case_id": te.test_case_id,
                     "result": te.result,
                     "started_time": te.started_time,
                     "is_re_run": re_run_info[te.suite_execution_id]}
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
                     "id": regression_script.id,
                     "baseline_suite_execution_id": regression_script.baseline_suite_execution_id}
        if "__init__.py" in regression_script.script_path:
            continue
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
def script_update(request, id):
    result = None
    request_json = json.loads(request.body)
    q = Q(id=id)
    script = RegresssionScripts.objects.get(q)
    if script:
        if "baseline_suite_execution_id" in request_json:
            script.baseline_suite_execution_id = request_json["baseline_suite_execution_id"]
        script.save()
    else:
        logging.error("Could not find script with id: {}".format(id))

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
    bug_files = glob.glob(SCRIPTS_DIR + "/bugs_and_analyses/*.py")
    bug_files = [x.replace(SCRIPTS_DIR, "") for x in bug_files]
    bug_files = filter(lambda x: "__init__.py" not in x, bug_files)
    bug_files = filter(lambda x: RegresssionScripts.objects.filter(script_path=x).count() == 0, bug_files)
    map(unallocated_scripts.append, bug_files)
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
                        jira_data["priority"] = jira_response.fields.priority
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
            if script_pk:
                c = RegresssionScripts.objects.get(pk=script_pk)
            try:
                q = Q()
                if script_pk is not None:
                    q = q & Q(script_id=script_pk)

                scripts = ScriptInfo.objects.filter(q)
                if scripts:
                    for script in scripts:
                        if script.bug:
                            jira_id = script.bug
                            jira_response = validate_jira(jira_id)
                            jira_data = {}
                            jira_data["id"] = jira_id
                            if jira_response:
                                jira_data["summary"] = jira_response.fields.summary
                                jira_data["status"] = jira_response.fields.status
                                jira_data["created"] = jira_response.fields.created
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
def test_case_execution_info(request, test_case_execution_id):
    """
    This one does not involve suite execution id
    :param request:
    :param test_case_execution_id:
    :return:
    """
    result = {}
    test_case_execution = TestCaseExecution.objects.get(execution_id=test_case_execution_id)
    result["execution_id"] = test_case_execution.execution_id
    result["suite_execution_id"] = test_case_execution.suite_execution_id
    result["log_prefix"] = test_case_execution.log_prefix
    result["re_run_history"] = test_case_execution.re_run_history
    return result


@csrf_exempt
@api_safe_json_response
def script_execution(request, id):
    result = None
    try:
        request_json = json.loads(request.body)
        r = RegresssionScripts.objects.get(id=id)
        script_path = r.script_path
        q = Q(script_path=script_path)
        if "suite_execution_id" in request_json:
            suite_execution_id = request_json["suite_execution_id"]
            q = q & Q(suite_execution_id=suite_execution_id)
        test_case_executions = TestCaseExecution.objects.filter(q)
        result = {}
        for test_case_execution in test_case_executions:
            result[test_case_execution.test_case_id] = {"execution_id": test_case_execution.execution_id,
                                                        "result": test_case_execution.result}
    except ObjectDoesNotExist:
        raise Exception("Script with id: {} does not exist".format(id))
    return result

@csrf_exempt
@api_safe_json_response
def job_spec(request, job_id):
    result = {}
    suite_execution = SuiteExecution.objects.get(execution_id=job_id)
    result["submitter_email"] = suite_execution.submitter_email
    result["emails"] = json.loads(suite_execution.emails)
    result["test_bed_type"] = suite_execution.test_bed_type
    result["environment"] = json.loads(suite_execution.environment)
    result["suite_path"] = suite_execution.suite_path
    result["script_path"] = suite_execution.script_path

    result["inputs"] = json.loads(suite_execution.inputs) if suite_execution.inputs else "{}"
    return result


def _get_attributes(suite_execution):
    attributes = {"result": suite_execution.result,
                  "state": suite_execution.state,
                  "scheduled_time": str(suite_execution.scheduled_time),
                  "completed_time": str(suite_execution.completed_time),
                  "suite_path": str(suite_execution.suite_path)}
    return attributes

@csrf_exempt
@api_safe_json_response
def re_run_info(request):
    result = None
    q = Q()
    if request.method == "POST":
        request_json = json.loads(request.body)
        original_suite_execution_id = request_json["original_suite_execution_id"] if "original_suite_execution_id" in request_json else None
        if original_suite_execution_id:
            q = q & Q(original_suite_execution_id=original_suite_execution_id)
        re_run_suite_execution_id = request_json["re_run_suite_execution_id"] if "re_run_suite_execution_id" in request_json else None
        if re_run_suite_execution_id:
            q = q & Q(re_run_suite_execution_id=re_run_suite_execution_id)
    entries = SuiteReRunInfo.objects.filter(q)
    if (entries.count):
        result = []
    for entry in entries:
        original_suite_execution = {}
        original_suite_execution["suite_execution_id"] = entry.original_suite_execution_id
        suite_execution = SuiteExecution.objects.get(execution_id=entry.original_suite_execution_id)
        original_suite_execution["attributes"] = _get_attributes(suite_execution=suite_execution)

        re_run_suite_execution = {}
        re_run_suite_execution["suite_execution_id"] = entry.re_run_suite_execution_id
        suite_execution = SuiteExecution.objects.get(execution_id=entry.re_run_suite_execution_id)
        re_run_suite_execution["attributes"] = _get_attributes(suite_execution=suite_execution)
        result.append({"original": original_suite_execution, "re_run": re_run_suite_execution})
    return result


@csrf_exempt
@api_safe_json_response
def git(request):
    result = {}
    if request.method == "POST":
        try:
            request_json = json.loads(request.body)
            command = request_json["command"]
            result = {"pull": None}
            if command == "pull":
                result["pull"] = subprocess.check_output("git pull &> /tmp/git.log", shell=True)
            if command == "logs":
                output = subprocess.check_output("git log -n 10", shell=True)
                result["logs"] = output
        except Exception as ex:
            logger.exception(str(ex))
    return result


def _get_job_spec(job_id):
    result = {}
    job_spec = SuiteExecution.objects.get(execution_id=job_id)
    result["execution_id"] = job_spec.execution_id
    result["suite_type"] = job_spec.suite_type
    result["suite_path"] = job_spec.suite_path
    result["email"] = job_spec.submitter_email
    return result


@csrf_exempt
@api_safe_json_response
def scheduler_queue(request, job_id):
    result = None
    if request.method == 'GET':
        result = []
        queue_elements = JobQueue.objects.all().order_by('priority')
        for queue_element in queue_elements:
            one_element = {"job_id": queue_element.job_id,
                           "priority": queue_element.priority,
                           "test_bed_type": queue_element.test_bed_type,
                           "job_spec": _get_job_spec(job_id=queue_element.job_id),
                           "message": queue_element.message,
                           "suspend": queue_element.suspend,
                           "pre_emption_allowed": queue_element.pre_emption_allowed}

            try:
                s = SuiteExecution.objects.get(execution_id=queue_element.job_id)
                one_element["queued_time_timestamp"] = get_epoch_time_from_datetime(s.scheduled_time)
            except ObjectDoesNotExist:
                pass
            result.append(one_element)
    elif request.method == 'POST':
        result = None
        request_json = json.loads(request.body)
        operation = request_json['operation']
        job_id = request_json["job_id"]
        if operation == QueueOperations.MOVE_UP:
            result = increase_decrease_priority(job_id=job_id, increase=True)
        if operation == QueueOperations.MOVE_DOWN:
            result = increase_decrease_priority(job_id=job_id, increase=False)
        if operation == QueueOperations.MOVE_TO_TOP:
            move_to_queue_head(job_id=job_id)
        if operation == QueueOperations.MOVE_TO_NEXT_QUEUE:
            move_to_higher_queue(job_id=job_id)
        if operation == QueueOperations.DELETE:
            delete_queued_job(job_id=job_id)
    elif request.method == 'DELETE':
        try:
            queue_entry = JobQueue.objects.get(job_id=int(job_id))
            scheduler.scheduler_helper.kill_job(job_id=int(job_id))
            queue_entry.delete()
        except ObjectDoesNotExist:
            pass
    elif request.method == "PUT":
        try:
            queue_entry = JobQueue.objects.get(job_id=int(job_id))
            request_json = json.loads(request.body)
            if "suspend" in request_json:
                queue_entry.suspend = request_json["suspend"]
            if "pre_emption_allowed" in request_json:
                queue_entry.pre_emption_allowed = request_json["pre_emption_allowed"]
            queue_entry.save()
        except ObjectDoesNotExist:
            pass
    return result


@csrf_exempt
@api_safe_json_response
def scheduler_queue_priorities(request):
    if request.method == "GET":
        return SchedulerJobPriority.__dict__
    elif request.method == 'POST':
        request_json = json.loads(request.body)
@csrf_exempt
@api_safe_json_response
def testbeds(request):
    result = {}
    testbeds = TestBed.objects.all()
    for testbed in testbeds:
        result[testbed.name] = {"name": testbed.name, "description": testbed.description}
    return result


@csrf_exempt
@api_safe_json_response
def get_networking_artifacts(request, sdk_version):
    files = glob.glob("{}/*{}*.*".format(LOGS_DIR, sdk_version))
    result = []
    for file in files:
        result.append(os.path.basename(file))
    return result
