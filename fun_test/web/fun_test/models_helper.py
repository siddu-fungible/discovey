import os, django, json, datetime
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
                           started_time=datetime.datetime.now(),
                           script_path=path)
    te.save()
    add_test_case_execution_id(suite_execution_id=suite_execution_id,
                               test_case_execution_id=te.execution_id)
    return te

def report_test_case_execution_result(execution_id, result):
    test_execution = get_test_case_execution(execution_id=execution_id)
    # fun_test.simple_assert(test_execution, "Test-execution") # TODO
    test_execution.result = result
    test_execution.end_time = datetime.datetime.now()
    test_execution.save()

def get_test_case_executions_by_suite_execution(suite_execution_id):
    results = TestCaseExecution.objects.filter(suite_execution_id=suite_execution_id)
    return results

def get_test_case_execution(execution_id):
    results = TestCaseExecution.objects.filter(execution_id=execution_id)
    return results[0]  #TODO: what if len(results) > 1