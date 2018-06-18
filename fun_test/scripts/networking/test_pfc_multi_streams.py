from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, GeneratorConfig, Ethernet2Header, Ipv4Header, Capture
from lib.utilities.pcap_parser import PcapParser
from lib.host.network_controller import NetworkController
from helper import *
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
capture_priority_limit = 7
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


def verify_spirent_stats(result_dict):
    for stream_key in result_dict.iterkeys():
        fun_test.test_assert_expected(expected=result_dict[stream_key]['tx_result']['FrameCount'],
                                      actual=result_dict[stream_key]['rx_result']['FrameCount'],
                                      message="Check results for %s" % stream_key)
    result = True
    return result


def get_key_to_change(class_dict, priority_val):
    result = None
    for key in class_dict.iterkeys():
        if 'time' in key:
            out = int(filter(str.isdigit, key))
            if out == priority_val:
                result = key
                break
    return result


def find_spirent_rx_counters_stopped(streamblock_handle_list, template_obj, subscribe_result):
    result_dict = {}
    value_dict = {}
    for i in range(2):
        value_dict[i] = template_obj.stc_manager.fetch_streamblock_results(subscribe_result=subscribe_result,
                                                                           streamblock_handle_list=streamblock_handle_list,
                                                                           rx_result=True)
    for stream in streamblock_handle_list:
        result_dict[stream] = None
        old_rx_counter = int(value_dict[0][stream]['rx_result']['FrameCount'])
        new_rx_counter = int(value_dict[1][stream]['rx_result']['FrameCount'])

        fun_test.log("Values of rx counter for stream %s are:- Old: %s ; New: %s" % (stream, old_rx_counter,
                                                                                     new_rx_counter))

        if old_rx_counter < new_rx_counter:
            result_dict[stream] = False
        elif old_rx_counter == new_rx_counter:
            result_dict[stream] = True
    return result_dict


def get_fpg_port_cbfcpause_counters(network_controller_obj, dut_port):
    output_dict = {}
    try:
        out = network_controller_obj.clear_port_stats(dut_port)
        fun_test.simple_assert(out, "Clear port stats on dut port %s" % dut_port)
        fun_test.sleep('Stats clear', seconds=2)
        stats = network_controller_obj.peek_fpg_port_stats(dut_port)
        fun_test.simple_assert(stats, "Fpg stats on port %s" % dut_port)

        for priority in priority_list:
            output_dict[priority] = False
            value = get_dut_output_stats_value(stats, stat_type=CBFC_PAUSE_FRAMES_RECEIVED,
                                               tx=False, class_value=priority)
            if value:
                fun_test.log("Value seen for priority %s is %s" % (priority, value))
                output_dict[priority] = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return output_dict


def get_psw_port_enqueue_dequeue_counters(network_controller_obj, dut_port, pg=False):
    output_dict = {}
    dequeue = 'dequeue'
    enqueue = 'enqueue'
    if pg:
        dequeue_type = 'pg_deq'
        enqueue_type = 'pg_enq'
    else:
        dequeue_type = 'q_deq'
        enqueue_type = 'q_enq'
    try:
        stats_1 = network_controller_obj.peek_psw_port_stats(port_num=dut_port)
        fun_test.simple_assert(stats_1, "Ensure psw command is executed on port %s" % dut_port)

        fun_test.sleep("Letting queries to be executed", seconds=5)

        stats_2 = network_controller_obj.peek_psw_port_stats(port_num=dut_port)
        fun_test.simple_assert(stats_2, "Ensure psw command is executed on port %s" % dut_port)

        for queue_num in priority_list:
            output_dict[queue_num] = {}
            output_dict[queue_num][dequeue] = True
            output_dict[queue_num][enqueue] = False
            if len(str(queue_num)) == 1:
                updated_queue = '0' + str(queue_num)
            else:
                updated_queue = str(queue_num)
            q_no = 'q_' + updated_queue

            old_dequeue_val = int(stats_1[q_no]['count'][dequeue_type]['pkts'])
            new_dequeue_val = int(stats_2[q_no]['count'][dequeue_type]['pkts'])
            old_enqueue_val = int(stats_1[q_no]['count'][enqueue_type]['pkts'])
            new_enqueue_val = int(stats_2[q_no]['count'][enqueue_type]['pkts'])

            fun_test.log("Values of dequeue seen for queue %s are:- Old: %s ; New: %s" % (q_no,
                                                                                           old_dequeue_val,
                                                                                           new_dequeue_val))
            fun_test.log("Values of enqueue seen for queue %s are:- Old: %s ; New: %s" % (q_no,
                                                                                          old_enqueue_val,
                                                                                          new_enqueue_val))

            if old_dequeue_val < new_dequeue_val:
                output_dict[queue_num][dequeue] = True
            elif old_dequeue_val == new_dequeue_val:
                output_dict[queue_num][dequeue] = False

            if old_enqueue_val < new_enqueue_val:
                output_dict[queue_num][enqueue] = True
            elif old_enqueue_val == new_enqueue_val:
                output_dict[queue_num][enqueue] = False

    except Exception as ex:
        fun_test.critical(str(ex))
    return output_dict


