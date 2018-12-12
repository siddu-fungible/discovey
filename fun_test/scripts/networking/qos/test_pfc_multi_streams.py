from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, GeneratorConfig, Ethernet2Header, Ipv4Header, Capture
from lib.utilities.pcap_parser import PcapParser
from lib.host.network_controller import NetworkController
from scripts.networking.nu_config_manager import nu_config_obj
from scripts.networking.helper import *
import re

num_ports = 2
good_stream_list = []
pfc_stream_list = []
pfc_stream_obj_list = []
good_streamblock_objs = {}
pfc_streamblock_objs = {}
streamblock_objs = {}
generator_config_objs = {}
generator_dict = {}
multiplyer = 52
default_quanta = 65535
pause_dut_port_quanta = 60000
pause_dut_port_threshold = 600
capture_priority_limit = 8
priority_dict = {'priority_0': {'priority_val': 0, 'ls_octet': '00000001', 'ms_octet': '00000000',
                                'quanta_val': {'0': '0', 'F': 'FFFF'}, 'dscp_high': '0', 'dscp_low': '0'},
                 'priority_1': {'priority_val': 1, 'ls_octet': '00000010', 'ms_octet': '00000000',
                                'quanta_val': {'0': '0', 'F': 'FFFF'}, 'dscp_high': '0', 'dscp_low': '1'},
                 'priority_2': {'priority_val': 2, 'ls_octet': '00000100', 'ms_octet': '00000000',
                                'quanta_val': {'0': '0', 'F': 'FFFF'}, 'dscp_high': '0', 'dscp_low': '2'},
                 'priority_3': {'priority_val': 3, 'ls_octet': '00001000', 'ms_octet': '00000000',
                                'quanta_val': {'0': '0', 'F': 'FFFF'}, 'dscp_high': '0', 'dscp_low': '3'},
                 'priority_4': {'priority_val': 4, 'ls_octet': '00010000', 'ms_octet': '00000000',
                                'quanta_val': {'0': '0', 'F': 'FFFF'}, 'dscp_high': '0', 'dscp_low': '4'},
                 'priority_5': {'priority_val': 5, 'ls_octet': '00100000', 'ms_octet': '00000000',
                                'quanta_val': {'0': '0', 'F': 'FFFF'}, 'dscp_high': '0', 'dscp_low': '5'},
                 'priority_6': {'priority_val': 6, 'ls_octet': '01000000', 'ms_octet': '00000000',
                                'quanta_val': {'0': '0', 'F': 'FFFF'}, 'dscp_high': '0', 'dscp_low': '6'},
                 'priority_7': {'priority_val': 7, 'ls_octet': '10000000', 'ms_octet': '00000000',
                                'quanta_val': {'0': '0', 'F': 'FFFF'}, 'dscp_high': '0', 'dscp_low': '7'},
                 'priority_8': {'priority_val': 8, 'ls_octet': '00000000', 'ms_octet': '00000001',
                                'quanta_val': {'0': '0' * multiplyer, 'F': 'F' * multiplyer}, 'dscp_high': '1', 'dscp_low': '0'},
                 'priority_9': {'priority_val': 9, 'ls_octet': '00000000', 'ms_octet': '00000010',
                                'quanta_val': {'0': '0' * multiplyer, 'F': 'F' * multiplyer}, 'dscp_high': '1', 'dscp_low': '1'},
                 'priority_10': {'priority_val': 10, 'ls_octet': '00000000', 'ms_octet': '00000100',
                                 'quanta_val': {'0': '0' * multiplyer, 'F': 'F' * multiplyer}, 'dscp_high': '1', 'dscp_low': '2'},
                 'priority_11': {'priority_val': 11, 'ls_octet': '00000000', 'ms_octet': '00001000',
                                 'quanta_val': {'0': '0' * multiplyer, 'F': 'F' * multiplyer}, 'dscp_high': '1', 'dscp_low': '3'},
                 'priority_12': {'priority_val': 12, 'ls_octet': '00000000', 'ms_octet': '00010000',
                                 'quanta_val': {'0': '0' * multiplyer, 'F': 'F' * multiplyer}, 'dscp_high': '1', 'dscp_low': '4'},
                 'priority_13': {'priority_val': 13, 'ls_octet': '00000000', 'ms_octet': '00100000',
                                 'quanta_val': {'0': '0' * multiplyer, 'F': 'F' * multiplyer}, 'dscp_high': '1', 'dscp_low': '5'},
                 'priority_14': {'priority_val': 14, 'ls_octet': '00000000', 'ms_octet': '01000000',
                                 'quanta_val': {'0': '0' * multiplyer, 'F': 'F' * multiplyer}, 'dscp_high': '1', 'dscp_low': '6'},
                 'priority_15': {'priority_val': 15, 'ls_octet': '00000000', 'ms_octet': '10000000',
                                 'quanta_val': {'0': '0' * multiplyer, 'F': 'F' * multiplyer}, 'dscp_high': '1', 'dscp_low': '7'}}

priority_list = [val['priority_val'] for val in priority_dict.itervalues()]
k_list = [x for x in range(0, 16)]
k_list.reverse()


class SpirentSetup(FunTestScript):
    min_thr = 512
    shr_thr = 2000
    hdr_thr = 20
    xoff_enable = 1
    shared_xon_thr = 5
    quanta = 5000
    threshold = 500

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
            dut_port_1, hnu, shape, pause_obj, dut_port_list, pause_streamblock, interface_obj_list

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
        pfc_load = 10
        pause_load = 60
        fun_test.log("Creating Template object")
        template_obj = SpirentEthernetTrafficTemplate(session_name="test_pfc_multi_stream", spirent_config=spirent_config,
                                                      chassis_type=chassis_type)
        fun_test.test_assert(template_obj, "Create template object")

        destination_mac1 = spirent_config['l2_config']['destination_mac']
        destination_ip1 = spirent_config['l3_config']['ipv4']['destination_ip1']
        dut_port_list = []
        dut_port_1 = dut_config['ports'][0]
        dut_port_2 = dut_config['ports'][1]
        dut_port_list.append(dut_port_1)
        dut_port_list.append(dut_port_2)

        # Create network controller object
        dpcsh_server_ip = dut_config['dpcsh_tcp_proxy_ip']
        dpcsh_server_port = int(dut_config['dpcsh_tcp_proxy_port'])
        network_controller_obj = NetworkController(dpc_server_ip=dpcsh_server_ip, dpc_server_port=dpcsh_server_port)

        for key in priority_dict.keys():
            priority_value = priority_dict[key]['priority_val']
            set_qos_ingress = network_controller_obj.set_qos_ingress_priority_group(port_num=dut_port_1,
                                                                                    priority_group_num=priority_value,
                                                                                    min_threshold=self.min_thr,
                                                                                    shared_threshold=self.shr_thr,
                                                                                    headroom_threshold=self.hdr_thr,
                                                                                    xoff_enable=self.xoff_enable,
                                                                                    shared_xon_threshold=self.shared_xon_thr)
            fun_test.test_assert(set_qos_ingress, "Setting qos ingress priority group")

            port_quanta = network_controller_obj.set_priority_flow_control_quanta(port_num=dut_port_1,
                                                                                  quanta=self.quanta,
                                                                                  class_num=priority_value,
                                                                                  shape=shape)
            fun_test.test_assert(port_quanta, "Ensure quanta %s is set on port %s" % (self.quanta, dut_port_1))

            port_thr = network_controller_obj.set_priority_flow_control_threshold(port_num=dut_port_1,
                                                                                  threshold=self.threshold,
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

        flow_dir = nu_config_obj.FLOW_DIRECTION_NU_NU
        if hnu:
            flow_dir = nu_config_obj.FLOW_DIRECTION_HNU_HNU
        result = template_obj.setup(no_of_ports_needed=num_ports, flow_direction=flow_dir)
        fun_test.test_assert(result['result'], "Configure setup")

        port_obj_list = result['port_list']
        port_1 = port_obj_list[0]
        port_2 = port_obj_list[1]
        interface_obj_list = result['interface_obj_list']

        # Enable flow control on both spirent ports
        for current_interface_obj in interface_obj_list:
            current_interface_obj.FlowControl = True

            update_result = template_obj.configure_physical_interface(interface_obj=current_interface_obj)
            fun_test.simple_assert(update_result, "Enable flow control on interface %s" %
                                   current_interface_obj._spirent_handle)

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

            else:
                for key, val in priority_dict.iteritems():
                    # Create stream on port 2
                    pfc_streamblock_objs[key] = {}
                    create_streamblock_2 = StreamBlock(load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND, load=pfc_load,
                                                       fixed_frame_length=64, insert_signature=False)
                    streamblock_2 = template_obj.configure_stream_block(create_streamblock_2, port_handle=port_2)
                    fun_test.test_assert(streamblock_2, message="Creating pfc streamblock with priority %s on port "
                                                                "%s" % (key, port_2))

                    if val['priority_val'] >= 8:
                        reserved = val['quanta_val']['F']
                    else:
                        reserved = ''
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
                                                                              ls_octet=val['ls_octet'],
                                                                              ms_octet=val['ms_octet'],
                                                                              reserved=reserved)
                    fun_test.test_assert(out['result'], message="Added frame stack")
                    pfc_streamblock_objs[key]['streamblock_obj'] = create_streamblock_2
                    pfc_streamblock_objs[key]['pfc_header_obj'] = out['pfc_header_obj']
                    pfc_stream_obj_list.append(create_streamblock_2)
                    pfc_stream_list.append(create_streamblock_2._spirent_handle)

                # Create stream on port 2
                pause_streamblock = StreamBlock(load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND,
                                                load=pause_load,
                                                fixed_frame_length=64, insert_signature=False)
                streamblock_2 = template_obj.configure_stream_block(pause_streamblock, port_handle=port_2)
                fun_test.test_assert(streamblock_2, message="Creating streamblock on port %s" % port_2)

                # Configure pause frame on stream 2
                out = template_obj.configure_pause_mac_control_header(pause_streamblock)
                fun_test.test_assert(out['result'], message="Added frame stack")
                pause_obj = out['pause_mac_control_header_obj']
                pause_ethernet_obj = out['ethernet8023_mac_control_header_obj']
        # Applying configuration
        apply = template_obj.stc_manager.apply_configuration()
        fun_test.test_assert(apply, "Applying Generator config")

        # Subscribe to results
        project = template_obj.stc_manager.get_project_handle()
        subscribe_results = template_obj.subscribe_to_all_results(parent=project)
        fun_test.test_assert(subscribe_results['result'], "Subscribing to results")
        del subscribe_results['result']

        disable_pfc_stream = template_obj.deactivate_stream_blocks(
            stream_obj_list=pfc_stream_obj_list)
        fun_test.test_assert(disable_pfc_stream, "Disable stream %s" % pfc_stream_list)

    def cleanup(self):
        # Cleanup spirent session
        fun_test.test_assert(template_obj.cleanup(), "Cleaning up session")

        disable_1 = network_controller_obj.disable_priority_flow_control(dut_port_1, shape=shape)
        fun_test.test_assert(disable_1, "Disable pfc on port %s" % dut_port_1)
        disable_2 = network_controller_obj.disable_priority_flow_control(dut_port_2, shape=shape)
        fun_test.test_assert(disable_2, "Disable pfc on port %s" % dut_port_2)


