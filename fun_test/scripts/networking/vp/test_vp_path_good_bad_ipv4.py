from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, GeneratorConfig, Ethernet2Header, TCP, UDP, Ipv4Header, RangeModifier, CustomBytePatternHeader, VxLAN
from lib.host.network_controller import NetworkController
from scripts.networking.helper import *
from scripts.networking.nu_config_manager import *

num_ports = 3
total_packets = 10
total_duration = total_packets
bad_load = 1
good_load = 50
aggregate_bad_load = 1
UL_BAD_IP_LEN_ERROR_INCR = "UL_BAD_IP_LEN_ERROR_INCR"
UL_BAD_UDP_XSUM = "UL_BAD_UDP_XSUM"
UL_BAD_UDP_FFFF_XSUM = "UL_BAD_UDP_FFFF_XSUM"
UL_GOOD_TCP_ZERO_XSUM = "UL_GOOD_TCP_ZERO_XSUM"
UL_BAD_TCP_XSUM = "UL_BAD_TCP_XSUM"
OL_VXLAN_BAD_IP_LEN_ERROR_INCR = "OL_VXLAN_BAD_IP_LEN_ERROR_INCR"
OL_VXLAN_BAD_UDP_XSUM = "OL_VXLAN_BAD_UDP_XSUM"
OL_VXLAN_BAD_UDP_FFFF_XSUM = "OL_VXLAN_BAD_UDP_FFFF_XSUM"
OL_VXLAN_BAD_TCP_XSUM = "OL_VXLAN_BAD_TCP_XSUM"
OL_VXLAN_BAD_TCP_ZERO_XSUM = "OL_VXLAN_BAD_TCP_ZERO_XSUM"
OL_MPLS_BAD_IP_LEN_ERROR_INCR = "OL_MPLS_BAD_IP_LEN_ERROR_INCR"
OL_MPLS_BAD_UDP_XSUM = "OL_MPLS_BAD_UDP_XSUM"
OL_MPLS_BAD_TCP_XSUM = "OL_MPLS_BAD_TCP_XSUM"
OL_MPLS_BAD_TCP_ZERO_XSUM = "OL_MPLS_BAD_TCP_ZERO_XSUM"
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
stream_objs = {}
stream_objs['bad'] = {}
stream_objs['good'] = {}
custom_headers = {UL_BAD_IP_LEN_ERROR_INCR: ['4500', '1500', '00010000FF11', 'CD93', 'C055010212000601'],
                  UL_BAD_UDP_XSUM : ['000125B0', '006E0001'], UL_BAD_UDP_FFFF_XSUM: ['00010001', '006EFFFF'],
                  OL_VXLAN_BAD_IP_LEN_ERROR_INCR: ['000112B5006E0000', '0800000000000000',
                                                   '00DEADBEEF000011223344550800', '4500', '1500', '00010000FF11', 'A0E6',
                                                   '0101010102020202'],
                  OL_VXLAN_BAD_UDP_XSUM: ['0001001006E1111'], OL_VXLAN_BAD_UDP_FFFF_XSUM: ['0001001006EFFFF'],
                  OL_MPLS_BAD_IP_LEN_ERROR_INCR: ['000119EB006E0000', '00012140', '4500', '1500', '00010000FF11', 'A0E6',
                                                  '0101010102020202'],
                  OL_MPLS_BAD_UDP_XSUM: ['00012140'],
                  OL_MPLS_BAD_TCP_XSUM: ['00012140'],
                  OL_MPLS_BAD_TCP_ZERO_XSUM: ['00012140'],
                  UL_GOOD_UDP_ZERO_XSUM: ['00010001006E0000'],
                  UL_GOOD_UDP_FFFF_XSUM: ['000125B9', '006EFFFF'],
                  OL_VXLAN_GOOD_UDP_FFFF_XSUM: ['0001F9D60008FFFF']}


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
        template_obj = SpirentEthernetTrafficTemplate(session_name="vp-negative-stream", spirent_config=spirent_config,
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
        l3_config = spirent_config["l3_config"]["ipv4"]
        ether_type = Ethernet2Header.INTERNET_IP_ETHERTYPE

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


class UlBadIpLenErrorIncremental(FunTestCase):
    expected_rx_count = 0
    current_stream = UL_BAD_IP_LEN_ERROR_INCR
    current_streamblock_obj = None
    id = 1

    def describe(self):
        self.set_test_details(
            id=1,summary="Test VP path FPG-HU with packet UL_BAD_IP_LEN_ERROR_INCR",
            steps="""
            1. Disable all streams and Enable stream UL_BAD_IP_LEN_ERROR_INCR
            2. Start traffic for 10 seconds
            3. Check counter on spirent rx. It must be 0 as DUT would drop packet with checksum error
            4. Check mac stats. No frames must be transmitted out of dut.
            5. Check erp stats for checksum/ip total len errors.
            """)

    def create_streamblock(self):
        # Streamblock
        self.current_streamblock_obj = StreamBlock(load=bad_load, load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND,
                                                   fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                                   frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_INCR,
                                                   min_frame_length=86, max_frame_length=1500, step_frame_length=1,
                                                   insert_signature=False)

        streamblock_obj = template_obj.configure_stream_block(stream_block_obj=self.current_streamblock_obj,
                                                              port_handle=port_1)
        fun_test.test_assert(streamblock_obj, "Create streamblock for underlay bad ip len error increamental")
        # MAC
        configure_mac = template_obj.stc_manager.configure_mac_address(
            streamblock=self.current_streamblock_obj._spirent_handle,
            source_mac=l2_config['source_mac'],
            destination_mac=l2_config['destination_mac'])
        fun_test.test_assert(configure_mac, "Configure mac address")

        # delete ipv4 header
        ip_header = Ipv4Header()
        header_type = ip_header.HEADER_TYPE.lower()
        header_type = 'children-' + header_type
        header_list = template_obj.stc_manager.get_object_children(handle=self.current_streamblock_obj._spirent_handle, child_type=header_type)
        header_handle = header_list[0]
        delete = template_obj.stc_manager.delete_handle(handle=header_handle)
        fun_test.test_assert(delete, "Ensure ipve header is deleted")

        for byte_pattern in custom_headers[self.current_stream]:
            cust_header = CustomBytePatternHeader(byte_pattern=byte_pattern)
            configure_cust_header = template_obj.stc_manager.configure_frame_stack(
                stream_block_handle=self.current_streamblock_obj._spirent_handle, header_obj=cust_header)
            fun_test.test_assert(configure_cust_header, "Configure custom header")

            if byte_pattern == '1500' or byte_pattern == 'CD93':
                modifier_mode = RangeModifier.INCR
                if byte_pattern == 'CD93':
                    modifier_mode = RangeModifier.DECR
                range_obj = RangeModifier(recycle_count=1000, step_value='0001', data=byte_pattern, mask='FFFF',
                                          modifier_mode=modifier_mode)
                modify_attribute = 'pattern'
                create_range = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=range_obj,
                                                                                 streamblock_obj=self.current_streamblock_obj,
                                                                                 header_obj=cust_header,
                                                                                 header_attribute=modify_attribute,
                                                                                 custom_header=True)
                fun_test.test_assert(create_range, "Ensure range modifier created on %s for attribute %s"
                                     % (cust_header._spirent_handle, modify_attribute))

            # Add Range Modifier

        udp = UDP()
        configure_udp = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=self.current_streamblock_obj._spirent_handle, header_obj=udp)
        fun_test.test_assert(configure_udp, "Configure udp header")

    def setup(self):
        # Deactivate all streamblocks
        if not self.current_stream == UL_BAD_IP_LEN_ERROR_INCR:
            deactivate = template_obj.deactivate_stream_blocks()
            fun_test.test_assert(deactivate, "Deactivated all streamblocks")

        self.create_streamblock()

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
            fun_test.log("Get stats after starting traffic")
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
            if self.current_stream == UL_BAD_IP_LEN_ERROR_INCR:
                check_ip_len_counter = ERP_COUNT_PACKETS_OUTER_IP_LEN_ERROR
            elif self.current_stream == OL_VXLAN_BAD_IP_LEN_ERROR_INCR or self.current_stream == OL_MPLS_BAD_IP_LEN_ERROR_INCR:
                check_ip_len_counter = ERP_COUNT_PACKETS_INNER_IP_LEN_ERROR
            else:
                check_layer4_cs_error_counter = ERP_COUNT_PACKETS_INNER_LAYER4_CS_ERROR
                if self.current_stream in [UL_BAD_UDP_FFFF_XSUM, UL_BAD_UDP_XSUM, UL_BAD_TCP_XSUM]:
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


