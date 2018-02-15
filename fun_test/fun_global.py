import pytz
import datetime
from fun_settings import TIME_ZONE
import os
from lib.utilities.http import fetch_text_file

BUILD_INFO_FILENAME = "build_info.txt"
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


def is_performance_server():
    return "PERFORMANCE_SERVER" in os.environ


def determine_version(build_url):
    content = fetch_text_file(url=build_url + "/" + BUILD_INFO_FILENAME)
    version = None
    if content:
        content = content.strip()
        version = int(content)
    return version
