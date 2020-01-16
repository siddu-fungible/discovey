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
from web.fun_test.web_interface import get_suite_detail_url, set_annoucement, clear_announcements
from fun_settings import JOBS_DIR, LOGS_DIR, WEB_STATIC_DIR, SUITES_DIR, TASKS_DIR
from fun_settings import TEAM_REGRESSION_EMAIL
from fun_global import RESULTS, get_current_time
from lib.utilities.send_mail import send_mail
from django.utils.timezone import activate
from fun_settings import TIME_ZONE
from web.fun_test.models import SchedulerInfo
from scheduler.scheduler_global import SchedulerStates, SuiteType, SchedulingType, JobStatusType
from scheduler.scheduler_global import SchedulerDirectiveTypes
from web.fun_test.models import SchedulerJobPriority, JobQueue, KilledJob, TestCaseExecution, TestbedNotificationEmails
from web.fun_test.models import SchedulerDirective
from asset.asset_global import AssetType
from web.fun_test.models import Asset
from web.fun_test.models import TestBed, User, Suite
from django.core.exceptions import ObjectDoesNotExist
from web.fun_test.models import SchedulerConfig
from django.db import transaction
from pytz import timezone
from datetime import timedelta
import random
import collections


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
scheduler_logger.propagate = False

TEN_MB = 1e7
DEBUG = False

if not DEBUG:
    handler = logging.handlers.RotatingFileHandler(LOG_FILE_NAME, maxBytes=TEN_MB, backupCount=5)
else:
    handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
if len(scheduler_logger.handlers):
    del scheduler_logger.handlers[:]
scheduler_logger.addHandler(hdlr=handler)


DAY_OF_WEEK_TO_INDEX = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6
}


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
    suite_execution = models_helper.get_suite_execution(suite_execution_id=int(job_id))
    suite_execution.state = JobStatusType.KILLED
    KilledJob(job_id=job_id).save()
    suite_execution.save()


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
    if spec.scheduling_type == SchedulingType.PERIODIC:
        result = get_periodic_scheduling_time_in_seconds(days=json.loads(spec.requested_days),
                                                         requested_hour=spec.requested_hour,
                                                         requested_minute=spec.requested_minute,
                                                         tz_string=spec.timezone_string)
    elif spec.scheduling_type == SchedulingType.TODAY:
        result = get_todays_scheduling_time_in_seconds(requested_hour=spec.requested_hour,
                                                       requested_minute=spec.requested_minute,
                                                       tz_string=spec.timezone_string)
    elif spec.scheduling_type == SchedulingType.ASAP:
        result = 1

    elif spec.scheduling_type == SchedulingType.REPEAT:
        result = 60
        if spec.repeat_in_minutes:
            result = spec.repeat_in_minutes
        result = result * 60  # Minutes to seconds
    return result


def validate_spec(spec):
    valid = False
    error_message = ""
    if spec.scheduling_type in [SchedulingType.PERIODIC, SchedulingType.TODAY]:
        if spec.requested_hour > 23:
            error_message = "requested_hour > 23"
        if spec.requested_minute > 59:
            error_message = "requested_minute > 59"
        supported_timezones = ["PST", "IST"]
        if spec.timezone_string not in supported_timezones:
            error_message = "unsupported timezone: {}".format(spec.timezone_string)
        valid = True
    if spec.scheduling_type == SchedulingType.PERIODIC and not spec.requested_days:
        valid = False
        error_message = "days list is empty"
    if spec.scheduling_type == SchedulingType.TODAY:
        if get_scheduling_time(spec=spec) < 0:
            valid = False
            error_message = "scheduling time should be in the future"
        else:
            valid = True
    if spec.scheduling_type == SchedulingType.ASAP:
        valid = True
    if spec.scheduling_type == SchedulingType.REPEAT:
        valid = True
    if not spec.scheduling_type:
        valid = False
        error_message = "scheduling type cannot be empty"
    return valid, error_message



def get_suite_level_tags(suite_spec):
    tags = []
    for item in suite_spec:
        if "info" in item:
            info = item["info"]
            if "tags" in info:
                tags = info["tags"]
            break
    return tags


