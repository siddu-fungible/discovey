import os, django, json, datetime
import sys
import random
import time
# from lib.system.fun_test import *
from datetime import datetime, timedelta
from django.core import paginator
from fun_global import RESULTS, get_current_time, get_localized_time
from fun_settings import SCRIPTS_DIR
from django.utils import timezone
import dateutil.parser
from django.db.models import Q
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from scheduler.scheduler_global import SuiteType, JobStatusType
from fun_settings import LOGS_DIR
from threading import Lock
import glob

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fun_test.settings")
django.setup()
import traceback
import re

import logging
from fun_settings import COMMON_WEB_LOGGER_NAME

logger = logging.getLogger(COMMON_WEB_LOGGER_NAME)

from web.fun_test.models import (
    SuiteExecution,
    LastSuiteExecution,
    LastTestCaseExecution,
    RESULT_CHOICES,
    TestCaseExecution,
    JenkinsJobIdMap,
    SuiteContainerExecution,
    SuiteReRunInfo,
    TestBed,
    TestCaseInfo,
    Suite,
    RegresssionScripts,
    MetricsDataRunTime,
    LastGoodBuild
)

SUITE_EXECUTION_FILTERS = {"PENDING": "PENDING",
                           "COMPLETED": "COMPLETED",
                           "ALL": "ALL",
                           "SCHEDULED": "SCHEDULED",
                           "SUBMITTED": "SUBMITTED",
                           "QUEUED": "QUEUED"}

pending_states = [RESULTS["UNKNOWN"], RESULTS["SCHEDULED"], RESULTS["QUEUED"]]


class TestCaseReRunState:
    RE_RUN_IN_PROGRESS = "re_run_in_progress"
    RE_RUN_COMPLETE = "re_run_complete"


def _is_sub_class(base_class, mros):
    result = None
    for mro in mros[1:]:
        if base_class in str(mro):
            result = True
            break
    return result


def inspect(module_name):
    result = {}
    result["classes"] = []
    sys.argv.append("--disable_fun_test")
    test_cases = []

    import imp
    import inspect
    f, filename, description = imp.find_module(os.path.basename(module_name).replace(".py", ""),
                                               [os.path.dirname(module_name)])
    flat_base_name = os.path.basename(module_name).replace(".", "_")
    loaded_module_name = "dynamic_load" + flat_base_name
    imp.load_module(loaded_module_name, f, filename, description)

    members = inspect.getmembers(sys.modules[loaded_module_name], inspect.isclass)
    for m in members:
        if len(m) > 1:
            klass = m[1]
            mros = inspect.getmro(klass)
            if len(mros) > 1 and _is_sub_class(base_class="lib.system.fun_test.FunTestCase", mros=mros):
                # print klass
                try:
                    o = klass()
                    o.describe()
                    result["classes"].append({"name": o.__class__.__name__, "summary": o.summary, "id": o.id})
                    test_cases.append(klass)
                except:
                    pass
                # print o.id
                # print o.summary
                # print o.steps

            if len(mros) > 1 and _is_sub_class(base_class="lib.system.fun_test.FunTestScript", mros=mros):
                test_script = klass
    # test_script_obj = test_script()
    # test_case_order = test_script().test_case_order
    '''
    for entry in test_script().test_case_order:
        print entry["tc"]
    '''
    return result


def get_all_test_cases(script_path):
    test_cases = {}

    all_test_cases = TestCaseInfo.objects.filter(script_path=script_path)

    try:
        for test_case in all_test_cases:
            test_cases[test_case.test_case_id] = {"summary": test_case.summary}
    except Exception as ex:
        print "Error: {}".format(str(ex))

    return test_cases


def get_test_case_details(script_path, test_case_id):
    # from lib.system.fun_test import fun_test
    # import os
    # os.environ["DISABLE_FUN_TEST"] = "1"

    # print "Script Path", script_path
    # result = fun_test.inspect(module_name=SCRIPTS_DIR + "/" + script_path)

    summary = "unknown"

    try:
        if int(test_case_id) == 999:
            summary = "Script cleanup"
        elif test_case_id:
            summary = TestCaseInfo.get_summary(test_case_id=test_case_id, script_path=script_path)
        else:
            summary = "Script setup"
    except Exception as ex:
        print "Error: {}".format(str(ex))

    this_summary = summary
    return {"summary": this_summary}


