import os, django, json, datetime
import sys
import random
import time
from datetime import datetime
from django.core import serializers, paginator
from fun_global import RESULTS, get_current_time, get_localized_time
from fun_settings import SCRIPTS_DIR
from django.utils import timezone
import dateutil.parser
from django.db.models import Q
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from scheduler.scheduler_global import SuiteType
from threading import Lock
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fun_test.settings")
django.setup()

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
    SuiteReRunInfo
)

SUITE_EXECUTION_FILTERS = {"PENDING": "PENDING",
                           "COMPLETED": "COMPLETED",
                           "ALL": "ALL"}

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

    try:
        result = inspect(module_name=SCRIPTS_DIR + "/" + script_path)
        if result:
            if "classes" in result:
                for c in result["classes"]:
                    test_cases[c["id"]] = c

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
        if test_case_id:
            from lib.system.fun_test import fun_test
            result = fun_test.inspect(module_name=SCRIPTS_DIR + "/" + script_path)
            # result = inspect(module_name=SCRIPTS_DIR + "/" + script_path)
            if result:
                if "classes" in result:
                    for c in result["classes"]:
                        if c["id"] == test_case_id:
                            summary = c["summary"]
                            # print "Summary", summary
        else:
            summary = "Script setup"
    except Exception as ex:
        print "Error: {}".format(str(ex))

    this_summary = summary
    return {"summary": this_summary}


def get_suite_container_execution(suite_container_execution_id):
    s = SuiteContainerExecution.objects.get(execution_id=suite_container_execution_id)
    return s

def update_suite_container_execution(suite_container_execution_id, version=None):
    s = get_suite_container_execution(suite_container_execution_id=suite_container_execution_id)
    if s:
        if version:
            s.version = version
    s.save()

def update_suite_execution(suite_execution_id, result=None, scheduled_time=None, version=None, tags=None):
    # print "Suite-Execution-ID: {}, result: {}, version: {}".format(suite_execution_id, result, version)
    te = SuiteExecution.objects.get(execution_id=suite_execution_id)
    if result:
        te.result = result
    if scheduled_time:
        te.scheduled_time = scheduled_time
    if version:
        te.version = version
    if tags:
        te.tags = json.dumps(tags)
    with transaction.atomic():
        te.save()
    # print te.version
    return te

def finalize_suite_execution(suite_execution_id):
    _get_suite_executions(execution_id=suite_execution_id, save_suite_info=True, finalize=True)

def get_new_suite_execution_id():
    last_suite_execution_id = LastSuiteExecution.objects.all()
    if not last_suite_execution_id:
        LastSuiteExecution().save()
    with transaction.atomic():
        time.sleep(random.uniform(0.1, 1.5))
        last_suite_execution_id = LastSuiteExecution.objects.last()
        last_suite_execution_id.last_suite_execution_id += 1
        last_suite_execution_id.save()
    return last_suite_execution_id

def add_suite_container_execution(suite_path, tags):
    last_suite_execution_id = get_new_suite_execution_id()
    s = SuiteContainerExecution(suite_path=suite_path, execution_id=last_suite_execution_id.last_suite_execution_id, tags=json.dumps(tags))
    s.save()
    return s


def add_suite_execution(submitted_time,
                        scheduled_time,
                        completed_time,
                        suite_path="unknown",
                        tags=None,
                        catalog_reference="",
                        suite_container_execution_id=-1,
                        test_bed_type=None,
                        suite_type=SuiteType.STATIC):

    if tags:
        tags = json.dumps(tags)
    else:
        tags = "[]"
    if not test_bed_type:
        test_bed_type = ""

    for i in xrange(4):
        try:
            last_suite_execution_id = get_new_suite_execution_id()
            s = SuiteExecution(execution_id=last_suite_execution_id.last_suite_execution_id, suite_path=suite_path,
                               submitted_time=submitted_time,
                               scheduled_time=scheduled_time,
                               completed_time=completed_time,
                               result="QUEUED",
                               tags=tags,
                               catalog_reference=catalog_reference,
                               suite_container_execution_id=suite_container_execution_id,
                               test_bed_type=test_bed_type,
                               suite_type=suite_type)
            s.save()

            break
        except Exception as ex:
            print "Error: add_suite_execution: {}".format(str(ex))
            time.sleep(random.uniform(0.1, 1.0))
    return s

def set_suite_execution_banner(suite_execution_id, banner):
    suite_execution = get_suite_execution(suite_execution_id)
    suite_execution.banner = banner
    suite_execution.save()

