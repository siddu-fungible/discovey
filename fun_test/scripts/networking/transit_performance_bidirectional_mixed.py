from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, Ethernet2Header, GeneratorConfig, AnalyzerConfig
from collections import OrderedDict
from lib.host.network_controller import NetworkController
from helper import *
from nu_config_manager import *

stream_port_obj_dict = OrderedDict()
performance_data = OrderedDict()
generator_port_obj_dict = {}
analyzer_port_obj_dict = {}
spirent_config = None
dut_config = None
latency_results = None
jitter_results = None
NU_CONFIG_SPEC = fun_test.get_script_parent_directory() + "/networking" + "/nu_configs.json"
TOLERANCE_PERCENT = 10
TRAFFIC_DURATION = 90
IPV4_FRAMES = [64, 200, 1500]
IPV6_FRAMES = [78, 200, 3000]
LOAD = 15
chassis_type = None


class NuTransitPerformance(FunTestScript):
    MTU = 16380
    NO_OF_PORTS = 2
    PERFORMANCE_DATA_FILE_NAME = "nu_transit_performance_data.json"

    def describe(self):
        self.set_test_details(steps="""
        1. Check the health of Spirent Test Center 
        2. Create %d port and ensure ports are online
        3. Change interface MTU to %d on all ports and also change on DUT if applicable
        4. Configure Generator and Analyzer configs for each port as follows
            a. Set Duration %d secs 
            b. Scheduling mode to Rate based
            c. Timestamp reference location to END_OF_FRAME
        """ % (self.NO_OF_PORTS, self.MTU, TRAFFIC_DURATION))

    def setup(self):
        global template_obj
        global performance_data
        global network_controller_obj
        global spirent_config
        global dut_config
        global generator_port_obj_dict
        global analyzer_port_obj_dict
        global chassis_type

        spirent_config = nu_config_obj.read_traffic_generator_config()
        dut_type = fun_test.get_local_setting(setting="dut_type")
        dut_config = nu_config_obj.read_dut_config(dut_type=dut_type)
        chassis_type = fun_test.get_local_setting(setting="chassis_type")

        template_obj = SpirentEthernetTrafficTemplate(session_name="performance_bidirectional",
                                                      chassis_type=chassis_type, spirent_config=spirent_config)
        result = template_obj.setup(no_of_ports_needed=self.NO_OF_PORTS)
        fun_test.test_assert(result['result'], "Ensure Setup is done")

        dpc_server_ip = dut_config["dpcsh_tcp_proxy_ip"]
        dpc_server_port = dut_config["dpcsh_tcp_proxy_port"]

        checkpoint = "Change ports MTU to %d" % self.MTU
        mtu_changed_on_spirent = template_obj.change_ports_mtu(interface_obj_list=result["interface_obj_list"],
                                                               mtu_value=self.MTU)
        fun_test.test_assert(mtu_changed_on_spirent, checkpoint)

        if chassis_type == NuConfigManager.CHASSIS_TYPE_PHYSICAL:
            network_controller_obj = NetworkController(dpc_server_ip=dpc_server_ip, dpc_server_port=dpc_server_port)

            checkpoint = "Change DUT ports MTU to %d" % self.MTU
            for port_num in dut_config['ports']:
                mtu_changed = network_controller_obj.set_port_mtu(port_num=port_num, mtu_value=self.MTU)
                fun_test.simple_assert(mtu_changed, "Change MTU on DUT port %d to %d" % (port_num, self.MTU))
            fun_test.add_checkpoint(checkpoint)

        checkpoint = "Read Performance expected data for fixed size scenario"
        file_path = LOGS_DIR + "/" + self.PERFORMANCE_DATA_FILE_NAME
        performance_data = template_obj.read_json_file_contents(file_path=file_path)
        fun_test.simple_assert(expression=performance_data, message=checkpoint)

        port1_generator_config = GeneratorConfig(scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED,
                                                 duration=TRAFFIC_DURATION,
                                                 duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                 time_stamp_latch_mode=GeneratorConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)

        port1_analyzer_config = AnalyzerConfig(timestamp_latch_mode=AnalyzerConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)

        for port in result['port_list']:
            checkpoint = "Create Generator Config for %s port" % port
            result = template_obj.configure_generator_config(port_handle=port,
                                                             generator_config_obj=port1_generator_config)
            fun_test.simple_assert(expression=result, message=checkpoint)

            checkpoint = "Create Analyzer Config for %s port" % port
            result = template_obj.configure_analyzer_config(port_handle=port,
                                                            analyzer_config_obj=port1_analyzer_config)
            fun_test.simple_assert(result, checkpoint)

            generator_port_obj_dict[port] = template_obj.stc_manager.get_generator(port_handle=port)
            analyzer_port_obj_dict[port] = template_obj.stc_manager.get_analyzer(port_handle=port)

    def cleanup(self):
        template_obj.cleanup()
        '''
        mode = template_obj.stc_manager.dut_config['mode']
        output_file_path = fun_test.get_script_parent_directory() + "/nu_transit_performance_data_bidirectional.json"
        template_obj.populate_performance_counters_json(mode=mode,
                                                        latency_results=latency_results,
                                                        jitter_results=jitter_results,
                                                        file_name=output_file_path)
        '''