class TestCase1(FunTestCase):
    final_quanta_value = 0
    quanta = 5000
    current_priority_value = 1
    priority_key = 'priority_%s' % current_priority_value
    zero_quanta_value = 0
    capture_quanta_checker = {'time1': quanta, 'time2': zero_quanta_value, 'time3': zero_quanta_value, 'time4': zero_quanta_value,
                              'time5': zero_quanta_value, 'time6': zero_quanta_value, 'time7': zero_quanta_value}

    def pcap_output(self):
        if not self.current_priority_value > 7:
            pcap_parser_1 = PcapParser(self.pcap_file_path_1)
            output = pcap_parser_1.verify_pfc_header_fields(last_packet=True, time1=str(self.final_quanta_value))
            fun_test.test_assert(output, "Ensure value of quanta is 0 in the last pfc packet")

            first = pcap_parser_1.verify_pfc_header_fields(first_packet=True,
                                                           time1=self.capture_quanta_checker['time1'],
                                                           time2=self.capture_quanta_checker['time2'],
                                                           time3=self.capture_quanta_checker['time3'],
                                                           time4=self.capture_quanta_checker['time4'],
                                                           time5=self.capture_quanta_checker['time5'],
                                                           time6=self.capture_quanta_checker['time6'],
                                                           time7=self.capture_quanta_checker['time7'])
            fun_test.test_assert(first, "Value of quanta %s seen in pfc first packet" % self.quanta)

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test DUT with pfc enabled for priority %s" % self.priority_key,
                              steps="""
                                1. Enable good streams for all priorities.
                                2. Now enable priority %s
                                3. Check rx counter on spirent for each good stream. Must be stopped only for 
                                   priority selected
                                4. Check fpg stats on pfc ingress port for correct counter getting marked
                                5. Check pg enqueue, dequeue in psw port stats for each queue. Enqueue must increase
                                   while dequeue must remain the same
                                6. Check q enqueue, dequeue in egress port for each queue. Enqueue must happen and
                                   dequeue must not happen
                                7. Start capture on dut port1
                                8. Check that rx has started for streams coming from port1 as pfc frames are stopped.
                                9. Check pg queue dequeue has started.
                                10. Check q dequeue has started
                                11. Check pg enqueue and pg dequeue continues to happen
                                12. Stop pfc traffic from port2 and stop capture on port1 after some time
                                13. Check quanta value of first packet in capture is set to quanta set on dut port
                                14. Check quanta value is 0 for last pfc packet sent from dut_port to spirent
                                """ % self.priority_key)

    def setup(self):
        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1, shape=shape)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2, shape=shape)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

    def cleanup(self):
        # Stop traffic from port 1
        stop = template_obj.disable_generator_configs(generator_configs=generator_dict[port_1])
        fun_test.test_assert(stop, "Stopping generator config on port %s" % port_1)

        # Stop traffic from port 2
        stop = template_obj.disable_generator_configs(generator_configs=generator_dict[port_2])
        fun_test.test_assert(stop, "Stopping generator config on port %s" % port_2)

        current_pfc_stream_obj = pfc_streamblock_objs[self.priority_key]['streamblock_obj']
        disable_pfc_stream = template_obj.deactivate_stream_blocks(stream_obj_list=[current_pfc_stream_obj])
        fun_test.simple_assert(disable_pfc_stream, "Disable stream %s" % current_pfc_stream_obj)

        # Clear all subscribed results
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

        if self.current_priority_value <= 7:
            if self.pcap_file_path_1:
                fun_test.remove_file(file_path=self.pcap_file_path_1)

    def run(self):
        sleep_time = 5
        result_dict = {}
        spirent_rx_counters = 'spirent_rx_counters'
        spirent_pfc_rx_counter = 'spirent_pfc_rx_counter'
        fpg_cbfcpause_counters_tx = 'fpg_cbfcpause_counters_tx'
        fpg_cbfcpause_counters_rx = 'fpg_cbfcpause_counters_rx'
        psw_port_pg_counters = 'psw_port_pg_counters'
        psw_port_q_counters = 'psw_port_q_counters'
        dequeue = 'dequeue'
        enqueue = 'enqueue'
        current_pfc_stream_obj = pfc_streamblock_objs[self.priority_key]['streamblock_obj']
        current_pfc_stream_handle = current_pfc_stream_obj._spirent_handle

        # Activate pfc stream
        enable_pfc_stream = template_obj.activate_stream_blocks(stream_obj_list=[current_pfc_stream_obj])
        fun_test.simple_assert(enable_pfc_stream, "Enable stream %s" % current_pfc_stream_handle)

        # Activate all good streams
        start_good = template_obj.stc_manager.start_traffic_stream(stream_blocks_list=good_stream_list)
        fun_test.test_assert(start_good, "Start good stream traffic")

        fun_test.sleep("Letting traffic get executed", seconds=sleep_time)
        fun_test.log("############ Starting traffic for pfc priority %s ###########" % self.current_priority_value)

        result_dict[self.current_priority_value] = {}

        fun_test.log("Starting traffic for priority %s" % self.current_priority_value)
        start_pfc = template_obj.stc_manager.start_traffic_stream(
            stream_blocks_list=[current_pfc_stream_handle])
        fun_test.test_assert(start_pfc, " PFC started for priority %s" % current_pfc_stream_handle)

        fun_test.sleep("Letting pfc stream get started", seconds=30)

        fun_test.log("Fetch spirent rx counter results for all good streams")
        result_dict[self.current_priority_value][spirent_rx_counters] = \
            find_spirent_rx_counters_stopped(streamblock_handle_list=good_stream_list, template_obj=template_obj,
                                             subscribe_result=subscribe_results)

        result_dict[self.current_priority_value][spirent_pfc_rx_counter] = \
            find_spirent_rx_counters_stopped(port_handle=port_1,
                                             template_obj=template_obj,
                                             subscribe_result=subscribe_results, pfc_stream=True)

        fun_test.log("Fetch fpg stats on dut port %s" % dut_port_2)
        result_dict[self.current_priority_value][fpg_cbfcpause_counters_tx] = \
            get_fpg_port_cbfcpause_counters(network_controller_obj=network_controller_obj, dut_port=dut_port_2, shape=shape)

        fun_test.log("Fetch fpg stats on dut port %s" % dut_port_1)
        result_dict[self.current_priority_value][fpg_cbfcpause_counters_rx] = \
            get_fpg_port_cbfcpause_counters(network_controller_obj=network_controller_obj, dut_port=dut_port_1,
                                            shape=shape, tx=True)

        fun_test.log("Get psw port group enqueue dequeue counters")
        result_dict[self.current_priority_value][psw_port_pg_counters] = \
            get_psw_port_enqueue_dequeue_counters(network_controller_obj=network_controller_obj,
                                                  dut_port=dut_port_1, pg=True, hnu=hnu)

        fun_test.log("Get psw port queue enqueue dequeue counters")
        result_dict[self.current_priority_value][psw_port_q_counters] = \
            get_psw_port_enqueue_dequeue_counters(network_controller_obj=network_controller_obj,
                                                  dut_port=dut_port_2, hnu=hnu)

        # ASSERTS
        spirent_counters_dict = result_dict[self.current_priority_value][spirent_rx_counters]
        fpg_counters_dict_2 = result_dict[self.current_priority_value][fpg_cbfcpause_counters_tx]
        fpg_counters_dict_1 = result_dict[self.current_priority_value][fpg_cbfcpause_counters_rx]
        pg_queue_counters_dict = result_dict[self.current_priority_value][psw_port_pg_counters]
        q_queue_counters_dict = result_dict[self.current_priority_value][psw_port_q_counters]

        # Spirent Asserts

        for stream in spirent_counters_dict.iterkeys():
            if stream == good_streamblock_objs[self.priority_key]['streamblock_obj']._spirent_handle:
                fun_test.test_assert(spirent_counters_dict[stream],
                                     message="Ensure rx counter stopped for stream %s "
                                             "corresponding to pfc priority %s" % (
                                     stream, self.current_priority_value))
            else:
                fun_test.test_assert(not spirent_counters_dict[stream],
                                     message="Ensure rx counter is not stopped "
                                             "for stream %s when pfc is started for priority %s" %
                                             (stream, self.current_priority_value))

        # Check spirent pfc rx is not stopped
        fun_test.test_assert(not result_dict[self.current_priority_value][spirent_pfc_rx_counter][str(port_1)],
                             message="Ensure spirent port %s is getting pfc frames from dut port %s" % (port_1,
                                                                                                       dut_port_1))

        for priority in priority_list:
            if self.current_priority_value == priority:
                fun_test.test_assert(fpg_counters_dict_2[priority], message="Ensure fpg mac stats seen for "
                                                                          "queue with priority %s when pfc "
                                                                          "stream for %s was received by dut port %s"
                                                                          % (priority, self.current_priority_value, 
                                                                             dut_port_2))

                fun_test.test_assert(fpg_counters_dict_1[priority], message="Ensure fpg mac stats seen for "
                                                                            "queue with priority %s when pfc "
                                                                            "stream for %s was sent from dut port %s"
                                                                            % (priority, self.current_priority_value, 
                                                                               dut_port_1))

                fun_test.test_assert(not pg_queue_counters_dict[priority][dequeue],
                                     message="Ensure pg dequeue is not happening for queue q_%s when pfc with "
                                             "priority %s was sent" % (priority, self.current_priority_value))

                fun_test.test_assert(pg_queue_counters_dict[priority][enqueue],
                                     message="Ensure pg enqueue is happening for queue q_%s when pfc with "
                                             "priority %s was sent" % (priority, self.current_priority_value))

                fun_test.test_assert(not q_queue_counters_dict[priority][dequeue],
                                     message="Ensure q dequeue is not happening for queue q_%s when pfc with "
                                             "priority %s was sent" % (priority, self.current_priority_value))

                fun_test.test_assert(q_queue_counters_dict[priority][enqueue],
                                     message="Ensure q enqueue is not happening for queue q_%s when pfc with "
                                             "priority %s was sent" % (priority, self.current_priority_value))

            else:
                fun_test.test_assert(not fpg_counters_dict_2[priority], message="Ensure counter values of queue %s "
                                                                              "were not seen on dut port %s when pfc with priority"
                                                                              " %s was sent" 
                                                                                % (priority, dut_port_2,
                                                                                   self.current_priority_value))

                fun_test.test_assert(not fpg_counters_dict_1[priority], message="Ensure counter values of queue %s "
                                                                                "were not seen on dut port %s when pfc with priority"
                                                                                " %s was sent"
                                                                                % (priority, dut_port_1,
                                                                                   self.current_priority_value))

                fun_test.test_assert(pg_queue_counters_dict[priority][dequeue],
                                     message="Ensure dequeue is happening for queue q_%s when pfc with "
                                             "priority %s was sent" % (priority, self.current_priority_value))

                fun_test.test_assert(pg_queue_counters_dict[priority][enqueue],
                                     message="Ensure enqueue is happening for queue q_%s when pfc with "
                                             "priority %s was sent" % (priority, self.current_priority_value))

                fun_test.test_assert(q_queue_counters_dict[priority][dequeue],
                                     message="Ensure dequeue is happening for queue q_%s when pfc with "
                                             "priority %s was sent" % (priority, self.current_priority_value))

                fun_test.test_assert(q_queue_counters_dict[priority][enqueue],
                                     message="Ensure enqueue is happening for queue q_%s when pfc with "
                                             "priority %s was sent" % (priority, self.current_priority_value))

        # Starting capture of packet
        if self.current_priority_value < capture_priority_limit:
            capture_obj = Capture()
            start_capture = template_obj.stc_manager.start_capture_command(capture_obj=capture_obj, port_handle=port_1)
            fun_test.test_assert(start_capture, "Started capture on port %s" % port_1)

            fun_test.sleep("Letting capture to start", seconds=5)

        # Stop traffic from port 1
        stop = template_obj.disable_generator_configs(generator_configs=generator_dict[port_2])
        fun_test.test_assert(stop, "Stopping pfc on port %s" % port_2)

        fun_test.sleep("Letting pfc get stopped", seconds=sleep_time)

        # Check if transmission has started for streams for whom pfc has been stopped
        output_dict = {}
        output_dict[self.current_priority_value] = {}
        fun_test.log("Fetch spirent rx counter results")
        output_dict[self.current_priority_value][spirent_rx_counters] = \
            find_spirent_rx_counters_stopped(streamblock_handle_list=good_stream_list, template_obj=template_obj,
                                             subscribe_result=subscribe_results)

        output_dict[self.current_priority_value][spirent_pfc_rx_counter] = \
            find_spirent_rx_counters_stopped(port_handle=port_1,
                                             template_obj=template_obj,
                                             subscribe_result=subscribe_results, pfc_stream=True)

        fun_test.log("Fetch fpg stats on dut port %s" % dut_port_2)
        output_dict[self.current_priority_value][fpg_cbfcpause_counters_tx] = \
            get_fpg_port_cbfcpause_counters(network_controller_obj=network_controller_obj, dut_port=dut_port_2, shape=shape)

        fun_test.log("Fetch fpg stats on dut port %s" % dut_port_1)
        output_dict[self.current_priority_value][fpg_cbfcpause_counters_rx] = \
            get_fpg_port_cbfcpause_counters(network_controller_obj=network_controller_obj, dut_port=dut_port_1, tx=True, shape=shape)

        fun_test.log("Get psw port group enqueue dequeue counters")
        output_dict[self.current_priority_value][psw_port_pg_counters] = \
            get_psw_port_enqueue_dequeue_counters(network_controller_obj=network_controller_obj,
                                                  dut_port=dut_port_1, pg=True, hnu=hnu)

        fun_test.log("Get psw port queue enqueue dequeue counters")
        output_dict[self.current_priority_value][psw_port_q_counters] = \
            get_psw_port_enqueue_dequeue_counters(network_controller_obj=network_controller_obj,
                                                  dut_port=dut_port_2, hnu=hnu)

        spirent_counters_dict = output_dict[self.current_priority_value][spirent_rx_counters]
        fpg_counters_dict_2 = output_dict[self.current_priority_value][fpg_cbfcpause_counters_tx]
        fpg_counters_dict_1 = output_dict[self.current_priority_value][fpg_cbfcpause_counters_rx]
        pg_queue_counters_dict = output_dict[self.current_priority_value][psw_port_pg_counters]
        q_queue_counters_dict = output_dict[self.current_priority_value][psw_port_q_counters]

        fun_test.log("Log all good stream counters %s" % spirent_counters_dict)
        fun_test.log("Log all pfc stream counters %s" % spirent_pfc_rx_counter)
        fun_test.log("Log cbfc pause counters on dut rx %s" % fpg_counters_dict_2)
        fun_test.log("Log cbfc pause counters on dut tx %s" % fpg_counters_dict_1)
        fun_test.log("Log pg queue counters on dut ingress port %s" % pg_queue_counters_dict)
        fun_test.log("Log queue counters on dut egress port %s" % pg_queue_counters_dict)

        for key in spirent_counters_dict.iterkeys():
            fun_test.test_assert(not spirent_counters_dict[key], "Ensure rx on spirent is happening for stream %s "
                                                                 "when pfc is stopped"
                                                                 " for priority %s" % (key, self.current_priority_value))

        # Check spirent pfc rx is stopped
        fun_test.test_assert(output_dict[self.current_priority_value][spirent_pfc_rx_counter][str(port_1)],
                             message="Ensure spirent port %s is not getting pfc frames from dut port %s" % (port_1,
                                                                                                        dut_port_1))

        for priority in priority_list:
            fun_test.test_assert(not fpg_counters_dict_2[priority], message="Ensure fpg mac stats not seen for "
                                                                        "queue with priority %s when pfc "
                                                                        "stream for %s was stopped by dut port %s"
                                                                        % (priority, self.current_priority_value,
                                                                           dut_port_2))

            fun_test.test_assert(not fpg_counters_dict_1[priority], message="Ensure fpg mac stats not seen for "
                                                                        "queue with priority %s when pfc "
                                                                        "stream for %s was stopped from dut port %s"
                                                                        % (priority, self.current_priority_value,
                                                                           dut_port_1))

            fun_test.test_assert(pg_queue_counters_dict[priority][dequeue],
                                 message="Ensure dequeue is happening for queue q_%s when pfc with "
                                         "priority %s was stopped" % (priority, self.current_priority_value))

            fun_test.test_assert(pg_queue_counters_dict[priority][enqueue],
                                 message="Ensure enqueue is happening for queue q_%s when pfc with "
                                         "priority %s was stopped" % (priority, self.current_priority_value))

            fun_test.test_assert(q_queue_counters_dict[priority][dequeue],
                                 message="Ensure dequeue is happening for queue q_%s when pfc with "
                                         "priority %s was stopped" % (priority, self.current_priority_value))

            fun_test.test_assert(q_queue_counters_dict[priority][enqueue],
                                 message="Ensure enqueue is happening for queue q_%s when pfc with "
                                         "priority %s was stopped" % (priority, self.current_priority_value))

        if self.current_priority_value < capture_priority_limit:
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

            self.pcap_output()


