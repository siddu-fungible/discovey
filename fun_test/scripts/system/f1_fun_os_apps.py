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


class ChannelParallTc(FunTestCase):
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
                  "RELEASE_BUILD": "true"}

        build_result = jenkins_manager.build(params=params)
        fun_test.test_assert(build_result, "Build completed normally")


class SoakFlowsBusyLoopTc(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Schedule Soak flows busy loop app on Jenkins",
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
        boot_args = "app=soak_flows_busy_loop_10usecs"
        max_duration = 5
        tags = "qa_soak_flows_busy_loop"
        params = {"BOOTARGS": boot_args,
                  "MAX_DURATION": max_duration,
                  "RUN_MODE": "Batch",
                  "TAGS": tags,
                  "NOTE": "soak flows busy loop",
                  "RELEASE_BUILD": "true"}

        build_result = jenkins_manager.build(params=params)
        fun_test.test_assert(build_result, "Build completed normally")


class SoakFlowsMemcpy1MbNonCohTc(FunTestCase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Schedule Soak flows memcpy 64KB non coh app on Jenkins",
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
        boot_args = "app=soak_flows_memcpy_64KB_non_coh"
        max_duration = 5
        tags = "qa_soak_flows_memcpy_non_coh"
        params = {"BOOTARGS": boot_args,
                  "MAX_DURATION": max_duration,
                  "RUN_MODE": "Batch",
                  "TAGS": tags,
                  "NOTE": "soak flows memcpy 64KB non coh",
                  "RELEASE_BUILD": "true"}

        build_result = jenkins_manager.build(params=params)
        fun_test.test_assert(build_result, "Build completed normally")


if __name__ == "__main__":
    myscript = MyScript()
    myscript.add_test_case(ChannelParallTc())
    myscript.add_test_case(SoakFlowsBusyLoopTc())
    myscript.add_test_case(SoakFlowsMemcpy1MbNonCohTc())
    myscript.run()
