import os, django, json, datetime
from django.core import serializers, paginator
from fun_global import RESULTS, get_current_time
from django.utils import timezone
import dateutil.parser
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fun_test.settings")
django.setup()

from web.fun_test.models import (
    SuiteExecution,
    LastSuiteExecution,
    LastTestCaseExecution,
    RESULT_CHOICES,
    TestCaseExecution
)


def add_suite_execution(submitted_time, scheduled_time, completed_time, suite_path="unknown"):

    last_suite_execution_id = LastSuiteExecution.objects.all()
    if not last_suite_execution_id:
        LastSuiteExecution().save()
    last_suite_execution_id = LastSuiteExecution.objects.last()
    last_suite_execution_id.last_suite_execution_id += 1
    last_suite_execution_id.save()

    s = SuiteExecution(execution_id=last_suite_execution_id.last_suite_execution_id, suite_path=suite_path,
                   submitted_time=submitted_time,
                   scheduled_time=scheduled_time,
                   completed_time=completed_time)
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

def add_test_case_execution(test_case_id, suite_execution_id, path, result=RESULT_CHOICES[0][0]):
    te = TestCaseExecution(execution_id=get_next_test_case_execution_id(), test_case_id=test_case_id,
                           suite_execution_id=suite_execution_id,
                           result=result,
                           started_time=get_current_time(), #timezone.now(), #get_current_time(),
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

def _get_suite_executions(execution_id, page=None, records_per_page=10, save_test_case_info=False):
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

        suite_execution["test_case_info"] = []
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

        if (num_passed == len(test_case_execution_ids)) and test_case_execution_ids:
            suite_result = RESULTS["PASSED"]
        if num_failed:
            suite_result = RESULTS["FAILED"]
        if num_in_progress:
            suite_result = RESULTS["IN_PROGRESS"]
        if "result" in suite_execution["fields"]:
            if suite_execution["fields"]["result"] == RESULTS["KILLED"]:
                suite_result = RESULTS["KILLED"]
        suite_execution["suite_result"] = suite_result
        suite_execution["num_passed"] = num_passed
        suite_execution["num_failed"] = num_failed
        suite_execution["num_skipped"] = num_skipped
        suite_execution["num_not_run"] = num_not_run
        suite_execution["num_in_progress"] = num_in_progress

        suite_execution["fields"]["scheduled_time"] = str(timezone.localtime(dateutil.parser.parse(suite_execution["fields"]["scheduled_time"])))
        suite_execution["fields"]["submitted_time"] = str(timezone.localtime(dateutil.parser.parse(suite_execution["fields"]["submitted_time"])))
        suite_execution["fields"]["completed_time"] = str(timezone.localtime(dateutil.parser.parse(suite_execution["fields"]["completed_time"])))

    return all_objects_dict

def _get_suite_execution_attributes(suite_execution):
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
    return suite_execution_attributes