from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, GeneratorConfig, Ethernet2Header, Ipv4Header


num_ports = 2
loads_file = "interface_loads.json"
streamblock_objects = {}
generator_list = []
generator_config_list = []
CRC_64B = 'CRC_64B'
CRC_1500B = 'CRC_1500B'
OVERSIZED = 'OVERSIZED'
PREAMBLE = 'PREAMBLE'
SFD = 'SFD'
CRC_OVERSIZED = 'CRC_OVERSIZED'
MTU_EGRESS = 'MTU_EGRESS'
CHECKSUM_ERROR = 'CHECKSUM_ERROR'
TOTAL_LENGTH_ERROR = 'TOTAL_LENGTH_ERROR'
IHL_ERROR = 'IHL_ERROR'
IP_VERSION_ERROR = 'IP_VERSION_ERROR'
TTL_ERROR = 'TTL_ERROR'
GOOD_FRAME = 'GOOD_FRAME'
MIN_FRAME_LENGTH = 64
MAX_FRAME_LENGTH = 1500
OVERSIZED_FRAME_LENGTH = 2000
MTU_TEST_FRAME_LENGTH = 1400
PREAMBLE_ERROR = '55555555556655d5'
SFD_ERROR = '55555555555555d6'

stream_list = [CRC_64B, CRC_1500B, OVERSIZED, PREAMBLE, SFD, CRC_OVERSIZED, CHECKSUM_ERROR,
               TOTAL_LENGTH_ERROR, IHL_ERROR, IP_VERSION_ERROR, TTL_ERROR, GOOD_FRAME]

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
        global template_obj, port_1, port_2, duration_seconds, subscribe_results, port_obj_list, bad_frame_load, good_frame_load

        fun_test.log("Creating Template object")
        template_obj = SpirentEthernetTrafficTemplate(session_name="test_good_bad_frames")
        fun_test.test_assert(template_obj, "Create template object")

        result = template_obj.setup(no_of_ports_needed=num_ports)
        fun_test.test_assert(result['result'], "Configure setup")

        port_obj_list = result['port_list']

        source_mac1 = template_obj.stc_manager.dut_config['source_mac1']
        destination_mac1 = template_obj.stc_manager.dut_config['destination_mac1']
        source_ip1 = template_obj.stc_manager.dut_config['source_ip1']
        source_ip2 = template_obj.stc_manager.dut_config['source_ip2']
        destination_ip1 = template_obj.stc_manager.dut_config['destination_ip1']
        destination_ip2 = template_obj.stc_manager.dut_config['destination_ip2']
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

            if str(port) == 'port' + str(port_nos[0]):
                current_source_ip = source_ip1
                current_destination_ip = destination_ip1
                port_1 = port
            else:
                port_2 = port
            for stream_type in stream_list:
                current_streamblock_obj = StreamBlock()
                current_streamblock_obj.Load = 1
                current_streamblock_obj.LoadUnit = current_streamblock_obj.LOAD_UNIT_MEGABITS_PER_SECOND
                current_ethernet_obj = Ethernet2Header(destination_mac=destination_mac1, source_mac=source_mac1)
                current_ipv4_obj = Ipv4Header(destination_address=current_destination_ip, source_address=current_source_ip)

                if stream_type == CRC_64B:
                    current_streamblock_obj.FixedFrameLength = MIN_FRAME_LENGTH
                    current_streamblock_obj.EnableFcsErrorInsertion = True
                elif stream_type == CRC_1500B:
                    current_streamblock_obj.FixedFrameLength = MAX_FRAME_LENGTH
                    current_streamblock_obj.EnableFcsErrorInsertion = True
                elif stream_type == OVERSIZED:
                    current_streamblock_obj.FixedFrameLength = OVERSIZED_FRAME_LENGTH
                elif stream_type == PREAMBLE:
                    current_ethernet_obj.preamble = PREAMBLE_ERROR
                elif stream_type == SFD:
                    current_ethernet_obj.preamble = SFD_ERROR
                elif stream_type == CRC_OVERSIZED:
                    current_streamblock_obj.EnableFcsErrorInsertion = True
                    current_streamblock_obj.FixedFrameLength = OVERSIZED_FRAME_LENGTH
                elif stream_type == MTU_EGRESS:
                    current_streamblock_obj.FixedFrameLength = MTU_TEST_FRAME_LENGTH
                elif stream_type == CHECKSUM_ERROR:
                    current_ipv4_obj.checksum = current_ipv4_obj.CHECKSUM_ERROR
                elif stream_type == TOTAL_LENGTH_ERROR:
                    current_ipv4_obj.totalLength = current_ipv4_obj.TOTAL_HEADER_LENGTH_ERROR
                elif stream_type == IHL_ERROR:
                    current_ipv4_obj.ihl = '3'
                elif stream_type == IP_VERSION_ERROR:
                    current_ipv4_obj.version = '1'
                elif stream_type == TTL_ERROR:
                    current_ipv4_obj.ttl = '0'
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

                configure_ip4 = template_obj.stc_manager.configure_frame_stack(
                    stream_block_handle=current_streamblock_obj.spirent_handle, header_obj=current_ipv4_obj)
                fun_test.simple_assert(configure_ip4, "Ensure ethernet frame is configured for stream %s on port %s and streamblock %s" % (
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
                              summary="Test CRC error with 64B frame size ",
                              steps="""
                        1. Active streams CRC error with 64B frame size on both ports
                        2. Execute generator traffic on both ports
                        3. All frames must be dropped and Rx count of spirent must be 0
                        """)

    def setup(self):
        # Deactivate all streamblocks
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivating all streamblock")

    def cleanup(self):
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        # Activate streams having CRC error and 64B frame size
        activate = template_obj.activate_stream_blocks([streamblock_objects[CRC_64B][str(port_1)],
                                                        streamblock_objects[CRC_64B][str(port_2)]])
        fun_test.test_assert(activate, "Activate streamblocks for %s " % CRC_64B)

        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=generator_list)
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=duration_seconds)

        # Get results for streamblock 1
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[CRC_64B][
                                                                                str(port_1)].spirent_handle))
        tx_results_1 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[CRC_64B][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_objects[CRC_64B][
                                                                                str(port_1)].spirent_handle))
        rx_results_1 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_objects[CRC_64B][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        # Get streambllock 2 results
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[CRC_64B][
                                                                                str(port_2)].spirent_handle))
        tx_results_2 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[CRC_64B][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_objects[CRC_64B][
                                                                                str(port_2)].spirent_handle))
        rx_results_2 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_objects[CRC_64B][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        fun_test.log("Tx 1 Results %s " % tx_results_1)
        fun_test.log("Rx 1 Results %s" % rx_results_1)
        fun_test.log("Tx 2 Results %s " % tx_results_2)
        fun_test.log("Rx 2 Results %s" % rx_results_2)

        expected_rx_count = 0
        fun_test.test_assert(tx_results_1["FrameCount"] > 0,
                             message="Ensure some frames were sent from %s" % str(port_1))
        fun_test.test_assert_expected(actual=rx_results_1["FrameCount"], expected=expected_rx_count,
                                      message="Ensure packets are dropped")
        fun_test.test_assert(tx_results_2["FrameCount"] > 0,
                             message="Ensure some frames were sent from %s" % str(port_1))
        fun_test.test_assert_expected(actual=rx_results_2["FrameCount"], expected=expected_rx_count,
                                      message="Ensure packets are dropped")


class TestCase2(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Test CRC error with 1500B frame size ",
                              steps="""
                        1. Active streams CRC error with 1500B frame size on both ports
                        2. Execute generator traffic on both ports
                        3. Frames must not be dropped but be sent with CRC errors
                        """)

    def setup(self):
        # Deactivate all streamblocks
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivating all streamblocks")

    def cleanup(self):
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        # Activate streams having CRC error and 64B frame size
        activate = template_obj.activate_stream_blocks([streamblock_objects[CRC_1500B][str(port_1)],
                                                        streamblock_objects[CRC_1500B][str(port_2)]])
        fun_test.test_assert(activate, "Activate streamblocks for %s " % CRC_1500B)

        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=generator_list)
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=duration_seconds)

        # Get results for streamblock 1
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[CRC_1500B][
                                                                                str(port_1)].spirent_handle))
        tx_results_1 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[CRC_1500B][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_objects[CRC_1500B][
                                                                                str(port_1)].spirent_handle))
        rx_results_1 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_objects[CRC_1500B][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        # Get streambllock 2 results
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[CRC_1500B][
                                                                                str(port_2)].spirent_handle))
        tx_results_2 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[CRC_1500B][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_objects[CRC_1500B][
                                                                                str(port_2)].spirent_handle))
        rx_results_2 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_objects[CRC_1500B][str(port_2)].spirent_handle,
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
        fun_test.log("Analyzer port results on port %s are %s" % (port_2,rx_port_analyzer_results_1))
        fun_test.log("Analyzer port results on port %s are %s" % (port_1, rx_port_analyzer_results_2))

        fun_test.test_assert(template_obj.compare_result_attribute(tx_results_1, rx_results_1),
                             message="Ensure frames are received")
        fun_test.test_assert_expected(actual=tx_results_1["FrameCount"],
                                      expected=rx_port_analyzer_results_1['FcsErrorFrameCount'],
                                      message="Ensure packets are received with FcsError")
        fun_test.test_assert(template_obj.compare_result_attribute(tx_results_2, rx_results_2),
                             message="Ensure frames are received")
        fun_test.test_assert_expected(actual=tx_results_2["FrameCount"],
                                      expected=rx_port_analyzer_results_2['FcsErrorFrameCount'],
                                      message="Ensure packets are received with FcsError")


