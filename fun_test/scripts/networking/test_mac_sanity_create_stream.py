from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, GeneratorConfig, Ethernet2Header, ARP
from lib.host.network_controller import NetworkController
from helper import *
from nu_config_manager import *

num_ports = 2


class SpirentSetup(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
                1. Create Spirent template
                2. Connect chassis, lab server and license server
                3. Attach Ports
                """)

    def setup(self):
        global template_obj, port_1, port_2, gen_obj, \
            gen_config_obj, network_controller_obj, dut_port_1, dut_port_2, dut_config, spirent_config, chassis_type

        dut_type = fun_test.get_local_setting(setting="dut_type")
        dut_config = nu_config_obj.read_dut_config(dut_type=dut_type)

        chassis_type = fun_test.get_local_setting(setting="chassis_type")
        spirent_config = nu_config_obj.read_traffic_generator_config()

        fun_test.log("Creating Template object")
        template_obj = SpirentEthernetTrafficTemplate(session_name="mac-sanity", spirent_config=spirent_config,
                                                      chassis_type=chassis_type)
        fun_test.test_assert(template_obj, "Create template object")

        result = template_obj.setup(no_of_ports_needed=num_ports)
        fun_test.test_assert(result['result'], "Configure setup")

        port_1 = result['port_list'][0]
        port_2 = result['port_list'][1]

        # Create network controller object
        dpcsh_server_ip = dut_config["dpcsh_tcp_proxy_ip"]
        dpcsh_server_port = dut_config['dpcsh_tcp_proxy_port']
        if dut_config['enable_dpcsh']:
            network_controller_obj = NetworkController(dpc_server_ip=dpcsh_server_ip, dpc_server_port=dpcsh_server_port)

        '''
        srcMac = spirent_config[chassis_type][""]
        destMac = template_obj.stc_manager.dut_config['destination_mac1']
        srcIp = template_obj.stc_manager.dut_config['source_ip1']
        destIp = template_obj.stc_manager.dut_config['destination_ip1']
        dut_port_1 = template_obj.stc_manager.dut_config['port_nos'][0]
        dut_port_2 = template_obj.stc_manager.dut_config['port_nos'][1]
        gateway = template_obj.stc_manager.dut_config['gateway1']
        ether_type = "0800"
        '''

        dut_port_1 = dut_config["ports"][0]
        dut_port_2 = dut_config['ports'][1]

        # Configure Generator
        gen_config_obj = GeneratorConfig()
        gen_config_obj.Duration = 30
        gen_config_obj.SchedulingMode = gen_config_obj.SCHEDULING_MODE_RATE_BASED
        gen_config_obj.DurationMode = gen_config_obj.DURATION_MODE_SECONDS
        gen_config_obj.AdvancedInterleaving = True

        gen_obj = template_obj.stc_manager.get_generator(port_handle=port_1)

        config_obj = template_obj.configure_generator_config(port_handle=port_1,
                                                             generator_config_obj=gen_config_obj)
        fun_test.test_assert(config_obj, "Creating generator config")

        # Applying configuration
        apply = template_obj.stc_manager.apply_configuration()
        fun_test.test_assert(apply, "Applying Generator config")

    def cleanup(self):
        fun_test.test_assert(template_obj.cleanup(), "Cleaning up session")


class IPv4GoodFrameTestCase1(FunTestCase):
    streamblock_obj = None
    subscribe_results = None
    duration_seconds = 30

    def describe(self):
        self.set_test_details(id=1,
                              summary="Creating good IPv4 streamblock",
                              steps="""
                        1. Create streamblock with following settings
                           a. Load: 500
                           b. Load Unit: Frames Per Seconds
                           c. Payload Fill Type: PRBS
                           d. Insert Signature 
                           e. Frame Size: Random Min: 74 and Max: 1500
                        2. Start traffic for 30 secs  
                        3. Compare Tx and Rx results for frame count of Spirent. Both must be same
                        4. Check for error counters. there must be no error counter
                        5. Verify frame count matches on dut ingress and egress
                        """)

    def setup(self):
        # Clear port results on DUT
        if dut_config['enable_dpcsh']:
            clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
            fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

            clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
            fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

        l2_config = spirent_config["l2_config"]
        l3_config = spirent_config["l3_config"]["ipv4"]
        ether_type = Ethernet2Header.INTERNET_IP_ETHERTYPE

        load = 500
        self.streamblock_obj = StreamBlock()
        self.streamblock_obj.LoadUnit = self.streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        self.streamblock_obj.Load = load
        self.streamblock_obj.FillType = self.streamblock_obj.FILL_TYPE_PRBS
        self.streamblock_obj.InsertSig = True
        self.streamblock_obj.FrameLengthMode = self.streamblock_obj.FRAME_LENGTH_MODE_RANDOM
        self.streamblock_obj.MinFrameLength = 74
        self.streamblock_obj.MaxFrameLength = 1500

        streamblock1 = template_obj.configure_stream_block(self.streamblock_obj, port_1)
        fun_test.test_assert(streamblock1, "Creating streamblock on port %s" % port_1)

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=self.streamblock_obj.spirent_handle,
                                                               source_mac=l2_config['source_mac'],
                                                               destination_mac=l2_config['destination_mac'],
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Adding source and destination mac")

        # Adding Ip address and gateway
        ip = template_obj.stc_manager.configure_ip_address(streamblock=self.streamblock_obj.spirent_handle,
                                                           source=l3_config["source_ip1"],
                                                           destination=l3_config["destination_ip1"],
                                                           gateway=l3_config["gateway"])
        fun_test.test_assert(ip, "Adding source ip, dest ip and gateway")

    def cleanup(self):
        fun_test.log("In testcase cleanup")
        fun_test.log("Deleting streamblock %s " % self.streamblock_obj.spirent_handle)
        template_obj.delete_streamblocks(streamblock_handle_list=[self.streamblock_obj.spirent_handle])
        if self.subscribe_results:
            # clear port results
            port_results = template_obj.stc_manager.clear_all_port_results(port_list=[port_1, port_2])
            fun_test.simple_assert(port_results, "Clear port results")

    def run(self):
        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=gen_obj)
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=self.duration_seconds)

        # Subscribe to results
        project = template_obj.stc_manager.get_project_handle()
        self.subscribe_results = template_obj.subscribe_to_all_results(parent=project)
        fun_test.test_assert(self.subscribe_results['result'], "Subscribing to results")

        fun_test.log("Fetching tx results for subscribed object %s" % self.subscribe_results['tx_subscribe'])
        tx_results = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=self.streamblock_obj.spirent_handle,
            subscribe_handle=self.subscribe_results['tx_subscribe'])

        fun_test.log("Fetching rx results for subscribed object %s" % self.subscribe_results['rx_subscribe'])
        rx_results = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=self.streamblock_obj.spirent_handle,
            subscribe_handle=self.subscribe_results['rx_subscribe'])

        fun_test.log("Fetching rx port results for subscribed object %s" % self.subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_2, subscribe_handle=self.subscribe_results['analyzer_subscribe'])

        dut_port_1_results = None
        dut_port_2_results = None
        dut_port_2_transmit = None
        dut_port_1_receive = None
        if dut_config['enable_dpcsh']:
            dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1)
            dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2)

            dut_port_2_transmit = get_dut_output_stats_value(dut_port_2_results, FRAMES_TRANSMITTED_OK)
            dut_port_1_receive = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)

            fun_test.log("DUT Port 1 Results: %s" % dut_port_1_results)
            fun_test.log("DUT Port 2 Results: %s" % dut_port_2_results)

        fun_test.log("Tx Results %s " % tx_results)
        fun_test.log("Rx Results %s" % rx_results)
        fun_test.log("Rx Port Analyzer Results %s" % rx_port_analyzer_results)

        fun_test.test_assert(template_obj.compare_result_attribute(tx_results,rx_results), "Check FrameCount")

        zero_counter_seen = template_obj.check_non_zero_error_count(rx_port_analyzer_results)
        fun_test.test_assert(zero_counter_seen['result'], "Check for error counters")
        if dut_config['enable_dpcsh']:
            fun_test.test_assert(dut_port_1_results, message="Ensure stats are obtained for %s" % dut_port_1)
            fun_test.test_assert(dut_port_2_results, message="Ensure stats are obtained for %s" % dut_port_2)

            fun_test.test_assert_expected(expected=int(dut_port_1_receive), actual=int(dut_port_2_transmit),
                                          message="Ensure frames received on DUT port %s are transmitted from DUT port %s"
                                                  % (dut_port_1, dut_port_2))

            fun_test.test_assert_expected(expected=int(dut_port_2_transmit), actual=int(rx_results['FrameCount']),
                                          message="Ensure frames transmitted from DUT and counter on spirent match")


class IPv6GoodFrameTestCase1(IPv4GoodFrameTestCase1):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Creating good IPv6 streamblock",
                              steps="""
                              1. Create streamblock with following settings
                                 a. Load: 500
                                 b. Load Unit: Frames Per Seconds
                                 c. Payload Fill Type: PRBS
                                 d. Insert Signature 
                                 e. Frame Size: Random Min: 78 and Max: 1500
                              2. Start traffic for 30 secs  
                              3. Compare Tx and Rx results for frame count of Spirent. Both must be same
                              4. Check for error counters. there must be no error counter
                              5. Verify frame count matches on dut ingress and egress
                              """)

    def setup(self):
        # Clear port results on DUT
        if dut_config['enable_dpcsh']:
            clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
            fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

            clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
            fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

        l2_config = spirent_config["l2_config"]
        l3_config = spirent_config["l3_config"]["ipv6"]
        ether_type = Ethernet2Header.INTERNET_IPV6_ETHERTYPE

        load = 500
        self.streamblock_obj = StreamBlock()
        self.streamblock_obj.LoadUnit = self.streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        self.streamblock_obj.Load = load
        self.streamblock_obj.FillType = self.streamblock_obj.FILL_TYPE_PRBS
        self.streamblock_obj.InsertSig = True
        self.streamblock_obj.FrameLengthMode = self.streamblock_obj.FRAME_LENGTH_MODE_RANDOM
        self.streamblock_obj.MinFrameLength = 78
        self.streamblock_obj.MaxFrameLength = 1500

        streamblock1 = template_obj.configure_stream_block(stream_block_obj=self.streamblock_obj,
                                                           port_handle=port_1, ip_header_version=6)
        fun_test.test_assert(streamblock1, "Creating streamblock on port %s" % port_1)

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=self.streamblock_obj.spirent_handle,
                                                               source_mac=l2_config['source_mac'],
                                                               destination_mac=l2_config['destination_mac'],
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Adding source and destination mac")

        # Adding Ip address and gateway
        ip = template_obj.stc_manager.configure_ip_address(streamblock=self.streamblock_obj.spirent_handle,
                                                           source=l3_config["source_ip1"],
                                                           destination=l3_config["destination_ip1"])
        fun_test.test_assert(ip, "Adding source ip, dest ip and gateway")

    def run(self):
        super(IPv6GoodFrameTestCase1, self).run()

    def cleanup(self):
        super(IPv6GoodFrameTestCase1, self).cleanup()


class IPv4RuntTestCase2(FunTestCase):
    streamblock_obj = None
    subscribe_results = None
    duration_seconds = 30

    def describe(self):
        self.set_test_details(id=2,
                              summary="Creating runt IPv4 streamblock",
                              steps="""
                        1. Create streamblock with following settings
                           a. Load: 500 fps
                           b. Payload Fill Type: PRBS
                           c. Insert Signature
                           d. Frame Size Mode: Random Min: 40 and Max:60
                        2. Start traffic for 30 secs 
                        3. Received frame count from analyzer port must be 0
                        4. Dropped frame count from analyzer port must be equal to the frames transmitted
                        5. Ensure undersize frames are received on dut ingress
                        6. Check psw global stats for cpr_sop_drop_pkt, fwd_frv, main_pkt_drop_eop, cpr_feop_pkt, 
                        ifpg_pkt
                        """)

    def setup(self):
        # Clear port results on DUT
        if dut_config['enable_dpcsh']:
            clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
            fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

            clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
            fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

        load = 500
        self.streamblock_obj = StreamBlock()
        self.streamblock_obj.LoadUnit = self.streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        self.streamblock_obj.Load = load
        self.streamblock_obj.FillType = self.streamblock_obj.FILL_TYPE_PRBS
        self.streamblock_obj.InsertSig = False
        self.streamblock_obj.FrameLengthMode = self.streamblock_obj.FRAME_LENGTH_MODE_RANDOM
        self.streamblock_obj.MinFrameLength = 40
        self.streamblock_obj.MaxFrameLength = 60

        l2_config = spirent_config["l2_config"]
        l3_config = spirent_config["l3_config"]["ipv4"]
        ether_type = Ethernet2Header.INTERNET_IP_ETHERTYPE

        streamblock1 = template_obj.configure_stream_block(self.streamblock_obj, port_1)
        fun_test.test_assert(streamblock1, "Creating streamblock on port %s" % port_1)

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=self.streamblock_obj.spirent_handle,
                                                               source_mac=l2_config['source_mac'],
                                                               destination_mac=l2_config['destination_mac'],
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Adding source and destination mac")

        # Adding Ip address and gateway
        ip = template_obj.stc_manager.configure_ip_address(streamblock=self.streamblock_obj.spirent_handle,
                                                           source=l3_config['source_ip1'],
                                                           destination=l3_config['destination_ip1'],
                                                           gateway=l3_config['gateway'])
        fun_test.test_assert(ip, "Adding source ip, dest ip and gateway")

    def cleanup(self):
        fun_test.log("In testcase cleanup")
        fun_test.log("Deleting streamblock %s " % self.streamblock_obj.spirent_handle)
        template_obj.delete_streamblocks(streamblock_handle_list=[self.streamblock_obj.spirent_handle])
        if self.subscribe_results:
            # clear port results
            port_results = template_obj.stc_manager.clear_all_port_results(port_list=[port_1, port_2])
            fun_test.simple_assert(port_results, "Clear port results")

    def run(self):
        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=gen_obj)
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=self.duration_seconds)

        # Subscribe to results
        project = template_obj.stc_manager.get_project_handle()
        self.subscribe_results = template_obj.subscribe_to_all_results(parent=project)
        fun_test.test_assert(self.subscribe_results['result'], "Subscribing to results")

        fun_test.log("Fetching tx results for subscribed object %s" % self.subscribe_results['tx_subscribe'])
        tx_results = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=self.streamblock_obj.spirent_handle,
            subscribe_handle=self.subscribe_results['tx_subscribe'])

        fun_test.log("Fetching rx results for subscribed object %s" % self.subscribe_results['rx_subscribe'])
        rx_results = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=self.streamblock_obj.spirent_handle,
            subscribe_handle=self.subscribe_results['rx_subscribe'])

        fun_test.log("Fetching rx port results for subscribed object %s" % self.subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_2, subscribe_handle=self.subscribe_results['analyzer_subscribe'])

        fun_test.log("Fetching tx port results for subscribed object %s" % self.subscribe_results['generator_subscribe'])
        tx_port_generator_results = template_obj.stc_manager.get_generator_port_results(
            port_handle=port_1, subscribe_handle=self.subscribe_results['generator_subscribe'])

        dut_port_2_results = None
        dut_port_1_results = None
        if dut_config['enable_dpcsh']:
            dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2)
            dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1)
            fun_test.log("DUT Port 1 Results: %s" % dut_port_1_results)
            fun_test.log("DUT Port 2 Results: %s" % dut_port_2_results)

        fun_test.log("Tx Results %s " % tx_results)
        fun_test.log("Rx Results %s" % rx_results)
        fun_test.log("Rx Port Analyzer Results %s" % rx_port_analyzer_results)
        fun_test.log("Tx Port Generator Results %s" % tx_port_generator_results)

        # Check frame counts
        frames_received = 0
        fun_test.test_assert_expected(actual=int(rx_port_analyzer_results['TotalFrameCount']), expected=frames_received,
                                      message="Ensure no frame is received")

        if dut_config['enable_dpcsh']:
            fun_test.test_assert(dut_port_2_results, message="Ensure stats are obtained for %s" % dut_port_2)
            fun_test.test_assert(dut_port_1_results, message="Ensure stats are obtained for %s" % dut_port_1)

            dut_port_2_transmit = get_dut_output_stats_value(dut_port_2_results, FRAMES_TRANSMITTED_OK)
            fun_test.test_assert(not dut_port_2_transmit, "Ensure frames transmitted is None")

            dut_port_1_undersize_pkts = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_UNDERSIZE_PKTS, tx=False)
            fun_test.test_assert_expected(expected=int(tx_results['FrameCount']), actual=int(dut_port_1_undersize_pkts),
                                          message="Ensure all packets are marked undersize on rx port of dut")
            '''
            psw_stats = network_controller_obj.peek_psw_global_stats()
            dut_port_1_fpg_value = get_fpg_port_value(dut_port_1)
            ifpg_pkt = 'ifpg' + str(dut_port_1_fpg_value) + '_pkt'
            cpr_feop_pkt = 'cpr_feop_pkt'
            cpr_sop_drop_pkt = 'cpr_sop_drop_pkt'
            fwd_frv = 'fwd_frv'
            main_pkt_drop_eop = 'main_pkt_drop_eop'
            fetch_list = [cpr_sop_drop_pkt, fwd_frv, main_pkt_drop_eop, cpr_feop_pkt, ifpg_pkt]

            psw_fetched_output = get_psw_global_stats_values(psw_stats, fetch_list)
            for key in fetch_list:
                fun_test.test_assert_expected(expected=int(tx_results['FrameCount']), actual=psw_fetched_output[key],
                                              message="Check counter %s in psw global stats" % key)
            '''


class IPv6RuntTestCase2(IPv4RuntTestCase2):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Creating runt IPv6 streamblock",
                              steps="""
                              1. Create streamblock with following settings
                                 a. Load: 500 fps
                                 b. Payload Fill Type: PRBS
                                 c. Insert Signature
                                 d. Frame Size Mode: Random Min: 58 and Max:75
                              2. Start traffic for 30 secs 
                              3. Received frame count from analyzer port must be 0
                              4. Dropped frame count from analyzer port must be equal to the frames transmitted
                              5. Ensure undersize frames are received on dut ingress
                              6. Check psw global stats for cpr_sop_drop_pkt, fwd_frv, main_pkt_drop_eop, cpr_feop_pkt, 
                              ifpg_pkt=
                              """)

    def setup(self):
        if dut_config['enable_dpcsh']:
            # Clear port results on DUT
            clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
            fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

            clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
            fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

        load = 500
        self.streamblock_obj = StreamBlock()
        self.streamblock_obj.LoadUnit = self.streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        self.streamblock_obj.Load = load
        self.streamblock_obj.FillType = self.streamblock_obj.FILL_TYPE_PRBS
        self.streamblock_obj.InsertSig = False
        self.streamblock_obj.FrameLengthMode = self.streamblock_obj.FRAME_LENGTH_MODE_RANDOM
        self.streamblock_obj.MinFrameLength = 58
        self.streamblock_obj.MaxFrameLength = 75

        l2_config = spirent_config["l2_config"]
        l3_config = spirent_config["l3_config"]["ipv6"]
        ether_type = Ethernet2Header.INTERNET_IPV6_ETHERTYPE

        streamblock1 = template_obj.configure_stream_block(stream_block_obj=self.streamblock_obj,
                                                           port_handle=port_1, ip_header_version=6)
        fun_test.test_assert(streamblock1, "Creating streamblock on port %s" % port_1)

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=self.streamblock_obj.spirent_handle,
                                                               source_mac=l2_config['source_mac'],
                                                               destination_mac=l2_config['destination_mac'],
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Adding source and destination mac")

        # Adding Ip address and gateway
        ip = template_obj.stc_manager.configure_ip_address(streamblock=self.streamblock_obj.spirent_handle,
                                                           source=l3_config['source_ip1'],
                                                           destination=l3_config['destination_ip1'])
        fun_test.test_assert(ip, "Adding source ip, dest ip and gateway")

    def run(self):
        super(IPv6RuntTestCase2, self).run()

    def cleanup(self):
        super(IPv6RuntTestCase2, self).cleanup()


class BroadcastTestCase4(FunTestCase):

    def describe(self):
        self.set_test_details(id=4,
                              summary="Test DUT broadcast frames",
                              steps="""
                        1. Create with following settings
                           a. Load: 10 fps
                           b. Frame Size: 64 
                           c. Payload Fill Type: PRBS
                           d. Insert Signature False
                           e. Headers: EthernetII and ARP
                        2. Execute traffic for 10 seconds
                        3. Check if arp is received at other end
                        4. Check DUT stats for frames with broadcast
                        """)

    def setup(self):
        if dut_config['enable_dpcsh']:
            # Clear port results on DUT
            clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
            fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

            clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
            fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

    def cleanup(self):
        pass

    def run(self):
        duration_seconds = 10
        fun_test.log("Creating streamblock")
        streamblock = StreamBlock(fixed_frame_length=64, insert_signature=False,
                                  load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND, load=10,
                                  fill_type=StreamBlock.FILL_TYPE_PRBS)
        config_streamblock = template_obj.configure_stream_block(stream_block_obj=streamblock, port_handle=port_1)
        fun_test.test_assert(config_streamblock, " Created streamblock %s" % streamblock._spirent_handle)

        fun_test.log("Adding ethernet frame")
        ethernet = Ethernet2Header(destination_mac=Ethernet2Header.BROADCAST_MAC,
                                   ether_type=Ethernet2Header.ARP_ETHERTYPE)
        config_ethernet = template_obj.stc_manager.configure_frame_stack(stream_block_handle=streamblock._spirent_handle,
                                                                         header_obj=ethernet)
        fun_test.test_assert(config_ethernet, "Ethernet frame added to streamblock")

        fun_test.log("Adding ARP into streamblock")
        arp = ARP()
        config_arp = template_obj.stc_manager.configure_frame_stack(stream_block_handle=streamblock._spirent_handle,
                                                                    header_obj=arp)
        fun_test.test_assert(config_arp, "ARP added to streamblock %s" % streamblock._spirent_handle)

        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=gen_obj)
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=duration_seconds)

        project = template_obj.stc_manager.get_project_handle()
        subscribe_results = template_obj.subscribe_to_all_results(parent=project)
        fun_test.test_assert(subscribe_results['result'], "Subscribing to results")
        del subscribe_results['result']

        result_dict = template_obj.stc_manager.fetch_streamblock_results(subscribe_result=subscribe_results,
                                                                         streamblock_handle_list=[
                                                                             streamblock._spirent_handle],
                                                                         tx_result=True, rx_result=False)

        port_dict = template_obj.stc_manager.fetch_port_results(subscribe_result=subscribe_results,
                                                                port_handle_list=[port_2],
                                                                analyzer_result=True)
        if dut_config['enable_dpcsh']:
            # Fetch results from dut
            dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1)
            dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2)

            dut_port_1_broadcast_receive = get_dut_output_stats_value(dut_port_1_results, IF_IN_BROADCAST_PKTS, tx=False)
            dut_port_1_good_receive = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)

            # Currently getting dropped
            # TODO: Change later

            expected_rx_count = 0
            fun_test.test_assert_expected(expected=int(result_dict[streamblock._spirent_handle]['tx_result']['FrameCount']),
                                          actual=int(dut_port_1_good_receive),
                                          message="Ensure frames are received as good")

            fun_test.test_assert_expected(expected=int(result_dict[streamblock._spirent_handle]['tx_result']['FrameCount']),
                                          actual=int(dut_port_1_broadcast_receive),
                                          message="Ensure frames are received as broadcast on dut port %s" % dut_port_1)


if __name__ == "__main__":
    test_case_mode = fun_test.get_local_setting(setting="ip_version")
    ts = SpirentSetup()
    test_case_mode = test_case_mode if test_case_mode else 4

    if test_case_mode == 6:
        ts.add_test_case(IPv6GoodFrameTestCase1())
        # ts.add_test_case(IPv6RuntTestCase2())
        # ts.add_test_case(IPv6GoodRuntTestCase3())
    elif test_case_mode == 4:
        ts.add_test_case(IPv4GoodFrameTestCase1())
        ts.add_test_case(IPv4RuntTestCase2())
    else:
        ts.add_test_case(IPv4GoodFrameTestCase1())
        ts.add_test_case(IPv4RuntTestCase2())

        ts.add_test_case(IPv6GoodFrameTestCase1())
        # ts.add_test_case(IPv6RuntTestCase2())
        # ts.add_test_case(IPv6GoodRuntTestCase3())

    # ts.add_test_case(BroadcastTestCase4())
    ts.run()
