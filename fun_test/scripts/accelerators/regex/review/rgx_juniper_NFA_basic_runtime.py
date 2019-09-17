from lib.system.fun_test import *
from lib.utilities.jenkins_manager import JenkinsManager
from lib.host.lsf_status_server import LsfStatusServer
from web.fun_test.models_helper import update_suite_execution
from lib.system import utils
import os, re
from fun_settings import DATA_STORE_DIR
from fun_settings import TEAM_REGRESSION_EMAIL

tags = ""
test_result = True

def validate_job(self, validation_required=True):
    #fun_test.sleep("Waiting 240 before fetching last job info ...", 240)
    self.lsf_status_server = fun_test.shared_variables["lsf_status_server"]
    print "self.lsf_status_server: ", self.lsf_status_server

    #job_resp = self.lsf_status_server.get_current_jobdir_by_tag(tag=tags)
    job_resp = self.lsf_status_server.get_jobs_by_tag(tag=tags)
    job_info = json.loads(job_resp)
    print "job_info:", type(job_info), job_info
    if job_info["past_jobs"] != []:
        self.job_dir = job_info['past_jobs'][0]['job_dir']
    else:
        self.job_dir = job_info['running_jobs'][0]['job_dir']
    fun_test.log("job directory:" + self.job_dir)
    return True


def validate_rgx_result(self):
    print "data store:", DATA_STORE_DIR
    test_result = True
    #funos_logs_file = DATA_STORE_DIR+"/funos_logs.txt"
    funos_logs_file = DATA_STORE_DIR+"/"+self.job_dir.split("/")[-1]+".txt"
    #file_name = self.job_dir+"/mail.txt"

    while not os.path.exists(funos_logs_file):
        fun_test.sleep("waiting as the file is not created",5)
    with open(funos_logs_file, "r") as f_in:
        log_data = f_in.read()
    try:
        action_seq = re.findall('(?:ACTION SEQUENCE\s.*)', log_data)
        fun_test.test_assert(len(action_seq) != 0, "Action sequence found in FunOS logs")
        for action in action_seq:
            all_bad_searches = re.findall("\(search\).*but.*", log_data)
            all_loads = re.findall("\(load\).*:.*", log_data)
            all_unloads = re.findall("\(unload\).*:.*", log_data)
            errors_count=re.findall(".*?Error\s*?\(status\s*?\d+\)")

            all_responses = ""
            for i in all_loads:
                all_responses = all_responses + i + "\n"
            try:
                fun_test.test_assert(1, "LOADS: " + all_responses)
            except:
                pass

            all_responses = ""
            for i in all_bad_searches:
                all_responses = all_responses + i + "\n"
            try:
                fun_test.test_assert(0, "SEARCHES: " + all_responses)
            except:
                pass

            all_responses = ""
            for i in all_unloads:
                all_responses = all_responses + i + "\n"
            try:
                fun_test.test_assert(1, "ULOADS: " + all_responses)
            except:
                pass

            action_id = re.search("ACTION SEQUENCE (\d+)", action).group(1)
            pass_num = re.search("PASS (\d+)", action).group(1)
            fail_num = re.search("FAIL (\d+)", action).group(1)
            mismatch_num = re.search("MISMATCHES (\d+)", action).group(1)

            try:
                fun_test.test_assert(int(pass_num) > 0, "Sequence: {}; Pass number: {}".format(action_id, pass_num))
            except:
                pass
            try:
                fun_test.test_assert(int(fail_num) == 0, "Sequence: {}; Fail number: {}".format(action_id, fail_num))
            except:
                test_result = False
                pass
            try:
                fun_test.test_assert(int(mismatch_num) == 0, "Sequence: {}; Mismatch number: {}".format(action_id, mismatch_num))
            except:
                test_result = False
                pass
            try:
                fun_test.test_assert(len(errors_count)==0,"Errors count :{}".format(len(errors_count)))
            except:
                test_result=False
    except:
        test_result = False
        try:
            fun_test.test_assert(test_result, "found ACTION_SEQUENCE or PASS/FAIL/MISMATCHES in log data")
        except:
            pass

    if not test_result:
        return False

    return True


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
        self.my_shared_variables = {}
        self.my_shared_variables["lsf_status_server"] = fun_test.shared_variables["lsf_status_server"]
        jenkins_manager = JenkinsManager()
        funos_makeflags = "PM_TESTS=1 XDATA_LISTS=" + self.XDATA_LISTS
        rbm_size = self.rbm_size
        max_duration = 10
        global tags
        print "All jsons: ", self.jsons
        for json in self.jsons:
            print "json:", json
            note = self.description + " " + self.XDATA_LISTS + " JSON: " + json
            boot_args = "app=pm_test_bootstrap rbm-size=" + rbm_size + " param-file=" + json + " --disable-wu-watchdog --bm-profile-regex syslog=3"
            tags = str(fun_test.get_wall_clock_time())
            print "TAGS:", tags
            params = {
                "BOOTARGS": boot_args,
                "FUNOS_MAKEFLAGS": funos_makeflags,
                "MAX_DURATION": max_duration,
                "RUN_MODE": "Batch",
                "NOTE": note,
                "FAST_EXIT": "True",
                "TAGS": tags,
                "BRANCH_FunOS": "nfa_s1_upgrade"
            }

            build_result = jenkins_manager.build(params=params, extra_emails=[
                "indranip@funigble.com"],
                                                 wait_time_for_build_complete=25 * 60)
            fun_test.test_assert(build_result, "Build completed normally: for Graphs in {}".format(json))
            fun_test.test_assert_expected(actual=build_result.lower(), expected="success", message="Successfully built")
            try:
                fun_test.test_assert(validate_job(self), "Validate job")
            except:
                pass

            test_result = validate_rgx_result(self)
            try:
                fun_test.test_assert(test_result, "Validate matches for graphs in {}".format(json))
            except:
                pass

            try:
                fun_test.test_assert(test_result, self.summary)
            except:
                pass
            fun_test.sleep("Waiting 60s before launching another build ...", 60)

    def cleanup(self):
        fun_test.log("Testcase cleanup")


