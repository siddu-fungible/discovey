from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import *
from lib.host.network_controller import NetworkController
from nu_config_manager import *
from helper import *

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
FLOW_DIRECTION = NuConfigManager.FLOW_DIRECTION_FPG_CC


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
        MIN_RX_PORT_COUNT = cc_path_config['rx_range_min']
        MAX_RX_PORT_COUNT = cc_path_config['rx_range_max']
        LOAD_UNIT = cc_path_config['load_unit']
        FRAME_SIZE = cc_path_config['frame_size']
        FRAME_LENGTH_MODE = cc_path_config['frame_length_mode']
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


class TestCcEthernetArpRequest(FunTestCase):
    stream_obj = None
    validate_meter_stats = True
    meter_id = None

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test CC Ethernet ARP Request",
                              steps="""
                              1. Create a stream with EthernetII and ARP headers under port %s
                                 a. Frame Size Mode: %s Frame Size %d
                                 b. Load: %d Load Unit: %s
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
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1,
                                     TRAFFIC_DURATION))

    def setup(self):
        checkpoint = "Configure a stream with EthernetII and ARP headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

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
        streams_group.append(self.stream_obj)
        self.meter_id = ETH_COPP_ARP_REQ_METER_ID

    def run(self):
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

            checkpoint = "Fetch Meter stats for meter id: %d" % self.meter_id
            meter_stats = network_controller_obj.peek_meter_stats_by_id(meter_id=self.meter_id)
            fun_test.simple_assert(meter_stats, checkpoint)

            fun_test.log("VP stats: %s" % vp_stats)
            fun_test.log("ERP stats: %s" % erp_stats)
            fun_test.log("WRO stats: %s" % wro_stats)
            fun_test.log("METER stats for id %d : %s" % (self.meter_id, meter_stats))

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
            fun_test.test_assert((MIN_RX_PORT_COUNT <= frames_transmitted <= MAX_RX_PORT_COUNT),
                                 checkpoint)
            # VP stats validation
            checkpoint = "From VP stats, Ensure T2C header counter equal to spirent Tx counter"
            fun_test.test_assert((MIN_RX_PORT_COUNT <= int(vp_stats[VP_PACKETS_CONTROL_T2C_COUNT]) <= MAX_RX_PORT_COUNT),
                                 checkpoint)

            checkpoint = "From VP stats, Ensure CC OUT counters are equal to spirent Tx Counter"
            fun_test.test_assert(
                (MIN_RX_PORT_COUNT <= int(vp_stats[VP_PACKETS_CC_OUT]) <= MAX_RX_PORT_COUNT),
                checkpoint)

            checkpoint = "Ensure VP total packets IN == VP total packets OUT"
            fun_test.test_assert_expected(expected=int(vp_stats[VP_PACKETS_TOTAL_IN]),
                                          actual=int(vp_stats[VP_PACKETS_TOTAL_OUT]),
                                          message=checkpoint)
            # ERP stats validation
            checkpoint = "From ERP stats, Ensure count for EFP to WQM decrement pulse equal to spirent Tx"
            fun_test.test_assert(
                (MIN_RX_PORT_COUNT <= int(erp_stats[ERP_COUNT_FOR_EFP_WQM_DECREMENT_PULSE]) <= MAX_RX_PORT_COUNT),
                checkpoint)

            checkpoint = "From ERP stats, Ensure count for EFP to WRO descriptors send equal to spirent Tx"
            fun_test.test_assert(
                (MIN_RX_PORT_COUNT <= int(erp_stats[ERP_COUNT_FOR_EFP_WRO_DESCRIPTORS_SENT]) <= MAX_RX_PORT_COUNT),
                checkpoint)

            checkpoint = "From ERP stats, Ensure count for ERP0 to EFP error interface flits equal to spirent Tx"
            fun_test.test_assert(
                (MIN_RX_PORT_COUNT <= int(erp_stats[ERP_COUNT_FOR_ERP0_EFP_ERROR_INTERFACE_FLITS]) <= MAX_RX_PORT_COUNT),
                checkpoint)

            checkpoint = "From ERP stats, Ensure count for all non FCP packets received equal to spirent Tx"
            fun_test.test_assert(
                (MIN_RX_PORT_COUNT <= int(erp_stats[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED]) <= MAX_RX_PORT_COUNT),
                checkpoint)

            checkpoint = "From ERP stats, Ensure count for EFP to FCB vld equal to spirent Tx"
            fun_test.test_assert(
                (MIN_RX_PORT_COUNT <= int(erp_stats[ERP_COUNT_FOR_EFP_FCP_VLD]) <= MAX_RX_PORT_COUNT),
                checkpoint)

            # WRO stats validation
            checkpoint = "From WRO stats, Ensure WRO IN packets equal to spirent Tx"
            fun_test.test_assert(
                (MIN_RX_PORT_COUNT <= int(wro_stats[WRO_IN_PKTS]) <= MAX_RX_PORT_COUNT),
                checkpoint)

            checkpoint = "From WRO stats, Ensure WRO In NFCP packets equal to spirent Tx"
            fun_test.test_assert(
                (MIN_RX_PORT_COUNT <= int(wro_stats[WRO_IN_NFCP_PKTS]) <= MAX_RX_PORT_COUNT),
                checkpoint)

            checkpoint = "From WRO stats, Ensure WRO out WUs equal to spirent tx"
            fun_test.test_assert(
                (MIN_RX_PORT_COUNT <= int(wro_stats[WRO_OUT_WUS]) <= MAX_RX_PORT_COUNT),
                checkpoint)

            checkpoint = "From WRO stats, Ensure WRO WU CNT VPP packets equal to spirent tx"
            fun_test.test_assert(
                (MIN_RX_PORT_COUNT <= int(wro_stats[WRO_WU_COUNT_VPP]) <= MAX_RX_PORT_COUNT),
                checkpoint)

            if self.validate_meter_stats:
                checkpoint = "Validate meter stats ensure frames_received == (green pkts + yellow pkts)"
                green_pkts = int(meter_stats['green']['pkts'])
                yellow_pkts = int(meter_stats['yellow']['pkts'])
                red_pkts = int(meter_stats['red']['pkts'])
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


class TestCcEthernetArpResponse(TestCcEthernetArpRequest):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=2,
                              summary="Test CC Ethernet ARP Response",
                              steps="""
                              1. Create a stream with EthernetII and ARP headers under port %s
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
        l2_config = spirent_config['l2_config']
        checkpoint = "Configure a stream with EthernetII and ARP headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.ARP_ETHERTYPE)
        arp_obj = ARP()

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=arp_obj, update=False,
                                                                delete_header=[Ipv4Header.HEADER_TYPE])
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = ETH_COPP_ARP_RESP_METER_ID

    def run(self):
        super(TestCcEthernetArpResponse, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)


