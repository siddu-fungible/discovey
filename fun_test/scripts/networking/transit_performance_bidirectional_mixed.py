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
    PERFORMANCE_DATA_FILE_NAME = "transit_performance.json"

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

        template_obj = SpirentEthernetTrafficTemplate(session_name="performance_bidirectional")
        result = template_obj.setup(no_of_ports_needed=self.NO_OF_PORTS)
        fun_test.test_assert(result['result'], "Ensure Setup is done")

        source_mac = template_obj.stc_manager.dut_config['source_mac1']
        destination_mac = template_obj.stc_manager.dut_config['destination_mac1']
        source_ip1 = template_obj.stc_manager.dut_config['source_ip1']
        destination_ip1 = template_obj.stc_manager.dut_config['destination_ip1']
        gateway = template_obj.stc_manager.dut_config['gateway1']
        destination_ip2 = template_obj.stc_manager.dut_config['destination_ip2']
        source_ip2 = "192.85.1.2"
        ether_type = Ethernet2Header.INTERNET_IP_ETHERTYPE

        checkpoint = "Change MTU for interface %s to %d" % (str(result['interface_obj_list'][0]), self.MTU)
        for interface_obj in result['interface_obj_list']:
            interface_obj.Mtu = self.MTU
            mtu_update_result = template_obj.configure_physical_interface(interface_obj=interface_obj)
            fun_test.simple_assert(mtu_update_result, checkpoint)
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Read Performance expected data for fixed size scenario"
        file_path = fun_test.get_script_parent_directory() + "/" + self.PERFORMANCE_DATA_FILE_NAME
        performance_data = template_obj.read_json_file_contents(file_path=file_path)
        fun_test.simple_assert(expression=performance_data, message=checkpoint)

        frame_load_dict = performance_data['mixed_size']['frames']

        # Create stream block objects for each port
        for port in result['port_list']:
            stream_objs = []
            for key in frame_load_dict:
                stream_objs.append(StreamBlock(fill_type=StreamBlock.FILL_TYPE_PRBS,
                                               insert_signature=True,
                                               fixed_frame_length=frame_load_dict[key][0],
                                               load=frame_load_dict[key][1],
                                               load_unit=StreamBlock.LOAD_UNIT_MEGABITS_PER_SECOND))
            stream_port_obj_dict[port] = stream_objs

        # Create Streams under each port
        for port in stream_port_obj_dict:
            stream_objects = stream_port_obj_dict[port]

            for stream_obj in stream_objects:
                checkpoint = "Create a raw stream with %d frame size under %s" % (stream_obj.FixedFrameLength,
                                                                                  port)
                result = template_obj.configure_stream_block(stream_block_obj=stream_obj,
                                                             port_handle=port)
                fun_test.test_assert(expression=result, message=checkpoint)

                checkpoint = "Configure Mac address for %s " % stream_obj.spirent_handle
                result = template_obj.stc_manager.configure_mac_address(streamblock=stream_obj.spirent_handle,
                                                                        source_mac=source_mac,
                                                                        destination_mac=destination_mac,
                                                                        ethernet_type=ether_type)
                fun_test.simple_assert(expression=result, message=checkpoint)

                if 'port2' in port:
                    source_ip = source_ip2
                    destination_ip = destination_ip2
                else:
                    source_ip = source_ip1
                    destination_ip = destination_ip1

                checkpoint = "Configure IP address for %s " % stream_obj.spirent_handle
                result = template_obj.stc_manager.configure_ip_address(streamblock=stream_obj.spirent_handle,
                                                                       source=source_ip,
                                                                       destination=destination_ip,
                                                                       gateway=gateway)
                fun_test.simple_assert(expression=result, message=checkpoint)

            checkpoint = "Deactivate All Streams under %s" % port
            result = template_obj.deactivate_stream_blocks(stream_obj_list=stream_objects)
            fun_test.test_assert(result, checkpoint)

    def cleanup(self):
        template_obj.cleanup()
        template_obj.populate_performance_counters_json(test_name="NU Transit Performance Bidirectional Mixed Frames",
                                                        latency_results=latency_results,
                                                        jitter_results=jitter_results,
                                                        file_name="nu_transit_performance_bidirectional_mixed_size")


