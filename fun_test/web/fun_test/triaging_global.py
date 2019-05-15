from fun_global import RESULTS

class Codes:
    def __init__(self):
        self.non_callable_attributes = [f for f in dir(self) if not callable(getattr(self, f))]
        self.non_callable_attributes = [x for x in self.non_callable_attributes if not x.startswith("__")]
        self.code_to_string_map = {}
        for non_callable_attribute in self.non_callable_attributes:
            value = getattr(self, non_callable_attribute)
            if type(value) is int:
                self.code_to_string_map[value] = non_callable_attribute

    def code_to_string(self, code):
        return self.code_to_string_map.get(code, "Unknown")

    def all_codes_to_string(self):
        return self.code_to_string_map

    def to_json(self):
        result = []
        for non_callable_attribute in self.non_callable_attributes:
            value = getattr(self, non_callable_attribute)
            result.append(value)
        return result


class TriagingStates(Codes):
    UNKNOWN = -100
    ERROR = -99
    KILLED = -30
    ABORTED = -20
    COMPLETED = 10
    INIT = 20
    IN_PROGRESS = 60
    SUSPENDED = 70




class TriageTrialStates(Codes):
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


class TriagingTypes(Codes):
    PASS_OR_FAIL = {"code": 0, "description": "Pass/Fail"}
    SCORE = {"code": 1, "description": "Score"}
    REGEX_MATCH = {"code": 2, "description": "Regex match"}



if __name__ == "__main__":
    print TriagingTypes().to_json()