#!/usr/bin/env python
from fun_settings import *
from fun_global import get_current_time, RESULTS, determine_version
import os
import re
import subprocess
from threading import Thread
import threading
from scheduler_helper import *
import dateutil.parser, signal, psutil

job_id_threads = {}
job_id_timers = {}


def timed_dispatcher(suite_worker_obj):
    job_id_threads[suite_worker_obj.job_id] = (suite_worker_obj)
    suite_worker_obj.start()
    if suite_worker_obj.job_id in job_id_timers:
        del job_id_timers[suite_worker_obj.job_id]


def get_scripts_in_suite(suite_name):
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
        self.job_build_url = "http://dochub.fungible.local/doc/jenkins/funos/940"
        if 'script_path' in job_spec:
            self.job_script_path = job_spec["script_path"]
        if "test_case_ids" in job_spec:
            self.job_test_case_ids = job_spec["test_case_ids"]
        if "build_url" in job_spec:
            self.job_build_url = job_spec["build_url"]
        self.current_script_process = None

        self.suite_shutdown = False
        self.abort_on_failure_requested = False

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

    def run(self):
        scheduler_logger.debug("Running Job: {}".format(self.job_id))
        models_helper.update_suite_execution(suite_execution_id=self.job_id, result=RESULTS["IN_PROGRESS"])
        if "tags" in self.job_spec and self.job_spec["tags"] and "jenkins-hourly" in self.job_spec["tags"]:
            set_jenkins_hourly_execution_status(status=RESULTS["IN_PROGRESS"])

        suite_execution_id = self.job_id
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
                models_helper.update_suite_execution(suite_execution_id=self.job_id, version=version)

        suite_summary = {}

        suite_spec = get_scripts_in_suite(suite_name=self.job_spec["suite_name"])
        script_paths = map(lambda f: SCRIPTS_DIR + "/" + f["path"], suite_spec)

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
        for script_item in suite_spec:
            script_path = SCRIPTS_DIR + "/" + script_item["path"]
            last_script_path = script_path
            if self.abort_on_failure_requested:
                continue
            if self.suite_shutdown:
                scheduler_logger.exception("{}: SUITE shutdown requested".format(self.job_id))
                local_scheduler_logger.exception("SUITE shutdown requested")
                suite_summary[os.path.basename(script_path)] = {"crashed": True, "result": False}
                continue

            relative_path = script_path.replace(SCRIPTS_DIR, "")
            if self.job_test_case_ids:
                if self.job_script_path not in relative_path:
                    continue
            crashed = False
            console_log_file_name = self.job_dir + "/" + get_flat_console_log_file_name("/{}".format(script_path))
            with open(console_log_file_name, "w") as console_log:
                self.local_scheduler_logger.info("Executing: {}".format(script_path))
                popens = ["python",
                          script_path,
                          "--" + "logs_dir={}".format(self.job_dir),
                          "--" + "suite_execution_id={}".format(suite_execution_id),
                          "--" + "relative_path={}".format(relative_path),
                          "--" + "build_url={}".format(self.job_build_url)]

                if self.job_test_case_ids:
                    popens.append("--test_case_ids=" + ','.join(str(v) for v in self.job_test_case_ids))
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
        if not self.suite_shutdown:
            if "repeat" in self.job_spec and self.job_spec["repeat"]:
                queue_job(job_spec=self.job_spec)
            elif "repeat_in_minutes" in self.job_spec and self.job_spec["repeat_in_minutes"]:
                repeat_in_minutes_value = self.job_spec["repeat_in_minutes"]
                new_job_spec = self.job_spec
                new_job_spec["schedule_in_minutes"] = repeat_in_minutes_value
                queue_job(job_spec=new_job_spec)

            del job_id_threads[self.job_id]
            models_helper.finalize_suite_execution(suite_execution_id=self.job_id)
        else:
            pass  # TODO: Send error report
        to_addresses = []
        if "email_list" in self.job_spec:
            to_addresses = self.job_spec["email_list"]
        email_on_fail_only = False
        if "email_on_fail_only" in self.job_spec:
            email_on_fail_only = self.job_spec["email_on_fail_only"]

        suite_executions = models_helper._get_suite_executions(execution_id=self.job_id, save_test_case_info=True)
        suite_execution = suite_executions[0]
        send_summary_mail(job_id=self.job_id, suite_execution=suite_execution, to_addresses=to_addresses, email_on_fail_only=email_on_fail_only)


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
            current_time = get_current_time()

            schedule_it = True
            scheduling_time = 1
            if "schedule_in_minutes" in job_spec and job_spec["schedule_in_minutes"]:
                scheduling_time = 60 * job_spec["schedule_in_minutes"]
            elif "schedule_at" in job_spec and job_spec["schedule_at"]:
                schedule_at_time_offset = dateutil.parser.parse(job_spec["schedule_at"]).replace(year=1, month=1, day=1)
                current_time_offset = current_time.replace(year=1, month=1, day=1)

                total_seconds = (schedule_at_time_offset - current_time_offset).total_seconds()
                if total_seconds < 0:
                    scheduling_time = (24 * 60 * 3600) + total_seconds
                elif total_seconds >= 0:
                    scheduling_time = total_seconds
                else:
                    schedule_it = False  # TODO: Email, report a scheduling failure

            scheduler_logger.info("Job Id: {} Schedule it: {} Time: {}".format(job_id, schedule_it, scheduling_time))
            if job_spec and schedule_it:
                suite_worker_obj = SuiteWorker(job_spec=job_spec)
                t = threading.Timer(scheduling_time, timed_dispatcher, (suite_worker_obj,))
                job_id_timers[suite_worker_obj.job_id] = t
                models_helper.update_suite_execution(suite_execution_id=suite_worker_obj.job_id,
                                                     scheduled_time=get_current_time() + datetime.timedelta(
                                                         seconds=scheduling_time),
                                                     result=RESULTS["SCHEDULED"])

                t.start()
        except Exception as ex:
            scheduler_logger.exception(str(ex))


        de_queue_job(job_file)


def de_queue_job(job_file):
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
    pass

def ensure_singleton():
    if os.path.exists(SCHEDULER_PID):
        raise SchedulerException("Only one instance of scheduler.py is permitted")
    else:
        with open(SCHEDULER_PID, "w") as f:
            pid = os.getpid()
            f.write(str(pid))


if __name__ == "__main1__":
    queue_job(suite_name="storage_basic")
    # queue_job(job_id=2, suite="suite2")
    # queue_job(job_id=4, suite="suite3")
    # queue_job(job_id=3, suite="suite4")
    # queue_job(job_id=5, suite="suite5")
    while True:
        process_queue()
    # process killed jobs
    # wait
    pass

if __name__ == "__main__":
    # ensure_singleton()
    scheduler_logger.debug("Started Scheduler")
    while True:
        process_killed_jobs()
        try:
            process_queue()
        except SchedulerException as ex:
            scheduler_logger.exception(str(ex))
        except Exception as ex:
            scheduler_logger.exception(str(ex))
        # wait
