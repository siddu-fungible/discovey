from lib.system.fun_test import *
from lib.host.linux import Linux
from scripts.networking.lib_nw import funcp
from fun_settings import REGRESSION_USER, REGRESSION_USER_PASSWORD
import os
import re


PTF_SERVER = 'cadence-pc-5'
PTF_SERVER_USERNAME = 'localadmin'
PTF_SERVER_PASSWD = 'Precious1*'


class PTFTestSuite(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Update FunControlPlane repo and set up PTF traffic server.
        2. Send traffic HU->NU to test ETP.
        3. Send traffic NU->HU to test ERP.
        4. Send traffic to FPG to test FPG and ERP parser.
        5. FCP loopback test.
        6. Other PTF tests for palladium.
                              """)

    def setup(self):
        linux_obj = Linux(host_ip='localhost', ssh_username=REGRESSION_USER, ssh_password=REGRESSION_USER_PASSWORD)
        workspace = '%s/tmp/' % os.getenv('HOME')
        linux_obj.command('WSTMP=$WORKSPACE; export WORKSPACE=%s' % workspace)
        funcp_obj = funcp.FunControlPlane(linux_obj, ws=workspace)
        funsdk_obj = funcp.FunSDK(linux_obj, ws=workspace)

        # Get FunControlPlane
        done_list = re.findall(r'done', funcp_obj.clone())
        fun_test.test_assert(done_list == ['done'] * 5 or done_list == ['done'] * 6,
                             'git clone FunControlPlane repo')
        fun_test.test_assert(re.search(r'Already up[-| ]to[-| ]date.', funcp_obj.pull()),
                             'git pull FunControlPlane repo')
        fun_test.test_assert(re.search(r'funnel_gen.py', funcp_obj.get_prebuilt(), re.DOTALL),
                             'Get FunControlPlane prebuilt pkg')

        # Get FunSDK
        done_list = re.findall(r'done', funsdk_obj.clone())
        fun_test.test_assert(done_list == ['done'] * 5 or done_list == ['done'] * 6,
                             'git clone FunSDK repo')
        fun_test.test_assert(re.search(r'Updating current build number', funsdk_obj.sdkup()), 'bob --sdkup')

        # Set up PTF server
        output = funcp_obj.setup_traffic_server('hu')
        fun_test.test_assert(re.search(r'pipenv', output) and not re.search(r'fail|error|abort|assert', output,
                                                                            re.IGNORECASE),
                             'Set up PTF traffic server')

        fun_test.shared_variables['linux_obj'] = linux_obj
        fun_test.shared_variables['funcp_obj'] = funcp_obj


    def cleanup(self):
        linux_obj_ptf = Linux(host_ip=PTF_SERVER, ssh_username=PTF_SERVER_USERNAME, ssh_password=PTF_SERVER_PASSWD)
        linux_obj_ptf.command('sudo pkill ptf')
        fun_test.shared_variables['funcp_obj'].cleanup()
        fun_test.shared_variables['linux_obj'].command('export WORKSPACE=$WSTMP')


def run_ptf_test(tc, server, timeout, tc_desc):
    """Run PTF test cases."""
    funcp_obj = fun_test.shared_variables['funcp_obj']
    output = funcp_obj.send_traffic(tc, server=server, timeout=timeout)
    failed = re.search(r'FAILED (failures=\d+)', output)
    match = re.search(r'The following tests failed:\n(.*?)', output, re.DOTALL)
    if match:
        failed_cases = match.group(1).split(',')
    else:
        failed_cases = []

    # TODO: Remove below workaround after SWOS-2890 is fixed
    if tc == 'etp':
        for tc in failed_cases:
            if '2mss' in tc or '3mss' in tc or 'chksum' in tc:
                failed_cases.remove(tc)

    if failed_cases:
        fun_test.log('Failed cases: %s' % '\n'.join(sorted(failed_cases)))

    fun_test.test_assert(not failed and len(failed_cases) == 0, tc_desc)


class EtpTest(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="ETP test",
                              steps="""
        1. Send traffic HU->NU to test ETP.
        """)

    def setup(self):
        # TODO: Remove below workaround after SWOS-2890 is fixed
        linux_obj_ptf = Linux(host_ip=PTF_SERVER, ssh_username=PTF_SERVER_USERNAME, ssh_password=PTF_SERVER_PASSWD)
        linux_obj_ptf.command('nohup ping 19.1.1.1 -i 100 &')
        pass

    def cleanup(self):
        # TODO: Remove below workaround after SWOS-2890 is fixed
        linux_obj_ptf = Linux(host_ip=PTF_SERVER, ssh_username=PTF_SERVER_USERNAME, ssh_password=PTF_SERVER_PASSWD)
        linux_obj_ptf.command('pkill ping')
        pass

    def run(self):
        run_ptf_test('etp', server='hu', timeout=6000, tc_desc='ETP test')


class ErpTest(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="ERP test",
                              steps="""
        1. Send traffic NU->HU to test ERP.
        """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        run_ptf_test('erp', server='hu', timeout=1800, tc_desc='ERP test')


class ParserTest(FunTestCase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Parser test",
                              steps="""
        1. Send traffic to FPG to test FPG and ERP parser.
        """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        run_ptf_test('prv', server='hu', timeout=7200, tc_desc='Parser test')


class FCPTest(FunTestCase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="FCP test",
                              steps="""
        1. FCP loopback test.
        """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        run_ptf_test('fcp_palladium', server='nu', timeout=1800, tc_desc='FCP loopback test')


class OtherPalladiumTest(FunTestCase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Other palladium enabled test - L2/L3, ACL, QoS, Sample, Punt, etc.",
                              steps="""
        1. Other palladium enabled test - L2/L3, ACL, QoS, Sample, Punt, etc..
        """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        run_ptf_test('palladium', server='nu', timeout=1800,
                     tc_desc='Other palladium enabled test - L2/L3, ACL, QoS, Sample, Punt, etc.')


if __name__ == "__main__":
    ts = PTFTestSuite()
    for tc in (
            EtpTest,
            ErpTest,
            #ParserTest,  # TODO: Enable these tests
            #FCPTest,
            #OtherPalladiumTest,
    ):
        ts.add_test_case(tc())
    ts.run()