class TestCcEthernetRarp(TestCcEthernetArpRequest):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=3, summary="Test CC Ethernet RARP (Reverse-ARP)",
                              steps="""
                              1. Create a stream with EthernetII and RARP headers under port %s
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
        checkpoint = "Configure stream with EthernetII and RARP headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.BROADCAST_MAC,
                                    ether_type=Ethernet2Header.RARP_ETHERTYPE)
        rarp_obj = RARP()

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=rarp_obj, update=False,
                                                                delete_header=[Ipv4Header.HEADER_TYPE])
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = ETH_COPP_RARP_METER_ID

    def run(self):
        super(TestCcEthernetRarp, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)


class TestCcEthernetLLDP(TestCcEthernetArpRequest):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=4, summary="Test CC Ethernet LLDP (Link Layer Discovery Protocol)",
                              steps="""
                              1. Create a stream with EthernetII (EtherType - 88CC)under port %s
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
        checkpoint = "Create a stream with EthernetII (EtherType - 88CC)under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.LLDP_MULTICAST_MAC,
                                    ether_type=Ethernet2Header.LLDP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        result = template_obj.stc_manager.delete_frame_headers(stream_block_handle=self.stream_obj.spirent_handle,
                                                               header_types=[Ipv4Header.HEADER_TYPE])
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = ETH_COPP_LLDP_METER_ID

    def run(self):
        super(TestCcEthernetLLDP, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)


class TestCcEthernetPTP(TestCcEthernetArpRequest):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=5, summary="Test CC Ethernet PTP (Precision Time Protocol)",
                              steps="""
                              1. Create a stream with EthernetII and PTP headers under port %s
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
        l2_config = spirent_config['l2_config']

        checkpoint = "Create a stream with EthernetII and PTP headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)

        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.PTP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ptp_header_obj = PtpFollowUpHeader(control_field=PtpFollowUpHeader.CONTROL_FIELD_FOLLOW_UP,
                                           message_type=PtpFollowUpHeader.MESSAGE_TYPE_FOLLOW_UP)

        result = template_obj.configure_ptp_header(stream_block_handle=self.stream_obj.spirent_handle,
                                                   header_obj=ptp_header_obj, create_header=True)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = ETH_COPP_PTP_METER_ID

    def run(self):
        super(TestCcEthernetPTP, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)


class TestCcEthArpRequestUnicast(TestCcEthernetArpRequest):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=6, summary="Test CC Ethernet ARP Request Unicast ",
                              steps="""
                              1. Create a stream with EthernetII and ARP header option under port %s
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
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and ARP header option under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.ARP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        arp_header_obj = ARP(target_ip_address=l3_config['cc_destination_ip1'], operation=ARP.ARP_OPERATION_REQUEST)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=arp_header_obj, update=False)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.validate_meter_stats = False

    def run(self):
        super(TestCcEthArpRequestUnicast, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)


