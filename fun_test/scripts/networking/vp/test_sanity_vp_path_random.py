from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, GeneratorConfig, Ethernet2Header, TCP, UDP, RangeModifier, Ipv4Header, Ipv6Header
from lib.host.network_controller import NetworkController
from scripts.networking.helper import *
from scripts.networking.nu_config_manager import *

loads_file = "interface_loads.json"
min_frame_length_ipv4 = 78
min_frame_length_ipv6 = 98
max_frame_length = 9000
overlay_ipv4_min_frame_length = 148
mpls_overlay_min_frame_length = 110
mtu = max_frame_length
generator_step = max_frame_length
cushion_sleep = 5
step_size = 1
num_ports = 2


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
        template_obj = SpirentEthernetTrafficTemplate(session_name="vp-sanity-random", spirent_config=spirent_config,
                                                      chassis_type=chassis_type)
        fun_test.test_assert(template_obj, "Create template object")

        result = template_obj.setup(no_of_ports_needed=num_ports, flow_type=NuConfigManager.VP_FLOW_TYPE,
                                    flow_direction=flow_direction)
        fun_test.test_assert(result['result'], "Configure setup")

        port_1 = result['port_list'][0]
        port_2 = result['port_list'][1]

        dut_port_1 = dut_config['ports'][0]
        dut_port_2 = dut_config['ports'][1]

        # Set Mtu
        interface_1_obj = result['interface_obj_list'][0]
        interface_2_obj = result['interface_obj_list'][1]
        interface_1_obj.Mtu = mtu
        interface_2_obj.Mtu = mtu

        set_mtu_1 = template_obj.configure_physical_interface(interface_1_obj)
        fun_test.test_assert(set_mtu_1, "Set mtu on %s " % interface_1_obj)
        set_mtu_2 = template_obj.configure_physical_interface(interface_2_obj)
        fun_test.test_assert(set_mtu_2, "Set mtu on %s " % interface_2_obj)

        if dut_config['enable_dpcsh']:
            # Create network controller object
            dpcsh_server_ip = dut_config["dpcsh_tcp_proxy_ip"]
            dpcsh_server_port = dut_config['dpcsh_tcp_proxy_port']
            network_controller_obj = NetworkController(dpc_server_ip=dpcsh_server_ip, dpc_server_port=dpcsh_server_port)

            # Enable qos pfc
            set_pfc = network_controller_obj.enable_qos_pfc()
            fun_test.test_assert(set_pfc, message="Enable qos pfc")
            buffer = network_controller_obj.set_qos_egress_buffer_pool(nonfcp_xoff_thr=max_frame_length,
                                                                       fcp_xoff_thr=max_frame_length)
            fun_test.test_assert(buffer, message="Set non fcp xoff threshold")

            # Set mtu on DUT
            mtu_1 = network_controller_obj.set_port_mtu(port_num=dut_port_1, mtu_value=mtu)
            fun_test.test_assert(mtu_1, " Set mtu on DUT port %s" % dut_port_1)
            mtu_2 = network_controller_obj.set_port_mtu(port_num=dut_port_2, mtu_value=mtu)
            fun_test.test_assert(mtu_2, " Set mtu on DUT port %s" % dut_port_2)

        # Configure Generator
        gen_config_obj = GeneratorConfig()
        gen_config_obj.SchedulingMode = gen_config_obj.SCHEDULING_MODE_RATE_BASED
        gen_config_obj.DurationMode = gen_config_obj.DURATION_MODE_SECONDS
        gen_config_obj.Duration = sleep_duration_seconds
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