class TestCase2(TestCase1):
    current_priority_value = 2
    priority_key = 'priority_%s' % current_priority_value
    capture_quanta_checker = {'time1': TestCase1.zero_quanta_value, 'time2': TestCase1.quanta,
                              'time3': TestCase1.zero_quanta_value,'time4': TestCase1.zero_quanta_value,
                              'time5': TestCase1.zero_quanta_value, 'time6': TestCase1.zero_quanta_value,
                              'time7': TestCase1.zero_quanta_value}

    def describe(self):
        self.set_test_details(id=2,
                              summary="Test DUT with pfc enabled for priority %s" % self.priority_key,
                              steps="""
                                  1. Enable good streams for all priorities.
                                  2. Now enable each priority %s
                                  3. Check rx counter on spirent for each good stream. Must be stopped only for 
                                     priority selected
                                  4. Check fpg stats on pfc ingress port for correct counter getting marked
                                  5. Check pg enqueue, dequeue in psw port stats for each queue. Enqueue must increase
                                     while dequeue must remain the same
                                  6. Check q enqueue, dequeue in egress port for each queue. Enqueue must not happen and
                                     dequeue also must not happen
                                  7. Start capture on dut port1
                                8. Check that rx has started for streams coming from port1 as pfc frames are stopped.
                                9. Check pg queue dequeue has started.
                                10. Check q dequeue has started
                                11. Check pg enqueue and pg dequeue continues to happen
                                12. Stop pfc traffic from port2 and stop capture on port1 after some time
                                13. Check quanta value of first packet in capture is set to quanta set on dut port
                                14. Check quanta value is 0 for last pfc packet sent from dut_port to spirent
                                  """ % self.priority_key)

    def setup(self):
        super(TestCase2, self).setup()

    def cleanup(self):
        super(TestCase2, self).cleanup()

    def run(self):
        super(TestCase2, self).run()


