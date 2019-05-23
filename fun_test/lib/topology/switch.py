from lib.system.utils import ToDictMixin

class Switch(ToDictMixin):
    SWITCH_TYPE_QFX = "SWITCH_TYPE_QFX"

    def __init__(self, name, spec):
        self.type = self.SWITCH_TYPE_QFX
        self.name = name
        self.spec = spec