def update_test_case_info(test_case_id, script_path, summary, steps=None):
    TestCaseInfo.add_update(test_case_id=test_case_id, script_path=script_path, summary=summary, steps=steps)

def get_suite_container_execution(suite_container_execution_id):
    s = SuiteContainerExecution.objects.get(execution_id=suite_container_execution_id)
    return s

def update_suite_container_execution(suite_container_execution_id, version=None):
    s = get_suite_container_execution(suite_container_execution_id=suite_container_execution_id)
    if s:
        if version:
            s.version = version
    s.save()


def update_suite_execution(suite_execution_id,
                           result=None,
                           scheduled_time=None,
                           version=None,
                           build_url=None,
                           tags=None,
                           state=None,
                           suite_path=None,
                           completed_time=None,
                           environment=None,
                           started_time=None,
                           assets_used=None):
    logger.debug("Suite-Execution-ID: {}, result: {}, version: {}".format(suite_execution_id, result, version))
    te = SuiteExecution.objects.get(execution_id=suite_execution_id)
    if result:
        te.result = result
    if scheduled_time:
        te.scheduled_time = scheduled_time
    if version:
        te.version = version
    if build_url:
        te.build_url = build_url
    if tags:
        te.tags = json.dumps(tags)
    if suite_path:
        te.suite_path = suite_path
    if state is not None:
        te.state = state
    if completed_time:
        te.completed_time = completed_time
    if environment is not None:
        te.environment = json.dumps(environment)
    if started_time:
        te.started_time = started_time
    if assets_used:
        te.assets_used = assets_used
    te.save()
    te.save()
    # transaction.commit()
    te = SuiteExecution.objects.get(execution_id=suite_execution_id)

    # print te.version
    # print "Begin:"
    # traceback.print_stack()
    logger.debug("End Suite-Execution-ID: {}, result: {}, version: {} state: {}".format(suite_execution_id, te.result,
                                                                                        te.version, te.state))
    # traceback.print_stack()
    # sys.stdout.flush()
    # print "End:"
    return te


def finalize_suite_execution(suite_execution_id):
    _get_suite_executions(execution_id=suite_execution_id, save_suite_info=True, finalize=True)

def get_suite_run_time(execution_id):
    result = None
    s = get_suite_execution(suite_execution_id=execution_id)
    if s:
        result = s.run_time
    return result

def set_suite_run_time(execution_id, run_time):
    result = None
    s = get_suite_execution(suite_execution_id=execution_id)
    if s:
        s.run_time = run_time
        s.save()
    return result

def get_new_suite_execution_id():
    last_suite_execution_id = LastSuiteExecution.objects.all()
    if not last_suite_execution_id:
        LastSuiteExecution().save()
    with transaction.atomic():
        time.sleep(random.uniform(0.1, 1.5))
        last_suite_execution_id = LastSuiteExecution.objects.last()
        last_suite_execution_id.last_suite_execution_id += 1
        last_suite_execution_id.save()
        last_suite_execution_id.save()
    return last_suite_execution_id


def add_suite_execution(submitted_time,
                        scheduled_time,
                        completed_time,
                        suite_id=None,
                        suite_path="unknown",
                        state=JobStatusType.UNKNOWN,
                        tags=None,
                        suite_container_execution_id=-1,
                        test_bed_type=None,
                        suite_type=SuiteType.STATIC,
                        submitter_email=None,
                        pause_on_failure=False):
    if tags:
        tags = json.dumps(tags)
    else:
        tags = "[]"
    if not test_bed_type:
        test_bed_type = ""

    last_suite_execution_id = get_new_suite_execution_id()
    s = SuiteExecution(execution_id=last_suite_execution_id.last_suite_execution_id,
                       suite_path=suite_path,
                       submitted_time=submitted_time,
                       scheduled_time=scheduled_time,
                       completed_time=completed_time,
                       tags=tags,
                       suite_container_execution_id=suite_container_execution_id,
                       test_bed_type=test_bed_type,
                       state=state,
                       suite_type=suite_type,
                       submitter_email=submitter_email,
                       suite_id=suite_id,
                       pause_on_failure=pause_on_failure)
    s.started_time = submitted_time
    s.save()
    return s

def set_suite_execution_banner(suite_execution_id, banner):
    suite_execution = get_suite_execution(suite_execution_id)
    suite_execution.banner = banner
    suite_execution.save()


