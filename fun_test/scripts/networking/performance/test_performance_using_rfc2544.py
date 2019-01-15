from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_rfc2544_template import *
from scripts.networking.nu_config_manager import *
from lib.host.network_controller import *


network_controller_obj = None
spirent_config = None
TIMESTAMP = None

class ScriptSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Connect to DPCSH and configure egress NU/HNU buffer_pool and enable global PFC
        """)

    def setup(self):
        global dut_config, network_controller_obj, spirent_config, TIMESTAMP

        dut_type = NuConfigManager.DUT_TYPE_PALLADIUM
        spirent_config = nu_config_obj.read_traffic_generator_config()
        dut_config = nu_config_obj.read_dut_config()
        network_controller_obj = NetworkController(dpc_server_ip="10.1.21.120", dpc_server_port=40221)

        checkpoint = "Configure QoS settings"
        enable_pfc = network_controller_obj.enable_qos_pfc()
        fun_test.simple_assert(enable_pfc, "Enable QoS PFC")
        buffer_pool_set = network_controller_obj.set_qos_egress_buffer_pool(fcp_xoff_thr=7000,
                                                                            nonfcp_xoff_thr=7000,
                                                                            df_thr=4000,
                                                                            dx_thr=4000,
                                                                            fcp_thr=8000,
                                                                            nonfcp_thr=8000,
                                                                            sample_copy_thr=255,
                                                                            sf_thr=4000,
                                                                            sf_xoff_thr=3500,
                                                                            sx_thr=4000)
        fun_test.test_assert(buffer_pool_set, checkpoint)

        checkpoint = "Configure HNU QoS settings"
        enable_pfc = network_controller_obj.enable_qos_pfc(hnu=True)
        fun_test.simple_assert(enable_pfc, "Enable QoS PFC")
        buffer_pool_set = network_controller_obj.set_qos_egress_buffer_pool(fcp_xoff_thr=900,
                                                                            nonfcp_xoff_thr=3500,
                                                                            df_thr=2000,
                                                                            dx_thr=1000,
                                                                            fcp_thr=1000,
                                                                            nonfcp_thr=4000,
                                                                            sample_copy_thr=255,
                                                                            sf_thr=2000,
                                                                            sf_xoff_thr=1900,
                                                                            sx_thr=250,
                                                                            mode="hnu")
        fun_test.test_assert(buffer_pool_set, checkpoint)

        TIMESTAMP = get_current_time()

    def cleanup(self):
        pass


class TestTransitPerformance(FunTestCase):
    tc_id = 1
    template_obj = None
    flow_direction = NuConfigManager.FLOW_DIRECTION_NU_NU
    # tcc_config_path = "/tmp/transit_bidirectional_palladium.tcc"
    tcc_config_path = "/tmp/test_all_frame_sizes.tcc"

    def describe(self):
        self.set_test_details(id=1, summary="%s RFC-2544 Latency/Throughput Bi-directional" % self.flow_direction,
                              steps="""
                              1. Dump PSW, BAM stats before tests 
                              2. Initialize RFC-2544 and load existing tcc configuration 
                              3. Start Sequencer
                              4. Wait for sequencer to complete
                              5. Dump PSW, BAM stats after tests
                              5. Fetch Results and validate that test result for each frame size [64, 1500, IMIX]
                              """)

    def setup(self):
        checkpoint = "Initialize RFC-2544 template"
        self.template_obj = Rfc2544Template(spirent_config=spirent_config)
        fun_test.test_assert(self.template_obj, checkpoint)

        checkpoint = "Load existing tcc configuration"
        result = self.template_obj.setup(tcc_config_path=self.tcc_config_path)
        fun_test.test_assert(result['result'], checkpoint)

    def run(self):
        fun_test.log("----------------> Start RFC-2544 test for %s Flow <----------------" % self.flow_direction)
        fun_test.log("Fetching PSW Global stats before test")
        network_controller_obj.peek_psw_global_stats()

        fun_test.log("Fetching BAM stats before test")
        network_controller_obj.peek_bam_stats()

        checkpoint = "Get Sequencer configuration"
        config = self.template_obj.get_sequencer_configuration()
        fun_test.test_assert(config, checkpoint)

        checkpoint = "Start Sequencer"
        result = self.template_obj.start_sequencer()
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Wait until test is finish"
        result = self.template_obj.wait_until_complete()
        fun_test.test_assert(result, checkpoint)

        fun_test.sleep('After traffic before fetching DUT stats', seconds=5)

        fun_test.log("Fetching PSW Global stats before test")
        network_controller_obj.peek_psw_global_stats()

        fun_test.log("Fetching BAM stats before test")
        network_controller_obj.peek_bam_stats()

        checkpoint = "Fetch DB name to read stats"
        db_name = self.template_obj.retrieve_database_file_name()
        fun_test.simple_assert(db_name, checkpoint)

        checkpoint = "Fetch summary result for latency and throughput for all frames and all iterations"
        records = self.template_obj.fetch_summary_result(db_name=db_name)
        fun_test.test_assert(records, checkpoint)

        checkpoint = "Validate results of current run"
        result = self.template_obj.validate_performance_result(records=records)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Display Performance Table"
        result = self.template_obj.create_performance_table(records=records,
                                                            table_name="Performance Numbers for %s flow "
                                                                       "(Bi-directional)" % self.flow_direction)
        fun_test.simple_assert(result, checkpoint)

        checkpoint = "Ensure output JSON populated for performance dashboard"
        result = self.template_obj.populate_performance_json_file(records=records, timestamp=TIMESTAMP,
                                                                  flow_direction=self.flow_direction)
        fun_test.simple_assert(result, checkpoint)
        fun_test.log("----------------> End RFC-2544 test for %s Flow <----------------" % self.flow_direction)

    def cleanup(self):
        self.template_obj.cleanup()


if __name__ == '__main__':
    ts = ScriptSetup()

    ts.add_test_case(TestTransitPerformance())

    ts.run()