class TestCase3(TestCase1):
    current_priority_value = 3
    priority_key = 'priority_%s' % current_priority_value
    capture_quanta_checker = {'time1': TestCase1.zero_quanta_value, 'time2': TestCase1.zero_quanta_value,
                              'time3': TestCase1.quanta, 'time4': TestCase1.zero_quanta_value,
                              'time5': TestCase1.zero_quanta_value, 'time6': TestCase1.zero_quanta_value,
                              'time7': TestCase1.zero_quanta_value}

    def describe(self):
        self.set_test_details(id=3,
                              summary="Test DUT with pfc enabled for priority %s" % self.priority_key,
                              steps="""
                                  1. Enable good streams for all priorities.
                                  2. Now enable each priority %s
                                  3. Check rx counter on spirent for each good stream. Must be stopped only for 
                                     priority selected
                                  4. Check fpg stats on pfc ingress port for correct counter getting marked
                                  5. Check pg enqueue, dequeue in psw port stats for each queue. Enqueue must increase
                                     while dequeue must remain the same
                                  6. Check q enqueue, dequeue in egress port for each queue. Enqueue must not happen and
                                     dequeue also must not happen
                                  7. Start capture on dut port1
                                8. Check that rx has started for streams coming from port1 as pfc frames are stopped.
                                9. Check pg queue dequeue has started.
                                10. Check q dequeue has started
                                11. Check pg enqueue and pg dequeue continues to happen
                                12. Stop pfc traffic from port2 and stop capture on port1 after some time
                                13. Check quanta value of first packet in capture is set to quanta set on dut port
                                14. Check quanta value is 0 for last pfc packet sent from dut_port to spirent
                                  """ % self.priority_key)

    def setup(self):
        super(TestCase3, self).setup()

    def cleanup(self):
        super(TestCase3, self).cleanup()

    def run(self):
        super(TestCase3, self).run()


class TestCase4(TestCase1):
    current_priority_value = 4
    priority_key = 'priority_%s' % current_priority_value
    capture_quanta_checker = {'time1': TestCase1.zero_quanta_value, 'time2': TestCase1.zero_quanta_value,
                              'time3': TestCase1.zero_quanta_value, 'time4': TestCase1.quanta,
                              'time5': TestCase1.zero_quanta_value, 'time6': TestCase1.zero_quanta_value,
                              'time7': TestCase1.zero_quanta_value}

    def describe(self):
        self.set_test_details(id=4,
                              summary="Test DUT with pfc enabled for priority %s" % self.priority_key,
                              steps="""
                              1. Enable good streams for all priorities.
                              2. Now enable pfc stream with priority %s
                              3. Check rx counter on spirent for each good stream. Must be stopped only for 
                                 priority selected
                              4. Check fpg stats on pfc ingress port for correct counter getting marked
                              5. Check pg enqueue, dequeue in psw port stats for each queue. Enqueue must increase
                                 while dequeue must remain the same
                              6. Check q enqueue, dequeue in egress port for each queue. Enqueue must not happen and
                                 dequeue also must not happen
                              7. Start capture on dut port1
                              8. Check that rx has started for streams coming from port1 as pfc frames are stopped.
                              9. Check pg queue dequeue has started.
                              10. Check q dequeue has started
                              11. Check pg enqueue and pg dequeue continues to happen
                              12. Stop pfc traffic from port2 and stop capture on port1 after some time
                              13. Check quanta value of first packet in capture is set to quanta set on dut port
                              14. Check quanta value is 0 for last pfc packet sent from dut_port to spirent
                                  """ % self.priority_key)

    def setup(self):
        super(TestCase4, self).setup()

    def cleanup(self):
        super(TestCase4, self).cleanup()

    def run(self):
        super(TestCase4, self).run()


class TestCase5(TestCase1):
    current_priority_value = 5
    priority_key = 'priority_%s' % current_priority_value
    capture_quanta_checker = {'time1': TestCase1.zero_quanta_value, 'time2': TestCase1.zero_quanta_value,
                              'time3': TestCase1.zero_quanta_value, 'time4': TestCase1.zero_quanta_value,
                              'time5': TestCase1.quanta, 'time6': TestCase1.zero_quanta_value,
                              'time7': TestCase1.zero_quanta_value}

    def describe(self):
        self.set_test_details(id=5,
                              summary="Test DUT with pfc enabled for priority %s" % self.priority_key,
                              steps="""
                              1. Enable good streams for all priorities.
                              2. Now enable pfc stream with priority %s
                              3. Check rx counter on spirent for each good stream. Must be stopped only for 
                                 priority selected
                              4. Check fpg stats on pfc ingress port for correct counter getting marked
                              5. Check pg enqueue, dequeue in psw port stats for each queue. Enqueue must increase
                                 while dequeue must remain the same
                              6. Check q enqueue, dequeue in egress port for each queue. Enqueue must not happen and
                                 dequeue also must not happen
                              7. Start capture on dut port1
                              8. Check that rx has started for streams coming from port1 as pfc frames are stopped.
                              9. Check pg queue dequeue has started.
                              10. Check q dequeue has started
                              11. Check pg enqueue and pg dequeue continues to happen
                              12. Stop pfc traffic from port2 and stop capture on port1 after some time
                              13. Check quanta value of first packet in capture is set to quanta set on dut port
                              14. Check quanta value is 0 for last pfc packet sent from dut_port to spirent
                                  """ % self.priority_key)

    def setup(self):
        super(TestCase5, self).setup()

    def cleanup(self):
        super(TestCase5, self).cleanup()

    def run(self):
        super(TestCase5, self).run()


class TestCase6(TestCase1):
    current_priority_value = 6
    priority_key = 'priority_%s' % current_priority_value
    capture_quanta_checker = {'time1': TestCase1.zero_quanta_value, 'time2': TestCase1.zero_quanta_value,
                              'time3': TestCase1.zero_quanta_value, 'time4': TestCase1.zero_quanta_value,
                              'time5': TestCase1.zero_quanta_value, 'time6': TestCase1.quanta,
                              'time7': TestCase1.zero_quanta_value}

    def describe(self):
        self.set_test_details(id=6,
                              summary="Test DUT with pfc enabled for priority %s" % self.priority_key,
                              steps="""
                              1. Enable good streams for all priorities.
                              2. Now enable pfc stream with priority %s
                              3. Check rx counter on spirent for each good stream. Must be stopped only for 
                                 priority selected
                              4. Check fpg stats on pfc ingress port for correct counter getting marked
                              5. Check pg enqueue, dequeue in psw port stats for each queue. Enqueue must increase
                                 while dequeue must remain the same
                              6. Check q enqueue, dequeue in egress port for each queue. Enqueue must not happen and
                                 dequeue also must not happen
                              7. Start capture on dut port1
                              8. Check that rx has started for streams coming from port1 as pfc frames are stopped.
                              9. Check pg queue dequeue has started.
                              10. Check q dequeue has started
                              11. Check pg enqueue and pg dequeue continues to happen
                              12. Stop pfc traffic from port2 and stop capture on port1 after some time
                              13. Check quanta value of first packet in capture is set to quanta set on dut port
                              14. Check quanta value is 0 for last pfc packet sent from dut_port to spirent
                                  """ % self.priority_key)

    def setup(self):
        super(TestCase6, self).setup()

    def cleanup(self):
        super(TestCase6, self).cleanup()

    def run(self):
        super(TestCase6, self).run()


class TestCase7(TestCase1):
    current_priority_value = 7
    priority_key = 'priority_%s' % current_priority_value
    capture_quanta_checker = {'time1': TestCase1.zero_quanta_value, 'time2': TestCase1.zero_quanta_value,
                              'time3': TestCase1.zero_quanta_value, 'time4': TestCase1.zero_quanta_value,
                              'time5': TestCase1.zero_quanta_value, 'time6': TestCase1.zero_quanta_value,
                              'time7': TestCase1.quanta}

    def describe(self):
        self.set_test_details(id=7,
                              summary="Test DUT with pfc enabled for priority %s" % self.priority_key,
                              steps="""
                              1. Enable good streams for all priorities.
                              2. Now enable pfc stream with priority %s
                              3. Check rx counter on spirent for each good stream. Must be stopped only for 
                                 priority selected
                              4. Check fpg stats on pfc ingress port for correct counter getting marked
                              5. Check pg enqueue, dequeue in psw port stats for each queue. Enqueue must increase
                                 while dequeue must remain the same
                              6. Check q enqueue, dequeue in egress port for each queue. Enqueue must not happen and
                                 dequeue also must not happen
                              7. Start capture on dut port1
                              8. Check that rx has started for streams coming from port1 as pfc frames are stopped.
                              9. Check pg queue dequeue has started.
                              10. Check q dequeue has started
                              11. Check pg enqueue and pg dequeue continues to happen
                              12. Stop pfc traffic from port2 and stop capture on port1 after some time
                              13. Check quanta value of first packet in capture is set to quanta set on dut port
                              14. Check quanta value is 0 for last pfc packet sent from dut_port to spirent
                                  """ % self.priority_key)

    def setup(self):
        super(TestCase7, self).setup()

    def cleanup(self):
        super(TestCase7, self).cleanup()

    def run(self):
        super(TestCase7, self).run()