def get_suite_execution_banner(suite_execution_id):
    suite_execution = get_suite_execution(suite_execution_id)
    return suite_execution.banner


def get_suite_execution(suite_execution_id):
    result = None
    try:
        result = SuiteExecution.objects.get(execution_id=suite_execution_id)
    except Exception as ex:
        print str(ex)
    return result


def get_next_test_case_execution_id():
    last_test_case_execution_id = LastTestCaseExecution.objects.all()
    if not last_test_case_execution_id:
        LastTestCaseExecution().save()
    with transaction.atomic():
        time.sleep(random.uniform(0.1, 2.0))
        last_test_case_execution_id = LastTestCaseExecution.objects.last()
        last_test_case_execution_id.last_test_case_execution_id += 1
        last_test_case_execution_id.save()
        last_test_case_execution_id.save()
    return last_test_case_execution_id.last_test_case_execution_id


def add_test_case_execution_id(suite_execution_id, test_case_execution_id):
    result = None
    with transaction.atomic():
        s = SuiteExecution.objects.get(execution_id=suite_execution_id)
        if s:
            current_list = json.loads(s.test_case_execution_ids)
            current_list.append(test_case_execution_id)
            s.test_case_execution_ids = json.dumps(current_list)
            s.save()
            s.save()
            result = True
        else:
            raise ("Unable to locate Suite Execution id: {}".format(suite_execution_id))
    return result


def add_test_case_execution(test_case_id,
                            suite_execution_id,
                            path,
                            result=RESULTS["NOT_RUN"],
                            log_prefix="",
                            tags=[],
                            inputs=None):
    max_retries = 10
    te = None
    inputs = inputs if inputs else {}
    for index in xrange(max_retries):
        try:
            te = TestCaseExecution(execution_id=get_next_test_case_execution_id(),
                                   test_case_id=test_case_id,
                                   suite_execution_id=suite_execution_id,
                                   result=result,
                                   started_time=get_current_time(),  # timezone.now(), #get_current_time(),
                                   script_path=path,
                                   log_prefix=log_prefix,
                                   tags=json.dumps(tags),
                                   inputs=json.dumps(inputs))
            te.save()
            te.save()
            add_test_case_execution_id(suite_execution_id=suite_execution_id,
                                       test_case_execution_id=te.execution_id)
            break
        except Exception as ex:
            time.sleep(random.uniform(0.1, 3.0))
            print "Error: add_test_case_execution: {} index: {}".format(str(ex), index)

    return te


def update_test_case_execution(test_case_execution_id, suite_execution_id, result, started_time=None):
    te = TestCaseExecution.objects.get(execution_id=test_case_execution_id,
                                       suite_execution_id=suite_execution_id)
    te.result = result
    if started_time:
        te.started_time = started_time
    te.save()
    te.save()
    return te


def report_re_run_result(execution_id, re_run_info=None):
    test_execution = get_test_case_execution(execution_id=execution_id)
    if re_run_info:
        if str(test_execution.test_case_id) in re_run_info.keys():
            info = re_run_info[str(test_execution.test_case_id)]
            original_test_case_execution_id = info["test_case_execution_id"]
            original_test_case_execution = get_test_case_execution(execution_id=original_test_case_execution_id)
            re_run_entry = {"started_time": str(original_test_case_execution.started_time),
                            "result": original_test_case_execution.result,
                            "re_run_suite_execution_id": test_execution.suite_execution_id,
                            "re_run_test_case_execution_id": test_execution.execution_id,
                            "re_run_result": test_execution.result}
            original_test_case_execution.result = test_execution.result
            # original_test_case_execution.suite_execution_id = test_execution.suite_execution_id
            # original_test_case_execution.started_time = test_execution.started_time
            # original_test_case_execution.end_time = test_execution.end_time
            # original_test_case_execution.log_prefix = test_execution.log_prefix
            original_test_case_execution.add_re_run_entry(re_run_entry)
            original_test_case_execution.re_run_state = TestCaseReRunState.RE_RUN_COMPLETE
            original_test_case_execution.save()
            original_test_case_execution.save()
            original_suite_execution = get_suite_execution(
                suite_execution_id=original_test_case_execution.suite_execution_id)
            original_suite_execution.finalized = False
            original_suite_execution.save()
            original_suite_execution.save()

            finalize_suite_execution(suite_execution_id=original_suite_execution.execution_id)


