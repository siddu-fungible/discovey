#!/usr/bin/env python
from fun_settings import *
from fun_global import determine_version
import re
import subprocess
from threading import Thread, Lock
import threading

from scheduler_helper import *
import signal
import psutil
import shutil

job_id_threads = {}
job_id_timers = {}

ONE_HOUR = 60 * 60

queue_lock = None


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


class TestBedWorker(Thread):
    def __init__(self):
        super(TestBedWorker, self).__init__()
        self.shutdown_requested = False
        self.warn_list = []

    def shutdown(self):
        self.shutdown_requested = True

    def test_bed_unlock_dispatch(self, test_bed_name):
        try:
            test_bed = get_test_bed_by_name(test_bed_name)

            if test_bed.manual_lock:
                if get_current_time() > test_bed.manual_lock_expiry_time:
                    test_bed.manual_lock = False
                    test_bed.save()
                    send_test_bed_remove_lock(test_bed=test_bed, warning=False)
                    self.warn_list.remove(test_bed.name)

        except Exception as ex:
            scheduler_logger.exception(str(ex))

    def run(self):
        while not self.shutdown_requested:
            test_beds = get_manual_lock_test_beds()
            for test_bed in test_beds:
                expiry_time = test_bed.manual_lock_expiry_time
                if test_bed.name not in self.warn_list:
                    if get_current_time() > expiry_time:
                        scheduler_logger.info("Test-bed {} manual lock expired".format(test_bed.name))
                        t = threading.Timer(60 * 60, self.test_bed_unlock_dispatch, (self, test_bed.name,))
                        self.warn_list.append(test_bed.name)
                        send_test_bed_remove_lock(test_bed=test_bed, warning=True)

            time.sleep(20)

        scheduler_logger.info("TestBedWorker shutdown")


class QueueWorker(Thread):
    def __init__(self):
        super(QueueWorker, self).__init__()
        self.job_threads = {}

    def submit_container_suite(self, container_suite_execution_id):
        # print ("Submit container suite")
        # return
        container_suite_execution = models_helper.get_suite_execution(suite_execution_id=container_suite_execution_id)
        container_suite_path = container_suite_execution.suite_path
        state = JobStatusType.IN_PROGRESS
        container_suite_execution.state = state
        container_suite_execution.save()
        container_suite_execution.save()
        try:
            container_spec = parse_suite(suite_name=container_suite_path)
            container_suite_level_tags = json.loads(container_suite_execution.tags)
        except Exception as ex:
            scheduler_logger.exception(
                "{} Unable to parse spec".format(get_job_string_from_spec(job_spec=container_suite_execution)))
            return

        try:
            common_build_url = container_suite_execution.build_url
            if not common_build_url:
                common_build_url = DEFAULT_BUILD_URL
            version = determine_version(build_url=common_build_url)
            if version:
                container_suite_execution.version = version
                container_suite_execution.save()
            for item in container_spec:
                item_suite = parse_suite(suite_name=item)
                item_suite_level_tags = get_suite_level_tags(suite_spec=item_suite)
                item_suite_level_tags.extend(container_suite_level_tags)

                if not version:
                    scheduler_logger.exception("{} Unable to determine version".format(
                        get_job_string_from_spec(job_spec=container_suite_execution)))
                else:
                    # print ("the item: {}".format(item))
                    result = queue_job3(suite_path=item,
                                        build_url=common_build_url,
                                        scheduling_type=SchedulingType.ASAP,
                                        tags=item_suite_level_tags,
                                        emails=json.loads(container_suite_execution.emails),
                                        email_on_fail_only=container_suite_execution.email_on_failure_only,
                                        suite_container_execution_id=container_suite_execution.execution_id,
                                        test_bed_type=container_suite_execution.test_bed_type,
                                        requested_priority_category=SchedulerJobPriority.NORMAL,
                                        submitter_email=container_suite_execution.submitter_email)
                    # container_suite_execution.set_state(state)
                    if result <= 0:
                        scheduler_logger.exception("Suite container: {}")
                        state = JobStatusType.ABORTED
                        scheduler_logger.exception("{} Unable to process suite container".format(
                            get_job_string_from_spec(job_spec=container_suite_execution)))
                        break
                    # container_suite_execution.set_state(state)
        except Exception as ex:
            scheduler_logger.exception(str(ex))
            state = JobStatusType.ABORTED

        container_suite_execution.state = state
        container_suite_execution.save()

    def run(self):
        from asset.asset_manager import AssetManager
        asset_manager = AssetManager()
        # while True:
        if True:

            queue_lock.acquire()
            scheduler_logger.info("Lock-acquire: QueueWorker")

            try:
                de_queued_jobs = []
                valid_jobs = self.get_valid_jobs()
                not_available = {}

                for queued_job in valid_jobs:

                    """
                    schedule a container if needed
                    """
                    suite_execution = models_helper.get_suite_execution(suite_execution_id=queued_job.job_id)
                    if suite_execution.suite_type == SuiteType.CONTAINER:
                        self.submit_container_suite(container_suite_execution_id=suite_execution.execution_id)
                        de_queued_jobs.append(queued_job)
                        continue

                    if queued_job.test_bed_type not in not_available:
                        availability = asset_manager.get_test_bed_availability(test_bed_type=queued_job.test_bed_type)
                        if availability["status"]:
                            de_queued_jobs.append(queued_job)
                            # self.job_threads[suite_execution.execution_id] = self.execute_job(queued_job.job_id)
                            job_id_threads[suite_execution.execution_id] = self.execute_job(queued_job.job_id)

                        else:
                            not_available[queued_job.test_bed_type] = availability["message"]
                            print("Not available: {}".format(availability["message"]))
                            queued_job.message = availability["message"]
                            queued_job.save()
                    else:
                        queued_job.message = not_available[queued_job.test_bed_type]
                        queued_job.save()

                time.sleep(5)

                for de_queued_job in de_queued_jobs:
                    scheduler_logger.info("Job: {} Dequeuing".format(de_queued_job.job_id))
                    d = JobQueue.objects.get(job_id=de_queued_job.job_id)
                    d.delete()
            except Exception as ex:
                scheduler_logger.exception(str(ex))
            # scheduler_logger.info("QueueWorker: Before lock release")
            scheduler_logger.info("Lock-release: QueueWorker")
            queue_lock.release()
            time.sleep(5)

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

    def execute_job(self, job_id):
        suite_execution = models_helper.get_suite_execution(suite_execution_id=job_id)
        scheduler_logger.info("{} Executing".format(get_job_string_from_spec(job_spec=suite_execution)))
        t = SuiteWorker(job_spec=suite_execution)
        suite_execution.state = JobStatusType.IN_PROGRESS
        suite_execution.save()
        suite_execution.save()
        t.initialize()
        # t.start()
        # t.run()
        return t

        # t.join()