class VPPathIPv4TCP(FunTestCase):
    streamblock_obj_1 = None
    min_frame_size = min_frame_length_ipv4
    generator_step_size = generator_step

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test VP path from FPG-HU for IPv4 and TCP with random frame sizes "
                                      "from 78B to %s" % max_frame_length,
                              steps="""
                        1. Create streamblock and add ethernet, ipv4 and tcp headers
                        1. Start traffic for random frame sizes
                        2. Compare Tx and Rx results for frame count
                        3. Check for error counters. there must be no error counter
                        4. Check dut ingress and egress frame count match
                        5. Check rx counter on spirent matches with dut egress counter
                        6. Check erp stats for non fcp packets
                        7. Check bam stats before and after traffic
                        8. Check psw nu for main_drop, fwd_error to be 0
                        9. Check psw nu for ifpg, epg0 and fpg counter to match spirent tx count
                        10. Check parser stats for eop_cnt, sop_cnt, prv_sent with spirent tx
                        11. Check vp pkts for vp in, vp out, vp forward nu le with spirent tx
                        """)

    def l4_setup(self):
        tcp = TCP()
        add_tcp = template_obj.stc_manager.configure_frame_stack(stream_block_handle=
                                                                 self.streamblock_obj_1._spirent_handle,
                                                                 header_obj=tcp)
        fun_test.test_assert(add_tcp, "Adding tcp header to frame")

        range_obj = RangeModifier(recycle_count=max_frame_length, step_value=1, data=1024)
        modify_attribute = 'sourcePort'
        create_range = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=range_obj,
                                                                         streamblock_obj=self.streamblock_obj_1,
                                                                         header_obj=tcp,
                                                                         header_attribute=modify_attribute)
        fun_test.test_assert(create_range, "Ensure range modifier created on %s for attribute %s"
                             % (tcp._spirent_handle, modify_attribute))

    def setup(self):
        # Clear port results on DUT
        if dut_config['enable_dpcsh']:
            clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
            fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

            clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
            fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

        #  Read loads from file
        file_path = SCRIPTS_DIR + "/networking" + "/" + loads_file
        output = fun_test.parse_file_to_json(file_path)
        l2_config = spirent_config["l2_config"]
        l3_config = spirent_config["l3_config"]["ipv4"]
        ether_type = Ethernet2Header.INTERNET_IP_ETHERTYPE

        # Create streamblock 1
        self.streamblock_obj_1 = StreamBlock()
        self.streamblock_obj_1.LoadUnit = StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND
        self.streamblock_obj_1.Load = fps
        self.streamblock_obj_1.FillType = StreamBlock.FILL_TYPE_PRBS
        self.streamblock_obj_1.InsertSig = True
        self.streamblock_obj_1.FrameLengthMode = StreamBlock.FRAME_LENGTH_MODE_RANDOM
        self.streamblock_obj_1.MinFrameLength = min_frame_length_ipv4
        self.streamblock_obj_1.MaxFrameLength = max_frame_length
        self.streamblock_obj_1.StepFrameLength = step_size

        streamblock1 = template_obj.configure_stream_block(self.streamblock_obj_1, port_1)
        fun_test.test_assert(streamblock1, "Creating streamblock on port %s" % port_1)

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=self.streamblock_obj_1.spirent_handle,
                                                               source_mac=l2_config['source_mac'],
                                                               destination_mac=l2_config['destination_mac'],
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Adding source and destination mac")

        # Adding Ip address and gateway
        destination = l3_config['hu_destination_ip1']
        if flow_direction == NuConfigManager.FLOW_DIRECTION_HU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_HNU:
            destination = l3_config['hnu_destination_ip1']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_CC:
            destination = l3_config['cc_destination_ip1']
        ip = template_obj.stc_manager.configure_ip_address(streamblock=self.streamblock_obj_1.spirent_handle,
                                                           source=l3_config['source_ip1'],
                                                           destination=destination)
        fun_test.test_assert(ip, "Adding source ip, dest ip and gateway")

    def cleanup(self):
        fun_test.log("In testcase cleanup")

        fun_test.log("Deleting streamblock %s " % self.streamblock_obj_1.spirent_handle)
        template_obj.delete_streamblocks(streamblock_handle_list=[self.streamblock_obj_1.spirent_handle])

        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        # Adding l4 header
        fun_test.add_checkpoint("Adding l4 header")
        self.l4_setup()

        if dut_config['enable_dpcsh']:
            # Get stats before starting traffic
            fun_test.log("Get stats before starting traffic")
            fun_test.sleep("Sleeping to clear bam stats", seconds=5)
            bam_stats_1 = get_bam_stats_values(network_controller_obj=network_controller_obj)
            parser_stats_1 = network_controller_obj.peek_parser_stats()
            vp_pkts_stats_1 = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)
            erp_stats_1 = get_erp_stats_values(network_controller_obj=network_controller_obj)
            psw_stats_1 = network_controller_obj.peek_psw_global_stats()
            wro_stats_1 = network_controller_obj.peek_wro_global_stats()

        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=[gen_obj_1])
        fun_test.test_assert(start, "Starting generator configs")

        stream_handle_1 = self.streamblock_obj_1.spirent_handle

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic for %s seconds" % sleep_duration_seconds,
                       seconds=sleep_duration_seconds)

        stop = template_obj.disable_generator_configs(generator_configs=[gen_obj_1])
        fun_test.test_assert(stop, "Stopping generator configs")

        fun_test.sleep("Letting rx to take place", seconds=2)

        # Asserts
        stream_result_dict = template_obj.stc_manager.fetch_streamblock_results(subscribe_result=subscribe_results,
                                                                                streamblock_handle_list=
                                                                                [stream_handle_1],
                                                                                tx_result=True, rx_result=True)

        port_result_dict = template_obj.stc_manager.fetch_port_results(subscribe_result=subscribe_results,
                                                                       port_handle_list=[port_2], analyzer_result=True)

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

            dut_port_2_transmit = get_dut_output_stats_value(dut_port_2_results, FRAMES_TRANSMITTED_OK)
            dut_port_1_receive = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)

            fun_test.log("Get system stats after traffic execution")
            fun_test.sleep("Sleeping to clear bam stats", seconds=5)
            bam_stats_2 = get_bam_stats_values(network_controller_obj=network_controller_obj)
            parser_stats_2 = network_controller_obj.peek_parser_stats()
            vp_pkts_stats_2 = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)
            erp_stats_2 = get_erp_stats_values(network_controller_obj=network_controller_obj)
            psw_stats_2 = network_controller_obj.peek_psw_global_stats()
            wro_stats_2 = network_controller_obj.peek_wro_global_stats()

            dut_port_2_fpg_value = get_fpg_port_value(dut_port_2)
            dut_port_1_fpg_value = get_fpg_port_value(dut_port_1)
            frv_error = 'frv_error'
            main_pkt_drop_eop = 'main_pkt_drop_eop'
            epg0_pkt = 'epg0_pkt'
            ifpg2 = 'ifpg' + str(dut_port_1_fpg_value) + '_pkt'
            fpg1 = 'fpg' + str(dut_port_2_fpg_value) + '_pkt'
            input_list = [frv_error, main_pkt_drop_eop, epg0_pkt, ifpg2]
            output_list = [epg0_pkt, fpg1]

            parsed_psw_stats_1 = get_psw_global_stats_values(psw_stats_output=psw_stats_1, input=True,
                                                             input_key_list=input_list, output=True,
                                                             output_key_list=output_list)
            parsed_psw_stats_2 = get_psw_global_stats_values(psw_stats_output=psw_stats_2, input=True,
                                                             input_key_list=input_list, output=True,
                                                             output_key_list=output_list)
            parsed_input_1 = parsed_psw_stats_1['input']
            parsed_output_1 = parsed_psw_stats_1['output']
            parsed_input_2 = parsed_psw_stats_2['input']
            parsed_output_2 = parsed_psw_stats_2['output']

            fun_test.test_assert_expected(expected=int(dut_port_1_receive), actual=int(dut_port_2_transmit),
                                          message="Ensure frames received on DUT port %s are transmitted from DUT port %s"
                                                  % (dut_port_2, dut_port_1))

            fun_test.test_assert_expected(expected=int(dut_port_2_transmit), actual=int(rx_results_1['FrameCount']),
                                          message="Ensure frames transmitted from DUT and counter on spirent match")

            # Check system stats
            # Check bam stats
            del bam_stats_2['durations_histogram']
            del bam_stats_1['durations_histogram']
            del bam_stats_2['num_bytes_in_use']
            del bam_stats_1['num_bytes_in_use']
            del bam_stats_2['num_in_use']
            del bam_stats_1['num_in_use']
            fun_test.test_assert(bam_stats_1 == bam_stats_2, message="Check BAM stats before and after match")

            # Check ERP stats
            diff_stats_erp = get_diff_stats(old_stats=erp_stats_1, new_stats=erp_stats_2,
                                            stats_list=[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED])
            fun_test.test_assert_expected(expected=(int(diff_stats_erp[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED])),
                                          actual=(int(tx_results_1['FrameCount'])),
                                          message="Check non fcp packets counter from erp stats")

            stats_list = [VP_PACKETS_TOTAL_IN, VP_PACKETS_TOTAL_OUT, VP_PACKETS_FORWARDING_NU_LE]
            if flow_direction == NuConfigManager.FLOW_DIRECTION_HU_FPG:
                stats_list = [VP_PACKETS_TOTAL_IN, VP_PACKETS_TOTAL_OUT, VP_PACKETS_OUT_ETP, VP_FAE_REQUESTS_SENT,
                              VP_FAE_RESPONSES_RECEIVED]
                diff_stats_vppkts = get_diff_stats(old_stats=vp_pkts_stats_1, new_stats=vp_pkts_stats_2,
                                                   stats_list=stats_list)

                fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']),
                                              actual=int(diff_stats_vppkts[VP_PACKETS_OUT_ETP]),
                                              message="Ensure VP stats has correct etp out packets")

                fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']),
                                              actual=int(diff_stats_vppkts[VP_FAE_REQUESTS_SENT]),
                                              message="Ensure VP stats has correct fae requests sent")

                fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']),
                                              actual=int(diff_stats_vppkts[VP_FAE_RESPONSES_RECEIVED]),
                                              message="Ensure VP stats has correct fae responses received")
            else:
                diff_stats_vppkts = get_diff_stats(old_stats=vp_pkts_stats_1, new_stats=vp_pkts_stats_2,
                                                   stats_list=stats_list)
                fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']),
                                              actual=int(diff_stats_vppkts[VP_PACKETS_FORWARDING_NU_LE]),
                                              message="Ensure VP stats has correct nu le packets")

            fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']),
                                          actual=int(diff_stats_vppkts[VP_PACKETS_TOTAL_IN]),
                                          message="Ensure VP stats has correct total in packets")

            fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']),
                                          actual=int(diff_stats_vppkts[VP_PACKETS_TOTAL_OUT]),
                                          message="Ensure VP stats has correct total out packets")

            # Check psw nu stats
            for key in input_list:
                if key in parsed_input_1:
                    actual = int(parsed_input_2[key]) - int(parsed_input_1[key])
                else:
                    actual = int(parsed_input_2[key])
                if key == main_pkt_drop_eop or key == frv_error:
                    fun_test.test_assert_expected(expected=0, actual=actual,
                                                  message="Errors for %s must be 0 in psw nu" % key)
                else:
                    fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']),
                                                  actual=actual,
                                                  message="Check %s counter in psw nu stats in input" % key)
            for key in output_list:
                if key in parsed_output_1:
                    actual = int(parsed_output_2[key]) - int(parsed_output_1[key])
                else:
                    actual = int(parsed_output_2[key])
                fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']),
                                              actual=actual,
                                              message="Check %s counter in psw nu stats in output" % key)

            # Check parser stats
            out = validate_parser_stats(parser_result=parser_stats_2, compare_value=int(tx_results_1['FrameCount']),
                                        check_list_keys=['erp', 'etp', 'fpg' + str(dut_port_1_fpg_value)],
                                        parser_old_result=parser_stats_1)
            if flow_direction == NuConfigManager.FLOW_DIRECTION_HU_FPG:
                out = validate_parser_stats(parser_result=parser_stats_2, compare_value=int(tx_results_1['FrameCount']),
                                            check_list_keys=['erp', 'etp', 'fpg' + str(dut_port_2_fpg_value), 'fae'],
                                            parser_old_result=parser_stats_1)
            fun_test.test_assert(out, message="Check parser nu stats")

        # SPIRENT ASSERTS
        fun_test.test_assert_expected(int(tx_results_1['FrameCount']), actual=rx_results_1['FrameCount'],
                                      message="Ensure frames transmitted and received on spirent match from %s" % flow_direction)

        zero_counter_seen = template_obj.check_non_zero_error_count(port_2_analyzer_result)
        if "PrbsErrorFrameCount" in zero_counter_seen.keys():
            zero_counter_seen['result'] = True
        fun_test.test_assert(zero_counter_seen['result'], "Check for error counters on port2")


