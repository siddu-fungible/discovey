#!/usr/bin/env python
from fun_settings import *
from fun_global import determine_version, is_development_mode
import re
import os
import subprocess
from threading import Thread, Lock
import threading
import traceback

from scheduler_helper import *
import signal
import psutil
import shutil

job_id_timers = {}
job_id_threads = {}

ONE_HOUR = 60 * 60

queue_lock = None


class FunTimer:
    def __init__(self, max_time=10000):
        self.max_time = max_time
        self.start_time = time.time()

    def start(self):
        self.start_time = time.time()

    def is_expired(self):
        return (self.elapsed_time()) > self.max_time

    def elapsed_time(self):
        current_time = time.time()
        return current_time - self.start_time

    def remaining_time(self):
        return self.max_time - self.elapsed_time()


class ShutdownReason:
    ABORTED = -2
    KILLED = -1
    COMPLETED = 1


def clone_job(job_id):
    suite_execution = models_helper.get_suite_execution(suite_execution_id=job_id)
    new_suite_execution_id = models_helper.get_new_suite_execution_id()
    suite_execution.execution_id = new_suite_execution_id.last_suite_execution_id
    suite_execution.pk = None
    return suite_execution

def debug_function(the_function):
    def inner(*args, **kwargs):
        debug_mode = SchedulerConfig.get_debug()
        if debug_mode:
            scheduler_logger.debug(the_function)
        return the_function(*args, **kwargs)
    return inner

class TestBedWorker(Thread):
    def __init__(self):
        super(TestBedWorker, self).__init__()
        self.shutdown_requested = False
        self.warn_list = []
        self.asset_warn_list = []
        self.test_bed_lock_timers = {}
        self.asset_lock_timers = {}

    @debug_function
    def shutdown(self):
        self.shutdown_requested = True

    @debug_function
    def test_bed_unlock_dispatch(self, test_bed_name):
        try:
            test_bed = get_test_bed_by_name(test_bed_name)

            if test_bed.manual_lock:
                if get_current_time() > test_bed.manual_lock_expiry_time:
                    test_bed.manual_lock = False
                    test_bed.save()
                    manual_un_lock_assets(test_bed_name=test_bed.name, manual_lock_submitter=test_bed.manual_lock_submitter)
                    send_test_bed_remove_lock(test_bed=test_bed, warning=False)

                    if test_bed_name in self.test_bed_lock_timers:
                        del self.test_bed_lock_timers[test_bed_name]
            self.warn_list.remove(test_bed_name)
        except Exception as ex:
            scheduler_logger.exception(str(ex))
        finally:
            if test_bed_name in self.warn_list:
                self.warn_list.remove(test_bed_name)

    @debug_function
    def asset_unlock_dispatch(self, asset_name, asset_type):
        composite_key = None
        try:
            composite_key = asset_name + asset_type
            asset = get_asset(asset_name=asset_name, asset_type=asset_type)

            if asset and asset.manual_lock_user:
                if get_current_time() > asset.manual_lock_expiry_time:
                    try:
                        send_test_bed_remove_lock(asset=asset, warning=False)
                    except:
                        pass
                    asset.manual_lock_user = None
                    asset.save()
                    if composite_key in self.asset_lock_timers:
                        del self.asset_lock_timers[composite_key]
            self.asset_warn_list.remove(composite_key)
        except Exception as ex:
            scheduler_logger.exception(str(ex))
        finally:
            if composite_key and composite_key in self.asset_warn_list:
                self.asset_warn_list.remove(composite_key)

    def is_asset_in_warn_list(self, asset):
        found = False
        for asset_in_warn_list in self.asset_warn_list:
            found = (asset.name == asset_in_warn_list["name"]) and (asset.type == asset_in_warn_list["type"])
            if found:
                break
        return found

    @debug_function
    def run(self):
        while not self.shutdown_requested:
            test_beds = get_manual_lock_test_beds()
            for test_bed in test_beds:
                expiry_time = test_bed.manual_lock_expiry_time
                if test_bed.name not in self.warn_list:
                    if get_current_time() > expiry_time:
                        scheduler_logger.info("Test-bed {} manual lock expired".format(test_bed.name))
                        un_lock_warning_time = 60 * SchedulerConfig.get_asset_unlock_warning_time()
                        self.test_bed_lock_timers[test_bed.name] = threading.Timer(un_lock_warning_time, self.test_bed_unlock_dispatch, (test_bed.name,))
                        self.test_bed_lock_timers[test_bed.name].start()
                        self.warn_list.append(test_bed.name)
                        send_test_bed_remove_lock(test_bed=test_bed, warning=True, un_lock_warning_time=un_lock_warning_time)

            assets = get_manual_lock_assets()
            for asset in assets:
                expiry_time = asset.manual_lock_expiry_time
                asset_name = asset.name
                asset_type = asset.type
                composite_key = asset_name + asset_type
                if composite_key not in self.asset_warn_list:
                    if get_current_time() > expiry_time:
                        scheduler_logger.info("Asset {} manual lock expired".format(asset_name))
                        un_lock_warning_time = 60 * SchedulerConfig.get_asset_unlock_warning_time()

                        self.asset_lock_timers[composite_key] = threading.Timer(un_lock_warning_time, self.asset_unlock_dispatch, (asset_name, asset_type))
                        self.asset_lock_timers[composite_key].start()
                        self.asset_warn_list.append(composite_key)
                        send_test_bed_remove_lock(asset=asset, warning=True, un_lock_warning_time=un_lock_warning_time)


            time.sleep(20)

        scheduler_logger.info("TestBedWorker shutdown")


