import os
import time
import datetime
import json
import glob
import shutil
import psutil
import logging.handlers
import sys
import web.fun_test.models_helper as models_helper
from web.fun_test.web_interface import get_suite_detail_url
from fun_settings import JOBS_DIR, ARCHIVED_JOBS_DIR, LOGS_DIR, KILLED_JOBS_DIR, WEB_STATIC_DIR, MEDIA_DIR, SUITES_DIR
from fun_global import RESULTS, get_current_time
from lib.utilities.send_mail import send_mail
from django.utils.timezone import activate
from fun_settings import TIME_ZONE
from web.fun_test.models import SchedulerInfo
from scheduler.scheduler_global import SchedulerStates, SuiteType, SchedulingType
from lib.utilities.http import fetch_text_file
from web.fun_test.models import JobSpec

from pytz import timezone
from datetime import timedelta
import random


activate(TIME_ZONE)

CONSOLE_LOG_EXTENSION = ".logs.txt"
HTML_LOG_EXTENSION = ".html"
LOG_DIR_PREFIX = "s_"
QUEUED_JOB_EXTENSION = "queued.json"
ARCHIVED_JOB_EXTENSION = "archived.json"
KILLED_JOB_EXTENSION = "killed_job"
SCHEDULED_JOB_EXTENSION = "scheduled.json"
JSON_EXTENSION = ".json"
LOG_FILE_NAME = LOGS_DIR + "/scheduler.log"
BUILD_INFO_FILENAME = "build_info.txt"


DYNAMIC_SUITE_JOBS_DIR = JOBS_DIR + "/" + "dynamic_suites"
DYNAMIC_SUITE_QUEUED_JOB_EXTENSION = "dynamic_queued.json"

scheduler_logger = logging.getLogger("main_scheduler_log")
scheduler_logger.setLevel(logging.DEBUG)

TEN_MB = 1e7
DEBUG = False

if not DEBUG:
    handler = logging.handlers.RotatingFileHandler(LOG_FILE_NAME, maxBytes=TEN_MB, backupCount=5)
else:
    handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
scheduler_logger.addHandler(hdlr=handler)
scheduler_logger.setLevel(logging.DEBUG)




DAY_OF_WEEK_TO_INDEX = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6
}


def set_jenkins_hourly_execution_status(status):
    source_file = MEDIA_DIR + "/regression_unknown.png"
    if status == RESULTS["PASSED"]:
        source_file = MEDIA_DIR + "/regression_passed.png"
    if status == RESULTS["FAILED"]:
        source_file = MEDIA_DIR + "/regression_failed.png"
    if status == RESULTS["IN_PROGRESS"]:
        source_file = MEDIA_DIR + "/regression_in_progress.png"
    status_file = LOGS_DIR + "/jenkins_hourly_execution_status.png"
    shutil.copy(src=source_file, dst=status_file)


class SchedulerException(Exception):
    def __init__(self, *args):
        super(SchedulerException, self).__init__(*args)
        scheduler_logger.exception(*args)


def get_flat_file_name(path):
    parts = path.split("/")
    flat = path
    if len(parts) > 2:
        flat = "_".join(parts[-2:])
    return flat.lstrip("/")


def get_flat_console_log_file_name(path, script_index):
    f = get_flat_file_name(path=path) + CONSOLE_LOG_EXTENSION
    basename = os.path.basename(f)
    new_basename = "{}_{}".format(script_index, basename)
    f = f.replace(basename, new_basename)
    return f


def get_flat_html_log_file_name(path, script_index):
    f = get_flat_file_name(path=path) + HTML_LOG_EXTENSION
    basename = os.path.basename(f)
    new_basename = "{}_{}".format(script_index, basename)
    f = f.replace(basename, new_basename)
    return f


def kill_job(job_id):
    filename = "{}/{}_{}".format(KILLED_JOBS_DIR, job_id, KILLED_JOB_EXTENSION)
    with open(filename, "w") as f:
        f.write(str(job_id))


def get_timezone_by_string(tz_string):
    tz = timezone('America/Los_Angeles')
    if tz_string == "IST":
        tz = timezone('Asia/Kolkata')
    return tz