class UlBadUdpXsum(UlBadIpLenErrorIncremental):
    current_stream = UL_BAD_UDP_XSUM

    def describe(self):
        self.set_test_details(
            id=2,summary="Test VP path FPG-HU with packet UL_BAD_UDP_XSUM",
            steps="""
            1. Disable all streams and Enable stream UL_BAD_UDP_XSUM
            2. Start traffic for 10 seconds
            3. Check counter on spirent rx. It must be 0 as DUT would drop packet with checksum error
            4. Check mac stats. No frames must be transmitted out of dut.
            5. Check erp stats for checksum/ip total len errors.
            """)

    def create_streamblock(self):
        # Streamblock
        self.current_streamblock_obj = StreamBlock(load=bad_load, load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND,
                                                   fill_type=StreamBlock.FILL_TYPE_PRBS, fixed_frame_length=148,
                                                   insert_signature=False)

        streamblock_obj = template_obj.configure_stream_block(stream_block_obj=self.current_streamblock_obj,
                                                              port_handle=port_1)
        fun_test.test_assert(streamblock_obj, "Create streamblock for UL_BAD_UDP_XSUM")
        # MAC
        configure_mac = template_obj.stc_manager.configure_mac_address(
            streamblock=self.current_streamblock_obj._spirent_handle,
            source_mac=l2_config['source_mac'],
            destination_mac=l2_config['destination_mac'])
        fun_test.test_assert(configure_mac, "Configure mac address")
        destination = l3_config['hu_destination_ip1']
        if flow_direction == NuConfigManager.FLOW_DIRECTION_HU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_HNU:
            destination = l3_config['hnu_destination_ip1']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_CC:
            destination = l3_config['cc_destination_ip1']
        ip_obj = Ipv4Header(destination_address=destination, protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
        configure_ip = template_obj.stc_manager.configure_frame_stack(stream_block_handle=
                                                                      self.current_streamblock_obj._spirent_handle,
                                                                      header_obj=ip_obj,
                                                                      delete_header=[ip_obj.HEADER_TYPE])
        fun_test.test_assert(configure_ip, "Configure IP header")

        for byte_pattern in custom_headers[self.current_stream]:
            cust_header = CustomBytePatternHeader(byte_pattern=byte_pattern)
            configure_cust_header = template_obj.stc_manager.configure_frame_stack(
                stream_block_handle=self.current_streamblock_obj._spirent_handle, header_obj=cust_header)
            fun_test.test_assert(configure_cust_header, "Configure custom header")

            modifier_needed = False
            if byte_pattern == '000125B0':
                modifier_needed = True
                recycle_count = 1000
                step = '00000001'
                mask = 'FFFFFFFF'
                data = byte_pattern
            elif byte_pattern == '00010001':
                modifier_needed = True
                recycle_count = 1000
                step = '00000001'
                mask = 'FFFFFFFF'
                data = byte_pattern
            elif byte_pattern == '006E0001':
                modifier_needed = True
                recycle_count = 65000
                step = '00000001'
                mask = '0000FFFF'
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

    def setup(self):
        # Deactivate all streamblocks
        deactivate = template_obj.deactivate_stream_blocks()
        fun_test.test_assert(deactivate, "Deactivated all streamblocks")

        self.create_streamblock()

        stream_objs['bad'][self.current_stream] = self.current_streamblock_obj

    def run(self):
        super(UlBadUdpXsum, self).run()

    def cleanup(self):
        super(UlBadUdpXsum, self).cleanup()


class UlBadUdpFFFFXsum(UlBadUdpXsum):
    current_stream = UL_BAD_UDP_FFFF_XSUM

    def describe(self):
        self.set_test_details(
            id=3,summary="Test VP path FPG-HU with packet UL_BAD_UDP_FFFF_XSUM",
            steps="""
            1. Disable all streams and Enable stream UL_BAD_UDP_FFFF_XSUM
            2. Start traffic for 10 seconds
            3. Check counter on spirent rx. It must be 0 as DUT would drop packet with checksum error
            4. Check mac stats. No frames must be transmitted out of dut.
            5. Check erp stats for checksum/ip total len errors.
            """)

    def setup(self):
        super(UlBadUdpFFFFXsum, self).setup()

    def run(self):
        super(UlBadUdpFFFFXsum, self).run()

    def cleanup(self):
        super(UlBadUdpFFFFXsum, self).cleanup()


class UlBadTcpXsum(UlBadIpLenErrorIncremental):
    current_stream = UL_BAD_TCP_XSUM
    checksum = '65535'

    def describe(self):
        self.set_test_details(
            id=4,summary="Test VP path FPG-HU with packet UL_BAD_TCP_XSUM",
            steps="""
            1. Disable all streams and Enable stream UL_BAD_TCP_XSUM
            2. Start traffic for 10 seconds
            3. Check counter on spirent rx. It must be 0 as DUT would drop packet with checksum error
            4. Check mac stats. No frames must be transmitted out of dut.
            5. Check erp stats for checksum/ip total len errors.
            """)

    def create_streamblock(self):
        # Streamblock
        self.current_streamblock_obj = StreamBlock(load=bad_load, load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND,
                                                   fill_type=StreamBlock.FILL_TYPE_CONSTANT, fixed_frame_length=148,
                                                   insert_signature=False)

        streamblock_obj = template_obj.configure_stream_block(stream_block_obj=self.current_streamblock_obj,
                                                              port_handle=port_1)
        fun_test.test_assert(streamblock_obj, "Create streamblock for UL_BAD_TCP_XSUM")
        # MAC
        configure_mac = template_obj.stc_manager.configure_mac_address(
            streamblock=self.current_streamblock_obj._spirent_handle,
            source_mac=l2_config['source_mac'],
            destination_mac=l2_config['destination_mac'])
        fun_test.test_assert(configure_mac, "Configure mac address")
        destination = l3_config['hu_destination_ip1']
        if flow_direction == NuConfigManager.FLOW_DIRECTION_HU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_HNU:
            destination = l3_config['hnu_destination_ip1']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_CC:
            destination = l3_config['cc_destination_ip1']
        ip_obj = Ipv4Header(destination_address=destination, protocol=Ipv4Header.PROTOCOL_TYPE_TCP)
        configure_ip = template_obj.stc_manager.configure_frame_stack(stream_block_handle=
                                                                      self.current_streamblock_obj._spirent_handle,
                                                                      header_obj=ip_obj,
                                                                      delete_header=[ip_obj.HEADER_TYPE])
        fun_test.test_assert(configure_ip, "Configure IP header")

        tcp = TCP(checksum=self.checksum)
        configure_udp = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=self.current_streamblock_obj._spirent_handle, header_obj=tcp)
        fun_test.test_assert(configure_udp, "Configure tcp header")

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
        fun_test.test_assert(create_range, "Ensure range modifier created on %s for attribute %s"
                             % (tcp._spirent_handle, modify_attribute))

    def setup(self):
        super(UlBadTcpXsum, self).setup()

    def run(self):
        super(UlBadTcpXsum, self).run()

    def cleanup(self):
        super(UlBadTcpXsum, self).cleanup()