class QueueWorker(Thread):
    def __init__(self):
        super(QueueWorker, self).__init__()
        self.job_threads = {}
        self.not_available_suite_based_test_beds = []

    @debug_function
    def is_high_priority(self, queued_job):
        this_jobs_priority = queued_job.priority
        return this_jobs_priority >= SchedulerJobPriority.RANGES[SchedulerJobPriority.HIGH][0] and this_jobs_priority <= SchedulerJobPriority.RANGES[SchedulerJobPriority.HIGH][1]

    @debug_function
    def abort_job(self, queued_job, reason):
        self.shutdown_reason = ShutdownReason.ABORTED
        scheduler_logger.exception("Queued Job ID: {} exception, Reason: {}".format(queued_job.job_id, reason))
        suite_execution = models_helper.get_suite_execution(suite_execution_id=queued_job.job_id)
        models_helper.update_suite_execution(suite_execution_id=queued_job.job_id,
                                             result=RESULTS["ABORTED"],
                                             state=JobStatusType.ABORTED)
        models_helper.finalize_suite_execution(suite_execution_id=queued_job.job_id)
        send_mail(to_addresses=[suite_execution.submitter_email, TEAM_REGRESSION_EMAIL],
                  subject="Regression: ERROR: Queue worker could not process the job: {}".format(queued_job.job_id),
                  content="Reason: {}".format(reason))

    @debug_function
    def is_not_available_suite_based(self, queued_job, suite_based_spec):
        result = False
        base_test_bed = suite_based_spec.get("base_test_bed", None)
        if base_test_bed and base_test_bed in self.not_available_suite_based_test_beds:
            result = True
        return result

    @debug_function
    def run(self):
        from asset.asset_manager import AssetManager
        asset_manager = AssetManager()
        scheduler_info = get_scheduler_info()
        if scheduler_info:
            if scheduler_info.state == SchedulerStates.SCHEDULER_STATE_PAUSED:
                return
        # while True:
        if True:

            queue_lock.acquire()
            try:
                de_queued_jobs = []
                valid_jobs = self.get_valid_jobs()
                not_available = {}
                self.not_available_suite_based_test_beds = []

                for queued_job in valid_jobs:

                    try:
                        """
                        schedule a container if needed
                        """
                        suite_execution = models_helper.get_suite_execution(suite_execution_id=queued_job.job_id)

                        if queued_job.suspend:
                            scheduler_logger.debug("Queued Job: {} suspended".format(queued_job.job_id))
                            queued_job.message = "De-queueing suspended"
                            queued_job.save()
                            continue

                        suite_based_spec = None
                        if queued_job.is_suite_based():
                            suite_based_spec = get_suite_based_test_bed_spec(job_id=queued_job.job_id)
                            if not suite_based_spec:
                                error_message = "suite-based is requested for: {} but it is invalid".format(queued_job.job_id)
                                scheduler_logger.error(error_message)
                                queued_job.message = error_message
                                queued_job.save()
                                raise Exception(error_message)

                        if queued_job.test_bed_type not in not_available:

                            if queued_job.is_suite_based():
                                if self.is_not_available_suite_based(queued_job=queued_job, suite_based_spec=suite_based_spec):
                                    scheduler_logger.debug(
                                        "Queued job: {} unavailable spec: {}".format(queued_job.job_id, suite_based_spec))
                                    queued_job.message = "Possibly non-preemptable job is queued"
                                    queued_job.save()
                                    continue

                            availability = asset_manager.get_test_bed_availability(test_bed_type=queued_job.test_bed_type,
                                                                                   suite_base_test_bed_spec=suite_based_spec)
                            if availability["status"]:
                                de_queued_jobs.append(queued_job)
                                assets_required = availability["assets_required"]
                                custom_test_bed_spec = availability.get("custom_test_bed_spec", None)
                                job_id_threads[suite_execution.execution_id] = self.execute_job(job_id=queued_job.job_id,
                                                                                                assets_required=assets_required,
                                                                                                custom_test_bed_spec=custom_test_bed_spec)

                            else:
                                if not queued_job.is_suite_based():
                                    not_available[queued_job.test_bed_type] = availability["message"]
                                if queued_job.is_suite_based():
                                    if not queued_job.pre_emption_allowed or self.is_high_priority(queued_job):
                                        if suite_based_spec:
                                            base_test_bed = suite_based_spec.get("base_test_bed", None)
                                            if base_test_bed:
                                                self.not_available_suite_based_test_beds.append(base_test_bed)

                                # print("Not available: {}".format(availability["message"]))
                                queued_job.message = availability["message"]
                                queued_job.save()
                        else:
                            queued_job.message = not_available[queued_job.test_bed_type]
                            queued_job.save()
                    except Exception as ex:
                        reason = "Exception: {}: {}".format(str(ex), traceback.format_exc())
                        scheduler_logger.exception(
                            "Queued Job ID: {} exception, Reason: {}".format(queued_job.job_id, reason))

                        self.abort_job(queued_job=queued_job, reason=reason)
                time.sleep(5)

                for de_queued_job in de_queued_jobs:
                    scheduler_logger.info("Job: {} Dequeuing".format(de_queued_job.job_id))
                    d = JobQueue.objects.get(job_id=de_queued_job.job_id)
                    d.delete()

            except Exception as ex:
                scheduler_logger.exception(str(ex))
            # scheduler_logger.info("QueueWorker: Before lock release")
            # scheduler_logger.info("Lock-release: QueueWorker")
            queue_lock.release()
            time.sleep(5)

    @debug_function
    def get_valid_jobs(self):
        # scheduler_logger.info("get_valid_jobs")
        valid_jobs = []
        invalid_jobs = []
        queued_jobs = JobQueue.objects.all().order_by('priority')
        for queued_job in queued_jobs:
            job_spec = models_helper.get_suite_execution(suite_execution_id=queued_job.job_id)
            if job_spec.state == JobStatusType.QUEUED:
                valid_jobs.append(queued_job)
            else:
                scheduler_logger.error(
                    "{} will be removed from queue".format(get_job_string_from_spec(job_spec=job_spec)))
                invalid_jobs.append(queued_job)
        for invalid_job in invalid_jobs:
            invalid_job.delete()
        return valid_jobs

    @debug_function
    def execute_job(self, job_id, assets_required=None, custom_test_bed_spec=None):
        suite_execution = models_helper.get_suite_execution(suite_execution_id=job_id)
        if custom_test_bed_spec:
            suite_execution.add_run_time_variable("custom_test_bed_spec", custom_test_bed_spec)
        scheduler_logger.info("{} Executing".format(get_job_string_from_spec(job_spec=suite_execution)))
        models_helper.update_suite_execution(suite_execution_id=job_id, state=JobStatusType.IN_PROGRESS)
        lock_assets(job_id=job_id, assets=assets_required)
        t = SuiteWorker(job_id=job_id)
        t.initialize()
        return t

