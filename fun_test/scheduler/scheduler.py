from fun_settings import *
import logging, logging.handlers
import json, os, sys
import glob
import time, subprocess, datetime
from threading import Thread
import web.fun_test.models_helper as models_helper

DEBUG = True

LOG_FILE_NAME = LOGS_DIR + "/scheduler.log"
LOG_DIR_PREFIX = "s_"
TEN_MB = 1e7
QUEUED_JOB_EXTENSION = "queued.json"

TEST_CASE_SPEC_DIR = SCRIPTS_DIR + "/test_case_spec"
SUITES_DIR = TEST_CASE_SPEC_DIR + "/suites"

CONSOLE_LOG_EXTENSION = ".logs.txt"
JSON_EXTENSION = ".json"

scheduler_logger = logging.getLogger("scheduler_log")
scheduler_logger.setLevel(logging.INFO)

if not DEBUG:
    handler = logging.handlers.RotatingFileHandler(LOG_FILE_NAME, maxBytes=TEN_MB, backupCount=5)
    handler.setFormatter(logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
else:
    handler = logging.StreamHandler(sys.stdout)
    scheduler_logger.addHandler(hdlr=handler)

threads = []


class SchedulerException(Exception):
    pass


def parse_file_to_json(file_name):
    result = None
    try:
        with open(file_name, "r") as infile:
            contents = infile.read()
            result = json.loads(contents)
    except Exception as ex:
        scheduler_logger.critical(str(ex))
    return result

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


    def prepare_job_folder(self):
        self.job_dir = LOGS_DIR + "/" + LOG_DIR_PREFIX + str(self.job_id)
        try:
            if not os.path.exists(self.job_dir):
                os.makedirs(self.job_dir)
        except Exception as ex:
            raise SchedulerException(str(ex))

    def run(self):
        scheduler_logger.info("Running Job: {}".format(self.job_spec["job_id"]))
        self.prepare_job_folder()

        # Setup the suites own logger
        local_scheduler_logger = logging.getLogger("scheduler_log")
        local_scheduler_logger.setLevel(logging.INFO)
        handler = logging.handlers.RotatingFileHandler(self.job_dir + "/scheduler.log", maxBytes=TEN_MB, backupCount=5)
        handler.setFormatter(
            logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        local_scheduler_logger.addHandler(hdlr=handler)
        self.local_scheduler_logger = local_scheduler_logger


        suite_summary = {}

        suite_spec = get_scripts_in_suite(suite_name=self.job_spec["suite_name"])
        script_paths = map(lambda f: SCRIPTS_DIR + "/" + f["path"], suite_spec)

        self.local_scheduler_logger.info("Scripts to be executed:")
        map(lambda f: self.local_scheduler_logger.info("{}: {}".format(f[0], f[1])), enumerate(script_paths))


        self.local_scheduler_logger.info("Starting Job-id: {}".format(self.job_id))

        suite_execution_id = self.job_id
        suite_execution = models_helper.get_suite_execution(suite_execution_id=suite_execution_id)
        if not suite_execution:
            raise SchedulerException("Unable to retrieve suite execution id: {}".format(suite_execution_id))
        suite_execution.scheduled_time = datetime.datetime.now()
        suite_execution.suite_path = self.job_spec["suite_name"]
        suite_execution.save()

        for script_path in script_paths:

            crashed = False
            console_log_file_name = self.job_dir + "/{}{}".format(os.path.basename(script_path), CONSOLE_LOG_EXTENSION)
            with open(console_log_file_name, "w") as console_log:
                self.local_scheduler_logger.info("Executing: {}".format(script_path))
                script_process = subprocess.Popen(["python",
                                                   script_path,
                                                   "--" + "logs_dir={}".format(self.job_dir),
                                                   "--" + "suite_execution_id={}".format(suite_execution_id),
                                                   "--" + "relative_path={}".format(script_path.replace(SCRIPTS_DIR, ""))],
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
        scheduler_logger.info("Job Id: {} complete".format(self.job_id))
        suite_execution = models_helper.get_suite_execution(suite_execution_id=suite_execution_id)
        suite_execution.completed_time = datetime.datetime.now()
        suite_execution.save()

        # print job summary
        self.local_scheduler_logger.info("Suite Summary:")
        scheduler_logger.info("{:50} {} {}".format("Script", "Result", "Crashed"))
        for script_path, script_metrics in suite_summary.items():
            scheduler_logger.info("{:50} {} {}".format(script_path,
                                                       str(script_metrics["result"]),
                                                       str(script_metrics["crashed"])))

def process_queue():
    # sort by date
    job_files = glob.glob("{}/*{}".format(JOBS_DIR, QUEUED_JOB_EXTENSION))
    job_files.sort(key=os.path.getmtime)

    for job_file in job_files:
        # Execute
        job_spec = parse_file_to_json(file_name=job_file)
        if job_spec:
            t = SuiteWorker(job_spec=job_spec)
            threads.append(t)
            t.start()
        else:
            raise SchedulerException("Unable to parse {}".format(job_file))
        de_queue_job(job_file)
    #for thread in threads:
    #    thread.join()


def queue_job(job_id, suite_name):
    time.sleep(0.1)  # enough time to keep the creation timestamp unique
    f = open("{}/{}.{}".format(JOBS_DIR, job_id, QUEUED_JOB_EXTENSION), "w")
    job_spec = {}

    job_spec["suite_name"] = suite_name
    suite_execution = models_helper.add_suite_execution(submitted_time=datetime.datetime.now(),
                                      scheduled_time=datetime.datetime.max,
                                      completed_time=datetime.datetime.max
                                    )
    job_spec["job_id"] = suite_execution.execution_id
    # job_spec["suite_execution_id"] = suite_execution.execution_id
    f.write(json.dumps(job_spec))
    f.close()
    scheduler_logger.info("Job Id: {} suite: {} Queued".format(job_id, suite_name))

def de_queue_job(job_file):
    try:
        os.remove(job_file)
    except Exception as ex:
        scheduler_logger.critical(str(ex))


if __name__ == "__main__":
    queue_job(job_id=1, suite_name="storage_basic")
    #queue_job(job_id=2, suite="suite2")
    #queue_job(job_id=4, suite="suite3")
    #queue_job(job_id=3, suite="suite4")
    #queue_job(job_id=5, suite="suite5")
    while True:
        process_queue()
    # process killed jobs
    # wait
    pass

# if __name__ == "__main1__":
