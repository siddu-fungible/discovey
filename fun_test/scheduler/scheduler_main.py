#!/usr/bin/env python
from fun_settings import *
from fun_global import get_current_time, RESULTS, determine_version
import re
import subprocess
from threading import Thread, Timer, RLock
import threading

from scheduler.scheduler_global import JobStatusType
from scheduler_helper import *
import signal
import psutil
import shutil
from django.db import transaction
from asset.asset_manager import AssetManager

job_id_threads = {}
job_id_timers = {}

ONE_HOUR = 60 * 60

queue_lock = None

class QueueWorker(Thread):
    def __init__(self):
        super(QueueWorker, self).__init__()
        self.job_threads = {}

    def run(self):
        from asset.asset_manager import AssetManager
        asset_manager = AssetManager()
        while True:
            de_queued_jobs = []
            queued_jobs = JobQueue.objects.all().order_by('priority')
            for queued_job in queued_jobs:
                print ("Testbed-type: {}".format(queued_job.test_bed_type))
                availability = asset_manager.get_test_bed_availability(test_bed_type=queued_job.test_bed_type)
                if availability["status"]:
                    de_queued_jobs.append(queued_job)
                    self.de_queue_job(queued_job)
                else:
                    print("Not available: {}".format(availability["message"]))
                    queued_job.message = availability["message"]
                    queued_job.save()
            print("Queue Worker")
            time.sleep(5)

            for de_queued_job in de_queued_jobs:
                d = JobQueue.objects.get(job_id=de_queued_job.job_id)
                d.delete()

    def de_queue_job(self, job):
        print("De-queueing Job: {}".format(job.job_id))
        suite_execution = models_helper.get_suite_execution(suite_execution_id=job.job_id)
        t = SuiteWorker(job_spec=suite_execution)
        self.job_threads[job.job_id] = t
        t.start()

    def thread_complete(self, job_id):
        del self.job_threads[job_id]
        # self.repeat_job(job_id=job_id)

    def repeat_job(self, job_id):
        suite_execution = models_helper.get_suite_execution(suite_execution_id=job_id)
        cloned_job = None

        if suite_execution.scheduling_type == SchedulingType.PERIODIC:
            cloned_job = self.clone_job_spec(job_id=job_id)
            cloned_job.state = JobStatusType.SUBMITTED
        if suite_execution.scheduling_type in [SchedulingType.TODAY, SchedulingType.REPEAT]:
            cloned_job = self.clone_job_spec(job_id=job_id)
            if suite_execution.repeat_in_minutes >= 0:
                cloned_job.state = JobStatusType.SUBMITTED
                cloned_job.scheduling_type = SchedulingType.REPEAT

        if cloned_job:
            scheduler_logger.info("Repeating job: {}".format(suite_execution.execution_id))
            cloned_job.save()

    def clone_job_spec(self, job_id):
        suite_execution = models_helper.get_suite_execution(suite_execution_id=job_id)
        new_suite_execution_id = models_helper.get_new_suite_execution_id()
        suite_execution.execution_id = new_suite_execution_id
        suite_execution.pk = None
        return suite_execution

queue_worker = QueueWorker()



def queue_job(job_spec):
    queue_lock.acquire()
    next_priority_value = get_next_priority_value(job_spec.requested_priority_category)
    new_job = JobQueue(priority=next_priority_value, job_id=job_spec.execution_id, test_bed_type=job_spec.test_bed_type)
    new_job.save()
    job_spec.set_state(JobStatusType.QUEUED)
    queue_lock.release()


def timer_dispatch(job_spec):
    # Add to queue
    queue_job(job_spec=job_spec)
    if job_spec.execution_id in job_id_timers:
        del job_id_timers[job_spec.execution_id]


