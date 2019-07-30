from web.fun_test.django_interactive import *

from web.fun_test.metrics_models import Triage3, Triage3Trial
from web.fun_test.triaging_global import *

def set_triage_state(triage_id, state):
    t = Triage3.objects.get(triage_id=triage_id)
    t.status = state
    t.save()

def set_triage_trial_state(triage_id, state):
    trials = Triage3Trial.objects.filter(triage_id=triage_id)
    for trial in trials:
        trial.status = state
        trial.save()

if __name__ == "__main__":
    triage_id = 110
    set_triage_trial_state(triage_id=triage_id, state=TriageTrialStates.IN_LSF)
    set_triage_state(triage_id=triage_id, state=TriagingStates.IN_PROGRESS)