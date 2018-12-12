from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, GeneratorConfig, Ethernet2Header, Ipv4Header
from lib.host.network_controller import NetworkController
from scripts.networking.nu_config_manager import nu_config_obj
from scripts.networking.helper import *
from qos_helper import *
from collections import OrderedDict
from lib.utilities.pcap_parser import PcapParser
import copy

num_ports = 2
total_normal_streams = 4
qos_json_file = fun_test.get_script_parent_directory() + '/qos.json'
qos_json_output = fun_test.parse_file_to_json(qos_json_file)
streamblock_objs_list = []
streamblock_handles_list = []
q_depth = 'avg_q_integ'
wred_q_drop = 'wred_q_drop'
queue_list = [x for x in range(16)]
reversed_list = copy.deepcopy(queue_list)


class SpirentSetup(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
                1. Create Spirent template
                2. Connect chassis, labserver and licenseserver
                3. Attach Ports
                4. Configure streams on port 1 and port 3 that will send traffic on port 2
                5. Subscribe to stream resulys
                6. Do traffic class to queue mapping on ingress and egress ports
                """)

    def setup(self):
        global template_obj, port_1, port_2, pfc_stream, network_controller_obj, dut_port_2, \
            dut_port_1, hnu, shape, port_obj_list, dut_port_list, mac_header, \
            pfc_frame, normal_stream, subscribe_results

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
        template_obj = SpirentEthernetTrafficTemplate(session_name="test_qos_wred_ecn",
                                                      spirent_config=spirent_config,
                                                      chassis_type=chassis_type)
        fun_test.test_assert(template_obj, "Create template object")

        destination_mac1 = spirent_config['l2_config']['destination_mac']
        destination_ip1 = spirent_config['l3_config']['ipv4']['destination_ip1']

        dut_port_list = []
        dut_port_1 = dut_config['ports'][0]
        dut_port_2 = dut_config['ports'][1]
        fun_test.log("Using dut ports %s, and %s" % (dut_port_1, dut_port_2))

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

        for port_obj in port_obj_list:
            gen_config_obj = GeneratorConfig(scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED,
                                             duration_mode=GeneratorConfig.DURATION_MODE_CONTINOUS,
                                             advanced_interleaving=True)

            gen_obj_1 = template_obj.stc_manager.get_generator(port_handle=port_obj)
            config_obj = template_obj.configure_generator_config(port_handle=port_obj,
                                                                 generator_config_obj=gen_config_obj)
            fun_test.test_assert(config_obj, "Creating generator config on port %s" % port_obj)

            if port_obj == port_1:
                for i in range(total_normal_streams):
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

                    ipv4 = Ipv4Header(destination_address=destination_ip1)
                    frame_stack = template_obj.stc_manager.configure_frame_stack(
                        stream_block_handle=normal_stream._spirent_handle, header_obj=ipv4)
                    fun_test.test_assert(frame_stack,
                                         "Added ipv4 header to stream %s" % normal_stream._spirent_handle)

                    fun_test.test_assert(normal_stream, "Ensure normal stream is created on port %s" % port_obj)
                    streamblock_objs_list.append(normal_stream)
                    streamblock_handles_list.append(normal_stream.spirent_handle)

            else:
                # Create pfc stream
                fun_test.log("Create pfc stream for priority %s" % 0)

                pfc_stream = StreamBlock(load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND, load=323,
                                         fixed_frame_length=64, insert_signature=False)
                streamblock_4 = template_obj.configure_stream_block(pfc_stream, port_handle=port_obj)
                fun_test.log("Created pfc stream on %s " % port_2)

                out = template_obj.configure_priority_flow_control_header(pfc_stream,
                                                                          class_enable_vector=True,
                                                                          time0=100,
                                                                          ls_octet='00000001')
                fun_test.test_assert(out['result'], message="Added frame stack")

                mac_header = out['ethernet8023_mac_control_header_obj']
                pfc_frame = out['pfc_header_obj']
                streamblock_handles_list.append(pfc_stream.spirent_handle)

        # Subscribe to results
        project = template_obj.stc_manager.get_project_handle()
        subscribe_results = template_obj.subscribe_to_all_results(parent=project)
        fun_test.test_assert(subscribe_results['result'], "Subscribing to results")
        del subscribe_results['result']

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

    def cleanup(self):
        fun_test.test_assert(template_obj.cleanup(), "Cleaning up session")


class Wred(FunTestCase):
    max_egress_load = qos_json_output['max_egress_load']
    qos_profile_dict = qos_json_output[QOS_PROFILE_WRED]
    normal_stream_pps_list = qos_profile_dict['stream_pps']
    timer = qos_profile_dict['wred_timer']
    min_thr = qos_profile_dict['wred_min_thr']
    max_thr = qos_profile_dict['wred_max_thr']
    wred_weight = qos_profile_dict['wred_weight']
    wred_enable = qos_profile_dict['wred_enable']
    pfc_pps = qos_profile_dict['pfc_pps']
    pfc_quanta = qos_profile_dict['pfc_quanta']
    prob_index = qos_profile_dict['wred_prob_index']
    prof_num = qos_profile_dict['wred_prof_num']
    non_wred_load_percent = qos_profile_dict['non_wred_load_percent']
    wred_queue_list = [0]
    non_wred_queue_list = [1, 2, 3]
    test_type = QOS_PROFILE_WRED
    enable_ecn = 0
    avg_period = qos_profile_dict['avg_period']
    cap_avg_sz = qos_profile_dict['cap_avg_sz']
    stats_list = [q_depth, wred_q_drop]

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test wred drop profiles on DUT",
                              steps="""
                              1. Update stream on port 1 to start with pps
                              2. Modify pfc stream from port 2 for appropriate priority
                              3. setup wred config
                              4. Start normal stream from port 1 and pfc from port 2
                              5. Note down 5 iterations of wred_ecn stats for q depth and wred drops and take average of it
                              6. Now iterate step 5 for different pps for normal stream.
                              7. Verify that as q depth increases, wred drop increases
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
        load_value = get_load_value_from_load_percent(load_percent=self.non_wred_load_percent,
                                                      max_egress_load=self.max_egress_load)
        fun_test.simple_assert(load_value, "Ensure load value is calculated")

        self.modify_pfc_stream()
        
        # Assgin dscp bits to stream
        wred_streamblock_list = []
        wred_streamblock_list.append(streamblock_objs_list[0])
        
        non_wred_streamblock_list = []
        non_wred_streamblock_list.extend(streamblock_objs_list[1:])

        for stream, queue_num in zip(wred_streamblock_list + non_wred_streamblock_list,
                                     self.wred_queue_list + self.non_wred_queue_list):

            dscp_values = template_obj.get_diff_serv_dscp_value_from_decimal_value(
                decimal_value_list=[queue_num], dscp_high=True, dscp_low=True)
            dscp_high = dscp_values[queue_num]['dscp_high']
            dscp_low = dscp_values[queue_num]['dscp_low']

            # Update dscp value
            dscp_set = template_obj.configure_diffserv(streamblock_obj=stream,
                                                       dscp_high=dscp_high,
                                                       dscp_low=dscp_low, update=True)
            fun_test.test_assert(dscp_set, "Ensure dscp value of %s is updated on ip header for stream %s"
                                 % (queue_num, stream.spirent_handle))

        set_prob = set_default_qos_probability(network_controller_obj=network_controller_obj,
                                               profile_type=self.test_type)
        fun_test.test_assert(set_prob, "Ensure prob range is set")

        set_avg_q_cfg = network_controller_obj.set_qos_wred_avg_queue_config(avg_en=1, avg_period=self.avg_period,
                                                                             cap_avg_sz=self.cap_avg_sz, q_avg_en=1)
        fun_test.test_assert(set_avg_q_cfg, "Ensure avg q config is set")

        if self.test_type == QOS_PROFILE_WRED:
            wred_profile = network_controller_obj.set_qos_wred_profile(prof_num=self.prof_num,
                                                                       min_threshold=self.min_thr,
                                                                       max_threshold=self.max_thr,
                                                                       wred_prob_index=self.prob_index)

            set_queue_cfg = network_controller_obj.set_qos_wred_queue_config(port_num=dut_port_2, queue_num=self.wred_queue_list[0],
                                                                             wred_enable=self.wred_enable,
                                                                             wred_weight=self.wred_weight,
                                                                             wred_prof_num=self.prof_num)
        else:
            wred_profile = network_controller_obj.set_qos_ecn_profile(prof_num=self.prof_num,
                                                                      min_threshold=self.min_thr,
                                                                      max_threshold=self.max_thr,
                                                                      ecn_prob_index=self.prob_index)

            set_queue_cfg = network_controller_obj.set_qos_wred_queue_config(port_num=dut_port_2,
                                                                             queue_num=self.wred_queue_list[0],
                                                                             enable_ecn=self.enable_ecn)
        fun_test.test_assert(wred_profile, "Ensure profile is set for %s" % self.test_type)
        fun_test.test_assert(set_queue_cfg, "Ensure queue config is set for %s" % self.test_type)

        start_streams = template_obj.stc_manager.start_traffic_stream(
            stream_blocks_list=streamblock_handles_list)
        fun_test.test_assert(start_streams, "Start running traffic")

        fun_test.sleep("Executing traffic")

        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_2, shape=shape)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_2)

        fun_test.log("Check if PFC frames are being rx at dut port %s" % dut_port_2)
        dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2, hnu=hnu)
        fun_test.simple_assert(dut_port_2_results, "Ensure dut stats are captured")

        dut_port_2_pause_receive = get_dut_output_stats_value(dut_port_2_results, CBFC_PAUSE_FRAMES_RECEIVED,
                                                              tx=False, class_value=self.wred_queue_list[0])
        fun_test.simple_assert(dut_port_2_pause_receive, "PFC frames received on port %s")
        fun_test.log("PFC frames are being rx on port %s" % dut_port_2)

    def cleanup(self):

        stop_streams = template_obj.stc_manager.stop_traffic_stream(
            stream_blocks_list=streamblock_handles_list)
        fun_test.test_assert(stop_streams, "Ensure dscp streams are stopped")

    def run(self):
        output_avg_dict = OrderedDict()
        for current_pps in self.normal_stream_pps_list:
            output_avg_dict[str(current_pps)] = {}

            # Update streamblock
            wred_streamblock = streamblock_objs_list[0]
            wred_streamblock.Load = current_pps
            update_stream = template_obj.configure_stream_block(stream_block_obj=wred_streamblock, update=True)
            fun_test.test_assert(update_stream, "Ensure load value is updated to %s in stream %s" %
                                 (current_pps, wred_streamblock.spirent_handle))

            fun_test.sleep("Letting load to be applied")

            fun_test.log("Taking 5 observations of q_depth and wred_drops for fps %s" % current_pps)
            # Take 5 observations of q_depth and wred_drops and do average
            observed_dict = capture_wred_ecn_stats_n_times(network_controller_obj=network_controller_obj, iterations=5,
                                                           stats_list=self.stats_list, port_num=dut_port_2,
                                                           queue_num=self.wred_queue_list[0])
            fun_test.simple_assert(observed_dict['result'], "Get 5 observations")
            fun_test.log("5 observations captured for pps %s" % current_pps)

            # Calculate average
            for stat in self.stats_list:
                avg_val = reduce(lambda a, b: a + b, observed_dict[stat]) / len(observed_dict[stat])
                fun_test.log("Average value seen for stat %s for pps %s is %s" % (stat, current_pps, avg_val))
                output_avg_dict[str(current_pps)][stat] = avg_val

        pps_key_list = output_avg_dict.keys()
        for i in range(0, len(pps_key_list)-1):
            for stat in self.stats_list:
                current_pps = self.normal_stream_pps_list[i]
                next_pps = self.normal_stream_pps_list[i+1]
                fun_test.test_assert(output_avg_dict[str(next_pps)][stat] >
                                     output_avg_dict[str(current_pps)][stat],
                                     "Ensure stat %s has value incremented for pps %s as compared to pps %s and it "
                                     "is %s and %s respectively" %
                                     (stat, next_pps, current_pps, output_avg_dict[str(next_pps)][stat],
                                      output_avg_dict[str(current_pps)][stat]))

        # Check if q depth and wred q drops are incrementing

        output = template_obj.stc_manager.fetch_streamblock_results(subscribe_result=subscribe_results,
                                                                    streamblock_handle_list=streamblock_handles_list,
                                                                    rx_summary_result=True, tx_stream_result=True)

        for stream, queue in zip(streamblock_objs_list[1:], self.non_wred_queue_list):
            tx_result = convert_bps_to_mbps(int(output[stream.spirent_handle]['tx_stream_result']['L1BitRate']))
            rx_result = convert_bps_to_mbps(int(output[stream.spirent_handle]['rx_summary_result']['L1BitRate']))
            fun_test.test_assert(rx_result - tx_result <= 0.2,
                                          message="Ensure no packet drop seen for queue %s when wred profile is "
                                                  "applied on %s" % (queue, self.wred_queue_list[0]))


if __name__ == "__main__":
    local_settings = nu_config_obj.get_local_settings_parameters(flow_direction=True, ip_version=True)
    flow_direction = local_settings[nu_config_obj.FLOW_DIRECTION]
    ts = SpirentSetup()
    ts.add_test_case(Wred())
    ts.run()