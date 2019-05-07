from lib.system.fun_test import *
from lib.utilities.jenkins_manager import JenkinsManager
from fun_settings import TEAM_REGRESSION_EMAIL

class MyScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps=
                              """
        1. Step 1
        2. Step 2
        3. Step 3""")

    def setup(self):
        fun_test.log("Script-level setup")

    def cleanup(self):
        fun_test.log("Script-level cleanup")


class FunTestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Sanity Test 1",
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
        boot_args = "app=patmat_rt_test_two param-file=apps/nightly_nfa_H_dflt_h_dflt_nfa.json rbm-size=1m --test-exit-fast"
        funos_makeflags = "XDATA_LISTS=/project/users/jlulla/sanity_runtime/jenkins.list"
        max_duration = 5
        params = {"BOOTARGS": boot_args,
                  "FUNOS_MAKEFLAGS": funos_makeflags,
                  "MAX_DURATION": max_duration,
                  "RUN_MODE": "Batch"}

        build_result = jenkins_manager.build(params=params, extra_emails=["john.abraham@fungible.com"], wait_time_for_build_complete=25 * 60)
        fun_test.test_assert(build_result, "Build completed normally")
        fun_test.test_assert_expected(actual=build_result.lower(), expected="success", message="Successfully built")

if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(FunTestCase1())
    myscript.run()