def queue_dynamic_suite(dynamic_suite_spec,
                        submitter_email,
                        original_suite_execution_id,
                        emails=None,
                        environment=None,
                        test_bed_type=None,
                        inputs=None,
                        build_url=None,
                        max_run_time=None):

    return queue_job3(dynamic_suite_spec=dynamic_suite_spec,
                      original_suite_execution_id=original_suite_execution_id,
                      suite_type=SuiteType.DYNAMIC,
                      emails=emails,
                      test_bed_type=test_bed_type,
                      environment=environment,
                      build_url=build_url,
                      submitter_email=submitter_email,
                      inputs=inputs,
                      max_run_time=max_run_time)

def is_auto_scheduled(scheduling_type, repeat_in_minutes):
    return (scheduling_type == SchedulingType.TODAY and repeat_in_minutes > 0) or (scheduling_type == SchedulingType.PERIODIC)

def queue_job3(suite_id=None,
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
               email_on_fail_only=False,
               environment=None,
               inputs=None,
               repeat_in_minutes=None,
               suite_container_execution_id=-1,  # A container of suites
               suite_type=SuiteType.STATIC,
               test_bed_type=None,
               version=None,
               requested_priority_category=SchedulerJobPriority.NORMAL,
               submitter_email=None,
               description=None,
               rich_inputs=None,
               max_run_time=7 * 24 * 3600,
               pause_on_failure=False):
    # time.sleep(0.1)
    result = -1
    if not tags:
        tags = []
    if not emails:
        emails = []
    if not inputs:
        inputs = {}

    suite_execution = None
    try:
        suite_path = None

        if suite_type == SuiteType.DYNAMIC:
            try:
                original_suite = Suite.objects.get(id=original_suite_execution_id)
                suite_path = original_suite.name
            except ObjectDoesNotExist:
                pass

        if suite_id:
            try:
                suite = Suite.objects.get(id=suite_id)
                suite_path = suite.name
            except ObjectDoesNotExist:
                pass

        final_suite_name = suite_path if suite_id else script_path

        is_auto_scheduled_job = is_auto_scheduled(scheduling_type=scheduling_type, repeat_in_minutes=repeat_in_minutes)
        job_state = JobStatusType.AUTO_SCHEDULED if is_auto_scheduled_job else JobStatusType.SUBMITTED


        suite_execution = models_helper.add_suite_execution(submitted_time=get_current_time(),
                                                            scheduled_time=get_current_time(),
                                                            completed_time=get_current_time(),
                                                            suite_path=final_suite_name,
                                                            suite_id=suite_id,
                                                            tags=tags,
                                                            suite_container_execution_id=suite_container_execution_id,
                                                            test_bed_type=test_bed_type,
                                                            submitter_email=submitter_email,
                                                            state=job_state,
                                                            pause_on_failure=pause_on_failure)
        if suite_type == SuiteType.DYNAMIC:
            if original_suite_execution_id:  # Must be a re-run
                models_helper.set_suite_re_run_info(original_suite_execution_id=original_suite_execution_id,
                                                    re_run_suite_execution_id=suite_execution.execution_id)
            else:
                scheduler_logger.error("Suite is dynamic, but original_suite_execution_id is missing")

        suite_execution.suite_path = final_suite_name
        suite_execution.script_path = script_path
        suite_execution.dynamic_suite_spec = json.dumps(dynamic_suite_spec)
        suite_execution.suite_type = suite_type
        suite_execution.scheduling_type = scheduling_type

        suite_execution.requested_days = json.dumps(requested_days)
        suite_execution.requested_hour = requested_hour
        suite_execution.requested_minute = requested_minute
        suite_execution.timezone_string = timezone_string
        suite_execution.repeat_in_minutes = repeat_in_minutes

        suite_execution.tags = json.dumps(tags)
        suite_execution.emails = json.dumps(emails)
        suite_execution.email_on_failure_only = email_on_fail_only if email_on_fail_only else False

        suite_execution.environment = json.dumps(environment)
        suite_execution.inputs = json.dumps(inputs)
        suite_execution.build_url = build_url
        suite_execution.version = version
        suite_execution.requested_priority_category = requested_priority_category
        suite_execution.description = description
        suite_execution.rich_inputs = rich_inputs
        suite_execution.max_run_time = max_run_time
        suite_execution.pause_on_failure = pause_on_failure
        job_spec_valid, error_message = validate_spec(spec=suite_execution)
        if not job_spec_valid:
            raise SchedulerException("Invalid job spec: {}, Error message: {}".format(suite_execution, error_message))
        suite_execution.is_auto_scheduled_job = is_auto_scheduled_job
        # print ("queue_job_3: {}".format(suite_execution.execution_id))
        suite_execution.save()

        result = suite_execution.execution_id

    except Exception as ex:
        scheduler_logger.exception(str(ex))
        if suite_execution:
            suite_execution.delete()
        raise SchedulerException("Unable to schedule job due to: " + str(ex))
        # TODO: Remove suite execution entry
    # print("Job Id: {} suite: {} Submitted".format(suite_execution.execution_id, suite_path))
    return result


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

