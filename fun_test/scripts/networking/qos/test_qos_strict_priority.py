from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, GeneratorConfig, Ethernet2Header, Ipv4Header
from lib.host.network_controller import NetworkController
from scripts.networking.nu_config_manager import nu_config_obj
from scripts.networking.helper import *
from scripts.networking.qos.qos_helper import *
import itertools

num_ports = 3
config = nu_config_obj.read_dut_config()
qos_json_file = fun_test.get_script_parent_directory() + '/qos.json'
if config['type'] == 'f1':
    qos_json_file = fun_test.get_script_parent_directory() + '/qos_f1.json'
qos_json_output = fun_test.parse_file_to_json(qos_json_file)
test_type = "strict_priority"
qos_sp_json = qos_json_output[test_type]
sleep_timer = qos_sp_json['sp_traffic_time']
streamblock_objs = {}
generator_config_objs = {}
generator_dict = {}
sp = 'sp'
non_sp = 'non_sp'
k_list = [x for x in range(0, 16)]
k_list.reverse()


class SpirentSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
                1. Create Spirent template
                2. Connect chassis, labserver and licenseserver
                3. Attach Ports
                4. Configure streams on port 1 and port 3 that will send traffic on port 2
                5. Subscribe to rx
                6. Perform ingress pg_to_priority_group and egress queue to pg
                """)

    def setup(self):
        global template_obj, port_1, port_2, pfc_frame, subscribe_results, network_controller_obj, dut_port_2, \
            dut_port_1, hnu, shape, port_3, port_obj_list, destination_ip1, destination_mac1, dut_port_list, flow_direction

        min_frame_length = 64
        max_frame_length = 1500

        flow_direction = nu_config_obj.FLOW_DIRECTION_NU_NU

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
                                                      chassis_type=nu_config_obj.FLOW_DIRECTION_NU_NU)
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
            streamblock_objs[port_obj] = []
            num_streams = 2
            if port_obj == port_1:
                num_streams = 1

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

            for i in range(num_streams):
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
                streamblock_objs[port_obj].append(create_streamblock_1)

        # Subscribe to results
        project = template_obj.stc_manager.get_project_handle()
        subscribe_results = template_obj.subscribe_to_all_results(parent=project)
        fun_test.test_assert(subscribe_results['result'], "Subscribing to results")
        del subscribe_results['result']

        for dut_port in dut_port_list:
            if not dut_port == dut_port_2:
                # set ingress priority to pg map list
                set_ingress_priority_map = network_controller_obj.set_qos_priority_to_pg_map(port_num=dut_port,
                                                                                             map_list=k_list)
                fun_test.test_assert(set_ingress_priority_map, message="Set priority to pg map")
            else:
                # set egress priority to pg map list
                set_egress_priority_map = network_controller_obj.set_qos_queue_to_priority_map(port_num=dut_port,
                                                                                               map_list=k_list)
                fun_test.test_assert(set_egress_priority_map, "Set queue to priority map")

    def cleanup(self):
        reset_config = reset_queue_scheduler_config(network_controller_obj=network_controller_obj, dut_port=dut_port_2)
        fun_test.add_checkpoint("Ensure default scheduler config is set for all queues")

        template_obj.cleanup()
        
        
class Q0_SP_Channel0(FunTestCase):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    channel = "channel_0"
    sp_queue_numbers = "Q0"
    max_egress_load = qos_json_output['max_egress_load']
    json_load_unit = qos_json_output['load_unit']
    test_streams = qos_sp_json[channel][sp_queue_numbers]
    multi_split_sp = False
    sp_dscp_list = [0]
    non_sp_dscp_list = [1, 2]
    sp_list_only = False

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test strict priority on channel 0 for queue 0 on egress port",
                              steps="""
                              1. Create stream with dscp 0 on port 1 and with dscp 1 and 2 on port 3
                              2. Ensure strict priority is applied to dscp 0 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. dscp 0 stream must be getting entire bandwidth assigned to it and remaining must
                              be shared between other two streams
                              """)

    def setup(self):
        # Create streams
        for port, streams in self.test_streams.iteritems():
            self.testcase_streamblocks[str(port)] = {}
            spirent_port = port_1
            current_list = self.sp_dscp_list
            if self.sp_list_only:
                current_list = []
                current_list.append(self.sp_dscp_list[0])
            if port == "ingress_port2":
                spirent_port = port_3
                current_list = self.non_sp_dscp_list
                if self.sp_list_only:
                    current_list = []
                    current_list.append(self.sp_dscp_list[1])

            counter = 0
            for stream_details, dscp_val in zip(streams, current_list):
                self.testcase_streamblocks[str(port)][dscp_val] = {}
                current_streamblock_obj = streamblock_objs[spirent_port][counter]
                load_value = get_load_value_from_load_percent(load_percent=stream_details['load_percent'],
                                                              max_egress_load=self.max_egress_load)
                fun_test.simple_assert(load_value, "Ensure load value is calculated")

                dscp_values = template_obj.get_diff_serv_dscp_value_from_decimal_value(
                    decimal_value_list=[dscp_val], dscp_high=True, dscp_low=True)
                dscp_high = dscp_values[dscp_val]['dscp_high']
                dscp_low = dscp_values[dscp_val]['dscp_low']

                # Update dscp value
                dscp_set = template_obj.configure_diffserv(streamblock_obj=current_streamblock_obj,
                                                           dscp_high=dscp_high,
                                                           dscp_low=dscp_low, update=True)
                fun_test.test_assert(dscp_set, "Ensure dscp value of %s is updated on ip header for stream %s"
                                     % (dscp_val, current_streamblock_obj.spirent_handle))

                # Update load value
                current_streamblock_obj.Load = load_value
                update_stream = template_obj.configure_stream_block(stream_block_obj=current_streamblock_obj, update=True)
                fun_test.test_assert(update_stream, "Ensure load value is updated to %s in stream %s" %
                                     (load_value, current_streamblock_obj.spirent_handle))
                counter += 1
                self.testcase_streamblocks[str(port)][dscp_val]['streamblock_obj'] = current_streamblock_obj
                self.streamblock_handles_list.append(current_streamblock_obj.spirent_handle)

        for dscp_val in itertools.chain(self.sp_dscp_list, self.non_sp_dscp_list):
            strict_priority = False
            if dscp_val in self.sp_dscp_list:
                strict_priority = True
            strict = network_controller_obj.set_qos_scheduler_config(port_num=dut_port_2, queue_num=dscp_val,
                                                                     scheduler_type=network_controller_obj.SCHEDULER_TYPE_STRICT_PRIORITY,
                                                                     strict_priority_enable=strict_priority,
                                                                     extra_bandwidth=1)
            fun_test.add_checkpoint("Set strict priority of %s on queue %s" % (strict_priority, dscp_val))

            shaper = network_controller_obj.set_qos_scheduler_config(port_num=dut_port_2, queue_num=dscp_val,
                                                                     scheduler_type=network_controller_obj.SCHEDULER_TYPE_SHAPER,
                                                                     shaper_enable=False,
                                                                     min_rate=qos_json_output['shaper']['default_cir'],
                                                                     shaper_threshold=qos_json_output['shaper']['default_threshold'])
            fun_test.add_checkpoint("Reset shaper cir and threshold to default values for queue %s" % dscp_val)

            dwrr = network_controller_obj.set_qos_scheduler_config(port_num=dut_port_2, queue_num=dscp_val,
                                                                   scheduler_type=network_controller_obj.SCHEDULER_TYPE_WEIGHTED_ROUND_ROBIN,
                                                                   weight=qos_json_output['dwrr']['default_weight'])
            fun_test.add_checkpoint("Reset dwrr to default values for queue %s" % dscp_val)

    def cleanup(self):
        stop_streams = template_obj.stc_manager.stop_traffic_stream(
            stream_blocks_list=self.streamblock_handles_list)
        fun_test.add_checkpoint("Ensure dscp streams are stopped")

        # Clear all subscribed results
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def start_and_fetch_streamblock_results(self):
        start_streams = template_obj.stc_manager.start_traffic_stream(
            stream_blocks_list=self.streamblock_handles_list)
        fun_test.test_assert(start_streams, "Ensure dscp streams are started")

        fun_test.sleep("Sleeping %s seconds for traffic to execute", seconds=sleep_timer)

        # Fetch Rx L1 rate
        output = template_obj.stc_manager.fetch_streamblock_results(subscribe_result=subscribe_results,
                                                                    streamblock_handle_list=self.streamblock_handles_list,
                                                                    rx_summary_result=True)
        return output

    def run(self):
        result_dict = {}
        result_dict[sp] = {}
        result_dict[non_sp] = {}

        output = self.start_and_fetch_streamblock_results()

        for port, streams in self.test_streams.iteritems():
            current_list = self.sp_dscp_list
            if self.sp_list_only:
                current_list = []
                current_list.append(self.sp_dscp_list[0])
            if port == "ingress_port2":
                current_list = self.non_sp_dscp_list
                if self.sp_list_only:
                    current_list = []
                    current_list.append(self.sp_dscp_list[1])

            for stream_details, dscp_val in zip(streams, current_list):
                expected_load_value = get_load_value_from_load_percent(load_percent=stream_details['expected_load_percent'],
                                                                       max_egress_load=self.max_egress_load)
                fun_test.simple_assert(expected_load_value is not None, "Ensure expected load value is calculated")

                current_streamblock_handle = \
                    self.testcase_streamblocks[str(port)][dscp_val]['streamblock_obj'].spirent_handle
                rx_l1_bit_rate = convert_bps_to_mbps(int(output[current_streamblock_handle]['rx_summary_result']['L1BitRate']))

                priority_type = non_sp
                if int(dscp_val) in self.sp_dscp_list:
                    priority_type = sp

                result_dict[priority_type][dscp_val] = {}
                result_dict[priority_type][dscp_val]['result'] = False
                result_dict[priority_type][dscp_val]['actual'] = rx_l1_bit_rate
                result_dict[priority_type][dscp_val]['expected'] = expected_load_value
                '''
                result = verify_load_output(actual_value=rx_l1_bit_rate,
                                            expected_value=expected_load_value)
                fun_test.test_assert(result, "Ensure output load for stream with dscp %s is within range."
                                             "Actual seen is %s. Expected is %s" % (dscp_val,
                                                                                    rx_l1_bit_rate,
                                                                                    expected_load_value))
                '''

        sp_output_dict = self.validate_sp_output(result_dict=result_dict[sp])
        if result_dict[non_sp]:
            non_sp_output_dict = self.validate_non_sp_output(result_dict=result_dict[non_sp])

        for dscp, stream_results in sp_output_dict.iteritems():
            fun_test.test_assert(stream_results['result'], "Actual value seen for dscp %s with strict priority is %s. "
                                                           "Expected is %s" % (dscp, stream_results['actual'],
                                                                               stream_results['expected']))

        if result_dict[non_sp]:
            for dscp, stream_results in non_sp_output_dict.iteritems():
                fun_test.test_assert(stream_results['result'], "Actual value seen for dscp %s with no strict priority is"
                                                               " %s. Expected is %s" % (dscp, stream_results['actual'],
                                                                                        stream_results['expected']))

    def validate_sp_output(self, result_dict):
        for dscp_val, stream_details in result_dict.iteritems():
            stream_details['result'] = verify_load_output(actual_value=stream_details['actual'],
                                                          expected_value=stream_details['expected'])
        return result_dict

    def validate_non_sp_output(self, result_dict):
        for dscp_val, stream_details in result_dict.iteritems():
            stream_details['result'] = verify_load_output(actual_value=stream_details['actual'],
                                                          expected_value=stream_details['expected'])
        return result_dict


class Q1_SP_Channel0(Q0_SP_Channel0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    channel = "channel_0"
    sp_queue_numbers = "Q0"
    max_egress_load = qos_json_output['max_egress_load']
    json_load_unit = qos_json_output['load_unit']
    test_streams = qos_sp_json[channel][sp_queue_numbers]
    multi_split_sp = False
    sp_dscp_list = [1]
    non_sp_dscp_list = [2, 3]
    sp_list_only = False

    def describe(self):
        self.set_test_details(id=2,
                              summary="Test strict priority on channel 0 for queue 0 on egress port",
                              steps="""
                              1. Create stream with dscp 1 on port 1 and with dscp 2 and 3 on port 3
                              2. Ensure strict priority is applied to dscp 0 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. dscp 1 stream must be getting entire bandwidth assigned to it and remaining must
                              be shared between other two streams
                              """)


class Q2_SP_Channel0(Q0_SP_Channel0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    channel = "channel_0"
    sp_queue_numbers = "Q0"
    max_egress_load = qos_json_output['max_egress_load']
    json_load_unit = qos_json_output['load_unit']
    test_streams = qos_sp_json[channel][sp_queue_numbers]
    multi_split_sp = False
    sp_dscp_list = [2]
    non_sp_dscp_list = [3, 4]
    sp_list_only = False

    def describe(self):
        self.set_test_details(id=3,
                              summary="Test strict priority on channel 0 for queue 2 on egress port",
                              steps="""
                              1. Create stream with dscp 2 on port 1 and with dscp 3 and 4 on port 3
                              2. Ensure strict priority is applied to dscp 0 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. dscp 2 stream must be getting entire bandwidth assigned to it and remaining must
                              be shared between other two streams
                              """)

class Q3_SP_Channel0(Q0_SP_Channel0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    channel = "channel_0"
    sp_queue_numbers = "Q0"
    max_egress_load = qos_json_output['max_egress_load']
    json_load_unit = qos_json_output['load_unit']
    test_streams = qos_sp_json[channel][sp_queue_numbers]
    multi_split_sp = False
    sp_dscp_list = [3]
    non_sp_dscp_list = [4, 5]
    sp_list_only = False

    def describe(self):
        self.set_test_details(id=4,
                              summary="Test strict priority on channel 0 for queue 3 on egress port",
                              steps="""
                              1. Create stream with dscp 1 on port 1 and with dscp 2 and 3 on port 3
                              2. Ensure strict priority is applied to dscp 0 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. dscp 1 stream must be getting entire bandwidth assigned to it and remaining must
                              be shared between other two streams
                              """)


class Q5_SP_Channel0(Q0_SP_Channel0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    channel = "channel_0"
    sp_queue_numbers = "Q0"
    max_egress_load = qos_json_output['max_egress_load']
    json_load_unit = qos_json_output['load_unit']
    test_streams = qos_sp_json[channel][sp_queue_numbers]
    multi_split_sp = False
    sp_dscp_list = [5]
    non_sp_dscp_list = [6, 7]
    sp_list_only = False

    def describe(self):
        self.set_test_details(id=5,
                              summary="Test strict priority on channel 0 for queue 5 on egress port",
                              steps="""
                              1. Create stream with dscp 5 on port 1 and with dscp 6 and 7 on port 3
                              2. Ensure strict priority is applied to dscp 0 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. dscp 5 stream must be getting entire bandwidth assigned to it and remaining must
                              be shared between other two streams
                              """)


class Q6_SP_Channel0(Q0_SP_Channel0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    channel = "channel_0"
    sp_queue_numbers = "Q0"
    max_egress_load = qos_json_output['max_egress_load']
    json_load_unit = qos_json_output['load_unit']
    test_streams = qos_sp_json[channel][sp_queue_numbers]
    multi_split_sp = False
    sp_dscp_list = [6]
    non_sp_dscp_list = [7, 1]
    sp_list_only = False

    def describe(self):
        self.set_test_details(id=6,
                              summary="Test strict priority on channel 0 for queue 6 on egress port",
                              steps="""
                              1. Create stream with dscp 6 on port 1 and with dscp 7 and 1 on port 3
                              2. Ensure strict priority is applied to dscp 0 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. dscp 6 stream must be getting entire bandwidth assigned to it and remaining must
                              be shared between other two streams
                              """)


class Q7_SP_Channel0(Q0_SP_Channel0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    channel = "channel_0"
    sp_queue_numbers = "Q0"
    max_egress_load = qos_json_output['max_egress_load']
    json_load_unit = qos_json_output['load_unit']
    test_streams = qos_sp_json[channel][sp_queue_numbers]
    multi_split_sp = False
    sp_dscp_list = [7]
    non_sp_dscp_list = [2, 3]
    sp_list_only = False

    def describe(self):
        self.set_test_details(id=7,
                              summary="Test strict priority on channel 0 for queue 7 on egress port",
                              steps="""
                              1. Create stream with dscp 7 on port 1 and with dscp 2 and 3 on port 3
                              2. Ensure strict priority is applied to dscp 0 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. dscp 7 stream must be getting entire bandwidth assigned to it and remaining must
                              be shared between other two streams
                              """)


class Q4_SP_Channel0(Q0_SP_Channel0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    multi_split_sp = False
    channel = "channel_0"
    sp_queue_numbers = "Q4"
    test_streams = qos_sp_json[channel][sp_queue_numbers]
    sp_dscp_list = [4]
    non_sp_dscp_list = [5, 0]
    sp_list_only = False

    def describe(self):
        self.set_test_details(id=8,
                              summary="Test strict priority on channel 0 for queue 4 on egress port",
                              steps="""
                              1. Create stream with dscp 4 on port 1 and with dscp 5 and 0 on port 3
                              2. Ensure strict priority is applied to dscp 0 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Ensure q4 gets its allocated b/w and rest is shared eequally among them 
                              """)


class Q8_SP_Channel1(Q0_SP_Channel0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    channel = "channel_1"
    sp_queue_numbers = "Q0"
    test_streams = qos_sp_json[channel][sp_queue_numbers]
    sp_dscp_list = [8]
    non_sp_dscp_list = [9, 10]
    sp_list_only = False

    def describe(self):
        self.set_test_details(id=9,
                              summary="Test strict priority on channel 1 for queue 8 on egress port",
                              steps="""
                              1. Create stream with dscp 8 on port 1 and with dscp 8 and 9 on port 3
                              2. Ensure strict priority is applied to dscp 0 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Ensure q8 gets its allocated b/w and rest is shared eequally among them 
                              """)


class Q9_SP_Channel1(Q0_SP_Channel0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    channel = "channel_1"
    sp_queue_numbers = "Q0"
    test_streams = qos_sp_json[channel][sp_queue_numbers]
    sp_dscp_list = [9]
    non_sp_dscp_list = [10, 11]
    sp_list_only = False

    def describe(self):
        self.set_test_details(id=10,
                              summary="Test strict priority on channel 1 for queue 9 on egress port",
                              steps="""
                              1. Create stream with dscp 9 on port 1 and with dscp 10 and 11 on port 3
                              2. Ensure strict priority is applied to dscp 0 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Ensure q9 gets its allocated b/w and rest is shared eequally among them 
                              """)

class Q10_SP_Channel1(Q0_SP_Channel0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    channel = "channel_1"
    sp_queue_numbers = "Q0"
    test_streams = qos_sp_json[channel][sp_queue_numbers]
    sp_dscp_list = [10]
    non_sp_dscp_list = [11, 12]
    sp_list_only = False

    def describe(self):
        self.set_test_details(id=11,
                              summary="Test strict priority on channel 1 for queue 10 on egress port",
                              steps="""
                              1. Create stream with dscp 10 on port 1 and with dscp 11 and 12 on port 3
                              2. Ensure strict priority is applied to dscp 0 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Ensure q10 gets its allocated b/w and rest is shared eequally among them 
                              """)

class Q12_SP_Channel1(Q0_SP_Channel0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    channel = "channel_1"
    sp_queue_numbers = "Q0"
    test_streams = qos_sp_json[channel][sp_queue_numbers]
    sp_dscp_list = [12]
    non_sp_dscp_list = [13, 14]
    sp_list_only = False

    def describe(self):
        self.set_test_details(id=12,
                              summary="Test strict priority on channel 1 for queue 12 on egress port",
                              steps="""
                              1. Create stream with dscp 12 on port 1 and with dscp 13 and 14 on port 3
                              2. Ensure strict priority is applied to dscp 0 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Ensure q12 gets its allocated b/w and rest is shared eequally among them 
                              """)

class Q13_SP_Channel1(Q0_SP_Channel0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    channel = "channel_1"
    sp_queue_numbers = "Q0"
    test_streams = qos_sp_json[channel][sp_queue_numbers]
    sp_dscp_list = [13]
    non_sp_dscp_list = [14, 15]
    sp_list_only = False

    def describe(self):
        self.set_test_details(id=13,
                              summary="Test strict priority on channel 1 for queue 13 on egress port",
                              steps="""
                              1. Create stream with dscp 13 on port 1 and with dscp 14 and 15 on port 3
                              2. Ensure strict priority is applied to dscp 0 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Ensure q13 gets its allocated b/w and rest is shared eequally among them 
                              """)

class Q14_SP_Channel1(Q0_SP_Channel0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    channel = "channel_1"
    sp_queue_numbers = "Q0"
    test_streams = qos_sp_json[channel][sp_queue_numbers]
    sp_dscp_list = [14]
    non_sp_dscp_list = [15, 9]
    sp_list_only = False

    def describe(self):
        self.set_test_details(id=14,
                              summary="Test strict priority on channel 1 for queue 14 on egress port",
                              steps="""
                              1. Create stream with dscp 14 on port 1 and with dscp 15 and 9 on port 3
                              2. Ensure strict priority is applied to dscp 0 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Ensure q14 gets its allocated b/w and rest is shared eequally among them 
                              """)

class Q15_SP_Channel1(Q0_SP_Channel0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    channel = "channel_1"
    sp_queue_numbers = "Q0"
    test_streams = qos_sp_json[channel][sp_queue_numbers]
    sp_dscp_list = [15]
    non_sp_dscp_list = [9, 10]
    sp_list_only = False

    def describe(self):
        self.set_test_details(id=15,
                              summary="Test strict priority on channel 1 for queue 15 on egress port",
                              steps="""
                              1. Create stream with dscp 15 on port 1 and with dscp 9 and 10 on port 3
                              2. Ensure strict priority is applied to dscp 0 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Ensure q15 gets its allocated b/w and rest is shared eequally among them 
                              """)


class Q11_SP_Channel1(Q0_SP_Channel0):
    channel = "channel_1"
    sp_queue_numbers = "Q4"
    testcase_streamblocks = {}
    streamblock_handles_list = []
    multi_split_sp = False
    test_streams = qos_sp_json[channel][sp_queue_numbers]
    sp_dscp_list = [11]
    non_sp_dscp_list = [12, 8]
    sp_list_only = False

    def describe(self):
        self.set_test_details(id=16,
                              summary="Test strict priority on channel 1 for queue 11 on egress port",
                              steps="""
                              1. Create stream with dscp 11 on port 1 and with dscp 12 and 8 on port 3
                              2. Ensure strict priority is applied to dscp 0 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Ensure q11 gets its allocated b/w and rest is shared eequally among them 
                              """)


class Q0_Q8_SP_Channel0_Channel1(Q0_SP_Channel0):
    channel = "channel_0_channel_1"
    sp_queue_numbers = "Q0_Q8"
    non_sp_dscp_list = []
    testcase_streamblocks = {}
    streamblock_handles_list = []
    test_streams = qos_sp_json[channel][sp_queue_numbers]
    sp_dscp_list = [0, 8]
    sp_list_only = True

    def describe(self):
        self.set_test_details(id=17,
                              summary="Test strict priority on channel 0 and channel 1 for queue 0 and queue 8"
                                      " on egress port",
                              steps="""
                              1. Create stream with dscp 0 on port 1 and with dscp 8 on port 3
                              2. Ensure strict priority is applied to dscp 0 and 8 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Ensure bandwidth is shared equally among two streams
                              """)


class Q1_Q9_SP_Channel0_Channel1(Q0_SP_Channel0):
    channel = "channel_0_channel_1"
    sp_queue_numbers = "Q0_Q8"
    non_sp_dscp_list = []
    testcase_streamblocks = {}
    streamblock_handles_list = []
    test_streams = qos_sp_json[channel][sp_queue_numbers]
    sp_dscp_list = [1, 9]
    sp_list_only = True

    def describe(self):
        self.set_test_details(id=18,
                              summary="Test strict priority on channel 0 and channel 1 for queue 1 and queue 9"
                                      " on egress port",
                              steps="""
                              1. Create stream with dscp 1 on port 1 and with dscp 9 on port 3
                              2. Ensure strict priority is applied to dscp 1 and 9 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Ensure bandwidth is shared equally among two streams
                              """)


class Q2_Q10_SP_Channel0_Channel1(Q0_SP_Channel0):
    channel = "channel_0_channel_1"
    sp_queue_numbers = "Q0_Q8"
    non_sp_dscp_list = []
    testcase_streamblocks = {}
    streamblock_handles_list = []
    test_streams = qos_sp_json[channel][sp_queue_numbers]
    sp_dscp_list = [2, 10]
    sp_list_only = True

    def describe(self):
        self.set_test_details(id=19,
                              summary="Test strict priority on channel 0 and channel 1 for queue 2 and queue 10"
                                      " on egress port",
                              steps="""
                              1. Create stream with dscp 2 on port 1 and with dscp 10 on port 3
                              2. Ensure strict priority is applied to dscp 2 and 10 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Ensure bandwidth is shared equally among two streams
                              """)


class Q3_Q11_SP_Channel0_Channel1(Q0_SP_Channel0):
    channel = "channel_0_channel_1"
    sp_queue_numbers = "Q0_Q8"
    non_sp_dscp_list = []
    testcase_streamblocks = {}
    streamblock_handles_list = []
    test_streams = qos_sp_json[channel][sp_queue_numbers]
    sp_dscp_list = [3, 11]
    sp_list_only = True

    def describe(self):
        self.set_test_details(id=20,
                              summary="Test strict priority on channel 0 and channel 1 for queue 3 and queue 11"
                                      " on egress port",
                              steps="""
                              1. Create stream with dscp 0 on port 3 and with dscp 11 on port 3
                              2. Ensure strict priority is applied to dscp 3 and 11 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Ensure bandwidth is shared equally among two streams
                              """)


class Q4_Q12_SP_Channel0_Channel1(Q0_SP_Channel0):
    channel = "channel_0_channel_1"
    sp_queue_numbers = "Q0_Q8"
    non_sp_dscp_list = []
    testcase_streamblocks = {}
    streamblock_handles_list = []
    test_streams = qos_sp_json[channel][sp_queue_numbers]
    sp_dscp_list = [4, 12]
    sp_list_only = True

    def describe(self):
        self.set_test_details(id=21,
                              summary="Test strict priority on channel 0 and channel 1 for queue 4 and queue 12"
                                      " on egress port",
                              steps="""
                              1. Create stream with dscp 4 on port 1 and with dscp 12 on port 3
                              2. Ensure strict priority is applied to dscp 4 and 12 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Ensure bandwidth is shared equally among two streams
                              """)


class Q5_Q13_SP_Channel0_Channel1(Q0_SP_Channel0):
    channel = "channel_0_channel_1"
    sp_queue_numbers = "Q0_Q8"
    non_sp_dscp_list = []
    testcase_streamblocks = {}
    streamblock_handles_list = []
    test_streams = qos_sp_json[channel][sp_queue_numbers]
    sp_dscp_list = [5, 13]
    sp_list_only = True

    def describe(self):
        self.set_test_details(id=22,
                              summary="Test strict priority on channel 0 and channel 1 for queue 5 and queue 13"
                                      " on egress port",
                              steps="""
                              1. Create stream with dscp 5 on port 1 and with dscp 13 on port 3
                              2. Ensure strict priority is applied to dscp 5 and 13 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Ensure bandwidth is shared equally among two streams
                              """)


class Q6_Q14_SP_Channel0_Channel1(Q0_SP_Channel0):
    channel = "channel_0_channel_1"
    sp_queue_numbers = "Q0_Q8"
    non_sp_dscp_list = []
    testcase_streamblocks = {}
    streamblock_handles_list = []
    test_streams = qos_sp_json[channel][sp_queue_numbers]
    sp_dscp_list = [6, 14]
    sp_list_only = True

    def describe(self):
        self.set_test_details(id=23,
                              summary="Test strict priority on channel 0 and channel 1 for queue 6 and queue 14"
                                      " on egress port",
                              steps="""
                              1. Create stream with dscp 6 on port 1 and with dscp 14 on port 3
                              2. Ensure strict priority is applied to dscp 6 and 14 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Ensure bandwidth is shared equally among two streams
                              """)

class Q7_Q15_SP_Channel0_Channel1(Q0_SP_Channel0):
    channel = "channel_0_channel_1"
    sp_queue_numbers = "Q0_Q8"
    non_sp_dscp_list = []
    testcase_streamblocks = {}
    streamblock_handles_list = []
    test_streams = qos_sp_json[channel][sp_queue_numbers]
    sp_dscp_list = [7, 15]
    sp_list_only = True

    def describe(self):
        self.set_test_details(id=24,
                              summary="Test strict priority on channel 0 and channel 1 for queue 7 and queue 15"
                                      " on egress port",
                              steps="""
                              1. Create stream with dscp 7 on port 1 and with dscp 15 on port 3
                              2. Ensure strict priority is applied to dscp 7 and 15 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Ensure bandwidth is shared equally among two streams
                              """)


class Q0_Q9_SP_Channel0_Channel1(Q0_Q8_SP_Channel0_Channel1):
    channel = "channel_0_channel_1"
    sp_queue_numbers = "Q0_Q9"
    non_sp_dscp_list = []
    testcase_streamblocks = {}
    streamblock_handles_list = []
    test_streams = qos_sp_json[channel][sp_queue_numbers]
    sp_dscp_list = [0, 9]
    sp_list_only = True

    def describe(self):
        self.set_test_details(id=25,
                              summary="Test strict priority on channel 0 and channel 1 for queue 0 and queue 9"
                                      " on egress port",
                              steps="""
                              1. Create stream with dscp 0 on port 1 and with dscp 9 on port 3
                              2. Ensure strict priority is applied to dscp 0 and 9 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Ensure bandwidth is shared equally among two streams
                              """)


if __name__ == "__main__":
    ts = SpirentSetup()
    ts.add_test_case(Q0_SP_Channel0())
    ts.add_test_case(Q1_SP_Channel0())
    ts.add_test_case(Q2_SP_Channel0())
    ts.add_test_case(Q3_SP_Channel0())
    ts.add_test_case(Q4_SP_Channel0())
    ts.add_test_case(Q5_SP_Channel0())
    ts.add_test_case(Q6_SP_Channel0())
    ts.add_test_case(Q7_SP_Channel0())
    ts.add_test_case(Q8_SP_Channel1())
    ts.add_test_case(Q9_SP_Channel1())
    ts.add_test_case(Q10_SP_Channel1())
    ts.add_test_case(Q11_SP_Channel1())
    ts.add_test_case(Q12_SP_Channel1())
    ts.add_test_case(Q13_SP_Channel1())
    ts.add_test_case(Q14_SP_Channel1())
    ts.add_test_case(Q15_SP_Channel1())
    ts.add_test_case(Q0_Q8_SP_Channel0_Channel1())
    ts.add_test_case(Q1_Q9_SP_Channel0_Channel1())
    ts.add_test_case(Q2_Q10_SP_Channel0_Channel1())
    ts.add_test_case(Q3_Q11_SP_Channel0_Channel1())
    ts.add_test_case(Q4_Q12_SP_Channel0_Channel1())
    ts.add_test_case(Q5_Q13_SP_Channel0_Channel1())
    ts.add_test_case(Q6_Q14_SP_Channel0_Channel1())
    ts.add_test_case(Q7_Q15_SP_Channel0_Channel1())
    ts.add_test_case(Q0_Q9_SP_Channel0_Channel1())
    ts.run()