class OlVxlanBadIpLenErrorIncr(UlBadIpLenErrorIncremental):
    current_stream = OL_VXLAN_BAD_IP_LEN_ERROR_INCR
    checksum = '0000'

    def describe(self):
        self.set_test_details(
            id=5,summary="Test VP path FPG-HU with packet OL_VXLAN_BAD_IP_LEN_ERROR_INCR",
            steps="""
            1. Disable all streams and Enable stream OL_VXLAN_BAD_IP_LEN_ERROR_INCR
            2. Start traffic for 10 seconds
            3. Check counter on spirent rx. It must be 0 as DUT would drop packet with checksum error
            4. Check mac stats. No frames must be transmitted out of dut.
            5. Check erp stats for checksum/ip total len errors.
            """)

    def create_streamblock(self):
        # Streamblock
        self.current_streamblock_obj = StreamBlock(load=bad_load, load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND,
                                                   fill_type=StreamBlock.FILL_TYPE_CONSTANT, insert_signature=False,
                                                   fixed_frame_length=148)

        streamblock_obj = template_obj.configure_stream_block(stream_block_obj=self.current_streamblock_obj,
                                                              port_handle=port_1)
        fun_test.test_assert(streamblock_obj, "Create streamblock for OL_VXLAN_BAD_IP_LEN_ERROR_INCR")
        # MAC
        configure_mac = template_obj.stc_manager.configure_mac_address(
            streamblock=self.current_streamblock_obj._spirent_handle,
            source_mac=l2_config['source_mac'],
            destination_mac=l2_config['destination_mac'])
        fun_test.test_assert(configure_mac, "Configure mac address")
        destination = l3_config['hu_destination_ip1']
        if flow_direction == NuConfigManager.FLOW_DIRECTION_HU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_HNU:
            destination = l3_config['hnu_destination_ip1']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_CC:
            destination = l3_config['cc_destination_ip1']
        ip_obj = Ipv4Header(destination_address=destination, protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
        configure_ip = template_obj.stc_manager.configure_frame_stack(stream_block_handle=
                                                                      self.current_streamblock_obj._spirent_handle,
                                                                      header_obj=ip_obj,
                                                                      delete_header=[ip_obj.HEADER_TYPE])
        fun_test.test_assert(configure_ip, "Configure IP header")

        for byte_pattern in custom_headers[self.current_stream]:
            cust_header = CustomBytePatternHeader(byte_pattern=byte_pattern)
            configure_cust_header = template_obj.stc_manager.configure_frame_stack(
                stream_block_handle=self.current_streamblock_obj._spirent_handle, header_obj=cust_header)
            fun_test.test_assert(configure_cust_header, "Configure custom header")

            # Add Range Modifier
            modifier_needed = False
            if byte_pattern == '1500':
                modifier_mode = RangeModifier.INCR
                modifier_needed = True
                recycle_count = 1000
                step = '0001'
                mask = 'FFFF'
                data = byte_pattern
            elif byte_pattern == 'A0E6':
                modifier_needed = True
                modifier_mode = RangeModifier.DECR
                recycle_count = 65535
                if self.current_stream == OL_MPLS_BAD_IP_LEN_ERROR_INCR:
                    recycle_count = 16383
                step = '0001'
                mask = 'FFFF'
                data = byte_pattern
            if modifier_needed:
                range_obj = RangeModifier(recycle_count=recycle_count, step_value=step, data=data, mask=mask,
                                          modifier_mode=modifier_mode)
                modify_attribute = 'pattern'
                create_range = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=range_obj,
                                                                                 streamblock_obj=self.current_streamblock_obj,
                                                                                 header_obj=cust_header,
                                                                                 header_attribute=modify_attribute,
                                                                                 custom_header=True)
                fun_test.test_assert(create_range, "Ensure range modifier created on %s for attribute %s"
                                     % (cust_header._spirent_handle, modify_attribute))

        udp = UDP()
        if self.checksum:
            udp = UDP(checksum=self.checksum)
        configure_udp = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=self.current_streamblock_obj._spirent_handle, header_obj=udp)
        fun_test.test_assert(configure_udp, "Configure udp header")

    def setup(self):
        super(OlVxlanBadIpLenErrorIncr, self).setup()

    def run(self):
        super(OlVxlanBadIpLenErrorIncr, self).run()

    def cleanup(self):
        super(OlVxlanBadIpLenErrorIncr, self).cleanup()


