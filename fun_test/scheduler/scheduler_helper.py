import os
import time, datetime, json, glob, shutil
import psutil, logging.handlers, sys
import web.fun_test.models_helper as models_helper
from web.fun_test.web_interface import get_suite_detail_url
from fun_settings import JOBS_DIR, ARCHIVED_JOBS_DIR, LOGS_DIR, KILLED_JOBS_DIR, WEB_STATIC_DIR, MEDIA_DIR
from fun_global import RESULTS, is_regression_server, is_performance_server, get_current_time
from lib.utilities.send_mail import send_mail
from django.utils.timezone import activate
from fun_settings import TIME_ZONE
from web.fun_test.models import SchedulerInfo
from scheduler.scheduler_states import SchedulerStates
from lib.utilities.http import fetch_text_file
from pytz import timezone
from datetime import timedelta


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

class SchedulingType:
    ASAP = "asap"
    PERIODIC = "periodic"
    TODAY = "today"
    REPEAT = "repeat"

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
    if spec["scheduling_type"] == SchedulingType.PERIODIC or spec["scheduling_type"] == SchedulingType.TODAY:
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
    return valid, error_message


def queue_job2(suite_path="unknown",
               build_url=None,
               scheduling_type=None,
               requested_days=None,
               requested_hour=None,
               requested_minute=None,
               tz_string=None,
               tags=None,
               email_list=None,
               email_on_fail_only=None,
               environment=None,
               repeat_in_minutes=None,
               job_spec=None):
    time.sleep(0.1)
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
    job_spec["scheduling_type"] = "asap"
    '''
    for k in ["schedule_at", "schedule_in_minutes", "schedule_in_minutes_at", "repeat", "repeat_in_minutes"]:
        try:
            del job_spec[k]
        except:
            pass
    '''
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


def set_scheduler_state(state):
    o = SchedulerInfo.objects.first()
    o.state = state
    o.save()
    scheduler_logger.info("Scheduler state: {}".format(state))


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
    header_list = ["TC-ID", "Summary", "Path", "Result"]
    list_of_rows = [[x["test_case_id"], models_helper.get_test_case_details(x["script_path"], x["test_case_id"]), x["script_path"], x["result"]] for x in
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
            print html
            scheduler_logger.info("Sent mail")
            if not result["status"]:
                scheduler_logger.error("Send Mail: {}".format(result["error_message"]))
        except Exception as ex:
            scheduler_logger.error("Send Mail Failure: {}".format(str(ex)))


if __name__ == "__main__":
    print get_flat_console_log_file_name(path="/clean_sanity.py")
    print get_flat_html_log_file_name(path="/examples/clean_sanity.py")
