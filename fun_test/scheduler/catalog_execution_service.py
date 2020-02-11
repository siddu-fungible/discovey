from django.db.models import Q

from fun_settings import TEAM_REGRESSION_EMAIL, LOGS_DIR
from fun_global import RESULTS
import web.fun_test.django_interactive
from web.fun_test.models import Daemon, LastGoodBuild
from fun_global import get_current_time, get_build_number_for_latest
from scheduler_global import JobStatusType
import time
import sys
import json
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
LOG_FILE_NAME = "{}/{}_log.txt".format(LOGS_DIR, DAEMON_NAME)

TEN_MB = 1e7
DEBUG = False

if not DEBUG:
    handler = logging.handlers.RotatingFileHandler(LOG_FILE_NAME, maxBytes=TEN_MB, backupCount=5)
else:
    handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(hdlr=handler)

# ReleaseCatalogExecution.objects.all().delete()


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

    def get_build_number(self, release_train):
        build_number = get_build_number_for_latest(release_train=release_train)
        return build_number

    def queue_job(self, catalog_execution, suite_execution, release_train, build_number):

        environment = {"bundle_image_parameters": {"release_train": release_train,
                                                   "build_number": build_number},
                       "test_bed_type": suite_execution["test_bed_name"]}

        job_id = queue_job3(suite_id=suite_execution["suite_id"],
                            emails=[TEAM_REGRESSION_EMAIL],
                            submitter_email=catalog_execution.owner,
                            tags=["release", catalog_execution.release_train],
                            test_bed_type=[suite_execution["test_bed_name"]],
                            environment=environment)
        logger.info("Queued job: {}: ID: {} SuID: {}".format(catalog_execution, job_id, suite_execution["suite_id"]))
        time.sleep(15) # Prevent flooding as this code is not tested properly
        return job_id

    def process_submitted_releases(self):

        q = Q(deleted=False, state=JobStatusType.SUBMITTED)
        catalog_executions = ReleaseCatalogExecution.objects.filter(q)
        for catalog_execution in catalog_executions:
            build_number = self.get_build_number(release_train=catalog_execution.release_train)
            catalog_execution.build_number = build_number
            if build_number:
                skip = ReleaseCatalogExecution.objects.filter(release_train=catalog_execution.release_train,
                                                              build_number=build_number,
                                                              description=catalog_execution.description).count() > 0
                if not skip:
                    for suite_execution in catalog_execution.suite_executions:
                        valid_job_parameters = True
                        if not suite_execution["test_bed_name"]:
                            valid_job_parameters = False
                            suite_execution["error_message"] = "Test-bed is invalid"
                        if valid_job_parameters:
                            job_id = self.queue_job(catalog_execution=catalog_execution,
                                                    suite_execution=suite_execution,
                                                    release_train=catalog_execution.release_train,
                                                    build_number=build_number)
                            if job_id:
                                suite_execution["job_id"] = job_id
                                suite_execution["error_message"] = None
                            else:
                                suite_execution["job_id"] = None

                    catalog_execution.state = JobStatusType.IN_PROGRESS
                    catalog_execution.started_date = get_current_time()
                else:
                    logger.info("Skipping Release: {} Build-number: {}".format(catalog_execution.release_train,
                                                                               catalog_execution.build_number))

            else:
                error_message = "{}: Unable determine build number for {}".format(catalog_execution,
                                                                                  catalog_execution.release_train)
                catalog_execution.error_message = error_message
                logger.exception(error_message)

            catalog_execution.save()

    def process_in_progress_releases(self):
        q = Q(deleted=False, state=JobStatusType.IN_PROGRESS)
        catalog_executions = ReleaseCatalogExecution.objects.filter(q)
        for catalog_execution in catalog_executions:
            logger.info("{}: Processing in progress release".format(catalog_execution))
            for suite_execution in catalog_execution.suite_executions:
                valid_job_parameters = True
                if not suite_execution["test_bed_name"]:

                    valid_job_parameters = False
                    suite_execution["error_message"] = "Test-bed is invalid"
                    logger.error('{}: SuID: {} Test-bed is invalid'.format(catalog_execution, suite_execution["suite_id"]))

                if valid_job_parameters:
                    if not suite_execution["job_id"] or \
                            ("re_run_request_submitted" in suite_execution
                             and suite_execution["re_run_request_submitted"]):
                        existing_job_id = None
                        if suite_execution["job_id"]:
                            existing_job_id = suite_execution["job_id"]
                        job_id = self.queue_job(catalog_execution=catalog_execution,
                                                suite_execution=suite_execution,
                                                release_train=catalog_execution.release_train,
                                                build_number=catalog_execution.build_number)
                        suite_execution["job_id"] = job_id
                        if existing_job_id:
                            if "run_history" not in suite_execution:
                                suite_execution["run_history"] = []
                            existing_job = SuiteExecution.objects.get(execution_id=existing_job_id)
                            suite_execution["run_history"].append({"job_id": existing_job_id,
                                                                   "job_result": existing_job.result})
                        suite_execution["re_run_request_submitted"] = False
                        suite_execution["error_message"] = None
                else:
                    logger.error('{}: SuID: {} is invalid'.format(catalog_execution, suite_execution["suite_id"]))
            catalog_execution.save()

        # Prepare to change the state of the release
        for catalog_execution in catalog_executions:
            job_ids = []
            for suite_execution in catalog_execution.suite_executions:
                if suite_execution["job_id"]:
                    job_ids.append(suite_execution["job_id"])

            job_results = []
            if job_ids:
                num_completed_jobs = 0
                for job_id in job_ids:
                    s = SuiteExecution.objects.get(execution_id=job_id)
                    if JobStatusType.is_completed(s.state):
                        num_completed_jobs += 1
                        time.sleep(60) # TODO: Result may not be available for a while
                        s = SuiteExecution.objects.get(execution_id=job_id)
                        job_results.append(s.result)
                if len(job_ids) == num_completed_jobs:
                    catalog_execution.state = JobStatusType.COMPLETED
                    catalog_execution.completion_date = get_current_time()
                if len(job_ids) == len(job_results):
                    if all(map(lambda x: x == RESULTS["PASSED"], job_results)):
                        catalog_execution.result = RESULTS["PASSED"]
                        if catalog_execution.update_last_good_build:
                            LastGoodBuild.set(release_train=catalog_execution.release_train,
                                              build_number=catalog_execution.build_number,
                                              release_catalog_execution_id=catalog_execution.id)
                    else:
                        catalog_execution.result = RESULTS["FAILED"]
                    logger.info("{}: Setting result: {}".format(catalog_execution, catalog_execution.result))
            catalog_execution.save()

    def clone_execution(self, execution):
        execution_object = ReleaseCatalogExecution.objects.get(id=execution.id)
        new_execution = execution_object
        new_execution.pk = None
        new_execution.id = None
        return new_execution

    def re_spawn(self, catalog_execution):
        new_catalog_execution = self.clone_execution(catalog_execution)
        new_catalog_execution.created_date = get_current_time()
        new_catalog_execution.completion_date = get_current_time()
        new_catalog_execution.started_date = get_current_time()
        new_catalog_execution.result = RESULTS["UNKNOWN"]
        new_catalog_execution.ready_for_execution = True
        new_catalog_execution.master_execution_id = catalog_execution.id
        new_catalog_execution.update_last_good_build = catalog_execution.update_last_good_build
        new_catalog_execution.recurring = False
        for suite_execution in new_catalog_execution.suite_executions:
            suite_execution["job_id"] = None
            suite_execution["build_number"] = None
        new_catalog_execution.state = JobStatusType.SUBMITTED
        new_catalog_execution.save()

    def process_recurring_releases(self):
        q = Q(deleted=False, state=JobStatusType.COMPLETED, recurring=True)
        catalog_executions = ReleaseCatalogExecution.objects.filter(q)
        for catalog_execution in catalog_executions:
            if (catalog_execution.state > JobStatusType.UNKNOWN) and (catalog_execution.state <= JobStatusType.COMPLETED):
                q2 = Q(deleted=False,
                       state__gt=JobStatusType.COMPLETED,
                       recurring=False,
                       master_execution_id=catalog_execution.id)
                recurrent_catalog_executions = ReleaseCatalogExecution.objects.filter(q2)
                if not recurrent_catalog_executions.count():
                    logger.info("{}: Re-spawning ".format(catalog_execution))
                    self.re_spawn(catalog_execution=catalog_execution)

    def run(self):
        self.process_submitted_releases()
        self.process_in_progress_releases()
        self.process_recurring_releases()


if __name__ == "__main__":
    while True:
        daemon = Daemon.get(name=DAEMON_NAME)
        daemon.beat()
        CatalogExecutionStateMachine().run()
        time.sleep(15)
        logger.setLevel(daemon.logging_level)