class VPPathIPv4UDP(VPPathIPv4TCP):
    generator_step_size = generator_step

    def describe(self):
        self.set_test_details(id=2,
                              summary="Test VP path from FPG-HU using random frame sizes between "
                                      "78B to %s for IPv4 and UDP" % max_frame_length,
                              steps="""
                        1. Create streamblock and add ethernet, ipv4 and udp headers
                        2. Start traffic for random frame sizes
                        3. Compare Tx and Rx results for frame count
                        4. Check for error counters. there must be no error counter
                        5. Check rx counter on spirent matches with dut egress counter
                        6. Check erp stats for non fcp packets
                        7. Check bam stats before and after traffic
                        8. Check psw nu for main_drop, fwd_error to be 0
                        9. Check psw nu for ifpg, epg0 and fpg counter to match spirent tx count
                        10. Check parser stats for eop_cnt, sop_cnt, prv_sent with spirent tx
                        11. Check vp pkts for vp in, vp out, vp forward nu le with spirent tx
                              """)

    def l4_setup(self):
        udp = UDP()
        add_udp = template_obj.stc_manager.configure_frame_stack(stream_block_handle=
                                                                 self.streamblock_obj_1._spirent_handle,
                                                                 header_obj=udp)
        fun_test.test_assert(add_udp, "Adding udp header to frame")

        range_obj = RangeModifier(recycle_count=max_frame_length, step_value=1, data=1024)
        modify_attribute = 'sourcePort'
        create_range = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=range_obj,
                                                                         streamblock_obj=self.streamblock_obj_1,
                                                                         header_obj=udp,
                                                                         header_attribute=modify_attribute)
        fun_test.test_assert(create_range, "Ensure range modifier created on %s for attribute %s"
                             % (udp._spirent_handle, modify_attribute))

    def setup(self):
        super(VPPathIPv4UDP, self).setup()

    def run(self):
        super(VPPathIPv4UDP, self).run()

    def cleanup(self):
        super(VPPathIPv4UDP, self).cleanup()


