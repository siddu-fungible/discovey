from lib.system.fun_test import *
from lib.utilities.jenkins_manager import JenkinsManager
from lib.host.lsf_status_server import LsfStatusServer
from web.fun_test.models_helper import update_suite_execution
import re
from fun_settings import TEAM_REGRESSION_EMAIL


class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""

        1. Step 1
        2. Step 2
        3. Step 3""")

    def setup(self):
        fun_test.log("Script-level setup")
        self.lsf_status_server = LsfStatusServer()
        fun_test.shared_variables["lsf_status_server"] = self.lsf_status_server

    def cleanup(self):
        fun_test.log("Script-level cleanup")


class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Functionality NFA",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        fun_test.log("Testcase setup")

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        fun_test.add_checkpoint("Some checkpoint")
        jenkins_manager = JenkinsManager()
        boot_args = "app=pm_test_bootstrap param-file=nightly_nfa_H_dflt_h_dflt_nfa.json rbm-size=1m syslog=2 --disable-wu-watchdog"
        funos_makeflags = "PM_TESTS=1 XDATA_LISTS=/project/users/jlulla/sanity_runtime/jenkins.list"
        max_duration = 5
        tags = "qa_rgx_nfa_runtime_sanity"
        params = {"BOOTARGS": boot_args,
                  "FUNOS_MAKEFLAGS": funos_makeflags,
                  "MAX_DURATION": max_duration,
                  "RUN_MODE": "Batch",
		  "NOTE": "RGX NFA strategy",
                  "FAST_EXIT": "False",
                  "TAGS": tags}

        build_result = jenkins_manager.build(params=params, extra_emails=[
            "john.abraham@fungible.com,team-regression@fungible.com,jitendra.lulla@fungible.com,renat.idrisov@fungible.com,ed.wimmers@fungible.com,indrani.p@fungible.com "],
                                             wait_time_for_build_complete=25 * 60)
        fun_test.test_assert(build_result, "Build completed normally")
        fun_test.test_assert_expected(actual=build_result.lower(), expected="success", message="Successfully built")


class FunTestCase2(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Functionality DFA",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        fun_test.log("Testcase setup")

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        fun_test.add_checkpoint("Some checkpoint")
        jenkins_manager = JenkinsManager()
        boot_args = "app=pm_test_bootstrap param-file=nightly_dfa_B_dflt_b_dflt_dfa.json rbm-size=1m syslog=2 --disable-wu-watchdog"
        funos_makeflags = "PM_TESTS=1 XDATA_LISTS=/project/users/jlulla/sanity_runtime/jenkins.list"
        max_duration = 5
        tags = "qa_rgx_dfa_runtime_sanity"
        params = {"BOOTARGS": boot_args,
                  "FUNOS_MAKEFLAGS": funos_makeflags,
                  "MAX_DURATION": max_duration,
                  "RUN_MODE": "Batch",
		  "NOTE": "RGX DFA strategy",
                  "FAST_EXIT": "False",
                  "TAGS": tags}

        build_result = jenkins_manager.build(params=params, extra_emails=[
            "john.abraham@fungible.com,team-regression@fungible.com,jitendra.lulla@fungible.com,renat.idrisov@fungible.com,ed.wimmers@fungible.com,indrani.p@fungible.com "],
                                             wait_time_for_build_complete=25 * 60)
        fun_test.test_assert(build_result, "Build completed normally")
        fun_test.test_assert_expected(actual=build_result.lower(), expected="success", message="Successfully built")


class FunTestCase3(FunTestCase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Functionality Combined",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        fun_test.log("Testcase setup")

    def cleanup(self):
        fun_test.log("Testcase cleanup")

    def run(self):
        fun_test.add_checkpoint("Some checkpoint")
        jenkins_manager = JenkinsManager()
        boot_args = "app=pm_test_bootstrap param-file=nightly_combined_H_dflt_h_dflt_combined.json rbm-size=1m syslog=2 --disable-wu-watchdog"
        funos_makeflags = "PM_TESTS=1 XDATA_LISTS=/project/users/jlulla/sanity_runtime/jenkins.list"
        max_duration = 5
        tags = "qa_rgx_software_runtime_sanity"
        params = {"BOOTARGS": boot_args,
                  "FUNOS_MAKEFLAGS": funos_makeflags,
                  "MAX_DURATION": max_duration,
                  "RUN_MODE": "Batch",
		  "NOTE": "RGX FFA strategy",
                  "FAST_EXIT": "False",
                  "TAGS": tags}

        build_result = jenkins_manager.build(params=params, extra_emails=[
            "john.abraham@fungible.com,team-regression@fungible.com,jitendra.lulla@fungible.com,renat.idrisov@fungible.com,ed.wimmers@fungible.com,indrani.p@fungible.com "],
                                             wait_time_for_build_complete=25 * 60)
        fun_test.test_assert(build_result, "Build completed normally")
        fun_test.test_assert_expected(actual=build_result.lower(), expected="success", message="Successfully built")

class RetrieveLogLinesCase1(FunTestCase):
    tag = "qa_rgx_nfa_runtime_sanity"
    result = fun_test.FAILED

    def __init__(self, **kwargs):
        super(RetrieveLogLinesCase1, self).__init__(**kwargs)
        self.tag = kwargs.get("tag")

    def describe(self):
        self.set_test_details(id=4,
                              summary="RetrieveLogLinesCase1",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        self.lsf_status_server = fun_test.shared_variables["lsf_status_server"]

    def validate_job(self, validation_required=True):
        job_info = self.lsf_status_server.get_last_job(tag="qa_rgx_nfa_runtime_sanity")
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

class RetrieveLogLinesCase2(FunTestCase):
    tag = "qa_rgx_dfa_runtime_sanity"
    result = fun_test.FAILED

    def __init__(self, **kwargs):
        super(RetrieveLogLinesCase2, self).__init__(**kwargs)
        self.tag = kwargs.get("tag")

    def describe(self):
        self.set_test_details(id=5,
                              summary="RetrieveLogLinesCase2",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        self.lsf_status_server = fun_test.shared_variables["lsf_status_server"]

    def validate_job(self, validation_required=True):
        job_info = self.lsf_status_server.get_last_job(tag="qa_rgx_dfa_runtime_sanity")
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

class RetrieveLogLinesCase3(FunTestCase):
    tag = "qa_rgx_software_runtime_sanity"
    result = fun_test.FAILED

    def __init__(self, **kwargs):
        super(RetrieveLogLinesCase3, self).__init__(**kwargs)
        self.tag = kwargs.get("tag")

    def describe(self):
        self.set_test_details(id=6,
                              summary="RetrieveLogLinesCase3",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        self.lsf_status_server = fun_test.shared_variables["lsf_status_server"]

    def validate_job(self, validation_required=True):
        job_info = self.lsf_status_server.get_last_job(tag="qa_rgx_software_runtime_sanity")
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


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.add_test_case(FunTestCase2())
    myscript.add_test_case(FunTestCase3())
    myscript.add_test_case(RetrieveLogLinesCase1())
    myscript.add_test_case(RetrieveLogLinesCase2())
    myscript.add_test_case(RetrieveLogLinesCase3())
    myscript.run()
