"""
Author: Rushikesh Pendse

Includes Following Sampling Cases
1. SampleIngressFPGtoFPG
2. SampleIngressFPGtoFPGWithRate
3. SampleFCOIngressFPGtoFPG
4. SamplePPStoFPG
5. SampleEgressFPGtoFPG
6. SampleIngressEnableDisable
"""

from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_traffic_generator_template import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import *
from lib.host.network_controller import *
from scripts.networking.nu_config_manager import *
from scripts.networking.helper import *
from lib.utilities.pcap_parser import *

spirent_config = {}
subscribed_results = None
TRAFFIC_DURATION = 30
NUM_PORTS = 3
generator_port_obj_dict = {}
analyzer_port_obj_dict = {}


class SpirentSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Configure Spirent Ports (No of ports needed 3)
        2. Configure Generator Configs and Get Generator Handle for Tx Port
        3. Subscribed to all types of results 
        """)

    def setup(self):
        global spirent_config, subscribed_results, dut_config, template_obj, network_controller_obj, tx_port, rx_port, \
            sample_port, generator_port_obj_dict, analyzer_port_obj_dict, generator_config, analyzer_config

        spirent_config = nu_config_obj.read_traffic_generator_config()

        dut_config = nu_config_obj.read_dut_config(dut_type=None, flow_type=NuConfigManager.SAMPLE_FLOW_TYPE,
                                                   flow_direction=NuConfigManager.FLOW_DIRECTION_NU_NU)

        template_obj = SpirentEthernetTrafficTemplate(session_name="sample", spirent_config=spirent_config,
                                                      chassis_type=nu_config_obj.CHASSIS_TYPE)
        result = template_obj.setup(no_of_ports_needed=NUM_PORTS, flow_type=NuConfigManager.SAMPLE_FLOW_TYPE,
                                    flow_direction=NuConfigManager.FLOW_DIRECTION_NU_NU)
        fun_test.test_assert(result['result'], "Ensure Setup is done")

        dpc_server_ip = dut_config["dpcsh_tcp_proxy_ip"]
        dpc_server_port = dut_config["dpcsh_tcp_proxy_port"]

        tx_port = result['port_list'][0]
        rx_port = result['port_list'][1]
        sample_port = result['port_list'][2]

        generator_config = GeneratorConfig(scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED,
                                           duration=TRAFFIC_DURATION,
                                           duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                           time_stamp_latch_mode=GeneratorConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)

        analyzer_config = AnalyzerConfig(timestamp_latch_mode=AnalyzerConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)

        for port in result['port_list']:
            checkpoint = "Create Generator Config for %s port" % port
            result = template_obj.configure_generator_config(port_handle=port,
                                                             generator_config_obj=generator_config)
            fun_test.simple_assert(expression=result, message=checkpoint)

            checkpoint = "Create Analyzer Config for %s port" % port
            result = template_obj.configure_analyzer_config(port_handle=port,
                                                            analyzer_config_obj=analyzer_config)
            fun_test.simple_assert(result, checkpoint)

            generator_port_obj_dict[port] = template_obj.stc_manager.get_generator(port_handle=port)
            analyzer_port_obj_dict[port] = template_obj.stc_manager.get_analyzer(port_handle=port)

        # Subscribe to all results
        project = template_obj.stc_manager.get_project_handle()
        subscribed_results = template_obj.subscribe_to_all_results(parent=project)
        fun_test.test_assert(subscribed_results['result'], "Subscribing to all results")
        del subscribed_results['result']

        if dut_config['enable_dpcsh']:
            network_controller_obj = NetworkController(dpc_server_ip=dpc_server_ip, dpc_server_port=dpc_server_port)
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

    def cleanup(self):
        template_obj.cleanup()


class SampleIngressFPGtoFPG(FunTestCase):
    routes_config = None
    l3_config = None
    load = 1
    load_type = StreamBlock.LOAD_UNIT_MEGABITS_PER_SECOND
    stream_obj = None
    sample_id = 50
    header_objs = {'eth_obj': None, 'ip_obj': None, 'tcp_obj': None}
    capture_results = None

    def describe(self):
        self.set_test_details(id=1, summary="Transit Flow Ingress Sampling Source FPG and Destination FPG",
                              steps="""
                              1. Create TCP frame stream on Tx Port with following settings
                                 a. Frame Size Mode: Random Min: 78 B and Max: 1500 B
                                 b. Payload Type: PRBS
                                 c. Insert Signature
                                 d. Load: 1 Mbps
                              2. Configure ingress sampling rule on FPG5 and dest: FPG15
                              3. Start Traffic for %d secs
                              4. Start packet capture sampling port 
                              5. Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count
                              6. Ensure Tx frame count must be equal to sample frame count
                              7. Ensure PSW sample_pkt counter must be equal to no of frames transmitted
                              8. Ensure sample counter for a rule must be equal to Tx frames  
                              9. Ensure on spirent Tx port frames must be equal to Rx port frames and sample port 
                                  frames
                              10. Ensure no errors are seen on spirent ports
                              11. Ensure sample packets are exactly same as ingress packets 
                              """ % TRAFFIC_DURATION)

    def setup(self):
        self.routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
        fun_test.simple_assert(self.routes_config, "Ensure routes config fetched")
        self.l3_config = self.routes_config['l3_config']

        checkpoint = "Create stream on %s port" % tx_port
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_PRBS,
                                      insert_signature=True,
                                      load=self.load,
                                      load_unit=self.load_type,
                                      frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_RANDOM,
                                      min_frame_length=78, max_frame_length=1500)
        stream_created = template_obj.configure_stream_block(stream_block_obj=self.stream_obj,
                                                             port_handle=tx_port)
        fun_test.test_assert(stream_created, checkpoint)

        ethernet_obj = Ethernet2Header(destination_mac=self.routes_config['routermac'],
                                       ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        checkpoint = "Configure Mac address for %s " % self.stream_obj.spirent_handle
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ethernet_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        ip_header_obj = Ipv4Header(destination_address=self.l3_config['destination_ip1'],
                                   protocol=Ipv4Header.PROTOCOL_TYPE_TCP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ip_header_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        checkpoint = "Add TCP header"
        tcp_header_obj = TCP()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=tcp_header_obj, update=False)
        fun_test.simple_assert(result, checkpoint)

        self.header_objs['eth_obj'] = ethernet_obj
        self.header_objs['ip_obj'] = ip_header_obj
        self.header_objs['tcp_obj'] = tcp_header_obj

        dut_rx_port = dut_config['ports'][0]
        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Add Ingress Sampling rule Ingress Port: FPG%d and dest port: FPG%d" % (dut_rx_port,
                                                                                             dut_sample_port)
        result = network_controller_obj.add_ingress_sample_rule(id=self.sample_id,
                                                                fpg=dut_rx_port, dest=dut_sample_port)
        fun_test.test_assert(result['status'], checkpoint)

    def run(self):
        dut_rx_port = dut_config['ports'][0]
        dut_tx_port = dut_config['ports'][1]
        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Clear FPG port stats on DUT"
        for port_num in dut_config['ports']:
            shape = 0
            if port_num == 1 or port_num == 2:
                shape = 1
            result = network_controller_obj.clear_port_stats(port_num=port_num, shape=shape)
            fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
        fun_test.add_checkpoint(checkpoint=checkpoint)

        checkpoint = "Get PSW stats before traffic"
        psw_stats_before = network_controller_obj.peek_psw_global_stats()
        fun_test.test_assert(psw_stats_before, checkpoint)

        checkpoint = "Get Sample stats before traffic"
        sample_stats_before = network_controller_obj.show_sample_stats()
        fun_test.test_assert(sample_stats_before, checkpoint)

        checkpoint = "Start traffic from %s port for %d secs" % (tx_port, TRAFFIC_DURATION)
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)

        checkpoint = "Packet captured on %s sample port" % sample_port
        self.capture_results = template_obj.start_default_capture_save_locally(port_handle=sample_port,
                                                                               sleep_time=10)
        fun_test.test_assert(self.capture_results['result'], checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION)

        # Getting Spirent results
        checkpoint = "Fetch Tx Port Results for %s" % tx_port
        tx_port_result = template_obj.stc_manager.get_generator_port_results(
            port_handle=tx_port, subscribe_handle=subscribed_results['generator_subscribe'])
        fun_test.simple_assert(expression=tx_port_result, message=checkpoint)

        checkpoint = "Fetch Rx Port Results for %s" % rx_port
        rx_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=rx_port_result, message=checkpoint)

        checkpoint = "Fetch Sample Port Results for %s" % sample_port
        sample_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=sample_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=sample_port_result, message=checkpoint)

        fun_test.log("Tx Port: %s" % tx_port_result)
        fun_test.log("Rx Port: %s" % rx_port_result)
        fun_test.log("Sample Port: %s" % sample_port_result)

        # Validate DUT stats
        dut_rx_port_results = network_controller_obj.peek_fpg_port_stats(dut_rx_port)
        fun_test.simple_assert(dut_rx_port_results, "Fetch DUT Rx port results. FPG%d" % dut_rx_port)

        dut_tx_port_results = network_controller_obj.peek_fpg_port_stats(dut_tx_port)
        fun_test.simple_assert(dut_tx_port_results, "Fetch DUT Tx port results. FPG%d" % dut_tx_port)

        dut_sample_port_results = network_controller_obj.peek_fpg_port_stats(dut_sample_port)
        fun_test.simple_assert(dut_sample_port_results, "Fetch DUT sample port results. FPG%d" % dut_sample_port)

        psw_stats = network_controller_obj.peek_psw_global_stats()
        fun_test.simple_assert(psw_stats, "Fetch PSW global stats")

        sample_stats = network_controller_obj.show_sample_stats()
        fun_test.simple_assert(sample_stats, "Fetch Sample stats")

        fun_test.log("DUT Rx Port %d Results: %s" % (dut_rx_port, dut_rx_port_results))
        fun_test.log("DUT Tx Port %d Results: %s" % (dut_tx_port, dut_tx_port_results))
        fun_test.log("DUT Sample Port %d Results: %s" % (dut_sample_port, dut_sample_port_results))
        fun_test.log("PSW stats: %s" % psw_stats)
        fun_test.log("Sample stats: %s" % sample_stats)

        checkpoint = "Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count"
        frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_results, stat_type=FRAMES_RECEIVED_OK,
                                                     tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on FPG%d: %d" % (
            dut_rx_port, frames_received, dut_tx_port, frames_transmitted))
        fun_test.test_assert_expected(expected=frames_received, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Ensure Tx frame count must be equal to sample frame count"
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_sample_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on Sample port FPG%d: %d" % (
            dut_rx_port, frames_received, dut_sample_port, frames_transmitted))
        fun_test.test_assert_expected(expected=frames_received, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Ensure PSW sample_pkt counter must be equal to no of frames transmitted"
        parsed_input_stats_1 = get_psw_global_stats_values(input=True, psw_stats_output=psw_stats_before,
                                                           input_key_list=[PSW_SAMPLED_PACKET_COUNT])

        parsed_input_stats_2 = get_psw_global_stats_values(input=True, psw_stats_output=psw_stats,
                                                           input_key_list=[PSW_SAMPLED_PACKET_COUNT])

        psw_diff_stats = get_diff_stats(old_stats=parsed_input_stats_1['input'],
                                        new_stats=parsed_input_stats_2['input'],
                                        stats_list=[PSW_SAMPLED_PACKET_COUNT])
        fun_test.test_assert_expected(expected=frames_received, actual=int(psw_diff_stats['sampled_pkt']),
                                      message=checkpoint)

        checkpoint = "Ensure sample counter for a rule must be equal to Tx frames"
        sample_diff_stats = get_diff_stats(old_stats=sample_stats_before[str(self.sample_id)],
                                           new_stats=sample_stats[str(self.sample_id)])
        fun_test.test_assert_expected(expected=frames_received,
                                      actual=int(sample_diff_stats['count']),
                                      message=checkpoint)

        # Validate Spirent stats
        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Rx spirent port FrameCount"
        fun_test.test_assert_expected(expected=tx_port_result['GeneratorFrameCount'],
                                      actual=rx_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Sample spirent port FrameCount"
        fun_test.test_assert_expected(expected=tx_port_result['GeneratorFrameCount'],
                                      actual=sample_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure no errors are seen on Rx spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure no errors are seen on Sample spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=sample_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure all the fields in a packet is correct"
        parser_obj = PcapParser(filename=self.capture_results['pcap_file_path'])
        packets = parser_obj.get_captures_from_file()
        result = parser_obj.validate_sample_packets_in_file(packets=packets, header_objs=self.header_objs)
        fun_test.test_assert(result, checkpoint)

    def cleanup(self):
        dut_rx_port = dut_config['ports'][0]
        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Delete sample rule for id: %d" % self.sample_id
        network_controller_obj.disable_sample_rule(id=self.sample_id, fpg=dut_rx_port, dest=dut_sample_port)
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Delete the stream"
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Delete tmp pcap file %s" % self.capture_results['pcap_file_path']
        fun_test.remove_file(self.capture_results['pcap_file_path'])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)


class SampleIngressFPGtoFPGWithRate(FunTestCase):
    routes_config = None
    l3_config = None
    load = 100
    load_type = StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND
    stream_obj = None
    sample_id = 51
    header_objs = {'eth_obj': None, 'ip_obj': None, 'tcp_obj': None}
    sampler_rate = 100
    capture_results = None

    def describe(self):
        self.set_test_details(id=2, summary="Test Ingress Traffic Sampling FPG to FPG with Sampler Rate %d" %
                                            self.sampler_rate,
                              steps="""
                              1. Create TCP frame stream on Tx Port with following settings
                                 a. Frame Size Mode: Random Min: 78 B and Max: 1500 B
                                 b. Payload Type: PRBS
                                 c. Insert Signature
                                 d. Load: 100 fps
                              2. Configure ingress sampling rule on FPG5 and dest with different sampler rate 
                              3. Start Traffic for %d secs
                              4. Start packet capture sampling port 
                              5. Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count
                              6. Ensure sample frame count should be 10 percent of total Tx frame count
                              7. Ensure PSW sample_pkt counter must be equal to no of frames transmitted on sample port
                              8. Ensure on spirent sample port frames must be equal to no of frames sampled
                              9. Ensure no errors are seen on spirent ports
                              10. Ensure sample packets are exactly same as ingress packets 
                              """ % TRAFFIC_DURATION)

    def setup(self):
        self.routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
        fun_test.simple_assert(self.routes_config, "Ensure routes config fetched")
        self.l3_config = self.routes_config['l3_config']

        checkpoint = "Create stream on %s port" % tx_port
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_PRBS,
                                      insert_signature=True,
                                      load=self.load,
                                      load_unit=self.load_type,
                                      frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_RANDOM,
                                      min_frame_length=78, max_frame_length=1500)
        stream_created = template_obj.configure_stream_block(stream_block_obj=self.stream_obj,
                                                             port_handle=tx_port)
        fun_test.test_assert(stream_created, checkpoint)

        ethernet_obj = Ethernet2Header(destination_mac=self.routes_config['routermac'],
                                       ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        checkpoint = "Configure Mac address for %s " % self.stream_obj.spirent_handle
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ethernet_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        ip_header_obj = Ipv4Header(destination_address=self.l3_config['destination_ip1'],
                                   protocol=Ipv4Header.PROTOCOL_TYPE_TCP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ip_header_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        checkpoint = "Add TCP header"
        tcp_header_obj = TCP()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=tcp_header_obj, update=False)
        fun_test.simple_assert(result, checkpoint)

        self.header_objs['eth_obj'] = ethernet_obj
        self.header_objs['ip_obj'] = ip_header_obj
        self.header_objs['tcp_obj'] = tcp_header_obj

        dut_rx_port = dut_config['ports'][0]
        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Add ingress Sampling rule Ingress Port: FPG%d and dest port: FPG%d" % (dut_rx_port,
                                                                                             dut_sample_port)
        result = network_controller_obj.add_ingress_sample_rule(id=self.sample_id,
                                                                fpg=dut_rx_port, dest=dut_sample_port,
                                                                sampler_rate=self.sampler_rate, sampler_en=1)
        fun_test.test_assert(result['status'], checkpoint)

    def run(self):
        dut_rx_port = dut_config['ports'][0]
        dut_tx_port = dut_config['ports'][1]
        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Clear FPG port stats on DUT"
        for port_num in dut_config['ports']:
            shape = 0
            if port_num == 1 or port_num == 2:
                shape = 1
            result = network_controller_obj.clear_port_stats(port_num=port_num, shape=shape)
            fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
        fun_test.add_checkpoint(checkpoint=checkpoint)

        checkpoint = "Get PSW stats before traffic"
        psw_stats_before = network_controller_obj.peek_psw_global_stats()
        fun_test.test_assert(psw_stats_before, checkpoint)

        checkpoint = "Get Sample stats before traffic"
        sample_stats_before = network_controller_obj.show_sample_stats()
        fun_test.test_assert(sample_stats_before, checkpoint)

        checkpoint = "Start traffic from %s port for %d secs" % (tx_port, TRAFFIC_DURATION)
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)

        checkpoint = "Packet captured on %s sample port" % sample_port
        self.capture_results = template_obj.start_default_capture_save_locally(port_handle=sample_port,
                                                                               sleep_time=10)
        fun_test.test_assert(self.capture_results['result'], checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION)

        # Getting Spirent results
        checkpoint = "Fetch Tx Port Results for %s" % tx_port
        tx_port_result = template_obj.stc_manager.get_generator_port_results(
            port_handle=tx_port, subscribe_handle=subscribed_results['generator_subscribe'])
        fun_test.simple_assert(expression=tx_port_result, message=checkpoint)

        checkpoint = "Fetch Rx Port Results for %s" % rx_port
        rx_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=rx_port_result, message=checkpoint)

        checkpoint = "Fetch Sample Port Results for %s" % sample_port
        sample_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=sample_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=sample_port_result, message=checkpoint)

        fun_test.log("Tx Port: %s" % tx_port_result)
        fun_test.log("Rx Port: %s" % rx_port_result)
        fun_test.log("Sample Port: %s" % sample_port_result)

        # Validate DUT stats
        dut_rx_port_results = network_controller_obj.peek_fpg_port_stats(dut_rx_port)
        fun_test.simple_assert(dut_rx_port_results, "Fetch DUT Rx port results. FPG%d" % dut_rx_port)

        dut_tx_port_results = network_controller_obj.peek_fpg_port_stats(dut_tx_port)
        fun_test.simple_assert(dut_tx_port_results, "Fetch DUT Tx port results. FPG%d" % dut_tx_port)

        dut_sample_port_results = network_controller_obj.peek_fpg_port_stats(dut_sample_port)
        fun_test.simple_assert(dut_sample_port_results, "Fetch DUT sample port results. FPG%d" % dut_sample_port)

        psw_stats = network_controller_obj.peek_psw_global_stats()
        fun_test.simple_assert(psw_stats, "Fetch PSW global stats")

        sample_stats = network_controller_obj.show_sample_stats()
        fun_test.simple_assert(sample_stats, "Fetch Sample stats")

        fun_test.log("DUT Rx Port %d Results: %s" % (dut_rx_port, dut_rx_port_results))
        fun_test.log("DUT Tx Port %d Results: %s" % (dut_tx_port, dut_tx_port_results))
        fun_test.log("DUT Sample Port %d Results: %s" % (dut_sample_port, dut_sample_port_results))
        fun_test.log("PSW stats: %s" % psw_stats)
        fun_test.log("Sample stats: %s" % sample_stats)

        checkpoint = "Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count"
        frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_results, stat_type=FRAMES_RECEIVED_OK,
                                                     tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on FPG%d: %d" % (
            dut_rx_port, frames_received, dut_tx_port, frames_transmitted))
        fun_test.test_assert_expected(expected=frames_received, actual=frames_transmitted, message=checkpoint)

        # Why 10%? It is LFSR pseudo random number based approach and sampling happens depending on random numbers
        # generated. With sampler_rate of 100, 10% of traffic should be sampled.
        checkpoint = "Ensure sample frame count should be 10 percent of total Tx frame count"
        sample_diff_stats = get_diff_stats(old_stats=sample_stats_before[str(self.sample_id)],
                                           new_stats=sample_stats[str(self.sample_id)])
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_sample_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on Sample port FPG%d: %d" % (
            dut_rx_port, frames_received, dut_sample_port, frames_transmitted))
        fun_test.log("Total Packets sampled: %d" % sample_diff_stats['count'])
        fun_test.test_assert_expected(expected=sample_diff_stats['count'], actual=frames_transmitted,
                                      message="Ensure sampled packets transmitted on sample port FPG%d must be equal "
                                              "to total packets sampled" % dut_sample_port)
        packets_sampled_in_percent = float(sample_diff_stats['count'] * 100 / frames_received)
        fun_test.log("No of packets actually sampled in percent %d" % packets_sampled_in_percent)
        fun_test.test_assert(9 >= packets_sampled_in_percent <= 10, checkpoint)

        checkpoint = "Ensure PSW sample_pkt counter must be equal to no of frames transmitted on sample port"
        parsed_input_stats_1 = get_psw_global_stats_values(input=True, psw_stats_output=psw_stats_before,
                                                           input_key_list=[PSW_SAMPLED_PACKET_COUNT])

        parsed_input_stats_2 = get_psw_global_stats_values(input=True, psw_stats_output=psw_stats,
                                                           input_key_list=[PSW_SAMPLED_PACKET_COUNT])

        psw_diff_stats = get_diff_stats(old_stats=parsed_input_stats_1['input'],
                                        new_stats=parsed_input_stats_2['input'],
                                        stats_list=[PSW_SAMPLED_PACKET_COUNT])
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_sample_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.test_assert_expected(expected=frames_transmitted, actual=int(psw_diff_stats['sampled_pkt']),
                                      message=checkpoint)

        # Validate Spirent stats
        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Rx spirent port FrameCount"
        fun_test.test_assert_expected(expected=tx_port_result['GeneratorFrameCount'],
                                      actual=rx_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure on spirent sample port frames must be equal to no of frames sampled"
        fun_test.test_assert_expected(expected=sample_diff_stats['count'],
                                      actual=sample_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure no errors are seen on Rx spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure no errors are seen on Sample spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=sample_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure all the fields in a packet is correct"
        parser_obj = PcapParser(filename=self.capture_results['pcap_file_path'])
        packets = parser_obj.get_captures_from_file()
        result = parser_obj.validate_sample_packets_in_file(packets=packets, header_objs=self.header_objs)
        fun_test.test_assert(result, checkpoint)

    def cleanup(self):
        dut_rx_port = dut_config['ports'][0]
        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Delete sample rule for id: %d" % self.sample_id
        network_controller_obj.disable_sample_rule(id=self.sample_id, fpg=dut_rx_port, dest=dut_sample_port)
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Delete the stream"
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Delete tmp pcap file %s" % self.capture_results['pcap_file_path']
        fun_test.remove_file(self.capture_results['pcap_file_path'])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)


class SampleFCOIngressFPGtoFPG(FunTestCase):
    routes_config = None
    l3_config = None
    load = 1
    load_type = StreamBlock.LOAD_UNIT_MEGABITS_PER_SECOND
    stream_obj = None
    sample_id = 52
    header_objs = {'eth_obj': None, 'ip_obj': None, 'tcp_obj': None}
    capture_results = None

    def describe(self):
        self.set_test_details(id=3, summary="Test Ingress Traffic Sampling with first cell only FPG to FPG",
                              steps="""
                                  1. Create TCP frame stream on Tx Port with following settings
                                     a. Frame Size Mode: Fixed size of 500 B
                                     b. Payload Type: PRBS
                                     c. Insert Signature
                                     d. Load: 1 Mbps
                                  2. Configure ingress sampling rule on FPG5 and dest with first cell only enabled 
                                  3. Start Traffic for %d secs
                                  4. Start packet capture sampling port 
                                  5. Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count
                                  6. Ensure Tx frame count must be equal to sample frame count
                                  7. Ensure that on sample FPG port no of bytes range is 192 B as only first cell of 
                                     packet is sampled
                                  8. Ensure PSW sample_pkt counter must be equal to no of frames transmitted
                                  9. Ensure sample counter for a rule must be equal to Tx frames  
                                  10. Ensure on spirent Tx port frames must be equal to Rx port frames and sample port 
                                      frames
                                  11. Ensure no errors are seen on spirent ports
                                  12. Ensure sample packets are exactly same as ingress packets 
                                  """ % TRAFFIC_DURATION)

    def setup(self):
        self.routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
        fun_test.simple_assert(self.routes_config, "Ensure routes config fetched")
        self.l3_config = self.routes_config['l3_config']

        checkpoint = "Create stream on %s port" % tx_port
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_PRBS,
                                      insert_signature=True,
                                      load=self.load,
                                      load_unit=self.load_type,
                                      frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_FIXED,
                                      fixed_frame_length=500)
        stream_created = template_obj.configure_stream_block(stream_block_obj=self.stream_obj,
                                                             port_handle=tx_port)
        fun_test.test_assert(stream_created, checkpoint)

        ethernet_obj = Ethernet2Header(destination_mac=self.routes_config['routermac'],
                                       ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        checkpoint = "Configure Mac address for %s " % self.stream_obj.spirent_handle
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ethernet_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        ip_header_obj = Ipv4Header(destination_address=self.l3_config['destination_ip1'],
                                   protocol=Ipv4Header.PROTOCOL_TYPE_TCP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ip_header_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        checkpoint = "Add TCP header"
        tcp_header_obj = TCP()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=tcp_header_obj, update=False)
        fun_test.simple_assert(result, checkpoint)

        self.header_objs['eth_obj'] = ethernet_obj
        self.header_objs['ip_obj'] = ip_header_obj
        self.header_objs['tcp_obj'] = tcp_header_obj

        dut_rx_port = dut_config['ports'][0]
        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Add Ingress Sampling rule Ingress Port: FPG%d and dest port: FPG%d with first cell only" % (
            dut_rx_port, dut_sample_port)
        result = network_controller_obj.add_ingress_sample_rule(id=self.sample_id,
                                                                fpg=dut_rx_port, dest=dut_sample_port,
                                                                first_cell_only=1)
        fun_test.test_assert(result['status'], checkpoint)

    def run(self):
        dut_rx_port = dut_config['ports'][0]
        dut_tx_port = dut_config['ports'][1]
        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Clear FPG port stats on DUT"
        for port_num in dut_config['ports']:
            shape = 0
            if port_num == 1 or port_num == 2:
                shape = 1
            result = network_controller_obj.clear_port_stats(port_num=port_num, shape=shape)
            fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
        fun_test.add_checkpoint(checkpoint=checkpoint)

        checkpoint = "Get PSW stats before traffic"
        psw_stats_before = network_controller_obj.peek_psw_global_stats()
        fun_test.test_assert(psw_stats_before, checkpoint)

        checkpoint = "Get Sample stats before traffic"
        sample_stats_before = network_controller_obj.show_sample_stats()
        fun_test.test_assert(sample_stats_before, checkpoint)

        checkpoint = "Start traffic from %s port for %d secs" % (tx_port, TRAFFIC_DURATION)
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)

        checkpoint = "Packet captured on %s sample port" % sample_port
        self.capture_results = template_obj.start_default_capture_save_locally(port_handle=sample_port,
                                                                               sleep_time=10)
        fun_test.test_assert(self.capture_results['result'], checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION)

        # Getting Spirent results
        checkpoint = "Fetch Tx Port Results for %s" % tx_port
        tx_port_result = template_obj.stc_manager.get_generator_port_results(
            port_handle=tx_port, subscribe_handle=subscribed_results['generator_subscribe'])
        fun_test.simple_assert(expression=tx_port_result, message=checkpoint)

        checkpoint = "Fetch Rx Port Results for %s" % rx_port
        rx_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=rx_port_result, message=checkpoint)

        checkpoint = "Fetch Sample Port Results for %s" % sample_port
        sample_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=sample_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=sample_port_result, message=checkpoint)

        fun_test.log("Tx Port: %s" % tx_port_result)
        fun_test.log("Rx Port: %s" % rx_port_result)
        fun_test.log("Sample Port: %s" % sample_port_result)

        # Validate DUT stats
        dut_rx_port_results = network_controller_obj.peek_fpg_port_stats(dut_rx_port)
        fun_test.simple_assert(dut_rx_port_results, "Fetch DUT Rx port results. FPG%d" % dut_rx_port)

        dut_tx_port_results = network_controller_obj.peek_fpg_port_stats(dut_tx_port)
        fun_test.simple_assert(dut_tx_port_results, "Fetch DUT Tx port results. FPG%d" % dut_tx_port)

        dut_sample_port_results = network_controller_obj.peek_fpg_port_stats(dut_sample_port)
        fun_test.simple_assert(dut_sample_port_results, "Fetch DUT sample port results. FPG%d" % dut_sample_port)

        psw_stats = network_controller_obj.peek_psw_global_stats()
        fun_test.simple_assert(psw_stats, "Fetch PSW global stats")

        sample_stats = network_controller_obj.show_sample_stats()
        fun_test.simple_assert(sample_stats, "Fetch Sample stats")

        fun_test.log("DUT Rx Port %d Results: %s" % (dut_rx_port, dut_rx_port_results))
        fun_test.log("DUT Tx Port %d Results: %s" % (dut_tx_port, dut_tx_port_results))
        fun_test.log("DUT Sample Port %d Results: %s" % (dut_sample_port, dut_sample_port_results))
        fun_test.log("PSW stats: %s" % psw_stats)
        fun_test.log("Sample stats: %s" % sample_stats)

        checkpoint = "Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count"
        frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_results, stat_type=FRAMES_RECEIVED_OK,
                                                     tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on FPG%d: %d" % (
            dut_rx_port, frames_received, dut_tx_port, frames_transmitted))
        fun_test.test_assert_expected(expected=frames_received, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Ensure Tx frame count must be equal to sample frame count"
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_sample_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on Sample port FPG%d: %d" % (
            dut_rx_port, frames_received, dut_sample_port, frames_transmitted))
        fun_test.test_assert_expected(expected=frames_received, actual=frames_transmitted, message=checkpoint)

        # TODO: On Sample DUT port validate Ether Stats packets size is 192 B ETHER_STATS_PKTS_128_TO_255_OCTETS

        checkpoint = "Ensure that on sample FPG port no of bytes range is 128 to 255 B as only first cell of packet " \
                     "is sampled"
        sample_frame_transmitted = get_dut_output_stats_value(result_stats=dut_sample_port_results,
                                                              stat_type=ETHER_STATS_PKTS_128_TO_255_OCTETS)
        fun_test.test_assert_expected(expected=frames_received, actual=sample_frame_transmitted, message=checkpoint)

        checkpoint = "Ensure PSW sample_pkt counter must be equal to no of frames transmitted"
        parsed_input_stats_1 = get_psw_global_stats_values(input=True, psw_stats_output=psw_stats_before,
                                                           input_key_list=[PSW_SAMPLED_PACKET_COUNT])

        parsed_input_stats_2 = get_psw_global_stats_values(input=True, psw_stats_output=psw_stats,
                                                           input_key_list=[PSW_SAMPLED_PACKET_COUNT])

        psw_diff_stats = get_diff_stats(old_stats=parsed_input_stats_1['input'],
                                        new_stats=parsed_input_stats_2['input'],
                                        stats_list=[PSW_SAMPLED_PACKET_COUNT])
        fun_test.test_assert_expected(expected=frames_received, actual=int(psw_diff_stats['sampled_pkt']),
                                      message=checkpoint)

        checkpoint = "Ensure sample counter for a rule must be equal to Tx frames"
        sample_diff_stats = get_diff_stats(old_stats=sample_stats_before[str(self.sample_id)],
                                           new_stats=sample_stats[str(self.sample_id)])
        fun_test.test_assert_expected(expected=frames_received,
                                      actual=int(sample_diff_stats['count']),
                                      message=checkpoint)

        # Validate Spirent stats
        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Rx spirent port FrameCount"
        fun_test.test_assert_expected(expected=tx_port_result['GeneratorFrameCount'],
                                      actual=rx_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Sample spirent port FrameCount"
        fun_test.test_assert_expected(expected=tx_port_result['GeneratorFrameCount'],
                                      actual=sample_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure no errors are seen on Rx spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure no errors are seen on Sample spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=sample_port_result)
        errors_seen = False
        if result['TcpChecksumErrorCount'] > 0 and result['PrbsErrorFrameCount'] > 0:
            errors_seen = True
        fun_test.test_assert(errors_seen, checkpoint)

        checkpoint = "Ensure all the fields in a packet is correct"
        parser_obj = PcapParser(filename=self.capture_results['pcap_file_path'])
        packets = parser_obj.get_captures_from_file()
        result = parser_obj.validate_sample_packets_in_file(packets=packets, header_objs=self.header_objs)
        fun_test.test_assert(result, checkpoint)

    def cleanup(self):
        dut_rx_port = dut_config['ports'][0]
        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Delete sample rule for id: %d" % self.sample_id
        network_controller_obj.disable_sample_rule(id=self.sample_id, fpg=dut_rx_port, dest=dut_sample_port)
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Delete the stream"
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Delete tmp pcap file %s" % self.capture_results['pcap_file_path']
        fun_test.remove_file(self.capture_results['pcap_file_path'])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)


class SamplePPStoFPG(FunTestCase):
    routes_config = None
    l3_config = None
    load = 100
    load_type = StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND
    stream_obj = None
    sample_id = 53
    header_objs = {'eth_obj': None, 'ip_obj': None, 'tcp_obj': None}
    generator_handle = None
    analyzer_handle = None
    capture_results = None

    def describe(self):
        self.set_test_details(id=4, summary="Test Ingress Traffic Sampling with pps",
                              steps="""
                                      1. Create TCP frame stream on Tx Port with following settings
                                         a. Frame Size Mode: Fixed 128 B
                                         b. Payload Type: PRBS
                                         c. Insert Signature
                                         d. Load: 100 fps
                                      2. Configure ingress sampling rule on FPG13 and dest port 15 with following config
                                         a. pps_en: 1
                                         b. pps_interval: 10000
                                         c. pps_burst: 1
                                         d. pps_tick: 256 
                                      3. Start Traffic for 60 secs
                                      4. Start packet capture sampling port 
                                      5. Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count
                                      6. Ensure sample frame count must be equal to 8 as per above PPS config
                                      7. Ensure PSW sample_pkt counter must be equal to sample frame count
                                      8. Ensure sample counter for a rule must be equal to 8
                                      9. Ensure on spirent Tx port frames must be equal to Rx port frames 
                                      10. Ensure on spirent sample frame count must be eqaul to no of packets sampled
                                      11. Ensure no errors are seen on spirent ports
                                      11. Ensure sample packets are exactly same as ingress packets 
                                      """)

    def setup(self):
        self.routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
        fun_test.simple_assert(self.routes_config, "Ensure routes config fetched")
        self.l3_config = self.routes_config['l3_config']

        checkpoint = "Create stream on %s port" % tx_port
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_PRBS,
                                      insert_signature=True,
                                      load=self.load,
                                      load_unit=self.load_type,
                                      frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_FIXED,
                                      fixed_frame_length=128)
        stream_created = template_obj.configure_stream_block(stream_block_obj=self.stream_obj,
                                                             port_handle=tx_port)
        fun_test.test_assert(stream_created, checkpoint)

        ethernet_obj = Ethernet2Header(destination_mac=self.routes_config['routermac'],
                                       ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        checkpoint = "Configure Mac address for %s " % self.stream_obj.spirent_handle
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ethernet_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        ip_header_obj = Ipv4Header(destination_address=self.l3_config['destination_ip1'],
                                   protocol=Ipv4Header.PROTOCOL_TYPE_TCP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ip_header_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        checkpoint = "Add TCP header"
        tcp_header_obj = TCP()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=tcp_header_obj, update=False)
        fun_test.simple_assert(result, checkpoint)

        self.header_objs['eth_obj'] = ethernet_obj
        self.header_objs['ip_obj'] = ip_header_obj
        self.header_objs['tcp_obj'] = tcp_header_obj

        dut_rx_port = dut_config['ports'][0]
        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Add Ingress Sampling rule Ingress Port: FPG%d and dest port: FPG%d with pps_burst as 1 " \
                     "and pps_interval as 10000 and pps_tick as 256 " % (dut_rx_port, dut_sample_port)
        result = network_controller_obj.add_ingress_sample_rule(id=self.sample_id,
                                                                fpg=dut_rx_port, dest=dut_sample_port,
                                                                pps_burst=1, pps_interval=10000, pps_en=1, pps_tick=256)
        fun_test.test_assert(result['status'], checkpoint)

        generator_config.Duration = 60

        checkpoint = "Create Generator Config for %s port" % tx_port
        result = template_obj.configure_generator_config(port_handle=tx_port,
                                                         generator_config_obj=generator_config, update=False)
        fun_test.simple_assert(expression=result, message=checkpoint)

    def run(self):
        dut_rx_port = dut_config['ports'][0]
        dut_tx_port = dut_config['ports'][1]
        dut_sample_port = dut_config['ports'][2]
        expected_sample_frames = 8

        checkpoint = "Clear FPG port stats on DUT"
        for port_num in dut_config['ports']:
            shape = 0
            if port_num == 1 or port_num == 2:
                shape = 1
            result = network_controller_obj.clear_port_stats(port_num=port_num, shape=shape)
            fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
        fun_test.add_checkpoint(checkpoint=checkpoint)

        checkpoint = "Get PSW stats before traffic"
        psw_stats_before = network_controller_obj.peek_psw_global_stats()
        fun_test.test_assert(psw_stats_before, checkpoint)

        checkpoint = "Get Sample stats before traffic"
        sample_stats_before = network_controller_obj.show_sample_stats()
        fun_test.test_assert(sample_stats_before, checkpoint)

        checkpoint = "Start traffic from %s port for %d secs" % (tx_port, 60)
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)

        checkpoint = "Packet captured on %s sample port" % sample_port
        self.capture_results = template_obj.start_default_capture_save_locally(port_handle=sample_port,
                                                                               sleep_time=10)
        fun_test.test_assert(self.capture_results['result'], checkpoint)

        fun_test.sleep("Traffic to complete", seconds=60)

        # Getting Spirent results
        checkpoint = "Fetch Tx Port Results for %s" % tx_port
        tx_port_result = template_obj.stc_manager.get_generator_port_results(
            port_handle=tx_port, subscribe_handle=subscribed_results['generator_subscribe'])
        fun_test.simple_assert(expression=tx_port_result, message=checkpoint)

        checkpoint = "Fetch Rx Port Results for %s" % rx_port
        rx_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=rx_port_result, message=checkpoint)

        checkpoint = "Fetch Sample Port Results for %s" % sample_port
        sample_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=sample_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=sample_port_result, message=checkpoint)

        fun_test.log("Tx Port: %s" % tx_port_result)
        fun_test.log("Rx Port: %s" % rx_port_result)
        fun_test.log("Sample Port: %s" % sample_port_result)

        # Validate DUT stats
        dut_rx_port_results = network_controller_obj.peek_fpg_port_stats(dut_rx_port)
        fun_test.simple_assert(dut_rx_port_results, "Fetch DUT Rx port results. FPG%d" % dut_rx_port)

        dut_tx_port_results = network_controller_obj.peek_fpg_port_stats(dut_tx_port)
        fun_test.simple_assert(dut_tx_port_results, "Fetch DUT Tx port results. FPG%d" % dut_tx_port)

        dut_sample_port_results = network_controller_obj.peek_fpg_port_stats(dut_sample_port)
        fun_test.simple_assert(dut_sample_port_results, "Fetch DUT sample port results. FPG%d" % dut_sample_port)

        psw_stats = network_controller_obj.peek_psw_global_stats()
        fun_test.simple_assert(psw_stats, "Fetch PSW global stats")

        sample_stats = network_controller_obj.show_sample_stats()
        fun_test.simple_assert(sample_stats, "Fetch Sample stats")

        fun_test.log("DUT Rx Port %d Results: %s" % (dut_rx_port, dut_rx_port_results))
        fun_test.log("DUT Tx Port %d Results: %s" % (dut_tx_port, dut_tx_port_results))
        fun_test.log("DUT Sample Port %d Results: %s" % (dut_sample_port, dut_sample_port_results))
        fun_test.log("PSW stats: %s" % psw_stats)
        fun_test.log("Sample stats: %s" % sample_stats)

        checkpoint = "Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count"
        frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_results, stat_type=FRAMES_RECEIVED_OK,
                                                     tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on FPG%d: %d" % (
            dut_rx_port, frames_received, dut_tx_port, frames_transmitted))
        fun_test.test_assert_expected(expected=frames_received, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Ensure sample frame count must be equal to 8 as per above PPS config"
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_sample_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Transmitted on Sample port FPG%d: %d" % (dut_sample_port, frames_transmitted))
        fun_test.test_assert_expected(expected=expected_sample_frames, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Ensure PSW sample_pkt counter must be equal to no of frames transmitted"
        parsed_input_stats_1 = get_psw_global_stats_values(input=True, psw_stats_output=psw_stats_before,
                                                           input_key_list=[PSW_SAMPLED_PACKET_COUNT])

        parsed_input_stats_2 = get_psw_global_stats_values(input=True, psw_stats_output=psw_stats,
                                                           input_key_list=[PSW_SAMPLED_PACKET_COUNT])

        psw_diff_stats = get_diff_stats(old_stats=parsed_input_stats_1['input'],
                                        new_stats=parsed_input_stats_2['input'],
                                        stats_list=[PSW_SAMPLED_PACKET_COUNT])
        fun_test.test_assert_expected(expected=expected_sample_frames, actual=int(psw_diff_stats['sampled_pkt']),
                                      message=checkpoint)

        checkpoint = "Ensure sample counter for a rule must be equal to Tx frames"
        sample_diff_stats = get_diff_stats(old_stats=sample_stats_before[str(self.sample_id)],
                                           new_stats=sample_stats[str(self.sample_id)])
        fun_test.test_assert_expected(expected=expected_sample_frames,
                                      actual=int(sample_diff_stats['count']),
                                      message=checkpoint)

        # Validate Spirent stats
        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Rx spirent port FrameCount"
        fun_test.test_assert_expected(expected=int(tx_port_result['GeneratorFrameCount']),
                                      actual=rx_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure Sample spirent Port FrameCount must be equal to 8"
        fun_test.test_assert_expected(expected=expected_sample_frames,
                                      actual=sample_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure no errors are seen on Rx spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure no errors are seen on Sample spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=sample_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure all the fields in a packet is correct"
        parser_obj = PcapParser(filename=self.capture_results['pcap_file_path'])
        packets = parser_obj.get_captures_from_file()
        result = parser_obj.validate_sample_packets_in_file(packets=packets, header_objs=self.header_objs)
        fun_test.test_assert(result, checkpoint)

    def cleanup(self):
        dut_rx_port = dut_config['ports'][0]
        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Delete sample rule for id: %d" % self.sample_id
        network_controller_obj.disable_sample_rule(id=self.sample_id, fpg=dut_rx_port, dest=dut_sample_port,
                                                   pps_burst=0, pps_interval=10000, pps_en=0, pps_tick=256)
        fun_test.add_checkpoint(checkpoint)

        generator_config.Duration = TRAFFIC_DURATION

        checkpoint = "Create Generator Config for %s port" % tx_port
        template_obj.configure_generator_config(port_handle=tx_port,
                                                generator_config_obj=generator_config, update=False)
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Delete the stream"
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Delete tmp pcap file %s" % self.capture_results['pcap_file_path']
        fun_test.remove_file(self.capture_results['pcap_file_path'])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)


class SampleEgressFPGtoFPG(FunTestCase):
    routes_config = None
    l3_config = None
    load = 100
    load_type = StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND
    stream_obj = None
    sample_id = 57
    header_objs = {'eth_obj': None, 'ip_obj': None, 'tcp_obj': None}
    capture_results = None

    def describe(self):
        self.set_test_details(id=5, summary="Test Egress Traffic Sampling FPG to FPG",
                              steps="""
                                      1. Create TCP frame stream on Tx Port with following settings
                                         a. Frame Size Mode: Random Min: 78 B and Max: 1500 B
                                         b. Payload Type: PRBS
                                         c. Insert Signature
                                         d. Load: 100 fps
                                      2. Configure egress sampling rule on FPG5 and dest FPG15 
                                      3. Start Traffic for %d secs
                                      4. Start packet capture sampling port 
                                      5. Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count
                                      6. Ensure Tx frame count must be equal to sample frame count
                                      7. Ensure PSW sample_pkt counter must be equal to no of frames transmitted
                                      8. Ensure sample counter for a rule must be equal to Tx frames  
                                      9. Ensure on spirent Tx port frames must be equal to Rx port frames and sample port 
                                          frames
                                      10. Ensure no errors are seen on spirent ports
                                      11. Ensure sample packets are exactly same as ingress packets 
                                      """ % TRAFFIC_DURATION)

    def setup(self):
        self.routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
        fun_test.simple_assert(self.routes_config, "Ensure routes config fetched")
        self.l3_config = self.routes_config['l3_config']

        checkpoint = "Create stream on %s port" % tx_port
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_PRBS,
                                      insert_signature=True,
                                      load=self.load,
                                      load_unit=self.load_type,
                                      frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_RANDOM,
                                      min_frame_length=78, max_frame_length=1500)
        stream_created = template_obj.configure_stream_block(stream_block_obj=self.stream_obj,
                                                             port_handle=tx_port)
        fun_test.test_assert(stream_created, checkpoint)

        ethernet_obj = Ethernet2Header(destination_mac=self.routes_config['routermac'],
                                       ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        checkpoint = "Configure Mac address for %s " % self.stream_obj.spirent_handle
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ethernet_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        ip_header_obj = Ipv4Header(destination_address=self.l3_config['destination_ip1'],
                                   protocol=Ipv4Header.PROTOCOL_TYPE_TCP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ip_header_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        checkpoint = "Add TCP header"
        tcp_header_obj = TCP()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=tcp_header_obj, update=False)
        fun_test.simple_assert(result, checkpoint)

        ethernet_obj.srcMac = self.routes_config['routermac']
        ethernet_obj.dstMac = "fe:dc:ba:44:55:99"  # Destination mac of spirent port
        ip_header_obj.ttl = 254

        self.header_objs['eth_obj'] = ethernet_obj
        self.header_objs['ip_obj'] = ip_header_obj
        self.header_objs['tcp_obj'] = tcp_header_obj

        dut_rx_port = dut_config['ports'][0]
        dut_sample_port = dut_config['ports'][2]

        # Egress sampling can be applied to INGRESS interface e.g for traffic from 6->7 and you want to sample
        # egress traffic on 7 you can configure sampler like below
        # sample {"id": 56, "fpg": 6, "mode": 1, "dest": 5}
        checkpoint = "Add Egress Sampling rule Ingress Port: FPG%d and dest port: FPG%d " % (
            dut_rx_port, dut_sample_port)
        result = network_controller_obj.add_egress_sample_rule(id=self.sample_id,
                                                               fpg=dut_rx_port, dest=dut_sample_port)
        fun_test.test_assert(result['status'], checkpoint)

    def run(self):
        dut_rx_port = dut_config['ports'][0]
        dut_tx_port = dut_config['ports'][1]
        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Clear FPG port stats on DUT"
        for port_num in dut_config['ports']:
            shape = 0
            if port_num == 1 or port_num == 2:
                shape = 1
            result = network_controller_obj.clear_port_stats(port_num=port_num, shape=shape)
            fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
        fun_test.add_checkpoint(checkpoint=checkpoint)

        checkpoint = "Get PSW stats before traffic"
        psw_stats_before = network_controller_obj.peek_psw_global_stats()
        fun_test.test_assert(psw_stats_before, checkpoint)

        checkpoint = "Get Sample stats before traffic"
        sample_stats_before = network_controller_obj.show_sample_stats()
        fun_test.test_assert(sample_stats_before, checkpoint)

        checkpoint = "Start traffic from %s port for %d secs" % (tx_port, TRAFFIC_DURATION)
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)

        checkpoint = "Packet captured on %s sample port" % sample_port
        self.capture_results = template_obj.start_default_capture_save_locally(port_handle=sample_port,
                                                                               sleep_time=10)
        fun_test.test_assert(self.capture_results['result'], checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION)

        # Getting Spirent results
        checkpoint = "Fetch Tx Port Results for %s" % tx_port
        tx_port_result = template_obj.stc_manager.get_generator_port_results(
            port_handle=tx_port, subscribe_handle=subscribed_results['generator_subscribe'])
        fun_test.simple_assert(expression=tx_port_result, message=checkpoint)

        checkpoint = "Fetch Rx Port Results for %s" % rx_port
        rx_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=rx_port_result, message=checkpoint)

        checkpoint = "Fetch Sample Port Results for %s" % sample_port
        sample_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=sample_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=sample_port_result, message=checkpoint)

        fun_test.log("Tx Port: %s" % tx_port_result)
        fun_test.log("Rx Port: %s" % rx_port_result)
        fun_test.log("Sample Port: %s" % sample_port_result)

        # Validate DUT stats
        dut_rx_port_results = network_controller_obj.peek_fpg_port_stats(dut_rx_port)
        fun_test.simple_assert(dut_rx_port_results, "Fetch DUT Rx port results. FPG%d" % dut_rx_port)

        dut_tx_port_results = network_controller_obj.peek_fpg_port_stats(dut_tx_port)
        fun_test.simple_assert(dut_tx_port_results, "Fetch DUT Tx port results. FPG%d" % dut_tx_port)

        dut_sample_port_results = network_controller_obj.peek_fpg_port_stats(dut_sample_port)
        fun_test.simple_assert(dut_sample_port_results, "Fetch DUT sample port results. FPG%d" % dut_sample_port)

        psw_stats = network_controller_obj.peek_psw_global_stats()
        fun_test.simple_assert(psw_stats, "Fetch PSW global stats")

        sample_stats = network_controller_obj.show_sample_stats()
        fun_test.simple_assert(sample_stats, "Fetch Sample stats")

        fun_test.log("DUT Rx Port %d Results: %s" % (dut_rx_port, dut_rx_port_results))
        fun_test.log("DUT Tx Port %d Results: %s" % (dut_tx_port, dut_tx_port_results))
        fun_test.log("DUT Sample Port %d Results: %s" % (dut_sample_port, dut_sample_port_results))
        fun_test.log("PSW stats: %s" % psw_stats)
        fun_test.log("Sample stats: %s" % sample_stats)

        checkpoint = "Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count"
        frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_results, stat_type=FRAMES_RECEIVED_OK,
                                                     tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on FPG%d: %d" % (
            dut_rx_port, frames_received, dut_tx_port, frames_transmitted))
        fun_test.test_assert_expected(expected=frames_received, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Ensure Tx frame count must be equal to sample frame count"
        sample_frames_transmitted = get_dut_output_stats_value(result_stats=dut_sample_port_results,
                                                               stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Egress Frames on FPG%d: %d and Frames Transmitted on Sample port FPG%d: %d" % (
            dut_tx_port, frames_transmitted, dut_sample_port, sample_frames_transmitted))
        fun_test.test_assert_expected(expected=frames_transmitted, actual=sample_frames_transmitted,
                                      message=checkpoint)

        checkpoint = "Ensure PSW sample_pkt counter must be equal to no of frames transmitted"
        parsed_input_stats_1 = get_psw_global_stats_values(input=True, psw_stats_output=psw_stats_before,
                                                           input_key_list=[PSW_SAMPLED_PACKET_COUNT])

        parsed_input_stats_2 = get_psw_global_stats_values(input=True, psw_stats_output=psw_stats,
                                                           input_key_list=[PSW_SAMPLED_PACKET_COUNT])

        psw_diff_stats = get_diff_stats(old_stats=parsed_input_stats_1['input'],
                                        new_stats=parsed_input_stats_2['input'],
                                        stats_list=[PSW_SAMPLED_PACKET_COUNT])
        fun_test.test_assert_expected(expected=frames_transmitted, actual=int(psw_diff_stats['sampled_pkt']),
                                      message=checkpoint)

        checkpoint = "Ensure sample counter for a rule must be equal to Tx frames"
        sample_diff_stats = get_diff_stats(old_stats=sample_stats_before[str(self.sample_id)],
                                           new_stats=sample_stats[str(self.sample_id)])
        fun_test.test_assert_expected(expected=frames_transmitted,
                                      actual=int(sample_diff_stats['count']),
                                      message=checkpoint)

        # Validate Spirent stats
        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Rx spirent port FrameCount"
        fun_test.test_assert_expected(expected=tx_port_result['GeneratorFrameCount'],
                                      actual=rx_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Sample spirent port FrameCount"
        fun_test.test_assert_expected(expected=rx_port_result['TotalFrameCount'],
                                      actual=sample_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure no errors are seen on Rx spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure no errors are seen on Sample spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=sample_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure all the fields in a packet is correct"
        parser_obj = PcapParser(filename=self.capture_results['pcap_file_path'])
        packets = parser_obj.get_captures_from_file()
        result = parser_obj.validate_sample_packets_in_file(packets=packets, header_objs=self.header_objs)
        fun_test.test_assert(result, checkpoint)

    def cleanup(self):
        dut_rx_port = dut_config['ports'][0]
        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Delete sample rule for id: %d" % self.sample_id
        network_controller_obj.disable_sample_rule(id=self.sample_id, fpg=dut_rx_port, dest=dut_sample_port)
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Delete the stream"
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Delete tmp pcap file %s" % self.capture_results['pcap_file_path']
        fun_test.remove_file(self.capture_results['pcap_file_path'])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)


class SampleIngressFPGtoFPGDisable(FunTestCase):
    routes_config = None
    l3_config = None
    load = 100
    load_type = StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND
    stream_obj = None
    sample_id = 58
    header_objs = {'eth_obj': None, 'ip_obj': None, 'tcp_obj': None}
    capture_results = None

    def describe(self):
        self.set_test_details(id=6, summary="Test Egress Traffic Sampling FPG to FPG. Disable sampler and check "
                                            "behaviour",
                              steps="""
                              1. Create TCP frame stream on Tx Port with following settings
                                 a. Frame Size Mode: Random Min: 78 B and Max: 1500 B
                                 b. Payload Type: PRBS
                                 c. Insert Signature
                                 d. Load: 100 fps
                              2. Configure egress sampling rule on FPG5 and dest FPG15 
                              3. Start Traffic for %d secs
                              4. Start packet capture sampling port 
                              5. Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count
                              6. Ensure Tx frame count must be equal to sample frame count
                              7. Ensure PSW sample_pkt counter must be equal to no of frames transmitted
                              8. Ensure sample counter for a rule must be equal to Tx frames  
                              9. Ensure on spirent Tx port frames must be equal to Rx port frames and sample port 
                                 frames
                              10. Ensure no errors are seen on spirent ports
                              11. Ensure sample packets are exactly same as ingress packets
                              12. Clear port stats and spirent stats
                              13. Disable sample rule added before
                              14. Run traffic for %d secs
                              15. Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count 
                              16. Ensure sample frame count is 0
                              17. Ensure sample port stats are 0
                              """ % (TRAFFIC_DURATION, TRAFFIC_DURATION))

    def setup(self):
        self.routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
        fun_test.simple_assert(self.routes_config, "Ensure routes config fetched")
        self.l3_config = self.routes_config['l3_config']

        checkpoint = "Create stream on %s port" % tx_port
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_PRBS,
                                      insert_signature=True,
                                      load=self.load,
                                      load_unit=self.load_type,
                                      frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_RANDOM,
                                      min_frame_length=78, max_frame_length=1500)
        stream_created = template_obj.configure_stream_block(stream_block_obj=self.stream_obj,
                                                             port_handle=tx_port)
        fun_test.test_assert(stream_created, checkpoint)

        ethernet_obj = Ethernet2Header(destination_mac=self.routes_config['routermac'],
                                       ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        checkpoint = "Configure Mac address for %s " % self.stream_obj.spirent_handle
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ethernet_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        ip_header_obj = Ipv4Header(destination_address=self.l3_config['destination_ip1'],
                                   protocol=Ipv4Header.PROTOCOL_TYPE_TCP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ip_header_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        checkpoint = "Add TCP header"
        tcp_header_obj = TCP()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=tcp_header_obj, update=False)
        fun_test.simple_assert(result, checkpoint)

        self.header_objs['eth_obj'] = ethernet_obj
        self.header_objs['ip_obj'] = ip_header_obj
        self.header_objs['tcp_obj'] = tcp_header_obj

        dut_rx_port = dut_config['ports'][0]
        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Add Ingress Sampling rule Ingress Port: FPG%d and dest port: FPG%d " % (
            dut_rx_port, dut_sample_port)
        result = network_controller_obj.add_ingress_sample_rule(id=self.sample_id,
                                                                fpg=dut_rx_port, dest=dut_sample_port)
        fun_test.test_assert(result['status'], checkpoint)

    def run(self):
        dut_rx_port = dut_config['ports'][0]
        dut_tx_port = dut_config['ports'][1]
        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Clear FPG port stats on DUT"
        for port_num in dut_config['ports']:
            shape = 0
            if port_num == 1 or port_num == 2:
                shape = 1
            result = network_controller_obj.clear_port_stats(port_num=port_num, shape=shape)
            fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
        fun_test.add_checkpoint(checkpoint=checkpoint)

        checkpoint = "Get PSW stats before traffic"
        psw_stats_before = network_controller_obj.peek_psw_global_stats()
        fun_test.test_assert(psw_stats_before, checkpoint)

        checkpoint = "Get Sample stats before traffic"
        sample_stats_before = network_controller_obj.show_sample_stats()
        fun_test.test_assert(sample_stats_before, checkpoint)

        checkpoint = "Start traffic from %s port for %d secs" % (tx_port, TRAFFIC_DURATION)
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)

        checkpoint = "Packet captured on %s sample port" % sample_port
        self.capture_results = template_obj.start_default_capture_save_locally(port_handle=sample_port,
                                                                               sleep_time=10)
        fun_test.test_assert(self.capture_results['result'], checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION)

        # Getting Spirent results
        checkpoint = "Fetch Tx Port Results for %s" % tx_port
        tx_port_result = template_obj.stc_manager.get_generator_port_results(
            port_handle=tx_port, subscribe_handle=subscribed_results['generator_subscribe'])
        fun_test.simple_assert(expression=tx_port_result, message=checkpoint)

        checkpoint = "Fetch Rx Port Results for %s" % rx_port
        rx_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=rx_port_result, message=checkpoint)

        checkpoint = "Fetch Sample Port Results for %s" % sample_port
        sample_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=sample_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=sample_port_result, message=checkpoint)

        fun_test.log("Tx Port: %s" % tx_port_result)
        fun_test.log("Rx Port: %s" % rx_port_result)
        fun_test.log("Sample Port: %s" % sample_port_result)

        # Validate DUT stats
        dut_rx_port_results = network_controller_obj.peek_fpg_port_stats(dut_rx_port)
        fun_test.simple_assert(dut_rx_port_results, "Fetch DUT Rx port results. FPG%d" % dut_rx_port)

        dut_tx_port_results = network_controller_obj.peek_fpg_port_stats(dut_tx_port)
        fun_test.simple_assert(dut_tx_port_results, "Fetch DUT Tx port results. FPG%d" % dut_tx_port)

        dut_sample_port_results = network_controller_obj.peek_fpg_port_stats(dut_sample_port)
        fun_test.simple_assert(dut_sample_port_results, "Fetch DUT sample port results. FPG%d" % dut_sample_port)

        psw_stats = network_controller_obj.peek_psw_global_stats()
        fun_test.simple_assert(psw_stats, "Fetch PSW global stats")

        sample_stats = network_controller_obj.show_sample_stats()
        fun_test.simple_assert(sample_stats, "Fetch Sample stats")

        fun_test.log("DUT Rx Port %d Results: %s" % (dut_rx_port, dut_rx_port_results))
        fun_test.log("DUT Tx Port %d Results: %s" % (dut_tx_port, dut_tx_port_results))
        fun_test.log("DUT Sample Port %d Results: %s" % (dut_sample_port, dut_sample_port_results))
        fun_test.log("PSW stats: %s" % psw_stats)
        fun_test.log("Sample stats: %s" % sample_stats)

        checkpoint = "Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count"
        frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_results, stat_type=FRAMES_RECEIVED_OK,
                                                     tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on FPG%d: %d" % (
            dut_rx_port, frames_received, dut_tx_port, frames_transmitted))
        fun_test.test_assert_expected(expected=frames_received, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Ensure Tx frame count must be equal to sample frame count"
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_sample_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on Sample port FPG%d: %d" % (
            dut_rx_port, frames_received, dut_sample_port, frames_transmitted))
        fun_test.test_assert_expected(expected=frames_received, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Ensure PSW sample_pkt counter must be equal to no of frames transmitted"
        parsed_input_stats_1 = get_psw_global_stats_values(input=True, psw_stats_output=psw_stats_before,
                                                           input_key_list=[PSW_SAMPLED_PACKET_COUNT])

        parsed_input_stats_2 = get_psw_global_stats_values(input=True, psw_stats_output=psw_stats,
                                                           input_key_list=[PSW_SAMPLED_PACKET_COUNT])

        psw_diff_stats = get_diff_stats(old_stats=parsed_input_stats_1['input'],
                                        new_stats=parsed_input_stats_2['input'],
                                        stats_list=[PSW_SAMPLED_PACKET_COUNT])
        fun_test.test_assert_expected(expected=frames_received, actual=int(psw_diff_stats['sampled_pkt']),
                                      message=checkpoint)

        checkpoint = "Ensure sample counter for a rule must be equal to Tx frames"
        sample_diff_stats = get_diff_stats(old_stats=sample_stats_before[str(self.sample_id)],
                                           new_stats=sample_stats[str(self.sample_id)])
        fun_test.test_assert_expected(expected=frames_received,
                                      actual=int(sample_diff_stats['count']),
                                      message=checkpoint)

        # Validate Spirent stats
        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Rx spirent port FrameCount"
        fun_test.test_assert_expected(expected=tx_port_result['GeneratorFrameCount'],
                                      actual=rx_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Sample spirent port FrameCount"
        fun_test.test_assert_expected(expected=tx_port_result['GeneratorFrameCount'],
                                      actual=sample_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure no errors are seen on Rx spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure no errors are seen on Sample spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=sample_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure all the fields in a packet is correct"
        parser_obj = PcapParser(filename=self.capture_results['pcap_file_path'])
        packets = parser_obj.get_captures_from_file()
        result = parser_obj.validate_sample_packets_in_file(packets=packets, header_objs=self.header_objs)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Clear FPG port stats on DUT"
        for port_num in dut_config['ports']:
            shape = 0
            if port_num == 1 or port_num == 2:
                shape = 1
            result = network_controller_obj.clear_port_stats(port_num=port_num, shape=shape)
            fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
        fun_test.add_checkpoint(checkpoint=checkpoint)

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Delete sample rule for id: %d" % self.sample_id
        result = network_controller_obj.disable_sample_rule(id=self.sample_id, fpg=dut_rx_port, dest=dut_sample_port)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Get PSW stats before traffic"
        psw_stats_before = network_controller_obj.peek_psw_global_stats()
        fun_test.test_assert(psw_stats_before, checkpoint)

        checkpoint = "Get Sample stats before traffic"
        sample_stats_before = network_controller_obj.show_sample_stats()
        fun_test.test_assert(sample_stats_before, checkpoint)

        checkpoint = "Start traffic from %s port for %d secs" % (tx_port, TRAFFIC_DURATION)
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)

        fun_test.sleep("Traffic to complete", seconds=40)

        # Getting Spirent results
        checkpoint = "Fetch Tx Port Results for %s" % tx_port
        tx_port_result = template_obj.stc_manager.get_generator_port_results(
            port_handle=tx_port, subscribe_handle=subscribed_results['generator_subscribe'])
        fun_test.simple_assert(expression=tx_port_result, message=checkpoint)

        checkpoint = "Fetch Rx Port Results for %s" % rx_port
        rx_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=rx_port_result, message=checkpoint)

        checkpoint = "Fetch Sample Port Results for %s" % sample_port
        sample_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=sample_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=sample_port_result, message=checkpoint)

        fun_test.log("Tx Port: %s" % tx_port_result)
        fun_test.log("Rx Port: %s" % rx_port_result)
        fun_test.log("Sample Port: %s" % sample_port_result)

        # Validate DUT stats
        dut_rx_port_results = network_controller_obj.peek_fpg_port_stats(dut_rx_port)
        fun_test.simple_assert(dut_rx_port_results, "Fetch DUT Rx port results. FPG%d" % dut_rx_port)

        dut_tx_port_results = network_controller_obj.peek_fpg_port_stats(dut_tx_port)
        fun_test.simple_assert(dut_tx_port_results, "Fetch DUT Tx port results. FPG%d" % dut_tx_port)

        dut_sample_port_results = network_controller_obj.peek_fpg_port_stats(dut_sample_port)
        fun_test.simple_assert(dut_sample_port_results, "Fetch DUT sample port results. FPG%d" % dut_sample_port)

        psw_stats = network_controller_obj.peek_psw_global_stats()
        fun_test.simple_assert(psw_stats, "Fetch PSW global stats")

        sample_stats = network_controller_obj.show_sample_stats()
        fun_test.simple_assert(sample_stats, "Fetch Sample stats")

        fun_test.log("DUT Rx Port %d Results: %s" % (dut_rx_port, dut_rx_port_results))
        fun_test.log("DUT Tx Port %d Results: %s" % (dut_tx_port, dut_tx_port_results))
        fun_test.log("DUT Sample Port %d Results: %s" % (dut_sample_port, dut_sample_port_results))
        fun_test.log("PSW stats: %s" % psw_stats)
        fun_test.log("Sample stats: %s" % sample_stats)

        checkpoint = "Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count"
        frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_results, stat_type=FRAMES_RECEIVED_OK,
                                                     tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on FPG%d: %d" % (
            dut_rx_port, frames_received, dut_tx_port, frames_transmitted))
        fun_test.test_assert_expected(expected=frames_received, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Ensure no packets are transmitted on sampled port FPG%d" % dut_sample_port
        sample_frames_transmitted = get_dut_output_stats_value(result_stats=dut_sample_port_results,
                                                               stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Transmitted on Sample port FPG%d: %s" % (dut_sample_port, sample_frames_transmitted))
        fun_test.test_assert(sample_frames_transmitted is None, message=checkpoint)

        checkpoint = "Ensure PSW sample_pkt counter must be 0 as no packets are sampled"
        parsed_input_stats_1 = get_psw_global_stats_values(input=True, psw_stats_output=psw_stats_before,
                                                           input_key_list=[PSW_SAMPLED_PACKET_COUNT])

        parsed_input_stats_2 = get_psw_global_stats_values(input=True, psw_stats_output=psw_stats,
                                                           input_key_list=[PSW_SAMPLED_PACKET_COUNT])

        psw_diff_stats = get_diff_stats(old_stats=parsed_input_stats_1['input'],
                                        new_stats=parsed_input_stats_2['input'],
                                        stats_list=[PSW_SAMPLED_PACKET_COUNT])
        fun_test.test_assert_expected(expected=0, actual=int(psw_diff_stats['sampled_pkt']),
                                      message=checkpoint)

        checkpoint = "Ensure no packets are getting sampled in sample stats"
        sample_diff_stats = get_diff_stats(old_stats=sample_stats_before[str(self.sample_id)],
                                           new_stats=sample_stats[str(self.sample_id)])
        fun_test.test_assert_expected(expected=0,
                                      actual=int(sample_diff_stats['count']),
                                      message=checkpoint)

        # Validate Spirent stats
        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Rx spirent port FrameCount"
        fun_test.test_assert_expected(expected=tx_port_result['GeneratorFrameCount'],
                                      actual=rx_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure no frames received on sample spirent port"
        fun_test.test_assert_expected(expected=0,
                                      actual=sample_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure no errors are seen on Rx spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure no errors are seen on Sample spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=sample_port_result)
        fun_test.test_assert(result['result'], checkpoint)

    def cleanup(self):
        dut_rx_port = dut_config['ports'][0]
        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Delete sample rule for id: %d" % self.sample_id
        network_controller_obj.disable_sample_rule(id=self.sample_id, fpg=dut_rx_port, dest=dut_sample_port)
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Delete the stream"
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Delete tmp pcap file %s" % self.capture_results['pcap_file_path']
        fun_test.remove_file(self.capture_results['pcap_file_path'])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)


if __name__ == '__main__':
    ts = SpirentSetup()

    ts.add_test_case(SampleIngressFPGtoFPG())
    ts.add_test_case(SampleIngressFPGtoFPGWithRate())
    ts.add_test_case(SampleFCOIngressFPGtoFPG())
    ts.add_test_case(SamplePPStoFPG())
    ts.add_test_case(SampleEgressFPGtoFPG())
    ts.add_test_case(SampleIngressFPGtoFPGDisable())

    ts.run()