def delete_queued_job(job_id):
    jobs_in_queue = JobQueue.objects.all().order_by('priority')
    job_found = False
    with transaction.atomic():
        for job_in_queue in jobs_in_queue:
            if job_id == jobs_in_queue.job_id:
                jobs_in_queue.delete()
            if job_found:
                job_in_queue.priority -= 1
                job_in_queue.save()

def get_next_priority_value(category):
    low, high = SchedulerJobPriority.RANGES[category]
    queued_jobs = JobQueue.objects.filter(priority__gte=low, priority__lte=high).order_by('priority')
    if queued_jobs.count():
        next_priority_value = queued_jobs.last().priority + 1
    else:
        next_priority_value = low
    if next_priority_value > high:
        raise SchedulerException("Exceeded high range for priority category: {}, high: {}".format(category, high))
    return next_priority_value


def get_priority_category_by_priority(priority):
    result = None
    for category, priority_range in SchedulerJobPriority.RANGES.iteritems():
        if (priority >= priority_range[0] and priority <= priority_range[1]):
            result = category
            break
    return result


def move_to_queue_head(job_id):
    this_job_queue_entry = JobQueue.objects.get(job_id=job_id)
    priority_category = get_priority_category_by_priority(priority=this_job_queue_entry.priority)
    low, high = SchedulerJobPriority.RANGES[priority_category]
    custom_test_bed_spec_this = get_suite_based_test_bed_spec(this_job_queue_entry.job_id)

    lowest_priority_allowed = low
    with transaction.atomic():
        queue_entries = JobQueue.objects.all().order_by('priority')
        for queue_entry in queue_entries:

            if custom_test_bed_spec_this:
                custom_test_bed_spec_other = get_suite_based_test_bed_spec(queue_entry.job_id)
                if not queue_entry.pre_emption_allowed:
                    base_test_bed_other = custom_test_bed_spec_other.get("base_test_bed")
                    base_test_bed_this = custom_test_bed_spec_this.get("base_test_bed")
                    if base_test_bed_other == base_test_bed_this:
                        lowest_priority_allowed = queue_entry.priority + 1
                        break

    with transaction.atomic():
        queue_entries = JobQueue.objects.all().order_by('priority').filter(priority__gte=lowest_priority_allowed)
        for queue_entry in queue_entries:
            queue_entry.priority += 1
            queue_entry.save()
        this_job_queue_entry.priority = lowest_priority_allowed
        this_job_queue_entry.save()


def move_to_higher_queue(job_id):
    this_job_queue_entry = JobQueue.objects.get(job_id=job_id)
    priority_category = get_priority_category_by_priority(priority=this_job_queue_entry.priority)

    next_priority_category = priority_category
    if priority_category == SchedulerJobPriority.LOW:
        next_priority_category = SchedulerJobPriority.NORMAL
    if priority_category == SchedulerJobPriority.NORMAL:
        next_priority_category = SchedulerJobPriority.HIGH

    if priority_category == SchedulerJobPriority.HIGH:
        scheduler_logger.exception(SchedulerException("Job-Id: {} already in high priority category"))
    else:
        next_priority_value = get_next_priority_value(next_priority_category)
        this_job_queue_entry.priority = next_priority_value
        this_job_queue_entry.save()


def swap_priorities(job1, job2):
    with transaction.atomic():
        temp = job1.priority
        job1.priority = job2.priority
        job2.priority = temp
        job1.save()
        job2.save()