class SpirentSetup(FunTestScript):
    pg = 0
    min_thr = 100
    shr_thr = 100
    hdr_thr = 20
    xoff_enable = 1
    shared_xon_thr = 10
    quanta = 50000
    class_val = 0
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
            dut_port_1

        good_load = 100
        pfc_load = 10
        fun_test.log("Creating Template object")
        template_obj = SpirentEthernetTrafficTemplate(session_name="test_pfc_multi_stream")
        fun_test.test_assert(template_obj, "Create template object")

        destination_mac1 = template_obj.stc_manager.dut_config['destination_mac1']
        destination_ip1 = template_obj.stc_manager.dut_config['destination_ip1']
        dut_port_1 = template_obj.stc_manager.dut_config['port_nos'][0]
        dut_port_2 = template_obj.stc_manager.dut_config['port_nos'][1]

        # Create network controller object
        dpcsh_server_ip = template_obj.stc_manager.dpcsh_server_config['dpcsh_server_ip']
        dpcsh_server_port = int(template_obj.stc_manager.dpcsh_server_config['dpcsh_server_port'])
        network_controller_obj = NetworkController(dpc_server_ip=dpcsh_server_ip, dpc_server_port=dpcsh_server_port)

        set_qos_ingress = network_controller_obj.set_qos_ingress_priority_group(port_num=dut_port_1,
                                                                                priority_group_num=self.pg,
                                                                                min_threshold=self.min_thr,
                                                                                shared_threshold=self.shr_thr,
                                                                                headroom_threshold=self.hdr_thr,
                                                                                xoff_enable=self.xoff_enable,
                                                                                shared_xon_threshold=self.shared_xon_thr)
        fun_test.test_assert(set_qos_ingress, "Setting qos ingress priority group")

        pfc_enable = network_controller_obj.set_qos_pfc(enable=True)
        fun_test.test_assert(pfc_enable, "Ensure qos pfc is enabled")

        enable_1 = network_controller_obj.enable_priority_flow_control(dut_port_1)
        fun_test.test_assert(enable_1, "Disable pfc on port %s" % dut_port_1)

        port_quanta = network_controller_obj.set_priority_flow_control_quanta(port_num=dut_port_1, quanta=self.quanta,
                                                                              class_num=self.class_val)
        fun_test.test_assert(port_quanta, "Ensure quanta %s is set on port %s" % (self.quanta, dut_port_1))

        port_thr = network_controller_obj.set_priority_flow_control_threshold(port_num=dut_port_1,
                                                                              threshold=self.threshold,
                                                                              class_num=self.class_val)
        fun_test.test_assert(port_thr, "Ensure threshold %s is set on port %s" % (port_thr, dut_port_1))

        # enable pfc on dut egress
        enable_2 = network_controller_obj.enable_priority_flow_control(dut_port_2)
        fun_test.test_assert(enable_2, "Enable pfc on port %s" % dut_port_2)

        result = template_obj.setup(no_of_ports_needed=num_ports)
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
                        stream_block_handle=create_streamblock_1._spirent_handle, header_obj=ethernet)
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
                    if val['priority_val'] == 0:
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

        # TODO: Disable pfc on both ports on DUT
        disable_1 = network_controller_obj.disable_priority_flow_control(dut_port_1)
        fun_test.test_assert(disable_1, "Disable pfc on port %s" % dut_port_1)
        disable_2 = network_controller_obj.disable_priority_flow_control(dut_port_2)
        fun_test.test_assert(disable_2, "Disable pfc on port %s" % dut_port_2)


