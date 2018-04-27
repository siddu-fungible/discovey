from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, GeneratorConfig


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
        gen_obj_1, gen_obj_2, duration_seconds, subscribe_results

        fun_test.log("Creating Template object")
        template_obj = SpirentEthernetTrafficTemplate(session_name="test_frame_size")
        fun_test.test_assert(template_obj, "Create template object")

        result = template_obj.setup(no_of_ports_needed=num_ports)
        fun_test.test_assert(result['result'], "Configure setup")

        port_1 = result['port_list'][0]
        port_2 = result['port_list'][1]

        srcMac = template_obj.stc_manager.dut_config['source_mac1']
        destMac = template_obj.stc_manager.dut_config['destination_mac1']
        srcIp = template_obj.stc_manager.dut_config['source_ip1']
        destIp = template_obj.stc_manager.dut_config['destination_ip1']
        destIp2 = template_obj.stc_manager.dut_config['destination_ip2']
        gateway = template_obj.stc_manager.dut_config['gateway1']
        interface_mode = template_obj.stc_manager.interface_mode

        #  Read loads from file
        file_path = fun_test.get_script_parent_directory() + "/" + loads_file
        output = fun_test.parse_file_to_json(file_path)
        Load = output[interface_mode]["incremental_load_mbps"]
        ether_type = "0800"
        min_frame_lenggth = 64
        max_frame_length = 16352
        mtu = max_frame_length
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
        gen_config_obj.DurationMode = gen_config_obj.DURATION_MODE_SECONDS
        gen_config_obj.AdvancedInterleaving = True

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
        pass

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
        rx_port_analyzer_results = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_2, subscribe_handle=subscribe_results['analyzer_subscribe'])

        fun_test.log("Tx 1 Results %s " % tx_results_1)
        fun_test.log("Rx 1 Results %s" % rx_results_1)
        fun_test.log("Tx 2 Results %s " % tx_results_2)
        fun_test.log("Rx 2 Results %s" % rx_results_2)
        fun_test.log("Rx Port Analyzer Results %s" % rx_port_analyzer_results)

        fun_test.test_assert(template_obj.compare_result_attribute(tx_results_1, rx_results_1),
                             "Check FrameCount for streamblock %s" % streamblock_obj_1.spirent_handle)
        fun_test.test_assert(template_obj.compare_result_attribute(tx_results_2, rx_results_2),
                             "Check FrameCount for streamblock %s" % streamblock_obj_2.spirent_handle)

        zero_counter_seen = template_obj.check_non_zero_error_count(rx_port_analyzer_results)
        fun_test.test_assert(zero_counter_seen['result'], "Check for error counters")

        fun_test.test_assert(int(rx_results_1['FrameCount']) >= int(streamblock_obj_1.MaxFrameLength),
                             "Ensure more than %s packets are received" % str(streamblock_obj_1.MaxFrameLength))


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

        streamblock1 = template_obj.configure_stream_block(streamblock_obj_1, port_1, update=True)
        fun_test.test_assert(streamblock1, "Configure streamblock %s on port %s" % (streamblock_obj_1.spirent_handle,
                                                                                    port_1))

        streamblock2 = template_obj.configure_stream_block(streamblock_obj_2, port_2, update=True)
        fun_test.test_assert(streamblock2, "Configure streamblock %s on port %s" % (streamblock_obj_2.spirent_handle,
                                                                                    port_2))

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
        rx_port_analyzer_results = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_2, subscribe_handle=subscribe_results['analyzer_subscribe'])

        fun_test.log("Tx 1 Results %s " % tx_results_1)
        fun_test.log("Rx 1 Results %s" % rx_results_1)
        fun_test.log("Tx 2 Results %s " % tx_results_2)
        fun_test.log("Rx 2 Results %s" % rx_results_2)
        fun_test.log("Rx Port Analyzer Results %s" % rx_port_analyzer_results)

        fun_test.test_assert(template_obj.compare_result_attribute(tx_results_1, rx_results_1),
                             "Check FrameCount for streamblock %s" % streamblock_obj_1.spirent_handle)
        fun_test.test_assert(template_obj.compare_result_attribute(tx_results_2, rx_results_2),
                             "Check FrameCount for streamblock %s" % streamblock_obj_2.spirent_handle)

        zero_counter_seen = template_obj.check_non_zero_error_count(rx_port_analyzer_results)
        fun_test.test_assert(zero_counter_seen['result'], "Check for error counters")


if __name__ == "__main__":
    ts = SpirentSetup()
    ts.add_test_case(TestCase1())
    ts.add_test_case(TestCase2())
    ts.run()
