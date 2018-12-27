from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, GeneratorConfig, Ethernet2Header, Ipv4Header
from lib.host.network_controller import NetworkController
from scripts.networking.nu_config_manager import nu_config_obj
from scripts.networking.helper import *
from qos_helper import *
import copy

num_ports = 3
streamblock_objs = {}
streamblock_handle_list = []
queue_list = [x for x in range(16)]
reversed_list = copy.deepcopy(queue_list)
reversed_list.reverse()
generator_config_objs = {}
generator_dict = {}
qos_json_file = fun_test.get_script_parent_directory() + '/qos.json'
qos_json_output = fun_test.parse_file_to_json(qos_json_file)
max_egress_load = qos_json_output['max_egress_load']
json_load_unit = qos_json_output['load_unit']
q_depth = 'avg_q_integ'
wred_q_drop = 'wred_q_drop'


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
        global template_obj, port_1, port_2, pfc_frame, subscribe_results, network_controller_obj, dut_port_2, \
            dut_port_1, hnu, shape, port_3, port_obj_list, destination_ip1, destination_mac1, dut_port_list

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
        template_obj = SpirentEthernetTrafficTemplate(session_name="test_pfc_ingress_qos",
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
        fun_test.log("Using dut ports %s, %s and %s" % (dut_port_1, dut_port_2, dut_port_3))

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

        load_unit = StreamBlock.LOAD_UNIT_MEGABITS_PER_SECOND

        # Create 2 streams on port_1
        for port_obj in port_obj_list[::2]:
            streamblock_objs[port_obj] = {}
            if port_obj == port_1:
                dscp_list = queue_list[:8]
            else:
                dscp_list = queue_list[8:]

            generator_config_objs[port_obj] = None
            gen_config_obj = GeneratorConfig(scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED,
                                             duration_mode=GeneratorConfig.DURATION_MODE_CONTINOUS,
                                             advanced_interleaving=True)

            gen_obj_1 = template_obj.stc_manager.get_generator(port_handle=port_obj)
            config_obj = template_obj.configure_generator_config(port_handle=port_obj,
                                                                 generator_config_obj=gen_config_obj)
            fun_test.test_assert(config_obj, "Creating generator config on port %s" % port_obj)

            generator_dict[port_obj] = gen_obj_1
            generator_config_objs[port_obj] = gen_config_obj

            for i in dscp_list:
                streamblock_objs[port_obj][str(i)] = None
                dscp_values = template_obj.get_diff_serv_dscp_value_from_decimal_value(
                    decimal_value_list=[i], dscp_high=True, dscp_low=True)
                dscp_high = dscp_values[i]['dscp_high']
                dscp_low = dscp_values[i]['dscp_low']

                create_streamblock_1 = StreamBlock(load_unit=load_unit, fill_type=StreamBlock.FILL_TYPE_PRBS,
                                                   min_frame_length=min_frame_length, max_frame_length=max_frame_length,
                                                   frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_RANDOM)
                streamblock_1 = template_obj.configure_stream_block(create_streamblock_1,
                                                                    port_handle=port_obj)
                fun_test.test_assert(streamblock_1, "Creating streamblock on port %s" % port_obj)

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
                                                           dscp_high=dscp_high,
                                                           dscp_low=dscp_low)
                fun_test.test_assert(dscp_set, "Ensure dscp value of %s is set on ip header for stream %s"
                                     % (i, create_streamblock_1._spirent_handle))
                streamblock_objs[port_obj][str(i)] = create_streamblock_1
                streamblock_handle_list.append(create_streamblock_1._spirent_handle)

        # Subscribe to results
        project = template_obj.stc_manager.get_project_handle()
        subscribe_results = template_obj.subscribe_to_all_results(parent=project, diff_serv=True)
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

        reset_config = reset_queue_scheduler_config(network_controller_obj=network_controller_obj, dut_port=dut_port_2)
        fun_test.add_checkpoint("Ensure default scheduler config is set for all queues")

    def cleanup(self):
        reset_config = reset_queue_scheduler_config(network_controller_obj=network_controller_obj, dut_port=dut_port_2)
        fun_test.add_checkpoint("Ensure default scheduler config is set for all queues")

        template_obj.cleanup()


