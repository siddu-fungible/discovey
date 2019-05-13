from fun_global import RESULTS


class TriagingStates:
    UNKNOWN = -100
    ERROR = -99
    KILLED = -30
    ABORTED = -20
    COMPLETED = 10
    INIT = 20
    IN_PROGRESS = 60
    SUSPENDED = 70

    def code_to_string(self, code):
        result = "UNKNOWN"
        non_callable_attributes = [f for f in dir(self) if not callable(getattr(self, f))]
        for non_callable_attribute in non_callable_attributes:
            if getattr(self, non_callable_attribute) == code:
                result = non_callable_attribute
                break
        return result


class TriageTrialStates:
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

    def code_to_string(self, code):
        result = "UNKNOWN"
        non_callable_attributes = [f for f in dir(self) if not callable(getattr(self, f))]
        for non_callable_attribute in non_callable_attributes:
            if getattr(self, non_callable_attribute) == code:
                result = non_callable_attribute
                break
        return result



class TriagingResult:
    UNKNOWN = RESULTS["UNKNOWN"]
    IN_PROGRESS = RESULTS["IN_PROGRESS"]
    FAILED = RESULTS["FAILED"]
    PASSED = RESULTS["PASSED"]
