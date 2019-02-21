import pytz
import datetime
from fun_settings import TIME_ZONE
import os
import dateutil
from lib.utilities.http import fetch_text_file

BUILD_INFO_FILENAME = "build_info.txt"
RESULT_PASS = "PASS"  #TODO merge it with RESULTS
RESULT_FAIL = "FAIL"

NUM_SECONDS_IN_DAY = 24 * 3600
MICROSECONDS = 10 ** 6

RESULTS = {"NOT_RUN": "NOT_RUN",
           "PASSED": "PASSED",
           "FAILED": "FAILED",
           "BLOCKED": "BLOCKED",
           "SKIPPED": "SKIPPED",
           "IN_PROGRESS": "IN_PROGRESS",
           "UNKNOWN": "UNKNOWN",
           "KILLED": "KILLED",
           "QUEUED": "QUEUED",
           "SCHEDULED": "SCHEDULED",
           "ABORTED": "ABORTED"}

METRIC_TYPE = {"SCORES": "SCORES",
               "PASS/FAIL": "PASS/FAIL"}

def get_current_time():
    utc = pytz.utc.localize(datetime.datetime.utcnow())
    return utc.astimezone(pytz.timezone(TIME_ZONE))

def get_localized_time(datetime_obj):
    tz = pytz.timezone(TIME_ZONE)
    # localized = pytz.dst.localize(datetime_obj)
    localized = tz.localize(datetime_obj, is_dst=None)
    return localized

epoch_obj = get_localized_time(datetime.datetime(1970, 1, 1, 0, 0, 0))  # Moving it here for efficiency

def get_epoch_time_from_datetime(datetime_obj):
    date_obj = datetime_obj
    if datetime_obj.tzinfo is None:
        date_obj = get_localized_time(datetime_obj)
    epoch_seconds = date_obj - epoch_obj
    epoch = (epoch_seconds.microseconds + (epoch_seconds.seconds + epoch_seconds.days * NUM_SECONDS_IN_DAY) * MICROSECONDS) / 1000
    return epoch

def get_datetime_from_epoch_time(epoch_in_milliseconds):
    date_time = datetime.datetime.utcfromtimestamp(epoch_in_milliseconds / 1000.0)
    return date_time


def is_production_mode():
    return "PRODUCTION_MODE" in os.environ


def is_development_mode():
    return "DEVELOPMENT_MODE" in os.environ


def is_lite_mode():
    """
    This is for running scripts that do not require a heavy weight DBMS like Postgres
    For cases that just sqlite
    For cases where the test-harness is the laptop
    """
    return (not is_production_mode()) and (not is_development_mode())

def determine_version(build_url):
    content = fetch_text_file(url=build_url + "/" + BUILD_INFO_FILENAME)
    version = None
    if content:
        content = content.strip()
        version = int(content)
    return version


def get_utc_offset():
    now = datetime.datetime.now(pytz.timezone(TIME_ZONE))
    offset = now.utcoffset().total_seconds() / 60 / 60
    return offset