class All_Queues_Share_BW(FunTestCase):
    test_type = "strict_priority"
    qos_sp_json = qos_json_output[test_type]['all_queues']
    sleep_timer = qos_sp_json['all_queues_traffic_time']
    difference_accept_range = 0.1
    same_expected_load = True

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test bandwidth is shared between all queues with default config",
                              steps="""
                                1. Disable strict priority and extra bandwidth for queue 0 and 8
                                2. Start traffic for all queues together
                                3. At egress bandwidth must be shared between all queues 
                                """)

    def setup(self):

        for queue in [0, 8]:
            disable = network_controller_obj.set_qos_scheduler_config(port_num=dut_port_2, queue_num=queue,
                                                                      scheduler_type=network_controller_obj.SCHEDULER_TYPE_STRICT_PRIORITY,
                                                                      strict_priority_enable=False, extra_bandwidth=0)
            fun_test.test_assert(disable, "Disbale sp and eb on queue %s" % queue, ignore_on_success=True)

    def cleanup(self):
        stop_streams = template_obj.stc_manager.stop_traffic_stream(
            stream_blocks_list=streamblock_handle_list)
        fun_test.add_checkpoint("Ensure all streams are stopped")

    def start_and_fetch_streamblock_results(self):
        start_streams = template_obj.stc_manager.start_traffic_stream(
            stream_blocks_list=streamblock_handle_list)
        fun_test.add_checkpoint("Ensure all streams are started")

        fun_test.sleep("Sleeping %s seconds for traffic to execute", seconds=self.sleep_timer)

        # Fetch Rx L1 rate
        output = template_obj.stc_manager.fetch_streamblock_results(subscribe_result=subscribe_results,
                                                                    streamblock_handle_list=streamblock_handle_list,
                                                                    rx_summary_result=True)
        return output

    def run(self):
        result_dict = {}

        output = self.start_and_fetch_streamblock_results()

        if self.same_expected_load:
            expected_load_value = get_load_value_from_load_percent(
                        load_percent=self.qos_sp_json['ingress_port1'][0]['expected_load_percent'],
                        max_egress_load=max_egress_load)
            fun_test.simple_assert(expected_load_value is not None, "Ensure expected load value is calculated")

        for queue in queue_list:
            current_port = port_1
            ingress_port = 'ingress_port1'
            if queue >= 8:
                current_port = port_3
                ingress_port = 'ingress_port2'
            result_dict[str(queue)] = {}

            current_streamblock_handle = \
                streamblock_objs[str(current_port)][str(queue)].spirent_handle
            rx_l1_bit_rate = convert_bps_to_mbps(
                int(output[current_streamblock_handle]['rx_summary_result']['L1BitRate']))
            fun_test.log("Actual value of bandwidth seen at egress for queue %s is %s" %(queue, rx_l1_bit_rate))

            result_dict[str(queue)]['actual'] = rx_l1_bit_rate

            if not self.same_expected_load:
                queue_value = queue
                if ingress_port =='ingress_port2':
                    queue_value = queue - 8
                expected_load_value = get_load_value_from_load_percent(
                    load_percent=self.qos_sp_json[ingress_port][queue_value]['expected_load_percent'],
                    max_egress_load=max_egress_load)
                fun_test.simple_assert(expected_load_value is not None, "Ensure expected load value is calculated for queue %s" % queue)

            result_dict[str(queue)]['expected'] = expected_load_value
        self.validate_stats(result_dict)

    def validate_stats(self, result_dict):
        for dscp, values in result_dict.iteritems():
            load_check = verify_load_output(actual_value=values['actual'],
                                            expected_value=values['expected'], accept_range=self.difference_accept_range, compare=True)
            fun_test.test_assert(load_check, "Ensure rate %s is seen for dscp %s. Actual seen %s" %
                                 (values['expected'], dscp, values['actual']))


