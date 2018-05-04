from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, Ethernet2Header, GeneratorConfig, AnalyzerConfig
from collections import OrderedDict

stream_port_obj_dict = OrderedDict()
performance_data = OrderedDict()
latency_results = None
jitter_results = None


class NuTransitPerformance(FunTestScript):
    MTU = 16380
    NO_OF_PORTS = 2
    EXPECTED_PERFORMANCE_DATA_FILE_NAME = "transit_performance.json"
    port1 = None

    def describe(self):
        self.set_test_details(steps="""
        1. Check the health of Spirent Test Center 
        2. Create %d port and ensure ports are online
        3. Change interface MTU to %d on all ports 
        4. Create raw streams with EthernetII and IPv4 headers on both ports
        5. Set load unit to Mbps for each stream and set different frame sizes to each stream
        6. Enable PRBS and signature
        7. Configure mac and ip addresses as per DUT
        """ % (self.NO_OF_PORTS, self.MTU))

    def setup(self):
        global template_obj
        global performance_data

        template_obj = SpirentEthernetTrafficTemplate(session_name="performance_Unidirectional")
        result = template_obj.setup(no_of_ports_needed=self.NO_OF_PORTS)
        fun_test.test_assert(result['result'], "Ensure Setup is done")
        self.port1 = result['port_list'][0]

        source_mac = template_obj.stc_manager.dut_config['source_mac1']
        destination_mac = template_obj.stc_manager.dut_config['destination_mac1']
        source_ip1 = template_obj.stc_manager.dut_config['source_ip1']
        destination_ip1 = template_obj.stc_manager.dut_config['destination_ip1']
        gateway = template_obj.stc_manager.dut_config['gateway1']
        ether_type = Ethernet2Header.INTERNET_IP_ETHERTYPE

        checkpoint = "Change MTU for interface %s to %d" % (str(result['interface_obj_list'][0]), self.MTU)
        for interface_obj in result['interface_obj_list']:
            interface_obj.Mtu = self.MTU
            mtu_update_result = template_obj.configure_physical_interface(interface_obj=interface_obj)
            fun_test.simple_assert(mtu_update_result, checkpoint)
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Read Performance expected data for fixed size scenario"
        file_path = fun_test.get_script_parent_directory() + "/" + self.EXPECTED_PERFORMANCE_DATA_FILE_NAME
        performance_data = template_obj.read_json_file_contents(file_path=file_path)
        fun_test.simple_assert(expression=performance_data, message=checkpoint)

        frame_load_dict = performance_data['fixed_size']['frames']

        stream_objs = []
        for key in frame_load_dict:
            stream_objs.append(StreamBlock(fill_type=StreamBlock.FILL_TYPE_PRBS,
                                           insert_signature=True,
                                           fixed_frame_length=frame_load_dict[key][0],
                                           load=frame_load_dict[key][1],
                                           load_unit=StreamBlock.LOAD_UNIT_MEGABITS_PER_SECOND))
        stream_port_obj_dict[self.port1] = stream_objs

        # Create Streams under port1
        for stream_obj in stream_objs:
            checkpoint = "Create a raw stream with %d frame size under %s" % (stream_obj.FixedFrameLength,
                                                                              self.port1)
            result = template_obj.configure_stream_block(stream_block_obj=stream_obj,
                                                         port_handle=self.port1)
            fun_test.test_assert(expression=result, message=checkpoint)

            checkpoint = "Configure Mac address for %s " % stream_obj.spirent_handle
            result = template_obj.stc_manager.configure_mac_address(streamblock=stream_obj.spirent_handle,
                                                                    source_mac=source_mac,
                                                                    destination_mac=destination_mac,
                                                                    ethernet_type=ether_type)
            fun_test.simple_assert(expression=result, message=checkpoint)

            checkpoint = "Configure IP address for %s " % stream_obj.spirent_handle
            result = template_obj.stc_manager.configure_ip_address(streamblock=stream_obj.spirent_handle,
                                                                   source=source_ip1,
                                                                   destination=destination_ip1,
                                                                   gateway=gateway)
            fun_test.simple_assert(expression=result, message=checkpoint)

            checkpoint = "Deactivate All Streams under %s" % self.port1
            result = template_obj.deactivate_stream_blocks(stream_obj_list=[stream_obj])
            fun_test.test_assert(result, checkpoint)

    def cleanup(self):
        template_obj.populate_performance_counters_json(test_name="NU Transit Performance Unidirectional Fixed Frames",
                                                        latency_results=latency_results,
                                                        jitter_results=jitter_results,
                                                        file_name="nu_transit_performance_unidirectional_fixed_size")

        template_obj.cleanup()