class TestCcEthernetIsis1(TestCcEthernetArpRequest):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=7, summary="Test CC IPv4 ISIS_1",
                              steps="""
                              1. Create a stream with EthernetII under port %s
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
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1,
                                     TRAFFIC_DURATION))

    def setup(self):
        checkpoint = "Create a stream with EthernetII under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.ISIS_MULTICAST_MAC_1,
                                    ether_type=Ethernet2Header.X25_LEVEL_3_ETHERTYPE)
        ipv4_header_obj = Ipv4Header()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header")
        result = template_obj.stc_manager.delete_frame_headers(header_types=[ipv4_header_obj.HEADER_TYPE],
                                                               stream_block_handle=self.stream_obj.spirent_handle)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = ETH_COPP_ISIS_1_METER_ID

    def run(self):
        super(TestCcEthernetIsis1, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)


class TestCcEthernetIsis2(TestCcEthernetArpRequest):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=8, summary="Test CC IPv4 ISIS_2",
                              steps="""
                              1. Create a stream with EthernetII under port %s
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
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1,
                                     TRAFFIC_DURATION))

    def setup(self):
        checkpoint = "Create a stream with EthernetII and  IPv4 headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ipv4_header_obj = Ipv4Header()
        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.ISIS_MULTICAST_MAC_2,
                                    ether_type=Ethernet2Header.X25_LEVEL_3_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header")
        result = template_obj.stc_manager.delete_frame_headers(header_types=[ipv4_header_obj.HEADER_TYPE],
                                                               stream_block_handle=self.stream_obj.spirent_handle)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = ETH_COPP_ISIS_2_METER_ID

    def run(self):
        super(TestCcEthernetIsis2, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)


class TestCcGlean(TestCcEthernetArpRequest):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=9, summary="Test CC IPv4 Glean ",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 with glean
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
                              7. Validate Tx and Rx on spirent and ensure no errors are seen.
                              8. Validate Tx and Rx on DUT
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

        checkpoint = "Create a stream with EthernetII and IPv4 with glean" \
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

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['cc_glean_ip1'])
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.validate_meter_stats = False

    def run(self):
        super(TestCcGlean, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)


