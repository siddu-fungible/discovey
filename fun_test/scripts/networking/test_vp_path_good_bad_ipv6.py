from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, GeneratorConfig, Ethernet2Header, TCP, UDP, Ipv4Header, RangeModifier, CustomBytePatternHeader, VxLAN, \
    Ipv6Header
from lib.host.network_controller import NetworkController
from helper import *
from nu_config_manager import *


num_ports = 3
total_packets = 10
total_duration = total_packets
bad_load = 1
good_load = 40
aggregate_bad_load = 1
stream_objs = {}
stream_objs['bad'] = OrderedDict()
stream_objs['good'] = OrderedDict()
UL_v6_BAD_UDP_XSUM = "UL_v6_BAD_UDP_XSUM"
UL_v6_BAD_UDP_ZERO_XSUM = "UL_v6_BAD_UDP_ZERO_XSUM"
UL_v6_BAD_TCP_XSUM = "UL_v6_BAD_TCP_XSUM"
UL_v4_OL_v6_BAD_UDP_XSUM = "UL_v4_OL_v6_BAD_UDP_XSUM"
UL_v4_ZERO_UDP_XSUM_OL_v6_ZERO_UDP_XSUM = "UL_v4_ZERO_UDP_XSUM_OL_v6_ZERO_UDP_XSUM"
UL_v4_ZERO_UDP_XSUM_OL_v6_BAD_TCP_XSUM = "UL_v4_ZERO_UDP_XSUM_OL_v6_BAD_TCP_XSUM"
UL_v6_OL_v6_BAD_UDP_XSUM = "UL_v6_OL_v6_BAD_UDP_XSUM"
UL_v6_OL_v6_BAD_TCP_XSUM = "UL_v6_OL_v6_BAD_TCP_XSUM"
UL_v6_ZERO_UDP_XSUM_OL_v6_GOOD_UDP_XSUM = "UL_v6_ZERO_UDP_XSUM_OL_v6_GOOD_UDP_XSUM"
UL_v6_ZERO_UDP_XSUM_OL_v6_GOOD_TCP_XSUM = "UL_v6_ZERO_UDP_XSUM_OL_v6_GOOD_TCP_XSUM"
UL_IPv6_LEN_ERROR = "UL_IPv6_LEN_ERROR"
UL_v4_OL_v6_IPLEN_ERROR = "UL_v4_OL_v6_IPLEN_ERROR"
UL_v6_OL_v6_IPLEN_ERROR = "UL_v6_OL_v6_IPLEN_ERROR"
UL_GOOD_UDP_XSUM = "UL_GOOD_UDP_XSUM"
UL_GOOD_UDP_ZERO_XSUM = "UL_GOOD_UDP_ZERO_XSUM"
UL_GOOD_UDP_FFFF_XSUM = "UL_GOOD_UDP_FFFF_XSUM"
UL_GOOD_TCP_XSUM = "UL_GOOD_TCP_XSUM"
OL_VXLAN_GOOD_UDP_ZERO_XSUM = "OL_VXLAN_GOOD_UDP_ZERO_XSUM"
OL_VXLAN_GOOD_UDP_FFFF_XSUM = "OL_VXLAN_GOOD_UDP_FFFF_XSUM"
OL_VXLAN_GOOD_UDP_XSUM = "OL_VXLAN_GOOD_UDP_XSUM"
OL_VXLAN_GOOD_TCP_XSUM = "OL_VXLAN_GOOD_TCP_XSUM"
OL_MPLS_GOOD_UDP_ZERO_XSUM = "OL_MPLS_GOOD_UDP_ZERO_XSUM"
OL_MPLS_GOOD_UDP_XSUM = "OL_MPLS_GOOD_UDP_XSUM"
OL_MPLS_GOOD_TCP_XSUM = "OL_MPLS_GOOD_TCP_XSUM"
UL_GOOD_TCP_FFFF_XSUM = "UL_GOOD_TCP_FFFF_XSUM"
UL_GOOD_TCP_ZERO_XSUM = "UL_GOOD_TCP_ZERO_XSUM"
custom_headers = {UL_GOOD_UDP_ZERO_XSUM: ['00010001006E0000'],
                  UL_GOOD_UDP_FFFF_XSUM: ['000125B9', '006EFFFF'], OL_VXLAN_GOOD_UDP_FFFF_XSUM: ['0001F9D60008FFFF'],
                  UL_GOOD_TCP_FFFF_XSUM: ['0400f5fa0001e2400003944750021000ffff0000'],
                  UL_GOOD_TCP_ZERO_XSUM: ['0400f5fa0001e240000394475002100000000000']
                  }