class TestCase3(FunTestCase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Test Oversizedframe size ",
                              steps="""
                        1. Active Oversized streams with 2000B frame size on both ports
                        2. Execute generator traffic on both ports
                        3. Frames must not be dropped but be sent with CRC errors
                        """)

    def setup(self):
        # Deactivate all streamblocks
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivating all streamblocks")

    def cleanup(self):
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        # Activate streams having CRC error and 64B frame size
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

        fun_test.test_assert(template_obj.compare_result_attribute(tx_results_1, rx_results_1),
                             message="Ensure frames are received")
        fun_test.test_assert_expected(actual=tx_results_1["FrameCount"],
                                      expected=rx_port_analyzer_results_1['FcsErrorFrameCount'],
                                      message="Ensure packets are received with FcsError")
        fun_test.test_assert(template_obj.compare_result_attribute(tx_results_2, rx_results_2),
                             message="Ensure frames are received")
        fun_test.test_assert_expected(actual=tx_results_2["FrameCount"],
                                      expected=rx_port_analyzer_results_2['FcsErrorFrameCount'],
                                      message="Ensure packets are received with FcsError")


class TestCase4(FunTestCase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Test CRC + Oversized frame size ",
                              steps="""
                        1. Active Oversized streams with 2000B frame size on both ports
                        2. Execute generator traffic on both ports
                        3. Frames must not be dropped but be sent with CRC errors
                        """)

    def setup(self):
        # Deactivate all streamblocks
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivating all streamblocks")

    def cleanup(self):
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        # Activate streams having CRC error and 64B frame size
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

        fun_test.test_assert(template_obj.compare_result_attribute(tx_results_1, rx_results_1),
                             message="Ensure frames are received")
        fun_test.test_assert_expected(actual=tx_results_1["FrameCount"],
                                      expected=rx_port_analyzer_results_1['FcsErrorFrameCount'],
                                      message="Ensure packets are received with FcsError")
        fun_test.test_assert(template_obj.compare_result_attribute(tx_results_2, rx_results_2),
                             message="Ensure frames are received")
        fun_test.test_assert_expected(actual=tx_results_2["FrameCount"],
                                      expected=rx_port_analyzer_results_2['FcsErrorFrameCount'],
                                      message="Ensure packets are received with FcsError")