class NuTransitLatencyTest(FunTestCase):
    generator_port_obj_dict = {}
    analyzer_port_obj_dict = {}
    subscribe_results = {}
    expected_latency_data = {}
    tolerance_percent = None
    ports = []
    traffic_duration = None

    def describe(self):
        self.set_test_details(id=1,
                              summary="NU Transit Performance Bidirectional Latency Test (Mixed Size Frames)",
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
        self.ports = template_obj.stc_manager.get_port_list()
        fun_test.test_assert(self.ports, "Get Port handle")
        self.traffic_duration = performance_data['mixed_size']['traffic_duration']

        port1_generator_config = GeneratorConfig(scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED,
                                                 duration=self.traffic_duration,
                                                 duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                 time_stamp_latch_mode=GeneratorConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)

        port1_analyzer_config = AnalyzerConfig(timestamp_latch_mode=AnalyzerConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)

        port2_generator_config = GeneratorConfig(scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED,
                                                 duration=self.traffic_duration,
                                                 duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                 time_stamp_latch_mode=GeneratorConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)

        port2_analyzer_config = AnalyzerConfig(timestamp_latch_mode=AnalyzerConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)

        self.generator_port_obj_dict[self.ports[0]] = port1_generator_config
        self.generator_port_obj_dict[self.ports[1]] = port2_generator_config

        self.analyzer_port_obj_dict[self.ports[0]] = port1_analyzer_config
        self.analyzer_port_obj_dict[self.ports[1]] = port2_analyzer_config

        for port in self.ports:
            checkpoint = "Create Generator Config for %s port" % port
            result = template_obj.configure_generator_config(port_handle=port,
                                                             generator_config_obj=self.generator_port_obj_dict[port])
            fun_test.simple_assert(expression=result, message=checkpoint)

            checkpoint = "Create Analyzer Config for %s port" % port
            result = template_obj.configure_analyzer_config(port_handle=port,
                                                            analyzer_config_obj=self.analyzer_port_obj_dict[port])
            fun_test.simple_assert(result, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribe_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(expression=self.subscribe_results['result'], message=checkpoint)

        self.expected_latency_data = performance_data['mixed_size']['latency']
        self.tolerance_percent = performance_data['mixed_size']['tolerance_percent']

    def run(self):
        port1 = self.ports[0]
        port2 = self.ports[1]
        global latency_results
        latency_results = OrderedDict()

        port1_stream_objs = stream_port_obj_dict[port1]
        port2_stream_objs = stream_port_obj_dict[port2]
        all_stream_objects = zip(port1_stream_objs, port2_stream_objs)
        frame_sizes = []
        loads = []
        for stream_obj in port1_stream_objs:
            frame_sizes.append(str(stream_obj.FixedFrameLength))
            loads.append(str(stream_obj.Load))

        checkpoint = "Performance for %s frame size with %s load" % (frame_sizes, str(loads))
        message = "---------------------------------> Start %s  <---------------------------------" % checkpoint
        fun_test.log(message)
        fun_test.add_checkpoint(message)

        checkpoint = "Activate %s frame size streams for all ports" % frame_sizes
        result = template_obj.activate_stream_blocks(stream_obj_list=port1_stream_objs)
        fun_test.simple_assert(result, checkpoint)
        result = template_obj.activate_stream_blocks(stream_obj_list=port2_stream_objs)
        fun_test.simple_assert(result, checkpoint)

        checkpoint = "Enable Generator Config and start traffic for %d secs for all ports" % self.traffic_duration
        result = template_obj.enable_generator_configs(generator_configs=[
            self.generator_port_obj_dict[port1].spirent_handle, self.generator_port_obj_dict[port2].spirent_handle])
        fun_test.simple_assert(expression=result, message=checkpoint)

        fun_test.sleep("Waiting for traffic to reach full throughput", seconds=5)
        for stream_objs in all_stream_objects:
            frame_size = str(stream_objs[0].FixedFrameLength)
            load = str(stream_objs[0].Load)
            checkpoint = "Validate Traffic Rates for %s frame size with %s load" % (frame_size, load)
            message = "--------------------------------->  %s  <---------------------------------" % checkpoint
            fun_test.log(message)
            fun_test.add_checkpoint(message)

            checkpoint = "Validate Tx and Rx Rate under %s streams " % port1
            rate_result = template_obj.validate_traffic_rate_results(
                rx_summary_subscribe_handle=self.subscribe_results['rx_summary_subscribe'],
                tx_summary_subscribe_handle=self.subscribe_results['tx_stream_subscribe'],
                stream_objects=stream_objs, wait_before_fetching_results=False)
            fun_test.simple_assert(expression=rate_result['result'], message=checkpoint)
            key = "frame_%s" % frame_size
            latency_results[key] = {'pps_count': rate_result['pps_count'][key],
                                    'throughput_count': rate_result['throughput_count'][key]}
        fun_test.sleep("Waiting for traffic to complete", seconds=self.traffic_duration)

        for stream_objs in all_stream_objects:
            frame_size = str(stream_objs[0].FixedFrameLength)
            load = str(stream_objs[0].Load)
            checkpoint = "Validate Latency Counters for %s frame size with %s load" % (frame_size, load)
            message = "--------------------------------->  %s  <---------------------------------" % checkpoint
            fun_test.log(message)
            fun_test.add_checkpoint(message)

            checkpoint = "Validate Latency Results under %s streams" % port1
            latency_result = template_obj.validate_performance_result(
                tx_subscribe_handle=self.subscribe_results['tx_subscribe'],
                rx_subscribe_handle=self.subscribe_results['rx_summary_subscribe'],
                stream_objects=stream_objs, expected_latency_count=self.expected_latency_data,
                tolerance_percent=self.tolerance_percent)
            fun_test.simple_assert(expression=latency_result['result'], message=checkpoint)
            '''
            checkpoint = "Validate Latency Results under %s streams" % port2
            port2_latency_result = template_obj.validate_performance_result(
                tx_subscribe_handle=self.subscribe_results['tx_subscribe'],
                rx_subscribe_handle=self.subscribe_results['rx_summary_subscribe'],
                stream_objects=port2_stream_objs, expected_latency_count=self.expected_latency_data,
                tolerance_percent=self.tolerance_percent)
            fun_test.simple_assert(expression=port2_latency_result['result'], message=checkpoint)
            '''
            key = "frame_%s" % stream_objs[0].FixedFrameLength
            latency_results[key].update(latency_count=latency_result[key])

        checkpoint = "Ensure no errors are seen for port %s" % self.analyzer_port_obj_dict[port1].spirent_handle
        analyzer_rx_results = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port1, subscribe_handle=self.subscribe_results['analyzer_subscribe'])
        result = template_obj.check_non_zero_error_count(rx_results=analyzer_rx_results)
        fun_test.test_assert(expression=result['result'], message=checkpoint)

        checkpoint = "Ensure no errors are seen for port %s" % self.analyzer_port_obj_dict[port2].spirent_handle
        analyzer_rx_results = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port2, subscribe_handle=self.subscribe_results['analyzer_subscribe'])
        result = template_obj.check_non_zero_error_count(rx_results=analyzer_rx_results)
        fun_test.test_assert(expression=result['result'], message=checkpoint)

        checkpoint = "Performance for %s frame size with %s load" % (frame_sizes, loads)
        message = "---------------------------------> End %s  <---------------------------------" % checkpoint
        fun_test.log(message)
        fun_test.add_checkpoint(message)

        checkpoint = "Display Latency Performance Counters"
        template_obj.display_latency_counters(latency_results)
        fun_test.add_checkpoint(checkpoint)

    def cleanup(self):
        for port in self.ports:
            template_obj.deactivate_stream_blocks(stream_obj_list=stream_port_obj_dict[port])


