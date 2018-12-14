from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import *
from lib.host.network_controller import NetworkController
from scripts.networking.nu_config_manager import *
from scripts.networking.helper import *

dut_config = {}
spirent_config = {}
network_controller_obj = None
port1 = None
port2 = None
port3 = None
generator_handle = None
subscribed_results = None
TRAFFIC_DURATION = 10
DURATION_SECONDS = 20
cc_path_config = {}
LOAD = 110
LOAD_UNIT = StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND
FRAME_SIZE = 128
FRAME_LENGTH_MODE = StreamBlock.FRAME_LENGTH_MODE_FIXED
INTERFACE_LOADS_SPEC = SCRIPTS_DIR + "/networking" + "/interface_loads.json"
NUM_PORTS = 3
streams_group = []
MIN_RX_PORT_COUNT = 80
MAX_RX_PORT_COUNT = 90


class SetupSpirent(FunTestScript):
    generator_config_obj = None

    def describe(self):
        self.set_test_details(steps="""
        1. Check health of Spirent. Connect to Lab server
        2. Create ports and attach ports
        3. Read configs 
        4. In cleanup, disconnect session  
        """)

    def setup(self):
        fun_test.log("In script setup")
        global template_obj, dut_config, spirent_config, network_controller_obj, port1, port2, port3, cc_path_config, \
            interface_obj1, interface_obj2, generator_handle, subscribed_results
        global LOAD, LOAD_UNIT, FRAME_SIZE, FRAME_LENGTH_MODE, MIN_RX_PORT_COUNT, MAX_RX_PORT_COUNT, TRAFFIC_DURATION

        dut_type = fun_test.get_local_setting('dut_type')
        dut_config = nu_config_obj.read_dut_config(dut_type=dut_type, flow_type=NuConfigManager.CC_FLOW_TYPE,
                                                   flow_direction=FLOW_DIRECTION)

        chassis_type = fun_test.get_local_setting('chassis_type')
        spirent_config = nu_config_obj.read_traffic_generator_config()

        template_obj = SpirentEthernetTrafficTemplate(session_name="cc_path", spirent_config=spirent_config,
                                                      chassis_type=chassis_type)
        result = template_obj.setup(no_of_ports_needed=NUM_PORTS, flow_type=NuConfigManager.CC_FLOW_TYPE,
                                    flow_direction=FLOW_DIRECTION)
        fun_test.test_assert(result['result'], "Ensure Spirent Setup done")

        port1 = result['port_list'][0]
        port2 = result['port_list'][1]
        port3 = result['port_list'][2]

        interface_obj1 = result['interface_obj_list'][0]
        interface_obj2 = result['interface_obj_list'][1]

        dpc_server_ip = dut_config['dpcsh_tcp_proxy_ip']
        dpc_server_port = dut_config['dpcsh_tcp_proxy_port']
        network_controller_obj = NetworkController(dpc_server_ip=dpc_server_ip, dpc_server_port=dpc_server_port)

        configs = fun_test.parse_file_to_json(INTERFACE_LOADS_SPEC)
        fun_test.simple_assert(configs, "Read Interface loads file")
        cc_path_config = configs['cc_path']
        LOAD = cc_path_config['load']
        LOAD_UNIT = cc_path_config['load_unit']
        FRAME_SIZE = cc_path_config['frame_size']
        FRAME_LENGTH_MODE = cc_path_config['frame_length_mode']
        MIN_RX_PORT_COUNT = cc_path_config['rx_range_min']
        MAX_RX_PORT_COUNT = cc_path_config['rx_range_max']
        TRAFFIC_DURATION = cc_path_config['duration']

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(subscribed_results, checkpoint)

    def cleanup(self):
        fun_test.log("In script cleanup")
        template_obj.cleanup()