class TestCase8(TestCase1):
    current_priority_value = 8
    priority_key = 'priority_%s' % current_priority_value

    def pcap_output(self):
        pass

    def describe(self):
        self.set_test_details(id=8,
                              summary="Test DUT with pfc enabled for priority %s" % self.priority_key,
                              steps="""
                              1. Enable good streams for all priorities.
                              2. Now enable pfc stream with priority %s
                              3. Check rx counter on spirent for each good stream. Must be stopped only for 
                                 priority selected
                              4. Check fpg stats on pfc ingress port for correct counter getting marked
                              5. Check pg enqueue, dequeue in psw port stats for each queue. Enqueue must increase
                                 while dequeue must remain the same
                              6. Check q enqueue, dequeue in egress port for each queue. Enqueue must not happen and
                                 dequeue also must not happen
                              7. Start capture on dut port1
                              8. Check that rx has started for streams coming from port1 as pfc frames are stopped.
                              9. Check pg queue dequeue has started.
                              10. Check q dequeue has started
                              11. Check pg enqueue and pg dequeue continues to happen
                              12. Stop pfc traffic from port2 and stop capture on port1 after some time
                              13. Check quanta value of first packet in capture is set to quanta set on dut port
                              14. Check quanta value is 0 for last pfc packet sent from dut_port to spirent
                                  """ % self.priority_key)

    def setup(self):
        super(TestCase8, self).setup()

    def cleanup(self):
        super(TestCase8, self).cleanup()

    def run(self):
        super(TestCase8, self).run()


class TestCase9(TestCase1):
    current_priority_value = 9
    priority_key = 'priority_%s' % current_priority_value

    def pcap_output(self):
        pass

    def describe(self):
        self.set_test_details(id=9,
                              summary="Test DUT with pfc enabled for priority %s" % self.priority_key,
                              steps="""
                              1. Enable good streams for all priorities.
                              2. Now enable pfc stream with priority %s
                              3. Check rx counter on spirent for each good stream. Must be stopped only for 
                                 priority selected
                              4. Check fpg stats on pfc ingress port for correct counter getting marked
                              5. Check pg enqueue, dequeue in psw port stats for each queue. Enqueue must increase
                                 while dequeue must remain the same
                              6. Check q enqueue, dequeue in egress port for each queue. Enqueue must not happen and
                                 dequeue also must not happen
                              7. Start capture on dut port1
                              8. Check that rx has started for streams coming from port1 as pfc frames are stopped.
                              9. Check pg queue dequeue has started.
                              10. Check q dequeue has started
                              11. Check pg enqueue and pg dequeue continues to happen
                              12. Stop pfc traffic from port2 and stop capture on port1 after some time
                              13. Check quanta value of first packet in capture is set to quanta set on dut port
                              14. Check quanta value is 0 for last pfc packet sent from dut_port to spirent
                                  """ % self.priority_key)

    def setup(self):
        super(TestCase9, self).setup()

    def cleanup(self):
        super(TestCase9, self).cleanup()

    def run(self):
        super(TestCase9, self).run()


class TestCase10(TestCase1):
    current_priority_value = 10
    priority_key = 'priority_%s' % current_priority_value

    def pcap_output(self):
        pass

    def describe(self):
        self.set_test_details(id=10,
                              summary="Test DUT with pfc enabled for priority %s" % self.priority_key,
                              steps="""
                              1. Enable good streams for all priorities.
                              2. Now enable pfc stream with priority %s
                              3. Check rx counter on spirent for each good stream. Must be stopped only for 
                                 priority selected
                              4. Check fpg stats on pfc ingress port for correct counter getting marked
                              5. Check pg enqueue, dequeue in psw port stats for each queue. Enqueue must increase
                                 while dequeue must remain the same
                              6. Check q enqueue, dequeue in egress port for each queue. Enqueue must not happen and
                                 dequeue also must not happen
                              7. Start capture on dut port1
                              8. Check that rx has started for streams coming from port1 as pfc frames are stopped.
                              9. Check pg queue dequeue has started.
                              10. Check q dequeue has started
                              11. Check pg enqueue and pg dequeue continues to happen
                              12. Stop pfc traffic from port2 and stop capture on port1 after some time
                              13. Check quanta value of first packet in capture is set to quanta set on dut port
                              14. Check quanta value is 0 for last pfc packet sent from dut_port to spirent
                                  """ % self.priority_key)

    def setup(self):
        super(TestCase10, self).setup()

    def cleanup(self):
        super(TestCase10, self).cleanup()

    def run(self):
        super(TestCase10, self).run()


class TestCase11(TestCase1):
    current_priority_value = 11
    priority_key = 'priority_%s' % current_priority_value

    def pcap_output(self):
        pass

    def describe(self):
        self.set_test_details(id=11,
                              summary="Test DUT with pfc enabled for priority %s" % self.priority_key,
                              steps="""
                              1. Enable good streams for all priorities.
                              2. Now enable pfc stream with priority %s
                              3. Check rx counter on spirent for each good stream. Must be stopped only for 
                                 priority selected
                              4. Check fpg stats on pfc ingress port for correct counter getting marked
                              5. Check pg enqueue, dequeue in psw port stats for each queue. Enqueue must increase
                                 while dequeue must remain the same
                              6. Check q enqueue, dequeue in egress port for each queue. Enqueue must not happen and
                                 dequeue also must not happen
                              7. Start capture on dut port1
                              8. Check that rx has started for streams coming from port1 as pfc frames are stopped.
                              9. Check pg queue dequeue has started.
                              10. Check q dequeue has started
                              11. Check pg enqueue and pg dequeue continues to happen
                              12. Stop pfc traffic from port2 and stop capture on port1 after some time
                              13. Check quanta value of first packet in capture is set to quanta set on dut port
                              14. Check quanta value is 0 for last pfc packet sent from dut_port to spirent
                                  """ % self.priority_key)

    def setup(self):
        super(TestCase11, self).setup()

    def cleanup(self):
        super(TestCase11, self).cleanup()

    def run(self):
        super(TestCase11, self).run()


class TestCase12(TestCase1):
    current_priority_value = 12
    priority_key = 'priority_%s' % current_priority_value

    def pcap_output(self):
        pass

    def describe(self):
        self.set_test_details(id=12,
                              summary="Test DUT with pfc enabled for priority %s" % self.priority_key,
                              steps="""
                              1. Enable good streams for all priorities.
                              2. Now enable pfc stream with priority %s
                              3. Check rx counter on spirent for each good stream. Must be stopped only for 
                                 priority selected
                              4. Check fpg stats on pfc ingress port for correct counter getting marked
                              5. Check pg enqueue, dequeue in psw port stats for each queue. Enqueue must increase
                                 while dequeue must remain the same
                              6. Check q enqueue, dequeue in egress port for each queue. Enqueue must not happen and
                                 dequeue also must not happen
                              7. Start capture on dut port1
                              8. Check that rx has started for streams coming from port1 as pfc frames are stopped.
                              9. Check pg queue dequeue has started.
                              10. Check q dequeue has started
                              11. Check pg enqueue and pg dequeue continues to happen
                              12. Stop pfc traffic from port2 and stop capture on port1 after some time
                              13. Check quanta value of first packet in capture is set to quanta set on dut port
                              14. Check quanta value is 0 for last pfc packet sent from dut_port to spirent
                                  """ % self.priority_key)

    def setup(self):
        super(TestCase12, self).setup()

    def cleanup(self):
        super(TestCase12, self).cleanup()

    def run(self):
        super(TestCase12, self).run()


class TestCase13(TestCase1):
    current_priority_value = 13
    priority_key = 'priority_%s' % current_priority_value

    def pcap_output(self):
        pass

    def describe(self):
        self.set_test_details(id=13,
                              summary="Test DUT with pfc enabled for priority %s" % self.priority_key,
                              steps="""
                              1. Enable good streams for all priorities.
                              2. Now enable pfc stream with priority %s
                              3. Check rx counter on spirent for each good stream. Must be stopped only for 
                                 priority selected
                              4. Check fpg stats on pfc ingress port for correct counter getting marked
                              5. Check pg enqueue, dequeue in psw port stats for each queue. Enqueue must increase
                                 while dequeue must remain the same
                              6. Check q enqueue, dequeue in egress port for each queue. Enqueue must not happen and
                                 dequeue also must not happen
                              7. Start capture on dut port1
                              8. Check that rx has started for streams coming from port1 as pfc frames are stopped.
                              9. Check pg queue dequeue has started.
                              10. Check q dequeue has started
                              11. Check pg enqueue and pg dequeue continues to happen
                              12. Stop pfc traffic from port2 and stop capture on port1 after some time
                              13. Check quanta value of first packet in capture is set to quanta set on dut port
                              14. Check quanta value is 0 for last pfc packet sent from dut_port to spirent
                                  """ % self.priority_key)

    def setup(self):
        super(TestCase13, self).setup()

    def cleanup(self):
        super(TestCase13, self).cleanup()

    def run(self):
        super(TestCase13, self).run()


class TestCase14(TestCase1):
    current_priority_value = 14
    priority_key = 'priority_%s' % current_priority_value

    def pcap_output(self):
        pass

    def describe(self):
        self.set_test_details(id=14,
                              summary="Test DUT with pfc enabled for priority %s" % self.priority_key,
                              steps="""
                              1. Enable good streams for all priorities.
                              2. Now enable pfc stream with priority %s
                              3. Check rx counter on spirent for each good stream. Must be stopped only for 
                                 priority selected
                              4. Check fpg stats on pfc ingress port for correct counter getting marked
                              5. Check pg enqueue, dequeue in psw port stats for each queue. Enqueue must increase
                                 while dequeue must remain the same
                              6. Check q enqueue, dequeue in egress port for each queue. Enqueue must not happen and
                                 dequeue also must not happen
                              7. Start capture on dut port1
                              8. Check that rx has started for streams coming from port1 as pfc frames are stopped.
                              9. Check pg queue dequeue has started.
                              10. Check q dequeue has started
                              11. Check pg enqueue and pg dequeue continues to happen
                              12. Stop pfc traffic from port2 and stop capture on port1 after some time
                              13. Check quanta value of first packet in capture is set to quanta set on dut port
                              14. Check quanta value is 0 for last pfc packet sent from dut_port to spirent
                                  """ % self.priority_key)

    def setup(self):
        super(TestCase14, self).setup()

    def cleanup(self):
        super(TestCase14, self).cleanup()

    def run(self):
        super(TestCase14, self).run()


