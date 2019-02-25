from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, GeneratorConfig, Ethernet2Header, Ipv4Header
from lib.host.network_controller import NetworkController
from scripts.networking.nu_config_manager import NuConfigManager
from scripts.networking.helper import *
from scripts.networking.qos.qos_helper import *
from collections import OrderedDict
import copy

num_ports = 3
streamblock_objs_list = []
streamblock_handles_list = []
queue_list = [x for x in range(16)]
reversed_list = copy.deepcopy(queue_list)
reversed_list.reverse()
percent_threshold = 5
DUT_ECN_COUNT = "dut_ecn_count"
SPIRENT_ECN_COUNT = "spirent_ecn_count"


def check_wred_ecn_counter_stopped(network_controller_obj, port_num, queue_num, type=QOS_PROFILE_WRED):
    result = False
    try:
        output_1 = network_controller_obj.get_qos_wred_ecn_stats(port_num=port_num, queue_num=queue_num)
        fun_test.simple_assert(output_1, "Get wred ecn counts")

        fun_test.sleep("Letting stats to be updated")

        output_2 = network_controller_obj.get_qos_wred_ecn_stats(port_num=port_num, queue_num=queue_num)
        fun_test.simple_assert(output_2, "Get wred ecn counts")

        if type == QOS_PROFILE_WRED:
            fun_test.log("Counter value of %s seen before was %s and after is %s" %
                         (QOS_PROFILE_WRED, output_1[wred_q_drop], output_2[wred_q_drop]))
            if output_1[wred_q_drop] == output_2[wred_q_drop]:
                result = True
        else:
            fun_test.log("Counter value of %s seen before was %s and after is %s" %
                         (QOS_PROFILE_ECN, output_1[ecn_count], output_2[ecn_count]))
            if output_1[ecn_count] == output_2[ecn_count]:
                result = True

    except Exception as ex:
        fun_test.critical(str(ex))
    return result