class TestCase1(FunTestCase):
    current_priority_value = 0
    priority_key = 'priority_%s' % current_priority_value

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
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
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

    def run(self):
        final_quanta_value = 0
        sleep_time = 5
        result_dict = {}
        spirent_rx_counters = 'spirent_rx_counters'
        fpg_cbfcpause_counters = 'fpg_cbfcpause_counters'
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

        fun_test.sleep("Letting pfc stream get started", seconds=sleep_time)

        fun_test.log("Fetch spirent rx counter results")
        result_dict[self.current_priority_value][spirent_rx_counters] = \
            find_spirent_rx_counters_stopped(streamblock_handle_list=good_stream_list, template_obj=template_obj,
                                             subscribe_result=subscribe_results)

        fun_test.log("Fetch fpg stats")
        result_dict[self.current_priority_value][fpg_cbfcpause_counters] = \
            get_fpg_port_cbfcpause_counters(network_controller_obj=network_controller_obj, dut_port=dut_port_2)

        fun_test.log("Get psw port group enqueue dequeue counters")
        result_dict[self.current_priority_value][psw_port_pg_counters] = \
            get_psw_port_enqueue_dequeue_counters(network_controller_obj=network_controller_obj,
                                                  dut_port=dut_port_1, pg=True)

        fun_test.log("Get psw port queue enqueue dequeue counters")
        result_dict[self.current_priority_value][psw_port_q_counters] = \
            get_psw_port_enqueue_dequeue_counters(network_controller_obj=network_controller_obj,
                                                  dut_port=dut_port_2)

        # ASSERTS
        spirent_counters_dict = result_dict[self.current_priority_value][spirent_rx_counters]
        fpg_counters_dict = result_dict[self.current_priority_value][fpg_cbfcpause_counters]
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

        for priority in priority_list:
            if self.current_priority_value == priority:
                fun_test.test_assert(fpg_counters_dict[priority], message="Ensure fpg mac stats seen for "
                                                                          "queue with priority %s when pfc "
                                                                          "stream for %s was sent"
                                                                          % (priority, self.current_priority_value))

                fun_test.test_assert(not pg_queue_counters_dict[priority][dequeue],
                                     message="Ensure dequeue is not happening for queue q_%s when pfc with "
                                             "priority %s was sent" % (priority, self.current_priority_value))

                fun_test.test_assert(pg_queue_counters_dict[priority][enqueue],
                                     message="Ensure enqueue is happening for queue q_%s when pfc with "
                                             "priority %s was sent" % (priority, self.current_priority_value))

                fun_test.test_assert(not q_queue_counters_dict[priority][dequeue],
                                     message="Ensure dequeue is not not happening for queue q_%s when pfc with "
                                             "priority %s was sent" % (priority, self.current_priority_value))

                fun_test.test_assert(q_queue_counters_dict[priority][enqueue],
                                     message="Ensure enqueue is happening for queue q_%s when pfc with "
                                             "priority %s was sent" % (priority, self.current_priority_value))

            else:
                fun_test.test_assert(not fpg_counters_dict[priority], message="Ensure counter values of queue %s "
                                                                              "were not seen when pfc with priority"
                                                                              " %s was sent")

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
            fun_test.test_assert(start_capture, "Started capture for quanta 0 on port %s" % port_1)

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

        fun_test.log("Fetch fpg stats")
        output_dict[self.current_priority_value][fpg_cbfcpause_counters] = \
            get_fpg_port_cbfcpause_counters(network_controller_obj=network_controller_obj, dut_port=dut_port_2)

        fun_test.log("Get psw port group enqueue dequeue counters")
        output_dict[self.current_priority_value][psw_port_pg_counters] = \
            get_psw_port_enqueue_dequeue_counters(network_controller_obj=network_controller_obj,
                                                  dut_port=dut_port_1, pg=True)

        fun_test.log("Get psw port queue enqueue dequeue counters")
        output_dict[self.current_priority_value][psw_port_q_counters] = \
            get_psw_port_enqueue_dequeue_counters(network_controller_obj=network_controller_obj,
                                                  dut_port=dut_port_2)

        spirent_counters_dict = output_dict[self.current_priority_value][spirent_rx_counters]
        fpg_counters_dict = output_dict[self.current_priority_value][fpg_cbfcpause_counters]
        pg_queue_counters_dict = output_dict[self.current_priority_value][psw_port_pg_counters]
        q_queue_counters_dict = output_dict[self.current_priority_value][psw_port_q_counters]

        for key in spirent_counters_dict.iterkeys():
            fun_test.test_assert(not spirent_counters_dict[key], "Ensure rx on spirent is happening for stream %s "
                                                                 "when pfc is stopped"
                                                                 " for priority %s" % (key, self.current_priority_value))

        for priority in priority_list:
            fun_test.test_assert(not fpg_counters_dict[priority], message="Ensure counter values of queue %s "
                                                                          "were not seen when pfc with priority"
                                                                          " %s was stopped")

            fun_test.test_assert(not pg_queue_counters_dict[priority][dequeue],
                                 message="Ensure dequeue is happening for queue q_%s when pfc with "
                                         "priority %s was stopped" % (priority, self.current_priority_value))

            fun_test.test_assert(pg_queue_counters_dict[priority][enqueue],
                                 message="Ensure enqueue is happening for queue q_%s when pfc with "
                                         "priority %s was stopped" % (priority, self.current_priority_value))

            fun_test.test_assert(not q_queue_counters_dict[priority][dequeue],
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

            pcap_parser_1 = PcapParser(self.pcap_file_path_1)
            output = pcap_parser_1.verify_pfc_header_fields(last_packet=True, time0=str(final_quanta_value))
            fun_test.test_assert(output, "Ensure value of quanta is 0 in the last pfc packet")

            first = pcap_parser_1.verify_pfc_header_fields(first_packet=True, time0=default_quanta)
            fun_test.test_assert(first, "Value of quanta %s seen in pfc first packet" % default_quanta)


class TestCase2(TestCase1):
    current_priority_value = 2
    priority_key = 'priority_%s' % current_priority_value

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
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut") % dut_port_1

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut") % dut_port_2

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
        for key, val in priority_dict.itervalues():
            if val['priority_val'] in self.priority_enabled_list:
                pfc_enabled_stream_objs.append(pfc_streamblock_objs[key]['streamblock_obj'])
        disable = template_obj.deactivate_stream_blocks(stream_obj_list=pfc_enabled_stream_objs)
        fun_test.simple_assert(disable, "Disable all pfc streams")

    def run(self):
        sleep_time = 5
        result_dict = {}
        spirent_rx_counters = 'spirent_rx_counters'
        fpg_cbfcpause_counters = 'fpg_cbfcpause_counters'
        psw_port_pg_counters = 'psw_port_pg_counters'
        psw_port_q_counters = 'psw_port_q_counters'
        dequeue = 'dequeue'
        enqueue = 'enqueue'

        pfc_enabled_stream_handle_list = []
        pfc_enabled_stream_objs = []
        for key, val in priority_dict.itervalues():
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

        fun_test.sleep("Letting pfc stream get started", seconds=sleep_time)

        # Start capturing stats
        fun_test.log("Fetch spirent rx counter results")
        result_dict[spirent_rx_counters] = \
            find_spirent_rx_counters_stopped(streamblock_handle_list=good_stream_list, template_obj=template_obj,
                                             subscribe_result=subscribe_results)

        fun_test.log("Fetch fpg stats")
        result_dict[fpg_cbfcpause_counters] = \
            get_fpg_port_cbfcpause_counters(network_controller_obj=network_controller_obj, dut_port=dut_port_2)

        fun_test.log("Get psw port group enqueue dequeue counters")
        result_dict[psw_port_pg_counters] = \
            get_psw_port_enqueue_dequeue_counters(network_controller_obj=network_controller_obj,
                                                  dut_port=dut_port_1, pg=True)

        fun_test.log("Get psw port queue enqueue dequeue counters")
        result_dict[psw_port_q_counters] = \
            get_psw_port_enqueue_dequeue_counters(network_controller_obj=network_controller_obj,
                                                  dut_port=dut_port_2)

        #ASSERTS
        spirent_counters_dict = result_dict[spirent_rx_counters]
        fpg_counters_dict = result_dict[fpg_cbfcpause_counters]
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

                fun_test.test_assert(fpg_counters_dict[current_priority_value], message="Ensure fpg mac stats seen for "
                                                                                        "queue with priority %s when pfc "
                                                                                        "stream for %s was sent"
                                                                                        % (current_priority_value,
                                                                                           current_pfc_stream_handle))
                fun_test.test_assert(not pg_queue_counters_dict[current_priority_value][dequeue],
                                     message="Ensure pg_dequeue is not happening for queue q_%s when pfc with "
                                             "priority %s was sent" % (current_priority_value, current_priority_value))

                fun_test.test_assert(pg_queue_counters_dict[current_priority_value][enqueue],
                                     message="Ensure pg_enqueue is happening for queue q_%s when pfc with "
                                             "priority %s was sent" % (current_priority_value, current_priority_value))

                fun_test.test_assert(not q_queue_counters_dict[current_priority_value][dequeue],
                                     message="Ensure q_dequeue is not happening for queue q_%s when pfc with "
                                             "priority %s was sent" % (current_priority_value, current_priority_value))

                fun_test.test_assert(not q_queue_counters_dict[current_priority_value][enqueue],
                                     message="Ensure q_enqueue is not happening for queue q_%s when pfc with "
                                             "priority %s was sent" % (current_priority_value, current_priority_value))
            else:
                fun_test.test_assert(not spirent_counters_dict[current_good_stream_handle],
                                     message="Ensure rx counter is not stopped "
                                             "for stream %s when pfc is started for priority %s" %
                                             (current_good_stream_handle, current_priority_value))

                fun_test.test_assert(not fpg_counters_dict[current_priority_value],
                                     message="Ensure queue counter in mac stats are not started as pfc was not started"
                                             "for %s stream" % current_pfc_stream_handle)

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

        fun_test.log("Fetch fpg stats")
        output_dict[fpg_cbfcpause_counters] = \
            get_fpg_port_cbfcpause_counters(network_controller_obj=network_controller_obj, dut_port=dut_port_2)

        fun_test.log("Get psw port group enqueue dequeue counters")
        output_dict[psw_port_pg_counters] = \
            get_psw_port_enqueue_dequeue_counters(network_controller_obj=network_controller_obj,
                                                  dut_port=dut_port_1, pg=True)

        fun_test.log("Get psw port queue enqueue dequeue counters")
        output_dict[psw_port_q_counters] = \
            get_psw_port_enqueue_dequeue_counters(network_controller_obj=network_controller_obj,
                                                  dut_port=dut_port_2)

        spirent_counters_dict = output_dict[spirent_rx_counters]
        fpg_counters_dict = output_dict[fpg_cbfcpause_counters]
        pg_queue_counters_dict = output_dict[psw_port_pg_counters]
        q_queue_counters_dict = output_dict[psw_port_q_counters]

        for key in spirent_counters_dict.iterkeys():
            fun_test.test_assert(not spirent_counters_dict[key], "Ensure rx on spirent is happening for stream %s "
                                                                 "when pfc is stopped" % key)

        for priority in priority_list:
            fun_test.test_assert(fpg_counters_dict[priority], message="Ensure counter values of queue %s "
                                                                          "were seen when pfc with priority"
                                                                          " %s was sent")

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


if __name__ == "__main__":
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
    ts.run()