class TestCase15(TestCase1):
    current_priority_value = 15
    priority_key = 'priority_%s' % current_priority_value

    def pcap_output(self):
        pass

    def describe(self):
        self.set_test_details(id=15,
                              summary="Test DUT with pfc enabled for priority %s" % self.priority_key,
                              steps="""
                              1. Enable good streams for all priorities.
                              2. Now enable pfc stream with priority %s
                              3. Check rx counter on spirent for each good stream. Must be stopped only for 
                                 priority selected
                              4. Check fpg stats on pfc ingress port for correct counter getting marked
                              5. Check pg enqueue, dequeue in psw port stats for each queue. Enqueue must increase
                                 while dequeue must remain the same
                              6. Check q enqueue, dequeue in egress port for each queue. Enqueue must not happen and
                                 dequeue also must not happen
                              7. Start capture on dut port1
                              8. Check that rx has started for streams coming from port1 as pfc frames are stopped.
                              9. Check pg queue dequeue has started.
                              10. Check q dequeue has started
                              11. Check pg enqueue and pg dequeue continues to happen
                              12. Stop pfc traffic from port2 and stop capture on port1 after some time
                              13. Check quanta value of first packet in capture is set to quanta set on dut port
                              14. Check quanta value is 0 for last pfc packet sent from dut_port to spirent
                                  """ % self.priority_key)

    def setup(self):
        super(TestCase15, self).setup()

    def cleanup(self):
        super(TestCase15, self).cleanup()

    def run(self):
        super(TestCase15, self).run()


class TestCase16(FunTestCase):
    priority_enabled_list = [x for x in range(len(priority_dict)) if x % 2 == 1]

    def describe(self):
        self.set_test_details(id=16,
                              summary="Test DUT with pfc enabled for odd priority",
                              steps="""
                                1. Enable good streams for all priorities.
                                2. Now enable even priority pfc streams 
                                3. Check rx counter on spirent for each good stream. Must be stopped only for 
                                   priority selected
                                4. Check fpg stats on pfc ingress port for correct counter getting marked
                                5. Check pg enqueue, dequeue in psw port stats for each queue. Enqueue must increase
                                   while dequeue must remain the same for enabled priority
                                6. Check q enqueue, dequeue in egress port for each queue. Enqueue must happen and
                                   dequeue must not happen for pfc enabled streams
                                7. Now stop traffic of pfc streams
                                8. Check that rx has started for streams coming from port1 as pfc frames are now stopped.
                                9. Check pg queue dequeue has started.
                                10. Check q dequeue has started
                                11. Check pg enqueue and q enqueue continues to happen
                                """)

    def setup(self):
        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1, shape=shape)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2, shape=shape)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

    def cleanup(self):
        # Stop traffic from port 1
        stop = template_obj.disable_generator_configs(generator_configs=generator_dict[port_1])
        fun_test.test_assert(stop, "Stopping generator config on port %s" % port_1)

        # Stop traffic from port 2
        stop = template_obj.disable_generator_configs(generator_configs=generator_dict[port_2])
        fun_test.test_assert(stop, "Stopping generator config on port %s" % port_2)

        # Clear all subscribed results
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

        # Disable pfc enabled streams
        pfc_enabled_stream_objs = []
        for key, val in priority_dict.iteritems():
            if val['priority_val'] in self.priority_enabled_list:
                pfc_enabled_stream_objs.append(pfc_streamblock_objs[key]['streamblock_obj'])
        disable = template_obj.deactivate_stream_blocks(stream_obj_list=pfc_enabled_stream_objs)
        fun_test.simple_assert(disable, "Disable all pfc streams")

    def run(self):
        sleep_time = 5
        result_dict = {}
        spirent_rx_counters = 'spirent_rx_counters'
        spirent_pfc_rx_counter = 'spirent_pfc_rx_counter'
        fpg_cbfcpause_counters_tx = 'fpg_cbfcpause_counters_tx'
        fpg_cbfcpause_counters_rx = 'fpg_cbfcpause_counters_rx'
        psw_port_pg_counters = 'psw_port_pg_counters'
        psw_port_q_counters = 'psw_port_q_counters'
        dequeue = 'dequeue'
        enqueue = 'enqueue'

        pfc_enabled_stream_handle_list = []
        pfc_enabled_stream_objs = []
        for key, val in priority_dict.iteritems():
            if val['priority_val'] in self.priority_enabled_list:
                pfc_enabled_stream_objs.append(pfc_streamblock_objs[key]['streamblock_obj'])
                pfc_enabled_stream_handle_list.append(pfc_streamblock_objs[key]['streamblock_obj']._spirent_handle)

        # Activate pfc streams
        enable_pfc_stream = template_obj.activate_stream_blocks(stream_obj_list=pfc_enabled_stream_objs)
        fun_test.simple_assert(enable_pfc_stream, "Enable stream %s" % pfc_enabled_stream_objs)

        # Activate all good streams
        start_good = template_obj.stc_manager.start_traffic_stream(stream_blocks_list=good_stream_list)
        fun_test.test_assert(start_good, "Start good stream traffic")

        fun_test.sleep("Letting traffic get executed", seconds=sleep_time)

        fun_test.log("Starting traffic for priority %s" % self.priority_enabled_list)
        start_pfc = template_obj.stc_manager.start_traffic_stream(
            stream_blocks_list=pfc_enabled_stream_handle_list)
        fun_test.test_assert(start_pfc, " PFC started for priority %s" % self.priority_enabled_list)

        fun_test.sleep("Letting pfc stream get started", seconds=30)

        # Start capturing stats
        fun_test.log("Fetch spirent rx counter results")
        result_dict[spirent_rx_counters] = \
            find_spirent_rx_counters_stopped(streamblock_handle_list=good_stream_list, template_obj=template_obj,
                                             subscribe_result=subscribe_results)

        result_dict[spirent_pfc_rx_counter] = \
            find_spirent_rx_counters_stopped(port_handle=port_1,
                                             template_obj=template_obj,
                                             subscribe_result=subscribe_results, pfc_stream=True)

        fun_test.log("Fetch fpg stats on dut port %s" % dut_port_2)
        result_dict[fpg_cbfcpause_counters_tx] = \
            get_fpg_port_cbfcpause_counters(network_controller_obj=network_controller_obj, dut_port=dut_port_2, shape=shape)

        fun_test.log("Fetch fpg stats on dut port %s" % dut_port_1)
        result_dict[fpg_cbfcpause_counters_rx] = \
            get_fpg_port_cbfcpause_counters(network_controller_obj=network_controller_obj, dut_port=dut_port_1, tx=True, shape=shape)

        fun_test.log("Get psw port pg group enqueue dequeue counters")
        result_dict[psw_port_pg_counters] = \
            get_psw_port_enqueue_dequeue_counters(network_controller_obj=network_controller_obj,
                                                  dut_port=dut_port_1, pg=True, hnu=hnu)

        fun_test.log("Get psw port q enqueue dequeue counters")
        result_dict[psw_port_q_counters] = \
            get_psw_port_enqueue_dequeue_counters(network_controller_obj=network_controller_obj,
                                                  dut_port=dut_port_2, hnu=hnu)

        # ASSERTS
        spirent_counters_dict = result_dict[spirent_rx_counters]
        fpg_counters_dict_2 = result_dict[fpg_cbfcpause_counters_tx]
        fpg_counters_dict_1 = result_dict[fpg_cbfcpause_counters_rx]
        pg_queue_counters_dict = result_dict[psw_port_pg_counters]
        q_queue_counters_dict = result_dict[psw_port_q_counters]

        for key, val in priority_dict.iteritems():
            current_good_stream_handle = good_streamblock_objs[key]['streamblock_obj']._spirent_handle
            current_pfc_stream_handle = pfc_streamblock_objs[key]['streamblock_obj']._spirent_handle
            current_priority_value = val['priority_val']

            if current_priority_value in self.priority_enabled_list:
                fun_test.test_assert(spirent_counters_dict[current_good_stream_handle],
                                     message="Ensure rx counters are stopped for stream %s as pfc with priority "
                                             "%s is enabled" % (current_good_stream_handle, current_priority_value))

                fun_test.test_assert(fpg_counters_dict_2[current_priority_value],
                                     message="Ensure fpg mac stats seen for queue with priority %s when pfc "
                                             "stream for %s was received by dut port %s"
                                             % (current_priority_value, current_priority_value,
                                                dut_port_2))

                fun_test.test_assert(fpg_counters_dict_1[current_priority_value],
                                     message="Ensure fpg mac stats seen for queue with priority %s when pfc stream "
                                             "for %s was sent from dut port %s" % (
                                     current_priority_value, current_priority_value, dut_port_1))

                fun_test.test_assert(not pg_queue_counters_dict[current_priority_value][dequeue],
                                     message="Ensure pg_dequeue is not happening for queue q_%s when pfc with "
                                             "priority %s was sent" % (current_priority_value, current_priority_value))

                fun_test.test_assert(pg_queue_counters_dict[current_priority_value][enqueue],
                                     message="Ensure pg_enqueue is happening for queue q_%s when pfc with "
                                             "priority %s was sent" % (current_priority_value, current_priority_value))

                fun_test.test_assert(not q_queue_counters_dict[current_priority_value][dequeue],
                                     message="Ensure q_dequeue is not happening for queue q_%s when pfc with "
                                             "priority %s was sent" % (current_priority_value, current_priority_value))

                fun_test.test_assert(q_queue_counters_dict[current_priority_value][enqueue],
                                     message="Ensure q_enqueue is happening for queue q_%s when pfc with "
                                             "priority %s was sent" % (current_priority_value, current_priority_value))
            else:
                fun_test.test_assert(not spirent_counters_dict[current_good_stream_handle],
                                     message="Ensure rx counter is not stopped "
                                             "for stream %s when pfc is started for priority %s" %
                                             (current_good_stream_handle, current_priority_value))

                fun_test.test_assert(not fpg_counters_dict_2[current_priority_value],
                                     message="Ensure fpg mac stats not seen for "
                                             "queue %s when priority on dut port %s"
                                             % (current_priority_value,
                                                dut_port_2))

                fun_test.test_assert(not fpg_counters_dict_1[current_priority_value],
                                     message="Ensure fpg mac stats not seen for "
                                             "queue %s with priority on dut port %s"
                                             % (current_priority_value,
                                                dut_port_1))

                fun_test.test_assert(pg_queue_counters_dict[current_priority_value][dequeue],
                                     message="Ensure pg_dequeue is happening for queue q_%s when pfc with "
                                             "priority %s was sent" % (current_priority_value, current_priority_value))

                fun_test.test_assert(pg_queue_counters_dict[current_priority_value][enqueue],
                                     message="Ensure pg_enqueue is happening for queue q_%s when pfc with "
                                             "priority %s was sent" % (current_priority_value, current_priority_value))

                fun_test.test_assert(q_queue_counters_dict[current_priority_value][dequeue],
                                     message="Ensure q_dequeue is happening for queue q_%s when pfc with "
                                             "priority %s was sent" % (current_priority_value, current_priority_value))

                fun_test.test_assert(q_queue_counters_dict[current_priority_value][enqueue],
                                     message="Ensure q_enqueue is happening for queue q_%s when pfc with "
                                             "priority %s was sent" % (current_priority_value, current_priority_value))

            fun_test.test_assert(not result_dict[spirent_pfc_rx_counter][str(port_1)],
                                 message="Ensure spirent port %s is getting pfc frames from dut port %s"
                                         % (port_1, dut_port_1))

        # Stop traffic from port 1
        stop = template_obj.disable_generator_configs(generator_configs=generator_dict[port_2])
        fun_test.test_assert(stop, "Stopping pfc on port %s" % port_2)

        fun_test.sleep("Letting pfc get stopped", seconds=sleep_time)

        # Check if transmission has started for streams for whom pfc has been stopped
        output_dict = {}
        fun_test.log("Fetch spirent rx counter results")
        output_dict[spirent_rx_counters] = \
            find_spirent_rx_counters_stopped(streamblock_handle_list=good_stream_list, template_obj=template_obj,
                                             subscribe_result=subscribe_results)

        output_dict[spirent_pfc_rx_counter] = \
            find_spirent_rx_counters_stopped(port_handle=port_1,
                                             template_obj=template_obj,
                                             subscribe_result=subscribe_results, pfc_stream=True)

        fun_test.log("Fetch fpg stats on dut port %s" % dut_port_2)
        output_dict[fpg_cbfcpause_counters_tx] = \
            get_fpg_port_cbfcpause_counters(network_controller_obj=network_controller_obj, dut_port=dut_port_2, shape=shape)

        fun_test.log("Fetch fpg stats on dut port %s" % dut_port_1)
        output_dict[fpg_cbfcpause_counters_rx] = \
            get_fpg_port_cbfcpause_counters(network_controller_obj=network_controller_obj, dut_port=dut_port_1, tx=True, shape=shape)

        fun_test.log("Get psw port group enqueue dequeue counters")
        output_dict[psw_port_pg_counters] = \
            get_psw_port_enqueue_dequeue_counters(network_controller_obj=network_controller_obj,
                                                  dut_port=dut_port_1, pg=True, hnu=hnu)

        fun_test.log("Get psw port queue enqueue dequeue counters")
        output_dict[psw_port_q_counters] = \
            get_psw_port_enqueue_dequeue_counters(network_controller_obj=network_controller_obj,
                                                  dut_port=dut_port_2, hnu=hnu)

        spirent_counters_dict = output_dict[spirent_rx_counters]
        fpg_counters_dict_2 = output_dict[fpg_cbfcpause_counters_tx]
        fpg_counters_dict_1 = output_dict[fpg_cbfcpause_counters_rx]
        pg_queue_counters_dict = output_dict[psw_port_pg_counters]
        q_queue_counters_dict = output_dict[psw_port_q_counters]

        for key in spirent_counters_dict.iterkeys():
            fun_test.test_assert(not spirent_counters_dict[key], "Ensure rx on spirent is happening for stream %s "
                                                                 "when pfc is stopped" % key)

        fun_test.test_assert(output_dict[spirent_pfc_rx_counter][str(port_1)],
                             message="Ensure spirent port %s is not getting pfc frames from dut port %s" % (port_1,
                                                                                                            dut_port_1))

        for priority in priority_list:
            fun_test.test_assert(not fpg_counters_dict_2[priority], message="Ensure fpg mac stats not seen for "
                                                                            "queue with priority %s when pfc "
                                                                            "stream was stopped by dut port %s"
                                                                            % (priority,
                                                                               dut_port_2))

            fun_test.test_assert(not fpg_counters_dict_1[priority], message="Ensure fpg mac stats not seen for "
                                                                            "queue with priority %s when pfc "
                                                                            "stream was stopped from dut port %s"
                                                                            % (priority,
                                                                               dut_port_1))

            fun_test.test_assert(pg_queue_counters_dict[priority][dequeue],
                                 message="Ensure dequeue is happening for queue q_%s " % priority)

            fun_test.test_assert(pg_queue_counters_dict[priority][enqueue],
                                 message="Ensure enqueue is happening for queue q_%s " % priority)

            fun_test.test_assert(q_queue_counters_dict[priority][dequeue],
                                 message="Ensure dequeue is happening for queue q_%s " % priority)

            fun_test.test_assert(q_queue_counters_dict[priority][enqueue],
                                 message="Ensure enqueue is happening for queue q_%s " % priority)


