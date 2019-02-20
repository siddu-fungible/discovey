from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, Ethernet2Header, Ipv4Header, Capture, GeneratorConfig
from lib.host.network_controller import NetworkController
from scripts.networking.helper import *
from scripts.networking.nu_config_manager import nu_config_obj
from lib.utilities.pcap_parser import PcapParser

num_ports = 3
dscp_high = 0
dscp_low = 2
dscp_value = 2
ls_octet = '00000100'
pfc_quanta = '65535'
quanta_value = 6000
zero_quanta_value = 0
threshold_value = 600
min_thr = 512
shr_thr = 2000
hdr_thr = 20
xoff_enable = 1
shared_xon_thr = 5
spirent_streamblock_objs = {}
spirent_streamblock_handles = {}


class SpirentSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
                1. Create Spirent template
                2. Connect chassis, labserver and licenseserver
                3. Attach Ports
                4. Configure stream with dscp 2 on port 1 and port 2
                5. Configure pfc stream for priority 2 on port 3
                6. Configure another stream with dscp 2 on port 1
                7. Use to 
                """)

    def setup(self):
        global template_obj, port_1, port_2, port_3, pfc_frame, subscribe_results, network_controller_obj, dut_port_2, \
            dut_port_1, dut_port_3, shape, hnu, dut_port_list, port_1_dscp_stream_1, \
            port_3_dscp_stream_1, port_2_pfc_stream, port_obj_list, flow_direction

        flow_direction = nu_config_obj.FLOW_DIRECTION_NU_NU

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
        template_obj = SpirentEthernetTrafficTemplate(session_name="test_pfc_3ports", chassis_type=nu_config_obj.CHASSIS_TYPE,
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

        routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
        fun_test.simple_assert(routes_config, "Ensure routes config fetched")
        l3_config = routes_config['l3_config']

        destination_mac1 = routes_config['routermac']
        destination_ip1 = l3_config['destination_ip1']
        if hnu:
            destination_ip1 = l3_config['hnu_destination_ip1']
        dut_port_1 = dut_config['ports'][0]
        dut_port_2 = dut_config['ports'][1]
        dut_port_3 = dut_config['ports'][2]
        dut_port_list.append(dut_port_1)
        dut_port_list.append(dut_port_2)
        dut_port_list.append(dut_port_3)

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
        set_egress_priority_map = network_controller_obj.set_qos_queue_to_priority_map(port_num=dut_port_2,
                                                                                       map_list=map_list)
        fun_test.test_assert(set_egress_priority_map, "Set queue to priority map %s" % dut_port_2)

        for port in port_obj_list[::2]:
            # Create good stream on port 1
            fun_test.log("Create streamblock on %s destined to %s" % (port, port_2))
            port_1_dscp_stream_1 = StreamBlock(load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND, load=good_stream_load,
                                               fill_type=StreamBlock.FILL_TYPE_PRBS)
            streamblock_1 = template_obj.configure_stream_block(port_1_dscp_stream_1, port_handle=port)
            fun_test.test_assert(streamblock_1, " Creating streamblock on port %s" % port)

            # Configure mac and ip on the stream
            ethernet = Ethernet2Header(destination_mac=destination_mac1)
            frame_stack = template_obj.stc_manager.configure_frame_stack(
                stream_block_handle=port_1_dscp_stream_1._spirent_handle, header_obj=ethernet,
                delete_header=[Ethernet2Header.HEADER_TYPE, Ipv4Header.HEADER_TYPE])
            fun_test.test_assert(frame_stack,
                                 "Added ethernet header to stream %s" % port_1_dscp_stream_1._spirent_handle)

            ipv4 = Ipv4Header(destination_address=destination_ip1)
            frame_stack = template_obj.stc_manager.configure_frame_stack(
                stream_block_handle=port_1_dscp_stream_1._spirent_handle, header_obj=ipv4)
            fun_test.test_assert(frame_stack,
                                 "Added ipv4 header to stream %s" % port_1_dscp_stream_1._spirent_handle)

            # Configure values in ip header
            dscp_set = template_obj.configure_diffserv(streamblock_obj=port_1_dscp_stream_1, ip_header_obj=ipv4,
                                                       dscp_high=dscp_high,
                                                       dscp_low=dscp_low)
            fun_test.test_assert(dscp_set, "Ensure dscp value of %s is set on ip header for stream %s"
                                 % (dscp_value, port_1_dscp_stream_1._spirent_handle))
            fun_test.log("Created streamblock on %s destined to %s" % (port, port_2))

            spirent_streamblock_objs[port] = port_1_dscp_stream_1
            spirent_streamblock_handles[port] = port_1_dscp_stream_1.spirent_handle

        # Create pfc stream
        fun_test.log("Create pfc stream for priority %s" % dscp_value)

        port_2_pfc_stream = StreamBlock(load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND, load=pfc_load,
                                        fixed_frame_length=64, insert_signature=False)
        streamblock_4 = template_obj.configure_stream_block(port_2_pfc_stream, port_handle=port_2)
        fun_test.test_assert(streamblock_4, message="Creating pfc streamblock with priority %s on port "
                                                    "%s" % (dscp_value, port_2))

        out = template_obj.configure_priority_flow_control_header(port_2_pfc_stream,
                                                                  class_enable_vector=True,
                                                                  time2=pfc_quanta,
                                                                  ls_octet=ls_octet)
        fun_test.test_assert(out['result'], message="Added frame stack")
        fun_test.log("Created pfc stream on %s " % port_2)

        spirent_streamblock_objs[port_2] = port_2_pfc_stream
        spirent_streamblock_handles[port_2] = port_2_pfc_stream.spirent_handle

        # Subscribe to results
        project = template_obj.stc_manager.get_project_handle()
        subscribe_results = template_obj.subscribe_to_all_results(parent=project)
        fun_test.test_assert(subscribe_results['result'], "Subscribing to results")
        del subscribe_results['result']

    def cleanup(self):
        # Cleanup spirent session
        template_obj.cleanup()

        disable_1 = network_controller_obj.disable_priority_flow_control(dut_port_1, shape=shape)
        fun_test.add_checkpoint("Disable pfc on port %s" % dut_port_1)
        disable_2 = network_controller_obj.disable_priority_flow_control(dut_port_2, shape=shape)
        fun_test.add_checkpoint("Disable pfc on port %s" % dut_port_2)
        disable_3 = network_controller_obj.disable_priority_flow_control(dut_port_3, shape=shape)
        fun_test.add_checkpoint("Disable pfc on port %s" % dut_port_3)


class TestCase1(FunTestCase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test PFC using 3 ports where 2 ports send frames with same dscp value towards 3rd "
                                      "port",
                              steps="""
                        1. Start dscp streams from port_1 and port_3
                        2. Start pfc frame from port_2
                        3. Let traffic for 30 seconds
                        4. Check Tx on port_2 has stopped
                        5. Capture and verify port_1 and port_3 tx pfc frames with assigned quanta
                        6. Stop pfc and check quanta 0 in both pcap captures
                        7. Verify tx of dscp streams from port_1 and port_3 on port_2
                        """)

    def setup(self):
        # Clear port results on DUT
        for dut_port in dut_port_list:
            clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port, shape=shape)
            fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port)

        start_streams = template_obj.stc_manager.start_traffic_stream(
            stream_blocks_list=spirent_streamblock_handles.values())
        fun_test.test_assert(start_streams, "Ensure stream dscp2 streams are started from ports %s and %s" % (port_1, 
                                                                                                              port_3))

    def cleanup(self):
        # Stop generator traffic on ports
        stop_streams = template_obj.stc_manager.stop_traffic_stream(
            stream_blocks_list=spirent_streamblock_handles.values())
        fun_test.add_checkpoint("Ensure stream dscp2 stream and pfc streams are stopped")

        # Clear all subscribed results
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        capture_obj_list = []
        fun_test.sleep("Letting traffic run for 30 seconds", seconds=30)

        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_2, shape=shape)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_2)

        dut_stat_2 = network_controller_obj.peek_fpg_port_stats(dut_port_2, hnu=hnu)
        dut_port_tx = get_dut_output_stats_value(dut_stat_2, FRAMES_TRANSMITTED_OK,
                                                 tx=True)

        fun_test.test_assert(not dut_port_tx, "Ensure no streams are transmitted out of %s" % dut_port_2)
        
        for dut_port in dut_port_list[::2]:
            dut_stat = network_controller_obj.peek_fpg_port_stats(dut_port, hnu=hnu)
            dut_port_pfc_tx = get_dut_output_stats_value(dut_stat, CBFC_PAUSE_FRAMES_TRANSMITTED,
                                                         tx=True, class_value=CLASS_2)

            fun_test.test_assert(dut_port_pfc_tx, "Ensure pfc streams are being tx on %s" % dut_port)

        fun_test.log("Start pcap capture to make sure that pfc frames are being sent out")
        capture_obj_1 = Capture()
        start_capture_1 = template_obj.stc_manager.start_capture_command(capture_obj=capture_obj_1, port_handle=port_1)
        fun_test.test_assert(start_capture_1, "Started capture on port %s" % port_1)
        capture_obj_list.append(capture_obj_1)

        capture_obj_2 = Capture()
        start_capture_2 = template_obj.stc_manager.start_capture_command(capture_obj=capture_obj_2, port_handle=port_3)
        fun_test.test_assert(start_capture_2, "Started capture on port %s" % port_3)
        capture_obj_list.append(capture_obj_2)
        
        fun_test.sleep("Letting capture for 5 seconds", seconds=5)

        stop_streams = template_obj.stc_manager.stop_traffic_stream(
            stream_blocks_list=[spirent_streamblock_handles[port_2]])
        fun_test.test_assert(stop_streams, "Ensure pfc streams are stopped")

        fun_test.sleep("Letting pfc for 5 seconds", seconds=5)

        stop_capture_1 = template_obj.stc_manager.stop_capture_command(capture_obj_1._spirent_handle)
        fun_test.test_assert(stop_capture_1, "Stopped capture on port %s" % port_1)

        stop_capture_2 = template_obj.stc_manager.stop_capture_command(capture_obj_2._spirent_handle)
        fun_test.test_assert(stop_capture_2, "Stopped capture on port %s" % port_3)

        fun_test.sleep("Letting capture be stopped", seconds=2)

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
            output = pcap_parser_1.verify_pfc_header_fields(last_packet=True, time2=str(zero_quanta_value))
            fun_test.test_assert(output, "Ensure value of quanta is 0 the last pfc packet")

            first = pcap_parser_1.verify_pfc_header_fields(first_packet=True,
                                                           time0=zero_quanta_value,
                                                           time1=zero_quanta_value,
                                                           time2=quanta_value,
                                                           time3=zero_quanta_value,
                                                           time4=zero_quanta_value,
                                                           time5=zero_quanta_value,
                                                           time6=zero_quanta_value,
                                                           time7=zero_quanta_value)
            fun_test.test_assert(first, "Value of quanta %s seen in pfc first packet" % quanta_value)

            fun_test.remove_file(pcap_file_path_1)
            fun_test.log("Removed file %s from local system" % pcap_file_path_1)

        # Spirent stats
        stream_result_dict = template_obj.stc_manager.fetch_streamblock_results(subscribe_result=subscribe_results,
                                                                                streamblock_handle_list=
                                                                                [spirent_streamblock_handles[port_1],
                                                                                spirent_streamblock_handles[port_3]],
                                                                                tx_result=True, rx_result=True)

        for port in port_obj_list[::2]:
            tx_results_1 = stream_result_dict[spirent_streamblock_handles[port]]['tx_result']
            rx_results_1 = stream_result_dict[spirent_streamblock_handles[port]]['rx_result']

            fun_test.log("rx results for stream on %s" % tx_results_1)
            fun_test.log("rx results for stream on %s" % rx_results_1)
            fun_test.test_assert((int(rx_results_1['FrameRate']) >= int(tx_results_1['FrameRate']) - 10) or
                                  (int(rx_results_1['FrameRate']) <= int(tx_results_1['FrameRate']) + 10),
                                 message="Check frame rate for stream on port %s" % port)


if __name__ == "__main__":
    ts = SpirentSetup()
    ts.add_test_case(TestCase1())
    ts.run()