def create_underlay_stream(template_obj, port, spirent_config, l4_header_type='UDP', l4_checksum=None,
                           ip_len_error=False, fixed_frame_length=300, load=bad_load):
    result = None
    try:
        l2_config = spirent_config["l2_config"]
        l3_config = spirent_config["l3_config"]["ipv6"]
        ether_type = Ethernet2Header.INTERNET_IPV6_ETHERTYPE
        streamblock_obj = StreamBlock(fixed_frame_length=fixed_frame_length, fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND, load=load,
                                      insert_signature=False)
        create_stream = template_obj.configure_stream_block(stream_block_obj=streamblock_obj,
                                                            port_handle=port, ip_header_version=6)
        fun_test.test_assert(create_stream, "Created streamblock %s" % streamblock_obj._spirent_handle)

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=streamblock_obj.spirent_handle,
                                                               source_mac=l2_config['source_mac'],
                                                               destination_mac=l2_config['destination_mac'],
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Configured mac address on stream")

        # Add ip header
        ipv6 = create_stream['ip_header_obj']
        # Adding Ip address and gateway
        ipv6.destAddr = l3_config['hu_destination_ip1']
        if flow_direction == NuConfigManager.FLOW_DIRECTION_HU_FPG:
            ipv6.destAddr = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_FPG:
            ipv6.destAddr = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_HNU:
            ipv6.destAddr = l3_config['hnu_destination_ip1']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_CC:
            ipv6.destAddr = l3_config['cc_destination_ip1']
        ipv6.sourceAddr = l3_config['source_ip1']
        if l4_header_type == 'TCP':
            ipv6.nextHeader = ipv6.NEXT_HEADER_TCP
            l4_header_obj = TCP()
        else:
            ipv6.nextHeader = ipv6.NEXT_HEADER_UDP
            l4_header_obj = UDP()

        if ip_len_error:
            ipv6.payloadLength = ipv6.PAYLOAD_LENGTH_ERROR
        ipv6_header = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=streamblock_obj._spirent_handle, header_obj=ipv6, update=True)
        fun_test.test_assert(ipv6_header, "Add ipv6 header to stream")

        if l4_checksum == 'error':
            l4_header_obj.checksum = l4_header_obj.CHECKSUM_ERROR
        elif l4_checksum:
            l4_header_obj.checksum = l4_checksum

        # ADD l4 header
        l4_add = template_obj.stc_manager.configure_frame_stack(stream_block_handle=streamblock_obj._spirent_handle,
                                                                header_obj=l4_header_obj)
        fun_test.test_assert(l4_add, "Added l4 header %s" % l4_header_obj._spirent_handle)
        result = streamblock_obj

    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def create_overlay_stream(template_obj, port, overlay_type, spirent_config, ul_ip_type=4, ul_l4_checksum=None, ol_l4_header='UDP',
                          ol_l4_checksum=None, ol_ip_len_error=False):
    result = None
    try:
        if ul_ip_type == 4:
            l3_config = spirent_config["l3_config"]["ipv4"]
            ip_header = Ipv4Header()
        else:
            l3_config = spirent_config["l3_config"]["ipv6"]
            ip_header = Ipv6Header()

        output = template_obj.configure_overlay_frame_stack(port=port,
                                                            overlay_type=overlay_type, streamblock_frame_length=300)

        streamblock_obj = output['streamblock_obj']
        destination = l3_config['hu_destination_ip1']
        if flow_direction == NuConfigManager.FLOW_DIRECTION_HU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_HNU:
            destination = l3_config['hnu_destination_ip1']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_CC:
            destination = l3_config['cc_destination_ip1']
        update = template_obj.update_overlay_frame_header(streamblock_obj=streamblock_obj,
                                                          header_obj=ip_header, overlay=False,
                                                          updated_header_attributes_dict=
                                                          {'destAddr': destination})
        fun_test.test_assert(update, message="Update ipv4 destination address in underlay")
        if ol_ip_len_error:
            ol_ip_v6_header = Ipv6Header()
            update = template_obj.update_overlay_frame_header(streamblock_obj=streamblock_obj,
                                                              header_obj=ol_ip_v6_header, overlay=True,
                                                              updated_header_attributes_dict=
                                                              {'payloadLength': ol_ip_v6_header.PAYLOAD_LENGTH_ERROR})
            fun_test.test_assert(update, message="Update ip len error in overlay")

        if ul_l4_checksum:
            ul_l4_header_obj = UDP()
            update = template_obj.update_overlay_frame_header(streamblock_obj=streamblock_obj,
                                                              header_obj=ul_l4_header_obj, overlay=False,
                                                              updated_header_attributes_dict=
                                                              {'checksum': ul_l4_checksum})
            fun_test.test_assert(update, message="Update l4 checksum to %s in underlay" % ul_l4_checksum)

        if ol_l4_checksum:
            if ol_l4_header == 'UDP':
                ol_l4_header_obj = UDP()
            else:
                ol_l4_header_obj = TCP()

            if ol_l4_checksum == 'error':
                ol_l4_checksum = '65535'

            update = template_obj.update_overlay_frame_header(streamblock_obj=streamblock_obj,
                                                              header_obj=ol_l4_header_obj, overlay=True,
                                                              updated_header_attributes_dict=
                                                              {'checksum': ol_l4_checksum})
            fun_test.test_assert(update, message="Update l4 checksum to %s in underlay" % ol_l4_checksum)

        streamblock_obj.Load = bad_load
        streamblock_obj.LoadUnit = streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        streamblock_obj.FillType = streamblock_obj.FILL_TYPE_CONSTANT

        stream_update = template_obj.configure_stream_block(stream_block_obj=streamblock_obj, update=True)
        fun_test.test_assert(stream_update,
                             message="Updated streamblock %s" % streamblock_obj._spirent_handle)
        result = output['streamblock_obj']

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
        global template_obj, port_1, port_2, gen_config_obj, \
            gen_obj_1, subscribe_results, dut_port_2, dut_port_1, network_controller_obj, \
            dut_config, spirent_config, l2_config, l3_config, dut_port_3, port_3, gen_obj_3

        dut_type = fun_test.get_local_setting(setting="dut_type")
        dut_config = nu_config_obj.read_dut_config(dut_type=dut_type,
                                                   flow_direction=flow_direction,
                                                   flow_type=NuConfigManager.VP_FLOW_TYPE)

        chassis_type = fun_test.get_local_setting(setting="chassis_type")
        spirent_config = nu_config_obj.read_traffic_generator_config()

        fun_test.log("Creating Template object")
        template_obj = SpirentEthernetTrafficTemplate(session_name="vp-negative-stream-ipv6", spirent_config=spirent_config,
                                                      chassis_type=chassis_type)
        fun_test.test_assert(template_obj, "Create template object")

        result = template_obj.setup(no_of_ports_needed=num_ports, flow_type=NuConfigManager.VP_FLOW_TYPE,
                                    flow_direction=flow_direction)
        fun_test.test_assert(result['result'], "Configure setup")

        port_1 = result['port_list'][0]
        port_2 = result['port_list'][1]
        port_3 = result['port_list'][2]

        dut_port_1 = dut_config['ports'][0]
        dut_port_2 = dut_config['ports'][1]
        dut_port_3 = dut_config['ports'][2]

        l2_config = spirent_config["l2_config"]
        l3_config = spirent_config["l3_config"]["ipv6"]

        # Configure Generator
        gen_config_obj = GeneratorConfig()
        gen_config_obj.SchedulingMode = gen_config_obj.SCHEDULING_MODE_RATE_BASED
        gen_config_obj.DurationMode = gen_config_obj.DURATION_MODE_SECONDS
        gen_config_obj.Duration = total_duration
        gen_config_obj.AdvancedInterleaving = True

        # Apply generator config on port 1
        gen_obj_1 = template_obj.stc_manager.get_generator(port_handle=port_1)
        gen_obj_3 = template_obj.stc_manager.get_generator(port_handle=port_3)
        config_obj = template_obj.configure_generator_config(port_handle=port_1,
                                                             generator_config_obj=gen_config_obj)
        fun_test.test_assert(config_obj, "Creating generator config on port %s" % port_1)
        config_obj = template_obj.configure_generator_config(port_handle=port_3,
                                                             generator_config_obj=gen_config_obj)
        fun_test.test_assert(config_obj, "Creating generator config on port %s" % port_3)

        # Applying configuration
        apply = template_obj.stc_manager.apply_configuration()
        fun_test.test_assert(apply, "Applying Generator config")

        # Subscribe to results
        project = template_obj.stc_manager.get_project_handle()
        subscribe_results = template_obj.subscribe_to_all_results(parent=project)
        fun_test.test_assert(subscribe_results['result'], "Subscribing to results")
        del subscribe_results['result']

        if dut_config['enable_dpcsh']:
            # Create network controller object
            dpcsh_server_ip = dut_config["dpcsh_tcp_proxy_ip"]
            dpcsh_server_port = dut_config['dpcsh_tcp_proxy_port']
            network_controller_obj = NetworkController(dpc_server_ip=dpcsh_server_ip, dpc_server_port=dpcsh_server_port)

    def cleanup(self):
        fun_test.test_assert(template_obj.cleanup(), "Cleaning up session")