def get_periodic_scheduling_time_in_seconds(days, requested_hour, requested_minute, tz_string):
    tz = get_timezone_by_string(tz_string=tz_string)
    now = get_current_time().astimezone(tz=tz)
    derived_time = now
    current_day_of_week = now.weekday()
    hour_of_day = now.hour
    minute_of_hour = now.minute

    requested_days = [DAY_OF_WEEK_TO_INDEX[x] for x in days]
    extra_seconds = -1
    for requested_day in requested_days:
        if requested_day == current_day_of_week:
            # Let's derive the time
            derived_time = now.replace(hour=requested_hour, minute=requested_minute)
            extra_seconds = (derived_time - now).total_seconds()
            if extra_seconds >= 0:
                break


        if requested_day > current_day_of_week:
            # process something
            derived_time = now.replace(hour=requested_hour, minute=requested_minute)
            number_of_days_between = requested_day - current_day_of_week
            derived_time = derived_time + timedelta(number_of_days_between)

            extra_seconds = (derived_time - now).total_seconds()
            if extra_seconds >= 0:
                break

    requested_day = requested_days[0]
    if extra_seconds < 0:
        derived_time = now.replace(hour=requested_hour, minute=requested_minute)
        derived_time = derived_time + timedelta(days=1)
        for i in range(7):
            derived_time_day_of_week = derived_time.weekday()
            if derived_time_day_of_week == requested_day:
                extra_seconds = (derived_time - now).total_seconds()
                break
            derived_time = derived_time + timedelta(days=1)
    print "Extra seconds", extra_seconds
    print now
    print derived_time
    print derived_time - now
    return extra_seconds


def get_todays_scheduling_time_in_seconds(requested_hour, requested_minute, tz_string):
    extra_seconds = -1
    tz = get_timezone_by_string(tz_string=tz_string)
    now = get_current_time().astimezone(tz=tz)
    derived_time = now.replace(hour=requested_hour, minute=requested_minute)
    if derived_time >= now:
        extra_seconds = (derived_time - now).total_seconds()
    return extra_seconds


def get_scheduling_time(spec):
    result = -1
    if spec["scheduling_type"] == SchedulingType.PERIODIC:
        result = get_periodic_scheduling_time_in_seconds(days=spec["requested_days"],
                                                         requested_hour=spec["requested_hour"],
                                                         requested_minute=spec["requested_minute"],
                                                         tz_string=spec["tz"])
    elif spec["scheduling_type"] == SchedulingType.TODAY:
        result = get_todays_scheduling_time_in_seconds(requested_hour=spec["requested_hour"],
                                                       requested_minute=spec["requested_minute"],
                                                       tz_string=spec["tz"])
    elif spec["scheduling_type"] == SchedulingType.ASAP:
        result = 1

    elif spec["scheduling_type"] == SchedulingType.REPEAT:
        result = 60
        if "repeat_in_minutes" in spec:
            result = spec["repeat_in_minutes"]
        result = result * 60  # Minutes to seconds
    return result


def validate_spec(spec):
    valid = False
    error_message = ""
    if spec["scheduling_type"] in [SchedulingType.PERIODIC, SchedulingType.TODAY]:
        if spec["requested_hour"] > 23:
            error_message = "requested_hour > 23"
        if spec["requested_minute"] > 59:
            error_message = "requested_minute > 59"
        supported_timezones = ["PST", "IST"]
        if spec["tz"] not in supported_timezones:
            error_message = "unsupported timezone: {}".format(spec["tz"])
        valid = True
    if spec["scheduling_type"] == SchedulingType.PERIODIC and not spec["requested_days"]:
        valid = False
        error_message = "days list is empty"
    if spec["scheduling_type"] == SchedulingType.TODAY:
        if get_scheduling_time(spec=spec) < 0:
            valid = False
            error_message = "scheduling time should be in the future"
        else:
            valid = True
    if spec["scheduling_type"] == SchedulingType.ASAP:
        valid = True
    if spec["scheduling_type"] == SchedulingType.REPEAT:
        valid = True
    if not spec["scheduling_type"]:
        valid = False
        error_message = "scheduling type cannot be empty"
    return valid, error_message

def parse_suite(suite_name=None, dynamic_suite_file=None):
    suite_file_name = None
    if not dynamic_suite_file:
        suite_file_name = SUITES_DIR + "/" + suite_name + JSON_EXTENSION
    else:
        suite_file_name = dynamic_suite_file
    suite_spec = parse_file_to_json(file_name=suite_file_name)
    if not suite_spec:
        raise SchedulerException("Unable to parse suite-spec: {}".format(suite_file_name))
    return suite_spec

