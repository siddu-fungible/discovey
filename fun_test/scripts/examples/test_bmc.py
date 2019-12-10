from lib.system.fun_test import fun_test
from lib.fun.fs import Bmc


class A(object):
    def __init__(self, a=None):
        print a


class B(A):
    def __init__(self, **kwargs):
        super(B, self).__init__(**kwargs)
blob = {"a": 1}

b = B(**blob)


am = fun_test.get_asset_manager()
all_fs_spec = am.get_all_fs_spec()

for fs_spec in all_fs_spec:
    bmc_spec = fs_spec.get("bmc")
    bmc = Bmc(**bmc_spec)
    output = bmc.command("dmesg | grep JGR")
    is_rev_2 = "REV2" in output
    fun_test.log("FS: {} Rev2: ".format(fs_spec["name"], is_rev_2))
