from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, GeneratorConfig, Ethernet2Header, Ipv4Header
from lib.host.network_controller import NetworkController
from scripts.networking.nu_config_manager import nu_config_obj
from scripts.networking.helper import *
from scripts.networking.qos.qos_helper import *

num_ports = 3
streamblock_objs = {}
generator_config_objs = {}
generator_dict = {}
config = nu_config_obj.read_dut_config()
qos_json_file = fun_test.get_script_parent_directory() + '/qos.json'
if config['type'] == 'f1':
    qos_json_file = fun_test.get_script_parent_directory() + '/qos_f1.json'
qos_json_output = fun_test.parse_file_to_json(qos_json_file)
test_type = "shaper"
qos_sp_json = qos_json_output[test_type]
sleep_timer = qos_sp_json['shaper_traffic_time']
cir = "pir"
max_egress_load = qos_json_output['max_egress_load']
json_load_unit = qos_json_output['load_unit']
test_streams = qos_sp_json[cir]
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
        global template_obj, port_1, port_2, pfc_frame, subscribe_results, network_controller_obj, dut_port_2, \
            dut_port_1, hnu, shape, port_3, port_obj_list, destination_ip1, destination_mac1, dut_port_list, flow_direction
        flow_direction = nu_config_obj.FLOW_DIRECTION_NU_NU

        min_frame_length = 64
        max_frame_length = 1500

        dut_type = fun_test.get_local_setting(setting="dut_type")
        dut_config = nu_config_obj.read_dut_config(dut_type=dut_type, flow_direction=flow_direction)

        shape = 0
        hnu = False
        if flow_direction == nu_config_obj.FLOW_DIRECTION_HNU_HNU:
            shape = 1
            hnu = True

        spirent_config = nu_config_obj.read_traffic_generator_config()

        fun_test.log("Creating Template object")
        template_obj = SpirentEthernetTrafficTemplate(session_name="test_pfc_ingress_qos",
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


class Pir_Q0(FunTestCase):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    pir_stream_dscp = 0
    other_stream_dscp = 1

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test shaper pir for queue 0",
                              steps="""
                              1. Create stream with dscp 0 on port 1
                              2. Configure pir for Q0
                              3. Start traffic having load greater than configured pir rate
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Verify bandwidth is such that it is restricted to pir rate assigned
                              """)

    def setup(self):
        # Create streams
        for port, streams in test_streams.iteritems():
            self.testcase_streamblocks[str(port)] = {}
            spirent_port = port_1
            current_dscp = self.pir_stream_dscp
            if port == 'ingress_port2':
                spirent_port = port_3
                current_dscp = self.other_stream_dscp

            counter = 0

            for stream_details in streams:
                self.testcase_streamblocks[str(port)][current_dscp] = {}
                current_streamblock_obj = streamblock_objs[spirent_port][counter]
                load_value = get_load_value_from_load_percent(load_percent=stream_details['load_percent'],
                                                              max_egress_load=max_egress_load)
                fun_test.simple_assert(load_value, "Ensure load value is calculated")

                dscp_values = template_obj.get_diff_serv_dscp_value_from_decimal_value(
                    decimal_value_list=[current_dscp], dscp_high=True, dscp_low=True)
                dscp_high = dscp_values[current_dscp]['dscp_high']
                dscp_low = dscp_values[current_dscp]['dscp_low']

                # Update dscp value
                dscp_set = template_obj.configure_diffserv(streamblock_obj=current_streamblock_obj,
                                                           dscp_high=dscp_high,
                                                           dscp_low=dscp_low, update=True)
                fun_test.test_assert(dscp_set, "Ensure dscp value of %s is updated on ip header for stream %s"
                                     % (current_dscp, current_streamblock_obj.spirent_handle))

                # Update load value
                current_streamblock_obj.Load = load_value
                update_stream = template_obj.configure_stream_block(stream_block_obj=current_streamblock_obj, update=True)
                fun_test.test_assert(update_stream, "Ensure load value is updated to %s in stream %s" %
                                     (load_value, current_streamblock_obj.spirent_handle))
                counter += 1
                self.testcase_streamblocks[str(port)][current_dscp]['streamblock_obj'] = current_streamblock_obj
                self.streamblock_handles_list.append(current_streamblock_obj.spirent_handle)

                # set shaper rate and threshold
                if 'rate' in stream_details:
                    set_rate = network_controller_obj.set_qos_scheduler_config(port_num=dut_port_2,
                                                                               queue_num=current_dscp,
                                                                               scheduler_type=network_controller_obj.SCHEDULER_TYPE_SHAPER,
                                                                               shaper_enable=True,
                                                                               max_rate=stream_details['rate'],
                                                                               shaper_threshold=stream_details[
                                                                                   'threshold'])
                    fun_test.test_assert(set_rate,
                                         "Ensure shaper rate is %s, threshold is %s set on port %s for queue %s" %
                                         (stream_details['rate'], stream_details['threshold'], dut_port_2,
                                          current_dscp))

    def cleanup(self):
        set_rate = network_controller_obj.set_qos_scheduler_config(port_num=dut_port_2,
                                                                   queue_num=self.pir_stream_dscp,
                                                                   scheduler_type=network_controller_obj.SCHEDULER_TYPE_SHAPER,
                                                                   shaper_enable=False,
                                                                   max_rate=0,
                                                                   shaper_threshold=0)
        fun_test.add_checkpoint("Reset shaper rate to 0, threshold is 0 set on port %s for queue %s" %
                             (dut_port_2, self.pir_stream_dscp))

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

        output = self.start_and_fetch_streamblock_results()

        for port, streams in test_streams.iteritems():
            current_dscp = self.pir_stream_dscp
            if port == 'ingress_port2':
                current_dscp = self.other_stream_dscp
            for stream_details in streams:
                expected_load_value = get_load_value_from_load_percent(load_percent=stream_details['expected_load_percent'],
                                                                       max_egress_load=max_egress_load)
                fun_test.simple_assert(expected_load_value, "Ensure expected load value is calculated")

                current_streamblock_handle = \
                    self.testcase_streamblocks[str(port)][current_dscp]['streamblock_obj'].spirent_handle
                rx_l1_bit_rate = convert_bps_to_mbps(int(output[current_streamblock_handle]['rx_summary_result']['L1BitRate']))

                result_dict[current_dscp] = {}
                result_dict[current_dscp]['actual'] = rx_l1_bit_rate
                result_dict[current_dscp]['expected'] = expected_load_value
        self.validate_stats(result_dict)

    def validate_stats(self, result_dict):
        for dscp, values in result_dict.iteritems():
            load_check = verify_load_output(actual_value=values['actual'],
                                            expected_value=values['expected'])
            fun_test.test_assert(load_check, "Ensure pir rate %s is seen for dscp %s. Actual seen %s" %
                                 (values['expected'], dscp, values['actual']))


