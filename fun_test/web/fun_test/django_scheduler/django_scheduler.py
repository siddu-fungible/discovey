import logging.handlers
from threading import Thread
import time
from fun_settings import JOBS_DIR, ARCHIVED_JOBS_DIR, LOGS_DIR, KILLED_JOBS_DIR, WEB_STATIC_DIR, MEDIA_DIR

scheduler_logger = logging.getLogger("main_scheduler_log")
scheduler_logger.setLevel(logging.DEBUG)


CONSOLE_LOG_EXTENSION = ".logs.txt"
HTML_LOG_EXTENSION = ".html"
LOG_DIR_PREFIX = "s_"
QUEUED_JOB_EXTENSION = "queued.json"
ARCHIVED_JOB_EXTENSION = "archived.json"
KILLED_JOB_EXTENSION = "killed_job"
JSON_EXTENSION = ".json"
LOG_FILE_NAME = LOGS_DIR + "/scheduler.log"
BUILD_INFO_FILENAME = "build_info.txt"

scheduler_logger = logging.getLogger("main_scheduler_log")
scheduler_logger.setLevel(logging.DEBUG)

TEN_MB = 1e7
DEBUG = False





if not DEBUG:
    handler = logging.handlers.RotatingFileHandler(LOG_FILE_NAME, maxBytes=TEN_MB, backupCount=5)
else:
    handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
scheduler_logger.addHandler(hdlr=handler)
scheduler_logger.setLevel(logging.DEBUG)


class SchedulerException(Exception):
    def __init__(self, *args):
        super(SchedulerException, self).__init__(*args)
        scheduler_logger.exception(*args)


class SchedulerMainWorker(Thread):
    def run(self):
        while True:
            time.sleep(5)
            print "Thread run"