def get_suite(id):
    result = None
    try:
        result = Suite.objects.get(id=id)
    except ObjectDoesNotExist:
        pass
    return result

def get_test_case_executions_by_suite_execution(suite_execution_id):
    results = TestCaseExecution.objects.filter(suite_execution_id=suite_execution_id)
    return results


def get_test_case_execution(execution_id):
    results = TestCaseExecution.objects.filter(execution_id=execution_id)
    return results[0]  # TODO: what if len(results) > 1


def _suite_execution_helper(suite_execution):
    result = {}
    result["fields"] = suite_execution.to_dict()
    return result

def _get_suite_executions(execution_id=None,
                          page=None,
                          records_per_page=10,
                          save_test_case_info=False,
                          save_suite_info=True,
                          state_filter_string="ALL",
                          submitter_email=None,
                          test_bed_type=None,
                          suite_path=None,
                          get_count=False,
                          tags=None,
                          finalize=None):
    all_objects = None
    q = Q()

    if state_filter_string == "ALL":
        q = Q()
    elif int(state_filter_string) == JobStatusType.IN_PROGRESS:
        q = Q(state=JobStatusType.IN_PROGRESS) | Q(state=JobStatusType.PAUSED)
    elif int(state_filter_string) == JobStatusType.QUEUED:
        q = Q(state=JobStatusType.QUEUED)
    elif int(state_filter_string) == JobStatusType.COMPLETED:
        q = Q(state=JobStatusType.COMPLETED) | Q(state=JobStatusType.KILLED) | Q(state=JobStatusType.ABORTED)
    elif int(state_filter_string) == JobStatusType.SUBMITTED:
        q = Q(state=JobStatusType.SUBMITTED)
    elif int(state_filter_string) == JobStatusType.SCHEDULED:
        q = Q(state=JobStatusType.SCHEDULED)
    elif int(state_filter_string) == JobStatusType.AUTO_SCHEDULED:
        q = Q(state=JobStatusType.AUTO_SCHEDULED)

    if execution_id:
        q = Q(execution_id=execution_id) & q

    if state_filter_string == "ALL":
        if execution_id:
            q = Q(execution_id=execution_id)
        else:
            q = Q()

    if tags:
        tag_q = None
        for tag in tags:
            tag_str = '"{}"'.format(tag)
            if not tag_q:
                tag_q = Q(tags__contains=tag_str)
            else:
                tag_q = Q(tags__contains=tag_str) | tag_q
            # print("Found tags:" + str(tags))
        if tags:
            q = q & tag_q
    if submitter_email:
        if ',' in submitter_email:
            submitter_email_parts = submitter_email.strip().split(',')
            q1 = Q()
            for submitter_email_part in submitter_email_parts:
                q1 = q1 | Q(submitter_email=submitter_email_part)
            q = q & q1
        else:
            q = q & Q(submitter_email=submitter_email)
    if test_bed_type:
        q = q & Q(test_bed_type=test_bed_type)
    if suite_path:
        if ',' in suite_path:
            suite_path_parts = suite_path.strip().split(',')
            q1 = Q()
            for suite_path_part in suite_path_parts:
                q1 = q1 | Q(suite_path=suite_path_part)
            q = q & q1
        else:
            q = q & Q(suite_path=suite_path)
    if execution_id is not None:
        q = q
    else:
        q = q & (Q(started_time__gt=get_current_time() - timedelta(days=30)) | Q(state=JobStatusType.AUTO_SCHEDULED))
    all_objects = SuiteExecution.objects.filter(q).order_by('-started_time')

    if get_count:
        return all_objects.count()

    if page:
        p = paginator.Paginator(all_objects, records_per_page)
        all_objects = p.page(page)

    # data = serializers.serialize("json", all_objects)
    # all_objects_dict = json.loads(data)

    return_results = []
    ses = []
    for suite_execution in all_objects:
        ts = get_test_case_executions_by_suite_execution(suite_execution_id=suite_execution.execution_id)
        test_case_execution_ids = []
        for t in ts:
            test_case_execution_ids.append(t.execution_id)
        suite_execution.test_case_execution_ids = json.dumps(test_case_execution_ids)
        # test_case_execution_ids = json.loads(suite_execution["fields"]["test_case_execution_ids"])
        suite_result = RESULTS["UNKNOWN"]
        num_passed = 0
        num_failed = 0
        num_skipped = 0
        num_not_run = 0
        num_in_progress = 0

        # suite_execution["test_case_info"] = []
        finalized = suite_execution.finalized

        for test_case_execution_id in test_case_execution_ids:
            test_case_execution = TestCaseExecution.objects.get(execution_id=test_case_execution_id)
            te_result = test_case_execution.result.upper()  # TODO: Upper?
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


        if not finalized:
            if finalize and (num_passed == len(test_case_execution_ids)) and test_case_execution_ids:
                suite_result = RESULTS["PASSED"]
            if finalize and num_failed:
                suite_result = RESULTS["FAILED"]

            if finalize and (not num_failed) and (not num_passed):
                suite_result = RESULTS["ABORTED"]
            if suite_execution.result:
                if suite_execution.result == RESULTS["KILLED"]:
                    suite_result = RESULTS["KILLED"]

            if finalize:  # TODO: Perf too many saves
                se = SuiteExecution.objects.get(execution_id=suite_execution.execution_id)
                if finalize:
                    se.finalized = True
                if suite_result not in pending_states:
                    se.result = suite_result
                    # logger.error("Updating ID: {} Suite result: {} ".format(execution_id, se.result))
                # se.save()
                ses.append(se)
                suite_result = se.result
        else:
            suite_result = suite_execution.result

        one_result = _suite_execution_helper(suite_execution)
        one_result["suite_result"] = suite_result
        one_result["num_passed"] = num_passed
        one_result["num_failed"] = num_failed
        one_result["num_skipped"] = num_skipped
        one_result["num_not_run"] = num_not_run
        one_result["num_in_progress"] = num_in_progress

        one_result["fields"]["scheduled_time"] = str(suite_execution.scheduled_time)
        one_result["fields"]["submitted_time"] = str(suite_execution.submitted_time)
        one_result["fields"]["completed_time"] = str(suite_execution.completed_time)
        return_results.append(one_result)
    with transaction.atomic():
        if finalize:
            for se in ses:
                se.save()
    return return_results


