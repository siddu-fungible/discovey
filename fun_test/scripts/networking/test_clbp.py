from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, GeneratorConfig, Ethernet2Header, TCP, UDP, RangeModifier, Ipv4Header
from lib.host.network_controller import NetworkController
from helper import *
from nu_config_manager import *

clbp_traffic_duration = 20
cushion_sleep = 5
num_ports = 2


def compare_spray_values(reference_value, actual_value):
    result = False
    if actual_value == reference_value or actual_value + 1 == reference_value or actual_value - 1 == reference_value:
        result = True
    return result


def check_per_vp_pkt_spray(flow_direction, per_vppkt_output_dict, dut_ingress_frame_count):
    result = False
    try:
        total_pkts_sent = int(dut_ingress_frame_count)
        total_vps = len(per_vppkt_output_dict)
        reference_value = int(total_pkts_sent / total_vps)
        for key, val in per_vppkt_output_dict.iteritems():
            total_vp_in = int(val[VP_PACKETS_TOTAL_IN])
            total_vp_out = int(val[VP_PACKETS_TOTAL_OUT])
            if flow_direction == NuConfigManager.FLOW_DIRECTION_HU_FPG:
                total_vp_fae_requests = int(val[VP_FAE_REQUESTS_SENT])
                total_vp_fae_responses = int(val[VP_FAE_RESPONSES_RECEIVED])
                total_vp_out_etp = int(val[VP_PACKETS_OUT_ETP])
            else:
                total_vp_fwd_nu_le = int(val[VP_PACKETS_FORWARDING_NU_LE])

            fun_test.log("======== Checks on %s =========" % str(key))
            fun_test.test_assert(compare_spray_values(reference_value, total_vp_in),
                                 "Check counter for %s. Expected value: %s Actual value %s " %
                                 (VP_PACKETS_TOTAL_IN, reference_value, total_vp_in))
            fun_test.test_assert(compare_spray_values(reference_value, total_vp_out),
                                 "Check counter for %s. Expected value: %s Actual value %s " %
                                 (VP_PACKETS_TOTAL_OUT, reference_value, total_vp_out))
            if flow_direction == NuConfigManager.FLOW_DIRECTION_FPG_HU:
                fun_test.test_assert(compare_spray_values(reference_value, total_vp_fwd_nu_le),
                                     "Check counter for %s. Expected value: %s Actual value %s " %
                                     (VP_PACKETS_FORWARDING_NU_LE, reference_value, total_vp_fwd_nu_le))
            else:
                fun_test.test_assert(compare_spray_values(reference_value, total_vp_fae_requests),
                                     "Check counter for %s. Expected value: %s Actual value %s " %
                                     (VP_FAE_REQUESTS_SENT, reference_value, total_vp_fae_requests))
                fun_test.test_assert(compare_spray_values(reference_value, total_vp_fae_responses),
                                     "Check counter for %s. Expected value: %s Actual value %s " %
                                     (VP_FAE_RESPONSES_RECEIVED, reference_value,
                                      total_vp_fae_responses))
                fun_test.test_assert(compare_spray_values(reference_value, total_vp_out_etp),
                                     "Check counter for %s. Expected value: %s Actual value %s " %
                                     (VP_PACKETS_OUT_ETP, reference_value, total_vp_out_etp))
        result = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


