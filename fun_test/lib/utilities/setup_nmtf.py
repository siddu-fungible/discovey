from scripts.networking.lib_nw import funcp
from lib.host.linux import Linux
from lib.system.fun_test import *

# Change WORKSPACE as per your workspace on your development vm for local use
# Below path is setup on qa-ubuntu-01 regression server for auto_admin user
# WORKSPACE = '/local/auto_admin/Projects'
WORKSPACE = '/tmp'
USERNAME = "auto_admin"
PASSWORD = "fun123"
HOST_IP = "localhost"
IS_LOCALHOST = True


def setup_nmtf(username=USERNAME, password=PASSWORD, host_ip="localhost", localhost=False):
    linux_obj = Linux(host_ip=host_ip, ssh_username=username, ssh_password=password, localhost=localhost)
    linux_obj.command('WSTMP=$WORKSPACE; export WORKSPACE=%s' % WORKSPACE)
    funcp_obj = funcp.FunControlPlane(linux_obj, ws=WORKSPACE)
    funsdk_obj = funcp.FunSDK(linux_obj, ws=WORKSPACE)
    fun_test.test_assert(funcp_obj.clone(), 'git clone FunControlPlane repo')
    fun_test.test_assert(funcp_obj.pull(), 'git pull FunControlPlane repo')
    fun_test.test_assert(funcp_obj.get_prebuilt(), 'Get FunControlPlane prebuilt pkg')
    # TODO: Provide an option to checkout FunSDK and do sdkup in workspace
    # fun_test.test_assert(funsdk_obj.clone(), 'git clone FunSDK repo')
    # fun_test.test_assert(funsdk_obj.sdkup(), 'FunSDK script/bob --sdkup')
    fun_test.test_assert(funcp_obj.make_gen_files(), "Gen Files")


if __name__ == "__main__":
    setup_nmtf(username=USERNAME, password=PASSWORD, host_ip=HOST_IP, localhost=IS_LOCALHOST)
