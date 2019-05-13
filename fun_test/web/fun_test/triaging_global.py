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


class TriageTrialStates:
    UNKNOWN = -100
    ERROR = -99
    KILLED = -20
    COMPLETED = 10
    INIT = 20
    BUILDING_ON_JENKINS = 30
    JENKINS_BUILD_COMPLETE = 40
    IN_LSF = 50
    QUEUED_ON_LSF = 60
    RUNNING_ON_LSF = 70


class TriagingResult:
    UNKNOWN = RESULTS["UNKNOWN"]
    IN_PROGRESS = RESULTS["IN_PROGRESS"]
    FAILED = RESULTS["FAILED"]
    PASSED = RESULTS["PASSED"]
