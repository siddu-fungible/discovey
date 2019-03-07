'''Author : Yajat N Singh'''
from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_traffic_generator_template import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import *
from lib.host.network_controller import *
from scripts.networking.nu_config_manager import *
from scripts.networking.helper import *
from scripts.networking.snapshot_helper import *


class Setup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Configure Spirent Ports (No of ports needed 2)
        2. Configure Generator Configs and Get Generator Handle for Tx Port
        3. Subscribed to all types of results
        """)

    def setup(self):

        setup_snapshot(smac=None, psw_stream=None, stream=None, unit=None, dpc_tcp_proxy_ip='10.1.40.24',
                       dpc_tcp_proxy_port=40221)

    def cleanup(self):
        pass


class SnapshotTest(FunTestCase):

    def describe(self):
        self.set_test_details(id=1, summary="Test Snapshot",
                              steps="""
                                  1. Example Script - SETUP SNAPSHOT
                                  2. Run traffic
                                  3. Run snapshot
                                  4. use snapshot functions to get desired outputs
                                  """)

    def setup(self):
        fun_test.sleep(message="wait for traffic", seconds=10)
        ss = run_snapshot()
        fun_test.log(ss)
        # ss1 = fun_test.parse_file_to_json('snapshot_output.json')
        print get_snapshot_main_sfg(ss)
        print get_snapshot_meter_id(snapshot_output=ss)
        print get_snapshot_meter_id(snapshot_output=ss, erp=True)
        print get_snapshot_acl_label(ss)

    def run(self):
        pass

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = Setup()
    ts.add_test_case(SnapshotTest())
    ts.run()
