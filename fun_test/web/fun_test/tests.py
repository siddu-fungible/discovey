import datetime
from fun_settings import *
from web.fun_test.models_helper import *

if __name__ == "__main__":
    st = datetime.datetime(day=1, month=1, year=2017, hour=0, minute=1, second=10)
    s = add_suite_execution(suite_path="/abc",
                   submitted_time=st,
                   scheduled_time=st,
                   completed_time=st)
    s2 = get_suite_execution(suite_execution_id=s.execution_id)
    if s2:
        print s2



    add_test_case_execution(suite_execution_id=s2.execution_id,
                            result="FAILED",
                            test_case_id=724)

    add_test_case_execution(suite_execution_id=s2.execution_id,
                            result="FAILED",
                            test_case_id=725)

    i = get_test_case_executions_by_suite_execution(suite_execution_id=s2.execution_id)
    for test_case_execution in i:
        print test_case_execution.test_case_id