def add_jenkins_job_id_map(jenkins_job_id, fun_sdk_branch, git_commit, software_date, hardware_version,
                           build_properties, lsf_job_id, sdk_version="", build_date=datetime.now,
                           suite_execution_id=-1, add_associated_suites=True):
    print"Hardware_version: {}".format(hardware_version)
    try:
        entry = JenkinsJobIdMap.objects.get(build_date=build_date)
        if add_associated_suites:
            if entry.suite_execution_id != suite_execution_id:
                entry.associated_suites.append(suite_execution_id)
                entry.associated_suites = list(set(entry.associated_suites))
                entry.save()
    except ObjectDoesNotExist:
        entry = JenkinsJobIdMap(jenkins_job_id=jenkins_job_id,
                                fun_sdk_branch=fun_sdk_branch,
                                git_commit=git_commit,
                                software_date=software_date,
                                hardware_version=hardware_version,
                                build_properties=build_properties,
                                lsf_job_id=lsf_job_id, sdk_version=sdk_version, build_date=build_date,
                                suite_execution_id=suite_execution_id)
        entry.save()

def add_metrics_data_run_time(run_time, date_time):
    try:
        lsf_job_id = run_time["lsf_job_id"]
        if lsf_job_id:
            entry = MetricsDataRunTime.objects.get(lsf_job_id=lsf_job_id)
        else:
            raise ObjectDoesNotExist
    except ObjectDoesNotExist:
        jenkins_build_number = run_time["jenkins_build_number"]
        lsf_job_id = run_time["lsf_job_id"]
        suite_execution_id = run_time["suite_execution_id"]
        build_properties = run_time["build_properties"]
        version = run_time["version"]
        associated_suites = run_time["associated_suites"]
        entry = MetricsDataRunTime(jenkins_build_number=jenkins_build_number, lsf_job_id=lsf_job_id,
                           suite_execution_id=suite_execution_id, build_properties=build_properties, version=version,
                           associated_suites=associated_suites, date_time=date_time)
        entry.save()
    return entry.id

