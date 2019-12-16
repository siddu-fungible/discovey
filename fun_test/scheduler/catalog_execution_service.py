from django.db.models import Q

from fun_settings import TEAM_REGRESSION_EMAIL
from fun_global import RESULTS
import web.fun_test.django_interactive
from web.fun_test.models import Daemon
from fun_global import get_current_time
from scheduler_global import JobStatusType
import time
import sys
import logging
import logging.handlers
from threading import Thread
import re
from scheduler.scheduler_helper import queue_job3
# from web.fun_test.models_helper import
from web.fun_test.models import ReleaseCatalogExecution, SuiteExecution
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


class CatalogExecutionStateMachine:
    def __init__(self):
        pass

    def queue_job(self, catalog_execution, suite_execution):
        environment = {"bundle_image_parameters": {"release_train": catalog_execution.release_train,
                                                   "build_number": "latest"}}
        job_id = queue_job3(suite_id=suite_execution["suite_id"],
                            emails=[TEAM_REGRESSION_EMAIL],
                            submitter_email=catalog_execution.owner,
                            tags="tbd",
                            test_bed_type=suite_execution["test_bed_name"],
                            environment=environment)
        return job_id

    def process_submitted_releases(self):
        q = Q(deleted=False, state=JobStatusType.SUBMITTED)
        catalog_executions = ReleaseCatalogExecution.objects.filter(q)
        for catalog_execution in catalog_executions:
            for suite_execution in catalog_execution.suite_executions:
                valid_job_parameters = True
                if not suite_execution["test_bed_name"]:
                    valid_job_parameters = False
                    suite_execution["error_message"] = "Test-bed is invalid"
                if valid_job_parameters:
                    job_id = self.queue_job(catalog_execution=catalog_execution, suite_execution=suite_execution)
                    suite_execution["job_id"] = job_id
                    suite_execution["error_message"] = None
            catalog_execution.state = JobStatusType.IN_PROGRESS
            catalog_execution.save()

    def process_in_progress_releases(self):
        q = Q(deleted=False, state=JobStatusType.IN_PROGRESS)
        catalog_executions = ReleaseCatalogExecution.objects.filter(q)
        for catalog_execution in catalog_executions:
            for suite_execution in catalog_execution.suite_executions:
                valid_job_parameters = True
                if not suite_execution["test_bed_name"]:
                    valid_job_parameters = False
                    suite_execution["error_message"] = "Test-bed is invalid"
                if valid_job_parameters and not suite_execution["job_id"]:
                    job_id = self.queue_job(catalog_execution=catalog_execution, suite_execution=suite_execution)
                    suite_execution["job_id"] = job_id
                    suite_execution["error_message"] = None
            catalog_execution.save()

        # Prepare to change the state of the release
        for catalog_execution in catalog_executions:
            job_ids = []
            for suite_execution in catalog_execution.suite_executions:
                job_ids.append(suite_execution["job_id"])

            if job_ids:
                completed_job_ids = 0
                for job_id in job_ids:
                    s = SuiteExecution.objects.get(execution_id=job_id)
                    if JobStatusType.is_completed(s.state):
                        completed_job_ids += 1
                if len(job_ids) == completed_job_ids:
                    catalog_execution.state = JobStatusType.COMPLETED
            catalog_execution.save()

    def run(self):
        self.process_submitted_releases()
        self.process_in_progress_releases()


if __name__ == "__main__":
    while True:
        Daemon.get(name=DAEMON_NAME).beat()
        CatalogExecutionStateMachine().run()
        time.sleep(15)
