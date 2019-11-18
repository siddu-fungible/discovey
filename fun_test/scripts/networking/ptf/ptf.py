from lib.system.fun_test import *
from lib.host.linux import Linux
from scripts.networking.funeth import sanity
from scripts.networking.lib_nw import funcp
from scripts.networking.tb_configs import tb_configs
from fun_settings import REGRESSION_USER, REGRESSION_USER_PASSWORD
import re


try:
    tb_config_obj = tb_configs.TBConfigs(sanity.TB)
    PTF_SERVER = tb_config_obj.get_hostname('hu')
    PTF_SERVER_USERNAME = tb_config_obj.get_username('hu')
    PTF_SERVER_PASSWD = tb_config_obj.get_password('hu')
except:
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
        workspace = '/tmp'
        linux_obj.command('WSTMP=$WORKSPACE; export WORKSPACE=%s' % workspace)
        funcp_obj = funcp.FunControlPlane(linux_obj, ws=workspace)
        funsdk_obj = funcp.FunSDK(linux_obj, ws=workspace)

        # Stop noise traffic, e.g. IPv6 ND, LLDP
        linux_obj_ptf = Linux(host_ip=PTF_SERVER, ssh_username=PTF_SERVER_USERNAME, ssh_password=PTF_SERVER_PASSWD)
        cmds = (
            'sysctl net.ipv6.conf.all.disable_ipv6=1',
            'pkill lldp',
        )
        for cmd in cmds:
            linux_obj_ptf.sudo_command(cmd)
        
        # Get FunControlPlane
        fun_test.test_assert(funcp_obj.clone(), 'git clone FunControlPlane repo')
        fun_test.test_assert(funcp_obj.pull(), 'git pull FunControlPlane repo')
        fun_test.test_assert(funcp_obj.get_prebuilt(), 'Get FunControlPlane prebuilt pkg')

        # Get FunSDK
        fun_test.test_assert(funsdk_obj.clone(), 'git clone FunSDK repo')
        fun_test.test_assert(funsdk_obj.sdkup(), 'FunSDK script/bob --sdkup')

        # Set up PTF server
        output = funcp_obj.setup_traffic_server('hu')
        fun_test.test_assert(
            re.search(r'pipenv', output) and not re.search(r'fail|error|abort|assert', output, re.IGNORECASE),
            'Set up PTF traffic server')

        fun_test.shared_variables['linux_obj'] = linux_obj
        fun_test.shared_variables['funcp_obj'] = funcp_obj
        fun_test.shared_variables['funsdk_obj'] = funsdk_obj

    def cleanup(self):
        linux_obj_ptf = Linux(host_ip=PTF_SERVER, ssh_username=PTF_SERVER_USERNAME, ssh_password=PTF_SERVER_PASSWD)
        linux_obj_ptf.command('sudo pkill ptf')
        fun_test.shared_variables['funcp_obj'].cleanup()
        fun_test.shared_variables['funsdk_obj'].cleanup()
        fun_test.shared_variables['linux_obj'].command('export WORKSPACE=$WSTMP')


def run_ptf_test(tc, server, timeout, tc_desc):
    """Run PTF test cases."""

    job_environment = fun_test.get_job_environment()
    try:
        dpc_proxy_ip = str(job_environment['UART_HOST'])
        dpc_proxy_port = int(job_environment['UART_TCP_PORT_0'])
    except:
        dpc_proxy_ip = '10.1.21.120'
        dpc_proxy_port = '42221'

    funcp_obj = fun_test.shared_variables['funcp_obj']
    output = funcp_obj.send_traffic(tc, server=server, dpc_proxy_ip=dpc_proxy_ip, dpc_proxy_port=dpc_proxy_port,
                                    timeout=timeout)
    not_pass = re.search(r'FAILED|ERROR|ATTENTION: SOME TESTS DID NOT PASS!!!', output)

    # Failed cases
    failed_match = re.search(r'The following tests failed:\n(.*)', output, re.DOTALL)
    if failed_match:
        failed_cases = failed_match.group(1).split(',')
    else:
        failed_cases = []

    # Errored cases
    errored_match = re.search(r'The following tests errored:\n(.*)', output, re.DOTALL)
    if errored_match:
        errored_cases = errored_match.group(1).split(',')
    else:
        errored_cases = []

    # TODO: Remove below workaround after EM-820 is fixed
    if tc == 'etp':
        for tc in failed_cases:
            if '2mss' in tc or '3mss' in tc or 'chksum' in tc:
                failed_cases.remove(tc)

    if failed_cases:
        fun_test.log('Failed cases: %s' % '\n'.join(sorted(failed_cases)))

    if errored_cases:
        fun_test.log('Errored cases: %s' % '\n'.join(sorted(errored_cases)))

    fun_test.test_assert(not not_pass and not failed_cases and not errored_cases, tc_desc)