class VPPathIPv6TCP(VPPathIPv4TCP):

    def describe(self):
        self.set_test_details(id=3,
                              summary="Test VP path from FPG-HU for IPv6 and TCP with random frame sizes "
                                      "from 98B to %s" % max_frame_length,
                              steps="""
                        1. Create streamblock and add ethernet, ipv6 and tcp headers
                        2. Start traffic for random frame sizes
                        3. Compare Tx and Rx results for frame count
                        4. Check for error counters. there must be no error counter
                        5. Check dut ingress and egress frame count match
                        6. Check rx counter on spirent matches with dut egress counter
                        7. Check erp stats for non fcp packets
                        8. Check bam stats before and after traffic
                        9. Check psw nu for main_drop, fwd_error to be 0
                        10. Check psw nu for ifpg, epg0 and fpg counter to match spirent tx count
                        11. Check parser stats for eop_cnt, sop_cnt, prv_sent with spirent tx
                        12. Check vp pkts for vp in, vp out, vp forward nu le with spirent tx
                        """)

    def setup(self):
        # Clear port results on DUT
        if dut_config['enable_dpcsh']:
            clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
            fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

            clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
            fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

        #  Read loads from file
        file_path = SCRIPTS_DIR + "/networking" "/" + loads_file
        output = fun_test.parse_file_to_json(file_path)
        l2_config = spirent_config["l2_config"]
        l3_config = spirent_config["l3_config"]["ipv6"]
        ether_type = Ethernet2Header.INTERNET_IPV6_ETHERTYPE

        # Create streamblock 1
        self.streamblock_obj_1 = StreamBlock()
        self.streamblock_obj_1.LoadUnit = StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND
        self.streamblock_obj_1.Load = fps
        self.streamblock_obj_1.FillType = StreamBlock.FILL_TYPE_PRBS
        self.streamblock_obj_1.InsertSig = True
        self.streamblock_obj_1.FrameLengthMode = StreamBlock.FRAME_LENGTH_MODE_RANDOM
        self.streamblock_obj_1.MinFrameLength = min_frame_length_ipv6
        self.streamblock_obj_1.MaxFrameLength = max_frame_length
        self.streamblock_obj_1.StepFrameLength = step_size

        streamblock1 = template_obj.configure_stream_block(stream_block_obj=self.streamblock_obj_1,
                                                           port_handle=port_1, ip_header_version=6)
        fun_test.test_assert(streamblock1, "Configure streamblock")

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=self.streamblock_obj_1.spirent_handle,
                                                               source_mac=l2_config['source_mac'],
                                                               destination_mac=l2_config['destination_mac'],
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Adding source and destination mac")

        ipv6 = streamblock1['ip_header_obj']
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
        ipv6.nextHeader = ipv6.NEXT_HEADER_TCP

        ipv6_header = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=self.streamblock_obj_1._spirent_handle, header_obj=ipv6, update=True)
        fun_test.test_assert(ipv6_header, "Add ipv6 header to stream")

    def run(self):
        super(VPPathIPv6TCP, self).run()

    def cleanup(self):
        super(VPPathIPv6TCP, self).cleanup()