class Ulv6BadUdpXsum(FunTestCase):
    current_stream = UL_v6_BAD_UDP_XSUM
    current_streamblock_obj = None
    expected_rx_count = 0

    def describe(self):
        self.set_test_details(
            id=1,summary="Test VP path FPG-HU with packet UL_v6_BAD_UDP_XSUM",
            steps="""
            1. Disable all streams and Enable stream UL_v6_BAD_UDP_XSUM
            2. Start traffic for 10 seconds
            3. Check counter on spirent rx. It must be 0 as DUT would drop packet with checksum error
            4. Check mac stats. No frames must be transmitted out of dut.
            5. Check erp stats for checksum/ip total len errors.
            """)

    def setup(self):
        # Deactivate all streamblocks
        if not self.current_stream == UL_v6_BAD_UDP_XSUM:
            deactivate = template_obj.deactivate_stream_blocks()
            fun_test.test_assert(deactivate, "Deactivated all streamblocks")

        self.current_streamblock_obj = create_underlay_stream(template_obj=template_obj, port=port_1,
                                                              spirent_config=spirent_config, l4_checksum='error')
        fun_test.test_assert(self.current_streamblock_obj, "Stream %s created" % self.current_stream)
        stream_objs['bad'][self.current_stream] = self.current_streamblock_obj

    def run(self):

        fun_test.test_assert(True, "Execute tc")

        current_streamblock_handle = self.current_streamblock_obj._spirent_handle

        if dut_config['enable_dpcsh']:
            # Clear port results on DUT
            clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
            fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

            clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
            fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

            # Get stats before starting traffic
            fun_test.log("Get stats before starting traffic")
            wro_stats_1 = network_controller_obj.peek_wro_global_stats()
            parser_stats_1 = network_controller_obj.peek_parser_stats()
            vp_pkts_stats_1 = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)
            erp_stats_1 = get_erp_stats_values(network_controller_obj=network_controller_obj)
            psw_stats_1 = network_controller_obj.peek_psw_global_stats()

        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=[gen_obj_1])
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic for seconds", seconds=total_duration + 2)

        # Stop traffic
        stop = template_obj.disable_generator_configs(generator_configs=[gen_obj_1])
        fun_test.test_assert(stop, "Stop generator config")

        # Asserts
        stream_result_dict = template_obj.stc_manager.fetch_streamblock_results(subscribe_result=subscribe_results,
                                                                                streamblock_handle_list=
                                                                                [current_streamblock_handle],
                                                                                tx_result=True, rx_result=False)

        port_result_dict = template_obj.stc_manager.fetch_port_results(subscribe_result=subscribe_results,
                                                                       port_handle_list=[port_2],
                                                                       analyzer_result=True)

        # Get DUT mac stats
        tx_results_1 = stream_result_dict[current_streamblock_handle]['tx_result']
        port_2_analyzer_result = port_result_dict[port_2]['analyzer_result']

        fun_test.log(tx_results_1)
        fun_test.log(port_2_analyzer_result)

        if dut_config['enable_dpcsh']:
            fun_test.log("Get stats before starting traffic")
            vp_pkts_stats_2 = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)
            erp_stats_2 = get_erp_stats_values(network_controller_obj=network_controller_obj)
            psw_stats_2 = network_controller_obj.peek_psw_global_stats()
            wro_stats_2 = network_controller_obj.peek_wro_global_stats()

            dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1)
            fun_test.test_assert(dut_port_1_results, message="Ensure stats are obtained for %s" % dut_port_1)
            dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2)
            fun_test.test_assert(dut_port_2_results, message="Ensure stats are obtained for %s" % dut_port_2)

            dut_port_2_transmit = get_dut_output_stats_value(dut_port_2_results, FRAMES_TRANSMITTED_OK)
            dut_port_1_receive = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)

            # Check on DUT
            fun_test.test_assert(not dut_port_2_transmit, "Ensure no frames are sent out from dut port to spirent")

            fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']), actual=int(dut_port_1_receive),
                                          message="Ensure all frames transmitted from spirent are seen on ingress dut")

            check_ip_len_counter = None
            if self.current_stream in [UL_IPv6_LEN_ERROR]:
                check_ip_len_counter = ERP_COUNT_PACKETS_OUTER_IP_LEN_ERROR
            elif self.current_stream in [UL_v4_OL_v6_IPLEN_ERROR, UL_v6_OL_v6_IPLEN_ERROR]:
                check_ip_len_counter = ERP_COUNT_PACKETS_INNER_IP_LEN_ERROR
            else:
                check_layer4_cs_error_counter = ERP_COUNT_PACKETS_INNER_LAYER4_CS_ERROR
                if self.current_stream in [UL_v6_BAD_TCP_XSUM, UL_v6_BAD_UDP_ZERO_XSUM, UL_v6_BAD_UDP_XSUM,
                                           UL_v6_ZERO_UDP_XSUM_OL_v6_GOOD_TCP_XSUM, UL_v6_ZERO_UDP_XSUM_OL_v6_GOOD_UDP_XSUM]:
                    check_layer4_cs_error_counter = ERP_COUNT_PACKETS_OUTER_LAYER4_CS_ERROR
                if check_layer4_cs_error_counter in erp_stats_1:
                    actual = int(erp_stats_2[check_layer4_cs_error_counter]) - int(erp_stats_1[check_layer4_cs_error_counter])
                else:
                    actual = int(erp_stats_2[check_layer4_cs_error_counter])
                fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']),
                                              actual=actual,
                                              message="Check stats %s in erp stats" % check_layer4_cs_error_counter)
            if check_ip_len_counter:
                if check_ip_len_counter in erp_stats_1:
                    actual = int(erp_stats_2[check_ip_len_counter]) - int(erp_stats_1[check_ip_len_counter])
                else:
                    actual = int(erp_stats_2[check_ip_len_counter])
                fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']),
                                              actual=actual,
                                              message="Check stats %s in erp stats" % check_ip_len_counter)

        # ASSERTS
        # Spirent asserts
        fun_test.test_assert(int(tx_results_1['FrameCount']) > 1, message="Ensure some traffic is sent")

        fun_test.test_assert_expected(expected=self.expected_rx_count,
                                      actual=int(port_2_analyzer_result['TotalFrameCount']),
                                      message="Ensure no frames are received as packet is %s " % self.current_stream)

    def cleanup(self):
        fun_test.log("In testcase cleanup")

        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])


class Ulv6BadUdpZeroXsum(Ulv6BadUdpXsum):
    current_stream = UL_v6_BAD_UDP_ZERO_XSUM
    checksum = '0'

    def describe(self):
        self.set_test_details(
            id=2,summary="Test VP path FPG-HU with packet UL_v6_BAD_UDP_ZERO_XSUM",
            steps="""
            1. Disable all streams and Enable stream UL_v6_BAD_UDP_ZERO_XSUM
            2. Start traffic for 10 seconds
            3. Check counter on spirent rx. It must be 0 as DUT would drop packet with checksum 0
            4. Check mac stats. No frames must be transmitted out of dut.
            5. Check erp stats for checksum/ip total len errors.
            """)

    def setup(self):
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivated all streamblocks")

        self.current_streamblock_obj = create_underlay_stream(template_obj=template_obj, port=port_1,
                                                              spirent_config=spirent_config,
                                                              l4_checksum=self.checksum)
        fun_test.test_assert(self.current_streamblock_obj, "Stream %s created" % self.current_stream)
        stream_objs['bad'][self.current_stream] = self.current_streamblock_obj

    def run(self):
        super(Ulv6BadUdpZeroXsum, self).run()

    def cleanup(self):
        super(Ulv6BadUdpZeroXsum, self).cleanup()


class Ulv6BadTcpXsum(Ulv6BadUdpXsum):
    current_stream = UL_v6_BAD_TCP_XSUM

    def describe(self):
        self.set_test_details(
            id=3,summary="Test VP path FPG-HU with packet UL_v6_BAD_TCP_XSUM",
            steps="""
            1. Disable all streams and Enable stream UL_v6_BAD_TCP_XSUM
            2. Start traffic for 10 seconds
            3. Check counter on spirent rx. It must be 0 as DUT would drop packet with checksum error
            4. Check mac stats. No frames must be transmitted out of dut.
            5. Check erp stats for checksum/ip total len errors.
            """)

    def setup(self):
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivated all streamblocks")

        self.current_streamblock_obj = create_underlay_stream(template_obj=template_obj, port=port_1,
                                                              spirent_config=spirent_config,
                                                              l4_header_type='TCP', l4_checksum='error')
        fun_test.test_assert(self.current_streamblock_obj, "Stream %s created" % self.current_stream)
        stream_objs['bad'][self.current_stream] = self.current_streamblock_obj

    def run(self):
        super(Ulv6BadTcpXsum, self).run()

    def cleanup(self):
        super(Ulv6BadTcpXsum, self).cleanup()


class Ulv4Olv6BadUdpXsum(Ulv6BadUdpXsum):
    current_stream = UL_v4_OL_v6_BAD_UDP_XSUM

    def describe(self):
        self.set_test_details(
            id=4,summary="Test VP path FPG-HU with packet UL_v4_OL_v6_BAD_UDP_XSUM",
            steps="""
            1. Disable all streams and Enable stream UL_v4_OL_v6_BAD_UDP_XSUM
            2. Start traffic for 10 seconds
            3. Check counter on spirent rx. It must be 0 as DUT would drop packet with checksum 0
            4. Check mac stats. No frames must be transmitted out of dut.
            5. Check erp stats for checksum/ip total len errors.
            """)

    def setup(self):
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivated all streamblocks")

        self.current_streamblock_obj = create_overlay_stream(template_obj=template_obj, port=port_1,
                                                                        overlay_type=template_obj.ETH_IPV4_UDP_VXLAN_ETH_IPV6_UDP,
                                                                        spirent_config=spirent_config, ol_l4_checksum='error')
        fun_test.test_assert(self.current_streamblock_obj, "Stream %s created" % self.current_stream)
        stream_objs['bad'][self.current_stream] = self.current_streamblock_obj

    def run(self):
        super(Ulv4Olv6BadUdpXsum, self).run()

    def cleanup(self):
        super(Ulv4Olv6BadUdpXsum, self).cleanup()


class Ulv4ZeroUdpXsumOlv6ZeroUdpXsum(Ulv6BadUdpXsum):
    current_stream = UL_v4_ZERO_UDP_XSUM_OL_v6_ZERO_UDP_XSUM

    def describe(self):
        self.set_test_details(
            id=5, summary="Test VP path FPG-HU with packet UL_v4_ZERO_UDP_XSUM_OL_v6_ZERO_UDP_XSUM",
            steps="""
            1. Disable all streams and Enable stream UL_v4_ZERO_UDP_XSUM_OL_v6_ZERO_UDP_XSUM
            2. Start traffic for 10 seconds
            3. Check counter on spirent rx. It must be 0 as DUT would drop packet with checksum 0
            4. Check mac stats. No frames must be transmitted out of dut.
            5. Check erp stats for checksum/ip total len errors.
            """)

    def setup(self):
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivated all streamblocks")

        self.current_streamblock_obj = create_overlay_stream(template_obj=template_obj, port=port_1,
                                                             overlay_type=template_obj.ETH_IPV4_UDP_VXLAN_ETH_IPV6_UDP,
                                                             ul_l4_checksum='0',
                                                             spirent_config=spirent_config,
                                                             ol_l4_checksum='0')
        fun_test.test_assert(self.current_streamblock_obj, "Stream %s created" % self.current_stream)
        stream_objs['bad'][self.current_stream] = self.current_streamblock_obj

    def run(self):
        super(Ulv4ZeroUdpXsumOlv6ZeroUdpXsum, self).run()

    def cleanup(self):
        super(Ulv4ZeroUdpXsumOlv6ZeroUdpXsum, self).cleanup()


