from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_rfc2544_template import *
from scripts.networking.nu_config_manager import *
from lib.host.network_controller import *
from scripts.networking.helper import *
from lib.host.linux import *
from lib.fun.fs import *

network_controller_obj = None
spirent_config = None
TIMESTAMP = None
OUTPUT_JSON_FILE_NAME = "nu_rfc2544_le_performance.json"
older_build = False


class ScriptSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Connect to DPCSH and configure egress NU/HNU buffer_pool and enable global PFC
        """)

    def setup(self):
        global dut_config, network_controller_obj, spirent_config, TIMESTAMP

        nu_config_obj = NuConfigManager()

        if fun_test.get_job_environment_variable('test_bed_type') == 'fs-7':
            fs = Fs.get()
            fun_test.test_assert(fs.bootup(reboot_bmc=False), 'FS bootup')

        dut_type = nu_config_obj.DUT_TYPE
        fun_test.shared_variables['dut_type'] = dut_type
        spirent_config = nu_config_obj.read_traffic_generator_config()
        dut_config = nu_config_obj.read_dut_config()
        network_controller_obj = NetworkController(dpc_server_ip=dut_config['dpcsh_tcp_proxy_ip'],
                                                   dpc_server_port=dut_config['dpcsh_tcp_proxy_port'])

        #TODO: To be enabled when dpcsh
        '''
        mode = 3
        num_flows = "16777216"
        benchmark_ports = [8, 12]
        
        result = network_controller_obj.set_etp(pkt_adj_size=8)
        fun_test.simple_assert(result['status'], "Reset pkt_adj_size to 8")

        output_1 = network_controller_obj.set_nu_benchmark_1(mode=mode, num_flows=num_flows, flow_le_ddr=False,
                                                             flow_state_ddr=False)
        for fpg in benchmark_ports:
            result = network_controller_obj.set_nu_benchmark_1(mode=mode, fpg=fpg)
            fun_test.simple_assert(result['status'], 'Enable Firewall benchmark')
        
        output_2 = network_controller_obj.set_nu_benchmark_flows(mode=mode, sport="10-1034", dport="10-7810", protocol=17,
                                                             ip_sa="29.1.1.1", ip_da="29.1.1.2", flow_offset=0,
                                                             flow_inport=8, flow_outport=12)


        output_3 = network_controller_obj.set_nu_benchmark_flows(mode=mode, sport="10-1034", dport="10-7810", protocol=17,
                                                             ip_sa="29.1.1.1", ip_da="29.1.1.2", flow_offset=7987200,
                                                             flow_inport=12, flow_outport=8)
        '''
        TIMESTAMP = get_current_time()

    def cleanup(self):
        pass


class TestFirewallPerformance(FunTestCase):
    tc_id = 1
    template_obj = None
    flow_direction = FLOW_TYPE_NU_LE_VP_NU_FWD_NFCP
    tcc_file_name = "nu_le_benchmark_throughput.tcc"  # Uni-directional
    spray = True
    half_load_latency = False

    def _get_tcc_config_file_path(self, flow_direction):
        dir_name = None
        if flow_direction == FLOW_TYPE_NU_LE_VP_NU_FWD_NFCP:
            dir_name = "nu_le_vp_nu_firewall"

        config_type = "palladium_configs"
        dut_type = fun_test.shared_variables['dut_type']
        if dut_type == NuConfigManager.DUT_TYPE_F1:
            config_type = "f1_configs"

        tcc_config_path = fun_test.get_helper_dir_path() + '/%s/%s/%s' % (
            config_type, dir_name, self.tcc_file_name)
        fun_test.debug("Dir Name: %s" % dir_name)
        return tcc_config_path

    def describe(self):
        self.set_test_details(id=self.tc_id,
                              summary="%s RFC-2544 Spray: %s Frames: [64B, 1500B, IMIX] to get throughput" % (
                                  self.flow_direction, self.spray),
                              steps="""
                              1. Dump PSW, BAM and vppkts stats before tests 
                              2. Initialize RFC-2544 and load existing tcc configuration 
                              3. Start Sequencer
                              4. Wait for sequencer to complete
                              5. Dump PSW, BAM and vppkts stats after tests
                              5. Fetch Results and validate that test result for each frame size [64, 1500, IMIX]
                              """)

    def setup(self):
        dut_type = fun_test.shared_variables['dut_type']
        checkpoint = "Initialize RFC-2544 template"
        self.template_obj = Rfc2544Template(spirent_config=spirent_config)
        fun_test.test_assert(self.template_obj, checkpoint)

        tcc_config_path = self._get_tcc_config_file_path(flow_direction=self.flow_direction)

        checkpoint = "Load existing tcc configuration"
        result = self.template_obj.setup(tcc_config_path=tcc_config_path)
        fun_test.test_assert(result['result'], checkpoint)

        if dut_type == NuConfigManager.DUT_TYPE_F1:
            checkpoint = "Enable per-port latency compensation adjustments"
            result = self.template_obj.enable_per_port_latency_adjustments()
            fun_test.test_assert(result, checkpoint)

            checkpoint = "Set compensation mode to REMOVED for each port"
            result = self.template_obj.set_ports_compensation_mode()
            fun_test.test_assert(result, checkpoint)

    def run(self):
        fun_test.log("----------------> Start RFC-2544 test using %s <----------------" % self.tcc_file_name)

        fun_test.log("Fetching per VP stats before traffic")
        network_controller_obj.peek_per_vp_stats()

        fun_test.log("Fetching PSW NU Global stats before test")
        network_controller_obj.peek_psw_global_stats()

        fun_test.log("Fetching VP packets before test")
        vp_stats_before = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)

        fun_test.log("Fetching BAM stats before test")
        network_controller_obj.peek_bam_stats()

        fun_test.log("Fetching flow output")
        network_controller_obj.show_nu_benchmark(flow_offset=1000000, num_flows=10, show="1")

        checkpoint = "Start Sequencer"
        result = self.template_obj.start_sequencer()
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Wait until test is finish"
        result = self.template_obj.wait_until_complete()
        fun_test.test_assert(result, checkpoint)

        fun_test.log("Fetching PSW NU Global stats after test")
        network_controller_obj.peek_psw_global_stats()

        fun_test.log("Fetching VP packets after test")
        vp_stats_after = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)

        diff_vp_stats = get_diff_stats(old_stats=vp_stats_before, new_stats=vp_stats_after)
        fun_test.log("VP Diff stats: %s" % diff_vp_stats)

        fun_test.test_assert(int(diff_vp_stats[VP_PACKETS_FORWARDING_NU_LE]) > 0,
                             "Ensure packets are going through VP NU direct")

        fun_test.log("Fetching BAM stats after test")
        network_controller_obj.peek_bam_stats()

        fun_test.log("Fetching per VP stats after traffic")
        network_controller_obj.peek_per_vp_stats()

        fun_test.log("Fetching flow output")
        network_controller_obj.show_nu_benchmark(flow_offset=1000000, num_flows=10, show="1")

        checkpoint = "Fetch summary result for latency and throughput for all frames and all iterations"
        result_dict = self.template_obj.get_throughput_summary_results_by_frame_size()
        fun_test.test_assert(result_dict['status'], checkpoint)

        # TODO: We need to validate script later on once we know numbers for palladium and F1
        # checkpoint = "Validate results of current run"
        # result = self.template_obj.validate_result(result_dict=result_dict['summary_result'])
        # fun_test.test_assert(result, checkpoint)

        checkpoint = "Display Performance Table"
        table_name = "Performance Numbers for %s flow " % self.flow_direction
        if self.spray:
            table_name += " Spray Enable"
        result = self.template_obj.create_performance_table(result_dict=result_dict['summary_result'],
                                                            table_name=table_name)
        fun_test.simple_assert(result, checkpoint)

        if self.spray:
            mode = self.template_obj.get_interface_mode_input_speed()
            result = self.template_obj.populate_performance_json_file_1(result_dict=result_dict['summary_result'],
                                                                      timestamp=TIMESTAMP,
                                                                      mode=mode,
                                                                      flow_direction=self.flow_direction,
                                                                      file_name=OUTPUT_JSON_FILE_NAME,
                                                                      num_flows=128000000,
                                                                        half_load_latency=self.half_load_latency)
            fun_test.simple_assert(result, "Ensure JSON file created")

        fun_test.log("----------------> End RFC-2544 test using %s  <----------------" % self.tcc_file_name)

    def cleanup(self):
        self.template_obj.cleanup()


class TestFirewallLatency(TestFirewallPerformance):
    tc_id = 2
    tcc_file_name = "nu_le_benchmark_latency.tcc"  # Uni-directional
    spray = True
    half_load_latency = True

    def describe(self):
        self.set_test_details(id=self.tc_id,
                              summary="%s RFC-2544 Spray: %s Frames: [64B, 1500B, IMIX] to get latency" % (
                                  self.flow_direction, self.spray),
                              steps="""
                              1. Dump PSW, BAM and vppkts stats before tests 
                              2. Initialize RFC-2544 and load existing tcc configuration 
                              3. Start Sequencer
                              4. Wait for sequencer to complete
                              5. Dump PSW, BAM and vppkts stats after tests
                              5. Fetch Results and validate that test result for each frame size [64, 1500, IMIX]
                              """)


if __name__ == '__main__':
    ts = ScriptSetup()

    # Multi flows
    ts.add_test_case(TestFirewallPerformance())
    ts.add_test_case(TestFirewallLatency())
    ts.run()