class OlVxlanBadUdpXsum(UlBadIpLenErrorIncremental):
    current_stream = OL_VXLAN_BAD_UDP_XSUM

    def describe(self):
        self.set_test_details(
            id=6,summary="Test VP path FPG-HU with packet OL_VXLAN_BAD_UDP_XSUM",
            steps="""
            1. Disable all streams and Enable stream OL_VXLAN_BAD_UDP_XSUM
            2. Start traffic for 10 seconds
            3. Check counter on spirent rx. It must be 0 as DUT would drop packet with checksum error
            4. Check mac stats. No frames must be transmitted out of dut.
            5. Check erp stats for checksum/ip total len errors.
            """)

    def run(self):
        super(OlVxlanBadUdpXsum, self).run()

    def cleanup(self):
        super(OlVxlanBadUdpXsum, self).cleanup()

    def create_streamblock(self):
        # Streamblock
        self.current_streamblock_obj = StreamBlock(load=bad_load, load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND,
                                                   fill_type=StreamBlock.FILL_TYPE_CONSTANT, insert_signature=False,
                                                   fixed_frame_length=300)

        streamblock_obj = template_obj.configure_stream_block(stream_block_obj=self.current_streamblock_obj,
                                                              port_handle=port_1)
        fun_test.test_assert(streamblock_obj, "Create streamblock for %s " % self.current_stream)
        # MAC
        configure_mac = template_obj.stc_manager.configure_mac_address(
            streamblock=self.current_streamblock_obj._spirent_handle,
            source_mac=l2_config['source_mac'],
            destination_mac=l2_config['destination_mac'])
        fun_test.test_assert(configure_mac, "Configure mac address")
        destination = l3_config['hu_destination_ip1']
        if flow_direction == NuConfigManager.FLOW_DIRECTION_HU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_HNU:
            destination = l3_config['hnu_destination_ip1']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_CC:
            destination = l3_config['cc_destination_ip1']
        ip_obj = Ipv4Header(destination_address=destination, protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
        configure_ip = template_obj.stc_manager.configure_frame_stack(stream_block_handle=
                                                                      self.current_streamblock_obj._spirent_handle,
                                                                      header_obj=ip_obj,
                                                                      delete_header=[ip_obj.HEADER_TYPE])
        fun_test.test_assert(configure_ip, "Configure IP header")

        udp = UDP(destination_port=4789)
        configure_udp = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=self.current_streamblock_obj._spirent_handle, header_obj=udp)
        fun_test.test_assert(configure_udp, "Configure udp header")

        vxlan = VxLAN()
        configure_vxlan = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=self.current_streamblock_obj._spirent_handle, header_obj=vxlan)
        fun_test.test_assert(configure_vxlan, "Configure vxlan header")

        ethernet = Ethernet2Header()
        configure_eth = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=self.current_streamblock_obj._spirent_handle, header_obj=ethernet)
        fun_test.test_assert(configure_eth, "Configure ethernet header")

        ip_obj_2 = Ipv4Header(protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
        configure_ip_2 = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=self.current_streamblock_obj._spirent_handle, header_obj=ip_obj_2)
        fun_test.test_assert(configure_ip_2, "Configure ip header")

        for byte_pattern in custom_headers[self.current_stream]:
            cust_header = CustomBytePatternHeader(byte_pattern=byte_pattern)
            configure_cust_header = template_obj.stc_manager.configure_frame_stack(
                stream_block_handle=self.current_streamblock_obj._spirent_handle, header_obj=cust_header)
            fun_test.test_assert(configure_cust_header, "Configure custom header")

            # Add Range Modifier

    def setup(self):
        super(OlVxlanBadUdpXsum, self).setup()


class OlVxlanBadUdpFFFFXsum(OlVxlanBadUdpXsum):
    current_stream = OL_VXLAN_BAD_UDP_FFFF_XSUM

    def describe(self):
        self.set_test_details(
            id=7,summary="Test VP path FPG-HU with packet OL_VXLAN_BAD_UDP_FFFF_XSUM",
            steps="""
            1. Disable all streams and Enable stream OL_VXLAN_BAD_UDP_FFFF_XSUM
            2. Start traffic for 10 seconds
            3. Check counter on spirent rx. It must be 0 as DUT would drop packet with checksum error
            4. Check mac stats. No frames must be transmitted out of dut.
            5. Check erp stats for checksum/ip total len errors.
            """)

    def run(self):
        super(OlVxlanBadUdpFFFFXsum, self).run()

    def cleanup(self):
        super(OlVxlanBadUdpFFFFXsum, self).cleanup()

    def setup(self):
        super(OlVxlanBadUdpFFFFXsum, self).setup()