class Ulv4ZeroUdpXsumOlv6BadTcpXsum(Ulv6BadUdpXsum):
    current_stream = UL_v4_ZERO_UDP_XSUM_OL_v6_BAD_TCP_XSUM

    def describe(self):
        self.set_test_details(
            id=6, summary="Test VP path FPG-HU with packet UL_v4_ZERO_UDP_XSUM_OL_v6_BAD_TCP_XSUM",
            steps="""
            1. Disable all streams and Enable stream UL_v4_ZERO_UDP_XSUM_OL_v6_BAD_TCP_XSUM
            2. Start traffic for 10 seconds
            3. Check counter on spirent rx. It must be 0 as DUT would drop packet with checksum 0
            4. Check mac stats. No frames must be transmitted out of dut.
            5. Check erp stats for checksum/ip total len errors.
            """)

    def setup(self):
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivated all streamblocks")

        self.current_streamblock_obj = create_overlay_stream(template_obj=template_obj, port=port_1,
                                                             overlay_type=template_obj.ETH_IPV4_UDP_VXLAN_ETH_IPV6_TCP,
                                                             ul_l4_checksum='0',
                                                             spirent_config=spirent_config,
                                                             ol_l4_checksum='error',
                                                             ol_l4_header='TCP')
        fun_test.test_assert(self.current_streamblock_obj, "Stream %s created" % self.current_stream)
        stream_objs['bad'][self.current_stream] = self.current_streamblock_obj

    def run(self):
        super(Ulv4ZeroUdpXsumOlv6BadTcpXsum, self).run()

    def cleanup(self):
        super(Ulv4ZeroUdpXsumOlv6BadTcpXsum, self).cleanup()


class Ulv6Olv6BadUdpXsum(Ulv6BadUdpXsum):
    current_stream = UL_v6_OL_v6_BAD_UDP_XSUM

    def describe(self):
        self.set_test_details(
            id=7, summary="Test VP path FPG-HU with packet UL_v6_OL_v6_BAD_UDP_XSUM",
            steps="""
            1. Disable all streams and Enable stream UL_v6_OL_v6_BAD_UDP_XSUM
            2. Start traffic for 10 seconds
            3. Check counter on spirent rx. It must be 0 as DUT would drop packet with checksum 0
            4. Check mac stats. No frames must be transmitted out of dut.
            5. Check erp stats for checksum/ip total len errors.
            """)

    def setup(self):
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivated all streamblocks")

        self.current_streamblock_obj = create_overlay_stream(template_obj=template_obj, port=port_1,
                                                             overlay_type=template_obj.ETH_IPV6_UDP_VXLAN_ETH_IPV6_UDP,
                                                             spirent_config=spirent_config,
                                                             ol_l4_checksum='error',
                                                             ul_ip_type=6)
        fun_test.test_assert(self.current_streamblock_obj, "Stream %s created" % self.current_stream)
        stream_objs['bad'][self.current_stream] = self.current_streamblock_obj

    def run(self):
        super(Ulv6Olv6BadUdpXsum, self).run()

    def cleanup(self):
        super(Ulv6Olv6BadUdpXsum, self).cleanup()


class Ulv6Olv6BadTcpXsum(Ulv6BadUdpXsum):
    current_stream = UL_v6_OL_v6_BAD_TCP_XSUM

    def describe(self):
        self.set_test_details(
            id=8, summary="Test VP path FPG-HU with packet UL_v6_OL_v6_BAD_TCP_XSUM",
            steps="""
            1. Disable all streams and Enable stream UL_v6_OL_v6_BAD_TCP_XSUM
            2. Start traffic for 10 seconds
            3. Check counter on spirent rx. It must be 0 as DUT would drop packet with checksum 0
            4. Check mac stats. No frames must be transmitted out of dut.
            5. Check erp stats for checksum/ip total len errors.
            """)

    def setup(self):
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivated all streamblocks")

        self.current_streamblock_obj = create_overlay_stream(template_obj=template_obj, port=port_1,
                                                             overlay_type=template_obj.ETH_IPV6_UDP_VXLAN_ETH_IPV6_TCP,
                                                             spirent_config=spirent_config,
                                                             ol_l4_checksum='error',
                                                             ol_l4_header='TCP',
                                                             ul_ip_type=6)
        fun_test.test_assert(self.current_streamblock_obj, "Stream %s created" % self.current_stream)
        stream_objs['bad'][self.current_stream] = self.current_streamblock_obj

    def run(self):
        super(Ulv6Olv6BadTcpXsum, self).run()

    def cleanup(self):
        super(Ulv6Olv6BadTcpXsum, self).cleanup()


class Ulv6ZeroUdpXsumOlv6GoodUdpXsum(Ulv6BadUdpXsum):
    current_stream = UL_v6_ZERO_UDP_XSUM_OL_v6_GOOD_UDP_XSUM

    def describe(self):
        self.set_test_details(
            id=9, summary="Test VP path FPG-HU with packet UL_v6_ZERO_UDP_XSUM_OL_v6_GOOD_UDP_XSUM",
            steps="""
            1. Disable all streams and Enable stream UL_v6_ZERO_UDP_XSUM_OL_v6_GOOD_UDP_XSUM
            2. Start traffic for 10 seconds
            3. Check counter on spirent rx. It must be 0 as DUT would drop packet
            4. Check mac stats. No frames must be transmitted out of dut.
            5. Check erp stats for checksum/ip total len errors.
            """)

    def setup(self):
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivated all streamblocks")

        self.current_streamblock_obj = create_overlay_stream(template_obj=template_obj, port=port_1,
                                                             overlay_type=template_obj.ETH_IPV6_UDP_VXLAN_ETH_IPV6_UDP,
                                                             spirent_config=spirent_config,
                                                             ol_l4_checksum=None,
                                                             ul_ip_type=6,
                                                             ul_l4_checksum='0')
        fun_test.test_assert(self.current_streamblock_obj, "Stream %s created" % self.current_stream)
        stream_objs['bad'][self.current_stream] = self.current_streamblock_obj

    def run(self):
        super(Ulv6ZeroUdpXsumOlv6GoodUdpXsum, self).run()

    def cleanup(self):
        super(Ulv6ZeroUdpXsumOlv6GoodUdpXsum, self).cleanup()


class Ulv6ZeroUdpXsumOlv6GoodTcpXsum(Ulv6BadUdpXsum):
    current_stream = UL_v6_ZERO_UDP_XSUM_OL_v6_GOOD_TCP_XSUM

    def describe(self):
        self.set_test_details(
            id=10, summary="Test VP path FPG-HU with packet UL_v6_ZERO_UDP_XSUM_OL_v6_GOOD_TCP_XSUM",
            steps="""
            1. Disable all streams and Enable stream UL_v6_ZERO_UDP_XSUM_OL_v6_GOOD_TCP_XSUM
            2. Start traffic for 10 seconds
            3. Check counter on spirent rx. It must be 0 as DUT would drop packet
            4. Check mac stats. No frames must be transmitted out of dut.
            5. Check erp stats for checksum/ip total len errors.
            """)

    def setup(self):
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivated all streamblocks")

        self.current_streamblock_obj = create_overlay_stream(template_obj=template_obj, port=port_1,
                                                             overlay_type=template_obj.ETH_IPV6_UDP_VXLAN_ETH_IPV6_TCP,
                                                             spirent_config=spirent_config,
                                                             ol_l4_checksum=None,
                                                             ul_ip_type=6,
                                                             ul_l4_checksum='0',
                                                             ol_l4_header='TCP')
        fun_test.test_assert(self.current_streamblock_obj, "Stream %s created" % self.current_stream)
        stream_objs['bad'][self.current_stream] = self.current_streamblock_obj

    def run(self):
        super(Ulv6ZeroUdpXsumOlv6GoodTcpXsum, self).run()

    def cleanup(self):
        super(Ulv6ZeroUdpXsumOlv6GoodTcpXsum, self).cleanup()


