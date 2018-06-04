from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, GeneratorConfig
from lib.host.network_controller import NetworkController
from helper import *


num_ports = 2
loads_file = "interface_loads.json"


class SpirentSetup(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
                1. Create Spirent template
                2. Connect chassis, labserver and licenseserver
                3. Attach Ports
                4. Create two streamblocks with frame mode as incremental from min size 64B to 16380B and step as 1 on 
                   each port.
                5. Configure generator that runs traffic for specified amount.
                6. Subscribe to tx, rx and analyzer results
                """)

    def setup(self):
        global template_obj, port_1, port_2, interface_1_obj, interface_2_obj, streamblock_obj_1, streamblock_obj_2, \
        gen_obj_1, gen_obj_2, duration_seconds, subscribe_results, dut_port_2, dut_port_1, network_controller_obj

        fun_test.log("Creating Template object")
        template_obj = SpirentEthernetTrafficTemplate(session_name="test_frame_size")
        fun_test.test_assert(template_obj, "Create template object")

        # Create network controller object
        dpcsh_server_ip = template_obj.stc_manager.dpcsh_server_config['dpcsh_server_ip']
        dpcsh_server_port = int(template_obj.stc_manager.dpcsh_server_config['dpcsh_server_port'])
        network_controller_obj = NetworkController(dpc_server_ip=dpcsh_server_ip, dpc_server_port=dpcsh_server_port)

        result = template_obj.setup(no_of_ports_needed=num_ports)
        fun_test.test_assert(result['result'], "Configure setup")

        port_1 = result['port_list'][0]
        port_2 = result['port_list'][1]

        srcMac = template_obj.stc_manager.dut_config['source_mac1']
        destMac = template_obj.stc_manager.dut_config['destination_mac1']
        srcIp = template_obj.stc_manager.dut_config['source_ip1']
        destIp = template_obj.stc_manager.dut_config['destination_ip1']
        destIp2 = template_obj.stc_manager.dut_config['destination_ip2']
        dut_port_1 = template_obj.stc_manager.dut_config['port_nos'][0]
        dut_port_2 = template_obj.stc_manager.dut_config['port_nos'][1]
        gateway = template_obj.stc_manager.dut_config['gateway1']
        interface_mode = template_obj.stc_manager.interface_mode

        #  Read loads from file
        file_path = fun_test.get_script_parent_directory() + "/" + loads_file
        output = fun_test.parse_file_to_json(file_path)
        Load = output[interface_mode]["incremental_load_mbps"]
        ether_type = "0800"
        min_frame_lenggth = 64
        max_frame_length = 16380
        mtu = max_frame_length
        generator_step = max_frame_length
        duration_seconds = 240
        step_size = 1

        # Set Mtu
        interface_1_obj = result['interface_obj_list'][0]
        interface_2_obj = result['interface_obj_list'][1]
        interface_1_obj.Mtu = mtu
        interface_2_obj.Mtu = mtu

        set_mtu_1 = template_obj.configure_physical_interface(interface_1_obj)
        fun_test.test_assert(set_mtu_1, "Set mtu on %s " % interface_1_obj)
        set_mtu_2 = template_obj.configure_physical_interface(interface_2_obj)
        fun_test.test_assert(set_mtu_2, "Set mtu on %s " % interface_2_obj)

        # Set mtu on DUT
        mtu_1 = network_controller_obj.set_port_mtu(port_num=dut_port_1, mtu_value=mtu)
        fun_test.test_assert(mtu_1, " Set mtu on DUT port %s" % dut_port_1)
        mtu_2 = network_controller_obj.set_port_mtu(port_num=dut_port_2, mtu_value=mtu)
        fun_test.test_assert(mtu_2, " Set mtu on DUT port %s" % dut_port_2)

        # Create streamblock 1
        streamblock_obj_1 = StreamBlock()
        streamblock_obj_1.LoadUnit = streamblock_obj_1.LOAD_UNIT_MEGABITS_PER_SECOND
        streamblock_obj_1.Load = Load
        streamblock_obj_1.FillType = streamblock_obj_1.FILL_TYPE_PRBS
        streamblock_obj_1.InsertSig = True
        streamblock_obj_1.FrameLengthMode = streamblock_obj_1.FRAME_LENGTH_MODE_INCR
        streamblock_obj_1.MinFrameLength = min_frame_lenggth
        streamblock_obj_1.MaxFrameLength = max_frame_length
        streamblock_obj_1.StepFrameLength = step_size

        streamblock1 = template_obj.configure_stream_block(streamblock_obj_1, port_1)
        fun_test.test_assert(streamblock1, "Creating streamblock on port %s" % port_1)

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=streamblock_obj_1.spirent_handle,
                                                               source_mac=srcMac,
                                                               destination_mac=destMac,
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Adding source and destination mac")

        # Adding Ip address and gateway
        ip = template_obj.stc_manager.configure_ip_address(streamblock=streamblock_obj_1.spirent_handle,
                                                           source=srcIp,
                                                           destination=destIp,
                                                           gateway=gateway)
        fun_test.test_assert(ip, "Adding source ip, dest ip and gateway")

        # Create streamblock 2
        streamblock_obj_2 = StreamBlock()
        streamblock_obj_2.LoadUnit = streamblock_obj_2.LOAD_UNIT_MEGABITS_PER_SECOND
        streamblock_obj_2.Load = Load
        streamblock_obj_2.FillType = streamblock_obj_2.FILL_TYPE_PRBS
        streamblock_obj_2.InsertSig = True
        streamblock_obj_2.FrameLengthMode = streamblock_obj_2.FRAME_LENGTH_MODE_INCR
        streamblock_obj_2.MinFrameLength = min_frame_lenggth
        streamblock_obj_2.MaxFrameLength = max_frame_length
        streamblock_obj_2.StepFrameLength = step_size

        streamblock2 = template_obj.configure_stream_block(streamblock_obj_2, port_2)
        fun_test.test_assert(streamblock2, "Creating streamblock on port %s" % port_2)

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=streamblock_obj_2.spirent_handle,
                                                               source_mac=srcMac,
                                                               destination_mac=destMac,
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Adding source and destination mac")

        # Adding Ip address and gateway
        ip = template_obj.stc_manager.configure_ip_address(streamblock=streamblock_obj_2.spirent_handle,
                                                           source=srcIp,
                                                           destination=destIp2,
                                                           gateway=gateway)
        fun_test.test_assert(ip, "Adding source ip, dest ip and gateway")

        # Configure Generator
        gen_config_obj = GeneratorConfig()
        gen_config_obj.Duration = duration_seconds
        gen_config_obj.SchedulingMode = gen_config_obj.SCHEDULING_MODE_RATE_BASED
        gen_config_obj.DurationMode = gen_config_obj.DURATION_MODE_STEP
        gen_config_obj.AdvancedInterleaving = True
        gen_config_obj.StepSize = generator_step

        # Apply generator config on port 1
        gen_obj_1 = template_obj.stc_manager.get_generator(port_handle=port_1)
        config_obj = template_obj.configure_generator_config(port_handle=port_1,
                                                             generator_config_obj=gen_config_obj)
        fun_test.test_assert(config_obj, "Creating generator config on port %s" % port_1)

        # Apply generator config on port 2
        gen_obj_2 = template_obj.stc_manager.get_generator(port_handle=port_2)
        config_obj = template_obj.configure_generator_config(port_handle=port_2,
                                                             generator_config_obj=gen_config_obj)
        fun_test.test_assert(config_obj, "Creating generator config on port %s" % port_2)

        # Applying configuration
        apply = template_obj.stc_manager.apply_configuration()
        fun_test.test_assert(apply, "Applying Generator config")

        # Subscribe to results
        project = template_obj.stc_manager.get_project_handle()
        subscribe_results = template_obj.subscribe_to_all_results(parent=project)
        fun_test.test_assert(subscribe_results['result'], "Subscribing to results")
        del subscribe_results['result']

    def cleanup(self):
        fun_test.test_assert(template_obj.cleanup(), "Cleaning up session")


class TestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Test all frame size ",
                              steps="""
                        3. Start traffic and subscribe to tx and rx results
                        4. Compare Tx and Rx results for frame count
                        5. Check for error counters. there must be no error counter
                        6. Verify number of frames received is more than max frame length
                        """)

    def setup(self):
        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

    def cleanup(self):
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=[gen_obj_1, gen_obj_2])
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic for %s seconds" % duration_seconds, seconds=duration_seconds)

        # Get results for streamblock 1
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_obj_1.spirent_handle))
        tx_results_1 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_obj_1.spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_obj_1.spirent_handle))
        rx_results_1 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_obj_1.spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        # Get streambllock 2 results
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_obj_2.spirent_handle))
        tx_results_2 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_obj_2.spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_obj_2.spirent_handle))
        rx_results_2 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_obj_2.spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        fun_test.log("Fetching rx port results for subscribed object %s" % subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results_2 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_2, subscribe_handle=subscribe_results['analyzer_subscribe'])

        fun_test.log("Fetching rx port results for subscribed object %s" % subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results_1 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_1, subscribe_handle=subscribe_results['analyzer_subscribe'])

        fun_test.log("Tx 1 Results %s " % tx_results_1)
        fun_test.log("Rx 1 Results %s" % rx_results_1)
        fun_test.log("Tx 2 Results %s " % tx_results_2)
        fun_test.log("Rx 2 Results %s" % rx_results_2)
        fun_test.log("Rx Port Analyzer Results %s" % rx_port_analyzer_results_1)
        fun_test.log("Rx Port Analyzer Results %s" % rx_port_analyzer_results_2)

        fun_test.test_assert(template_obj.compare_result_attribute(tx_results_1, rx_results_1),
                             "Check FrameCount for streamblock %s" % streamblock_obj_1.spirent_handle)
        fun_test.test_assert(template_obj.compare_result_attribute(tx_results_2, rx_results_2),
                             "Check FrameCount for streamblock %s" % streamblock_obj_2.spirent_handle)

        zero_counter_seen = template_obj.check_non_zero_error_count(rx_port_analyzer_results_1)
        fun_test.test_assert(zero_counter_seen['result'], "Check for error counters on port2")

        zero_counter_seen = template_obj.check_non_zero_error_count(rx_port_analyzer_results_2)
        fun_test.test_assert(zero_counter_seen['result'], "Check for error counters on port1")

        fun_test.test_assert(int(rx_results_1['FrameCount']) >= int(streamblock_obj_1.MaxFrameLength),
                             "Ensure more than %s packets are received on port2" % str(streamblock_obj_1.MaxFrameLength))

        fun_test.test_assert(int(rx_results_2['FrameCount']) >= int(streamblock_obj_1.MaxFrameLength),
                             "Ensure more than %s packets are received on port1" % str(streamblock_obj_1.MaxFrameLength))

        dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1)
        fun_test.test_assert(dut_port_1_results, message="Ensure stats are obtained for %s" % dut_port_1)
        dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2)
        fun_test.test_assert(dut_port_2_results, message="Ensure stats are obtained for %s" % dut_port_2)

        dut_port_1_transmit = get_dut_output_stats_value(dut_port_1_results, FRAMES_TRANSMITTED_OK)
        dut_port_2_transmit = get_dut_output_stats_value(dut_port_2_results, FRAMES_TRANSMITTED_OK)
        dut_port_1_receive = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)
        dut_port_2_receive = get_dut_output_stats_value(dut_port_2_results, FRAMES_RECEIVED_OK, tx=False)

        # ether stats pkts
        dut_port_1_rx_eth_stats_pkts = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_PKTS, tx=False)
        dut_port_2_rx_eth_stats_pkts = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_PKTS, tx=False)
        dut_port_1_tx_eth_stats_pkts = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_PKTS)
        dut_port_2_tx_eth_stats_pkts = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_PKTS)

        # Octet count
        dut_port_1_rx_octet_stats = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_OCTETS, tx=False)
        dut_port_1_tx_octet_stats = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_OCTETS)
        dut_port_2_rx_octet_stats = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_OCTETS, tx=False)
        dut_port_2_tx_octet_stats = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_OCTETS)

        # Get rx octet range
        dut_port_1_rx_octet_64 = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_PKTS_64_OCTETS, tx=False)
        dut_port_1_rx_octet_65_127 = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_PKTS_65_TO_127_OCTETS,
                                                                tx=False)
        dut_port_1_rx_octet_128_255 = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_PKTS_128_TO_255_OCTETS,
                                                                 tx=False)
        dut_port_1_rx_octet_256_511 = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_PKTS_256_TO_511_OCTETS,
                                                                 tx=False)
        dut_port_1_rx_octet_512_1023 = get_dut_output_stats_value(dut_port_1_results,
                                                                  ETHER_STATS_PKTS_512_TO_1023_OCTETS,
                                                                  tx=False)
        dut_port_1_rx_octet_1024_1518 = get_dut_output_stats_value(dut_port_1_results,
                                                                   ETHER_STATS_PKTS_1024_TO_1518_OCTETS,
                                                                   tx=False)
        dut_port_1_rx_octet_1519_max = get_dut_output_stats_value(dut_port_1_results,
                                                                  ETHER_STATS_PKTS_1519_TO_MAX_OCTETS,
                                                                  tx=False)

        dut_port_2_rx_octet_64 = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_PKTS_64_OCTETS, tx=False)
        dut_port_2_rx_octet_65_127 = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_PKTS_65_TO_127_OCTETS,
                                                                tx=False)
        dut_port_2_rx_octet_128_255 = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_PKTS_128_TO_255_OCTETS,
                                                                 tx=False)
        dut_port_2_rx_octet_256_511 = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_PKTS_256_TO_511_OCTETS,
                                                                 tx=False)
        dut_port_2_rx_octet_512_1023 = get_dut_output_stats_value(dut_port_2_results,
                                                                  ETHER_STATS_PKTS_512_TO_1023_OCTETS,
                                                                  tx=False)
        dut_port_2_rx_octet_1024_1518 = get_dut_output_stats_value(dut_port_2_results,
                                                                   ETHER_STATS_PKTS_1024_TO_1518_OCTETS,
                                                                   tx=False)
        dut_port_2_rx_octet_1519_max = get_dut_output_stats_value(dut_port_2_results,
                                                                  ETHER_STATS_PKTS_1519_TO_MAX_OCTETS,
                                                                  tx=False)

        # Get tx octet range
        dut_port_1_tx_octet_64 = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_PKTS_64_OCTETS)
        dut_port_1_tx_octet_65_127 = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_PKTS_65_TO_127_OCTETS)
        dut_port_1_tx_octet_128_255 = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_PKTS_128_TO_255_OCTETS)
        dut_port_1_tx_octet_256_511 = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_PKTS_256_TO_511_OCTETS)
        dut_port_1_tx_octet_512_1023 = get_dut_output_stats_value(dut_port_1_results,
                                                                  ETHER_STATS_PKTS_512_TO_1023_OCTETS)
        dut_port_1_tx_octet_1024_1518 = get_dut_output_stats_value(dut_port_1_results,
                                                                   ETHER_STATS_PKTS_1024_TO_1518_OCTETS)
        dut_port_1_tx_octet_1519_max = get_dut_output_stats_value(dut_port_1_results,
                                                                  ETHER_STATS_PKTS_1519_TO_MAX_OCTETS)

        dut_port_2_tx_octet_64 = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_PKTS_64_OCTETS)
        dut_port_2_tx_octet_65_127 = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_PKTS_65_TO_127_OCTETS)
        dut_port_2_tx_octet_128_255 = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_PKTS_128_TO_255_OCTETS)
        dut_port_2_tx_octet_256_511 = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_PKTS_256_TO_511_OCTETS)
        dut_port_2_tx_octet_512_1023 = get_dut_output_stats_value(dut_port_2_results,
                                                                  ETHER_STATS_PKTS_512_TO_1023_OCTETS)
        dut_port_2_tx_octet_1024_1518 = get_dut_output_stats_value(dut_port_2_results,
                                                                   ETHER_STATS_PKTS_1024_TO_1518_OCTETS)
        dut_port_2_tx_octet_1519_max = get_dut_output_stats_value(dut_port_2_results,
                                                                  ETHER_STATS_PKTS_1519_TO_MAX_OCTETS)

        dut_octet_range_stats = {dut_port_1:
                                     {'RX': {'64': dut_port_1_rx_octet_64,
                                             '127': dut_port_1_rx_octet_65_127,
                                             '255': dut_port_1_rx_octet_128_255,
                                             '511': dut_port_1_rx_octet_256_511,
                                             '1023': dut_port_1_rx_octet_512_1023,
                                             '1518': dut_port_1_rx_octet_1024_1518,
                                             'max': dut_port_1_rx_octet_1519_max},
                                      'TX': {'64': dut_port_1_tx_octet_64,
                                             '127': dut_port_1_tx_octet_65_127,
                                             '255': dut_port_1_tx_octet_128_255,
                                             '511': dut_port_1_tx_octet_256_511,
                                             '1023': dut_port_1_tx_octet_512_1023,
                                             '1518': dut_port_1_tx_octet_1024_1518,
                                             'max': dut_port_1_tx_octet_1519_max}},
                                 dut_port_2:
                                     {'RX': {'64': dut_port_2_rx_octet_64,
                                             '127': dut_port_2_rx_octet_65_127,
                                             '255': dut_port_2_rx_octet_128_255,
                                             '511': dut_port_2_rx_octet_256_511,
                                             '1023': dut_port_2_rx_octet_512_1023,
                                             '1518': dut_port_2_rx_octet_1024_1518,
                                             'max': dut_port_2_rx_octet_1519_max},
                                      'TX': {'64': dut_port_2_tx_octet_64,
                                             '127': dut_port_2_tx_octet_65_127,
                                             '255': dut_port_2_tx_octet_128_255,
                                             '511': dut_port_2_tx_octet_256_511,
                                             '1023': dut_port_2_tx_octet_512_1023,
                                             '1518': dut_port_2_tx_octet_1024_1518,
                                             'max': dut_port_2_tx_octet_1519_max}}
                                 }

        expected_octet_counters = {'64': 1, '127': 63, '255': 128, '511': 256, '1023': 1024, '1518': 495, 'max': 14862}

        # TODO: add for greater than 1518

        fun_test.test_assert_expected(expected=int(dut_port_1_receive), actual=int(dut_port_2_transmit),
                                      message="Ensure frames received on DUT port %s are transmitted from DUT port %s"
                                              % (dut_port_1, dut_port_2))

        fun_test.test_assert_expected(expected=int(dut_port_2_receive), actual=int(dut_port_1_transmit),
                                      message="Ensure frames received on DUT port %s are transmitted from DUT port %s"
                                              % (dut_port_2, dut_port_1))

        fun_test.test_assert_expected(expected=int(dut_port_2_transmit), actual=int(rx_results_1['FrameCount']),
                                      message="Ensure frames transmitted from DUT and counter on spirent match")

        fun_test.test_assert_expected(expected=int(dut_port_1_transmit), actual=int(rx_results_2['FrameCount']),
                                      message="Ensure frames transmitted from DUT and counter on spirent match")

        # Check ether stats pkts
        fun_test.test_assert_expected(expected=int(dut_port_1_rx_eth_stats_pkts),
                                      actual=int(dut_port_2_tx_eth_stats_pkts),
                                      message="Ensure eth stat pkts received by DUT port %s are transmitted "
                                              "by DUT port %s" % (dut_port_1, dut_port_2))

        fun_test.test_assert_expected(expected=int(dut_port_2_tx_eth_stats_pkts),
                                      actual=int(rx_results_1['FrameCount']),
                                      message="Ensure eth stat pkts transmitted from DUT and counter on spirent match")

        fun_test.test_assert_expected(expected=int(dut_port_2_rx_eth_stats_pkts),
                                      actual=int(dut_port_1_tx_eth_stats_pkts),
                                      message="Ensure eth stat pkts received by DUT port %s are transmitted "
                                              "by DUT port %s" % (dut_port_2, dut_port_1))

        fun_test.test_assert_expected(expected=int(dut_port_1_tx_eth_stats_pkts),
                                      actual=int(rx_results_2['FrameCount']),
                                      message="Ensure eth stat pkts transmitted from DUT and counter on spirent match")

        # Check octet counts
        fun_test.test_assert_expected(expected=int(dut_port_1_rx_octet_stats), actual=int(dut_port_2_tx_octet_stats),
                                      message="Ensure correct ether stats octets are seen on both DUT ports")

        fun_test.test_assert_expected(expected=int(tx_results_1['OctetCount']), actual=int(rx_results_1['OctetCount']),
                                      message="Ensure octet counts match on spirent rx and tx")

        fun_test.test_assert_expected(expected=int(rx_results_1['OctetCount']), actual=int(dut_port_2_tx_octet_stats),
                                      message="Ensure octets hsown on tx port of DUT matches rx of spirent")

        fun_test.test_assert_expected(expected=int(dut_port_2_rx_octet_stats), actual=int(dut_port_1_tx_octet_stats),
                                      message="Ensure correct ether stats octets are seen on both DUT ports")

        fun_test.test_assert_expected(expected=int(tx_results_2['OctetCount']), actual=int(rx_results_2['OctetCount']),
                                      message="Ensure octet counts match on spirent rx and tx")

        fun_test.test_assert_expected(expected=int(rx_results_2['OctetCount']), actual=int(dut_port_1_tx_octet_stats),
                                      message="Ensure octets hsown on tx port of DUT matches rx of spirent")

        for key, val in dut_octet_range_stats.iteritems():    # DUT level
            for key1, val1 in val.iteritems():                # RX, TX level
                for key2, val2 in val1.iteritems():           # Octet level
                    fun_test.test_assert_expected(expected=expected_octet_counters[key2], actual=int(val2),
                                                  message="Ensure correct value is seen for %s octet in %s of "
                                                          "dut port %s" % (key2, key1, key))

        '''
        fun_test.test_assert_expected(expected=expected_octet_counters['64'], actual=int(dut_port_1_rx_octet_64),
                                      message="Ensure rx dut stats has correct count for octet 64")

        fun_test.test_assert_expected(expected=expected_octet_counters['64'], actual=int(dut_port_2_tx_octet_64),
                                      message="Ensure tx dut stats has correct count for octet 64")

        fun_test.test_assert_expected(expected=expected_octet_counters['127'], actual=int(dut_port_1_rx_octet_65_127),
                                      message="Ensure rx dut stats has correct count for octet 65-127")

        fun_test.test_assert_expected(expected=expected_octet_counters['127'], actual=int(dut_port_2_tx_octet_65_127),
                                      message="Ensure tx dut stats has correct count for octet 65-127")

        fun_test.test_assert_expected(expected=expected_octet_counters['255'], actual=int(dut_port_1_rx_octet_128_255),
                                      message="Ensure rx dut stats has correct count for octet 128-255")

        fun_test.test_assert_expected(expected=expected_octet_counters['255'], actual=int(dut_port_2_tx_octet_128_255),
                                      message="Ensure tx dut stats has correct count for octet 128-255")

        fun_test.test_assert_expected(expected=expected_octet_counters['511'], actual=int(dut_port_1_rx_octet_256_511),
                                      message="Ensure rx dut stats has correct count for octet 256-511")

        fun_test.test_assert_expected(expected=expected_octet_counters['511'], actual=int(dut_port_2_tx_octet_256_511),
                                      message="Ensure tx dut stats has correct count for octet 256-511")

        fun_test.test_assert_expected(expected=expected_octet_counters['1023'], actual=int(dut_port_1_rx_octet_512_1023),
                                      message="Ensure rx dut stats has correct count for octet 512-1023")

        fun_test.test_assert_expected(expected=expected_octet_counters['1023'], actual=int(dut_port_2_tx_octet_512_1023),
                                      message="Ensure tx dut stats has correct count for octet 512-1023")

        fun_test.test_assert_expected(expected=expected_octet_counters['1518'], actual=int(dut_port_1_rx_octet_1024_1518),
                                      message="Ensure rx dut stats has correct count for octet 1024-1518")

        fun_test.test_assert_expected(expected=expected_octet_counters['1518'], actual=int(dut_port_2_tx_octet_1024_1518),
                                      message="Ensure tx dut stats has correct count for octet 1024-1518")
        '''

class TestCase2(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Test large random frame size",
                              steps="""
                        1. Start traffic and subscribe to tx and rx results
                        2. Compare Tx and Rx results for frame count for each stream
                        3. Check for error counters. there must be no error counter
                        """)

    def setup(self):
        streamblock_obj_1.FrameLengthMode = streamblock_obj_1.FRAME_LENGTH_MODE_RANDOM
        streamblock_obj_2.FrameLengthMode = streamblock_obj_2.FRAME_LENGTH_MODE_RANDOM

        streamblock1 = template_obj.stc_manager.stc.config(streamblock_obj_1.spirent_handle,
                                                           FrameLengthMode=streamblock_obj_1.FrameLengthMode)
        fun_test.log("Update streamblock %s on port %s" % (streamblock_obj_1.spirent_handle,
                                                                                    port_1))

        streamblock2 = template_obj.stc_manager.stc.config(streamblock_obj_2.spirent_handle,
                                                           FrameLengthMode=streamblock_obj_2.FrameLengthMode)
        fun_test.log("Update streamblock %s on port %s" % (streamblock_obj_2.spirent_handle,
                                                                                    port_2))

        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

    def cleanup(self):
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        # Execute traffic

        start = template_obj.enable_generator_configs(generator_configs=[gen_obj_1, gen_obj_2])
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic for %s seconds" % duration_seconds, seconds=duration_seconds)

        # Get results for streamblock 1
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_obj_1.spirent_handle))
        tx_results_1 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_obj_1.spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_obj_1.spirent_handle))
        rx_results_1 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_obj_1.spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        # Get streambllock 2 results
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_obj_2.spirent_handle))
        tx_results_2 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_obj_2.spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_obj_2.spirent_handle))
        rx_results_2 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_obj_2.spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        fun_test.log("Fetching rx port results for subscribed object %s" % subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results_2 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_2, subscribe_handle=subscribe_results['analyzer_subscribe'])

        fun_test.log("Fetching rx port results for subscribed object %s" % subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results_1 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_1, subscribe_handle=subscribe_results['analyzer_subscribe'])

        fun_test.log("Tx 1 Results %s " % tx_results_1)
        fun_test.log("Rx 1 Results %s" % rx_results_1)
        fun_test.log("Tx 2 Results %s " % tx_results_2)
        fun_test.log("Rx 2 Results %s" % rx_results_2)
        fun_test.log("Rx Port Analyzer Results %s" % rx_port_analyzer_results_1)
        fun_test.log("Rx Port Analyzer Results %s" % rx_port_analyzer_results_2)

        fun_test.test_assert(template_obj.compare_result_attribute(tx_results_1, rx_results_1),
                             "Check FrameCount for streamblock %s" % streamblock_obj_1.spirent_handle)
        fun_test.test_assert(template_obj.compare_result_attribute(tx_results_2, rx_results_2),
                             "Check FrameCount for streamblock %s" % streamblock_obj_2.spirent_handle)

        zero_counter_seen = template_obj.check_non_zero_error_count(rx_port_analyzer_results_1)
        fun_test.test_assert(zero_counter_seen['result'], "Check for error counters on port2")

        zero_counter_seen = template_obj.check_non_zero_error_count(rx_port_analyzer_results_2)
        fun_test.test_assert(zero_counter_seen['result'], "Check for error counters on port1")

        dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1)
        fun_test.test_assert(dut_port_1_results, message="Ensure stats are obtained for %s" % dut_port_1)
        dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2)
        fun_test.test_assert(dut_port_2_results, message="Ensure stats are obtained for %s" % dut_port_2)

        dut_port_1_transmit = get_dut_output_stats_value(dut_port_1_results, FRAMES_TRANSMITTED_OK)
        dut_port_2_transmit = get_dut_output_stats_value(dut_port_2_results, FRAMES_TRANSMITTED_OK)
        dut_port_1_receive = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)
        dut_port_2_receive = get_dut_output_stats_value(dut_port_2_results, FRAMES_RECEIVED_OK, tx=False)

        fun_test.test_assert_expected(expected=int(dut_port_1_receive), actual=int(dut_port_2_transmit),
                                      message="Ensure frames received on DUT port %s are transmitted from DUT port %s"
                                              % (dut_port_1, dut_port_2))

        fun_test.test_assert_expected(expected=int(dut_port_2_receive), actual=int(dut_port_1_transmit),
                                      message="Ensure frames received on DUT port %s are transmitted from DUT port %s"
                                              % (dut_port_2, dut_port_1))

        fun_test.test_assert_expected(expected=int(dut_port_2_transmit), actual=int(rx_results_1['FrameCount']),
                                      message="Ensure frames transmitted from DUT and counter on spirent match")

        fun_test.test_assert_expected(expected=int(dut_port_1_transmit), actual=int(rx_results_2['FrameCount']),
                                      message="Ensure frames transmitted from DUT and counter on spirent match")

        '''
        psw_stats = network_controller_obj.peek_psw_global_stats()
        fun_test.simple_assert(psw_stats, message="Ensure psw stats are received")

        fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']) + int(tx_results_2['FrameCount']),
                                      actual=int(psw_stats['input']['fwd_frv']),
                                      message="Check all packets are seen in fwd_frv")

        fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']) + int(tx_results_2['FrameCount']),
                                      actual=int(psw_stats['input']['ifpg1_pkt']),
                                      message="Check all packets are seen in ifpg1_pkt")

        fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']) + int(tx_results_2['FrameCount']),
                                      actual=int(psw_stats['output']['fpg1_pkt']),
                                      message="Check all packets are seen in fpg1_pkt")

        fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']) + int(tx_results_2['FrameCount']),
                                      actual=int(psw_stats['prm']['ct_pkt']),
                                      message="Check all packets are seen in ct_pkt")
        '''

if __name__ == "__main__":
    ts = SpirentSetup()
    ts.add_test_case(TestCase1())
    ts.add_test_case(TestCase2())
    ts.run()
