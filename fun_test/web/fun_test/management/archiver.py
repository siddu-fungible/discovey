"""
Archive old suite files
"""
from fun_global import get_current_time
from web.fun_test.django_interactive import *
from web.fun_test.models import SuiteExecution, RegresssionScripts
from fun_settings import LOGS_DIR
from django.core.exceptions import ObjectDoesNotExist
from scheduler.scheduler_global import JobStatusType

import logging
import logging.handlers
import glob
import os
import sys
import tarfile
import shutil

logger = logging.getLogger("archiver_log")
logger.setLevel(logging.DEBUG)

TEN_MB = 1e7
DEBUG = False

if len(sys.argv) > 1:
    DEBUG = sys.argv[1]
LOG_FILE_NAME = "archiver.log.txt"

if not DEBUG:
    handler = logging.handlers.RotatingFileHandler(LOG_FILE_NAME, maxBytes=TEN_MB, backupCount=5)
else:
    handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(hdlr=handler)


"""
Policies:
1. Mark directories older than KEEP_SUITE_DAYS for archiving
2. Exclude suites used as baseline 
"""

ARCHIVE_DIRECTORY = "/project/users/QA/regression/data_store/jobs_backup"
RECOVERY_DIRECTORY = ARCHIVE_DIRECTORY + "/recovery"

if not os.path.exists(ARCHIVE_DIRECTORY):
    os.mkdir(ARCHIVE_DIRECTORY)
    logger.debug("Created archive directory: {}".format(ARCHIVE_DIRECTORY))
if not os.path.exists(RECOVERY_DIRECTORY):
    os.mkdir(RECOVERY_DIRECTORY)
    logger.debug("Created recovery directory: {}".format(RECOVERY_DIRECTORY))

KEEP_SUITE_DAYS = 1 * 30
files = glob.glob(LOGS_DIR + "/s_*")
suites_that_do_not_exist = []

s = RegresssionScripts.objects.all().values('baseline_suite_execution_id')
baseline_suite_execution_ids = [x['baseline_suite_execution_id'] for x in s if x['baseline_suite_execution_id'] > -1]


logger.debug("Baseline execution IDs")
for baseline_suite_execution_id in baseline_suite_execution_ids:
    logger.debug(baseline_suite_execution_id)


def move_directory(source):
    try:
        shutil.move(src=source, dst=RECOVERY_DIRECTORY + "/")
    except Exception as ex:
        print ("Move directory: {}".format(str(ex)))

for file in files:
    try:
        suite_execution_id = file.replace(LOGS_DIR, "").replace("/s_", "")
        suite_execution_id = int(suite_execution_id)
    except Exception as ex:
        print "Unable to parse: {}".format(file)
        continue
    if suite_execution_id in baseline_suite_execution_ids:
        logger.debug("Skipping {} as it is a baseline".format(suite_execution_id))
        continue
    try:
        s = SuiteExecution.objects.get(execution_id=suite_execution_id)
        if ((get_current_time() - s.completed_time).days > KEEP_SUITE_DAYS) and (s.state != JobStatusType.IN_PROGRESS):
            if not DEBUG:
                # print s.completed_time
                tgz_file_name = ARCHIVE_DIRECTORY + "/s_{}.tgz".format(suite_execution_id)
                tar = tarfile.open(tgz_file_name, "w:gz")
                tar.add(file, arcname="s_{}".format(suite_execution_id))
                tar.close()

                move_directory(source=file)
                logger.debug("Created {}".format(tgz_file_name))
            else:
                logger.debug("Candidate: {}".format(file))

    except ObjectDoesNotExist:
        suites_that_do_not_exist.append(suite_execution_id)
        if not DEBUG:
            move_directory(source=file)


logger.debug("Non-existing suites")
for non_existing_suite in suites_that_do_not_exist:
    logger.debug(non_existing_suite)
