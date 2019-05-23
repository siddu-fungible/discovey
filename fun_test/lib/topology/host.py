from lib.system.fun_test import fun_test
from lib.system.utils import ToDictMixin
from lib.host.linux import Linux

class Host(ToDictMixin):
    def __init__(self, name, spec):
        self.name = name
        self.spec = spec
        self.instance = None

    def set_instance(self, instance):
        self.instance = instance

    def get_instance(self):
        return self.instance