def get_percent_diff(rx_result, tx_result):
    result = None
    try:
        temp = (rx_result - tx_result) / float(tx_result)
        result = temp * 100
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


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
        global template_obj, port_1, port_2, port_3, pfc_stream, network_controller_obj, dut_port_2, \
            dut_port_1, hnu, shape, port_obj_list, dut_port_list, normal_stream, subscribe_results, flow_direction, \
            nu_config_obj, qos_json_output, max_egress_load

        nu_config_obj = NuConfigManager()

        qos_json_file = fun_test.get_script_parent_directory() + '/qos.json'
        if nu_config_obj.DUT_TYPE == nu_config_obj.DUT_TYPE_F1:
            qos_json_file = fun_test.get_script_parent_directory() + '/qos_f1.json'
        qos_json_output = fun_test.parse_file_to_json(qos_json_file)

        max_egress_load = nu_config_obj.SPEED
        if nu_config_obj.DUT_TYPE == nu_config_obj.DUT_TYPE_PALLADIUM:
            max_egress_load = qos_json_output['max_egress_load']

        flow_direction = nu_config_obj.FLOW_DIRECTION_NU_NU

        dut_config = nu_config_obj.read_dut_config(dut_type=nu_config_obj.DUT_TYPE, flow_direction=flow_direction)

        shape = 0
        hnu = False
        if flow_direction == nu_config_obj.FLOW_DIRECTION_HNU_HNU:
            shape = 1
            hnu = True

        spirent_config = nu_config_obj.read_traffic_generator_config()

        fun_test.log("Creating Template object")
        template_obj = SpirentEthernetTrafficTemplate(session_name="test_qos_wred_ecn",
                                                      spirent_config=spirent_config,
                                                      chassis_type=nu_config_obj.CHASSIS_TYPE)
        fun_test.test_assert(template_obj, "Create template object")

        routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
        fun_test.simple_assert(routes_config, "Ensure routes config fetched")
        l3_config = routes_config['l3_config']

        destination_mac1 = routes_config['routermac']
        destination_ip1 = l3_config['destination_ip1']
        if hnu:
            destination_ip1 = l3_config['hnu_destination_ip1']

        dut_port_list = []
        dut_port_1 = dut_config['ports'][0]
        dut_port_2 = dut_config['ports'][1]
        dut_port_3 = dut_config['ports'][2]
        dut_port_list.append(dut_port_1)
        dut_port_list.append(dut_port_2)
        dut_port_list.append(dut_port_3)
        fun_test.log("Using dut ports %s, %s and %s" % (dut_port_1, dut_port_2, dut_port_3))

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
            gen_config_obj = GeneratorConfig(scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED,
                                             duration_mode=GeneratorConfig.DURATION_MODE_CONTINOUS,
                                             advanced_interleaving=True)

            gen_obj_1 = template_obj.stc_manager.get_generator(port_handle=port_obj)
            config_obj = template_obj.configure_generator_config(port_handle=port_obj,
                                                                 generator_config_obj=gen_config_obj)
            fun_test.test_assert(config_obj, "Creating generator config on port %s" % port_obj)

            fun_test.log("Creating stream with starting pps as 40")
            normal_stream = StreamBlock(fill_type=StreamBlock.FILL_TYPE_PRBS,
                                        frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_FIXED,
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

        # Subscribe to results
        project = template_obj.stc_manager.get_project_handle()
        subscribe_results = template_obj.subscribe_to_all_results(parent=project, diff_serv=True, port=port_2)
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
                set_egress_priority_map = network_controller_obj.set_qos_queue_to_priority_map(
                    port_num=dut_port,
                    map_list=reversed_list)
                fun_test.test_assert(set_egress_priority_map, "Set queue to priority map")

    def cleanup(self):
        template_obj.cleanup()


class Wred_Q0(FunTestCase):
    test_type = None
    qos_profile_dict = None
    normal_stream_pps_list = None
    timer = None
    min_thr = None
    max_thr = None
    wred_weight = None
    wred_enable = None
    prob_index = None
    prof_num = None
    test_queue = 0
    avg_period = None
    cap_avg_sz = None
    stats_list = None
    max_queue_pps = 0
    port_1_stream_load = None
    port_3_stream_load_list = None
    packet_size = 0

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test wred drop increases as queue depth increases on DUT for Q0",
                              steps="""
                              1. Update stream on port 1 to start with pps
                              3. setup wred config
                              4. Start stream from port 1 and port 3
                              5. Note down 5 iterations of wred_ecn stats for q depth and wred drops and take average of it
                              6. Now iterate step 5 for different pps for normal stream.
                              7. Verify that as q depth increases, wred drop increases
                              """)

    def setup_variables(self):
        self.test_type = QOS_PROFILE_WRED
        self.qos_profile_dict = qos_json_output[self.test_type]
        self.normal_stream_pps_list = self.qos_profile_dict['stream_pps']
        self.timer = self.qos_profile_dict['wred_timer']
        self.min_thr = self.qos_profile_dict['wred_min_thr']
        self.max_thr = self.qos_profile_dict['wred_max_thr']
        self.wred_weight = self.qos_profile_dict['wred_weight']
        self.wred_enable = self.qos_profile_dict['wred_enable']
        self.prob_index = self.qos_profile_dict['wred_prob_index']
        self.prof_num = self.qos_profile_dict['wred_prof_num']
        self.test_queue = 0
        self.avg_period = self.qos_profile_dict['avg_period']
        self.cap_avg_sz = self.qos_profile_dict['cap_avg_sz']
        self.stats_list = [q_depth, wred_q_drop]
        self.max_queue_pps = 0
        self.port_1_stream_load = self.normal_stream_pps_list['ingress_port_1']
        self.port_3_stream_load_list = self.normal_stream_pps_list['ingress_port_2']
        self.packet_size = self.qos_profile_dict['packet_size']

    def setup(self):
        self.setup_variables()

        fun_test.log("Setting stream rate on stream coming from port %s to 80 percent of egress b/w" % port_1)
        self.max_queue_pps = get_load_pps_for_each_queue(max_egress_load, self.packet_size, 1)

        load_value = int(get_load_value_from_load_percent(load_percent=self.port_1_stream_load,
                                                          max_egress_load=self.max_queue_pps))
        fun_test.simple_assert(load_value, "Ensure load value is calculated")

        # Update streamblock
        if self.test_type == QOS_PROFILE_WRED:
            wred_streamblock = streamblock_objs_list[0]
            wred_streamblock.Load = load_value
            wred_streamblock.FixedFrameLength = self.packet_size
            update_stream = template_obj.configure_stream_block(stream_block_obj=wred_streamblock, update=True)
            fun_test.test_assert(update_stream, "Ensure load value is updated to %s in stream %s" %
                                 (load_value, wred_streamblock.spirent_handle))
        else:
            for ecn_streamblock in streamblock_objs_list:
                ecn_streamblock.Load = load_value
                ecn_streamblock.FixedFrameLength = self.packet_size
                update_stream = template_obj.configure_stream_block(stream_block_obj=ecn_streamblock, update=True)
                fun_test.test_assert(update_stream, "Ensure load value is updated to %s in stream %s" %
                                     (load_value, ecn_streamblock.spirent_handle))

                update_ecn = template_obj.configure_diffserv(streamblock_obj=ecn_streamblock, reserved=self.ecn_bits,
                                                             update=True)
                fun_test.test_assert(update_ecn, "Update ecn bits in stream %s" % ecn_streamblock.spirent_handle)

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

            set_queue_cfg = network_controller_obj.set_qos_wred_queue_config(port_num=dut_port_2,
                                                                             queue_num=self.test_queue,
                                                                             wred_enable=self.wred_enable,
                                                                             wred_weight=self.wred_weight,
                                                                             wred_prof_num=self.prof_num)
        else:
            wred_profile = network_controller_obj.set_qos_ecn_profile(prof_num=self.prof_num,
                                                                      min_threshold=self.min_thr,
                                                                      max_threshold=self.max_thr,
                                                                      ecn_prob_index=self.prob_index)

            set_queue_cfg = network_controller_obj.set_qos_wred_queue_config(port_num=dut_port_2,
                                                                             queue_num=self.test_queue,
                                                                             enable_ecn=1)
        fun_test.test_assert(wred_profile, "Ensure profile is set for %s" % self.test_type)
        fun_test.test_assert(set_queue_cfg, "Ensure queue config is set for %s" % self.test_type)

    def cleanup(self):
        if self.test_type == QOS_PROFILE_WRED:
            set_queue_cfg = network_controller_obj.set_qos_wred_queue_config(port_num=dut_port_2,
                                                                             queue_num=self.test_queue,
                                                                             wred_enable=0,
                                                                             wred_weight=self.wred_weight,
                                                                             wred_prof_num=self.prof_num)
        else:
            set_queue_cfg = network_controller_obj.set_qos_wred_queue_config(port_num=dut_port_2,
                                                                             queue_num=self.test_queue,
                                                                             enable_ecn=0)

        stop_streams = template_obj.stc_manager.stop_traffic_stream(
            stream_blocks_list=streamblock_handles_list)
        fun_test.add_checkpoint("Ensure dscp streams are stopped")

    def run(self):
        start_streams = template_obj.stc_manager.start_traffic_stream(
            stream_blocks_list=streamblock_handles_list)
        fun_test.test_assert(start_streams, "Start running traffic")

        fun_test.sleep("Executing traffic", seconds=self.timer)

        output_avg_dict = OrderedDict()
        for load_percent in self.port_3_stream_load_list:
            current_pps = int(get_load_value_from_load_percent(load_percent=load_percent,
                                                               max_egress_load=self.max_queue_pps))
            fun_test.simple_assert(current_pps, "Ensure load value is calculated")

            output_avg_dict[str(current_pps)] = {}

            # Update streamblock
            wred_streamblock = streamblock_objs_list[1]
            wred_streamblock.Load = current_pps
            update_stream = template_obj.configure_stream_block(stream_block_obj=wred_streamblock, update=True)
            fun_test.test_assert(update_stream, "Ensure load value is updated to %s in stream %s" %
                                 (current_pps, wred_streamblock.spirent_handle))

            fun_test.sleep("Letting load to be applied")

            fun_test.log("Taking 5 observations of q_depth and wred_drops for fps %s" % current_pps)
            # Take 5 observations of q_depth and wred_drops and do average
            observed_dict = capture_wred_ecn_stats_n_times(network_controller_obj=network_controller_obj, iterations=5,
                                                           stats_list=self.stats_list, port_num=dut_port_2,
                                                           queue_num=self.test_queue)
            fun_test.simple_assert(observed_dict['result'], "Get 5 observations")
            fun_test.log("5 observations captured for pps %s" % current_pps)

            # Calculate average
            for stat in self.stats_list:
                fun_test.log("Values seen for stats %s for load %s are %s" % (stat, load_percent, observed_dict[stat]))
                avg_val = reduce(lambda a, b: a + b, observed_dict[stat]) / len(observed_dict[stat])
                fun_test.log("Average value seen for stat %s for pps %s is %s" % (stat, current_pps, avg_val))
                output_avg_dict[str(current_pps)][stat] = avg_val

        pps_key_list = output_avg_dict.keys()
        for i in range(0, len(pps_key_list) - 1):
            for stat in self.stats_list:
                current_pps = pps_key_list[i]
                next_pps = pps_key_list[i + 1]
                fun_test.test_assert(output_avg_dict[str(next_pps)][stat] >
                                     output_avg_dict[str(current_pps)][stat],
                                     "Ensure stat %s has value incremented for pps %s as compared to pps %s and it "
                                     "is %s and %s respectively" %
                                     (stat, next_pps, current_pps, output_avg_dict[str(next_pps)][stat],
                                      output_avg_dict[str(current_pps)][stat]))

        stop_streams = template_obj.stc_manager.stop_traffic_stream(
            stream_blocks_list=[streamblock_handles_list[1]])
        fun_test.add_checkpoint("Ensure one stream is stopped")

        fun_test.sleep("Letting one stream traffic to be stopped")

        # Check wred counters have stopped incrementing
        check_stop = check_wred_ecn_counter_stopped(network_controller_obj=network_controller_obj, port_num=dut_port_2,
                                                           queue_num=self.test_queue)
        fun_test.test_assert(check_stop, "Ensure wred q drop counters are not seen when we do not exceed bandwidth")


