
from lib.system.fun_test import *
from lib.utilities.jenkins_manager import JenkinsManager
from lib.host.lsf_status_server import LsfStatusServer
from lib.system import utils
from fun_settings import DATA_STORE_DIR
import regex_helper

tags = ""
test_result = True



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


class HigherLevelTestcase(FunTestCase):

    def describe(self):
        pass

    def setup(self):
        testcase = self.__class__.__name__
        fun_test.log("Testcase setup")

        testcase_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("json file being used: {}".format(testcase_file))
        testcase_dict = utils.parse_file_to_json(testcase_file)

        for k, v in testcase_dict[testcase].iteritems():
            setattr(self, k, v)

    def run(self):
        fun_test.add_checkpoint("Starting checkpoint")
        lsf_status_server = fun_test.shared_variables["lsf_status_server"]
        data_store_dir = DATA_STORE_DIR

        jenkins_manager = JenkinsManager()
        funos_makeflags = "PM_TESTS=1 XDATA_LISTS=" + self.XDATA_LISTS
        global tags
        print "All jsons: ", self.jsons
        for jsn in self.jsons:
            print "params json:", jsn
            note = self.description + " " + self.XDATA_LISTS + " JSON: " + jsn
            boot_args = "app=pm_test_bootstrap rbm-size=" + self.rbm_size + " param-file=" \
                        + jsn + " --disable-wu-watchdog --bm-profile-regex syslog=" + self.syslog_level
            tags = str(fun_test.get_wall_clock_time())
            print "TAGS:", tags
            params = {
                "BOOTARGS": boot_args,
                "FUNOS_MAKEFLAGS": funos_makeflags,
                "RUN_TARGET": self.run_target,
                "HW_MODEL": self.hw_model,
                "HW_VERSION": self.hw_version,
                "BRANCH_FunOS": self.funos_branch,
                "MAX_DURATION": self.max_duration,
                "RUN_MODE": "Batch",
                "NOTE": note,
                "FAST_EXIT": "True",
                "TAGS": tags
            }

            build_result = jenkins_manager.build(params=params, extra_emails=[
                "indrani.p@fungible.com"],
                                                 wait_time_for_build_complete=25 * 60)
            fun_test.test_assert(build_result, "Build completed normally: for Graphs in {}".format(json))
            fun_test.test_assert_expected(actual=build_result.lower(), expected="success", message="Successfully built")
            try:
                job_dir = regex_helper.validate_job(lsf_status_server, tags)
                fun_test.test_assert(job_dir, "Validate job")
            except Exception as e:
                print e, "\n"

            test_result = regex_helper.validate_rgx_result(data_store_dir, job_dir, num_polls=50, private_run=False)
            try:
                fun_test.test_assert(test_result, "Validate matches for graphs in {}".format(json))
            except Exception as e:
                print e, "\n"


            try:
                fun_test.test_assert(test_result, self.summary)
            except:
                pass
            # fun_test.sleep("Waiting 60s before launching another build ...", 60)

    def cleanup(self):
        fun_test.log("Testcase cleanup")


class Pcre1DfaRuntime(HigherLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="F1:Runtime: FFA Graphs, default args",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        super(Pcre1DfaRuntime, self).setup()

    def run(self):
        super(Pcre1DfaRuntime, self).run()

    def cleanup(self):
        super(Pcre1DfaRuntime, self).cleanup()

class Pcre1DfaMatchAcrossPackets(HigherLevelTestcase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="F1:Runtime: match across packets FFA Graphs, default args",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        super(Pcre1DfaMatchAcrossPackets, self).setup()

    def run(self):
        super(Pcre1D`faMatchAcrossPackets, self).run()

    def cleanup(self):
        super(Pcre1DfaMatchAcrossPackets, self).cleanup()


class Pcre1DfaRuntimeSerial1(HigherLevelTestcase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="F1:Runtime: Serial1 FFA Graphs, default args",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        super(Pcre1DfaRuntimeSerial1, self).setup()

    def run(self):
        super(Pcre1DfaRuntimeSerial1, self).run()

    def cleanup(self):
        super(Pcre1DfaRuntimeSerial1, self).cleanup()

class Pcre1DfaRuntimeSerial2(HigherLevelTestcase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="F1:Runtime: Serial2 FFA Graphs, default args",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        super(Pcre1DfaRuntimeSerial2, self).setup()

    def run(self):
        super(Pcre1DfaRuntimeSerial2, self).run()

    def cleanup(self):
        super(Pcre1DfaRuntimeSerial2, self).cleanup()



if __name__ == "__main__":
    myscript = MyScript()

    myscript.add_test_case(Pcre1DfaRuntime())
    myscript.add_test_case(Pcre1DfaMatchAcrossPackets())
    myscript.add_test_case(Pcre1DfaRuntimeSerial1())
    myscript.add_test_case(Pcre1DfaRuntimeSerial2())
    myscript.run()

