from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, GeneratorConfig, Ethernet2Header, Ipv4Header, CustomBytePatternHeader
from lib.host.network_controller import NetworkController
from helper import *

num_ports = 2
loads_file = "interface_loads.json"
streamblock_objects = {}
generator_list = []
generator_config_list = []
OVERSIZED = 'OVERSIZED'
CRC_OVERSIZED = 'CRC_OVERSIZED'
MTU_EGRESS = 'MTU_EGRESS'
TOTAL_LENGTH_ERROR = 'TOTAL_LENGTH_ERROR'
TOTAL_LENGTH_ERROR_1K = 'TOTAL_LENGTH_ERROR_1K'
TOTAL_LENGTH_ERROR_100B = 'TOTAL_LENGTH_ERROR_100B'
PADDED = 'PADDED'
GOOD_FRAME = 'GOOD_FRAME'
MIN_FRAME_LENGTH = 64
MAX_FRAME_LENGTH = 1500
OVERSIZED_FRAME_LENGTH = 2000
MTU_TEST_FRAME_LENGTH = 1400


stream_list = [OVERSIZED, CRC_OVERSIZED, TOTAL_LENGTH_ERROR, TOTAL_LENGTH_ERROR_1K, TOTAL_LENGTH_ERROR_100B, MTU_EGRESS,
               PADDED, GOOD_FRAME]

for stream in stream_list:
    streamblock_objects[stream] = {}


