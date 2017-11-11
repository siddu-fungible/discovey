import time, datetime, json, glob
import psutil, logging.handlers, sys
import web.fun_test.models_helper as models_helper
from web.fun_test.web_interface import get_suite_detail_url
from fun_settings import JOBS_DIR, ARCHIVED_JOBS_DIR, LOGS_DIR, KILLED_JOBS_DIR, WEB_STATIC_DIR
from fun_global import RESULTS, is_regression_server
from lib.utilities.send_mail import send_mail

CONSOLE_LOG_EXTENSION = ".logs.txt"
HTML_LOG_EXTENSION = ".html"
LOG_DIR_PREFIX = "s_"
QUEUED_JOB_EXTENSION = "queued.json"
ARCHIVED_JOB_EXTENSION = "archived.json"
KILLED_JOB_EXTENSION = "killed_job"
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

def kill_job(job_id):
    filename = "{}/{}_{}".format(KILLED_JOBS_DIR, job_id, KILLED_JOB_EXTENSION)
    with open(filename, "w") as f:
        f.write(str(job_id))

def queue_job(suite_path="unknown",
              build_url=None,
              job_spec=None,
              schedule_at=None,
              repeat=False,
              schedule_in_minutes=None,
              repeat_in_minutes=None):
    time.sleep(0.1)  # enough time to keep the creation timestamp unique

    if suite_path == "unknown":
        if job_spec:
            suite_path = job_spec["suite_name"].replace(JSON_EXTENSION, "")
    suite_execution = models_helper.add_suite_execution(submitted_time=datetime.datetime.now(),
                                      scheduled_time=datetime.datetime.max,
                                      completed_time=datetime.datetime.max,
                                                        suite_path=suite_path)
    if not job_spec:
        job_spec = {}
        suite_path = suite_path.replace(JSON_EXTENSION, "")
        job_spec["suite_name"] = suite_path.replace(JSON_EXTENSION, "")
        job_spec["build_url"] = build_url
        job_spec["schedule_at"] = schedule_at
        job_spec["repeat"] = repeat
        job_spec["schedule_in_minutes"] = schedule_in_minutes
        job_spec["repeat_in_minutes"] = repeat_in_minutes
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
    for k in ["schedule_at", "schedule_in_minutes", "schedule_in_minutes_at", "repeat"]:
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

def send_summary_mail(job_id):
    suite_executions = models_helper._get_suite_executions(execution_id=job_id, save_test_case_info=True)
    suite_execution = suite_executions[0]
    suite_execution_attributes = models_helper._get_suite_execution_attributes(suite_execution=suite_execution)
    header_list = ["Metric", "Value"]
    table1 = _get_table(header_list=header_list, list_of_rows=suite_execution_attributes)
    header_list = ["TC-ID", "Summary", "Path", "Result"]
    list_of_rows = [[x["test_case_id"], "Summary1", x["script_path"], x["result"]] for x in suite_execution["test_case_info"]]
    table2 = _get_table(header_list=header_list, list_of_rows=list_of_rows)

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
        <br>
        %s
        <br>
        <br>
        %s
        """ % (css, suite_detail_url, table1, table2)

        # print html

        subject = "Automation: {}: {} P:{} F:{}".format(suite_execution["suite_result"],
                                            suite_execution["fields"]["suite_path"],
                                            suite_execution["num_passed"],
                                            suite_execution["num_failed"])

        if is_regression_server():
            result = send_mail(subject=subject, content=html)
            if not result["status"]:
                scheduler_logger.error("Send Mail: {}".format(result["error_message"]))

if __name__ == "__main__":
    print get_flat_console_log_file_name(path="/clean_sanity.py")
    print get_flat_html_log_file_name(path="/examples/clean_sanity.py")