class TestCcErrorTrapTtlError1(FunTestCase):
    stream_obj = None
    validate_meter_stats = True
    meter_id = None
    erp = False

    def describe(self):
        self.set_test_details(id=1, summary="Test CC IPv4 TTL Error (TTL = 1)",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic   
                              6. Dump all the stats in logs
                              7. Validate Tx and Rx on spirent and ensure no errors are seen.
                              8. Validate Tx and Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX    
                              """ % (
                                  port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and IPv4 headers under port %s with IPv4 TTL = 1" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['destination_ip1'], ttl=1)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = IPV4_COPP_TTL_ERR_METER_ID

    def run(self):
        vp_stats_before = None
        erp_stats_before = None
        wro_stats_before = None
        meter_stats_before = None
        if dut_config['enable_dpcsh']:
            # TODO: Clear PSW, VP, WRO, meter stats. Will add this once support for clear stats provided in dpc
            checkpoint = "Clear FPG stats on all DUT ports"
            for port in dut_config['ports']:
                clear_stats = network_controller_obj.clear_port_stats(port_num=port)
                fun_test.simple_assert(clear_stats, "FPG stats clear on DUT port %d" % port)
            fun_test.add_checkpoint(checkpoint)

            checkpoint = "Get PSW and Parser NU stats before traffic"
            psw_stats = network_controller_obj.peek_psw_global_stats()
            parser_stats = network_controller_obj.peek_parser_stats()
            fun_test.log("PSW Stats: %s \n" % psw_stats)
            fun_test.log("Parser stats: %s \n" % parser_stats)
            fun_test.add_checkpoint(checkpoint)

            vp_stats_before = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)

            erp_stats_before = get_erp_stats_values(network_controller_obj=network_controller_obj)

            wro_stats_before = get_wro_global_stats_values(network_controller_obj=network_controller_obj)

            if self.meter_id:
                meter_stats_before = network_controller_obj.peek_meter_stats_by_id(meter_id=self.meter_id, erp=self.erp)

            fun_test.log("VP stats: %s" % vp_stats_before)
            fun_test.log("ERP stats: %s" % erp_stats_before)
            fun_test.log("WRO stats: %s" % wro_stats_before)
            if meter_stats_before:
                fun_test.log("METER stats for id %s : %s" % (str(self.meter_id), meter_stats_before))

        checkpoint = "Start traffic Traffic Duration: %d" % TRAFFIC_DURATION
        result = template_obj.enable_generator_configs([generator_handle])
        fun_test.test_assert(result, checkpoint)

        fun_test.sleep("Traffic to complete", seconds=DURATION_SECONDS)

        checkpoint = "Ensure Spirent stats fetched"
        tx_results = template_obj.stc_manager.get_tx_stream_block_results(stream_block_handle=self.stream_obj.
                                                                          spirent_handle,
                                                                          subscribe_handle=subscribed_results
                                                                          ['tx_subscribe'])
        rx_results = template_obj.stc_manager.get_rx_stream_block_results(stream_block_handle=self.stream_obj.
                                                                          spirent_handle,
                                                                          subscribe_handle=subscribed_results
                                                                          ['rx_subscribe'])
        rx_port_results = template_obj.stc_manager.get_rx_port_analyzer_results(port_handle=port3,
                                                                                subscribe_handle=subscribed_results
                                                                                ['analyzer_subscribe'])
        rx_port2_results = template_obj.stc_manager.get_rx_port_analyzer_results(port_handle=port2,
                                                                                 subscribe_handle=subscribed_results
                                                                                 ['analyzer_subscribe'])
        tx_port_results = template_obj.stc_manager.get_generator_port_results(port_handle=port1,
                                                                              subscribe_handle=subscribed_results
                                                                              ['generator_subscribe'])
        fun_test.simple_assert(rx_port_results and tx_port_results and rx_port2_results, checkpoint)

        fun_test.log("Tx Spirent Stats: %s" % tx_results)
        fun_test.log("Rx Spirent Stats: %s" % rx_results)
        fun_test.log("Tx Port Stats: %s" % tx_port_results)
        fun_test.log("Rx Port Stats: %s" % rx_port_results)
        fun_test.log("Rx Port 2 Stats: %s" % rx_port2_results)

        dut_tx_port_stats = None
        dut_rx_port_stats = None
        vp_stats = None
        erp_stats = None
        wro_stats = None
        meter_stats = None
        if dut_config['enable_dpcsh']:
            checkpoint = "Fetch PSW and Parser DUT stats after traffic"
            psw_stats = network_controller_obj.peek_psw_global_stats()
            parser_stats = network_controller_obj.peek_parser_stats()
            fun_test.log("PSW Stats: %s \n" % psw_stats)
            fun_test.log("Parser stats: %s \n" % parser_stats)
            fun_test.add_checkpoint(checkpoint)

            checkpoint = "Get FPG port stats for all ports"
            dut_tx_port_stats = network_controller_obj.peek_fpg_port_stats(port_num=dut_config['ports'][0])
            dut_rx_port_stats = network_controller_obj.peek_fpg_port_stats(port_num=dut_config['ports'][2])
            fun_test.simple_assert(dut_tx_port_stats and dut_rx_port_stats, checkpoint)

            fun_test.log("DUT Tx stats: %s" % dut_tx_port_stats)
            fun_test.log("DUT Rx stats: %s" % dut_rx_port_stats)

            checkpoint = "Fetch VP stats"
            vp_stats = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)
            fun_test.simple_assert(vp_stats, checkpoint)

            checkpoint = "Fetch ERP NU stats"
            erp_stats = get_erp_stats_values(network_controller_obj=network_controller_obj)
            fun_test.simple_assert(erp_stats, checkpoint)

            checkpoint = "Fetch WRO NU stats"
            wro_stats = get_wro_global_stats_values(network_controller_obj=network_controller_obj)
            fun_test.simple_assert(wro_stats, checkpoint)

            if self.meter_id:
                checkpoint = "Fetch Meter stats for meter id: %s" % str(self.meter_id)
                meter_stats = network_controller_obj.peek_meter_stats_by_id(meter_id=self.meter_id, erp=self.erp)
                fun_test.simple_assert(meter_stats, checkpoint)

            fun_test.log("VP stats: %s" % vp_stats)
            fun_test.log("ERP stats: %s" % erp_stats)
            fun_test.log("WRO stats: %s" % wro_stats)
            if meter_stats:
                fun_test.log("METER stats for id %s : %s" % (str(self.meter_id), meter_stats))

        # validation asserts
        # Spirent stats validation
        checkpoint = "Validate Tx and Rx on spirent"
        fun_test.log("Tx FrameCount: %d Rx FrameCount: %d" % (int(tx_port_results['GeneratorFrameCount']),
                                                              int(rx_port_results['TotalFrameCount'])))
        fun_test.test_assert((MIN_RX_PORT_COUNT <= int(rx_port_results['TotalFrameCount']) <= MAX_RX_PORT_COUNT),
                             checkpoint)

        checkpoint = "Ensure %s does not received any frames" % port2
        fun_test.log("Rx Port2 FrameCount: %d" % int(rx_port2_results['TotalFrameCount']))
        fun_test.test_assert_expected(expected=0, actual=int(rx_port2_results['TotalFrameCount']),
                                      message=checkpoint)

        checkpoint = "Ensure no errors are seen on spirent"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_results)
        fun_test.test_assert(expression=result['result'], message=checkpoint)

        # DUT stats validation
        if dut_config['enable_dpcsh']:
            checkpoint = "Validate Tx and Rx on DUT"
            frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_stats,
                                                            stat_type=FRAMES_RECEIVED_OK)
            frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_stats,
                                                         stat_type=FRAMES_TRANSMITTED_OK)
            fun_test.log("DUT Tx FrameCount: %s DUT Rx FrameCount: %s" % (str(frames_transmitted),
                                                                          str(frames_received)))
            fun_test.test_assert((MIN_RX_PORT_COUNT <= frames_received <= MAX_RX_PORT_COUNT),
                                 checkpoint)
            # VP stats validation
            checkpoint = "From VP stats, Ensure T2C header counter equal to spirent Tx counter"
            vp_stats_diff = get_diff_stats(old_stats=vp_stats_before, new_stats=vp_stats,
                                           stats_list=[VP_PACKETS_CONTROL_T2C_COUNT, VP_PACKETS_CC_OUT,
                                                       VP_PACKETS_TOTAL_OUT, VP_PACKETS_TOTAL_IN])
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=vp_stats_diff[VP_PACKETS_CONTROL_T2C_COUNT],
                                          message=checkpoint)
            checkpoint = "From VP stats, Ensure CC OUT counters are equal to spirent Tx Counter"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=vp_stats_diff[VP_PACKETS_CC_OUT],
                                          message=checkpoint)

            checkpoint = "Ensure VP total packets IN == VP total packets OUT"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=vp_stats_diff[VP_PACKETS_TOTAL_IN],
                                          message=checkpoint)
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=vp_stats_diff[VP_PACKETS_TOTAL_OUT],
                                          message=checkpoint)
            # ERP stats validation
            checkpoint = "From ERP stats, Ensure count for EFP to WQM decrement pulse equal to spirent Tx"
            erp_stats_diff = get_diff_stats(old_stats=erp_stats_before, new_stats=erp_stats,
                                            stats_list=[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED,
                                                        ERP_COUNT_FOR_EFP_WRO_DESCRIPTORS_SENT,
                                                        ERP_COUNT_FOR_EFP_WQM_DECREMENT_PULSE,
                                                        ERP_COUNT_FOR_ERP0_EFP_ERROR_INTERFACE_FLITS,
                                                        ERP_COUNT_FOR_EFP_FCP_VLD])
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=erp_stats_diff[ERP_COUNT_FOR_EFP_WQM_DECREMENT_PULSE],
                                          message=checkpoint)
            checkpoint = "From ERP stats, Ensure count for EFP to WRO descriptors send equal to spirent Tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=erp_stats_diff[ERP_COUNT_FOR_EFP_WRO_DESCRIPTORS_SENT],
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for ERP0 to EFP error interface flits equal to spirent Tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=erp_stats_diff[ERP_COUNT_FOR_ERP0_EFP_ERROR_INTERFACE_FLITS],
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for all non FCP packets received equal to spirent Tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=erp_stats_diff[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED],
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for EFP to FCB vld equal to spirent Tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=erp_stats_diff[ERP_COUNT_FOR_EFP_FCP_VLD],
                                          message=checkpoint)
            # WRO stats validation
            checkpoint = "From WRO stats, Ensure WRO IN packets equal to spirent Tx"
            wro_stats_diff = get_diff_stats(old_stats=wro_stats_before, new_stats=wro_stats)
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=wro_stats_diff['global'][WRO_IN_PKTS],
                                          message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO In NFCP packets equal to spirent Tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=wro_stats_diff['global'][WRO_IN_NFCP_PKTS],
                                          message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO out WUs equal to spirent tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=wro_stats_diff['global'][WRO_OUT_WUS],
                                          message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO WU CNT VPP packets equal to spirent tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=wro_stats_diff['global'][WRO_WU_COUNT_VPP],
                                          message=checkpoint)

            if self.validate_meter_stats:
                checkpoint = "Validate meter stats ensure frames_received == (green pkts + yellow pkts)"
                meter_stats_diff = get_diff_stats(old_stats=meter_stats_before, new_stats=meter_stats)
                green_pkts = int(meter_stats_diff['green']['pkts'])
                yellow_pkts = int(meter_stats_diff['yellow']['pkts'])
                red_pkts = int(meter_stats_diff['red']['pkts'])
                fun_test.log("Green: %d Yellow: %d Red: %d" % (green_pkts, yellow_pkts, red_pkts))
                fun_test.test_assert_expected(expected=frames_received, actual=(green_pkts + yellow_pkts),
                                              message=checkpoint)
                checkpoint = "Ensure red pkts are equal to DroppedFrameCount on Spirent Rx results"
                dropped_frame_count = int(rx_results['DroppedFrameCount'])
                fun_test.test_assert_expected(expected=dropped_frame_count, actual=red_pkts,
                                              message=checkpoint)

    def cleanup(self):
        fun_test.log("In test case cleanup")

        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)


class TestCcErrorTrapTtlError2(TestCcErrorTrapTtlError1):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=2, summary="Test CC IPv4 TTL Error (TTL = 0)",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic
                              6. Dump all the stats in logs
                              7. Validate Tx and Rx on spirent and ensure no errors are seen.
                              8. Validate Tx and Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX       
                              """ % (
                                  port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and IPv4 headers under port %s with IPv4 TTL = 0" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['destination_ip1'], ttl=0)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = IPV4_COPP_TTL_ERR_METER_ID

    def run(self):
        super(TestCcErrorTrapTtlError2, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)


class TestCcErrorTrapTtlError3(TestCcErrorTrapTtlError1):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=3, summary="Test CC IPv4 TTL Error (TTL = 1)",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic
                              6. Dump all the stats in logs
                              7. Validate Tx and Rx on spirent and ensure no errors are seen.
                              8. Validate Tx and Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX       
                              """ % (
                                  port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and IPv4 headers under port %s with IPv4 TTL = 1" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['cc_destination_ip1'], ttl=1)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = IPV4_COPP_TTL_ERR_METER_ID

    def run(self):
        super(TestCcErrorTrapTtlError3, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)


class TestCcIpv4ErrorTrapIpOpts1(TestCcErrorTrapTtlError1):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=4, summary="Test CC IPv4 OPTS Error (Header Option: timestamp)",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 with timestamp header option under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic
                              6. Dump all the stats in logs
                              7. Validate Tx == Rx on spirent and ensure no errors are seen.
                              8. Validate Tx == Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX       
                              """ % (
                                  port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and IPv4 with timestamp header option under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['destination_ip1'])
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Configure Ipv4 Header")
        timestamp_header_option_obj = IPv4HeaderOptionTimestamp()
        result = template_obj.stc_manager.update_header_options(header_obj=ipv4_header_obj,
                                                                option_obj=timestamp_header_option_obj,
                                                                stream_block_handle=self.stream_obj.spirent_handle)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = IPV4_COPP_OPTS_METER_ID

    def run(self):
        super(TestCcIpv4ErrorTrapIpOpts1, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)


class TestCcIpv4ErrorTrapIpOpts2(TestCcErrorTrapTtlError1):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=5, summary="Test CC IPv4 OPTS Error (Header Option: Loose Src Route)",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 with Loose Src Route header option under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic
                              6. Dump all the stats in logs
                              7. Validate Tx and Rx on spirent and ensure no errors are seen.
                              8. Validate Tx and Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX       
                              """ % (
                                  port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and IPv4 with Loose Src Route header option under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['destination_ip1'])
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Configure Ipv4 Header")
        lsr_header_option_obj = IPv4HeaderOptionLooseSourceRoute()
        result = template_obj.stc_manager.update_header_options(header_obj=ipv4_header_obj,
                                                                option_obj=lsr_header_option_obj,
                                                                stream_block_handle=self.stream_obj.spirent_handle)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = IPV4_COPP_OPTS_METER_ID

    def run(self):
        super(TestCcIpv4ErrorTrapIpOpts2, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)


class TestCcIpChecksumError(FunTestCase):
    stream_obj = None
    validate_meter_stats = True
    meter_id = None

    def describe(self):
        self.set_test_details(id=6, summary="Test CC IP checksum Error ",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 header option under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic
                              6. Dump all the stats in logs
                              7. Validate Tx and Rx on spirent and ensure IPv4 Checksum error are seen.
                              8. Validate Tx and Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX   
                              """ % (
                                  port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and Ipv4 header option under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['destination_ip1'],
                                     checksum=Ipv4Header.CHECKSUM_ERROR)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = ERR_TRAP_COPP_OUTER_CKSUM_ERR_METER_ID

    def run(self):
        vp_stats_before = None
        erp_stats_before = None
        wro_stats_before = None
        meter_stats_before = None

        if dut_config['enable_dpcsh']:
            # TODO: Clear PSW, VP, WRO, meter stats. Will add this once support for clear stats provided in dpc
            checkpoint = "Clear FPG stats on all DUT ports"
            for port in dut_config['ports']:
                clear_stats = network_controller_obj.clear_port_stats(port_num=port)
                fun_test.simple_assert(clear_stats, "FPG stats clear on DUT port %d" % port)
            fun_test.add_checkpoint(checkpoint)

            checkpoint = "Get PSW and Parser NU stats before traffic"
            psw_stats = network_controller_obj.peek_psw_global_stats()
            parser_stats = network_controller_obj.peek_parser_stats()
            fun_test.log("PSW Stats: %s \n" % psw_stats)
            fun_test.log("Parser stats: %s \n" % parser_stats)
            fun_test.add_checkpoint(checkpoint)

            vp_stats_before = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)

            erp_stats_before = get_erp_stats_values(network_controller_obj=network_controller_obj)

            wro_stats_before = get_wro_global_stats_values(network_controller_obj=network_controller_obj)

            if self.meter_id:
                meter_stats_before = network_controller_obj.peek_meter_stats_by_id(meter_id=self.meter_id)

            fun_test.log("VP stats: %s" % vp_stats_before)
            fun_test.log("ERP stats: %s" % erp_stats_before)
            fun_test.log("WRO stats: %s" % wro_stats_before)
            if meter_stats_before:
                fun_test.log("METER stats for id %s : %s" % (str(self.meter_id), meter_stats_before))

        checkpoint = "Start traffic Traffic Duration: %d" % TRAFFIC_DURATION
        result = template_obj.enable_generator_configs([generator_handle])
        fun_test.test_assert(result, checkpoint)

        fun_test.sleep("Traffic to complete", seconds=DURATION_SECONDS)

        checkpoint = "Ensure Spirent stats fetched"
        tx_results = template_obj.stc_manager.get_tx_stream_block_results(stream_block_handle=self.stream_obj.
                                                                          spirent_handle,
                                                                          subscribe_handle=subscribed_results
                                                                          ['tx_subscribe'])

        rx_results = template_obj.stc_manager.get_rx_stream_block_results(stream_block_handle=self.stream_obj.
                                                                          spirent_handle,
                                                                          subscribe_handle=subscribed_results
                                                                          ['rx_subscribe'])
        tx_port_results = template_obj.stc_manager.get_generator_port_results(port_handle=port1,
                                                                              subscribe_handle=subscribed_results
                                                                              ['generator_subscribe'])
        rx_port_results = template_obj.stc_manager.get_rx_port_analyzer_results(port_handle=port3,
                                                                                subscribe_handle=subscribed_results
                                                                                ['analyzer_subscribe'])
        rx_port2_results = template_obj.stc_manager.get_rx_port_analyzer_results(port_handle=port2,
                                                                                 subscribe_handle=subscribed_results
                                                                                 ['analyzer_subscribe'])
        fun_test.simple_assert(tx_port_results and rx_port2_results and rx_port_results, checkpoint)

        fun_test.log("Tx Spirent Stats: %s" % tx_results)
        fun_test.log("Rx Spirent Stats: %s" % rx_results)
        fun_test.log("Tx Port Stats: %s" % tx_port_results)
        fun_test.log("Rx Port Stats: %s" % rx_port_results)
        fun_test.log("Rx Port2 Stats: %s" % rx_port2_results)

        dut_tx_port_stats = None
        dut_rx_port_stats = None
        vp_stats = None
        erp_stats = None
        wro_stats = None
        meter_stats = None
        if dut_config['enable_dpcsh']:
            checkpoint = "Fetch PSW and Parser DUT stats after traffic"
            psw_stats = network_controller_obj.peek_psw_global_stats()
            parser_stats = network_controller_obj.peek_parser_stats()
            fun_test.log("PSW Stats: %s \n" % psw_stats)
            fun_test.log("Parser stats: %s \n" % parser_stats)
            fun_test.add_checkpoint(checkpoint)

            checkpoint = "Get FPG port stats for all ports"
            dut_tx_port_stats = network_controller_obj.peek_fpg_port_stats(port_num=dut_config['ports'][0])
            dut_rx_port_stats = network_controller_obj.peek_fpg_port_stats(port_num=dut_config['ports'][2])
            fun_test.simple_assert(dut_tx_port_stats and dut_rx_port_stats, checkpoint)

            fun_test.log("DUT Tx stats: %s" % dut_tx_port_stats)
            fun_test.log("DUT Rx stats: %s" % dut_rx_port_stats)

            checkpoint = "Fetch VP stats"
            vp_stats = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)
            fun_test.simple_assert(vp_stats, checkpoint)

            checkpoint = "Fetch ERP NU stats"
            erp_stats = get_erp_stats_values(network_controller_obj=network_controller_obj)
            fun_test.simple_assert(erp_stats, checkpoint)

            checkpoint = "Fetch WRO NU stats"
            wro_stats = get_wro_global_stats_values(network_controller_obj=network_controller_obj)
            fun_test.simple_assert(wro_stats, checkpoint)

            if self.meter_id:
                checkpoint = "Fetch Meter stats for meter id: %s" % str(self.meter_id)
                meter_stats = network_controller_obj.peek_meter_stats_by_id(meter_id=self.meter_id)
                fun_test.simple_assert(meter_stats, checkpoint)

            fun_test.log("VP stats: %s" % vp_stats)
            fun_test.log("ERP stats: %s" % erp_stats)
            fun_test.log("WRO stats: %s" % wro_stats)
            if meter_stats:
                fun_test.log("METER stats for id %s : %s" % (str(self.meter_id), meter_stats))

        # validation asserts
        # Spirent stats validation
        checkpoint = "Validate Tx and Rx on spirent"
        fun_test.log("Tx FrameCount: %d Rx FrameCount: %d" % (int(tx_port_results['GeneratorFrameCount']),
                                                              int(rx_port_results['TotalFrameCount'])))
        fun_test.test_assert((MIN_RX_PORT_COUNT <= int(rx_port_results['TotalFrameCount']) <= MAX_RX_PORT_COUNT),
                             checkpoint)

        checkpoint = "Ensure %s does not received any frames" % port2
        fun_test.log("Rx Port2 FrameCount: %d" % int(rx_port2_results['TotalFrameCount']))
        fun_test.test_assert_expected(expected=0, actual=int(rx_port2_results['TotalFrameCount']),
                                      message=checkpoint)

        checkpoint = "Ensure checksum errors are seen on spirent"
        result = template_obj.check_non_zero_error_count(rx_results=rx_results)
        checksum_error_seen = False
        if result['Ipv4ChecksumErrorCount'] > 0 and len(result) == 3 and result['DroppedFrameCount'] > 0:
            checksum_error_seen = True
        fun_test.test_assert(expression=checksum_error_seen, message=checkpoint)

        # DUT stats validation
        if dut_config['enable_dpcsh']:
            checkpoint = "Validate Tx and Rx on DUT"
            frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_stats,
                                                            stat_type=FRAMES_RECEIVED_OK)
            frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_stats,
                                                         stat_type=FRAMES_TRANSMITTED_OK)
            fun_test.log("DUT Tx FrameCount: %s DUT Rx FrameCount: %s" % (str(frames_transmitted),
                                                                          str(frames_received)))
            fun_test.test_assert((MIN_RX_PORT_COUNT <= frames_received <= MAX_RX_PORT_COUNT),
                                 checkpoint)
            # VP stats validation
            checkpoint = "From VP stats, Ensure T2C header counter equal to spirent Tx counter"
            vp_stats_diff = get_diff_stats(old_stats=vp_stats_before, new_stats=vp_stats,
                                           stats_list=[VP_PACKETS_CONTROL_T2C_COUNT, VP_PACKETS_CC_OUT,
                                                       VP_PACKETS_TOTAL_OUT, VP_PACKETS_TOTAL_IN])
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=vp_stats_diff[VP_PACKETS_CONTROL_T2C_COUNT],
                                          message=checkpoint)
            checkpoint = "From VP stats, Ensure CC OUT counters are equal to spirent Tx Counter"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=vp_stats_diff[VP_PACKETS_CC_OUT],
                                          message=checkpoint)

            checkpoint = "Ensure VP total packets IN == VP total packets OUT"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=vp_stats_diff[VP_PACKETS_TOTAL_IN],
                                          message=checkpoint)
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=vp_stats_diff[VP_PACKETS_TOTAL_OUT],
                                          message=checkpoint)
            # ERP stats validation
            checkpoint = "From ERP stats, Ensure count for EFP to WQM decrement pulse equal to spirent Tx"
            erp_stats_diff = get_diff_stats(old_stats=erp_stats_before, new_stats=erp_stats,
                                            stats_list=[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED,
                                                        ERP_COUNT_FOR_EFP_WRO_DESCRIPTORS_SENT,
                                                        ERP_COUNT_FOR_EFP_WQM_DECREMENT_PULSE,
                                                        ERP_COUNT_FOR_ERP0_EFP_ERROR_INTERFACE_FLITS,
                                                        ERP_COUNT_FOR_EFP_FCP_VLD])
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=erp_stats_diff[ERP_COUNT_FOR_EFP_WQM_DECREMENT_PULSE],
                                          message=checkpoint)
            checkpoint = "From ERP stats, Ensure count for EFP to WRO descriptors send equal to spirent Tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=erp_stats_diff[ERP_COUNT_FOR_EFP_WRO_DESCRIPTORS_SENT],
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for ERP0 to EFP error interface flits equal to spirent Tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=erp_stats_diff[ERP_COUNT_FOR_ERP0_EFP_ERROR_INTERFACE_FLITS],
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for all non FCP packets received equal to spirent Tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=erp_stats_diff[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED],
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for EFP to FCB vld equal to spirent Tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=erp_stats_diff[ERP_COUNT_FOR_EFP_FCP_VLD],
                                          message=checkpoint)
            # WRO stats validation
            checkpoint = "From WRO stats, Ensure WRO IN packets equal to spirent Tx"
            wro_stats_diff = get_diff_stats(old_stats=wro_stats_before, new_stats=wro_stats)
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=wro_stats_diff['global'][WRO_IN_PKTS],
                                          message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO In NFCP packets equal to spirent Tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=wro_stats_diff['global'][WRO_IN_NFCP_PKTS],
                                          message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO out WUs equal to spirent tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=wro_stats_diff['global'][WRO_OUT_WUS],
                                          message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO WU CNT VPP packets equal to spirent tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=wro_stats_diff['global'][WRO_WU_COUNT_VPP],
                                          message=checkpoint)

            if self.validate_meter_stats:
                checkpoint = "Validate meter stats ensure frames_received == (green pkts + yellow pkts)"
                meter_stats_diff = get_diff_stats(old_stats=meter_stats_before, new_stats=meter_stats)
                green_pkts = int(meter_stats_diff['green']['pkts'])
                yellow_pkts = int(meter_stats_diff['yellow']['pkts'])
                red_pkts = int(meter_stats_diff['red']['pkts'])
                fun_test.log("Green: %d Yellow: %d Red: %d" % (green_pkts, yellow_pkts, red_pkts))
                fun_test.test_assert_expected(expected=frames_received, actual=(green_pkts + yellow_pkts),
                                              message=checkpoint)
                checkpoint = "Ensure red pkts are equal to DroppedFrameCount on Spirent Rx results"
                dropped_frame_count = int(rx_results['DroppedFrameCount'])
                fun_test.test_assert_expected(expected=dropped_frame_count, actual=red_pkts,
                                              message=checkpoint)

    def cleanup(self):
        fun_test.log("In test case cleanup")

        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)


