from fun_global import Codes


class AssetType(Codes):
    DUT = "DUT"
    HOST = "Host"
    PERFORMANCE_LISTENER_HOST = "Perf Listener"
    PCIE_HOST = "PCIE-host"


class AssetHealthStates(Codes):
    DISABLED = 10
    UNHEALTHY = 20
    DEGRADING = 30
    HEALTHY = 50