class UlIpv6LenError(Ulv6BadUdpXsum):
    current_stream = UL_IPv6_LEN_ERROR

    def describe(self):
        self.set_test_details(
            id=11, summary="Test VP path FPG-HU with packet UL_IPv6_LEN_ERROR",
            steps="""
            1. Disable all streams and Enable stream UL_IPv6_LEN_ERROR
            2. Start traffic for 10 seconds
            3. Check counter on spirent rx. It must be 0 as DUT would drop packet
            4. Check mac stats. No frames must be transmitted out of dut.
            5. Check erp stats for checksum/ip total len errors.
            """)

    def setup(self):
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivated all streamblocks")

        self.current_streamblock_obj = create_underlay_stream(template_obj=template_obj, port=port_1,
                                                              spirent_config=spirent_config, ip_len_error=True,
                                                              l4_checksum=None)
        fun_test.test_assert(self.current_streamblock_obj, "Stream %s created" % self.current_stream)
        stream_objs['bad'][self.current_stream] = self.current_streamblock_obj

    def run(self):
        super(UlIpv6LenError, self).run()

    def cleanup(self):
        super(UlIpv6LenError, self).cleanup()


class Ulv4Olv6IpLenError(Ulv6BadUdpXsum):
    current_stream = UL_v4_OL_v6_IPLEN_ERROR

    def describe(self):
        self.set_test_details(
            id=12, summary="Test VP path FPG-HU with packet UL_v4_OL_v6_IPLEN_ERROR",
            steps="""
            1. Disable all streams and Enable stream UL_v4_OL_v6_IPLEN_ERROR
            2. Start traffic for 10 seconds
            3. Check counter on spirent rx. It must be 0 as DUT would drop packet
            4. Check mac stats. No frames must be transmitted out of dut.
            5. Check erp stats for checksum/ip total len errors.
            """)

    def setup(self):
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivated all streamblocks")

        self.current_streamblock_obj = create_overlay_stream(template_obj=template_obj, port=port_1,
                                                             overlay_type=template_obj.ETH_IPV4_UDP_VXLAN_ETH_IPV6_TCP,
                                                             spirent_config=spirent_config,
                                                             ol_l4_checksum=None,
                                                             ul_ip_type=4,
                                                             ul_l4_checksum='0',
                                                             ol_l4_header='TCP',
                                                             ol_ip_len_error=True)
        stream_objs['bad'][self.current_stream] = self.current_streamblock_obj

    def run(self):
        super(Ulv4Olv6IpLenError, self).run()

    def cleanup(self):
        super(Ulv4Olv6IpLenError, self).cleanup()


class Ulv6Olv6IpLenError(Ulv6BadUdpXsum):
    current_stream = UL_v6_OL_v6_IPLEN_ERROR

    def describe(self):
        self.set_test_details(
            id=13, summary="Test VP path FPG-HU with packet UL_v6_OL_v6_IPLEN_ERROR",
            steps="""
            1. Disable all streams and Enable stream UL_v6_OL_v6_IPLEN_ERROR
            2. Start traffic for 10 seconds
            3. Check counter on spirent rx. It must be 0 as DUT would drop packet
            4. Check mac stats. No frames must be transmitted out of dut.
            5. Check erp stats for checksum/ip total len errors.
            """)

    def setup(self):
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivated all streamblocks")

        self.current_streamblock_obj = create_overlay_stream(template_obj=template_obj, port=port_1,
                                                             overlay_type=template_obj.ETH_IPV6_UDP_VXLAN_ETH_IPV6_UDP,
                                                             spirent_config=spirent_config,
                                                             ol_l4_checksum=None,
                                                             ul_ip_type=6,
                                                             ol_ip_len_error=True)
        stream_objs['bad'][self.current_stream] = self.current_streamblock_obj

    def run(self):
        super(Ulv6Olv6IpLenError, self).run()

    def cleanup(self):
        super(Ulv6Olv6IpLenError, self).cleanup()


