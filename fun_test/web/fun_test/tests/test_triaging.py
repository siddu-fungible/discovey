import web.fun_test.django_interactive
from web.fun_test.metrics_models import TriagingResult, TriagingStates
from web.fun_test.metrics_models import Triage3, Triage3Trial
from fun_global import get_current_time
import time
import sys
from lib.utilities.git_utilities import GitManager
import logging
import logging.handlers

logger = logging.getLogger("triaging_logger")
logger.setLevel(logging.DEBUG)
logger.propagate = False
LOG_FILE_NAME = "triaging_log.txt"

TEN_MB = 1e7
DEBUG = True

if not DEBUG:
    handler = logging.handlers.RotatingFileHandler(LOG_FILE_NAME, maxBytes=TEN_MB, backupCount=5)
else:
    handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
logger.addHandler(hdlr=handler)


# Trial set: a set of git trials.
# Each set has a from: fun os sha and and to: fun os sha
# from: usually indicates the sha where the score was good (or the run was a Pass)
# to: usually indicates the sha where the score indicated a degrade (or the run was a Fail)
# one trial is one execution instance of a fun_os_sha on the execution environment
# in one trial set we execute multiple trials. The fun_os_sha for each trial is selected
#


class TriageStateMachine:
    STEP = 4

    def __init__(self, triage):
        self.triage_id = triage.triage_id
        self.set_all_commits()

    def get_triage(self):
        return Triage3.objects.get(triage_id=triage_id)

    def set_all_commits(self):
        t = self.get_triage()
        from_fun_os_sha = t.from_fun_os_sha
        to_fun_os_sha = t.to_fun_os_sha
        all_commits = GitManager().get_commits_between(from_sha=from_fun_os_sha, to_sha=to_fun_os_sha)
        all_commits.reverse()

        self.all_commits = all_commits
        logger.debug("This triage has {} commits".format(len(all_commits)))
        logger.debug("First commit: {}".format(str(self.all_commits[0])))
        logger.debug("Second commit: {}".format(str(self.all_commits[-1])))

    def start_trial(self, fun_os_sha):
        t = self.get_triage()
        trial = Triage3Trial(fun_os_sha=fun_os_sha,
                             triage_id=self.triage_id,
                             trial_set_id=t.current_trial_set_id,
                             status=TriagingStates.INIT)
        trial.save()

    def start_trial_set(self, from_fun_os_sha, to_fun_os_sha):
        # create trial sets for boundary shas and in-between shas
        # get potential list of shas to try
        logger.debug("Starting Trial set, from: {}, to: {}".format(from_fun_os_sha, to_fun_os_sha))
        increment = len(self.all_commits)/self.STEP
        if not increment:
            increment = 1

        for commit_index in range(0, len(self.all_commits), increment):
            this_commit = self.all_commits[commit_index]
            logger.debug("Candidate: {}".format(str(this_commit)))
            self.start_trial(fun_os_sha=this_commit.sha)
        l = []
        l.append(from_fun_os_sha)
        l.append(to_fun_os_sha)
        pass


    def is_current_trial_set_complete(self):
        pass

    def process_trials(self):
        t = self.get_triage()
        logger.debug("Processing trials for trial set: {}".format(t.current_trial_set_id))
        trials = Triage3Trial.objects.filter(triage_id=triage_id, trial_set_id=t.current_trial_set_id)
        for trial in trials:
            logger.debug("Processing trial: {}".format(str(trial)))
            TrialStateMachine(triage_id=t.triage_id, sha=trial.fun_os_sha)


    def process(self):
        triage_id = self.triage_id
        t = self.get_triage()

        trials_count = Triage3Trial.objects.filter(triage_id=triage_id, trial_set_id=t.current_trial_set_id).count()
        logger.debug("Active trials: {}".format(trials_count))
        if not trials_count:
            self.start_trial_set(from_fun_os_sha=t.from_fun_os_sha,
                                 to_fun_os_sha=t.to_fun_os_sha)
            t.current_trial_set_id = t.current_trial_set_id + 1
            t.save()
        else:
            self.process_trials()

    def run(self):
        while True:
            self.process()
            time.sleep(60)


class TrialStateMachine:
    def __init__(self, triage_id, fun_os_sha):
        self.triage_id = triage_id
        self.fun_os_sha = fun_os_sha

    def run(self):
        trial = Triage3Trial(triage_id=self.triage_id, )

if __name__ == "__main__":

    triage_id = 123
    metric_id = 143
    from_sha = "2e82b54db9599c4badf09f341149de19fcea2e1a"
    to_sha = "21dafef77642ecbfc33441a1779422eed9b31831"
    build_properties = {}

    if Triage3.objects.filter(triage_id=triage_id).count() == 0:

        t = Triage3(triage_id=triage_id,
                    metric_id=metric_id,
                    from_fun_os_sha=from_sha,
                    to_fun_os_sha=to_sha,
                    build_parameters=build_properties,
                    submission_date_time=get_current_time(),
                    status=TriagingStates.IN_PROGRESS,
                    current_trial_set_id=1)
        t.save()
    else:
        t = Triage3.objects.get(triage_id=triage_id)
        s = TriageStateMachine(triage=t)
        s.run()