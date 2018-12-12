"""
Author: Rushikesh Pendse

Includes Following Sampling Cases
1. SampleIngressFPGtoFPGIPv6
2. SampleIngressDropIpChecksumError
3. SampleSinglePacketMultiDestination (Multiple Destination Single Source)
4. SampleFlagMaskTTL0Packets (Flag Mask 45)
5. SampleMultiSourceSameDestination (Multiple Sources Single Destination)
6. SampleIngressEgressMTUCase
7. SampleSamePortIngressEgress
8. SampleIngressEgressSamePacket
9. SampleACLtoFPG
10. SampleIngressARPRequest
11. SampleIngressLLDP
12. SampleIngressDropFSFHwError
13. SampleIngressDropIPv4VerError
14. SampleIngressDropFwdErrorWrongDIP
15. SampleEgressMTUCase
16. SampleEgressDropACL
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
NUM_PORTS = 5
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
            sample_port, generator_port_obj_dict, analyzer_port_obj_dict, port4, cc_port

        chassis_type = fun_test.get_local_setting(setting="chassis_type")
        spirent_config = nu_config_obj.read_traffic_generator_config()

        dut_config = nu_config_obj.read_dut_config(dut_type=NuConfigManager.DUT_TYPE_PALLADIUM,
                                                   flow_type=NuConfigManager.SAMPLE_FLOW_TYPE,
                                                   flow_direction=NuConfigManager.FLOW_DIRECTION_NU_NU)

        template_obj = SpirentEthernetTrafficTemplate(session_name="sample", spirent_config=spirent_config,
                                                      chassis_type=chassis_type)
        result = template_obj.setup(no_of_ports_needed=NUM_PORTS, flow_type=NuConfigManager.SAMPLE_FLOW_TYPE,
                                    flow_direction=NuConfigManager.FLOW_DIRECTION_NU_NU)
        fun_test.test_assert(result['result'], "Ensure Setup is done")

        dpc_server_ip = dut_config["dpcsh_tcp_proxy_ip"]
        dpc_server_port = dut_config["dpcsh_tcp_proxy_port"]

        tx_port = result['port_list'][0]
        rx_port = result['port_list'][1]
        sample_port = result['port_list'][2]
        port4 = result['port_list'][3]
        cc_port = result['port_list'][4]

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


class SampleIngressFPGtoFPGIPv6(FunTestCase):
    l2_config = None
    l3_config = None
    load = 100
    load_type = StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND
    stream_obj = None
    sample_id = 48
    header_objs = {'eth_obj': None, 'ip_obj': None, 'tcp_obj': None}
    capture_results = None
    spirent_tx_port = None
    spirent_rx_port = None

    def describe(self):
        self.set_test_details(id=1, summary="Test Ingress Traffic Sampling FPG to FPG (IPv6)",
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
        self.l2_config = spirent_config['l2_config']
        self.l3_config = spirent_config['l3_config']['ipv6']

        self.spirent_tx_port = tx_port
        self.spirent_rx_port = rx_port

        checkpoint = "Create stream on %s port" % self.spirent_tx_port
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_PRBS,
                                      insert_signature=True,
                                      load=self.load,
                                      load_unit=self.load_type,
                                      frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_RANDOM,
                                      min_frame_length=98, max_frame_length=1500)
        stream_created = template_obj.configure_stream_block(stream_block_obj=self.stream_obj,
                                                             port_handle=self.spirent_tx_port, ip_header_version=6)
        fun_test.test_assert(stream_created, checkpoint)

        ethernet_obj = Ethernet2Header(destination_mac=self.l2_config['destination_mac'],
                                       ether_type=Ethernet2Header.INTERNET_IPV6_ETHERTYPE)

        checkpoint = "Configure Mac address for %s " % self.stream_obj.spirent_handle
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ethernet_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        ip_header_obj = Ipv6Header(destination_address=self.l3_config['destination_ip1'],
                                   next_header=Ipv4Header.PROTOCOL_TYPE_TCP)
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

        checkpoint = "Start traffic from %s port for %d secs" % (self.spirent_tx_port, TRAFFIC_DURATION)
        result = template_obj.enable_generator_configs(generator_configs=[
            generator_port_obj_dict[self.spirent_tx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)

        checkpoint = "Packet captured on %s sample port" % sample_port
        self.capture_results = template_obj.start_default_capture_save_locally(port_handle=sample_port,
                                                                               sleep_time=10)
        fun_test.test_assert(self.capture_results['result'], checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION)

        # Getting Spirent results
        checkpoint = "Fetch Tx Port Results for %s" % self.spirent_tx_port
        tx_port_result = template_obj.stc_manager.get_generator_port_results(
            port_handle=self.spirent_tx_port, subscribe_handle=subscribed_results['generator_subscribe'])
        fun_test.simple_assert(expression=tx_port_result, message=checkpoint)

        checkpoint = "Fetch Rx Port Results for %s" % self.spirent_rx_port
        rx_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=self.spirent_rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
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
        result = parser_obj.validate_sample_packets_in_file(packets=packets, header_objs=self.header_objs,
                                                            ip_version=6)
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
        
        
class SampleIngressDropIpChecksumError(FunTestCase):
    l2_config = None
    l3_config = None
    load = 10
    load_type = StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND
    stream_obj = None
    sample_id = 49
    header_objs = {'eth_obj': None, 'ip_obj': None, 'tcp_obj': None}
    capture_results = None
    
    def describe(self):
        self.set_test_details(id=2, summary="Test Ingress Drop Sampling IP checksum error packet",
                              steps="""
                              1. Create TCP frame stream on Tx Port with following settings
                                 a. Frame Size Mode: Random Min: 78 B and Max: 1500 B
                                 b. Payload Type: PRBS
                                 c. Insert Signature
                                 d. Load: 100 fps
                                 e. Include IP checksum error
                              2. Configure ingress sampling rule on FPG5 and dest: FPG15
                              3. Start Traffic for %d secs
                              4. Start packet capture sampling port 
                              5. Validate that packets are getting punted to CC. Ensure packets received on ingress FPG 
                                 port is equal to packets seen on CC FPG port
                              6. Ensure Tx frame count must be equal to sample frame count
                              7. Ensure PSW sample_pkt counter must be equal to no of frames transmitted
                              8. Ensure sample counter for a rule must be equal to Tx frames
                              9. Ensure IN_FFE_DESC equal to OUT_FFE_DESC in sfg nu stats
                              10. Ensure CNTR_SAMPLERID and SAMPLER_COPY count is equal to no of frames transmitted on 
                                  sample port   
                              11. Ensure on spirent Tx port frames must be equal to Rx port frames and sample port 
                                  frames
                              12. Ensure no errors are seen on spirent ports
                              13. Ensure sample packets are exactly same as ingress packets 
                              """ % TRAFFIC_DURATION)
    
    def setup(self):
        self.l2_config = spirent_config['l2_config']
        self.l3_config = spirent_config['l3_config']['ipv4']

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

        ethernet_obj = Ethernet2Header(destination_mac=self.l2_config['destination_mac'],
                                       ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        checkpoint = "Configure Mac address for %s " % self.stream_obj.spirent_handle
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ethernet_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        ip_header_obj = Ipv4Header(destination_address=self.l3_config['destination_ip1'],
                                   protocol=Ipv4Header.PROTOCOL_TYPE_TCP, checksum=Ipv4Header.CHECKSUM_ERROR)
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
        dut_sample_port = dut_config['ports'][2]
        dut_cc_port = dut_config['ports'][4]

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
        
        checkpoint = "Get SFG NU stats before traffic"
        sfg_stats_before = network_controller_obj.peek_sfg_stats()
        fun_test.test_assert(sfg_stats_before, checkpoint)

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

        checkpoint = "Fetch CC Port Results for %s" % cc_port
        cc_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=cc_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=cc_port_result, message=checkpoint)

        checkpoint = "Fetch Sample Port Results for %s" % sample_port
        sample_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=sample_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=sample_port_result, message=checkpoint)

        fun_test.log("Tx Port: %s" % tx_port_result)
        fun_test.log("CC Port: %s" % cc_port_result)
        fun_test.log("Sample Port: %s" % sample_port_result)

        # Validate DUT stats
        dut_rx_port_results = network_controller_obj.peek_fpg_port_stats(dut_rx_port)
        fun_test.simple_assert(dut_rx_port_results, "Fetch DUT Rx port results. FPG%d" % dut_rx_port)

        dut_cc_port_results = network_controller_obj.peek_fpg_port_stats(dut_cc_port)
        fun_test.simple_assert(dut_cc_port_results, "Fetch DUT CC port results. FPG%d" % dut_cc_port)

        dut_sample_port_results = network_controller_obj.peek_fpg_port_stats(dut_sample_port)
        fun_test.simple_assert(dut_sample_port_results, "Fetch DUT sample port results. FPG%d" % dut_sample_port)

        psw_stats = network_controller_obj.peek_psw_global_stats()
        fun_test.simple_assert(psw_stats, "Fetch PSW global stats")

        sample_stats = network_controller_obj.show_sample_stats()
        fun_test.simple_assert(sample_stats, "Fetch Sample stats")
        
        sfg_stats = network_controller_obj.peek_sfg_stats()
        fun_test.simple_assert(sfg_stats, "Fetch SFG stats")

        fun_test.log("DUT Rx Port %d Results: %s" % (dut_rx_port, dut_rx_port_results))
        fun_test.log("DUT CC Port %d Results: %s" % (dut_cc_port, dut_cc_port_results))
        fun_test.log("DUT Sample Port %d Results: %s" % (dut_sample_port, dut_sample_port_results))
        fun_test.log("PSW stats: %s" % psw_stats)
        fun_test.log("Sample stats: %s" % sample_stats)
        fun_test.log("Sfg stats: %s" % sfg_stats)

        checkpoint = "Validate that packets are getting punted to CC. Ensure packets received on ingress FPG " \
                     "port is equal to packets seen on CC FPG port"
        frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_results, stat_type=FRAMES_RECEIVED_OK,
                                                     tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_cc_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on CC FPG%d: %d" % (
            dut_rx_port, frames_received, dut_cc_port, frames_transmitted))
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
        
        checkpoint = "Ensure IN_FFE_DESC equal to OUT_PSW_DESC in sfg nu stats"
        sfg_diff_stats = get_diff_stats(old_stats=sfg_stats_before, new_stats=sfg_stats)
        fun_test.test_assert_expected(expected=sfg_diff_stats[SFG_IN_FFE_DESC], actual=sfg_diff_stats[SFG_OUT_PSW_DESC],
                                      message=checkpoint)
        
        checkpoint = "Ensure CNTR_SAMPLER%d count is equal to no of frames transmitted on sample port %d" % (
            self.sample_id, dut_sample_port)
        fun_test.test_assert_expected(expected=frames_transmitted, 
                                      actual=sfg_diff_stats['CNTR_SAMPLER%d' % self.sample_id], message=checkpoint)
        
        # Validate Spirent stats
        if int(tx_port_result['GeneratorFrameCount']) == int(cc_port_result['TotalFrameCount']):
            checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Rx spirent port FrameCount"
            fun_test.test_assert_expected(expected=tx_port_result['GeneratorFrameCount'],
                                          actual=cc_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Sample spirent port FrameCount"
        fun_test.test_assert_expected(expected=tx_port_result['GeneratorFrameCount'],
                                      actual=sample_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure no errors are seen on Rx spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=cc_port_result)
        error_seen = False
        if result['Ipv4ChecksumErrorCount'] > 0:
            error_seen = True
        fun_test.test_assert(error_seen, checkpoint)

        checkpoint = "Ensure no errors are seen on Sample spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=sample_port_result)
        error_seen = False
        if result['Ipv4ChecksumErrorCount'] > 0:
            error_seen = True
        fun_test.test_assert(error_seen, checkpoint)

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


class SampleSourceMultiDestination(FunTestCase):
    l2_config = None
    l3_config = None
    load = 10
    load_type = StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND
    stream_obj = None
    sample_id1 = 54
    sample_id2 = 55
    header_objs = {'eth_obj': None, 'ip_obj': None, 'tcp_obj': None}
    capture_results = None

    def describe(self):
        self.set_test_details(id=3, summary="Test Sampling Multiple Destination Single Source",
                              steps="""
                              1. Create TCP frame stream on Tx Port with following settings
                                 a. Frame Size Mode: Random Min: 78 B and Max: 1500 B
                                 b. Payload Type: PRBS
                                 c. Insert Signature
                                 d. Load: 100 fps
                              2. Configure ingress sampling rule on FPG5 and dest: FPG15 and dest: FPG18
                              3. Start Traffic for %d secs
                              4. Start packet capture sampling ports 
                              5. Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count
                              6. Ensure Tx frame count must be equal to sample frame count on both sampling ports
                              7. Ensure PSW sample_pkt counter must be equal to no of frames transmitted
                              8. Ensure sample counter for a rule must be equal to Tx frames  
                              9. Ensure on spirent Tx port frames must be equal to Rx port frames and sample port frames
                              10. Ensure no errors are seen on spirent ports
                              11. Ensure sample packets are exactly same as ingress packets 
                              """ % TRAFFIC_DURATION)

    def setup(self):
        self.l2_config = spirent_config['l2_config']
        self.l3_config = spirent_config['l3_config']['ipv4']

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

        ethernet_obj = Ethernet2Header(destination_mac=self.l2_config['destination_mac'],
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
        dut_sample_port1 = dut_config['ports'][2]
        dut_sample_port2 = dut_config['ports'][3]

        checkpoint = "Add Ingress Sampling rule Ingress Port: FPG%d and dest port: FPG%d" % (dut_rx_port,
                                                                                             dut_sample_port1)
        result = network_controller_obj.add_ingress_sample_rule(id=self.sample_id1,
                                                                fpg=dut_rx_port, dest=dut_sample_port1)
        fun_test.test_assert(result['status'], checkpoint)

        checkpoint = "Add Ingress Sampling rule Ingress Port: FPG%d and dest port: FPG%d" % (dut_rx_port,
                                                                                             dut_sample_port2)
        result = network_controller_obj.add_ingress_sample_rule(id=self.sample_id2,
                                                                fpg=dut_rx_port, dest=dut_sample_port2)
        fun_test.test_assert(result['status'], checkpoint)

    def run(self):
        dut_rx_port = dut_config['ports'][0]
        dut_tx_port = dut_config['ports'][1]
        dut_sample_port1 = dut_config['ports'][2]
        dut_sample_port2 = dut_config['ports'][3]

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

        fun_test.sleep("Traffic to complete", seconds=35)

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

        checkpoint = "Fetch Sample Port Results for %s" % port4
        sample_port_result1 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port4, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=sample_port_result1, message=checkpoint)

        fun_test.log("Tx Port: %s" % tx_port_result)
        fun_test.log("Rx Port: %s" % rx_port_result)
        fun_test.log("Sample Port: %s" % sample_port_result)
        fun_test.log("Sample Port: %s" % sample_port_result1)

        # Validate DUT stats
        dut_rx_port_results = network_controller_obj.peek_fpg_port_stats(dut_rx_port)
        fun_test.simple_assert(dut_rx_port_results, "Fetch DUT Rx port results. FPG%d" % dut_rx_port)

        dut_tx_port_results = network_controller_obj.peek_fpg_port_stats(dut_tx_port)
        fun_test.simple_assert(dut_tx_port_results, "Fetch DUT Tx port results. FPG%d" % dut_tx_port)

        dut_sample_port1_results = network_controller_obj.peek_fpg_port_stats(dut_sample_port1)
        fun_test.simple_assert(dut_sample_port1_results, "Fetch DUT sample port results. FPG%d" % dut_sample_port1)

        dut_sample_port2_results = network_controller_obj.peek_fpg_port_stats(dut_sample_port2)
        fun_test.simple_assert(dut_sample_port2_results, "Fetch DUT sample port results. FPG%d" % dut_sample_port2)

        psw_stats = network_controller_obj.peek_psw_global_stats()
        fun_test.simple_assert(psw_stats, "Fetch PSW global stats")

        sample_stats = network_controller_obj.show_sample_stats()
        fun_test.simple_assert(sample_stats, "Fetch Sample stats")

        fun_test.log("DUT Rx Port %d Results: %s" % (dut_rx_port, dut_rx_port_results))
        fun_test.log("DUT Tx Port %d Results: %s" % (dut_tx_port, dut_tx_port_results))
        fun_test.log("DUT Sample Port %d Results: %s" % (dut_sample_port1, dut_sample_port1_results))
        fun_test.log("DUT Sample Port %d Results: %s" % (dut_sample_port2, dut_sample_port2_results))
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

        checkpoint = "Ensure Tx frame count must be equal to sample frame count port: FPG%d" % dut_sample_port1
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_sample_port1_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on Sample port FPG%d: %d" % (
            dut_rx_port, frames_received, dut_sample_port1, frames_transmitted))
        fun_test.test_assert_expected(expected=frames_received, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Ensure Tx frame count must be equal to sample frame count port: FPG%d" % dut_sample_port2
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_sample_port2_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on Sample port FPG%d: %d" % (
            dut_rx_port, frames_received, dut_sample_port2, frames_transmitted))
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

        checkpoint = "Ensure sample counter for a rule must be equal to Tx frames for sample ID: %d" % self.sample_id1
        sample_diff_stats = get_diff_stats(old_stats=sample_stats_before[str(self.sample_id1)],
                                           new_stats=sample_stats[str(self.sample_id1)])
        fun_test.test_assert_expected(expected=frames_received,
                                      actual=int(sample_diff_stats['count']),
                                      message=checkpoint)

        checkpoint = "Ensure sample counter for a rule must be equal to Tx frames for sample ID: %d" % self.sample_id2
        sample_diff_stats = get_diff_stats(old_stats=sample_stats_before[str(self.sample_id2)],
                                           new_stats=sample_stats[str(self.sample_id2)])
        fun_test.test_assert_expected(expected=frames_received,
                                      actual=int(sample_diff_stats['count']),
                                      message=checkpoint)

        # Validate Spirent stats
        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Rx spirent port FrameCount"
        fun_test.test_assert_expected(expected=int(tx_port_result['GeneratorFrameCount']),
                                      actual=int(rx_port_result['TotalFrameCount']), message=checkpoint)

        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Sample spirent port FrameCount FPG%d" % \
                     dut_sample_port1
        fun_test.test_assert_expected(expected=int(tx_port_result['GeneratorFrameCount']),
                                      actual=int(sample_port_result['TotalFrameCount']), message=checkpoint)

        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Sample spirent port FrameCount FPG%d" % \
                     dut_sample_port2
        fun_test.test_assert_expected(expected=tx_port_result['GeneratorFrameCount'],
                                      actual=sample_port_result1['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure no errors are seen on Rx spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure no errors are seen on Sample spirent port FPG%d" % dut_sample_port1
        result = template_obj.check_non_zero_error_count(rx_results=sample_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure no errors are seen on Sample spirent port FPG%d" % dut_sample_port2
        result = template_obj.check_non_zero_error_count(rx_results=sample_port_result1)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure all the fields in a packet is correct"
        parser_obj = PcapParser(filename=self.capture_results['pcap_file_path'])
        packets = parser_obj.get_captures_from_file()
        result = parser_obj.validate_sample_packets_in_file(packets=packets, header_objs=self.header_objs)
        fun_test.test_assert(result, checkpoint)

    def cleanup(self):
        dut_rx_port = dut_config['ports'][0]
        dut_sample_port1 = dut_config['ports'][2]
        dut_sample_port2 = dut_config['ports'][3]

        checkpoint = "Delete sample rule for id: %d" % self.sample_id1
        network_controller_obj.disable_sample_rule(id=self.sample_id1, fpg=dut_rx_port, dest=dut_sample_port1)
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Delete sample rule for id: %d" % self.sample_id2
        network_controller_obj.disable_sample_rule(id=self.sample_id2, fpg=dut_rx_port, dest=dut_sample_port2)
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


class SampleFlagMaskTTL0Packets(FunTestCase):
    l2_config = None
    l3_config = None
    load = 10
    load_type = StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND
    stream_obj = None
    sample_id = 1
    header_objs = {'eth_obj': None, 'ip_obj': None, 'tcp_obj': None}
    capture_results = None

    def describe(self):
        self.set_test_details(id=4, summary="Test Sampling Using FlagMask 45 (TTL 0)",
                              steps="""
                              1. Create TCP frame stream on Tx Port with following settings
                                 a. Frame Size Mode: Random Min: 78 B and Max: 1500 B
                                 b. Payload Type: PRBS
                                 c. Insert Signature
                                 d. Load: 100 fps
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
        self.l2_config = spirent_config['l2_config']
        self.l3_config = spirent_config['l3_config']['ipv4']

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

        ethernet_obj = Ethernet2Header(destination_mac=self.l2_config['destination_mac'],
                                       ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        checkpoint = "Configure Mac address for %s " % self.stream_obj.spirent_handle
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ethernet_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        ip_header_obj = Ipv4Header(destination_address=self.l3_config['destination_ip1'],
                                   protocol=Ipv4Header.PROTOCOL_TYPE_TCP, ttl=0)
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
                                                                fpg=dut_rx_port, dest=dut_sample_port, flag_mask=45)
        fun_test.test_assert(result['status'], checkpoint)

    def run(self):
        dut_rx_port = dut_config['ports'][0]
        dut_tx_port = dut_config['ports'][4]
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
        cc_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=cc_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=cc_port_result, message=checkpoint)

        checkpoint = "Fetch Sample Port Results for %s" % sample_port
        sample_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=sample_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=sample_port_result, message=checkpoint)

        fun_test.log("Tx Port: %s" % tx_port_result)
        fun_test.log("Rx Port: %s" % cc_port_result)
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
                                      actual=cc_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Sample spirent port FrameCount"
        fun_test.test_assert_expected(expected=tx_port_result['GeneratorFrameCount'],
                                      actual=sample_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure no errors are seen on Rx spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=cc_port_result)
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
                                                   flag_mask=45)
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