class NuTransitLatencyIPv4Test(FunTestCase):
    subscribe_results = {}
    expected_latency_data = {}
    ports = []

    def describe(self):
        self.set_test_details(id=1,
                              summary="NU Transit Performance Bidirectional Latency Test (Mixed Size Frames IPv4)",
                              steps="""
                              1. Get port handles
                              2. Create stream block EthernetII and IPv4 Headers. Stream Config as follows
                                 a. Frames: %s
                                 b. Load: %d Mbps
                                 c. Fill TYpe PRBS
                                 d. Signature True
                              3. Activate stream on all ports and start traffic
                              4. Validate Tx and Rx rate for active streams under each port
                              5. Wait for traffic to complete
                              6. Validate Tx FrameCount and Rx FrameCount for active streams under each port
                              9. Ensure no errors are seen 
                              10. Validate latency numbers for each streams under each port
                              11. Deactivate current stream  
                              """ % (IPV4_FRAMES, LOAD))

    def setup(self):
        self.ports = template_obj.stc_manager.get_port_list()
        fun_test.simple_assert(self.ports, "Get Port handle")

        l3_config = spirent_config["l3_config"]["ipv4"]
        l2_config = spirent_config["l2_config"]
        ether_type = Ethernet2Header.INTERNET_IP_ETHERTYPE

        # Create stream block objects for each port
        for port in self.ports:
            stream_objs = []
            for frame_size in IPV4_FRAMES:
                stream_objs.append(StreamBlock(fill_type=StreamBlock.FILL_TYPE_PRBS,
                                               insert_signature=True,
                                               fixed_frame_length=frame_size,
                                               load=LOAD,
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
                                                                        source_mac=l2_config["source_mac"],
                                                                        destination_mac=l2_config["destination_mac"],
                                                                        ethernet_type=ether_type)
                fun_test.simple_assert(expression=result, message=checkpoint)

                if 'port2' in port:
                    source_ip = l3_config['source_ip2']
                    destination_ip = l3_config['destination_ip2']
                else:
                    source_ip = l3_config['source_ip1']
                    destination_ip = l3_config['destination_ip1']

                checkpoint = "Configure IP address for %s " % stream_obj.spirent_handle
                result = template_obj.stc_manager.configure_ip_address(streamblock=stream_obj.spirent_handle,
                                                                       source=source_ip,
                                                                       destination=destination_ip,
                                                                       gateway=l3_config['gateway'])
                fun_test.simple_assert(expression=result, message=checkpoint)

            checkpoint = "Deactivate All Streams under %s" % port
            result = template_obj.deactivate_stream_blocks(stream_obj_list=stream_objects)
            fun_test.test_assert(result, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribe_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(expression=self.subscribe_results['result'], message=checkpoint)

        self.expected_latency_data = performance_data

        if chassis_type == NuConfigManager.CHASSIS_TYPE_PHYSICAL:
            checkpoint = "Clear FPG port stats on DUT"
            for port_num in dut_config['ports']:
                result = network_controller_obj.clear_port_stats(port_num=port_num)
                fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
            fun_test.add_checkpoint(checkpoint=checkpoint)

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

        checkpoint = "Enable Generator Config and start traffic for %d secs for all ports" % TRAFFIC_DURATION
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[port1],
                                                                          generator_port_obj_dict[port2]])
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
        fun_test.sleep("Waiting for traffic to complete", seconds=TRAFFIC_DURATION)

        checkpoint = "Validate FPG FrameCount Tx == Rx for port direction %d --> %d on DUT" % (dut_config['ports'][0],
                                                                                               dut_config['ports'][1])
        port1_result = network_controller_obj.peek_fpg_port_stats(port_num=dut_config['ports'][0])
        fun_test.test_assert(port1_result, "Get %d Port FPG Stats" % dut_config['ports'][0])
        port2_result = network_controller_obj.peek_fpg_port_stats(port_num=dut_config['ports'][1])
        fun_test.test_assert(port2_result, "Get %d Port FPG Stats" % dut_config['ports'][1])

        frames_transmitted = get_dut_output_stats_value(result_stats=port1_result, stat_type=FRAMES_TRANSMITTED_OK)
        frames_received = get_dut_output_stats_value(result_stats=port2_result, stat_type=FRAMES_RECEIVED_OK)

        fun_test.test_assert_expected(expected=frames_transmitted, actual=frames_received,
                                      message=checkpoint)

        checkpoint = "Validate FPG FrameCount Tx == Rx for port direction %d --> %d on DUT" % (dut_config['ports'][1],
                                                                                               dut_config['ports'][0])
        frames_transmitted = get_dut_output_stats_value(result_stats=port2_result, stat_type=FRAMES_TRANSMITTED_OK)
        frames_received = get_dut_output_stats_value(result_stats=port1_result, stat_type=FRAMES_RECEIVED_OK)

        fun_test.test_assert_expected(expected=frames_transmitted, actual=frames_received,
                                      message=checkpoint)

        # Ensure NO error are seen on DUT port 1

        if_in_err_count = get_dut_output_stats_value(result_stats=port1_result, stat_type=IF_IN_ERRORS)
        fun_test.test_assert_expected(expected=None, actual=if_in_err_count,
                                      message="Ensure no IN error count on DUT port %d" % dut_config['ports'][0])
        if_out_err_count = get_dut_output_stats_value(result_stats=port1_result, stat_type=IF_OUT_ERRORS)
        fun_test.test_assert_expected(expected=None, actual=if_out_err_count,
                                      message="Ensure no OUT error count on DUT port %d" % dut_config['ports'][0])
        fcs_err_count = get_dut_output_stats_value(result_stats=port1_result, stat_type=FRAME_CHECK_SEQUENCE_ERROR)
        fun_test.test_assert_expected(expected=None, actual=fcs_err_count,
                                      message="Ensure no FCS errors seen on DUT port %d" % dut_config['ports'][0])

        # Ensure NO error are seen on DUT port 2

        if_in_err_count = get_dut_output_stats_value(result_stats=port2_result, stat_type=IF_IN_ERRORS)
        fun_test.test_assert_expected(expected=None, actual=if_in_err_count,
                                      message="Ensure no IN error count on DUT port %d" % dut_config['ports'][1])
        if_out_err_count = get_dut_output_stats_value(result_stats=port2_result, stat_type=IF_OUT_ERRORS)
        fun_test.test_assert_expected(expected=None, actual=if_out_err_count,
                                      message="Ensure no OUT error count on DUT port %d" % dut_config['ports'][1])
        fcs_err_count = get_dut_output_stats_value(result_stats=port2_result, stat_type=FRAME_CHECK_SEQUENCE_ERROR)
        fun_test.test_assert_expected(expected=None, actual=fcs_err_count,
                                      message="Ensure no FCS errors seen on DUT port %d" % dut_config['ports'][1])

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
                stream_objects=stream_objs, expected_performance_data=self.expected_latency_data,
                tolerance_percent=TOLERANCE_PERCENT)
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

        checkpoint = "Ensure no errors are seen for port %s" % analyzer_port_obj_dict[port1]
        analyzer_rx_results = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port1, subscribe_handle=self.subscribe_results['analyzer_subscribe'])
        result = template_obj.check_non_zero_error_count(rx_results=analyzer_rx_results)
        fun_test.test_assert(expression=result['result'], message=checkpoint)

        checkpoint = "Ensure no errors are seen for port %s" % analyzer_port_obj_dict[port2]
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
            template_obj.delete_streamblocks(stream_obj_list=stream_port_obj_dict[port])
        '''
        mode = dut_config['interface_mode']
        output_file_path = fun_test.get_script_parent_directory() + "/nu_transit_performance_data_bidirectional.json"
        template_obj.populate_performance_counters_json(mode=mode,
                                                        ip_version="IPv4",
                                                        latency_results=latency_results,
                                                        jitter_results=None,
                                                        file_name=output_file_path)
        '''


