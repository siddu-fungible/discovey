from lib.system.fun_test import *
from lib.host.linux import Linux
from scripts.networking.lib_nw import funcp
from fun_settings import REGRESSION_USER, REGRESSION_USER_PASSWORD
import re


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
        #linux_obj = #Linux(host_ip='localhost', ssh_username=REGRESSION_USER, ssh_password=REGRESSION_USER_PASSWORD))
        # TODO: Replace below with regression user
        linux_obj = Linux(host_ip='localhost', ssh_username='gliang', ssh_password='fun123')
        funcp_obj = funcp.FunControlPlane(linux_obj)
        done_list = re.findall(r'done', funcp_obj.clone())
        fun_test.test_assert( done_list == ['done'] * 5 or done_list == ['done'] * 6,
                             'git clone FunControlPlane repo')
        fun_test.test_assert(re.search(r'Already up[-| ]to[-| ]date.', funcp_obj.pull(branch='george/ep')),
                             'git pull FunControlPlane repo')
        fun_test.test_assert(re.search(r'funnel_gen.py', funcp_obj.get_prebuilt(), re.DOTALL),
                             'Get FunControlPlane prebuilt pkg')
        output = funcp_obj.setup_traffic_server('hu')
        fun_test.test_assert(re.search(r'pipenv', output) and not re.search(r'fail|error|abort|assert', output,
                                                                            re.IGNORECASE),
                             'Set up PTF traffic server')
        fun_test.shared_variables['funcp_obj'] = funcp_obj

    def cleanup(self):
        fun_test.shared_variables['funcp_obj'].cleanup()


class EtpTest(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="ETP test",
                              steps="""
        1. Send traffic HU->NU to test ETP.
        """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        funcp_obj = fun_test.shared_variables['funcp_obj']
        output = funcp_obj.send_traffic('endpoint.EtpTest_simple_tcp', server='hu', timeout=60)
        fun_test.test_assert(re.search(r'Ran \d+ test.*OK', output, re.DOTALL), "ETP test")


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
        funcp_obj = fun_test.shared_variables['funcp_obj']
        #output = funcp_obj.send_traffic('endpoint.ErpTest_simple_tcp', server='hu', timeout=60)
        output = funcp_obj.send_traffic('erp', server='hu', timeout=3600)
        match = re.search(r'The following tests failed:\n(.*?)\n', output, re.DOTALL)
        failed_cases = match.group(1).split(',')
        fun_test.log('Failed cases: %s' % '\n'.join(sorted(failed_cases)))
        fun_test.test_assert(len(failed_cases) == 0, "ERP test")


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
        funcp_obj = fun_test.shared_variables['funcp_obj']
        output = funcp_obj.send_traffic('prv.PrvTest_simple_tcp', server='hu', timeout=60)
        fun_test.test_assert(re.search(r'Ran \d+ test.*OK', output, re.DOTALL), "Parser test")


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
        funcp_obj = fun_test.shared_variables['funcp_obj']
        output = funcp_obj.send_traffic('fcp_palladium', server='nu', timeout=60)
        fun_test.test_assert(re.search(r'Ran \d+ test.*OK', output, re.DOTALL), "FCP loopback test")


class OtherPalladiumTest(FunTestCase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Other palladium enabled test - L2/L3, ACL, QoS, Sample, Punt, etc.",
                              steps="""
        1. FCP loopback test.
        """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        funcp_obj = fun_test.shared_variables['funcp_obj']
        output = funcp_obj.send_traffic('fcp_palladium', server='nu', timeout=60)
        fun_test.test_assert(re.search(r'Ran \d+ test.*OK', output, re.DOTALL),
                             "Other palladium enabled test - L2/L3, ACL, QoS, Sample, Punt, etc.")


if __name__ == "__main__":
    ts = PTFTestSuite()
    for tc in (
            EtpTest,
            ErpTest,
    ):
        ts.add_test_case(tc())
    ts.run()