queue_worker = QueueWorker()
test_bed_monitor = TestBedWorker()

@debug_function
def get_job_string_from_spec(job_spec):
    return "{} st={}".format(get_job_string(job_spec.execution_id), job_spec.state)

@debug_function
def get_job_string(job_id):
    return "Job: {}".format(job_id)

@debug_function
def queue_job(job_id):
    queue_lock.acquire()
    # scheduler_logger.info("Lock-acquire: queue_job")
    job_spec = models_helper.get_suite_execution(suite_execution_id=job_id)
    if job_spec and job_spec.state == JobStatusType.SCHEDULED:
        next_priority_value = get_next_priority_value(job_spec.requested_priority_category)
        new_job = JobQueue(priority=next_priority_value, job_id=job_spec.execution_id,
                           test_bed_type=job_spec.test_bed_type)
        new_job.save()
        models_helper.update_suite_execution(suite_execution_id=job_spec.execution_id, state=JobStatusType.QUEUED)

        time.sleep(1)

    else:
        if job_spec:
            scheduler_logger.error("{} trying to be queued".format(get_job_string_from_spec(job_spec)))

    # scheduler_logger.info("Lock-release: queue_job")
    queue_lock.release()

@debug_function
def timer_dispatch(job_id):
    # Add to queue
    queue_job(job_id=job_id)
    if job_id in job_id_timers:
        del job_id_timers[job_id]


def report_error(job_spec, error_message, local_logger=None):
    emails = json.loads(job_spec.emails)
    scheduler_logger.exception(error_message)
    if local_logger:
        local_logger.exception(error_message)
    # send email