class TestCcFSFError(TestCcErrorTrapTtlError1):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=7, summary="Test CC FSF Error",
                              steps="""
                              1. Create a stream with EthernetII and Custom header option under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic
                              6. Dump all the stats in logs
                              7. Validate Tx and Rx on spirent and ensure no errors are seen.
                              8. Validate Tx and Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX   
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        checkpoint = "Create a stream with EthernetII and Custom header option under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.ETHERNET_FLOW_CONTROL_MAC,
                                    ether_type=Ethernet2Header.ETHERNET_FLOW_CONTROL_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        custom_header_obj = CustomBytePatternHeader(byte_pattern="11010000")
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=custom_header_obj, update=False,
                                                                delete_header=[Ipv4Header.HEADER_TYPE])
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = ERR_TRAP_COPP_FSF_METER_ID
        self.erp = True

    def run(self):
        super(TestCcFSFError, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)


class TestCcOuterChecksumError(FunTestCase):
    stream_obj = None
    frame_size = 148
    meter_id = None
    validate_meter_stats = True

    def describe(self):
        self.set_test_details(id=8, summary="Test CC IPv4 Outer Checksum Error",
                              steps="""
                              1. Create a stream with Overlay Frame Stack under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic
                              6. Dump all the stats in logs
                              7. Validate Tx == Rx on spirent and ensure no errors are seen.
                              8. Validate Tx == Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX   
                                  """ % (port1, FRAME_LENGTH_MODE, self.frame_size, LOAD, LOAD_UNIT, port1,
                                         TRAFFIC_DURATION))

    def setup(self):
        checkpoint = "Create a stream with Overlay Frame Stack under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=self.frame_size,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        result = template_obj.configure_overlay_frame_stack(port=port1, streamblock_obj=self.stream_obj,
                                                            overlay_type=SpirentEthernetTrafficTemplate.ETH_IPV4_UDP_VXLAN_ETH_IPV4_TCP)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Update IPv4 stack with destination IP and checksum error"
        ipv4_header_obj = Ipv4Header(checksum=Ipv4Header.CHECKSUM_ERROR, destination_address="29.1.1.1")
        result = template_obj.update_overlay_frame_header(streamblock_obj=self.stream_obj, header_obj=ipv4_header_obj,
                                                          overlay=False,
                                                          updated_header_attributes_dict={
                                                              "checksum": Ipv4Header.CHECKSUM_ERROR,
                                                              "destAddr": "29.1.1.1"})
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = ERR_TRAP_COPP_OUTER_CKSUM_ERR_METER_ID

    def run(self):
        vp_stats_before = None
        erp_stats_before = None
        wro_stats_before = None
        meter_stats_before = None
        if dut_config['enable_dpcsh']:
            # TODO: Clear PSW, VP, WRO, meter stats. Will add this once support for clear stats provided in dpc
            checkpoint = "Clear FPG stats on all DUT ports"
            for port in dut_config['ports']:
                clear_stats = network_controller_obj.clear_port_stats(port_num=port)
                fun_test.simple_assert(clear_stats, "FPG stats clear on DUT port %d" % port)
            fun_test.add_checkpoint(checkpoint)

            checkpoint = "Get PSW and Parser NU stats before traffic"
            psw_stats = network_controller_obj.peek_psw_global_stats()
            parser_stats = network_controller_obj.peek_parser_stats()
            fun_test.log("PSW Stats: %s \n" % psw_stats)
            fun_test.log("Parser stats: %s \n" % parser_stats)
            fun_test.add_checkpoint(checkpoint)

            vp_stats_before = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)

            erp_stats_before = get_erp_stats_values(network_controller_obj=network_controller_obj)

            wro_stats_before = get_wro_global_stats_values(network_controller_obj=network_controller_obj)

            if self.meter_id:
                meter_stats_before = network_controller_obj.peek_meter_stats_by_id(meter_id=self.meter_id, erp=True)

            fun_test.log("VP stats: %s" % vp_stats_before)
            fun_test.log("ERP stats: %s" % erp_stats_before)
            fun_test.log("WRO stats: %s" % wro_stats_before)
            if meter_stats_before:
                fun_test.log("METER stats for id %s : %s" % (str(self.meter_id), meter_stats_before))

        checkpoint = "Start traffic Traffic Duration: %d" % TRAFFIC_DURATION
        result = template_obj.enable_generator_configs([generator_handle])
        fun_test.test_assert(result, checkpoint)

        fun_test.sleep("Traffic to complete", seconds=DURATION_SECONDS)

        checkpoint = "Ensure Spirent stats fetched"
        tx_results = template_obj.stc_manager.get_tx_stream_block_results(stream_block_handle=self.stream_obj.
                                                                          spirent_handle,
                                                                          subscribe_handle=subscribed_results
                                                                          ['tx_subscribe'])

        rx_results = template_obj.stc_manager.get_rx_stream_block_results(stream_block_handle=self.stream_obj.
                                                                          spirent_handle,
                                                                          subscribe_handle=subscribed_results
                                                                          ['rx_subscribe'])
        tx_port_results = template_obj.stc_manager.get_generator_port_results(port_handle=port1,
                                                                              subscribe_handle=subscribed_results
                                                                              ['generator_subscribe'])
        rx_port_results = template_obj.stc_manager.get_rx_port_analyzer_results(port_handle=port3,
                                                                                subscribe_handle=subscribed_results
                                                                                ['analyzer_subscribe'])
        rx_port2_results = template_obj.stc_manager.get_rx_port_analyzer_results(port_handle=port2,
                                                                                 subscribe_handle=subscribed_results
                                                                                 ['analyzer_subscribe'])
        fun_test.simple_assert(tx_port_results and rx_port2_results and rx_port_results, checkpoint)

        fun_test.log("Tx Spirent Stats: %s" % tx_results)
        fun_test.log("Rx Spirent Stats: %s" % rx_results)
        fun_test.log("Tx Port stats: %s" % tx_port_results)
        fun_test.log("Rx Port 2 Stats: %s" % rx_port2_results)
        fun_test.log("Rx Port Stats: %s" % rx_port_results)

        dut_tx_port_stats = None
        dut_rx_port_stats = None
        vp_stats = None
        erp_stats = None
        wro_stats = None
        meter_stats = None
        if dut_config['enable_dpcsh']:
            checkpoint = "Fetch PSW and Parser DUT stats after traffic"
            psw_stats = network_controller_obj.peek_psw_global_stats()
            parser_stats = network_controller_obj.peek_parser_stats()
            fun_test.log("PSW Stats: %s \n" % psw_stats)
            fun_test.log("Parser stats: %s \n" % parser_stats)
            fun_test.add_checkpoint(checkpoint)

            checkpoint = "Get FPG port stats for all ports"
            dut_tx_port_stats = network_controller_obj.peek_fpg_port_stats(port_num=dut_config['ports'][0])
            dut_rx_port_stats = network_controller_obj.peek_fpg_port_stats(port_num=dut_config['ports'][2])
            fun_test.simple_assert(dut_tx_port_stats and dut_rx_port_stats, checkpoint)

            fun_test.log("DUT Tx stats: %s" % dut_tx_port_stats)
            fun_test.log("DUT Rx stats: %s" % dut_rx_port_stats)

            checkpoint = "Fetch VP stats"
            vp_stats = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)
            fun_test.simple_assert(vp_stats, checkpoint)

            checkpoint = "Fetch ERP NU stats"
            erp_stats = get_erp_stats_values(network_controller_obj=network_controller_obj)
            fun_test.simple_assert(erp_stats, checkpoint)

            checkpoint = "Fetch WRO NU stats"
            wro_stats = get_wro_global_stats_values(network_controller_obj=network_controller_obj)
            fun_test.simple_assert(wro_stats, checkpoint)

            if self.meter_id:
                checkpoint = "Fetch Meter stats for meter id: %s" % str(self.meter_id)
                meter_stats = network_controller_obj.peek_meter_stats_by_id(meter_id=self.meter_id, erp=True)
                fun_test.simple_assert(meter_stats, checkpoint)

            fun_test.log("VP stats: %s" % vp_stats)
            fun_test.log("ERP stats: %s" % erp_stats)
            fun_test.log("WRO stats: %s" % wro_stats)
            if meter_stats:
                fun_test.log("METER stats for id %s : %s" % (str(self.meter_id), meter_stats))

        # validation asserts
        # Spirent stats validation
        checkpoint = "Validate Tx and Rx on spirent"
        fun_test.log("Tx FrameCount: %d Rx FrameCount: %d" % (int(tx_port_results['GeneratorFrameCount']),
                                                              int(rx_port_results['TotalFrameCount'])))
        fun_test.test_assert((MIN_RX_PORT_COUNT <= int(rx_port_results['TotalFrameCount']) <= MAX_RX_PORT_COUNT),
                             checkpoint)

        checkpoint = "Ensure %s does not received any frames" % port2
        fun_test.log("Rx Port2 FrameCount: %d" % int(rx_port2_results['TotalFrameCount']))
        fun_test.test_assert_expected(expected=0, actual=int(rx_port2_results['TotalFrameCount']),
                                      message=checkpoint)

        checkpoint = "Ensure checksum errors are seen on spirent"
        result = template_obj.check_non_zero_error_count(rx_results=rx_results)
        checksum_error_seen = False
        if result['Ipv4ChecksumErrorCount'] > 0 and len(result) == 3 and result['DroppedFrameCount'] > 0:
            checksum_error_seen = True
        fun_test.test_assert(expression=checksum_error_seen, message=checkpoint)

        # DUT stats validation
        if dut_config['enable_dpcsh']:
            checkpoint = "Validate Tx and Rx on DUT"
            frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_stats,
                                                            stat_type=FRAMES_RECEIVED_OK)
            frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_stats,
                                                         stat_type=FRAMES_TRANSMITTED_OK)
            fun_test.log("DUT Tx FrameCount: %s DUT Rx FrameCount: %s" % (str(frames_transmitted),
                                                                          str(frames_received)))
            fun_test.test_assert((MIN_RX_PORT_COUNT <= frames_received <= MAX_RX_PORT_COUNT),
                                 checkpoint)
            # VP stats validation
            checkpoint = "From VP stats, Ensure T2C header counter equal to spirent Tx counter"
            vp_stats_diff = get_diff_stats(old_stats=vp_stats_before, new_stats=vp_stats,
                                           stats_list=[VP_PACKETS_CONTROL_T2C_COUNT, VP_PACKETS_CC_OUT,
                                                       VP_PACKETS_TOTAL_OUT, VP_PACKETS_TOTAL_IN])
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=vp_stats_diff[VP_PACKETS_CONTROL_T2C_COUNT],
                                          message=checkpoint)
            checkpoint = "From VP stats, Ensure CC OUT counters are equal to spirent Tx Counter"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=vp_stats_diff[VP_PACKETS_CC_OUT],
                                          message=checkpoint)

            checkpoint = "Ensure VP total packets IN == VP total packets OUT"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=vp_stats_diff[VP_PACKETS_TOTAL_IN],
                                          message=checkpoint)
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=vp_stats_diff[VP_PACKETS_TOTAL_OUT],
                                          message=checkpoint)
            # ERP stats validation
            checkpoint = "From ERP stats, Ensure count for EFP to WQM decrement pulse equal to spirent Tx"
            erp_stats_diff = get_diff_stats(old_stats=erp_stats_before, new_stats=erp_stats,
                                            stats_list=[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED,
                                                        ERP_COUNT_FOR_EFP_WRO_DESCRIPTORS_SENT,
                                                        ERP_COUNT_FOR_EFP_WQM_DECREMENT_PULSE,
                                                        ERP_COUNT_FOR_ERP0_EFP_ERROR_INTERFACE_FLITS,
                                                        ERP_COUNT_FOR_EFP_FCP_VLD])
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=erp_stats_diff[ERP_COUNT_FOR_EFP_WQM_DECREMENT_PULSE],
                                          message=checkpoint)
            checkpoint = "From ERP stats, Ensure count for EFP to WRO descriptors send equal to spirent Tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=erp_stats_diff[ERP_COUNT_FOR_EFP_WRO_DESCRIPTORS_SENT],
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for ERP0 to EFP error interface flits equal to spirent Tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=erp_stats_diff[ERP_COUNT_FOR_ERP0_EFP_ERROR_INTERFACE_FLITS],
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for all non FCP packets received equal to spirent Tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=erp_stats_diff[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED],
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for EFP to FCB vld equal to spirent Tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=erp_stats_diff[ERP_COUNT_FOR_EFP_FCP_VLD],
                                          message=checkpoint)
            # WRO stats validation
            checkpoint = "From WRO stats, Ensure WRO IN packets equal to spirent Tx"
            wro_stats_diff = get_diff_stats(old_stats=wro_stats_before, new_stats=wro_stats)
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=wro_stats_diff['global'][WRO_IN_PKTS],
                                          message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO In NFCP packets equal to spirent Tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=wro_stats_diff['global'][WRO_IN_NFCP_PKTS],
                                          message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO out WUs equal to spirent tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=wro_stats_diff['global'][WRO_OUT_WUS],
                                          message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO WU CNT VPP packets equal to spirent tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=wro_stats_diff['global'][WRO_WU_COUNT_VPP],
                                          message=checkpoint)

            if self.validate_meter_stats:
                checkpoint = "Validate meter stats ensure frames_received == (green pkts + yellow pkts)"
                meter_stats_diff = get_diff_stats(old_stats=meter_stats_before, new_stats=meter_stats)
                green_pkts = int(meter_stats_diff['green']['pkts'])
                yellow_pkts = int(meter_stats_diff['yellow']['pkts'])
                red_pkts = int(meter_stats_diff['red']['pkts'])
                fun_test.log("Green: %d Yellow: %d Red: %d" % (green_pkts, yellow_pkts, red_pkts))
                fun_test.test_assert_expected(expected=frames_received, actual=(green_pkts + yellow_pkts),
                                              message=checkpoint)
                checkpoint = "Ensure red pkts are equal to DroppedFrameCount on Spirent Rx results"
                dropped_frame_count = int(rx_results['DroppedFrameCount'])
                fun_test.test_assert_expected(expected=dropped_frame_count, actual=red_pkts,
                                              message=checkpoint)

    def cleanup(self):
        fun_test.log("In test case cleanup")
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)


class TestCcInnerChecksumError(TestCcErrorTrapTtlError1):
    stream_obj = None
    frame_size = 148

    def describe(self):
        self.set_test_details(id=9, summary="Test CC IPv4 Inner Checksum Error",
                              steps="""
                              1. Create a stream with Overlay Frame Stack under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic
                              6. Dump all the stats in logs
                              7. Validate Tx == Rx on spirent and ensure no errors are seen.
                              8. Validate Tx == Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX   
                                  """ % (port1, FRAME_LENGTH_MODE, self.frame_size, LOAD, LOAD_UNIT, port1,
                                         TRAFFIC_DURATION))

    def setup(self):
        checkpoint = "Create a stream with Overlay Frame Stack under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=self.frame_size,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        result = template_obj.configure_overlay_frame_stack(port=port1, streamblock_obj=self.stream_obj,
                                                            overlay_type=SpirentEthernetTrafficTemplate.ETH_IPV4_UDP_VXLAN_ETH_IPV4_TCP)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Update IPv4 stack with destination IP"
        ipv4_header_obj = Ipv4Header(destination_address="29.1.1.1", checksum=Ipv4Header.CHECKSUM_ERROR)
        result = template_obj.update_overlay_frame_header(streamblock_obj=self.stream_obj, header_obj=ipv4_header_obj,
                                                          overlay=False,
                                                          updated_header_attributes_dict={"destAddr": "29.1.1.1"})
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Update IPv4 stack with Checksum"
        result = template_obj.update_overlay_frame_header(streamblock_obj=self.stream_obj, header_obj=ipv4_header_obj,
                                                          overlay=True,
                                                          updated_header_attributes_dict={
                                                              "checksum": Ipv4Header.CHECKSUM_ERROR})
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Update UDP with destination_port = 4789"
        udp_header_obj = UDP(destination_port=4789)
        result = template_obj.update_overlay_frame_header(streamblock_obj=self.stream_obj, header_obj=udp_header_obj,
                                                          updated_header_attributes_dict={"destPort": 4789})
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = ERR_TRAP_COPP_INNER_CKSUM_ERR_METER_ID
        self.erp = True

    def run(self):
        super(TestCcInnerChecksumError, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4OverlayVersionError(TestCcErrorTrapTtlError1):
    stream_obj = None
    frame_size = 148

    def describe(self):
        self.set_test_details(id=10, summary="Test CC IPv4 Overlay Version (version = 2) Error",
                              steps="""
                              1. Create a stream with Overlay Frame Stack under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic
                              6. Dump all the stats in logs
                              7. Validate Tx == Rx on spirent and ensure no errors are seen.
                              8. Validate Tx == Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX   
                                  """ % (port1, FRAME_LENGTH_MODE, self.frame_size, LOAD, LOAD_UNIT, port1,
                                         TRAFFIC_DURATION))

    def setup(self):
        checkpoint = "Create a stream with Overlay Frame Stack under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=self.frame_size,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        result = template_obj.configure_overlay_frame_stack(port=port1, streamblock_obj=self.stream_obj,
                                                            overlay_type=SpirentEthernetTrafficTemplate.ETH_IPV4_UDP_VXLAN_ETH_IPV4_TCP)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Update IPv4 stack with destination IP"
        ipv4_header_obj = Ipv4Header(destination_address="29.1.1.1", version=2)
        result = template_obj.update_overlay_frame_header(streamblock_obj=self.stream_obj, header_obj=ipv4_header_obj,
                                                          overlay=False,
                                                          updated_header_attributes_dict={"destAddr": "29.1.1.1"})
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Update IPv4 stack with version = 2"
        result = template_obj.update_overlay_frame_header(streamblock_obj=self.stream_obj, header_obj=ipv4_header_obj,
                                                          overlay=True, updated_header_attributes_dict={"version": 2})
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Update UDP with destination_port = 4789"
        udp_header_obj = UDP(destination_port=4789)
        result = template_obj.update_overlay_frame_header(streamblock_obj=self.stream_obj, header_obj=udp_header_obj,
                                                          updated_header_attributes_dict={"destPort": 4789})
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = ERR_TRAP_COPP_PRSR_OL_V4_VER_METER_ID

    def run(self):
        super(TestCcIPv4OverlayVersionError, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4OverlayIhlError(TestCcErrorTrapTtlError1):
    stream_obj = None
    frame_size = 148

    def describe(self):
        self.set_test_details(id=11, summary="Test CC IPv4 Overlay Internet Header length (ihl = 3) Error",
                              steps="""
                              1. Create a stream with Overlay Frame Stack under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic 
                              6. Dump all the stats in logs
                              7. Validate Tx == Rx on spirent and ensure no errors are seen.
                              8. Validate Tx == Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX  
                                  """ % (port1, FRAME_LENGTH_MODE, self.frame_size, LOAD, LOAD_UNIT, port1,
                                         TRAFFIC_DURATION))

    def setup(self):
        checkpoint = "Create a stream with Overlay Frame Stack under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=self.frame_size,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        result = template_obj.configure_overlay_frame_stack(port=port1, streamblock_obj=self.stream_obj,
                                                            overlay_type=SpirentEthernetTrafficTemplate.ETH_IPV4_UDP_VXLAN_ETH_IPV4_TCP)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Update IPv4 stack with destination IP"
        ipv4_header_obj = Ipv4Header(destination_address="29.1.1.1", ihl=3)
        result = template_obj.update_overlay_frame_header(streamblock_obj=self.stream_obj, header_obj=ipv4_header_obj,
                                                          overlay=False,
                                                          updated_header_attributes_dict={"destAddr": "29.1.1.1"})
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Update IPv4 stack with ihl = 3"
        result = template_obj.update_overlay_frame_header(streamblock_obj=self.stream_obj, header_obj=ipv4_header_obj,
                                                          overlay=True, updated_header_attributes_dict={"ihl": 3})
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Update UDP with destination_port = 4789"
        udp_header_obj = UDP(destination_port=4789)
        result = template_obj.update_overlay_frame_header(streamblock_obj=self.stream_obj, header_obj=udp_header_obj,
                                                          updated_header_attributes_dict={"destPort": 4789})
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = ERR_TRAP_COPP_PRSR_OL_IHL_METER_ID

    def run(self):
        super(TestCcIPv4OverlayIhlError, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4VersionError(TestCcErrorTrapTtlError1):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=12, summary="Test CC IPv4 Version Error",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 with version = 0  under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic
                              6. Dump all the stats in logs
                              7. Validate Tx == Rx on spirent and ensure no errors are seen.
                              8. Validate Tx == Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX   
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']
        checkpoint = "Create a stream with EthernetII and IPv4 with version = 0  under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['destination_ip1'], version=0)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = ERR_TRAP_COPP_PRSR_V4_VER_METER_ID

    def run(self):
        super(TestCcIPv4VersionError, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4InternetHeaderLengthError(TestCcErrorTrapTtlError1):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=13, summary="Test CC IPv4 Internet Header Length Error",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 with Header Length = 4  under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic
                              6. Dump all the stats in logs
                              7. Validate Tx == Rx on spirent and ensure no errors are seen.
                              8. Validate Tx == Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX   
                                  """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1,
                                         TRAFFIC_DURATION))

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']
        checkpoint = "Create a stream with EthernetII and IPv4 with ihl = 4  under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['destination_ip1'], ihl=4)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = ERR_TRAP_COPP_PRSR_IHL_METER_ID

    def run(self):
        super(TestCcIPv4InternetHeaderLengthError, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4FlagZeroError(TestCcErrorTrapTtlError1):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=14, summary="Test CC IPv4 Control Flags Reserved = 1 Error",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 with Control Flags Reserved = 1 Error 
                                 under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic 
                              6. Dump all the stats in logs
                              7. Validate Tx == Rx on spirent and ensure no errors are seen.
                              8. Validate Tx == Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX  
                                  """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1,
                                         TRAFFIC_DURATION))

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']
        checkpoint = "Create a stream with EthernetII and IPv4 with Control Flags Reserved = 1 Error " \
                     "under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['destination_ip1'])
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Updated IPv4 Header")
        result = template_obj.stc_manager.update_control_flags(stream_block_obj=self.stream_obj,
                                                               header_obj=ipv4_header_obj, reserved=1)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = ERR_TRAP_COPP_PRSR_IP_FLAG_ZERO_METER_ID

    def run(self):
        super(TestCcIPv4FlagZeroError, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)


class TestCcIpv4Version6Error(TestCcErrorTrapTtlError1):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=15, summary="Test CC IPv4 Version 6 (Ver = 6) Error",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 with Version 6 (Ver = 6)  Error 
                                 under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic 
                              6. Dump all the stats in logs
                              7. Validate Tx == Rx on spirent and ensure no errors are seen.
                              8. Validate Tx == Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX  
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1,
                                     TRAFFIC_DURATION))

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']
        checkpoint = "Create a stream with EthernetII and IPv4 with Control Flags Reserved = 1 Error " \
                     "under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['destination_ip1'], version=6)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = ERR_TRAP_COPP_PRSR_V6_VER_METER_ID

    def run(self):
        super(TestCcIpv4Version6Error, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)


class TestCcCrcBadVerError(FunTestCase):
    stream_obj = None
    frame_size = 1500

    def describe(self):
        self.set_test_details(id=16, summary="Test CC IPv4 CRC Bad version error ",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 with CRC Bad version (version =2) error 
                                 under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic 
                              6. Dump all the stats in logs
                              7. Validate Tx != Rx on spirent and ensure CRC/Dropped Frame Count errors are seen.
                              8. Validate Tx != Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are not equal to spirent TX
                              10. From VP stats, validate VP total IN != VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be not equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be not equal to spirent TX  
                              """ % (port1, FRAME_LENGTH_MODE, self.frame_size, LOAD,
                                     LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and IPv4 with glean" \
                     "under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=self.frame_size,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['destination_ip1'], version=2)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)

    def run(self):
        vp_stats_before = None
        erp_stats_before = None
        wro_stats_before = None
        meter_stats_before = None

        if dut_config['enable_dpcsh']:
            checkpoint = "Clear FPG stats on all DUT ports"
            for port in dut_config['ports']:
                clear_stats = network_controller_obj.clear_port_stats(port_num=port)
                fun_test.simple_assert(clear_stats, "FPG stats clear on DUT port %d" % port)
            fun_test.add_checkpoint(checkpoint)

            checkpoint = "Get PSW and Parser NU stats before traffic"
            psw_stats = network_controller_obj.peek_psw_global_stats()
            parser_stats = network_controller_obj.peek_parser_stats()
            fun_test.log("PSW Stats: %s \n" % psw_stats)
            fun_test.log("Parser stats: %s \n" % parser_stats)
            fun_test.add_checkpoint(checkpoint)

            vp_stats_before = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)

            erp_stats_before = get_erp_stats_values(network_controller_obj=network_controller_obj)

            wro_stats_before = get_wro_global_stats_values(network_controller_obj=network_controller_obj)

            fun_test.log("VP stats: %s" % vp_stats_before)
            fun_test.log("ERP stats: %s" % erp_stats_before)
            fun_test.log("WRO stats: %s" % wro_stats_before)

        checkpoint = "Start traffic Traffic Duration: %d" % TRAFFIC_DURATION
        result = template_obj.enable_generator_configs([generator_handle])
        fun_test.test_assert(result, checkpoint)

        fun_test.sleep("Traffic to complete", seconds=DURATION_SECONDS)

        checkpoint = "Ensure Spirent stats fetched"
        tx_results = template_obj.stc_manager.get_tx_stream_block_results(stream_block_handle=self.stream_obj.
                                                                          spirent_handle,
                                                                          subscribe_handle=subscribed_results
                                                                          ['tx_subscribe'])

        rx_results = template_obj.stc_manager.get_rx_stream_block_results(stream_block_handle=self.stream_obj.
                                                                          spirent_handle,
                                                                          subscribe_handle=subscribed_results
                                                                          ['rx_subscribe'])
        tx_port_results = template_obj.stc_manager.get_generator_port_results(port_handle=port1,
                                                                              subscribe_handle=subscribed_results
                                                                              ['generator_subscribe'])
        rx_port_results = template_obj.stc_manager.get_rx_port_analyzer_results(port_handle=port2,
                                                                                subscribe_handle=subscribed_results
                                                                                ['analyzer_subscribe'])
        rx_port3_results = template_obj.stc_manager.get_rx_port_analyzer_results(port_handle=port3,
                                                                                 subscribe_handle=subscribed_results
                                                                                 ['analyzer_subscribe'])
        fun_test.simple_assert(tx_port_results and rx_port3_results and rx_port_results, checkpoint)

        fun_test.log("Tx Spirent Stats: %s" % tx_results)
        fun_test.log("Rx Spirent Stats: %s" % rx_results)
        fun_test.log("Tx Port Stats: %s" % tx_port_results)
        fun_test.log("Rx Port Stats: %s" % rx_port_results)
        fun_test.log("Rx Port 3 stats: %s" % rx_port3_results)

        dut_tx_port_stats = None
        dut_rx_port_stats = None
        vp_stats = None
        erp_stats = None
        wro_stats = None
        if dut_config['enable_dpcsh']:
            checkpoint = "Fetch PSW and Parser DUT stats after traffic"
            psw_stats = network_controller_obj.peek_psw_global_stats()
            parser_stats = network_controller_obj.peek_parser_stats()
            fun_test.log("PSW Stats: %s \n" % psw_stats)
            fun_test.log("Parser stats: %s \n" % parser_stats)
            fun_test.add_checkpoint(checkpoint)

            checkpoint = "Get FPG port stats for all ports"
            dut_tx_port_stats = network_controller_obj.peek_fpg_port_stats(port_num=dut_config['ports'][0])
            dut_rx_port_stats = network_controller_obj.peek_fpg_port_stats(port_num=dut_config['ports'][1])
            fun_test.simple_assert(dut_tx_port_stats and dut_rx_port_stats, checkpoint)

            fun_test.log("DUT Tx stats: %s" % dut_tx_port_stats)
            fun_test.log("DUT Rx stats: %s" % dut_rx_port_stats)

            checkpoint = "Fetch VP stats"
            vp_stats = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)
            fun_test.simple_assert(vp_stats, checkpoint)

            checkpoint = "Fetch ERP NU stats"
            erp_stats = get_erp_stats_values(network_controller_obj=network_controller_obj)
            fun_test.simple_assert(erp_stats, checkpoint)

            checkpoint = "Fetch WRO NU stats"
            wro_stats = get_wro_global_stats_values(network_controller_obj=network_controller_obj)
            fun_test.simple_assert(wro_stats, checkpoint)

            fun_test.log("VP stats: %s" % vp_stats)
            fun_test.log("ERP stats: %s" % erp_stats)
            fun_test.log("WRO stats: %s" % wro_stats)

        # validation asserts
        # Spirent stats validation
        checkpoint = "Validate Tx == Rx on spirent"
        fun_test.log("Tx Frame Count: %d Rx FrameCount: %d" % (int(tx_port_results['GeneratorFrameCount']),
                                                               int(rx_port3_results['TotalFrameCount'])))
        fun_test.test_assert((MIN_RX_PORT_COUNT <= int(rx_port3_results['TotalFrameCount']) <= MAX_RX_PORT_COUNT),
                             checkpoint)

        checkpoint = "Ensure no errors are seen on spirent"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_results)
        fun_test.test_assert(expression=result, message=checkpoint)

        # DUT stats validation
        if dut_config['enable_dpcsh']:
            checkpoint = "Validate Tx and Rx on DUT"
            frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_stats,
                                                            stat_type=FRAMES_RECEIVED_OK)
            frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_stats,
                                                         stat_type=FRAMES_TRANSMITTED_OK)
            fun_test.log("DUT Tx FrameCount: %s DUT Rx FrameCount: %s" % (str(frames_transmitted),
                                                                          str(frames_received)))
            fun_test.test_assert((MIN_RX_PORT_COUNT <= frames_received <= MAX_RX_PORT_COUNT),
                                 checkpoint)
            # VP stats validation
            checkpoint = "From VP stats, Ensure T2C header counter equal to spirent Tx counter"
            vp_stats_diff = get_diff_stats(old_stats=vp_stats_before, new_stats=vp_stats,
                                           stats_list=[VP_PACKETS_CONTROL_T2C_COUNT, VP_PACKETS_CC_OUT,
                                                       VP_PACKETS_TOTAL_OUT, VP_PACKETS_TOTAL_IN])
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=vp_stats_diff[VP_PACKETS_CONTROL_T2C_COUNT],
                                          message=checkpoint)
            checkpoint = "From VP stats, Ensure CC OUT counters are equal to spirent Tx Counter"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=vp_stats_diff[VP_PACKETS_CC_OUT],
                                          message=checkpoint)

            checkpoint = "Ensure VP total packets IN == VP total packets OUT"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=vp_stats_diff[VP_PACKETS_TOTAL_IN],
                                          message=checkpoint)
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=vp_stats_diff[VP_PACKETS_TOTAL_OUT],
                                          message=checkpoint)
            # ERP stats validation
            checkpoint = "From ERP stats, Ensure count for EFP to WQM decrement pulse equal to spirent Tx"
            erp_stats_diff = get_diff_stats(old_stats=erp_stats_before, new_stats=erp_stats,
                                            stats_list=[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED,
                                                        ERP_COUNT_FOR_EFP_WRO_DESCRIPTORS_SENT,
                                                        ERP_COUNT_FOR_EFP_WQM_DECREMENT_PULSE,
                                                        ERP_COUNT_FOR_ERP0_EFP_ERROR_INTERFACE_FLITS,
                                                        ERP_COUNT_FOR_EFP_FCP_VLD])
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=erp_stats_diff[ERP_COUNT_FOR_EFP_WQM_DECREMENT_PULSE],
                                          message=checkpoint)
            checkpoint = "From ERP stats, Ensure count for EFP to WRO descriptors send equal to spirent Tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=erp_stats_diff[ERP_COUNT_FOR_EFP_WRO_DESCRIPTORS_SENT],
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for ERP0 to EFP error interface flits equal to spirent Tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=erp_stats_diff[ERP_COUNT_FOR_ERP0_EFP_ERROR_INTERFACE_FLITS],
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for all non FCP packets received equal to spirent Tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=erp_stats_diff[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED],
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for EFP to FCB vld equal to spirent Tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=erp_stats_diff[ERP_COUNT_FOR_EFP_FCP_VLD],
                                          message=checkpoint)
            # WRO stats validation
            checkpoint = "From WRO stats, Ensure WRO IN packets equal to spirent Tx"
            wro_stats_diff = get_diff_stats(old_stats=wro_stats_before, new_stats=wro_stats)
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=wro_stats_diff['global'][WRO_IN_PKTS],
                                          message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO In NFCP packets equal to spirent Tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=wro_stats_diff['global'][WRO_IN_NFCP_PKTS],
                                          message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO out WUs equal to spirent tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=wro_stats_diff['global'][WRO_OUT_WUS],
                                          message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO WU CNT VPP packets equal to spirent tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=wro_stats_diff['global'][WRO_WU_COUNT_VPP],
                                          message=checkpoint)

    def cleanup(self):
        fun_test.log("In test case cleanup")
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)