class VPPathIPv6UDP(VPPathIPv6TCP):

    def describe(self):
        self.set_test_details(id=4,
                              summary="Test VP path from FPG-HU using random frame sizes between "
                                      "98B to %s for IPv6 and UDP" % max_frame_length,
                              steps="""
                        1. Create streamblock and add ethernet, ipv6 and udp headers
                        2. Start traffic for random frame sizes
                        3. Compare Tx and Rx results for frame count
                        4. Check for error counters. there must be no error counter
                        5. Check dut ingress and egress frame count match
                        6. Check rx counter on spirent matches with dut egress counter
                        7. Check erp stats for non fcp packets
                        8. Check bam stats before and after traffic
                        9. Check psw nu for main_drop, fwd_error to be 0
                        10. Check psw nu for ifpg, epg0 and fpg counter to match spirent tx count
                        11. Check parser stats for eop_cnt, sop_cnt, prv_sent with spirent tx
                        12. Check vp pkts for vp in, vp out, vp forward nu le with spirent tx
                        """)

    def l4_setup(self):
        udp = UDP()
        add_udp = template_obj.stc_manager.configure_frame_stack(stream_block_handle=
                                                                 self.streamblock_obj_1._spirent_handle,
                                                                 header_obj=udp)
        fun_test.test_assert(add_udp, "Adding udp header to frame")

        range_obj = RangeModifier(recycle_count=max_frame_length, step_value=1, data=1024)
        modify_attribute = 'sourcePort'
        create_range = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=range_obj,
                                                                         streamblock_obj=self.streamblock_obj_1,
                                                                         header_obj=udp,
                                                                         header_attribute=modify_attribute)
        fun_test.test_assert(create_range, "Ensure range modifier created on %s for attribute %s"
                             % (udp._spirent_handle, modify_attribute))

    def setup(self):
        if dut_config['enable_dpcsh']:
            clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
            fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

            clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
            fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

        #  Read loads from file
        file_path = SCRIPTS_DIR + "/networking" "/" + loads_file
        output = fun_test.parse_file_to_json(file_path)
        l2_config = spirent_config["l2_config"]
        l3_config = spirent_config["l3_config"]["ipv6"]
        ether_type = Ethernet2Header.INTERNET_IPV6_ETHERTYPE

        # Create streamblock 1
        self.streamblock_obj_1 = StreamBlock()
        self.streamblock_obj_1.LoadUnit = StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND
        self.streamblock_obj_1.Load = fps
        self.streamblock_obj_1.FillType = StreamBlock.FILL_TYPE_PRBS
        self.streamblock_obj_1.InsertSig = True
        self.streamblock_obj_1.FrameLengthMode = StreamBlock.FRAME_LENGTH_MODE_RANDOM
        self.streamblock_obj_1.MinFrameLength = min_frame_length_ipv6
        self.streamblock_obj_1.MaxFrameLength = max_frame_length
        self.streamblock_obj_1.StepFrameLength = step_size

        streamblock1 = template_obj.configure_stream_block(stream_block_obj=self.streamblock_obj_1,
                                                           port_handle=port_1, ip_header_version=6)
        fun_test.test_assert(streamblock1, "Configure streamblock")

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=self.streamblock_obj_1.spirent_handle,
                                                               source_mac=l2_config['source_mac'],
                                                               destination_mac=l2_config['destination_mac'],
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Adding source and destination mac")

        ipv6 = streamblock1['ip_header_obj']
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
        ipv6.nextHeader = ipv6.NEXT_HEADER_UDP

        ipv6_header = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=self.streamblock_obj_1._spirent_handle, header_obj=ipv6, update=True)
        fun_test.test_assert(ipv6_header, "Add ipv6 header to stream")

    def run(self):
        super(VPPathIPv6UDP, self).run()

    def cleanup(self):
        super(VPPathIPv6UDP, self).cleanup()


