from scripts.networking.lib_nw import funcp
from lib.host.linux import Linux
from lib.system.fun_test import *
import subprocess
import os
import git

USERNAME = "rushi"
PASSWORD = "rushi@123"
HOST_IP = "localhost"
IS_LOCALHOST = True
FUNCP = "FunControlPlane"
FUNSDK = "FunSDK"
FUNSDK_REPO = "FunSDK-small"
GIT_BASE = "git@github.com:fungible-inc"


def setup_funcp_repo(branch='master'):
    result = True
    try:
        if os.path.exists(SYSTEM_TMP_DIR + "/%s" % FUNCP):
            repo = git.Repo(SYSTEM_TMP_DIR + "/%s" % FUNCP)
            repo.remotes.origin.pull()
        else:
            git.Git(SYSTEM_TMP_DIR).clone("%s/%s.git" % (GIT_BASE, FUNCP))
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def get_funcp_prebuilt():
    result = True
    try:
        filename = 'functrlp_palladium.tgz'
        cmds = (
            'cd %s/%s' % (SYSTEM_TMP_DIR, FUNCP),
            'wget http://dochub.fungible.local/doc/jenkins/funcontrolplane/latest/%s' % filename,
            'tar xzvf %s' % filename,
        )
        exit_val = subprocess.call(cmds, shell=True)
        if exit_val != 0:
            result = False
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def setup_funsdk_repo():
    result = True
    try:
        if not os.path.exists(SYSTEM_TMP_DIR + "/%s" % FUNSDK):
            git.Git(SYSTEM_TMP_DIR).clone("%s/%s.git" % (GIT_BASE, FUNSDK_REPO))
            cmd = 'mv %s %s' % (FUNSDK_REPO, FUNSDK)
            subprocess.call(cmd, shell=True)
    except Exception as ex:
        result = False
        fun_test.critical(str(ex))
    return result


def funsdk_up():
    result = True
    try:
        exit_val = os.system("%s/%s/scripts/bob --sdkup" % (SYSTEM_TMP_DIR, FUNSDK))
        if exit_val != 0:
            result = False
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def make_gen_files():
    result = False
    try:
        fun_test.test_assert(os.path.exists('%s/%s/networking/tools/nmtf/setup.py' % (SYSTEM_TMP_DIR, FUNCP)),
                             message="Check file exists locally")
        fun_test.test_assert(os.path.exists('%s/%s/networking/tools/dpcsh/setup.py' % (SYSTEM_TMP_DIR, FUNCP)),
                             message="Check file exists locally")
        cmds = (
            'cd %s/%s/networking/tools/dpcsh' % (SYSTEM_TMP_DIR, FUNCP),
            'sudo python setup.py install',
            'cd %s/%s/networking/tools/nmtf' % (SYSTEM_TMP_DIR, FUNCP),
            'sudo python setup.py install',
        )
        exit_val = subprocess.call(cmds, shell=True)
        if exit_val == 0:
            result = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def setup_nmtf():
    result = False
    try:
        fun_test.test_assert(setup_funcp_repo(), 'Setup FunControlPlane repo')
        fun_test.test_assert(get_funcp_prebuilt(), 'Get FunControlPlane prebuilt pkg')
        fun_test.test_assert(setup_funsdk_repo(), 'Setup FunSDK repo')
        fun_test.test_assert(funsdk_up(), 'FunSDK script/bob --sdkup')
        fun_test.test_assert(make_gen_files(), "Gen Files")
        result = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


if __name__ == "__main__":
    setup_nmtf()