def increase_decrease_priority(job_id, increase=True):
    priorities_changed = False
    this_job_queue_entry = JobQueue.objects.get(job_id=job_id)
    this_job_priority = this_job_queue_entry.priority
    priority_category = get_priority_category_by_priority(this_job_priority)
    low, high = SchedulerJobPriority.RANGES[priority_category]

    if increase:
        other_priority_jobs = JobQueue.objects.filter(priority__lt=this_job_priority, priority__gte=low).order_by('priority')
    else:
        other_priority_jobs = JobQueue.objects.filter(priority__gt=this_job_priority, priority__lte=high).order_by('-priority')

    if other_priority_jobs.count():
        other_priority_job = other_priority_jobs.last()
        if all(lambda x: x == "suite-based" for x in [other_priority_job.test_bed_type, this_job_queue_entry.test_bed_type]) and (not other_priority_job.pre_emption_allowed):
            # get base test-bed
            custom_test_bed_spec_other = get_suite_based_test_bed_spec(other_priority_job.job_id)
            custom_test_bed_spec_this = get_suite_based_test_bed_spec(this_job_queue_entry.job_id)
            if custom_test_bed_spec_other["base_test_bed"] != custom_test_bed_spec_this["base_test_bed"]:
                swap_priorities(this_job_queue_entry, other_priority_job)
                priorities_changed = True
        else:
            swap_priorities(this_job_queue_entry, other_priority_job)
            priorities_changed = True
    else:
        pass # You are already the highest
    return priorities_changed

def get_manual_lock_test_beds():
    return TestBed.objects.filter(manual_lock=True)

def get_manual_lock_assets():
    return Asset.objects.filter(manual_lock_user__isnull=False)

def get_test_bed_by_name(test_bed_name):
    return TestBed.objects.get(name=test_bed_name)

def get_asset(asset_name, asset_type):
    return Asset.objects.get(name=asset_name, type=asset_type)

def manual_un_lock_assets(test_bed_name, manual_lock_submitter):
    from asset.asset_manager import AssetManager
    AssetManager().manual_un_lock_assets_by_test_bed(test_bed_name=test_bed_name, user=manual_lock_submitter)

def send_error_mail(message, submitter_email=None, job_id=None):
    to_addresses = [TEAM_REGRESSION_EMAIL]
    if submitter_email:
        to_addresses.append(submitter_email)
    content = message
    subject = "Regression: Suite execution error. Job-Id: {}".format(job_id)
    send_mail(to_addresses=to_addresses, content=content, subject=subject)
    pass


def send_test_bed_remove_lock(test_bed=None, asset=None, warning=False, un_lock_warning_time=60 * 10):

    if test_bed:
        submitter_email = test_bed.manual_lock_submitter
        expiry_time = test_bed.manual_lock_expiry_time
        item_name = "test-bed {}".format(test_bed.name)
    else:
        submitter_email = asset.manual_lock_user
        expiry_time = asset.manual_lock_expiry_time
        item_name = "asset {}".format(asset.name)

    default_email_list = [x.email for x in TestbedNotificationEmails.objects.all()]
    to_addresses = [submitter_email]
    to_addresses.extend(default_email_list)

    user = User.objects.get(email=submitter_email)
    content = "Hi {},".format(user.first_name) + "<br>"
    content += "Manual-testing lock duration for {} has exceeded. Expiry time: {}".format(item_name, str(expiry_time)) + "<br>"
    if warning:
        content += "We will unlock {} in {} minutes".format(item_name, un_lock_warning_time / 60) + "<br>"
        subject = "Manual-testing lock duration for {} has exceeded".format(item_name)
    else:
        content += "Unlocking now" + "<br>"
        subject = "Manual lock for {} removed".format(item_name)
    content += "- Regression" + "<br>"

    send_mail(to_addresses=to_addresses, content=content, subject=subject)


def get_job_inputs(job_id):
    job_spec = models_helper.get_suite_execution(suite_execution_id=job_id)
    job_inputs = {}
    if hasattr(job_spec, "inputs"):
        if (job_spec.inputs):
            job_inputs = json.loads(job_spec.inputs)
    return job_inputs


def get_suite(suite_id):
    result = models_helper.get_suite(id=suite_id)
    return result

def get_suite_based_test_bed_spec(job_id):
    spec = None
    s = models_helper.get_suite_execution(suite_execution_id=job_id)
    suite_id = s.suite_id
    if suite_id:
        job_inputs = get_job_inputs(job_id=job_id)
        if "custom_test_bed_spec" in job_inputs:
            spec = job_inputs.get("custom_test_bed_spec", None)
        else:
            suite_spec = get_suite(suite_id=suite_id)
            if suite_spec:
                spec = suite_spec.custom_test_bed_spec
    return spec

def lock_assets(job_id, assets):
    if assets:
        for asset_type, assets in assets.items():
            for asset in assets:
                Asset.add_update(name=asset, type=asset_type)
                Asset.add_job_id(name=asset, type=asset_type, job_id=job_id)

