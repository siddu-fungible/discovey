from lib.system.fun_test import *
from scripts.networking.snapshot_helper import SnapshotHelper
from scripts.networking.nu_config_manager import *


class SetupScript(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Fetch dut config
        """)

    def setup(self):
        checkpoint = "Fetch DUT config"
        nu_config_obj = NuConfigManager()
        dut_config = nu_config_obj.read_dut_config(dut_type=nu_config_obj.DUT_TYPE)
        fun_test.test_assert(dut_config, checkpoint)
        fun_test.shared_variables['dut_config'] = dut_config

    def cleanup(self):
        pass


class TestSnapshotReady(FunTestCase):
    snapshot_helper = None

    def describe(self):
        self.set_test_details(id=1, summary="Ensure snapshot lib is installed",
                              steps="""
                              1. Initialize SnapshotHelper and import required packages 
                              2. If package installation failed then setup nmtf/snapshot
                              """)

    def setup(self):
        dut_config = fun_test.shared_variables['dut_config']

        dpc_server_ip = dut_config['dpcsh_tcp_proxy_ip']
        dpc_server_port = dut_config['dpcsh_tcp_proxy_port']

        checkpoint = "Initialize SnapshotHelper"
        self.snapshot_helper = SnapshotHelper(dpc_proxy_ip=dpc_server_ip, dpc_proxy_port=dpc_server_port)
        fun_test.test_assert(self.snapshot_helper, checkpoint)

    def run(self):
        checkpoint = "Setup snapshot"
        result = self.snapshot_helper.setup_snapshot(stream='etp')
        fun_test.test_assert(result, checkpoint)
        '''
        fun_test.sleep("Wait for traffic", seconds=40)

        snapshot_dict = self.snapshot_helper.run_snapshot()
        print "MAIN SFG PRV: %s" % snapshot_dict['Main SFG']['PRV']
        print "==============="
        print "MAIN SFG FRV: %s" % snapshot_dict['Main SFG']['FRV']
        print "==============="
        print "MAIN SFG MD: %s" % snapshot_dict['Main SFG']['MD']
        print "==============="
        print "MAIN SFG PSW_CTL: %s" % snapshot_dict['Main SFG']['PSW_CTL']
        print "==============="
        print "ERP SFG: %s" % snapshot_dict['ERP SFG']
        '''
    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = SetupScript()
    ts.add_test_case(TestSnapshotReady())
    ts.run()

