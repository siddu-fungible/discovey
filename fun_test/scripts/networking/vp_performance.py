"""
Results Header Dict
{ "frame_size": {"is_input": true, "description": "Fixed Frame Size Test"},
  "test_type": {"is_input": false, "description": "Unidirectional Test"},
  "throughput": {"is_input": false, "description": "Throughput in Mbps"},
  "latency": {"is_input": false, "description": "Latency in us"},
  "jitter": {"is_input": false, "description": "Jitter in us"},
  "pps": {"is_input": false, "description": "Packets per secs"},
  "version": {"is_input": false, "description": "DUT version or FunOS version"}
  "mode": {"is_input": true, "description": "Port modes (25, 50 or 100 G)"},
  "timestamp": {"is_input": false, "description": "Date time of result data"},
  "flow_type": {"is_input": true, "description": "Traffic Direction for e.g FPG_HU or HU_FPG"},
  "spray_enable": {"is_input": true, "description": "VP Spray enable i.e adding IP Header Range Modifier to use
                  specific range of DIPs. For e.g 51.1.1.2 -- 51.1.1.14"}
}
"""

from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import *
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
INTERFACE_LOAD_SPEC = fun_test.get_script_parent_directory() + "/interface_loads.json"
TOLERANCE_PERCENT = 10
TRAFFIC_DURATION = 60
IPV4_FRAMES = [64, 200, 1000, 1500, 3000, 9000]
LOAD = 1200
chassis_type = None
FLOW_DIRECTION = NuConfigManager.FLOW_DIRECTION_FPG_HU
SPRAY_ENABLE = False


class NuVpPerformance(FunTestScript):
    MTU = 9000
    NO_OF_PORTS = 2
    EXPECTED_PERFORMANCE_DATA_FILE_NAME = "nu_vp_performance_data.json"
    port1 = None

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
        global chassis_type, perf_loads

        spirent_config = nu_config_obj.read_traffic_generator_config()
        dut_type = fun_test.get_local_setting(setting="dut_type")
        dut_config = nu_config_obj.read_dut_config(dut_type=dut_type, flow_type=NuConfigManager.VP_FLOW_TYPE,
                                                   flow_direction=FLOW_DIRECTION)
        chassis_type = fun_test.get_local_setting(setting="chassis_type")

        template_obj = SpirentEthernetTrafficTemplate(session_name="performance_bidirectional",
                                                      chassis_type=chassis_type, spirent_config=spirent_config)
        result = template_obj.setup(no_of_ports_needed=self.NO_OF_PORTS, flow_type=NuConfigManager.VP_FLOW_TYPE,
                                    flow_direction=FLOW_DIRECTION)
        fun_test.test_assert(result['result'], "Ensure Setup is done")

        dpc_server_ip = dut_config["dpcsh_tcp_proxy_ip"]
        dpc_server_port = dut_config["dpcsh_tcp_proxy_port"]

        self.port1 = result['port_list'][0]

        checkpoint = "Change ports MTU to %d" % self.MTU
        mtu_changed_on_spirent = template_obj.change_ports_mtu(interface_obj_list=result["interface_obj_list"],
                                                               mtu_value=self.MTU)
        fun_test.test_assert(mtu_changed_on_spirent, checkpoint)

        if dut_config['enable_dpcsh']:
            network_controller_obj = NetworkController(dpc_server_ip=dpc_server_ip, dpc_server_port=dpc_server_port)
            checkpoint = "Change DUT ports MTU to %d" % self.MTU
            for port_num in dut_config['ports']:
                if port_num == 1 or port_num == 2:
                    shape = 1
                else:
                    shape = 0
                mtu_changed = network_controller_obj.set_port_mtu(port_num=port_num, mtu_value=self.MTU, shape=shape)
                fun_test.simple_assert(mtu_changed, "Change MTU on DUT port %d to %d" % (port_num, self.MTU))
            fun_test.add_checkpoint(checkpoint)

            checkpoint = "Configure QoS settings"
            enable_pfc = network_controller_obj.enable_qos_pfc()
            fun_test.simple_assert(enable_pfc, "Enable QoS PFC")
            buffer_pool_set = network_controller_obj.set_qos_egress_buffer_pool(fcp_xoff_thr=16380,
                                                                                nonfcp_xoff_thr=16380)
            fun_test.test_assert(buffer_pool_set, checkpoint)

            if "HNU" in FLOW_DIRECTION:
                checkpoint = "Configure HNU QoS settings"
                enable_pfc = network_controller_obj.enable_qos_pfc(hnu=True)
                fun_test.simple_assert(enable_pfc, "Enable QoS PFC")
                buffer_pool_set = network_controller_obj.set_qos_egress_buffer_pool(fcp_xoff_thr=16380,
                                                                                    nonfcp_xoff_thr=16380,
                                                                                    mode="hnu")
                fun_test.test_assert(buffer_pool_set, checkpoint)

        checkpoint = "Read Performance expected data for fixed size scenario"
        file_path = LOGS_DIR + "/" + self.EXPECTED_PERFORMANCE_DATA_FILE_NAME
        performance_data = template_obj.read_json_file_contents(file_path=file_path)
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Get load as per flow_type"
        perf_loads = template_obj.read_json_file_contents(file_path=INTERFACE_LOAD_SPEC)['vp_performance']
        fun_test.simple_assert(perf_loads, checkpoint)

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


