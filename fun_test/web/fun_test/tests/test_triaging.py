import web.fun_test.django_interactive
from web.fun_test.metrics_models import Triage2, TriagingResult, TriagingStates, Triage2Trial
from fun_global import get_current_time
import time
from lib.utilities.git_utilities import GitManager


# Trial set: a set of git trials.
# Each set has a from: fun os sha and and to: fun os sha
# from: usually indicates the sha where the score was good (or the run was a Pass)
# to: usually indicates the sha where the score indicated a degrade (or the run was a Fail)
# one trial is one execution instance of a fun_os_sha on the execution environment
# in one trial set we execute multiple trials. The fun_os_sha for each trial is selected
#



class StateMachine:
    STEP = 4

    def __init__(self, triage):
        self.triage_id = triage.triage_id
        self.this_triage = Triage2.objects.get(triage_id=triage_id)
        self.set_all_commits()

    def set_all_commits(self):
        from_fun_os_sha = self.this_triage.from_fun_os_sha
        to_fun_os_sha = self.this_triage.to_fun_os_sha
        all_commits = GitManager().get_commits_between(from_sha=from_fun_os_sha, to_sha=to_fun_os_sha)
        all_commits.reverse()
        #for commit in all_commits:
        #    print commit["sha"], commit["commit"]["committer"]["date"]
        self.all_commits = all_commits
        print("This triage has {} commits".format(len(all_commits)))
        print("First commit: {}".format(str(self.all_commits[0])))
        print("Second commit: {}".format(str(self.all_commits[-1])))


    def start_trial(self, fun_os_sha):
        trial = Triage2Trial(fun_os_sha=fun_os_sha, triage_id=self.triage_id, trial_set_id=self.this_triage.current_trial_set_id)
        trial.save()

    def start_trial_set(self, from_fun_os_sha, to_fun_os_sha):
        # create trial sets for boundary shas and in-between shas
        # get potential list of shas to try
        for commit_index in range(0, len(self.all_commits), self.STEP):
            this_commit = self.all_commits[commit_index]
            print("Candidate: {}".format(str()))
            self.start_trial(fun_os_sha=this_commit.sha)
        l = []
        l.append(from_fun_os_sha)
        l.append(to_fun_os_sha)
        pass


    def is_current_trial_set_complete(self):
        pass

    def process(self):
        triage_id = self.triage_id

        trials_count = Triage2Trial.objects.filter(triage_id=triage_id).count()
        if not trials_count:
            self.start_trial_set(from_fun_os_sha=self.this_triage.from_fun_os_sha,
                                 to_fun_os_sha=self.this_triage.to_fun_os_sha)

    def run(self):
        while True:
            self.process()
            time.sleep(60)

if __name__ == "__main__":

    triage_id = 123
    metric_id = 143
    from_sha = "2e82b54db9599c4badf09f341149de19fcea2e1a"
    to_sha = "21dafef77642ecbfc33441a1779422eed9b31831"
    build_properties = {}

    if Triage2.objects.filter(triage_id=triage_id).count() == 0:

        t = Triage2(triage_id=triage_id,
                    metric_id=metric_id,
                    from_fun_os_sha=from_sha,
                    to_fun_os_sha=to_sha,
                    build_parameters=build_properties,
                    submission_date_time=get_current_time(),
                    status=TriagingStates.IN_PROGRESS)
        t.save()
    else:
        t = Triage2.objects.get(triage_id=triage_id)
        s = StateMachine(triage=t)
        s.run()