class TestCase5(FunTestCase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Test DUT with wrong preamble",
                              steps="""
                        1. Active streams which have wrong preamble both ports
                        2. Execute generator traffic on both ports
                        3. All frames must be dropped and Rx count of spirent must be 0
                        """)

    def setup(self):
        # Deactivate all streamblocks
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivating all streamblock")

    def cleanup(self):
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        # Activate streams having CRC error and 64B frame size
        activate = template_obj.activate_stream_blocks([streamblock_objects[PREAMBLE][str(port_1)],
                                                        streamblock_objects[PREAMBLE][str(port_2)]])
        fun_test.test_assert(activate, "Activate streamblocks for %s " % PREAMBLE)

        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=generator_list)
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=duration_seconds)

        # Get results for streamblock 1
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[PREAMBLE][
                                                                                str(port_1)].spirent_handle))
        tx_results_1 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[PREAMBLE][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_objects[PREAMBLE][
                                                                                str(port_1)].spirent_handle))
        rx_results_1 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_objects[PREAMBLE][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        # Get streambllock 2 results
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[PREAMBLE][
                                                                                str(port_2)].spirent_handle))
        tx_results_2 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[PREAMBLE][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_objects[PREAMBLE][
                                                                                str(port_2)].spirent_handle))
        rx_results_2 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_objects[PREAMBLE][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        fun_test.log("Tx 1 Results %s " % tx_results_1)
        fun_test.log("Rx 1 Results %s" % rx_results_1)
        fun_test.log("Tx 2 Results %s " % tx_results_2)
        fun_test.log("Rx 2 Results %s" % rx_results_2)

        expected_rx_count = 0
        fun_test.test_assert(tx_results_1["FrameCount"] > 0,
                             message="Ensure some frames were sent from %s" % str(port_1))
        fun_test.test_assert_expected(actual=rx_results_1["FrameCount"], expected=expected_rx_count,
                                      message="Ensure packets are dropped as PREAMBLE is incorrect")
        fun_test.test_assert(tx_results_2["FrameCount"] > 0,
                             message="Ensure some frames were sent from %s" % str(port_1))
        fun_test.test_assert_expected(actual=rx_results_2["FrameCount"], expected=expected_rx_count,
                                      message="Ensure packets are dropped as PREAMBLE is incorrect")
        
        
class TestCase6(FunTestCase):
    def describe(self):
        self.set_test_details(id=6,
                              summary="Test DUT with wrong SFD",
                              steps="""
                        1. Active streams with incorrect SFD both ports
                        2. Execute generator traffic on both ports
                        3. All frames must be dropped and Rx count of spirent must be 0
                        """)

    def setup(self):
        # Deactivate all streamblocks
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivating all streamblock")

    def cleanup(self):
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        # Activate streams having CRC error and 64B frame size
        activate = template_obj.activate_stream_blocks([streamblock_objects[SFD][str(port_1)],
                                                        streamblock_objects[SFD][str(port_2)]])
        fun_test.test_assert(activate, "Activate streamblocks for %s " % SFD)

        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=generator_list)
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=duration_seconds)

        # Get results for streamblock 1
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[SFD][
                                                                                str(port_1)].spirent_handle))
        tx_results_1 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[SFD][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_objects[SFD][
                                                                                str(port_1)].spirent_handle))
        rx_results_1 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_objects[SFD][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        # Get streambllock 2 results
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[SFD][
                                                                                str(port_2)].spirent_handle))
        tx_results_2 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[SFD][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_objects[SFD][
                                                                                str(port_2)].spirent_handle))
        rx_results_2 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_objects[SFD][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        fun_test.log("Tx 1 Results %s " % tx_results_1)
        fun_test.log("Rx 1 Results %s" % rx_results_1)
        fun_test.log("Tx 2 Results %s " % tx_results_2)
        fun_test.log("Rx 2 Results %s" % rx_results_2)

        expected_rx_count = 0
        fun_test.test_assert(tx_results_1["FrameCount"] > 0,
                             message="Ensure some frames were sent from %s" % str(port_1))
        fun_test.test_assert_expected(actual=rx_results_1["FrameCount"], expected=expected_rx_count,
                                      message="Ensure packets are dropped as SFD is incorrect")
        fun_test.test_assert(tx_results_2["FrameCount"] > 0,
                             message="Ensure some frames were sent from %s" % str(port_1))
        fun_test.test_assert_expected(actual=rx_results_2["FrameCount"], expected=expected_rx_count,
                                      message="Ensure packets are dropped as SFD is incorrect")
        
        
class TestCase7(FunTestCase):
    def describe(self):
        self.set_test_details(id=7,
                              summary="Test DUT with IP checksum error",
                              steps="""
                        1. Active streams with IP checksum error on both ports
                        2. Execute generator traffic on both ports
                        3. All frames must be dropped and Rx count of spirent must be 0
                        """)

    def setup(self):
        # Deactivate all streamblocks
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivated all streamblocks")

    def cleanup(self):
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        # Activate streams having CRC error and 64B frame size
        activate = template_obj.activate_stream_blocks([streamblock_objects[CHECKSUM_ERROR][str(port_1)],
                                                        streamblock_objects[CHECKSUM_ERROR][str(port_2)]])
        fun_test.test_assert(activate, "Activate streamblocks for %s " % CHECKSUM_ERROR)

        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=generator_list)
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=duration_seconds)

        # Get results for streamblock 1
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[CHECKSUM_ERROR][
                                                                                str(port_1)].spirent_handle))
        tx_results_1 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[CHECKSUM_ERROR][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_objects[CHECKSUM_ERROR][
                                                                                str(port_1)].spirent_handle))
        rx_results_1 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_objects[CHECKSUM_ERROR][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        # Get streambllock 2 results
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[CHECKSUM_ERROR][
                                                                                str(port_2)].spirent_handle))
        tx_results_2 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[CHECKSUM_ERROR][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_objects[CHECKSUM_ERROR][
                                                                                str(port_2)].spirent_handle))
        rx_results_2 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_objects[CHECKSUM_ERROR][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        fun_test.log("Tx 1 Results %s " % tx_results_1)
        fun_test.log("Rx 1 Results %s" % rx_results_1)
        fun_test.log("Tx 2 Results %s " % tx_results_2)
        fun_test.log("Rx 2 Results %s" % rx_results_2)

        expected_rx_count = 0
        fun_test.test_assert(tx_results_1["FrameCount"] > 0,
                             message="Ensure some frames were sent from %s" % str(port_1))
        fun_test.test_assert_expected(actual=rx_results_1["FrameCount"], expected=expected_rx_count,
                                      message="Ensure packets are dropped as CHECKSUM_ERROR is present in the frame")
        fun_test.test_assert(tx_results_2["FrameCount"] > 0,
                             message="Ensure some frames were sent from %s" % str(port_1))
        fun_test.test_assert_expected(actual=rx_results_2["FrameCount"], expected=expected_rx_count,
                                      message="Ensure packets are dropped as CHECKSUM_ERROR is present in the frame")


class TestCase8(FunTestCase):
    def describe(self):
        self.set_test_details(id=8,
                              summary="Test DUT with IP total length error",
                              steps="""
                        1. Active streams with IP total length error on both ports
                        2. Execute generator traffic on both ports
                        3. All frames must be dropped and Rx count of spirent must be 0
                        """)

    def setup(self):
        # Deactivate all streamblocks
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivated all streamblocks")

    def cleanup(self):
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        # Activate streams having CRC error and 64B frame size
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

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_objects[TOTAL_LENGTH_ERROR][
                                                                                str(port_1)].spirent_handle))
        rx_results_1 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_objects[TOTAL_LENGTH_ERROR][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        # Get streambllock 2 results
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[TOTAL_LENGTH_ERROR][
                                                                                str(port_2)].spirent_handle))
        tx_results_2 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[TOTAL_LENGTH_ERROR][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_objects[TOTAL_LENGTH_ERROR][
                                                                                str(port_2)].spirent_handle))
        rx_results_2 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_objects[TOTAL_LENGTH_ERROR][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        fun_test.log("Tx 1 Results %s " % tx_results_1)
        fun_test.log("Rx 1 Results %s" % rx_results_1)
        fun_test.log("Tx 2 Results %s " % tx_results_2)
        fun_test.log("Rx 2 Results %s" % rx_results_2)

        expected_rx_count = 0
        fun_test.test_assert(tx_results_1["FrameCount"] > 0,
                             message="Ensure some frames were sent from %s" % str(port_1))
        fun_test.test_assert_expected(actual=rx_results_1["FrameCount"], expected=expected_rx_count,
                                      message="Ensure packets are dropped as TOTAL_LENGTH_ERROR is present in the frame")
        fun_test.test_assert(tx_results_2["FrameCount"] > 0,
                             message="Ensure some frames were sent from %s" % str(port_1))
        fun_test.test_assert_expected(actual=rx_results_2["FrameCount"], expected=expected_rx_count,
                                      message="Ensure packets are dropped as TOTAL_LENGTH_ERROR is present in the frame")


class TestCase9(FunTestCase):
    def describe(self):
        self.set_test_details(id=9,
                              summary="Test DUT with IP header length error",
                              steps="""
                        1. Active streams with IP total header error on both ports
                        2. Execute generator traffic on both ports
                        3. All frames must be dropped and Rx count of spirent must be 0
                        """)

    def setup(self):
        # Deactivate all streamblocks
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivated all streamblocks")

    def cleanup(self):
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        # Activate streams having CRC error and 64B frame size
        activate = template_obj.activate_stream_blocks([streamblock_objects[IHL_ERROR][str(port_1)],
                                                        streamblock_objects[IHL_ERROR][str(port_2)]])
        fun_test.test_assert(activate, "Activate streamblocks for %s " % IHL_ERROR)

        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=generator_list)
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=duration_seconds)

        # Get results for streamblock 1
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[IHL_ERROR][
                                                                                str(port_1)].spirent_handle))
        tx_results_1 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[IHL_ERROR][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_objects[IHL_ERROR][
                                                                                str(port_1)].spirent_handle))
        rx_results_1 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_objects[IHL_ERROR][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        # Get streambllock 2 results
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[IHL_ERROR][
                                                                                str(port_2)].spirent_handle))
        tx_results_2 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[IHL_ERROR][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_objects[IHL_ERROR][
                                                                                str(port_2)].spirent_handle))
        rx_results_2 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_objects[IHL_ERROR][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        fun_test.log("Tx 1 Results %s " % tx_results_1)
        fun_test.log("Rx 1 Results %s" % rx_results_1)
        fun_test.log("Tx 2 Results %s " % tx_results_2)
        fun_test.log("Rx 2 Results %s" % rx_results_2)

        expected_rx_count = 0
        fun_test.test_assert(tx_results_1["FrameCount"] > 0,
                             message="Ensure some frames were sent from %s" % str(port_1))
        fun_test.test_assert_expected(actual=rx_results_1["FrameCount"], expected=expected_rx_count,
                                      message="Ensure packets are dropped as IHL_ERROR is present in the frame")
        fun_test.test_assert(tx_results_2["FrameCount"] > 0,
                             message="Ensure some frames were sent from %s" % str(port_1))
        fun_test.test_assert_expected(actual=rx_results_2["FrameCount"], expected=expected_rx_count,
                                      message="Ensure packets are dropped as IHL_ERROR is present in the frame")


class TestCase10(FunTestCase):
    def describe(self):
        self.set_test_details(id=10,
                              summary="Test DUT with bad IP version error",
                              steps="""
                        1. Active streams with bad IP version on both ports
                        2. Execute generator traffic on both ports
                        3. All frames must be dropped and Rx count of spirent must be 0
                        """)

    def setup(self):
        # Deactivate all streamblocks
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivated all streamblocks")

    def cleanup(self):
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        # Activate streams having CRC error and 64B frame size
        activate = template_obj.activate_stream_blocks([streamblock_objects[IP_VERSION_ERROR][str(port_1)],
                                                        streamblock_objects[IP_VERSION_ERROR][str(port_2)]])
        fun_test.test_assert(activate, "Activate streamblocks for %s " % IP_VERSION_ERROR)

        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=generator_list)
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=duration_seconds)

        # Get results for streamblock 1
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[IP_VERSION_ERROR][
                                                                                str(port_1)].spirent_handle))
        tx_results_1 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[IP_VERSION_ERROR][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_objects[IP_VERSION_ERROR][
                                                                                str(port_1)].spirent_handle))
        rx_results_1 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_objects[IP_VERSION_ERROR][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        # Get streambllock 2 results
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[IP_VERSION_ERROR][
                                                                                str(port_2)].spirent_handle))
        tx_results_2 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[IP_VERSION_ERROR][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_objects[IP_VERSION_ERROR][
                                                                                str(port_2)].spirent_handle))
        rx_results_2 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_objects[IP_VERSION_ERROR][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        fun_test.log("Tx 1 Results %s " % tx_results_1)
        fun_test.log("Rx 1 Results %s" % rx_results_1)
        fun_test.log("Tx 2 Results %s " % tx_results_2)
        fun_test.log("Rx 2 Results %s" % rx_results_2)

        expected_rx_count = 0
        fun_test.test_assert(tx_results_1["FrameCount"] > 0,
                             message="Ensure some frames were sent from %s" % str(port_1))
        fun_test.test_assert_expected(actual=rx_results_1["FrameCount"], expected=expected_rx_count,
                                      message="Ensure packets are dropped as IP_VERSION_ERROR is present in the frame")
        fun_test.test_assert(tx_results_2["FrameCount"] > 0,
                             message="Ensure some frames were sent from %s" % str(port_1))
        fun_test.test_assert_expected(actual=rx_results_2["FrameCount"], expected=expected_rx_count,
                                      message="Ensure packets are dropped as IP_VERSION_ERROR is present in the frame")


class TestCase11(FunTestCase):
    def describe(self):
        self.set_test_details(id=11,
                              summary="Test DUT with TTL error in ip header",
                              steps="""
                        1. Active streams with TTL error in ip header on both ports
                        2. Execute generator traffic on both ports
                        3. All frames must be dropped and Rx count of spirent must be 0
                        """)

    def setup(self):
        # Deactivate all streamblocks
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivated all streamblocks")

    def cleanup(self):
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        # Activate streams having CRC error and 64B frame size
        activate = template_obj.activate_stream_blocks([streamblock_objects[TTL_ERROR][str(port_1)],
                                                        streamblock_objects[TTL_ERROR][str(port_2)]])
        fun_test.test_assert(activate, "Activate streamblocks for %s " % TTL_ERROR)

        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=generator_list)
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=duration_seconds)

        # Get results for streamblock 1
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[TTL_ERROR][
                                                                                str(port_1)].spirent_handle))
        tx_results_1 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[TTL_ERROR][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_objects[TTL_ERROR][
                                                                                str(port_1)].spirent_handle))
        rx_results_1 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_objects[TTL_ERROR][str(port_1)].spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        # Get streambllock 2 results
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            streamblock_objects[TTL_ERROR][
                                                                                str(port_2)].spirent_handle))
        tx_results_2 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=streamblock_objects[TTL_ERROR][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            streamblock_objects[TTL_ERROR][
                                                                                str(port_2)].spirent_handle))
        rx_results_2 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=streamblock_objects[TTL_ERROR][str(port_2)].spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        fun_test.log("Tx 1 Results %s " % tx_results_1)
        fun_test.log("Rx 1 Results %s" % rx_results_1)
        fun_test.log("Tx 2 Results %s " % tx_results_2)
        fun_test.log("Rx 2 Results %s" % rx_results_2)

        expected_rx_count = 0
        fun_test.test_assert(tx_results_1["FrameCount"] > 0,
                             message="Ensure some frames were sent from %s" % str(port_1))
        fun_test.test_assert_expected(actual=rx_results_1["FrameCount"], expected=expected_rx_count,
                                      message="Ensure packets are dropped as TTL_ERROR is present in the frame")
        fun_test.test_assert(tx_results_2["FrameCount"] > 0,
                             message="Ensure some frames were sent from %s" % str(port_1))
        fun_test.test_assert_expected(actual=rx_results_2["FrameCount"], expected=expected_rx_count,
                                      message="Ensure packets are dropped as TTL_ERROR is present in the frame")