class NuTransitLatencyIPv6Test(NuTransitLatencyIPv4Test):
    def describe(self):
        self.set_test_details(id=2,
                              summary="NU Transit Performance Bidirectional Latency Test ((Mixed Size Frames IPv6)",
                              steps="""
                              1. Get port handles
                              2. Create stream block EthernetII and IPv6 Headers. Stream Config as follows
                                 a. Frames: %s
                                 b. Load: %d Mbps
                                 c. Fill TYpe PRBS
                                 d. Signature True
                              3. Activate stream on all ports and start traffic
                              4. Validate Tx and Rx rate for active streams under each port
                              5. Wait for traffic to complete
                              6. Validate Tx FrameCount and Rx FrameCount for active streams under each port
                              9. Ensure no errors are seen 
                              10. Validate latency numbers for each streams under each port
                              11. Deactivate current stream
                              """ % (IPV6_FRAMES, LOAD))

    def setup(self):
        # Re-initialize stream block global dict
        global stream_port_obj_dict
        stream_port_obj_dict = OrderedDict()

        self.ports = template_obj.stc_manager.get_port_list()
        fun_test.simple_assert(self.ports, "Get Port handle")

        l3_config = spirent_config["l3_config"]["ipv6"]
        l2_config = spirent_config["l2_config"]
        ether_type = Ethernet2Header.INTERNET_IPV6_ETHERTYPE

        # Create stream block objects for each port
        for port in self.ports:
            stream_objs = []
            for frame_size in IPV6_FRAMES:
                stream_objs.append(StreamBlock(fill_type=StreamBlock.FILL_TYPE_PRBS,
                                               insert_signature=True,
                                               fixed_frame_length=frame_size,
                                               load=LOAD,
                                               load_unit=StreamBlock.LOAD_UNIT_MEGABITS_PER_SECOND))
            stream_port_obj_dict[port] = stream_objs

        # Create Streams under each port
        for port in stream_port_obj_dict:
            stream_objects = stream_port_obj_dict[port]

            for stream_obj in stream_objects:
                checkpoint = "Create a IPv6 raw stream with %d frame size under %s" % (stream_obj.FixedFrameLength,
                                                                                       port)
                result = template_obj.configure_stream_block(stream_block_obj=stream_obj,
                                                             port_handle=port, ip_header_version=6)
                fun_test.test_assert(expression=result, message=checkpoint)

                checkpoint = "Configure Mac address for %s " % stream_obj.spirent_handle
                result = template_obj.stc_manager.configure_mac_address(streamblock=stream_obj.spirent_handle,
                                                                        source_mac=l2_config["source_mac"],
                                                                        destination_mac=l2_config["destination_mac"],
                                                                        ethernet_type=ether_type)
                fun_test.simple_assert(expression=result, message=checkpoint)

                if 'port2' in port:
                    source_ip = l3_config['source_ip2']
                    destination_ip = l3_config['destination_ip2']
                else:
                    source_ip = l3_config['source_ip1']
                    destination_ip = l3_config['destination_ip1']

                checkpoint = "Configure IP address for %s " % stream_obj.spirent_handle
                result = template_obj.stc_manager.configure_ip_address(streamblock=stream_obj.spirent_handle,
                                                                       source=source_ip,
                                                                       destination=destination_ip,
                                                                       ip_version=template_obj.stc_manager.IP_VERSION_6)
                fun_test.simple_assert(expression=result, message=checkpoint)

            checkpoint = "Deactivate All Streams under %s" % port
            result = template_obj.deactivate_stream_blocks(stream_obj_list=stream_objects)
            fun_test.test_assert(result, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribe_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(expression=self.subscribe_results['result'], message=checkpoint)

        self.expected_latency_data = performance_data

        if chassis_type == NuConfigManager.CHASSIS_TYPE_PHYSICAL:
            checkpoint = "Clear FPG port stats on DUT"
            for port_num in dut_config['ports']:
                result = network_controller_obj.clear_port_stats(port_num=port_num)
                fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
            fun_test.add_checkpoint(checkpoint=checkpoint)

    def run(self):
        super(NuTransitLatencyIPv6Test, self).run()

    def cleanup(self):
        for port in self.ports:
            template_obj.delete_streamblocks(stream_obj_list=stream_port_obj_dict[port])
        '''
        mode = dut_config['interface_mode']
        output_file_path = fun_test.get_script_parent_directory() + "/nu_transit_performance_data_bidirectional.json"
        template_obj.populate_performance_counters_json(mode=mode,
                                                        ip_version="IPv6",
                                                        latency_results=latency_results,
                                                        jitter_results=None,
                                                        file_name=output_file_path)
        '''


class NuTransitJitterTest(FunTestCase):
    subscribe_results = {}
    expected_jitter_data = {}
    ports = []
    view_attribute_list = ["AvgJitter", "MinJitter", "MaxJitter", "L1BitRate", "FrameRate", "FrameCount"]

    def describe(self):
        self.set_test_details(id=2,
                              summary="NU Transit Performance Bidirectional Jitter Test (Mixed Size Frames IPv4)",
                              steps="""
                              1. Get port handles
                              2. Create stream block EthernetII and IPv4 Headers. Stream Config as follows
                                 a. Frames: %s
                                 b. Load: %d Mbps
                                 c. Fill TYpe PRBS
                                 d. Signature True
                              3. Activate stream on all ports and start traffic
                              4. Validate Tx and Rx rate for active streams under each port
                              5. Wait for traffic to complete
                              6. Validate Tx FrameCount and Rx FrameCount for active streams under each port
                              9. Ensure no errors are seen 
                              10. Validate latency numbers for each streams under each port
                              11. Deactivate current stream
                              """ % (IPV4_FRAMES, LOAD))

    def setup(self):
        # Re-initialize streamblock global dict
        global stream_port_obj_dict
        stream_port_obj_dict = OrderedDict()

        self.ports = template_obj.stc_manager.get_port_list()
        fun_test.test_assert(self.ports, "Get Port handle")

        self.expected_jitter_data = performance_data

        l3_config = spirent_config["l3_config"]["ipv4"]
        l2_config = spirent_config["l2_config"]
        ether_type = Ethernet2Header.INTERNET_IP_ETHERTYPE

        # Create stream block objects for each port
        for port in self.ports:
            stream_objs = []
            for frame_size in IPV4_FRAMES:
                stream_objs.append(StreamBlock(fill_type=StreamBlock.FILL_TYPE_PRBS,
                                               insert_signature=True,
                                               fixed_frame_length=frame_size,
                                               load=LOAD,
                                               load_unit=StreamBlock.LOAD_UNIT_MEGABITS_PER_SECOND))
            stream_port_obj_dict[port] = stream_objs

        # Create Streams under each port
        for port in stream_port_obj_dict:
            stream_objects = stream_port_obj_dict[port]

            for stream_obj in stream_objects:
                checkpoint = "Create a IPv4 raw stream with %d frame size under %s" % (stream_obj.FixedFrameLength,
                                                                                       port)
                result = template_obj.configure_stream_block(stream_block_obj=stream_obj,
                                                             port_handle=port, ip_header_version=4)
                fun_test.test_assert(expression=result, message=checkpoint)

                checkpoint = "Configure Mac address for %s " % stream_obj.spirent_handle
                result = template_obj.stc_manager.configure_mac_address(streamblock=stream_obj.spirent_handle,
                                                                        source_mac=l2_config["source_mac"],
                                                                        destination_mac=l2_config["destination_mac"],
                                                                        ethernet_type=ether_type)
                fun_test.simple_assert(expression=result, message=checkpoint)

                if 'port2' in port:
                    source_ip = l3_config['source_ip2']
                    destination_ip = l3_config['destination_ip2']
                else:
                    source_ip = l3_config['source_ip1']
                    destination_ip = l3_config['destination_ip1']

                checkpoint = "Configure IP address for %s " % stream_obj.spirent_handle
                result = template_obj.stc_manager.configure_ip_address(streamblock=stream_obj.spirent_handle,
                                                                       source=source_ip,
                                                                       destination=destination_ip,
                                                                       gateway=l3_config['gateway'],
                                                                       ip_version=template_obj.stc_manager.IP_VERSION_6)
                fun_test.simple_assert(expression=result, message=checkpoint)

            checkpoint = "Deactivate All Streams under %s" % port
            result = template_obj.deactivate_stream_blocks(stream_obj_list=stream_objects)
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

        if chassis_type == NuConfigManager.CHASSIS_TYPE_PHYSICAL:
            checkpoint = "Clear FPG port stats on DUT"
            for port_num in dut_config['ports']:
                result = network_controller_obj.clear_port_stats(port_num=port_num)
                fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
            fun_test.add_checkpoint(checkpoint=checkpoint)

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

        checkpoint = "Enable Generator Config and start traffic for %d secs for all ports" % TRAFFIC_DURATION
        result = template_obj.enable_generator_configs(generator_configs=[
            generator_port_obj_dict[port1], generator_port_obj_dict[port2]])
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

        fun_test.sleep("Waiting for traffic to complete", seconds=TRAFFIC_DURATION)

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
                stream_objects=stream_objs, expected_performance_data=self.expected_jitter_data,
                tolerance_percent=TOLERANCE_PERCENT, jitter=True)
            fun_test.simple_assert(expression=jitter_result['result'], message=checkpoint)
            jitter_results[key].update(jitter_count=jitter_result[key])

        checkpoint = "Ensure no errors are seen for port %s" % analyzer_port_obj_dict[port1]
        analyzer_rx_results = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port1, subscribe_handle=self.subscribe_results['analyzer_subscribe'])
        result = template_obj.check_non_zero_error_count(rx_results=analyzer_rx_results)
        fun_test.test_assert(expression=result['result'], message=checkpoint)

        checkpoint = "Ensure no errors are seen for port %s" % analyzer_port_obj_dict[port2]
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
        for port in self.ports:
            template_obj.delete_streamblocks(stream_obj_list=stream_port_obj_dict[port])

        mode = dut_config['interface_mode']
        output_file_path = LOGS_DIR + "/nu_transit_performance_data_bidirectional.json"
        template_obj.populate_performance_counters_json(mode=mode,
                                                        ip_version="IPv4",
                                                        latency_results=latency_results,
                                                        jitter_results=jitter_results,
                                                        file_name=output_file_path)