class GoodBad(FunTestCase):
    current_streamblock_obj = None

    def describe(self):
        self.set_test_details(id=14,
                              summary="Test VP path FPG-HU with packet good and bad packets",
                              steps="""
                              1. Enable all streams.
                              2. Start traffic for 10 seconds
                              3. Packets with errors must be dropped
                              4. Check dut has transmitted packets that are good.
                              5. Check spirent tx and rx results
                              """)

    def setup(self):
        # Enable stream
        activate = template_obj.activate_stream_blocks()
        fun_test.test_assert(activate, "Activate all streamblocks")

    def cleanup(self):
        pass

    def create_common_streamblock(self, protocol_tcp=False, src_ip=None, frame_length=148, insert_sig=False):
        # Streamblock
        self.current_streamblock_obj = StreamBlock(load=good_load, load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND,
                                                   fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                                   fixed_frame_length=frame_length, insert_signature=insert_sig)

        streamblock_obj = template_obj.configure_stream_block(stream_block_obj=self.current_streamblock_obj,
                                                              port_handle=port_3)
        fun_test.test_assert(streamblock_obj, "Create streamblock")
        # MAC
        configure_mac = template_obj.stc_manager.configure_mac_address(
            streamblock=self.current_streamblock_obj._spirent_handle,
            source_mac=l2_config['source_mac'],
            destination_mac=l2_config['destination_mac'])
        fun_test.test_assert(configure_mac, "Configure mac address")

        protocol = Ipv4Header.PROTOCOL_TYPE_UDP
        if protocol_tcp:
            protocol = Ipv4Header.PROTOCOL_TYPE_TCP
        l3_config = spirent_config["l3_config"]["ipv4"]
        destination = l3_config['hu_destination_ip1']
        if flow_direction == NuConfigManager.FLOW_DIRECTION_HU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_HNU:
            destination = l3_config['hnu_destination_ip1']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_CC:
            destination = l3_config['cc_destination_ip1']
        ip_header = Ipv4Header(destination_address=destination,
                               protocol=protocol, source_address=src_ip)
        configure_ip = template_obj.stc_manager.configure_frame_stack(stream_block_handle=
                                                                      self.current_streamblock_obj._spirent_handle,
                                                                      header_obj=ip_header,
                                                                      delete_header=[ip_header.HEADER_TYPE])
        fun_test.test_assert(configure_ip, "Configure IP header")
        return self.current_streamblock_obj

    def run(self):
        error_stream_handle_list = []
        for stream in stream_objs['bad'].values():
            # Update load for bad streams
            stream.load = aggregate_bad_load
            stream_update = template_obj.configure_stream_block(stream_block_obj=stream,
                                                                update=True)
            fun_test.test_assert(stream_update,
                                 message="Updated bad load in streamblock %s" % stream._spirent_handle)
            error_stream_handle_list.append(stream._spirent_handle)
        good_stream_handle_list = []

        # Add streams here
        fun_test.log("========= NEW GOOD STREAM =========")
        self.current_streamblock_obj = None
        current_stream = UL_GOOD_UDP_XSUM
        self.current_streamblock_obj = self.create_common_streamblock()
        fun_test.simple_assert(self.current_streamblock_obj, "Ensure streamblock handle is mnot none")
        udp = UDP()
        configure_udp_header = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=self.current_streamblock_obj._spirent_handle, header_obj=udp)
        fun_test.test_assert(configure_udp_header, "Configure udp header")
        fun_test.test_assert(self.current_streamblock_obj, "Stream %s created" % current_stream)
        stream_objs['good'][current_stream] = self.current_streamblock_obj

        fun_test.log("========= NEW GOOD STREAM =========")
        self.current_streamblock_obj = None
        fun_test.log("Create stream %s" % UL_GOOD_UDP_ZERO_XSUM)
        self.current_streamblock_obj = self.create_common_streamblock()
        custom_header_1 = CustomBytePatternHeader(byte_pattern=custom_headers[UL_GOOD_UDP_ZERO_XSUM][0])
        configure_cust_header = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=self.current_streamblock_obj._spirent_handle, header_obj=custom_header_1)
        fun_test.test_assert(configure_cust_header, "Configure custom header")
        stream_objs['good'][UL_GOOD_UDP_ZERO_XSUM] = self.current_streamblock_obj

        fun_test.log("========= NEW GOOD STREAM =========")
        self.current_streamblock_obj = None
        fun_test.log("Create stream %s" % UL_GOOD_UDP_FFFF_XSUM)
        self.current_streamblock_obj = self.create_common_streamblock()
        for byte_pattern in custom_headers[UL_GOOD_UDP_FFFF_XSUM]:
            cust_header = CustomBytePatternHeader(byte_pattern=byte_pattern)
            configure_cust_header = template_obj.stc_manager.configure_frame_stack(
                stream_block_handle=self.current_streamblock_obj._spirent_handle, header_obj=cust_header)
            fun_test.test_assert(configure_cust_header, "Configure custom header")

            modifier_needed = False
            if byte_pattern == '000125B9':
                modifier_needed = True
                recycle_count = 1
                step = '00000000'
                mask = 'FFFFFFFF'
                data = byte_pattern
            if modifier_needed:
                range_obj = RangeModifier(recycle_count=recycle_count, step_value=step, data=data, mask=mask)
                modify_attribute = 'pattern'
                create_range = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=range_obj,
                                                                                 streamblock_obj=self.current_streamblock_obj,
                                                                                 header_obj=cust_header,
                                                                                 header_attribute=modify_attribute,
                                                                                 custom_header=True)
                fun_test.test_assert(create_range, "Ensure range modifier created on %s for attribute %s"
                                     % (cust_header._spirent_handle, modify_attribute))
        ipv4 = Ipv4Header()
        update = template_obj.update_overlay_frame_header(streamblock_obj=self.current_streamblock_obj,
                                                          header_obj=ipv4, overlay=False,
                                                          updated_header_attributes_dict=
                                                          {'gateway': '192.85.1.1'})
        fun_test.test_assert(update, message="Update gateway in ip header")

        update = template_obj.update_overlay_frame_header(streamblock_obj=self.current_streamblock_obj,
                                                          header_obj=ipv4, overlay=False,
                                                          updated_header_attributes_dict=
                                                          {'sourceAddr': '192.85.1.2'})
        fun_test.test_assert(update, message="Reapplying source addr in ip header")

        self.current_streamblock_obj.FillType = StreamBlock.FILL_TYPE_CONSTANT
        self.current_streamblock_obj.InsertSig = False
        stream_update = template_obj.configure_stream_block(stream_block_obj=self.current_streamblock_obj, update=True)
        fun_test.test_assert(stream_update,
                             message="Updated streamblock %s" % self.current_streamblock_obj._spirent_handle)

        stream_objs['good'][UL_GOOD_UDP_FFFF_XSUM] = self.current_streamblock_obj

        fun_test.log("========= NEW GOOD STREAM =========")
        self.current_streamblock_obj = None
        fun_test.log("Create stream %s" % UL_GOOD_TCP_XSUM)
        self.current_streamblock_obj = self.create_common_streamblock(protocol_tcp=True)
        tcp = TCP()
        configure_cust_header = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=self.current_streamblock_obj._spirent_handle, header_obj=tcp)
        fun_test.test_assert(configure_cust_header, "Configure tcp header")

        # Add Range Modifier
        recycle_count = 10
        step = 1
        mask = 15
        data = 5
        range_obj = RangeModifier(recycle_count=recycle_count, step_value=step, data=data, mask=mask)
        modify_attribute = 'offset'
        create_range = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=range_obj,
                                                                         streamblock_obj=self.current_streamblock_obj,
                                                                         header_obj=tcp,
                                                                         header_attribute=modify_attribute,
                                                                         custom_header=False)
        fun_test.test_assert(create_range, "Ensure range modifier created for attribute %s"
                             % modify_attribute)
        stream_objs['good'][UL_GOOD_TCP_XSUM] = self.current_streamblock_obj

        fun_test.log("========= NEW GOOD STREAM =========")
        self.current_streamblock_obj = None
        fun_test.log("Create stream %s" % OL_VXLAN_GOOD_UDP_ZERO_XSUM)
        output = template_obj.configure_overlay_frame_stack(port=port_3,
                                                            overlay_type=template_obj.ETH_IPV4_UDP_VXLAN_ETH_IPV4_UDP)
        l3_config = spirent_config["l3_config"]["ipv4"]
        ip_header = Ipv4Header()
        destination = l3_config['hu_destination_ip1']
        if flow_direction == NuConfigManager.FLOW_DIRECTION_HU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_HNU:
            destination = l3_config['hnu_destination_ip1']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_CC:
            destination = l3_config['cc_destination_ip1']
        update = template_obj.update_overlay_frame_header(streamblock_obj=output['streamblock_obj'],
                                                          header_obj=ip_header, overlay=False,
                                                          updated_header_attributes_dict=
                                                          {'destAddr': destination})
        fun_test.test_assert(update, message="Update ipv4 destination address in underlay")

        udp = UDP()
        update = template_obj.update_overlay_frame_header(streamblock_obj=output['streamblock_obj'],
                                                          header_obj=udp, overlay=False,
                                                          updated_header_attributes_dict=
                                                          {'checksum': '0000'})
        fun_test.test_assert(update, message="Update udp checksum to 0000 in overlay")
        update = template_obj.update_overlay_frame_header(streamblock_obj=output['streamblock_obj'],
                                                          header_obj=udp, overlay=True,
                                                          updated_header_attributes_dict=
                                                          {'checksum': '0000'})
        fun_test.test_assert(update, message="Update udp checksum to 0000 in overlay")

        # Update streamblock
        self.current_streamblock_obj = output['streamblock_obj']
        self.current_streamblock_obj.Load = good_load
        self.current_streamblock_obj.LoadUnit = self.current_streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        self.current_streamblock_obj.FillType = self.current_streamblock_obj.FILL_TYPE_CONSTANT
        self.current_streamblock_obj.FixedFrameLength = 148
        self.current_streamblock_obj.InsertSig = True

        stream_update = template_obj.configure_stream_block(stream_block_obj=self.current_streamblock_obj, update=True)
        fun_test.test_assert(stream_update,
                             message="Updated streamblock %s" % self.current_streamblock_obj._spirent_handle)

        stream_objs['good'][OL_VXLAN_GOOD_UDP_ZERO_XSUM] = self.current_streamblock_obj

        fun_test.log("========= NEW GOOD STREAM =========")
        self.current_streamblock_obj = None
        fun_test.log("Create stream %s" % OL_VXLAN_GOOD_UDP_FFFF_XSUM)
        self.current_streamblock_obj = self.create_common_streamblock()
        udp = UDP(destination_port=4789)
        configure_cust_header = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=self.current_streamblock_obj._spirent_handle, header_obj=udp)
        fun_test.test_assert(configure_cust_header, "Configure udp header")

        vxlan = VxLAN()
        configure_cust_header = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=self.current_streamblock_obj._spirent_handle, header_obj=vxlan)
        fun_test.test_assert(configure_cust_header, "Configure vxlan header")

        ethernet = Ethernet2Header()
        configure_cust_header = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=self.current_streamblock_obj._spirent_handle, header_obj=ethernet)
        fun_test.test_assert(configure_cust_header, "Configure ethernet header")

        ip_header = Ipv4Header(source_address='1.1.1.1', destination_address='2.2.2.3',
                               protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
        configure_cust_header = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=self.current_streamblock_obj._spirent_handle, header_obj=ip_header)
        fun_test.test_assert(configure_cust_header, "Configure ip header")

        for byte_pattern in custom_headers[OL_VXLAN_GOOD_UDP_FFFF_XSUM]:
            cust_header = CustomBytePatternHeader(byte_pattern=byte_pattern)
            configure_cust_header = template_obj.stc_manager.configure_frame_stack(
                stream_block_handle=self.current_streamblock_obj._spirent_handle, header_obj=cust_header)
            fun_test.test_assert(configure_cust_header, "Configure custom header")

        # Update streamblock
        self.current_streamblock_obj.Load = good_load
        self.current_streamblock_obj.LoadUnit = self.current_streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        self.current_streamblock_obj.FillType = self.current_streamblock_obj.FILL_TYPE_CONSTANT
        self.current_streamblock_obj.FixedFrameLength = 148
        self.current_streamblock_obj.InsertSig = True

        stream_update = template_obj.configure_stream_block(stream_block_obj=self.current_streamblock_obj,
                                                            update=True)
        fun_test.test_assert(stream_update,
                             message="Updated streamblock %s" % self.current_streamblock_obj._spirent_handle)
        stream_objs['good'][OL_VXLAN_GOOD_UDP_FFFF_XSUM] = self.current_streamblock_obj
        
        fun_test.log("========= NEW GOOD STREAM =========")
        self.current_streamblock_obj = None
        fun_test.log("Create stream %s" % OL_VXLAN_GOOD_TCP_XSUM)
        output = template_obj.configure_overlay_frame_stack(port=port_3,
                                                            overlay_type=template_obj.ETH_IPV4_UDP_VXLAN_ETH_IPV4_TCP)
        l3_config = spirent_config["l3_config"]["ipv4"]
        ip_header = Ipv4Header()
        destination = l3_config['hu_destination_ip1']
        if flow_direction == NuConfigManager.FLOW_DIRECTION_HU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_HNU:
            destination = l3_config['hnu_destination_ip1']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_CC:
            destination = l3_config['cc_destination_ip1']
        update = template_obj.update_overlay_frame_header(streamblock_obj=output['streamblock_obj'],
                                                          header_obj=ip_header, overlay=False,
                                                          updated_header_attributes_dict=
                                                          {'destAddr': destination})
        fun_test.test_assert(update, message="Update ipv4 destination address in underlay")

        update = template_obj.update_overlay_frame_header(streamblock_obj=output['streamblock_obj'],
                                                          header_obj=ip_header, overlay=True,
                                                          updated_header_attributes_dict=
                                                          {'destAddr': '2.2.2.2'})
        fun_test.test_assert(update, message="Update ipv4 destination address in overlay")

        update = template_obj.update_overlay_frame_header(streamblock_obj=output['streamblock_obj'],
                                                          header_obj=ip_header, overlay=True,
                                                          updated_header_attributes_dict=
                                                          {'sourceAddr': '1.1.1.1'})
        fun_test.test_assert(update, message="Update ipv4 source address in overlay")
        ether = Ethernet2Header()
        update = template_obj.update_overlay_frame_header(streamblock_obj=output['streamblock_obj'],
                                                          header_obj=ether, overlay=True,
                                                          updated_header_attributes_dict=
                                                          {'dstMac': '00:00:01:00:00:01'})
        fun_test.test_assert(update, message="Update dest mac in overlay")

        tcp = TCP()
        udp = UDP()
        update = template_obj.update_overlay_frame_header(streamblock_obj=output['streamblock_obj'],
                                                          header_obj=udp, overlay=False,
                                                          updated_header_attributes_dict=
                                                          {'checksum': '0000'})
        fun_test.test_assert(update, message="Update udp checksum in underlay")

        # Update streamblock
        self.current_streamblock_obj = output['streamblock_obj']
        self.current_streamblock_obj.Load = good_load
        self.current_streamblock_obj.LoadUnit = self.current_streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        self.current_streamblock_obj.FillType = self.current_streamblock_obj.FILL_TYPE_CONSTANT
        self.current_streamblock_obj.FixedFrameLength = 148
        self.current_streamblock_obj.InsertSig = True

        stream_update = template_obj.configure_stream_block(stream_block_obj=self.current_streamblock_obj, update=True)
        fun_test.test_assert(stream_update,
                             message="Updated streamblock %s" % self.current_streamblock_obj._spirent_handle)

        # Add Range Modifier
        recycle_count = 10
        step = 1
        mask = 15
        data = 5
        range_obj = RangeModifier(recycle_count=recycle_count, step_value=step, data=data, mask=mask)
        modify_attribute = 'offset'
        create_range = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=range_obj,
                                                                         streamblock_obj=self.current_streamblock_obj,
                                                                         header_obj=tcp,
                                                                         header_attribute=modify_attribute,
                                                                         custom_header=False)
        fun_test.test_assert(create_range, "Ensure range modifier created for attribute %s"
                             % modify_attribute)

        stream_objs['good'][OL_VXLAN_GOOD_TCP_XSUM] = self.current_streamblock_obj

        fun_test.log("========= NEW GOOD STREAM =========")
        self.current_streamblock_obj = None
        fun_test.log("Create stream %s" % OL_MPLS_GOOD_UDP_ZERO_XSUM)
        output = template_obj.configure_overlay_frame_stack(port=port_3,
                                                            overlay_type=template_obj.MPLS_ETH_IPV4_UDP_CUST_IPV4_UDP,
                                                            mpls=True)
        l3_config = spirent_config["l3_config"]["ipv4"]
        ip_header = Ipv4Header()
        destination = l3_config['hu_destination_ip1']
        if flow_direction == NuConfigManager.FLOW_DIRECTION_HU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_HNU:
            destination = l3_config['hnu_destination_ip1']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_CC:
            destination = l3_config['cc_destination_ip1']
        update = template_obj.update_overlay_frame_header(streamblock_obj=output['streamblock_obj'],
                                                          header_obj=ip_header, overlay=False,
                                                          updated_header_attributes_dict=
                                                          {'destAddr': destination})
        fun_test.test_assert(update, message="Update ipv4 destination address in underlay")

        udp = UDP()
        update = template_obj.update_overlay_frame_header(streamblock_obj=output['streamblock_obj'],
                                                          header_obj=udp, overlay=False,
                                                          updated_header_attributes_dict=
                                                          {'checksum': '0000'})
        fun_test.test_assert(update, message="Update udp checksum to 0000 in underlay")

        update = template_obj.update_overlay_frame_header(streamblock_obj=output['streamblock_obj'],
                                                          header_obj=udp, overlay=True,
                                                          updated_header_attributes_dict=
                                                          {'checksum': '0000'})
        fun_test.test_assert(update, message="Update udp checksum to 0000 in overlay")

        # Update streamblock
        self.current_streamblock_obj = output['streamblock_obj']
        self.current_streamblock_obj.Load = good_load
        self.current_streamblock_obj.LoadUnit = self.current_streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        self.current_streamblock_obj.FillType = self.current_streamblock_obj.FILL_TYPE_CONSTANT
        self.current_streamblock_obj.FixedFrameLength = 148
        self.current_streamblock_obj.InsertSig = True

        stream_update = template_obj.configure_stream_block(stream_block_obj=self.current_streamblock_obj, update=True)
        fun_test.test_assert(stream_update,
                             message="Updated streamblock %s" % self.current_streamblock_obj._spirent_handle)

        range_obj = RangeModifier(recycle_count=65000, step_value=1, data=1)
        modify_attribute = 'sourcePort'
        create_range = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=range_obj,
                                                                         streamblock_obj=self.current_streamblock_obj,
                                                                         header_obj=udp,
                                                                         header_attribute=modify_attribute,
                                                                         overlay=True)
        fun_test.test_assert(create_range, "Ensure range modifier created on %s for attribute %s"
                             % (tcp._spirent_handle, modify_attribute))
        stream_objs['good'][OL_MPLS_GOOD_UDP_ZERO_XSUM] = self.current_streamblock_obj
        
        fun_test.log("========= NEW GOOD STREAM =========")
        self.current_streamblock_obj = None
        fun_test.log("Create stream %s" % OL_MPLS_GOOD_TCP_XSUM)
        output = template_obj.configure_overlay_frame_stack(port=port_3,
                                                            overlay_type=template_obj.MPLS_ETH_IPV4_UDP_CUST_IPV4_TCP,
                                                            mpls=True)
        l3_config = spirent_config["l3_config"]["ipv4"]
        ip_header = Ipv4Header()
        destination = l3_config['hu_destination_ip1']
        if flow_direction == NuConfigManager.FLOW_DIRECTION_HU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_HNU:
            destination = l3_config['hnu_destination_ip1']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_CC:
            destination = l3_config['cc_destination_ip1']
        update = template_obj.update_overlay_frame_header(streamblock_obj=output['streamblock_obj'],
                                                          header_obj=ip_header, overlay=False,
                                                          updated_header_attributes_dict=
                                                          {'destAddr': destination})
        fun_test.test_assert(update, message="Update ipv4 destination address in underlay")
        # Update streamblock
        self.current_streamblock_obj = output['streamblock_obj']
        self.current_streamblock_obj.Load = good_load
        self.current_streamblock_obj.LoadUnit = self.current_streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        self.current_streamblock_obj.FillType = self.current_streamblock_obj.FILL_TYPE_CONSTANT
        self.current_streamblock_obj.FixedFrameLength = 148
        self.current_streamblock_obj.InsertSig = False

        stream_update = template_obj.configure_stream_block(stream_block_obj=self.current_streamblock_obj, update=True)
        fun_test.test_assert(stream_update,
                             message="Updated streamblock %s" % self.current_streamblock_obj._spirent_handle)

        udp = UDP()
        update = template_obj.update_overlay_frame_header(streamblock_obj=output['streamblock_obj'],
                                                          header_obj=udp, overlay=False,
                                                          updated_header_attributes_dict=
                                                          {'checksum': '0000'})
        fun_test.test_assert(update, message="Update udp checksum to 0000 in underlay")

        tcp = TCP()
        # Add Range Modifier
        recycle_count = 10
        step = 1
        mask = 15
        data = 5
        range_obj = RangeModifier(recycle_count=recycle_count, step_value=step, data=data, mask=mask)
        modify_attribute = 'offset'
        create_range = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=range_obj,
                                                                         streamblock_obj=self.current_streamblock_obj,
                                                                         header_obj=tcp,
                                                                         header_attribute=modify_attribute,
                                                                         custom_header=False)
        fun_test.test_assert(create_range, "Ensure range modifier created for attribute %s"
                             % modify_attribute)
        stream_objs['good'][OL_MPLS_GOOD_TCP_XSUM] = self.current_streamblock_obj

        fun_test.log("========= NEW GOOD STREAM =========") 
        self.current_streamblock_obj = None
        fun_test.log("Create stream %s" % UL_GOOD_TCP_FFFF_XSUM)
        self.current_streamblock_obj = self.create_common_streamblock(protocol_tcp=True, src_ip='18.0.5.1')
        custom_header_1 = CustomBytePatternHeader(byte_pattern=custom_headers[UL_GOOD_TCP_FFFF_XSUM])
        configure_cust_header = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=self.current_streamblock_obj._spirent_handle, header_obj=custom_header_1)
        fun_test.test_assert(configure_cust_header, "Configure custom header")
        stream_objs['good'][UL_GOOD_TCP_FFFF_XSUM] = self.current_streamblock_obj

        fun_test.log("========= NEW GOOD STREAM =========")
        self.current_streamblock_obj = None
        fun_test.log("Create stream %s" % UL_GOOD_TCP_ZERO_XSUM)
        self.current_streamblock_obj = self.create_common_streamblock(protocol_tcp=True, src_ip='18.0.5.1')
        custom_header_1 = CustomBytePatternHeader(byte_pattern=custom_headers[UL_GOOD_TCP_ZERO_XSUM])
        configure_cust_header = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=self.current_streamblock_obj._spirent_handle, header_obj=custom_header_1)
        fun_test.test_assert(configure_cust_header, "Configure custom header")
        stream_objs['good'][UL_GOOD_TCP_ZERO_XSUM] = self.current_streamblock_obj

        for stream in stream_objs['good'].values():
            good_stream_handle_list.append(stream._spirent_handle)

        fun_test.log("GOOD stream list %s" % good_stream_handle_list)
        fun_test.log("Error stream list %s" % error_stream_handle_list)

        if dut_config['enable_dpcsh']:
            # Clear port results on DUT
            clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
            fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

            clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
            fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

            clear_3 = network_controller_obj.clear_port_stats(port_num=dut_port_3)
            fun_test.test_assert(clear_3, message="Clear stats on port num %s of dut" % dut_port_3)

            # Get stats before starting traffic
            fun_test.log("Get stats before starting traffic")
            wro_stats_1 = network_controller_obj.peek_wro_global_stats()
            parser_stats_1 = network_controller_obj.peek_parser_stats()
            vp_pkts_stats_1 = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)
            erp_stats_1 = get_erp_stats_values(network_controller_obj=network_controller_obj)
            psw_stats_1 = network_controller_obj.peek_psw_global_stats()

        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=[gen_obj_1, gen_obj_3])
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic for %s seconds" % total_duration, seconds=total_duration + 2)

        # Stop traffic
        stop = template_obj.disable_generator_configs(generator_configs=[gen_obj_1, gen_obj_3])
        fun_test.test_assert(stop, "Stop generator config")

        # Asserts
        stream_result_dict = template_obj.stc_manager.fetch_streamblock_results(subscribe_result=subscribe_results,
                                                                                streamblock_handle_list=
                                                                                good_stream_handle_list,
                                                                                tx_result=True, rx_result=True)

        port_result_dict = template_obj.stc_manager.fetch_port_results(subscribe_result=subscribe_results,
                                                                       port_handle_list=[port_2], analyzer_result=True)
        port_2_analyzer_result = port_result_dict[port_2]['analyzer_result']
        fun_test.log(port_2_analyzer_result)

        if dut_config['enable_dpcsh']:
            # Get stats before starting traffic
            fun_test.log("Get stats after starting traffic")
            wro_stats_2 = network_controller_obj.peek_wro_global_stats()
            parser_stats_2 = network_controller_obj.peek_parser_stats()
            vp_pkts_stats_2 = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)
            erp_stats_2 = get_erp_stats_values(network_controller_obj=network_controller_obj)
            psw_stats_2 = network_controller_obj.peek_psw_global_stats()

            dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1)
            dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2)
            dut_port_3_results = network_controller_obj.peek_fpg_port_stats(dut_port_3)

            # ASSERTS
            fun_test.test_assert(dut_port_2_results, message="Ensure stats are obtained for %s" % dut_port_2)
            fun_test.test_assert(dut_port_1_results, message="Ensure stats are obtained for %s" % dut_port_1)
            fun_test.test_assert(dut_port_3_results, message="Ensure stats are obtained for %s" % dut_port_3)

            dut_port_2_transmit = get_dut_output_stats_value(dut_port_2_results, FRAMES_TRANSMITTED_OK)
            dut_port_3_receive = get_dut_output_stats_value(dut_port_3_results, FRAMES_RECEIVED_OK, tx=False)

            # DUT ASSERT
            fun_test.test_assert_expected(expected=int(dut_port_3_receive), actual=int(dut_port_2_transmit),
                                          message="Ensure good packets received are transmitted correctly")

        # SPIRENT ASSERT
        for good_stream in good_stream_handle_list:
            tx_results = stream_result_dict[good_stream]['tx_result']
            rx_results = stream_result_dict[good_stream]['rx_result']
            fun_test.log("good tx results for stream %s is %s" % (good_stream, tx_results['FrameCount']))
            fun_test.log("good rx results for stream %s is %s" % (good_stream, rx_results['FrameCount']))

        positive_packets_spirent_tx = 0
        for handle in good_stream_handle_list:
            fun_test.log("Adding tx counter for stream %s" % handle)
            positive_packets_spirent_tx += int(stream_result_dict[handle]['tx_result']['FrameCount'])

        fun_test.test_assert_expected(expected=int(positive_packets_spirent_tx),
                                      actual=int(port_2_analyzer_result['TotalFrameCount']),
                                      message="Ensure all good streams are transmitted and seen on spirent")