class OverlayIpv4TCP(VPPathIPv4TCP):
    streamblock_obj_1 = None
    min_frame_size = overlay_ipv4_min_frame_length
    update_header = TCP()

    def describe(self):
        self.set_test_details(id=5,
                              summary="Test VP path from FPG-HU for overlay packet with IPv4 and TCP "
                                      "with fixed frame size",
                              steps="""
                            1. Create overlay stream on spirent and start traffic
                            2. Compare Tx and Rx results for frame count
                            3. Check for error counters. there must be no error counter
                            4. Check dut ingress and egress frame count match
                            5. Check egress frame count with spirent rx counter
                            6. Check rx counter on spirent matches with dut egress counter
                            7. Check erp stats for non fcp packets
                            8. Check bam stats before and after traffic
                            9. Check psw nu for main_drop, fwd_error to be 0
                            10. Check psw nu for ifpg, epg0 and fpg counter to match spirent tx count
                            11. Check parser stats for eop_cnt, sop_cnt, prv_sent with spirent tx
                            12. Check vp pkts for vp in, vp out, vp forward nu le with spirent tx
                            """)

    def stream_type(self):
        return template_obj.ETH_IPV4_UDP_VXLAN_ETH_IPV4_TCP

    def l4_setup(self):
        pass

    def setup(self):
        # Clear port results on DUT
        if dut_config['enable_dpcsh']:
            clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
            fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

            clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
            fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

        configure_overlay = template_obj.configure_overlay_frame_stack(
            port=port_1, overlay_type=self.stream_type())
        fun_test.test_assert(configure_overlay['result'], message="Configure overlay stream")
        self.streamblock_obj_1 = configure_overlay['streamblock_obj']

        l3_config = spirent_config["l3_config"]["ipv4"]
        update_header = Ipv4Header()
        # Adding Ip address and gateway
        destination = l3_config['hu_destination_ip1']
        if flow_direction == NuConfigManager.FLOW_DIRECTION_HU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_HNU:
            destination = l3_config['hnu_destination_ip1']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_CC:
            destination = l3_config['cc_destination_ip1']
        update = template_obj.update_overlay_frame_header(streamblock_obj=self.streamblock_obj_1,
                                                          header_obj=update_header, overlay=False,
                                                          updated_header_attributes_dict=
                                                          {'destAddr': destination})
        fun_test.test_assert(update, message="Update ipv4 destination address")

        range_obj = RangeModifier(recycle_count=max_frame_length, step_value=1, data=1024)
        modify_attribute = 'sourcePort'
        create_range = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=range_obj,
                                                                         streamblock_obj=self.streamblock_obj_1,
                                                                         header_obj=self.update_header,
                                                                         header_attribute=modify_attribute,
                                                                         overlay=True)
        fun_test.test_assert(create_range, "Ensure range modifier created for attribute %s"
                             % modify_attribute)

        self.streamblock_obj_1.Load = fps
        self.streamblock_obj_1.LoadUnit = self.streamblock_obj_1.LOAD_UNIT_FRAMES_PER_SECOND
        self.streamblock_obj_1.FillType = self.streamblock_obj_1.FILL_TYPE_PRBS

        if self.stream_type() == template_obj.MPLS_ETH_IPV4_UDP_CUST_IPV4_UDP:
            self.streamblock_obj_1.FrameLengthMode = self.streamblock_obj_1.FRAME_LENGTH_MODE_RANDOM
            self.streamblock_obj_1.MinFrameLength = overlay_ipv4_min_frame_length
            self.streamblock_obj_1.MaxFrameLength = max_frame_length
        else:
            self.streamblock_obj_1.FixedFrameLength = overlay_ipv4_min_frame_length

        stream_update = template_obj.configure_stream_block(stream_block_obj=self.streamblock_obj_1, update=True)
        fun_test.test_assert(stream_update, message="Updated streamblock %s" % self.streamblock_obj_1._spirent_handle)

    def run(self):
        super(OverlayIpv4TCP, self).run()

    def cleanup(self):
        super(OverlayIpv4TCP, self).cleanup()