class SpirentSetup(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
                1. Create Spirent template
                2. Connect chassis, labserver and licenseserver
                3. Attach Ports
                4. Configure all required streamblock on both ports
                5. Configure generator that runs traffic for specified amount.
                6. Subscribe to tx, rx and analyzer results
                """)

    def setup(self):
        global template_obj, port_1, port_2, duration_seconds, subscribe_results, port_obj_list, bad_frame_load, \
            good_frame_load, interface_obj_list, network_controller_obj, dut_port_1, dut_port_2

        fun_test.log("Creating Template object")
        template_obj = SpirentEthernetTrafficTemplate(session_name="test_good_bad_frames2")
        fun_test.test_assert(template_obj, "Create template object")

        # Create network controller object
        dpcsh_server_ip = template_obj.stc_manager.dpcsh_server_config['dpcsh_server_ip']
        dpcsh_server_port = int(template_obj.stc_manager.dpcsh_server_config['dpcsh_server_port'])
        network_controller_obj = NetworkController(dpc_server_ip=dpcsh_server_ip, dpc_server_port=dpcsh_server_port)

        poke = network_controller_obj.set_syslog_level(3)
        fun_test.simple_assert(poke, "Ensure syslogs are disabled")

        result = template_obj.setup(no_of_ports_needed=num_ports)
        fun_test.test_assert(result['result'], "Configure setup")

        port_obj_list = result['port_list']
        interface_obj_list = result['interface_obj_list']

        source_mac1 = template_obj.stc_manager.dut_config['source_mac1']
        destination_mac1 = template_obj.stc_manager.dut_config['destination_mac1']
        source_ip1 = template_obj.stc_manager.dut_config['source_ip1']
        source_ip2 = template_obj.stc_manager.dut_config['source_ip2']
        destination_ip1 = template_obj.stc_manager.dut_config['destination_ip1']
        destination_ip2 = template_obj.stc_manager.dut_config['destination_ip2']
        dut_port_1 = template_obj.stc_manager.dut_config['port_nos'][0]
        dut_port_2 = template_obj.stc_manager.dut_config['port_nos'][1]
        interface_mode = template_obj.stc_manager.interface_mode

        #  Read loads from file
        file_path = fun_test.get_script_parent_directory() + "/" + loads_file
        output = fun_test.parse_file_to_json(file_path)
        bad_frame_load = output[interface_mode]["bad_frame_load_mbps"]
        good_frame_load = output[interface_mode]["good_frame_load_mbps"]

        port_nos = template_obj.stc_manager.host_config['test_module']["port_nos"]

        # Configure streams
        for port in port_obj_list:
            current_source_ip = source_ip2
            current_destination_ip = destination_ip2
            current_positive = output["padding"]["reverse"]["positive"]
            current_1k = output["padding"]["reverse"]["1k"]
            current_100B = output["padding"]["reverse"]["100B"]

            if str(port) == 'port' + str(port_nos[0]):
                current_source_ip = source_ip1
                current_destination_ip = destination_ip1
                current_positive = output["padding"]["straight"]["positive"]
                current_1k = output["padding"]["straight"]["1k"]
                current_100B = output["padding"]["straight"]["100B"]
                port_1 = port
            else:
                port_2 = port
            for stream_type in stream_list:
                current_streamblock_obj = StreamBlock()
                current_streamblock_obj.Load = 1
                current_streamblock_obj.LoadUnit = current_streamblock_obj.LOAD_UNIT_MEGABITS_PER_SECOND
                current_streamblock_obj.FillType = current_streamblock_obj.FILL_TYPE_PRBS
                current_ethernet_obj = Ethernet2Header(destination_mac=destination_mac1, source_mac=source_mac1)

                if not stream_type == TOTAL_LENGTH_ERROR_100B or not stream_type == TOTAL_LENGTH_ERROR_1K or \
                        stream_type == PADDED:
                    current_ipv4_obj = Ipv4Header(destination_address=current_destination_ip,
                                                  source_address=current_source_ip)

                if stream_type == OVERSIZED:
                    current_streamblock_obj.FixedFrameLength = OVERSIZED_FRAME_LENGTH
                elif stream_type == CRC_OVERSIZED:
                    current_streamblock_obj.EnableFcsErrorInsertion = True
                    current_streamblock_obj.FixedFrameLength = OVERSIZED_FRAME_LENGTH
                elif stream_type == MTU_EGRESS:
                    current_streamblock_obj.FixedFrameLength = MTU_TEST_FRAME_LENGTH
                elif stream_type == TOTAL_LENGTH_ERROR:
                    current_ipv4_obj.totalLength = current_ipv4_obj.TOTAL_HEADER_LENGTH_ERROR
                elif stream_type == TOTAL_LENGTH_ERROR_1K:
                    current_streamblock_obj.Load = 100
                    current_streamblock_obj.LoadUnit = current_streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
                    current_streamblock_obj.FixedFrameLength = 192
                    custom_header_obj = CustomBytePatternHeader(byte_pattern=current_1k)
                elif stream_type == TOTAL_LENGTH_ERROR_100B:
                    current_streamblock_obj.Load = 10
                    current_streamblock_obj.LoadUnit = current_streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
                    current_streamblock_obj.FrameLengthMode = current_streamblock_obj.FRAME_LENGTH_MODE_RANDOM
                    current_streamblock_obj.MinFrameLength = MIN_FRAME_LENGTH
                    current_streamblock_obj.MaxFrameLength = MAX_FRAME_LENGTH
                    custom_header_obj = CustomBytePatternHeader(byte_pattern=current_100B)
                elif stream_type == PADDED:
                    current_streamblock_obj.FrameLengthMode = current_streamblock_obj.FRAME_LENGTH_MODE_INCR
                    current_streamblock_obj.MinFrameLength = MIN_FRAME_LENGTH
                    current_streamblock_obj.MaxFrameLength = MAX_FRAME_LENGTH
                    current_streamblock_obj.Load = 100
                    current_streamblock_obj.LoadUnit = current_streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
                    custom_header_obj = CustomBytePatternHeader(byte_pattern=current_positive)
                elif stream_type == GOOD_FRAME:
                    current_streamblock_obj.FrameLengthMode = current_streamblock_obj.FRAME_LENGTH_MODE_RANDOM
                    current_streamblock_obj.MinFrameLength = MIN_FRAME_LENGTH
                    current_streamblock_obj.MaxFrameLength = MAX_FRAME_LENGTH
                else:
                    raise Exception("Stream %s not found" % stream_type)

                create_streamblock = template_obj.configure_stream_block(stream_block_obj=current_streamblock_obj,
                                                                         port_handle=port)
                fun_test.simple_assert(create_streamblock, "Creating streamblock %s on port %s" %
                                       (current_streamblock_obj, port))

                configure_ethernet = template_obj.stc_manager.configure_frame_stack(
                    stream_block_handle=current_streamblock_obj.spirent_handle, header_obj=current_ethernet_obj)
                fun_test.simple_assert(configure_ethernet,
                                       "Ensure ethernet frame is configured for stream %s on port %s and streamblock %s" % (
                                           stream_type, port, current_streamblock_obj.spirent_handle))

                if stream_type == TOTAL_LENGTH_ERROR_100B or stream_type == TOTAL_LENGTH_ERROR_1K or \
                        stream_type == PADDED:
                    configure_custom = template_obj.stc_manager.configure_frame_stack(
                        stream_block_handle=current_streamblock_obj.spirent_handle, header_obj=custom_header_obj)
                    fun_test.simple_assert(configure_custom,
                                           "Ensure custom header is configured for stream %s on port %s and streamblock %s" % (
                                               stream_type, port, current_streamblock_obj.spirent_handle))
                else:
                    configure_ip4 = template_obj.stc_manager.configure_frame_stack(
                        stream_block_handle=current_streamblock_obj.spirent_handle, header_obj=current_ipv4_obj)
                    fun_test.simple_assert(configure_ip4,
                                           "Ensure ipv4 is configured for stream %s on port %s and streamblock %s" % (
                                               stream_type, port, current_streamblock_obj.spirent_handle))

                streamblock_objects[stream_type][port] = current_streamblock_obj

            # Configure Generator
            duration_seconds = 10
            gen_config_obj = GeneratorConfig()
            gen_config_obj.Duration = duration_seconds
            gen_config_obj.SchedulingMode = gen_config_obj.SCHEDULING_MODE_RATE_BASED
            gen_config_obj.DurationMode = gen_config_obj.DURATION_MODE_SECONDS
            gen_config_obj.AdvancedInterleaving = True
            config_obj = template_obj.configure_generator_config(port_handle=port,
                                                                 generator_config_obj=gen_config_obj)
            fun_test.test_assert(config_obj, "Creating generator config on port %s" % port)

            generator_list.append(template_obj.stc_manager.get_generator(port))
            generator_config_list.append(gen_config_obj)

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
                              summary="Test Oversizedframe size ",
                              steps="""
                        1. Active Oversized streams with 2000B frame size on both ports
                        2. Execute generator traffic on both ports
                        3. Frames must not be dropped but be sent with CRC errors
                        4. Check oversized frames from dut ingress.
                        5. Check outerrors on dut egress
                        6. Check psw stats
                        """)

    def setup(self):
        # Deactivate all streamblocks
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivating all streamblocks")

        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

    def cleanup(self):
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        activate = template_obj.activate_stream_blocks([streamblock_objects[OVERSIZED][str(port_1)],
                                                        streamblock_objects[OVERSIZED][str(port_2)]])
        fun_test.test_assert(activate, "Activate streamblocks for %s " % OVERSIZED)

        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=generator_list)
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=duration_seconds)

        # Get results for streamblock 1
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[OVERSIZED][
                                                                                str(port_1)].spirent_handle))
        tx_results_1 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[OVERSIZED][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_objects[OVERSIZED][
                                                                                str(port_1)].spirent_handle))
        rx_results_1 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_objects[OVERSIZED][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        # Get streambllock 2 results
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[OVERSIZED][
                                                                                str(port_2)].spirent_handle))
        tx_results_2 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[OVERSIZED][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_objects[OVERSIZED][
                                                                                str(port_2)].spirent_handle))
        rx_results_2 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_objects[OVERSIZED][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        fun_test.log("Fetching rx port results for subscribed object %s" % subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results_1 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_2, subscribe_handle=subscribe_results['analyzer_subscribe'])

        fun_test.log("Fetching rx port results for subscribed object %s" % subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results_2 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_1, subscribe_handle=subscribe_results['analyzer_subscribe'])

        fun_test.log("Tx 1 Results %s " % tx_results_1)
        fun_test.log("Rx 1 Results %s" % rx_results_1)
        fun_test.log("Tx 2 Results %s " % tx_results_2)
        fun_test.log("Rx 2 Results %s" % rx_results_2)
        fun_test.log("Analyzer port results on port %s are %s" % (port_2, rx_port_analyzer_results_1))
        fun_test.log("Analyzer port results on port %s are %s" % (port_1, rx_port_analyzer_results_2))

        fun_test.test_assert_expected(actual=rx_port_analyzer_results_1['TotalFrameCount'],
                                      expected=tx_results_1['FrameCount'],
                                      message="Ensure frames are received")
        fun_test.test_assert_expected(actual=tx_results_1["FrameCount"],
                                      expected=rx_port_analyzer_results_1['FcsErrorFrameCount'],
                                      message="Ensure packets are received with FcsError")
        fun_test.test_assert_expected(actual=rx_port_analyzer_results_2['TotalFrameCount'],
                                      expected=tx_results_2['FrameCount'],
                                      message="Ensure frames are received")
        fun_test.test_assert_expected(actual=tx_results_2["FrameCount"],
                                      expected=rx_port_analyzer_results_2['FcsErrorFrameCount'],
                                      message="Ensure packets are received with FcsError")

        dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1)
        fun_test.test_assert(dut_port_1_results, message="Ensure stats are obtained for %s" % dut_port_1)
        dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2)
        fun_test.test_assert(dut_port_2_results, message="Ensure stats are obtained for %s" % dut_port_2)

        dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1)
        fun_test.test_assert(dut_port_1_results, message="Ensure stats are obtained for %s" % dut_port_1)
        dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2)
        fun_test.test_assert(dut_port_2_results, message="Ensure stats are obtained for %s" % dut_port_2)

        dut_port_1_error_transmit = get_dut_output_stats_value(dut_port_1_results, IF_OUT_ERRORS)
        dut_port_2_error_transmit = get_dut_output_stats_value(dut_port_2_results, IF_OUT_ERRORS)
        dut_port_2_frame_long_error_transmit = get_dut_output_stats_value(dut_port_2_results, FRAME_TOO_LONG_ERRORS,
                                                                          tx=False)
        dut_port_1_frame_long_error_transmit = get_dut_output_stats_value(dut_port_1_results, FRAME_TOO_LONG_ERRORS,
                                                                          tx=False)
        dut_port_1_oversized_pkts = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_OVERSIZE_PKTS, tx=False)
        dut_port_2_oversized_pkts = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_OVERSIZE_PKTS, tx=False)
        dut_port_1_tx_ether_stats_1024_1518 = get_dut_output_stats_value(dut_port_1_results,
                                                                         ETHER_STATS_PKTS_1024_TO_1518_OCTETS)
        dut_port_2_tx_ether_stats_1024_1518 = get_dut_output_stats_value(dut_port_2_results,
                                                                         ETHER_STATS_PKTS_1024_TO_1518_OCTETS)

        fun_test.test_assert_expected(expected=int(dut_port_2_error_transmit),
                                      actual=int(rx_port_analyzer_results_1['TotalFrameCount']),
                                      message="Ensure crc oversized frames are sent as errors")

        fun_test.test_assert_expected(expected=int(dut_port_1_error_transmit),
                                      actual=int(rx_port_analyzer_results_2['TotalFrameCount']),
                                      message="Ensure crc oversized frames are sent as errors")

        fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']),
                                      actual=int(dut_port_1_frame_long_error_transmit),
                                      message="Ensure frame too long error seen in rx dut")

        fun_test.test_assert_expected(expected=int(tx_results_2['FrameCount']),
                                      actual=int(dut_port_2_frame_long_error_transmit),
                                      message="Ensure frame too long error seen in rx dut")

        fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']),
                                      actual=int(dut_port_1_oversized_pkts),
                                      message="Check oversized packets in dut ingress")

        fun_test.test_assert_expected(expected=int(tx_results_2['FrameCount']),
                                      actual=int(dut_port_2_oversized_pkts),
                                      message="Check oversized packets in dut ingress")

        fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']),
                                      actual=int(dut_port_1_tx_ether_stats_1024_1518),
                                      message="Check oversized packets are marked in range 1024-1518 on dut egress")

        fun_test.test_assert_expected(expected=int(tx_results_2['FrameCount']),
                                      actual=int(dut_port_2_tx_ether_stats_1024_1518),
                                      message="Check oversized packets are marked in range 1024-1518 on dut egress")

        '''
        # Fetch psw global stats
        psw_stats = network_controller_obj.peek_psw_global_stats()
        different = False
        fwd_frv = 'fwd_frv'
        ct_pkt = 'ct_pkt'
        cpr_feop_pkt = 'cpr_feop_pkt'
        fetch_list = [fwd_frv, ct_pkt, cpr_feop_pkt]
        dut_port_1_fpg_value = get_fpg_port_value(dut_port_1)
        dut_port_2_fpg_value = get_fpg_port_value(dut_port_2)
        if not dut_port_1_fpg_value == dut_port_2_fpg_value:
            different = True
            ifpg1 = 'ifpg' + str(dut_port_1_fpg_value) + '_pkt'
            fpg1 = 'fpg' + str(dut_port_1_fpg_value) + '_pkt'
            fpg1_error = 'fpg' + str(dut_port_1_fpg_value) + '_err_pkt'
            ifpg2 = 'ifpg' + str(dut_port_2_fpg_value) + '_pkt'
            fpg2 = 'fpg' + str(dut_port_2_fpg_value) + '_pkt'
            fpg2_error = 'fpg' + str(dut_port_2_fpg_value) + '_err_pkt'
            fetch_list_1 = [ifpg1, fpg1, ifpg2, fpg2, fpg1_error, fpg2_error]
            fetch_list.extend(fetch_list_1)
        else:
            fetch_list.append('ifpg' + str(dut_port_1_fpg_value) + '_pkt')
            fetch_list.append('fpg' + str(dut_port_1_fpg_value) + '_pkt')
            fetch_list.append('fpg' + str(dut_port_1_fpg_value) + '_err_pkt')

        psw_fetched_output = get_psw_global_stats_values(psw_stats, fetch_list)
        if different:
            ifpg = int(psw_fetched_output[ifpg1]) + int(psw_fetched_output[ifpg2])
            del psw_fetched_output[ifpg1]
            del psw_fetched_output[ifpg2]
            fpg = int(psw_fetched_output[fpg1]) + int(psw_fetched_output[fpg2])
            del psw_fetched_output[fpg1]
            del psw_fetched_output[fpg2]
            fpg_err = int(psw_fetched_output[fpg1_error]) + int(psw_fetched_output[fpg2_error])
            del psw_fetched_output[fpg1_error]
            del psw_fetched_output[fpg2_error]
            psw_fetched_output['ifpg'] = ifpg
            psw_fetched_output['fpg'] = fpg
            psw_fetched_output['fpg_err_pkt'] = fpg_err

        for key in fetch_list:
            fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']) + int(tx_results_2['FrameCount']),
                                          actual=psw_fetched_output[key],
                                          message="Check counter %s in psw global stats" % key)
        '''

class TestCase2(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Test CRC + Oversized frame size ",
                              steps="""
                        1. Active Oversized streams with 2000B frame size on both ports
                        2. Execute generator traffic on both ports
                        3. Frames must not be dropped but be sent with CRC errors
                        4. Check FCS error in dut ingress.
                        5. Check OutError at dut egress
                        """)

    def setup(self):
        # Deactivate all streamblocks
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivating all streamblocks")

        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

    def cleanup(self):
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        activate = template_obj.activate_stream_blocks([streamblock_objects[CRC_OVERSIZED][str(port_1)],
                                                        streamblock_objects[CRC_OVERSIZED][str(port_2)]])
        fun_test.test_assert(activate, "Activate streamblocks for %s " % CRC_OVERSIZED)

        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=generator_list)
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=duration_seconds)

        # Get results for streamblock 1
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[CRC_OVERSIZED][
                                                                                str(port_1)].spirent_handle))
        tx_results_1 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[CRC_OVERSIZED][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_objects[CRC_OVERSIZED][
                                                                                str(port_1)].spirent_handle))
        rx_results_1 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_objects[CRC_OVERSIZED][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        # Get streambllock 2 results
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[CRC_OVERSIZED][
                                                                                str(port_2)].spirent_handle))
        tx_results_2 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[CRC_OVERSIZED][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_objects[CRC_OVERSIZED][
                                                                                str(port_2)].spirent_handle))
        rx_results_2 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_objects[CRC_OVERSIZED][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        fun_test.log("Fetching rx port results for subscribed object %s" % subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results_1 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_2, subscribe_handle=subscribe_results['analyzer_subscribe'])

        fun_test.log("Fetching rx port results for subscribed object %s" % subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results_2 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_1, subscribe_handle=subscribe_results['analyzer_subscribe'])

        fun_test.log("Tx 1 Results %s " % tx_results_1)
        fun_test.log("Rx 1 Results %s" % rx_results_1)
        fun_test.log("Tx 2 Results %s " % tx_results_2)
        fun_test.log("Rx 2 Results %s" % rx_results_2)
        fun_test.log("Analyzer port results on port %s are %s" % (port_2, rx_port_analyzer_results_1))
        fun_test.log("Analyzer port results on port %s are %s" % (port_1, rx_port_analyzer_results_2))

        fun_test.test_assert_expected(actual=rx_port_analyzer_results_1['TotalFrameCount'],
                                      expected=tx_results_1['FrameCount'],
                                      message="Ensure frames are received")
        fun_test.test_assert_expected(actual=tx_results_1["FrameCount"],
                                      expected=rx_port_analyzer_results_1['FcsErrorFrameCount'],
                                      message="Ensure packets are received with FcsError")
        fun_test.test_assert_expected(actual=rx_port_analyzer_results_2['TotalFrameCount'],
                                      expected=tx_results_2['FrameCount'],
                                      message="Ensure frames are received")
        fun_test.test_assert_expected(actual=tx_results_2["FrameCount"],
                                      expected=rx_port_analyzer_results_2['FcsErrorFrameCount'],
                                      message="Ensure packets are received with FcsError")

        dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1)
        fun_test.test_assert(dut_port_1_results, message="Ensure stats are obtained for %s" % dut_port_1)
        dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2)
        fun_test.test_assert(dut_port_2_results, message="Ensure stats are obtained for %s" % dut_port_2)

        dut_port_1_error_transmit = get_dut_output_stats_value(dut_port_1_results, IF_OUT_ERRORS)
        dut_port_2_error_transmit = get_dut_output_stats_value(dut_port_2_results, IF_OUT_ERRORS)
        dut_port_2_frame_long_error_transmit = get_dut_output_stats_value(dut_port_2_results, FRAME_TOO_LONG_ERRORS,
                                                                          tx=False)
        dut_port_1_frame_long_error_transmit = get_dut_output_stats_value(dut_port_1_results, FRAME_TOO_LONG_ERRORS,
                                                                          tx=False)
        dut_port_1_jabbers_pkts = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_JABBERS, tx=False)
        dut_port_2_jabbers_pkts = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_JABBERS, tx=False)

        fun_test.test_assert_expected(expected=int(dut_port_2_error_transmit),
                                      actual=int(rx_port_analyzer_results_1['TotalFrameCount']),
                                      message="Ensure crc oversized frames are sent as errors")

        fun_test.test_assert_expected(expected=int(dut_port_1_error_transmit),
                                      actual=int(rx_port_analyzer_results_2['TotalFrameCount']),
                                      message="Ensure crc oversized frames are sent as errors")

        fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']),
                                      actual=int(dut_port_1_frame_long_error_transmit),
                                      message="Ensure frame too long error seen in rx dut")

        fun_test.test_assert_expected(expected=int(tx_results_2['FrameCount']),
                                      actual=int(dut_port_2_frame_long_error_transmit),
                                      message="Ensure frame too long error seen in rx dut")

        fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']),
                                      actual=int(dut_port_1_jabbers_pkts),
                                      message="Check oversized packets in dut ingress")

        fun_test.test_assert_expected(expected=int(tx_results_2['FrameCount']),
                                      actual=int(dut_port_2_jabbers_pkts),
                                      message="Check oversized packets in dut ingress")


class TestCase3(FunTestCase):
    interface_obj = None
    EGRESS_MTU_VALUE = 1200
    DEFAULT_MTU_VALUE = 1500

    def describe(self):
        self.set_test_details(id=3,
                              summary="Test when egress MTU is less than frame size",
                              steps="""
                        1. Set MTU of 1200 on the egress port of DUT and spirent
                        2. Activate streamblock of 1500B.
                        3. Start traffic on streamlock for 10 seconds
                        4. At egress port frames must be marked with CRC errors by DUT
                        5. Check dut egress for out errors
                        """)

    def setup(self):
        # Deactivate all streamblocks
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivating all streamblocks")

        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

    def cleanup(self):
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

        # Set back to default
        set_mtu = network_controller_obj.set_port_mtu(dut_port_2, self.DEFAULT_MTU_VALUE)
        fun_test.test_assert(set_mtu, message="Ensure egress mtu is set to %s" % self.DEFAULT_MTU_VALUE)

        self.interface_obj.Mtu = self.DEFAULT_MTU_VALUE
        mtu_update_result = template_obj.configure_physical_interface(interface_obj=self.interface_obj)
        fun_test.simple_assert(mtu_update_result, "Set spirent mtu to %s" % self.DEFAULT_MTU_VALUE)

    def run(self):
        # Activate streams with 1400B
        activate = template_obj.activate_stream_blocks([streamblock_objects[MTU_EGRESS][str(port_1)],
                                                        streamblock_objects[MTU_EGRESS][str(port_2)]])
        fun_test.test_assert(activate, "Activate streamblocks for %s " % MTU_EGRESS)

        parent = template_obj.stc_manager.get_object_parent(interface_obj_list[0]._spirent_handle)
        if str(parent[0]) == str(port_2):
            self.interface_obj = interface_obj_list[0]
        else:
            self.interface_obj = interface_obj_list[1]

        set_mtu = network_controller_obj.set_port_mtu(dut_port_2, self.EGRESS_MTU_VALUE)
        fun_test.test_assert(set_mtu, message="Ensure egress mtu is set to %s" % self.EGRESS_MTU_VALUE)

        # Set MTU 1200 on spirent on port2
        self.interface_obj.Mtu = self.EGRESS_MTU_VALUE
        mtu_update_result = template_obj.configure_physical_interface(interface_obj=self.interface_obj)
        fun_test.simple_assert(mtu_update_result, "Set spirent mtu to %s" % self.EGRESS_MTU_VALUE)

        # Execute traffic
        current_gen_handle = None
        for gen_handle in generator_list:
            parent = template_obj.stc_manager.get_object_parent(gen_handle)
            if str(parent[0]) == str(port_1):
                current_gen_handle = gen_handle
                break
            else:
                pass

        start = template_obj.enable_generator_configs(generator_configs=[current_gen_handle])
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=duration_seconds)

        # Get results for streamblock 1
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[MTU_EGRESS][
                                                                                str(port_1)].spirent_handle))
        tx_results_1 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[MTU_EGRESS][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log("Fetching rx port results for subscribed object %s" % subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results_1 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_2, subscribe_handle=subscribe_results['analyzer_subscribe'])

        fun_test.log("Tx 1 Results %s " % tx_results_1)
        fun_test.log("Analyzer port results on port %s are %s" % (port_2, rx_port_analyzer_results_1))

        dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1)
        fun_test.test_assert(dut_port_1_results, message="Ensure stats are obtained for %s" % dut_port_1)
        dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2)
        fun_test.test_assert(dut_port_2_results, message="Ensure stats are obtained for %s" % dut_port_2)

        dut_port_1_good_receive = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)
        dut_port_2_error_transmit = get_dut_output_stats_value(dut_port_2_results, IF_OUT_ERRORS)

        fun_test.test_assert_expected(actual=rx_port_analyzer_results_1['TotalFrameCount'],
                                      expected=tx_results_1['FrameCount'],
                                      message="Ensure frames are received on port2")

        fun_test.test_assert_expected(actual=tx_results_1["FrameCount"],
                                      expected=rx_port_analyzer_results_1['FcsErrorFrameCount'],
                                      message="Ensure packets are received with FcsError")

        fun_test.test_assert_expected(actual=int(dut_port_2_error_transmit),
                                      expected=int(rx_port_analyzer_results_1['TotalFrameCount']),
                                      message="Ensure crc oversized frames are sent as errors")

        fun_test.test_assert_expected(expected=int(dut_port_1_good_receive), actual=int(dut_port_2_error_transmit),
                                      message="Ensure pkts received are marked as outerror on dut egress")


class TestCase4(FunTestCase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Test DUT with IP total length error via spirent",
                              steps="""
                        1. Active streams with IP total length error on both ports
                        2. Execute generator traffic on both ports
                        3. All frames must be dropped and Rx count of spirent must be 0
                        4. Check dut egress must not transmit
                        """)

    def setup(self):
        # Deactivate all streamblocks
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivated all streamblocks")

        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

    def cleanup(self):
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        activate = template_obj.activate_stream_blocks([streamblock_objects[TOTAL_LENGTH_ERROR][str(port_1)],
                                                        streamblock_objects[TOTAL_LENGTH_ERROR][str(port_2)]])
        fun_test.test_assert(activate, "Activate streamblocks for %s " % TOTAL_LENGTH_ERROR)

        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=generator_list)
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=duration_seconds)

        # Get results for streamblock 1
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[TOTAL_LENGTH_ERROR][
                                                                                str(port_1)].spirent_handle))
        tx_results_1 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[TOTAL_LENGTH_ERROR][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        # Get streambllock 2 results
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[TOTAL_LENGTH_ERROR][
                                                                                str(port_2)].spirent_handle))
        tx_results_2 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[TOTAL_LENGTH_ERROR][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log("Fetching rx port results for subscribed object %s" % subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results_1 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_2, subscribe_handle=subscribe_results['analyzer_subscribe'])

        fun_test.log("Fetching rx port results for subscribed object %s" % subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results_2 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_1, subscribe_handle=subscribe_results['analyzer_subscribe'])

        fun_test.log("Tx 1 Results %s " % tx_results_1)
        fun_test.log("Tx 2 Results %s " % tx_results_2)

        fun_test.test_assert(tx_results_1["FrameCount"] > 0,
                             message="Ensure some frames were sent from %s" % str(port_1))
        # Currently F1 does not look in total length and passes frame as is
        # TODO: when fixed frames must be dropped
        expected_rx = 0
        fun_test.test_assert_expected(actual=rx_port_analyzer_results_1["TotalFrameCount"],
                                      expected=expected_rx,
                                      message="Ensure all frames are dropped")

        fun_test.test_assert(tx_results_2["FrameCount"] > 0,
                             message="Ensure some frames were sent from %s" % str(port_1))
        fun_test.test_assert_expected(actual=rx_port_analyzer_results_2["TotalFrameCount"],
                                      expected=expected_rx,
                                      message="Ensure all frames are dropped")

        # Check from dut
        dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1)
        fun_test.test_assert(dut_port_1_results, message="Ensure stats are obtained for %s" % dut_port_1)
        dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2)
        fun_test.test_assert(dut_port_2_results, message="Ensure stats are obtained for %s" % dut_port_2)

        dut_port_1_transmit = get_dut_output_stats_value(dut_port_1_results, FRAMES_TRANSMITTED_OK)
        dut_port_2_transmit = get_dut_output_stats_value(dut_port_2_results, FRAMES_TRANSMITTED_OK)
        dut_port_1_receive = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)
        dut_port_2_receive = get_dut_output_stats_value(dut_port_2_results, FRAMES_RECEIVED_OK, tx=False)

        fun_test.test_assert(not dut_port_2_transmit, message="Ensure no frame is transmitted from DUT")

        fun_test.test_assert(not dut_port_1_transmit, message="Ensure no frame is transmitted from DUT")

        fun_test.test_assert_expected(expected=int(tx_results_1["FrameCount"]), actual=int(dut_port_1_receive),
                                      message="Check frames are received by dut ingress port")

        fun_test.test_assert_expected(expected=int(tx_results_2["FrameCount"]), actual=int(dut_port_2_receive),
                                      message="Check frames are received by dut ingress port")


class TestCase5(FunTestCase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Test DUT with IP total length error with 1k",
                              steps="""
                        1. Active streams with IP total length error padding 1k on both ports
                        2. Execute generator traffic on both ports
                        3. All frames must match on spirent tx and rx
                        4. Check frames received on dut ingress port
                        5. Check frames transmitted by dut egress must match rx of spirent
                        """)

    def setup(self):
        # Deactivate all streamblocks
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivated all streamblocks")

        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

    def cleanup(self):
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        activate = template_obj.activate_stream_blocks([streamblock_objects[TOTAL_LENGTH_ERROR_1K][str(port_1)],
                                                        streamblock_objects[TOTAL_LENGTH_ERROR_1K][str(port_2)]])
        fun_test.test_assert(activate, "Activate streamblocks for %s " % TOTAL_LENGTH_ERROR_1K)

        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=generator_list)
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=duration_seconds)

        # Get results for streamblock 1
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[TOTAL_LENGTH_ERROR_1K][
                                                                                str(port_1)].spirent_handle))
        tx_results_1 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[TOTAL_LENGTH_ERROR_1K][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        # Get streambllock 2 results
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[TOTAL_LENGTH_ERROR_1K][
                                                                                str(port_2)].spirent_handle))
        tx_results_2 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[TOTAL_LENGTH_ERROR_1K][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log("Fetching rx port results for subscribed object %s" % subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results_1 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_2, subscribe_handle=subscribe_results['analyzer_subscribe'])

        fun_test.log("Fetching rx port results for subscribed object %s" % subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results_2 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_1, subscribe_handle=subscribe_results['analyzer_subscribe'])

        fun_test.log("Tx 1 Results %s " % tx_results_1)
        fun_test.log("Tx 2 Results %s " % tx_results_2)

        fun_test.test_assert(tx_results_1["FrameCount"] > 0,
                             message="Ensure some frames were sent from %s" % str(port_1))
        expected_rx = 0
        fun_test.test_assert_expected(actual=rx_port_analyzer_results_1["TotalFrameCount"],
                                      expected=tx_results_1["FrameCount"],
                                      message="Ensure all frames are received")

        fun_test.test_assert(tx_results_2["FrameCount"] > 0,
                             message="Ensure some frames were sent from %s" % str(port_1))
        fun_test.test_assert_expected(actual=rx_port_analyzer_results_2["TotalFrameCount"],
                                      expected=tx_results_2["FrameCount"],
                                      message="Ensure all frames are received")

        # Check from dut
        dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1)
        fun_test.test_assert(dut_port_1_results, message="Ensure stats are obtained for %s" % dut_port_1)
        dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2)
        fun_test.test_assert(dut_port_2_results, message="Ensure stats are obtained for %s" % dut_port_2)

        dut_port_1_transmit = get_dut_output_stats_value(dut_port_1_results, FRAMES_TRANSMITTED_OK)
        dut_port_2_transmit = get_dut_output_stats_value(dut_port_2_results, FRAMES_TRANSMITTED_OK)
        dut_port_1_receive = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)
        dut_port_2_receive = get_dut_output_stats_value(dut_port_2_results, FRAMES_RECEIVED_OK, tx=False)

        fun_test.test_assert_expected(expected=int(tx_results_1["FrameCount"]), actual=int(dut_port_1_receive),
                                      message="Check frames are received by dut ingress port")

        fun_test.test_assert_expected(expected=int(tx_results_2["FrameCount"]), actual=int(dut_port_2_receive),
                                      message="Check frames are received by dut ingress port")

        fun_test.test_assert_expected(expected=int(rx_port_analyzer_results_2["TotalFrameCount"]), actual=int(dut_port_1_transmit),
                                      message="Check frames are received by spirewnt port")

        fun_test.test_assert_expected(expected=int(rx_port_analyzer_results_1["TotalFrameCount"]), actual=int(dut_port_2_transmit),
                                      message="Check frames are received by spirent port")


class TestCase6(FunTestCase):
    def describe(self):
        self.set_test_details(id=6,
                              summary="Test DUT with IP total length error with 100B incremental",
                              steps="""
                        1. Active streams with IP total length error on both ports
                        2. Execute generator traffic on both ports
                        3. All frames must match on spirent tx and rx
                        4. Check frames received on dut ingress port
                        5. Check frames transmitted by dut egress must match rx of spirent
                        """)

    def setup(self):
        # Deactivate all streamblocks
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivated all streamblocks")

        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

    def cleanup(self):
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        activate = template_obj.activate_stream_blocks([streamblock_objects[TOTAL_LENGTH_ERROR_100B][str(port_1)],
                                                        streamblock_objects[TOTAL_LENGTH_ERROR_100B][str(port_2)]])
        fun_test.test_assert(activate, "Activate streamblocks for %s " % TOTAL_LENGTH_ERROR_100B)

        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=generator_list)
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=duration_seconds)

        # Get results for streamblock 1
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[TOTAL_LENGTH_ERROR_100B][
                                                                                str(port_1)].spirent_handle))
        tx_results_1 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[TOTAL_LENGTH_ERROR_100B][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        # Get streambllock 2 results
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[TOTAL_LENGTH_ERROR_100B][
                                                                                str(port_2)].spirent_handle))
        tx_results_2 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[TOTAL_LENGTH_ERROR_100B][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log("Fetching rx port results for subscribed object %s" % subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results_1 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_2, subscribe_handle=subscribe_results['analyzer_subscribe'])

        fun_test.log("Fetching rx port results for subscribed object %s" % subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results_2 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_1, subscribe_handle=subscribe_results['analyzer_subscribe'])

        fun_test.log("Tx 1 Results %s " % tx_results_1)
        fun_test.log("Tx 2 Results %s " % tx_results_2)

        fun_test.test_assert(tx_results_1["FrameCount"] > 0,
                             message="Ensure some frames were sent from %s" % str(port_1))
        expected_rx = 0
        fun_test.test_assert_expected(actual=rx_port_analyzer_results_1["TotalFrameCount"],
                                      expected=tx_results_1["FrameCount"],
                                      message="Ensure all frames are received")

        fun_test.test_assert(tx_results_2["FrameCount"] > 0,
                             message="Ensure some frames were sent from %s" % str(port_1))
        fun_test.test_assert_expected(actual=rx_port_analyzer_results_2["TotalFrameCount"],
                                      expected=tx_results_2["FrameCount"],
                                      message="Ensure all frames are received")

        # Check from dut
        dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1)
        fun_test.test_assert(dut_port_1_results, message="Ensure stats are obtained for %s" % dut_port_1)
        dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2)
        fun_test.test_assert(dut_port_2_results, message="Ensure stats are obtained for %s" % dut_port_2)

        dut_port_1_transmit = get_dut_output_stats_value(dut_port_1_results, FRAMES_TRANSMITTED_OK)
        dut_port_2_transmit = get_dut_output_stats_value(dut_port_2_results, FRAMES_TRANSMITTED_OK)
        dut_port_1_receive = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)
        dut_port_2_receive = get_dut_output_stats_value(dut_port_2_results, FRAMES_RECEIVED_OK, tx=False)

        fun_test.test_assert_expected(expected=int(tx_results_1["FrameCount"]), actual=int(dut_port_1_receive),
                                      message="Check frames are received by dut ingress port")

        fun_test.test_assert_expected(expected=int(tx_results_2["FrameCount"]), actual=int(dut_port_2_receive),
                                      message="Check frames are received by dut ingress port")

        fun_test.test_assert_expected(expected=int(rx_port_analyzer_results_2["TotalFrameCount"]), actual=int(dut_port_1_transmit),
                                      message="Check frames are received by spirewnt port")

        fun_test.test_assert_expected(expected=int(rx_port_analyzer_results_1["TotalFrameCount"]), actual=int(dut_port_2_transmit),
                                      message="Check frames are received by spirent port")


class TestCase7(FunTestCase):
    def describe(self):
        self.set_test_details(id=7,
                              summary="Test DUT with padding",
                              steps="""
                        1. Active streams with PADDED on both ports
                        2. Execute generator traffic on both ports
                        3. All frames must match on spirent tx and rx
                        4. Check frames received on dut ingress port
                        5. Check frames transmitted by dut egress must match rx of spirent
                        """)

    def setup(self):
        # Deactivate all streamblocks
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivated all streamblocks")

        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

    def cleanup(self):
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        activate = template_obj.activate_stream_blocks([streamblock_objects[PADDED][str(port_1)],
                                                        streamblock_objects[PADDED][str(port_2)]])
        fun_test.test_assert(activate, "Activate streamblocks for %s " % PADDED)

        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=generator_list)
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=duration_seconds)

        # Get results for streamblock 1
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[PADDED][
                                                                                str(port_1)].spirent_handle))
        tx_results_1 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[PADDED][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        # Get streambllock 2 results
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[PADDED][
                                                                                str(port_2)].spirent_handle))
        tx_results_2 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[PADDED][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log("Fetching rx port results for subscribed object %s" % subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results_1 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_2, subscribe_handle=subscribe_results['analyzer_subscribe'])

        fun_test.log("Fetching rx port results for subscribed object %s" % subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results_2 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_1, subscribe_handle=subscribe_results['analyzer_subscribe'])

        fun_test.log("Tx 1 Results %s " % tx_results_1)
        fun_test.log("Tx 2 Results %s " % tx_results_2)

        fun_test.test_assert(tx_results_1["FrameCount"] > 0,
                             message="Ensure some frames were sent from %s" % str(port_1))
        expected_rx = 0
        fun_test.test_assert_expected(actual=rx_port_analyzer_results_1["TotalFrameCount"],
                                      expected=tx_results_1['FrameCount'],
                                      message="Ensure all frames are sent correctly")

        fun_test.test_assert(tx_results_2["FrameCount"] > 0,
                             message="Ensure some frames were sent from %s" % str(port_1))
        fun_test.test_assert_expected(actual=rx_port_analyzer_results_2["TotalFrameCount"],
                                      expected=tx_results_2['FrameCount'],
                                      message="Ensure all frames are sent correctly")

        # Check from dut
        dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1)
        fun_test.test_assert(dut_port_1_results, message="Ensure stats are obtained for %s" % dut_port_1)
        dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2)
        fun_test.test_assert(dut_port_2_results, message="Ensure stats are obtained for %s" % dut_port_2)

        dut_port_1_transmit = get_dut_output_stats_value(dut_port_1_results, FRAMES_TRANSMITTED_OK)
        dut_port_2_transmit = get_dut_output_stats_value(dut_port_2_results, FRAMES_TRANSMITTED_OK)
        dut_port_1_receive = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)
        dut_port_2_receive = get_dut_output_stats_value(dut_port_2_results, FRAMES_RECEIVED_OK, tx=False)

        fun_test.test_assert_expected(expected=int(tx_results_1["FrameCount"]), actual=int(dut_port_1_receive),
                                      message="Check frames are received by dut ingress port")

        fun_test.test_assert_expected(expected=int(tx_results_2["FrameCount"]), actual=int(dut_port_2_receive),
                                      message="Check frames are received by dut ingress port")

        fun_test.test_assert_expected(expected=int(rx_port_analyzer_results_2["TotalFrameCount"]), actual=int(dut_port_1_transmit),
                                      message="Check frames are received by spirent port")

        fun_test.test_assert_expected(expected=int(rx_port_analyzer_results_1["TotalFrameCount"]), actual=int(dut_port_2_transmit),
                                      message="Check frames are received by spirent port")


class TestCase8(FunTestCase):
    def describe(self):
        self.set_test_details(id=8,
                              summary="Test DUT with Good+Bad frames",
                              steps="""
                        1. Active all streams on both ports including good and bad
                        2. Execute generator traffic on both ports
                        3. All good frames must be received correclty 
                        4. Check that tx and rx counters match on spirent
                        5. Check dut frames received and transmitted 
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
        duration = 20

        # Activate streams
        activate = template_obj.activate_stream_blocks()
        fun_test.test_assert(activate, "Activate all streamblocks")

        # Apply correct loads
        for port in port_obj_list:
            for stream in stream_list:
                current_stream_obj = streamblock_objects[stream][port]
                if stream == GOOD_FRAME:
                    current_load = good_frame_load
                elif stream == TOTAL_LENGTH_ERROR_1K or stream == TOTAL_LENGTH_ERROR_100B or stream == PADDED:
                    current_load = 1
                else:
                    current_load = bad_frame_load

                configure_stream = template_obj.stc_manager.stc.config(current_stream_obj.spirent_handle,
                                                                       Load=current_load)
                fun_test.log("Updating streamblock %s on port %s" % (current_stream_obj.spirent_handle, port))

        # Increase duration of generator configs
        for gen_config_obj in generator_config_list:
            gen_config_obj.Duration = duration

        for i in range(len(generator_config_list)):
            config_obj = template_obj.configure_generator_config(port_handle=port_obj_list[i],
                                                                 generator_config_obj=generator_config_list[i],
                                                                 update=True)
            fun_test.simple_assert(config_obj, "Updating generator config on port %s" % str(port_obj_list[i]))

        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=generator_list)
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=duration)

        # Get results for streamblock 1
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[GOOD_FRAME][
                                                                                str(port_1)].spirent_handle))
        tx_results_1 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[GOOD_FRAME][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_objects[GOOD_FRAME][
                                                                                str(port_1)].spirent_handle))
        rx_results_1 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_objects[GOOD_FRAME][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        # Get streambllock 2 results
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[GOOD_FRAME][
                                                                                str(port_2)].spirent_handle))
        tx_results_2 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[GOOD_FRAME][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_objects[GOOD_FRAME][
                                                                                str(port_2)].spirent_handle))
        rx_results_2 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_objects[GOOD_FRAME][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        tx_results_oversized_1 = {}
        tx_results_oversized_2 = {}
        tx_results_crc_oversized_1 = {}
        tx_results_crc_oversized_2 = {}
        tx_results_total_len_1 = {}
        tx_results_total_len_2 = {}

        tx_results_oversized_1['FrameCount'] = 0
        tx_results_oversized_2['FrameCount'] = 0
        tx_results_crc_oversized_1['FrameCount'] = 0
        tx_results_crc_oversized_2['FrameCount'] = 0
        tx_results_total_len_1['FrameCount'] = 0
        tx_results_total_len_2['FrameCount'] = 0

        # Get results of other frames
        if OVERSIZED in stream_list:
            fun_test.log("Fetch results of %s to be added to final good frame" % OVERSIZED)
            tx_results_oversized_1 = template_obj.stc_manager.get_tx_stream_block_results(
                stream_block_handle=streamblock_objects[OVERSIZED][str(port_1)].spirent_handle,
                subscribe_handle=subscribe_results['tx_subscribe'])

            fun_test.log("Fetch results of %s to be added to final good frame" % OVERSIZED)
            tx_results_oversized_2 = template_obj.stc_manager.get_tx_stream_block_results(
                stream_block_handle=streamblock_objects[OVERSIZED][str(port_2)].spirent_handle,
                subscribe_handle=subscribe_results['tx_subscribe'])

        if CRC_OVERSIZED in stream_list:
            fun_test.log("Fetch results of %s to be added to final good frame" % CRC_OVERSIZED)
            tx_results_crc_oversized_1 = template_obj.stc_manager.get_tx_stream_block_results(
                stream_block_handle=streamblock_objects[CRC_OVERSIZED][str(port_1)].spirent_handle,
                subscribe_handle=subscribe_results['tx_subscribe'])

            fun_test.log("Fetch results of %s to be added to final good frame" % CRC_OVERSIZED)
            tx_results_crc_oversized_2 = template_obj.stc_manager.get_tx_stream_block_results(
                stream_block_handle=streamblock_objects[CRC_OVERSIZED][str(port_2)].spirent_handle,
                subscribe_handle=subscribe_results['tx_subscribe'])

        if TOTAL_LENGTH_ERROR in stream_list:
            fun_test.log("Fetch results of %s to be added to final good frame" % TOTAL_LENGTH_ERROR)
            tx_results_total_len_1 = template_obj.stc_manager.get_tx_stream_block_results(
                stream_block_handle=streamblock_objects[TOTAL_LENGTH_ERROR][str(port_1)].spirent_handle,
                subscribe_handle=subscribe_results['tx_subscribe'])

            fun_test.log("Fetch results of %s to be added to final good frame" % TOTAL_LENGTH_ERROR)
            tx_results_total_len_2 = template_obj.stc_manager.get_tx_stream_block_results(
                stream_block_handle=streamblock_objects[TOTAL_LENGTH_ERROR][str(port_2)].spirent_handle,
                subscribe_handle=subscribe_results['tx_subscribe'])

        if TOTAL_LENGTH_ERROR_1K in stream_list:
            fun_test.log("Fetch results of %s to be added to final good frame" % TOTAL_LENGTH_ERROR_1K)
            tx_results_total_len_1k_1 = template_obj.stc_manager.get_tx_stream_block_results(
                stream_block_handle=streamblock_objects[TOTAL_LENGTH_ERROR_1K][str(port_1)].spirent_handle,
                subscribe_handle=subscribe_results['tx_subscribe'])

            fun_test.log("Fetch results of %s to be added to final good frame" % TOTAL_LENGTH_ERROR_1K)
            tx_results_total_len_1k_2 = template_obj.stc_manager.get_tx_stream_block_results(
                stream_block_handle=streamblock_objects[TOTAL_LENGTH_ERROR_1K][str(port_2)].spirent_handle,
                subscribe_handle=subscribe_results['tx_subscribe'])

        if TOTAL_LENGTH_ERROR_100B in stream_list:
            fun_test.log("Fetch results of %s to be added to final good frame" % TOTAL_LENGTH_ERROR_100B)
            tx_results_total_len_100B_1 = template_obj.stc_manager.get_tx_stream_block_results(
                stream_block_handle=streamblock_objects[TOTAL_LENGTH_ERROR_100B][str(port_1)].spirent_handle,
                subscribe_handle=subscribe_results['tx_subscribe'])

            fun_test.log("Fetch results of %s to be added to final good frame" % TOTAL_LENGTH_ERROR_100B)
            tx_results_total_len_100B_2 = template_obj.stc_manager.get_tx_stream_block_results(
                stream_block_handle=streamblock_objects[TOTAL_LENGTH_ERROR_100B][str(port_2)].spirent_handle,
                subscribe_handle=subscribe_results['tx_subscribe'])

        if PADDED in stream_list:
            fun_test.log("Fetch results of %s to be added to final good frame" % PADDED)
            tx_results_total_len_padded_1 = template_obj.stc_manager.get_tx_stream_block_results(
                stream_block_handle=streamblock_objects[PADDED][str(port_1)].spirent_handle,
                subscribe_handle=subscribe_results['tx_subscribe'])

            fun_test.log("Fetch results of %s to be added to final good frame" % PADDED)
            tx_results_total_len_padded_2 = template_obj.stc_manager.get_tx_stream_block_results(
                stream_block_handle=streamblock_objects[PADDED][str(port_2)].spirent_handle,
                subscribe_handle=subscribe_results['tx_subscribe'])

        if MTU_EGRESS in stream_list:
            fun_test.log("Fetch results of %s to be added to final good frame" % MTU_EGRESS)
            tx_results_mtu_1 = template_obj.stc_manager.get_tx_stream_block_results(
                stream_block_handle=streamblock_objects[MTU_EGRESS][str(port_1)].spirent_handle,
                subscribe_handle=subscribe_results['tx_subscribe'])

            fun_test.log("Fetch results of %s to be added to final good frame" % MTU_EGRESS)
            tx_results_mtu_2 = template_obj.stc_manager.get_tx_stream_block_results(
                stream_block_handle=streamblock_objects[MTU_EGRESS][str(port_2)].spirent_handle,
                subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching analyzer port results for subscribed object %s" % subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results_1 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_2, subscribe_handle=subscribe_results['analyzer_subscribe'])

        fun_test.log(
            "Fetching analyzer port results for subscribed object %s" % subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results_2 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_1, subscribe_handle=subscribe_results['analyzer_subscribe'])

        port_2_errors = template_obj.check_non_zero_error_count(rx_port_analyzer_results_1)
        port_1_errors = template_obj.check_non_zero_error_count(rx_port_analyzer_results_2)

        fun_test.log("Tx 1 Results %s " % tx_results_1)
        fun_test.log("Rx 1 Results %s" % rx_results_1)
        fun_test.log("Tx 2 Results %s " % tx_results_2)
        fun_test.log("Rx 2 Results %s" % rx_results_2)

        fun_test.test_assert_expected(
            actual=int(tx_results_oversized_1['FrameCount']) + int(tx_results_crc_oversized_1['FrameCount']),
            expected=int(rx_port_analyzer_results_1['FcsErrorFrameCount']),
            message="Ensure correct fcs error frames are seen on port %s" % port_2)

        fun_test.test_assert_expected(
            actual=int(tx_results_oversized_2['FrameCount']) + int(tx_results_crc_oversized_2['FrameCount']),
            expected=int(rx_port_analyzer_results_2['FcsErrorFrameCount']),
            message="Ensure correct fcs error frames are seen on port %s" % port_1)

        if (int(port_2_errors['FcsErrorFrameCount']) == int(tx_results_oversized_1['FrameCount']) + int(tx_results_crc_oversized_1['FrameCount'])) and len(port_2_errors) == 2:
            port_2_errors['result'] = True
        if (int(port_1_errors['FcsErrorFrameCount']) == int(tx_results_oversized_2['FrameCount']) + int(tx_results_crc_oversized_2['FrameCount'])) and len(port_1_errors) == 2:
            port_1_errors['result'] = True

        #total_good_tx_1 = int(tx_results_total_len_1['FrameCount']) + int(tx_results_1['FrameCount'])
        #total_good_tx_2 = int(tx_results_total_len_2['FrameCount']) + int(tx_results_2['FrameCount'])

        # To test fix
        total_good_tx_1 = int(tx_results_1['FrameCount'])
        total_good_tx_2 = int(tx_results_2['FrameCount'])

        total_good_rx_spirent_1 = int(rx_results_1['FrameCount']) - (int(tx_results_oversized_1['FrameCount']) +
                                                                     int(tx_results_crc_oversized_1['FrameCount']) +
                                                                     int(tx_results_total_len_1k_1['FrameCount']))
        total_good_rx_spirent_2 = int(rx_results_2['FrameCount']) - (int(tx_results_oversized_2['FrameCount']) +
                                                                     int(tx_results_crc_oversized_2['FrameCount']) +
                                                                     int(tx_results_total_len_1k_2['FrameCount']))

        spirent_good_check_1 = False
        spirent_good_check_2 = False
        dut_good_check_1 = False
        dut_good_check_2 = False

        if total_good_tx_1 == total_good_rx_spirent_1:
            fun_test.log("Counters on spirent have matched for port %s" % port_1)
            spirent_good_check_1 = True
        if total_good_tx_2 == total_good_rx_spirent_2:
            fun_test.log("Counters on spirent have matched for port %s" % port_2)
            spirent_good_check_2 = True

        # TODO: Get stats from DUT
        # 1. Check FramesReceivedOK on ingress DUT port
        # 2. Check FramesTransmittedOK on egress DUT port
        # 3. Set DUT check to true
        dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1)
        fun_test.test_assert(dut_port_1_results, message="Ensure stats are obtained for %s" % dut_port_1)
        dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2)
        fun_test.test_assert(dut_port_2_results, message="Ensure stats are obtained for %s" % dut_port_2)

        dut_port_1_transmit = get_dut_output_stats_value(dut_port_1_results, FRAMES_TRANSMITTED_OK)
        dut_port_1_receive_jabbers = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_JABBERS, tx=False)
        dut_port_1_receive_oversized = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_OVERSIZE_PKTS,
                                                                  tx=False)
        dut_port_1_receive = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)
        dut_port_1_good_received = int(dut_port_1_receive) - int(tx_results_total_len_1['FrameCount'])
        dut_port_2_transmit = get_dut_output_stats_value(dut_port_2_results, FRAMES_TRANSMITTED_OK)
        dut_port_2_receive = get_dut_output_stats_value(dut_port_2_results, FRAMES_RECEIVED_OK, tx=False)
        dut_port_2_receive_jabbers = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_JABBERS, tx=False)
        dut_port_2_receive_oversized = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_OVERSIZE_PKTS,
                                                                  tx=False)
        dut_port_2_good_received = int(dut_port_2_receive) - int(tx_results_total_len_2['FrameCount'])

        dut_port_2_good_transmit = int(dut_port_2_transmit) - (int(tx_results_total_len_1k_1['FrameCount']) +
                                                               int(tx_results_mtu_1['FrameCount']) +
                                                               int(tx_results_total_len_padded_1['FrameCount']) +
                                                               int(tx_results_total_len_100B_1['FrameCount']))
        dut_port_1_good_transmit = int(dut_port_1_transmit) - (int(tx_results_total_len_1k_2['FrameCount']) +
                                                               int(tx_results_mtu_2['FrameCount']) +
                                                               int(tx_results_total_len_padded_2['FrameCount']) +
                                                               int(tx_results_total_len_100B_2['FrameCount']))

        fun_test.test_assert_expected(expected=int(dut_port_1_good_received),
                                      actual=int(dut_port_2_transmit),
                                      message="Ensure frames received ok on %s port are transmitted by %s port" % (
                                      dut_port_1, dut_port_2))
        fun_test.test_assert_expected(expected=total_good_tx_1, actual=int(dut_port_2_good_transmit),
                                      message="Ensure good frames sent from spirent are transmitted out via DUT")
        dut_good_check_1 = True
        
        fun_test.test_assert_expected(expected=int(dut_port_2_good_received),
                                      actual=int(dut_port_1_transmit),
                                      message="Ensure frames received ok on %s port are transmitted by %s port" % (
                                      dut_port_2, dut_port_1))
        fun_test.test_assert_expected(expected=total_good_tx_2, actual=int(dut_port_1_good_transmit),
                                      message="Ensure good frames sent from spirent are transmitted out via DUT")
        dut_good_check_2 = True

        fun_test.test_assert((spirent_good_check_1 or dut_good_check_1),
                             message="Check counters for traffic sent from port %s" % port_1)

        fun_test.test_assert((spirent_good_check_2 or dut_good_check_2),
                             message="Check counters for traffic sent from port %s" % port_2)

        fun_test.test_assert(port_2_errors['result'], "Check no other error counter has gone up")
        fun_test.test_assert(port_1_errors['result'], "Check no other error counter has gone up")


if __name__ == "__main__":
    ts = SpirentSetup()
    ts.add_test_case(TestCase1())
    ts.add_test_case(TestCase2())
    ts.add_test_case(TestCase3())
    ts.add_test_case(TestCase4())
    ts.add_test_case(TestCase5())
    ts.add_test_case(TestCase6())
    ts.add_test_case(TestCase7())
    ts.add_test_case(TestCase8())
    ts.run()
