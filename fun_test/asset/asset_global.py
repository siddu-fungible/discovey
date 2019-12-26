from fun_global import Codes


class AssetType(Codes):
    DUT = "DUT"
    HOST = "Host"
    PERFORMANCE_LISTENER_HOST = "Perf Listener"
    # DUT_WITH_SERVERS = "DUT with server"
    # DUT_WITH_SSDS = "DUT with SSD"


class AssetHealth(Codes):
    DEAD = 1
    DISABLED = 10
    ACTIVE = 50
