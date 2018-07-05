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
TRAFFIC_DURATION = 10
cc_path_config = {}
LOAD = 81
LOAD_UNIT = StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND
FRAME_SIZE = 128
FRAME_LENGTH_MODE = StreamBlock.FRAME_LENGTH_MODE_FIXED
INTERFACE_LOADS_SPEC = SCRIPTS_DIR + "/networking" + "/interface_loads.json"
NUM_PORTS = 3
FLOW_DIRECTION = NuConfigManager.FLOW_DIRECTION_FPG_CC


class SetupSpirent(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Check health of Spirent. Connect to Lab server
        2. Create ports and attach ports
        3. Read configs 
        4. In cleanup, disconnect session 
        """)

    def setup(self):
        fun_test.log("In script setup")
        global template_obj, dut_config, spirent_config, network_controller_obj, port1, port2, cc_path_config, \
            interface_obj1, interface_obj2
        global LOAD, LOAD_UNIT, FRAME_SIZE, FRAME_LENGTH_MODE

        dut_type = fun_test.get_local_setting('dut_type')
        dut_config = nu_config_obj.read_dut_config(dut_type=dut_type, flow_type=NuConfigManager.CC_FLOW_TYPE,
                                                   flow_direction=FLOW_DIRECTION)

        chassis_type = fun_test.get_local_setting('chassis_type')
        spirent_config = nu_config_obj.read_traffic_generator_config()

        template_obj = SpirentEthernetTrafficTemplate(session_name="cc_path", spirent_config=spirent_config,
                                                      chassis_type=chassis_type)
        result = template_obj.setup(no_of_ports_needed=NUM_PORTS, flow_type=NuConfigManager.CC_FLOW_TYPE,
                                    flow_direction=NuConfigManager.FLOW_DIRECTION_FPG_CC)
        fun_test.test_assert(result['result'], "Ensure Spirent Setup done")

        port1 = result['port_list'][0]
        port2 = result['port_list'][1]

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

    def cleanup(self):
        fun_test.log("In script cleanup")
        template_obj.cleanup()


class TestCcEthernetArpRequest(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

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
        checkpoint = "Configure a stream with EthernetII and ARP headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=40, load_unit=LOAD_UNIT)
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

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
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
        result = template_obj.enable_generator_configs([self.generator_handle])
        fun_test.test_assert(result, checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION)

        checkpoint = "Ensure Spirent stats fetched"
        tx_results = template_obj.stc_manager.get_tx_stream_block_results(stream_block_handle=self.stream_obj.
                                                                          spirent_handle,
                                                                          subscribe_handle=self.subscribed_results
                                                                          ['tx_subscribe'])

        rx_results = template_obj.stc_manager.get_rx_stream_block_results(stream_block_handle=self.stream_obj.
                                                                          spirent_handle,
                                                                          subscribe_handle=self.subscribed_results
                                                                          ['rx_subscribe'])
        rx_port_results = template_obj.stc_manager.get_rx_port_analyzer_results(port_handle=port1,
                                                                                subscribe_handle=self.subscribed_results
                                                                                ['analyzer_subscribe'])
        fun_test.simple_assert(tx_results and rx_results and rx_port_results, checkpoint)

        fun_test.log("Tx Spirent Stats: %s" % tx_results)
        fun_test.log("Rx Spirent Stats: %s" % rx_results)
        fun_test.log("Rx Port Stats: %s" % rx_port_results)

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
        checkpoint = "Validate Tx == Rx on spirent"
        fun_test.test_assert_expected(expected=int(tx_results['FrameCount']), actual=int(rx_results['FrameCount']),
                                      message=checkpoint)

        checkpoint = "Ensure no errors are seen on spirent"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_results)
        fun_test.test_assert(expression=result['result'], message=checkpoint)

        # DUT stats validation
        if dut_config['enable_dpcsh']:
            checkpoint = "Validate Tx == Rx on DUT"
            frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_stats,
                                                            stat_type=FRAMES_TRANSMITTED_OK)
            frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_stats,
                                                         stat_type=FRAMES_RECEIVED_OK)

            fun_test.test_assert_expected(expected=frames_transmitted, actual=frames_received,
                                          message=checkpoint)
            # VP stats validation
            checkpoint = "From VP stats, Ensure T2C header counter equal to spirent Tx counter"
            fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                          actual=int(vp_stats[VP_PACKETS_CONTROL_T2C_COUNT]), message=checkpoint)

            checkpoint = "From VP stats, Ensure CC OUT counters are equal to spirent Tx Counter"
            fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                          actual=int(vp_stats[VP_PACKETS_CC_OUT]), message=checkpoint)

            checkpoint = "Ensure VP total packets IN == VP total packets OUT"
            fun_test.test_assert_expected(expected=int(vp_stats[VP_PACKETS_TOTAL_IN]),
                                          actual=int(vp_stats[VP_PACKETS_TOTAL_OUT]),
                                          message=checkpoint)
            # ERP stats validation
            checkpoint = "From ERP stats, Ensure count for EFP to WQM decrement pulse equal to spirent Tx"
            fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                          actual=int(erp_stats[ERP_COUNT_FOR_EFP_WQM_DECREMENT_PULSE]),
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for EFP to WRO descriptors send equal to spirent Tx"
            fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                          actual=int(erp_stats[ERP_COUNT_FOR_EFP_WRO_DESCRIPTORS_SENT]),
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for ERP0 to EFP error interface flits equal to spirent Tx"
            fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                          actual=int(erp_stats[ERP_COUNT_FOR_ERP0_EFP_ERROR_INTERFACE_FLITS]),
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for all non FCP packets received equal to spirent Tx"
            fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                          actual=int(erp_stats[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED]),
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for EFP to FCB vld equal to spirent Tx"
            fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                          actual=int(erp_stats[ERP_COUNT_FOR_EFP_FCP_VLD]),
                                          message=checkpoint)
            # WRO stats validation
            checkpoint = "From WRO stats, Ensure WRO IN packets equal to spirent Tx"
            fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                          actual=wro_stats[WRO_IN_NFCP_PKTS], message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO In NFCP packets equal to spirent Tx"
            fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                          actual=wro_stats[WRO_IN_NFCP_PKTS], message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO In packets equal to spirent tx"
            fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                          actual=int(wro_stats[WRO_IN_PKTS]), message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO out WUs equal to spirent tx"
            fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                          actual=int(wro_stats[WRO_OUT_WUS]), message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO WU CNT VPP packets equal to spirent tx"
            fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                          actual=int(wro_stats[WRO_WU_COUNT_VPP]), message=checkpoint)

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcEthernetArpResponse(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

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
        checkpoint = "Configure a stream with EthernetII and ARP headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=41, load_unit=LOAD_UNIT)
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

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcEthernetArpResponse, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcEthernetRarp(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

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

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcEthernetRarp, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcEthernetLLDP(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

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
        checkpoint = "Configure stream with EthernetII under port %s" % port1
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

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcEthernetLLDP, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcEthernetPTP(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

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

        checkpoint = "Configure stream with EthernetII under port %s" % port1
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

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcEthernetPTP, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4ICMP(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=6, summary="Test CC IPv4 ICMP (Internet Control Message Protocol)",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and ICMP Echo Request 
                                 headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              4. Start traffic
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

        checkpoint = "Configure stream with EthernetII, IPv4 and ICMP Echo Request under port %s" % port1
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

        ipv4_header_obj = Ipv4Header(protocol=Ipv4Header.PROTOCOL_TYPE_ICMP, destination_address="20.1.1.2")
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        icmp_echo_req_obj = IcmpEchoRequestHeader()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=icmp_echo_req_obj, update=False)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIPv4ICMP, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4Ospfv2Hello(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=7, summary="Test CC IPv4 OSPF V2 Hello (Open Shortest Path First)",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and OSPFv2 Hello headers under port %s
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
        checkpoint = "Create a stream with EthernetII and IPv4 and OSPFv2 Hello headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)

        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.OSPF_MULTICAST_MAC_1,
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(protocol=Ipv4Header.PROTOCOL_TYPE_OSPFIGP,
                                     destination_address=Ipv4Header.OSPF_MULTICAST_IP_1)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        ospf_header_obj = Ospfv2HelloHeader()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ospf_header_obj, update=False)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIPv4Ospfv2Hello, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4Ospfv2LinkStateUpdate(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=8, summary="Test CC IPv4 OSPF V2 Link State Update (Open Shortest Path First)",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and OSPFv2 Link State Update 
                                 headers under port %s
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
        checkpoint = "Create a stream with EthernetII and IPv4 and OSPFv2 Link State Update headers under port %s" % \
                     port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.OSPF_MULTICAST_MAC_2,
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(protocol=Ipv4Header.PROTOCOL_TYPE_OSPFIGP,
                                     destination_address=Ipv4Header.OSPF_MULTICAST_IP_2)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        ospf_header_obj = Ospfv2LinkStateUpdateHeader()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ospf_header_obj, update=False)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIPv4Ospfv2LinkStateUpdate, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIpv4Pim(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=9, summary="Test CC IPv4 PIM (Protocol Independent Multicast)",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and PIMv4Hello
                                 headers under port %s
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
        checkpoint = "Create a stream with EthernetII and IPv4 and PIMv4Hello headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)

        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.PIM_MULTICAST_MAC,
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(protocol=Ipv4Header.PROTOCOL_TYPE_PIM,
                                     destination_address=Ipv4Header.PIM_MULTICAST_IP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        pim_header_obj = Pimv4HelloHeader()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=pim_header_obj, update=False)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIpv4Pim, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIpv4BGP(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=10, summary="Test CC IPv4 BGP (Border Gateway Protocol)",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and TCP headers under port %s
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

        checkpoint = "Create a stream with EthernetII and IPv4 and TCP headers under port %s" % port1
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

        ipv4_header_obj = Ipv4Header(protocol=Ipv4Header.PROTOCOL_TYPE_TCP,
                                     destination_address=l3_config['cc_destination_ip1'])
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        tcp_header_obj = TCP(source_port=1024, destination_port=TCP.DESTINATION_PORT_BGP, checksum=20047)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=tcp_header_obj, update=False)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIpv4BGP, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIpv4Igmp(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=11, summary="Test CC IPv4 IGMP (Internet Group Management Protocol)",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and IGMP headers under port %s
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

        checkpoint = "Create a stream with EthernetII and IPv4 and IGMP headers under port %s" % port1
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

        ipv4_header_obj = Ipv4Header(protocol=Ipv4Header.PROTOCOL_TYPE_IGMP,
                                     destination_address=l3_config['cc_destination_ip1'])
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        igmp_header_obj = Igmpv1Header()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=igmp_header_obj, update=False)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIpv4Igmp, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4ForUs(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=12, summary="Test CC IPv4 FOR US",
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

        checkpoint = "Create a stream with EthernetII and IPv4 headers under port %s" % port1
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

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['cc_destination_ip1'])
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIPv4ForUs, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4PTP1(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=13, summary="Test CC IPv4 PTP with Destination port 319 with PTP sync",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and UDP (dest port 319) PTP sync 
                                 headers under port %s
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

        checkpoint = "Create a stream with EthernetII and IPv4 headers under port %s" % port1
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

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['cc_destination_ip1'],
                                     protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        udp_header_obj = UDP(destination_port=319)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=udp_header_obj, update=False)
        fun_test.simple_assert(result, "Added UDP header with dest port 319")
        ptp_sync_obj = PtpSyncHeader()
        result = template_obj.configure_ptp_header(header_obj=ptp_sync_obj,
                                                   stream_block_handle=self.stream_obj.spirent_handle,
                                                   create_header=True, delete_header_type=None)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIPv4PTP1, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4PTP2(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=14, summary="Test CC IPv4 PTP with Destination port 320 with PTP sync",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and UDP (dest port 320) PTP sync 
                                 headers under port %s
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

        checkpoint = "Create a stream with EthernetII and IPv4 headers under port %s" % port1
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

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['cc_destination_ip1'],
                                     protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        udp_header_obj = UDP(destination_port=320)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=udp_header_obj, update=False)
        fun_test.simple_assert(result, "Added UDP header with destination port 320")
        ptp_sync_obj = PtpSyncHeader()
        result = template_obj.configure_ptp_header(header_obj=ptp_sync_obj,
                                                   stream_block_handle=self.stream_obj.spirent_handle,
                                                   create_header=True, delete_header_type=None)
        fun_test.test_assert(result, checkpoint)

        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIPv4PTP2, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4PTP3(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=15, summary="Test CC IPv4 PTP Sync with UDP",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and UDP (PTP Sync) headers under port %s
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
        checkpoint = "Create a stream with EthernetII and IPv4 and UDP (PTP Sync) headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.LLDP_MULTICAST_MAC,
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=Ipv4Header.PTP_SYNC_MULTICAST_IP,
                                     protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        udp_header_obj = UDP(destination_port=319)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=udp_header_obj, update=False)
        fun_test.simple_assert(result, "Add UDP header")

        ptp_sync_header_obj = PtpSyncHeader()
        result = template_obj.configure_ptp_header(header_obj=ptp_sync_header_obj,
                                                   stream_block_handle=self.stream_obj.spirent_handle,
                                                   create_header=True, delete_header_type=None)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIPv4PTP3, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4PTP4(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=16, summary="Test CC IPv4 PTP Delay Request with UDP",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and UDP (PTP Delay Request) 
                                 headers under port %s
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
        checkpoint = "Create a stream with EthernetII and IPv4 and UDP (PTP Delay Request) headers under port %s" % \
                     port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.PTP_MULTICAST_MAC,
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=Ipv4Header.PTP_DELAY_MULTICAST_IP,
                                     protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        udp_header_obj = UDP(destination_port=319)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=udp_header_obj, update=False)
        fun_test.simple_assert(result, "Add UDP header")

        ptp_delay_header_obj = PtpDelayReqHeader()
        result = template_obj.configure_ptp_header(header_obj=ptp_delay_header_obj,
                                                   stream_block_handle=self.stream_obj.spirent_handle,
                                                   create_header=True, delete_header_type=None)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIPv4PTP4, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4TtlError1(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None
    LOAD = 27

    def describe(self):
        self.set_test_details(id=17, summary="Test CC IPv4 TTL Error (TTL = 1)",
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
                              7. Validate Tx == Rx on spirent and ensure no errors are seen.
                              8. Validate Tx == Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX    
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, self.LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and IPv4 headers under port %s with IPv4 TTL = 1" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=self.LOAD, load_unit=LOAD_UNIT)
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

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIPv4TtlError1, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4TtlError2(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None
    LOAD = 27

    def describe(self):
        self.set_test_details(id=18, summary="Test CC IPv4 TTL Error (TTL = 0)",
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
                              7. Validate Tx == Rx on spirent and ensure no errors are seen.
                              8. Validate Tx == Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX       
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, self.LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and IPv4 headers under port %s with IPv4 TTL = 0" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=self.LOAD, load_unit=LOAD_UNIT)
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

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIPv4TtlError2,self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4TtlError3(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None
    LOAD = 27

    def describe(self):
        self.set_test_details(id=19, summary="Test CC IPv4 TTL Error (TTL = 1)",
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
                              7. Validate Tx == Rx on spirent and ensure no errors are seen.
                              8. Validate Tx == Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX       
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, self.LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and IPv4 headers under port %s with IPv4 TTL = 1" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=self.LOAD, load_unit=LOAD_UNIT)
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

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIPv4TtlError3, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIpv4ErrorTrapIpOpts1(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None
    LOAD = 40

    def describe(self):
        self.set_test_details(id=20, summary="Test CC IPv4 OPTS Error (Header Option: timestamp)",
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
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, self.LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and IPv4 with timestamp header option under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=self.LOAD, load_unit=LOAD_UNIT)
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

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIpv4ErrorTrapIpOpts1, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIpv4ErrorTrapIpOpts2(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None
    LOAD = 41

    def describe(self):
        self.set_test_details(id=21, summary="Test CC IPv4 OPTS Error (Header Option: Loose Src Route)",
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
                              7. Validate Tx == Rx on spirent and ensure no errors are seen.
                              8. Validate Tx == Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX       
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, self.LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and IPv4 with Loose Src Route header option under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=self.LOAD, load_unit=LOAD_UNIT)
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

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIpv4ErrorTrapIpOpts2, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcEthArpRequestUnicast(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None
    LOAD = 40

    def describe(self):
        self.set_test_details(id=22, summary="Test CC Ethernet ARP Request Unicast ",
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
                              7. Validate Tx == Rx on spirent and ensure no errors are seen.
                              8. Validate Tx == Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX                                 
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, self.LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and ARP header option under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=self.LOAD, load_unit=LOAD_UNIT)
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

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcEthArpRequestUnicast, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIpChecksumError(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None
    LOAD = 41

    def describe(self):
        self.set_test_details(id=23, summary="Test CC IP checksum Error ",
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
                              7. Validate Tx == Rx on spirent and ensure IPv4 Checksum error are seen.
                              8. Validate Tx == Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX   
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, self.LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and Ipv4 header option under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=self.LOAD, load_unit=LOAD_UNIT)
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

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
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
        result = template_obj.enable_generator_configs([self.generator_handle])
        fun_test.test_assert(result, checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION)

        checkpoint = "Ensure Spirent stats fetched"
        tx_results = template_obj.stc_manager.get_tx_stream_block_results(stream_block_handle=self.stream_obj.
                                                                          spirent_handle,
                                                                          subscribe_handle=self.subscribed_results
                                                                          ['tx_subscribe'])

        rx_results = template_obj.stc_manager.get_rx_stream_block_results(stream_block_handle=self.stream_obj.
                                                                          spirent_handle,
                                                                          subscribe_handle=self.subscribed_results
                                                                          ['rx_subscribe'])
        rx_port_results = template_obj.stc_manager.get_rx_port_analyzer_results(port_handle=port1,
                                                                                subscribe_handle=self.subscribed_results
                                                                                ['analyzer_subscribe'])
        fun_test.simple_assert(tx_results and rx_results and rx_port_results, checkpoint)

        fun_test.log("Tx Spirent Stats: %s" % tx_results)
        fun_test.log("Rx Spirent Stats: %s" % rx_results)
        fun_test.log("Rx Port Stats: %s" % rx_port_results)

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
        fun_test.test_assert_expected(expected=int(tx_results['FrameCount']), actual=int(rx_results['FrameCount']),
                                      message=checkpoint)

        checkpoint = "Ensure no errors are seen on spirent"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_results)
        checksum_error_seen = False
        if result['Ipv4ChecksumErrorCount'] > 0 and len(result) == 2:
            checksum_error_seen = True
        fun_test.test_assert(expression=checksum_error_seen, message=checkpoint)

        # DUT stats validation
        if dut_config['enable_dpcsh']:
            checkpoint = "Validate Tx == Rx on DUT"
            frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_stats,
                                                            stat_type=FRAMES_TRANSMITTED_OK)
            frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_stats,
                                                         stat_type=FRAMES_RECEIVED_OK)

            fun_test.test_assert_expected(expected=frames_transmitted, actual=frames_received,
                                          message=checkpoint)
            # VP stats validation
            checkpoint = "From VP stats, Ensure T2C header counter equal to spirent Tx counter"
            fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                          actual=int(vp_stats[VP_PACKETS_CONTROL_T2C_COUNT]), message=checkpoint)

            checkpoint = "From VP stats, Ensure CC OUT counters are equal to spirent Tx Counter"
            fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                          actual=int(vp_stats[VP_PACKETS_CC_OUT]), message=checkpoint)

            checkpoint = "Ensure VP total packets IN == VP total packets OUT"
            fun_test.test_assert_expected(expected=int(vp_stats[VP_PACKETS_TOTAL_IN]),
                                          actual=int(vp_stats[VP_PACKETS_TOTAL_OUT]),
                                          message=checkpoint)
            # ERP stats validation
            checkpoint = "From ERP stats, Ensure count for EFP to WQM decrement pulse equal to spirent Tx"
            fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                          actual=int(erp_stats[ERP_COUNT_FOR_EFP_WQM_DECREMENT_PULSE]),
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for EFP to WRO descriptors send equal to spirent Tx"
            fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                          actual=int(erp_stats[ERP_COUNT_FOR_EFP_WRO_DESCRIPTORS_SENT]),
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for ERP0 to EFP error interface flits equal to spirent Tx"
            fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                          actual=int(erp_stats[ERP_COUNT_FOR_ERP0_EFP_ERROR_INTERFACE_FLITS]),
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for all non FCP packets received equal to spirent Tx"
            fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                          actual=int(erp_stats[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED]),
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for EFP to FCB vld equal to spirent Tx"
            fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                          actual=int(erp_stats[ERP_COUNT_FOR_EFP_FCP_VLD]),
                                          message=checkpoint)
            # WRO stats validation
            checkpoint = "From WRO stats, Ensure WRO IN packets equal to spirent Tx"
            fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                          actual=wro_stats[WRO_IN_NFCP_PKTS], message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO In NFCP packets equal to spirent Tx"
            fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                          actual=wro_stats[WRO_IN_NFCP_PKTS], message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO In packets equal to spirent tx"
            fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                          actual=int(wro_stats[WRO_IN_PKTS]), message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO out WUs equal to spirent tx"
            fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                          actual=int(wro_stats[WRO_OUT_WUS]), message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO WU CNT VPP packets equal to spirent tx"
            fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                          actual=int(wro_stats[WRO_WU_COUNT_VPP]), message=checkpoint)

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIpv4Dhcp(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=24, summary="Test CC IPv4 DHCP",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and DHCp header option under port %s
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
        checkpoint = "Create a stream with EthernetII and IPv4 and DHCp header option under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.BROADCAST_MAC,
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=Ipv4Header.DHCP_RELAY_AGENT_MULTICAST_IP,
                                     protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Configure IPv4 Header with DHCP Relay Agent Multicast IP")

        udp_header_obj = UDP()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=udp_header_obj, update=False)
        fun_test.simple_assert(result, "Added UDP header")

        dhcp_client_message_header = DhcpClientMessageHeader()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=dhcp_client_message_header,
                                                                update=False)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIpv4Dhcp, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcFSFError(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=25, summary="Test CC FSF Error",
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

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcFSFError, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcOuterChecksumError(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None
    frame_size = 148
    load = 40

    def describe(self):
        self.set_test_details(id=26, summary="Test CC IPv4 Outer Checksum Error",
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
                                  """ % (port1, FRAME_LENGTH_MODE, self.frame_size, self.load, LOAD_UNIT, port1,
                                         TRAFFIC_DURATION))

    def setup(self):
        checkpoint = "Create a stream with Overlay Frame Stack under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=self.frame_size,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=self.load, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        result = template_obj.configure_overlay_frame_stack(port=port1, streamblock_obj=self.stream_obj,
                                                            overlay_type=SpirentEthernetTrafficTemplate.ETH_IPV4_UDP_VXLAN_ETH_IPV4_TCP)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Update IPv4 stack with destination IP and checksum error"
        ipv4_header_obj = Ipv4Header(checksum=Ipv4Header.CHECKSUM_ERROR, destination_address="29.1.1.1")
        result = template_obj.update_overlay_frame_header(streamblock_obj=self.stream_obj, header_obj=ipv4_header_obj,
                                                          overlay=False)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcOuterChecksumError, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcInnerChecksumError(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None
    frame_size = 148
    load = 40

    def describe(self):
        self.set_test_details(id=27, summary="Test CC IPv4 Inner Checksum Error",
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
                                  """ % (port1, FRAME_LENGTH_MODE, self.frame_size, self.load, LOAD_UNIT, port1,
                                         TRAFFIC_DURATION))

    def setup(self):
        checkpoint = "Create a stream with Overlay Frame Stack under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=self.frame_size,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=self.load, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        result = template_obj.configure_overlay_frame_stack(port=port1, streamblock_obj=self.stream_obj,
                                                            overlay_type=SpirentEthernetTrafficTemplate.ETH_IPV4_UDP_VXLAN_ETH_IPV4_TCP)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Update IPv4 stack with destination IP"
        ipv4_header_obj = Ipv4Header(destination_address="29.1.1.1")
        result = template_obj.update_overlay_frame_header(streamblock_obj=self.stream_obj, header_obj=ipv4_header_obj,
                                                          overlay=False)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Update IPv4 stack with Checksum"
        ipv4_header_obj = Ipv4Header(checksum=Ipv4Header.CHECKSUM_ERROR)
        result = template_obj.update_overlay_frame_header(streamblock_obj=self.stream_obj, header_obj=ipv4_header_obj,
                                                          overlay=True)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcInnerChecksumError, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4OverlayVersionError(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None
    frame_size = 148
    load = 2

    def describe(self):
        self.set_test_details(id=28, summary="Test CC IPv4 Overlay Version (version = 0) Error",
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
                                  """ % (port1, FRAME_LENGTH_MODE, self.frame_size, self.load, LOAD_UNIT, port1,
                                         TRAFFIC_DURATION))

    def setup(self):
        checkpoint = "Create a stream with Overlay Frame Stack under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=self.frame_size,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=self.load, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        result = template_obj.configure_overlay_frame_stack(port=port1, streamblock_obj=self.stream_obj,
                                                            overlay_type=SpirentEthernetTrafficTemplate.ETH_IPV4_UDP_VXLAN_ETH_IPV4_TCP)
        fun_test.test_assert(result['result'], checkpoint)

        checkpoint = "Update IPv4 stack with destination IP"
        ipv4_header_obj = Ipv4Header(destination_address="29.1.1.1")
        result = template_obj.update_overlay_frame_header(streamblock_obj=self.stream_obj, header_obj=ipv4_header_obj,
                                                          overlay=False)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Update IPv4 stack with version = 0"
        ipv4_header_obj = Ipv4Header(version=0)
        result = template_obj.update_overlay_frame_header(streamblock_obj=self.stream_obj, header_obj=ipv4_header_obj,
                                                          overlay=True)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIPv4OverlayVersionError, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4OverlayIhlError(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None
    frame_size = 148

    def describe(self):
        self.set_test_details(id=29, summary="Test CC IPv4 Overlay Internet Header length (ihl = 3) Error",
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
        ipv4_header_obj = Ipv4Header(destination_address="29.1.1.1")
        result = template_obj.update_overlay_frame_header(streamblock_obj=self.stream_obj, header_obj=ipv4_header_obj,
                                                          overlay=False)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Update IPv4 stack with ihl = 3"
        ipv4_header_obj = Ipv4Header(ihl=3)
        result = template_obj.update_overlay_frame_header(streamblock_obj=self.stream_obj, header_obj=ipv4_header_obj,
                                                          overlay=True)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIPv4OverlayIhlError, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIpv4Isis1(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=30, summary="Test CC IPv4 ISIS_1",
                              steps="""
                              1. Create a stream with EthernetII and  IPv4 headers under port %s
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
        l3_config = spirent_config['l3_config']['ipv4']
        checkpoint = "Create a stream with EthernetII and  IPv4 headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.ISIS_MULTICAST_MAC_1,
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['cc_destination_ip1'])
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIpv4Isis1, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIpv4Isis2(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=31, summary="Test CC IPv4 ISIS_2",
                              steps="""
                              1. Create a stream with EthernetII and  IPv4 headers under port %s
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
        l3_config = spirent_config['l3_config']['ipv4']
        checkpoint = "Create a stream with EthernetII and  IPv4 headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.ISIS_MULTICAST_MAC_2,
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['cc_destination_ip1'])
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIpv4Isis2, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4VersionError(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=32, summary="Test CC IPv4 Version Error",
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

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIPv4VersionError, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4InternetHeaderLengthError(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=33, summary="Test CC IPv4 Internet Header Length Error",
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
        checkpoint = "Create a stream with EthernetII and IPv4 with Header Length = 4  under port %s " % port1
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

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIPv4InternetHeaderLengthError, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4FlagZeroError(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=34, summary="Test CC IPv4 Control Flags Reserved = 1 Error",
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

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIPv4FlagZeroError, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4MTUCase(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None
    mtu = 10000
    frame_size = mtu
    load = 1

    def describe(self):
        self.set_test_details(id=35, summary="Test CC IPv4 10K MTU Case",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                                 e. MTU on ports: %d
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
                                  """ % (port1, FRAME_LENGTH_MODE, self.frame_size, self.load, LOAD_UNIT, self.mtu,
                                         port1, TRAFFIC_DURATION))

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']
        checkpoint = "Create a stream with EthernetII and IPv4 with Control Flags Reserved = 1 Error " \
                     "under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=self.frame_size,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=self.load, load_unit=LOAD_UNIT)
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
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Update ports MTU on spirent ports. MTU: %d" % self.mtu
        mtu_changed_on_spirent = template_obj.change_ports_mtu(interface_obj_list=[interface_obj1, interface_obj2],
                                                               mtu_value=self.mtu)
        fun_test.test_assert(mtu_changed_on_spirent, checkpoint)

        if dut_config['enable_dpcsh']:
            checkpoint = "Update MTU on DUT ports. MTU: %d" % self.mtu
            for port in dut_config['ports']:
                mtu_changed = network_controller_obj.set_port_mtu(port_num=port, mtu_value=self.mtu)
                fun_test.simple_assert(mtu_changed, "Change MTU on DUT port %d to %d" % (port, self.mtu))
            fun_test.add_checkpoint(checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIPv4MTUCase, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4BGPNotForUs(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None
    load = 100

    def describe(self):
        self.set_test_details(id=36, summary="Test CC IPv4 BGP Not For US",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 BGP under port %s
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
                              9. From VP stats, validate CC OUT and Control T2C counters are not equal to spirent TX
                              10. From VP stats, validate VP total IN != VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be not equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be not equal to spirent TX   
                                  """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, self.load, LOAD_UNIT,
                                         port1, TRAFFIC_DURATION))

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']
        checkpoint = "Create a stream with EthernetII and IPv4 with Control Flags Reserved = 1 Error " \
                     "under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=self.load, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['destination_ip1'],
                                     protocol=Ipv4Header.PROTOCOL_TYPE_TCP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Configure IPv4 header")
        tcp_header_obj = TCP(destination_port=TCP.DESTINATION_PORT_BGP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=tcp_header_obj, update=False)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
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
        result = template_obj.enable_generator_configs([self.generator_handle])
        fun_test.test_assert(result, checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION)

        checkpoint = "Ensure Spirent stats fetched"
        tx_results = template_obj.stc_manager.get_tx_stream_block_results(stream_block_handle=self.stream_obj.
                                                                          spirent_handle,
                                                                          subscribe_handle=self.subscribed_results
                                                                          ['tx_subscribe'])

        rx_results = template_obj.stc_manager.get_rx_stream_block_results(stream_block_handle=self.stream_obj.
                                                                          spirent_handle,
                                                                          subscribe_handle=self.subscribed_results
                                                                          ['rx_subscribe'])
        rx_port_results = template_obj.stc_manager.get_rx_port_analyzer_results(port_handle=port1,
                                                                                subscribe_handle=self.subscribed_results
                                                                                ['analyzer_subscribe'])
        fun_test.simple_assert(tx_results and rx_results and rx_port_results, checkpoint)

        fun_test.log("Tx Spirent Stats: %s" % tx_results)
        fun_test.log("Rx Spirent Stats: %s" % rx_results)
        fun_test.log("Rx Port Stats: %s" % rx_port_results)

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
        fun_test.test_assert_expected(expected=int(tx_results['FrameCount']), actual=int(rx_results['FrameCount']),
                                      message=checkpoint)

        checkpoint = "Ensure no errors are seen on spirent"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_results)
        fun_test.test_assert(expression=result['result'], message=checkpoint)

        # DUT stats validation
        if dut_config['enable_dpcsh']:
            checkpoint = "Validate Tx == Rx on DUT"
            frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_stats,
                                                            stat_type=FRAMES_TRANSMITTED_OK)
            frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_stats,
                                                         stat_type=FRAMES_RECEIVED_OK)

            fun_test.test_assert_expected(expected=frames_transmitted, actual=frames_received,
                                          message=checkpoint)
            # VP stats validation
            checkpoint = "From VP stats, Ensure T2C header counter equal to spirent Tx counter"
            fun_test.test_assert_expected(expected=0,
                                          actual=int(vp_stats[VP_PACKETS_CONTROL_T2C_COUNT]), message=checkpoint)

            checkpoint = "From VP stats, Ensure CC OUT counters are equal to spirent Tx Counter"
            fun_test.test_assert_expected(expected=0,
                                          actual=int(vp_stats[VP_PACKETS_CC_OUT]), message=checkpoint)

            checkpoint = "Ensure VP total packets IN == VP total packets OUT"
            fun_test.test_assert_expected(expected=0,
                                          actual=int(vp_stats[VP_PACKETS_TOTAL_OUT]),
                                          message=checkpoint)
            # ERP stats validation
            checkpoint = "From ERP stats, Ensure count for EFP to WQM decrement pulse equal to spirent Tx"
            fun_test.test_assert_expected(expected=0,
                                          actual=int(erp_stats[ERP_COUNT_FOR_EFP_WQM_DECREMENT_PULSE]),
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for EFP to WRO descriptors send equal to spirent Tx"
            fun_test.test_assert_expected(expected=0,
                                          actual=int(erp_stats[ERP_COUNT_FOR_EFP_WRO_DESCRIPTORS_SENT]),
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for ERP0 to EFP error interface flits equal to spirent Tx"
            fun_test.test_assert_expected(expected=0,
                                          actual=int(erp_stats[ERP_COUNT_FOR_ERP0_EFP_ERROR_INTERFACE_FLITS]),
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for all non FCP packets received equal to spirent Tx"
            fun_test.test_assert_expected(expected=0,
                                          actual=int(erp_stats[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED]),
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for EFP to FCB vld equal to spirent Tx"
            fun_test.test_assert_expected(expected=0,
                                          actual=int(erp_stats[ERP_COUNT_FOR_EFP_FCP_VLD]),
                                          message=checkpoint)
            # WRO stats validation
            checkpoint = "From WRO stats, Ensure WRO IN packets equal to spirent Tx"
            fun_test.test_assert_expected(expected=0,
                                          actual=wro_stats[WRO_IN_NFCP_PKTS], message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO In NFCP packets equal to spirent Tx"
            fun_test.test_assert_expected(expected=0,
                                          actual=wro_stats[WRO_IN_NFCP_PKTS], message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO In packets equal to spirent tx"
            fun_test.test_assert_expected(expected=0,
                                          actual=int(wro_stats[WRO_IN_PKTS]), message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO out WUs equal to spirent tx"
            fun_test.test_assert_expected(expected=0,
                                          actual=int(wro_stats[WRO_OUT_WUS]), message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO WU CNT VPP packets equal to spirent tx"
            fun_test.test_assert_expected(expected=0,
                                          actual=int(wro_stats[WRO_WU_COUNT_VPP]), message=checkpoint)

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIpv4Version6Error(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None
    load = 40

    def describe(self):
        self.set_test_details(id=37, summary="Test CC IPv4 Version 6 (Ver = 6) Error",
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
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, self.load, LOAD_UNIT, port1,
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
                                      load=self.load, load_unit=LOAD_UNIT)
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

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIpv4Version6Error, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcGlean(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=38, summary="Test CC IPv4 Glean ",
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

        ipv4_header_obj = Ipv4Header(destination_address="32.1.1.1")
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcGlean, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcCrcBadVerError(FunTestCase):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None
    frame_size = 1500
    load = 1

    def describe(self):
        self.set_test_details(id=39, summary="Test CC IPv4 CRC Bad version error ",
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
                              """ % (port1, FRAME_LENGTH_MODE, self.frame_size, self.load,
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
                                      load=self.load, load_unit=LOAD_UNIT)
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

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
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
        result = template_obj.enable_generator_configs([self.generator_handle])
        fun_test.test_assert(result, checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION)

        checkpoint = "Ensure Spirent stats fetched"
        tx_results = template_obj.stc_manager.get_tx_stream_block_results(stream_block_handle=self.stream_obj.
                                                                          spirent_handle,
                                                                          subscribe_handle=self.subscribed_results
                                                                          ['tx_subscribe'])

        rx_results = template_obj.stc_manager.get_rx_stream_block_results(stream_block_handle=self.stream_obj.
                                                                          spirent_handle,
                                                                          subscribe_handle=self.subscribed_results
                                                                          ['rx_subscribe'])
        rx_port_results = template_obj.stc_manager.get_rx_port_analyzer_results(port_handle=port1,
                                                                                subscribe_handle=self.subscribed_results
                                                                                ['analyzer_subscribe'])
        fun_test.simple_assert(tx_results and rx_results and rx_port_results, checkpoint)

        fun_test.log("Tx Spirent Stats: %s" % tx_results)
        fun_test.log("Rx Spirent Stats: %s" % rx_results)
        fun_test.log("Rx Port Stats: %s" % rx_port_results)

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
        checkpoint = "Validate Tx != Rx on spirent"
        fun_test.test_assert(int(tx_results['FrameCount']) != int(rx_results['FrameCount']), message=checkpoint)
        fun_test.test_assert_expected(expected=0, actual=int(rx_results['FrameCount']),
                                      message="Ensure Spirent Rx count should be 0")

        checkpoint = "Ensure no errors are seen on spirent"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_results)
        dropped_frame_count_seen = False
        if result['DroppedFrameCount'] > 0:
            dropped_frame_count_seen = True
        fun_test.test_assert(expression=dropped_frame_count_seen, message=checkpoint)

        # DUT stats validation
        if dut_config['enable_dpcsh']:
            checkpoint = "Validate Tx == Rx on DUT"
            frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_stats,
                                                            stat_type=FRAMES_TRANSMITTED_OK)
            frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_stats,
                                                         stat_type=FRAMES_RECEIVED_OK)

            fun_test.test_assert(frames_transmitted != frames_received,message=checkpoint)
            fun_test.test_assert_expected(expected=0, actual=frames_received, message="Ensure DUT Rx count should be 0")
            # VP stats validation
            checkpoint = "From VP stats, Ensure T2C header counter equal to spirent Tx counter"
            fun_test.test_assert_expected(expected=0,
                                          actual=int(vp_stats[VP_PACKETS_CONTROL_T2C_COUNT]), message=checkpoint)

            checkpoint = "From VP stats, Ensure CC OUT counters are equal to spirent Tx Counter"
            fun_test.test_assert_expected(expected=0,
                                          actual=int(vp_stats[VP_PACKETS_CC_OUT]), message=checkpoint)

            checkpoint = "Ensure VP total packets IN == VP total packets OUT"
            fun_test.test_assert_expected(expected=0,
                                          actual=int(vp_stats[VP_PACKETS_TOTAL_OUT]),
                                          message=checkpoint)
            # ERP stats validation
            checkpoint = "From ERP stats, Ensure count for EFP to WQM decrement pulse equal to spirent Tx"
            fun_test.test_assert_expected(expected=0,
                                          actual=int(erp_stats[ERP_COUNT_FOR_EFP_WQM_DECREMENT_PULSE]),
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for EFP to WRO descriptors send equal to spirent Tx"
            fun_test.test_assert_expected(expected=0,
                                          actual=int(erp_stats[ERP_COUNT_FOR_EFP_WRO_DESCRIPTORS_SENT]),
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for ERP0 to EFP error interface flits equal to spirent Tx"
            fun_test.test_assert_expected(expected=0,
                                          actual=int(erp_stats[ERP_COUNT_FOR_ERP0_EFP_ERROR_INTERFACE_FLITS]),
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for all non FCP packets received equal to spirent Tx"
            fun_test.test_assert_expected(expected=0,
                                          actual=int(erp_stats[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED]),
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for EFP to FCB vld equal to spirent Tx"
            fun_test.test_assert_expected(expected=0,
                                          actual=int(erp_stats[ERP_COUNT_FOR_EFP_FCP_VLD]),
                                          message=checkpoint)
            # WRO stats validation
            checkpoint = "From WRO stats, Ensure WRO IN packets equal to spirent Tx"
            fun_test.test_assert_expected(expected=0,
                                          actual=wro_stats[WRO_IN_NFCP_PKTS], message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO In NFCP packets equal to spirent Tx"
            fun_test.test_assert_expected(expected=0,
                                          actual=wro_stats[WRO_IN_NFCP_PKTS], message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO In packets equal to spirent tx"
            fun_test.test_assert_expected(expected=0,
                                          actual=int(wro_stats[WRO_IN_PKTS]), message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO out WUs equal to spirent tx"
            fun_test.test_assert_expected(expected=0,
                                          actual=int(wro_stats[WRO_OUT_WUS]), message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO WU CNT VPP packets equal to spirent tx"
            fun_test.test_assert_expected(expected=0,
                                          actual=int(wro_stats[WRO_WU_COUNT_VPP]), message=checkpoint)

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcMultiError(TestCcIpChecksumError):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None
    LOAD = 1

    def describe(self):
        self.set_test_details(id=40, summary="Test CC IPv4 Multiple Errors (checksum and ttl=5) ",
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
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, self.LOAD, LOAD_UNIT, port1,
                                     TRAFFIC_DURATION))

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']

        checkpoint = "Create a stream with EthernetII and Ipv4 header option under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=self.LOAD, load_unit=LOAD_UNIT)
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

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcMultiError, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcMtuCaseForUs(TestCcEthernetArpRequest):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None
    mtu = 10000
    frame_size = mtu
    load = 1

    def describe(self):
        self.set_test_details(id=41, summary="Test CC IPv4 10K MTU Case For US",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                                 e. MTU on ports: %d
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
                              """ % (port1, FRAME_LENGTH_MODE, self.frame_size, self.load, LOAD_UNIT, self.mtu,
                                     port1, TRAFFIC_DURATION))

    def setup(self):
        l2_config = spirent_config['l2_config']
        l3_config = spirent_config['l3_config']['ipv4']
        checkpoint = "Create a stream with EthernetII and IPv4 with Control Flags Reserved = 1 Error " \
                     "under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=self.frame_size,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=self.load, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['cc_destination_ip1'])
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Update ports MTU on spirent ports. MTU: %d" % self.mtu
        mtu_changed_on_spirent = template_obj.change_ports_mtu(interface_obj_list=[interface_obj1, interface_obj2],
                                                               mtu_value=self.mtu)
        fun_test.test_assert(mtu_changed_on_spirent, checkpoint)

        if dut_config['enable_dpcsh']:
            checkpoint = "Update MTU on DUT ports. MTU: %d" % self.mtu
            for port in dut_config['ports']:
                mtu_changed = network_controller_obj.set_port_mtu(port_num=port, mtu_value=self.mtu)
                fun_test.simple_assert(mtu_changed, "Change MTU on DUT port %d to %d" % (port, self.mtu))
            fun_test.add_checkpoint(checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcMtuCaseForUs, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4Ptp1NotForUs(TestCcIPv4BGPNotForUs):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=42, summary="Test CC IPv4 PTP1 Not For US",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 UDP and PTP Sync under port %s
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
                              9. From VP stats, validate CC OUT and Control T2C counters are not equal to spirent TX
                              10. From VP stats, validate VP total IN != VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be not equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be not equal to spirent TX   
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, self.load, LOAD_UNIT,
                                     port1, TRAFFIC_DURATION))

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

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['destination_ip1'],
                                     protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Configure IPv4 header")
        udp_header_obj = UDP(destination_port=319)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=udp_header_obj, update=False)
        fun_test.simple_assert(result, "Configure UDP Header")

        ptp_header_obj = PtpSyncHeader()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ptp_header_obj, update=False)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIPv4Ptp1NotForUs, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4Ptp2NotForUs(TestCcIPv4BGPNotForUs):
    stream_obj = None
    generator_handle = None
    generator_config_obj = None
    subscribed_results = None

    def describe(self):
        self.set_test_details(id=43, summary="Test CC IPv4 PTP1 Not For US",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 UDP and PTP Sync under port %s
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
                              9. From VP stats, validate CC OUT and Control T2C counters are not equal to spirent TX
                              10. From VP stats, validate VP total IN != VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be not equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be not equal to spirent TX   
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, self.load, LOAD_UNIT,
                                     port1, TRAFFIC_DURATION))

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

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['destination_ip1'],
                                     protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Configure IPv4 header")
        udp_header_obj = UDP(destination_port=320)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=udp_header_obj, update=False)
        fun_test.simple_assert(result, "Configure UDP Header")

        ptp_header_obj = PtpSyncHeader()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ptp_header_obj, update=False)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(self.generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(self.subscribed_results, checkpoint)

    def run(self):
        super(TestCcIPv4Ptp2NotForUs, self).run()

    def cleanup(self):
        fun_test.log("In test case cleanup")

        checkpoint = "Delete %s " % self.stream_obj.spirent_handle
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)


if __name__ == '__main__':
    cc_flow_types = nu_config_obj.read_dut_spirent_map()["cc_flow"]
    for flow_type in cc_flow_types:
        fun_test.log("<---------------> Validating %s Flow Direction <--------------->" % flow_type)
        FLOW_DIRECTION = flow_type

        ts = SetupSpirent()
        # Ethernet CC
        ts.add_test_case(TestCcEthernetArpRequest())
        ts.add_test_case(TestCcEthernetArpResponse())
        ts.add_test_case(TestCcEthernetRarp())
        ts.add_test_case(TestCcEthernetLLDP())
        ts.add_test_case(TestCcEthernetPTP())

        # IPv4 CC
        ts.add_test_case(TestCcIPv4ICMP())
        ts.add_test_case(TestCcIPv4Ospfv2Hello())
        ts.add_test_case(TestCcIPv4Ospfv2LinkStateUpdate())
        ts.add_test_case(TestCcIpv4Pim())
        ts.add_test_case(TestCcIpv4BGP())
        ts.add_test_case(TestCcIpv4Igmp())
        ts.add_test_case(TestCcIPv4ForUs())
        ts.add_test_case(TestCcIPv4PTP1())
        ts.add_test_case(TestCcIPv4PTP2())
        ts.add_test_case(TestCcIPv4PTP3())
        ts.add_test_case(TestCcIPv4PTP4())

        # Error Traps
        ts.add_test_case(TestCcIPv4TtlError1())
        ts.add_test_case(TestCcIPv4TtlError2())
        ts.add_test_case(TestCcIPv4TtlError3())
        ts.add_test_case(TestCcIpv4ErrorTrapIpOpts1())
        ts.add_test_case(TestCcIpv4ErrorTrapIpOpts2())

        # Unicast CC
        ts.add_test_case(TestCcEthArpRequestUnicast())
        
        ts.add_test_case(TestCcIpChecksumError())
        ts.add_test_case(TestCcIpv4Dhcp())
        ts.add_test_case(TestCcFSFError())
        ts.add_test_case(TestCcIpv4Isis1())
        ts.add_test_case(TestCcIpv4Isis2())
        ts.add_test_case(TestCcIPv4VersionError())
        ts.add_test_case(TestCcIPv4InternetHeaderLengthError())
        ts.add_test_case(TestCcIPv4FlagZeroError())
        ts.add_test_case(TestCcIPv4MTUCase())
        ts.add_test_case(TestCcOuterChecksumError())
        ts.add_test_case(TestCcInnerChecksumError())
        ts.add_test_case(TestCcIPv4OverlayVersionError())
        ts.add_test_case(TestCcIPv4OverlayIhlError())

        ts.add_test_case(TestCcIpv4Version6Error())
        ts.add_test_case(TestCcGlean())
        ts.add_test_case(TestCcCrcBadVerError())
        ts.add_test_case(TestCcMultiError())
        ts.add_test_case(TestCcMtuCaseForUs())
        ts.add_test_case(TestCcIPv4Ptp1NotForUs())
        ts.add_test_case(TestCcIPv4Ptp2NotForUs())

        ts.run()