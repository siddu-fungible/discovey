from fun_global import RESULTS

class States:
    def __init__(self):
        self.non_callable_attributes = [f for f in dir(self) if not callable(getattr(self, f))]
        self.non_callable_attributes = [x for x in self.non_callable_attributes if not x.startswith("__")]
        self.code_to_string_map = {}
        for non_callable_attribute in self.non_callable_attributes:
            value = getattr(self, non_callable_attribute)
            self.code_to_string_map[value] = non_callable_attribute


    def code_to_string(self, code):
        return self.code_to_string_map.get(code, "Unknown")

    def all_codes_to_string(self):
        return self.code_to_string_map


class TriagingStates(States):
    UNKNOWN = -100
    ERROR = -99
    KILLED = -30
    ABORTED = -20
    COMPLETED = 10
    INIT = 20
    IN_PROGRESS = 60
    SUSPENDED = 70




class TriageTrialStates(States):
    UNKNOWN = -100
    ERROR = -99
    KILLED = -20
    COMPLETED = 10
    INIT = 20
    SUBMITTED_TO_JENKINS = 29
    BUILDING_ON_JENKINS = 30
    JENKINS_BUILD_COMPLETE = 40
    IN_LSF = 50
    QUEUED_ON_LSF = 60
    RUNNING_ON_LSF = 70
    PREPARING_RESULTS = 80




class TriagingResult:
    UNKNOWN = RESULTS["UNKNOWN"]
    IN_PROGRESS = RESULTS["IN_PROGRESS"]
    FAILED = RESULTS["FAILED"]
    PASSED = RESULTS["PASSED"]