def un_lock_assets(job_id):
    assets = Asset.objects.filter(job_ids__contains=[job_id])
    for asset in assets:
        asset.job_ids = asset.remove_job_id(job_id=job_id)


def pause():
    SchedulerDirective.remove(directive=SchedulerDirectiveTypes.UNPAUSE_QUEUE_WORKER)
    SchedulerDirective.add(directive=SchedulerDirectiveTypes.PAUSE_QUEUE_WORKER)


def unpause():
    SchedulerDirective.remove(directive=SchedulerDirectiveTypes.PAUSE_QUEUE_WORKER)
    SchedulerDirective.add(directive=SchedulerDirectiveTypes.UNPAUSE_QUEUE_WORKER)


class DatetimeEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return super(DatetimeEncoder, obj).default(obj)
        except TypeError:
            return str(obj)



def parse_it(test_case_info, execution):
    if execution.script_path not in test_case_info:
        test_case_info[execution.script_path] = {"num_passed": 0, "num_failed": 0, "num_not_run": 0, "test_cases": {}}
    entry = test_case_info[execution.script_path]
    if execution.result == "PASSED":
        entry["num_passed"] += 1
    elif execution.result == "FAILED":
        entry["num_failed"] += 1
    else:
        entry["num_not_run"] += 1
    entry["test_cases"][execution.test_case_id] = execution


def send_summary_mail(job_id, extra_message=""):
    suite_execution = models_helper.get_suite_execution(suite_execution_id=job_id)
    if suite_execution.email_on_failure_only and suite_execution.result == RESULTS["PASSED"]:
        return True

    test_case_info = collections.OrderedDict()
    test_case_executions = TestCaseExecution.objects.filter(suite_execution_id=job_id).order_by('started_time')
    for test_case_execution in test_case_executions:
        parse_it(test_case_info=test_case_info, execution=test_case_execution)

    scheduler_logger.info("Job {}: Suite Execution: {}".format(str(suite_execution.execution_id), suite_execution))

    suite_execution_attributes = models_helper._get_suite_execution_attributes(suite_execution=models_helper._get_suite_executions(execution_id=suite_execution.execution_id)[0])
    header_list = ["Metric", "Value"]
    table1 = _get_table(header_list=header_list, list_of_rows=suite_execution_attributes)

    all_tables = ""

    for script_path, script_info in test_case_info.iteritems():
        s = ""
        s += "<table class='table table-nonfluid'>"
        s += "<tr><td class='card-header' colspan='4'>{}</td></tr>".format(script_path)
        s += "<tr>"
        s += "<th>Id</th>"
        s += "<th>Result</th>"
        s += "<th>Summary</th>"
        s += "<th>Inputs</th>"
        s += "</tr>"
        test_cases = script_info["test_cases"]
        for test_case_id, test_case_entry in test_cases.iteritems():
            s += "<tr>"

            # Test-case Id
            s += "<td>{}</td>".format(test_case_id)

            # Results
            result_class = "{}"
            if test_case_entry.result == "PASSED":
                result_class = " class='passed' "
            elif test_case_entry.result == "FAILED":
                result_class = " class='failed'"
            s += "<td{}>{}</td>".format(result_class, test_case_entry.result)

            # Summary
            test_case_details = models_helper.get_test_case_details(script_path=script_path, test_case_id=test_case_id)
            summary = test_case_details['summary']
            s += "<td>{}</td>".format(summary)

            # Inputs
            inputs = json.loads(test_case_entry.inputs)
            if inputs:
                s += "<td>{}</td>".format(json.dumps(inputs))

        s += "</table>"
        all_tables += s + "<br>"

    banner = ""
    if suite_execution.banner:
        banner = suite_execution.banner

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
        """ % (css, banner, extra_message, suite_detail_url, table1, all_tables)

        # print html
        attributes_dict = {x["name"]: x["value"] for x in suite_execution_attributes}
        subject = "Regression: Result: {}: {} P:{} F:{}".format(attributes_dict["Result"],
                                                                suite_execution.suite_path,
                                                                attributes_dict["Passed"],
                                                                attributes_dict["Failed"])

        try:
            to_addresses = [suite_execution.submitter_email, TEAM_REGRESSION_EMAIL]
            to_addresses.extend(json.loads(suite_execution.emails))

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