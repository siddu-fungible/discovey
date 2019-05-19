from fun_global import RESULTS
import web.fun_test.django_interactive
from web.fun_test.triaging_global import TriagingStates, TriageTrialStates, TriagingTypes
from web.fun_test.metrics_models import TriagingResult
from web.fun_test.metrics_models import Triage3, Triage3Trial
from lib.host.lsf_status_server import LsfStatusServer

from fun_global import get_current_time
import time
import sys
from lib.utilities.git_utilities import GitManager
from lib.utilities.jenkins_manager import JenkinsManager
import logging
import logging.handlers
from threading import Thread
import re

logger = logging.getLogger("triaging_logger")
logger.setLevel(logging.DEBUG)
logger.propagate = False
LOG_FILE_NAME = "triaging_log.txt"

TEN_MB = 1e7
DEBUG = False

if not DEBUG:
    handler = logging.handlers.RotatingFileHandler(LOG_FILE_NAME, maxBytes=TEN_MB, backupCount=5)
else:
    handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(hdlr=handler)


class FunTimer:
    def __init__(self, max_time=10000):
        self.max_time = max_time
        self.start_time = time.time()

    def start(self):
        self.start_time = time.time()

    def is_expired(self):
        return (self.elapsed_time()) > self.max_time

    def elapsed_time(self):
        current_time = time.time()
        return current_time - self.start_time

    def remaining_time(self):
        return (self.start_time + self.max_time) - time.time()

# Trial set: a set of git trials.
# Each set has a from: fun os sha and and to: fun os sha
# from: usually indicates the sha where the score was good (or the run was a Pass)
# to: usually indicates the sha where the score indicated a degrade (or the run was a Fail)
# one trial is one execution instance of a fun_os_sha on the execution environment
# in one trial set we execute multiple trials. The fun_os_sha for each trial is selected
#

class Test1(Thread):
    def __init__(self, triage_id):
        super(Test1, self).__init__()
        self.triage_id = triage_id

    def run(self):
        t = Triage3.objects.get(triage_id=self.triage_id)
        current_trial_set_id = t.current_trial_set_id
        ft = FunTimer(max_time=20)
        new_set_timer = FunTimer(max_time=60)

        while True:
            trials = Triage3Trial.objects.filter(triage_id=t.triage_id, trial_set_id=current_trial_set_id)
            for trial in trials:
                if not ft.is_expired():
                    trial.status = TriageTrialStates.BUILDING_ON_JENKINS
                    trial.save()
                else:
                    trial.status = TriageTrialStates.COMPLETED
                    trial.save()
                if new_set_timer.is_expired():
                    t.current_trial_set_id = t.current_trial_set_id + 1
                    t.save()
                    new_set_timer.start()
            time.sleep(5)

def long_to_short_sha(long_sha):
    return long_sha[:7]