class NuTransitJitterTest(FunTestCase):
    generator_port_obj_dict = {}
    analyzer_port_obj_dict = {}
    subscribe_results = {}
    expected_jitter_data = {}
    tolerance_percent = None
    ports = []
    traffic_duration = None
    view_attribute_list = ["AvgJitter", "MinJitter", "MaxJitter", "FrameRate", "FrameCount"]

    def describe(self):
        self.set_test_details(id=2,
                              summary="NU Transit Performance Bidirectional Jitter Test (Mixed Size Frames)",
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
        self.ports = template_obj.stc_manager.get_port_list()
        fun_test.test_assert(self.ports, "Get Port handle")
        self.traffic_duration = performance_data['mixed_size']['traffic_duration']
        self.expected_jitter_data = performance_data['mixed_size']['jitter']
        self.tolerance_percent = performance_data['mixed_size']['tolerance_percent']

        port1_generator_config = GeneratorConfig(scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED,
                                                 duration=self.traffic_duration,
                                                 duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                 time_stamp_latch_mode=GeneratorConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)

        port1_analyzer_config = AnalyzerConfig(timestamp_latch_mode=AnalyzerConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)

        port2_generator_config = GeneratorConfig(scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED,
                                                 duration=self.traffic_duration,
                                                 duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                 time_stamp_latch_mode=GeneratorConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)

        port2_analyzer_config = AnalyzerConfig(timestamp_latch_mode=AnalyzerConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)

        self.generator_port_obj_dict[self.ports[0]] = port1_generator_config
        self.generator_port_obj_dict[self.ports[1]] = port2_generator_config

        self.analyzer_port_obj_dict[self.ports[0]] = port1_analyzer_config
        self.analyzer_port_obj_dict[self.ports[1]] = port2_analyzer_config

        for port in self.ports:
            checkpoint = "Create Generator Config for %s port" % port
            result = template_obj.configure_generator_config(port_handle=port,
                                                             generator_config_obj=self.generator_port_obj_dict[port])
            fun_test.test_assert(expression=result, message=checkpoint)

            checkpoint = "Create Analyzer Config for %s port" % port
            result = template_obj.configure_analyzer_config(port_handle=port,
                                                            analyzer_config_obj=self.analyzer_port_obj_dict[port])
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
                                                                 change_mode=True,
                                                                 view_attribute_list=self.view_attribute_list)
        fun_test.test_assert(rx_summary_subscribe, checkpoint)

        checkpoint = "Subscribe to Analyzer Results"
        analyzer_subscribe = template_obj.subscribe_analyzer_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(analyzer_subscribe, checkpoint)

        self.subscribe_results = {"tx_subscribe": tx_subscribe, "tx_stream_subscribe": tx_stream_subscribe,
                                  "rx_summary_subscribe": rx_summary_subscribe,
                                  "analyzer_subscribe": analyzer_subscribe}

    def run(self):
        global jitter_results
        jitter_results = OrderedDict()
        port1 = self.ports[0]
        port2 = self.ports[1]
        template_obj.clear_subscribed_results(subscribe_handle_list=self.subscribe_results.values())

        port1_stream_objs = stream_port_obj_dict[port1]
        port2_stream_objs = stream_port_obj_dict[port2]
        all_stream_objects = zip(port1_stream_objs, port2_stream_objs)

        frame_sizes = []
        loads = []
        for stream_obj in port1_stream_objs:
            frame_sizes.append(str(stream_obj.FixedFrameLength))
            loads.append(str(stream_obj.Load))

        checkpoint = "Performance for %s frame size with %s load" % (frame_sizes, loads)
        message = "---------------------------------> Start %s  <---------------------------------" % checkpoint
        fun_test.log(message)
        fun_test.add_checkpoint(message)

        checkpoint = "Activate %s frame size streams for all ports" % frame_sizes
        result = template_obj.activate_stream_blocks(stream_obj_list=port1_stream_objs)
        fun_test.simple_assert(result, checkpoint)
        result = template_obj.activate_stream_blocks(stream_obj_list=port2_stream_objs)
        fun_test.simple_assert(result, checkpoint)

        checkpoint = "Enable Generator Config and start traffic for %d secs for all ports" % self.traffic_duration
        result = template_obj.enable_generator_configs(generator_configs=[
            self.generator_port_obj_dict[port1].spirent_handle, self.generator_port_obj_dict[port2].spirent_handle])
        fun_test.simple_assert(expression=result, message=checkpoint)

        fun_test.sleep("Waiting for traffic to reach full throughput", seconds=5)
        for stream_objs in all_stream_objects:
            frame_size = str(stream_objs[0].FixedFrameLength)
            load = str(stream_objs[0].Load)
            key = "frame_%s" % frame_size
            checkpoint = "Validate Traffic Rates for %s frame size with %s load" % (frame_size, load)
            message = "--------------------------------->  %s  <---------------------------------" % checkpoint
            fun_test.log(message)
            fun_test.add_checkpoint(message)

            checkpoint = "Validate Tx and Rx Rate"
            rate_result = template_obj.validate_traffic_rate_results(
                rx_summary_subscribe_handle=self.subscribe_results['rx_summary_subscribe'],
                tx_summary_subscribe_handle=self.subscribe_results['tx_stream_subscribe'],
                stream_objects=stream_objs, wait_before_fetching_results=False, validate_throughput=False)
            fun_test.simple_assert(expression=rate_result['result'], message=checkpoint)
            jitter_results[key] = {'pps_count': rate_result['pps_count'][key]}

        fun_test.sleep("Waiting for traffic to complete", seconds=self.traffic_duration)

        for stream_objs in all_stream_objects:
            frame_size = str(stream_objs[0].FixedFrameLength)
            load = str(stream_objs[0].Load)
            key = "frame_%s" % frame_size
            checkpoint = "Validate Jitter Counters for %s frame size with %s load" % (frame_size, load)
            message = "--------------------------------->  %s  <---------------------------------" % checkpoint
            fun_test.log(message)
            fun_test.add_checkpoint(message)

            checkpoint = "Validate Jitter Results"
            jitter_result = template_obj.validate_performance_result(
                tx_subscribe_handle=self.subscribe_results['tx_subscribe'],
                rx_subscribe_handle=self.subscribe_results['rx_summary_subscribe'],
                stream_objects=stream_objs, expected_jitter_count=self.expected_jitter_data,
                tolerance_percent=self.tolerance_percent, jitter=True)
            fun_test.simple_assert(expression=jitter_result['result'], message=checkpoint)
            jitter_results[key].update(jitter_count=jitter_result[key])

        checkpoint = "Ensure no errors are seen for port %s" % self.analyzer_port_obj_dict[port1].spirent_handle
        analyzer_rx_results = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port1, subscribe_handle=self.subscribe_results['analyzer_subscribe'])
        result = template_obj.check_non_zero_error_count(rx_results=analyzer_rx_results)
        fun_test.test_assert(expression=result['result'], message=checkpoint)

        checkpoint = "Ensure no errors are seen for port %s" % self.analyzer_port_obj_dict[port2].spirent_handle
        analyzer_rx_results = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port2, subscribe_handle=self.subscribe_results['analyzer_subscribe'])
        result = template_obj.check_non_zero_error_count(rx_results=analyzer_rx_results)
        fun_test.test_assert(expression=result['result'], message=checkpoint)

        checkpoint = "Performance for %s frame size with %s load" % (frame_sizes, loads)
        message = "---------------------------------> End %s  <---------------------------------" % checkpoint
        fun_test.log(message)
        fun_test.add_checkpoint(message)

        checkpoint = "Display Jitter Performance Counters"
        template_obj.display_jitter_counters(jitter_results)
        fun_test.add_checkpoint(checkpoint)

    def cleanup(self):
        pass


if __name__ == "__main__":
    ts = NuTransitPerformance()
    ts.add_test_case(NuTransitLatencyTest())
    ts.add_test_case(NuTransitJitterTest())
    ts.run()