class OverlayIpv4UDP(OverlayIpv4TCP):
    update_header = UDP()

    def describe(self):
        self.set_test_details(id=6,
                              summary="Test VP path from FPG-HU for overlay packet with IPv4 and UDP "
                                      "with frame size random "
                                      "from 148B to %s" % max_frame_length,
                              steps="""
                            1. Create overlay stream on spirent and start traffic in random
                            2. Compare Tx and Rx results for frame count
                            3. Check for error counters. there must be no error counter
                            4. Check dut ingress and egress frame count match
                            5. Check egress frame count with spirent rx counter
                            6. Check rx counter on spirent matches with dut egress counter
                            7. Check erp stats for non fcp packets
                            8. Check bam stats before and after traffic
                            9. Check psw nu for main_drop, fwd_error to be 0
                            10. Check psw nu for ifpg, epg0 and fpg counter to match spirent tx count
                            11. Check parser stats for eop_cnt, sop_cnt, prv_sent with spirent tx
                            12. Check vp pkts for vp in, vp out, vp forward nu le with spirent tx
                            """)

    def stream_type(self):
        return template_obj.ETH_IPV4_UDP_VXLAN_ETH_IPV4_UDP

    def l4_setup(self):
        super(OverlayIpv4UDP, self).l4_setup()

    def setup(self):
        super(OverlayIpv4UDP, self).setup()

        update = template_obj.update_overlay_frame_header(streamblock_obj=self.streamblock_obj_1,
                                                          header_obj=self.update_header, overlay=True,
                                                          updated_header_attributes_dict=
                                                          {'checksum': '0'})
        fun_test.test_assert(update, message="Update checksum to 0 in overlay")

    def run(self):
        super(OverlayIpv4UDP, self).run()

    def cleanup(self):
        super(OverlayIpv4UDP, self).cleanup()


class OverlayMPLSTCP(OverlayIpv4TCP):
    update_header = TCP()

    def describe(self):
        self.set_test_details(id=7,
                              summary="Test VP path from FPG-HU for MPLS overlay packet with IPv4 and TCP "
                                      "with fixed frame size",
                              steps="""
                            1. Create overlay stream on spirent and start traffic in random
                            2. Compare Tx and Rx results for frame count
                            3. Check for error counters. there must be no error counter
                            4. Check dut ingress and egress frame count match
                            5. Check egress frame count with spirent rx counter
                            6. Check rx counter on spirent matches with dut egress counter
                            7. Check erp stats for non fcp packets
                            8. Check bam stats before and after traffic
                            9. Check psw nu for main_drop, fwd_error to be 0
                            10. Check psw nu for ifpg, epg0 and fpg counter to match spirent tx count
                            11. Check parser stats for eop_cnt, sop_cnt, prv_sent with spirent tx
                            12. Check vp pkts for vp in, vp out, vp forward nu le with spirent tx
                            """)

    def stream_type(self):
        return template_obj.MPLS_ETH_IPV4_UDP_CUST_IPV4_TCP

    def l4_setup(self):
        super(OverlayMPLSTCP, self).l4_setup()

    def setup(self):
        # Clear port results on DUT
        if dut_config['enable_dpcsh']:
            clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
            fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

            clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
            fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

        configure_overlay = template_obj.configure_overlay_frame_stack(
            port=port_1, overlay_type=self.stream_type(), mpls=True)
        fun_test.test_assert(configure_overlay['result'], message="Configure overlay stream")
        self.streamblock_obj_1 = configure_overlay['streamblock_obj']

        l3_config = spirent_config["l3_config"]["ipv4"]
        # Adding Ip address and gateway
        destination = l3_config['hu_destination_ip1']
        if flow_direction == NuConfigManager.FLOW_DIRECTION_HU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_FPG:
            destination = l3_config['destination_ip2']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_HNU:
            destination = l3_config['hnu_destination_ip1']
        elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_CC:
            destination = l3_config['cc_destination_ip1']
        update_header = Ipv4Header()
        update = template_obj.update_overlay_frame_header(streamblock_obj=self.streamblock_obj_1,
                                                          header_obj=update_header, overlay=False,
                                                          updated_header_attributes_dict=
                                                          {'destAddr': destination})
        fun_test.test_assert(update, message="Update ipv4 destination address in underlay")

        range_obj = RangeModifier(recycle_count=max_frame_length, step_value=1, data=1024)
        modify_attribute = 'sourcePort'
        create_range = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=range_obj,
                                                                         streamblock_obj=self.streamblock_obj_1,
                                                                         header_obj=self.update_header,
                                                                         header_attribute=modify_attribute,
                                                                         overlay=True)
        fun_test.test_assert(create_range, "Ensure range modifier created for attribute %s"
                             % modify_attribute)

        self.streamblock_obj_1.Load = fps
        self.streamblock_obj_1.LoadUnit = self.streamblock_obj_1.LOAD_UNIT_FRAMES_PER_SECOND
        self.streamblock_obj_1.FillType = self.streamblock_obj_1.FILL_TYPE_PRBS
        if self.stream_type() == template_obj.MPLS_ETH_IPV4_UDP_CUST_IPV4_UDP:
            self.streamblock_obj_1.FrameLengthMode = self.streamblock_obj_1.FRAME_LENGTH_MODE_RANDOM
            self.streamblock_obj_1.MinFrameLength = overlay_ipv4_min_frame_length
            self.streamblock_obj_1.MaxFrameLength = max_frame_length
        else:
            self.streamblock_obj_1.FixedFrameLength = overlay_ipv4_min_frame_length

        stream_update = template_obj.configure_stream_block(stream_block_obj=self.streamblock_obj_1, update=True)
        fun_test.test_assert(stream_update, message="Updated streamblock %s" % self.streamblock_obj_1._spirent_handle)

    def run(self):
        super(OverlayMPLSTCP, self).run()

    def cleanup(self):
        super(OverlayMPLSTCP, self).cleanup()


