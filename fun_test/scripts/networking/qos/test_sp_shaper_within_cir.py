from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, GeneratorConfig, Ethernet2Header, Ipv4Header
from lib.host.network_controller import NetworkController
from scripts.networking.nu_config_manager import nu_config_obj
from scripts.networking.helper import *
from qos_helper import *

num_ports = 3
streamblock_objs = {}
generator_config_objs = {}
generator_dict = {}
config = nu_config_obj.read_dut_config()
qos_json_file = fun_test.get_script_parent_directory() + '/qos.json'
if config['type'] == 'f1':
    qos_json_file = fun_test.get_script_parent_directory() + '/qos_f1.json'
qos_json_output = fun_test.parse_file_to_json(qos_json_file)
test_type = "sp_shaper"
qos_sp_json = qos_json_output[test_type]
sleep_timer = qos_sp_json['sp_shaper_timer']

max_egress_load = qos_json_output['max_egress_load']
json_load_unit = qos_json_output['load_unit']
k_list = [x for x in range(0, 16)]
k_list.reverse()


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
        global template_obj, port_1, port_2, subscribe_results, network_controller_obj, dut_port_2, \
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

        json_load_unit = qos_json_output['load_unit']
        load_unit = None
        if json_load_unit == "Mbps":
            load_unit = StreamBlock.LOAD_UNIT_MEGABITS_PER_SECOND

        # Create 2 streams on port_1
        for port_obj in port_obj_list[::2]:
            streamblock_objs[port_obj] = []
            num_streams = 2

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

        reset_config = reset_queue_scheduler_config(network_controller_obj=network_controller_obj, dut_port=dut_port_2)
        fun_test.test_assert(reset_config, "Ensure default scheduler config is set for all queues")

    def cleanup(self):
        reset_config = reset_queue_scheduler_config(network_controller_obj=network_controller_obj, dut_port=dut_port_2)
        fun_test.test_assert(reset_config, "Ensure default scheduler config is set for all queues")

        fun_test.test_assert(template_obj.cleanup(), "Cleaning up session")