class NuVpLatencyIPv4Test(FunTestCase):
    subscribe_results = {}
    expected_latency_data = {}
    port = None

    def describe(self):
        self.set_test_details(id=1,
                              summary="NU VP Performance Unidirectional Latency Test (IPv4)",
                              steps="""
                              1. Get port handles
                              2. Create stream block EthernetII and IPv4 Headers. Stream Config as follows
                                 a. Frames: %s
                                 b. Load: %d fps
                                 c. Fill TYpe PRBS
                                 d. Signature True
                              3. Activate stream on one port and start traffic
                              4. Validate Tx and Rx rate for active streams under each port
                              5. Wait for traffic to complete
                              6. Validate Tx FrameCount and Rx FrameCount for active streams under each port
                              9. Ensure no errors are seen 
                              10. Validate latency numbers for each streams under each port
                              11. Deactivate current stream  
                              """ % (IPV4_FRAMES, LOAD))

    def setup(self):
        global LOAD
        ports = template_obj.stc_manager.get_port_list()
        self.port = ports[0]
        fun_test.simple_assert(self.port, "Get Port handle")

        l3_config = spirent_config["l3_config"]["ipv4"]
        l2_config = spirent_config["l2_config"]
        ether_type = Ethernet2Header.INTERNET_IP_ETHERTYPE

        # Create stream block objects for each port
        stream_objs = []
        spray = "spray_disable"
        if SPRAY_ENABLE:
            spray = "spray_enable"

        for frame_size in IPV4_FRAMES:
            LOAD = perf_loads[FLOW_DIRECTION][spray][str(frame_size)]
            stream_objs.append(StreamBlock(fill_type=StreamBlock.FILL_TYPE_PRBS,
                                           insert_signature=True,
                                           fixed_frame_length=frame_size,
                                           load=LOAD,
                                           load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND))
        stream_port_obj_dict[self.port] = stream_objs

        stream_objects = stream_port_obj_dict[self.port]

        for stream_obj in stream_objects:
            checkpoint = "Create a raw stream with %d frame size under %s" % (stream_obj.FixedFrameLength,
                                                                              self.port)
            result = template_obj.configure_stream_block(stream_block_obj=stream_obj,
                                                         port_handle=self.port)
            fun_test.test_assert(expression=result, message=checkpoint)

            ethernet_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'], ether_type=ether_type)

            checkpoint = "Configure Mac address for %s " % stream_obj.spirent_handle
            result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=stream_obj.spirent_handle,
                                                                    header_obj=ethernet_obj, update=True)
            fun_test.simple_assert(expression=result, message=checkpoint)

            checkpoint = "Configure IP address for %s " % stream_obj.spirent_handle
            if FLOW_DIRECTION == NuConfigManager.FLOW_DIRECTION_FPG_HU:
                recycle_count = 200
                dest_ip = l3_config['vp_destination_ip1']
            elif FLOW_DIRECTION == NuConfigManager.FLOW_DIRECTION_FPG_HNU or \
                    FLOW_DIRECTION == NuConfigManager.FLOW_DIRECTION_HNU_HNU:
                recycle_count = 13
                dest_ip = l3_config['hnu_destination_ip2']
            elif FLOW_DIRECTION == NuConfigManager.FLOW_DIRECTION_FCP_HNU_HNU:
                recycle_count = 1
                dest_ip = l3_config['hnu_fcp_destination_ip1']
            else:
                recycle_count = 200
                dest_ip = l3_config['destination_ip2']
            if stream_obj.FixedFrameLength == 64:
                ip_header_obj = Ipv4Header(destination_address=dest_ip,
                                           protocol=Ipv4Header.PROTOCOL_TYPE_EXPERIMENTAL)
            else:
                ip_header_obj = Ipv4Header(destination_address=dest_ip,
                                           protocol=Ipv4Header.PROTOCOL_TYPE_TCP)
            result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=stream_obj.spirent_handle,
                                                                    header_obj=ip_header_obj, update=True)
            fun_test.simple_assert(expression=result, message=checkpoint)

            if FLOW_DIRECTION != NuConfigManager.FLOW_DIRECTION_HU_FPG and FLOW_DIRECTION != \
                    NuConfigManager.FLOW_DIRECTION_HNU_FPG and \
                    FLOW_DIRECTION != NuConfigManager.FLOW_DIRECTION_FCP_HNU_HNU and \
                    FLOW_DIRECTION != NuConfigManager.FLOW_DIRECTION_HNU_HNU:
                if SPRAY_ENABLE:
                    checkpoint = "Configure IP range modifier"
                    modifier_obj = RangeModifier(modifier_mode=RangeModifier.INCR, recycle_count=recycle_count,
                                                 step_value="0.0.0.1", mask="255.255.255.255",
                                                 data=dest_ip)
                    result = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=modifier_obj,
                                                                               header_obj=ip_header_obj,
                                                                               streamblock_obj=stream_obj,
                                                                               header_attribute="destAddr")
                    fun_test.simple_assert(result, checkpoint)

            if stream_obj.FixedFrameLength != 64:
                checkpoint = "Add TCP header"
                tcp_header_obj = TCP()
                result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=stream_obj.spirent_handle,
                                                                        header_obj=tcp_header_obj, update=False)
                fun_test.simple_assert(result, checkpoint)

                if SPRAY_ENABLE:
                    checkpoint = "Configure Port Modifier"
                    port_modifier_obj = RangeModifier(modifier_mode=RangeModifier.INCR, step_value=1, recycle_count=200,
                                                      data=1024)
                    result = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=port_modifier_obj,
                                                                               header_obj=tcp_header_obj,
                                                                               streamblock_obj=stream_obj,
                                                                               header_attribute="destPort")
                    fun_test.simple_assert(result, checkpoint)
                    result = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=port_modifier_obj,
                                                                               header_obj=tcp_header_obj,
                                                                               streamblock_obj=stream_obj,
                                                                               header_attribute="sourcePort")
                    fun_test.simple_assert(result, checkpoint)

        checkpoint = "Deactivate All Streams under %s" % self.port
        result = template_obj.deactivate_stream_blocks(stream_obj_list=stream_objects)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Subscribe to all results"
        self.subscribe_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(expression=self.subscribe_results['result'], message=checkpoint)

        self.expected_latency_data = performance_data

        if dut_config['enable_dpcsh']:
            checkpoint = "Clear FPG port stats on DUT"
            for port_num in dut_config['ports']:
                result = network_controller_obj.clear_port_stats(port_num=port_num)
                fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
            fun_test.add_checkpoint(checkpoint=checkpoint)

    def run(self):
        ports = template_obj.stc_manager.get_port_list()
        rx_port = ports[1]
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

            vp_stats = None
            if dut_config['enable_dpcsh']:
                vp_stats = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)
                fun_test.simple_assert(vp_stats, "Ensure VP stats fetched before traffic")
                fun_test.log("VP stats: %s" % vp_stats)

            checkpoint = "Enable Generator Config and start traffic for %d secs for all ports" % TRAFFIC_DURATION
            result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[port1]])
            fun_test.simple_assert(expression=result, message=checkpoint)

            fun_test.sleep("Traffic to start", seconds=4)

            checkpoint = "Validate Tx and Rx Rate"
            rate_result = template_obj.validate_traffic_rate_results(
                rx_summary_subscribe_handle=self.subscribe_results['rx_summary_subscribe'],
                tx_summary_subscribe_handle=self.subscribe_results['tx_stream_subscribe'],
                stream_objects=[stream_obj])
            fun_test.simple_assert(expression=rate_result['result'], message=checkpoint)
            fun_test.sleep("Waiting for traffic to complete", seconds=TRAFFIC_DURATION)

            if dut_config['enable_dpcsh']:
                checkpoint = "Validate FPG FrameCount Tx == Rx for port direction %d --> %d on DUT" % (
                    dut_config['ports'][0], dut_config['ports'][1])
                if FLOW_DIRECTION == NuConfigManager.FLOW_DIRECTION_HNU_FPG or "HNU_HNU" in FLOW_DIRECTION:
                    port1_result = network_controller_obj.peek_fpg_port_stats(port_num=dut_config['ports'][0], hnu=True)
                    fun_test.log("Port %d Results: %s" % (dut_config['ports'][0], port1_result))
                    fun_test.test_assert(port1_result, "Get %d Port FPG Stats" % dut_config['ports'][0])
                else:
                    port1_result = network_controller_obj.peek_fpg_port_stats(port_num=dut_config['ports'][0], hnu=False)
                    fun_test.log("Port %d Results: %s" % (dut_config['ports'][0], port1_result))
                    fun_test.test_assert(port1_result, "Get %d Port FPG Stats" % dut_config['ports'][0])

                if FLOW_DIRECTION == NuConfigManager.FLOW_DIRECTION_FPG_HNU or "HNU_HNU" in FLOW_DIRECTION:
                    port2_result = network_controller_obj.peek_fpg_port_stats(port_num=dut_config['ports'][1], hnu=True)
                    fun_test.log("Port %d Results: %s" % (dut_config['ports'][1], port2_result))
                    fun_test.test_assert(port2_result, "Get %d Port FPG Stats" % dut_config['ports'][1])
                else:
                    port2_result = network_controller_obj.peek_fpg_port_stats(port_num=dut_config['ports'][1], hnu=False)
                    fun_test.log("Port %d Results: %s" % (dut_config['ports'][1], port2_result))
                    fun_test.test_assert(port2_result, "Get %d Port FPG Stats" % dut_config['ports'][1])

                frames_transmitted = get_dut_output_stats_value(result_stats=port1_result,
                                                                stat_type=FRAMES_TRANSMITTED_OK)
                frames_received = get_dut_output_stats_value(result_stats=port2_result, stat_type=FRAMES_RECEIVED_OK)

                fun_test.test_assert_expected(expected=frames_transmitted, actual=frames_received,
                                              message=checkpoint)

                checkpoint = "Validate VP total IN == total OUT"
                vp_stats_after = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)
                fun_test.log("VP stats: %s" % vp_stats_after)
                vp_stats_diff = get_diff_stats(old_stats=vp_stats, new_stats=vp_stats_after)
                fun_test.simple_assert(vp_stats_diff, "Ensure VP stats diff fetched")
                actual_vp_stats = vp_stats_diff[VP_PACKETS_TOTAL_OUT] + vp_stats_diff[
                    VP_PACKETS_FORWARDING_NU_DIRECT] + vp_stats_diff[VP_PACKETS_CC_OUT]
                fun_test.test_assert_expected(expected=vp_stats_diff[VP_PACKETS_TOTAL_IN],
                                              actual=actual_vp_stats,
                                              message=checkpoint)

            checkpoint = "Validate Latency Results"
            latency_result = template_obj.validate_performance_result(
                tx_subscribe_handle=self.subscribe_results['tx_subscribe'],
                rx_subscribe_handle=self.subscribe_results['rx_summary_subscribe'],
                stream_objects=[stream_obj], expected_performance_data=self.expected_latency_data,
                tolerance_percent=TOLERANCE_PERCENT, flow_type=FLOW_DIRECTION, spray_enabled=SPRAY_ENABLE)
            fun_test.simple_assert(expression=latency_result['result'], message=checkpoint)

            checkpoint = "Ensure no errors are seen for port %s" % analyzer_port_obj_dict[rx_port]
            analyzer_rx_results = template_obj.stc_manager.get_rx_port_analyzer_results(
                port_handle=rx_port, subscribe_handle=self.subscribe_results['analyzer_subscribe'])
            result = template_obj.check_non_zero_error_count(rx_results=analyzer_rx_results)
            if (FLOW_DIRECTION == NuConfigManager.FLOW_DIRECTION_FPG_HNU or FLOW_DIRECTION == NuConfigManager.FLOW_DIRECTION_HNU_FPG) \
                    and SPRAY_ENABLE:
                fun_test.log("Error Counters are seen Reordered Frame Count: %d \n PrbsErrorFrameCount: %d" % (
                    result['ReorderedFrameCount'], result['PrbsErrorFrameCount']))
            else:
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
        template_obj.delete_streamblocks(stream_obj_list=stream_port_obj_dict[self.port])


