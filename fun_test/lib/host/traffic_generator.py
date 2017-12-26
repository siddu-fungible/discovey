class TrafficGenerator:
    TRAFFIC_GENERATOR_TYPE_FIO = "TRAFFIC_GENERATOR_TYPE_FIO"
    TRAFFIC_GENERATOR_TYPE_LINUX_HOST = "TRAFFIC_GENERATOR_TYPE_LINUX_HOST"
    TRAFFIC_GENERATOR_TYPE = TRAFFIC_GENERATOR_TYPE_LINUX_HOST
    def __init__(self):
        self.type = self.TRAFFIC_GENERATOR_TYPE

class Fio(TrafficGenerator):
    TRAFFIC_GENERATOR_TYPE = TrafficGenerator.TRAFFIC_GENERATOR_TYPE_FIO

class LinuxHost(TrafficGenerator):
    TRAFFIC_GENERATOR_TYPE = TrafficGenerator.TRAFFIC_GENERATOR_TYPE_LINUX_HOST
