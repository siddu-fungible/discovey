from lib.system.fun_test import fun_test
from lib.host.linux import Linux


class FungibleController(Linux):
    pass

    def initialize(self, reset=False):
        fun_test.log("Fungible controller: {} initialize".format(self))

    def is_ready_for_deploy(self):
        result = False
        return result

    def health(self, only_reachability=False):
        base_health = super(FungibleController, self).health(only_reachability=only_reachability)
        result = base_health
        return result

    def deploy(self, dut_instances, already_deployed=False):
        fs_objs = dut_instances
        return True