class TestCcEthernetAllTogether(FunTestCase):

    def describe(self):
        self.set_test_details(id=10, summary="Test CC All Streams Together",
                              steps="""
                              1. Activate following streams
                                 1. Ethernet ARP Request
                                 2. Ethernet ARP Response
                                 3. Ethernet Reverse-ARP
                                 4. Ethernet LLDP
                                 5. Ethernet PTP
                                 6. Ethernet ARP Request Unicast
                                 7. Ethernet ISIS1
                                 8. Ethernet ISIS2
                                 9. Glean
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
        MIN_RX_PORT_COUNT = 200 * len(streams_group)
        MAX_RX_PORT_COUNT = 400 * len(streams_group)
        checkpoint = "Validate Tx and Rx on spirent. Ensure Rx Port counter should be in a range of %d - %d pps" % (
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
            fun_test.log(
                "DUT Tx FrameCount: %s DUT Rx FrameCount: %s" % (str(frames_transmitted), str(frames_received)))
            fun_test.test_assert((MIN_RX_PORT_COUNT <= frames_transmitted <= MAX_RX_PORT_COUNT),
                                 checkpoint)
            # VP stats validation
            checkpoint = "From VP stats, Ensure T2C header counter equal to spirent Tx counter"
            fun_test.test_assert(
                (MIN_RX_PORT_COUNT <= int(vp_stats[VP_PACKETS_CONTROL_T2C_COUNT]) <= MAX_RX_PORT_COUNT),
                checkpoint)

            checkpoint = "From VP stats, Ensure CC OUT counters are equal to spirent Tx Counter"
            fun_test.test_assert(
                (MIN_RX_PORT_COUNT <= int(vp_stats[VP_PACKETS_CC_OUT]) <= MAX_RX_PORT_COUNT),
                checkpoint)

            checkpoint = "Ensure VP total packets IN == VP total packets OUT"
            fun_test.test_assert_expected(expected=int(vp_stats[VP_PACKETS_TOTAL_IN]),
                                          actual=int(vp_stats[VP_PACKETS_TOTAL_OUT]),
                                          message=checkpoint)
            # ERP stats validation
            checkpoint = "From ERP stats, Ensure count for EFP to WQM decrement pulse equal to spirent Tx"
            fun_test.test_assert(
                (MIN_RX_PORT_COUNT <= int(erp_stats[ERP_COUNT_FOR_EFP_WQM_DECREMENT_PULSE]) <= MAX_RX_PORT_COUNT),
                checkpoint)

            checkpoint = "From ERP stats, Ensure count for EFP to WRO descriptors send equal to spirent Tx"
            fun_test.test_assert(
                (MIN_RX_PORT_COUNT <= int(erp_stats[ERP_COUNT_FOR_EFP_WRO_DESCRIPTORS_SENT]) <= MAX_RX_PORT_COUNT),
                checkpoint)

            checkpoint = "From ERP stats, Ensure count for ERP0 to EFP error interface flits equal to spirent Tx"
            fun_test.test_assert(
                (MIN_RX_PORT_COUNT <= int(
                    erp_stats[ERP_COUNT_FOR_ERP0_EFP_ERROR_INTERFACE_FLITS]) <= MAX_RX_PORT_COUNT),
                checkpoint)

            checkpoint = "From ERP stats, Ensure count for all non FCP packets received equal to spirent Tx"
            fun_test.test_assert(
                (MIN_RX_PORT_COUNT <= int(erp_stats[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED]) <= MAX_RX_PORT_COUNT),
                checkpoint)

            checkpoint = "From ERP stats, Ensure count for EFP to FCB vld equal to spirent Tx"
            fun_test.test_assert(
                (MIN_RX_PORT_COUNT <= int(erp_stats[ERP_COUNT_FOR_EFP_FCP_VLD]) <= MAX_RX_PORT_COUNT),
                checkpoint)

            # WRO stats validation
            checkpoint = "From WRO stats, Ensure WRO IN packets equal to spirent Tx"
            fun_test.test_assert(
                (MIN_RX_PORT_COUNT <= int(wro_stats[WRO_IN_PKTS]) <= MAX_RX_PORT_COUNT),
                checkpoint)

            checkpoint = "From WRO stats, Ensure WRO In NFCP packets equal to spirent Tx"
            fun_test.test_assert(
                (MIN_RX_PORT_COUNT <= int(wro_stats[WRO_IN_NFCP_PKTS]) <= MAX_RX_PORT_COUNT),
                checkpoint)

            checkpoint = "From WRO stats, Ensure WRO out WUs equal to spirent tx"
            fun_test.test_assert(
                (MIN_RX_PORT_COUNT <= int(wro_stats[WRO_OUT_WUS]) <= MAX_RX_PORT_COUNT),
                checkpoint)

            checkpoint = "From WRO stats, Ensure WRO WU CNT VPP packets equal to spirent tx"
            fun_test.test_assert(
                (MIN_RX_PORT_COUNT <= int(wro_stats[WRO_WU_COUNT_VPP]) <= MAX_RX_PORT_COUNT),
                checkpoint)

    def cleanup(self):
        fun_test.log("In test case cleanup")
        pass


if __name__ == '__main__':
    cc_flow_type = fun_test.get_local_setting(setting="cc_flow")
    flow_type = cc_flow_type if cc_flow_type else "FPG_CC"
    fun_test.log("<---------------> Validating %s Flow Direction <--------------->" % flow_type)
    FLOW_DIRECTION = flow_type

    ts = SetupSpirent()
    # Ethernet CC
    ts.add_test_case(TestCcEthernetArpRequest())
    ts.add_test_case(TestCcEthernetArpResponse())
    
    ts.add_test_case(TestCcEthernetRarp())
    ts.add_test_case(TestCcEthernetLLDP())
    ts.add_test_case(TestCcEthernetPTP())

    # Unicast CC
    ts.add_test_case(TestCcEthArpRequestUnicast())

    ts.add_test_case(TestCcEthernetIsis1())
    ts.add_test_case(TestCcEthernetIsis2())

    # Glean
    ts.add_test_case(TestCcGlean())

    # All together
    ts.add_test_case(TestCcEthernetAllTogether())

    ts.run()
