from scripts.networking.lib_nw import funcp
from lib.host.linux import Linux
import sys
from fun_settings import REGRESSION_USER, REGRESSION_USER_PASSWORD

from lib.system.fun_test import *


def setup_nmtf(username='auto_admin', password='fun123', host_ip="localhost"):
    linux_obj = Linux(host_ip=host_ip, ssh_username=username, ssh_password=password)
    workspace = '/tmp'
    linux_obj.command('WSTMP=$WORKSPACE; export WORKSPACE=%s' % workspace)
    funcp_obj = funcp.FunControlPlane(linux_obj, ws=workspace)
    fun_test.test_assert(funcp_obj.clone(), 'git clone FunControlPlane repo')
    fun_test.test_assert(funcp_obj.pull(), 'git pull FunControlPlane repo')
    fun_test.test_assert(funcp_obj.get_prebuilt(), 'Get FunControlPlane prebuilt pkg')
    fun_test.test_assert(funcp_obj.make_gen_files(), "Gen Files")


if __name__ == "__main__":
    setup_nmtf(username='yajat', password='messi3006', host_ip="localhost")




    def make_gen_files(self):
        cmds = (
            'cd %s/%s/networking/tools/dpcsh' % (self.ws, self.name),
            'python setup.py install',
            'cd ../nmtf',
            'sudo python setup.py install',
        )
        output = self.linux_obj.sudo_command(';'.join(cmds), timeout=120)
        return output
