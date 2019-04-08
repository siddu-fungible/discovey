from lib.system.fun_test import *
from lib.host.lsf_status_server import LsfStatusServer
from web.fun_test.models_helper import update_suite_execution
import re

TERAMARK_CRYPTO = "crypto_teramark"


class PalladiumAppParserScript(FunTestScript):

    def __init__(self, **kwargs):
        super(PalladiumAppParserScript, self).__init__()
        self.tag = kwargs.get("tag")

    def describe(self):
        self.set_test_details(steps=
                              """
        1. Step 1
        2. Step 2""")

    def setup(self):
        self.lsf_status_server = LsfStatusServer()
        tags = [self.tag]
        self.lsf_status_server.workaround(tags=tags)
        fun_test.shared_variables["lsf_status_server"] = self.lsf_status_server

    def cleanup(self):
        pass


class RetrieveLogLinesCase(FunTestCase):
    tag = TERAMARK_CRYPTO
    result = fun_test.FAILED

    def __init__(self, **kwargs):
        super(RetrieveLogLinesCase, self).__init__(**kwargs)
        self.tag = kwargs.get("tag")

    def describe(self):
        self.set_test_details(id=1,
                              summary="RetrieveLogLinesCase",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        self.lsf_status_server = fun_test.shared_variables["lsf_status_server"]

    def validate_job(self, validation_required=True):
        job_info = self.lsf_status_server.get_last_job(tag=self.tag)
        fun_test.test_assert(job_info, "Ensure Job Info exists")
        self.jenkins_job_id = job_info["jenkins_build_number"]
        self.job_id = job_info["job_id"]
        self.git_commit = job_info["git_commit"]
        self.git_commit = self.git_commit.replace("https://github.com/fungible-inc/FunOS/commit/", "")
        if validation_required:
            fun_test.test_assert(not job_info["return_code"], "Valid return code")
            fun_test.test_assert("output_text" in job_info, "output_text found in job info: {}".format(self.job_id))
        lines = job_info["output_text"].split("\n")
        dt = job_info["date_time"]
        self.job_info = job_info
        self.lines = lines
        try:
            for line in lines:
                m = re.search(r'Version=bld_(\d+)', line)
                if m:
                    this_version = int(m.group(1))
                    fun_test.set_version(version=this_version)
                    update_suite_execution(suite_execution_id=fun_test.suite_execution_id, version=this_version)
                    break
        except Exception as ex:
            fun_test.critical("Unable to update version: {}".format(str(ex)))
            # Not expected to work in a local setup
            pass
        self.dt = dt
        fun_test.shared_variables["lines"] = lines
        return True

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        fun_test.test_assert(self.validate_job(), "Validate job")
        fun_test.log("Lines")
        for line in self.lines:
            fun_test.log(line)
