import pytz, datetime
from fun_settings import TIME_ZONE
import os
RESULT_PASS = "PASS"  #TODO merge it with RESULTS
RESULT_FAIL = "FAIL"

RESULTS = {"NOT_RUN": "NOT_RUN",
           "PASSED": "PASSED",
           "FAILED": "FAILED",
           "SKIPPED": "SKIPPED",
           "IN_PROGRESS": "IN_PROGRESS",
           "UNKNOWN": "UNKNOWN",
           "KILLED": "KILLED",
           "QUEUED": "QUEUED",
           "SCHEDULED": "SCHEDULED",
           "ABORTED": "ABORTED"}


def get_current_time():
    utc = pytz.utc.localize(datetime.datetime.utcnow())
    return utc.astimezone(pytz.timezone(TIME_ZONE))

def is_regression_server():
    return "REGRESSION_SERVER" in os.environ