class Pir_Q1(Pir_Q0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    pir_stream_dscp = 1
    other_stream_dscp = 2

    def describe(self):
        self.set_test_details(id=2,
                              summary="Test shaper pir for queue 1",
                              steps="""
                              1. Create stream with dscp 1 on port 1
                              2. Configure pir for Q1
                              3. Start traffic having load greater than configured pir rate
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Verify bandwidth is such that it is restricted to pir rate assigned
                              """)


class Pir_Q2(Pir_Q0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    pir_stream_dscp = 2
    other_stream_dscp = 3

    def describe(self):
        self.set_test_details(id=3,
                              summary="Test shaper pir for queue 2",
                              steps="""
                              1. Create stream with dscp 2 on port 1
                              2. Configure pir for Q2
                              3. Start traffic having load greater than configured pir rate
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Verify bandwidth is such that it is restricted to pir rate assigned
                              """)


class Pir_Q3(Pir_Q0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    pir_stream_dscp = 3
    other_stream_dscp = 4

    def describe(self):
        self.set_test_details(id=4,
                              summary="Test shaper pir for queue 3",
                              steps="""
                              1. Create stream with dscp 3 on port 1
                              2. Configure pir for Q3
                              3. Start traffic having load greater than configured pir rate
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Verify bandwidth is such that it is restricted to pir rate assigned
                              """)


class Pir_Q4(Pir_Q0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    pir_stream_dscp = 4
    other_stream_dscp = 5

    def describe(self):
        self.set_test_details(id=5,
                              summary="Test shaper pir for queue 4",
                              steps="""
                              1. Create stream with dscp 4 on port 1
                              2. Configure pir for Q4
                              3. Start traffic having load greater than configured pir rate
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Verify bandwidth is such that it is restricted to pir rate assigned
                              """)


class Pir_Q5(Pir_Q0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    pir_stream_dscp = 5
    other_stream_dscp = 6

    def describe(self):
        self.set_test_details(id=6,
                              summary="Test shaper pir for queue 5",
                              steps="""
                              1. Create stream with dscp 5 on port 1
                              2. Configure pir for Q5
                              3. Start traffic having load greater than configured pir rate
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Verify bandwidth is such that it is restricted to pir rate assigned
                              """)


class Pir_Q6(Pir_Q0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    pir_stream_dscp = 6
    other_stream_dscp = 7

    def describe(self):
        self.set_test_details(id=7,
                              summary="Test shaper pir for queue 6",
                              steps="""
                              1. Create stream with dscp 6 on port 1
                              2. Configure pir for Q6
                              3. Start traffic having load greater than configured pir rate
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Verify bandwidth is such that it is restricted to pir rate assigned
                              """)


class Pir_Q7(Pir_Q0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    pir_stream_dscp = 7
    other_stream_dscp = 8

    def describe(self):
        self.set_test_details(id=8,
                              summary="Test shaper pir for queue 7",
                              steps="""
                              1. Create stream with dscp 7 on port 1
                              2. Configure pir for Q7
                              3. Start traffic having load greater than configured pir rate
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Verify bandwidth is such that it is restricted to pir rate assigned
                              """)


class Pir_Q8(Pir_Q0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    pir_stream_dscp = 8
    other_stream_dscp = 9

    def describe(self):
        self.set_test_details(id=9,
                              summary="Test shaper pir for queue 8",
                              steps="""
                              1. Create stream with dscp 8 on port 1
                              2. Configure pir for Q8
                              3. Start traffic having load greater than configured pir rate
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Verify bandwidth is such that it is restricted to pir rate assigned
                              """)


class Pir_Q9(Pir_Q0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    pir_stream_dscp = 9
    other_stream_dscp = 10

    def describe(self):
        self.set_test_details(id=10,
                              summary="Test shaper pir for queue 9",
                              steps="""
                              1. Create stream with dscp 9 on port 1
                              9. Configure pir for Q2
                              3. Start traffic having load greater than configured pir rate
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Verify bandwidth is such that it is restricted to pir rate assigned
                              """)


class Pir_Q10(Pir_Q0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    pir_stream_dscp = 10
    other_stream_dscp = 11

    def describe(self):
        self.set_test_details(id=11,
                              summary="Test shaper pir for queue 10",
                              steps="""
                              1. Create stream with dscp 10 on port 1
                              2. Configure pir for Q10
                              3. Start traffic having load greater than configured pir rate
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Verify bandwidth is such that it is restricted to pir rate assigned
                              """)


class Pir_Q11(Pir_Q0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    pir_stream_dscp = 11
    other_stream_dscp = 12

    def describe(self):
        self.set_test_details(id=12,
                              summary="Test shaper pir for queue 11",
                              steps="""
                              1. Create stream with dscp 11 on port 1
                              2. Configure pir for Q11
                              3. Start traffic having load greater than configured pir rate
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Verify bandwidth is such that it is restricted to pir rate assigned
                              """)


class Pir_Q12(Pir_Q0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    pir_stream_dscp = 12
    other_stream_dscp = 13

    def describe(self):
        self.set_test_details(id=13,
                              summary="Test shaper pir for queue 12",
                              steps="""
                              1. Create stream with dscp 12 on port 1
                              2. Configure pir for Q12
                              3. Start traffic having load greater than configured pir rate
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Verify bandwidth is such that it is restricted to pir rate assigned
                              """)


class Pir_Q13(Pir_Q0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    pir_stream_dscp = 13
    other_stream_dscp = 14

    def describe(self):
        self.set_test_details(id=14,
                              summary="Test shaper pir for queue 13",
                              steps="""
                              1. Create stream with dscp 13 on port 1
                              2. Configure pir for Q13
                              3. Start traffic having load greater than configured pir rate
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Verify bandwidth is such that it is restricted to pir rate assigned
                              """)


class Pir_Q14(Pir_Q0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    pir_stream_dscp = 14
    other_stream_dscp = 15

    def describe(self):
        self.set_test_details(id=15,
                              summary="Test shaper pir for queue 14",
                              steps="""
                              1. Create stream with dscp 14 on port 1
                              2. Configure pir for Q14
                              3. Start traffic having load greater than configured pir rate
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Verify bandwidth is such that it is restricted to pir rate assigned
                              """)


class Pir_Q15(Pir_Q0):
    testcase_streamblocks = {}
    streamblock_handles_list = []
    pir_stream_dscp = 15
    other_stream_dscp = 4

    def describe(self):
        self.set_test_details(id=16,
                              summary="Test shaper pir for queue 15",
                              steps="""
                              1. Create stream with dscp 15 on port 1
                              2. Configure pir for Q15
                              3. Start traffic having load greater than configured pir rate
                              4. After 10 seconds, get RxL1BitRate from spirent for each stream
                              5. Verify bandwidth is such that it is restricted to pir rate assigned
                              """)


if __name__ == "__main__":
    ts = SpirentSetup()
    ts.add_test_case(Pir_Q0())
    ts.add_test_case(Pir_Q1())
    ts.add_test_case(Pir_Q2())
    ts.add_test_case(Pir_Q3())
    ts.add_test_case(Pir_Q4())
    ts.add_test_case(Pir_Q5())
    ts.add_test_case(Pir_Q6())
    ts.add_test_case(Pir_Q7())
    ts.add_test_case(Pir_Q8())
    ts.add_test_case(Pir_Q9())
    ts.add_test_case(Pir_Q10())
    ts.add_test_case(Pir_Q11())
    ts.add_test_case(Pir_Q12())
    ts.add_test_case(Pir_Q13())
    ts.add_test_case(Pir_Q14())
    ts.add_test_case(Pir_Q15())
    ts.run()