class TestCcMultiError(TestCcIpChecksumError):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=17, summary="Test CC IPv4 Multiple Errors (checksum and ttl=5) ",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 Multiple Errors (checksum and ttl=5 ) 
                              under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic
                              6. Dump all the stats in logs
                              7. Validate Tx == Rx on spirent and ensure IPv4 Checksum error are seen.
                              8. Validate Tx == Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX   
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1,
                                     TRAFFIC_DURATION))

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and IPv4 Multiple Errors (checksum and ttl=5 ) under port %s" % \
                     port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['destination_ip1'],
                                     checksum=Ipv4Header.CHECKSUM_ERROR, ttl=5)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)

    def run(self):
        super(TestCcMultiError, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)


class TestCcErrorTrapsAllTogether(FunTestCase):

    def describe(self):
        self.set_test_details(id=18, summary="Test CC All Stream Together",
                              steps="""
                              1. Activate following streams
                                 1. Error Traps TTL Error 1
                                 2. Error Traps TTL Error 2
                                 3. Error Traps TTL Error 3
                                 4. Error Traps IP OPTS 1
                                 5. Error Traps IP OPTS 2
                                 6. IP Checksum Error
                                 7. Error Trap FSF
                                 8. Error Trap Outer Checksum error
                                 9. Error Trap Inner Checksum error
                                 10. Error Trap Parser Outerlay V4 Version
                                 11. Error Trap Parser Outerlay IHL
                                 12. Error Trap Parser v4 Version
                                 13. Error Trap Parser IHL
                                 14. Error Trap Parser IP Flag Zero
                                 15. Error Trap Parser V4 Version 6
                                 16. CRC Bad Version
                                 17. Error Trap Multiple Errors
                              2. Clear DUT stats before running traffic
                              3. Start Traffic run all streams together
                              4. Dump all the stats in logs
                              5. Validate Tx and Rx on spirent Rx should be in range of 80-90 pps and 
                                 ensure no errors are seen.
                              6. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              7. From VP stats, validate VP total IN == VP total OUT
                              8. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              9. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX   
                              10. Validate Meter stats
                              """)

    def setup(self):
        checkpoint = "Activate streams on spirent"
        result = template_obj.activate_stream_blocks(stream_obj_list=streams_group)
        fun_test.test_assert(result, checkpoint)

    def run(self):
        global MIN_RX_PORT_COUNT, MAX_RX_PORT_COUNT
        if dut_config['enable_dpcsh']:
            checkpoint = "Clear FPG stats on all DUT ports"
            for port in dut_config['ports']:
                clear_stats = network_controller_obj.clear_port_stats(port_num=port)
                fun_test.simple_assert(clear_stats, "FPG stats clear on DUT port %d" % port)
            fun_test.add_checkpoint(checkpoint)

            checkpoint = "Get PSW and Parser NU stats before traffic"
            psw_stats = network_controller_obj.peek_psw_global_stats()
            parser_stats = network_controller_obj.peek_parser_stats()
            fun_test.log("PSW Stats: %s \n" % psw_stats)
            fun_test.log("Parser stats: %s \n" % parser_stats)
            fun_test.add_checkpoint(checkpoint)

        checkpoint = "Start traffic Traffic Duration: %d" % TRAFFIC_DURATION
        result = template_obj.enable_generator_configs([generator_handle])
        fun_test.test_assert(result, checkpoint)

        fun_test.sleep("Traffic to complete", seconds=DURATION_SECONDS)

        checkpoint = "Ensure Spirent stats fetched"
        rx_port_results = template_obj.stc_manager.get_rx_port_analyzer_results(port_handle=port3,
                                                                                subscribe_handle=subscribed_results
                                                                                ['analyzer_subscribe'])
        rx_port2_results = template_obj.stc_manager.get_rx_port_analyzer_results(port_handle=port2,
                                                                                 subscribe_handle=subscribed_results
                                                                                 ['analyzer_subscribe'])
        tx_port_results = template_obj.stc_manager.get_generator_port_results(port_handle=port1,
                                                                              subscribe_handle=subscribed_results
                                                                              ['generator_subscribe'])
        fun_test.simple_assert(rx_port_results and tx_port_results and rx_port2_results, checkpoint)

        fun_test.log("Tx Port Stats: %s" % tx_port_results)
        fun_test.log("Rx Port Stats: %s" % rx_port_results)
        fun_test.log("Rx Port 2 Stats: %s" % rx_port2_results)

        dut_tx_port_stats = None
        dut_rx_port_stats = None
        vp_stats = None
        erp_stats = None
        wro_stats = None
        if dut_config['enable_dpcsh']:
            checkpoint = "Fetch PSW and Parser DUT stats after traffic"
            psw_stats = network_controller_obj.peek_psw_global_stats()
            parser_stats = network_controller_obj.peek_parser_stats()
            fun_test.log("PSW Stats: %s \n" % psw_stats)
            fun_test.log("Parser stats: %s \n" % parser_stats)
            fun_test.add_checkpoint(checkpoint)

            checkpoint = "Get FPG port stats for all ports"
            dut_tx_port_stats = network_controller_obj.peek_fpg_port_stats(port_num=dut_config['ports'][0])
            dut_rx_port_stats = network_controller_obj.peek_fpg_port_stats(port_num=dut_config['ports'][2])
            fun_test.simple_assert(dut_tx_port_stats and dut_rx_port_stats, checkpoint)

            fun_test.log("DUT Tx stats: %s" % dut_tx_port_stats)
            fun_test.log("DUT Rx stats: %s" % dut_rx_port_stats)

            checkpoint = "Fetch VP stats"
            vp_stats = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)
            fun_test.simple_assert(vp_stats, checkpoint)

            checkpoint = "Fetch ERP NU stats"
            erp_stats = get_erp_stats_values(network_controller_obj=network_controller_obj)
            fun_test.simple_assert(erp_stats, checkpoint)

            checkpoint = "Fetch WRO NU stats"
            wro_stats = get_wro_global_stats_values(network_controller_obj=network_controller_obj)
            fun_test.simple_assert(wro_stats, checkpoint)

            fun_test.log("VP stats: %s" % vp_stats)
            fun_test.log("ERP stats: %s" % erp_stats)
            fun_test.log("WRO stats: %s" % wro_stats)

        # validation asserts
        # Spirent stats validation
        MIN_RX_PORT_COUNT = 500 * len(streams_group)
        MAX_RX_PORT_COUNT = 600 * len(streams_group)
        checkpoint = "Validate Tx and Rx on spirent. Ensure Rx Port counter should be in a range of %d - %d" % (
            MIN_RX_PORT_COUNT, MAX_RX_PORT_COUNT)
        fun_test.log("Tx FrameCount: %d Rx FrameCount: %d" % (int(tx_port_results['GeneratorFrameCount']),
                                                              int(rx_port_results['TotalFrameCount'])))
        fun_test.test_assert((MIN_RX_PORT_COUNT <= int(rx_port_results['TotalFrameCount']) <= MAX_RX_PORT_COUNT),
                             checkpoint)

        checkpoint = "Ensure %s does not received any frames" % port2
        fun_test.log("Rx Port2 FrameCount: %d" % int(rx_port2_results['TotalFrameCount']))
        fun_test.test_assert_expected(expected=0, actual=int(rx_port2_results['TotalFrameCount']),
                                      message=checkpoint)

        checkpoint = "Ensure no errors are seen on spirent"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_results)
        fun_test.test_assert(expression=result['result'], message=checkpoint)

        # DUT stats validation
        if dut_config['enable_dpcsh']:
            checkpoint = "Validate Tx and Rx on DUT"
            frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_stats,
                                                            stat_type=FRAMES_TRANSMITTED_OK)
            frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_stats,
                                                         stat_type=FRAMES_RECEIVED_OK)
            fun_test.log("DUT Tx FrameCount: %d DUT Rx FrameCount: %d" % (frames_transmitted, frames_received))
            fun_test.test_assert((MIN_RX_PORT_COUNT <= frames_received <= MAX_RX_PORT_COUNT),
                                 checkpoint)
            # VP stats validation
            checkpoint = "From VP stats, Ensure T2C header counter equal to spirent Tx counter"
            fun_test.test_assert_expected(expected=int(tx_port_results['GeneratorFrameCount']),
                                          actual=int(vp_stats[VP_PACKETS_CONTROL_T2C_COUNT]), message=checkpoint)

            checkpoint = "From VP stats, Ensure CC OUT counters are equal to spirent Tx Counter"
            fun_test.test_assert_expected(expected=int(tx_port_results['GeneratorFrameCount']),
                                          actual=int(vp_stats[VP_PACKETS_CC_OUT]), message=checkpoint)

            checkpoint = "Ensure VP total packets IN == VP total packets OUT"
            fun_test.test_assert_expected(expected=int(vp_stats[VP_PACKETS_TOTAL_IN]),
                                          actual=int(vp_stats[VP_PACKETS_TOTAL_OUT]),
                                          message=checkpoint)
            # ERP stats validation
            checkpoint = "From ERP stats, Ensure count for EFP to WQM decrement pulse equal to spirent Tx"
            fun_test.test_assert_expected(expected=int(tx_port_results['GeneratorFrameCount']),
                                          actual=int(erp_stats[ERP_COUNT_FOR_EFP_WQM_DECREMENT_PULSE]),
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for EFP to WRO descriptors send equal to spirent Tx"
            fun_test.test_assert_expected(expected=int(tx_port_results['GeneratorFrameCount']),
                                          actual=int(erp_stats[ERP_COUNT_FOR_EFP_WRO_DESCRIPTORS_SENT]),
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for ERP0 to EFP error interface flits equal to spirent Tx"
            fun_test.test_assert_expected(expected=int(tx_port_results['GeneratorFrameCount']),
                                          actual=int(erp_stats[ERP_COUNT_FOR_ERP0_EFP_ERROR_INTERFACE_FLITS]),
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for all non FCP packets received equal to spirent Tx"
            fun_test.test_assert_expected(expected=int(tx_port_results['GeneratorFrameCount']),
                                          actual=int(erp_stats[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED]),
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for EFP to FCB vld equal to spirent Tx"
            fun_test.test_assert_expected(expected=int(tx_port_results['GeneratorFrameCount']),
                                          actual=int(erp_stats[ERP_COUNT_FOR_EFP_FCP_VLD]),
                                          message=checkpoint)
            # WRO stats validation
            checkpoint = "From WRO stats, Ensure WRO IN packets equal to spirent Tx"
            fun_test.test_assert_expected(expected=int(tx_port_results['GeneratorFrameCount']),
                                          actual=wro_stats[WRO_IN_NFCP_PKTS], message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO In NFCP packets equal to spirent Tx"
            fun_test.test_assert_expected(expected=int(tx_port_results['GeneratorFrameCount']),
                                          actual=wro_stats[WRO_IN_NFCP_PKTS], message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO In packets equal to spirent tx"
            fun_test.test_assert_expected(expected=int(tx_port_results['GeneratorFrameCount']),
                                          actual=int(wro_stats[WRO_IN_PKTS]), message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO out WUs equal to spirent tx"
            fun_test.test_assert_expected(expected=int(tx_port_results['GeneratorFrameCount']),
                                          actual=int(wro_stats[WRO_OUT_WUS]), message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO WU CNT VPP packets equal to spirent tx"
            fun_test.test_assert_expected(expected=int(tx_port_results['GeneratorFrameCount']),
                                          actual=int(wro_stats[WRO_WU_COUNT_VPP]), message=checkpoint)

    def cleanup(self):
        pass


if __name__ == '__main__':
    cc_flow_type = nu_config_obj.get_local_settings_parameters(flow_direction=True)
    FLOW_DIRECTION = cc_flow_type[nu_config_obj.FLOW_DIRECTION]

    ts = SetupSpirent()
    ts.add_test_case(TestCcErrorTrapTtlError1())
    ts.add_test_case(TestCcErrorTrapTtlError2())
    ts.add_test_case(TestCcErrorTrapTtlError3())

    # TODO: Commented out this cases as it is causing a system to crash which is affecting further cases.
    # TODO: once fixed uncomment this
    if FLOW_DIRECTION != "HU_CC":
        ts.add_test_case(TestCcIpv4ErrorTrapIpOpts1())
        ts.add_test_case(TestCcIpv4ErrorTrapIpOpts2())

    ts.add_test_case(TestCcIpChecksumError())

    ts.add_test_case(TestCcFSFError())

    ts.add_test_case(TestCcOuterChecksumError())

    ts.add_test_case(TestCcInnerChecksumError())
    ts.add_test_case(TestCcIPv4OverlayVersionError())
    ts.add_test_case(TestCcIPv4OverlayIhlError())

    ts.add_test_case(TestCcIPv4VersionError())
    ts.add_test_case(TestCcIPv4InternetHeaderLengthError())
    ts.add_test_case(TestCcIPv4FlagZeroError())

    ts.add_test_case(TestCcIpv4Version6Error())
    ts.add_test_case(TestCcCrcBadVerError())
    ts.add_test_case(TestCcMultiError())

    ts.add_test_case(TestCcErrorTrapsAllTogether())

    ts.run()