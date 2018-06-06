"""
Results Header Dict
{ "frame_size": {"is_input": true, "description": "Fixed Frame Size Test"},
  "test_type": {"is_input": false, "description": "Unidirectional Test"},
  "throughput": {"is_input": true, "description": "Throughput in Mbps"},
  "latency": {"is_input": false, "description": "Latency in us"},
  "jitter": {"is_input": false, "description": "Jitter in us"},
  "pps": {"is_input": false, "description": "Packets per secs"},
  "version": {"is_input": false, "description": "DUT version or FunOS version"}
  "mode": {"is_input": false, "description": "Port modes (25, 50 or 100 G)"},
  "timestamp": {"is_input": false, "description": "Date time of result data"}
}
"""

from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, Ethernet2Header, GeneratorConfig, AnalyzerConfig
from collections import OrderedDict
from lib.host.network_controller import NetworkController
from helper import *

stream_port_obj_dict = OrderedDict()
performance_data = OrderedDict()
latency_results = None
jitter_results = None
DUT_PORTS = []


class NuTransitPerformance(FunTestScript):
    MTU = 16380
    NO_OF_PORTS = 2
    EXPECTED_PERFORMANCE_DATA_FILE_NAME = "nu_transit_performance_data.json"
    TRANSIT_PERFORMANCE_INPUTS_FILE_NAME = "transit_performance_inputs.json"
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
        global performance_inputs
        global DUT_PORTS
        global network_controller_obj

        template_obj = SpirentEthernetTrafficTemplate(session_name="performance_Unidirectional")
        result = template_obj.setup(no_of_ports_needed=self.NO_OF_PORTS)
        fun_test.test_assert(result['result'], "Ensure Setup is done")
        self.port1 = result['port_list'][0]

        source_mac = template_obj.stc_manager.dut_config['source_mac1']
        destination_mac = template_obj.stc_manager.dut_config['destination_mac1']
        source_ip1 = template_obj.stc_manager.dut_config['source_ip1']
        destination_ip1 = template_obj.stc_manager.dut_config['destination_ip1']
        gateway = template_obj.stc_manager.dut_config['gateway1']
        DUT_PORTS = template_obj.stc_manager.dut_config['port_nos']
        ether_type = Ethernet2Header.INTERNET_IP_ETHERTYPE
        dpc_server_ip = template_obj.stc_manager.dpcsh_server_config['dpcsh_server_ip']
        dpc_server_port = int(template_obj.stc_manager.dpcsh_server_config['dpcsh_server_port'])

        checkpoint = "Change MTU for interface %s to %d" % (str(result['interface_obj_list'][0]), self.MTU)
        for interface_obj in result['interface_obj_list']:
            interface_obj.Mtu = self.MTU
            mtu_update_result = template_obj.configure_physical_interface(interface_obj=interface_obj)
            fun_test.simple_assert(mtu_update_result, checkpoint)
        fun_test.add_checkpoint(checkpoint)

        network_controller_obj = NetworkController(dpc_server_ip=dpc_server_ip, dpc_server_port=dpc_server_port)

        checkpoint = "Change DUT ports MTU to %d" % self.MTU
        for port_num in DUT_PORTS:
            mtu_changed = network_controller_obj.set_port_mtu(port_num=port_num, mtu_value=self.MTU)
            fun_test.simple_assert(mtu_changed, "Change MTU on DUT port %d to %d" % (port_num, self.MTU))
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Read Performance expected data for fixed size scenario"
        file_path = fun_test.get_script_parent_directory() + "/" + self.EXPECTED_PERFORMANCE_DATA_FILE_NAME
        performance_data = template_obj.read_json_file_contents(file_path=file_path)
        fun_test.simple_assert(expression=performance_data, message=checkpoint)
        checkpoint = "Read Performance input data for fixed size scenario"
        file_path = fun_test.get_script_parent_directory() + "/" + self.TRANSIT_PERFORMANCE_INPUTS_FILE_NAME
        performance_inputs = template_obj.read_json_file_contents(file_path=file_path)
        fun_test.simple_assert(expression=performance_inputs, message=checkpoint)

        frame_load_dict = performance_inputs['fixed_size']['frames']

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
        template_obj.cleanup()
        mode = template_obj.stc_manager.dut_config['mode']
        output_file_path = fun_test.get_script_parent_directory() + "/nu_transit_performance_data.json"
        template_obj.populate_performance_counters_json(mode=mode,
                                                        latency_results=latency_results,
                                                        jitter_results=jitter_results,
                                                        file_name=output_file_path)


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
        self.traffic_duration = performance_inputs['fixed_size']['traffic_duration']

        port1_generator_config = GeneratorConfig(scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED,
                                                 duration=self.traffic_duration,
                                                 duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                 time_stamp_latch_mode=GeneratorConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)

        port1_analyzer_config = AnalyzerConfig(timestamp_latch_mode=AnalyzerConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)

        port2_analyzer_config = AnalyzerConfig(timestamp_latch_mode=AnalyzerConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)

        checkpoint = "Create Generator Config for %s port" % self.port
        result = template_obj.configure_generator_config(port_handle=self.port,
                                                         generator_config_obj=port1_generator_config)
        fun_test.simple_assert(expression=result, message=checkpoint)
        self.generator_port_obj_dict[self.port] = template_obj.stc_manager.get_generator(port_handle=self.port)

        checkpoint = "Create Analyzer Config for %s port" % self.port
        result = template_obj.configure_analyzer_config(port_handle=self.port,
                                                        analyzer_config_obj=port1_analyzer_config)
        fun_test.simple_assert(result, checkpoint)

        checkpoint = "Create Analyzer Config for %s port" % ports[1]
        result = template_obj.configure_analyzer_config(port_handle=ports[1],
                                                        analyzer_config_obj=port2_analyzer_config)
        fun_test.simple_assert(result, checkpoint)
        self.analyzer_port_obj_dict[self.port] = template_obj.stc_manager.get_analyzer(port_handle=self.port)
        self.analyzer_port_obj_dict[ports[1]] = template_obj.stc_manager.get_analyzer(port_handle=ports[1])

        checkpoint = "Subscribe to all results"
        self.subscribe_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(expression=self.subscribe_results['result'], message=checkpoint)

        self.expected_latency_data = performance_data
        self.tolerance_percent = performance_inputs['fixed_size']['tolerance_percent']

        checkpoint = "Clear FPG port stats on DUT"
        for port_num in DUT_PORTS:
            result = network_controller_obj.clear_port_stats(port_num=port_num)
            fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
        fun_test.add_checkpoint(checkpoint=checkpoint)

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
                self.generator_port_obj_dict[port1]])
            fun_test.simple_assert(expression=result, message=checkpoint)

            checkpoint = "Validate Tx and Rx Rate"
            rate_result = template_obj.validate_traffic_rate_results(
                rx_summary_subscribe_handle=self.subscribe_results['rx_summary_subscribe'],
                tx_summary_subscribe_handle=self.subscribe_results['tx_stream_subscribe'],
                stream_objects=[stream_obj])
            fun_test.simple_assert(expression=rate_result['result'], message=checkpoint)
            fun_test.sleep("Waiting for traffic to complete", seconds=self.traffic_duration)

            checkpoint = "Validate FPG FrameCount Tx == Rx for port direction %d --> %d on DUT" % (DUT_PORTS[0],
                                                                                                   DUT_PORTS[1])
            port1_result = network_controller_obj.peek_fpg_port_stats(port_num=DUT_PORTS[0])
            fun_test.test_assert(port1_result, "Get %d Port FPG Stats" % DUT_PORTS[0])
            port2_result = network_controller_obj.peek_fpg_port_stats(port_num=DUT_PORTS[1])
            fun_test.test_assert(port2_result, "Get %d Port FPG Stats" % DUT_PORTS[1])

            frames_transmitted = get_dut_output_stats_value(result_stats=port1_result, stat_type=FRAMES_TRANSMITTED_OK)
            frames_received = get_dut_output_stats_value(result_stats=port2_result, stat_type=FRAMES_RECEIVED_OK)

            fun_test.test_assert_expected(expected=frames_transmitted, actual=frames_received,
                                          message=checkpoint)

            # Ensure NO error are seen on DUT port 1

            if_in_err_count = get_dut_output_stats_value(result_stats=port1_result, stat_type=IF_IN_ERRORS)
            fun_test.test_assert_expected(expected=None, actual=if_in_err_count,
                                          message="Ensure no IN error count on DUT port %d" % DUT_PORTS[0])
            if_out_err_count = get_dut_output_stats_value(result_stats=port1_result, stat_type=IF_OUT_ERRORS)
            fun_test.test_assert_expected(expected=None, actual=if_out_err_count,
                                          message="Ensure no OUT error count on DUT port %d" % DUT_PORTS[0])
            fcs_err_count = get_dut_output_stats_value(result_stats=port1_result, stat_type=FRAME_CHECK_SEQUENCE_ERROR)
            fun_test.test_assert_expected(expected=None, actual=fcs_err_count,
                                          message="Ensure no FCS errors seen on DUT port %d" % DUT_PORTS[0])

            # Ensure NO error are seen on DUT port 2

            if_in_err_count = get_dut_output_stats_value(result_stats=port2_result, stat_type=IF_IN_ERRORS)
            fun_test.test_assert_expected(expected=None, actual=if_in_err_count,
                                          message="Ensure no IN error count on DUT port %d" % DUT_PORTS[1])
            if_out_err_count = get_dut_output_stats_value(result_stats=port2_result, stat_type=IF_OUT_ERRORS)
            fun_test.test_assert_expected(expected=None, actual=if_out_err_count,
                                          message="Ensure no OUT error count on DUT port %d" % DUT_PORTS[1])
            fcs_err_count = get_dut_output_stats_value(result_stats=port2_result, stat_type=FRAME_CHECK_SEQUENCE_ERROR)
            fun_test.test_assert_expected(expected=None, actual=fcs_err_count,
                                          message="Ensure no FCS errors seen on DUT port %d" % DUT_PORTS[1])

            checkpoint = "Validate Latency Results"
            latency_result = template_obj.validate_performance_result(
                tx_subscribe_handle=self.subscribe_results['tx_subscribe'],
                rx_subscribe_handle=self.subscribe_results['rx_summary_subscribe'],
                stream_objects=[stream_obj], expected_performance_data=self.expected_latency_data,
                tolerance_percent=self.tolerance_percent)
            fun_test.simple_assert(expression=latency_result['result'], message=checkpoint)

            checkpoint = "Ensure no errors are seen for port %s" % \
                         self.analyzer_port_obj_dict[port1]
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
        self.traffic_duration = performance_inputs['fixed_size']['traffic_duration']
        self.expected_jitter_data = performance_data
        self.tolerance_percent = performance_inputs['fixed_size']['tolerance_percent']

        port1_generator_config = GeneratorConfig(scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED,
                                                 duration=self.traffic_duration,
                                                 duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                 time_stamp_latch_mode=GeneratorConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)

        port1_analyzer_config = AnalyzerConfig(timestamp_latch_mode=AnalyzerConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)

        port2_analyzer_config = AnalyzerConfig(timestamp_latch_mode=AnalyzerConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)

        checkpoint = "Create Generator Config for %s port" % self.port
        result = template_obj.configure_generator_config(port_handle=self.port,
                                                         generator_config_obj=port1_generator_config)
        fun_test.test_assert(expression=result, message=checkpoint)
        self.generator_port_obj_dict[self.port] = template_obj.stc_manager.get_generator(port_handle=self.port)

        checkpoint = "Create Analyzer Config for %s port" % self.port
        result = template_obj.configure_analyzer_config(port_handle=self.port,
                                                        analyzer_config_obj=port1_analyzer_config)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Create Analyzer Config for %s port" % ports[1]
        result = template_obj.configure_analyzer_config(port_handle=ports[1],
                                                        analyzer_config_obj=port2_analyzer_config)
        fun_test.test_assert(result, checkpoint)
        self.analyzer_port_obj_dict[self.port] = template_obj.stc_manager.get_analyzer(port_handle=self.port)
        self.analyzer_port_obj_dict[ports[1]] = template_obj.stc_manager.get_analyzer(port_handle=ports[1])

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
                self.generator_port_obj_dict[self.port]])
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
                stream_objects=stream_objs, expected_performance_data=self.expected_jitter_data,
                tolerance_percent=self.tolerance_percent, jitter=True)
            fun_test.simple_assert(expression=jitter_result, message=checkpoint)

            checkpoint = "Ensure no errors are seen for port %s" % self.analyzer_port_obj_dict[self.port]
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













