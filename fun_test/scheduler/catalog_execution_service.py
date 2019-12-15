from fun_global import RESULTS
import web.fun_test.django_interactive
from web.fun_test.models import Daemon
from fun_global import get_current_time
import time
import sys
import logging
import logging.handlers
from threading import Thread
import re
from web.fun_test.models_helper import get_suite_execution, get_log_files
DAEMON_NAME = "catalog_execution_service"
logger = logging.getLogger("{}_logger".format(DAEMON_NAME))
logger.setLevel(logging.DEBUG)
logger.propagate = False
LOG_FILE_NAME = "{}_log.txt".format(DAEMON_NAME)

TEN_MB = 1e7
DEBUG = False

if not DEBUG:
    handler = logging.handlers.RotatingFileHandler(LOG_FILE_NAME, maxBytes=TEN_MB, backupCount=5)
else:
    handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(hdlr=handler)


class FunTimer:
    def __init__(self, max_time=10000):
        self.max_time = max_time
        self.start_time = time.time()

    def start(self):
        self.start_time = time.time()

    def is_expired(self):
        return (self.elapsed_time()) > self.max_time

    def elapsed_time(self):
        current_time = time.time()
        return current_time - self.start_time

    def remaining_time(self):
        return (self.start_time + self.max_time) - time.time()



if __name__ == "__main__":
    while True:
        Daemon.get(name=DAEMON_NAME).beat()
        """
        for triage in triages:
            try:
                s = TriageStateMachine(triage=triage)
                s.run()

            except Exception as ex:
                logger.exception(ex)
        """
        time.sleep(15)
