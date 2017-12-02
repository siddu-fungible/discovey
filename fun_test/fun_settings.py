from os.path import dirname, abspath
import sys

FUN_TEST_DIR = dirname(abspath(__file__))
SCHEDULER_DIR = FUN_TEST_DIR + "/scheduler"
WEB_DIR = FUN_TEST_DIR + "/web"
STATIC_RELATIVE_DIR = "/static"
UPLOADS_RELATIVE_DIR = STATIC_RELATIVE_DIR + "/uploads"
WEB_STATIC_DIR = WEB_DIR + STATIC_RELATIVE_DIR
WEB_UPLOADS_DIR = WEB_DIR + UPLOADS_RELATIVE_DIR
TEST_ARTIFACTS_RELATIVE_DIR = "/test_artifacts"
TEST_ARTIFACTS_DIR = WEB_STATIC_DIR + TEST_ARTIFACTS_RELATIVE_DIR
LOGS_DIR = WEB_STATIC_DIR + "/logs"
LOGS_RELATIVE_DIR = STATIC_RELATIVE_DIR + "/logs"
MEDIA_DIR = WEB_STATIC_DIR + "/media"

WEB_SERVER_PORT = 5000
COMMON_WEB_LOGGER_NAME = "web"


ASSET_DIR = FUN_TEST_DIR + "/asset"
JOBS_DIR = WEB_STATIC_DIR + "/jobs"
ARCHIVED_JOBS_DIR = JOBS_DIR + "/archived"
KILLED_JOBS_DIR = JOBS_DIR + "/killed"
SCRIPTS_DIR = FUN_TEST_DIR + "/scripts"

TEST_CASE_SPEC_DIR = SCRIPTS_DIR + "/test_case_spec"
SUITES_DIR = TEST_CASE_SPEC_DIR + "/suites"

JIRA_URL = "http://jira.fungible.local"
TCMS_PROJECT = "TCM"


SYSTEM_TMP_DIR = "/tmp"
sys.path.append(WEB_DIR)

DEFAULT_BUILD_URL = "http://dochub.fungible.local/doc/jenkins/funos/latest/"
TIME_ZONE = "America/Los_Angeles"


MAIL_SERVER = "localhost"
AUTOMATION_EMAIL = "automation@fungible.com"

SCHEDULER_PID = "/tmp/fun_test_scheduler.pid"