class All_Queues_Pir(All_Queues_Share_BW):
    test_type = "shaper"
    qos_sp_json = qos_json_output[test_type]['all_queues_pir']
    sleep_timer = qos_sp_json['all_queues_traffic_time']
    difference_accept_range = 0.1

    def describe(self):
        self.set_test_details(id=2,
                              summary="Test all queues follow the pir assigned to it",
                              steps="""
                                1. Disable strict priority and extra bandwidth for queue 0 and 8
                                2. Set pir value to each queue
                                3. Start traffic for all queues together
                                4. Verify that each queue only tx at its pir assigned
                                """)

    def setup(self):
        reset_config = reset_queue_scheduler_config(network_controller_obj=network_controller_obj, dut_port=dut_port_2)
        fun_test.add_checkpoint("Ensure default scheduler config is set for all queues")

        for queue in queue_list:
            disable = network_controller_obj.set_qos_scheduler_config(port_num=dut_port_2, queue_num=queue,
                                                                      scheduler_type=network_controller_obj.SCHEDULER_TYPE_SHAPER,
                                                                      shaper_enable=True,
                                                                      max_rate=self.qos_sp_json['ingress_port1'][0]['rate'],
                                                                      shaper_threshold=self.qos_sp_json['ingress_port1'][0]['threshold'])
            fun_test.test_assert(disable, "Set pir on queue %s" % queue, ignore_on_success=True)

    def cleanup(self):
        super(All_Queues_Pir, self).cleanup()

        for queue in queue_list:
            disable = network_controller_obj.set_qos_scheduler_config(port_num=dut_port_2, queue_num=queue,
                                                                      scheduler_type=network_controller_obj.SCHEDULER_TYPE_SHAPER,
                                                                      shaper_enable=False,
                                                                      max_rate=0,
                                                                      shaper_threshold=0)
            fun_test.add_checkpoint("Remove pir on queue %s" % queue, ignore_on_success=True)


class All_Queues_DWRR(All_Queues_Share_BW):
    test_type = "all_queues_dwrr"
    qos_sp_json = qos_json_output[test_type]
    sleep_timer = qos_sp_json['all_queues_traffic_time']
    difference_accept_range = 0.1
    same_expected_load = False

    def describe(self):
        self.set_test_details(id=3,
                              summary="Test all queues follow the weights assigned to it",
                              steps="""
                                1. Disable strict priority and extra bandwidth for queue 0 and 8
                                2. Set weight value to each queue
                                3. Start traffic for all queues together
                                4. Verify that each queue only tx at its weight assigned
                                """)

    def setup(self):
        super(All_Queues_DWRR, self).setup()

        for queue in queue_list:
            ingress_port = "ingress_port1"
            spirent_port = port_1
            if queue >= 8:
                ingress_port = "ingress_port2"
                spirent_port = port_3
            ingress_port_list = self.qos_sp_json[ingress_port]
            for stream_info in ingress_port_list:
                if stream_info['dscp'] == queue:
                    # Update streamblock load value
                    load_value = get_load_value_from_load_percent(load_percent=stream_info['load_percent'],
                                                                  max_egress_load=max_egress_load)
                    fun_test.simple_assert(load_value, "Ensure load value is calculated")

                    current_streamblock = streamblock_objs[spirent_port][str(queue)]
                    current_streamblock.Load = load_value
                    update_stream = template_obj.configure_stream_block(stream_block_obj=current_streamblock,
                                                                        update=True)
                    fun_test.test_assert(update_stream, "Ensure load value is updated to %s in stream %s" %
                                         (load_value, current_streamblock.spirent_handle))

                    current_weight = stream_info['weight']
                    break
            weight = network_controller_obj.set_qos_scheduler_config(port_num=dut_port_2, queue_num=queue,
                                                                     scheduler_type=network_controller_obj.SCHEDULER_TYPE_WEIGHTED_ROUND_ROBIN,
                                                                     weight=current_weight)
            fun_test.test_assert(weight, "Set weight %s on queue %s" % (current_weight, queue), ignore_on_success=True)

            rate = network_controller_obj.set_qos_scheduler_config(port_num=dut_port_2, queue_num=queue,
                                                                   scheduler_type=network_controller_obj.SCHEDULER_TYPE_SHAPER,
                                                                   shaper_enable=True, min_rate=1,
                                                                   shaper_threshold=282000)
            fun_test.test_assert(rate, "Set rate 1 on queue %s" % queue, ignore_on_success=True)

    def cleanup(self):
        for queue in queue_list:
            weight = network_controller_obj.set_qos_scheduler_config(port_num=dut_port_2, queue_num=queue,
                                                                     scheduler_type=network_controller_obj.SCHEDULER_TYPE_WEIGHTED_ROUND_ROBIN,
                                                                     weight=1)
            fun_test.add_checkpoint("Set weight %s on queue %s" % (1, queue))


            rate = network_controller_obj.set_qos_scheduler_config(port_num=dut_port_2, queue_num=queue,
                                                                   scheduler_type=network_controller_obj.SCHEDULER_TYPE_SHAPER,
                                                                   shaper_enable=True, min_rate=2000,
                                                                   shaper_threshold=1000)
            fun_test.add_checkpoint("Set default rate 2000 on queue %s" % queue)
        fun_test.log("Resetted dwrr and shaper values to default")