class SpirentSetup(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
                1. Create Spirent template
                2. Connect chassis, labserver and licenseserver
                3. Attach Ports
                4. Configure generator that runs traffic for specified amount.
                5. Subscribe to tx, rx and analyzer results
                """)

    def setup(self):
        global template_obj, port_1, port_2, interface_1_obj, interface_2_obj, gen_config_obj, \
            gen_obj_1, subscribe_results, dut_port_2, dut_port_1, network_controller_obj, \
            dut_config, spirent_config

        dut_type = fun_test.get_local_setting(setting="dut_type")
        dut_config = nu_config_obj.read_dut_config(dut_type=dut_type,
                                                   flow_direction=flow_direction,
                                                   flow_type=NuConfigManager.VP_FLOW_TYPE)

        chassis_type = fun_test.get_local_setting(setting="chassis_type")
        spirent_config = nu_config_obj.read_traffic_generator_config()

        fun_test.log("Creating Template object")
        template_obj = SpirentEthernetTrafficTemplate(session_name="test_vp_pkt_spray", spirent_config=spirent_config,
                                                      chassis_type=chassis_type)
        fun_test.test_assert(template_obj, "Create template object")

        result = template_obj.setup(no_of_ports_needed=num_ports, flow_type=NuConfigManager.VP_FLOW_TYPE,
                                    flow_direction=flow_direction)
        fun_test.test_assert(result['result'], "Configure setup")

        port_1 = result['port_list'][0]
        port_2 = result['port_list'][1]

        dut_port_1 = dut_config['ports'][0]
        dut_port_2 = dut_config['ports'][1]

        if dut_config['enable_dpcsh']:
            # Create network controller object
            dpcsh_server_ip = dut_config["dpcsh_tcp_proxy_ip"]
            dpcsh_server_port = dut_config['dpcsh_tcp_proxy_port']
            network_controller_obj = NetworkController(dpc_server_ip=dpcsh_server_ip, dpc_server_port=dpcsh_server_port)

            # Enable qos pfc
            set_pfc = network_controller_obj.enable_qos_pfc()
            fun_test.test_assert(set_pfc, "Enable qos pfc")
            buffer = network_controller_obj.set_qos_egress_buffer_pool(nonfcp_xoff_thr=16380,
                                                                       fcp_xoff_thr=16380)
            fun_test.test_assert(buffer, "Set non fcp xoff threshold")

        # Configure Generator
        gen_config_obj = GeneratorConfig()
        gen_config_obj.SchedulingMode = gen_config_obj.SCHEDULING_MODE_RATE_BASED
        gen_config_obj.DurationMode = gen_config_obj.DURATION_MODE_SECONDS
        gen_config_obj.Duration = clbp_traffic_duration
        gen_config_obj.AdvancedInterleaving = True

        # Apply generator config on port 1
        gen_obj_1 = template_obj.stc_manager.get_generator(port_handle=port_1)
        config_obj = template_obj.configure_generator_config(port_handle=port_1,
                                                             generator_config_obj=gen_config_obj)
        fun_test.test_assert(config_obj, "Creating generator config on port %s" % port_1)

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


class CLBP(FunTestCase):
    streamblock_obj = None

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test cluster load balancing behaviour for VP pkts",
                              steps="""
                            1. Create streamblock with varying source port, dest port, source ip and dest ip
                            2. Start traffic 
                            3. Check if peek stats are being load balanced among all VPs
                            """)

    def setup(self):
        self.streamblock_obj = StreamBlock(load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND, load=fps,
                                           fill_type=StreamBlock.FILL_TYPE_PRBS)

        create_stream =template_obj.configure_stream_block(stream_block_obj=self.streamblock_obj, port_handle=port_1)
        fun_test.test_assert(create_stream, "Create streamblock")

        l2_config = spirent_config["l2_config"]
        ether_type = Ethernet2Header.INTERNET_IP_ETHERTYPE

        ether = template_obj.stc_manager.configure_mac_address(streamblock=self.streamblock_obj.spirent_handle,
                                                               source_mac=l2_config['source_mac'],
                                                               destination_mac=l2_config['destination_mac'],
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Adding source and destination mac")

        tcp = TCP()
        add_tcp = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj._spirent_handle,
                                                                 header_obj=tcp)
        fun_test.test_assert(add_tcp, "Added tcp header to stack")

        ip_header = Ipv4Header()

        # Vary source ip
        l3_config = spirent_config["l3_config"]["ipv4"]
        source_ip = l3_config['source_ip1']
        destination_ip = l3_config['hu_destination_ip1']
        if flow_direction == NuConfigManager.FLOW_DIRECTION_HU_FPG:
            temp_ip = source_ip
            source_ip = destination_ip
            destination_ip = temp_ip
        recycle_count = 200
        data = source_ip
        step = '0.0.0.1'
        mask = "255.255.255.255"
        range_obj = RangeModifier(recycle_count=recycle_count, step_value=step, data=data, mask=mask)
        modify_attribute = 'sourceAddr'
        create_range = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=range_obj,
                                                                         streamblock_obj=self.streamblock_obj,
                                                                         header_obj=ip_header,
                                                                         header_attribute=modify_attribute)
        fun_test.test_assert(create_range, "Ensure range modifier created for attribute %s"
                             % modify_attribute)

        # Vary dest ip
        data = destination_ip
        range_obj = RangeModifier(recycle_count=recycle_count, step_value=step, data=data, mask=mask)
        modify_attribute = 'destAddr'
        create_range = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=range_obj,
                                                                         streamblock_obj=self.streamblock_obj,
                                                                         header_obj=ip_header,
                                                                         header_attribute=modify_attribute)
        fun_test.test_assert(create_range, "Ensure range modifier created for attribute %s"
                             % modify_attribute)

        # Vary source port
        data = 1024
        step = 1
        range_obj = RangeModifier(recycle_count=recycle_count, step_value=step, data=data)
        modify_attribute = 'sourcePort'
        create_range = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=range_obj,
                                                                         streamblock_obj=self.streamblock_obj,
                                                                         header_obj=tcp,
                                                                         header_attribute=modify_attribute)
        fun_test.test_assert(create_range, "Ensure range modifier created for attribute %s"
                             % modify_attribute)

        # Vary dest port
        modify_attribute = 'destPort'
        create_range = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=range_obj,
                                                                         streamblock_obj=self.streamblock_obj,
                                                                         header_obj=tcp,
                                                                         header_attribute=modify_attribute)
        fun_test.test_assert(create_range, "Ensure range modifier created for attribute %s"
                             % modify_attribute)

    def run(self):
        if dut_config['enable_dpcsh']:
            # Get stats before starting traffic
            fun_test.log("Get stats before starting traffic")
            bam_stats_1 = get_bam_stats_values(network_controller_obj=network_controller_obj)
            parser_stats_1 = network_controller_obj.peek_parser_stats()
            vp_pkts_stats_1 = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)
            erp_stats_1 = get_erp_stats_values(network_controller_obj=network_controller_obj)
            psw_stats_1 = network_controller_obj.peek_psw_global_stats()
            wro_stats_1 = network_controller_obj.peek_wro_global_stats()

        # Modify generator
        gen_config_obj.Duration = clbp_traffic_duration
        config_obj = template_obj.configure_generator_config(port_handle=port_1,
                                                             generator_config_obj=gen_config_obj, update=True)
        fun_test.test_assert(config_obj, "Updating generator config on port %s" % port_1)

        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=[gen_obj_1])
        fun_test.test_assert(start, "Starting generator config")

        stream_handle_1 = self.streamblock_obj.spirent_handle

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic for %s seconds" % clbp_traffic_duration,
                       seconds=clbp_traffic_duration)

        stop = template_obj.disable_generator_configs(generator_configs=[gen_obj_1])
        fun_test.test_assert(stop, "Stopping generator configs")

        fun_test.sleep("Letting rx to take place", seconds=2)

        # Asserts
        stream_result_dict = template_obj.stc_manager.fetch_streamblock_results(subscribe_result=subscribe_results,
                                                                                streamblock_handle_list=
                                                                                [stream_handle_1],
                                                                                tx_result=True, rx_result=True)

        port_result_dict = template_obj.stc_manager.fetch_port_results(subscribe_result=subscribe_results,
                                                                       port_handle_list=[port_2],
                                                                       analyzer_result=True)

        tx_results_1 = stream_result_dict[stream_handle_1]['tx_result']
        rx_results_1 = stream_result_dict[stream_handle_1]['rx_result']
        port_2_analyzer_result = port_result_dict[port_2]['analyzer_result']

        fun_test.log(tx_results_1)
        fun_test.log(rx_results_1)
        fun_test.log(port_2_analyzer_result)

        if dut_config['enable_dpcsh']:
            dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1)
            fun_test.test_assert(dut_port_1_results, message="Ensure stats are obtained for %s" % dut_port_1)
            dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2)
            fun_test.test_assert(dut_port_2_results, message="Ensure stats are obtained for %s" % dut_port_2)

            fun_test.log("Get system stats after traffic execution")
            bam_stats_2 = get_bam_stats_values(network_controller_obj=network_controller_obj)
            parser_stats_2 = network_controller_obj.peek_parser_stats()
            vp_pkts_stats_2 = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)
            erp_stats_2 = get_erp_stats_values(network_controller_obj=network_controller_obj)
            psw_stats_2 = network_controller_obj.peek_psw_global_stats()
            vp_per_packet_stats_2 = get_vp_per_pkts_stats_values(network_controller_obj=network_controller_obj)
            wro_stats_2 = network_controller_obj.peek_wro_global_stats()

            dut_port_1_receive = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)

            fun_test.log("Check counters for vp spray")
            counter_check = check_per_vp_pkt_spray(flow_direction=flow_direction, per_vppkt_output_dict=vp_per_packet_stats_2,
                                                   dut_ingress_frame_count=dut_port_1_receive)
            fun_test.test_assert(counter_check, "Check cluster load balancing in per vppkts")

        # SPIRENT ASSERTS
        fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']), actual=int(rx_results_1['FrameCount']),
                                      message="Ensure frames transmitted and received on spirent match from %s" % flow_direction)

        zero_counter_seen = template_obj.check_non_zero_error_count(port_2_analyzer_result)
        fun_test.test_assert(zero_counter_seen['result'], "Check for error counters on port2")

    def cleanup(self):
        fun_test.log("In testcase cleanup")

        fun_test.log("Deleting streamblock %s " % self.streamblock_obj.spirent_handle)
        template_obj.delete_streamblocks(streamblock_handle_list=[self.streamblock_obj.spirent_handle])

        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])


if __name__ == "__main__":
    local_settings = nu_config_obj.get_local_settings_parameters(flow_direction=True, ip_version=True)
    flow_direction = local_settings[nu_config_obj.FLOW_DIRECTION]
    fps = 150
    if flow_direction == NuConfigManager.FLOW_DIRECTION_HU_FPG:
        fps = 50
    elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_FPG:
        fps = 50
    elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_HNU:
        fps = 50
    elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_CC:
        fps = 50
    ts = SpirentSetup()
    ts.add_test_case(CLBP())
    ts.run()