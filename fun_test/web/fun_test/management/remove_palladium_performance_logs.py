from fun_global import get_current_time
from web.fun_test.django_interactive import *
from web.fun_test.models import SuiteExecution, RegresssionScripts
from fun_settings import LOGS_DIR
from django.core.exceptions import ObjectDoesNotExist
import shutil

ARCHIVE_DIRECTORY = "/project/users/QA/regression/data_store/jobs_backup"
RECOVERY_DIRECTORY = ARCHIVE_DIRECTORY + "/recovery"

def move_directory(source):
    shutil.move(src=source, dst=RECOVERY_DIRECTORY + "/")

palladium_suites = SuiteExecution.objects.filter(suite_path="palladium_performance_master.json")
for palladium_suite in palladium_suites:

    if (get_current_time() - palladium_suite.completed_time).days > 6:
        suite_logs_path = LOGS_DIR + "/s_{}".format(palladium_suite.execution_id)
        print suite_logs_path
        move_directory(source=suite_logs_path)