class SP_Shaper_Q0_SP(FunTestCase):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    cir = "within_cir_1"
    test_streams = qos_sp_json[cir]
    total_streams = 0
    port_1_dscp = [0, 1]
    port_3_dscp = [2, 3]

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test scheduler when all queues are within cir and one queue is in SP",
                              steps="""
                              1. Create stream with dscp 0 and dscp 1 on port 1 and with dscp 2 and 3 on port 3
                              2. Ensure strict priority is applied to dscp 0 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Verify bandwidth is such that SP gets its assigned bandwidth and 
                                 rest queues are in served in RR
                              """)

    def setup(self):
        # Create streams
        for port, streams in self.test_streams.iteritems():
            self.total_streams += len(streams)
            self.testcase_streamblocks[str(port)] = {}
            spirent_port = port_1
            current_list = self.port_1_dscp
            if port == "ingress_port2":
                spirent_port = port_3
                current_list = self.port_3_dscp

            counter = 0

            for stream_details, dscp_val in zip(streams, current_list):
                self.testcase_streamblocks[str(port)][dscp_val] = {}
                current_streamblock_obj = streamblock_objs[spirent_port][counter]
                load_value = get_load_value_from_load_percent(load_percent=stream_details['load_percent'],
                                                              max_egress_load=max_egress_load)
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

                # set shaper rate and threshold
                set_rate = network_controller_obj.set_qos_scheduler_config(port_num=dut_port_2,
                                                                           queue_num=dscp_val,
                                                                           scheduler_type=network_controller_obj.SCHEDULER_TYPE_SHAPER,
                                                                           shaper_enable=True,
                                                                           min_rate=stream_details['rate'],
                                                                           shaper_threshold=stream_details['threshold'])
                fun_test.test_assert(set_rate, "Ensure shaper rate is %s, threshold is %s set on port %s for queue %s" %
                                     (stream_details['rate'], stream_details['threshold'], dut_port_2,
                                      dscp_val))

                set_strict = network_controller_obj.set_qos_scheduler_config(port_num=dut_port_2,
                                                                             queue_num=dscp_val,
                                                                             scheduler_type=network_controller_obj.SCHEDULER_TYPE_STRICT_PRIORITY,
                                                                             strict_priority_enable=stream_details['sp'],
                                                                             extra_bandwidth=stream_details['eb'])
                fun_test.test_assert(set_strict, "Ensure strict priority is %s and extra bandwidth is %s set on port %s for queue %s" %
                                     (stream_details['sp'], stream_details['eb'], dut_port_2,
                                      dscp_val))

                if 'weight' in stream_details:
                    set_weight = network_controller_obj.set_qos_scheduler_config(port_num=dut_port_2,
                                                                                 queue_num=dscp_val,
                                                                                 scheduler_type=network_controller_obj.SCHEDULER_TYPE_WEIGHTED_ROUND_ROBIN,
                                                                                 weight=stream_details['weight'])
                    fun_test.test_assert(set_weight, "Ensure dwrr weight is %s set on port %s for queue %s" %
                                         (stream_details['weight'], dut_port_2,
                                          dscp_val))

    def cleanup(self):

        stop_streams = template_obj.stc_manager.stop_traffic_stream(
            stream_blocks_list=self.streamblock_handles_list)
        fun_test.test_assert(stop_streams, "Ensure dscp streams are stopped")

        reset_config = reset_queue_scheduler_config(network_controller_obj=network_controller_obj, dut_port=dut_port_2)
        fun_test.test_assert(reset_config, "Ensure default scheduler config is set for all queues")

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

        output = self.start_and_fetch_streamblock_results()

        for port, streams in self.test_streams.iteritems():
            current_list = self.port_1_dscp
            if port == "ingress_port2":
                current_list = self.port_3_dscp
            for stream_details, dscp_val in zip(streams, current_list):
                expected_load_value = get_load_value_from_load_percent(
                    load_percent=stream_details['expected_load_percent'],
                    max_egress_load=max_egress_load)
                fun_test.simple_assert(expected_load_value is not None, "Ensure expected load value is calculated")

                current_streamblock_handle = \
                    self.testcase_streamblocks[str(port)][dscp_val]['streamblock_obj'].spirent_handle
                rx_l1_bit_rate = convert_bps_to_mbps(int(output[current_streamblock_handle]['rx_summary_result']['L1BitRate']))

                result_dict[dscp_val] = {}
                result_dict[dscp_val]['actual'] = rx_l1_bit_rate
                result_dict[dscp_val]['expected'] = expected_load_value
        self.validate_stats(result_dict)

    def validate_stats(self, result_dict):
        for dscp, values in result_dict.iteritems():
            load_check = verify_load_output(actual_value=values['actual'],
                                            expected_value=values['expected'])
            fun_test.test_assert(load_check, "Ensure shaper rate %s is seen for dscp %s. Actual seen %s" %
                                 (values['expected'], dscp, values['actual']))


class SP_Shaper_Q0_Q2_SP(SP_Shaper_Q0_SP):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    cir = "within_cir_2"
    test_streams = qos_sp_json[cir]
    total_streams = 0
    port_1_dscp = [0, 1]
    port_3_dscp = [2, 3]

    def describe(self):
        self.set_test_details(id=2,
                              summary="Test scheduler when all queues are within cir and two queues is in SP",
                              steps="""
                              1. Create stream with dscp 0 and dscp 1 on port 1 and with dscp 2 and 3 on port 3
                              2. Ensure strict priority is applied to dscp 0 and dscp 2 on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Verify bandwidth is such that SP gets its assigned bandwidth and 
                                 rest queues are in served in RR
                              """)


class SP_Shaper_All_SP(SP_Shaper_Q0_SP):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    cir = "within_cir_3"
    test_streams = qos_sp_json[cir]
    total_streams = 0
    port_1_dscp = [0, 1]
    port_3_dscp = [2, 3]

    def describe(self):
        self.set_test_details(id=3,
                              summary="Test scheduler when all queues are within cir and all are SP",
                              steps="""
                              1. Create stream with dscp 0 and dscp 1 on port 1 and with dscp 2 and 3 on port 3
                              2. Ensure strict priority is applied to all queues on egress port.
                              3. Start traffic
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Verify bandwidth is such that SP queues with lower number hoggs the bandwidth
                              """)


if __name__ == "__main__":
    local_settings = nu_config_obj.get_local_settings_parameters(flow_direction=True, ip_version=True)
    flow_direction = local_settings[nu_config_obj.FLOW_DIRECTION]
    ts = SpirentSetup()
    ts.add_test_case(SP_Shaper_Q0_SP())
    ts.add_test_case(SP_Shaper_Q0_Q2_SP())
    ts.add_test_case(SP_Shaper_All_SP())
    ts.run()