def get_suite_level_tags(suite_spec):
    tags = []
    for item in suite_spec:
        if "info" in item:
            info = item["info"]
            if "tags" in info:
                tags = info["tags"]
            break
    return tags

def queue_suite_container(suite_path,
                          build_url=None,
                          tags=None, **kwargs):
    job_id = -1
    container_execution = models_helper.add_suite_container_execution(suite_path=suite_path, tags=tags)
    if container_execution:
        job_id = container_execution.execution_id
        container_spec = parse_suite(suite_name=suite_path.replace(".json", ""))
        container_tags = get_suite_level_tags(suite_spec=container_spec)
        container_tags.extend(tags)

        for item_suite_path in container_spec:
            item_spec = parse_suite(suite_name=item_suite_path.replace(".json", ""))
            suite_level_tags = get_suite_level_tags(suite_spec=item_spec)
            suite_level_tags.extend(container_tags)
            time.sleep(random.uniform(0.1, 0.3))
            queue_job2(suite_path=item_suite_path, tags=suite_level_tags, build_url=build_url, suite_container_execution_id=container_execution.execution_id, **kwargs)
    return job_id

def queue_dynamic_job(suite_path, scheduling_type, build_url, tags, email_list, email_on_fail_only=None):
    # jobs that don't have a suite file. we create a suite dynamically
    return queue_job2(suite_path=suite_path,
                      build_url=build_url,
                      tags=tags,
                      email_list=email_list,
                      email_on_fail_only=email_on_fail_only,
                      suite_type=SuiteType.DYNAMIC,
                      scheduling_type=scheduling_type)


def queue_dynamic_suite(dynamic_suite_spec,
                        original_suite_execution_id,
                        email_list=None,
                        environment=None,
                        test_bed_type=None,
                        build_url=None):
    return queue_job2(dynamic_suite_spec=dynamic_suite_spec,
                      suite_type=SuiteType.DYNAMIC,
                      original_suite_execution_id=original_suite_execution_id,
                      email_list=email_list,
                      test_bed_type=test_bed_type,
                      environment=environment,
                      build_url=build_url)

