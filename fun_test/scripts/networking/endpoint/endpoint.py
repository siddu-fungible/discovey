from lib.system.fun_test import *
from lib.host.linux import Linux
from scripts.networking.lib_nw import funcp
from fun_settings import REGRESSION_USER, REGRESSION_USER_PASSWORD
import re


class EndPointTestSuite(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Update FunControlPlane repo and set up PTF traffic server.
        2. Send traffic HU->NU to test ETP.
        3. Send traffic NU->HU to test ERP.
                              """)

    def setup(self):
        #linux_obj = #Linux(host_ip='localhost', ssh_username=REGRESSION_USER, ssh_password=REGRESSION_USER_PASSWORD))
        linux_obj = Linux(host_ip='localhost', ssh_username='gliang', ssh_password='fun123')
        funcp_obj = funcp.FunControlPlane(linux_obj)
        funcp_obj.clone()
        funcp_obj.pull()
        funcp_obj.setup_traffic_server('hu')
        fun_test.shared_variables['funcp_obj'] = funcp_obj

    def cleanup(self):
        fun_test.shared_variables['funcp_obj'].cleanup()


class EtpTest(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="ETP test",
                              steps="""
        1. Run ETP test
        """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        funcp_obj = fun_test.shared_variables['funcp_obj']
        output = funcp_obj.send_traffic('endpoint.EtpTest_simple_tcp', timeout=60)
        fun_test.test_assert(not re.search(r'FAIL', output), "ETP test")


class ErpTest(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="ERP test",
                              steps="""
        1. Run ERP test
        """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def run(self):
        funcp_obj = fun_test.shared_variables['funcp_obj']
        output = funcp_obj.send_traffic('endpoint.ErpTest_simple_tcp', timeout=60)
        fun_test.test_assert(not re.search(r'FAIL', output), "ERP test")


if __name__ == "__main__":
    ts = EndPointTestSuite()
    for tc in (EtpTest, ErpTest):
        ts.add_test_case(tc())
    ts.run()