class SuiteWorker(Thread):
    RUN_TIME_ROOT_VARIABLE = "scheduler"

    def __init__(self, job_id):
        super(SuiteWorker, self).__init__()
        self.job_id = job_id

        self.initialized = False
        self.local_scheduler_logger = None
        self.log_handler = None
        self.script_items = None

        self.suite_execution = None
        self.shutdown_reason = None
        self.active_script_item_index = -1
        self.current_script_process_id = None  # run-time # done
        self.current_script_path = None     # run-time
        self.suite_shutdown = False  # run-time
        self.summary_extra_message = ""
        self.current_script_item_index = 0  # run-time  # done
        self.suite_completed = False   # run-time
        self.job_state = JobStatusType.IN_PROGRESS

    @debug_function
    def re_initialize(self):
        try:
            self.prepare_loggers()
            self.prepare_script_items()
            current_script_info = self.get_suite_run_time("current_script_info")
            if current_script_info:
                self.current_script_process_id = current_script_info.get("current_script_process_id", None)
                self.current_script_path = current_script_info.get("current_script_path", None)
                self.current_script_item_index = current_script_info.get("current_script_item_index", None)

                self.active_script_item_index = current_script_info.get("active_script_item_index", None)
            else:
                self.abort_suite("Unable to re-initialize suite as current_script_info could not recovered")

        except Exception as ex:
            scheduler_logger.exception(str(ex))
            suite_execution = models_helper.get_suite_execution(suite_execution_id=self.job_id)
            send_error_mail(submitter_email=suite_execution.submitter_email,
                            job_id=self.job_id,
                            message="Suite execution error due to: {}".format(str(ex)))

    @debug_function
    def prepare_loggers(self):
        local_scheduler_logger = logging.getLogger("scheduler_log_{}.txt".format(self.job_id))
        local_scheduler_logger.setLevel(logging.INFO)
        self.log_handler = logging.handlers.RotatingFileHandler(self.get_job_dir() + "/scheduler.log.txt",
                                                                maxBytes=TEN_MB,
                                                                backupCount=5)
        self.log_handler.setFormatter(
            logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        if len(local_scheduler_logger.handlers):
            del local_scheduler_logger.handlers[:]
        local_scheduler_logger.addHandler(hdlr=self.log_handler)
        self.local_scheduler_logger = local_scheduler_logger

    @debug_function
    def initialize(self):

        # Setup the suites own logger
        try:
            self.prepare_job_directory()
            self.prepare_loggers()
            models_helper.update_suite_execution(suite_execution_id=self.job_id,
                                                 result=RESULTS["IN_PROGRESS"],
                                                 state=JobStatusType.IN_PROGRESS,
                                                 started_time=get_current_time())

            try:
                self.prepare_tags()
                self.prepare_script_items()
            except Exception as ex:
                self.error("Prepare script items exception: {}".format(str(ex)))
                self.shutdown_suite(reason=ShutdownReason.ABORTED)
            self.initialized = True
        except Exception as ex:
            scheduler_logger.exception(str(ex))
            suite_execution = models_helper.get_suite_execution(suite_execution_id=self.job_id)
            send_error_mail(submitter_email=suite_execution.submitter_email,
                            job_id=self.job_id,
                            message="Suite execution error due to: {}".format(str(ex)))

    @debug_function
    def get_suite_execution(self, refresh=False):
        if not self.suite_execution or refresh:
            self.suite_execution = models_helper.get_suite_execution(suite_execution_id=self.job_id)
        return self.suite_execution

    @debug_function
    def shutdown_suite(self, reason=ShutdownReason.KILLED):
        self.shutdown_reason = reason
        scheduler_logger.info("{} Shutdown_suite. Reason: {}".format(get_job_string_from_spec(job_spec=self.get_suite_execution()), reason))
        self.suite_shutdown = True
        if self.current_script_process_id:
            for i in range(2):
                try:
                    if self.is_process_running(pid=self.current_script_process_id, script_path=self.current_script_path):
                        os.kill(self.current_script_process_id, signal.SIGINT)
                        time.sleep(5)
                        os.kill(self.current_script_process_id, signal.SIGKILL)
                except Exception as ex:
                    pass

        suite_execution = models_helper.get_suite_execution(suite_execution_id=self.job_id)
        if suite_execution:  # If we used the delete option from the UI, this will be None
            suite_execution.completed_time = get_current_time()
            suite_execution.save()
        self.suite_complete()

    @debug_function
    def get_job_dir(self):
        return LOGS_DIR + "/" + LOG_DIR_PREFIX + str(self.job_id)

    @debug_function
    def prepare_job_directory(self):
        job_dir = self.get_job_dir()
        try:
            if not os.path.exists(job_dir):
                os.makedirs(job_dir)
        except Exception as ex:
            raise SchedulerException(str(ex))

    @debug_function
    def ensure_scripts_exists(self, script_paths):
        result = True
        error_message = ""
        for script_path in script_paths:
            if not os.path.exists(script_path):
                error_message = "Script {} not found".format(script_path)
                result = False
                break
        return result, error_message

    @debug_function
    def get_scripts(self, suite_id=None):
        suite = Suite.objects.get(id=suite_id)
        return suite.entries

    @debug_function
    def abort_suite(self, error_message):
        self.shutdown_reason = ShutdownReason.ABORTED
        models_helper.update_suite_execution(suite_execution_id=self.job_id,
                                             result=RESULTS["ABORTED"],
                                             state=JobStatusType.ABORTED)
        models_helper.finalize_suite_execution(suite_execution_id=self.job_id)
        self.error(error_message)
        self.shutdown_suite(reason=self.shutdown_reason)

    @debug_function
    def get_script_string(self, script_path=None):
        script_string = " "
        if script_path:
            script_string = " Script: {} ".format(script_path)
        return script_string

    @debug_function
    def debug(self, message, script_path=None):
        self.local_scheduler_logger.info("{} {}{}".format(get_job_string_from_spec(job_spec=self.get_suite_execution()),
                                                          self.get_script_string(script_path=script_path), message))

    @debug_function
    def error(self, message, script_path=None):
        scheduler_logger.exception("{} {}{}".format(get_job_string_from_spec(job_spec=self.get_suite_execution()),
                                                    self.get_script_string(script_path=script_path), message))
        self.local_scheduler_logger.exception(message)

    @debug_function
    def get_script_inputs(self, script_item):
        script_inputs = script_item.get("inputs", None)
        job_inputs = self.get_suite_execution().get_inputs()
        final_inputs = {}
        if job_inputs:
            final_inputs.update(job_inputs)
        if script_inputs:
            final_inputs.update(script_inputs)

        return final_inputs

    @debug_function
    def suite_complete(self):
        state = JobStatusType.COMPLETED
        un_lock_assets(self.job_id)
        if self.shutdown_reason == ShutdownReason.ABORTED:
            state = JobStatusType.ABORTED
        if self.shutdown_reason == ShutdownReason.KILLED:
            state = JobStatusType.KILLED

        self.debug("Before updating suite execution: {}".format(self.job_id))
        models_helper.update_suite_execution(suite_execution_id=self.job_id,
                                             state=state,
                                             completed_time=get_current_time())
        time.sleep(1)
        models_helper.update_suite_execution(suite_execution_id=self.job_id,
                                             state=state,
                                             completed_time=get_current_time())
        self.debug("After updating suite execution: {}".format(self.job_id))
        self.debug("Before finalize")
        models_helper.finalize_suite_execution(suite_execution_id=self.job_id)
        self.debug("After finalize")

        suite_executions = models_helper._get_suite_executions(execution_id=self.job_id, save_test_case_info=True)
        send_summary_mail(job_id=self.job_id,
                          extra_message=self.summary_extra_message)
        models_helper.update_suite_execution(suite_execution_id=self.job_id,
                                             state=state)
        self.suite_completed = True

    @debug_function
    def cleanup(self):
        self.log_handler.close()

    @debug_function
    def get_suite(self):
        result = None
        suite_execution = self.get_suite_execution()
        if suite_execution.suite_id:
            result = get_suite(suite_id=suite_execution.suite_id)
        return result

    @debug_function
    def prepare_script_items(self):
        script_items = []
        suite = self.get_suite()
        suite_execution = self.get_suite_execution()
        if suite:
            script_items = self.get_scripts(suite_id=suite_execution.suite_id)
        elif suite_execution.script_path:
            script_items.append({"script_path": suite_execution.script_path})

        script_paths = [SCRIPTS_DIR + "/" + x["script_path"].lstrip("/") for x in script_items]

        scripts_exist, error_message = self.ensure_scripts_exists(script_paths)
        if not scripts_exist:
            self.abort_suite(error_message=error_message)

        self.debug("Scripts to be executed")
        map(lambda f: self.local_scheduler_logger.debug("{}: {}".format(f[0], f[1])), enumerate(script_paths))
        self.debug("Starting executing scripts")

        self.script_items = script_items
        if not self.script_items:
            self.abort_suite("No scripts detected in suite")

        return self.script_items

    @debug_function
    def prepare_tags(self):
        suite_execution = self.get_suite_execution()
        all_tags = []
        job_tags = suite_execution.get_tags()
        if job_tags:
            all_tags = job_tags

        suite = self.get_suite()
        if suite and suite.tags:
            all_tags.extend(suite.tags)
        models_helper.update_suite_execution(suite_execution_id=self.job_id,
                                             tags=all_tags)

    @debug_function
    def is_process_running(self, pid, script_path):
        # scheduler_logger.info("is process running: {} {}".format(pid, script_path))
        running = False
        for p in psutil.process_iter():
            try:
                if p.pid == pid and (script_path in p.cmdline()):
                    # running = p.status() == "running"
                    running = True
                    # scheduler_logger.info("PID: {} is running: {}".format(pid, running))
                    break
            except Exception as ex:
                scheduler_logger.exception("is process running: {} {}: {}".format(pid, script_path, str(ex)))
        return running

    @debug_function
    def run_next(self):
        if not self.initialized:
            self.initialize()
        suite_execution = self.get_suite_execution()
        if suite_execution:
            if suite_execution.state >= JobStatusType.IN_PROGRESS and ((get_current_time() - suite_execution.started_time).total_seconds() > suite_execution.max_run_time):
                self.abort_suite(error_message="Max run-time exceeded")

        if self.suite_shutdown or self.suite_completed:
            return



        script_item = self.script_items[self.current_script_item_index]

        if self.current_script_item_index == self.active_script_item_index:
            if not self.is_process_running(pid=self.current_script_process_id, script_path=self.current_script_path):
                self.debug(message="Executed", script_path=self.current_script_path)
                self.set_next_script_item_index()

        elif self.current_script_item_index > self.active_script_item_index:
            self.start_script(script_item=script_item, script_item_index=self.current_script_item_index)  # schedule it

    @debug_function
    def update_suite_run_time(self, variable_name, value):
        s = self.get_suite_execution(refresh=True)
        if s:
            if self.RUN_TIME_ROOT_VARIABLE not in s.run_time:
                s.add_run_time_variable(self.RUN_TIME_ROOT_VARIABLE, None)

            rt = s.get_run_time_variable(self.RUN_TIME_ROOT_VARIABLE)
            if not rt:
                rt = {variable_name: value}
            else:
                rt[variable_name] = value
            s.add_run_time_variable(self.RUN_TIME_ROOT_VARIABLE, rt)

    @debug_function
    def get_suite_run_time(self, variable_name):
        s = self.get_suite_execution(refresh=True)
        run_time = s.get_run_time_variable(name= self.RUN_TIME_ROOT_VARIABLE)
        result = run_time.get(variable_name, None)
        return result

    @debug_function
    def clear_run_time(self):
        s = models_helper.get_suite_execution(suite_execution_id=self.job_id)
        if self.RUN_TIME_ROOT_VARIABLE in s.run_time:
            s.run_time["scheduler"] = None
            s.save()

    @debug_function
    def start_script(self, script_item, script_item_index):
        # print ("Start_script: {}".format(script_item))
        script_path = SCRIPTS_DIR + "/" + script_item["script_path"].lstrip("/")

        if self.suite_shutdown:
            self.error(message="Suite shutdown requested", script_path=script_path)
            self.summary_extra_message = "Suite was shutdown"
            self.shutdown_suite(reason=ShutdownReason.ABORTED)
            return

        relative_path = script_path.replace(SCRIPTS_DIR, "")

        self.debug("Before running script: {}".format(script_path))

        console_log_file_name = self.get_job_dir() + "/" + get_flat_console_log_file_name("/{}".format(script_path), script_item_index)
        suite = self.get_suite()
        # if suite and suite.type == "TASK":
        #    console_log_file_name = self.get_job_dir() + "/" + os.path.basename(script_path) + ".task.log.txt"

        try:

            with open(console_log_file_name, "w") as console_log:
                self.local_scheduler_logger.info("Executing: {}".format(script_path))

                popens = ["python",
                          script_path,
                          "--" + "logs_dir={}".format(self.get_job_dir()),
                          "--" + "suite_execution_id={}".format(self.job_id),
                          "--" + "relative_path={}".format(relative_path),
                          "--" + "log_prefix={}".format(script_item_index)]

                script_level_test_case_ids = script_item.get("test_case_ids", None)
                if script_level_test_case_ids:
                    popens.append("--test_case_ids=" + ','.join(str(v) for v in script_item["test_case_ids"]))

                suite_execution = self.get_suite_execution()
                if suite_execution.environment:
                    popens.append("--environment='{}'".format(json.dumps(suite_execution.get_environment())))  # TODO: validate

                script_inputs = self.get_script_inputs(script_item=script_item)
                if script_inputs:
                    popens.append("--inputs='{}'".format(json.dumps(script_inputs)))  # TODO: validate

                do_run = True
                if suite_execution.is_re_run:
                    if suite_execution.re_run_info:
                        if str(script_item_index) in suite_execution.re_run_info:
                            re_run_info = suite_execution.re_run_info[str(script_item_index)]
                            popens.append("--re_run_info='{}'".format(json.dumps(re_run_info)))
                        else:
                            do_run = False
                disabled_script = script_item.get("disabled", None)
                if disabled_script:
                    do_run = False
                if do_run:
                    self.debug("Before subprocess Script: {}".format(script_path))
                    popens = ['nohup'] + popens + [" &"]
                    full_command = ' '.join(popens)
                    new_process = subprocess.Popen(full_command, stdout=console_log, stderr=console_log, shell=True)
                    self.current_script_process_id = None
                    script_start_timer = FunTimer(max_time=20)
                    while not script_start_timer.is_expired():
                        suite_execution = self.get_suite_execution(refresh=True)
                        process_id_run_time = suite_execution.get_run_time_variable("process_id")
                        if process_id_run_time:
                            script_process_id_from_run_time = process_id_run_time.get(str(script_item_index), None)
                            if script_process_id_from_run_time:
                                self.current_script_process_id = int(script_process_id_from_run_time)
                                break

                    if not self.current_script_process_id:
                        self.abort_suite("Unable to fetch process id from script")
                    else:
                        self.current_script_path = script_path
                        self.current_script_item_index = script_item_index
                        self.active_script_item_index = script_item_index

                        current_script_info = {"current_script_process_id": self.current_script_process_id,
                                               "current_script_item_index": self.current_script_item_index,
                                               "current_script_path": script_path,
                                               "active_script_item_index": self.active_script_item_index}
                        self.update_suite_run_time("current_script_info", current_script_info)
                else:
                    self.set_next_script_item_index()

        except Exception as ex:
            self.error("Script error {}, exception: {}".format(script_item, str(ex)))
            self.set_next_script_item_index()

    @debug_function
    def is_suite_completed(self):
        return self.suite_completed is True

    @debug_function
    def set_next_script_item_index(self):
        self.current_script_item_index += 1
        if self.current_script_item_index >= len(self.script_items):
            self.suite_complete()
            self.cleanup()

@debug_function
def process_killed_jobs():
    killed_jobs = KilledJob.objects.order_by('killed_time')
    for killed_job in killed_jobs:
        killed_job_id = killed_job.job_id
        try:
            q = JobQueue.objects.get(job_id=killed_job.job_id)
            q.delete()
        except:
            pass

        if killed_job_id in job_id_threads:
            try:
                models_helper.update_suite_execution(suite_execution_id=killed_job_id, result=RESULTS["KILLED"])
            except:
                pass
            t = job_id_threads[killed_job_id]
            scheduler_logger.info("Job: {} Killing".format(get_job_string(killed_job_id)))
            try:
                t.shutdown_suite(reason=ShutdownReason.KILLED)
                scheduler_logger.info("Job: {} Completed shutdown_suite".format(get_job_string(killed_job_id)))
            except Exception as ex:
                scheduler_logger.exception(str(ex))
            finally:
                pass

            if killed_job_id in job_id_timers:
                try:
                    if killed_job_id in job_id_timers:
                        t = job_id_timers[killed_job_id]
                        t.cancel()
                except Exception as ex:
                    scheduler_logger.error(str(ex))
                finally:
                    try:
                        del job_id_timers[killed_job_id]
                    except:
                        pass

        killed_job.delete()

@debug_function
def process_submissions():
    """
    Process job submissions that came in through queue_job
    :return:
    """
    time.sleep(1)
    # sort by date
    """

    """
    # Process only from yesterday
    now = get_current_time()
    yesterday = now - timedelta(days=1)
    # job_specs = JobSpec.objects.filter().order_by("-submission_time")

    queue_lock.acquire()
    # scheduler_logger.info("Lock: process_submissions")
    job_specs = models_helper.get_suite_executions_by_filter(submitted_time__gte=yesterday,
                                                             state=JobStatusType.SUBMITTED).order_by("submitted_time")

    for job_spec in job_specs:
        try:
            # Execute
            job_id = job_spec.execution_id
            scheduler_logger.info(
                "{} Process submission : submitter: {}".format(get_job_string(job_id=job_id), job_spec.submitter_email))

            schedule_it = True
            scheduling_time = get_scheduling_time(spec=job_spec)
            scheduler_logger.info(
                "{} Schedule it: {} Time: {}".format(get_job_string_from_spec(job_spec=job_spec), schedule_it,
                                                     scheduling_time))
            if job_spec and schedule_it and (scheduling_time >= 0):
                t = threading.Timer(scheduling_time, timer_dispatch, (job_spec.execution_id,))
                job_id_timers[job_id] = t
                models_helper.update_suite_execution(suite_execution_id=job_id, scheduled_time=get_current_time() + datetime.timedelta(seconds=scheduling_time), state=JobStatusType.SCHEDULED)
                t.start()
            if scheduling_time < 0:
                scheduler_logger.critical("{} Unable to process job submission. Scheduling time in the past".format(
                    get_job_string_from_spec(job_spec=job_spec)))
                job_spec.delete()

        except Exception as ex:
            scheduler_logger.exception(str(ex))
    queue_lock.release()

@debug_function
def process_external_requests():
    """
    request_file = SCHEDULER_REQUESTS_DIR + "/request.json"
    request = parse_file_to_json(file_name=request_file)
    if request and "request" in request:
        if request["request"] == "stop":
            set_scheduler_state(SchedulerStates.SCHEDULER_STATE_STOPPING)
    return request
    """
    directive = SchedulerDirective.get_recent()
    if directive:
        if directive.directive == SchedulerDirectiveTypes.PAUSE_QUEUE_WORKER:
            set_scheduler_state(SchedulerStates.SCHEDULER_STATE_PAUSED)
            SchedulerDirective.remove(directive.directive)
            set_annoucement("Scheduler queue worker is paused")
        if directive.directive == SchedulerDirectiveTypes.UNPAUSE_QUEUE_WORKER:
            scheduler_info = get_scheduler_info()
            if scheduler_info.state == SchedulerStates.SCHEDULER_STATE_PAUSED:
                clear_announcements()
                set_scheduler_state(SchedulerStates.SCHEDULER_STATE_RUNNING)
            SchedulerDirective.remove(directive.directive)
    pass

@debug_function
def ensure_singleton():
    if os.path.exists(SCHEDULER_PID):
        raise SchedulerException("Only one instance of scheduler.py is permitted")
    else:
        with open(SCHEDULER_PID, "w") as f:
            pid = os.getpid()
            f.write(str(pid))

@debug_function
def run_to_completion(max_wait_time=ONE_HOUR):
    num_active_threads = len(job_id_threads.keys())
    retry_interval = 60
    shutdown_grace_period = max_wait_time
    elapsed_time = 0
    start_time = time.time()
    while num_active_threads and elapsed_time < shutdown_grace_period:
        scheduler_logger.info("Active threads: {}".format(num_active_threads))
        time.sleep(retry_interval)
        scheduler_logger.info("Sleeping for {}".format(retry_interval))
        num_active_threads = len(job_id_threads.keys())
        elapsed_time = time.time() - start_time
    if elapsed_time > shutdown_grace_period:
        scheduler_logger.critical("Shutdown grace period expired")

@debug_function
def remove_pid():
    if os.path.exists(SCHEDULER_PID):
        os.remove(SCHEDULER_PID)

@debug_function
def graceful_shutdown(max_wait_time=ONE_HOUR):
    scheduler_logger.info("Trying graceful shutdown")
    run_to_completion(max_wait_time=max_wait_time)
    remove_pid()
    set_scheduler_state(SchedulerStates.SCHEDULER_STATE_STOPPED)
    scheduler_logger.info("Exiting graceful shutdown")

@debug_function
def process_auto_scheduled_jobs():
    # Get auto_scheduled_jobs
    auto_scheduled_jobs = models_helper.get_suite_executions_by_filter(is_auto_scheduled_job=True, disable_schedule=False)
    auto_scheduled_jobs = auto_scheduled_jobs.order_by('submitted_time')

    for auto_scheduled_job in auto_scheduled_jobs:
        auto_schedule_job_id = auto_scheduled_job.execution_id
        in_progress_suites = models_helper.get_suite_executions_by_filter(state__gt=JobStatusType.AUTO_SCHEDULED,
                                                                          auto_scheduled_execution_id=auto_schedule_job_id)
        if not in_progress_suites.count():
            # if job_id not in progress, clone and submit
            print("Cloning")
            cloned_job = clone_job(job_id=auto_schedule_job_id)
            cloned_job.submitted_time = get_current_time()
            cloned_job.state = JobStatusType.SUBMITTED
            cloned_job.is_auto_scheduled_job = False
            cloned_job.auto_scheduled_execution_id = auto_schedule_job_id
            if auto_scheduled_job.scheduling_type == SchedulingType.TODAY and auto_scheduled_job.repeat_in_minutes > 0:
                auto_scheduled_job.scheduling_type = SchedulingType.REPEAT
                auto_scheduled_job.save()
            scheduler_logger.info("{} instantiating auto-scheduled job to {}".format(
                get_job_string_from_spec(job_spec=auto_scheduled_job),
                get_job_string_from_spec(job_spec=cloned_job)))
            cloned_job.save()

@debug_function
def process_container_suites():
    container_executions = models_helper.get_suite_executions_by_filter(suite_type=SuiteType.CONTAINER,
                                                                        state=JobStatusType.IN_PROGRESS)

    for container_execution in container_executions:
        container_execution_id = container_execution.execution_id
        all_jobs_completed = True

        item_executions = models_helper.get_suite_executions_by_filter(
            suite_container_execution_id=container_execution_id)
        for item_execution in item_executions:
            if item_execution.state > JobStatusType.AUTO_SCHEDULED:
                all_jobs_completed = False
                break

        if all_jobs_completed:
            models_helper.update_suite_execution(suite_execution_id=container_execution.execution_id,
                                                 state=JobStatusType.COMPLETED)

@debug_function
def clear_out_queue():
    JobQueue.objects.all().delete()

@debug_function
def initialize():
    set_scheduler_state(SchedulerStates.SCHEDULER_STATE_RUNNING)
    test_bed_monitor.start()
    clear_out_old_jobs()
    recover_in_progress_jobs()

    if is_development_mode():
        auto_scheduled_jobs = models_helper.get_suite_executions_by_filter(state=JobStatusType.AUTO_SCHEDULED)
        for auto_scheduled_job in auto_scheduled_jobs:
            auto_scheduled_job.disable_schedule = True
            auto_scheduled_job.save()

@debug_function
def join_suite_workers():
    jobs_to_be_removed = []
    for job_id, t in job_id_threads.iteritems():
        try:

            if not t.is_suite_completed():
                t.run_next()
            else:
                jobs_to_be_removed.append(job_id)
            if job_id not in job_id_threads:
                jobs_to_be_removed.append(job_id)
        except Exception as ex:
            traceback.print_exc()
            submitter_email = TEAM_REGRESSION_EMAIL
            suite_execution = models_helper.get_suite_execution(suite_execution_id=job_id)
            if suite_execution:
                submitter_email = suite_execution.submitter_email
            send_error_mail(submitter_email=submitter_email,
                            job_id=job_id,
                            message="Suite execution error at run_next. Exception: {}".format(str(ex)))
            jobs_to_be_removed.append(job_id)

    for job_to_be_removed in jobs_to_be_removed:
        if job_to_be_removed in job_id_threads:
            del job_id_threads[job_to_be_removed]

@debug_function
def recover_in_progress_jobs():
    in_progress_jobs = models_helper.get_suite_executions_by_filter(state=JobStatusType.IN_PROGRESS)
    for in_progress_job in in_progress_jobs:
        suite_worker = SuiteWorker(job_id=in_progress_job.execution_id)
        job_id_threads[in_progress_job.execution_id] = suite_worker
        suite_worker.re_initialize()
        pass
    pass

@debug_function
def clear_out_old_jobs():
    old_jobs = models_helper.get_suite_executions_by_filter(state=JobStatusType.SCHEDULED)
    for old_job in old_jobs:
        old_job.state = JobStatusType.ABORTED
        old_job.save()

    if is_development_mode():
        old_jobs = models_helper.get_suite_executions_by_filter(state=JobStatusType.AUTO_SCHEDULED)
        for old_job in old_jobs:
            old_job.delete()

        old_jobs = models_helper.get_suite_executions_by_filter(state=JobStatusType.QUEUED)
        for old_job in old_jobs:
            old_job.delete()

        old_jobs = models_helper.get_suite_executions_by_filter(state=JobStatusType.SCHEDULED)
        for old_job in old_jobs:
            old_job.delete()

        old_jobs = models_helper.get_suite_executions_by_filter(state=JobStatusType.IN_PROGRESS)
        for old_job in old_jobs:
            old_job.delete()

        JobQueue.objects.all().delete()

@debug_function
def cleanup_unused_assets():
    try:
        all_assets = Asset.objects.all()
        for asset in all_assets:
            job_ids = asset.job_ids

            job_ids_to_remove = []
            if job_ids:
                for job_id in job_ids:
                    s = models_helper.get_suite_execution(suite_execution_id=job_id)
                    if s:
                        if s.state <= JobStatusType.COMPLETED:
                            job_ids_to_remove.append(job_id)
                    else:
                        asset.remove_job_id(job_id=job_id)
            job_ids = filter(lambda x: x not in job_ids_to_remove, job_ids)
            asset.job_ids = job_ids
            asset.save()
    except Exception as ex:
        scheduler_logger.exception(str(ex))


def handle_pdb(sig, frame):
    import pdb
    pdb.Pdb().set_trace(frame)



if __name__ == "__main__":
    queue_lock = Lock()
    ensure_singleton()
    initialize()
    scheduler_logger.info("Started Scheduler")
    signal.signal(signal.SIGUSR1, handle_pdb)

    run = True
    while run:
        time.sleep(1)
        set_main_loop_heartbeat()
        scheduler_info = get_scheduler_info()
        process_external_requests()
        if scheduler_info.state == SchedulerStates.SCHEDULER_STATE_STOPPED:
            scheduler_logger.info("Scheduler Bye bye!")
            run = False
            os.kill(os.getpid(), 9)
            break
        if scheduler_info.state == SchedulerStates.SCHEDULER_STATE_PAUSED:
            scheduler_logger.info("Scheduler is paused")
            time.sleep(1)

            continue

        try:
            process_killed_jobs()
            process_container_suites()
            queue_worker.run()
            scheduler_info = get_scheduler_info()

            cleanup_unused_assets()
            join_suite_workers()
            if (scheduler_info.state != SchedulerStates.SCHEDULER_STATE_STOPPING) and \
                    (scheduler_info.state != SchedulerStates.SCHEDULER_STATE_STOPPED):
                process_auto_scheduled_jobs()
                process_submissions()

            """
            if scheduler_info.state == SchedulerStates.SCHEDULER_STATE_STOPPING:
                max_wait_time = ONE_HOUR
                if request and "max_wait_time" in request:
                    max_wait_time = int(request["max_wait_time"])
                graceful_shutdown(max_wait_time=max_wait_time)
            """

        except (SchedulerException, Exception) as ex:
            scheduler_logger.exception(str(ex))
            send_error_mail(message="Scheduler exception: Ex: {}".format(ex))
            time.sleep(60)