def queue_job3(suite_path=None,
               original_suite_execution_id=None,
               dynamic_suite_spec=None,
               script_path=None,
               build_url=None,
               scheduling_type=SchedulingType.ASAP,
               requested_days=None,
               requested_hour=None,
               requested_minute=None,
               timezone_string="PST",
               tags=None,
               emails=None,
               email_on_fail_only=None,
               environment=None,
               inputs=None,
               repeat_in_minutes=None,
               suite_container_execution_id=-1,
               job_spec=None,
               suite_type=SuiteType.STATIC,
               test_bed_type=None,
               version=None):
    time.sleep(0.1)
    job_id = -1
    if not suite_path:
        if job_spec:
            suite_path = job_spec["suite_name"].replace(JSON_EXTENSION, "")
            tags = job_spec["tags"]

    if suite_type == SuiteType.DYNAMIC:
        suite_path = "dynamic"
    final_suite_path = suite_path if suite_path else script_path

    suite_execution = models_helper.add_suite_execution(submitted_time=get_current_time(),
                                                        scheduled_time=get_current_time(),
                                                        completed_time=get_current_time(),
                                                        suite_path=final_suite_path,
                                                        tags=tags,
                                                        suite_container_execution_id=suite_container_execution_id,
                                                        test_bed_type=test_bed_type)
    dynamic_suite_file = None
    if suite_type == SuiteType.DYNAMIC:
        dynamic_suite_file = prepare_dynamic_suite(spec=dynamic_suite_spec, suite_execution_id=suite_execution.execution_id)
        if original_suite_execution_id:  # Must be a re-run
            models_helper.set_suite_re_run_info(original_suite_execution_id=original_suite_execution_id,
                                                re_run_suite_execution_id=suite_execution.execution_id)
        else:
            scheduler_logger.error("Suite is dynamic, but original_suite_execution_id is missing")
    if not job_spec:
        job_spec = {}
        if suite_path:
            suite_path = suite_path.replace(JSON_EXTENSION, "")
        job_spec["suite_name"] = suite_path  #.replace(JSON_EXTENSION, "")
        job_spec["dynamic_suite_file"] = dynamic_suite_file
        job_spec["script_path"] = script_path
        job_spec["build_url"] = build_url
        job_spec["scheduling_type"] = scheduling_type
        job_spec["requested_days"] = requested_days
        job_spec["requested_hour"] = requested_hour
        job_spec["requested_minute"] = requested_minute
        job_spec["repeat_in_minutes"] = repeat_in_minutes
        job_spec["tags"] = tags
        job_spec["emails"] = emails
        job_spec["email_on_fail_only"] = email_on_fail_only
        job_spec["environment"] = environment
        job_spec["timezone_string"] = timezone_string
        job_spec["suite_type"] = suite_type
        job_spec["inputs"] = inputs
    job_spec_valid, error_message = validate_spec(spec=job_spec)

    if not job_spec_valid:
        scheduler_logger.error("Invalid job spec: {}, Error message: {}".format(job_spec, error_message))
        job_id = -1
    else:
        job_id = suite_execution.execution_id
        job_spec["job_id"] = job_id
        try:
            job_spec_entry = JobSpec()
            job_spec_entry.suite_name = job_spec["suite_path"]
            job_spec_entry.dynamic_suite_file = job_spec["dynamic_suite_file"]
            job_spec_entry.script_path = job_spec["script_path"]
            job_spec_entry.suite_type = job_spec["suite_type"]
            job_spec_entry.scheduling_type = job_spec["scheduling_type"]

            job_spec_entry.requested_days = job_spec["requested_days"]
            job_spec_entry.requested_hour = job_spec["requested_hour"]
            job_spec_entry.requested_minute = job_spec["requested_minute"]
            job_spec_entry.timezone_string = job_spec["timezone_string"]
            job_spec_entry.repeat_in_minutes = job_spec["repeat_in_minutes"]

            job_spec_entry.tags = job_spec["tags"]
            job_spec_entry.emails = job_spec["emails"]
            job_spec_entry.email_on_failure_only = job_spec["email_on_fail_only"]

            job_spec_entry.environment = job_spec["environment"]
            job_spec_entry.inputs = job_spec["inputs"]
            job_spec_entry.build_url = job_spec["build_url"]
            job_spec_entry.version = job_spec["version"]

            job_spec_entry.save()

            queued_file_name = "{}/{}.{}".format(JOBS_DIR, job_id, QUEUED_JOB_EXTENSION)
            with open(queued_file_name, "w+") as qf:
                qf.write(json.dumps(job_spec))
                qf.close()
        except Exception as ex:
            scheduler_logger.error("Job spec is invalid: {}".format(job_spec))
        print("Job Id: {} suite: {} Queued. Spec: {}".format(job_id, suite_path, job_spec))
    return job_id

