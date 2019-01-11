#!/usr/bin/env python
from fun_settings import *
from fun_global import get_current_time, RESULTS, determine_version
import os
import re
import subprocess
from threading import Thread
import threading
from scheduler_helper import *
import dateutil.parser
import signal
import psutil
import shutil

job_id_threads = {}
job_id_timers = {}

ONE_HOUR = 60 * 60

def timed_dispatcher(suite_worker_obj):
    job_id_threads[suite_worker_obj.job_id] = (suite_worker_obj)
    suite_worker_obj.start()
    if suite_worker_obj.job_id in job_id_timers:
        del job_id_timers[suite_worker_obj.job_id]


def parse_suite(suite_name):
    suite_file_name = SUITES_DIR + "/" + suite_name + JSON_EXTENSION
    suite_spec = parse_file_to_json(file_name=suite_file_name)
    if not suite_spec:
        raise SchedulerException("Unable to parse suite-spec: {}".format(suite_file_name))
    return suite_spec


class SuiteWorker(Thread):
    def __init__(self, job_spec):
        super(SuiteWorker, self).__init__()
        self.job_spec = job_spec
        self.job_id = job_spec["job_id"]
        self.job_dir = None
        self.job_test_case_ids = None
        self.job_environment = {}
        self.job_build_url = "http://dochub.fungible.local/doc/jenkins/funsdk/latest/"
        if 'script_path' in job_spec:
            self.job_script_path = job_spec["script_path"]
        if "test_case_ids" in job_spec:
            self.job_test_case_ids = job_spec["test_case_ids"]
        if "build_url" in job_spec:
            self.job_build_url = job_spec["build_url"]
        if "environment" in job_spec:
            self.job_environment = job_spec["environment"] 
        self.current_script_process = None

        self.suite_shutdown = False
        self.abort_on_failure_requested = False
        self.summary_extra_message = ""

    def shutdown_suite(self):
        job_id = self.job_spec["job_id"]
        scheduler_logger.info("Job Id: {} Shutdown_suite".format(job_id))
        if self.current_script_process:
            try:
                os.kill(self.current_script_process.pid, signal.SIGINT)
                time.sleep(5)
            except Exception as ex:
                scheduler_logger.error(str(ex))
            if psutil.pid_exists(self.current_script_process.pid):
                try:
                    os.kill(self.current_script_process.pid, signal.SIGKILL)
                except Exception as ex:
                    scheduler_logger.error(str(ex))

    def prepare_job_directory(self):
        self.job_dir = LOGS_DIR + "/" + LOG_DIR_PREFIX + str(self.job_id)
        try:
            if not os.path.exists(self.job_dir):
                os.makedirs(self.job_dir)
        except Exception as ex:
            raise SchedulerException(str(ex))

    def ensure_scripts_exists(self, script_paths):
        result = True
        error_message = ""
        for script_path in script_paths:
            if not os.path.exists(script_path):
                error_message = "Script {} not found".format(script_path)
                result = False
                break
        return result, error_message

    def get_scripts(self, suite_file):
        items = []
        if suite_file.endswith("container"):
            container_spec = parse_suite(suite_name=suite_file)
            for item in container_spec:
                item_suite = parse_suite(suite_name=item.replace(".json", ""))
                items.extend(item_suite)
        else:
            suite_spec = parse_suite(suite_name=suite_file)
            items = suite_spec
        return items

    def run(self):

        scheduler_logger.debug("Running Job: {}".format(self.job_id))
        models_helper.update_suite_execution(suite_execution_id=self.job_id, result=RESULTS["IN_PROGRESS"])
        if "tags" in self.job_spec and self.job_spec["tags"] and "jenkins-hourly" in self.job_spec["tags"]:
            set_jenkins_hourly_execution_status(status=RESULTS["IN_PROGRESS"])

        suite_execution_id = self.job_id
        job_environment = self.job_environment
        self.prepare_job_directory()
        build_url = self.job_build_url

        # Setup the suites own logger
        local_scheduler_logger = logging.getLogger("scheduler_log_{}.txt".format(self.job_id))
        local_scheduler_logger.setLevel(logging.INFO)
        handler = logging.handlers.RotatingFileHandler(self.job_dir + "/scheduler.log.txt", maxBytes=TEN_MB,
                                                       backupCount=5)
        handler.setFormatter(
            logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        local_scheduler_logger.addHandler(hdlr=handler)
        self.local_scheduler_logger = local_scheduler_logger

        if build_url:
            version = determine_version(build_url=build_url)
            if not version:
                models_helper.update_suite_execution(suite_execution_id=self.job_id, result=RESULTS["ABORTED"])
                error_message = "Unable to determine version from build url: {}".format(build_url)
                scheduler_logger.exception(error_message)
                local_scheduler_logger.exception(error_message)
                self.suite_shutdown = True
            else:
                build_url = build_url.replace("latest", str(version))
                self.job_build_url = build_url
                models_helper.update_suite_execution(suite_execution_id=self.job_id, version=version)

        suite_summary = {}

        script_items = self.get_scripts(suite_file=self.job_spec["suite_name"])
        script_paths = map(lambda f: SCRIPTS_DIR + "/" + f["path"], script_items)
        scripts_exist, error_message = self.ensure_scripts_exists(script_paths)
        if not scripts_exist:
            scheduler_logger.exception(error_message)
            local_scheduler_logger.exception(error_message)
            self.suite_shutdown = True

        self.local_scheduler_logger.debug("Scripts to be executed:")
        map(lambda f: self.local_scheduler_logger.debug("{}: {}".format(f[0], f[1])), enumerate(script_paths))

        self.local_scheduler_logger.info("Starting Job-id: {}".format(self.job_id))

        suite_execution = models_helper.get_suite_execution(suite_execution_id=suite_execution_id)
        if not suite_execution:
            raise SchedulerException("Unable to retrieve suite execution id: {}".format(suite_execution_id))
        suite_execution.scheduled_time = get_current_time()
        suite_execution.suite_path = self.job_spec["suite_name"]
        suite_execution.save()

        self.abort_on_failure_requested = False
        last_script_path = ""
        script_index = 0
        for script_item in script_items:
            script_index += 1
            script_path = SCRIPTS_DIR + "/" + script_item["path"]
            last_script_path = script_path
            if self.abort_on_failure_requested:
                continue
            if self.suite_shutdown:
                scheduler_logger.exception("{}: SUITE shutdown requested".format(self.job_id))
                local_scheduler_logger.exception("SUITE shutdown requested")
                suite_summary[os.path.basename(script_path)] = {"crashed": True, "result": False}
                self.summary_extra_message = "Suite was shutdown"
                continue

            relative_path = script_path.replace(SCRIPTS_DIR, "")
            if self.job_test_case_ids:
                if self.job_script_path not in relative_path:
                    continue
            crashed = False
            console_log_file_name = self.job_dir + "/" + get_flat_console_log_file_name("/{}".format(script_path), script_index)
            with open(console_log_file_name, "w") as console_log:
                self.local_scheduler_logger.info("Executing: {}".format(script_path))
                popens = ["python",
                          script_path,
                          "--" + "logs_dir={}".format(self.job_dir),
                          "--" + "suite_execution_id={}".format(suite_execution_id),
                          "--" + "relative_path={}".format(relative_path),
                          "--" + "build_url={}".format(self.job_build_url),
                          "--" + "log_prefix={}".format(script_index)]

                if self.job_test_case_ids:
                    popens.append("--test_case_ids=" + ','.join(str(v) for v in self.job_test_case_ids))
                if "test_case_ids" in script_item:
                    popens.append("--test_case_ids=" + ','.join(str(v) for v in script_item["test_case_ids"]))
                if self.job_environment:
                    popens.append("--environment={}".format(json.dumps(self.job_environment)))
                self.current_script_process = subprocess.Popen(popens,
                                                               close_fds=True,
                                                               stdout=console_log,
                                                               stderr=console_log)
            poll_status = None
            while poll_status is None:
                # print("Still working...")
                poll_status = self.current_script_process.poll()
            if poll_status:  #
                scheduler_logger.exception("FAILED: Script {}".format(os.path.basename(script_path)))
                self.local_scheduler_logger.info("FAILED: {}".format(script_path))
                local_scheduler_logger.exception("FAILED")
                crashed = True  # TODO: Need to re-check this based on exit code
            script_result = False
            if self.current_script_process.returncode == 0:
                script_result = True
            else:
                if "abort_suite_on_failure" in script_item and script_item["abort_suite_on_failure"]:
                    self.abort_on_failure_requested = True
                    models_helper.update_suite_execution(suite_execution_id=self.job_id, result=RESULTS["ABORTED"])
                    error_message = "Abort Requested on failure for: {}".format(script_path)
                    scheduler_logger.exception(error_message)
                    local_scheduler_logger.exception(error_message)

            self.local_scheduler_logger.info("Executed: {}".format(script_path))
            suite_summary[os.path.basename(script_path)] = {"crashed": crashed, "result": script_result}

        self.local_scheduler_logger.info("Job Id: {} complete".format(self.job_id))
        scheduler_logger.info("Job Id: {} complete".format(self.job_id))
        suite_execution = models_helper.get_suite_execution(suite_execution_id=suite_execution_id)

        if self.abort_on_failure_requested:
            models_helper.update_suite_execution(suite_execution_id=self.job_id, result=RESULTS["ABORTED"])
            error_message = "Abort Requested on failure for: {}".format(last_script_path)
            scheduler_logger.exception(error_message)
            local_scheduler_logger.exception(error_message)
            suite_execution = models_helper.get_suite_execution(suite_execution_id=self.job_id)
            suite_execution.result = RESULTS["ABORTED"]
            suite_execution.finalized = True
            suite_execution.save()

        suite_execution.completed_time = get_current_time()
        suite_execution.save()

        # print job summary
        self.local_scheduler_logger.debug("Suite Summary:")
        scheduler_logger.debug("{:50} {} {}".format("Script", "Result", "Crashed"))
        for script_path, script_metrics in suite_summary.items():
            scheduler_logger.debug("{:50} {} {}".format(script_path,
                                                        str(script_metrics["result"]),
                                                        str(script_metrics["crashed"])))

        handler.close()
        '''
        if "repeat" in self.job_spec and self.job_spec["repeat"]:
            queue_job(job_spec=self.job_spec)

        elif "repeat_in_minutes" in self.job_spec and self.job_spec["repeat_in_minutes"]:
            repeat_in_minutes_value = self.job_spec["repeat_in_minutes"]
            new_job_spec = self.job_spec
            new_job_spec["schedule_in_minutes"] = repeat_in_minutes_value
            queue_job(job_spec=new_job_spec)

        '''
        models_helper.finalize_suite_execution(suite_execution_id=self.job_id)

        to_addresses = []
        if "email_list" in self.job_spec:
            to_addresses = self.job_spec["email_list"]
        email_on_fail_only = False
        if "email_on_fail_only" in self.job_spec:
            email_on_fail_only = self.job_spec["email_on_fail_only"]

        suite_executions = models_helper._get_suite_executions(execution_id=self.job_id, save_test_case_info=True)
        suite_execution = suite_executions[0]
        send_summary_mail(job_id=self.job_id,
                          suite_execution=suite_execution,
                          to_addresses=to_addresses,
                          email_on_fail_only=email_on_fail_only,
                          extra_message=self.summary_extra_message)

        del job_id_threads[self.job_id]
        if self.job_spec["scheduling_type"] == SchedulingType.PERIODIC:
            remove_scheduled_job(self.job_id)
            queue_job2(job_spec=self.job_spec)
        if self.job_spec["scheduling_type"] == SchedulingType.TODAY or self.job_spec["scheduling_type"] == SchedulingType.REPEAT:
            remove_scheduled_job(self.job_id)
            if "repeat_in_minutes" in self.job_spec:
                new_spec = dict(self.job_spec)
                new_spec["scheduling_type"] = SchedulingType.REPEAT
                queue_job2(job_spec=new_spec)


def process_killed_jobs():
    job_files = glob.glob("{}/*{}".format(KILLED_JOBS_DIR, KILLED_JOB_EXTENSION))
    job_files.sort(key=os.path.getmtime)

    for job_file in job_files:
        with open(job_file, "r") as f:
            contents = f.read()
            job_id = int(contents)
            if job_id in job_id_threads:
                t = job_id_threads[job_id]
                scheduler_logger.info("Killing Job: {}".format(job_id))
                try:
                    t.shutdown_suite()
                except Exception as ex:
                    scheduler_logger.error(str(ex))
                finally:
                    try:
                        del job_id_threads[job_id]
                    except:
                        pass

            if job_id in job_id_timers:
                try:
                    if job_id in job_id_timers:
                        t = job_id_timers[job_id]
                        t.cancel()
                except Exception as ex:
                    scheduler_logger.error(str(ex))
                finally:
                    try:
                        del job_id_timers[job_id]
                    except:
                        pass
                suite_execution = models_helper.get_suite_execution(suite_execution_id=job_id)
                suite_execution.completed_time = get_current_time()
                suite_execution.result = RESULTS["KILLED"]
                suite_execution.save()
            revive_scheduled_jobs(job_ids=[job_id])
        os.remove(job_file)


def process_queue():
    time.sleep(1)
    # sort by date
    job_files = glob.glob("{}/*{}".format(JOBS_DIR, QUEUED_JOB_EXTENSION))
    job_files.sort(key=os.path.getmtime)

    for job_file in job_files:
        try:
            # Execute
            job_spec = parse_file_to_json(file_name=job_file)
            job_id = job_spec["job_id"]
            scheduler_logger.info("Process queue: {}".format(job_id))

            schedule_it = True

            scheduling_time = get_scheduling_time(spec=job_spec)
            scheduler_logger.info("Job Id: {} Schedule it: {} Time: {}".format(job_id, schedule_it, scheduling_time))
            if job_spec and schedule_it and (scheduling_time >= 0):
                suite_worker_obj = SuiteWorker(job_spec=job_spec)
                t = threading.Timer(scheduling_time, timed_dispatcher, (suite_worker_obj,))
                job_id_timers[suite_worker_obj.job_id] = t
                models_helper.update_suite_execution(suite_execution_id=suite_worker_obj.job_id,
                                                     scheduled_time=get_current_time() + datetime.timedelta(
                                                         seconds=scheduling_time),
                                                     result=RESULTS["SCHEDULED"])

                if job_spec["scheduling_type"] in [SchedulingType.PERIODIC, SchedulingType.REPEAT, SchedulingType.TODAY]:
                    copy_to_scheduled_job(job_file)
                t.start()
            if scheduling_time < 0:
                scheduler_logger.critical("Unable to schedule. Job-id: {}, Job-file: {}".format(job_id, job_file))
        except Exception as ex:
            scheduler_logger.exception(str(ex))

        de_queue_job(job_file)

def copy_to_scheduled_job(job_file):
    destination_filename = SCHEDULED_JOBS_DIR + "/" + os.path.basename(job_file)
    destination_filename = destination_filename.replace(QUEUED_JOB_EXTENSION, SCHEDULED_JOB_EXTENSION)
    shutil.copy(job_file, destination_filename)


def remove_scheduled_job(job_id):
    job_file = SCHEDULED_JOBS_DIR + "/" + str(job_id) + "." + SCHEDULED_JOB_EXTENSION
    try:
        os.remove(job_file)
    except Exception as ex:
        scheduler_logger.exception(str(ex))


def de_queue_job(job_file):
    # remove job from the jobs directory and move it to the archived directory
    try:
        archived_file = ARCHIVED_JOBS_DIR + "/" + os.path.basename(job_file)
        archived_file = re.sub('(\d+).{}'.format(QUEUED_JOB_EXTENSION),
                               "\\1.{}".format(ARCHIVED_JOB_EXTENSION),
                               archived_file)
        os.rename(job_file, archived_file)
    except Exception as ex:
        scheduler_logger.exception(str(ex))
        # TODO: Ensure job_file is removed


def process_external_requests():
    request_file = SCHEDULER_REQUESTS_DIR + "/request.json"
    request = parse_file_to_json(file_name=request_file)
    if request and "request" in request:
        if request["request"] == "stop":
            set_scheduler_state(SchedulerStates.SCHEDULER_STATE_STOPPING)
    return request

def ensure_singleton():
    if os.path.exists(SCHEDULER_PID):
        raise SchedulerException("Only one instance of scheduler.py is permitted")
    else:
        with open(SCHEDULER_PID, "w") as f:
            pid = os.getpid()
            f.write(str(pid))


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


def remove_pid():
    if os.path.exists(SCHEDULER_PID):
        os.remove(SCHEDULER_PID)


def graceful_shutdown(max_wait_time=ONE_HOUR):
    run_to_completion(max_wait_time=max_wait_time)
    remove_pid()
    set_scheduler_state(SchedulerStates.SCHEDULER_STATE_STOPPED)


def revive_scheduled_jobs(job_ids=None):
    job_files = glob.glob("{}/*{}".format(SCHEDULED_JOBS_DIR, SCHEDULED_JOB_EXTENSION))

    for job_file in job_files:
        job_spec = parse_file_to_json(file_name=job_file)
        if job_ids:
            job_id = job_spec["job_id"]
            if job_id not in job_ids:
                continue
        scheduler_logger.info("Reviving Job file: {}".format(job_file))
        '''
        dst_filename = os.path.basename(job_file)
        dst_filename = dst_filename.replace(SCHEDULED_JOB_EXTENSION, QUEUED_JOB_EXTENSION)
        dst_filename = "{}/{}".format(JOBS_DIR, dst_filename)
        shutil.copy(job_file, dst_filename)
        '''
        queue_job2(job_spec=job_spec)
        os.remove(job_file)


if __name__ == "__main__":
    ensure_singleton()
    scheduler_logger.debug("Started Scheduler")
    set_scheduler_state(SchedulerStates.SCHEDULER_STATE_RUNNING)

    revive_scheduled_jobs()
    while True:
        scheduler_info = get_scheduler_info()
        if scheduler_info.state == SchedulerStates.SCHEDULER_STATE_STOPPED:
            scheduler_logger.info("Scheduler Bye bye!")
            break
        process_killed_jobs()
        try:
            scheduler_info = get_scheduler_info()
            request = process_external_requests()
            if (scheduler_info.state != SchedulerStates.SCHEDULER_STATE_STOPPING) or \
                    (scheduler_info.state != SchedulerStates.SCHEDULER_STATE_STOPPED):
                process_queue()
            if scheduler_info.state == SchedulerStates.SCHEDULER_STATE_STOPPING:
                max_wait_time = ONE_HOUR
                if request and "max_wait_time" in request:
                    max_wait_time = int(request["max_wait_time"])
                graceful_shutdown(max_wait_time=max_wait_time)

        except SchedulerException as ex:
            scheduler_logger.exception(str(ex))
        except Exception as ex:
            scheduler_logger.exception(str(ex))
        # wait