class SampleMultiSourceSameDestination(FunTestCase):
    l2_config = None
    l3_config = None
    load = 100
    load_type = StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND
    stream_obj1 = None
    stream_obj2 = None
    sample_id = 56
    header_objs_stream1 = {'eth_obj': None, 'ip_obj': None, 'tcp_obj': None}
    header_objs_stream2 = {'eth_obj': None, 'ip_obj': None, 'tcp_obj': None}
    capture_results = None

    def describe(self):
        self.set_test_details(id=5, summary="Test Sample Multi Source Same Destination (Same Sample ID)",
                              steps="""
                              1. Create TCP frame stream on Tx Port with following settings
                                 a. Frame Size Mode: Random Min: 78 B and Max: 1500 B
                                 b. Payload Type: PRBS
                                 c. Insert Signature
                                 d. Load: 100 fps
                              2. Configure ingress sampling rule on FPG5 and FPG13 and dest: FPG15
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
        self.l2_config = spirent_config['l2_config']
        self.l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create stream on %s port" % tx_port
        self.stream_obj1 = StreamBlock(fill_type=StreamBlock.FILL_TYPE_PRBS,
                                       insert_signature=True,
                                       load=self.load,
                                       load_unit=self.load_type,
                                       frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_RANDOM,
                                       min_frame_length=78, max_frame_length=1500)
        stream_created = template_obj.configure_stream_block(stream_block_obj=self.stream_obj1,
                                                             port_handle=tx_port)
        fun_test.test_assert(stream_created, checkpoint)

        ethernet_obj = Ethernet2Header(destination_mac=self.l2_config['destination_mac'],
                                       ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        checkpoint = "Configure Mac address for %s " % self.stream_obj1.spirent_handle
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj1.spirent_handle,
                                                                header_obj=ethernet_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        ip_header_obj = Ipv4Header(destination_address=self.l3_config['destination_ip1'],
                                   protocol=Ipv4Header.PROTOCOL_TYPE_TCP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj1.spirent_handle,
                                                                header_obj=ip_header_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        checkpoint = "Add TCP header"
        tcp_header_obj = TCP()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj1.spirent_handle,
                                                                header_obj=tcp_header_obj, update=False)
        fun_test.simple_assert(result, checkpoint)

        self.header_objs_stream1['eth_obj'] = ethernet_obj
        self.header_objs_stream1['ip_obj'] = ip_header_obj
        self.header_objs_stream1['tcp_obj'] = tcp_header_obj

        checkpoint = "Create stream on %s port" % rx_port
        self.stream_obj2 = StreamBlock(fill_type=StreamBlock.FILL_TYPE_PRBS,
                                       insert_signature=True,
                                       load=self.load,
                                       load_unit=self.load_type,
                                       frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_RANDOM,
                                       min_frame_length=78, max_frame_length=1500)
        stream_created = template_obj.configure_stream_block(stream_block_obj=self.stream_obj2,
                                                             port_handle=rx_port)
        fun_test.test_assert(stream_created, checkpoint)

        ethernet_obj = Ethernet2Header(destination_mac=self.l2_config['destination_mac'],
                                       ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        checkpoint = "Configure Mac address for %s " % self.stream_obj2.spirent_handle
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj2.spirent_handle,
                                                                header_obj=ethernet_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        ip_header_obj = Ipv4Header(destination_address=self.l3_config['destination_ip2'],
                                   protocol=Ipv4Header.PROTOCOL_TYPE_TCP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj2.spirent_handle,
                                                                header_obj=ip_header_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        checkpoint = "Add TCP header"
        tcp_header_obj = TCP()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj2.spirent_handle,
                                                                header_obj=tcp_header_obj, update=False)
        fun_test.simple_assert(result, checkpoint)

        self.header_objs_stream2['eth_obj'] = ethernet_obj
        self.header_objs_stream2['ip_obj'] = ip_header_obj
        self.header_objs_stream2['tcp_obj'] = tcp_header_obj

        dut_rx_port1 = dut_config['ports'][0]
        dut_rx_port2 = dut_config['ports'][1]
        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Add Ingress Sampling rule Ingress Port: FPG%d and dest port: FPG%d" % (dut_rx_port1,
                                                                                             dut_sample_port)
        result = network_controller_obj.add_ingress_sample_rule(id=self.sample_id,
                                                                fpg=dut_rx_port1, dest=dut_sample_port)
        fun_test.test_assert(result['status'], checkpoint)

        checkpoint = "Add Ingress Sampling rule Ingress Port: FPG%d and dest port: FPG%d" % (dut_rx_port2,
                                                                                             dut_sample_port)
        result = network_controller_obj.add_ingress_sample_rule(id=self.sample_id,
                                                                fpg=dut_rx_port2, dest=dut_sample_port)
        fun_test.test_assert(result['status'], checkpoint)

    def run(self):
        dut_rx_port1 = dut_config['ports'][0]
        dut_rx_port2 = dut_config['ports'][1]
        dut_tx_port1 = dut_config['ports'][1]
        dut_tx_port2 = dut_config['ports'][0]
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
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port],
                                                                          generator_port_obj_dict[rx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)

        checkpoint = "Packet captured on %s sample port" % sample_port
        self.capture_results = template_obj.start_default_capture_save_locally(port_handle=sample_port,
                                                                               sleep_time=10)
        fun_test.test_assert(self.capture_results['result'], checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION)

        # Getting Spirent results
        checkpoint = "Fetch Tx Port Results for %s" % tx_port
        tx_port_result1 = template_obj.stc_manager.get_generator_port_results(
            port_handle=tx_port, subscribe_handle=subscribed_results['generator_subscribe'])
        fun_test.simple_assert(expression=tx_port_result1, message=checkpoint)

        checkpoint = "Fetch Tx Port Results for %s" % rx_port
        tx_port_result2 = template_obj.stc_manager.get_generator_port_results(
            port_handle=rx_port, subscribe_handle=subscribed_results['generator_subscribe'])
        fun_test.simple_assert(expression=tx_port_result2, message=checkpoint)

        checkpoint = "Fetch Rx Port Results for %s" % rx_port
        rx_port_result1 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=rx_port_result1, message=checkpoint)

        checkpoint = "Fetch Rx Port Results for %s" % tx_port
        rx_port_result2 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=tx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=rx_port_result2, message=checkpoint)

        checkpoint = "Fetch Sample Port Results for %s" % sample_port
        sample_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=sample_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=sample_port_result, message=checkpoint)

        fun_test.log("Spirent Tx Port FPG%d: %s" % (dut_rx_port1, tx_port_result1))
        fun_test.log("Spirent Tx Port FPG%d: %s" % (dut_rx_port2, tx_port_result2))
        fun_test.log("Spirent Rx Port FPG%d: %s" % (dut_tx_port1, rx_port_result1))
        fun_test.log("Spirent Rx Port FPG%d: %s" % (dut_tx_port2, rx_port_result2))
        fun_test.log("Spirent Sample Port FPG%d: %s" % (dut_sample_port, sample_port_result))

        # Validate DUT stats
        dut_rx_port_results1 = network_controller_obj.peek_fpg_port_stats(dut_rx_port1)
        fun_test.simple_assert(dut_rx_port_results1, "Fetch DUT Rx port results. FPG%d" % dut_rx_port1)

        dut_rx_port_results2 = network_controller_obj.peek_fpg_port_stats(dut_rx_port2)
        fun_test.simple_assert(dut_rx_port_results1, "Fetch DUT Rx port results. FPG%d" % dut_rx_port2)

        dut_tx_port_results1 = network_controller_obj.peek_fpg_port_stats(dut_tx_port1)
        fun_test.simple_assert(dut_tx_port_results1, "Fetch DUT Tx port results. FPG%d" % dut_tx_port1)

        dut_tx_port_results2 = network_controller_obj.peek_fpg_port_stats(dut_tx_port2)
        fun_test.simple_assert(dut_tx_port_results2, "Fetch DUT Tx port results. FPG%d" % dut_tx_port2)

        dut_sample_port_results = network_controller_obj.peek_fpg_port_stats(dut_sample_port)
        fun_test.simple_assert(dut_sample_port_results, "Fetch DUT sample port results. FPG%d" % dut_sample_port)

        psw_stats = network_controller_obj.peek_psw_global_stats()
        fun_test.simple_assert(psw_stats, "Fetch PSW global stats")

        sample_stats = network_controller_obj.show_sample_stats()
        fun_test.simple_assert(sample_stats, "Fetch Sample stats")

        fun_test.log("DUT Rx Port FPG%d Results: %s" % (dut_rx_port1, dut_rx_port_results1))
        fun_test.log("DUT Rx Port FPG%d Results: %s" % (dut_rx_port2, dut_rx_port_results2))
        fun_test.log("DUT Tx Port FPG%d Results: %s" % (dut_tx_port1, dut_tx_port_results1))
        fun_test.log("DUT Tx Port FPG%d Results: %s" % (dut_tx_port2, dut_tx_port_results2))
        fun_test.log("DUT Sample Port FPG%d Results: %s" % (dut_sample_port, dut_sample_port_results))
        fun_test.log("PSW stats: %s" % psw_stats)
        fun_test.log("Sample stats: %s" % sample_stats)

        checkpoint = "Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count " \
                     "(FPG%d --> FPG%d)" % (dut_rx_port1, dut_tx_port1)
        frames_received1 = get_dut_output_stats_value(result_stats=dut_rx_port_results1, stat_type=FRAMES_RECEIVED_OK,
                                                      tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_results1,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on FPG%d: %d" % (
            dut_rx_port1, frames_received1, dut_tx_port1, frames_transmitted))
        fun_test.test_assert_expected(expected=frames_received1, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count " \
                     "(FPG%d --> FPG%d)" % (dut_rx_port2, dut_tx_port2)
        frames_received2 = get_dut_output_stats_value(result_stats=dut_rx_port_results2, stat_type=FRAMES_RECEIVED_OK,
                                                      tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_results2,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on FPG%d: %d" % (
            dut_rx_port1, frames_received2, dut_tx_port1, frames_transmitted))
        fun_test.test_assert_expected(expected=frames_received2, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Ensure sample frame count must be equal to frames received on FPG%d + frames received on " \
                     "FPG%d" % (dut_rx_port1, dut_rx_port2)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_sample_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        expected_sample_frames = frames_received1 + frames_received2
        fun_test.log("Expected Frames on sample port (Received FPG%d frames + Received FPG%d frames): %d and "
                     "Frames Transmitted on Sample port FPG%d: %d" % (dut_rx_port1, dut_rx_port2,
                                                                      expected_sample_frames, dut_sample_port,
                                                                      frames_transmitted))
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

        checkpoint = "Ensure sample counter for a rule must be equal to frames received on FPG%d + frames received " \
                     "on FPG%d" % (dut_rx_port1, dut_rx_port2)
        sample_diff_stats = get_diff_stats(old_stats=sample_stats_before[str(self.sample_id)],
                                           new_stats=sample_stats[str(self.sample_id)])
        fun_test.test_assert_expected(expected=expected_sample_frames,
                                      actual=int(sample_diff_stats['count']),
                                      message=checkpoint)

        # Validate Spirent stats
        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Rx spirent port FrameCount"
        fun_test.test_assert_expected(expected=tx_port_result1['GeneratorFrameCount'],
                                      actual=rx_port_result1['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Rx spirent port FrameCount"
        fun_test.test_assert_expected(expected=tx_port_result2['GeneratorFrameCount'],
                                      actual=rx_port_result2['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Sample spirent port FrameCount"
        fun_test.test_assert_expected(expected=expected_sample_frames,
                                      actual=sample_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure no errors are seen on Rx spirent port1"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_result1)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure no errors are seen on Rx spirent port2"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_result2)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure no errors are seen on Sample spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=sample_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure all the fields in a packet is correct for dest address %s" % \
                     self.header_objs_stream1['ip_obj'].destAddr
        parser_obj = PcapParser(filename=self.capture_results['pcap_file_path'])
        packets = parser_obj.get_captures_from_file(display_filter="ip.addr == %s" %
                                                                   self.header_objs_stream1['ip_obj'].destAddr)
        result = parser_obj.validate_sample_packets_in_file(packets=packets, header_objs=self.header_objs_stream1)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Ensure all the fields in a packet is correct for dest address %s" % \
                     self.header_objs_stream2['ip_obj'].destAddr
        parser_obj = PcapParser(filename=self.capture_results['pcap_file_path'])
        packets = parser_obj.get_captures_from_file(display_filter="ip.addr == %s" %
                                                                   self.header_objs_stream2['ip_obj'].destAddr)
        result = parser_obj.validate_sample_packets_in_file(packets=packets, header_objs=self.header_objs_stream2)

        fun_test.test_assert(result, checkpoint)

    def cleanup(self):
        dut_rx_port1 = dut_config['ports'][0]
        dut_rx_port2 = dut_config['ports'][1]
        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Delete sample rule for id: %d" % self.sample_id
        network_controller_obj.disable_sample_rule(id=self.sample_id, fpg=dut_rx_port1, dest=dut_sample_port)
        network_controller_obj.disable_sample_rule(id=self.sample_id, fpg=dut_rx_port2, dest=dut_sample_port)
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Delete the stream"
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj1.spirent_handle])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Delete the stream"
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj2.spirent_handle])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Delete tmp pcap file %s" % self.capture_results['pcap_file_path']
        fun_test.remove_file(self.capture_results['pcap_file_path'])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)


class SampleIngressEgressMTUCase(FunTestCase):
    l2_config = None
    l3_config = None
    load = 10
    load_type = StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND
    stream_obj = None
    sample_id = 59
    header_objs = {'eth_obj': None, 'ip_obj': None, 'tcp_obj': None}
    MTU = 1500

    def describe(self):
        self.set_test_details(id=6, summary="Test Sample Ingress and Egress MTU case (Default MTU 1500)",
                              steps="""
                              1. Create TCP frame stream on Tx Port with following settings
                                 a. Frame Size Mode: Fixed 9000 B
                                 b. Payload Type: PRBS
                                 c. Insert Signature
                                 d. Load: 10 fps
                              2. Configure ingress sampling rule on FPG5 and dest: FPG15
                              3. Start Traffic for %d secs
                              4. Validate FPG ports stats ensure frames on Rx ports are marked as Jumbo
                              5. Ensure Tx frame count on DUT is 0 
                              6. Ensure sample counter for a rule must be equal to no of Jumbo frames received 
                              7. Ensure on spirent Rx port frame count is 0 and spirent sample port should not receive 
                                 any frames  
                              8. Ensure no errors are seen on spirent ports
                              9. Disable Ingress sampling rule 
                              10. Start same traffic for %d secs
                              11. Ensure no frames sample on sample port
                              12. Configure Egress sampling rule on FPG5 and dest: FPG15
                              13. Start same traffic for %d secs
                              14. Repeat above step 4,5,6 and 7, 8
                              """ % (TRAFFIC_DURATION, TRAFFIC_DURATION, TRAFFIC_DURATION))

    def setup(self):
        self.l2_config = spirent_config['l2_config']
        self.l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create stream on %s port" % tx_port
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_PRBS,
                                      insert_signature=True,
                                      load=self.load,
                                      load_unit=self.load_type,
                                      frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_FIXED,
                                      fixed_frame_length=9000)
        stream_created = template_obj.configure_stream_block(stream_block_obj=self.stream_obj,
                                                             port_handle=tx_port)
        fun_test.test_assert(stream_created, checkpoint)

        ethernet_obj = Ethernet2Header(destination_mac=self.l2_config['destination_mac'],
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

        checkpoint = "Change DUT ports MTU to %d" % self.MTU
        for port_num in dut_config['ports']:
            if port_num == 1 or port_num == 2:
                shape = 1
            else:
                shape = 0
            mtu_changed = network_controller_obj.set_port_mtu(port_num=port_num, mtu_value=self.MTU, shape=shape)
            fun_test.simple_assert(mtu_changed, "Change MTU on DUT port %d to %d" % (port_num, self.MTU))
        fun_test.add_checkpoint(checkpoint)

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

        checkpoint = "Validate FPG ports stats ensure frames on Rx ports are marked as Jumbo"
        frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_results, stat_type=FRAME_TOO_LONG_ERRORS,
                                                     tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Too Long Errors Received on FPG%d: %d " % (dut_rx_port, frames_received))
        fun_test.test_assert_expected(expected=None, actual=frames_transmitted,
                                      message="No frames are transmitted from FPG%d" % dut_tx_port)

        fun_test.test_assert_expected(expected=tx_port_result['GeneratorFrameCount'], actual=frames_received,
                                      message=checkpoint)

        checkpoint = "Ensure no frames are transmitted from sample port FPG%d" % dut_sample_port
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_sample_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Transmitted on Sample port FPG%d: %s" % (dut_sample_port, frames_transmitted))
        fun_test.test_assert_expected(expected=None, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Ensure sample counter for a rule must be equal to no of Jumbo frames received"
        sample_diff_stats = get_diff_stats(old_stats=sample_stats_before[str(self.sample_id)],
                                           new_stats=sample_stats[str(self.sample_id)])
        fun_test.test_assert_expected(expected=frames_received,
                                      actual=int(sample_diff_stats['count']),
                                      message=checkpoint)

        # Validate Spirent stats
        checkpoint = "Ensure on spirent Rx port frame count is 0"
        fun_test.test_assert_expected(expected=0,
                                      actual=rx_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure spirent sample port should not receive any frames"
        fun_test.test_assert_expected(expected=0,
                                      actual=sample_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure no errors are seen on Rx spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure no errors are seen on Sample spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=sample_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Delete sample rule for id: %d" % self.sample_id
        result = network_controller_obj.disable_sample_rule(id=self.sample_id, fpg=dut_rx_port, dest=dut_sample_port)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Clear FPG port stats on DUT"
        for port_num in dut_config['ports']:
            shape = 0
            if port_num == 1 or port_num == 2:
                shape = 1
            result = network_controller_obj.clear_port_stats(port_num=port_num, shape=shape)
            fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
        fun_test.add_checkpoint(checkpoint=checkpoint)

        checkpoint = "Start traffic from %s port for %d secs" % (tx_port, TRAFFIC_DURATION)
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION)

        psw_stats = network_controller_obj.peek_psw_global_stats()
        fun_test.simple_assert(psw_stats, "Fetch PSW global stats")

        sample_stats_after_disable = network_controller_obj.show_sample_stats()
        fun_test.simple_assert(sample_stats_after_disable, "Fetch Sample stats")

        fun_test.log("PSW stats: %s" % psw_stats)
        fun_test.log("Sample stats: %s" % sample_stats_after_disable)

        checkpoint = "Ensure sample counter for a rule must be equal to no of Jumbo frames received"
        sample_diff_stats = get_diff_stats(old_stats=sample_stats[str(self.sample_id)],
                                           new_stats=sample_stats_after_disable[str(self.sample_id)])
        fun_test.test_assert_expected(expected=0,
                                      actual=int(sample_diff_stats['count']),
                                      message=checkpoint)

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Clear FPG port stats on DUT"
        for port_num in dut_config['ports']:
            shape = 0
            if port_num == 1 or port_num == 2:
                shape = 1
            result = network_controller_obj.clear_port_stats(port_num=port_num, shape=shape)
            fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
        fun_test.add_checkpoint(checkpoint=checkpoint)

        checkpoint = "Add Egress Sampling rule Ingress Port: FPG%d and dest port: FPG%d" % (dut_rx_port,
                                                                                            dut_sample_port)
        result = network_controller_obj.add_egress_sample_rule(id=self.sample_id,
                                                               fpg=dut_rx_port, dest=dut_sample_port)
        fun_test.test_assert(result['status'], checkpoint)

        checkpoint = "Start traffic from %s port for %d secs" % (tx_port, TRAFFIC_DURATION)
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)

        fun_test.sleep("Traffic to complete", seconds=40)

        # Getting Spirent results
        checkpoint = "Fetch Tx Port Results for %s" % tx_port
        tx_port_result_egress = template_obj.stc_manager.get_generator_port_results(
            port_handle=tx_port, subscribe_handle=subscribed_results['generator_subscribe'])
        fun_test.simple_assert(expression=tx_port_result_egress, message=checkpoint)

        checkpoint = "Fetch Rx Port Results for %s" % rx_port
        rx_port_result_egress = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=rx_port_result_egress, message=checkpoint)

        checkpoint = "Fetch Sample Port Results for %s" % sample_port
        sample_port_result_egress = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=sample_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=sample_port_result_egress, message=checkpoint)

        fun_test.log("Tx Port: %s" % tx_port_result_egress)
        fun_test.log("Rx Port: %s" % rx_port_result_egress)
        fun_test.log("Sample Port: %s" % sample_port_result_egress)

        # Validate DUT stats
        dut_rx_port_results_egress = network_controller_obj.peek_fpg_port_stats(dut_rx_port)
        fun_test.simple_assert(dut_rx_port_results_egress, "Fetch DUT Rx port results. FPG%d" % dut_rx_port)

        dut_tx_port_results_egress = network_controller_obj.peek_fpg_port_stats(dut_tx_port)
        fun_test.simple_assert(dut_tx_port_results_egress, "Fetch DUT Tx port results. FPG%d" % dut_tx_port)

        dut_sample_port_results_egress = network_controller_obj.peek_fpg_port_stats(dut_sample_port)
        fun_test.simple_assert(dut_sample_port_results_egress, "Fetch DUT sample port results. FPG%d" % dut_sample_port)

        psw_stats = network_controller_obj.peek_psw_global_stats()
        fun_test.simple_assert(psw_stats, "Fetch PSW global stats")

        sample_stats_egress = network_controller_obj.show_sample_stats()
        fun_test.simple_assert(sample_stats_egress, "Fetch Sample stats")

        fun_test.log("DUT Rx Port %d Results: %s" % (dut_rx_port, dut_rx_port_results_egress))
        fun_test.log("DUT Tx Port %d Results: %s" % (dut_tx_port, dut_tx_port_results_egress))
        fun_test.log("DUT Sample Port %d Results: %s" % (dut_sample_port, dut_sample_port_results_egress))
        fun_test.log("PSW stats: %s" % psw_stats)
        fun_test.log("Sample stats: %s" % sample_stats_egress)

        # TODO: Check exact behaviour for egress sampling rule and Jumbo packet

        checkpoint = "Validate FPG ports stats ensure frames on Rx ports are marked as Jumbo"
        frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_results_egress,
                                                     stat_type=FRAME_TOO_LONG_ERRORS, tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_results_egress,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Too Long Errors Received on FPG%d: %d " % (dut_rx_port, frames_received))
        fun_test.test_assert_expected(expected=None, actual=frames_transmitted,
                                      message="No frames are transmitted from FPG%d" % dut_tx_port)

        fun_test.test_assert_expected(expected=tx_port_result['GeneratorFrameCount'], actual=frames_received,
                                      message=checkpoint)

        checkpoint = "Ensure no frames are transmitted from sample port FPG%d" % dut_sample_port
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_sample_port_results_egress,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Transmitted on Sample port FPG%d: %s" % (dut_sample_port, frames_transmitted))
        fun_test.test_assert_expected(expected=None, actual=frames_transmitted, message=checkpoint)

        # TODO: For egress sampling, only those packets should be sample which are transmitted.
        # TODO: In this case no packets are being transmitted so we should not see any sample packets
        checkpoint = "Ensure sample counter for a rule must be equal to no of Jumbo frames received"
        sample_diff_stats = get_diff_stats(old_stats=sample_stats_after_disable[str(self.sample_id)],
                                           new_stats=sample_stats_egress[str(self.sample_id)])
        fun_test.test_assert_expected(expected=frames_received,
                                      actual=int(sample_diff_stats['count']),
                                      message=checkpoint)

        # Validate Spirent stats
        checkpoint = "Ensure on spirent Rx port frame count is 0"
        fun_test.test_assert_expected(expected=0,
                                      actual=rx_port_result_egress['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure spirent sample port should not receive any frames"
        fun_test.test_assert_expected(expected=0,
                                      actual=sample_port_result_egress['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure no errors are seen on Rx spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_result_egress)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure no errors are seen on Sample spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=sample_port_result_egress)
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

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)


class SampleSamePortIngressEgress(FunTestCase):
    l2_config = None
    l3_config = None
    load = 10
    load_type = StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND
    stream_obj1 = None
    stream_obj2 = None
    sample_id1 = 60
    sample_id2 = 59
    header_objs1 = {'eth_obj': None, 'ip_obj': None, 'tcp_obj': None}
    header_objs2 = {'eth_obj': None, 'ip_obj': None, 'tcp_obj': None}
    capture_results_port1 = None
    capture_results_port2 = None

    def describe(self):
        self.set_test_details(id=7, summary="Test Sampling on same port Ingress and Egress",
                              steps="""
                              1. Create TCP frame stream on Tx Port with following settings
                                 a. Frame Size Mode: Random Min: 78 B and Max: 1500 B
                                 b. Payload Type: PRBS
                                 c. Insert Signature
                                 d. Load: 10 fps
                              2. Configure ingress sampling rule on FPG5 and dest: FPG15 
                              3. Configure egress sampling rule on FPG5 and dest: FPG18
                              4. Start Traffic for %d secs
                              5. Start packet capture sampling ports 
                              6. Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count
                              7. Ensure Tx frame count must be equal to sample frame count on both sampling ports
                              8. Ensure PSW sample_pkt counter must be equal to no of frames transmitted
                              9. Ensure sample counter for a rule must be equal to Tx frames  
                              10. Ensure on spirent Tx port frames must be equal to Rx port frames and sample port frames
                              11. Ensure no errors are seen on spirent ports
                              12. Ensure sample packets are exactly same as ingress packets 
                              """ % TRAFFIC_DURATION)

    def setup(self):
        self.l2_config = spirent_config['l2_config']
        self.l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create stream on %s port" % tx_port
        self.stream_obj1 = StreamBlock(fill_type=StreamBlock.FILL_TYPE_PRBS,
                                       insert_signature=True,
                                       load=self.load,
                                       load_unit=self.load_type,
                                       frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_RANDOM,
                                       min_frame_length=78, max_frame_length=1500)
        stream_created = template_obj.configure_stream_block(stream_block_obj=self.stream_obj1,
                                                             port_handle=tx_port)
        fun_test.test_assert(stream_created, checkpoint)

        ethernet_obj = Ethernet2Header(destination_mac=self.l2_config['destination_mac'],
                                       ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        checkpoint = "Configure Mac address for %s " % self.stream_obj1.spirent_handle
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj1.spirent_handle,
                                                                header_obj=ethernet_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        ip_header_obj = Ipv4Header(destination_address=self.l3_config['destination_ip1'],
                                   protocol=Ipv4Header.PROTOCOL_TYPE_TCP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj1.spirent_handle,
                                                                header_obj=ip_header_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        checkpoint = "Add TCP header"
        tcp_header_obj = TCP()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj1.spirent_handle,
                                                                header_obj=tcp_header_obj, update=False)
        fun_test.simple_assert(result, checkpoint)

        self.header_objs1['eth_obj'] = ethernet_obj
        self.header_objs1['ip_obj'] = ip_header_obj
        self.header_objs1['tcp_obj'] = tcp_header_obj

        checkpoint = "Create stream on %s port" % rx_port
        self.stream_obj2 = StreamBlock(fill_type=StreamBlock.FILL_TYPE_PRBS,
                                       insert_signature=True,
                                       load=self.load,
                                       load_unit=self.load_type,
                                       frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_RANDOM,
                                       min_frame_length=78, max_frame_length=1500)
        stream_created = template_obj.configure_stream_block(stream_block_obj=self.stream_obj2,
                                                             port_handle=rx_port)
        fun_test.test_assert(stream_created, checkpoint)

        ethernet_obj = Ethernet2Header(destination_mac=self.l2_config['destination_mac'],
                                       ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        checkpoint = "Configure Mac address for %s " % self.stream_obj2.spirent_handle
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj2.spirent_handle,
                                                                header_obj=ethernet_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        ip_header_obj = Ipv4Header(destination_address=self.l3_config['destination_ip2'],
                                   protocol=Ipv4Header.PROTOCOL_TYPE_TCP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj2.spirent_handle,
                                                                header_obj=ip_header_obj, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        checkpoint = "Add TCP header"
        tcp_header_obj = TCP()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj2.spirent_handle,
                                                                header_obj=tcp_header_obj, update=False)
        fun_test.simple_assert(result, checkpoint)

        self.header_objs2['eth_obj'] = ethernet_obj
        self.header_objs2['ip_obj'] = ip_header_obj
        self.header_objs2['tcp_obj'] = tcp_header_obj

        dut_rx_port = dut_config['ports'][0]
        dut_sample_port1 = dut_config['ports'][2]
        dut_sample_port2 = dut_config['ports'][3]

        checkpoint = "Add Ingress Sampling rule Ingress Port: FPG%d and dest port: FPG%d" % (dut_rx_port,
                                                                                             dut_sample_port1)
        result = network_controller_obj.add_ingress_sample_rule(id=self.sample_id1,
                                                                fpg=dut_rx_port, dest=dut_sample_port1)
        fun_test.test_assert(result['status'], checkpoint)

        checkpoint = "Add Egress Sampling rule Ingress Port: FPG%d and dest port: FPG%d" % (dut_rx_port,
                                                                                            dut_sample_port2)
        result = network_controller_obj.add_egress_sample_rule(id=self.sample_id2,
                                                               fpg=dut_rx_port, dest=dut_sample_port2)
        fun_test.test_assert(result['status'], checkpoint)

    def run(self):
        dut_rx_port = dut_config['ports'][0]
        dut_tx_port = dut_config['ports'][1]
        dut_sample_port1 = dut_config['ports'][2]
        dut_sample_port2 = dut_config['ports'][3]

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
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port],
                                                                          generator_port_obj_dict[rx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)

        checkpoint = "Packet captured on %s sample port" % sample_port
        self.capture_results_port1 = template_obj.start_default_capture_save_locally(port_handle=sample_port,
                                                                                     sleep_time=10)
        fun_test.test_assert(self.capture_results_port1['result'], checkpoint)

        checkpoint = "Packet captured on %s sample port" % port4
        self.capture_results_port2 = template_obj.start_default_capture_save_locally(port_handle=port4,
                                                                                     sleep_time=10)
        fun_test.test_assert(self.capture_results_port2['result'], checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION)

        # Getting Spirent results
        checkpoint = "Fetch Tx Port Results for %s" % tx_port
        tx_port_result1 = template_obj.stc_manager.get_generator_port_results(
            port_handle=tx_port, subscribe_handle=subscribed_results['generator_subscribe'])
        fun_test.simple_assert(expression=tx_port_result1, message=checkpoint)

        checkpoint = "Fetch Rx Port Results for %s" % rx_port
        rx_port_result1 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=rx_port_result1, message=checkpoint)

        checkpoint = "Fetch Tx Port Results for %s" % rx_port
        tx_port_result2 = template_obj.stc_manager.get_generator_port_results(
            port_handle=rx_port, subscribe_handle=subscribed_results['generator_subscribe'])
        fun_test.simple_assert(expression=tx_port_result2, message=checkpoint)

        checkpoint = "Fetch Rx Port Results for %s" % tx_port
        rx_port_result2 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=tx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=rx_port_result2, message=checkpoint)

        checkpoint = "Fetch Sample Port Results for %s" % sample_port
        sample_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=sample_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=sample_port_result, message=checkpoint)

        checkpoint = "Fetch Sample Port Results for %s" % port4
        sample_port_result1 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port4, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=sample_port_result1, message=checkpoint)

        fun_test.log("Spirent FPG%d Tx Port: %s" % (dut_rx_port, tx_port_result1))
        fun_test.log("Spirent FPG%d Rx Port: %s" % (dut_tx_port, rx_port_result1))
        fun_test.log("Spirent FPG%d Tx Port: %s" % (dut_tx_port, tx_port_result2))
        fun_test.log("Spirent FPG%d Rx Port: %s" % (dut_rx_port, rx_port_result2))
        fun_test.log("Sample Port: %s" % sample_port_result)
        fun_test.log("Sample Port: %s" % sample_port_result1)

        # Validate DUT stats
        dut_rx_port_results = network_controller_obj.peek_fpg_port_stats(dut_rx_port)
        fun_test.simple_assert(dut_rx_port_results, "Fetch DUT Rx port results. FPG%d" % dut_rx_port)

        dut_tx_port_results = network_controller_obj.peek_fpg_port_stats(dut_tx_port)
        fun_test.simple_assert(dut_tx_port_results, "Fetch DUT Tx port results. FPG%d" % dut_tx_port)

        dut_sample_port1_results = network_controller_obj.peek_fpg_port_stats(dut_sample_port1)
        fun_test.simple_assert(dut_sample_port1_results, "Fetch DUT sample port results. FPG%d" % dut_sample_port1)

        dut_sample_port2_results = network_controller_obj.peek_fpg_port_stats(dut_sample_port2)
        fun_test.simple_assert(dut_sample_port2_results, "Fetch DUT sample port results. FPG%d" % dut_sample_port2)

        psw_stats = network_controller_obj.peek_psw_global_stats()
        fun_test.simple_assert(psw_stats, "Fetch PSW global stats")

        sample_stats = network_controller_obj.show_sample_stats()
        fun_test.simple_assert(sample_stats, "Fetch Sample stats")

        fun_test.log("DUT Rx Port %d Results: %s" % (dut_rx_port, dut_rx_port_results))
        fun_test.log("DUT Tx Port %d Results: %s" % (dut_tx_port, dut_tx_port_results))
        fun_test.log("DUT Sample Port %d Results: %s" % (dut_sample_port1, dut_sample_port1_results))
        fun_test.log("DUT Sample Port %d Results: %s" % (dut_sample_port2, dut_sample_port2_results))
        fun_test.log("PSW stats: %s" % psw_stats)
        fun_test.log("Sample stats: %s" % sample_stats)

        checkpoint = "Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count " \
                     "(FPG%d --> FPG%d)" % (dut_rx_port, dut_tx_port)
        frames_received1 = get_dut_output_stats_value(result_stats=dut_rx_port_results, stat_type=FRAMES_RECEIVED_OK,
                                                      tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on FPG%d: %d" % (
            dut_rx_port, frames_received1, dut_tx_port, frames_transmitted))
        fun_test.test_assert_expected(expected=frames_received1, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count " \
                     "(FPG%d --> FPG%d)" % (dut_tx_port, dut_rx_port)
        frames_received2 = get_dut_output_stats_value(result_stats=dut_tx_port_results, stat_type=FRAMES_RECEIVED_OK,
                                                      tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_rx_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on FPG%d: %d" % (
            dut_tx_port, frames_received2, dut_rx_port, frames_transmitted))
        fun_test.test_assert_expected(expected=frames_received2, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Ensure Tx frame count must be equal to sample frame count port: FPG%d" % dut_sample_port1
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_sample_port1_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on Sample port FPG%d: %d" % (
            dut_rx_port, frames_received1, dut_sample_port1, frames_transmitted))
        fun_test.test_assert_expected(expected=frames_received1, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Ensure Tx frame count must be equal to sample frame count port: FPG%d" % dut_sample_port2
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_sample_port2_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on Sample port FPG%d: %d" % (
            dut_rx_port, frames_received2, dut_sample_port2, frames_transmitted))
        fun_test.test_assert_expected(expected=frames_received2, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Ensure PSW sample_pkt counter must be equal to no of frames transmitted"
        parsed_input_stats_1 = get_psw_global_stats_values(input=True, psw_stats_output=psw_stats_before,
                                                           input_key_list=[PSW_SAMPLED_PACKET_COUNT])

        parsed_input_stats_2 = get_psw_global_stats_values(input=True, psw_stats_output=psw_stats,
                                                           input_key_list=[PSW_SAMPLED_PACKET_COUNT])

        psw_diff_stats = get_diff_stats(old_stats=parsed_input_stats_1['input'],
                                        new_stats=parsed_input_stats_2['input'],
                                        stats_list=[PSW_SAMPLED_PACKET_COUNT])
        fun_test.test_assert_expected(expected=frames_received1, actual=int(psw_diff_stats['sampled_pkt']),
                                      message=checkpoint)

        checkpoint = "Ensure sample counter for a rule must be equal to Tx frames for sample ID: %d" % self.sample_id1
        sample_diff_stats = get_diff_stats(old_stats=sample_stats_before[str(self.sample_id1)],
                                           new_stats=sample_stats[str(self.sample_id1)])
        fun_test.test_assert_expected(expected=frames_received1,
                                      actual=int(sample_diff_stats['count']),
                                      message=checkpoint)

        checkpoint = "Ensure sample counter for a rule must be equal to Tx frames for sample ID: %d" % self.sample_id2
        sample_diff_stats = get_diff_stats(old_stats=sample_stats_before[str(self.sample_id2)],
                                           new_stats=sample_stats[str(self.sample_id2)])
        fun_test.test_assert_expected(expected=frames_received2,
                                      actual=int(sample_diff_stats['count']),
                                      message=checkpoint)

        # Validate Spirent stats
        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Rx spirent port FrameCount " \
                     "(FPG%d --> FPG%d)" % (dut_rx_port, dut_tx_port)
        fun_test.test_assert_expected(expected=int(tx_port_result1['GeneratorFrameCount']),
                                      actual=int(rx_port_result1['TotalFrameCount']), message=checkpoint)

        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Rx spirent port FrameCount " \
                     "(FPG%d --> FPG%d)" % (dut_tx_port, dut_rx_port)
        fun_test.test_assert_expected(expected=tx_port_result2['GeneratorFrameCount'],
                                      actual=rx_port_result2['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Sample spirent port FrameCount FPG%d" % \
                     dut_sample_port1
        fun_test.test_assert_expected(expected=tx_port_result1['GeneratorFrameCount'],
                                      actual=sample_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Sample spirent port FrameCount FPG%d" % \
                     dut_sample_port2
        fun_test.test_assert_expected(expected=tx_port_result2['GeneratorFrameCount'],
                                      actual=sample_port_result1['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure no errors are seen on Rx spirent port FPG%d" % dut_tx_port
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_result1)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure no errors are seen on Rx spirent port FPG%d" % dut_rx_port
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_result2)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure no errors are seen on Sample spirent port FPG%d" % dut_sample_port1
        result = template_obj.check_non_zero_error_count(rx_results=sample_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure no errors are seen on Sample spirent port FPG%d" % dut_sample_port2
        result = template_obj.check_non_zero_error_count(rx_results=sample_port_result1)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure all the fields in a packet is correct on sample port FPG%d" % dut_sample_port1
        parser_obj = PcapParser(filename=self.capture_results_port1['pcap_file_path'])
        packets = parser_obj.get_captures_from_file(display_filter="ip.addr == %s" % self.l3_config['destination_ip1'])
        result = parser_obj.validate_sample_packets_in_file(packets=packets, header_objs=self.header_objs1)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Ensure all the fields in a packet is correct on sample port FPG%d" % dut_sample_port2
        parser_obj = PcapParser(filename=self.capture_results_port2['pcap_file_path'])
        packets = parser_obj.get_captures_from_file(display_filter="ip.addr == %s" % self.l3_config['destination_ip2'])
        result = parser_obj.validate_sample_packets_in_file(packets=packets, header_objs=self.header_objs2)
        fun_test.test_assert(result, checkpoint)

    def cleanup(self):
        dut_rx_port = dut_config['ports'][0]
        dut_sample_port1 = dut_config['ports'][2]
        dut_sample_port2 = dut_config['ports'][3]

        checkpoint = "Delete sample rule for id: %d" % self.sample_id1
        network_controller_obj.disable_sample_rule(id=self.sample_id1, fpg=dut_rx_port, dest=dut_sample_port1)
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Delete sample rule for id: %d" % self.sample_id2
        network_controller_obj.disable_sample_rule(id=self.sample_id2, fpg=dut_rx_port, dest=dut_sample_port2)
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Delete the stream %s" % self.stream_obj1.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj1.spirent_handle])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Delete the stream %s" % self.stream_obj2.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj2.spirent_handle])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Delete tmp pcap file %s" % self.capture_results_port1['pcap_file_path']
        fun_test.remove_file(self.capture_results_port1['pcap_file_path'])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Delete tmp pcap file %s" % self.capture_results_port2['pcap_file_path']
        fun_test.remove_file(self.capture_results_port2['pcap_file_path'])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)


class SampleIngressEgressSamePacket(FunTestCase):
    l2_config = None
    l3_config = None
    load = 10
    load_type = StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND
    stream_obj = None
    sample_id1 = 60
    sample_id2 = 59
    header_objs = {'eth_obj': None, 'ip_obj': None, 'tcp_obj': None}
    capture_results_port1 = None
    capture_results_port2 = None

    def describe(self):
        self.set_test_details(id=8, summary="Test Sampling on Ingress and Egress on same packet",
                              steps="""
                              1. Create TCP frame stream on Tx Port with following settings
                                 a. Frame Size Mode: Random Min: 78 B and Max: 1500 B
                                 b. Payload Type: PRBS
                                 c. Insert Signature
                                 d. Load: 10 fps
                              2. Configure ingress sampling rule on FPG5 and dest: FPG15 
                              3. Configure egress sampling rule on FPG5 and dest: FPG18
                              4. Start Traffic for %d secs
                              5. Start packet capture sampling ports 
                              6. Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count
                              7. Ensure Tx frame count must be equal to sample frame count on both sampling ports
                              8. Ensure PSW sample_pkt counter must be equal to no of frames transmitted
                              9. Ensure sample counter for a rule must be equal to Tx frames  
                              10. Ensure on spirent Tx port frames must be equal to Rx port frames and sample port frames
                              11. Ensure no errors are seen on spirent ports
                              12. Ensure sample packets are exactly same as ingress packets 
                              """ % TRAFFIC_DURATION)

    def setup(self):
        self.l2_config = spirent_config['l2_config']
        self.l3_config = spirent_config['l3_config']['ipv4']

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

        ethernet_obj = Ethernet2Header(destination_mac=self.l2_config['destination_mac'],
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
        dut_sample_port1 = dut_config['ports'][2]
        dut_sample_port2 = dut_config['ports'][3]

        checkpoint = "Add Ingress Sampling rule Ingress Port: FPG%d and dest port: FPG%d" % (dut_rx_port,
                                                                                             dut_sample_port1)
        result = network_controller_obj.add_ingress_sample_rule(id=self.sample_id1,
                                                                fpg=dut_rx_port, dest=dut_sample_port1)
        fun_test.test_assert(result['status'], checkpoint)

        checkpoint = "Add Egress Sampling rule Ingress Port: FPG%d and dest port: FPG%d" % (dut_rx_port,
                                                                                            dut_sample_port2)
        result = network_controller_obj.add_egress_sample_rule(id=self.sample_id2,
                                                               fpg=dut_rx_port, dest=dut_sample_port2)
        fun_test.test_assert(result['status'], checkpoint)

    def run(self):
        dut_rx_port = dut_config['ports'][0]
        dut_tx_port = dut_config['ports'][1]
        dut_sample_port1 = dut_config['ports'][2]
        dut_sample_port2 = dut_config['ports'][3]

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
        self.capture_results_port1 = template_obj.start_default_capture_save_locally(port_handle=sample_port,
                                                                                     sleep_time=10)
        fun_test.test_assert(self.capture_results_port1['result'], checkpoint)

        checkpoint = "Packet captured on %s sample port" % port4
        self.capture_results_port2 = template_obj.start_default_capture_save_locally(port_handle=port4,
                                                                                     sleep_time=10)
        fun_test.test_assert(self.capture_results_port2['result'], checkpoint)

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

        checkpoint = "Fetch Sample Port Results for %s" % port4
        sample_port_result1 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port4, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=sample_port_result1, message=checkpoint)

        fun_test.log("Spirent FPG%d Tx Port: %s" % (dut_rx_port, tx_port_result))
        fun_test.log("Spirent FPG%d Rx Port: %s" % (dut_tx_port, rx_port_result))
        fun_test.log("Sample Port: %s" % sample_port_result)
        fun_test.log("Sample Port: %s" % sample_port_result1)

        # Validate DUT stats
        dut_rx_port_results = network_controller_obj.peek_fpg_port_stats(dut_rx_port)
        fun_test.simple_assert(dut_rx_port_results, "Fetch DUT Rx port results. FPG%d" % dut_rx_port)

        dut_tx_port_results = network_controller_obj.peek_fpg_port_stats(dut_tx_port)
        fun_test.simple_assert(dut_tx_port_results, "Fetch DUT Tx port results. FPG%d" % dut_tx_port)

        dut_sample_port1_results = network_controller_obj.peek_fpg_port_stats(dut_sample_port1)
        fun_test.simple_assert(dut_sample_port1_results, "Fetch DUT sample port results. FPG%d" % dut_sample_port1)

        dut_sample_port2_results = network_controller_obj.peek_fpg_port_stats(dut_sample_port2)
        fun_test.simple_assert(dut_sample_port2_results, "Fetch DUT sample port results. FPG%d" % dut_sample_port2)

        psw_stats = network_controller_obj.peek_psw_global_stats()
        fun_test.simple_assert(psw_stats, "Fetch PSW global stats")

        sample_stats = network_controller_obj.show_sample_stats()
        fun_test.simple_assert(sample_stats, "Fetch Sample stats")

        fun_test.log("DUT Rx Port %d Results: %s" % (dut_rx_port, dut_rx_port_results))
        fun_test.log("DUT Tx Port %d Results: %s" % (dut_tx_port, dut_tx_port_results))
        fun_test.log("DUT Sample Port %d Results: %s" % (dut_sample_port1, dut_sample_port1_results))
        fun_test.log("DUT Sample Port %d Results: %s" % (dut_sample_port2, dut_sample_port2_results))
        fun_test.log("PSW stats: %s" % psw_stats)
        fun_test.log("Sample stats: %s" % sample_stats)

        checkpoint = "Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count " \
                     "(FPG%d --> FPG%d)" % (dut_rx_port, dut_tx_port)
        frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_results, stat_type=FRAMES_RECEIVED_OK,
                                                     tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on FPG%d: %d" % (
            dut_rx_port, frames_received, dut_tx_port, frames_transmitted))
        fun_test.test_assert_expected(expected=frames_received, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Ensure Tx frame count must be equal to sample frame count port: FPG%d" % dut_sample_port1
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_sample_port1_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on Sample port FPG%d: %d" % (
            dut_rx_port, frames_received, dut_sample_port1, frames_transmitted))
        fun_test.test_assert_expected(expected=frames_received, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Ensure Tx frame count must be equal to sample frame count port: FPG%d" % dut_sample_port2
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_sample_port2_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on Sample port FPG%d: %d" % (
            dut_rx_port, frames_received, dut_sample_port2, frames_transmitted))
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

        checkpoint = "Ensure sample counter for a rule must be equal to Tx frames for sample ID: %d" % self.sample_id1
        sample_diff_stats = get_diff_stats(old_stats=sample_stats_before[str(self.sample_id1)],
                                           new_stats=sample_stats[str(self.sample_id1)])
        fun_test.test_assert_expected(expected=frames_received,
                                      actual=int(sample_diff_stats['count']),
                                      message=checkpoint)

        checkpoint = "Ensure sample counter for a rule must be equal to Tx frames for sample ID: %d" % self.sample_id2
        sample_diff_stats = get_diff_stats(old_stats=sample_stats_before[str(self.sample_id2)],
                                           new_stats=sample_stats[str(self.sample_id2)])
        fun_test.test_assert_expected(expected=frames_received,
                                      actual=int(sample_diff_stats['count']),
                                      message=checkpoint)

        # Validate Spirent stats
        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Rx spirent port FrameCount " \
                     "(FPG%d --> FPG%d)" % (dut_rx_port, dut_tx_port)
        fun_test.test_assert_expected(expected=tx_port_result['GeneratorFrameCount'],
                                      actual=rx_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Sample spirent port FrameCount FPG%d" % \
                     dut_sample_port1
        fun_test.test_assert_expected(expected=tx_port_result['GeneratorFrameCount'],
                                      actual=sample_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Sample spirent port FrameCount FPG%d" % \
                     dut_sample_port2
        fun_test.test_assert_expected(expected=tx_port_result['GeneratorFrameCount'],
                                      actual=sample_port_result1['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure no errors are seen on Rx spirent port FPG%d" % dut_tx_port
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure no errors are seen on Sample spirent port FPG%d" % dut_sample_port1
        result = template_obj.check_non_zero_error_count(rx_results=sample_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure no errors are seen on Sample spirent port FPG%d" % dut_sample_port2
        result = template_obj.check_non_zero_error_count(rx_results=sample_port_result1)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Ensure all the fields in a packet is correct on sample port FPG%d" % dut_sample_port1
        parser_obj = PcapParser(filename=self.capture_results_port1['pcap_file_path'])
        packets = parser_obj.get_captures_from_file()
        result = parser_obj.validate_sample_packets_in_file(packets=packets, header_objs=self.header_objs)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Ensure all the fields in a packet is correct on sample port FPG%d" % dut_sample_port2
        parser_obj = PcapParser(filename=self.capture_results_port2['pcap_file_path'])
        packets = parser_obj.get_captures_from_file()
        result = parser_obj.validate_sample_packets_in_file(packets=packets, header_objs=self.header_objs)
        fun_test.test_assert(result, checkpoint)

    def cleanup(self):
        dut_rx_port = dut_config['ports'][0]
        dut_sample_port1 = dut_config['ports'][2]
        dut_sample_port2 = dut_config['ports'][3]

        checkpoint = "Delete sample rule for id: %d" % self.sample_id1
        network_controller_obj.disable_sample_rule(id=self.sample_id1, fpg=dut_rx_port, dest=dut_sample_port1)
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Delete sample rule for id: %d" % self.sample_id2
        network_controller_obj.disable_sample_rule(id=self.sample_id2, fpg=dut_rx_port, dest=dut_sample_port2)
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Delete the stream %s" % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Delete tmp pcap file %s" % self.capture_results_port1['pcap_file_path']
        fun_test.remove_file(self.capture_results_port1['pcap_file_path'])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Delete tmp pcap file %s" % self.capture_results_port2['pcap_file_path']
        fun_test.remove_file(self.capture_results_port2['pcap_file_path'])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)


class SampleACLtoFPG(FunTestCase):
    """
    ACL Used here:
     {
            "acl_id" : "test_ingacl10",
            "label_id" : 2,
            "priority" : 10,
        "type" : "pacl_ingress",
            "is_routed" : "true",
            "ttl_err" : "false",
            "frag" : "false",
            "first_frag" : "true",
            "proto" : "any",
            "ecn" : "any",
            "ip_sa" : "any",
            "ip_da" : "any",
            "tcp_flags" : "any",
            "src_port" : "any",
            "dst_port" : "961",
            "ip_id" : "any",
            "range" : "any",
            "action" : "sample",
            "sample_id" : 62
        },
     Applied on FPG13 and FPG5

    """
    l2_config = None
    l3_config = None
    load = 10
    load_type = StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND
    stream_obj = None
    sample_id = 62  # This sample ID needs to be mentioned in nutest.json in ACL
    header_objs = {'eth_obj': None, 'ip_obj': None, 'tcp_obj': None}
    capture_results = None

    def describe(self):
        self.set_test_details(id=9, summary="Test Ingress Traffic Sampling ACL to FPG",
                              steps="""
                              1. Create TCP frame stream on Tx Port with following settings
                                 a. Frame Size Mode: Fixed 128 B
                                 b. Payload Type: PRBS
                                 c. Insert Signature
                                 d. Load: 10 fps
                                 e. TCP dest port 950
                              2. Configure ingress sampling rule with ID 61 and dest 15 without ingress FPG
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
                              12. Disable sample rule 
                              13. Start Traffic for %d secs
                              14. Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count
                              15. Ensure sample counter must be 0
                              """ % (TRAFFIC_DURATION, TRAFFIC_DURATION))

    def setup(self):
        self.l2_config = spirent_config['l2_config']
        self.l3_config = spirent_config['l3_config']['ipv4']

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

        ethernet_obj = Ethernet2Header(destination_mac=self.l2_config['destination_mac'],
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
        tcp_header_obj = TCP(destination_port=961)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=tcp_header_obj, update=False)
        fun_test.simple_assert(result, checkpoint)

        self.header_objs['eth_obj'] = ethernet_obj
        self.header_objs['ip_obj'] = ip_header_obj
        self.header_objs['tcp_obj'] = tcp_header_obj

        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Add Ingress Sampling rule and dest port: FPG%d" % dut_sample_port
        result = network_controller_obj.add_ingress_sample_rule(id=self.sample_id, dest=dut_sample_port)
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

        checkpoint = "Disable sample rule ID %d" % self.sample_id
        result = network_controller_obj.disable_sample_rule(id=self.sample_id, dest=dut_sample_port)
        fun_test.test_assert(result['status'], checkpoint)

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

        fun_test.sleep("Traffic to complete", seconds=40)

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

        checkpoint = "Ensure sample frame count must be None"
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_sample_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Sample Frames Transmitted on Sample port FPG%d: %s" % (dut_sample_port, frames_transmitted))
        fun_test.test_assert_expected(expected=None, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Ensure sample counter must be 0"
        sample_diff_stats = get_diff_stats(old_stats=sample_stats_before[str(self.sample_id)],
                                           new_stats=sample_stats[str(self.sample_id)])
        fun_test.test_assert_expected(expected=0,
                                      actual=int(sample_diff_stats['count']),
                                      message=checkpoint)

    def cleanup(self):
        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Delete sample rule for id: %d" % self.sample_id
        network_controller_obj.disable_sample_rule(id=self.sample_id, dest=dut_sample_port)
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


class SampleIngressARPRequest(FunTestCase):
    l2_config = None
    l3_config = None
    load = 10
    load_type = StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND
    stream_obj = None
    sample_id = 49

    def describe(self):
        self.set_test_details(id=10, summary="Test Ingress Sample ARP Request",
                              steps="""
                              1. Create ARP frame stream on Tx Port with following settings
                                 a. Frame Size Mode: Fixed 128 B
                                 b. Payload Type: PRBS
                                 c. Insert Signature
                                 d. Load: 10 fps
                              2. Configure ingress sampling rule on FPG5 and dest: FPG15
                              3. Start Traffic for %d secs
                              4. Validate that packets are getting punted to CC. Ensure packets received on ingress FPG 
                                 port is equal to packets seen on CC FPG port
                              5. Ensure Tx frame count must be equal to sample frame count
                              6. Ensure PSW sample_pkt counter must be equal to no of frames transmitted
                              7. Ensure sample counter for a rule must be equal to Tx frames
                              8. Ensure IN_FFE_DESC equal to OUT_FFE_DESC in sfg nu stats
                              9. Ensure CNTR_SAMPLERID and SAMPLER_COPY count is equal to no of frames transmitted on 
                                  sample port   
                              10. Ensure on spirent Tx port frames must be equal to Rx port frames and sample port 
                                  frames
                              11. Ensure no errors are seen on spirent ports
                              """ % TRAFFIC_DURATION)

    def setup(self):
        self.l2_config = spirent_config['l2_config']
        self.l3_config = spirent_config['l3_config']['ipv4']

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

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.BROADCAST_MAC,
                                    ether_type=Ethernet2Header.ARP_ETHERTYPE)
        arp_obj = ARP()

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=arp_obj, update=False,
                                                                delete_header=[Ipv4Header.HEADER_TYPE])
        fun_test.test_assert(result, checkpoint)

        dut_rx_port = dut_config['ports'][0]
        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Add Ingress Sampling rule Ingress Port: FPG%d and dest port: FPG%d" % (dut_rx_port,
                                                                                             dut_sample_port)
        result = network_controller_obj.add_ingress_sample_rule(id=self.sample_id,
                                                                fpg=dut_rx_port, dest=dut_sample_port)
        fun_test.test_assert(result['status'], checkpoint)

    def run(self):
        dut_rx_port = dut_config['ports'][0]
        dut_sample_port = dut_config['ports'][2]
        dut_cc_port = dut_config['ports'][4]

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

        checkpoint = "Get SFG NU stats before traffic"
        sfg_stats_before = network_controller_obj.peek_sfg_stats()
        fun_test.test_assert(sfg_stats_before, checkpoint)

        checkpoint = "Start traffic from %s port for %d secs" % (tx_port, TRAFFIC_DURATION)
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)

        fun_test.sleep("Traffic to complete", seconds=40)

        # Getting Spirent results
        checkpoint = "Fetch Tx Port Results for %s" % tx_port
        tx_port_result = template_obj.stc_manager.get_generator_port_results(
            port_handle=tx_port, subscribe_handle=subscribed_results['generator_subscribe'])
        fun_test.simple_assert(expression=tx_port_result, message=checkpoint)

        checkpoint = "Fetch CC Port Results for %s" % cc_port
        cc_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=cc_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=cc_port_result, message=checkpoint)

        checkpoint = "Fetch Sample Port Results for %s" % sample_port
        sample_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=sample_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=sample_port_result, message=checkpoint)

        fun_test.log("Tx Port: %s" % tx_port_result)
        fun_test.log("CC Port: %s" % cc_port_result)
        fun_test.log("Sample Port: %s" % sample_port_result)

        # Validate DUT stats
        dut_rx_port_results = network_controller_obj.peek_fpg_port_stats(dut_rx_port)
        fun_test.simple_assert(dut_rx_port_results, "Fetch DUT Rx port results. FPG%d" % dut_rx_port)

        dut_cc_port_results = network_controller_obj.peek_fpg_port_stats(dut_cc_port)
        fun_test.simple_assert(dut_cc_port_results, "Fetch DUT CC port results. FPG%d" % dut_cc_port)

        dut_sample_port_results = network_controller_obj.peek_fpg_port_stats(dut_sample_port)
        fun_test.simple_assert(dut_sample_port_results, "Fetch DUT sample port results. FPG%d" % dut_sample_port)

        psw_stats = network_controller_obj.peek_psw_global_stats()
        fun_test.simple_assert(psw_stats, "Fetch PSW global stats")

        sample_stats = network_controller_obj.show_sample_stats()
        fun_test.simple_assert(sample_stats, "Fetch Sample stats")

        sfg_stats = network_controller_obj.peek_sfg_stats()
        fun_test.simple_assert(sfg_stats, "Fetch SFG stats")

        fun_test.log("DUT Rx Port %d Results: %s" % (dut_rx_port, dut_rx_port_results))
        fun_test.log("DUT CC Port %d Results: %s" % (dut_cc_port, dut_cc_port_results))
        fun_test.log("DUT Sample Port %d Results: %s" % (dut_sample_port, dut_sample_port_results))
        fun_test.log("PSW stats: %s" % psw_stats)
        fun_test.log("Sample stats: %s" % sample_stats)
        fun_test.log("Sfg stats: %s" % sfg_stats)

        checkpoint = "Validate that packets are getting punted to CC. Ensure packets received on ingress FPG " \
                     "port is equal to packets seen on CC FPG port"
        frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_results, stat_type=FRAMES_RECEIVED_OK,
                                                     tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_cc_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on CC FPG%d: %d" % (
            dut_rx_port, frames_received, dut_cc_port, frames_transmitted))
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

        checkpoint = "Ensure IN_FFE_DESC equal to OUT_PSW_DESC in sfg nu stats"
        sfg_diff_stats = get_diff_stats(old_stats=sfg_stats_before, new_stats=sfg_stats)
        fun_test.test_assert_expected(expected=sfg_diff_stats[SFG_IN_FFE_DESC], actual=sfg_diff_stats[SFG_OUT_PSW_DESC],
                                      message=checkpoint)

        checkpoint = "Ensure CNTR_SAMPLER%d count is equal to no of frames transmitted on sample port %d" % (
            self.sample_id, dut_sample_port)
        fun_test.test_assert_expected(expected=frames_transmitted,
                                      actual=sfg_diff_stats['CNTR_SAMPLER%d' % self.sample_id], message=checkpoint)

        # Validate Spirent stats
        if int(tx_port_result['GeneratorFrameCount']) == int(cc_port_result['TotalFrameCount']):
            checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Rx spirent port FrameCount"
            fun_test.test_assert_expected(expected=tx_port_result['GeneratorFrameCount'],
                                          actual=cc_port_result['TotalFrameCount'], message=checkpoint)
        if int(tx_port_result['GeneratorFrameCount']) == int(sample_port_result['TotalFrameCount']):
            checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Sample spirent port FrameCount"
            fun_test.test_assert_expected(expected=tx_port_result['GeneratorFrameCount'],
                                          actual=sample_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure no errors are seen on Rx spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=cc_port_result)
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

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)


class SampleIngressLLDP(SampleIngressARPRequest):

    def describe(self):
        self.set_test_details(id=11, summary="Test Ingress Sample LLDP (Link Layer Discovery Protocol)",
                              steps="""
                              1. Create LLDP frame stream on Tx Port with following settings
                                 a. Frame Size Mode: Fixed 128 B
                                 b. Payload Type: PRBS
                                 c. Insert Signature
                                 d. Load: 10 fps
                              2. Configure ingress sampling rule on FPG5 and dest: FPG15
                              3. Start Traffic for %d secs
                              4. Validate that packets are getting punted to CC. Ensure packets received on ingress FPG 
                                 port is equal to packets seen on CC FPG port
                              5. Ensure Tx frame count must be equal to sample frame count
                              6. Ensure PSW sample_pkt counter must be equal to no of frames transmitted
                              7. Ensure sample counter for a rule must be equal to Tx frames
                              8. Ensure IN_FFE_DESC equal to OUT_FFE_DESC in sfg nu stats
                              9. Ensure CNTR_SAMPLERID and SAMPLER_COPY count is equal to no of frames transmitted on 
                                  sample port   
                              10. Ensure on spirent Tx port frames must be equal to Rx port frames and sample port 
                                  frames
                              11. Ensure no errors are seen on spirent ports
                              """ % TRAFFIC_DURATION)

    def setup(self):
        self.l2_config = spirent_config['l2_config']
        self.l3_config = spirent_config['l3_config']['ipv4']

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

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.LLDP_MULTICAST_MAC,
                                    ether_type=Ethernet2Header.LLDP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        result = template_obj.stc_manager.delete_frame_headers(stream_block_handle=self.stream_obj.spirent_handle,
                                                               header_types=[Ipv4Header.HEADER_TYPE])
        fun_test.test_assert(result, checkpoint)

        dut_rx_port = dut_config['ports'][0]
        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Add Ingress Sampling rule Ingress Port: FPG%d and dest port: FPG%d" % (dut_rx_port,
                                                                                             dut_sample_port)
        result = network_controller_obj.add_ingress_sample_rule(id=self.sample_id,
                                                                fpg=dut_rx_port, dest=dut_sample_port)
        fun_test.test_assert(result['status'], checkpoint)


class SampleIngressDropIPv4VerError(FunTestCase):
    l2_config = None
    l3_config = None
    load = 10
    load_type = StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND
    stream_obj = None
    sample_id = 49
    header_objs = {'eth_obj': None, 'ip_obj': None}
    capture_results = None

    def describe(self):
        self.set_test_details(id=12, summary="Test Ingress Sample Drop IPv4 Version SW Error",
                              steps="""
                              1. Create IPv4 frame stream on Tx Port with following settings
                                 a. Frame Size Mode: Fixed 128 B
                                 b. Payload Type: PRBS
                                 c. Insert Signature
                                 d. Load: 10 fps
                                 e. IPv4 Version = 0
                              2. Configure ingress sampling rule on FPG5 and dest: FPG15
                              3. Start Traffic for %d secs
                              4. Capture packets on sample port
                              4. Validate that packets are getting punted to CC. Ensure packets received on ingress FPG 
                                 port is equal to packets seen on CC FPG port
                              5. Ensure Tx frame count must be equal to sample frame count
                              6. Ensure PSW sample_pkt counter must be equal to no of frames transmitted
                              7. Ensure sample counter for a rule must be equal to Tx frames
                              8. Ensure on spirent Tx port frames must be equal to Rx port frames and sample port 
                                  frames
                              9. Ensure no errors are seen on spirent ports
                              10. Ensure sample packet is exactly same as ingress packet
                              """ % TRAFFIC_DURATION)

    def setup(self):
        self.l2_config = spirent_config['l2_config']
        self.l3_config = spirent_config['l3_config']['ipv4']

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

        ether_obj = Ethernet2Header(destination_mac=self.l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=self.l3_config['destination_ip1'], version=0)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)

        self.header_objs['ether_obj'] = ether_obj
        self.header_objs['ip_obj'] = ipv4_header_obj

        dut_rx_port = dut_config['ports'][0]
        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Add Ingress Sampling rule Ingress Port: FPG%d and dest port: FPG%d" % (dut_rx_port,
                                                                                             dut_sample_port)
        result = network_controller_obj.add_ingress_sample_rule(id=self.sample_id,
                                                                fpg=dut_rx_port, dest=dut_sample_port)
        fun_test.test_assert(result['status'], checkpoint)

    def run(self):
        dut_rx_port = dut_config['ports'][0]
        dut_sample_port = dut_config['ports'][2]
        dut_cc_port = dut_config['ports'][4]

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

        checkpoint = "Get SFG NU stats before traffic"
        sfg_stats_before = network_controller_obj.peek_sfg_stats()
        fun_test.test_assert(sfg_stats_before, checkpoint)

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

        checkpoint = "Fetch CC Port Results for %s" % cc_port
        cc_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=cc_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=cc_port_result, message=checkpoint)

        checkpoint = "Fetch Sample Port Results for %s" % sample_port
        sample_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=sample_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=sample_port_result, message=checkpoint)

        fun_test.log("Tx Port: %s" % tx_port_result)
        fun_test.log("CC Port: %s" % cc_port_result)
        fun_test.log("Sample Port: %s" % sample_port_result)

        # Validate DUT stats
        dut_rx_port_results = network_controller_obj.peek_fpg_port_stats(dut_rx_port)
        fun_test.simple_assert(dut_rx_port_results, "Fetch DUT Rx port results. FPG%d" % dut_rx_port)

        dut_cc_port_results = network_controller_obj.peek_fpg_port_stats(dut_cc_port)
        fun_test.simple_assert(dut_cc_port_results, "Fetch DUT CC port results. FPG%d" % dut_cc_port)

        dut_sample_port_results = network_controller_obj.peek_fpg_port_stats(dut_sample_port)
        fun_test.simple_assert(dut_sample_port_results, "Fetch DUT sample port results. FPG%d" % dut_sample_port)

        psw_stats = network_controller_obj.peek_psw_global_stats()
        fun_test.simple_assert(psw_stats, "Fetch PSW global stats")

        sample_stats = network_controller_obj.show_sample_stats()
        fun_test.simple_assert(sample_stats, "Fetch Sample stats")

        sfg_stats = network_controller_obj.peek_sfg_stats()
        fun_test.simple_assert(sfg_stats, "Fetch SFG stats")

        fun_test.log("DUT Rx Port %d Results: %s" % (dut_rx_port, dut_rx_port_results))
        fun_test.log("DUT CC Port %d Results: %s" % (dut_cc_port, dut_cc_port_results))
        fun_test.log("DUT Sample Port %d Results: %s" % (dut_sample_port, dut_sample_port_results))
        fun_test.log("PSW stats: %s" % psw_stats)
        fun_test.log("Sample stats: %s" % sample_stats)
        fun_test.log("Sfg stats: %s" % sfg_stats)

        checkpoint = "Validate that packets are getting punted to CC. Ensure packets received on ingress FPG " \
                     "port is equal to packets seen on CC FPG port"
        frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_results, stat_type=FRAMES_RECEIVED_OK,
                                                     tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_cc_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on CC FPG%d: %d" % (
            dut_rx_port, frames_received, dut_cc_port, frames_transmitted))
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
                                      actual=cc_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Sample spirent port FrameCount"
        fun_test.test_assert_expected(expected=tx_port_result['GeneratorFrameCount'],
                                      actual=sample_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure no errors are seen on Rx spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=cc_port_result)
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


class SampleIngressDropFwdErrorWrongDIP(FunTestCase):
    l2_config = None
    l3_config = None
    load = 10
    load_type = StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND
    stream_obj = None
    sample_id = 49
    header_objs = {'eth_obj': None, 'ip_obj': None}

    def describe(self):
        self.set_test_details(id=13, summary="Test Ingress Sample Drop FWD Error Wrong DIP",
                              steps="""
                              1. Create IPv4 frame stream on Tx Port with following settings
                                 a. Frame Size Mode: Fixed 128 B
                                 b. Payload Type: PRBS
                                 c. Insert Signature
                                 d. Load: 10 fps
                                 e. IPv4 Version = 0
                              2. Configure ingress sampling rule on FPG5 and dest: FPG15
                              3. Start Traffic for %d secs
                              4. Capture packets on sample port
                              5. Validate that packets are getting dropped
                              6. Ensure Tx frame count must be equal to sample frame count
                              7. Validate that packets are getting dropped due to frv_error
                              8. Ensure sample counter for a rule must be equal to Tx frames
                              9. Validate that packets are getting dropped on spirent
                              10. Ensure no errors are seen on spirent ports
                              11. Ensure sample packet is exactly same as ingress packet
                              """ % TRAFFIC_DURATION)

    def setup(self):
        self.l2_config = spirent_config['l2_config']
        self.l3_config = spirent_config['l3_config']['ipv4']

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

        ether_obj = Ethernet2Header(destination_mac=self.l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)

        self.header_objs['ether_obj'] = ether_obj
        self.header_objs['ip_obj'] = ipv4_header_obj

        dut_rx_port = dut_config['ports'][0]
        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Add Ingress Sampling rule Ingress Port: FPG%d and dest port: FPG%d" % (dut_rx_port,
                                                                                             dut_sample_port)
        result = network_controller_obj.add_ingress_sample_rule(id=self.sample_id,
                                                                fpg=dut_rx_port, dest=dut_sample_port)
        fun_test.test_assert(result['status'], checkpoint)

    def run(self):
        dut_rx_port = dut_config['ports'][0]
        dut_sample_port = dut_config['ports'][2]
        dut_tx_port = dut_config['ports'][1]

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

        checkpoint = "Get SFG NU stats before traffic"
        sfg_stats_before = network_controller_obj.peek_sfg_stats()
        fun_test.test_assert(sfg_stats_before, checkpoint)

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

        sfg_stats = network_controller_obj.peek_sfg_stats()
        fun_test.simple_assert(sfg_stats, "Fetch SFG stats")

        fun_test.log("DUT Rx Port %d Results: %s" % (dut_rx_port, dut_rx_port_results))
        fun_test.log("DUT Tx Port %d Results: %s" % (dut_tx_port, dut_tx_port_results))
        fun_test.log("DUT Sample Port %d Results: %s" % (dut_sample_port, dut_sample_port_results))
        fun_test.log("PSW stats: %s" % psw_stats)
        fun_test.log("Sample stats: %s" % sample_stats)
        fun_test.log("Sfg stats: %s" % sfg_stats)

        checkpoint = "Validate that packets are getting dropped"
        frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_results, stat_type=FRAMES_RECEIVED_OK,
                                                     tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on Rx FPG%d: %s" % (
            dut_rx_port, frames_received, dut_tx_port, frames_transmitted))
        fun_test.test_assert_expected(expected=None, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Validate that packets are getting dropped due frv_error"
        parsed_input_stats_1 = get_psw_global_stats_values(input=True, psw_stats_output=psw_stats_before,
                                                           input_key_list=[PSW_FRV_ERROR_COUNT])

        parsed_input_stats_2 = get_psw_global_stats_values(input=True, psw_stats_output=psw_stats,
                                                           input_key_list=[PSW_FRV_ERROR_COUNT])

        psw_diff_stats = get_diff_stats(old_stats=parsed_input_stats_1['input'],
                                        new_stats=parsed_input_stats_2['input'],
                                        stats_list=[PSW_FRV_ERROR_COUNT])
        fun_test.test_assert_expected(expected=frames_received, actual=int(psw_diff_stats['frv_error']),
                                      message=checkpoint)

        checkpoint = "Ensure Tx frame count must be equal to sample frame count"
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_sample_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on Sample port FPG%d: %s" % (
            dut_rx_port, frames_received, dut_sample_port, frames_transmitted))
        fun_test.test_assert_expected(expected=None, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Ensure sample counter for a rule must be equal to Tx frames"
        sample_diff_stats = get_diff_stats(old_stats=sample_stats_before[str(self.sample_id)],
                                           new_stats=sample_stats[str(self.sample_id)])
        fun_test.test_assert_expected(expected=frames_received,
                                      actual=int(sample_diff_stats['count']),
                                      message=checkpoint)

        # Validate Spirent stats
        checkpoint = "Ensure Packets are getting dropped on spirent Rx port %s" % rx_port
        fun_test.test_assert_expected(expected=0,
                                      actual=rx_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure Packets are getting dropped on spirent Sample port %s" % sample_port
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

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)


class SampleEgressMTUCase(FunTestCase):
    l2_config = None
    l3_config = None
    load = 5
    load_type = StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND
    stream_obj = None
    sample_id = 49
    header_objs = {'eth_obj': None, 'ip_obj': None, 'tcp_obj': None}
    capture_results = None

    def describe(self):
        self.set_test_details(id=14, summary="Test Egress Sample MTU case (egress/sample interface MTU < frame size)",
                              steps="""
                              1. Create TCP frame stream on Tx Port with following settings
                                 a. Frame Size Mode: Fixed 1000 B
                                 b. Payload Type: PRBS
                                 c. Insert Signature
                                 d. Load: 10 fps
                              2. Configure MTU on egress interface to 300B and ingress interface to 1500B
                              3. Configure egress sampling rule on FPG5 and dest: FPG15
                              4. Start Traffic for %d secs
                              5. Capture packets on sample port
                              6. Validate that packets are getting dropped at egress interface
                              7. Ensure packets are getting sampled in PSW block and being transmitted by sample port
                              8. Ensure that sampled packet is exactly same as ingress packet
                              9. Validate that packets are getting dropped on spirent at Rx port
                              10. Ensure packets are getting received on sample spirent port
                              11. Ensure no errors are seen on spirent ports
                              12. Configure MTU on egress interface to 1500 and sample interface to 300
                              13. Start Traffic for %d secs
                              14. Validate that ingress packets count must be equal to egress packets count
                              15. Ensure packets are getting sampled in PSW block and not being transmitted by sample 
                                  port. Sampling is done by PSW block so that is working but for packet to go out 
                                  its size has to be less than interface MTU which is not the case here and so 
                                  its dropped
                              16. Validate that packets are received Rx spirent port    
                              17. Ensure that no packets are received on sample spirent port
                              18. Ensure no errors are seen on spirent ports  
                              """ % (TRAFFIC_DURATION, TRAFFIC_DURATION))

    def setup(self):
        self.l2_config = spirent_config['l2_config']
        self.l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create stream on %s port" % tx_port
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_PRBS,
                                      insert_signature=True,
                                      load=self.load,
                                      load_unit=self.load_type,
                                      frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_FIXED,
                                      fixed_frame_length=1000)
        stream_created = template_obj.configure_stream_block(stream_block_obj=self.stream_obj,
                                                             port_handle=tx_port)
        fun_test.test_assert(stream_created, checkpoint)

        ether_obj = Ethernet2Header(destination_mac=self.l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=self.l3_config['destination_ip1'],
                                     protocol=Ipv4Header.PROTOCOL_TYPE_TCP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, checkpoint)

        checkpoint = "Add TCP Header"
        tcp_obj = TCP()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=tcp_obj, update=False)
        fun_test.simple_assert(result, checkpoint)

        ipv4_header_obj.ttl = 254

        self.header_objs['ether_obj'] = ether_obj
        self.header_objs['ip_obj'] = ipv4_header_obj
        self.header_objs['tcp_obj'] = tcp_obj

        dut_rx_port = dut_config['ports'][0]
        dut_tx_port = dut_config['ports'][1]
        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Configure MTU on egress interface FPG%d to 300 and ingress interface FPG%d to 1500 and " \
                     "sample interface FPG%d to 1500" % (dut_tx_port, dut_rx_port, dut_sample_port)
        mtu_changed = network_controller_obj.set_port_mtu(port_num=dut_tx_port, mtu_value=300, shape=0)
        fun_test.simple_assert(mtu_changed, "Change MTU on DUT port %d to 300" % dut_tx_port)
        mtu_changed = network_controller_obj.set_port_mtu(port_num=dut_rx_port, mtu_value=1500, shape=0)
        fun_test.simple_assert(mtu_changed, "Change MTU on DUT port %d to 1500" % dut_rx_port)
        mtu_changed = network_controller_obj.set_port_mtu(port_num=dut_sample_port, mtu_value=1500, shape=0)
        fun_test.test_assert(mtu_changed, checkpoint)

        checkpoint = "Add egress Sampling rule Ingress Port: FPG%d and dest port: FPG%d" % (dut_rx_port,
                                                                                            dut_sample_port)
        result = network_controller_obj.add_egress_sample_rule(id=self.sample_id,
                                                               fpg=dut_rx_port, dest=dut_sample_port)
        fun_test.test_assert(result['status'], checkpoint)

    def run(self):
        dut_rx_port = dut_config['ports'][0]
        dut_sample_port = dut_config['ports'][2]
        dut_tx_port = dut_config['ports'][1]

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

        fun_test.log("Spirent Tx Port: %s" % tx_port_result)
        fun_test.log("Spirent Rx Port: %s" % rx_port_result)
        fun_test.log("Spirent Sample Port: %s" % sample_port_result)

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

        checkpoint = "Validate that packets are getting dropped at egress interface FPG%d" % dut_tx_port
        frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_results, stat_type=FRAMES_RECEIVED_OK,
                                                     tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on Rx FPG%d: %s" % (
            dut_rx_port, frames_received, dut_tx_port, frames_transmitted))
        fun_test.test_assert_expected(expected=None, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Ensure packets are getting sampled in PSW block"
        parsed_input_stats_1 = get_psw_global_stats_values(input=True, psw_stats_output=psw_stats_before,
                                                           input_key_list=[PSW_SAMPLED_PACKET_COUNT])

        parsed_input_stats_2 = get_psw_global_stats_values(input=True, psw_stats_output=psw_stats,
                                                           input_key_list=[PSW_SAMPLED_PACKET_COUNT])

        psw_diff_stats = get_diff_stats(old_stats=parsed_input_stats_1['input'],
                                        new_stats=parsed_input_stats_2['input'],
                                        stats_list=[PSW_SAMPLED_PACKET_COUNT])
        fun_test.test_assert_expected(expected=frames_received, actual=int(psw_diff_stats['sampled_pkt']),
                                      message=checkpoint)

        checkpoint = "Ensure sample frames are being transmitted by sample port FPG%d" % dut_sample_port
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_sample_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on Sample port FPG%d: %s" % (
            dut_rx_port, frames_received, dut_sample_port, frames_transmitted))
        fun_test.test_assert_expected(expected=frames_received, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Ensure sample counter for a rule must be equal to Tx frames"
        sample_diff_stats = get_diff_stats(old_stats=sample_stats_before[str(self.sample_id)],
                                           new_stats=sample_stats[str(self.sample_id)])
        fun_test.test_assert_expected(expected=frames_received,
                                      actual=int(sample_diff_stats['count']),
                                      message=checkpoint)
        # Validate Spirent stats
        checkpoint = "Ensure Packets are getting dropped on spirent Rx port %s" % rx_port
        fun_test.test_assert_expected(expected=0,
                                      actual=rx_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure packets are getting received on sample spirent port %s" % sample_port
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
        result = parser_obj.validate_sample_packets_in_file(packets=packets, header_objs=self.header_objs,
                                                            expected_packet_length=1000)
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

        checkpoint = "Configure MTU on egress interface FPG%d to 1500 and sample interface FPG%d to 300" % (
            dut_tx_port, dut_sample_port)
        mtu_changed = network_controller_obj.set_port_mtu(port_num=dut_tx_port, mtu_value=1500, shape=0)
        fun_test.simple_assert(mtu_changed, "Change MTU on DUT port %d to 1500" % dut_tx_port)
        mtu_changed = network_controller_obj.set_port_mtu(port_num=dut_sample_port, mtu_value=300, shape=0)
        fun_test.test_assert(mtu_changed, checkpoint)

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

        fun_test.log("Spirent Tx Port: %s" % tx_port_result)
        fun_test.log("Spirent Rx Port: %s" % rx_port_result)
        fun_test.log("Spirent Sample Port: %s" % sample_port_result)

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

        checkpoint = "Validate that ingress packets count must be equal to egress packets count (FPG%d --> FPG%d)" % (
            dut_rx_port, dut_tx_port)
        frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_results, stat_type=FRAMES_RECEIVED_OK,
                                                     tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on Rx FPG%d: %s" % (
            dut_rx_port, frames_received, dut_tx_port, frames_transmitted))
        fun_test.test_assert_expected(expected=frames_received, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Ensure packets are getting sampled in PSW block"
        parsed_input_stats_1 = get_psw_global_stats_values(input=True, psw_stats_output=psw_stats_before,
                                                           input_key_list=[PSW_SAMPLED_PACKET_COUNT])

        parsed_input_stats_2 = get_psw_global_stats_values(input=True, psw_stats_output=psw_stats,
                                                           input_key_list=[PSW_SAMPLED_PACKET_COUNT])

        psw_diff_stats = get_diff_stats(old_stats=parsed_input_stats_1['input'],
                                        new_stats=parsed_input_stats_2['input'],
                                        stats_list=[PSW_SAMPLED_PACKET_COUNT])
        fun_test.test_assert_expected(expected=frames_received, actual=int(psw_diff_stats['sampled_pkt']),
                                      message=checkpoint)

        checkpoint = "Sampling is done by PSW block so that is working but for packet to go out its size has to be " \
                     "less than interface MTU which is not the case here and so its dropped. sample port FPG%d" % \
                     dut_sample_port
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_sample_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on Sample port FPG%d: %s" % (
            dut_rx_port, frames_received, dut_sample_port, frames_transmitted))
        fun_test.test_assert_expected(expected=None, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Ensure sample counter for a rule must be equal to Tx frames"
        sample_diff_stats = get_diff_stats(old_stats=sample_stats_before[str(self.sample_id)],
                                           new_stats=sample_stats[str(self.sample_id)])
        fun_test.test_assert_expected(expected=frames_received,
                                      actual=int(sample_diff_stats['count']),
                                      message=checkpoint)
        # Validate Spirent stats
        checkpoint = "Validate that packets are received Rx spirent port %s" % rx_port
        fun_test.test_assert_expected(expected=tx_port_result['GeneratorFrameCount'],
                                      actual=rx_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure packets are getting received on sample spirent port %s" % sample_port
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

        checkpoint = "Change DUT ports MTU to 1500"
        for port_num in dut_config['ports']:
            if port_num == 1 or port_num == 2:
                shape = 1
            else:
                shape = 0
            network_controller_obj.set_port_mtu(port_num=port_num, mtu_value=1500, shape=shape)
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


class SampleEgressDropACL(FunTestCase):
    l2_config = None
    l3_config = None
    load = 10
    load_type = StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND
    stream_obj = None
    sample_id = 62
    header_objs = {'eth_obj': None, 'ip_obj': None, 'tcp_obj': None}
    captured_results = None

    def describe(self):
        self.set_test_details(id=15, summary="Test Egress Sample Drop using ACL",
                              steps="""
                              1. Create TCP frame stream on Tx Port with following settings
                                 a. Frame Size Mode: Fixed 128 B
                                 b. Payload Type: PRBS
                                 c. Insert Signature
                                 d. Load: 10 fps
                                 e. TCP dest port 960
                              2. Configure egress sampling rule on FPG5 and dest: FPG15
                              3. Start Traffic for %d secs
                              4. Capture packets on sample port
                              5. Validate that packets are getting dropped at egress interface due to ACL configured
                              6. Ensure packets are getting sampled in PSW block and being transmitted by sample port
                              7. Ensure that sampled packet is exactly same as ingress packet
                              8. Validate that packets are getting dropped on spirent at Rx port due to ACL configured
                              9. Ensure packets are getting received on sample spirent port
                              10. Ensure no errors are seen on spirent ports
                              """ % TRAFFIC_DURATION)

    def setup(self):
        self.l2_config = spirent_config['l2_config']
        self.l3_config = spirent_config['l3_config']['ipv4']

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

        ether_obj = Ethernet2Header(destination_mac=self.l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=self.l3_config['destination_ip1'],
                                     protocol=Ipv4Header.PROTOCOL_TYPE_TCP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, checkpoint)

        checkpoint = "Add TCP Header"
        tcp_obj = TCP(destination_port=960)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=tcp_obj, update=False)
        fun_test.simple_assert(result, checkpoint)

        ipv4_header_obj.ttl = 254
        self.header_objs['ether_obj'] = ether_obj
        self.header_objs['ip_obj'] = ipv4_header_obj
        self.header_objs['tcp_obj'] = tcp_obj

        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Add egress Sampling rule dest port: FPG%d" % dut_sample_port
        result = network_controller_obj.add_egress_sample_rule(id=self.sample_id, dest=dut_sample_port)
        fun_test.test_assert(result['status'], checkpoint)

    def run(self):
        dut_rx_port = dut_config['ports'][0]
        dut_sample_port = dut_config['ports'][2]
        dut_tx_port = dut_config['ports'][1]

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

        fun_test.log("Spirent Tx Port: %s" % tx_port_result)
        fun_test.log("Spirent Rx Port: %s" % rx_port_result)
        fun_test.log("Spirent Sample Port: %s" % sample_port_result)

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

        checkpoint = "Validate that packets are getting dropped at egress interface FPG%d due to ACL configured" % \
                     dut_tx_port
        frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_results, stat_type=FRAMES_RECEIVED_OK,
                                                     tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on Rx FPG%d: %s" % (
            dut_rx_port, frames_received, dut_tx_port, frames_transmitted))
        fun_test.test_assert_expected(expected=None, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Ensure packets are getting sampled in PSW block"
        parsed_input_stats_1 = get_psw_global_stats_values(input=True, psw_stats_output=psw_stats_before,
                                                           input_key_list=[PSW_SAMPLED_PACKET_COUNT])

        parsed_input_stats_2 = get_psw_global_stats_values(input=True, psw_stats_output=psw_stats,
                                                           input_key_list=[PSW_SAMPLED_PACKET_COUNT])

        psw_diff_stats = get_diff_stats(old_stats=parsed_input_stats_1['input'],
                                        new_stats=parsed_input_stats_2['input'],
                                        stats_list=[PSW_SAMPLED_PACKET_COUNT])
        fun_test.test_assert_expected(expected=frames_received, actual=int(psw_diff_stats['sampled_pkt']),
                                      message=checkpoint)

        checkpoint = "Ensure sample frames are being transmitted by sample port FPG%d" % dut_sample_port
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_sample_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%d: %d and Frames Transmitted on Sample port FPG%d: %s" % (
            dut_rx_port, frames_received, dut_sample_port, frames_transmitted))
        fun_test.test_assert_expected(expected=frames_received, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Ensure sample counter for a rule must be equal to Tx frames"
        sample_diff_stats = get_diff_stats(old_stats=sample_stats_before[str(self.sample_id)],
                                           new_stats=sample_stats[str(self.sample_id)])
        fun_test.test_assert_expected(expected=frames_received,
                                      actual=int(sample_diff_stats['count']),
                                      message=checkpoint)
        # Validate Spirent stats
        checkpoint = "Ensure Packets are getting dropped on spirent Rx port %s due to ACL configured" % rx_port
        fun_test.test_assert_expected(expected=0,
                                      actual=rx_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure packets are getting received on sample spirent port %s" % sample_port
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
        dut_sample_port = dut_config['ports'][2]

        checkpoint = "Delete sample rule for id: %d" % self.sample_id
        network_controller_obj.disable_sample_rule(id=self.sample_id, dest=dut_sample_port)
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

    ts.add_test_case(SampleIngressFPGtoFPGIPv6())
    ts.add_test_case(SampleIngressDropIpChecksumError())
    ts.add_test_case(SampleSourceMultiDestination())
    ts.add_test_case(SampleFlagMaskTTL0Packets())
    ts.add_test_case(SampleMultiSourceSameDestination())
    ts.add_test_case(SampleIngressEgressMTUCase())
    
    ts.add_test_case(SampleSamePortIngressEgress())
    
    ts.add_test_case(SampleIngressEgressSamePacket())
    
    ts.add_test_case(SampleACLtoFPG())  # Failing due to SWOS-3682

    ts.add_test_case(SampleIngressARPRequest())
    
    ts.add_test_case(SampleIngressLLDP())

    ts.add_test_case(SampleIngressDropIPv4VerError())
    ts.add_test_case(SampleIngressDropFwdErrorWrongDIP())
    
    ts.add_test_case(SampleEgressMTUCase())

    ts.add_test_case(SampleEgressDropACL())

    ts.run()