class TestCase12(FunTestCase):
    def describe(self):
        self.set_test_details(id=12,
                              summary="Test DUT with Good+Bad frames",
                              steps="""
                        1. Active all streams on both ports including good and bad
                        2. Execute generator traffic on both ports
                        3. All good frames must be received correclty 
                        """)

    def setup(self):
        pass

    def cleanup(self):
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        duration = 60

        # Activate streams
        activate = template_obj.activate_stream_blocks()
        fun_test.test_assert(activate, "Activate all streamblocks")

        # Apply correct loads
        for port in port_obj_list:
            for stream in stream_list:
                current_stream_obj = streamblock_objects[stream][port]
                if not stream == GOOD_FRAME:
                    current_load = bad_frame_load
                else:
                    current_load = good_frame_load

                configure_stream = template_obj.stc_manager.stc.config(current_stream_obj.spirent_handle,
                                                                       Load=current_load)
                fun_test.log("Updating streamblock %s on port %s" % (current_stream_obj.spirent_handle, port))

        # Increase duration of generator configs
        for gen_config_obj in generator_config_list:
            gen_config_obj.Duration = duration

        for i in range(len(generator_config_list)):
            config_obj = template_obj.configure_generator_config(port_handle=port_obj_list[i],
                                                                 generator_config_obj=generator_config_list[i], update=True)
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

        fun_test.log("Tx 1 Results %s " % tx_results_1)
        fun_test.log("Rx 1 Results %s" % rx_results_1)
        fun_test.log("Tx 2 Results %s " % tx_results_2)
        fun_test.log("Rx 2 Results %s" % rx_results_2)

        fun_test.test_assert_expected(expected=tx_results_1["FrameCount"], actual=rx_results_1["FrameCount"],
                                      message="Check all frames from port %s are received by %s" % (port_1, port_2))
        fun_test.test_assert_expected(expected=tx_results_2["FrameCount"], actual=rx_results_2["FrameCount"],
                                      message="Check all frames from port %s are received by %s" % (port_2, port_1))

        expected_fcs_errors = 0
        fun_test.test_assert_expected(expected=expected_fcs_errors, actual=rx_results_1["FcsErrorFrameCount"],
                                      message="Ensure fcs errors are not seen in good frames on port %s" % port_2)
        fun_test.test_assert_expected(expected=expected_fcs_errors, actual=rx_results_1["FcsErrorFrameCount"],
                                      message="Ensure fcs errors are not seen in good frames on port %s" % port_2)


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
    ts.add_test_case(TestCase9())
    ts.add_test_case(TestCase10())
    ts.add_test_case(TestCase11())
    ts.add_test_case(TestCase12())
    ts.run()
