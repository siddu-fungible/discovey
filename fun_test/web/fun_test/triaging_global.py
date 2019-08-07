from fun_global import RESULTS, Codes


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
    JENKINS_BUILD_FAILED = 90




class TriagingResult:
    UNKNOWN = RESULTS["UNKNOWN"]
    IN_PROGRESS = RESULTS["IN_PROGRESS"]
    FAILED = RESULTS["FAILED"]
    PASSED = RESULTS["PASSED"]


class TriagingTypes(Codes):
    PASS_OR_FAIL = 1
    SCORE = 2
    REGEX_MATCH = 3
    PASS_OR_FAIL_INTEGRATION = 4
    JENKINS_FUN_OS_ON_DEMAND = 5



if __name__ == "__main__":
    print TriagingTypes().to_json()