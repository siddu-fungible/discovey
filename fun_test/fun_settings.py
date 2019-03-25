import os
from os.path import dirname, abspath
import sys

FUN_TEST_DIR = dirname(abspath(__file__))
INTEGRATION_DIR = dirname(abspath(FUN_TEST_DIR))
SCHEDULER_DIR = FUN_TEST_DIR + "/scheduler"
WEB_DIR = FUN_TEST_DIR + "/web"
STASH_DIR = FUN_TEST_DIR + "/stash"
WEB_ROOT_DIR = WEB_DIR + "/fun_test"
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
# if "PRODUCTION_MODE" in os.environ:
#    WEB_SERVER_PORT = 80

COMMON_WEB_LOGGER_NAME = "web"


ASSET_DIR = FUN_TEST_DIR + "/asset"
JOBS_DIR = WEB_STATIC_DIR + "/jobs"
ARCHIVED_JOBS_DIR = JOBS_DIR + "/archived"
KILLED_JOBS_DIR = JOBS_DIR + "/killed"
SCRIPTS_DIR = FUN_TEST_DIR + "/scripts"
SCHEDULED_JOBS_DIR = JOBS_DIR + "/scheduled"
SCHEDULER_REQUESTS_DIR = JOBS_DIR + "/requests"

TEST_CASE_SPEC_DIR = SCRIPTS_DIR + "/test_case_spec"
SUITES_DIR = TEST_CASE_SPEC_DIR + "/suites"

JIRA_URL = "http://jira.fungible.local"
TCMS_PROJECT = "TCM"


SYSTEM_TMP_DIR = "/tmp"
sys.path.append(WEB_DIR)

DOCKHUB_FUNGIBLE_LOCAL = "10.1.20.99"
DEFAULT_BUILD_URL = "http://{}/doc/jenkins/funsdk/latest".format(DOCKHUB_FUNGIBLE_LOCAL)
TIME_ZONE = "America/Los_Angeles"


MAIL_SERVER = "localhost"
REGRESSION_EMAIL = "regression@fungible.com"
TEAM_REGRESSION_EMAIL = "team-regression@fungible.com"

SCHEDULER_PID = "/tmp/fun_test_scheduler.pid"

REGRESSION_USER = "regression"
REGRESSION_USER_PASSWORD = "R3gr35510n123"

MAIN_WEB_APP = 'fun_test'

TFTP_SERVER = "10.1.21.48"