class JuniperNFA_Basic_Runtime(HigherLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="JUNIPER NFA basic runtime",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        super(JuniperNFA_Basic_Runtime, self).setup()

    def run(self):
        super(JuniperNFA_Basic_Runtime, self).run()

    def cleanup(self):
        super(JuniperNFA_Basic_Runtime, self).cleanup()


class JuniperNFA_MatchAcrossPacket(HigherLevelTestcase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="JUNIPER NFA match across packet",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        super( JuniperNFA_MatchAcrossPacket, self).setup()

    def run(self):
        super( JuniperNFA_MatchAcrossPacket, self).run()

    def cleanup(self):
        super( JuniperNFA_MatchAcrossPacket, self).cleanup()

class JuniperNFA_Sequential1(HigherLevelTestcase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="JUNIPER NFA LSU serial:loading graphs on different clusters",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        super(JuniperNFA_Sequential1, self).setup()

    def run(self):
        super(JuniperNFA_Sequential1, self).run()

    def cleanup(self):
        super(JuniperNFA_Sequential1, self).cleanup()

class JuniperNFA_Sequential2(HigherLevelTestcase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="JUNIPER NFA LSU serial:loading graphs on single cluster",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        super(JuniperNFA_Sequential2, self).setup()

    def run(self):
        super(JuniperNFA_Sequential2, self).run()

    def cleanup(self):
        super(JuniperNFA_Sequential2, self).cleanup()

class JuniperNFA_parallel1(HigherLevelTestcase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="JUNIPER NFA LSU parallel:loading graphs on different cluster",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        super(JuniperNFA_parallel1, self).setup()

    def run(self):
        super(JuniperNFA_parallel1, self).run()

    def cleanup(self):
        super(JuniperNFA_parallel1, self).cleanup()


class JuniperNFA_parallel2(HigherLevelTestcase):
    def describe(self):
        self.set_test_details(id=6,
                              summary="JUNIPER NFA LSU parallel:loading graphs on single cluster",
                              steps="""
        1. Steps 1
        2. Steps 2
        3. Steps 3
                              """)

    def setup(self):
        super(JuniperNFA_parallel2, self).setup()

    def run(self):
        super(JuniperNFA_parallel2, self).run()

    def cleanup(self):
        super(JuniperNFA_parallel2, self).cleanup()



if __name__ == "__main__":

    myscript = MyScript()

    myscript.add_test_case(JuniperNFA_Basic_Runtime())

    myscript.run()

