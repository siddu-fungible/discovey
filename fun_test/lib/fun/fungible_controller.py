from lib.system.fun_test import fun_test
from lib.host.linux import Linux


class FungibleController(Linux):
    def __init__(self, **kwargs):
        super(FungibleController, self).__init__(**kwargs)
        self.initialized = False

    def initialize(self, reset=False):
        fun_test.log("Fungible controller: {} initialize".format(self))
        self.initialized = True

    def is_ready_for_deploy(self):
        result = False
        if not self.initialized:
            self.initialize()
        return result

    def health(self, only_reachability=False):
        base_health = super(FungibleController, self).health(only_reachability=only_reachability)
        result = base_health
        return result

    def deploy(self, dut_instances, already_deployed=False):
        if not self.initialized:
            self.initialize()
        fs_objs = dut_instances
        return True