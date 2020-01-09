from fun_global import Codes

class SchedulingType:
    ASAP = "asap"
    PERIODIC = "periodic"  # Like Monday, Tuesdays at 1PM
    TODAY = "today"  # Schedule sometime today
    REPEAT = "repeat"  # Goes with the today type. Repeat the job after some minutes

    @staticmethod
    def get_deferred_types():
        return [SchedulingType.PERIODIC, SchedulingType.REPEAT, SchedulingType.TODAY]


class SchedulerStates(Codes):
    SCHEDULER_STATE_UNKNOWN = "SCHEDULER_STATE_UNKNOWN"
    SCHEDULER_STATE_STARTING = "SCHEDULER_STATE_STARTING"
    SCHEDULER_STATE_RUNNING = "SCHEDULER_STATE_RUNNING"
    SCHEDULER_STATE_RESTART_REQUESTED = "SCHEDULER_STATE_RESTART_REQUESTED"
    SCHEDULER_STATE_RESTARTING = "SCHEDULER_STATET_RESTARTING"
    SCHEDULER_STATE_STOPPED = "SCHEDULER_STATE_STOPPED"
    SCHEDULER_STATE_STOPPING = "SCHEDULER_STATE_STOPPING"
    SCHEDULER_STATE_PAUSED = "SCHEDULER_STATE_PAUSED"


class SuiteType:
    STATIC = "regular"
    DYNAMIC = "dynamic"  # Usually for re-runs
    CONTAINER = "container"
    TASK = "task"


class SchedulerJobPriority:
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    RANGES = {LOW: (16385, 24576),  NORMAL: (8193, 16384), HIGH: (1, 8192)}


class QueueOperations:
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    MOVE_TO_TOP = "move_to_top"
    MOVE_TO_NEXT_QUEUE = "move_to_next_queue"
    DELETE = "delete"


class JobStatusType(Codes):
    UNKNOWN = -40
    ERROR = -30
    KILLED = -20
    ABORTED = -10
    COMPLETED = 10
    AUTO_SCHEDULED = 20
    SUBMITTED = 30
    SCHEDULED = 40
    QUEUED = 50
    IN_PROGRESS = 60
    PAUSED = 70

    def code_to_string(self, code):
        result = "UNKNOWN"
        non_callable_attributes = [f for f in dir(self) if not callable(getattr(self, f))]
        for non_callable_attribute in non_callable_attributes:
            if getattr(self, non_callable_attribute) == code:
                result = non_callable_attribute
                break
        return result

    def is_idle_state(self, state):
        return (state == self.AUTO_SCHEDULED) or (state == self.KILLED) or (state == self.ABORTED) or (state == self.COMPLETED) or (state == self.ERROR)

    @staticmethod
    def is_completed(state):
        return state <= JobStatusType.COMPLETED


class SchedulerDirectiveTypes(Codes):
    PAUSE_QUEUE_WORKER = 1
    UNPAUSE_QUEUE_WORKER = 2


class TaskCategory(Codes):
    SYSTEM = 0