class ECN_10(Wred_Q0):
    test_type = QOS_PROFILE_ECN
    ecn_bits = ECN_BITS_10
    qos_profile_dict = None
    normal_stream_pps_list = None
    timer = None
    min_thr = None
    max_thr = None
    wred_enable = None
    prob_index = None
    prof_num = None
    test_queue = 0
    avg_period = None
    cap_avg_sz = None
    port_1_stream_load = None
    port_3_stream_load_list = None
    sleep_interval = 5
    iterations = 3
    max_queue_pps = 0
    stats_list = [q_depth, ecn_count]
    packet_size = 0

    def describe(self):
        self.set_test_details(id=2,
                              summary="Test ecn count increases as queue depth increases on DUT for Q0 with ECN bits in packet set to 10",
                              steps="""
                                  1. Update stream on port 1 to start with pps
                                  3. setup ecn config
                                  4. Start stream from port 1 and port 3
                                  5. Note down 3 iterations of wred_ecn stats for q depth and ecn count and take average of it
                                  6. Now iterate step 5 for different pps for normal stream.
                                  7. Verify that as q depth increases, ecn count increases
                                  8. For every iteration check if ecn count on dut and spirent match
                                  """)

    def setup_variables(self):
        self.test_type = QOS_PROFILE_ECN
        self.ecn_bits = self.ecn_bits
        self.qos_profile_dict = qos_json_output[self.test_type]
        self.normal_stream_pps_list = self.qos_profile_dict['stream_pps']
        self.timer = self.qos_profile_dict['ecn_timer']
        self.min_thr = self.qos_profile_dict['ecn_min_thr']
        self.max_thr = self.qos_profile_dict['ecn_max_thr']
        self.wred_enable = self.qos_profile_dict['ecn_enable']
        self.prob_index = self.qos_profile_dict['ecn_prob_index']
        self.prof_num = self.qos_profile_dict['ecn_prof_num']
        self.test_queue = 0
        self.avg_period = self.qos_profile_dict['avg_period']
        self.cap_avg_sz = self.qos_profile_dict['cap_avg_sz']
        self.stats_list = self.stats_list
        self.max_queue_pps = self.max_queue_pps
        self.port_1_stream_load = self.normal_stream_pps_list['ingress_port_1']
        self.port_3_stream_load_list = self.normal_stream_pps_list['ingress_port_2']
        self.sleep_interval = 5
        self.iterations = 3
        self.packet_size = self.qos_profile_dict['packet_size']

    def setup(self):
        super(ECN_10, self).setup()

        # Set non fcp curr count
        egress = network_controller_obj.set_qos_egress_buffer_pool(df_thr=6000, dx_thr=6000, fcp_thr=8000,
                                                          nonfcp_thr=8000, nonfcp_xoff_thr=7000, sample_copy_thr=250,
                                                                   sf_thr=6000, sf_xoff_thr=5000, sx_thr=6000)
        fun_test.test_assert(egress, "Set egress buffer pool threshold values")

    def run(self):
        output_avg_dict = OrderedDict()
        for load_percent in self.port_3_stream_load_list:
            current_pps = int(get_load_value_from_load_percent(load_percent=load_percent,
                                                               max_egress_load=self.max_queue_pps))
            fun_test.simple_assert(current_pps, "Ensure load value is calculated")

            output_avg_dict[str(current_pps)] = {}
            output_avg_dict[str(current_pps)][SPIRENT_ECN_COUNT] = 0

            # Update streamblock
            wred_streamblock = streamblock_objs_list[1]
            wred_streamblock.Load = current_pps
            update_stream = template_obj.configure_stream_block(stream_block_obj=wred_streamblock, update=True)
            fun_test.test_assert(update_stream, "Ensure load value is updated to %s in stream %s" %
                                 (current_pps, wred_streamblock.spirent_handle))

            fun_test.sleep("Letting load to be applied")

            fun_test.log("Get initial ecn count")
            output_1 = network_controller_obj.get_qos_wred_ecn_stats(port_num=dut_port_2, queue_num=self.test_queue)
            fun_test.simple_assert(output_1, "Get wred ecn stats")
            ecn_count_before = int(output_1['ecn_count'])

            # Clear spirent stats
            for key in subscribe_results.iterkeys():
                template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

            fun_test.log("Get psw nu stats before capturing ecn counts")
            network_controller_obj.peek_psw_global_stats(hnu=hnu)

            start_streams = template_obj.stc_manager.start_traffic_stream(
                stream_blocks_list=streamblock_handles_list)
            fun_test.test_assert(start_streams, "Start running traffic")

            fun_test.sleep("Executing traffic", seconds=self.timer)

            fun_test.log("Taking %s observations of q_depth and wred_drops for fps %s" % (self.iterations, current_pps))
            # Take 5 observations of q_depth and wred_drops and do average
            observed_dict = capture_wred_ecn_stats_n_times(network_controller_obj=network_controller_obj, iterations=self.iterations,
                                                           stats_list=self.stats_list, port_num=dut_port_2,
                                                           queue_num=self.test_queue, sleep_interval=self.sleep_interval)
            fun_test.simple_assert(observed_dict['result'], "Get 5 observations")
            fun_test.log("5 observations captured for pps %s" % current_pps)

            # Check stats increase
            for stats in self.stats_list:
                fun_test.log("Check %s stats incrementing" % stats)

                out = observed_dict[stats]
                fun_test.log("Values seen for stat %s are %s" % (stats, out))
                for i in range(0, len(out) - 1):
                    current_value = out[i]
                    next_value = out[i + 1]
                    fun_test.test_assert(next_value > current_value, "Ensure %s stats incremented. "
                                                                     "Initial value %s. New value %s" %
                                         (stats, current_value, next_value))

            # Stop traffic
            stop_streams = template_obj.stc_manager.stop_traffic_stream(
                stream_blocks_list=streamblock_handles_list)
            fun_test.simple_assert(stop_streams, "Ensure dscp streams are stopped")

            fun_test.log("Get psw nu stats after capturing ecn counter stats")
            network_controller_obj.peek_psw_global_stats(hnu=hnu)

            fun_test.sleep("Letting traffic to get stopped")

            # Get dut ecn count and subtract with one taken before starting traffic
            fun_test.log("Get initial ecn count after traffic is stopped")
            output_1 = network_controller_obj.get_qos_wred_ecn_stats(port_num=dut_port_2, queue_num=self.test_queue)
            fun_test.simple_assert(output_1, "Get wred ecn stats once")
            ecn_count_after = int(output_1['ecn_count'])

            # Add dut ecn count to output_avg_dict
            dut_ecn_count = ecn_count_after - ecn_count_before
            output_avg_dict[str(current_pps)][DUT_ECN_COUNT] = dut_ecn_count

            # Get spirent count of ecn11
            out = template_obj.stc_manager.get_port_diffserv_results(port_handle=port_2,
                                                                     subscribe_handle=subscribe_results[
                                                                         'diff_serv_subscribe'])

            ecn_qos_val = template_obj.get_diff_serv_dscp_value_from_decimal_value(decimal_value_list=[self.test_queue],
                                                                                   dscp_value=True)
            qos_binary_value = get_ecn_qos_binary(qos_binary=ecn_qos_val[self.test_queue]['dscp_value'])
            for key in out.keys():
                if key == str(qos_binary_value):
                    output_avg_dict[str(current_pps)][SPIRENT_ECN_COUNT] = int(out[key]['Ipv4FrameCount'])
        '''
        pps_key_list = output_avg_dict.keys()
        for i in range(0, len(pps_key_list) - 1):
            for stat in self.stats_list:
                current_pps = pps_key_list[i]
                next_pps = pps_key_list[i + 1]
                fun_test.test_assert(output_avg_dict[str(next_pps)][stat] >
                                     output_avg_dict[str(current_pps)][stat],
                                     "Ensure stat %s has value incremented for pps %s as compared to pps %s and it "
                                     "is %s and %s respectively" %
                                     (stat, next_pps, current_pps, output_avg_dict[str(next_pps)][stat],
                                      output_avg_dict[str(current_pps)][stat]))
        '''

        for key, val in output_avg_dict.iteritems():
            fun_test.log("Check for pps %s" % key)

            fun_test.test_assert_expected(expected=val[DUT_ECN_COUNT], actual=val[SPIRENT_ECN_COUNT],
                                          message="Check ecn counts in DUT and seen on spirent match")

        # Check ecn counters have stopped incrementing
        check_stop = check_wred_ecn_counter_stopped(network_controller_obj=network_controller_obj,
                                                    port_num=dut_port_2,
                                                    queue_num=self.test_queue, type=QOS_PROFILE_ECN)
        fun_test.test_assert(check_stop, "Ensure ecn counters are not seen when we do not exceed bandwidth")


