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
OUTPUT_JSON_FILE_NAME = "firewall_ipsec_performance.json"
older_build = False
frame_threshold = 5000
FRAME_SIZE_64B = 64.0
FRAME_SIZE_IMIX = 362.94


class ScriptSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Connect to DPCSH and configure flows
        """)

    def setup(self):
        global dut_config, network_controller_obj, spirent_config, TIMESTAMP, publish_results, branch_name, \
            use_new_tcc, load_profile_only, test_streams, template_obj, multi_flow_encrypt_64B_start_data_mpps, \
            multi_flow_encrypt_64B_end_data_mpps, multi_flow_encrypt_64B_step_data_mpps, \
            multi_flow_encrypt_IMIX_start_data_mpps, multi_flow_encrypt_IMIX_end_data_mpps, \
            multi_flow_encrypt_IMIX_step_data_mpps, single_flow_encrypt_64B_start_data_mpps, \
            single_flow_encrypt_64B_end_data_mpps, single_flow_encrypt_64B_step_data_mpps, \
            single_flow_encrypt_IMIX_start_data_mpps, single_flow_encrypt_IMIX_end_data_mpps,\
            single_flow_encrypt_IMIX_step_data_mpps, multi_flow_decrypt_start_data_mpps, \
            multi_flow_decrypt_end_data_mpps, multi_flow_decrypt_step_data_mpps, \
            single_flow_decrypt_start_data_mpps, single_flow_decrypt_end_data_mpps, single_flow_decrypt_step_data_mpps

        nu_config_obj = NuConfigManager()
        f1_index = nu_config_obj.get_f1_index()
        if not f1_index:
            f1_index = 0
        if fun_test.get_job_environment_variable('test_bed_type') == 'fs-7':
            bootargs = 'app=hw_hsu_test sku=SKU_FS1600_0 --dpc-server --dis-stats --dpc-uart --csr-replay --all_100g --disable-wu-watchdog \
                                                override={"NetworkUnit/VP":[{"nu_bm_alloc_clusters":255,}]} hbm-coh-pool-mb=550 hbm-ncoh-pool-mb=3303'
            #fs = Fs.get(disable_f1_index=f1_index)
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
        test_streams = ["MULTI_FLOW_ENCRYPT_IMIX", "MULTI_FLOW_ENCRYPT_64B", "SINGLE_FLOW_ENCRYPT_64B", "SINGLE_FLOW_ENCRYPT_IMIX",
                        "MULTI_FLOW_DECRYPT", "SINGLE_FLOW_DECRYPT"]
        publish_results = False
        branch_name = None
        publish_results = True
        if inputs:
            if 'publish_results' in inputs:
                publish_results = bool(inputs['publish_results'])

            if 'test_streams' in inputs:
                test_streams = inputs['test_streams']

            multi_flow_encrypt_64B_start_data_mpps = 60
            multi_flow_encrypt_64B_end_data_mpps = 100
            multi_flow_encrypt_64B_step_data_mpps = 5
            multi_flow_encrypt_IMIX_start_data_mpps = 59
            multi_flow_encrypt_IMIX_end_data_mpps = 100
            multi_flow_encrypt_IMIX_step_data_mpps = 5
            single_flow_encrypt_64B_start_data_mpps = 2.6
            single_flow_encrypt_64B_end_data_mpps = 5.6
            single_flow_encrypt_64B_step_data_mpps = 0.5
            single_flow_encrypt_IMIX_start_data_mpps = 2.6
            single_flow_encrypt_IMIX_end_data_mpps = 5.6
            single_flow_encrypt_IMIX_step_data_mpps = 0.5
            multi_flow_decrypt_start_data_mpps = 52
            multi_flow_decrypt_end_data_mpps = 82
            multi_flow_decrypt_step_data_mpps = 5
            single_flow_decrypt_start_data_mpps = 2
            single_flow_decrypt_end_data_mpps = 5
            single_flow_decrypt_step_data_mpps = 0.5

            if 'multi_flow_encrypt_64B_start_data_mpps' in inputs:
                multi_flow_encrypt_64B_start_data_mpps = int(inputs['multi_flow_encrypt_64B_start_data_mpps'])

            if 'multi_flow_encrypt_64B_end_data_mpps' in inputs:
                multi_flow_encrypt_64B_end_data_mpps = int(inputs['multi_flow_encrypt_64B_end_data_mpps'])

            if 'multi_flow_encrypt_64B_step_data_mpps' in inputs:
                multi_flow_encrypt_64B_step_data_mpps = int(inputs['multi_flow_encrypt_64B_step_data_mpps'])

            if 'multi_flow_encrypt_IMIX_start_data_mpps' in inputs:
                multi_flow_encrypt_IMIX_start_data_mpps = int(inputs['multi_flow_encrypt_IMIX_start_data_mpps'])

            if 'multi_flow_encrypt_IMIX_end_data_mpps' in inputs:
                multi_flow_encrypt_IMIX_end_data_mpps = int(inputs['multi_flow_encrypt_IMIX_end_data_mpps'])

            if 'multi_flow_encrypt_IMIX_step_data_mpps' in inputs:
                multi_flow_encrypt_IMIX_step_data_mpps = int(inputs['multi_flow_encrypt_IMIX_step_data_mpps'])

            if 'single_flow_encrypt_64B_start_data_mpps' in inputs:
                single_flow_encrypt_64B_start_data_mpps = int(inputs['single_flow_encrypt_64B_start_data_mpps'])

            if 'single_flow_encrypt_64B_end_data_mpps' in inputs:
                single_flow_encrypt_64B_end_data_mpps = int(inputs['single_flow_encrypt_64B_end_data_mpps'])

            if 'single_flow_encrypt_64B_step_data_mpps' in inputs:
                single_flow_encrypt_64B_step_data_mpps = int(inputs['single_flow_encrypt_64B_step_data_mpps'])

            if 'single_flow_encrypt_IMIX_start_data_mpps' in inputs:
                single_flow_encrypt_IMIX_start_data_mpps = int(inputs['single_flow_encrypt_IMIX_start_data_mpps'])

            if 'single_flow_encrypt_IMIX_end_data_mpps' in inputs:
                single_flow_encrypt_IMIX_end_data_mpps = int(inputs['single_flow_encrypt_IMIX_end_data_mpps'])

            if 'single_flow_encrypt_IMIX_step_data_mpps' in inputs:
                single_flow_encrypt_IMIX_step_data_mpps = int(inputs['single_flow_encrypt_IMIX_step_data_mpps'])

            if 'multi_flow_decrypt_start_data_mpps' in inputs:
                multi_flow_decrypt_start_data_mpps = int(inputs['multi_flow_decrypt_start_data_mpps'])

            if 'multi_flow_decrypt_end_data_mpps' in inputs:
                multi_flow_decrypt_end_data_mpps = int(inputs['multi_flow_decrypt_end_data_mpps'])

            if 'multi_flow_decrypt_step_data_mpps' in inputs:
                multi_flow_decrypt_step_data_mpps = int(inputs['multi_flow_decrypt_step_data_mpps'])

            if 'single_flow_decrypt_start_data_mpps' in inputs:
                single_flow_decrypt_start_data_mpps = int(inputs['single_flow_decrypt_start_data_mpps'])

            if 'single_flow_decrypt_end_data_mpps' in inputs:
                single_flow_decrypt_end_data_mpps = int(inputs['single_flow_decrypt_end_data_mpps'])

            if 'multi_flow_encrypt_64B_start_data_mpps' in inputs:
                single_flow_decrypt_step_data_mpps = int(inputs['single_flow_decrypt_step_data_mpps'])

        if 'funos_branch' in fun_test.shared_variables:
            branch_name = fun_test.shared_variables['funos_branch']

        mode = 3
        num_flows = 8192
        benchmark_ports = [8, 12, 0, 20]

        result = network_controller_obj.set_etp(pkt_adj_size=8)
        fun_test.simple_assert(result['status'], "Reset pkt_adj_size to 8")

        output_1 = network_controller_obj.set_nu_benchmark_1(mode=mode, num_flows=num_flows, flow_le_ddr=True,
                                                             flow_state_ddr=True)
        for fpg in benchmark_ports:
            result = network_controller_obj.set_nu_benchmark_1(mode=mode, fpg=fpg)
            fun_test.simple_assert(result['status'], 'Enable Firewall benchmark')

        fun_test.log("Add ipsec encryption SAs")
        mode_4 = 4
        ipsec = network_controller_obj.set_nu_benchmark_1(mode=mode_4, num_tunnels=64, is_encryption=True, spi=1024,
                                                          tunnel_src="1.1.1.1", tunnel_dst="1.1.1.2")

        output_2 = network_controller_obj.set_nu_benchmark_1(mode=mode_4, sport="1024-1040", dport="80-81", protocol=17,
                                                             ip_sa="29.1.1.1", ip_da="29.1.1.2", flow_offset=0,
                                                             flow_inport=8, flow_outport=12, ipsec=True)

        output_3 = network_controller_obj.set_nu_benchmark_1(mode=mode_4, sport="1040-1056", dport="80-81", protocol=17,
                                                             ip_sa="29.1.1.1", ip_da="29.1.1.2", flow_offset=16,
                                                             flow_inport=0, flow_outport=20, ipsec=True)

        output_4 = network_controller_obj.set_nu_benchmark_1(mode=mode_4, sport="1056-1072", dport="80-81", protocol=17,
                                                             ip_sa="29.1.1.1", ip_da="29.1.1.2", flow_offset=32,
                                                             flow_inport=12, flow_outport=8, ipsec=True)

        output_5 = network_controller_obj.set_nu_benchmark_1(mode=mode_4, sport="1072-1088", dport="80-81", protocol=17,
                                                             ip_sa="29.1.1.1", ip_da="29.1.1.2", flow_offset=48,
                                                             flow_inport=20, flow_outport=0, ipsec=True)

        # Decrypt
        ipsec = network_controller_obj.set_nu_benchmark_1(mode=mode_4, num_tunnels=64, is_encryption=False, spi=4000,
                                                          tunnel_src="1.1.1.2", tunnel_dst="1.1.1.1")
        output_6 = network_controller_obj.set_nu_benchmark_1(mode=mode_4, sport="0-1", dport="4000-4016", protocol=50,
                                                             ip_sa="1.1.1.2", ip_da="1.1.1.1", flow_offset=64,
                                                             flow_inport=8, flow_outport=12, ipsec=True)

        output_7 = network_controller_obj.set_nu_benchmark_1(mode=mode_4, sport="0-1", dport="4016-4032", protocol=50,
                                                             ip_sa="1.1.1.2", ip_da="1.1.1.1", flow_offset=80,
                                                             flow_inport=0, flow_outport=20, ipsec=True)

        output_8 = network_controller_obj.set_nu_benchmark_1(mode=mode_4, sport="0-1", dport="4032-4048", protocol=50,
                                                             ip_sa="1.1.1.2", ip_da="1.1.1.1", flow_offset=96,
                                                             flow_inport=12, flow_outport=8, ipsec=True)

        output_9 = network_controller_obj.set_nu_benchmark_1(mode=mode_4, sport="0-1", dport="4048-4064", protocol=50,
                                                             ip_sa="1.1.1.2", ip_da="1.1.1.1", flow_offset=112,
                                                             flow_inport=20, flow_outport=0, ipsec=True)

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

        set_1 = network_controller_obj.set_qos_egress_buffer_pool(sf_thr=sf_thr, sx_thr=sx_thr, dx_thr=dx_thr,
                                                                  df_thr=df_thr,
                                                                  fcp_thr=fcp_thr, nonfcp_thr=nonfcp_thr,
                                                                  sf_xoff_thr=sf_xoff_thr,
                                                                  fcp_xoff_thr=fcp_xoff_thr,
                                                                  nonfcp_xoff_thr=nonfcp_xoff_thr,
                                                                  sf_xon_thr=sf_xon_thr, fcp_xon_thr=fcp_xon_thr,
                                                                  nonfcp_xon_thr=nonfcp_xon_thr)

        set_2 = network_controller_obj.set_qos_egress_queue_buffer(port_num=27, queue_num=0, dynamic_enable=0,
                                                                   min_threshold=15000)
        set_3 = network_controller_obj.set_qos_egress_queue_buffer(port_num=35, queue_num=0, dynamic_enable=0,
                                                                   min_threshold=15000)
        set_4 = network_controller_obj.set_qos_egress_queue_buffer(port_num=43, queue_num=0, dynamic_enable=0,
                                                                   min_threshold=15000)

        out = network_controller_obj.poke_fcp_config_scheduler(total_bw=400, fcp_ctl_bw=10, fcp_data_bw=10)

        TIMESTAMP = get_current_time()

        # Upload tcc file to spirent and reserve ports
        fun_test.log("Upload tcc file to spirent and reserve ports")
        dut_type = fun_test.shared_variables['dut_type']
        checkpoint = "Initialize RFC-2544 template"
        template_obj = Rfc2544Template(spirent_config=spirent_config)
        fun_test.test_assert(template_obj, checkpoint)

        tcc_config_path = self._get_tcc_config_file_path()

        checkpoint = "Load existing tcc configuration"
        result = template_obj.setup(tcc_config_path=tcc_config_path)
        fun_test.test_assert(result['result'], checkpoint)

        if dut_type == NuConfigManager.DUT_TYPE_F1:
            checkpoint = "Enable per-port latency compensation adjustments"
            result = template_obj.enable_per_port_latency_adjustments()
            fun_test.test_assert(result, checkpoint)

            checkpoint = "Set compensation mode to REMOVED for each port"
            result = template_obj.set_ports_compensation_mode()
            fun_test.test_assert(result, checkpoint)

    def _get_tcc_config_file_path(self):
        dir_name = "nu_le_vp_nu_firewall"

        config_type = "palladium_configs"
        dut_type = fun_test.shared_variables['dut_type']
        if dut_type == NuConfigManager.DUT_TYPE_F1:
            config_type = "f1_configs"

        tcc_file_name = "ipsec.tcc"

        tcc_config_path = fun_test.get_helper_dir_path() + '/%s/%s/%s' % (
            config_type, dir_name, tcc_file_name)
        fun_test.debug("Dir Name: %s" % dir_name)
        return tcc_config_path

    def cleanup(self):
        if 'fs' in fun_test.shared_variables:
            fs = fun_test.shared_variables['fs']
            fs.cleanup()


class TestL4IPsecPerformance(FunTestCase):
    tc_id = 1
    tcc_file_name = "ipsec.tcc"
    total_test_time = 20
    initial_test_time = 10

    def describe(self):
        self.set_test_details(id=self.tc_id,
                              summary="RFC-2544, Frames: [64B, IMIX],"
                                      "To get throughput and multi/single tunnel for IPSEC Encrypt/Decrypt",
                              steps="""
                              1. Dump PSW, BAM and vppkts stats before tests 
                              2. Initialize RFC-2544 and load existing tcc configuration 
                              3. Start Sequencer
                              4. Wait for sequencer to complete
                              5. Dump PSW, BAM and vppkts stats after tests
                              5. Fetch Results and validate that test result for each frame size [64, IMIX]
                              """)

    def setup(self):
        pass

    def cleanup(self):
        pass

    def calculate_throughput(self, pps_mpps, frame_size):
        return pps_mpps * (frame_size + 20) * 8

    def run(self):
        default_load_pps = 10

        # Subscribe to results
        project = template_obj.stc_manager.get_project_handle()
        subscribe_results = template_obj.subscribe_to_all_results(parent=project)
        fun_test.test_assert(subscribe_results['result'], "Subscribing to results")
        del subscribe_results['result']

        result = {}
        port_list = template_obj.stc_manager.get_port_list()
        num_ports = len(port_list)
        fun_test.log("Port handles found are %s" % port_list)

        # Get all generators
        generator_list = []
        for port in port_list:
            generator_list.append(template_obj.stc_manager.get_generator(port))

        handle_list = []
        for port_handle in port_list:
            handles = template_obj.stc_manager.get_stream_handle_list(port_handle)
            handle_list.extend(handles)

        for stream in test_streams:
            update_attributes = {"Load": default_load_pps}
            for traffic_streamblock in handle_list:
                template_obj.stc_manager.update_stream_block(traffic_streamblock, update_attributes)
            fun_test.log("Updated frame load to %s on each port" % default_load_pps)

            fun_test.sleep("Letting remaining traffic go through", seconds=10)

            result[stream] = {}
            result[stream]['pps'] = -1
            result[stream]['throughput'] = -1
            result[stream]['main_pkt_drop_eop'] = 0
            result[stream][VP_PACKETS_NU_LE_LOOKUP_MISS] = 0
            current_test_streamblocks = []
            for handle in handle_list:
                streamblock_params = template_obj.stc_manager.get_stream_parameters(handle)
                if stream == streamblock_params['Name']:
                    current_test_streamblocks.append(handle)

            if 'MULTI_FLOW_ENCRYPT_64B' in stream:
                start_data = multi_flow_encrypt_64B_start_data_mpps
                end_data = multi_flow_encrypt_64B_end_data_mpps
                step_data = multi_flow_encrypt_64B_step_data_mpps
                frame_size = FRAME_SIZE_64B
                self.flow_direction = IPSEC_ENCRYPT_MULTI_TUNNEL
            elif 'MULTI_FLOW_ENCRYPT_IMIX' in stream:
                start_data = multi_flow_encrypt_IMIX_start_data_mpps
                end_data = multi_flow_encrypt_IMIX_end_data_mpps
                step_data = multi_flow_encrypt_IMIX_step_data_mpps
                frame_size = FRAME_SIZE_IMIX
                self.flow_direction = IPSEC_ENCRYPT_MULTI_TUNNEL
            elif 'SINGLE_FLOW_ENCRYPT_64B' in stream:
                start_data = single_flow_encrypt_64B_start_data_mpps
                end_data = single_flow_encrypt_64B_end_data_mpps
                step_data = single_flow_encrypt_64B_step_data_mpps
                frame_size = FRAME_SIZE_64B
                self.flow_direction = IPSEC_ENCRYPT_SINGLE_TUNNEL
            elif 'SINGLE_FLOW_ENCRYPT_IMIX' in stream:
                start_data = single_flow_encrypt_IMIX_start_data_mpps
                end_data = single_flow_encrypt_IMIX_end_data_mpps
                step_data = single_flow_encrypt_IMIX_step_data_mpps
                frame_size = FRAME_SIZE_IMIX
                self.flow_direction = IPSEC_ENCRYPT_SINGLE_TUNNEL
            elif 'MULTI_FLOW_DECRYPT' in stream:
                start_data = multi_flow_decrypt_start_data_mpps
                end_data = multi_flow_decrypt_end_data_mpps
                step_data = multi_flow_decrypt_step_data_mpps
                frame_size = FRAME_SIZE_IMIX
                self.flow_direction = IPSEC_DECRYPT_MULTI_TUNNEL
            elif 'SINGLE_FLOW_DECRYPT' in stream:
                start_data = single_flow_decrypt_start_data_mpps
                end_data = single_flow_decrypt_end_data_mpps
                step_data = single_flow_decrypt_step_data_mpps
                frame_size = FRAME_SIZE_IMIX
                self.flow_direction = IPSEC_DECRYPT_SINGLE_TUNNEL


            current_data = start_data
            continue_higher = True
            while current_data <= end_data and continue_higher:
                total_rate = current_data * 1000000
                single_port_rate = float(total_rate/num_ports)
                update_attributes = {"Load": single_port_rate}
                if 'SINGLE' in stream:
                    single_port_rate = float(total_rate)
                    update_attributes = {"Load": single_port_rate}
                for traffic_streamblock in current_test_streamblocks:
                    template_obj.stc_manager.update_stream_block(traffic_streamblock, update_attributes)
                fun_test.log("Updated frame load to %s on each port" % single_port_rate)

                run_time_psw_stats_before = network_controller_obj.peek_psw_global_stats()

                start_streams = template_obj.stc_manager.start_traffic_stream(
                    stream_blocks_list=current_test_streamblocks)
                fun_test.sleep("Started streamblock %s" % current_test_streamblocks)

                fun_test.sleep("Letting traffic run", seconds=self.initial_test_time)
                total_tx_generator_fps = 0.0
                total_rx_analyzer_fps = 0.0

                for port_obj in port_list:
                    tx_port_generator_results = template_obj.stc_manager.get_generator_port_results(
                        port_handle=port_obj, subscribe_handle=subscribe_results['generator_subscribe'])
                    rx_port_analyzer_results = template_obj.stc_manager.get_rx_port_analyzer_results(
                        port_handle=port_obj, subscribe_handle=subscribe_results['analyzer_subscribe'])

                    total_tx_generator_fps += int(tx_port_generator_results['TotalFrameRate'])
                    total_rx_analyzer_fps += int(rx_port_analyzer_results['TotalFrameRate'])

                fun_test.log("total Tx Frame rate is %s and Rx frame rate is %s for stream %s at load %s mpps" %
                             (total_tx_generator_fps, total_rx_analyzer_fps, stream, current_data))

                run_time_psw_stats_after = network_controller_obj.peek_psw_global_stats()
                output = get_psw_diff_counters(hnu_1=False, hnu_2=False, input_list=['main_pkt_drop_eop'],
                                               psw_stats_nu_1=run_time_psw_stats_before, psw_stats_nu_2=run_time_psw_stats_after)

                main_pkt_drop = int(output["input"]['main_pkt_drop_eop'])
                if main_pkt_drop <= 10:
                    result[stream]['pps'] = total_rx_analyzer_fps
                    result[stream]['throughput'] = self.calculate_throughput(current_data, frame_size)
                    fun_test.log("Max fps and throughput seen when pps %s are running is %s and %s" % (
                        total_rate, result[stream]['pps'], result[stream]['throughput']))
                    working_load = single_port_rate
                else:
                    fun_test.log("main pkt eop drop seen is %s" % main_pkt_drop)
                    fun_test.log("Difference seen for pps Tx: %s and Rx: %s for frame %s at rate %s" % (total_tx_generator_fps, total_rx_analyzer_fps,
                                                                                                        stream, single_port_rate * num_ports))
                    continue_higher = False

                stop_streams = template_obj.stc_manager.stop_traffic_stream(
                    stream_blocks_list=current_test_streamblocks)

                fun_test.sleep("Letting traffic be dispersed")

                fun_test.log("Updating load value")
                current_data = current_data + step_data

            add_result = template_obj.populate_non_rfc_performance_json_file(flow_type=self.flow_direction,
                                                                             frame_size=frame_size,
                                                                             pps=result[stream]["pps"],
                                                                             throughput=result[stream]['throughput'],
                                                                             filename=OUTPUT_JSON_FILE_NAME,
                                                                             timestamp=TIMESTAMP)
            fun_test.add_checkpoint("Added result for frame size %s" % frame_size)

            # Run traffic for remaining time if no significant drops are seen
            if result[stream]['pps'] > 0.0:
                update_attributes = {"Load": working_load}
                for traffic_streamblock in current_test_streamblocks:
                    template_obj.stc_manager.update_stream_block(traffic_streamblock, update_attributes)
                fun_test.log("Updated frame load to max working load %s on each port" % working_load)

                start_streams = template_obj.stc_manager.start_traffic_stream(
                    stream_blocks_list=current_test_streamblocks)
                fun_test.sleep("Started streamblock %s" % current_test_streamblocks)

                psw_stats_before = network_controller_obj.peek_psw_global_stats()

                fun_test.log("Fetching VP packets before test")
                vp_stats_before = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)

                fun_test.log("Running traffic for remaining time and populating stats in file")
                generic_file_name_part = "%s" % (str(stream))
                populate_stats_file(network_controller_obj=network_controller_obj,
                                    test_time=self.total_test_time - self.initial_test_time,
                                    generic_file_name_part=generic_file_name_part)

                # Update PSW stat in dict
                psw_stats_after = network_controller_obj.peek_psw_global_stats()
                output = get_psw_diff_counters(hnu_1=False, hnu_2=False, input_list=['main_pkt_drop_eop'],
                                               psw_stats_nu_1=psw_stats_before, psw_stats_nu_2=psw_stats_after)
                result[stream]['main_pkt_drop_eop'] = int(output["input"]['main_pkt_drop_eop'])
                fun_test.log(
                    "PSW pakcet drop seen for %s stream is %s" % (
                    stream, result[stream]['main_pkt_drop_eop']))

                fun_test.log("Fetching VP packets after test")
                vp_stats_after = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)

                # Update lookup stat in dict
                diff_vp_stats = get_diff_stats(old_stats=vp_stats_before, new_stats=vp_stats_after)
                fun_test.log("VP Diff stats: %s" % diff_vp_stats)

                result[stream][VP_PACKETS_NU_LE_LOOKUP_MISS] = int(diff_vp_stats[VP_PACKETS_NU_LE_LOOKUP_MISS])
                fun_test.log(
                    "NU LE lookup miss seen for %s stream is %s" % (
                    stream, result[stream][VP_PACKETS_NU_LE_LOOKUP_MISS]))

                stop_streams = template_obj.stc_manager.stop_traffic_stream(
                    stream_blocks_list=current_test_streamblocks)
                fun_test.sleep("Stopped streamblock %s" % current_test_streamblocks)

                update_attributes = {"Load": default_load_pps}
                for traffic_streamblock in current_test_streamblocks:
                    template_obj.stc_manager.update_stream_block(traffic_streamblock, update_attributes)
                fun_test.log("Updated frame load to %s" % default_load_pps)

        for stream in test_streams:
            fun_test.test_assert_expected(expected=0, actual=result[stream]['main_pkt_drop_eop'],
                                          message="Check no psw main_pkt_drop_eop seen for %s" % stream)
            fun_test.test_assert_expected(expected=0, actual=result[stream][VP_PACKETS_NU_LE_LOOKUP_MISS],
                                          message="Check no le lookup miss seen for %s" % stream)


if __name__ == '__main__':
    ts = ScriptSetup()

    # Multi flows
    ts.add_test_case(TestL4IPsecPerformance())
    ts.run()