class OlVxlanBadTcpXsum(UlBadIpLenErrorIncremental):
    current_stream = OL_VXLAN_BAD_TCP_XSUM
    update_header = TCP()
    checksum = update_header.CHECKSUM_ERROR

    def describe(self):
        self.set_test_details(
            id=8,summary="Test VP path FPG-HU with packet OL_VXLAN_BAD_TCP_XSUM",
            steps="""
            1. Disable all streams and Enable stream OL_VXLAN_BAD_TCP_XSUM
            2. Start traffic for 10 seconds
            3. Check counter on spirent rx. It must be 0 as DUT would drop packet with checksum error
            4. Check mac stats. No frames must be transmitted out of dut.
            5. Check erp stats for checksum/ip total len errors.
            """)

    def run(self):
        super(OlVxlanBadTcpXsum, self).run()

    def cleanup(self):
        super(OlVxlanBadTcpXsum, self).cleanup()

    def create_streamblock(self):
        output = template_obj.configure_overlay_frame_stack(port=port_1)
        self.current_streamblock_obj = output['streamblock_obj']
        destination = l3_config['hu_destination_ip1']
        if flow_direction == NuConfigManager.FLOW_DIRECTION_HU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_HNU:
            destination = l3_config['hnu_destination_ip1']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_CC:
            destination = l3_config['cc_destination_ip1']
        ip_header = Ipv4Header()
        update = template_obj.update_overlay_frame_header(streamblock_obj=output['streamblock_obj'],
                                                          header_obj=ip_header, overlay=False,
                                                          updated_header_attributes_dict=
                                                          {'destAddr': destination})
        fun_test.test_assert(update, message="Update ipv4 destination address in underlay")

        update = template_obj.update_overlay_frame_header(streamblock_obj=self.current_streamblock_obj,
                                                          header_obj=self.update_header, overlay=True,
                                                          updated_header_attributes_dict=
                                                          {'checksum': self.checksum})
        fun_test.test_assert(update, message="Update tcp checksum to error")

        range_obj = RangeModifier(recycle_count=65000, step_value=1, data=1024)
        modify_attribute = 'sourcePort'
        create_range = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=range_obj,
                                                                         streamblock_obj=self.current_streamblock_obj,
                                                                         header_obj=self.update_header,
                                                                         header_attribute=modify_attribute, overlay=True)
        fun_test.test_assert(create_range, "Ensure range modifier created on for attribute %s"
                             % modify_attribute)

        # Update streamblock
        self.current_streamblock_obj.Load = bad_load
        self.current_streamblock_obj.LoadUnit = self.current_streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        self.current_streamblock_obj.FillType = self.current_streamblock_obj.FILL_TYPE_CONSTANT
        self.current_streamblock_obj.FixedFrameLength = 148
        self.current_streamblock_obj.InsertSig = False

        stream_update = template_obj.configure_stream_block(stream_block_obj=self.current_streamblock_obj, update=True)
        fun_test.test_assert(stream_update, message="Updated streamblock %s" % self.current_streamblock_obj._spirent_handle)

    def setup(self):
        super(OlVxlanBadTcpXsum, self).setup()


class OlVxlanBadTcpZeroXsum(OlVxlanBadTcpXsum):
    current_stream = OL_VXLAN_BAD_TCP_ZERO_XSUM
    update_header = TCP()
    checksum = '0000'

    def describe(self):
        self.set_test_details(
            id=9,summary="Test VP path FPG-HU with packet OL_VXLAN_BAD_TCP_ZERO_XSUM",
            steps="""
            1. Disable all streams and Enable stream OL_VXLAN_BAD_TCP_ZERO_XSUM
            2. Start traffic for 10 seconds
            3. Check counter on spirent rx. It must be 0 as DUT would drop packet with checksum error
            4. Check mac stats. No frames must be transmitted out of dut.
            5. Check erp stats for checksum/ip total len errors.
            """)

    def run(self):
        super(OlVxlanBadTcpZeroXsum, self).run()

    def cleanup(self):
        super(OlVxlanBadTcpZeroXsum, self).cleanup()

    def setup(self):
        super(OlVxlanBadTcpZeroXsum, self).setup()


class OlMplsBadIpLenErrorIncr(OlVxlanBadIpLenErrorIncr):
    current_stream = OL_MPLS_BAD_IP_LEN_ERROR_INCR
    checksum ='0000'

    def describe(self):
        self.set_test_details(
            id=10,summary="Test VP path FPG-HU with packet OL_MPLS_BAD_IP_LEN_ERROR_INCR",
            steps="""
            1. Disable all streams and Enable stream OL_MPLS_BAD_IP_LEN_ERROR_INCR
            2. Start traffic for 10 seconds
            3. Check counter on spirent rx. It must be 0 as DUT would drop packet with checksum error
            4. Check mac stats. No frames must be transmitted out of dut.
            5. Check erp stats for checksum/ip total len errors.
            """)

    def run(self):
        super(OlMplsBadIpLenErrorIncr, self).run()

    def cleanup(self):
        super(OlMplsBadIpLenErrorIncr, self).cleanup()

    def setup(self):
        super(OlMplsBadIpLenErrorIncr, self).setup()


