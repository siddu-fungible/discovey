import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from lib.utilities.jira_manager import JiraManager
from lib.utilities.script_fixup import fix
from fun_global import *
from fun_settings import TCMS_PROJECT
from web.fun_test.models import SiteConfig
from django.views.decorators.cache import never_cache


import json
import os
from web.fun_test.settings import COMMON_WEB_LOGGER_NAME
from django.http import HttpResponse
from django.shortcuts import render
from django.core import serializers, paginator
from fun_global import RESULTS, get_datetime_from_epoch_time, get_epoch_time_from_datetime
from fun_global import is_production_mode, is_triaging_mode, get_current_time
from fun_settings import LOGS_RELATIVE_DIR, SUITES_DIR, LOGS_DIR, MAIN_WEB_APP, DEFAULT_BUILD_URL, SCRIPTS_DIR
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
from web.fun_test.models import SuiteReRunInfo, JobQueue
from web.fun_test.models import SuiteReRunInfo
from web.fun_test.models import TestBed
from lib.utilities.send_mail import send_mail
from web.fun_test.web_interface import get_suite_detail_url
from web.fun_test.models import User, SiteConfig
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

logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)
app_config = apps.get_app_config(app_label=MAIN_WEB_APP)


@csrf_exempt
def publish(request):
    logs = []
    response = {}
    response["status"] = RESULT_FAIL
    if request.method == 'POST':
        request_json = json.loads(request.body)

        test_case_id = request_json["id"]
        test_case_summary = request_json["summary"]
        test_case_steps = request_json["steps"]
        setup_summary = request_json["setup_summary"]
        setup_steps = request_json["setup_steps"]
        full_script_path = request_json["full_script_path"]
        if str(test_case_id) in [str(0), str(999)]:  #TODO: hardcoded 999
            response["status"] = RESULTS["PASSED"]
        else:
            jira_manager = JiraManager()
            jira_summary = test_case_summary
            jira_description = "Setup:\n{}\n{}\n\n\nTest:\n{}\n{}\n".format(setup_summary,
                                                                        setup_steps,
                                                                        test_case_summary,
                                                                        test_case_steps)

            if test_case_id == "$tc":  #TODO: make this global
                result = jira_manager.generate_issue()

                if not result["status"] == RESULTS["PASSED"]:
                    response["status"] = RESULTS["FAILED"]
                    logs.append(result["err_msg"])
                else:
                    response["status"] = RESULTS["PASSED"]
                    test_case_id = result["issue_id"]
                    logs.append("Fetched JIRA {}-{}".format(TCMS_PROJECT, test_case_id))
                    fix(script_path=full_script_path, id=test_case_id)
            jira_manager.update_test_case(id=test_case_id, summary=jira_summary, description=jira_description)  #TODO: what about an error here?
            logs.append("Updated Test-case: {}".format(test_case_id))
    response["logs"] = logs
    return HttpResponse(json.dumps(response))

@csrf_exempt
def get_script_content(request):
    contents = "Could not find script"
    if request.method == 'POST':
        try:
            request_json = json.loads(request.body)
            full_script_path = request_json["full_script_path"]
            f = open(full_script_path, "r")
            contents = f.read()
            f.close()
        except Exception as ex:
            contents = str(ex)
    return HttpResponse(contents)


@csrf_exempt
@never_cache
def angular_home(request):
    angular_home = 'qa_dashboard/angular_home_development.html'
    site_version = SiteConfig.get_version()
    if is_production_mode() and not is_triaging_mode():
        angular_home = 'qa_dashboard/angular_home_production.html'
    return render(request, angular_home, locals())

def index(request):
    request.session.clear()
    return render(request, 'base.html', locals())



@csrf_exempt
@api_safe_json_response
def test(request):
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