def queue_job2(suite_path=None,
               original_suite_execution_id=None,
               dynamic_suite_spec=None,
               script_path=None,
               build_url=None,
               scheduling_type=SchedulingType.ASAP,
               requested_days=None,
               requested_hour=None,
               requested_minute=None,
               tz_string="PST",
               tags=None,
               email_list=None,
               email_on_fail_only=None,
               environment=None,
               inputs=None,
               repeat_in_minutes=None,
               suite_container_execution_id=-1,
               job_spec=None,
               suite_type=SuiteType.STATIC,
               test_bed_type=None):
    time.sleep(0.1)
    # print "Environment: {}".format(environment)
    if not suite_path:
        if job_spec:
            suite_path = job_spec["suite_name"].replace(JSON_EXTENSION, "")
            tags = job_spec["tags"]

    if suite_type == SuiteType.DYNAMIC:
        suite_path = "dynamic"
    final_suite_path = suite_path if suite_path else script_path

    suite_execution = models_helper.add_suite_execution(submitted_time=get_current_time(),
                                                        scheduled_time=get_current_time(),
                                                        completed_time=get_current_time(),
                                                        suite_path=final_suite_path,
                                                        tags=tags,
                                                        suite_container_execution_id=suite_container_execution_id,
                                                        suite_type=suite_type,
                                                        test_bed_type=test_bed_type)
    dynamic_suite_file = None
    if suite_type == SuiteType.DYNAMIC:
        dynamic_suite_file = prepare_dynamic_suite(spec=dynamic_suite_spec, suite_execution_id=suite_execution.execution_id)
        if original_suite_execution_id:  # Must be a re-run
            models_helper.set_suite_re_run_info(original_suite_execution_id=original_suite_execution_id,
                                          re_run_suite_execution_id=suite_execution.execution_id)
    if not job_spec:
        job_spec = {}
        if suite_path:
            suite_path = suite_path.replace(JSON_EXTENSION, "")
        job_spec["suite_name"] = suite_path #.replace(JSON_EXTENSION, "")
        job_spec["dynamic_suite_file"] = dynamic_suite_file
        job_spec["script_path"] = script_path
        job_spec["build_url"] = build_url
        job_spec["scheduling_type"] = scheduling_type
        job_spec["requested_days"] = requested_days
        job_spec["requested_hour"] = requested_hour
        job_spec["requested_minute"] = requested_minute
        job_spec["repeat_in_minutes"] = repeat_in_minutes
        job_spec["tags"] = tags
        job_spec["email_list"] = email_list
        job_spec["email_on_fail_only"] = email_on_fail_only
        job_spec["environment"] = environment
        job_spec["tz"] = tz_string
        job_spec["suite_type"] = suite_type
        job_spec["inputs"] = inputs
    job_id = suite_execution.execution_id
    job_spec["job_id"] = job_id
    job_spec_valid, error_message = validate_spec(spec=job_spec)
    if not job_spec_valid:
        scheduler_logger.critical("Invalid job spec: {}, Error message: {}".format(job_spec, error_message))
        job_id = -1
    if job_spec_valid:
        try:
            queued_file_name = "{}/{}.{}".format(JOBS_DIR, job_id, QUEUED_JOB_EXTENSION)
            with open(queued_file_name, "w+") as qf:
                qf.write(json.dumps(job_spec))
                qf.close()
        except Exception as ex:
            print str(ex)
        print("Job Id: {} suite: {} Queued. Spec: {}".format(job_id, suite_path, job_spec))
    return job_id


def queue_job(suite_path="unknown",
              build_url=None,
              job_spec=None,
              schedule_at=None,
              repeat=False,
              schedule_in_minutes=None,
              repeat_in_minutes=None,
              email_list=None,
              tags=None,
              email_on_fail_only=None,
              environment=None):
    time.sleep(0.1)  # enough time to keep the creation timestamp unique
    print "Environment: {}".format(environment)

    if suite_path == "unknown":
        if job_spec:
            suite_path = job_spec["suite_name"].replace(JSON_EXTENSION, "")
            tags = job_spec["tags"]
    suite_execution = models_helper.add_suite_execution(submitted_time=get_current_time(),
                                                        scheduled_time=get_current_time(),
                                                        completed_time=get_current_time(),
                                                        suite_path=suite_path,
                                                        tags=tags)
    # if tags and "jenkins-hourly" in tags:
    #    set_jenkins_hourly_execution_status(status=RESULTS["QUEUED"])
    if not job_spec:
        job_spec = {}
        suite_path = suite_path.replace(JSON_EXTENSION, "")
        job_spec["suite_name"] = suite_path.replace(JSON_EXTENSION, "")
        job_spec["build_url"] = build_url
        job_spec["schedule_at"] = schedule_at
        job_spec["repeat"] = repeat
        job_spec["schedule_in_minutes"] = schedule_in_minutes
        job_spec["repeat_in_minutes"] = repeat_in_minutes
        job_spec["tags"] = tags
        job_spec["email_list"] = email_list
        job_spec["email_on_fail_only"] = email_on_fail_only
        job_spec["environment"] = environment
    job_id = suite_execution.execution_id
    job_spec["job_id"] = job_id
    try:
        queued_file_name = "{}/{}.{}".format(JOBS_DIR, job_id, QUEUED_JOB_EXTENSION)
        with open(queued_file_name, "w+") as qf:
            qf.write(json.dumps(job_spec))
            qf.close()
    except Exception as ex:
        print str(ex)
    print("Job Id: {} suite: {} Queued. Spec: {}".format(job_id, suite_path, job_spec))
    return job_id


def get_archived_file_name(suite_execution_id):
    glob_str = ARCHIVED_JOBS_DIR + "/{}.{}".format(suite_execution_id,
                                                   ARCHIVED_JOB_EXTENSION)
    files = glob.glob(glob_str)
    return files[0]