class All_Queues_WRED(FunTestCase):
    """
    For WRED we are using the same key from qos.json that is used in other testcases
    """
    test_type = "all_queue_wred"
    qos_test_json = qos_json_output[test_type]
    sleep_timer = qos_test_json['wred_timer']
    normal_stream_pps_list = qos_test_json['stream_pps_percent']
    min_thr = qos_test_json['wred_min_thr']
    max_thr = qos_test_json['wred_max_thr']
    wred_weight = qos_test_json['wred_weight']
    wred_enable = qos_test_json['wred_enable']
    pfc_pps = qos_test_json['pfc_pps']
    pfc_quanta = qos_test_json['pfc_quanta']
    prob_index = qos_test_json['wred_prob_index']
    prof_num = qos_test_json['wred_prof_num']
    non_wred_load_percent = qos_test_json['non_wred_load_percent']
    avg_period = qos_test_json['avg_period']
    cap_avg_sz = qos_test_json['cap_avg_sz']
    stats_list = [q_depth, wred_q_drop]
    reserved_val = '0064' * 13
    cushion_drops = 30
    cushion_depth = 5
    queue_monitor_iteration = 5
    packet_size = 128

    def describe(self):
        self.set_test_details(id=4,
                              summary="Test all queues follow the wred profile assigned to it",
                              steps="""
                                1. Assign wred profile id to all queues
                                2. Start traffic for all queues together
                                3. Verify that each queue has wred drops and compare them with all other queues
                                """)

    def setup(self):
        for queue in [0, 8]:
            disable = network_controller_obj.set_qos_scheduler_config(port_num=dut_port_2, queue_num=queue,
                                                                      scheduler_type=network_controller_obj.SCHEDULER_TYPE_STRICT_PRIORITY,
                                                                      strict_priority_enable=False, extra_bandwidth=0)
            fun_test.test_assert(disable, "Disbale sp and eb on queue %s" % queue, ignore_on_success=True)

        fun_test.log("Enable qos pfc")
        qos_pfc = network_controller_obj.enable_qos_pfc(hnu=hnu)
        fun_test.simple_assert(qos_pfc, "Enabled qos pfc")

        fun_test.log("Enable pfc on dut port %s" % dut_port_2)
        dut_port_pfc = network_controller_obj.enable_priority_flow_control(port_num=dut_port_2, shape=shape)
        fun_test.simple_assert(dut_port_pfc, "Enable pfc on dut port %s" % dut_port_2)

        set_avg_q_cfg = network_controller_obj.set_qos_wred_avg_queue_config(avg_en=1, avg_period=self.avg_period,
                                                                             cap_avg_sz=self.cap_avg_sz, q_avg_en=1)
        fun_test.simple_assert(set_avg_q_cfg, "Ensure avg q config is set")

        if QOS_PROFILE_WRED in self.test_type:
            set_prob = set_default_qos_probability(network_controller_obj=network_controller_obj,
                                                   profile_type=QOS_PROFILE_WRED)
            fun_test.simple_assert(set_prob, "Ensure prob range is set")

            wred_profile = network_controller_obj.set_qos_wred_profile(prof_num=self.prof_num,
                                                                       min_threshold=self.min_thr,
                                                                       max_threshold=self.max_thr,
                                                                       wred_prob_index=self.prob_index)

            for queue in queue_list:
                set_queue_cfg = network_controller_obj.set_qos_wred_queue_config(port_num=dut_port_2,
                                                                                 queue_num=queue,
                                                                                 wred_enable=self.wred_enable,
                                                                                 wred_prof_num=self.prof_num,
                                                                                 wred_weight=self.wred_weight)
                fun_test.simple_assert(set_queue_cfg, "Ensure queue config is set for queue %s" % queue)
        else:
            set_prob = set_default_qos_probability(network_controller_obj=network_controller_obj,
                                                   profile_type=QOS_PROFILE_ECN)
            fun_test.simple_assert(set_prob, "Ensure prob range is set")

            wred_profile = network_controller_obj.set_qos_ecn_profile(prof_num=self.prof_num,
                                                                       min_threshold=self.min_thr,
                                                                       max_threshold=self.max_thr,
                                                                       ecn_prob_index=self.prob_index)

            for queue in queue_list:
                set_queue_cfg = network_controller_obj.set_qos_wred_queue_config(port_num=dut_port_2,
                                                                                 queue_num=queue,
                                                                                 ecn_profile_num=self.prof_num,
                                                                                 enable_ecn=self.ecn_enable)
                fun_test.simple_assert(set_queue_cfg, "Ensure queue config is set for queue %s" % queue)
        fun_test.simple_assert(wred_profile, "Ensure profile is set")

    def run(self):
        result_dict = {}

        max_egress_packets = get_load_pps_for_each_queue(max_egress_load_mbps=max_egress_load,
                                                         packet_size=self.packet_size, total_queues=len(queue_list))
        packet_num_list = []
        for percent_load in self.normal_stream_pps_list:
            packet_num_list.append(int((percent_load / 100.0) * max_egress_packets))

        for pps in packet_num_list:
            result_dict[str(pps)] = {}
            # Update load on all streams
            port_1_stream_obj = streamblock_objs[str(port_1)]
            port_3_stream_obj = streamblock_objs[str(port_3)]
            for queue in queue_list:
                result_dict[str(pps)][str(queue)] = {}
                if str(queue) in port_1_stream_obj.keys():
                    current_streamblock = port_1_stream_obj[str(queue)]
                else:
                    current_streamblock = port_3_stream_obj[str(queue)]

                if QOS_PROFILE_ECN in self.test_type:
                    dscp_values = template_obj.get_diff_serv_dscp_value_from_decimal_value(
                        decimal_value_list=[queue], dscp_high=True, dscp_low=True)
                    dscp_high = dscp_values[queue]['dscp_high']
                    dscp_low = dscp_values[queue]['dscp_low']

                    # Update dscp value
                    dscp_set = template_obj.configure_diffserv(streamblock_obj=current_streamblock,
                                                               dscp_high=dscp_high,
                                                               dscp_low=dscp_low,
                                                               update=True)
                    fun_test.simple_assert(dscp_set, "Ensure dscp value of %s is updated on ip header for stream %s"
                                           % (queue, current_streamblock.spirent_handle))

                current_streamblock.FrameLengthMode = current_streamblock.FRAME_LENGTH_MODE_FIXED
                current_streamblock.FixedFrameLength = self.packet_size
                current_streamblock.LoadUnit = current_streamblock.LOAD_UNIT_FRAMES_PER_SECOND

                update = template_obj.configure_stream_block(current_streamblock, update=True)
                fun_test.simple_assert(update, "Update stream load pps and unit to fps for stream %s" %
                                       current_streamblock.spirent_handle)

            start_streams = template_obj.stc_manager.start_traffic_stream(
                stream_blocks_list=streamblock_handle_list)
            fun_test.test_assert(start_streams, "Ensure all streams are started")

            fun_test.sleep("Letting traffic run", seconds=self.sleep_timer)

            for queue in queue_list:
                fun_test.log("Fetching q depth and wred q drops for for %s" % queue)
                result_dict[str(pps)][str(queue)] = capture_wred_ecn_stats_n_times(network_controller_obj=network_controller_obj,
                                                                         port_num=dut_port_2, queue_num=queue,
                                                                         iterations=self.queue_monitor_iteration,
                                                                         stats_list=self.stats_list)

                for stat in self.stats_list:
                    avg_val = reduce(lambda a, b: a + b, result_dict[str(pps)][str(queue)][stat]) / len(result_dict[str(pps)][str(queue)][stat])
                    fun_test.log("Average value seen for stat %s for pps %s for queue %s is %s" % (stat, pps,
                                                                                      queue, avg_val))
                    result_dict[str(pps)][str(queue)][stat] = avg_val

            stop_streams = template_obj.stc_manager.stop_traffic_stream(
                stream_blocks_list=streamblock_handle_list)
            fun_test.test_assert(stop_streams, "Ensure all streams are stopped")

        # Taking q0 values as reference and will compare with others
        queue_0 = queue_list[0]
        reference_wred_q_drops = result_dict[str(queue_0)][wred_q_drop]
        reference_q_depth = result_dict[str(queue_0)][q_depth]
        lower_wred_q_drop_limit = reference_wred_q_drops - self.cushion_drops
        higher_wred_q_drop_limit = reference_wred_q_drops + self.cushion_drops
        lower_q_depth_limit = reference_q_depth - self.cushion_depth
        higher_q_depth_limit = reference_q_depth + self.cushion_depth
        for pps in packet_num_list:
            fun_test.log("Checking results for pps %s" % pps)
            for queue in queue_list[1:]:
                fun_test.test_assert(lower_wred_q_drop_limit < result_dict[str(pps)][str(queue)][wred_q_drop] < higher_wred_q_drop_limit,
                                     "Ensure stat %s for queue %s is in range between %s and %s" %
                                     (wred_q_drop, queue, lower_wred_q_drop_limit, higher_wred_q_drop_limit))

                fun_test.test_assert(
                    lower_q_depth_limit < result_dict[str(pps)][str(queue)][q_depth] < higher_q_depth_limit,
                    "Ensure stat %s for queue %s is in range between %s and %s" %
                    (q_depth, queue, lower_q_depth_limit, higher_q_depth_limit))
            fun_test.log("=========x===========x===========x==========")

    def cleanup(self):
        for queue in queue_list:
            set_queue_cfg = network_controller_obj.set_qos_wred_queue_config(port_num=dut_port_2,
                                                                             queue_num=queue,
                                                                             wred_enable=0,
                                                                             wred_weight=self.wred_weight,
                                                                             wred_prof_num=self.prof_num)
            fun_test.add_checkpoint("Ensure queue config is set for %s" % queue)


