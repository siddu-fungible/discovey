"""
Archive old suite files
"""
from fun_global import get_current_time
from web.fun_test.django_interactive import *
from web.fun_test.models import SuiteExecution, RegresssionScripts
from fun_settings import LOGS_DIR
from django.core.exceptions import ObjectDoesNotExist


import glob
import os
import tarfile

"""
Policies:
1. Mark directories older than KEEP_SUITE_DAYS for archiving
2. Exclude suites used as baseline 
"""

ARCHIVE_DIRECTORY = "/tmp/archives"

KEEP_SUITE_DAYS = 1 * 30

files = glob.glob(LOGS_DIR + "/s_*")
suites_that_do_not_exist = []

s = RegresssionScripts.objects.all().values('baseline_suite_execution_id')
baseline_suite_execution_ids = [x['baseline_suite_execution_id'] for x in s if x['baseline_suite_execution_id'] > -1]

for baseline_suite_execution_id in baseline_suite_execution_ids:
    print baseline_suite_execution_id


for file in files:
    suite_execution_id = file.replace(LOGS_DIR, "").replace("/s_", "")
    suite_execution_id = int(suite_execution_id)
    if suite_execution_id in baseline_suite_execution_ids:
        print "Skipping {} as it is a baseline".format(suite_execution_id)
        continue
    try:
        s = SuiteExecution.objects.get(execution_id=suite_execution_id)
        if (get_current_time() - s.completed_time).days > KEEP_SUITE_DAYS:
            # print s.completed_time
            tgz_file_name = ARCHIVE_DIRECTORY + "/s_{}.tgz".format(suite_execution_id)
            tar = tarfile.open(tgz_file_name, "w:gz")
            tar.add(file, arcname="s_{}".format(suite_execution_id))
            tar.close()
            print "Created {}".format(tgz_file_name)

    except ObjectDoesNotExist:
        suites_that_do_not_exist.append(suite_execution_id)


print "Non-existing suites"
for non_existing_suite in suites_that_do_not_exist:
    print non_existing_suite