class NuTransitJitterIPv6Test(NuTransitJitterTest):

    def describe(self):
        self.set_test_details(id=2,
                              summary="NU Transit Performance Bidirectional Jitter Test (IPv6)",
                              steps="""
                              1. Get port handles
                              2. Create stream block EthernetII and IPv6 Headers. Stream Config as follows
                                 a. Frames: %s
                                 b. Load: %d Mbps
                                 c. Fill TYpe PRBS
                                 d. Signature True
                              3. Activate stream on all ports and start traffic
                              4. Validate Tx and Rx rate for active streams under each port
                              5. Wait for traffic to complete
                              6. Validate Tx FrameCount and Rx FrameCount for active streams under each port
                              9. Ensure no errors are seen 
                              10. Validate latency numbers for each streams under each port
                              11. Deactivate current stream
                              """ % (IPV6_FRAMES, LOAD))

    def setup(self):
        # Re-initialize streamblock global dict
        global stream_port_obj_dict
        stream_port_obj_dict = OrderedDict()

        self.ports = template_obj.stc_manager.get_port_list()
        fun_test.test_assert(self.ports, "Get Port handle")

        self.expected_jitter_data = performance_data

        l3_config = spirent_config["l3_config"]["ipv6"]
        l2_config = spirent_config["l2_config"]
        ether_type = Ethernet2Header.INTERNET_IPV6_ETHERTYPE

        # Create stream block objects for each port
        for port in self.ports:
            stream_objs = []
            for frame_size in IPV6_FRAMES:
                stream_objs.append(StreamBlock(fill_type=StreamBlock.FILL_TYPE_PRBS,
                                               insert_signature=True,
                                               fixed_frame_length=frame_size,
                                               load=LOAD,
                                               load_unit=StreamBlock.LOAD_UNIT_MEGABITS_PER_SECOND))
            stream_port_obj_dict[port] = stream_objs

        # Create Streams under each port
        for port in stream_port_obj_dict:
            stream_objects = stream_port_obj_dict[port]

            for stream_obj in stream_objects:
                checkpoint = "Create a IPv6 raw stream with %d frame size under %s" % (stream_obj.FixedFrameLength,
                                                                                       port)
                result = template_obj.configure_stream_block(stream_block_obj=stream_obj,
                                                             port_handle=port, ip_header_version=6)
                fun_test.test_assert(expression=result, message=checkpoint)

                checkpoint = "Configure Mac address for %s " % stream_obj.spirent_handle
                result = template_obj.stc_manager.configure_mac_address(streamblock=stream_obj.spirent_handle,
                                                                        source_mac=l2_config["source_mac"],
                                                                        destination_mac=l2_config["destination_mac"],
                                                                        ethernet_type=ether_type)
                fun_test.simple_assert(expression=result, message=checkpoint)

                if 'port2' in port:
                    source_ip = l3_config['source_ip2']
                    destination_ip = l3_config['destination_ip2']
                else:
                    source_ip = l3_config['source_ip1']
                    destination_ip = l3_config['destination_ip1']

                checkpoint = "Configure IP address for %s " % stream_obj.spirent_handle
                result = template_obj.stc_manager.configure_ip_address(streamblock=stream_obj.spirent_handle,
                                                                       source=source_ip,
                                                                       destination=destination_ip,
                                                                       ip_version=template_obj.stc_manager.IP_VERSION_6)
                fun_test.simple_assert(expression=result, message=checkpoint)

            checkpoint = "Deactivate All Streams under %s" % port
            result = template_obj.deactivate_stream_blocks(stream_obj_list=stream_objects)
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

        if chassis_type == NuConfigManager.CHASSIS_TYPE_PHYSICAL:
            checkpoint = "Clear FPG port stats on DUT"
            for port_num in dut_config['ports']:
                result = network_controller_obj.clear_port_stats(port_num=port_num)
                fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
            fun_test.add_checkpoint(checkpoint=checkpoint)

    def run(self):
        super(NuTransitJitterIPv6Test, self).run()

    def cleanup(self):
        for port in self.ports:
            template_obj.delete_streamblocks(stream_obj_list=stream_port_obj_dict[port])

        mode = dut_config['interface_mode']
        output_file_path = LOGS_DIR + "/nu_transit_performance_data_bidirectional.json"
        template_obj.populate_performance_counters_json(mode=mode,
                                                        ip_version="IPv6",
                                                        latency_results=latency_results,
                                                        jitter_results=jitter_results,
                                                        file_name=output_file_path)


if __name__ == "__main__":
    test_case_mode = fun_test.get_local_setting(setting="ip_version")
    ts = NuTransitPerformance()
    if test_case_mode == 6:
        ts.add_test_case(NuTransitLatencyIPv6Test())
        ts.add_test_case(NuTransitJitterIPv6Test())
    elif test_case_mode == 4:
        ts.add_test_case(NuTransitLatencyIPv4Test())
        ts.add_test_case(NuTransitJitterTest())
    else:
        ts.add_test_case(NuTransitLatencyIPv4Test())
        ts.add_test_case(NuTransitJitterTest())
        ts.add_test_case(NuTransitLatencyIPv6Test())
        ts.add_test_case(NuTransitJitterIPv6Test())
    ts.run()