class All_Queues_ECN(All_Queues_WRED):
    test_type = QOS_PROFILE_ECN
    qos_test_json = qos_json_output[test_type]
    sleep_timer = qos_test_json['ecn_timer']
    normal_stream_pps = qos_test_json['stream_pps']
    min_thr = qos_test_json['ecn_min_thr']
    max_thr = qos_test_json['ecn_max_thr']
    ecn_enable = qos_test_json['ecn_enable']
    pfc_pps = qos_test_json['pfc_pps']
    pfc_quanta = qos_test_json['pfc_quanta']
    prob_index = qos_test_json['ecn_prob_index']
    prof_num = qos_test_json['ecn_prof_num']
    avg_period = qos_test_json['avg_period']
    cap_avg_sz = qos_test_json['cap_avg_sz']
    stats_list = [q_depth, ecn_count]
    reserved_val = '0064' * 13
    current_ecn_bits = ECN_BITS_10

    def describe(self):
        self.set_test_details(id=4,
                              summary="Test all queues work with ecn compatible bits and set to 11 "
                                      "when congestion occurs",
                              steps="""
                                    1. Assign ecn profile id to all queues
                                    2. Create pfc stream on port 2
                                    3. Start traffic for all queues together
                                    4. Verify that each queue has some frames sent out with ecn bits 11
                                    """)

    def run(self):
        super(All_Queues_ECN).run()

        result = {}
        out = template_obj.stc_manager.get_port_diffserv_results(port_handle=port_2,
                                                                 subscribe_handle=subscribe_results[
                                                                     'diff_serv_subscribe'])

        for queue in queue_list:
            result[str(queue)] = False
            ecn_qos_val = template_obj.get_diff_serv_dscp_value_from_decimal_value(decimal_value_list=[queue],
                                                                                   dscp_value=True)
            qos_binary_value = get_ecn_qos_binary(qos_binary=ecn_qos_val[queue]['dscp_value'])
            for key in out.keys():
                if key == str(qos_binary_value):
                    if int(out[key]['Ipv4FrameCount']) > 0:
                        result[str(queue)] = True

        for queue in queue_list:
            fun_test.test_assert(result[str(queue)], message="Check ECN set counters on spirent are seen for queue %s" % queue)

    def cleanup(self):
        for queue in queue_list:
            set_queue_cfg = network_controller_obj.set_qos_wred_queue_config(port_num=dut_port_2,
                                                                             queue_num=queue,
                                                                             enable_ecn=0,
                                                                             ecn_profile_num=self.prof_num)
            fun_test.add_checkpoint("Ensure queue config is set for %s" % queue)



if __name__ == "__main__":
    local_settings = nu_config_obj.get_local_settings_parameters(flow_direction=True, ip_version=True)
    flow_direction = local_settings[nu_config_obj.FLOW_DIRECTION]
    ts = SpirentSetup()
    ts.add_test_case(All_Queues_Share_BW())
    ts.add_test_case(All_Queues_Pir())
    ts.add_test_case(All_Queues_DWRR())
    ts.add_test_case(All_Queues_WRED())
    ts.add_test_case(All_Queues_ECN())
    ts.run()