class NuTransitLatencyTest(FunTestCase):
    generator_port_obj_dict = {}
    analyzer_port_obj_dict = {}
    subscribe_results = {}
    expected_latency_data = {}
    tolerance_percent = None
    port = None
    traffic_duration = None

    def describe(self):
        self.set_test_details(id=1,
                              summary="NU Transit Performance Unidirectional Latency Test",
                              steps="""
                              1. Get port handles
                              2. Create Generator Config for each port and set below parameters
                                 a. Set Duration 60 secs (configurable)
                                 b. Scheduling mode to Rate based
                                 c. Timestamp reference location to END_OF_FRAME
                              3. Create Analyzer config for each port and set below parameter
                                 a. Timestamp reference location to END_OF_FRAME
                              4. Activate stream on all ports and generator traffic
                              5. Validate Tx and Rx rate for active streams under each port
                              6. Wait for traffic to complete
                              7. Validate Tx FrameCount and Rx FrameCount for active streams under each port
                              8. Ensure no errors are seen 
                              9. Validate latency numbers for each streams under each port
                              10. Deactivate current stream  
                              """)

    def setup(self):
        ports = template_obj.stc_manager.get_port_list()
        self.port = ports[0]
        fun_test.simple_assert(self.port, "Get Port handle")
        self.traffic_duration = performance_data['fixed_size']['traffic_duration']

        port1_generator_config = GeneratorConfig(scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED,
                                                 duration=self.traffic_duration,
                                                 duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                 time_stamp_latch_mode=GeneratorConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)

        port1_analyzer_config = AnalyzerConfig(timestamp_latch_mode=AnalyzerConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)

        port2_analyzer_config = AnalyzerConfig(timestamp_latch_mode=AnalyzerConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)

        self.generator_port_obj_dict[self.port] = port1_generator_config

        self.analyzer_port_obj_dict[self.port] = port1_analyzer_config

        checkpoint = "Create Generator Config for %s port" % self.port
        result = template_obj.configure_generator_config(port_handle=self.port,
                                                         generator_config_obj=port1_generator_config)
        fun_test.simple_assert(expression=result, message=checkpoint)

        checkpoint = "Create Analyzer Config for %s port" % self.port
        result = template_obj.configure_analyzer_config(port_handle=self.port,
                                                        analyzer_config_obj=port1_analyzer_config)
        fun_test.simple_assert(result, checkpoint)

        checkpoint = "Create Analyzer Config for %s port" % ports[1]
        result = template_obj.configure_analyzer_config(port_handle=ports[1],
                                                        analyzer_config_obj=port2_analyzer_config)
        fun_test.simple_assert(result, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribe_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(expression=self.subscribe_results['result'], message=checkpoint)

        self.expected_latency_data = performance_data['fixed_size']['latency']
        self.tolerance_percent = performance_data['fixed_size']['tolerance_percent']

    def run(self):
        port1 = self.port
        global latency_results
        latency_results = OrderedDict()

        for stream_obj in stream_port_obj_dict[port1]:
            frame_size = str(stream_obj.FixedFrameLength)
            load = stream_obj.Load
            key = "frame_%s" % frame_size

            checkpoint = "Performance for %s frame size with %s load" % (frame_size, str(load))
            message = "---------------------------------> Start %s  <---------------------------------" % checkpoint
            fun_test.log(message)
            fun_test.add_checkpoint(message)

            checkpoint = "Activate %s frame size streams for all port" % frame_size
            result = template_obj.activate_stream_blocks(stream_obj_list=[stream_obj])
            fun_test.simple_assert(result, checkpoint)

            checkpoint = "Enable Generator Config and start traffic for %d secs for all ports" % self.traffic_duration
            result = template_obj.enable_generator_configs(generator_configs=[
                self.generator_port_obj_dict[port1].spirent_handle])
            fun_test.simple_assert(expression=result, message=checkpoint)

            checkpoint = "Validate Tx and Rx Rate"
            rate_result = template_obj.validate_traffic_rate_results(
                rx_summary_subscribe_handle=self.subscribe_results['rx_summary_subscribe'],
                tx_summary_subscribe_handle=self.subscribe_results['tx_stream_subscribe'],
                stream_objects=[stream_obj])
            fun_test.simple_assert(expression=rate_result['result'], message=checkpoint)
            fun_test.sleep("Waiting for traffic to complete", seconds=self.traffic_duration)

            checkpoint = "Validate Latency Results"
            latency_result = template_obj.validate_performance_result(
                tx_subscribe_handle=self.subscribe_results['tx_subscribe'],
                rx_subscribe_handle=self.subscribe_results['rx_summary_subscribe'],
                stream_objects=[stream_obj], expected_latency_count=self.expected_latency_data,
                tolerance_percent=self.tolerance_percent)
            fun_test.simple_assert(expression=latency_result['result'], message=checkpoint)

            checkpoint = "Ensure no errors are seen for port %s" % \
                         self.analyzer_port_obj_dict[port1].spirent_handle
            analyzer_rx_results = template_obj.stc_manager.get_rx_port_analyzer_results(
                port_handle=port1, subscribe_handle=self.subscribe_results['analyzer_subscribe'])
            result = template_obj.check_non_zero_error_count(rx_results=analyzer_rx_results)
            fun_test.test_assert(expression=result['result'], message=checkpoint)

            checkpoint = "Deactivate %s frame size streams for all ports" % frame_size
            result = template_obj.deactivate_stream_blocks(stream_obj_list=[stream_obj])
            fun_test.simple_assert(expression=result, message=checkpoint)

            latency_results[key] = {'pps_count': rate_result['pps_count'][key],
                                    'throughput_count': rate_result['throughput_count'][key],
                                    'latency_count': latency_result[key]}

            checkpoint = "Performance for %s frame size with %s load" % (frame_size, str(load))
            message = "---------------------------------> End %s  <---------------------------------" % checkpoint
            fun_test.log(message)
            fun_test.add_checkpoint(message)

        checkpoint = "Display Latency Performance Counters"
        template_obj.display_latency_counters(result=latency_results)
        fun_test.add_checkpoint(checkpoint)

    def cleanup(self):
        template_obj.deactivate_stream_blocks(stream_obj_list=stream_port_obj_dict[self.port])


class NuTransitJitterTest(FunTestCase):
    generator_port_obj_dict = {}
    analyzer_port_obj_dict = {}
    subscribe_results = {}
    expected_jitter_data = {}
    tolerance_percent = None
    port = None
    traffic_duration = None
    view_attribute_list = ["AvgJitter", "MinJitter", "MaxJitter", "L1BitRate", "FrameRate", "FrameCount"]

    def describe(self):
        self.set_test_details(id=2,
                              summary="NU Transit Performance Unidirectional Jitter Test",
                              steps="""
                              1. Get port handles
                              2. Create Generator Config for each port and set below parameters
                                 a. Set Duration 60 secs (configurable)
                                 b. Scheduling mode to Rate based
                                 c. Timestamp reference location to END_OF_FRAME
                              3. Create Analyzer config for each port and set below parameter
                                 a. Timestamp reference location to END_OF_FRAME
                              4. Activate stream on all ports and generator traffic
                              5. Validate Tx and Rx rate for active streams under each port
                              6. Wait for traffic to complete
                              7. Validate Tx FrameCount and Rx FrameCount for active streams under each port
                              8. Ensure no errors are seen 
                              9. Validate jitter numbers for each streams under each port
                              10. Deactivate current stream  
                              """)

    def setup(self):
        ports = template_obj.stc_manager.get_port_list()
        self.port = ports[0]
        fun_test.test_assert(self.port, "Get Port handle")
        self.traffic_duration = performance_data['fixed_size']['traffic_duration']
        self.expected_jitter_data = performance_data['fixed_size']['jitter']
        self.tolerance_percent = performance_data['fixed_size']['tolerance_percent']

        port1_generator_config = GeneratorConfig(scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED,
                                                 duration=self.traffic_duration,
                                                 duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                 time_stamp_latch_mode=GeneratorConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)

        port1_analyzer_config = AnalyzerConfig(timestamp_latch_mode=AnalyzerConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)

        port2_analyzer_config = AnalyzerConfig(timestamp_latch_mode=AnalyzerConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)

        self.generator_port_obj_dict[self.port] = port1_generator_config

        self.analyzer_port_obj_dict[self.port] = port1_analyzer_config
        self.analyzer_port_obj_dict[ports[1]] = port2_analyzer_config

        checkpoint = "Create Generator Config for %s port" % self.port
        result = template_obj.configure_generator_config(port_handle=self.port,
                                                         generator_config_obj=port1_generator_config)
        fun_test.test_assert(expression=result, message=checkpoint)

        checkpoint = "Create Analyzer Config for %s port" % self.port
        result = template_obj.configure_analyzer_config(port_handle=self.port,
                                                        analyzer_config_obj=self.analyzer_port_obj_dict[self.port])
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Create Analyzer Config for %s port" % ports[1]
        result = template_obj.configure_analyzer_config(port_handle=ports[1],
                                                        analyzer_config_obj=self.analyzer_port_obj_dict[ports[1]])
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Subscribe to Tx Stream Block results"
        tx_subscribe = template_obj.subscribe_tx_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(expression=tx_subscribe, message=checkpoint)

        checkpoint = "Subscribe to Tx Stream results"
        tx_stream_subscribe = template_obj.subscribe_tx_results(parent=template_obj.stc_manager.project_handle,
                                                                result_type="TxStreamResults")
        fun_test.test_assert(tx_stream_subscribe, checkpoint)

        checkpoint = "Subscribe to Rx Stream Summary Results"
        rx_summary_subscribe = template_obj.subscribe_rx_results(parent=template_obj.stc_manager.project_handle,
                                                                 result_type="RxStreamSummaryResults",
                                                                 view_attribute_list=self.view_attribute_list,
                                                                 change_mode=True)
        fun_test.test_assert(rx_summary_subscribe, checkpoint)

        checkpoint = "Subscribe to Analyzer Results"
        analyzer_subscribe = template_obj.subscribe_analyzer_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(analyzer_subscribe, checkpoint)

        self.subscribe_results = {"tx_subscribe": tx_subscribe, "tx_stream_subscribe": tx_stream_subscribe,
                                  "rx_summary_subscribe": rx_summary_subscribe,
                                  "analyzer_subscribe": analyzer_subscribe}

    def run(self):
        stream_objs = stream_port_obj_dict[self.port]
        global jitter_results
        jitter_results = OrderedDict()
        template_obj.clear_subscribed_results(subscribe_handle_list=self.subscribe_results.values())

        for stream_obj in stream_objs:
            frame_size = str(stream_obj.FixedFrameLength)
            load = stream_obj.Load
            key = "frame_%s" % frame_size

            checkpoint = "Performance for %s frame size with %s load" % (frame_size, str(load))
            message = "---------------------------------> Start %s  <---------------------------------" % checkpoint
            fun_test.log(message)
            fun_test.add_checkpoint(message)

            checkpoint = "Activate %s frame size streams for all ports" % frame_size
            result = template_obj.activate_stream_blocks(stream_obj_list=[stream_obj])
            fun_test.simple_assert(result, checkpoint)

            checkpoint = "Enable Generator Config and start traffic for %d secs for all ports" % self.traffic_duration
            result = template_obj.enable_generator_configs(generator_configs=[
                self.generator_port_obj_dict[self.port].spirent_handle])
            fun_test.simple_assert(expression=result, message=checkpoint)

            fun_test.sleep("Waiting for traffic to reach full throughput", seconds=5)
            checkpoint = "Validate Tx and Rx Rate"
            rate_result = template_obj.validate_traffic_rate_results(
                rx_summary_subscribe_handle=self.subscribe_results['rx_summary_subscribe'],
                tx_summary_subscribe_handle=self.subscribe_results['tx_stream_subscribe'],
                stream_objects=stream_objs, wait_before_fetching_results=False, validate_throughput=False)
            fun_test.simple_assert(expression=rate_result['result'], message=checkpoint)

            fun_test.sleep("Waiting for traffic to complete", seconds=self.traffic_duration)

            checkpoint = "Validate Jitter Results"
            jitter_result = template_obj.validate_performance_result(
                tx_subscribe_handle=self.subscribe_results['tx_subscribe'],
                rx_subscribe_handle=self.subscribe_results['rx_summary_subscribe'],
                stream_objects=stream_objs, expected_jitter_count=self.expected_jitter_data,
                tolerance_percent=self.tolerance_percent, jitter=True)
            fun_test.simple_assert(expression=jitter_result, message=checkpoint)

            checkpoint = "Ensure no errors are seen for port %s" % self.analyzer_port_obj_dict[self.port].spirent_handle
            analyzer_rx_results = template_obj.stc_manager.get_rx_port_analyzer_results(
                port_handle=self.port, subscribe_handle=self.subscribe_results['analyzer_subscribe'])
            result = template_obj.check_non_zero_error_count(rx_results=analyzer_rx_results)
            fun_test.test_assert(expression=result['result'], message=checkpoint)

            checkpoint = "Deactivate %s frame size streams for all ports" % frame_size
            result = template_obj.deactivate_stream_blocks(stream_obj_list=[stream_obj])
            fun_test.simple_assert(expression=result, message=checkpoint)

            jitter_results[key] = {'pps_count': rate_result['pps_count'][key],
                                   'jitter_count': jitter_result[key]}

            checkpoint = "Performance for %s frame size with %s load" % (frame_size, str(load))
            message = "---------------------------------> End %s  <---------------------------------" % checkpoint
            fun_test.log(message)
            fun_test.add_checkpoint(message)

        checkpoint = "Display Jitter Performance Counters"
        template_obj.display_jitter_counters(result=jitter_results)
        fun_test.add_checkpoint(checkpoint)

    def cleanup(self):
        pass


if __name__ == "__main__":
    ts = NuTransitPerformance()
    ts.add_test_case(NuTransitLatencyTest())
    ts.add_test_case(NuTransitJitterTest())
    ts.run()













