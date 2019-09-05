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
OUTPUT_JSON_FILE_NAME = "nu_rfc2544_l4_firewall.json"
older_build = False
frame_threshold = 100
throughput_threshold = 1


class ScriptSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Connect to DPCSH and configure egress NU/HNU buffer_pool and enable global PFC
        """)

    def setup(self):
        global dut_config, network_controller_obj, spirent_config, TIMESTAMP, publish_results, branch_name

        nu_config_obj = NuConfigManager()
        f1_index = nu_config_obj.get_f1_index()
        if not f1_index:
            f1_index = 1
        if fun_test.get_job_environment_variable('test_bed_type') == 'fs-7':
            bootargs = 'app=hw_hsu_test sku=SKU_FS1600_0 --dpc-server --dis-stats --dpc-uart --csr-replay --all_100g --disable-wu-watchdog \
                                    override={"NetworkUnit/VP":[{"nu_bm_alloc_clusters":255,}]} hbm-coh-pool-mb=550 hbm-ncoh-pool-mb=3303'
            # fs = Fs.get(disable_f1_index=f1_index)
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

        inputs = fun_test.shared_variables['inputs']
        publish_results = True
        branch_name = None
        if inputs:
            if 'publish_results' in inputs:
                publish_results = inputs['publish_results']

        if 'funos_branch' in fun_test.shared_variables:
            branch_name = fun_test.shared_variables['funos_branch']

        mode = 3
        num_flows = 268435456
        benchmark_ports = [8, 12, 0 ,20]

        result = network_controller_obj.set_etp(pkt_adj_size=8)
        fun_test.simple_assert(result['status'], "Reset pkt_adj_size to 8")

        output_1 = network_controller_obj.set_nu_benchmark_1(mode=mode, num_flows=num_flows, flow_le_ddr=True,
                                                             flow_state_ddr=True)
        for fpg in benchmark_ports:
            result = network_controller_obj.set_nu_benchmark_1(mode=mode, fpg=fpg)
            fun_test.simple_assert(result['status'], 'Enable Firewall benchmark')

        output_2 = network_controller_obj.set_nu_benchmark_1(mode=mode, sport="10-2058", dport="10000-26384", protocol=17,
                                                             ip_sa="29.1.1.1", ip_da="29.1.1.2", flow_offset=0,
                                                             flow_inport=8, flow_outport=12)

        output_3 = network_controller_obj.set_nu_benchmark_1(mode=mode, sport="10-2058", dport="10000-26384", protocol=17,
                                                             ip_sa="29.1.1.1", ip_da="29.1.1.2", flow_offset=33554432,
                                                             flow_inport=0, flow_outport=20)

        output_4 = network_controller_obj.set_nu_benchmark_1(mode=mode, sport="10-2058", dport="10000-26384", protocol=17,
                                                             ip_sa="29.1.1.1", ip_da="29.1.1.2", flow_offset=67108864,
                                                             flow_inport=12, flow_outport=8)
        
        output_5 = network_controller_obj.set_nu_benchmark_1(mode=mode, sport="10-2058", dport="10000-26384", protocol=17,
                                                             ip_sa="29.1.1.1", ip_da="29.1.1.2", flow_offset=100663296,
                                                             flow_inport=20, flow_outport=0)

        sf_thr = 500
        sx_thr = 10
        df_thr = 15000
        dx_thr = 10
        fcp_thr = 10
        nonfcp_thr = 16000
        sf_xoff_thr = 1800
        fcp_xoff_thr = 8
        nonfcp_xoff_thr = 15800
        sf_xon_thr = 400
        fcp_xon_thr = 6
        nonfcp_xon_thr = 15500

        set_1 = network_controller_obj.set_qos_egress_buffer_pool(sf_thr=sf_thr, sx_thr=sx_thr, dx_thr=dx_thr, df_thr=df_thr,
                                                                  fcp_thr=fcp_thr, nonfcp_thr=nonfcp_thr, sf_xoff_thr=sf_xoff_thr,
                                                                  fcp_xoff_thr=fcp_xoff_thr, nonfcp_xoff_thr=nonfcp_xoff_thr,
                                                                  sf_xon_thr=sf_xon_thr, fcp_xon_thr=fcp_xon_thr,
                                                                  nonfcp_xon_thr=nonfcp_xon_thr)

        set_2 = network_controller_obj.set_qos_egress_queue_buffer(port_num=27, queue_num=0, dynamic_enable=0, min_threshold=15000)
        set_3 = network_controller_obj.set_qos_egress_queue_buffer(port_num=35, queue_num=0, dynamic_enable=0, min_threshold=15000)
        set_4 = network_controller_obj.set_qos_egress_queue_buffer(port_num=43, queue_num=0, dynamic_enable=0, min_threshold=15000)
        
        out = network_controller_obj.poke_fcp_config_scheduler(total_bw=400, fcp_ctl_bw=10, fcp_data_bw=10)

        TIMESTAMP = get_current_time()

    def cleanup(self):
        if 'fs' in fun_test.shared_variables:
            fs = fun_test.shared_variables['fs']
            fs.cleanup()


class TestL4FirewallPerformance(FunTestCase):
    tc_id = 1
    template_obj = None
    flow_direction = FLOW_TYPE_NU_LE_VP_NU_L4_FW
    tcc_file_name = "l4_firewall_4M_flows_throughput.tcc"  # Uni-directional
    spray = True
    half_load_latency = False
    num_flows = 4000000
    update_charts = True
    update_json = True
    single_flow = False
    total_test_time = 20
    initial_test_time = 10

    def _get_tcc_config_file_path(self, flow_direction):
        dir_name = None
        if flow_direction == FLOW_TYPE_NU_LE_VP_NU_L4_FW:
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
                              summary="RFC-2544 Flow: %s Frames: [64B, IMIX],"
                                      "To get throughput and full load latency for L4 Firewall" % (
                                          self.flow_direction),
                              steps="""
                              1. Dump PSW, BAM and vppkts stats before tests 
                              2. Initialize RFC-2544 and load existing tcc configuration 
                              3. Start Sequencer
                              4. Wait for sequencer to complete
                              5. Dump PSW, BAM and vppkts stats after tests
                              5. Fetch Results and validate that test result for each frame size [64, IMIX]
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

        #fun_test.log("Fetching flow output")
        #network_controller_obj.show_nu_benchmark(flow_offset=1000000, num_flows=10, show="1")

        checkpoint = "Start Sequencer"
        result = self.template_obj.start_sequencer()
        fun_test.test_assert(result, checkpoint)

        sequencer_handle = self.template_obj.get_sequencer_handle()

        output = run_dpcsh_commands(template_obj=self.template_obj, sequencer_handle=sequencer_handle,
                                    network_controller_obj=network_controller_obj,
                                    test_type=MEMORY_TYPE_HBM, single_flow=self.single_flow,
                                    half_load_latency=self.half_load_latency, test_time=self.total_test_time)

        fun_test.log("Fetching PSW NU Global stats after test")
        network_controller_obj.peek_psw_global_stats()

        fun_test.log("Fetching VP packets after test")
        vp_stats_after = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)

        diff_vp_stats = get_diff_stats(old_stats=vp_stats_before, new_stats=vp_stats_after)
        fun_test.log("VP Diff stats: %s" % diff_vp_stats)

        if not int(diff_vp_stats[VP_PACKETS_FORWARDING_NU_LE]) > 0:
            display_negative_results = True
            fun_test.log("VP packets not going via NU LE")

        if not int(diff_vp_stats[VP_PACKETS_NU_LE_LOOKUP_MISS]) == 0:
            display_negative_results = display_negative_results or True
            fun_test.log("VP packets shows nu le lookup miss for %s packets" % (int(diff_vp_stats[VP_PACKETS_NU_LE_LOOKUP_MISS])))

        fun_test.log("Fetching BAM stats after test")
        network_controller_obj.peek_resource_bam_stats()

        fun_test.log("Fetching per VP stats after traffic")
        network_controller_obj.peek_per_vp_stats()

        #fun_test.log("Fetching flow output")
        #network_controller_obj.show_nu_benchmark(flow_offset=1000000, num_flows=10, show="1")

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