def _get_suite_execution_attributes(suite_execution):
    suite_execution_attributes = []
    suite_execution_attributes.append({"name": "Job state", "value": suite_execution["fields"]["state"]})
    suite_execution_attributes.append({"name": "Result", "value": str(suite_execution["suite_result"])})
    suite_execution_attributes.append({"name": "Version", "value": str(suite_execution["fields"]["version"])})
    # suite_execution_attributes.append(
    #     {"name": "Scheduled Time", "value": str(suite_execution["fields"]["scheduled_time"])})
    # suite_execution_attributes.append(
    #    {"name": "Started Time", "value": str(suite_execution["fields"]["started_time"])})
    # suite_execution_attributes.append(
    #    {"name": "Completed Time", "value": str(suite_execution["fields"]["completed_time"])})
    suite_execution_attributes.append({"name": "Path", "value": str(suite_execution["fields"]["suite_path"])})
    suite_execution_attributes.append({"name": "Passed", "value": suite_execution["num_passed"]})
    suite_execution_attributes.append({"name": "Failed", "value": suite_execution["num_failed"]})
    suite_execution_attributes.append({"name": "Not Run", "value": suite_execution["num_not_run"]})
    suite_execution_attributes.append({"name": "In Progress", "value": suite_execution["num_in_progress"]})
    suite_execution_attributes.append({"name": "Test-bed type", "value": suite_execution["fields"]["test_bed_type"]})
    suite_execution_attributes.append({"name": "Submitter", "value": suite_execution["fields"]["submitter_email"]})
    return suite_execution_attributes


def set_suite_re_run_info(original_suite_execution_id, re_run_suite_execution_id):
    re_run = SuiteReRunInfo(original_suite_execution_id=original_suite_execution_id,
                            re_run_suite_execution_id=re_run_suite_execution_id)
    re_run.save()
    re_run.save()


def get_suite_executions_by_filter(**kwargs):
    suite_executions = SuiteExecution.objects.filter(**kwargs)
    return suite_executions


def is_test_bed_with_manual_lock(test_bed_name):
    result = None
    try:
        t = TestBed.objects.get(name=test_bed_name, manual_lock=True)
        result = {"manual_lock_submitter": t.manual_lock_submitter}
    except ObjectDoesNotExist:
        pass
    return result


def is_suite_in_progress(job_id, test_bed_type):
    result = None
    try:
        s = SuiteExecution.objects.get(execution_id=int(job_id))
        # print ("Checking suite in progress: {}: {}".format(job_id, s.state))
        result = s.state >= JobStatusType.IN_PROGRESS
        # print ("Checking suite in progress: {} {}: {}: Result: {}".format(test_bed_type, job_id, s.state, result))
    except ObjectDoesNotExist:
        pass
    return result


def get_scripts_by_suite_execution(suite_execution_id):
    test_case_executions = TestCaseExecution.objects.filter(suite_execution_id=suite_execution_id)
    scripts = set()
    for test_case_execution in test_case_executions:
        scripts.add(test_case_execution.script_path)
    return scripts


def get_log_files(suite_execution_id):
    scripts = get_scripts_by_suite_execution(suite_execution_id=suite_execution_id)
    log_files = []
    if scripts:
        for script in scripts:
            base_name = os.path.basename(script)
            suite_log_directory = LOGS_DIR + "/s_" + str(suite_execution_id)

            glob_pattern = suite_log_directory + "/*" + base_name + "*"
            associated_files = glob.glob(glob_pattern)
            for associated_file in associated_files:
                log_files.append(associated_file)
    return log_files


def get_fun_test_time_series_collection_name(suite_execution_id):
    return "s_{}".format(suite_execution_id)


def get_ts_test_case_context_info_collection_name(suite_execution_id):
    return "s_{}_{}_context_info".format(suite_execution_id, script_id)


def get_ts_script_run_time_collection_name(suite_execution_id, script_id):
    return "s_{}_{}_script_run_time".format(suite_execution_id, script_id)


def get_script_id(test_case_execution_id):
    result = None
    test_case_execution = get_test_case_execution(execution_id=test_case_execution_id)
    if test_case_execution:
        script_path = test_case_execution.script_path
        if script_path:
            try:
                regression_script = RegresssionScripts.objects.get(script_path=script_path)
                result = regression_script.id
            except ObjectDoesNotExist:
                pass
    return result

def get_stable_build_number(release_train):
    result = None
    try:
        result = LastGoodBuild.get(release_train=release_train)
    except Exception as ex:
        print "Exception: {}".format(str(ex))
    return result