def get_archived_job_spec(job_id):
    archive_file_name = get_archived_file_name(suite_execution_id=job_id)
    result = parse_file_to_json(file_name=archive_file_name)
    return result


def re_queue_job(suite_execution_id,
                 test_case_execution_id=None,
                 suite_path=None,
                 script_path=None):
    archived_job_file = get_archived_file_name(suite_execution_id=suite_execution_id)
    job_spec = parse_file_to_json(file_name=archived_job_file)
    if test_case_execution_id:
        job_spec["test_case_ids"] = [test_case_execution_id]
        job_spec["suite_path"] = suite_path
        job_spec["script_path"] = script_path
        if "email_list" in job_spec:
            job_spec["email_list"] = job_spec["email_list"]
    job_spec["scheduling_type"] = SchedulingType.ASAP
    return queue_job2(job_spec=job_spec)


def parse_file_to_json(file_name):
    result = None
    try:
        with open(file_name, "r") as infile:
            contents = infile.read()
            result = json.loads(contents)
    except Exception as ex:
        scheduler_logger.exception(str(ex))
    return result


def process_list(process_name):
    processes = []

    for proc in psutil.process_iter():
        try:
            proc_name = proc.name()
            pid = proc.pid()
            result = process_name in proc_name
            proc_cmd_line = proc.cmdline()

            if result:
                processes.append((proc_name, proc_cmd_line))
                continue
            else:
                for s in proc_cmd_line:
                    result = process_name in s
                    if result:
                        processes.append((proc_name, proc_cmd_line))
                        break
        except:
            pass
    # print processes
    return processes


def _get_table(header_list, list_of_rows):
    s = '<table class="table table-nonfluid"\n'
    s += "\t<tr>\n"
    for header in header_list:
        s += "\t\t<th>" + header + "</th>\n"
    s += "\t</tr>"
    s += "\n"

    for row in list_of_rows:
        s += "\t<tr>\n"
        s += "\t\t"
        elements = row
        if type(row) is dict:
            elements = row.values()
        for element in elements:
            klass = ""
            if element == RESULTS["PASSED"]:
                klass = ' class="passed"'
            elif element == RESULTS["FAILED"]:
                klass = ' class="failed"'
            s += "<td{}>".format(klass)
            s += str(element)
            s += "</td>"
        s += "\n\t</tr>\n"
    s += "</table>"

    return s


def process_dynamic_suite():
    job_files = glob.glob("{}/*{}".format(DYNAMIC_SUITE_JOBS_DIR, DYNAMIC_SUITE_QUEUED_JOB_EXTENSION))
    job_files.sort(key=os.path.getmtime)
    for job_file in job_files:
        print parse_file_to_json(job_file)


def prepare_dynamic_suite(spec, suite_execution_id):
    queued_file_name = "{}/{}.{}".format(DYNAMIC_SUITE_JOBS_DIR, suite_execution_id, DYNAMIC_SUITE_QUEUED_JOB_EXTENSION)
    with open(queued_file_name, "w+") as qf:
        qf.write(json.dumps(spec))
        qf.close()
    return queued_file_name


    '''
        dynamic_suite_contents = {}
    suite_execution = models_helper.add_suite_execution(submitted_time=get_current_time(),
                                                        scheduled_time=get_current_time(),
                                                        completed_time=get_current_time(),
                                                        suite_path=SuiteType.DYNAMIC)
    dynamic_suite_contents["suite_execution_id"] = suite_execution.execution_id
    queued_file_name = "{}/{}.{}".format(DYNAMIC_SUITE_JOBS_DIR, suite_execution.execution_id, DYNAMIC_SUITE_QUEUED_JOB_EXTENSION)
    with open(queued_file_name, "w+") as qf:
        qf.write(json.dumps(dynamic_suite_contents))
        qf.close()

    return suite_execution.execution_id
    '''





    '''
    suite_execution = models_helper.add_suite_execution(submitted_time=get_current_time(),
                                                        scheduled_time=get_current_time(),
                                                        completed_time=get_current_time(),
                                                        suite_path=SuiteType.DYNAMIC)
    queued_file_name = "{}/{}.{}".format(JOBS_DIR, suite_execution.execution_id, QUEUED_JOB_EXTENSION)
    with open(queued_file_name, "w+") as qf:
        qf.write(json.dumps(spec))
        qf.close()
    '''

