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
OUTPUT_JSON_FILE_NAME = "nu_rfc2544_fwd_performance.json"
older_build = False


class ScriptSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Connect to DPCSH and configure etp pkt size
        """)

    def setup(self):
        global dut_config, network_controller_obj, spirent_config, TIMESTAMP, publish_results, \
            branch_name

        nu_config_obj = NuConfigManager()
        f1_index = nu_config_obj.get_f1_index()
        if not f1_index:
            f1_index = 0
        if fun_test.get_job_environment_variable('test_bed_type') == 'fs-7':
            bootargs = 'app=hw_hsu_test sku=SKU_FS1600_0 --dpc-server --dis-stats --dpc-uart --csr-replay --all_100g --disable-wu-watchdog'
            fs = Fs.get(disable_f1_index=f1_index, boot_args=bootargs)
            fun_test.shared_variables['fs'] = fs
            fun_test.test_assert(fs.bootup(reboot_bmc=False), 'FS bootup')

        private_branch_funos = fun_test.get_build_parameter(parameter='BRANCH_FunOS')
        if private_branch_funos:
            fun_test.shared_variables['funos_branch'] = private_branch_funos

        job_inputs = fun_test.get_job_inputs()
        fun_test.shared_variables['inputs'] = job_inputs

        dut_type = nu_config_obj.DUT_TYPE
        fun_test.shared_variables['dut_type'] = dut_type
        spirent_config = nu_config_obj.read_traffic_generator_config()
        dut_config = nu_config_obj.read_dut_config()
        network_controller_obj = NetworkController(dpc_server_ip=dut_config['dpcsh_tcp_proxy_ip'],
                                                   dpc_server_port=dut_config['dpcsh_tcp_proxy_port'])

        network_controller_obj.debug_vp_util()
        '''
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

        nu_port_list = [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
        hnu_port_list = [0, 1, 2, 3]
        shape = 0
        for port in nu_port_list:
            result = network_controller_obj.set_port_mtu(port_num=port, shape=shape, mtu_value=9000)
            fun_test.simple_assert(result, "Set MTU to 9000 on all interfaces")

        for port in hnu_port_list:
            shape = 1
            result = network_controller_obj.set_port_mtu(port_num=port, shape=shape, mtu_value=9000)
            fun_test.simple_assert(result, "Set MTU to 9000 on all interfaces")
        '''
        inputs = fun_test.shared_variables['inputs']
        publish_results = False
        branch_name = None
        publish_results = True
        if inputs:
            if 'publish_results' in inputs:
                publish_results = inputs['publish_results']

        if 'funos_branch' in fun_test.shared_variables:
            branch_name = fun_test.shared_variables['funos_branch']

        if not older_build:
            fwd_benchmark_ports = [8, 12]
            for fpg in fwd_benchmark_ports:
                result = network_controller_obj.set_nu_benchmark_1(mode=1, fpg=fpg)
                fun_test.simple_assert(result['status'], 'Enable FWD benchmark')

            result = network_controller_obj.set_etp(pkt_adj_size=8)
            fun_test.simple_assert(result['status'], "Set pkt_adj_size")
        else:
            fwd_benchmark_ports = [8, 12]
            for fpg in fwd_benchmark_ports:
                result = network_controller_obj.set_nu_benchmark(fpg=fpg, main=1, erp=1, nh_id=4097, clbp_idx=20)
                fun_test.simple_assert(result['status'], 'Enable FWD benchmark')

        TIMESTAMP = get_current_time()

    def cleanup(self):
        if not older_build:
            fwd_benchmark_ports = [8, 12]
            for fpg in fwd_benchmark_ports:
                result = network_controller_obj.set_nu_benchmark_1(mode=0, fpg=fpg)
                fun_test.simple_assert(result['status'], 'Enable FWD benchmark')

            result = network_controller_obj.set_etp(pkt_adj_size=24)
            fun_test.simple_assert(result['status'], "Reset pkt_adj_size to 24")
        else:
            fwd_benchmark_ports = [8, 12]
            for fpg in fwd_benchmark_ports:
                result = network_controller_obj.set_nu_benchmark(fpg=fpg, main=0, erp=1, nh_id=4097, clbp_idx=20)
                fun_test.simple_assert(result['status'], 'Enable FWD benchmark')

        if 'fs' in fun_test.shared_variables:
            fs = fun_test.shared_variables['fs']
            fs.cleanup()


class TestFwdPerformance(FunTestCase):
    tc_id = 1
    template_obj = None
    flow_direction = FLOW_TYPE_NU_VP_NU_FWD_NFCP
    tcc_file_name = "nu_fwd_benchmark_throughput.tcc"  # Uni-directional
    spray = True
    half_load_latency = False
    update_charts = True
    update_json = True
    single_flow = False
    test_time = 20
    test_type = FLOW_TYPE_FWD
    num_flows = 128000000

    def _get_tcc_config_file_path(self, flow_direction):
        dir_name = None
        if flow_direction == FLOW_TYPE_NU_VP_NU_FWD_NFCP:
            dir_name = "nu_nu_vp_fwd"

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
                              summary="RFC-2544 Flow: %s, Spray: %s, Frames: [64B, 1500B, IMIX],"
                                      "To get throughput and full load latency for FWD" % (
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
        display_negative_results = False
        fun_test.log("----------------> Start RFC-2544 test using %s <----------------" % self.tcc_file_name)

        fun_test.log("Fetching per VP stats before traffic")
        network_controller_obj.peek_per_vp_stats()

        fun_test.log("Fetching PSW NU Global stats before test")
        network_controller_obj.peek_psw_global_stats()

        fun_test.log("Fetching VP packets before test")
        vp_stats_before = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)

        fun_test.log("Fetching BAM stats before test")
        network_controller_obj.peek_resource_bam_stats()

        checkpoint = "Start Sequencer"
        result = self.template_obj.start_sequencer()
        fun_test.test_assert(result, checkpoint)

        sequencer_handle = self.template_obj.get_sequencer_handle()

        output = run_dpcsh_commands(template_obj=self.template_obj, sequencer_handle=sequencer_handle, network_controller_obj=network_controller_obj,
                                    test_type=self.test_type, single_flow=self.single_flow, half_load_latency=self.half_load_latency, test_time=self.test_time)

        fun_test.log("Fetching PSW NU Global stats after test")
        network_controller_obj.peek_psw_global_stats()

        fun_test.log("Fetching VP packets after test")
        vp_stats_after = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)

        diff_vp_stats = get_diff_stats(old_stats=vp_stats_before, new_stats=vp_stats_after)
        fun_test.log("VP Diff stats: %s" % diff_vp_stats)

        if not int(diff_vp_stats[VP_PACKETS_FORWARDING_NU_DIRECT]) > 0:
            display_negative_results = True

        fun_test.log("Fetching BAM stats after test")
        network_controller_obj.peek_resource_bam_stats()

        fun_test.log("Fetching per VP stats after traffic")
        network_controller_obj.peek_per_vp_stats()

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
        result = self.template_obj.create_performance_table(result=result_dict['summary_result'],
                                                            table_name=table_name)
        fun_test.simple_assert(result, checkpoint)

        if self.spray or self.single_flow:
            mode = self.template_obj.get_interface_mode_input_speed()
            if not branch_name:
                if publish_results:
                    result = self.template_obj.populate_performance_json_file(result_dict=result_dict['summary_result'],
                                                                              timestamp=TIMESTAMP,
                                                                              mode=mode,
                                                                              flow_direction=self.flow_direction,
                                                                              file_name=OUTPUT_JSON_FILE_NAME,
                                                                              num_flows=self.num_flows,
                                                                              half_load_latency=self.half_load_latency,
                                                                              model_name=JUNIPER_PERFORMANCE_MODEL_NAME,
                                                                              update_charts=self.update_charts,
                                                                              update_json=self.update_json,
                                                                              display_negative_results=display_negative_results)

        fun_test.log("----------------> End RFC-2544 test using %s  <----------------" % self.tcc_file_name)

    def cleanup(self):
        self.template_obj.cleanup()


class TestFwdLatency(TestFwdPerformance):
    tc_id = 2
    template_obj = None
    flow_direction = FLOW_TYPE_NU_VP_NU_FWD_NFCP
    tcc_file_name = "nu_fwd_benchmark_latency.tcc"  # Uni-directional
    spray = True
    half_load_latency = True
    update_charts = True
    update_json = True
    single_flow = False
    num_flows = 128000000

    def describe(self):
        self.set_test_details(id=self.tc_id,
                              summary="RFC-2544 Flow: %s, Spray: %s, Frames: [64B, 1500B, IMIX],"
                                      "To get half load latency for FWD" % (
                                          self.flow_direction, self.spray),
                              steps="""
                              1. Dump PSW, BAM and vppkts stats before tests 
                              2. Initialize RFC-2544 and load existing tcc configuration 
                              3. Start Sequencer
                              4. Wait for sequencer to complete
                              5. Dump PSW, BAM and vppkts stats after tests
                              5. Fetch Results and validate that test result for each frame size [64, 1500, IMIX]
                              """)


class TestFwdSingleFlowFullLoad(TestFwdPerformance):
    tc_id = 3
    tcc_file_name = "nu_fwd_benchmark_single_flow_full_load.tcc"
    spray = False
    half_load_latency = False
    num_flows = 1
    update_charts = True
    update_json = True
    single_flow = True

    def describe(self):
        self.set_test_details(id=self.tc_id,
                              summary="RFC-2544 Flow: %s, Spray: %s, Frames: [64B, 1500B, IMIX],"
                                      "To get throughput and full load latency for single flow in FWD" % (
                                          self.flow_direction, self.spray),
                              steps="""
                              1. Dump PSW, BAM and vppkts stats before tests 
                              2. Initialize RFC-2544 and load existing tcc configuration 
                              3. Start Sequencer
                              4. Wait for sequencer to complete
                              5. Dump PSW, BAM and vppkts stats after tests
                              5. Fetch Results and validate that test result for each frame size [64, 1500, IMIX]
                              """)

class TestFwdSingleFlowHalfLoad(TestFwdPerformance):
    tc_id = 4
    tcc_file_name = "nu_fwd_benchmark_single_flow_half_load.tcc"
    spray = False
    half_load_latency = True
    num_flows = 1
    update_charts = True
    update_json = True
    single_flow = True

    def describe(self):
        self.set_test_details(id=self.tc_id,
                              summary="RFC-2544 Flow: %s, Spray: %s, Frames: [64B, 1500B, IMIX],"
                                      "To get half load latency for single flow in FWD" % (
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
    ts.add_test_case(TestFwdPerformance())
    ts.add_test_case(TestFwdLatency())
    ts.add_test_case(TestFwdSingleFlowFullLoad())
    ts.add_test_case(TestFwdSingleFlowHalfLoad())
    ts.run()