class ECN_01(ECN_10):
    test_type = QOS_PROFILE_ECN
    ecn_bits = ECN_BITS_01
    max_queue_pps = 0
    stats_list = [q_depth, ecn_count]

    def describe(self):
        self.set_test_details(id=3,
                              summary="Test ecn count increases as queue depth increases on DUT for Q0 with ECN bits in packet set to 01",
                              steps="""
                                  1. Update stream on port 1 to start with pps
                                  3. setup ecn config
                                  4. Start stream from port 1 and port 3
                                  5. Note down 5 iterations of wred_ecn stats for q depth and ecn count and take average of it
                                  6. Now iterate step 5 for different pps for normal stream.
                                  7. Verify that as q depth increases, ecn count increases
                                  8. For every iteration check if ecn count on dut and spirent match
                                  """)


class ECN_10_00(FunTestCase):
    port_1_stream_dscp = 0
    port_3_stream_dscp = 16
    stream_ecn_bits_list = [ECN_BITS_10, ECN_BITS_00]
    stream_dscps = None
    test_type = QOS_PROFILE_ECN
    qos_profile_dict = None
    timer = None
    min_thr = None
    max_thr = None
    prob_index = None
    prof_num = None
    stream_pps_list = None
    enable_ecn = None
    avg_period = None
    cap_avg_sz = None
    cap_avg_enable = None
    max_egress_load = None

    def describe(self):
        self.set_test_details(id=4,
                              summary="Test ecn bits are set for packets only who have ecn bit set to 10",
                              steps="""
                              1. Update stream from port 1 and port 3 with dscp 0 and 16 having ecn bits set to 
                                 10 and 01 respectively.
                              2. Add ecn profile for queue 0 on egress dut port.
                              3. Start traffic for both streams.
                              4. Verify from diff serv stats on spirent that only dscp 0 has packets with ecn bits set 
                                 and dscp 16 have no packets with ecn bits set
                              """)
    def setup_variables(self):
        self.port_1_stream_dscp = 0
        self.port_3_stream_dscp = 16
        self.stream_dscps = [self.port_1_stream_dscp, self.port_3_stream_dscp]
        self.test_type = QOS_PROFILE_ECN
        self.qos_profile_dict = qos_json_output[self.test_type]
        self.timer = self.qos_profile_dict['ecn_timer']
        self.min_thr = self.qos_profile_dict['ecn_min_thr']
        self.max_thr = self.qos_profile_dict['ecn_max_thr']
        self.prob_index = self.qos_profile_dict['ecn_prob_index']
        self.prof_num = self.qos_profile_dict['ecn_prof_num']
        self.stream_pps_list = self.qos_profile_dict['stream_pps']['ingress_port_1']
        self.enable_ecn = self.qos_profile_dict['ecn_enable']
        self.avg_period = self.qos_profile_dict['avg_period']
        self.cap_avg_sz = self.qos_profile_dict['cap_avg_sz']
        self.cap_avg_enable = self.qos_profile_dict['cap_avg_enable']
        self.max_egress_load = max_egress_load

    def setup(self):
        self.setup_variables()
        # Update streams to dscp and ecn bits
        stream_pps = get_load_value_from_load_percent(load_percent=self.stream_pps_list,
                                                      max_egress_load=max_egress_load)

        for stream, queue_num, ecn_bits in zip(streamblock_objs_list, self.stream_dscps, self.stream_ecn_bits_list):
            fun_test.log("Updating stream %s with dscp %s having ecn 10 and load to %s" % (stream.spirent_handle,
                                                                                           queue_num, stream_pps))
            dscp_values = template_obj.get_diff_serv_dscp_value_from_decimal_value(
                decimal_value_list=[queue_num], dscp_high=True, dscp_low=True)
            dscp_high = dscp_values[queue_num]['dscp_high']
            dscp_low = dscp_values[queue_num]['dscp_low']

            dscp_set = template_obj.configure_diffserv(streamblock_obj=stream,
                                                       dscp_high=dscp_high,
                                                       dscp_low=dscp_low, reserved=ecn_bits, update=True)
            fun_test.test_assert(dscp_set, "Ensure dscp value of %s is updated on ip header for stream %s"
                                 % (queue_num, stream.spirent_handle))

            stream.Load = stream_pps
            stream.LoadUnit = stream.LOAD_UNIT_MEGABITS_PER_SECOND
            streamblock_1 = template_obj.configure_stream_block(stream, update=True)
            fun_test.test_assert(streamblock_1, "Update stream %s with load as %s" % (stream.spirent_handle,
                                                                                      stream_pps))

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
            stream_blocks_list=streamblock_handles_list)
        fun_test.test_assert(start_streams, "Start running traffic")

        fun_test.sleep("Letting traffic to be run", seconds=self.timer)

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
                        fun_test.add_checkpoint("Diff serv count having ECN bits set to 11 for queue %s is %s" % (
                            queue, int(out[key]['Ipv4FrameCount'])))
                    else:
                        fun_test.add_checkpoint("Diff serv count having ECN bits set to 11 for queue %s is %s" % (
                        queue, 0))

        # Display ecn stats
        network_controller_obj.get_qos_wred_ecn_stats(dut_port_2, self.port_1_stream_dscp)

        self.do_test_asserts(result)

    def do_test_asserts(self, result):
        fun_test.test_assert(result[str(self.stream_dscps[0])], "Ensure ECN bits is set to 11 for DSCP 0 as it had "
                                                                "ecn bits 01")

        fun_test.test_assert(not result[str(self.stream_dscps[1])],
                             "Ensure ECN bits is not set to 11 for DSCP 16 as it had "
                             "ecn bits 00")

    def cleanup(self):
        stop_streams = template_obj.stc_manager.stop_traffic_stream(
            stream_blocks_list=streamblock_handles_list)
        fun_test.add_checkpoint("Stop running traffic")

        # Clear all subscribed results
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

        set_queue_cfg = network_controller_obj.set_qos_wred_queue_config(port_num=dut_port_2,
                                                                         queue_num=self.port_1_stream_dscp,
                                                                         enable_ecn=0,
                                                                         ecn_profile_num=self.prof_num)
        fun_test.add_checkpoint("Disable ecn on queue %s" % self.port_1_stream_dscp)


