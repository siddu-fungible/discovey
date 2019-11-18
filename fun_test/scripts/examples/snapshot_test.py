'''Author : Yajat N Singh'''
from lib.host.network_controller import *
from scripts.networking.snapshot_helper import *


class Setup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Configure Spirent Ports (No of ports needed 2)
        2. Configure Generator Configs and Get Generator Handle for Tx Port
        3. Subscribed to all types of results
        """)

    def setup(self):
        global network_controller_obj
        network_controller_obj = NetworkController(dpc_server_ip='10.1.21.120', dpc_server_port=42221)
        fun_test.log("Network done1")

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
        network_controller_obj.echo_hello()
        fun_test.log("echo done 1")

        network_controller_obj.disconnect()
        snapshot_obj = SnapshotHelper(dpc_proxy_ip="10.1.21.120", dpc_proxy_port=42221)
        snapshot_obj.setup_snapshot()
        fun_test.sleep(message="wait for traffic", seconds=10)
        ss = snapshot_obj.run_snapshot()
        snapshot_obj.exit_snapshot()
        fun_test.log(ss)

        print snapshot_obj.get_snapshot_main_sfg(ss)
        dut_rx_port_results = network_controller_obj.peek_fpg_port_stats(5)
        fun_test.log(dut_rx_port_results)
        print snapshot_obj.get_snapshot_meter_id(snapshot_output=ss)
        print snapshot_obj.get_snapshot_meter_id(snapshot_output=ss, erp=True)
        print snapshot_obj.get_snapshot_acl_label(ss, erp=True)
        print snapshot_obj.get_pkt_color_from_snapshot(ss, erp=True)

    def run(self):
        pass

    def cleanup(self):
        pass


if __name__ == '__main__':
    ts = Setup()
    ts.add_test_case(SnapshotTest())
    ts.run()