def get_ptf_log():
    for log_file in ('ptf.log',):
        artifact_file_name = fun_test.get_test_case_artifact_file_name(post_fix_name=log_file)
        fun_test.scp(source_ip=PTF_SERVER,
                     source_file_path="/home/{}/FunControlPlane/{}".format(PTF_SERVER_USERNAME, log_file),
                     source_username=PTF_SERVER_USERNAME,
                     source_password=PTF_SERVER_PASSWD,
                     target_file_path=artifact_file_name)
        fun_test.add_auxillary_file(description="{} Log".format(log_file.split('.')[0]), filename=artifact_file_name)


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
        get_ptf_log()

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
        get_ptf_log()

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
        get_ptf_log()

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
        get_ptf_log()

    def run(self):
        run_ptf_test('fcp_palladium', server='nu', timeout=1800, tc_desc='FCP loopback test')


class AclTest(FunTestCase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="ACL test",
                              steps="""
        1. Acl Test.
        """)

    def setup(self):
        pass

    def cleanup(self):
        get_ptf_log()

    def run(self):
        run_ptf_test('acl_palladium', server='nu', timeout=300,
                     tc_desc='Acl Test.')


class QosTest(FunTestCase):
    def describe(self):
        self.set_test_details(id=6,
                              summary="QoS test",
                              steps="""
        1. Qos Test.
        """)

    def setup(self):
        pass

    def cleanup(self):
        get_ptf_log()

    def run(self):
        run_ptf_test('qos_palladium', server='nu', timeout=300,
                     tc_desc='Qos Test.')


class L2Test(FunTestCase):
    def describe(self):
        self.set_test_details(id=7,
                              summary="L2 test",
                              steps="""
        1. GPH Test.
        """)

    def setup(self):
        pass

    def cleanup(self):
        get_ptf_log()

    def run(self):
        run_ptf_test('l2_palladium', server='nu', timeout=300,
                     tc_desc='L2 Test.')


class L3Test(FunTestCase):
    def describe(self):
        self.set_test_details(id=8,
                              summary="L3 test",
                              steps="""
        1. L3 Test.
        """)

    def setup(self):
        pass

    def cleanup(self):
        get_ptf_log()

    def run(self):
        run_ptf_test('l3_palladium', server='nu', timeout=600,
                     tc_desc='L3 Test.')


class GphTest(FunTestCase):
    def describe(self):
        self.set_test_details(id=9,
                              summary="GPH test",
                              steps="""
        1. GPH Test.
        """)

    def setup(self):
        pass

    def cleanup(self):
        get_ptf_log()

    def run(self):
        run_ptf_test('gph_palladium', server='nu', timeout=600,
                     tc_desc='GPH Test.')



if __name__ == "__main__":
    ts = PTFTestSuite()
    for tc in (
            EtpTest,
            ErpTest,
            ParserTest,
            #FCPTest,  # TODO: Enable these tests
            #AclTest,
            #QosTest,
            #L2Test,
            #L3Test,
            #GphTest,
    ):
        ts.add_test_case(tc())
    ts.run()