class NuVpJitterTest(FunTestCase):
    port = None
    view_attribute_list = ["AvgJitter", "MinJitter", "MaxJitter", "L1BitRate", "FrameRate", "FrameCount"]
    expected_jitter_data = {}
    subscribe_results = {}

    def describe(self):
        self.set_test_details(id=2,
                              summary="NU VP Performance Unidirectional Jitter Test (IPv4)",
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
        global LOAD
        ports = template_obj.stc_manager.get_port_list()
        self.port = ports[0]
        fun_test.test_assert(self.port, "Get Port handle")
        self.expected_jitter_data = performance_data

        # Re-initialize streamblock global dict
        global stream_port_obj_dict
        stream_port_obj_dict = OrderedDict()

        l3_config = spirent_config["l3_config"]["ipv4"]
        l2_config = spirent_config["l2_config"]
        ether_type = Ethernet2Header.INTERNET_IP_ETHERTYPE

        # Create stream block objects for each port
        stream_objs = []
        spray = "spray_disable"
        if SPRAY_ENABLE:
            spray = "spray_enable"

        for frame_size in IPV4_FRAMES:
            LOAD = perf_loads[FLOW_DIRECTION][spray][str(frame_size)]
            stream_objs.append(StreamBlock(fill_type=StreamBlock.FILL_TYPE_PRBS,
                                           insert_signature=True,
                                           fixed_frame_length=frame_size,
                                           load=LOAD,
                                           load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND))
        stream_port_obj_dict[self.port] = stream_objs

        stream_objects = stream_port_obj_dict[self.port]

        for stream_obj in stream_objects:
            checkpoint = "Create a raw stream with %d frame size under %s" % (stream_obj.FixedFrameLength,
                                                                              self.port)
            result = template_obj.configure_stream_block(stream_block_obj=stream_obj,
                                                         port_handle=self.port)
            fun_test.test_assert(expression=result, message=checkpoint)

            ethernet_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'], ether_type=ether_type)

            checkpoint = "Configure Mac address for %s " % stream_obj.spirent_handle
            result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=stream_obj.spirent_handle,
                                                                    header_obj=ethernet_obj, update=True)
            fun_test.simple_assert(expression=result, message=checkpoint)

            if FLOW_DIRECTION == NuConfigManager.FLOW_DIRECTION_FPG_HU:
                recycle_count = 200
                dest_ip = l3_config['vp_destination_ip1']
            elif FLOW_DIRECTION == NuConfigManager.FLOW_DIRECTION_FPG_HNU:
                recycle_count = 13
                dest_ip = l3_config['hnu_destination_ip2']
            else:
                recycle_count = 200
                dest_ip = l3_config['destination_ip2']
            if stream_obj.FixedFrameLength == 64:
                ip_header_obj = Ipv4Header(destination_address=dest_ip,
                                           protocol=Ipv4Header.PROTOCOL_TYPE_EXPERIMENTAL)
            else:
                ip_header_obj = Ipv4Header(destination_address=dest_ip,
                                           protocol=Ipv4Header.PROTOCOL_TYPE_TCP)
            result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=stream_obj.spirent_handle,
                                                                    header_obj=ip_header_obj, update=True)
            fun_test.simple_assert(expression=result, message=checkpoint)

            if FLOW_DIRECTION != NuConfigManager.FLOW_DIRECTION_HU_FPG and FLOW_DIRECTION != \
                    NuConfigManager.FLOW_DIRECTION_HNU_FPG:
                if SPRAY_ENABLE:
                    checkpoint = "Configure IP range modifier"
                    modifier_obj = RangeModifier(modifier_mode=RangeModifier.INCR, recycle_count=recycle_count,
                                                 step_value="0.0.0.1", mask="255.255.255.255",
                                                 data=dest_ip)
                    result = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=modifier_obj,
                                                                               header_obj=ip_header_obj,
                                                                               streamblock_obj=stream_obj,
                                                                               header_attribute="destAddr")
                    fun_test.simple_assert(result, checkpoint)

            if stream_obj.FixedFrameLength != 64:
                checkpoint = "Add TCP header"
                tcp_header_obj = TCP()
                result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=stream_obj.spirent_handle,
                                                                        header_obj=tcp_header_obj, update=False)
                fun_test.simple_assert(result, checkpoint)

                if SPRAY_ENABLE:
                    checkpoint = "Configure Port Modifier"
                    port_modifier_obj = RangeModifier(modifier_mode=RangeModifier.INCR, step_value=1, recycle_count=200,
                                                      data=1024)
                    result = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=port_modifier_obj,
                                                                               header_obj=tcp_header_obj,
                                                                               streamblock_obj=stream_obj,
                                                                               header_attribute="destPort")
                    fun_test.simple_assert(result, checkpoint)
                    result = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=port_modifier_obj,
                                                                               header_obj=tcp_header_obj,
                                                                               streamblock_obj=stream_obj,
                                                                               header_attribute="sourcePort")
                    fun_test.simple_assert(result, checkpoint)

        checkpoint = "Deactivate All Streams under %s" % self.port
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

    def run(self):
        ports = template_obj.stc_manager.get_port_list()
        rx_port = ports[1]
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

            checkpoint = "Enable Generator Config and start traffic for %d secs for all ports" % TRAFFIC_DURATION
            result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[self.port]])
            fun_test.simple_assert(expression=result, message=checkpoint)

            fun_test.sleep("Waiting for traffic to reach full throughput", seconds=10)
            checkpoint = "Validate Tx and Rx Rate"
            rate_result = template_obj.validate_traffic_rate_results(
                rx_summary_subscribe_handle=self.subscribe_results['rx_summary_subscribe'],
                tx_summary_subscribe_handle=self.subscribe_results['tx_stream_subscribe'],
                stream_objects=[stream_obj], wait_before_fetching_results=False, validate_throughput=False)
            fun_test.simple_assert(expression=rate_result['result'], message=checkpoint)

            fun_test.sleep("Waiting for traffic to complete", seconds=TRAFFIC_DURATION)

            checkpoint = "Validate Jitter Results"
            jitter_result = template_obj.validate_performance_result(
                tx_subscribe_handle=self.subscribe_results['tx_subscribe'],
                rx_subscribe_handle=self.subscribe_results['rx_summary_subscribe'],
                stream_objects=[stream_obj], expected_performance_data=self.expected_jitter_data,
                tolerance_percent=TOLERANCE_PERCENT, jitter=True, flow_type=FLOW_DIRECTION, spray_enabled=SPRAY_ENABLE)
            fun_test.simple_assert(expression=jitter_result, message=checkpoint)

            checkpoint = "Ensure no errors are seen for port %s" % analyzer_port_obj_dict[rx_port]
            analyzer_rx_results = template_obj.stc_manager.get_rx_port_analyzer_results(
                port_handle=rx_port, subscribe_handle=self.subscribe_results['analyzer_subscribe'])
            result = template_obj.check_non_zero_error_count(rx_results=analyzer_rx_results)
            if (FLOW_DIRECTION == NuConfigManager.FLOW_DIRECTION_FPG_HNU or FLOW_DIRECTION == NuConfigManager.FLOW_DIRECTION_HNU_FPG) \
                    and SPRAY_ENABLE:
                fun_test.log("Error Counters are seen Reordered Frame Count: %d \n PrbsErrorFrameCount: %d" % (
                    result['ReorderedFrameCount'], result['PrbsErrorFrameCount']))
            else:
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
        template_obj.delete_streamblocks(stream_obj_list=stream_port_obj_dict[self.port])

        mode = dut_config['interface_mode']
        output_file_path = LOGS_DIR + "/nu_vp_performance_data.json"
        template_obj.populate_performance_counters_json(mode=mode, flow_type=FLOW_DIRECTION,
                                                        latency_results=latency_results,
                                                        jitter_results=jitter_results,
                                                        file_name=output_file_path, spray_enable=SPRAY_ENABLE)


if __name__ == "__main__":
    cc_flow_type = nu_config_obj.get_local_settings_parameters(flow_direction=True, spray_enable=True)
    FLOW_DIRECTION = cc_flow_type[NuConfigManager.FLOW_DIRECTION]
    SPRAY_ENABLE = cc_flow_type[NuConfigManager.SPRAY_ENABLE]
    ts = NuVpPerformance()
    ts.add_test_case(NuVpLatencyIPv4Test())
    ts.add_test_case(NuVpJitterTest())
    ts.run()

