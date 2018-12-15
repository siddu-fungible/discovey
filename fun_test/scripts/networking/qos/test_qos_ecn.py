from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, GeneratorConfig, Ethernet2Header, Ipv4Header
from lib.host.network_controller import NetworkController
from scripts.networking.nu_config_manager import nu_config_obj
from scripts.networking.helper import *
from qos_helper import *
import copy

num_ports = 3
source_ip_list = ['1.1.1.1', '2.2.2.2']
streamblock_obj_list = []
streamblock_handles_list = []
config = nu_config_obj.read_dut_config()
qos_json_file = fun_test.get_script_parent_directory() + '/qos.json'
if config['type'] == 'f1':
    qos_json_file = fun_test.get_script_parent_directory() + '/qos_f1.json'
qos_json_output = fun_test.parse_file_to_json(qos_json_file)
queue_list = [x for x in range(16)]
reversed_list = copy.deepcopy(queue_list)
reversed_list.reverse()
DUT_ECN_COUNT = "dut_ecn_count"
SPIRENT_ECN_COUNT = "spirent_ecn_count"



class SpirentSetup(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
                1. Create Spirent template
                2. Connect chassis, labserver and license server
                3. Attach Ports
                4. Configure streams on port 1 and port 3 that will send traffic on port 2
                5. Subscribe to stream resulys
                6. Do traffic class to queue mapping on ingress and egress ports
                """)

    def setup(self):
        global template_obj, port_1, port_2, pfc_stream, network_controller_obj, dut_port_2, \
            dut_port_1, hnu, shape, port_obj_list, destination_ip1, destination_mac1, dut_port_list, mac_header, \
            pfc_frame, port_obj, dut_port_1, dut_port_2, dut_port_3, port_3, subscribe_results

        min_frame_length = 64
        max_frame_length = 1500

        dut_type = fun_test.get_local_setting(setting="dut_type")
        dut_config = nu_config_obj.read_dut_config(dut_type=dut_type, flow_direction=flow_direction)

        shape = 0
        hnu = False
        if flow_direction == nu_config_obj.FLOW_DIRECTION_HNU_HNU:
            shape = 1
            hnu = True

        chassis_type = fun_test.get_local_setting(setting="chassis_type")
        spirent_config = nu_config_obj.read_traffic_generator_config()

        fun_test.log("Creating Template object")
        template_obj = SpirentEthernetTrafficTemplate(session_name="test_qos_ecn",
                                                      spirent_config=spirent_config,
                                                      chassis_type=chassis_type)
        fun_test.test_assert(template_obj, "Create template object")

        destination_mac1 = spirent_config['l2_config']['destination_mac']
        destination_ip1 = spirent_config['l3_config']['ipv4']['destination_ip1']

        dut_port_list = []
        dut_port_1 = dut_config['ports'][0]
        dut_port_2 = dut_config['ports'][1]
        dut_port_3 = dut_config['ports'][2]
        dut_port_list.append(dut_port_1)
        dut_port_list.append(dut_port_2)
        dut_port_list.append(dut_port_3)
        fun_test.log("Using dut ports %s, %s, and %s" % (dut_port_1, dut_port_2, dut_port_3))

        # Create network controller object
        dpcsh_server_ip = dut_config['dpcsh_tcp_proxy_ip']
        dpcsh_server_port = int(dut_config['dpcsh_tcp_proxy_port'])
        network_controller_obj = NetworkController(dpc_server_ip=dpcsh_server_ip, dpc_server_port=dpcsh_server_port)
        
        fun_test.log("Enable qos pfc")
        qos_pfc = network_controller_obj.enable_qos_pfc(hnu=hnu)
        fun_test.simple_assert(qos_pfc, "Enabled qos pfc")

        fun_test.log("Enable pfc on dut port %s" % dut_port_2)
        dut_port_pfc = network_controller_obj.enable_priority_flow_control(port_num=dut_port_2, shape=shape)
        fun_test.simple_assert(dut_port_pfc, "Enable pfc on dut port %s" % dut_port_2)

        flow_dir = nu_config_obj.FLOW_DIRECTION_NU_NU
        if hnu:
            flow_dir = nu_config_obj.FLOW_DIRECTION_HNU_HNU
        result = template_obj.setup(no_of_ports_needed=num_ports, flow_direction=flow_dir)
        fun_test.test_assert(result['result'], "Configure setup")

        port_obj_list = result['port_list']
        port_1 = port_obj_list[0]
        port_2 = port_obj_list[1]
        port_3 = port_obj_list[2]

        for port_obj in port_obj_list[::2]:
            ip = source_ip_list[1]
            if port_obj == port_1:
                ip = source_ip_list[0]

            gen_config_obj = GeneratorConfig(scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED,
                                             duration_mode=GeneratorConfig.DURATION_MODE_CONTINOUS,
                                             advanced_interleaving=True)

            gen_obj_1 = template_obj.stc_manager.get_generator(port_handle=port_obj)
            config_obj = template_obj.configure_generator_config(port_handle=port_obj,
                                                                 generator_config_obj=gen_config_obj)
            fun_test.test_assert(config_obj, "Creating generator config on port %s" % port_obj)


            fun_test.log("Creating stream with starting pps as 40")
            normal_stream = StreamBlock(fill_type=StreamBlock.FILL_TYPE_PRBS,
                                        min_frame_length=min_frame_length, max_frame_length=max_frame_length,
                                        frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_RANDOM,
                                        load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND, load=40)
            streamblock_1 = template_obj.configure_stream_block(normal_stream, port_handle=port_obj)
            fun_test.test_assert(streamblock_1, "Ensure streamblock is created on port %s" % port_obj)

            # Configure mac and ip on the stream
            ethernet = Ethernet2Header(destination_mac=destination_mac1)
            frame_stack = template_obj.stc_manager.configure_frame_stack(
                stream_block_handle=normal_stream.spirent_handle, header_obj=ethernet,
                delete_header=[Ethernet2Header.HEADER_TYPE, Ipv4Header.HEADER_TYPE])
            fun_test.test_assert(frame_stack,
                                 "Added ethernet header to stream %s" % normal_stream._spirent_handle)

            ipv4 = Ipv4Header(source_address=ip, destination_address=destination_ip1)
            frame_stack = template_obj.stc_manager.configure_frame_stack(
                stream_block_handle=normal_stream._spirent_handle, header_obj=ipv4)
            fun_test.test_assert(frame_stack,
                                 "Added ipv4 header to stream %s" % normal_stream._spirent_handle)

            fun_test.test_assert(normal_stream, "Ensure normal stream is created on port %s" % port_obj)
            streamblock_obj_list.append(normal_stream)
            streamblock_handles_list.append(normal_stream.spirent_handle)

        # Create pfc stream
        gen_config_obj = GeneratorConfig(scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED,
                                         duration_mode=GeneratorConfig.DURATION_MODE_CONTINOUS,
                                         advanced_interleaving=True)

        gen_obj_1 = template_obj.stc_manager.get_generator(port_handle=port_2)
        config_obj = template_obj.configure_generator_config(port_handle=port_2,
                                                             generator_config_obj=gen_config_obj)
        fun_test.test_assert(config_obj, "Creating generator config on port %s" % port_2)

        fun_test.log("Create pfc stream for priority %s" % 0)

        pfc_stream = StreamBlock(load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND, load=323,
                                 fixed_frame_length=64, insert_signature=False)
        streamblock_4 = template_obj.configure_stream_block(pfc_stream, port_handle=port_2)
        fun_test.log("Created pfc stream on %s " % port_2)

        out = template_obj.configure_priority_flow_control_header(pfc_stream,
                                                                  class_enable_vector=True,
                                                                  time0=100,
                                                                  ls_octet='00000001')
        fun_test.test_assert(out['result'], message="Added frame stack")

        mac_header = out['ethernet8023_mac_control_header_obj']
        pfc_frame = out['pfc_header_obj']

        for dut_port in dut_port_list:
            if not dut_port == dut_port_2:
                # set ingress priority to pg map list
                set_ingress_priority_map = network_controller_obj.set_qos_priority_to_pg_map(port_num=dut_port,
                                                                                             map_list=reversed_list)
                fun_test.test_assert(set_ingress_priority_map, message="Set priority to pg map")
            else:
                # set egress priority to pg map list
                set_egress_priority_map = network_controller_obj.set_qos_queue_to_priority_map(port_num=dut_port,
                                                                                               map_list=reversed_list)
                fun_test.test_assert(set_egress_priority_map, "Set queue to priority map")

        for queue in [0, 8]:
            disable = network_controller_obj.set_qos_scheduler_config(port_num=dut_port_2, queue_num=queue,
                                                                      scheduler_type=network_controller_obj.SCHEDULER_TYPE_STRICT_PRIORITY,
                                                                      strict_priority_enable=False, extra_bandwidth=0)
            fun_test.test_assert(disable, "Disbale sp and eb on queue %s" % queue, ignore_on_success=True)

        # Subscribe to results
        project = template_obj.stc_manager.get_project_handle()
        subscribe_results = template_obj.subscribe_to_all_results(parent=project, diff_serv=True, port=port_2)
        fun_test.test_assert(subscribe_results['result'], "Subscribing to results")
        del subscribe_results['result']

    def cleanup(self):
        fun_test.test_assert(template_obj.cleanup(), "Cleaning up session")


class ECN_10(FunTestCase):
    test_type = QOS_PROFILE_ECN
    qos_profile_dict = qos_json_output[test_type]
    timer = qos_profile_dict['ecn_timer']
    min_thr = qos_profile_dict['ecn_min_thr']
    max_thr = qos_profile_dict['ecn_max_thr']
    pfc_pps = qos_profile_dict['pfc_pps']
    pfc_quanta = qos_profile_dict['pfc_quanta']
    prob_index = qos_profile_dict['ecn_prob_index']
    prof_num = qos_profile_dict['ecn_prof_num']
    ecn_applied_queue_num = 0
    non_ecn_applied_queue_num = 1
    stream_ecn_bits_list = [ECN_BITS_10, ECN_BITS_10]
    stream_pps = qos_profile_dict['stream_pps']
    test_queues_list = [ecn_applied_queue_num, non_ecn_applied_queue_num]
    enable_ecn = qos_profile_dict['ecn_enable']
    avg_period = qos_profile_dict['avg_period']
    cap_avg_sz = qos_profile_dict['cap_avg_sz']
    cap_avg_enable = qos_profile_dict['cap_avg_enable']
    pcap_file = None
    traffic_sleep = 20

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test ecn drop profile is applied on correct queue and other queue "
                                      "traffic is not affected. Set ecn bits to 10",
                              steps="""
                              1. Update stream from port 1 with dscp 0 and 1 having respectively and ecn bits set to 10.
                              2. Add ecn profile for queue 0 on egress dut port
                              3. Start traffic for both streams and pfc stream.
                              4. Verify from capture that all packets whose ecn bits are 11 have dscp bit 0 and not 1 
                              """)

    def modify_pfc_stream(self):
        pfc_frame.time0 = self.pfc_quanta

        fun_test.log("Modify pfc stream to correct pps")

        ls_octet = '00000001'
        output = template_obj.stc_manager.configure_pfc_header(class_enable_vector=True, update=True,
                                                               stream_block_handle=pfc_stream.spirent_handle,
                                                               header_obj=pfc_frame, ls_octet=ls_octet)
        fun_test.test_assert(output, message="Updated %s and %s for pfc stream %s" % (pfc_frame.time0,
                                                                                      ls_octet,
                                                                                      pfc_stream.spirent_handle))

        # Update load value
        pfc_stream.Load = self.pfc_pps
        update_stream = template_obj.configure_stream_block(stream_block_obj=pfc_stream, update=True)
        fun_test.test_assert(update_stream, "Ensure load value is updated to %s in stream %s" %
                            (self.pfc_pps, pfc_stream.spirent_handle))

    def setup(self):
        # Update streams to dscp and ecn bits
        for stream, queue_num, ecn_bits in zip(streamblock_obj_list, self.test_queues_list, self.stream_ecn_bits_list):
            fun_test.log("Updating stream %s with dscp %s having ecn 10 and load to %s" % (stream.spirent_handle,
                                                                                           queue_num, self.stream_pps))
            dscp_values = template_obj.get_diff_serv_dscp_value_from_decimal_value(
                decimal_value_list=[queue_num], dscp_high=True, dscp_low=True)
            dscp_high = dscp_values[queue_num]['dscp_high']
            dscp_low = dscp_values[queue_num]['dscp_low']

            dscp_set = template_obj.configure_diffserv(streamblock_obj=stream,
                                                       dscp_high=dscp_high,
                                                       dscp_low=dscp_low, reserved=ecn_bits, update=True)
            fun_test.test_assert(dscp_set, "Ensure dscp value of %s is updated on ip header for stream %s"
                                 % (queue_num, stream.spirent_handle))

            stream.Load = self.stream_pps
            streamblock_1 = template_obj.configure_stream_block(stream, update=True)
            fun_test.test_assert(streamblock_1, "Update stream %s with load as %s" % (stream.spirent_handle,
                                                                                      self.stream_pps))

        self.modify_pfc_stream()

        set_prob = set_default_qos_probability(network_controller_obj=network_controller_obj,
                                               profile_type=self.test_type)
        fun_test.test_assert(set_prob, "Ensure prob range is set")

        set_avg_q_cfg = network_controller_obj.set_qos_wred_avg_queue_config(avg_en=self.cap_avg_enable, avg_period=self.avg_period,
                                                                             cap_avg_sz=self.cap_avg_sz, q_avg_en=1)
        fun_test.test_assert(set_avg_q_cfg, "Ensure avg q config is set")
        wred_profile = network_controller_obj.set_qos_ecn_profile(prof_num=self.prof_num,
                                                                  min_threshold=self.min_thr,
                                                                  max_threshold=self.max_thr,
                                                                  ecn_prob_index=self.prob_index)

        set_queue_cfg = network_controller_obj.set_qos_wred_queue_config(port_num=dut_port_2,
                                                                         queue_num=self.ecn_applied_queue_num,
                                                                         enable_ecn=self.enable_ecn,
                                                                         ecn_profile_num=self.prof_num)

        fun_test.test_assert(wred_profile, "Ensure profile is set for %s" % self.test_type)
        fun_test.test_assert(set_queue_cfg, "Ensure queue config is set for %s" % self.test_type)

    def run(self):

        # Start capture packets
        '''
        take_capture = template_obj.start_default_capture_save_locally(port_2, sleep_time=self.capture_sleep)
        fun_test.test_assert(take_capture['result']," Take capture and save locally")

        self.pcap_file = take_capture['pcap_file_path']

        self.validate_packet_output()
        out = template_obj.stc_manager.get_port_diffserv_results(port_handle=port_2,
                                                                 subscribe_handle=subscribe_results['diff_serv_subscribe'])
        print out
        '''
        result_dict = {}
        ecn_count_before = DUT_ECN_COUNT + "_before"
        ecn_count_after = DUT_ECN_COUNT + "_after"
        for queue in self.test_queues_list:
            result_dict[str(queue)] = {}

            # Collect stats before starting traffic
            output_1 = network_controller_obj.get_qos_wred_ecn_stats(port_num=dut_port_2, queue_num=queue)
            fun_test.simple_assert(output_1, "Get wred ecn stats before starting traffic")
            result_dict[str(queue)][ecn_count_before] = int(output_1[ecn_count])
            fun_test.log("Ecn count value seen for queue %s before start is %s" % (queue, result_dict[str(queue)][ecn_count_before]))

        start_streams = template_obj.stc_manager.start_traffic_stream(
            stream_blocks_list=streamblock_handles_list + [pfc_stream.spirent_handle])
        fun_test.test_assert(start_streams, "Start running traffic")

        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_2, shape=shape)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_2)

        fun_test.log("Check if PFC frames are being rx at dut port %s" % dut_port_2)
        dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2, hnu=hnu)
        fun_test.simple_assert(dut_port_2_results, "Ensure dut stats are captured")

        dut_port_2_pause_receive = get_dut_output_stats_value(dut_port_2_results, CBFC_PAUSE_FRAMES_RECEIVED,
                                                              tx=False, class_value=self.ecn_applied_queue_num)
        fun_test.simple_assert(dut_port_2_pause_receive, "PFC frames received on port %s")
        fun_test.log("PFC frames are being rx on port %s" % dut_port_2)

        fun_test.sleep("Executing traffic", seconds=self.traffic_sleep)

        fun_test.log("Capturing L1 rate for each individual stream")
        output = template_obj.stc_manager.fetch_streamblock_results(subscribe_result=subscribe_results,
                                                                    streamblock_handle_list=streamblock_handles_list,
                                                                    rx_summary_result=True, tx_stream_result=True)

        stop_streams = template_obj.stc_manager.stop_traffic_stream(
            stream_blocks_list=streamblock_handles_list + [pfc_stream.spirent_handle])
        fun_test.test_assert(stop_streams, "Stop running traffic")

        fun_test.sleep("Letting traffic to be stopped",seconds=2)

        out = template_obj.stc_manager.get_port_diffserv_results(port_handle=port_2,
                                                                 subscribe_handle=subscribe_results[
                                                                     'diff_serv_subscribe'])

        for queue in self.test_queues_list:
            output_1 = network_controller_obj.get_qos_wred_ecn_stats(port_num=dut_port_2, queue_num=queue)
            fun_test.simple_assert(output_1, "Get wred ecn stats  after starting traffic")
            result_dict[str(queue)][ecn_count_after] = int(output_1[ecn_count])
            fun_test.log("Ecn count value seen for queue %s after stop is %s" % (
            queue, result_dict[str(queue)][ecn_count_after]))

            result_dict[str(queue)][DUT_ECN_COUNT] = result_dict[str(queue)][ecn_count_after] - result_dict[str(queue)][ecn_count_before]
            result_dict[str(queue)][SPIRENT_ECN_COUNT] = 0

            ecn_qos_val = template_obj.get_diff_serv_dscp_value_from_decimal_value(decimal_value_list=[queue], dscp_value=True)
            qos_binary_value = get_ecn_qos_binary(qos_binary=ecn_qos_val[queue]['dscp_value'])
            for key in out.keys():
                if key == str(qos_binary_value):
                    result_dict[str(queue)][SPIRENT_ECN_COUNT] = int(out[key]['Ipv4FrameCount'])

        for queue in self.test_queues_list:
            if queue == self.ecn_applied_queue_num:
                fun_test.test_assert(result_dict[str(queue)][DUT_ECN_COUNT] > 0,
                                     "Ensure frames are marked with ecn bits 11 for queue %s from dut" % queue)
                fun_test.test_assert_expected(expected=result_dict[str(queue)][SPIRENT_ECN_COUNT],
                                              actual=result_dict[str(queue)][DUT_ECN_COUNT],
                                              message="Ensure ecn count in wred stats and frames received on spirent match")
            else:
                fun_test.test_assert_expected(actual=result_dict[str(queue)][DUT_ECN_COUNT], expected=0,
                                              message="Ensure queue %s does not have any frames marked ecn 11" % queue)

                fun_test.test_assert_expected(expected=result_dict[str(queue)][SPIRENT_ECN_COUNT],
                                              actual=result_dict[str(queue)][DUT_ECN_COUNT],
                                              message="Ensure ecn count in wred stats and frames received on spirent match")

        # Check L1Rate for other stream
        for stream, queue in zip(streamblock_obj_list[1:], [self.non_ecn_applied_queue_num]):
            tx_result = convert_bps_to_mbps(int(output[stream.spirent_handle]['tx_stream_result']['L1BitRate']))
            rx_result = convert_bps_to_mbps(int(output[stream.spirent_handle]['rx_summary_result']['L1BitRate']))
            fun_test.test_assert(rx_result - tx_result <= 0.2,
                                 message="Ensure no packet drop seen for queue %s when ecn profile is "
                                         "applied on %s" % (queue, self.non_ecn_applied_queue_num))

    def cleanup(self):
        # Clear all subscribed results
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

        set_queue_cfg = network_controller_obj.set_qos_wred_queue_config(port_num=dut_port_2,
                                                                         queue_num=self.ecn_applied_queue_num,
                                                                         enable_ecn=0,
                                                                         ecn_profile_num=self.prof_num)
        fun_test.simple_assert(set_queue_cfg, "Disable ecn on queue %s" % self.ecn_applied_queue_num)

class ECN_01(ECN_10):
    ecn_applied_queue_num = 0
    non_ecn_applied_queue_num = 1
    stream_ecn_bits_list = [ECN_BITS_01, ECN_BITS_01]
    test_queues_list = [ecn_applied_queue_num, non_ecn_applied_queue_num]
    pcap_file = None


    def describe(self):
        self.set_test_details(id=2,
                              summary="Test ecn drop profile is applied on correct queue and other queue "
                                      "traffic is not affected. Set ecn bits to 01",
                              steps="""
                              1. Update stream from port 1 with dscp 0 and 1 having respectively and ecn bits set to 01.
                              2. Add ecn profile for queue 0 on egress dut port
                              3. Start traffic for both streams and pfc stream.
                              4. Verify from dut stats that all packets are marked ecn for only queue 0
                              """)


class ECN_10_00(FunTestCase):
    port_1_stream_dscp = 0
    port_3_stream_dscp = 16
    stream_ecn_bits_list = [ECN_BITS_10, ECN_BITS_00]
    stream_dscps = [port_1_stream_dscp, port_3_stream_dscp]
    pcap_file = None
    test_type = QOS_PROFILE_ECN
    qos_profile_dict = qos_json_output[test_type]
    timer = qos_profile_dict['ecn_timer']
    min_thr = qos_profile_dict['ecn_min_thr']
    max_thr = qos_profile_dict['ecn_max_thr']
    pfc_pps = qos_profile_dict['pfc_pps']
    pfc_quanta = qos_profile_dict['pfc_quanta']
    prob_index = qos_profile_dict['ecn_prob_index']
    prof_num = qos_profile_dict['ecn_prof_num']
    stream_pps = qos_profile_dict['stream_pps']
    enable_ecn = qos_profile_dict['ecn_enable']
    avg_period = qos_profile_dict['avg_period']
    cap_avg_sz = qos_profile_dict['cap_avg_sz']
    cap_avg_enable = qos_profile_dict['cap_avg_enable']
    capture_sleep = 20

    def describe(self):
        self.set_test_details(id=3,
                              summary="Test packets having ecn bits 00 sent on a queue for which "
                                      "ecn profile is applied does not change to 11",
                              steps="""
                              1. Update stream from port 1 and port 3 with dscp 0 and 16 and src_ip 1.1.1.1 and 2.2.2.2 
                                 having respectively and ecn bits set to 10.
                              2. Add ecn profile for queue 0 on egress dut port
                              3. Start traffic for both streams and pfc stream.
                              4. Verify from capture that all packets whose ecn bits are 11 have dscp bit 4 and not 5
                              """)

    def modify_pfc_stream(self):
        pfc_frame.time0 = self.pfc_quanta

        fun_test.log("Modify pfc stream to correct pps")

        ls_octet = '00000001'
        output = template_obj.stc_manager.configure_pfc_header(class_enable_vector=True, update=True,
                                                               stream_block_handle=pfc_stream.spirent_handle,
                                                               header_obj=pfc_frame, ls_octet=ls_octet)
        fun_test.test_assert(output, message="Updated %s and %s for pfc stream %s" % (pfc_frame.time0,
                                                                                      ls_octet,
                                                                                      pfc_stream.spirent_handle))

        # Update load value
        pfc_stream.Load = self.pfc_pps
        update_stream = template_obj.configure_stream_block(stream_block_obj=pfc_stream, update=True)
        fun_test.test_assert(update_stream, "Ensure load value is updated to %s in stream %s" %
                             (self.pfc_pps, pfc_stream.spirent_handle))

    def setup(self):
        # Update streams to dscp and ecn bits
        for stream, queue_num, ecn_bits in zip(streamblock_obj_list, self.stream_dscps, self.stream_ecn_bits_list):
            fun_test.log("Updating stream %s with dscp %s having ecn 10 and load to %s" % (stream.spirent_handle,
                                                                                           queue_num, self.stream_pps))
            dscp_values = template_obj.get_diff_serv_dscp_value_from_decimal_value(
                decimal_value_list=[queue_num], dscp_high=True, dscp_low=True)
            dscp_high = dscp_values[queue_num]['dscp_high']
            dscp_low = dscp_values[queue_num]['dscp_low']

            dscp_set = template_obj.configure_diffserv(streamblock_obj=stream,
                                                       dscp_high=dscp_high,
                                                       dscp_low=dscp_low, reserved=ecn_bits, update=True)
            fun_test.test_assert(dscp_set, "Ensure dscp value of %s is updated on ip header for stream %s"
                                 % (queue_num, stream.spirent_handle))

            stream.Load = self.stream_pps
            streamblock_1 = template_obj.configure_stream_block(stream, update=True)
            fun_test.test_assert(streamblock_1, "Update stream %s with load as %s" % (stream.spirent_handle,
                                                                                      self.stream_pps))

        self.modify_pfc_stream()
        set_prob = set_default_qos_probability(network_controller_obj=network_controller_obj,
                                               profile_type=self.test_type)
        fun_test.test_assert(set_prob, "Ensure prob range is set")

        set_avg_q_cfg = network_controller_obj.set_qos_wred_avg_queue_config(avg_en=self.cap_avg_enable,
                                                                             avg_period=self.avg_period,
                                                                             cap_avg_sz=self.cap_avg_sz, q_avg_en=1)
        fun_test.test_assert(set_avg_q_cfg, "Ensure avg q config is set")
        wred_profile = network_controller_obj.set_qos_ecn_profile(prof_num=self.prof_num,
                                                                  min_threshold=self.min_thr,
                                                                  max_threshold=self.max_thr,
                                                                  ecn_prob_index=self.prob_index)

        set_queue_cfg = network_controller_obj.set_qos_wred_queue_config(port_num=dut_port_2,
                                                                         queue_num=self.port_1_stream_dscp,
                                                                         enable_ecn=self.enable_ecn,
                                                                         ecn_profile_num=self.prof_num)

        fun_test.test_assert(wred_profile, "Ensure profile is set for %s" % self.test_type)
        fun_test.test_assert(set_queue_cfg, "Ensure queue config is set for %s" % self.test_type)

        start_streams = template_obj.stc_manager.start_traffic_stream(
            stream_blocks_list=streamblock_handles_list + [pfc_stream.spirent_handle])
        fun_test.test_assert(start_streams, "Start running traffic")

        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_2, shape=shape)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_2)

        fun_test.log("Check if PFC frames are being rx at dut port %s" % dut_port_2)
        dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2, hnu=hnu)
        fun_test.simple_assert(dut_port_2_results, "Ensure dut stats are captured")

        dut_port_2_pause_receive = get_dut_output_stats_value(dut_port_2_results, CBFC_PAUSE_FRAMES_RECEIVED,
                                                              tx=False, class_value=self.port_1_stream_dscp)
        fun_test.simple_assert(dut_port_2_pause_receive, "PFC frames received on port %s")
        fun_test.log("PFC frames are being rx on port %s" % dut_port_2)

        fun_test.sleep("Executing traffic", seconds=self.timer)

    def run(self):
        result = {}
        out = template_obj.stc_manager.get_port_diffserv_results(port_handle=port_2,
                                                                 subscribe_handle=subscribe_results[
                                                                     'diff_serv_subscribe'])

        for queue in self.stream_dscps:
            result[str(queue)] = False
            ecn_qos_val = template_obj.get_diff_serv_dscp_value_from_decimal_value(decimal_value_list=[queue],
                                                                                   dscp_value=True)
            qos_binary_value = get_ecn_qos_binary(qos_binary=ecn_qos_val[queue]['dscp_value'])
            for key in out.keys():
                if key == str(qos_binary_value):
                    if int(out[key]['Ipv4FrameCount']) > 0:
                        result[str(queue)] = True
        self.do_test_asserts(result)

    def do_test_asserts(self, result):
        fun_test.test_assert(result[str(self.stream_dscps[0])], "Ensure ECN bits is set to 11 for DSCP 0 as it had "
                                                   "ecn bits 01")

        fun_test.test_assert(not result[str(self.stream_dscps[1])], "Ensure ECN bits is not set to 11 for DSCP 16 as it had "
                                                   "ecn bits 00")

    def cleanup(self):
        stop_streams = template_obj.stc_manager.stop_traffic_stream(
            stream_blocks_list=streamblock_handles_list + [pfc_stream.spirent_handle])
        fun_test.test_assert(stop_streams, "Stop running traffic")

        # Clear all subscribed results
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

        set_queue_cfg = network_controller_obj.set_qos_wred_queue_config(port_num=dut_port_2,
                                                                         queue_num=self.port_1_stream_dscp,
                                                                         enable_ecn=0,
                                                                         ecn_profile_num=self.prof_num)
        fun_test.simple_assert(set_queue_cfg, "Disable ecn on queue %s" % self.port_1_stream_dscp)

class ECN_10_10(ECN_10_00):
    stream_ecn_bits_list = [ECN_BITS_10, ECN_BITS_10]

    def describe(self):
        self.set_test_details(id=4,
                              summary="Test packets having ecn bits 10 sent from different port having different ip "
                                      "on a queue for which ecn profile is applied has some packets from "
                                      "each port marked with ecn bits 11",
                              steps="""
                              1. Update stream from port 1 and port 3 with dscp 0 and 16 and src_ip 1.1.1.1 and 2.2.2.2 
                                 having respectively and ecn bits set to 10.
                              2. Add ecn profile for queue 0 on egress dut port
                              3. Start traffic for both streams and pfc stream.
                              4. Verify from capture that all packets whose ecn bits are 11 have source ip from both ports
                              """)

    def do_test_asserts(self, result):
        fun_test.test_assert(result[str(self.stream_dscps[0])], "Ensure ECN bits is set to 11 for DSCP 0 as it had "
                                                   "ecn bits 01")

        fun_test.test_assert(result[str(self.stream_dscps[1])], "Ensure ECN bits is set to 11 for DSCP 16 as it had "
                                                    "ecn bits 01")


if __name__ == "__main__":
    local_settings = nu_config_obj.get_local_settings_parameters(flow_direction=True, ip_version=True)
    flow_direction = local_settings[nu_config_obj.FLOW_DIRECTION]
    ts = SpirentSetup()
    ts.add_test_case(ECN_10())
    ts.add_test_case(ECN_01())
    ts.add_test_case(ECN_10_00())
    ts.add_test_case(ECN_10_10())
    ts.run()