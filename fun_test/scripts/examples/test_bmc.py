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

results = []
errored_outs = []

for fs_spec in all_fs_spec:
    bmc_spec = fs_spec.get("bmc")
    bmc = Bmc(host_ip=bmc_spec["mgmt_ip"], ssh_username=bmc_spec["mgmt_ssh_username"], ssh_password=bmc_spec["mgmt_ssh_password"])
    try:
        bmc.command("cd /mnt/sdmmc0p1/scripts")

        #output = bmc.command("dmesg | grep JGR")
        output = bmc.command('gpiotool 8 --get-data | grep High >/dev/null 2>&1 && echo FS1600_REV2 || echo FS1600_REV1')
        is_rev_2 = "REV2" in output
        rev = "Unknown"
        if "REV1.1" in output:
            rev = "1.1"
        elif "REV1" in output:
            rev = "1"
        elif "REV2" in output:
            rev = "2"
        results.append((fs_spec["name"], rev))
    except:
        errored_outs.append((fs_spec["name"]))

for result in results:
    fun_test.log("FS: {}, Rev: {}".format(result[0], result[1]))

fun_test.log("Following FS errored out")
for errored_out in errored_outs:
    fun_test.log(errored_out)