class OlMplsBadUdpXsum(UlBadIpLenErrorIncremental):
    current_stream = OL_MPLS_BAD_UDP_XSUM
    update_header = UDP()
    checksum = update_header.CHECKSUM_ERROR

    def describe(self):
        self.set_test_details(
            id=11,summary="Test VP path FPG-HU with packet OL_MPLS_BAD_UDP_XSUM",
            steps="""
            1. Disable all streams and Enable stream OL_MPLS_BAD_UDP_XSUM
            2. Start traffic for 10 seconds
            3. Check counter on spirent rx. It must be 0 as DUT would drop packet with checksum error
            4. Check mac stats. No frames must be transmitted out of dut.
            5. Check erp stats for checksum/ip total len errors.
            """)

    def run(self):
        super(OlMplsBadUdpXsum, self).run()

    def cleanup(self):
        super(OlMplsBadUdpXsum, self).cleanup()

    def create_streamblock(self):
        overlay_type = template_obj.MPLS_ETH_IPV4_UDP_CUST_IPV4_UDP
        if not self.current_stream == OL_MPLS_BAD_UDP_XSUM:
            overlay_type = template_obj.MPLS_ETH_IPV4_UDP_CUST_IPV4_TCP
        output = template_obj.configure_overlay_frame_stack(port=port_1,
                                                            overlay_type=overlay_type,
                                                            mpls=True,
                                                            byte_pattern=custom_headers[self.current_stream][0])
        self.current_streamblock_obj = output['streamblock_obj']

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

        update = template_obj.update_overlay_frame_header(streamblock_obj=self.current_streamblock_obj,
                                                          header_obj=self.update_header, overlay=True,
                                                          updated_header_attributes_dict=
                                                          {'checksum': self.checksum})
        fun_test.test_assert(update, message="Update %s checksum to error" % self.update_header.HEADER_TYPE)

        # Update streamblock
        self.current_streamblock_obj.Load = bad_load
        self.current_streamblock_obj.LoadUnit = self.current_streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        self.current_streamblock_obj.FillType = self.current_streamblock_obj.FILL_TYPE_CONSTANT
        self.current_streamblock_obj.FixedFrameLength = 148
        self.current_streamblock_obj.InsertSig = False

        stream_update = template_obj.configure_stream_block(stream_block_obj=self.current_streamblock_obj, update=True)
        fun_test.test_assert(stream_update,
                             message="Updated streamblock %s" % self.current_streamblock_obj._spirent_handle)

        recycle_count = 65000
        data = 1024
        if self.current_stream == OL_MPLS_BAD_UDP_XSUM:
            recycle_count = 16000
            data = 1024
        range_obj = RangeModifier(recycle_count=recycle_count, step_value=1, data=data)
        modify_attribute = 'sourcePort'
        create_range = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=range_obj,
                                                                         streamblock_obj=self.current_streamblock_obj,
                                                                         header_obj=self.update_header,
                                                                         header_attribute=modify_attribute, overlay=True)
        fun_test.test_assert(create_range, "Ensure range modifier created for attribute %s"
                             % modify_attribute)

    def setup(self):
        super(OlMplsBadUdpXsum, self).setup()


class OlMplsBadTcpXsum(OlMplsBadUdpXsum):
    current_stream = OL_MPLS_BAD_TCP_XSUM
    update_header = TCP()
    checksum = update_header.CHECKSUM_ERROR

    def describe(self):
        self.set_test_details(
            id=12,summary="Test VP path FPG-HU with packet OL_MPLS_BAD_TCP_XSUM",
            steps="""
            1. Disable all streams and Enable stream OL_MPLS_BAD_TCP_XSUM
            2. Start traffic for 10 seconds
            3. Check counter on spirent rx. It must be 0 as DUT would drop packet with checksum error
            4. Check mac stats. No frames must be transmitted out of dut.
            5. Check erp stats for checksum/ip total len errors.
            """)

    def run(self):
        super(OlMplsBadTcpXsum, self).run()

    def cleanup(self):
        super(OlMplsBadTcpXsum, self).cleanup()

    def setup(self):
        super(OlMplsBadTcpXsum, self).setup()


class OlMplsBadTcpZeroXsum(OlMplsBadUdpXsum):
    current_stream = OL_MPLS_BAD_TCP_ZERO_XSUM
    update_header = TCP()
    checksum = '0000'

    def describe(self):
        self.set_test_details(
            id=13,summary="Test VP path FPG-HU with packet OL_MPLS_BAD_TCP_ZERO_XSUM",
            steps="""
            1. Disable all streams and Enable stream OL_MPLS_BAD_TCP_ZERO_XSUM
            2. Start traffic for 10 seconds
            3. Check counter on spirent rx. It must be 0 as DUT would drop packet with checksum error
            4. Check mac stats. No frames must be transmitted out of dut.
            5. Check erp stats for checksum/ip total len errors.
            """)

    def run(self):
        super(OlMplsBadTcpZeroXsum, self).run()

    def cleanup(self):
        super(OlMplsBadTcpZeroXsum, self).cleanup()

    def setup(self):
        super(OlMplsBadTcpZeroXsum, self).setup()