class TriageStateMachine:
    STEP = 4

    def __init__(self, triage):
        self.triage_id = triage.triage_id
        self.set_all_commits()

    def error(self, message):
        s = "{}: {}".format(self._get_triage_string(), str(message))
        logger.exception(s)
        triage = self.get_triage()
        triage.status = TriagingStates.ERROR
        triage.save()

    def debug(self, message):
        s = "{}: {}".format(self._get_triage_string(), str(message))
        logger.debug(s)

    def _get_triage_string(self):
        t = self.get_triage()
        return "T: {} Set: {}".format(self.triage_id, t.current_trial_set_id)

    def get_triage(self):
        return Triage3.objects.get(triage_id=self.triage_id)

    def set_all_commits(self):
        t = self.get_triage()
        from_fun_os_sha = t.from_fun_os_sha
        to_fun_os_sha = t.to_fun_os_sha
        all_commits = GitManager().get_commits_between(from_sha=from_fun_os_sha, to_sha=to_fun_os_sha)
        all_commits.reverse()
        t.from_fun_os_sha = all_commits[0].sha  #TODO
        t.to_fun_os_sha = all_commits[-1].sha
        t.save()

        self.all_commits = all_commits
        logger.debug("This triage has {} commits".format(len(all_commits)))
        logger.debug("First commit: {}".format(str(self.all_commits[0])))
        logger.debug("Second commit: {}".format(str(self.all_commits[-1])))
        self.all_shas = [x.sha for x in self.all_commits]


    def get_trial_tag(self, base_tag, fun_os_sha):
        t = self.get_triage()
        return "{}_{}_{}".format(base_tag, t.triage_id, long_to_short_sha(fun_os_sha))

    def start_trial(self, fun_os_sha):
        t = self.get_triage()
        started = False
        if not Triage3Trial.objects.filter(triage_id=t.triage_id, fun_os_sha=fun_os_sha).exists():
            trial = Triage3Trial(fun_os_sha=fun_os_sha,
                                 triage_id=self.triage_id,
                                 trial_set_id=t.current_trial_set_id,
                                 status=TriagingStates.INIT,
                                 submission_date_time=get_current_time())
            base_tag = t.base_tag
            trial_tag = self.get_trial_tag(base_tag="qa_triage", fun_os_sha=fun_os_sha)
            trial.tag = trial_tag
            trial.save()
            logger.debug("Started trial for {}".format(fun_os_sha))
            started = True
        else:
            trial = Triage3Trial.objects.get(triage_id=t.triage_id, fun_os_sha=fun_os_sha)
            trial.trial_set_id = t.current_trial_set_id
            trial.save()
            logger.debug("Skipping trial for {} as it was already complete".format(fun_os_sha))
        return started

    def start_trial_set(self, from_fun_os_sha, to_fun_os_sha):
        # create trial sets for boundary shas and in-between shas
        # get potential list of shas to try
        logger.debug("Starting Trial set, from: {}, to: {}".format(from_fun_os_sha, to_fun_os_sha))

        for sha in self.all_shas:
            print sha
        commits_subset = self.all_shas[self.all_shas.index(from_fun_os_sha): self.all_shas.index(to_fun_os_sha) + 1]
        first_commit = commits_subset[0]
        last_commit = commits_subset[-1]

        t = self.get_triage()
        t.current_trial_from_sha = first_commit
        t.current_trial_to_sha = last_commit
        t.save()


        increment = len(commits_subset)/self.STEP
        if t.triage_type == TriagingTypes.PASS_OR_FAIL:
            increment = len(commits_subset)/2

        if not increment:
            increment = 1
        num_trials = 0
        max_trials = 8
        for commit_index in range(0, len(commits_subset), increment):
            this_commit = commits_subset[commit_index]
            logger.debug("Candidate: {}".format(str(this_commit)))
            started = self.start_trial(fun_os_sha=this_commit)
            if started:
                num_trials += 1
            if num_trials > max_trials:
                raise Exception("Too many trials")

        if not num_trials:
            pass

    def is_current_trial_set_complete(self):
        trial_count = Triage3Trial.objects.filter(triage_id=triage_id, trial_set_id=t.current_trial_set_id, status__gt=TriageTrialStates.COMPLETED)
        return trial_count == 0

    def process_trials(self):
        t = self.get_triage()
        logger.debug("Processing trials") # for trial set: {}".format(t.current_trial_set_id))
        trials = Triage3Trial.objects.filter(triage_id=t.triage_id, status__gt=TriageTrialStates.COMPLETED)
        if trials:
            for trial in trials:

                logger.debug("Processing trial: {}".format(str(trial)))
                sm = TrialStateMachine(triage_id=t.triage_id, fun_os_sha=trial.fun_os_sha)
                sm.run()
                time.sleep(1)
        else:
            logger.debug("No trials to process")
        self.next()

    def next(self):
        """
        Check if we need a new trial
        :return:
        """
        t = self.get_triage()
        if t.status > TriagingStates.COMPLETED and t.triage_type == TriagingTypes.PASS_OR_FAIL:
            completed_trials = Triage3Trial.objects.filter(triage_id=t.triage_id, trial_set_id=t.current_trial_set_id, status=TriageTrialStates.COMPLETED).order_by('-submission_date_time')
            trials_in_current_set = Triage3Trial.objects.filter(triage_id=t.triage_id, trial_set_id=t.current_trial_set_id)

            self.debug("Num trials in set: {}, completed count: {}".format(trials_in_current_set.count(),
                                                                           completed_trials.count()))

            last_pass_sha = None
            last_fail_sha = None
            if completed_trials.count() == trials_in_current_set.count():
                self.debug("Trials in set have completed ")

                for completed_trial in completed_trials:
                    pass  # Look for last pass
                    trial_result = completed_trial.result
                    if completed_trial.fun_os_sha == t.to_fun_os_sha:
                        if trial_result == RESULTS["PASSED"]:
                            self.error("The latest commit: {} actually PASSED. Please re-submit triage".format(t.to_fun_os_sha))

                    elif completed_trial.fun_os_sha == t.from_fun_os_sha:
                        if trial_result == RESULTS["FAILED"]:
                            self.error("The earliest commit: {} actually FAILED. Please re-submit triage".format(t.from_fun_os_sha))
                    else:
                        if trial_result == RESULTS["PASSED"]:
                            last_pass_sha = completed_trial.fun_os_sha
                        elif trial_result == RESULTS["FAILED"]:
                            last_fail_sha = completed_trial.fun_os_sha
                        if last_pass_sha and last_fail_sha:
                            break
                if not last_pass_sha:
                    return self.error("last pass sha not available")
                if not last_fail_sha:
                    return self.error("last fail sha not available")

                last_pass_index = self.all_shas.index(last_pass_sha)
                last_fail_index = self.all_shas.index(last_fail_sha)
                if last_fail_index < last_pass_index:
                    self.error("last fail index: {} is lesser than last pass index: {}".format(last_fail_index, last_pass_index))
                if (last_fail_index - last_pass_index) <= 1:
                    return self.complete()
                else:
                    self.start_trial_set(from_fun_os_sha=last_pass_sha, to_fun_os_sha=last_fail_sha)


    def complete(self):
        t = self.get_triage()
        t.status = TriagingStates.COMPLETED
        t.save()

    def process(self):
        t = self.get_triage()
        status = t.status

        if status == TriagingStates.INIT:
            t.current_trial_from_sha = t.from_fun_os_sha
            t.current_trial_to_sha = t.to_fun_os_sha
            t.status = TriagingStates.IN_PROGRESS
            t.save()

        elif status == TriagingStates.IN_PROGRESS:
            trials_count = Triage3Trial.objects.filter(triage_id=t.triage_id,
                                                       trial_set_id=t.current_trial_set_id).count()
            logger.debug("Active trials: {}".format(trials_count))
            if not trials_count:
                self.start_trial_set(from_fun_os_sha=t.current_trial_from_sha,
                                     to_fun_os_sha=t.current_trial_to_sha)
            else:
                self.process_trials()

    def run(self):
        self.process()