def get_suite_execution_banner(suite_execution_id, banner):
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
            add_test_case_execution_id(suite_execution_id=suite_execution_id,
                                       test_case_execution_id=te.execution_id)
            break
        except Exception as ex:
            time.sleep(random.uniform(0.1, 3.0))
            print "Error: add_test_case_execution: {} index: {}".format(str(ex), index)


    return te

def update_test_case_execution(test_case_execution_id, suite_execution_id, result):
    te = TestCaseExecution.objects.get(execution_id=test_case_execution_id,
                                       suite_execution_id=suite_execution_id)
    te.result = result
    te.save()
    return te

def report_test_case_execution_result(execution_id, result, re_run_info=None):
    test_execution = get_test_case_execution(execution_id=execution_id)
    # fun_test.simple_assert(test_execution, "Test-execution") # TODO
    test_execution.result = result
    test_execution.end_time = get_current_time()#timezone.now()
    test_execution.save()
    if re_run_info:
        if str(test_execution.test_case_id) in re_run_info.keys():
            info = re_run_info[str(test_execution.test_case_id)]
            original_test_case_execution_id = info["test_case_execution_id"]
            original_test_case_execution = get_test_case_execution(execution_id=original_test_case_execution_id)
            re_run_entry = {"started_time": str(original_test_case_execution.started_time),
                            "result": original_test_case_execution.result,
                            "re_run_suite_execution_id": test_execution.suite_execution_id}
            original_test_case_execution.result = test_execution.result
            # original_test_case_execution.suite_execution_id = test_execution.suite_execution_id
            original_test_case_execution.started_time = test_execution.started_time
            original_test_case_execution.end_time = test_execution.end_time
            # original_test_case_execution.log_prefix = test_execution.log_prefix
            original_test_case_execution.add_re_run_entry(re_run_entry)
            original_test_case_execution.re_run_state = TestCaseReRunState.RE_RUN_COMPLETE
            original_test_case_execution.save()
            original_suite_execution = get_suite_execution(suite_execution_id=original_test_case_execution.suite_execution_id)
            original_suite_execution.finalized = False
            original_suite_execution.save()
            finalize_suite_execution(suite_execution_id=original_suite_execution.execution_id)


def get_test_case_executions_by_suite_execution(suite_execution_id):
    results = TestCaseExecution.objects.filter(suite_execution_id=suite_execution_id)
    return results

def get_test_case_execution(execution_id):
    results = TestCaseExecution.objects.filter(execution_id=execution_id)
    return results[0]  #TODO: what if len(results) > 1

