from lib.system.fun_test import *
from lib.utilities.jenkins_manager import JenkinsManager
from lib.host.lsf_status_server import LsfStatusServer


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


class ChannelParallTC(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Schedule Channel parall app on Jenkins",
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
        fun_test.add_checkpoint("Starting the jenkins build")
        jenkins_manager = JenkinsManager()
        boot_args = "app=channel_parall_speed"
        max_duration = 5
        tags = "qa_channel_parall"
        params = {"BOOTARGS": boot_args,
                  "MAX_DURATION": max_duration,
                  "RUN_MODE": "Batch",
                  "TAGS": tags,
                  "NOTE": "channel parall app",
                  "DISABLE_ASSERTIONS": "true"}

        build_result = jenkins_manager.build(params=params, extra_emails=[
            "team-regression@fungible.com"],
                                             wait_time_for_build_complete=25 * 60)
        fun_test.test_assert(build_result, "Build completed normally")
        fun_test.test_assert_expected(actual=build_result.lower(), expected="success", message="Successfully built")


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(ChannelParallTC())
    myscript.run()