class ECN_10_10(ECN_10_00):
    stream_ecn_bits_list = [ECN_BITS_10, ECN_BITS_10]

    def describe(self):
        self.set_test_details(id=5,
                              summary="Test ecn bits are set for packets coming from all ingress ports",
                              steps="""
                              1. Update stream from port 1 and port 3 with dscp 0 and 16 having respectively and 
                              ecn bits set to 10.
                              2. Add ecn profile for queue 0 on egress dut port.
                              3. Start traffic for both streams.
                              4. Verify from diff serv stats on spirent that both dscp 0 and dscp 16 have 
                              some packets that have ecn bits set to 11
                              """)

    def do_test_asserts(self, result):
        fun_test.test_assert(result[str(self.stream_dscps[0])], "Ensure ECN bits is set to 11 for DSCP 0 as it had "
                                                                "ecn bits 01")

        fun_test.test_assert(result[str(self.stream_dscps[1])], "Ensure ECN bits is set to 11 for DSCP 16 as it had "
                                                                "ecn bits 01")


if __name__ == "__main__":
    ts = SpirentSetup()
    ts.add_test_case(Wred_Q0())
    '''
    ts.add_test_case(ECN_10())
    ts.add_test_case(ECN_01())
    ts.add_test_case(ECN_10_00())
    ts.add_test_case(ECN_10_10())
    '''
    ts.run()