class TrialStateMachine:
    def __init__(self, triage_id, fun_os_sha):
        self.triage_id = triage_id
        self.fun_os_sha = fun_os_sha

    def error(self, message):
        s = "{}: {}".format(self._get_trial_string(), str(message))
        logger.exception(s)
        trial = self.get_trial()
        trial.status = TriageTrialStates.ERROR
        trial.save()

    def _get_trial_string(self):
        return "T: {} S: {}".format(self.triage_id, self.fun_os_sha)

    def get_trial(self):
        trial = Triage3Trial.objects.get(triage_id=self.triage_id, fun_os_sha=self.fun_os_sha)
        return trial

    def run(self):
        triage = Triage3.objects.get(triage_id=self.triage_id)
        trial = self.get_trial()
        status = trial.status
        if status == TriageTrialStates.INIT:
            jm = JenkinsManager()
            params = triage.build_parameters
            params["TAGS"] = "qa_triage," + trial.tag
            params["RUN_MODE"] = "Batch"
            params["PRIORITY"] = "low_priority"
            params["BRANCH_FunOS"] = self.fun_os_sha
            params["HW_VERSION"] = "rel_081618_svn67816_emu"
            # params["PCI_MODE"] = "root_complex"
            try:
                queue_item = jm.build(params=params)
                build_number = jm.get_build_number(queue_item=queue_item)
                trial.jenkins_build_number = build_number  #TODO: Failure here
            except Exception as ex:  #TODO
                pass
            finally:
                trial.status = TriageTrialStates.BUILDING_ON_JENKINS
            trial.save()
        elif status == TriageTrialStates.BUILDING_ON_JENKINS:
            try:
                jm = JenkinsManager()
                job_info = jm.get_job_info(build_number=trial.jenkins_build_number)
                if not job_info["building"]:
                    job_result = job_info["result"]
                    if job_result.lower() == "success":
                        trial.status = TriageTrialStates.JENKINS_BUILD_COMPLETE
                        trial.save()
                pass
            except Exception as ex:
                self.error(str(ex))
        elif status == TriageTrialStates.JENKINS_BUILD_COMPLETE:
            lsf_server = LsfStatusServer()  #TODO
            past_jobs = lsf_server.get_past_jobs_by_tag(add_info_to_db=False, tag=trial.tag)
            if past_jobs:
                trial.status = TriageTrialStates.IN_LSF
                trial.save()
        elif status == TriageTrialStates.IN_LSF:
            lsf_server = LsfStatusServer()  #TODO
            past_jobs = lsf_server.get_past_jobs_by_tag(add_info_to_db=False, tag=trial.tag)
            if past_jobs:
                trial.status = TriageTrialStates.IN_LSF
                trial.save()
            job_info = lsf_server.get_last_job(tag=trial.tag)
            if job_info and "job_id" in job_info:
                trial.lsf_job_id = job_info["job_id"]
            if job_info and "state" in job_info:
                if job_info["state"] == "completed":
                    trial.status = TriageTrialStates.PREPARING_RESULTS
                    trial.save()

        elif status == TriageTrialStates.PREPARING_RESULTS:
            lsf_server = LsfStatusServer()  # TODO
            job_info = lsf_server.get_last_job(tag=trial.tag)
            if triage.triage_type == TriagingTypes.REGEX_MATCH:
                if "output_text" in job_info:
                    lines = job_info["output_text"].split("\n")

                    trial.regex_match = ""
                    for line in lines:
                        m = re.search(triage.regex_match_string, line)
                        if m:
                            trial.regex_match = m.group(0)
                    trial.status = TriageTrialStates.COMPLETED
                    trial.save()
            elif triage.triage_type == TriagingTypes.PASS_OR_FAIL:
                code, message = self.validate_lsf_job(trial=trial)
                if code == 0:
                    trial.result = RESULTS["PASSED"]
                    trial.status = TriageTrialStates.COMPLETED
                    trial.save()
                elif code == 1:
                    trial.result = RESULTS["FAILED"]
                    trial.status = TriageTrialStates.COMPLETED
                    trial.save()
                elif code == -1:
                    trial.result = RESULTS["UNKNOWN"]
                    trial.status = TriageTrialStates.ERROR
                    self.error("Error in validating LSF: {}".format(message))
                    trial.save()
        trial.save()
        return status

    def validate_lsf_job(self, trial):
        code = 0
        message = ""
        lsf_server = LsfStatusServer()
        job_info = lsf_server.get_last_job(tag=trial.tag)
        if not job_info:
            code = -1
            message = "No job info"
        else:
            if "return_code" not in job_info:
                code = -1
                message = "return_code not in job_info"
            else:
                if not job_info["return_code"]:
                    code = 0
                else:
                    code = 1

        return code, message