queue_worker = QueueWorker()
test_bed_monitor = TestBedWorker()


def get_job_string_from_spec(job_spec):
    return "{} st={}".format(get_job_string(job_spec.execution_id), job_spec.state)


def get_job_string(job_id):
    return "Job: {}".format(job_id)


def queue_job(job_id):
    queue_lock.acquire()
    scheduler_logger.info("Lock-acquire: queue_job")
    job_spec = models_helper.get_suite_execution(suite_execution_id=job_id)
    if job_spec.state == JobStatusType.SCHEDULED:
        next_priority_value = get_next_priority_value(job_spec.requested_priority_category)
        new_job = JobQueue(priority=next_priority_value, job_id=job_spec.execution_id,
                           test_bed_type=job_spec.test_bed_type)
        new_job.save()
        new_job.save()
        models_helper.update_suite_execution(suite_execution_id=job_spec.execution_id, state=JobStatusType.QUEUED)
        time.sleep(1)
        models_helper.update_suite_execution(suite_execution_id=job_spec.execution_id, state=JobStatusType.QUEUED)

    else:
        scheduler_logger.error("{} trying to be queued".format(get_job_string_from_spec(job_spec)))

    scheduler_logger.info("Lock-release: queue_job")
    queue_lock.release()


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
    def __init__(self, job_spec):
        super(SuiteWorker, self).__init__()
        self.job_spec = job_spec
        self.job_suite_path = None
        if job_spec.suite_path:
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

        self.job_tags = json.loads(job_spec.tags)

        self.job_script_path = None
        if hasattr(job_spec, 'script_path'):
            self.job_script_path = job_spec.script_path

        self.job_test_case_ids = None
        if hasattr(job_spec, "test_case_ids"):
            self.job_test_case_ids = job_spec.test_case_ids

        self.job_build_url = None
        if hasattr(job_spec, "build_url"):
            self.job_build_url = job_spec.build_url

        if job_spec.scheduling_type in [SchedulingType.TODAY, SchedulingType.REPEAT]:
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
        self.local_scheduler_logger = None
        self.job_state = JobStatusType.IN_PROGRESS
        self.log_handler = None

        self.shutdown_reason = None
        self.script_items = None
        self.initialized = False
        self.current_script_item_index = 0
        self.active_script_item_index = -1
        self.suite_completed = False
        self.initialize()

    def initialize(self):
        # Setup the suites own logger
        # TODO: Failure here should be reported to global logger
        self.prepare_job_directory()
        local_scheduler_logger = logging.getLogger("scheduler_log_{}.txt".format(self.job_id))
        local_scheduler_logger.setLevel(logging.INFO)
        self.log_handler = logging.handlers.RotatingFileHandler(self.job_dir + "/scheduler.log.txt",
                                                                maxBytes=TEN_MB,
                                                                backupCount=5)
        self.log_handler.setFormatter(
            logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        local_scheduler_logger.addHandler(hdlr=self.log_handler)
        self.local_scheduler_logger = local_scheduler_logger
        models_helper.update_suite_execution(suite_execution_id=self.job_id,
                                             result=RESULTS["IN_PROGRESS"],
                                             state=JobStatusType.IN_PROGRESS)

        build_url = self.job_build_url
        if not build_url:
            build_url = DEFAULT_BUILD_URL

        version = determine_version(build_url=build_url)
        if not version:
            self.abort_suite(error_message="Unable to determine version from build url: {}".format(build_url))
        else:
            build_url = build_url.replace("latest", str(version))
            self.job_build_url = build_url
            self.debug("Build url: {}".format(self.job_build_url))

        self.job_version = version
        self.abort_on_failure_requested = False
        self.prepare_script_items()
        self.initialized = True

    def shutdown_suite(self, reason=ShutdownReason.KILLED):

        self.shutdown_reason = reason
        scheduler_logger.info("{} Shutdown_suite".format(get_job_string_from_spec(job_spec=self.job_spec)))
        self.suite_shutdown = True
        if self.current_script_process:
            for i in range(2):
                try:
                    while self.current_script_process.poll() is None:
                        # os.kill(self.current_script_process.pid, signal.SIGINT)
                        time.sleep(5)
                        self.current_script_process.kill()
                        os.kill(self.current_script_process.pid, signal.SIGKILL)
                        self.current_script_process.communicate()
                except Exception as ex:
                    pass

        suite_execution = models_helper.get_suite_execution(suite_execution_id=self.job_id)
        suite_execution.completed_time = datetime.datetime.now()
        suite_execution.save()
        suite_execution.save()
        self.suite_complete()

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

    def get_scripts(self, suite_execution_id, suite_file=None, dynamic_suite_spec=None):
        all_tags = []
        items = []
        if suite_file:
            suite_spec = parse_suite(suite_name=suite_file)
            suite_level_tags = get_suite_level_tags(suite_spec=suite_spec)
            all_tags.extend(suite_level_tags)
            items = suite_spec
        else:
            suite_spec = json.loads(dynamic_suite_spec)
            suite_level_tags = get_suite_level_tags(suite_spec=suite_spec)
            all_tags.extend(suite_level_tags)
            items = suite_spec

        all_tags = list(set(all_tags))
        self.apply_tags_to_items(items=items, tags=all_tags)
        suite_execution = models_helper.get_suite_execution(suite_execution_id=suite_execution_id)
        if suite_execution:
            suite_execution_tags = json.loads(suite_execution.tags)
            all_tags.extend(suite_execution_tags)

        return items, all_tags

    def abort_suite(self, error_message):
        self.shutdown_reason = ShutdownReason.ABORTED
        models_helper.update_suite_execution(suite_execution_id=self.job_id,
                                             result=RESULTS["ABORTED"],
                                             state=JobStatusType.ABORTED)
        models_helper.finalize_suite_execution(suite_execution_id=self.job_id)
        self.error(error_message)
        self.suite_shutdown = True

    def get_script_string(self, script_path=None):
        script_string = " "
        if script_path:
            script_string = " Script: {} ".format(script_path)
        return script_string

    def debug(self, message, script_path=None):
        self.local_scheduler_logger.info("{} {}{}".format(get_job_string_from_spec(job_spec=self.job_spec),
                                                          self.get_script_string(script_path=script_path), message))

    def error(self, message, script_path=None):
        scheduler_logger.exception("{} {}{}".format(get_job_string_from_spec(job_spec=self.job_spec),
                                                    self.get_script_string(script_path=script_path), message))
        self.local_scheduler_logger.exception(message)

    def get_script_inputs(self, script_item):
        script_inputs = {}
        if "inputs" in script_item:
            script_inputs = script_item["inputs"]
        job_inputs = self.job_inputs
        if not script_inputs and job_inputs:
            script_inputs = {}
            script_inputs.update(job_inputs)
        return script_inputs

    def poll_script(self, script_path):
        crashed = False
        self.debug("Begin polling Script: {}".format(script_path))
        poll_status = None
        while poll_status is None:
            poll_status = self.current_script_process.poll()
        if poll_status:  #
            self.debug("FAILED: Script {}".format(os.path.basename(script_path)))
            crashed = True  # TODO: Need to re-check this based on exit code
        self.debug("Done polling Script: {}".format(script_path))
        return crashed

    def suite_complete(self):
        state = JobStatusType.COMPLETED
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

    def cleanup(self):
        self.log_handler.close()

    def prepare_script_items(self):
        script_items = []
        all_tags = self.job_tags
        if self.job_suite_path and self.job_suite_type == SuiteType.STATIC:
            script_items, all_tags = self.get_scripts(suite_execution_id=self.job_id,
                                                      suite_file=self.job_suite_path)

        elif self.job_script_path:
            script_items.append({"path": self.job_script_path})
        elif self.job_suite_type == SuiteType.DYNAMIC:
            script_items, all_tags = self.get_scripts(suite_execution_id=self.job_id,
                                                      dynamic_suite_spec=self.job_dynamic_suite_spec)
            # TODO: Delete dynamic spec

        script_paths = map(lambda f: SCRIPTS_DIR + "/" + f["path"], filter(lambda f: "info" not in f, script_items))
        scripts_exist, error_message = self.ensure_scripts_exists(script_paths)
        if not scripts_exist:
            self.abort_suite(error_message=error_message)

        self.debug("Scripts to be executed")
        map(lambda f: self.local_scheduler_logger.debug("{}: {}".format(f[0], f[1])), enumerate(script_paths))
        self.debug("Starting executing scripts")

        suite_path = self.job_suite_path if self.job_suite_path else self.job_script_path
        models_helper.update_suite_execution(suite_execution_id=self.job_id,
                                             tags=all_tags,
                                             build_url=self.job_build_url,
                                             version=self.job_version,
                                             suite_path=suite_path)
        self.script_items = script_items
        if not self.script_items:
            self.abort_suite("No scripts detected in suite")

        return self.script_items

    def run_next(self):
        if not self.initialized:
            self.initialize()
        if self.suite_shutdown or self.suite_completed or self.abort_on_failure_requested:
            return

        script_item = self.script_items[self.current_script_item_index]
        if "info" in script_item or ("disabled" in script_item and script_item["disabled"]):
            self.set_next_script_item_index()
        script_item = self.script_items[self.current_script_item_index]
        if self.current_script_item_index == self.active_script_item_index:

            if self.current_script_process.poll() is None:
                '''
                poll_result = self.current_script_process.poll()
                self.debug("Script polling is done")
                self.set_next_script_item_index()
                '''
                self.debug(message="Executed", script_path=self.last_script_path)

                script_result = False
                if self.current_script_process.returncode == 0:
                    script_result = True
                if not script_result:
                    if "abort_suite_on_failure" in script_item and script_item["abort_suite_on_failure"]:
                        self.abort_on_failure_requested = True
                        self.error(message="Abort Requested on failure", script_path=self.last_script_path)
            else:
                print ("PID: {} does not exist".format(self.current_script_process.pid))
                self.set_next_script_item_index()

        elif self.current_script_item_index > self.active_script_item_index:
            self.start_script(script_item=script_item, script_item_index=self.current_script_item_index)  # schedule it


    def start_script(self, script_item, script_item_index):
        print ("Start_script: {}".format(script_item))
        script_path = SCRIPTS_DIR + "/" + script_item["path"]
        self.last_script_path = script_path
        if self.abort_on_failure_requested:
            self.error(message="Skipping, as abort_on_failure_requested", script_path=script_path)
            self.shutdown_suite(reason=ShutdownReason.ABORTED)
            return
        if self.suite_shutdown:
            self.error(message="Suite shutdown requested", script_path=script_path)
            self.summary_extra_message = "Suite was shutdown"
            self.shutdown_suite(reason=ShutdownReason.ABORTED)
            return

        relative_path = script_path.replace(SCRIPTS_DIR, "")
        self.debug("Before running script: {}".format(script_path))

        console_log_file_name = self.job_dir + "/" + get_flat_console_log_file_name("/{}".format(script_path),
                                                                                    script_item_index)
        try:
            with open(console_log_file_name, "w") as console_log:
                self.local_scheduler_logger.info("Executing: {}".format(script_path))
                popens = ["python",
                          script_path,
                          "--" + "logs_dir={}".format(self.job_dir),
                          "--" + "suite_execution_id={}".format(self.job_id),
                          "--" + "relative_path={}".format(relative_path),
                          "--" + "build_url={}".format(self.job_build_url),
                          "--" + "log_prefix={}".format(script_item_index)]

                if self.job_test_case_ids:
                    popens.append("--test_case_ids=" + ','.join(str(v) for v in self.job_test_case_ids))
                if "test_case_ids" in script_item:
                    popens.append("--test_case_ids=" + ','.join(str(v) for v in script_item["test_case_ids"]))
                if "re_run_info" in script_item:
                    popens.append("--re_run_info={}".format(json.dumps(script_item["re_run_info"])))
                if self.job_environment:
                    popens.append("--environment={}".format(json.dumps(self.job_environment)))  # TODO: validate

                script_inputs = self.get_script_inputs(script_item=script_item)
                if script_inputs:
                    popens.append("--inputs={}".format(json.dumps(script_inputs)))  # TODO: validate

                self.debug("Before subprocess Script: {}".format(script_path))

                self.current_script_process = subprocess.Popen(popens,
                                                               stdout=console_log,
                                                               stderr=console_log)

                time.sleep(5)


                self.active_script_item_index = script_item_index
        except Exception as ex:
            self.error("Script error {}, exception: {}".format(script_item, str(ex)))
            self.set_next_script_item_index()

    def is_suite_completed(self):
        return self.suite_completed is True

    def set_next_script_item_index(self):
        self.current_script_item_index += 1
        if self.current_script_item_index >= len(self.script_items):

            self.suite_complete()
            self.cleanup()

    def run(self):
        if not self.initialized:
            self.initialize()
        last_script_path = ""
        try:
            self.debug("{} Running")
            script_index = 0

            for script_item in self.script_items:
                script_index += 1
                if "info" in script_item or ("disabled" in script_item and script_item["disabled"]):
                    continue
                script_path = SCRIPTS_DIR + "/" + script_item["path"]
                last_script_path = script_path
                if self.abort_on_failure_requested:
                    self.debug(message="Skipping, as abort_on_failure_requested", script_path=script_path)
                    continue
                if self.suite_shutdown:
                    self.error(message="Suite shutdown requested", script_path=script_path)
                    self.summary_extra_message = "Suite was shutdown"
                    continue

                relative_path = script_path.replace(SCRIPTS_DIR, "")
                if self.job_test_case_ids:
                    if self.job_script_path not in relative_path:
                        continue
                self.debug("Before running script: {}".format(script_path))

                console_log_file_name = self.job_dir + "/" + get_flat_console_log_file_name("/{}".format(script_path),
                                                                                            script_index)
                try:
                    with open(console_log_file_name, "w") as console_log:
                        self.local_scheduler_logger.info("Executing: {}".format(script_path))
                        popens = ["python",
                                  script_path,
                                  "--" + "logs_dir={}".format(self.job_dir),
                                  "--" + "suite_execution_id={}".format(self.job_id),
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
                            popens.append("--environment={}".format(json.dumps(self.job_environment)))  # TODO: validate

                        script_inputs = self.get_script_inputs(script_item=script_item)
                        if script_inputs:
                            popens.append("--inputs={}".format(json.dumps(script_inputs)))  # TODO: validate

                        self.debug("Before subprocess Script: {}".format(script_path))
                        self.current_script_process = subprocess.Popen(popens,
                                                                       close_fds=True,
                                                                       stdout=console_log,
                                                                       stderr=console_log)
                        self.debug("After subprocess Script: {}".format(script_path))
                        wait_return_code = self.current_script_process.wait()
                        self.debug(message="Wait return_code: {}".format(wait_return_code))
                except Exception as ex:
                    self.error(str(ex))
                self.poll_script(script_path=script_path)

                script_result = False
                if self.current_script_process.returncode == 0:
                    script_result = True
                else:
                    if "abort_suite_on_failure" in script_item and script_item["abort_suite_on_failure"]:
                        self.abort_on_failure_requested = True
                        self.error(message="Abort Requested on failure", script_path=script_path)
                self.debug(message="Executed", script_path=script_path)

            self.debug("Completed")

            if self.abort_on_failure_requested:
                self.abort_suite(error_message="Abort Requested on failure for: {}".format(last_script_path))

        except Exception as ex:
            self.abort_suite(error_message=str(ex))
        self.suite_complete()
        self.cleanup()


    def post_process(self):
        pass


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
                t.shutdown_suite()
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
                job_spec.set_properties(scheduled_time=get_current_time() + datetime.timedelta(seconds=scheduling_time),
                                        state=JobStatusType.SCHEDULED)
                t.start()
            if scheduling_time < 0:
                scheduler_logger.critical("{} Unable to process job submission. Scheduling time in the past".format(
                    get_job_string_from_spec(job_spec=job_spec)))
                job_spec.delete()

        except Exception as ex:
            scheduler_logger.exception(str(ex))
    queue_lock.release()


def remove_scheduled_job(job_id):
    job_spec = JobSpec.objects.get(job_id=job_id)
    job_spec.is_auto_scheduled_job = False
    job_spec.save()
    # TODO handle exception


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
    scheduler_logger.info("Trying graceful shutdown")
    run_to_completion(max_wait_time=max_wait_time)
    remove_pid()
    set_scheduler_state(SchedulerStates.SCHEDULER_STATE_STOPPED)
    scheduler_logger.info("Exiting graceful shutdown")


def process_auto_scheduled_jobs():
    # Get auto_scheduled_jobs
    auto_scheduled_jobs = models_helper.get_suite_executions_by_filter(is_auto_scheduled_job=True)
    auto_scheduled_jobs = auto_scheduled_jobs.order_by('submitted_time')

    for auto_scheduled_job in auto_scheduled_jobs:
        auto_schedule_job_id = auto_scheduled_job.execution_id
        in_progress_suites = models_helper.get_suite_executions_by_filter(state__gt=JobStatusType.AUTO_SCHEDULED,
                                                                          auto_scheduled_execution_id=auto_schedule_job_id)
        if not in_progress_suites.count():
            # if job_id not in progress, clone and submit
            print("Cloning")
            cloned_job = clone_job(job_id=auto_schedule_job_id)
            cloned_job.state = JobStatusType.SUBMITTED
            cloned_job.is_auto_scheduled_job = False
            cloned_job.auto_scheduled_execution_id = auto_schedule_job_id
            if auto_scheduled_job.scheduling_type == SchedulingType.TODAY and auto_scheduled_job.repeat_in_minutes > 0:
                auto_scheduled_job.scheduling_type = SchedulingType.REPEAT
                auto_scheduled_job.save()
                auto_scheduled_job.save()
            scheduler_logger.info("{} instantiating auto-scheduled job to {}".format(
                get_job_string_from_spec(job_spec=auto_scheduled_job),
                get_job_string_from_spec(job_spec=cloned_job)))
            cloned_job.save()
            cloned_job.save()


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


def clear_out_queue():
    JobQueue.objects.all().delete()


def initialize():
    JobQueue.objects.all().delete()


def join_suite_workers():
    jobs_to_be_removed = []
    for job_id, t in job_id_threads.iteritems():
        try:
            if not t.is_suite_completed():
                t.run_next()
            else:
                jobs_to_be_removed.append(job_id)
        except Exception as ex:
            print str(ex)

    for job_to_be_removed in jobs_to_be_removed:
        if job_to_be_removed in job_id_threads:
            del job_id_threads[job_to_be_removed]


if __name__ == "__main__":
    queue_lock = Lock()
    ensure_singleton()
    initialize()
    scheduler_logger.info("Started Scheduler")
    set_scheduler_state(SchedulerStates.SCHEDULER_STATE_RUNNING)
    # queue_worker.start()
    test_bed_monitor.start()
    clear_out_queue()

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

        try:
            process_killed_jobs()
            process_container_suites()
            queue_worker.run()
            scheduler_info = get_scheduler_info()
            request = process_external_requests()
            join_suite_workers()
            if (scheduler_info.state != SchedulerStates.SCHEDULER_STATE_STOPPING) and \
                    (scheduler_info.state != SchedulerStates.SCHEDULER_STATE_STOPPED):
                process_auto_scheduled_jobs()
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
