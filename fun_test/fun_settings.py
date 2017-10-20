from os.path import dirname, abspath
import sys

FUN_TEST_DIR = dirname(abspath(__file__))
WEB_DIR = FUN_TEST_DIR + "/web"
STATIC_RELATIVE_DIR = "/static"
UPLOADS_RELATIVE_DIR = STATIC_RELATIVE_DIR + "/uploads"
WEB_STATIC_DIR = WEB_DIR + STATIC_RELATIVE_DIR
WEB_UPLOADS_DIR = WEB_DIR + UPLOADS_RELATIVE_DIR
LOGS_DIR = WEB_STATIC_DIR + "/logs"
LOGS_RELATIVE_DIR = STATIC_RELATIVE_DIR + "/logs"
WEB_SERVER_PORT = 5000

ASSET_DIR = FUN_TEST_DIR + "/asset"
JOBS_DIR = WEB_STATIC_DIR + "/jobs"

SCRIPTS_DIR = FUN_TEST_DIR + "/scripts"

DOCKER_REMOTE_API_PORT = 4243

JIRA_URL = "http://jira.fungible.local"
TCMS_PROJECT = "TCM"


sys.path.append(WEB_DIR)