class SuiteWorker(Thread):
    def __init__(self, job_spec):
        super(SuiteWorker, self).__init__()
        self.job_spec = job_spec
        self.job_suite_path = job_spec.suite_path
        self.job_suite_path = re.sub(r'.json', '', self.job_suite_path)
        self.job_suite_path += ".json"

        self.job_suite_type = job_spec.suite_type
        self.job_id = job_spec.execution_id
        self.job_dir = None
        self.job_test_case_ids = None
        self.job_environment = {}
        self.job_build_url = "http://dochub.fungible.local/doc/jenkins/funsdk/latest/"
        self.job_test_bed_type = None
        self.job_scheduling_type = job_spec.scheduling_type

        self.job_script_path = None
        if hasattr(job_spec, 'script_path'):
            self.job_script_path = job_spec.script_path

        self.job_test_case_ids = None
        if hasattr(job_spec, "test_case_ids"):
            self.job_test_case_ids = job_spec.test_case_ids

        self.job_build_url = None
        if hasattr(job_spec, "build_url"):
            self.job_build_url = job_spec.build_url

        if job_spec.scheduling_type in [SchedulingType.TODAY,  SchedulingType.REPEAT]:
            self.job_build_url = None

        self.job_environment = None
        if hasattr(job_spec, "environment"):
            self.job_environment = json.loads(job_spec.environment)

        self.job_inputs = {}
        if hasattr(job_spec, "inputs"):
            self.job_inputs = job_spec.inputs

        self.job_dynamic_suite_spec = None
        if hasattr(job_spec, "dynamic_suite_spec"):
            self.job_dynamic_suite_spec = job_spec.dynamic_suite_spec

        self.job_emails = None
        if hasattr(job_spec, "emails"):
            self.job_emails = job_spec.emails

        self.job_email_on_failure_only = None
        if hasattr(job_spec, "email_on_failure_only"):
            self.job_email_on_failure_only = job_spec.email_on_failure_only

        self.job_test_bed_type = job_spec.test_bed_type
        self.current_script_process = None

        self.suite_shutdown = False
        self.abort_on_failure_requested = False
        self.summary_extra_message = ""


    def shutdown_suite(self):
        job_id = self.job_id
        scheduler_logger.info("Job Id: {} Shutdown_suite".format(job_id))
        self.suite_shutdown = True
        if self.current_script_process:
            try:
                os.kill(self.current_script_process.pid, signal.SIGINT)
                self.current_script_process.terminate()
                time.sleep(5)
            except Exception as ex:
                scheduler_logger.error(str(ex))
            if psutil.pid_exists(self.current_script_process.pid):
                try:
                    for i in xrange(100):
                        time.sleep(0.5)
                        self.current_script_process.kill()
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

    def apply_tags_to_items(self, items, tags):
        for item in items:
            if "info" in item:
                continue
            else:
                item["tags"] = tags

    def get_scripts(self, suite_execution_id, suite_file=None, dynamic_suite_file=None):
        all_tags = []
        items = []
        if suite_file:
            if suite_file.endswith("container"):
                container_spec = parse_suite(suite_name=suite_file)
                suite_level_tags = get_suite_level_tags(suite_spec=container_spec)
                all_tags.extend(suite_level_tags)
                for item in container_spec:
                    item_suite = parse_suite(suite_name=item)
                    item_suite_level_tags = get_suite_level_tags(suite_spec=item_suite)
                    all_tags.extend(item_suite_level_tags)
                    items.extend(item_suite)
            else:
                suite_spec = parse_suite(suite_name=suite_file)
                suite_level_tags = get_suite_level_tags(suite_spec=suite_spec)
                all_tags.extend(suite_level_tags)
                items = suite_spec
        else:
            suite_spec = parse_suite(dynamic_suite_file=dynamic_suite_file)
            suite_level_tags = get_suite_level_tags(suite_spec=suite_spec)
            all_tags.extend(suite_level_tags)
            items = suite_spec

        all_tags = list(set(all_tags))
        self.apply_tags_to_items(items=items, tags=all_tags)
        # use job submission tags as well
        suite_execution = models_helper.get_suite_execution(suite_execution_id=suite_execution_id)
        if suite_execution:
            suite_execution_tags = json.loads(suite_execution.tags)
            all_tags.extend(suite_execution_tags)

        return items, all_tags

    def run(self):
        # Setup the suites own logger
        # TODO: Failure here should be reported to global logger
        self.prepare_job_directory()
        local_scheduler_logger = logging.getLogger("scheduler_log_{}.txt".format(self.job_id))
        local_scheduler_logger.setLevel(logging.INFO)
        handler = logging.handlers.RotatingFileHandler(self.job_dir + "/scheduler.log.txt", maxBytes=TEN_MB,
                                                       backupCount=5)
        handler.setFormatter(
            logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        local_scheduler_logger.addHandler(hdlr=handler)
        self.local_scheduler_logger = local_scheduler_logger


        try:
            scheduler_logger.debug("Running Job: {}".format(self.job_id))
            # print "Updating to IN_PROGRESS"
            models_helper.update_suite_execution(suite_execution_id=self.job_id, result=RESULTS["IN_PROGRESS"], state=JobStatusType.IN_PROGRESS)

            suite_execution_id = self.job_id
            suite_execution = models_helper.get_suite_execution(suite_execution_id=suite_execution_id)
            if not suite_execution:
                raise SchedulerException("Unable to retrieve suite execution id: {}".format(suite_execution_id))



            build_url = self.job_build_url
            if not build_url:
                build_url = DEFAULT_BUILD_URL
            if build_url:
                version = determine_version(build_url=build_url)

                if not version:
                    models_helper.update_suite_execution(suite_execution_id=self.job_id,
                                                         result=RESULTS["ABORTED"],
                                                         state=JobStatusType.ABORTED)
                    error_message = "Unable to determine version from build url: {}".format(build_url)
                    scheduler_logger.exception(error_message)
                    local_scheduler_logger.exception(error_message)
                    self.suite_shutdown = True
                else:
                    if suite_execution and suite_execution.suite_container_execution_id > 0:
                        container_execution = models_helper.get_suite_container_execution(suite_execution.suite_container_execution_id)
                        if int(container_execution.version) <= 0:
                            models_helper.update_suite_container_execution(suite_container_execution_id=container_execution.execution_id, version=version)
                            container_execution = models_helper.get_suite_container_execution(
                                suite_execution.suite_container_execution_id)
                        version = int(container_execution.version)
                    build_url = build_url.replace("latest", str(version))
                    self.job_build_url = build_url
                    # print "Job: {} Updating to Version1".format(self.job_id)
                    models_helper.update_suite_execution(suite_execution_id=self.job_id, version=version)
                    # print "Job: {} Updating to Version2".format(self.job_id)

            suite_summary = {}
            script_items = []
            if self.job_suite_path and self.job_suite_type == SuiteType.STATIC:
                script_items, all_tags = self.get_scripts(suite_execution_id=suite_execution_id, suite_file=self.job_suite_path)
                models_helper.update_suite_execution(suite_execution_id=suite_execution_id, tags=all_tags)
            elif self.job_script_path:
                script_items.append({"path": self.job_script_path})
            elif self.job_suite_type == SuiteType.DYNAMIC:
                script_items, all_tags = self.get_scripts(suite_execution_id=suite_execution_id, dynamic_suite_file=self.job_dynamic_suite_spec)
                models_helper.update_suite_execution(suite_execution_id=suite_execution_id, tags=all_tags)

            script_paths = map(lambda f: SCRIPTS_DIR + "/" + f["path"], filter(lambda f: "info" not in f, script_items))
            scripts_exist, error_message = self.ensure_scripts_exists(script_paths)
            if not scripts_exist:
                scheduler_logger.exception(error_message)
                local_scheduler_logger.exception(error_message)
                self.suite_shutdown = True
            self.local_scheduler_logger.debug("Scripts to be executed:")
            map(lambda f: self.local_scheduler_logger.debug("{}: {}".format(f[0], f[1])), enumerate(script_paths))
            self.local_scheduler_logger.info("Starting Job-id: {}".format(self.job_id))
            suite_execution = models_helper.get_suite_execution(suite_execution_id=suite_execution_id)
            suite_execution.scheduled_time = get_current_time()
            if self.job_suite_path:
                suite_execution.suite_path = self.job_suite_path
            else:
                suite_execution.suite_path = self.job_script_path
            suite_execution.save()

            self.abort_on_failure_requested = False
            last_script_path = ""
            script_index = 0
            #TODO: What if there are no scripts
            for script_item in script_items:
                script_index += 1
                if "info" in script_item or ("disabled" in script_item and script_item["disabled"]):
                    continue
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
                scheduler_logger.debug("Job Id: {} before running script: {}".format(self.job_id, script_path))

                console_log_file_name = self.job_dir + "/" + get_flat_console_log_file_name("/{}".format(script_path), script_index)
                try:
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
                        if "re_run_info" in script_item:
                            popens.append("--re_run_info={}".format(json.dumps(script_item["re_run_info"])))
                        if self.job_environment:
                            popens.append("--environment={}".format(json.dumps(self.job_environment)))  #TODO: validate

                        script_inputs = {}
                        if "inputs" in script_item:
                            script_inputs = script_item["inputs"]
                        job_inputs = self.job_inputs
                        if not script_inputs and job_inputs:
                            script_inputs = {}
                            script_inputs.update(job_inputs)
                        if script_inputs:
                            popens.append("--inputs={}".format(json.dumps(script_inputs))) #TODO: validate

                        scheduler_logger.debug("Job Id: {} before subprocess Script: {}".format(self.job_id, script_path))
                        self.current_script_process = subprocess.Popen(popens,
                                                                       close_fds=True,
                                                                       stdout=console_log,
                                                                       stderr=console_log)
                        self.current_script_process.wait()
                        scheduler_logger.debug("Job Id: {} after subprocess Script: {}".format(self.job_id, script_path))
                except Exception as ex:
                    scheduler_logger.error(str(ex))
                    local_scheduler_logger.error(str(ex))
                scheduler_logger.debug("Job Id: {} begin polling Script: {}".format(self.job_id, script_path))
                poll_status = None
                while poll_status is None:
                    # print("Still working...")
                    poll_status = self.current_script_process.poll()
                if poll_status:  #
                    scheduler_logger.exception("FAILED: Script {}".format(os.path.basename(script_path)))
                    self.local_scheduler_logger.info("FAILED: {}".format(script_path))
                    local_scheduler_logger.exception("FAILED")
                    crashed = True  # TODO: Need to re-check this based on exit code
                scheduler_logger.debug("Job Id: {} Done polling Script: {}".format(self.job_id, script_path))

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
                suite_execution.state = JobStatusType.ABORTED
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
            models_helper.update_suite_execution(suite_execution_id=self.job_id, state=JobStatusType.COMPLETED)
            models_helper.finalize_suite_execution(suite_execution_id=self.job_id)

            to_addresses = self.job_emails
            email_on_fail_only = self.job_email_on_failure_only

            suite_executions = models_helper._get_suite_executions(execution_id=self.job_id, save_test_case_info=True)
            suite_execution = suite_executions[0]
            send_summary_mail(job_id=self.job_id,
                              suite_execution=suite_execution,
                              to_addresses=to_addresses,
                              email_on_fail_only=email_on_fail_only,
                              extra_message=self.summary_extra_message)

            queue_worker.thread_complete(job_id=self.job_id)



        except Exception as ex:
            scheduler_logger.exception(str(ex))
            local_scheduler_logger.exception(str(ex))
            models_helper.update_suite_execution(suite_execution_id=self.job_id, result=RESULTS["ABORTED"], state=JobStatusType.ABORTED)

def process_killed_jobs():
    job_files = glob.glob("{}/*{}".format(KILLED_JOBS_DIR, KILLED_JOB_EXTENSION))
    job_files.sort(key=os.path.getmtime)

    for job_file in job_files:
        suite_execution_status = None
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
            if suite_execution:
                suite_execution_status = suite_execution.result
                suite_execution.completed_time = get_current_time()
                suite_execution.result = RESULTS["KILLED"]
                suite_execution.save()
            if suite_execution_status and suite_execution_status not in [RESULTS["ABORTED"], RESULTS["SCHEDULED"], RESULTS["KILLED"]]:
                revive_scheduled_jobs(job_ids=[job_id])
            remove_scheduled_job(job_id=job_id)
        os.remove(job_file)


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

    job_specs = models_helper.get_suite_executions_by_filter(submitted_time__gte=yesterday,
                                       state=JobStatusType.SUBMITTED).order_by("-submitted_time")
    for job_spec in job_specs:
        try:
            # Execute
            job_id = job_spec.execution_id
            scheduler_logger.info("Process queue: {}".format(job_id))

            schedule_it = True
            scheduling_time = get_scheduling_time(spec=job_spec)
            scheduler_logger.info("Job Id: {} Schedule it: {} Time: {}".format(job_id, schedule_it, scheduling_time))
            if job_spec and schedule_it and (scheduling_time >= 0):
                t = threading.Timer(scheduling_time, timer_dispatch, (job_spec,))
                job_id_timers[job_id] = t
                models_helper.update_suite_execution(suite_execution_id=job_id,
                                                     scheduled_time=get_current_time() + datetime.timedelta(
                                                         seconds=scheduling_time))

                if job_spec.scheduling_type in SchedulingType.get_deferred_types():
                    copy_to_scheduled_job(job_spec)

                job_spec.set_state(JobStatusType.SCHEDULED)
                t.start()
            if scheduling_time < 0:
                scheduler_logger.critical("Unable to process job submission. Job-id: {}".format(job_spec.job_id))
        except Exception as ex:
            scheduler_logger.exception(str(ex))



def copy_to_scheduled_job(job_spec):
    job_spec.is_scheduled_job = True
    job_spec.save()


def remove_scheduled_job(job_id):
    job_spec = JobSpec.objects.get(job_id=job_id)
    job_spec.is_scheduled_job = False
    job_spec.save()
    # TODO handle exception


def set_processed_job(job_spec):
    job_spec.state = RESULTS["PROCESSED"]
    job_spec.save()


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
    print "Trying graceful shutdown"
    run_to_completion(max_wait_time=max_wait_time)
    remove_pid()
    set_scheduler_state(SchedulerStates.SCHEDULER_STATE_STOPPED)
    print "Exiting graceful shutdown"


def revive_scheduled_jobs(job_ids=None):
    job_files = glob.glob("{}/*{}".format(SCHEDULED_JOBS_DIR, SCHEDULED_JOB_EXTENSION))

    for job_file in job_files:
        job_spec = parse_file_to_json(file_name=job_file)
        job_spec["suite_type"] = SuiteType.STATIC
        if job_ids:
            job_id = job_spec["job_id"]
            if job_id not in job_ids:
                continue
        kill_job(job_id=job_spec["job_id"])
        scheduler_logger.info("Reviving Job file: {}".format(job_file))
        queue_job2(job_spec=job_spec)
        os.remove(job_file)




if __name__ == "__main__":
    queue_lock = RLock()
    # ensure_singleton()
    scheduler_logger.debug("Started Scheduler")
    set_scheduler_state(SchedulerStates.SCHEDULER_STATE_RUNNING)


    queue_worker.start()

    revive_scheduled_jobs()
    run = True
    while run:
        time.sleep(1)
        set_main_loop_heartbeat()
        scheduler_info = get_scheduler_info()
        if scheduler_info.state == SchedulerStates.SCHEDULER_STATE_STOPPED:
            scheduler_logger.info("Scheduler Bye bye!")
            run = False
            os.kill(os.getpid(), 9)
            break

        process_killed_jobs()
        try:
            scheduler_info = get_scheduler_info()
            request = process_external_requests()
            if (scheduler_info.state != SchedulerStates.SCHEDULER_STATE_STOPPING) and \
                    (scheduler_info.state != SchedulerStates.SCHEDULER_STATE_STOPPED):
                process_submissions()
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
    queue_worker.join()
