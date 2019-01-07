from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, Ethernet2Header, Ipv4Header, Capture, GeneratorConfig
from lib.host.network_controller import NetworkController
from scripts.networking.helper import *
from scripts.networking.nu_config_manager import nu_config_obj
from lib.utilities.pcap_parser import PcapParser

num_ports = 4
dscp_high = 0
dscp_low = 1
dscp_value = 0
ls_octet = '00000001'
pfc_quanta = '65535'
quanta_value = 6000
zero_quanta_value = 0
threshold_value = 600
min_thr = 512
shr_thr = 2000
hdr_thr = 20
xoff_enable = 1
shared_xon_thr = 5
port1_port2_dscp0_frame_len = 64
port3_port2_dscp0_frame_len = 128
port3_port4_dscp0_frame_len = 264
port3_port2_dscp1_frame_len = 512


class SpirentSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
                1. Create Spirent template
                2. Connect chassis, labserver and licenseserver
                3. Attach 4 Ports
                4. Configure stream with dscp 0 on port 1 to port_2, port 3 to port_2 and port_3 to port_4 
                5. Configure pfc stream for priority 0 on port 2
                6. Configure another stream with dscp 2 on port 3 to port_2
                """)

    def setup(self):
        global template_obj, port_1, port_2, port_3, subscribe_results, network_controller_obj, dut_port_2, \
            dut_port_1, dut_port_3, dut_port_4, shape, hnu, dut_port_list, port_obj_list, port_1_dscp_0_stream, \
            port_3_dscp_0_stream_1, port_3_dscp_0_stream_2, port_3_dscp_1_stream, port_2_pfc_stream

        dut_port_list = []
        map_list = [x for x in range(16)]
        map_list.reverse()
        dut_type = fun_test.get_local_setting(setting="dut_type")
        dut_config = nu_config_obj.read_dut_config(dut_type=dut_type, flow_direction=flow_direction)

        shape = 0
        hnu = False
        if flow_direction == nu_config_obj.FLOW_DIRECTION_HNU_HNU:
            shape = 1
            hnu = True

        chassis_type = fun_test.get_local_setting(setting="chassis_type")
        spirent_config = nu_config_obj.read_traffic_generator_config()

        good_stream_load = 250
        pfc_load = 30
        fun_test.log("Creating Template object")
        template_obj = SpirentEthernetTrafficTemplate(session_name="test_pfc_4ports", chassis_type=chassis_type,
                                                      spirent_config=spirent_config)
        fun_test.test_assert(template_obj, "Create template object")

        # Create network controller object
        dpcsh_server_ip = dut_config['dpcsh_tcp_proxy_ip']
        dpcsh_server_port = int(dut_config['dpcsh_tcp_proxy_port'])
        network_controller_obj = NetworkController(dpc_server_ip=dpcsh_server_ip, dpc_server_port=dpcsh_server_port)

        flow_dir = nu_config_obj.FLOW_DIRECTION_NU_NU
        if hnu:
            flow_dir = nu_config_obj.FLOW_DIRECTION_HNU_HNU
        result = template_obj.setup(no_of_ports_needed=num_ports, flow_direction=flow_dir)
        fun_test.test_assert(result['result'], "Configure setup")

        port_obj_list = result['port_list']
        port_1 = port_obj_list[0]
        port_2 = port_obj_list[1]
        port_3 = port_obj_list[2]
        port_4 = port_obj_list[3]

        destination_mac1 = spirent_config['l2_config']['destination_mac']
        destination_ip1 = spirent_config['l3_config']['ipv4']['destination_ip1']
        destination_ip4 = spirent_config['l3_config']['ipv4']['destination_ip4']
        if hnu:
            destination_ip1 = spirent_config['l3_config']['ipv4']['hnu_destination_ip1']
            destination_ip4 = spirent_config['l3_config']['ipv4']['hnu_destination_ip4']
        dut_port_1 = dut_config['ports'][0]
        dut_port_2 = dut_config['ports'][1]
        dut_port_3 = dut_config['ports'][2]
        dut_port_4 = dut_config['ports'][3]
        dut_port_list.append(dut_port_1)
        dut_port_list.append(dut_port_2)
        dut_port_list.append(dut_port_3)
        dut_port_list.append(dut_port_4)

        gen_config_obj = GeneratorConfig(scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        for port in port_obj_list:
            gen_obj_1 = template_obj.stc_manager.get_generator(port_handle=port)
            config_obj = template_obj.configure_generator_config(port_handle=port,
                                                                 generator_config_obj=gen_config_obj)
            fun_test.test_assert(config_obj, "Creating generator config on port %s" % port)

        pfc_enable = network_controller_obj.enable_qos_pfc(hnu=hnu)
        fun_test.test_assert(pfc_enable, "Ensure qos pfc is enabled")

        for dut_port in dut_port_list:
            enable_1 = network_controller_obj.enable_priority_flow_control(dut_port, shape=shape)
            fun_test.test_assert(enable_1, "Enable pfc on port %s" % dut_port)

        for dut_port in dut_port_list[::2]:
            # set quanta value
            port_quanta = network_controller_obj.set_priority_flow_control_quanta(port_num=dut_port,
                                                                                  quanta=quanta_value,
                                                                                  class_num=dscp_value,
                                                                                  shape=shape)
            fun_test.test_assert(port_quanta, "Ensure quanta %s is set on port %s" % (quanta_value, dut_port))

            # set threshold value
            port_thr = network_controller_obj.set_priority_flow_control_threshold(port_num=dut_port,
                                                                                  threshold=threshold_value,
                                                                                  class_num=dscp_value,
                                                                                  shape=shape)
            fun_test.test_assert(port_thr, "Ensure threshold %s is set on port %s" % (port_thr, dut_port))

            set_qos_ingress = network_controller_obj.set_qos_ingress_priority_group(port_num=dut_port,
                                                                                    priority_group_num=dscp_value,
                                                                                    min_threshold=min_thr,
                                                                                    shared_threshold=shr_thr,
                                                                                    headroom_threshold=hdr_thr,
                                                                                    xoff_enable=xoff_enable,
                                                                                    shared_xon_threshold=shared_xon_thr)
            fun_test.test_assert(set_qos_ingress, "Setting qos ingress priority group on %s" % dut_port)

            # set ingress priority to pg map list
            set_ingress_priority_map = network_controller_obj.set_qos_priority_to_pg_map(port_num=dut_port,
                                                                                         map_list=map_list)
            fun_test.test_assert(set_ingress_priority_map, message="Set priority to pg map on %s" % dut_port)

        # set egress priority to pg map list
        for dut_port in dut_port_list[1::2]:
            set_egress_priority_map = network_controller_obj.set_qos_queue_to_priority_map(port_num=dut_port,
                                                                                           map_list=map_list)
            fun_test.test_assert(set_egress_priority_map, "Set queue to priority map %s" % dut_port)

        # Create streamblock
        # Creeate streamblock from port_1 to port_2
        fun_test.log("Create streamblock on %s destined to %s" % (port_1, port_2))
        port_1_dscp_0_stream = StreamBlock(load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND, load=good_stream_load,
                                           fill_type=StreamBlock.FILL_TYPE_PRBS, fixed_frame_length=port1_port2_dscp0_frame_len)
        streamblock_1 = template_obj.configure_stream_block(port_1_dscp_0_stream, port_handle=port_1)
        fun_test.test_assert(streamblock_1, " Creating streamblock on port %s" % port_1)

        # Configure mac and ip on the stream
        ethernet = Ethernet2Header(destination_mac=destination_mac1)
        frame_stack = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=port_1_dscp_0_stream._spirent_handle, header_obj=ethernet,
            delete_header=[Ethernet2Header.HEADER_TYPE, Ipv4Header.HEADER_TYPE])
        fun_test.test_assert(frame_stack,
                             "Added ethernet header to stream %s" % port_1_dscp_0_stream._spirent_handle)

        ipv4 = Ipv4Header(destination_address=destination_ip1)
        frame_stack = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=port_1_dscp_0_stream._spirent_handle, header_obj=ipv4)
        fun_test.test_assert(frame_stack,
                             "Added ipv4 header to stream %s" % port_1_dscp_0_stream._spirent_handle)

        # Create streamblock
        # Creeate streamblock from port_3 to port_2
        fun_test.log("Create streamblock on %s destined to %s" % (port_3, port_2))
        port_3_dscp_0_stream_1 = StreamBlock(load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND, load=good_stream_load,
                                           fill_type=StreamBlock.FILL_TYPE_PRBS, fixed_frame_length=port3_port2_dscp0_frame_len)
        streamblock_1 = template_obj.configure_stream_block(port_3_dscp_0_stream_1, port_handle=port_3)
        fun_test.test_assert(streamblock_1, " Creating streamblock on port %s" % port_3)

        # Configure mac and ip on the stream
        ethernet = Ethernet2Header(destination_mac=destination_mac1)
        frame_stack = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=port_3_dscp_0_stream_1._spirent_handle, header_obj=ethernet,
            delete_header=[Ethernet2Header.HEADER_TYPE, Ipv4Header.HEADER_TYPE])
        fun_test.test_assert(frame_stack,
                             "Added ethernet header to stream %s" % port_3_dscp_0_stream_1._spirent_handle)

        ipv4 = Ipv4Header(destination_address=destination_ip1)
        frame_stack = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=port_3_dscp_0_stream_1._spirent_handle, header_obj=ipv4)
        fun_test.test_assert(frame_stack,
                             "Added ipv4 header to stream %s" % port_3_dscp_0_stream_1._spirent_handle)

        # Create streamblock
        # Creeate streamblock from port_3 to port_4
        fun_test.log("Create streamblock on %s destined to %s" % (port_3, port_2))
        port_3_dscp_0_stream_2 = StreamBlock(load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND, load=good_stream_load,
                                             fill_type=StreamBlock.FILL_TYPE_PRBS, fixed_frame_length=port3_port4_dscp0_frame_len)
        streamblock_1 = template_obj.configure_stream_block(port_3_dscp_0_stream_2, port_handle=port_3)
        fun_test.test_assert(streamblock_1, " Creating streamblock on port %s" % port_3)

        # Configure mac and ip on the stream
        ethernet = Ethernet2Header(destination_mac=destination_mac1)
        frame_stack = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=port_3_dscp_0_stream_2._spirent_handle, header_obj=ethernet,
            delete_header=[Ethernet2Header.HEADER_TYPE, Ipv4Header.HEADER_TYPE])
        fun_test.test_assert(frame_stack,
                             "Added ethernet header to stream %s" % port_3_dscp_0_stream_2._spirent_handle)

        ipv4 = Ipv4Header(destination_address=destination_ip4)
        frame_stack = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=port_3_dscp_0_stream_2._spirent_handle, header_obj=ipv4)
        fun_test.test_assert(frame_stack,
                             "Added ipv4 header to stream %s" % port_3_dscp_0_stream_2._spirent_handle)

        # Create streamblock
        # Creeate streamblock from port_3 to port_2
        fun_test.log("Create streamblock on %s destined to %s" % (port_3, port_2))
        port_3_dscp_1_stream = StreamBlock(load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND, load=good_stream_load,
                                           fill_type=StreamBlock.FILL_TYPE_PRBS, fixed_frame_length=port3_port2_dscp1_frame_len)
        streamblock_1 = template_obj.configure_stream_block(port_3_dscp_1_stream, port_handle=port_3)
        fun_test.test_assert(streamblock_1, " Creating streamblock on port %s" % port_3)

        # Configure mac and ip on the stream
        ethernet = Ethernet2Header(destination_mac=destination_mac1)
        frame_stack = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=port_3_dscp_1_stream._spirent_handle, header_obj=ethernet,
            delete_header=[Ethernet2Header.HEADER_TYPE, Ipv4Header.HEADER_TYPE])
        fun_test.test_assert(frame_stack,
                             "Added ethernet header to stream %s" % port_3_dscp_1_stream._spirent_handle)

        ipv4 = Ipv4Header(destination_address=destination_ip1)
        frame_stack = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=port_3_dscp_1_stream._spirent_handle, header_obj=ipv4)
        fun_test.test_assert(frame_stack,
                             "Added ipv4 header to stream %s" % port_3_dscp_1_stream._spirent_handle)

        # Configure values in ip header
        dscp_set = template_obj.configure_diffserv(streamblock_obj=port_3_dscp_1_stream, ip_header_obj=ipv4,
                                                   dscp_high=dscp_high,
                                                   dscp_low=dscp_low)
        fun_test.test_assert(dscp_set, "Ensure dscp value of %s is set on ip header for stream %s"
                             % (dscp_value, port_3_dscp_1_stream._spirent_handle))
        fun_test.log("Created streamblock on %s destined to %s" % (port_3, port_2))

        # Create pfc stream
        # Create pfc stream on port_2
        fun_test.log("Create pfc stream for priority %s" % dscp_value)

        port_2_pfc_stream = StreamBlock(load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND, load=pfc_load,
                                        fixed_frame_length=64, insert_signature=False)
        streamblock_4 = template_obj.configure_stream_block(port_2_pfc_stream, port_handle=port_2)
        fun_test.test_assert(streamblock_4, message="Creating pfc streamblock with priority %s on port "
                                                    "%s" % (dscp_value, port_2))

        out = template_obj.configure_priority_flow_control_header(port_2_pfc_stream,
                                                                  class_enable_vector=True,
                                                                  time0=pfc_quanta,
                                                                  ls_octet=ls_octet)
        fun_test.test_assert(out['result'], message="Added frame stack")
        fun_test.log("Created pfc stream on %s " % port_2)

        # Subscribe to results
        project = template_obj.stc_manager.get_project_handle()
        subscribe_results = template_obj.subscribe_to_all_results(parent=project)
        fun_test.test_assert(subscribe_results['result'], "Subscribing to results")
        del subscribe_results['result']

    def cleanup(self):
        # Cleanup spirent session
        template_obj.cleanup()

        reset_pfc_configs(network_controller_obj=network_controller_obj, dut_port_list=[dut_port_1, dut_port_2,
                                                                                        dut_port_3, dut_port_4],
                          queue_list=[0], quanta=True, threshold=True, shared_configs=True,
                          shared_config_port_list=[dut_port_1, dut_port_3])


class TestCase1(FunTestCase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test PFC using 4 ports to check"
                                      "1. Traffic going to different queue is unaffected"
                                      "2. Traffic transmitted to another port is unaffected",
                              steps="""
                        1. Start dscp 0 stream from port_1 to port_2, port_3 to port_4
                        2. Start dscp 1 stream from port_3 to port_2
                        3. Start pfc stream for priority 0 from port_2
                        4. stream on step2 must be unaffected and must tx out of port_2
                        5. stream with dscp 0 from port_3 to port_4 must be unaffected.
                        """)

    def setup(self):
        # Clear port results on DUT
        for dut_port in dut_port_list:
            clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port, shape=shape)
            fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port)

        start_streams = template_obj.stc_manager.start_traffic_stream(
            stream_blocks_list=[port_1_dscp_0_stream.spirent_handle, port_3_dscp_1_stream.spirent_handle,
                                port_3_dscp_0_stream_2.spirent_handle,
                                port_2_pfc_stream.spirent_handle])
        fun_test.test_assert(start_streams, "Ensure streams are started")

    def cleanup(self):
        # Stop generator traffic on ports
        stop_streams = template_obj.stc_manager.stop_traffic_stream(
            stream_blocks_list=[port_1_dscp_0_stream.spirent_handle, port_3_dscp_0_stream_2.spirent_handle,
                                port_3_dscp_1_stream.spirent_handle, port_2_pfc_stream.spirent_handle])
        fun_test.add_checkpoint("Ensure stream dscp2 stream and pfc streams are stopped")

        # Clear all subscribed results
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        capture_obj_list = []
        fun_test.sleep("Letting traffic run for 30 seconds", seconds=30)

        # Check stats on port_2
        # 1. tx stopped for Q-0 and not stopped for Q-1
        # 2. Tx FramesTransmittedOK equals Octet of Q-1
        # 3. Check no out errors on dut port 2
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_2, shape=shape)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_2)

        fun_test.sleep("Letting traffic after clearing stats", seconds=2)

        dut_stat_2 = network_controller_obj.peek_fpg_port_stats(dut_port_2, hnu=hnu)
        dut_port_tx = get_dut_output_stats_value(dut_stat_2, FRAMES_TRANSMITTED_OK,
                                                 tx=True)
        dut_port_dscp_0_tx = get_dut_output_stats_value(dut_stat_2, ETHER_STATS_PKTS_64_OCTETS,
                                                        tx=True)
        dut_port_dscp_1_tx = get_dut_output_stats_value(dut_stat_2, ETHER_STATS_PKTS_512_TO_1023_OCTETS,
                                                        tx=True)
        dut_port_out_error = get_dut_output_stats_value(dut_stat_2, IF_OUT_ERRORS, tx=True)

        fun_test.test_assert(not dut_port_dscp_0_tx, "Ensure no tx is happening for dscp 0")
        fun_test.test_assert(int(dut_port_dscp_1_tx) > 0, "Ensure tx is happening for dscp 1")
        fun_test.test_assert(not dut_port_out_error,
                             message="Ensure no error frames are tx out from %s" % dut_port_2)

        # Check stats on dut port 4
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_4, shape=shape)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_4)

        fun_test.sleep("Letting traffic after clearing stats", seconds=2)

        dut_stat_4 = network_controller_obj.peek_fpg_port_stats(dut_port_4, hnu=hnu)
        dut_port_4_tx = get_dut_output_stats_value(dut_stat_4, FRAMES_TRANSMITTED_OK,
                                                   tx=True)
        dut_port_4_out_error = get_dut_output_stats_value(dut_stat_4, IF_OUT_ERRORS, tx=True)

        fun_test.test_assert(int(dut_port_4_tx) > 0, "Ensure tx is not stopped on %s" % dut_port_4)
        fun_test.test_assert(not dut_port_4_out_error,
                             message="Ensure no error frames are tx out from %s" % dut_port_4)

        # Check stats on port_1 and port_3
        # 1. TX_CBFCPauseTransmitted must be seen on port_1 and not on port_3

        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1, shape=shape)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        fun_test.sleep("Letting traffic after clearing stats", seconds=2)

        dut_stat = network_controller_obj.peek_fpg_port_stats(dut_port_1, hnu=hnu)
        dut_pfc_tx = get_dut_output_stats_value(dut_stat, CBFC_PAUSE_FRAMES_TRANSMITTED, tx=True,
                                                class_value=CLASS_0)

        fun_test.test_assert(int(dut_pfc_tx) > 0, "Ensure pfc frame are sent out of DUT %s" % dut_port_1)

        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_3, shape=shape)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_3)

        fun_test.sleep("Letting traffic after clearing stats", seconds=2)

        dut_stat = network_controller_obj.peek_fpg_port_stats(dut_port_3, hnu=hnu)
        dut_pfc_tx = get_dut_output_stats_value(dut_stat, CBFC_PAUSE_FRAMES_TRANSMITTED, tx=True,
                                                class_value=CLASS_0)

        fun_test.test_assert(not dut_pfc_tx, "Ensure pfc frame are not sent out of DUT %s" % dut_port_3)


class TestCase2(TestCase1):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Test PFC frames are transmitted out of DUT even if ingress traffic is stopped and"
                                      " transmission is stopped only when pfc stream is stopped from spirent",
                              steps="""
                        1. Start dscp 0 streams from port_1 to port_2 and port_3 towards port_2 and port_4
                        2. Start pfc frame from port_2
                        3. Let traffic for 30 seconds
                        4. tx on port_2 must be stopped
                        5. CBFCPause_Transmitted must be seen on port_1 and port_3
                        6. Stop dscp 0 from port_3 towards port_2
                        7. Verify steps 4 and 5
                        8. Now stop dscp 0 from port_3 towards port_2 and PFC stream
                        9. Check traffic must now resume
                        """)

    def run(self):
        def inner_check():
            # Check stats on port_2
            # 1. tx stopped for Q-0 and not stopped for Q-1
            # 2. Tx FramesTransmittedOK equals Octet of Q-1
            # 3. Check no out errors on dut port 2
            clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_2, shape=shape)
            fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_2)

            fun_test.sleep("Letting traffic after clearing stats", seconds=2)

            dut_stat_2 = network_controller_obj.peek_fpg_port_stats(dut_port_2, hnu=hnu)
            dut_port_tx = get_dut_output_stats_value(dut_stat_2, FRAMES_TRANSMITTED_OK,
                                                     tx=True)
            dut_port_dscp_0_tx = get_dut_output_stats_value(dut_stat_2, ETHER_STATS_PKTS_64_OCTETS,
                                                            tx=True)
            dut_port_dscp_1_tx = get_dut_output_stats_value(dut_stat_2, ETHER_STATS_PKTS_512_TO_1023_OCTETS,
                                                            tx=True)
            dut_port_out_error = get_dut_output_stats_value(dut_stat_2, IF_OUT_ERRORS, tx=True)

            fun_test.test_assert(not dut_port_dscp_0_tx, "Ensure no tx is happening for dscp 0 on %s" % dut_port_2)
            fun_test.test_assert(int(dut_port_dscp_1_tx) > 0, "Ensure tx is happening for dscp 1 on %s " % dut_port_2)

            # Check stats on dut port 4
            clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_4, shape=shape)
            fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_4)

            fun_test.sleep("Letting traffic after clearing stats", seconds=2)

            dut_stat_4 = network_controller_obj.peek_fpg_port_stats(dut_port_4, hnu=hnu)
            dut_port_4_tx = get_dut_output_stats_value(dut_stat_4, FRAMES_TRANSMITTED_OK,
                                                       tx=True)

            fun_test.test_assert(not dut_port_4_tx, "Ensure tx is stopped on %s for dscp 0" % dut_port_4)

            for dut_port in dut_port_list[::2]:
                clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port, shape=shape)
                fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port)

                fun_test.sleep("Letting traffic after clearing stats", seconds=2)

                dut_stat = network_controller_obj.peek_fpg_port_stats(dut_port, hnu=hnu)
                dut_pfc_tx = get_dut_output_stats_value(dut_stat, CBFC_PAUSE_FRAMES_TRANSMITTED, tx=True,
                                                        class_value=CLASS_0)

                fun_test.test_assert(int(dut_pfc_tx) > 0, "Ensure pfc frame are sent out of DUT %s" % dut_port)

        capture_obj_list = []
        fun_test.sleep("Letting traffic run for 30 seconds", seconds=30)

        start_streams = template_obj.stc_manager.start_traffic_stream(
            stream_blocks_list=[port_3_dscp_0_stream_1.spirent_handle])
        fun_test.test_assert(start_streams, "Ensure streams are started")

        fun_test.log("Start pcap capture to make sure that pfc frames are being sent out")
        capture_obj_1 = Capture()
        start_capture_1 = template_obj.stc_manager.start_capture_command(capture_obj=capture_obj_1, port_handle=port_1)
        fun_test.test_assert(start_capture_1, "Started capture on port %s" % port_1)
        capture_obj_list.append(capture_obj_1)

        capture_obj_2 = Capture()
        start_capture_2 = template_obj.stc_manager.start_capture_command(capture_obj=capture_obj_2, port_handle=port_3)
        fun_test.test_assert(start_capture_2, "Started capture on port %s" % port_3)
        capture_obj_list.append(capture_obj_2)

        inner_check()

        # Stop Q0 from port_3 to port_2. PFC streams must continue to tx out
        # Check pfc still comes out on port_1 and port_3
        # Q0 stream is stopped from port_3 to port_4
        stop_streams = template_obj.stc_manager.stop_traffic_stream(
            stream_blocks_list=[port_3_dscp_0_stream_1.spirent_handle])
        fun_test.test_assert(stop_streams, "Ensure stream dscp 0 from port_3 to port_2 is stopped")

        fun_test.sleep("Letting traffic of dscp 0 from port_3 to port_2 stop")

        inner_check()

        # Stop pfc stream
        stop_streams = template_obj.stc_manager.stop_traffic_stream(
            stream_blocks_list=[port_2_pfc_stream.spirent_handle])
        fun_test.test_assert(stop_streams, "Ensure pfc stream stopped")

        fun_test.sleep("Stopped pfc stream", seconds=5)

        # Stop generator traffic on ports
        start_stream = template_obj.stc_manager.start_traffic_stream(
            stream_blocks_list=[port_3_dscp_0_stream_1.spirent_handle])
        fun_test.test_assert(start_stream, "Ensure stream dscp 0 from port_3 to port_2 is started")

        fun_test.sleep("Letting traffic of dscp 0 from port_3 to port_2 start")

        # check stats on port_2 and port_4, they must transmit
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_2, shape=shape)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_2)

        fun_test.sleep("Letting traffic after clearing stats", seconds=2)

        dut_stat_2 = network_controller_obj.peek_fpg_port_stats(dut_port_2, hnu=hnu)
        dut_port_1_dscp_0_tx = get_dut_output_stats_value(dut_stat_2, ETHER_STATS_PKTS_64_OCTETS,
                                                          tx=True)
        dut_port_dscp_1_tx = get_dut_output_stats_value(dut_stat_2, ETHER_STATS_PKTS_512_TO_1023_OCTETS,
                                                        tx=True)
        dut_port_3_dscp_0_tx = get_dut_output_stats_value(dut_stat_2, ETHER_STATS_PKTS_128_TO_255_OCTETS,
                                                          tx=True)
        dut_port_out_error = get_dut_output_stats_value(dut_stat_2, IF_OUT_ERRORS, tx=True)

        fun_test.test_assert(int(dut_port_1_dscp_0_tx) > 0,
                             message="Ensure dscp 0 stream from port_1 to port_2 is tx out")
        fun_test.test_assert(int(dut_port_dscp_1_tx) > 0,
                             message="Ensure dscp 1 stream from port_3 to port_2 is tx out")
        fun_test.test_assert(int(dut_port_3_dscp_0_tx) > 0,
                             message="Ensure dscp 0 stream from port_3 to port_2 is tx out")
        fun_test.test_assert(not dut_port_out_error,
                             message="Ensure no error frames are tx out from %s" % dut_port_2)

        # Check stats on dut port 4
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_4, shape=shape)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_4)

        fun_test.sleep("Letting traffic after clearing stats", seconds=2)

        dut_stat_4 = network_controller_obj.peek_fpg_port_stats(dut_port_4, hnu=hnu)
        dut_port_4_tx = get_dut_output_stats_value(dut_stat_4, FRAMES_TRANSMITTED_OK,
                                                   tx=True)
        fun_test.test_assert(int(dut_port_4_tx) > 0, message="Ensure dscp 0 from port_3 to port_4 is tx_out")

        # Check capture for quanta values
        stop_capture_1 = template_obj.stc_manager.stop_capture_command(capture_obj_1._spirent_handle)
        fun_test.test_assert(stop_capture_1, "Stopped capture on port %s" % port_1)

        stop_capture_2 = template_obj.stc_manager.stop_capture_command(capture_obj_2._spirent_handle)
        fun_test.test_assert(stop_capture_2, "Stopped capture on port %s" % port_3)

        for capture_obj in capture_obj_list:
            file = fun_test.get_temp_file_name()
            file_name_1 = file + '.pcap'
            file_path = SYSTEM_TMP_DIR
            pcap_file_path_1 = file_path + "/" + file_name_1

            saved = template_obj.stc_manager.save_capture_data_command(capture_handle=capture_obj._spirent_handle,
                                                                       file_name=file_name_1,
                                                                       file_name_path=file_path)
            fun_test.test_assert(saved, "Saved pcap %s to local machine" % pcap_file_path_1)

            fun_test.test_assert(os.path.exists(pcap_file_path_1), message="Check pcap file exists locally")

            pcap_parser_1 = PcapParser(pcap_file_path_1)
            output = pcap_parser_1.verify_pfc_header_fields(last_packet=True, time2=str(0))
            fun_test.test_assert(output, "Ensure value of quanta is 0 the last pfc packet")

            first = pcap_parser_1.verify_pfc_header_fields(first_packet=True,
                                                           time0=quanta_value,
                                                           time1=zero_quanta_value,
                                                           time2=zero_quanta_value,
                                                           time3=zero_quanta_value,
                                                           time4=zero_quanta_value,
                                                           time5=zero_quanta_value,
                                                           time6=zero_quanta_value,
                                                           time7=zero_quanta_value)
            fun_test.test_assert(first, "Value of quanta %s seen in pfc first packet" % quanta_value)

            fun_test.remove_file(pcap_file_path_1)
            fun_test.log("Removed file %s from local system" % pcap_file_path_1)


if __name__ == "__main__":
    local_settings = nu_config_obj.get_local_settings_parameters(flow_direction=True, ip_version=True)
    flow_direction = local_settings[nu_config_obj.FLOW_DIRECTION]
    ts = SpirentSetup()
    ts.add_test_case(TestCase1())
    ts.add_test_case(TestCase2())
    ts.run()