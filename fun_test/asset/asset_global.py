from fun_global import Codes


class AssetType(Codes):
    DUT = "DUT"
    HOST = "Host"
    PERFORMANCE_LISTENER_HOST = "Perf Listener"


class AssetHealthStates(Codes):
    UNHEALTHY = 20
    PENDING_HEALTH_CHECK = 30
    HEALTHY = 50