class TestCase17(TestCase16):
    priority_enabled_list = [x for x in range(len(priority_dict)) if x % 2 == 0]

    def describe(self):
        self.set_test_details(id=17,
                              summary="Test DUT with pfc enabled for even priority",
                              steps="""
                                  1. Enable good streams for all priorities.
                                  2. Now enable pfc for even priorities only
                                  3. Check rx counter on spirent for each good stream. Must be stopped only for priority selected
                                  4. Check fpg stats on pfc ingress port for correct counter getting marked
                                  5. Check pg enqueue, dequeue in psw port stats for each queue in ingress port. 
                                     Enqueue must increase while deque must remain the same for enabled priority
                                  6. Check q enqueue, dequeue in psw port stats for each queue in ingress port. 
                                     Enqueue must increase while deque must remain the same for enabled priority
                                  7. Now stop traffic of pfc streams
                                  8. Check that rx has started for streams coming from port1 as pfc frames are now stopped.
                                  9. Check pg queue dequeue has started.
                                  10. Check q dequeue has started
                                  11. Check pg enqueue and q enqueue continues to happen
                                  """)

    def setup(self):
        super(TestCase17, self).setup()

    def cleanup(self):
        super(TestCase17, self).cleanup()

    def run(self):
        super(TestCase17, self).run()


