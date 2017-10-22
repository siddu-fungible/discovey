import time, datetime, json
import web.fun_test.models_helper as models_helper
from fun_settings import JOBS_DIR

CONSOLE_LOG_EXTENSION = ".logs.txt"
HTML_LOG_EXTENSION = ".html"
LOG_DIR_PREFIX = "s_"
QUEUED_JOB_EXTENSION = "queued.json"
JSON_EXTENSION = ".json"


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

def queue_job(suite_path):
    time.sleep(0.1)  # enough time to keep the creation timestamp unique

    suite_execution = models_helper.add_suite_execution(submitted_time=datetime.datetime.now(),
                                      scheduled_time=datetime.datetime.max,
                                      completed_time=datetime.datetime.max)
    job_spec = {}
    job_spec["suite_name"] = suite_path.replace(JSON_EXTENSION, "")
    job_id = suite_execution.execution_id
    job_spec["job_id"] = job_id
    f = open("{}/{}.{}".format(JOBS_DIR, job_id, QUEUED_JOB_EXTENSION), "w")
    f.write(json.dumps(job_spec))
    f.close()
    print("Job Id: {} suite: {} Queued".format(job_id, suite_path))
    return job_id

if __name__ == "__main__":
    print get_flat_console_log_file_name(path="/clean_sanity.py")
    print get_flat_html_log_file_name(path="/examples/clean_sanity.py")