if __name__ == "__main2__":
    triage_id = 123
    metric_id = 143
    Triage3.objects.filter(triage_id=triage_id).delete()
    Triage3Trial.objects.filter(triage_id=triage_id).delete()
    from_sha = "2e82b54db9599c4badf09f341149de19fcea2e1a"
    to_sha = "21dafef77642ecbfc33441a1779422eed9b31831"
    build_properties = {}
    t = Triage3(triage_id=triage_id,
                metric_id=metric_id,
                from_fun_os_sha=from_sha,
                to_fun_os_sha=to_sha,
                build_parameters=build_properties,
                submission_date_time=get_current_time(),
                status=TriagingStates.INIT,
                current_trial_set_id=1)
    if metric_id:
        t.base_tag = t.base_tag + "_{}_{}".format(triage_id, metric_id)
    t.save()

new_triage_id = 107

if __name__ == "__main2__":
    original_triage_id = 304
    original_t = Triage3.objects.get(triage_id=original_triage_id)
    original_t.pk = None
    original_t.triage_id = new_triage_id
    original_t.status = TriagingStates.INIT
    original_t.save()

if __name__ == "__main__":
    while True:
        triages = Triage3.objects.filter(status__gt=TriagingStates.COMPLETED)
        for triage in triages:
            s = TriageStateMachine(triage=triage)
            s.run()
            time.sleep(5)