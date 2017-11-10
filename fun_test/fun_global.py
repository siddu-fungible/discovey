import pytz, datetime
from fun_settings import TIME_ZONE
RESULT_PASS = "PASS"  #TODO merge it with RESULTS
RESULT_FAIL = "FAIL"

RESULTS = {"NOT_RUN": "NOT_RUN",
           "PASSED": "PASSED",
           "FAILED": "FAILED",
           "SKIPPED": "SKIPPED",
           "IN_PROGRESS": "IN_PROGRESS",
           "UNKNOWN": "UNKNOWN",
           "KILLED": "KILLED"}


def get_current_time():
    utc = pytz.utc.localize(datetime.datetime.utcnow())
    return utc.astimezone(pytz.timezone(TIME_ZONE))