class TestCase18(FunTestCase):
    current_pause_quanta = 0
    dut_pause_enable = True
    will_streams_stop = False

    def describe(self):
        self.set_test_details(id=18,
                              summary="Test link pause when quanta value is 0",
                              steps="""
                              1. Enable link pause on both ports
                              2. Set quanta to 0 in link pause frame on spirent
                              3. Start traffic from port 1
                              4. Start link pause frame from port 2
                              5. Ensure tx of stream is not stopped
                              6. Ensure no pause frames seen on port_1
                              """)

    def setup(self):
        for dut_port in dut_port_list:
            disable_pfc = network_controller_obj.disable_priority_flow_control(port_num=dut_port, shape=shape)
            fun_test.test_assert(disable_pfc, "Ensure pfc is disabled on %s" % dut_port)

            if self.dut_pause_enable:
                enable_tx_pause = network_controller_obj.enable_link_pause(port_num=dut_port, shape=shape)
                fun_test.test_assert(enable_tx_pause, "Enable link pause in %s" % dut_port)
            else:
                disable_tx_pause = network_controller_obj.disable_link_pause(port_num=dut_port, shape=shape)
                fun_test.test_assert(disable_tx_pause, "Disable link pause in %s" % dut_port)

            # Clear port results on DUT
            clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port, shape=shape)
            fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port)

            quanta = network_controller_obj.set_link_pause_quanta(port_num=dut_port, quanta=pause_dut_port_quanta)
            fun_test.test_assert(quanta, "Assign quanta value %s on port %s" % (pause_dut_port_quanta, dut_port))

            threshold = network_controller_obj.set_link_pause_threshold(port_num=dut_port, threshold=pause_dut_port_threshold)
            fun_test.test_assert(threshold, "Assign threshold value %s on port %s" % (pause_dut_port_threshold, dut_port))

        # Activate pfc streams
        enable_pfc_stream = template_obj.activate_stream_blocks(stream_obj_list=[pause_streamblock])
        fun_test.simple_assert(enable_pfc_stream, "Enable stream %s" % pause_streamblock._spirent_handle)

        pause_obj.pauseTime = self.current_pause_quanta
        modify_pause = template_obj.stc_manager.configure_frame_stack(stream_block_handle=pause_streamblock.spirent_handle,
                                                                      header_obj=pause_obj, update=True)
        fun_test.test_assert(modify_pause, "Change quanta value to %s" % self.current_pause_quanta)

    def cleanup(self):
        for dut_port in dut_port_list:
            disable_tx_pause = network_controller_obj.disable_link_pause(port_num=dut_port, shape=shape)
            fun_test.test_assert(disable_tx_pause, "Disable link pause in %s" % dut_port)

        all_stream_handles = good_stream_list + [pause_streamblock.spirent_handle]

        stop_streams = template_obj.stc_manager.stop_traffic_stream(
            stream_blocks_list=all_stream_handles)
        fun_test.test_assert(stop_streams, "Ensure all streams are stopped")

        disable_pfc_stream = template_obj.deactivate_stream_blocks(stream_obj_list=[pause_streamblock])
        fun_test.simple_assert(disable_pfc_stream, "Disable stream %s" % pause_streamblock._spirent_handle)

    def run(self):
        result_dict = {}
        spirent_rx_counters = 'spirent_rx_counters'
        psw_port_pg_counters = 'psw_port_pg_counters'
        psw_port_q_counters = 'psw_port_q_counters'
        dequeue = 'dequeue'
        enqueue = 'enqueue'
        pause_mac_ctrl_rx = "pause_mac_ctrl_rx"
        pause_mac_ctrl_tx = "pause_mac_ctrl_tx"
        # Start regular stream
        start_streams = template_obj.stc_manager.start_traffic_stream(
            stream_blocks_list=good_stream_list)
        fun_test.test_assert(start_streams, "Ensure good stream is started")

        fun_test.sleep("Letting traffic to be run")

        # Start pause stream
        start_streams = template_obj.stc_manager.start_traffic_stream(
            stream_blocks_list=pause_streamblock._spirent_handle)
        fun_test.test_assert(start_streams, "Ensure link pause stream is started")

        fun_test.sleep("Letting traffic to be run", seconds=10)

        fun_test.log("Fetch spirent rx counter results for all good streams")
        result_dict[spirent_rx_counters] = find_spirent_rx_counters_stopped(template_obj=template_obj,
                                                                            subscribe_result=subscribe_results,
                                                                            streamblock_handle_list=good_stream_list)

        fun_test.log("Get psw port group enqueue dequeue counters")
        result_dict[psw_port_pg_counters] = \
            get_psw_port_enqueue_dequeue_counters(network_controller_obj=network_controller_obj,
                                                  dut_port=dut_port_1, pg=True, hnu=hnu)

        fun_test.log("Get psw port queue enqueue dequeue counters")
        result_dict[psw_port_q_counters] = \
            get_psw_port_enqueue_dequeue_counters(network_controller_obj=network_controller_obj,
                                                  dut_port=dut_port_2, hnu=hnu)

        fun_test.log("Check pause mac control stat")
        result_dict[pause_mac_ctrl_rx] = \
            get_fpg_port_pause_mac_ctrl_counters(network_controller_obj=network_controller_obj, dut_port=dut_port_2,
                                                 tx=False, shape=shape)

        fun_test.log("Check pause mac control stat")
        result_dict[pause_mac_ctrl_tx] = \
            get_fpg_port_pause_mac_ctrl_counters(network_controller_obj=network_controller_obj, dut_port=dut_port_1,
                                                 tx=True, shape=shape)

        dut_2_stats_2 = network_controller_obj.peek_fpg_port_stats(port_num=dut_port_2, hnu=hnu)
        dut_2_tx_frames_1 = get_dut_output_stats_value(dut_2_stats_2, FRAMES_TRANSMITTED_OK, tx=True)

        dut_2_stats_2 = network_controller_obj.peek_fpg_port_stats(port_num=dut_port_2, hnu=hnu)
        dut_2_tx_frames_2 = get_dut_output_stats_value(dut_2_stats_2, FRAMES_TRANSMITTED_OK, tx=True)

        # Check pause streams on both ports. They must not be seen
        spirent_counters_dict = result_dict[spirent_rx_counters]
        pg_queue_counters_dict = result_dict[psw_port_pg_counters]
        q_queue_counters_dict = result_dict[psw_port_q_counters]

        if not self.dut_pause_enable:
            if int(dut_2_tx_frames_2) > int(dut_2_tx_frames_1):
                for key in spirent_counters_dict.keys():
                    spirent_counters_dict[key] = False

        for key, val in spirent_counters_dict.iteritems():
            if self.will_streams_stop:
                fun_test.test_assert(spirent_counters_dict[key], "Ensure rx on spirent is not happening for stream %s "
                                                                     "when pause with quanta %s is sent" % (key, self.current_pause_quanta))
            else:
                fun_test.test_assert(not spirent_counters_dict[key], "Ensure rx on spirent is happening for stream %s "
                                                                     "when pause with quanta %s is sent" % (key, self.current_pause_quanta))

        for key, val in priority_dict.iteritems():
            if self.will_streams_stop:
                fun_test.test_assert(not pg_queue_counters_dict[val['priority_val']][dequeue],
                                     message="Ensure pg_dequeue is not happening for queue q_%s when pause with quanta %s "
                                             "is sent" % (val['priority_val'], self.current_pause_quanta))

                fun_test.test_assert(not q_queue_counters_dict[val['priority_val']][dequeue],
                                     message="Ensure q_dequeue is not happening for queue q_%s when pause with quanta %s "
                                             "is sent" % (val['priority_val'], self.current_pause_quanta))
            else:

                fun_test.test_assert(pg_queue_counters_dict[val['priority_val']][dequeue],
                                     message="Ensure pg_dequeue is happening for queue q_%s when pause  with quanta %s "
                                             "is sent" % (val['priority_val'], self.current_pause_quanta))

                fun_test.test_assert(q_queue_counters_dict[val['priority_val']][dequeue],
                                     message="Ensure q_dequeue is happening for queue q_%s when pause  with quanta %s "
                                             "is sent" % (val['priority_val'], self.current_pause_quanta))

            fun_test.test_assert(pg_queue_counters_dict[val['priority_val']][enqueue],
                                 message="Ensure pg_enqueue is happening for queue q_%s when pause with quanta %s "
                                         "is sent" % (val['priority_val'], self.current_pause_quanta))

            fun_test.test_assert(q_queue_counters_dict[val['priority_val']][enqueue],
                                 message="Ensure q_enqueue is happening for queue q_%s when pause with quanta %s "
                                         "is sent" % (val['priority_val'], self.current_pause_quanta))

        if self.will_streams_stop:
            fun_test.test_assert(result_dict[pause_mac_ctrl_tx], "Check pause mac cntrl tx seen on %s" % dut_port_1)
        else:
            fun_test.test_assert(not result_dict[pause_mac_ctrl_tx], "Check pause mac cntrl tx not seen on %s" % dut_port_1)
        fun_test.test_assert(result_dict[pause_mac_ctrl_rx], "Check pause mac cntrl rx seen on %s" % dut_port_2)


class TestCase19(TestCase18):
    current_pause_quanta = 65535
    dut_pause_enable = False

    def describe(self):
        self.set_test_details(id=19,
                              summary="Test link pause when quanta value is 65535 and link pause is disabled on DUT port",
                              steps="""
                              1. Enable link pause on both ports
                              2. Set quanta to 0 in link pause frame on spirent
                              3. Start traffic from port 1
                              4. Start link pause frame from port 2
                              5. Ensure tx of stream is not stopped as link pause is disabled on DUT
                              6. Ensure no pause frames seen on port_1
                              """)

    def setup(self):
        super(TestCase19, self).setup()

        # Disable flow control on both spirent ports
        for current_interface_obj in interface_obj_list:
            current_interface_obj.FlowControl = False

            update_result = template_obj.configure_physical_interface(interface_obj=current_interface_obj)
            fun_test.simple_assert(update_result, "Disable flow control on interface %s" %
                                   current_interface_obj._spirent_handle)

    def cleanup(self):
        super(TestCase19, self).cleanup()

        # Enable flow control on both spirent ports
        for current_interface_obj in interface_obj_list:
            current_interface_obj.FlowControl = True

            update_result = template_obj.configure_physical_interface(interface_obj=current_interface_obj)
            fun_test.simple_assert(update_result, "Enable flow control on interface %s" %
                                   current_interface_obj._spirent_handle)


class TestCase20(TestCase18):
    current_pause_quanta = 65535
    dut_pause_enable = True
    will_streams_stop = True

    def describe(self):
        self.set_test_details(id=20,
                              summary="Test link pause when quanta value is 65535 and link pause is enabled on DUT port",
                              steps="""
                              1. Enable link pause on both ports
                              2. Set quanta to 65535 in link pause frame on spirent
                              3. Start traffic from port 1
                              4. Start link pause frame from port 2
                              5. Ensure tx of stream is stopped as link pause is enabled on DUT
                              6. Ensure pause frames seen on port_1 and port 2
                              7. start capture on port 1 and then Stop pause frames from spirent
                              8. Ensure tx is started from dut port 2
                              9. Stop capture and check quanta value in captured packet. First packet to have quanta %s
                                 and last packet to have quanta 0 
                              """)

    def run(self):
        super(TestCase20, self).run()
        '''
        # start capture
        capture_obj = Capture()
        start_capture = template_obj.stc_manager.start_capture_command(capture_obj=capture_obj, port_handle=port_1)
        fun_test.test_assert(start_capture, "Starting capture on %s" % port_1)

        fun_test.sleep("Letting capture to start on %s" % port_1)

        stop_streams = template_obj.stc_manager.stop_traffic_stream(
            stream_blocks_list=[pause_streamblock._spirent_handle])
        fun_test.test_assert(stop_streams, "Ensure dscp streams are stopped")

        fun_test.sleep("Letting pause to stop")

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
        out = pcap_parser_1.verify_pause_header_fields(first_packet=True, time=self.current_pause_quanta)
        fun_test.test_assert(out, "Ensure first packet capture shows quanta value %s" % self.current_pause_quanta)

        out = pcap_parser_1.verify_pause_header_fields(last_packet=True, time=0)
        fun_test.test_assert(out, "Ensure last packet capture shows quanta value 0")
        '''

if __name__ == "__main__":
    local_settings = nu_config_obj.get_local_settings_parameters(flow_direction=True, ip_version=True)
    flow_direction = local_settings[nu_config_obj.FLOW_DIRECTION]
    ts = SpirentSetup()
    ts.add_test_case(TestCase1())
    ts.add_test_case(TestCase2())
    ts.add_test_case(TestCase3())
    ts.add_test_case(TestCase4())
    ts.add_test_case(TestCase5())
    ts.add_test_case(TestCase6())
    ts.add_test_case(TestCase7())
    ts.add_test_case(TestCase8())
    ts.add_test_case(TestCase9())
    ts.add_test_case(TestCase10())
    ts.add_test_case(TestCase11())
    ts.add_test_case(TestCase12())
    ts.add_test_case(TestCase13())
    ts.add_test_case(TestCase14())
    ts.add_test_case(TestCase15())
    ts.add_test_case(TestCase16())
    ts.add_test_case(TestCase17())
    ts.add_test_case(TestCase18())
    ts.add_test_case(TestCase19())
    ts.add_test_case(TestCase20())
    ts.run()