from lib.system.fun_test import fun_test
from lib.host.linux import Linux


class FungibleController(Linux):
    pass

    def initialize(self, reset=False):
        fun_test.log("Fungible controller initialize")