if __name__ == "__main__":
    local_settings = nu_config_obj.get_local_settings_parameters(flow_direction=True, ip_version=True)
    flow_direction = local_settings[nu_config_obj.FLOW_DIRECTION]
    ts = SpirentSetup()
    ts.add_test_case(Ulv6BadUdpXsum())
    ts.add_test_case(Ulv6BadUdpZeroXsum())
    ts.add_test_case(Ulv6BadTcpXsum())
    ts.add_test_case(Ulv4Olv6BadUdpXsum())
    ts.add_test_case(Ulv4ZeroUdpXsumOlv6ZeroUdpXsum())
    ts.add_test_case(Ulv4ZeroUdpXsumOlv6BadTcpXsum())
    ts.add_test_case(Ulv6Olv6BadUdpXsum())
    ts.add_test_case(Ulv6Olv6BadTcpXsum())
    ts.add_test_case(Ulv6ZeroUdpXsumOlv6GoodUdpXsum())
    ts.add_test_case(Ulv6ZeroUdpXsumOlv6GoodTcpXsum())
    ts.add_test_case(UlIpv6LenError())
    ts.add_test_case(Ulv4Olv6IpLenError())
    ts.add_test_case(Ulv6Olv6IpLenError())
    ts.add_test_case(GoodBad())
    ts.run()