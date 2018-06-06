from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, GeneratorConfig, Ethernet2Header, ARP
from lib.host.network_controller import NetworkController
from helper import *

num_ports = 2


class SpirentSetup(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
                1. Create Spirent template
                2. Connect chassis, labserver and licenseserver
                3. Attach Ports
                """)

    def setup(self):
        global template_obj, port_1, port_2, srcMac, srcIp, destMac, destIp, gateway, ether_type, gen_obj, \
            gen_config_obj, network_controller_obj, dut_port_1, dut_port_2

        fun_test.log("Creating Template object")
        template_obj = SpirentEthernetTrafficTemplate(session_name="mac-sanity")
        fun_test.test_assert(template_obj, "Create template object")

        result = template_obj.setup(no_of_ports_needed=num_ports)
        fun_test.test_assert(result['result'], "Configure setup")

        port_1 = result['port_list'][0]
        port_2 = result['port_list'][1]

        # Create network controller object
        dpcsh_server_ip = template_obj.stc_manager.dpcsh_server_config['dpcsh_server_ip']
        dpcsh_server_port = int(template_obj.stc_manager.dpcsh_server_config['dpcsh_server_port'])
        network_controller_obj = NetworkController(dpc_server_ip=dpcsh_server_ip, dpc_server_port=dpcsh_server_port)

        srcMac = template_obj.stc_manager.dut_config['source_mac1']
        destMac = template_obj.stc_manager.dut_config['destination_mac1']
        srcIp = template_obj.stc_manager.dut_config['source_ip1']
        destIp = template_obj.stc_manager.dut_config['destination_ip1']
        dut_port_1 = template_obj.stc_manager.dut_config['port_nos'][0]
        dut_port_2 = template_obj.stc_manager.dut_config['port_nos'][1]
        gateway = template_obj.stc_manager.dut_config['gateway1']
        ether_type = "0800"

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


class TestCase1(FunTestCase):
    streamblock_obj = None
    subscribe_results = None

    def describe(self):
        self.set_test_details(id=1,
                              summary="Creating good streamblock",
                              steps="""
                        1. Create streamblock with load=500 and loadunit=fps and framelength as random
                        2. Configure generator with duration=30
                        3. Start traffic for specified duration 
                        4. subscribe to tx and rx results on streamblock
                        4. Compare Tx and Rx results for frame count. Both must be same
                        5. Check for error counters. there must be no error counter
                        6. Verify frame count matches on dut ingress and egress
                        """)

    def setup(self):
        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

    def cleanup(self):
        fun_test.log("In testcase cleanup")
        fun_test.log("Deleting streamblock %s " % self.streamblock_obj.spirent_handle)
        template_obj.delete_streamblocks(streamblock_handle_list=[self.streamblock_obj.spirent_handle])
        if self.subscribe_results:
            # clear port results
            port_results = template_obj.stc_manager.clear_all_port_results(port_list=[port_1, port_2])
            fun_test.simple_assert(port_results, "Clear port results")

    def run(self):
        duration_seconds = 30
        Load = 500
        self.streamblock_obj = StreamBlock()
        self.streamblock_obj.LoadUnit = self.streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        self.streamblock_obj.Load = Load
        self.streamblock_obj.FillType = self.streamblock_obj.FILL_TYPE_PRBS
        self.streamblock_obj.InsertSig = True
        self.streamblock_obj.FrameLengthMode = self.streamblock_obj.FRAME_LENGTH_MODE_RANDOM
        self.streamblock_obj.MinFrameLength = 74
        self.streamblock_obj.MaxFrameLength = 1500

        streamblock1 = template_obj.configure_stream_block(self.streamblock_obj, port_1)
        fun_test.test_assert(streamblock1, "Creating streamblock on port %s" % port_1)

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=self.streamblock_obj.spirent_handle,
                                                               source_mac=srcMac,
                                                               destination_mac=destMac,
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Adding source and destination mac")

        # Adding Ip address and gateway
        ip = template_obj.stc_manager.configure_ip_address(streamblock=self.streamblock_obj.spirent_handle,
                                                           source=srcIp,
                                                           destination=destIp,
                                                           gateway=gateway)
        fun_test.test_assert(ip, "Adding source ip, dest ip and gateway")

        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=gen_obj)
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=duration_seconds)

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

        fun_test.log("Tx Results %s " % tx_results)
        fun_test.log("Rx Results %s" % rx_results)
        fun_test.log("Rx Port Analyzer Results %s" % rx_port_analyzer_results)

        fun_test.test_assert(template_obj.compare_result_attribute(tx_results,rx_results), "Check FrameCount")

        zero_counter_seen = template_obj.check_non_zero_error_count(rx_port_analyzer_results)
        fun_test.test_assert(zero_counter_seen['result'], "Check for error counters")

        dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1)
        fun_test.test_assert(dut_port_1_results, message="Ensure stats are obtained for %s" % dut_port_1)
        dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2)
        fun_test.test_assert(dut_port_2_results, message="Ensure stats are obtained for %s" % dut_port_2)

        dut_port_2_transmit = get_dut_output_stats_value(dut_port_2_results, FRAMES_TRANSMITTED_OK)
        dut_port_1_receive = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)

        fun_test.test_assert_expected(expected=int(dut_port_1_receive), actual=int(dut_port_2_transmit),
                                      message="Ensure frames received on DUT port %s are transmitted from DUT port %s"
                                              % (dut_port_1, dut_port_2))

        fun_test.test_assert_expected(expected=int(dut_port_2_transmit), actual=int(rx_results['FrameCount']),
                                      message="Ensure frames transmitted from DUT and counter on spirent match")


class TestCase2(FunTestCase):
    streamblock_obj = None
    subscribe_results = None

    def describe(self):
        self.set_test_details(id=2,
                              summary="Creating runt streamblock",
                              steps="""
                        1. Create streamblock with load=500 and loadunit=fps and frame length between 40 and 60
                        2. Configure generator with duration=30
                        3. Start traffic and subscribe to tx and rx results and analyzer results
                        4. Received frame count from analyzer port must be 0
                        5. Dropped frame count from analyzer port must be equal to the frames transmitted
                        6. Ensure undersize frames are received on dut ingress
                        7. Check psw global stats for cpr_sop_drop_pkt, fwd_frv, main_pkt_drop_eop, cpr_feop_pkt, 
                        ifpg_pkt
                        """)

    def setup(self):
        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

    def cleanup(self):
        fun_test.log("In testcase cleanup")
        fun_test.log("Deleting streamblock %s " % self.streamblock_obj.spirent_handle)
        template_obj.delete_streamblocks(streamblock_handle_list=[self.streamblock_obj.spirent_handle])
        if self.subscribe_results:
            # clear port results
            port_results = template_obj.stc_manager.clear_all_port_results(port_list=[port_1, port_2])
            fun_test.simple_assert(port_results, "Clear port results")

    def run(self):
        duration_seconds = 30
        Load = 500
        self.streamblock_obj = StreamBlock()
        self.streamblock_obj.LoadUnit = self.streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        self.streamblock_obj.Load = Load
        self.streamblock_obj.FillType = self.streamblock_obj.FILL_TYPE_PRBS
        self.streamblock_obj.InsertSig = False
        self.streamblock_obj.FrameLengthMode = self.streamblock_obj.FRAME_LENGTH_MODE_RANDOM
        self.streamblock_obj.MinFrameLength = 40
        self.streamblock_obj.MaxFrameLength = 60

        streamblock1 = template_obj.configure_stream_block(self.streamblock_obj, port_1)
        fun_test.test_assert(streamblock1, "Creating streamblock on port %s" % port_1)

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=self.streamblock_obj.spirent_handle,
                                                               source_mac=srcMac,
                                                               destination_mac=destMac,
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Adding source and destination mac")

        # Adding Ip address and gateway
        ip = template_obj.stc_manager.configure_ip_address(streamblock=self.streamblock_obj.spirent_handle,
                                                           source=srcIp,
                                                           destination=destIp,
                                                           gateway=gateway)
        fun_test.test_assert(ip, "Adding source ip, dest ip and gateway")

        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=gen_obj)
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=duration_seconds)

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

        fun_test.log("Tx Results %s " % tx_results)
        fun_test.log("Rx Results %s" % rx_results)
        fun_test.log("Rx Port Analyzer Results %s" % rx_port_analyzer_results)
        fun_test.log("Tx Port Generator Results %s" % tx_port_generator_results)

        # Check frame counts
        frames_received = 0
        fun_test.test_assert_expected(actual=int(rx_port_analyzer_results['TotalFrameCount']), expected=frames_received,
                                      message="Ensure no frame is received")

        dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2)
        fun_test.test_assert(dut_port_2_results, message="Ensure stats are obtained for %s" % dut_port_2)
        dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1)
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

class TestCase3(FunTestCase):
    streamblock_obj = None
    subscribe_results = None

    def describe(self):
        self.set_test_details(id=3,
                              summary="Creating good and runt streamblock",
                              steps="""
                        1. Create streamblock with load=1 fps and frame length between 40 and 70 and 
                           incremental step size of 1
                        2. Configure generator with duration=max - min frame length
                        3. Start traffic and subscribe to tx and rx results and analyzer results
                        4. Runts must be dropped and good frames must be received
                        5. Ensure count of good frames + undersize generated match tx of stream.
                        6. Ensure runts are not transmitted from dut egress.
                        7. Ensure dut egress receives undersize frames
                        """)

    def setup(self):
        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

    def cleanup(self):
        fun_test.log("In testcase cleanup")
        fun_test.log("Deleting streamblock %s " % self.streamblock_obj.spirent_handle)
        template_obj.delete_streamblocks(streamblock_handle_list=[self.streamblock_obj.spirent_handle])
        if self.subscribe_results:
            # clear port results
            port_results = template_obj.stc_manager.clear_all_port_results(port_list=[port_1, port_2])
            fun_test.simple_assert(port_results, "Clear port results")

    def run(self):
        Load = 21000
        self.streamblock_obj = StreamBlock()
        self.streamblock_obj.LoadUnit = self.streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        self.streamblock_obj.Load = Load
        self.streamblock_obj.FillType = self.streamblock_obj.FILL_TYPE_PRBS
        self.streamblock_obj.InsertSig = False
        self.streamblock_obj.FrameLengthMode = self.streamblock_obj.FRAME_LENGTH_MODE_RANDOM
        self.streamblock_obj.MinFrameLength = 40
        self.streamblock_obj.MaxFrameLength = 70
        duration_seconds = 30

        # Change generator config parameters
        gen_config_obj.Duration = duration_seconds
        config_obj = template_obj.configure_generator_config(port_handle=port_1,
                                                             generator_config_obj=gen_config_obj)
        fun_test.test_assert(config_obj, "Creating generator config")

        # Create streamblock
        streamblock1 = template_obj.configure_stream_block(self.streamblock_obj, port_1)
        fun_test.test_assert(streamblock1, "Creating streamblock on port %s" % port_1)

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=self.streamblock_obj.spirent_handle,
                                                               source_mac=srcMac,
                                                               destination_mac=destMac,
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Adding source and destination mac")

        # Adding Ip address and gateway
        ip = template_obj.stc_manager.configure_ip_address(streamblock=self.streamblock_obj.spirent_handle,
                                                           source=srcIp,
                                                           destination=destIp,
                                                           gateway=gateway)
        fun_test.test_assert(ip, "Adding source ip, dest ip and gateway")

        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=gen_obj)
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=duration_seconds)

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

        fun_test.log("Fetching rx port results for subscribed object %s" % self.subscribe_results['generator_subscribe'])
        tx_port_generator_results = template_obj.stc_manager.get_generator_port_results(
            port_handle=port_1, subscribe_handle=self.subscribe_results['generator_subscribe'])

        fun_test.log("Fetching tx port results for subscribed object %s" % self.subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_2, subscribe_handle=self.subscribe_results['analyzer_subscribe'])

        fun_test.log("Tx Results %s " % tx_results)
        fun_test.log("Rx Results %s " % rx_results)
        fun_test.log("Tx Generator resukts %s" % tx_port_generator_results)
        fun_test.log("Rx Port Analyzer Results %s" % rx_port_analyzer_results)

        fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                      actual=int(tx_port_generator_results['GeneratorUndersizeFrameCount']) +
                                             int(rx_port_analyzer_results['TotalFrameCount']),
                                      message="Ensure transmitted match with undersize + received")

        fun_test.test_assert_expected(expected=0, actual=int(rx_port_analyzer_results['FcsErrorFrameCount']),
                                      message="Ensure no FCS errors are seen")

        dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2)
        fun_test.test_assert(dut_port_2_results, message="Ensure stats are obtained for %s" % dut_port_2)

        dut_port_2_transmit = get_dut_output_stats_value(dut_port_2_results, FRAMES_TRANSMITTED_OK)
        fun_test.test_assert_expected(actual=int(dut_port_2_transmit),
                                      expected=int(rx_port_analyzer_results['TotalFrameCount']),
                                      message="Ensure frames transmitted is None")

        dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1)
        fun_test.test_assert(dut_port_1_results, message="Ensure stats are obtained for %s" % dut_port_1)

        dut_port_1_undersize_pkts = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_UNDERSIZE_PKTS, tx=False)
        fun_test.test_assert_expected(expected=int(tx_port_generator_results['GeneratorUndersizeFrameCount']),
                                      actual=int(dut_port_1_undersize_pkts),
                                      message="Ensure packets are marked undersize on rx port of dut")

class TestCase4(FunTestCase):

    def describe(self):
        self.set_test_details(id=4,
                              summary="Test DUT broadcast frames",
                              steps="""
                        1. Create an Ethernet frame having destination mac as FF:FF:FF:FF:FF:FF
                        2. Add an arp into the streamblock
                        3. Execute traffic for 10 seconds
                        4. Check if arp is received at other end
                        5. Check DUT stats for frames with broadcast
                        """)

    def setup(self):
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
    ts = SpirentSetup()
    ts.add_test_case(TestCase1())
    ts.add_test_case(TestCase2())
    ts.add_test_case(TestCase3())
    ts.add_test_case(TestCase4())
    ts.run()