class OverlayMPLSUDP(OverlayMPLSTCP):
    update_header = UDP()

    def describe(self):
        self.set_test_details(id=8,
                              summary="Test VP path from FPG-HU for MPLS overlay packet with IPv4 and UDP "
                                      "with frame size random "
                                      "from 148B to %s" % max_frame_length,
                              steps="""
                            1. Create overlay stream on spirent and start traffic in random
                            2. Compare Tx and Rx results for frame count
                            3. Check for error counters. there must be no error counter
                            4. Check dut ingress and egress frame count match
                            5. Check egress frame count with spirent rx counter
                            6. Check rx counter on spirent matches with dut egress counter
                            7. Check erp stats for non fcp packets
                            8. Check bam stats before and after traffic
                            9. Check psw nu for main_drop, fwd_error to be 0
                            10. Check psw nu for ifpg, epg0 and fpg counter to match spirent tx count
                            11. Check parser stats for eop_cnt, sop_cnt, prv_sent with spirent tx
                            12. Check vp pkts for vp in, vp out, vp forward nu le with spirent tx
                            """)

    def stream_type(self):
        return template_obj.MPLS_ETH_IPV4_UDP_CUST_IPV4_UDP

    def l4_setup(self):
        super(OverlayMPLSUDP, self).l4_setup()

    def setup(self):
        super(OverlayMPLSUDP, self).setup()

        update = template_obj.update_overlay_frame_header(streamblock_obj=self.streamblock_obj_1,
                                                          header_obj=self.update_header, overlay=True,
                                                          updated_header_attributes_dict=
                                                          {'checksum': '0'})
        fun_test.test_assert(update, message="Update udp checksum to 0 in overlay")

    def run(self):
        super(OverlayMPLSUDP, self).run()

    def cleanup(self):
        super(OverlayMPLSUDP, self).cleanup()


if __name__ == "__main__":
    local_settings = nu_config_obj.get_local_settings_parameters(flow_direction=True, ip_version=True)
    flow_direction = nu_config_obj.FLOW_DIRECTION_FPG_HU
    ip_version = local_settings[nu_config_obj.IP_VERSION]
    fps = 150
    if flow_direction == NuConfigManager.FLOW_DIRECTION_HU_FPG:
        fps = 50
    elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_FPG:
        fps = 50
    elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_HNU:
        fps = 50
    elif flow_direction == NuConfigManager.FLOW_DIRECTION_HNU_CC:
        fps = 50
    sleep_duration_seconds = (generator_step / fps) + cushion_sleep
    ts = SpirentSetup()
    if ip_version == '6':
        ts.add_test_case(VPPathIPv6TCP())
        ts.add_test_case(VPPathIPv6UDP())
    elif ip_version == '4':
        ts.add_test_case(VPPathIPv4TCP())
        ts.add_test_case(VPPathIPv4UDP())
        ts.add_test_case(OverlayIpv4TCP())
        ts.add_test_case(OverlayIpv4UDP())
        ts.add_test_case(OverlayMPLSTCP())
        ts.add_test_case(OverlayMPLSUDP())
    else:
        ts.add_test_case(VPPathIPv4TCP())
        ts.add_test_case(VPPathIPv4UDP())
        ts.add_test_case(OverlayMPLSTCP())
        ts.add_test_case(OverlayMPLSUDP())
        ts.add_test_case(VPPathIPv6TCP())
        ts.add_test_case(VPPathIPv6UDP())
    ts.run()