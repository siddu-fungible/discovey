from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, GeneratorConfig, Ethernet2Header, Ipv4Header, Capture
from lib.utilities.pcap_parser import PcapParser
from lib.host.network_controller import NetworkController
from scripts.networking.nu_config_manager import nu_config_obj
from scripts.networking.helper import *
from collections import OrderedDict

num_ports = 2
default_quanta = 65535
min_thr = 512
shr_thr = 2000
hdr_thr = 20
xoff_enable = 1
shared_xon_thr = 5
quanta = 5000
threshold = 500
zero_quanta_value = 0
good_stream_list = []
pfc_stream_list = []
pfc_stream_obj_list = []
good_streamblock_objs = OrderedDict()
pfc_streamblock_objs = OrderedDict()
streamblock_objs = OrderedDict()
generator_config_objs = OrderedDict()
generator_dict = {}
priority_dict = OrderedDict()

priority_dict['priority_0'] = {'priority_val': 0, 'ls_octet': '00000001', 'ms_octet': '00000000',
                                'quanta_val': {'0': '0', 'F': 'FFFF'}, 'dscp_high': '0', 'dscp_low': '0'}
priority_dict['priority_1'] = {'priority_val': 1, 'ls_octet': '00000010', 'ms_octet': '00000000',
                                'quanta_val': {'0': '0', 'F': 'FFFF'}, 'dscp_high': '0', 'dscp_low': '1'}
priority_dict['priority_2'] = {'priority_val': 2, 'ls_octet': '00000100', 'ms_octet': '00000000',
                                'quanta_val': {'0': '0', 'F': 'FFFF'}, 'dscp_high': '0', 'dscp_low': '2'}
priority_dict['priority_3'] = {'priority_val': 3, 'ls_octet': '00001000', 'ms_octet': '00000000',
                                'quanta_val': {'0': '0', 'F': 'FFFF'}, 'dscp_high': '0', 'dscp_low': '3'}
priority_dict['priority_4'] = {'priority_val': 4, 'ls_octet': '00010000', 'ms_octet': '00000000',
                                'quanta_val': {'0': '0', 'F': 'FFFF'}, 'dscp_high': '0', 'dscp_low': '4'}
priority_dict['priority_5'] = {'priority_val': 5, 'ls_octet': '00100000', 'ms_octet': '00000000',
                                'quanta_val': {'0': '0', 'F': 'FFFF'}, 'dscp_high': '0', 'dscp_low': '5'}
priority_dict['priority_6'] = {'priority_val': 6, 'ls_octet': '01000000', 'ms_octet': '00000000',
                                'quanta_val': {'0': '0', 'F': 'FFFF'}, 'dscp_high': '0', 'dscp_low': '6'}
priority_dict['priority_7'] = {'priority_val': 7, 'ls_octet': '10000000', 'ms_octet': '00000000',
                                'quanta_val': {'0': '0', 'F': 'FFFF'}, 'dscp_high': '0', 'dscp_low': '7'}
priority_list = [val['priority_val'] for val in priority_dict.itervalues()]
k_list = [x for x in range(0, 16)]
k_list.reverse()


class SpirentSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
                1. Create Spirent template
                2. Connect chassis, labserver and licenseserver
                3. Attach Ports
                4. Configure good stream on port 1 of spirent
                5. Configure pfc frame on port 2
                """)

    def setup(self):
        global template_obj, port_1, port_2, pfc_frame, subscribe_results, network_controller_obj, dut_port_2, \
            dut_port_1, hnu, shape

        dut_type = fun_test.get_local_setting(setting="dut_type")
        dut_config = nu_config_obj.read_dut_config(dut_type=dut_type, flow_direction=flow_direction)

        shape = 0
        hnu = False
        if flow_direction == nu_config_obj.FLOW_DIRECTION_HNU_HNU:
            shape = 1
            hnu = True

        chassis_type = fun_test.get_local_setting(setting="chassis_type")
        spirent_config = nu_config_obj.read_traffic_generator_config()

        good_load = 100
        pfc_load = 20
        fun_test.log("Creating Template object")
        template_obj = SpirentEthernetTrafficTemplate(session_name="test_pfc_ingress_qos",
                                                      spirent_config=spirent_config,
                                                      chassis_type=chassis_type)
        fun_test.test_assert(template_obj, "Create template object")

        destination_mac1 = spirent_config['l2_config']['destination_mac']
        destination_ip1 = spirent_config['l3_config']['ipv4']['destination_ip3']

        # TODO: To be changed once we are able to change qos values using curl call
        dut_port_1 = dut_config['ports'][1]
        dut_port_2 = dut_config['ports'][2]
        fun_test.log("Using dut ports %s, %s" % (dut_port_1, dut_port_2))

        # Create network controller object
        dpcsh_server_ip = dut_config['dpcsh_tcp_proxy_ip']
        dpcsh_server_port = int(dut_config['dpcsh_tcp_proxy_port'])
        network_controller_obj = NetworkController(dpc_server_ip=dpcsh_server_ip, dpc_server_port=dpcsh_server_port)

        for key in priority_dict.keys():
            priority_value = priority_dict[key]['priority_val']
            set_qos_ingress = network_controller_obj.set_qos_ingress_priority_group(port_num=dut_port_1,
                                                                                    priority_group_num=priority_value,
                                                                                    min_threshold=min_thr,
                                                                                    shared_threshold=shr_thr,
                                                                                    headroom_threshold=hdr_thr,
                                                                                    xoff_enable=xoff_enable,
                                                                                    shared_xon_threshold=shared_xon_thr)
            fun_test.test_assert(set_qos_ingress, "Setting qos ingress priority group")

            port_quanta = network_controller_obj.set_priority_flow_control_quanta(port_num=dut_port_1,
                                                                                  quanta=quanta,
                                                                                  class_num=priority_value,
                                                                                  shape=shape)
            fun_test.test_assert(port_quanta, "Ensure quanta %s is set on port %s" % (quanta, dut_port_1))

            port_thr = network_controller_obj.set_priority_flow_control_threshold(port_num=dut_port_1,
                                                                                  threshold=threshold,
                                                                                  class_num=priority_value,
                                                                                  shape=shape)
            fun_test.test_assert(port_thr, "Ensure threshold %s is set on port %s" % (port_thr, dut_port_1))

        pfc_enable = network_controller_obj.enable_qos_pfc(hnu=hnu)
        fun_test.test_assert(pfc_enable, "Ensure qos pfc is enabled")

        enable_1 = network_controller_obj.enable_priority_flow_control(dut_port_1, shape=shape)
        fun_test.test_assert(enable_1, "Enable pfc on port %s" % dut_port_1)

        # enable pfc on dut egress
        enable_2 = network_controller_obj.enable_priority_flow_control(dut_port_2, shape=shape)
        fun_test.test_assert(enable_2, "Enable pfc on port %s" % dut_port_2)

        # set ingress priority to pg map list
        set_ingress_priority_map = network_controller_obj.set_qos_priority_to_pg_map(port_num=dut_port_1,
                                                                                     map_list=k_list)
        fun_test.test_assert(set_ingress_priority_map, message="Set priority to pg map")

        # set egress priority to pg map list
        set_egress_priority_map = network_controller_obj.set_qos_queue_to_priority_map(port_num=dut_port_2,
                                                                                       map_list=k_list)
        fun_test.test_assert(set_egress_priority_map, "Set queue to priority map")

        all_ports_map = nu_config_obj.get_spirent_dut_port_mapper(no_of_ports_needed=4,
                                                                  flow_direction=flow_direction)
        ports_map = OrderedDict()
        ports_map['FPG' + str(dut_port_1)] = all_ports_map['FPG' + str(dut_port_1)]
        ports_map['FPG' + str(dut_port_2)] = all_ports_map['FPG' + str(dut_port_2)]

        flow_dir = nu_config_obj.FLOW_DIRECTION_NU_NU
        if hnu:
            flow_dir = nu_config_obj.FLOW_DIRECTION_HNU_HNU
        result = template_obj.setup(no_of_ports_needed=num_ports, flow_direction=flow_dir, ports_map=ports_map)
        fun_test.test_assert(result['result'], "Configure setup")

        port_obj_list = result['port_list']
        port_1 = port_obj_list[0]
        port_2 = port_obj_list[1]

        # Configure Generator
        for port in port_obj_list:
            generator_config_objs[port] = None
            duration_seconds = 1500
            gen_config_obj = GeneratorConfig(duration=duration_seconds,
                                             scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED,
                                             duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                             advanced_interleaving=True)

            gen_obj_1 = template_obj.stc_manager.get_generator(port_handle=port)
            config_obj = template_obj.configure_generator_config(port_handle=port,
                                                                 generator_config_obj=gen_config_obj)
            fun_test.test_assert(config_obj, "Creating generator config on port %s" % port)

            generator_dict[port] = gen_obj_1
            generator_config_objs[port] = gen_config_obj

            if port == str(port_1):
                for key, val in priority_dict.iteritems():
                    good_streamblock_objs[key] = {}

                    # Create good stream on port 1
                    create_streamblock_1 = StreamBlock(load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND,
                                                       load=good_load, fill_type=StreamBlock.FILL_TYPE_PRBS)
                    streamblock_1 = template_obj.configure_stream_block(create_streamblock_1, port_handle=port_1)
                    fun_test.test_assert(streamblock_1, "Creating streamblock for priority %s on port %s" % (key,
                                                                                                             port_1))

                    # Configure mac and ip on the stream
                    ethernet = Ethernet2Header(destination_mac=destination_mac1)
                    frame_stack = template_obj.stc_manager.configure_frame_stack(
                        stream_block_handle=create_streamblock_1._spirent_handle, header_obj=ethernet,
                        delete_header=[Ethernet2Header.HEADER_TYPE, Ipv4Header.HEADER_TYPE])
                    fun_test.test_assert(frame_stack,
                                         "Added ethernet header to stream %s" % create_streamblock_1._spirent_handle)

                    ipv4 = Ipv4Header(destination_address=destination_ip1)
                    frame_stack = template_obj.stc_manager.configure_frame_stack(
                        stream_block_handle=create_streamblock_1._spirent_handle, header_obj=ipv4)
                    fun_test.test_assert(frame_stack,
                                         "Added ipv4 header to stream %s" % create_streamblock_1._spirent_handle)

                    # Configure values in ip header
                    dscp_set = template_obj.configure_diffserv(streamblock_obj=create_streamblock_1, ip_header_obj=ipv4,
                                                               dscp_high=val['dscp_high'],
                                                               dscp_low=val['dscp_low'])
                    fun_test.test_assert(dscp_set, "Ensure dscp value of %s is set on ip header for stream %s"
                                         % (val['priority_val'], create_streamblock_1._spirent_handle))
                    good_streamblock_objs[key]['streamblock_obj'] = create_streamblock_1
                    good_stream_list.append(create_streamblock_1._spirent_handle)

        pfc_streamblock_objs = {}
        create_streamblock_2 = StreamBlock(load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND, load=pfc_load,
                                           fixed_frame_length=64, insert_signature=False)
        streamblock_2 = template_obj.configure_stream_block(create_streamblock_2, port_handle=port_2)
        fun_test.test_assert(streamblock_2, message="Creating pfc streamblock with priority 0 on port "
                                                    "%s" % port_2)
        out = template_obj.configure_priority_flow_control_header(create_streamblock_2,
                                                                  class_enable_vector=True,
                                                                  time0=default_quanta,
                                                                  time1=default_quanta,
                                                                  time3=default_quanta,
                                                                  time4=default_quanta,
                                                                  time5=default_quanta,
                                                                  time6=default_quanta,
                                                                  time2=default_quanta,
                                                                  time7=default_quanta,
                                                                  ls_octet='00010000')
        fun_test.test_assert(out['result'], message="Added frame stack")
        pfc_streamblock_objs['streamblock_obj'] = create_streamblock_2
        pfc_streamblock_objs['pfc_header_obj'] = out['pfc_header_obj']
        pfc_stream_obj_list.append(create_streamblock_2)
        pfc_stream_list.append(create_streamblock_2._spirent_handle)

        # Applying configuration
        apply = template_obj.stc_manager.apply_configuration()
        fun_test.test_assert(apply, "Applying Generator config")

        # Subscribe to results
        project = template_obj.stc_manager.get_project_handle()
        subscribe_results = template_obj.subscribe_to_all_results(parent=project)
        fun_test.test_assert(subscribe_results['result'], "Subscribing to results")
        del subscribe_results['result']

    def cleanup(self):
        # TODO: Add code for re-setting qos profile values

        # Cleanup spirent session
        fun_test.test_assert(template_obj.cleanup(), "Cleaning up session")

        disable_1 = network_controller_obj.disable_priority_flow_control(dut_port_1, shape=shape)
        fun_test.test_assert(disable_1, "Disable pfc on port %s" % dut_port_1)
        disable_2 = network_controller_obj.disable_priority_flow_control(dut_port_2, shape=shape)
        fun_test.test_assert(disable_2, "Disable pfc on port %s" % dut_port_2)


class TestCase1(FunTestCase):
    pcap_file_path_1 = None

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test egress qos value 3 for PFC",
                              steps="""
                              1. Start traffic for streams with dscp 0-7
                              2. Start pfc frame for priority 1.
                              3. Rx on spirent for streams with dscp 4-7 must not change
                              4. q_deq for q_04 must not be changed, but for q_00 must change
                              5. pg_deq for q_01 must not change but for q_00 must change
                              6. mac stats must have CBFCPauseTransmitted for priority 4-7
                              7. Capture must verify for quanta value for priorities 4-7
                              """)

    def setup(self):
        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1, shape=shape)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2, shape=shape)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

    def cleanup(self):
        # Clear all subscribed results
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

        stop_streams = template_obj.stc_manager.stop_traffic_stream(
            stream_blocks_list=good_stream_list)
        fun_test.test_assert(stop_streams, "Ensure dscp streams are stopped")

    def run(self):
        result_dict = {}
        spirent_rx_counters = 'spirent_rx_counters'
        fpg_cbfcpause_counters_tx = 'fpg_cbfcpause_counters_tx'
        fpg_cbfcpause_counters_rx = 'fpg_cbfcpause_counters_rx'
        psw_port_pg_counters = 'psw_port_pg_counters'
        psw_port_q_counters = 'psw_port_q_counters'
        dequeue = 'dequeue'
        enqueue = 'enqueue'
        egress_check_streams = good_stream_list[4:]
        pfc_affected_priority = [x for x in range(4,8)]

        start_streams = template_obj.stc_manager.start_traffic_stream(
            stream_blocks_list=good_stream_list)
        fun_test.test_assert(start_streams, "Ensure dscp streams are started")

        start_pfc = template_obj.stc_manager.start_traffic_stream(
            stream_blocks_list=pfc_stream_list[0])
        fun_test.test_assert(start_pfc, "Ensure pfc stream started")

        fun_test.sleep("Letting traffic run for 30 seconds", seconds=30)

        fun_test.log("Fetch spirent rx counter results for all good streams")
        result_dict[spirent_rx_counters] = find_spirent_rx_counters_stopped(template_obj=template_obj,
                                                                            subscribe_result=subscribe_results,
                                                                            streamblock_handle_list=good_stream_list)

        fun_test.log("Get psw port group enqueue dequeue counters")
        result_dict[psw_port_pg_counters] = \
            get_psw_port_enqueue_dequeue_counters(network_controller_obj=network_controller_obj,
                                                  dut_port=dut_port_1, pg=True, hnu=hnu, priority_list=priority_list)

        fun_test.log("Get psw port queue enqueue dequeue counters")
        result_dict[psw_port_q_counters] = \
            get_psw_port_enqueue_dequeue_counters(network_controller_obj=network_controller_obj,
                                                  dut_port=dut_port_2, hnu=hnu, priority_list=priority_list)

        fun_test.log("Fetch fpg stats on dut port %s" % dut_port_2)
        result_dict[fpg_cbfcpause_counters_rx] = \
            get_fpg_port_cbfcpause_counters(network_controller_obj=network_controller_obj, dut_port=dut_port_2,
                                            shape=shape, priority_list=priority_list)

        fun_test.log("Fetch fpg stats on dut port %s" % dut_port_1)
        result_dict[fpg_cbfcpause_counters_tx] = \
            get_fpg_port_cbfcpause_counters(network_controller_obj=network_controller_obj, dut_port=dut_port_1,
                                            shape=shape, tx=True, priority_list=priority_list)

        for key, val in result_dict[spirent_rx_counters].iteritems():
            if key in egress_check_streams:
                fun_test.test_assert(val, message="Ensure rx counter stopped for stream %s" % key)
            else:
                fun_test.test_assert(not val, message="Ensure rx counter hasn't stopped for stream %s" % key)

        for priority_val in priority_list:
            if priority_val <= 3:
                fun_test.test_assert(result_dict[psw_port_pg_counters][priority_val][dequeue],
                                     message="Ensure pg dequeue is happening for queue q_%s" % priority_val)

            else:
                fun_test.test_assert(not result_dict[psw_port_pg_counters][priority_val][dequeue],
                                     message="Ensure pg dequeue is not happening for queue q_%s" % priority_val)

            fun_test.test_assert(result_dict[psw_port_pg_counters][priority_val][enqueue],
                                 message="Ensure pg enqueue is happening for queue q_%s" % priority_val)

        for priority_val in priority_list[::4]:
            if priority_val == 0:
                fun_test.test_assert(result_dict[psw_port_q_counters][priority_val][dequeue],
                                     message="Ensure q dequeue is happening for queue q_%s" % priority_val)
            else:
                fun_test.test_assert(not result_dict[psw_port_q_counters][priority_val][dequeue],
                                     message="Ensure q dequeue is not happening for queue q_%s" % priority_val)
            fun_test.test_assert(result_dict[psw_port_q_counters][priority_val][enqueue],
                                 message="Ensure q enqueue is not happening for queue q_%s" % priority_val)

        for queue in priority_list:
            if queue == 4:
                fun_test.test_assert(result_dict[fpg_cbfcpause_counters_rx][queue],
                                     message="Ensure CBFCPause_Received in seen for priority %s" % queue)
            else:
                fun_test.test_assert(not result_dict[fpg_cbfcpause_counters_rx][queue],
                                     message="Ensure CBFCPause_Received in not seen for priority %s" % queue)

            if queue in priority_list[4:]:
                fun_test.test_assert(result_dict[fpg_cbfcpause_counters_tx][queue],
                                     message="Ensure CBFCPause_Transmitted in seen for priority %s" % queue)
            else:
                fun_test.test_assert(not result_dict[fpg_cbfcpause_counters_tx][queue],
                                     message="Ensure CBFCPause_Transmitted in not seen for priority %s" % queue)

        # Start capture
        capture_obj = Capture()
        start_capture = template_obj.stc_manager.start_capture_command(capture_obj=capture_obj,
                                                                       port_handle=port_1)
        fun_test.test_assert(start_capture, "Started capture on port %s" % port_1)

        fun_test.sleep("Letting capture to start", seconds=5)

        # Stop pfc stream
        stop_pfc = template_obj.stc_manager.stop_traffic_stream(
            stream_blocks_list=pfc_stream_list[0])
        fun_test.test_assert(stop_pfc, "Ensure pfc is stopped")

        fun_test.sleep("Letting pfc to stop", seconds=10)

        stop_capture = template_obj.stc_manager.stop_capture_command(capture_obj._spirent_handle)
        fun_test.test_assert(stop_capture, "Stopped capture on port %s" % port_1)

        file = fun_test.get_temp_file_name()
        file_name_1 = file + '.pcap'
        file_path = SYSTEM_TMP_DIR
        self.pcap_file_path_1 = file_path + "/" + file_name_1

        saved = template_obj.stc_manager.save_capture_data_command(capture_handle=capture_obj._spirent_handle,
                                                                   file_name=file_name_1,
                                                                   file_name_path=file_path)
        fun_test.test_assert(saved, "Saved pcap %s to local machine" % self.pcap_file_path_1)

        fun_test.test_assert(os.path.exists(self.pcap_file_path_1), message="Check pcap file exists locally")

        pcap_parser_1 = PcapParser(self.pcap_file_path_1)

        # Check if atleast one packet exists for each priority with quanta value specified and 0
        compare_dict = {}
        cbfc_class_pause_times = 'cbfc_class_pause_times'
        macc_cbfc_enbv_tree = 'macc_cbfc_enbv_tree'
        all_captures = pcap_parser_1.get_captures_from_file()
        for priority in pfc_affected_priority:
            compare_dict[priority] = {}
            compare_dict[priority]['quanta_val_seen'] = False
            compare_dict[priority]['zero_quanta_seen'] = False
            for capture in all_captures:
                output_dict = pcap_parser_1.get_all_packet_fields(capture)
                layer = output_dict[pcap_parser_1.LAYER_MACC]
                macc_cbfc_pause_time = 'macc_cbfc_pause_time_c' + str(priority)
                macc_cbfc_enbv = 'macc_cbfc_enbv_c' + str(priority)
                if str(layer[macc_cbfc_enbv_tree][macc_cbfc_enbv]) == '1':
                    if str(layer[cbfc_class_pause_times][macc_cbfc_pause_time]) == str(quanta):
                        compare_dict[priority]['quanta_val_seen'] = True
                    elif str(layer[cbfc_class_pause_times][macc_cbfc_pause_time]) == str(zero_quanta_value):
                        compare_dict[priority]['zero_quanta_seen'] = True
                if compare_dict[priority]['quanta_val_seen'] and compare_dict[priority]['zero_quanta_seen']:
                    break

        for priority in pfc_affected_priority:
            fun_test.test_assert(compare_dict[priority]['quanta_val_seen'],
                                 message="Ensure quanta value %s seen for priotiy %s in capture file" %
                                         (quanta, priority))
            fun_test.test_assert(compare_dict[priority]['quanta_val_seen'],
                                 message="Ensure quanta value %s seen for priotiy %s in capture file" %
                                         (zero_quanta_value, priority))


if __name__ == "__main__":
    local_settings = nu_config_obj.get_local_settings_parameters(flow_direction=True, ip_version=True)
    flow_direction = local_settings[nu_config_obj.FLOW_DIRECTION]
    ts = SpirentSetup()
    ts.add_test_case(TestCase1())
    ts.run()