def set_scheduler_state(state):
    o = SchedulerInfo.objects.first()
    o.state = state
    o.save()
    scheduler_logger.info("Scheduler state: {}".format(state))

def set_main_loop_heartbeat():
    o = SchedulerInfo.objects.first()
    o.main_loop_heartbeat = o.main_loop_heartbeat + 1
    if o.main_loop_heartbeat > 100000:
        o.main_loop_heartbeat = 0
    o.save()

def get_scheduler_info():
    o = SchedulerInfo.objects.first()
    return o


def send_summary_mail(job_id, suite_execution, to_addresses=None, email_on_fail_only=None, extra_message=""):
    scheduler_logger.info("Suite Execution: {}".format(str(suite_execution)))
    if email_on_fail_only and suite_execution["suite_result"] == RESULTS["PASSED"]:
        return True

    # if "jenkins-hourly" in suite_execution["fields"]["tags"]:
    #    set_jenkins_hourly_execution_status(status=suite_execution["suite_result"])
    suite_execution_attributes = models_helper._get_suite_execution_attributes(suite_execution=suite_execution)
    header_list = ["Metric", "Value"]
    table1 = _get_table(header_list=header_list, list_of_rows=suite_execution_attributes)
    header_list = ["TC-ID", "Summary", "Inputs", "Path", "Result"]
    list_of_rows = [[x["test_case_id"],
                     models_helper.get_test_case_details(x["script_path"], x["test_case_id"])['summary'], x["inputs"], x["script_path"], x["result"]] for x in
                    suite_execution["test_case_info"]]
    table2 = _get_table(header_list=header_list, list_of_rows=list_of_rows)

    banner = ""
    if suite_execution["fields"]["banner"]:
        banner = suite_execution["fields"]["banner"]

    if extra_message:
        extra_message = "<p><b>{}</b></p><br>".format(extra_message)
    suite_detail_url = """
    <p>
        <a href="%s">Details Link</a>
    </p>
    """ % (get_suite_detail_url(suite_execution_id=job_id))

    css_file = WEB_STATIC_DIR + "/css/common/mail.css"
    with open(css_file, "r") as f:
        css = f.read()
        html = """
        <head>
        <style>
        %s
        </style>
        </head>
        %s
        %s
        %s
        <br>
        %s
        <br>
        <br>
        %s
        """ % (css, banner, extra_message, suite_detail_url, table1, table2)

        # print html

        subject = "Automation: {}: {} P:{} F:{}".format(suite_execution["suite_result"],
                                                        suite_execution["fields"]["suite_path"],
                                                        suite_execution["num_passed"],
                                                        suite_execution["num_failed"])

        try:
            result = send_mail(subject=subject, content=html, to_addresses=to_addresses)
            # print html
            scheduler_logger.info("Sent mail")
            if not result["status"]:
                scheduler_logger.error("Send Mail: {}".format(result["error_message"]))
        except Exception as ex:
            scheduler_logger.error("Send Mail Failure: {}".format(str(ex)))




if __name__ == "__main__":
    # print get_flat_console_log_file_name(path="/clean_sanity.py")
    # print get_flat_html_log_file_name(path="/examples/clean_sanity.py")
    # queue_dynamic_job(suite_path="abc.json", build_url=None, tags="tag1", email_list=['john.abraham@fungible.com'], scheduling_type=SchedulingType.ASAP)
    '''
    queue_job2(script_path="examples/vanilla.py",
               build_url=None,
               tags=["tag1"],
               email_list=['john.abraham@fungible.com'],
               scheduling_type=SchedulingType.ASAP)
    '''
    # queue_dynamic_suite(suite_path="test", script_path="ab.py", test_cases=[1, 32])
    scripts = []
    one_script = {"path": "examples/vanilla.py"}
    scripts.append(one_script)
    one_script = {"path": "examples/sanity.py", "test_case_ids": [3, 5]}
    scripts.append(one_script)
    a_suite = [
        {"path": "examples/vanilla.py", "test_case_ids": [1, 4, 5], "re_run_info": {4: {"test_case_execution_id": 53335}}}

    ]
    queue_job2(dynamic_suite_spec=a_suite, suite_type=SuiteType.DYNAMIC)
    # queue_dynamic_suite(scripts=scripts)

    # process_dynamic_suite()