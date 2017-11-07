from fun_settings import *
from fun_global import get_current_time
import os
import re
import subprocess
from threading import Thread
from scheduler_helper import *
import dateutil.parser

threads = []

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

    def prepare_job_directory(self):
        self.job_dir = LOGS_DIR + "/" + LOG_DIR_PREFIX + str(self.job_id)
        try:
            if not os.path.exists(self.job_dir):
                os.makedirs(self.job_dir)
        except Exception as ex:
            raise SchedulerException(str(ex))

    def run(self):
        scheduler_logger.debug("Running Job: {}".format(self.job_id))
        suite_execution_id = self.job_id
        self.prepare_job_directory()
        build_url = self.job_build_url

        # Setup the suites own logger
        local_scheduler_logger = logging.getLogger("scheduler_log")
        local_scheduler_logger.setLevel(logging.ERROR)
        handler = logging.handlers.RotatingFileHandler(self.job_dir + "/scheduler.log", maxBytes=TEN_MB, backupCount=5)
        handler.setFormatter(
            logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        local_scheduler_logger.addHandler(hdlr=handler)
        self.local_scheduler_logger = local_scheduler_logger

        suite_summary = {}

        suite_spec = get_scripts_in_suite(suite_name=self.job_spec["suite_name"])
        script_paths = map(lambda f: SCRIPTS_DIR + "/" + f["path"], suite_spec)

        self.local_scheduler_logger.debug("Scripts to be executed:")
        map(lambda f: self.local_scheduler_logger.debug("{}: {}".format(f[0], f[1])), enumerate(script_paths))


        self.local_scheduler_logger.debug("Starting Job-id: {}".format(self.job_id))

        suite_execution = models_helper.get_suite_execution(suite_execution_id=suite_execution_id)
        if not suite_execution:
            raise SchedulerException("Unable to retrieve suite execution id: {}".format(suite_execution_id))
        suite_execution.scheduled_time = datetime.datetime.now()
        suite_execution.suite_path = self.job_spec["suite_name"]
        suite_execution.save()

        for script_path in script_paths:
            relative_path = script_path.replace(SCRIPTS_DIR, "")
            if self.job_test_case_ids:
                if not self.job_script_path in relative_path:
                    continue
            crashed = False
            # console_log_file_name = self.job_dir + "/{}{}".format(os.path.basename(script_path), CONSOLE_LOG_EXTENSION)
            console_log_file_name = self.job_dir + "/" + get_flat_console_log_file_name("/{}".format(script_path))
            with open(console_log_file_name, "w") as console_log:
                self.local_scheduler_logger.debug("Executing: {}".format(script_path))
                popens = ["python",
                          script_path,
                          "--" + "logs_dir={}".format(self.job_dir),
                          "--" + "suite_execution_id={}".format(suite_execution_id),
                          "--" + "relative_path={}".format(relative_path),
                          "--" + "build_url={}".format(self.job_build_url)]

                if self.job_test_case_ids:
                    popens.append("--test_case_ids=" + ','.join(str(v) for v in self.job_test_case_ids))
                script_process = subprocess.Popen(popens,
                                                  close_fds=True,
                                                  stdout=console_log,
                                                  stderr=console_log)
            poll_status = None
            while poll_status is None:
                # print("Still working...")
                poll_status = script_process.poll()
            if poll_status:  #
                scheduler_logger.critical("CRASH: Script {}".format(os.path.basename(script_path)))
                crashed = True  #TODO: Need to re-check this based on exit code
            script_result = False
            if script_process.returncode == 0:
                script_result = True
            suite_summary[os.path.basename(script_path)] = {"crashed": crashed, "result": script_result}
        scheduler_logger.debug("Job Id: {} complete".format(self.job_id))
        suite_execution = models_helper.get_suite_execution(suite_execution_id=suite_execution_id)
        suite_execution.completed_time = datetime.datetime.now()
        suite_execution.save()

        # print job summary
        self.local_scheduler_logger.debug("Suite Summary:")
        scheduler_logger.debug("{:50} {} {}".format("Script", "Result", "Crashed"))
        for script_path, script_metrics in suite_summary.items():
            scheduler_logger.debug("{:50} {} {}".format(script_path,
                                                       str(script_metrics["result"]),
                                                       str(script_metrics["crashed"])))

def process_queue():
    time.sleep(1)
    # sort by date
    job_files = glob.glob("{}/*{}".format(JOBS_DIR, QUEUED_JOB_EXTENSION))
    job_files.sort(key=os.path.getmtime)

    for job_file in job_files:
        # Execute
        job_spec = parse_file_to_json(file_name=job_file)
        current_time = get_current_time()
        if "schedule_in_minutes" in job_spec and (not "schedule_in_minutes_at" in job_spec):
            job_spec["schedule_in_minutes_at"] = str(current_time + datetime.timedelta(minutes=int(job_spec["schedule_in_minutes"])))
            with open(job_file, "w") as f:
                f.write(json.dumps(job_spec))
        if "schedule_in_minutes_at" in job_spec:
            scheduling_time = dateutil.parser.parse(job_spec["schedule_in_minutes_at"])
            if not current_time >= scheduling_time:
                continue
            else:
                scheduler_logger.debug("Job {}: schedule_in_minutes_at ready to run".format(job_spec["job_id"]))


        if job_spec:
            t = SuiteWorker(job_spec=job_spec)
            threads.append(t)
            t.start()
        else:
            raise SchedulerException("Unable to parse {}".format(job_file))
        de_queue_job(job_file)


def de_queue_job(job_file):
    try:
        archived_file = ARCHIVED_JOBS_DIR + "/" + os.path.basename(job_file)
        archived_file = re.sub('(\d+).{}'.format(QUEUED_JOB_EXTENSION),
                               "\\1.{}".format(ARCHIVED_JOB_EXTENSION),
                               archived_file)
        os.rename(job_file, archived_file)
    except Exception as ex:
        scheduler_logger.critical(str(ex))
        #TODO: Ensure job_file is removed

def ensure_singleton():
    if len(process_list(process_name=os.path.basename(__file__))) > 1:
        raise SchedulerException("Only one instance of scheduler.py is permitted")

if __name__ == "__main1__":
    queue_job(suite_name="storage_basic")
    #queue_job(job_id=2, suite="suite2")
    #queue_job(job_id=4, suite="suite3")
    #queue_job(job_id=3, suite="suite4")
    #queue_job(job_id=5, suite="suite5")
    while True:
        process_queue()
    # process killed jobs
    # wait
    pass

if __name__ == "__main__":
    ensure_singleton()
    scheduler_logger.debug("Started Scheduler")
    while True:
        process_queue()
        # process killed jobs
        # wait
