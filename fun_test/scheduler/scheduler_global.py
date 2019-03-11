class SchedulingType:
    ASAP = "asap"
    PERIODIC = "periodic"  # Like Monday, Tuesdays at 1PM
    TODAY = "today"  # Schedule sometime today
    REPEAT = "repeat"  # Goes with the today type. Repeat the job after some minutes

    @staticmethod
    def get_deferred_types():
        return [SchedulingType.PERIODIC, SchedulingType.REPEAT, SchedulingType.TODAY]


class SchedulerStates:
    SCHEDULER_STATE_UNKNOWN = "SCHEDULER_STATE_UNKNOWN"
    SCHEDULER_STATE_STARTING = "SCHEDULER_STATE_STARTING"
    SCHEDULER_STATE_RUNNING = "SCHEDULER_STATE_RUNNING"
    SCHEDULER_STATE_RESTART_REQUESTED = "SCHEDULER_STATE_RESTART_REQUESTED"
    SCHEDULER_STATE_RESTARTING = "SCHEDULER_STATET_RESTARTING"
    SCHEDULER_STATE_STOPPED = "SCHEDULER_STATE_STOPPED"
    SCHEDULER_STATE_STOPPING = "SCHEDULER_STATE_STOPPING"


class SuiteType:
    STATIC = "regular"
    DYNAMIC = "dynamic"  # Usually for re-runs


class SchedulerJobPriority:
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    RANGES = {LOW: (2049, 3072),  NORMAL: (1025, 2048), HIGH: (1, 1024)}


class QueueOperations:
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    MOVE_TO_TOP = "move_to_top"
    MOVE_TO_NEXT_QUEUE = "move_to_next_queue"
    DELETE = "delete"
    