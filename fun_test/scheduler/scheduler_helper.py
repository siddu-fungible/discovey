import time, datetime, json, glob
import psutil, logging.handlers, sys
import web.fun_test.models_helper as models_helper
from fun_settings import JOBS_DIR, ARCHIVED_JOBS_DIR, LOGS_DIR


CONSOLE_LOG_EXTENSION = ".logs.txt"
HTML_LOG_EXTENSION = ".html"
LOG_DIR_PREFIX = "s_"
QUEUED_JOB_EXTENSION = "queued.json"
ARCHIVED_JOB_EXTENSION = "archived.json"
JSON_EXTENSION = ".json"
LOG_FILE_NAME = LOGS_DIR + "/scheduler.log"

scheduler_logger = logging.getLogger("main_scheduler_log")
scheduler_logger.setLevel(logging.DEBUG)

TEN_MB = 1e7
DEBUG = True


if not DEBUG:
    handler = logging.handlers.RotatingFileHandler(LOG_FILE_NAME, maxBytes=TEN_MB, backupCount=5)
    handler.setFormatter(logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
else:
    handler = logging.StreamHandler(sys.stdout)
    scheduler_logger.addHandler(hdlr=handler)
    scheduler_logger.setLevel(logging.DEBUG)

class SchedulerException(Exception):
    def __init__(self, *args):
        super(SchedulerException, self).__init__(*args)
        scheduler_logger.critical(*args)

def get_flat_file_name(path):
    parts = path.split("/")
    flat = path
    if len(parts) > 2:
        flat = "_".join(parts[-2:])
    return flat.lstrip("/")

def get_flat_console_log_file_name(path):
    return get_flat_file_name(path=path) + CONSOLE_LOG_EXTENSION

def get_flat_html_log_file_name(path):
    return get_flat_file_name(path=path) + HTML_LOG_EXTENSION

def queue_job(suite_path=None,
              build_url=None,
              job_spec=None,
              schedule_at=None,
              schedule_in_minutes=None,
              repeat=False):
    time.sleep(0.1)  # enough time to keep the creation timestamp unique

    suite_execution = models_helper.add_suite_execution(submitted_time=datetime.datetime.now(),
                                      scheduled_time=datetime.datetime.max,
                                      completed_time=datetime.datetime.max)
    if not job_spec:
        job_spec = {}
        suite_path = suite_path.replace(JSON_EXTENSION, "")
        job_spec["suite_name"] = suite_path.replace(JSON_EXTENSION, "")
        job_spec["build_url"] = build_url
        job_spec["schedule_at"] = schedule_at
        job_spec["schedule_in_minutes"] = schedule_in_minutes
        job_spec["repeat"] = repeat
    job_id = suite_execution.execution_id
    job_spec["job_id"] = job_id


    f = open("{}/{}.{}".format(JOBS_DIR, job_id, QUEUED_JOB_EXTENSION), "w")
    f.write(json.dumps(job_spec))
    f.close()
    print("Job Id: {} suite: {} Queued".format(job_id, suite_path))
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
    for k in ["schedule_at", "schedule_in_minutes", "schedule_in_minutes_at"]:
        try:
            del job_spec[k]
        except:
            pass
    return queue_job(job_spec=job_spec)

def parse_file_to_json(file_name):
    result = None
    try:
        with open(file_name, "r") as infile:
            contents = infile.read()
            result = json.loads(contents)
    except Exception as ex:
        scheduler_logger.critical(str(ex))
    return result

def process_list(process_name):
    processes = []

    for proc in psutil.process_iter():
        try:
            proc_name = proc.name()
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
    return processes

if __name__ == "__main__":
    print get_flat_console_log_file_name(path="/clean_sanity.py")
    print get_flat_html_log_file_name(path="/examples/clean_sanity.py")