class GoodBad(FunTestCase):
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

    def create_common_streamblock(self, protocol_tcp=False):
        # Streamblock
        self.current_streamblock_obj = StreamBlock(load=good_load, load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND,
                                                   fill_type=StreamBlock.FILL_TYPE_CONSTANT, insert_signature=False,
                                                   fixed_frame_length=148)

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
                               protocol=protocol)
        configure_ip = template_obj.stc_manager.configure_frame_stack(stream_block_handle=
                                                                      self.current_streamblock_obj._spirent_handle,
                                                                      header_obj=ip_header,
                                                                      delete_header=[ip_header.HEADER_TYPE])
        fun_test.test_assert(configure_ip, "Configure IP header")

    def setup(self):

        # Enable stream
        activate = template_obj.activate_stream_blocks()
        fun_test.test_assert(activate, "Activate all streamblocks")

    def cleanup(self):
        pass

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

        # Add good streams
        fun_test.log("========= NEW GOOD STREAM =========")
        self.current_streamblock_obj = None
        fun_test.log("Create stream %s" % UL_GOOD_UDP_ZERO_XSUM)
        self.create_common_streamblock()
        custom_header_1 = CustomBytePatternHeader(byte_pattern=custom_headers[UL_GOOD_UDP_ZERO_XSUM][0])
        configure_cust_header = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=self.current_streamblock_obj._spirent_handle, header_obj=custom_header_1)
        fun_test.test_assert(configure_cust_header, "Configure custom header")
        stream_objs['good'][UL_GOOD_UDP_ZERO_XSUM] = self.current_streamblock_obj

        fun_test.log("========= NEW GOOD STREAM =========")
        self.current_streamblock_obj = None
        fun_test.log("Create stream %s" % UL_GOOD_UDP_FFFF_XSUM)
        self.create_common_streamblock()
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

        self.current_streamblock_obj.FillType = StreamBlock.FILL_TYPE_CONSTANT
        self.current_streamblock_obj.InsertSig = False
        stream_update = template_obj.configure_stream_block(stream_block_obj=self.current_streamblock_obj, update=True)
        fun_test.test_assert(stream_update,
                             message="Updated streamblock %s" % self.current_streamblock_obj._spirent_handle)

        stream_objs['good'][UL_GOOD_UDP_FFFF_XSUM] = self.current_streamblock_obj

        fun_test.log("========= NEW GOOD STREAM =========")
        self.current_streamblock_obj = None
        fun_test.log("Create stream %s" % UL_GOOD_TCP_XSUM)
        self.create_common_streamblock(protocol_tcp=True)
        tcp=TCP()
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
        fun_test.log("Create stream %s" % UL_GOOD_TCP_ZERO_XSUM)
        self.current_streamblock_obj = StreamBlock(load=good_load, load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND,
                                                   fill_type=StreamBlock.FILL_TYPE_CONSTANT, fixed_frame_length=148,
                                                   insert_signature=False)

        streamblock_obj = template_obj.configure_stream_block(stream_block_obj=self.current_streamblock_obj,
                                                              port_handle=port_3)
        fun_test.test_assert(streamblock_obj, "Create streamblock for UL_GOOD_TCP_ZERO_XSUM")
        # MAC
        configure_mac = template_obj.stc_manager.configure_mac_address(
            streamblock=self.current_streamblock_obj._spirent_handle,
            source_mac=l2_config['source_mac'],
            destination_mac=l2_config['destination_mac'])
        fun_test.test_assert(configure_mac, "Configure mac address")
        destination = l3_config['hu_destination_ip1']
        if flow_direction == NuConfigManager.FLOW_DIRECTION_HU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_HNU:
            destination = l3_config['hnu_destination_ip1']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_CC:
            destination = l3_config['cc_destination_ip1']
        ip_obj = Ipv4Header(destination_address=destination, protocol=Ipv4Header.PROTOCOL_TYPE_TCP)
        configure_ip = template_obj.stc_manager.configure_frame_stack(stream_block_handle=
                                                                      self.current_streamblock_obj._spirent_handle,
                                                                      header_obj=ip_obj,
                                                                      delete_header=[ip_obj.HEADER_TYPE])
        fun_test.test_assert(configure_ip, "Configure IP header")

        tcp = TCP(checksum='0000')
        configure_udp = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=self.current_streamblock_obj._spirent_handle, header_obj=tcp)
        fun_test.test_assert(configure_udp, "Configure tcp header")

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
        fun_test.test_assert(create_range, "Ensure range modifier created on %s for attribute %s"
                             % (tcp._spirent_handle, modify_attribute))
        stream_objs['good'][UL_GOOD_TCP_ZERO_XSUM] = self.current_streamblock_obj

        fun_test.log("========= NEW GOOD STREAM =========")
        self.current_streamblock_obj = None
        fun_test.log("Create stream %s" % OL_VXLAN_GOOD_UDP_ZERO_XSUM)
        output = template_obj.configure_overlay_frame_stack(port=port_3,
                                                            overlay_type=template_obj.ETH_IPV4_UDP_VXLAN_ETH_IPV4_UDP)

        ip_header = Ipv4Header()
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
        self.current_streamblock_obj.InsertSig = False

        stream_update = template_obj.configure_stream_block(stream_block_obj=self.current_streamblock_obj, update=True)
        fun_test.test_assert(stream_update,
                             message="Updated streamblock %s" % self.current_streamblock_obj._spirent_handle)

        stream_objs['good'][OL_VXLAN_GOOD_UDP_ZERO_XSUM] = self.current_streamblock_obj

        fun_test.log("========= NEW GOOD STREAM =========")
        self.current_streamblock_obj = None
        fun_test.log("Create stream %s" % OL_VXLAN_GOOD_UDP_FFFF_XSUM)
        self.create_common_streamblock()
        udp=UDP(destination_port=4789)
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

        ip_header = Ipv4Header(source_address='1.1.1.1', destination_address='2.2.2.3', protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
        configure_cust_header = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=self.current_streamblock_obj._spirent_handle, header_obj=ip_header)
        fun_test.test_assert(configure_cust_header, "Configure ip header")

        for byte_pattern in custom_headers[OL_VXLAN_GOOD_UDP_FFFF_XSUM]:
            cust_header = CustomBytePatternHeader(byte_pattern=byte_pattern)
            configure_cust_header = template_obj.stc_manager.configure_frame_stack(
                stream_block_handle=self.current_streamblock_obj._spirent_handle, header_obj=cust_header)
            fun_test.test_assert(configure_cust_header, "Configure custom header")

        # Update streamblock
        self.current_streamblock_obj = output['streamblock_obj']
        self.current_streamblock_obj.Load = good_load
        self.current_streamblock_obj.LoadUnit = self.current_streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        self.current_streamblock_obj.FillType = self.current_streamblock_obj.FILL_TYPE_CONSTANT
        self.current_streamblock_obj.FixedFrameLength = 148
        self.current_streamblock_obj.InsertSig = False

        stream_update = template_obj.configure_stream_block(stream_block_obj=self.current_streamblock_obj,
                                                            update=True)
        fun_test.test_assert(stream_update,
                             message="Updated streamblock %s" % self.current_streamblock_obj._spirent_handle)
        stream_objs['good'][OL_VXLAN_GOOD_UDP_FFFF_XSUM] = self.current_streamblock_obj

        fun_test.log("========= NEW GOOD STREAM =========")
        self.current_streamblock_obj = None
        fun_test.log("Create stream %s" % OL_VXLAN_GOOD_UDP_XSUM)
        output = template_obj.configure_overlay_frame_stack(port=port_3,
                                                            overlay_type=template_obj.ETH_IPV4_UDP_VXLAN_ETH_IPV4_UDP)
        ip_header = Ipv4Header()
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
        # Add Range Modifier
        recycle_count = 16000
        step = 1
        mask = 65535
        data = 1
        range_obj = RangeModifier(recycle_count=recycle_count, step_value=step, data=data, mask=mask)
        modify_attribute = 'sourcePort'
        create_range = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=range_obj,
                                                                         streamblock_obj=self.current_streamblock_obj,
                                                                         header_obj=udp,
                                                                         header_attribute=modify_attribute,
                                                                         overlay=True)
        fun_test.test_assert(create_range, "Ensure range modifier created for attribute %s"
                             % modify_attribute)
        stream_objs['good'][OL_VXLAN_GOOD_UDP_XSUM] = self.current_streamblock_obj

        fun_test.log("========= NEW GOOD STREAM =========")
        self.current_streamblock_obj = None
        fun_test.log("Create stream %s" % OL_VXLAN_GOOD_TCP_XSUM)
        output = template_obj.configure_overlay_frame_stack(port=port_3,
                                                            overlay_type=template_obj.ETH_IPV4_UDP_VXLAN_ETH_IPV4_TCP)
        ip_header = Ipv4Header()
        update = template_obj.update_overlay_frame_header(streamblock_obj=output['streamblock_obj'],
                                                          header_obj=ip_header, overlay=False,
                                                          updated_header_attributes_dict=
                                                          {'destAddr': destination})
        fun_test.test_assert(update, message="Update ipv4 destination address in underlay")
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
        self.current_streamblock_obj.InsertSig = False

        stream_update = template_obj.configure_stream_block(stream_block_obj=self.current_streamblock_obj, update=True)
        fun_test.test_assert(stream_update,
                             message="Updated streamblock %s" % self.current_streamblock_obj._spirent_handle)

        range_obj = RangeModifier(recycle_count=65000, step_value=1, data=1)
        modify_attribute = 'sourcePort'
        create_range = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=range_obj,
                                                                         streamblock_obj=self.current_streamblock_obj,
                                                                         header_obj=tcp,
                                                                         header_attribute=modify_attribute,
                                                                         overlay=True)
        fun_test.test_assert(create_range, "Ensure range modifier created on %s for attribute %s"
                             % (tcp._spirent_handle, modify_attribute))

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
        ip_header = Ipv4Header()
        update = template_obj.update_overlay_frame_header(streamblock_obj=output['streamblock_obj'],
                                                          header_obj=ip_header, overlay=False,
                                                          updated_header_attributes_dict=
                                                          {'destAddr': destination})
        fun_test.test_assert(update, message="Update ipv4 destination address in underlay")

        udp=UDP()
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
        self.current_streamblock_obj.InsertSig = False

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
        fun_test.log("Create stream %s" % OL_MPLS_GOOD_UDP_XSUM)
        output = template_obj.configure_overlay_frame_stack(port=port_3,
                                                            overlay_type=template_obj.MPLS_ETH_IPV4_UDP_CUST_IPV4_UDP,
                                                            mpls=True)
        ip_header = Ipv4Header()
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
        stream_objs['good'][OL_MPLS_GOOD_UDP_XSUM] = self.current_streamblock_obj

        # Adding range modifier
        udp = UDP()
        range_obj = RangeModifier(recycle_count=65000, step_value=1, data=1)
        modify_attribute = 'sourcePort'
        create_range = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=range_obj,
                                                                         streamblock_obj=self.current_streamblock_obj,
                                                                         header_obj=udp,
                                                                         header_attribute=modify_attribute,
                                                                         overlay=True)
        fun_test.test_assert(create_range, "Ensure range modifier created on %s for attribute %s"
                             % (tcp._spirent_handle, modify_attribute))
        stream_objs['good'][OL_MPLS_GOOD_UDP_XSUM] = self.current_streamblock_obj

        fun_test.log("========= NEW GOOD STREAM =========")
        self.current_streamblock_obj = None
        fun_test.log("Create stream %s" % OL_MPLS_GOOD_TCP_XSUM)
        output = template_obj.configure_overlay_frame_stack(port=port_3,
                                                            overlay_type=template_obj.MPLS_ETH_IPV4_UDP_CUST_IPV4_TCP,
                                                            mpls=True)
        ip_header = Ipv4Header()
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

        # Adding range modifier
        range_obj = RangeModifier(recycle_count=65000, step_value=1, data=1)
        modify_attribute = 'sourcePort'
        create_range = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=range_obj,
                                                                         streamblock_obj=self.current_streamblock_obj,
                                                                         header_obj=tcp,
                                                                         header_attribute=modify_attribute,
                                                                         overlay=True)
        fun_test.test_assert(create_range, "Ensure range modifier created on %s for attribute %s"
                             % (tcp._spirent_handle, modify_attribute))

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
                                                                                tx_result=True, rx_result=False)

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

            fun_test.test_assert_expected(expected=int(dut_port_3_receive), actual=int(dut_port_2_transmit),
                                          message="Ensure good packets received are transmitted correctly")

        # SPIRENT ASSERT
        '''
        for good_stream in good_stream_handle_list:
            tx_results = stream_result_dict[good_stream]['tx_result']
            rx_results = stream_result_dict[good_stream]['rx_result']
            fun_test.log("good tx results for stream %s is %s" % (good_stream, tx_results))
            fun_test.log("good rx results for stream %s is %s" % (good_stream, rx_results))
            fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                          actual=int(rx_results['FrameCount']),
                                          message="Ensure tx and counter match for %s stream" % good_stream)
        '''
        positive_packets_spirent_tx = 0
        for handle in good_stream_handle_list:
            positive_packets_spirent_tx += int(stream_result_dict[handle]['tx_result']['FrameCount'])

        fun_test.test_assert_expected(expected=int(positive_packets_spirent_tx),
                                      actual=int(port_2_analyzer_result['TotalFrameCount']),
                                      message="Ensure all good streams are transmitted and seen on spirent port_2")


if __name__ == "__main__":
    local_settings = nu_config_obj.get_local_settings_parameters(flow_direction=True, ip_version=True)
    flow_direction = local_settings[nu_config_obj.FLOW_DIRECTION]
    ts = SpirentSetup()
    ts.add_test_case(UlBadIpLenErrorIncremental())
    ts.add_test_case(UlBadUdpXsum())
    ts.add_test_case(UlBadUdpFFFFXsum())
    ts.add_test_case(UlBadTcpXsum())
    ts.add_test_case(OlVxlanBadIpLenErrorIncr())
    ts.add_test_case(OlVxlanBadUdpXsum())
    ts.add_test_case(OlVxlanBadUdpFFFFXsum())
    ts.add_test_case(OlVxlanBadTcpXsum())
    ts.add_test_case(OlVxlanBadTcpZeroXsum())
    ts.add_test_case(OlMplsBadIpLenErrorIncr())
    ts.add_test_case(OlMplsBadUdpXsum())
    ts.add_test_case(OlMplsBadTcpXsum())
    ts.add_test_case(OlMplsBadTcpZeroXsum())
    ts.add_test_case(GoodBad())
    ts.run()