import pytz
import datetime
from fun_settings import TIME_ZONE
import os
import dateutil
from lib.utilities.http import fetch_text_file

BUILD_INFO_FILENAME = "build_info.txt"

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

def is_triaging_mode():
    return "TRIAGE" in os.environ

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

class PerfUnit:
    # Units taken from Bertrand's perf library 'perf_metric.h' from FUNOS common utils. Link given below:
    # https://github.com/fungible-inc/FunOS/blob/master/utils/common/perf_metric.h
    UNIT_USECS = "usecs"
    UNIT_NSECS = "nsecs"
    UNIT_MSECS = "msecs"
    UNIT_SECS = "secs"

    UNIT_OPS = "ops"
    UNIT_KOPS = "Kops"
    UNIT_MOPS = "Mops"
    UNIT_GOPS = "Gops"

    UNIT_OP = "op"
    UNIT_KOP = "Kop"
    UNIT_MOP = "Mop"
    UNIT_GOP = "Gop"

    UNIT_CYCLES = "cycles"

    UNIT_NUMBER = "number"

    UNIT_BITS = "b"
    UNIT_BYTES = "B"
    UNIT_KB = "KB"
    UNIT_MB = "MB"
    UNIT_GB = "GB"
    UNIT_TB = "TB"

    UNIT_BITS_PER_SEC = "bps"
    UNIT_KBITS_PER_SEC = "Kbps"
    UNIT_MBITS_PER_SEC = "Mbps"
    UNIT_GBITS_PER_SEC = "Gbps"
    UNIT_TBITS_PER_SEC = "Tbps"

    UNIT_BYTES_PER_SEC = "Bps"
    UNIT_KBYTES_PER_SEC = "KBps"
    UNIT_MBYTES_PER_SEC = "MBps"
    UNIT_GBYTES_PER_SEC = "GBps"
    UNIT_TBYTES_PER_SEC = "TBps"

    UNIT_PPS = "pps"
    UNIT_MPPS = "Mpps"
    UNIT_KPPS = "Kpps"
    UNIT_GPPS = "Gpps"

    UNIT_CPS = "cps"
    UNIT_MCPS = "Mcps"
    UNIT_KCPS = "Kcps"
    UNIT_GCPS = "Gcps"

class FunPlatform:
    F1 = "F1"
    S1 = "S1"
    F11 = "F1.1"

class ChartType:
    REGULAR = "REGULAR"
    FUN_METIRC = "FUN_METIRC"

class FunChartType:
    VERTICAL_BAR_CHART = "vertical_colored_bar_chart"
    HORIZONTAL_BAR_CHART = "horizontal_bar_chart"
    LINE_CHART = "line"
    PIE_CHART = "pie_chart"