def _get_suite_executions(execution_id=None,
                          page=None,
                          records_per_page=10,
                          save_test_case_info=False,
                          save_suite_info=True,
                          filter_string="ALL",
                          get_count=False,
                          tags=None,
                          finalize=None):
    all_objects = None
    q = Q(result=RESULTS["UNKNOWN"])

    if filter_string == SUITE_EXECUTION_FILTERS["PENDING"]:
        q = Q(result=RESULTS["UNKNOWN"]) | Q(result=RESULTS["IN_PROGRESS"]) | Q(result=RESULTS["QUEUED"]) | Q(result=RESULTS["SCHEDULED"])
    elif filter_string == SUITE_EXECUTION_FILTERS["COMPLETED"]:
        q = Q(result=RESULTS["PASSED"]) | Q(result=RESULTS["FAILED"]) | Q(result=RESULTS["KILLED"]) | Q(result=RESULTS["ABORTED"])
    if execution_id:
        q = Q(execution_id=execution_id) & q

    if filter_string == "ALL":
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

    all_objects = SuiteExecution.objects.filter(q).order_by('-id')


    if get_count:
        return all_objects.count()

    if page:
        p = paginator.Paginator(all_objects, records_per_page)
        all_objects = p.page(page)

    data = serializers.serialize("json", all_objects)
    all_objects_dict = json.loads(data)

    ses = []
    for suite_execution in all_objects_dict:
        ts = get_test_case_executions_by_suite_execution(suite_execution_id=suite_execution["fields"]["execution_id"])
        test_case_execution_ids = []
        for t in ts:
            test_case_execution_ids.append(t.execution_id)
        suite_execution["fields"]["test_case_execution_ids"] = json.dumps(test_case_execution_ids)
        # test_case_execution_ids = json.loads(suite_execution["fields"]["test_case_execution_ids"])
        suite_result = RESULTS["UNKNOWN"]
        num_passed = 0
        num_failed = 0
        num_skipped = 0
        num_not_run = 0
        num_in_progress = 0

        suite_execution["test_case_info"] = []
        finalized = suite_execution["fields"]["finalized"]

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

            if save_test_case_info:
                suite_execution["test_case_info"].append({"script_path": test_case_execution.script_path,
                                                          "test_case_id": test_case_execution.test_case_id,
                                                          "inputs": test_case_execution.inputs,
                                                          "result": test_case_execution.result})


        if not finalized:
            if finalize and (num_passed == len(test_case_execution_ids)) and test_case_execution_ids:
                suite_result = RESULTS["PASSED"]
            if finalize and num_failed:
                suite_result = RESULTS["FAILED"]

            if finalize and (not num_failed) and (not num_passed):
                suite_result = RESULTS["ABORTED"]
            if "result" in suite_execution["fields"]:
                if suite_execution["fields"]["result"] == RESULTS["KILLED"]:
                    suite_result = RESULTS["KILLED"]

            if save_suite_info or finalize:  #TODO: Perf too many saves
                se = SuiteExecution.objects.get(execution_id=suite_execution["fields"]["execution_id"])
                if finalize:
                    se.finalized = True
                if suite_result not in pending_states:
                    se.result = suite_result
                    # logger.error("Updating ID: {} Suite result: {} ".format(execution_id, se.result))
                # se.save()
                ses.append(se)
                suite_result = se.result
        else:
            suite_result = suite_execution["fields"]["result"]

        suite_execution["suite_result"] = suite_result
        suite_execution["num_passed"] = num_passed
        suite_execution["num_failed"] = num_failed
        suite_execution["num_skipped"] = num_skipped
        suite_execution["num_not_run"] = num_not_run
        suite_execution["num_in_progress"] = num_in_progress

        suite_execution["fields"]["scheduled_time"] = str(timezone.localtime(dateutil.parser.parse(suite_execution["fields"]["scheduled_time"])))
        suite_execution["fields"]["submitted_time"] = str(timezone.localtime(dateutil.parser.parse(suite_execution["fields"]["submitted_time"])))
        suite_execution["fields"]["completed_time"] = str(timezone.localtime(dateutil.parser.parse(suite_execution["fields"]["completed_time"])))

    with transaction.atomic():
        if save_suite_info:
            for se in ses:
                se.save()

    return all_objects_dict

def add_jenkins_job_id_map(jenkins_job_id, fun_sdk_branch, git_commit, software_date, hardware_version, completion_date, build_properties):
    print"Hardware_version: {}".format(hardware_version)
    try:
        entry = JenkinsJobIdMap.objects.get(completion_date=completion_date)
    except ObjectDoesNotExist:
        entry = JenkinsJobIdMap(completion_date=completion_date,
                                jenkins_job_id=jenkins_job_id,
                                fun_sdk_branch=fun_sdk_branch,
                                git_commit=git_commit,
                                software_date=software_date,
                                hardware_version=hardware_version,
                                build_properties=build_properties)
        entry.save()

def _get_suite_execution_attributes(suite_execution):
    suite_execution_attributes = []
    suite_execution_attributes.append({"name": "Result", "value": str(suite_execution["suite_result"])})
    suite_execution_attributes.append({"name": "Version", "value": str(suite_execution["fields"]["version"])})
    suite_execution_attributes.append({"name": "Scheduled Time", "value": str(suite_execution["fields"]["scheduled_time"])})
    suite_execution_attributes.append({"name": "Completed Time", "value": str(suite_execution["fields"]["completed_time"])})
    suite_execution_attributes.append({"name": "Path", "value": str(suite_execution["fields"]["suite_path"])})
    suite_execution_attributes.append({"name": "Passed", "value": suite_execution["num_passed"]})
    suite_execution_attributes.append({"name": "Failed", "value": suite_execution["num_failed"]})
    suite_execution_attributes.append({"name": "Not Run", "value": suite_execution["num_not_run"]})
    suite_execution_attributes.append({"name": "In Progress", "value": suite_execution["num_in_progress"]})
    suite_execution_attributes.append({"name": "Skipped", "value": suite_execution["num_skipped"]})
    return suite_execution_attributes


def set_suite_re_run_info(original_suite_execution_id, re_run_suite_execution_id):
    re_run = SuiteReRunInfo(original_suite_execution_id=original_suite_execution_id, re_run_suite_execution_id=re_run_suite_execution_id)
    re_run.save()