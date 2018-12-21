import os, django, json, datetime
from datetime import datetime
from django.core import serializers, paginator
from fun_global import RESULTS, get_current_time, get_localized_time
from django.utils import timezone
import dateutil.parser
from django.db.models import Q
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fun_test.settings")
django.setup()

from web.fun_test.models import (
    SuiteExecution,
    LastSuiteExecution,
    LastTestCaseExecution,
    RESULT_CHOICES,
    TestCaseExecution,
    JenkinsJobIdMap
)

SUITE_EXECUTION_FILTERS = {"PENDING": "PENDING",
                           "COMPLETED": "COMPLETED",
                           "ALL": "ALL"}

pending_states = [RESULTS["UNKNOWN"], RESULTS["SCHEDULED"], RESULTS["QUEUED"]]

def update_suite_execution(suite_execution_id, result=None, scheduled_time=None, version=None):
    te = SuiteExecution.objects.get(execution_id=suite_execution_id)
    if result:
        te.result = result
    if scheduled_time:
        te.scheduled_time = scheduled_time
    if version:
        te.version = version
    te.save()
    return te

def finalize_suite_execution(suite_execution_id):
    _get_suite_executions(execution_id=suite_execution_id, save_suite_info=True, finalize=True)

def add_suite_execution(submitted_time,
                        scheduled_time,
                        completed_time,
                        suite_path="unknown",
                        tags=None,
                        catalog_reference=""):

    if tags:
        tags = json.dumps(tags)
    else:
        tags = "[]"
    last_suite_execution_id = LastSuiteExecution.objects.all()
    if not last_suite_execution_id:
        LastSuiteExecution().save()
    last_suite_execution_id = LastSuiteExecution.objects.last()
    last_suite_execution_id.last_suite_execution_id += 1
    last_suite_execution_id.save()

    s = SuiteExecution(execution_id=last_suite_execution_id.last_suite_execution_id, suite_path=suite_path,
                       submitted_time=submitted_time,
                       scheduled_time=scheduled_time,
                       completed_time=completed_time,
                       result="QUEUED",
                       tags=tags,
                       catalog_reference=catalog_reference)
    s.save()
    return s


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
    last_test_case_execution_id = LastTestCaseExecution.objects.last()
    last_test_case_execution_id.last_test_case_execution_id += 1
    last_test_case_execution_id.save()
    return last_test_case_execution_id.last_test_case_execution_id

def add_test_case_execution_id(suite_execution_id, test_case_execution_id):
    result = None
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

def add_test_case_execution(test_case_id, suite_execution_id, path, result=RESULTS["NOT_RUN"]):
    te = TestCaseExecution(execution_id=get_next_test_case_execution_id(),
                           test_case_id=test_case_id,
                           suite_execution_id=suite_execution_id,
                           result=result,
                           started_time=get_current_time(),  # timezone.now(), #get_current_time(),
                            script_path=path)
    te.save()
    add_test_case_execution_id(suite_execution_id=suite_execution_id,
                               test_case_execution_id=te.execution_id)
    return te

def update_test_case_execution(test_case_execution_id, suite_execution_id, result):
    te = TestCaseExecution.objects.get(execution_id=test_case_execution_id,
                                       suite_execution_id=suite_execution_id)
    te.result = result
    te.save()
    return te

def report_test_case_execution_result(execution_id, result):
    test_execution = get_test_case_execution(execution_id=execution_id)
    # fun_test.simple_assert(test_execution, "Test-execution") # TODO
    test_execution.result = result
    test_execution.end_time = get_current_time()#timezone.now()
    test_execution.save()

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
        test_case_execution_ids = json.loads(suite_execution["fields"]["test_case_execution_ids"])
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
        entry.fun_sdk_branch = fun_sdk_branch
        entry.git_commit = git_commit
        entry.software_date = software_date
        entry.hardware_version = hardware_version
        entry.build_properties = build_properties
        entry.save()
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