class TestL4FirewallLatency(TestL4FirewallPerformance):
    tc_id = 2
    tcc_file_name = "l4_firewall_4M_flows_latency.tcc"  # Uni-directional
    spray = True
    half_load_latency = True
    num_flows = 4000000
    update_charts = True
    update_json = True
    single_flow = False

    def describe(self):
        self.set_test_details(id=self.tc_id,
                              summary="RFC-2544 Flow: %s, Spray: %s, Frames: [64B, 1500B, IMIX],"
                                      "To get half load latency for L4 Firewall" % (
                                          self.flow_direction, self.spray),
                              steps="""
                              1. Dump PSW, BAM and vppkts stats before tests 
                              2. Initialize RFC-2544 and load existing tcc configuration 
                              3. Start Sequencer
                              4. Wait for sequencer to complete
                              5. Dump PSW, BAM and vppkts stats after tests
                              5. Fetch Results and validate that test result for each frame size [64, 1500, IMIX]
                              """)


class TestL4FirewallPerformance128M(TestL4FirewallPerformance):
    tc_id = 3
    tcc_file_name = "l4_firewall_128M_flows_throughput.tcc"  # Uni-directional
    spray = False
    half_load_latency = False
    num_flows = 128000000
    update_charts = True
    update_json = True
    single_flow = False
    test_frame_sizes = [64.0]
    total_test_time = 20

    def describe(self):
        self.set_test_details(id=self.tc_id,
                              summary="RFC-2544 Flow: %s Frames: %s,"
                                      "To get pps and throughput for 128M flows" % (
                                          self.flow_direction),
                              steps="""
                              1. Upload tcc file 
                              2. Start traffic for stream size
                              3. Start generator for single port at a time.
                              4. Check tx, rx pps and throughput
                              5. If above step passes, start generator for next port.
                              6. Repeat steps 1-5 till all ports are covered.
                              7. Once max number of ports are found wher tx and rx pps and throughput matches;
                                 run traffic for 120 seconds.
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
        # Subscribe to results
        project = self.template_obj.stc_manager.get_project_handle()
        subscribe_results = self.template_obj.subscribe_to_all_results(parent=project)
        fun_test.test_assert(subscribe_results['result'], "Subscribing to results")
        del subscribe_results['result']

        result = {}
        port_list = self.template_obj.stc_manager.get_port_list()
        num_ports = len(port_list)
        fun_test.log("Port handles found are %s" % port_list)

        traffic_port_mapper = {}
        traffic_port_mapper[port_list[0]] = port_list[2]
        traffic_port_mapper[port_list[1]] = port_list[3]
        traffic_port_mapper.update(dict([(value, key) for key, value in traffic_port_mapper.items()]))

        # Get all generators
        generator_list = []
        for port in port_list:
            generator_list.append(self.template_obj.stc_manager.get_generator(port))

        fun_test.log("Generator handles found are %s" % generator_list)
        started_generators = []

        first_streamblock = self.template_obj.get_streams_by_port(port_list[0])[0]
        fun_test.log("Streamblock object to be used in test for latency and jitter numbers is %s" % first_streamblock)

        # Test all frame sizes
        for frame_size in self.test_frame_sizes:
            result["pps"] = 0.0
            result["throughput"] = 0.0
            if frame_size == "IMIX":
                frame_size = 362.4

            fun_test.log("Starting test for frame size %s" % frame_size)
            # Start one generator at a time and get throughput and pps
            for generator_handle in generator_list:
                gen_start = self.template_obj.stc_manager.start_generator_command(generator_handle)
                fun_test.add_checkpoint("Started generator %s" % generator_handle)

                fun_test.sleep("Letting traffic run 10 seconds", seconds=self.initial_test_time)

                total_tx_generator_fps = 0.0
                total_rx_analyzer_fps = 0.0
                total_tx_generator_throughput = 0.0
                total_rx_analyzer_throughput = 0.0

                # Sum pps and throughput seen for tx and rx on each port
                for port_obj in port_list:
                    tx_port_generator_results = self.template_obj.stc_manager.get_generator_port_results(
                        port_handle=port_obj, subscribe_handle=subscribe_results['generator_subscribe'])
                    rx_port_analyzer_results = self.template_obj.stc_manager.get_rx_port_analyzer_results(
                        port_handle=traffic_port_mapper[port_obj], subscribe_handle=subscribe_results['analyzer_subscribe'])

                    total_tx_generator_fps += int(tx_port_generator_results['TotalFrameRate'])
                    total_rx_analyzer_fps += int(rx_port_analyzer_results['TotalFrameRate'])

                    total_tx_generator_throughput += float(int(tx_port_generator_results['GeneratorBitRate']) / 1000000)
                    total_rx_analyzer_throughput += float(int(rx_port_analyzer_results['TotalBitRate']) / 1000000)

                lower_fps_limit = total_tx_generator_fps - frame_threshold
                upper_fps_limit = total_rx_analyzer_fps + frame_threshold
                lower_limit_throughput = total_tx_generator_throughput - throughput_threshold
                upper_limit_throughput = total_rx_analyzer_throughput + throughput_threshold

                # Verify rx stats are within limit with tx
                if (total_rx_analyzer_fps >= lower_fps_limit and total_rx_analyzer_fps <= upper_fps_limit and total_rx_analyzer_fps != 0)\
                        and (total_rx_analyzer_throughput >= lower_limit_throughput and total_rx_analyzer_throughput <= upper_limit_throughput and
                    total_rx_analyzer_throughput != 0.0):
                    result['pps'] = total_rx_analyzer_fps
                    result['throughput'] = total_rx_analyzer_throughput
                    started_generators.append(generator_handle)
                    fun_test.log("Max fps and throughput seen when generators %s are running is %s and %s" % (
                    started_generators, result['pps'], result['throughput']))
                else:
                    # Stop traffic if failures are seen
                    if len(started_generators) == 0:
                        started_generators.append(generator_handle)
                    fun_test.log("Difference seen for throughput Tx: %s and Rx: %s for frame size %s and traffic from ports %s"
                                 % (total_rx_analyzer_throughput, total_tx_generator_throughput, frame_size, started_generators))
                    fun_test.log(
                        "Difference seen for pps Tx: %s and Rx: %s for frame size %s and traffic from ports %s"
                        % (total_tx_generator_fps, total_rx_analyzer_fps, frame_size, started_generators))
                    self.template_obj.stc_manager.stop_generator_command(generator_handles=[generator_handle])
                    fun_test.log("Stopped generator %s" % generator_handle)
                    break

            fun_test.log("Max fps and throughput seen when generators %s are running is %s and %s" % (started_generators, result['pps'], result['throughput']))

            fun_test.log("Capture latency and jitter numbers for one streamblocks")

            latency_dict = self.template_obj.get_latency_values_for_streamblock(
                streamblock_handle=first_streamblock,
                rx_streamblock_subscribe_handle=subscribe_results["rx_summary_subscribe"])

            jitter_dict = self.template_obj.get_jitter_values_for_streamblock(
                streamblock_handle=first_streamblock,
                rx_streamblock_subscribe_handle=subscribe_results["rx_summary_subscribe"], change_mode_jitter=True)

            add_result = self.template_obj.populate_non_rfc_performance_json_file(flow_type=self.flow_direction,
                                                                                  frame_size=frame_size,
                                                                                  pps=result["pps"],
                                                                                  throughput=result["throughput"],
                                                                                  filename=OUTPUT_JSON_FILE_NAME,
                                                                                  timestamp=TIMESTAMP,
                                                                                  num_flows=self.num_flows,
                                                                                  latency_min=latency_dict["latency_min"],
                                                                                  latency_max=latency_dict["latency_max"],
                                                                                  latency_avg=latency_dict["latency_avg"],
                                                                                  jitter_min=jitter_dict["jitter_min"],
                                                                                  jitter_max=jitter_dict["jitter_max"],
                                                                                  jitter_avg=jitter_dict["jitter_avg"]
                                                                                  )
            fun_test.test_assert(add_result, message="Added result for frame size %s" % frame_size)

            # Run traffic for remaining time if no significant drops are seen
            if result['pps'] > 0.0:
                fun_test.log("Running traffic for remaining time and populating stats in file")
                generic_file_name_part = "%s_%s" % (str(frame_size), str(self.num_flows))
                populate_stats_file(network_controller_obj=network_controller_obj, test_time=self.total_test_time - self.initial_test_time,
                                    generic_file_name_part=generic_file_name_part)

            fun_test.log("Stop all generators")
            stop = self.template_obj.stc_manager.stop_generator_command(generator_handles=generator_list)
            fun_test.add_checkpoint("Stop traffic generators on all ports")


class TestL4FirewallPerformanceOld128M(TestL4FirewallPerformance):
    tc_id = 4
    template_obj = None
    flow_direction = FLOW_TYPE_NU_LE_VP_NU_L4_FW
    tcc_file_name = "l4_firewall_128M_flows_throughput_old.tcc"
    spray = True
    half_load_latency = False
    num_flows = 128000000
    update_charts = True
    update_json = True
    single_flow = False
    total_test_time = 20
    initial_test_time = 10

    def describe(self):
        self.set_test_details(id=self.tc_id,
                              summary="RFC-2544 Flow: %s,"
                                      "To get pps and throughput for 128M flows" % (
                                          self.flow_direction),
                              steps="""
                              1. Upload tcc file 
                              2. Start traffic for stream size
                              3. Start generator for single port at a time.
                              4. Check tx, rx pps and throughput
                              5. If above step passes, start generator for next port.
                              6. Repeat steps 1-5 till all ports are covered.
                              7. Once max number of ports are found wher tx and rx pps and throughput matches;
                                 run traffic for 120 seconds.
                                  """)

class TestL4FirewallLatencyOld128M(TestL4FirewallPerformance):
    tc_id = 5
    template_obj = None
    flow_direction = FLOW_TYPE_NU_LE_VP_NU_L4_FW
    tcc_file_name = "l4_firewall_128M_flows_latency_old.tcc"
    spray = True
    half_load_latency = True
    num_flows = 128000000
    update_charts = True
    update_json = True
    single_flow = False
    total_test_time = 20
    initial_test_time = 10

    def describe(self):
        self.set_test_details(id=self.tc_id,
                              summary="RFC-2544 Flow: %s,"
                                      "To get latency for 128M flows" % (
                                          self.flow_direction),
                              steps="""
                              1. Upload tcc file 
                              2. Start traffic for stream size
                              3. Start generator for single port at a time.
                              4. Check tx, rx pps and throughput
                              5. If above step passes, start generator for next port.
                              6. Repeat steps 1-5 till all ports are covered.
                              7. Once max number of ports are found wher tx and rx pps and throughput matches;
                                 run traffic for 120 seconds.
                                  """)

if __name__ == '__main__':
    ts = ScriptSetup()

    # Multi flows
    #ts.add_test_case(TestL4FirewallPerformance())
    #ts.add_test_case(TestL4FirewallLatency())
    #ts.add_test_case(TestL4FirewallPerformance128M())
    ts.add_test_case(TestL4FirewallLatencyOld128M())
    ts.add_test_case(TestL4FirewallPerformanceOld128M())
    ts.run()
