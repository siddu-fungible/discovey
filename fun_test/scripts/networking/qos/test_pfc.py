from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, GeneratorConfig, Capture
from lib.host.network_controller import  NetworkController
from scripts.networking.helper import *
from lib.utilities.pcap_parser import PcapParser
from scripts.networking.nu_config_manager import nu_config_obj

num_ports = 2
streamblock_objs = {}
generator_config_objs = {}
generator_dict = {}


def verify_spirent_stats(result_dict):
    for stream_key in result_dict.iterkeys():
            fun_test.test_assert_expected(expected=result_dict[stream_key]['tx_result']['FrameCount'],
                                          actual=result_dict[stream_key]['rx_result']['FrameCount'],
                                          message="Check results for %s" % stream_key)
    result = True
    return result


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
            dut_port_1, shape, hnu
        dut_type = fun_test.get_local_setting(setting="dut_type")
        dut_config = nu_config_obj.read_dut_config(dut_type=dut_type, flow_direction=flow_direction)

        shape = 0
        hnu = False
        if flow_direction == nu_config_obj.FLOW_DIRECTION_HNU_HNU:
            shape = 1
            hnu = True

        chassis_type = fun_test.get_local_setting(setting="chassis_type")
        spirent_config = nu_config_obj.read_traffic_generator_config()

        good_stream_load = 250
        pfc_load = 10
        fun_test.log("Creating Template object")
        template_obj = SpirentEthernetTrafficTemplate(session_name="test_pfc", chassis_type=chassis_type,
                                                      spirent_config=spirent_config)
        fun_test.test_assert(template_obj, "Create template object")

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

        source_mac1 = spirent_config['l2_config']['source_mac']
        destination_mac1 = spirent_config['l2_config']['destination_mac']
        destination_ip1 = spirent_config['l3_config']['ipv4']['destination_ip1']
        if hnu:
            destination_ip1 = spirent_config['l3_config']['ipv4']['hnu_destination_ip1']
        dut_port_1 = dut_config['ports'][0]
        dut_port_2 = dut_config['ports'][1]
        source_ip1 = spirent_config['l3_config']['ipv4']['source_ip1']
        gateway = spirent_config['l3_config']['ipv4']['gateway']

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

        # Applying configuration
        apply = template_obj.stc_manager.apply_configuration()
        fun_test.test_assert(apply, "Applying Generator config")

        # Create good stream on port 1
        create_streamblock_1 = StreamBlock(load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND, load=good_stream_load,
                                           fill_type=StreamBlock.FILL_TYPE_PRBS)
        streamblock_1 = template_obj.configure_stream_block(create_streamblock_1, port_handle=port_1)
        fun_test.test_assert(streamblock_1, " Creating streamblock on port %s" % port_1)

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=create_streamblock_1.spirent_handle,
                                                               destination_mac=destination_mac1, source_mac=source_mac1)
        fun_test.test_assert(ether, "Adding source and destination mac")

        # Adding Ip address and gateway
        ip = template_obj.stc_manager.configure_ip_address(streamblock=create_streamblock_1.spirent_handle,
                                                           destination=destination_ip1, source=source_ip1,
                                                           gateway=gateway)
        fun_test.test_assert(ip, "Adding source ip, dest ip and gateway")

        # Create stream on port 2
        create_streamblock_2 = StreamBlock(load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND, load=pfc_load,
                                           fixed_frame_length=64, insert_signature=False)
        streamblock_2 = template_obj.configure_stream_block(create_streamblock_2, port_handle=port_2)
        fun_test.test_assert(streamblock_2, message="Creating streamblock on port %s" % port_2)

        # Configure pfc frame on stream 2
        ls_octet = '00000001'
        out = template_obj.configure_priority_flow_control_header(create_streamblock_2,
                                                                  class_enable_vector=True, ls_octet=ls_octet)
        fun_test.test_assert(out['result'], message="Added frame stack")

        mac_header = out['ethernet8023_mac_control_header_obj']
        pfc_frame = out['pfc_header_obj']

        streamblock_objs['good_stream_obj'] = create_streamblock_1
        streamblock_objs['pfc_stream_obj'] = create_streamblock_2

        # Subscribe to results
        project = template_obj.stc_manager.get_project_handle()
        subscribe_results = template_obj.subscribe_to_all_results(parent=project)
        fun_test.test_assert(subscribe_results['result'], "Subscribing to results")
        del subscribe_results['result']

    def cleanup(self):
        # Cleanup spirent session
        template_obj.cleanup()
        disable_1 = network_controller_obj.disable_priority_flow_control(dut_port_1, shape=shape)
        fun_test.test_assert(disable_1, "Disable pfc on port %s" % dut_port_1)
        disable_2 = network_controller_obj.disable_priority_flow_control(dut_port_2, shape=shape)
        fun_test.test_assert(disable_2, "Disable pfc on port %s" % dut_port_2)


class TestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Test DUT with pfc disabled on DUT egress with quanta 5000 for priority 0",
                              steps="""
                        1. Disable pfc on both ports of DUT
                        2. Start traffic of good frame from port 1 of spirent.
                        3. Send pfc frames from port 2 of spirent with quanta 5000 for priority 0
                        4. Traffic from port 1 must not be stopped as pfc is disabled on DUT egress.
                        5. Verify stats on spirent:
                           a. Tx counter of good stream does not stop
                           b. Rx counter of good stream does not stop
                           c. Tx counter of pfc frame increases
                        6. Verify stats on DUT.
                           a. Tx counter of good stream does not stop.
                           b. Rx counter of good stream does not stop.
                        """)

    def setup(self):
        disable_1 = network_controller_obj.disable_priority_flow_control(dut_port_1, shape=shape)
        fun_test.test_assert(disable_1, "Disable pfc on port %s" % dut_port_1)
        disable_2 = network_controller_obj.disable_priority_flow_control(dut_port_2, shape=shape)
        fun_test.test_assert(disable_2, "Disable pfc on port %s" % dut_port_2)

        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1, shape=shape)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2, shape=shape)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

    def cleanup(self):
        # Stop generator traffic on ports
        stop = template_obj.disable_generator_configs(generator_configs=generator_dict[port_1])
        fun_test.test_assert(stop, "Stopping generator config on port %s" % port_1)

        # Stop traffic from port 1
        stop = template_obj.disable_generator_configs(generator_configs=generator_dict[port_2])
        fun_test.test_assert(stop, "Stopping generator config on port %s" % port_2)

        # Clear all subscribed results
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        sleep_time = 5
        check_intervals = 3
        good_stream_obj = streamblock_objs['good_stream_obj']
        good_stream_handle = good_stream_obj.spirent_handle
        pfc_stream_obj = streamblock_objs['pfc_stream_obj']
        pfc_stream_handle = pfc_stream_obj.spirent_handle

        pfc_frame.time0 = '5000'
        modify_pfc = template_obj.stc_manager.configure_frame_stack(stream_block_handle=pfc_stream_obj.spirent_handle,
                                                                    header_obj=pfc_frame, update=True)
        fun_test.test_assert(modify_pfc, "Change quanta value of priority 0 to %s" % pfc_frame.time0)

        # Execute traffic from port 1
        start = template_obj.enable_generator_configs(generator_configs=generator_dict[port_1])
        fun_test.test_assert(start, "Starting generator config on port %s" % port_1)

        fun_test.sleep(message="Letting some good traffic from port %s" % port_1, seconds=sleep_time)

        # Enable pfc from port 2
        start = template_obj.enable_generator_configs(generator_configs=generator_dict[port_2])
        fun_test.test_assert(start, "Starting generator config on port %s" % port_2)

        fun_test.sleep("Letting pfc frames to be sent", seconds=sleep_time)

        result_dict = {}
        for i in range(check_intervals):
            fun_test.sleep("Letting traffic to be executed", seconds=sleep_time)
            if i == 0:
                old_good_stream_spirent_tx_counter = 0
                old_good_stream_spirent_rx_counter = 0
                old_dut_port_1_good_receive = 0
                old_dut_port_2_good_transmit = 0
                old_pfc_stream_spirent_tx_counter = 0
            else:
                old_good_stream_spirent_tx_counter = result_dict[good_stream_handle]['tx_result']['FrameCount']
                old_good_stream_spirent_rx_counter = result_dict[good_stream_handle]['rx_result']['FrameCount']
                old_dut_port_1_good_receive = dut_port_1_good_receive
                old_dut_port_2_good_transmit = dut_port_2_good_transmit
                old_pfc_stream_spirent_tx_counter = result_dict[pfc_stream_handle]['tx_result']['FrameCount']

            # Fetch results for streamblocks
            result_dict = template_obj.stc_manager.fetch_streamblock_results(subscribe_result=subscribe_results,
                                                                             streamblock_handle_list=[good_stream_handle,
                                                                                                      pfc_stream_handle],
                                                                             tx_result=True, rx_result=True)
            fun_test.log("Value of transmit for good frame are:- Old: %s ; New: %s" %
                         (old_good_stream_spirent_tx_counter,
                          result_dict[good_stream_handle]['tx_result']['FrameCount']))
            fun_test.log("Value of receive for good frame are:- Old: %s ; New: %s" %
                         (old_good_stream_spirent_rx_counter,
                          result_dict[good_stream_handle]['rx_result']['FrameCount']))
            fun_test.log("Old value of transmit for pfc frame are:- Old: %s ; New: %s" %
                         (old_pfc_stream_spirent_tx_counter,
                          result_dict[pfc_stream_handle]['tx_result']['FrameCount']))

            fun_test.test_assert(int(result_dict[good_stream_handle]['tx_result']['FrameCount']) >
                                 int(old_good_stream_spirent_tx_counter),
                                 message="Ensure tx counter for %s stream has not been stopped" % good_stream_handle)

            fun_test.test_assert(int(result_dict[good_stream_handle]['rx_result']['FrameCount']) >
                                 int(old_good_stream_spirent_rx_counter),
                                 message="Ensure rx counter for %s stream has not been stopped" % good_stream_handle)

            fun_test.test_assert(int(result_dict[pfc_stream_handle]['tx_result']['FrameCount']) >
                                 int(old_pfc_stream_spirent_tx_counter),
                                 message="Ensure pfc frames are being sent via spirent")

            # Fetch results from dut
            dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1, hnu=hnu)
            dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2, hnu=hnu)

            dut_port_1_good_receive = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)
            dut_port_2_good_transmit = get_dut_output_stats_value(dut_port_2_results, FRAMES_TRANSMITTED_OK)

            fun_test.log("Value of transmit for good stream on dut are:- Old: %s ; New: %s" %
                         (old_dut_port_1_good_receive,
                          dut_port_1_good_receive))
            fun_test.log("Value of receive for good frame on dut are:- Old: %s ; New: %s" %
                         (old_dut_port_2_good_transmit,
                          dut_port_2_good_transmit))

            fun_test.test_assert(int(dut_port_1_good_receive) > int(old_dut_port_1_good_receive),
                                 message="Ensure rx counter for %s stream is not stopped on dut from port %s" %
                                         (good_stream_handle, dut_port_1))

            fun_test.test_assert(int(dut_port_2_good_transmit) > int(old_dut_port_2_good_transmit),
                                 message="Ensure tx counter for %s stream is not stopped on dut from port %s" %
                                         (good_stream_handle, dut_port_2))

        # Fetch results for port
        port_dict = template_obj.stc_manager.fetch_port_results(subscribe_result=subscribe_results,
                                                                port_handle_list=[port_1, port_2], analyzer_result=True)

        port_2_errors = template_obj.check_non_zero_error_count(port_dict[port_2]['analyzer_result'])
        port_1_errors = template_obj.check_non_zero_error_count(port_dict[port_1]['analyzer_result'])

        fun_test.test_assert(port_2_errors['result'],
                             message="Check error counters on port %s" % port_2)
        fun_test.test_assert(port_1_errors['result'],
                             message="Check error counters on port %s" % port_1)


class TestCase2(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Test DUT with pfc enabled on DUT egress with quanta 0 for priority 0",
                              steps="""
                        1. Enable pfc on egress port of DUT
                        2. Start traffic of good frame from port 1 of spirent.
                        3. Send pfc frames from port 2 of spirent with quanta 0 for priority 0
                        4. Traffic from port 1 must not be stopped as quanta is 0.
                        5. Verify stats on spirent:
                           a. Tx counter of good stream does not stop
                           b. Rx counter of good stream does not stop
                           c. Tx counter of pfc frame increases
                        6. Verify stats on DUT.
                           a. Tx counter of good stream does not stop.
                           b. Rx counter of good stream does not stop.
                        """)

    def setup(self):

        disable_1 = network_controller_obj.disable_priority_flow_control(dut_port_1, shape=shape)
        fun_test.test_assert(disable_1, "Disable pfc on port %s" % dut_port_1)

        # enable pfc on dut egress
        enable_1 = network_controller_obj.enable_priority_flow_control(dut_port_2, shape=shape)
        fun_test.test_assert(enable_1, "Enable pfc on port %s" % dut_port_2)

        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1, shape=shape)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2, shape=shape)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

    def cleanup(self):
        # Stop generator traffic on ports
        stop = template_obj.disable_generator_configs(generator_configs=generator_dict[port_1])
        fun_test.test_assert(stop, "Stopping generator config on port %s" % port_1)

        # Stop traffic from port 1
        stop = template_obj.disable_generator_configs(generator_configs=generator_dict[port_2])
        fun_test.test_assert(stop, "Stopping generator config on port %s" % port_2)

        # Clear all subscribed results
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        sleep_time = 5
        check_intervals = 3
        good_stream_obj = streamblock_objs['good_stream_obj']
        good_stream_handle = good_stream_obj.spirent_handle
        pfc_stream_obj = streamblock_objs['pfc_stream_obj']
        pfc_stream_handle = pfc_stream_obj.spirent_handle

        pfc_frame.time0 = '0'
        modify_pfc = template_obj.stc_manager.configure_frame_stack(stream_block_handle=pfc_stream_obj.spirent_handle,
                                                                    header_obj=pfc_frame, update=True)
        fun_test.test_assert(modify_pfc, "Change quanta value of priority 0 to %s" % pfc_frame.time0)

        # Execute traffic from port 1
        start = template_obj.enable_generator_configs(generator_configs=generator_dict[port_1])
        fun_test.test_assert(start, "Starting generator config on port %s" % port_1)

        fun_test.sleep(message="Letting some good traffic from port %s" % port_1, seconds=sleep_time)

        # Enable pfc from port 2
        start = template_obj.enable_generator_configs(generator_configs=generator_dict[port_2])
        fun_test.test_assert(start, "Starting generator config on port %s" % port_2)

        fun_test.sleep("Letting pfc frames to be sent", seconds=sleep_time)

        result_dict = {}
        for i in range(check_intervals):
            fun_test.sleep("Letting traffic to be executed", seconds=sleep_time)
            if i == 0:
                old_good_stream_spirent_tx_counter = 0
                old_good_stream_spirent_rx_counter = 0
                old_dut_port_1_good_receive = 0
                old_dut_port_2_good_transmit = 0
                old_pfc_stream_spirent_tx_counter = 0
            else:
                old_good_stream_spirent_tx_counter = result_dict[good_stream_handle]['tx_result']['FrameCount']
                old_good_stream_spirent_rx_counter = result_dict[good_stream_handle]['rx_result']['FrameCount']
                old_dut_port_1_good_receive = dut_port_1_good_receive
                old_dut_port_2_good_transmit = dut_port_2_good_transmit
                old_pfc_stream_spirent_tx_counter = result_dict[pfc_stream_handle]['tx_result']['FrameCount']

            # Fetch results for streamblocks
            result_dict = template_obj.stc_manager.fetch_streamblock_results(subscribe_result=subscribe_results,
                                                                             streamblock_handle_list=[
                                                                                 good_stream_handle,
                                                                                 pfc_stream_handle],
                                                                             tx_result=True, rx_result=True)
            fun_test.log("Value of transmit for good frame are:- Old: %s ; New: %s" %
                         (old_good_stream_spirent_tx_counter,
                          result_dict[good_stream_handle]['tx_result']['FrameCount']))
            fun_test.log("Value of receive for good frame are:- Old: %s ; New: %s" %
                         (old_good_stream_spirent_rx_counter,
                          result_dict[good_stream_handle]['rx_result']['FrameCount']))
            fun_test.log("Old value of transmit for pfc frame are:- Old: %s ; New: %s" %
                         (old_pfc_stream_spirent_tx_counter,
                          result_dict[pfc_stream_handle]['tx_result']['FrameCount']))

            fun_test.test_assert(int(result_dict[good_stream_handle]['tx_result']['FrameCount']) >
                                 int(old_good_stream_spirent_tx_counter),
                                 message="Ensure tx counter for %s stream has not been stopped" % good_stream_handle)

            fun_test.test_assert(int(result_dict[good_stream_handle]['rx_result']['FrameCount']) >
                                 int(old_good_stream_spirent_rx_counter),
                                 message="Ensure rx counter for %s stream has not been stopped" % good_stream_handle)

            fun_test.test_assert(int(result_dict[pfc_stream_handle]['tx_result']['FrameCount']) >
                                 int(old_pfc_stream_spirent_tx_counter),
                                 message="Ensure pfc frames are being sent via spirent")

            # Fetch results from dut

            dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1, hnu=hnu)
            dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2, hnu=hnu)

            dut_port_1_good_receive = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)
            dut_port_2_good_transmit = get_dut_output_stats_value(dut_port_2_results, FRAMES_TRANSMITTED_OK)

            fun_test.log("Value of transmit for good stream on dut are:- Old: %s ; New: %s" %
                         (old_dut_port_1_good_receive,
                          dut_port_1_good_receive))
            fun_test.log("Value of receive for good frame on dut are:- Old: %s ; New: %s" %
                         (old_dut_port_2_good_transmit,
                          dut_port_2_good_transmit))

            fun_test.test_assert(int(dut_port_1_good_receive) > int(old_dut_port_1_good_receive),
                                 message="Ensure rx counter for %s stream is not stopped on dut from port %s" %
                                         (good_stream_handle, dut_port_1))

            fun_test.test_assert(int(dut_port_2_good_transmit) > int(old_dut_port_2_good_transmit),
                                 message="Ensure tx counter for %s stream is not stopped on dut from port %s" %
                                         (good_stream_handle, dut_port_2))

        # Fetch results for port
        port_dict = template_obj.stc_manager.fetch_port_results(subscribe_result=subscribe_results,
                                                                port_handle_list=[port_1, port_2], analyzer_result=True)

        port_2_errors = template_obj.check_non_zero_error_count(port_dict[port_2]['analyzer_result'])
        port_1_errors = template_obj.check_non_zero_error_count(port_dict[port_1]['analyzer_result'])

        fun_test.test_assert(port_2_errors['result'],
                             message="Check error counters on port %s" % port_2)
        fun_test.test_assert(port_1_errors['result'],
                             message="Check error counters on port %s" % port_1)


class TestCase3(FunTestCase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Test DUT with pfc enabled on DUT egress with quanta 65535 for priority 0",
                              steps="""
                        1. Enable pfc on egress port of DUT
                        2. Start traffic of good frame from port 1 of spirent.
                        3. Send pfc frames from port 2 of spirent with quanta 65535 for priority 0
                        4. Traffic from port 1 must be stopped as quanta is 65535.
                        5. Verify stats on spirent:
                           a. Tx counter of good stream does not stop
                           b. Rx counter of good stream stops
                           c. Tx counter of pfc frame increases
                        6. Verify stats on DUT.
                           a. Tx counter of good stream does not stop.
                           b. Rx counter of good stream stops.
                           c. Tx counter of pause frame increases
                        """)

    def setup(self):

        disable_1 = network_controller_obj.disable_priority_flow_control(dut_port_1, shape=shape)
        fun_test.test_assert(disable_1, "Disable pfc on port %s" % dut_port_1)

        # enable pfc on dut egress
        enable_1 = network_controller_obj.enable_priority_flow_control(dut_port_2, shape=shape)
        fun_test.test_assert(enable_1, "Enable pfc on port %s" % dut_port_2)

        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1, shape=shape)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2, shape=shape)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

    def cleanup(self):
        # Stop generator traffic on ports
        stop = template_obj.disable_generator_configs(generator_configs=generator_dict[port_1])
        fun_test.test_assert(stop, "Stopping generator config on port %s" % port_1)

        # Stop traffic from port 1
        stop = template_obj.disable_generator_configs(generator_configs=generator_dict[port_2])
        fun_test.test_assert(stop, "Stopping generator config on port %s" % port_2)

        # Clear all subscribed results
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        sleep_time = 5
        check_intervals = 3
        good_stream_obj = streamblock_objs['good_stream_obj']
        good_stream_handle = good_stream_obj.spirent_handle
        pfc_stream_obj = streamblock_objs['pfc_stream_obj']
        pfc_stream_handle = pfc_stream_obj.spirent_handle

        pfc_frame.time0 = '65535'
        modify_pfc = template_obj.stc_manager.configure_frame_stack(stream_block_handle=pfc_stream_obj.spirent_handle,
                                                                    header_obj=pfc_frame, update=True)
        fun_test.test_assert(modify_pfc, "Change quanta value of priority 0 to %s" % pfc_frame.time0)

        # Execute traffic from port 1
        start = template_obj.enable_generator_configs(generator_configs=generator_dict[port_1])
        fun_test.test_assert(start, "Starting generator config on port %s" % port_1)

        fun_test.sleep(message="Letting some good traffic from port %s" % port_1, seconds=sleep_time)

        # Enable pfc from port 2
        start = template_obj.enable_generator_configs(generator_configs=generator_dict[port_2])
        fun_test.test_assert(start, "Starting generator config on port %s" % port_2)

        fun_test.sleep("Letting pfc frames to be sent", seconds=sleep_time)

        for i in range(check_intervals + 1):
            fun_test.sleep("Letting traffic to be executed", seconds=sleep_time)

            # Fetch results for streamblocks from spirent
            result_dict = template_obj.stc_manager.fetch_streamblock_results(subscribe_result=subscribe_results,
                                                                             streamblock_handle_list=[
                                                                                 good_stream_handle,
                                                                                 pfc_stream_handle],
                                                                             tx_result=True, rx_result=True)

            new_good_stream_spirent_tx_counter = result_dict[good_stream_handle]['tx_result']['FrameCount']
            new_good_stream_spirent_rx_counter = result_dict[good_stream_handle]['rx_result']['FrameCount']
            new_pfc_stream_spirent_tx_counter = result_dict[pfc_stream_handle]['tx_result']['FrameCount']

            # Fetch results from dut
            dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1, hnu=hnu)
            dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2, hnu=hnu)

            dut_port_1_good_receive = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)
            dut_port_2_good_transmit = get_dut_output_stats_value(dut_port_2_results, FRAMES_TRANSMITTED_OK)
            dut_port_2_pause_receive = get_dut_output_stats_value(dut_port_2_results, CBFC_PAUSE_FRAMES_RECEIVED,
                                                                  tx=False, class_value=CLASS_0)

            if i == 0:
                # Fetch counter values
                pass
            else:
                fun_test.log("Values of tx for good stream on spirent are:- Old: %s ; New: %s" %
                             (old_good_stream_spirent_tx_counter, new_good_stream_spirent_tx_counter))
                fun_test.log("Values of rx for good stream on spirent are:- Old: %s ; New: %s" %
                             (old_good_stream_spirent_rx_counter, new_good_stream_spirent_rx_counter))
                fun_test.log("Values of tx for pfc stream on spirent are:- Old: %s ; New: %s" %
                             (old_pfc_stream_spirent_tx_counter, new_pfc_stream_spirent_tx_counter))

                fun_test.log("Values of tx for good stream on dut are:- Old: %s ; New: %s" %
                             (old_dut_port_1_good_receive, dut_port_1_good_receive))
                fun_test.log("Values of rx for good stream on spirent are:- Old: %s ; New: %s" %
                             (old_dut_port_2_good_transmit, dut_port_2_good_transmit))
                fun_test.log("Values of tx for pfc stream on spirent are:- Old: %s ; New: %s" %
                             (old_dut_port_2_pause_receive, dut_port_2_pause_receive))

                fun_test.test_assert(int(new_good_stream_spirent_tx_counter) >
                                     int(old_good_stream_spirent_tx_counter),
                                     message="Ensure tx counter for %s stream has not been stopped" %
                                             good_stream_handle)

                fun_test.test_assert_expected(expected=int(new_good_stream_spirent_rx_counter),
                                              actual=int(old_good_stream_spirent_rx_counter),
                                              message="Ensure rx counter for %s stream has  been stopped" %
                                                      good_stream_handle)

                fun_test.test_assert(int(new_pfc_stream_spirent_tx_counter) >
                                     int(old_pfc_stream_spirent_tx_counter),
                                     message="Ensure tx counter for %s stream has not been stopped" %
                                             pfc_stream_handle)

                fun_test.test_assert(int(dut_port_1_good_receive) > int(old_dut_port_1_good_receive),
                                     message="Ensure tx counter for %s stream is not stopped on dut" %
                                             good_stream_handle)

                fun_test.test_assert_expected(expected=int(dut_port_2_good_transmit),
                                              actual=int(old_dut_port_2_good_transmit),
                                              message="Ensure rx counter for %s stream is stopped on dut" %
                                                      good_stream_handle)

                fun_test.test_assert(int(dut_port_2_pause_receive) > int(old_dut_port_2_pause_receive),
                                     message="Ensure tx counter for %s stream is not stopped on dut" %
                                             good_stream_handle)

            old_good_stream_spirent_tx_counter = new_good_stream_spirent_tx_counter
            old_good_stream_spirent_rx_counter = new_good_stream_spirent_rx_counter
            old_pfc_stream_spirent_tx_counter = new_pfc_stream_spirent_tx_counter
            old_dut_port_1_good_receive = dut_port_1_good_receive
            old_dut_port_2_good_transmit = dut_port_2_good_transmit
            old_dut_port_2_pause_receive = dut_port_2_pause_receive

        # Fetch results for port
        port_dict = template_obj.stc_manager.fetch_port_results(subscribe_result=subscribe_results,
                                                                port_handle_list=[port_1, port_2], analyzer_result=True)

        port_2_errors = template_obj.check_non_zero_error_count(port_dict[port_2]['analyzer_result'])
        port_1_errors = template_obj.check_non_zero_error_count(port_dict[port_1]['analyzer_result'])

        fun_test.test_assert(port_2_errors['result'],
                             message="Check error counters on port %s" % port_2)
        fun_test.test_assert(port_1_errors['result'],
                             message="Check error counters on port %s" % port_1)


class TestCase4(FunTestCase):
    queue_num = '00'
    pcap_file_path = None
    pcap_file_path_1 = None
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
        self.set_test_details(id=4,
                              summary="Test DUT with pfc enabled on both DUT ports with quanta 52428 for priority 0",
                              steps="""
                        1. Enable pfc on both port of DUT
                        2. Start traffic of good frame from port 1 of spirent.
                        3. Send pfc frames from port 2 of spirent with quanta 52428 for priority 0
                        4. Traffic from port 1 must be stopped as quanta is 52428.
                        5. Verify stats on spirent:
                           a. Tx counter of good stream stops
                           b. Rx counter of good stream stops
                           c. Tx counter of pfc frame increases
                           d. Rx counter of pfc frame increases
                        6. Verify stats on DUT.
                           a. Tx counter of good stream stops.
                           b. Rx counter of good stream stops.
                           c. Counter of pause frame increases on incoming port
                           d. Counter of pause frame increases on outgoing port
                        7. Start capture on dut port1
                        8. Check that rx has started for streams coming from port1 as pfc frames are stopped.
                        9. Check pg queue dequeue has started.
                        10. Check q dequeue has started
                        11. Check pg enqueue and pg dequeue continues to happen
                        12. Stop pfc traffic from port2 and stop capture on port1 after some time
                        13. Check quanta value of first packet in capture is set to quanta set on dut port
                        14. Check quanta value is 0 for last pfc packet sent from dut_port to spirent
                        """)

    def setup(self):
        set_qos_ingress = network_controller_obj.set_qos_ingress_priority_group(port_num=dut_port_1,
                                                                                priority_group_num=self.pg,
                                                                                min_threshold=self.min_thr,
                                                                                shared_threshold=self.shr_thr,
                                                                                headroom_threshold=self.hdr_thr,
                                                                                xoff_enable=self.xoff_enable,
                                                                                shared_xon_threshold=self.shared_xon_thr,
                                                                                hnu=hnu)
        fun_test.test_assert(set_qos_ingress, "Setting qos ingress priority group")

        pfc_enable = network_controller_obj.enable_qos_pfc(hnu=hnu)
        fun_test.test_assert(pfc_enable, "Ensure qos pfc is enabled")

        enable_1 = network_controller_obj.enable_priority_flow_control(dut_port_1, shape=shape)
        fun_test.test_assert(enable_1, "Disable pfc on port %s" % dut_port_1)

        port_quanta = network_controller_obj.set_priority_flow_control_quanta(port_num=dut_port_1, quanta=self.quanta,
                                                                              class_num=self.class_val, shape=shape)
        fun_test.test_assert(port_quanta, "Ensure quanta %s is set on port %s" % (self.quanta, dut_port_1))

        port_thr = network_controller_obj.set_priority_flow_control_threshold(port_num=dut_port_1, threshold=self.threshold,
                                                                              class_num=self.class_val, shape=shape)
        fun_test.test_assert(port_thr, "Ensure threshold %s is set on port %s" % (port_thr, dut_port_1))

        # enable pfc on dut egress
        enable_2 = network_controller_obj.enable_priority_flow_control(dut_port_2, shape=shape)
        fun_test.test_assert(enable_2, "Enable pfc on port %s" % dut_port_2)

        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1, shape=shape)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2, shape=shape)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

    def cleanup(self):
        # Stop generator traffic on ports
        stop = template_obj.disable_generator_configs(generator_configs=generator_dict[port_1])
        fun_test.test_assert(stop, "Stopping generator config on port %s" % port_1)

        # Stop traffic from port 1
        stop = template_obj.disable_generator_configs(generator_configs=generator_dict[port_2])
        fun_test.test_assert(stop, "Stopping generator config on port %s" % port_2)

        # Clear all subscribed results
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

        if self.pcap_file_path:
            fun_test.remove_file(self.pcap_file_path)
            fun_test.log("Removed file %s from local system" % self.pcap_file_path)

        if self.pcap_file_path_1:
            fun_test.remove_file(self.pcap_file_path_1)
            fun_test.log("Removed file %s from local system" % self.pcap_file_path_1)

    def run(self):
        final_quanta_value = 0
        sleep_time = 5
        check_intervals = 3
        good_stream_obj = streamblock_objs['good_stream_obj']
        good_stream_handle = good_stream_obj.spirent_handle
        pfc_stream_obj = streamblock_objs['pfc_stream_obj']
        pfc_stream_handle = pfc_stream_obj.spirent_handle

        pfc_frame.time0 = '52428'
        modify_pfc = template_obj.stc_manager.configure_frame_stack(stream_block_handle=pfc_stream_obj.spirent_handle,
                                                                    header_obj=pfc_frame, update=True)
        fun_test.test_assert(modify_pfc, "Change quanta value of priority 0 to %s" % pfc_frame.time0)

        # Execute traffic from port 1
        start = template_obj.enable_generator_configs(generator_configs=generator_dict[port_1])
        fun_test.test_assert(start, "Starting generator config on port %s" % port_1)

        fun_test.sleep(message="Letting some good traffic from port %s" % port_1, seconds=sleep_time)

        # Enable pfc from port 2
        start = template_obj.enable_generator_configs(generator_configs=generator_dict[port_2])
        fun_test.test_assert(start, "Starting generator config on port %s" % port_2)

        fun_test.sleep("Letting pfc frames to be sent", seconds=30)

        for i in range(check_intervals):
            fun_test.sleep("Letting traffic to be executed", seconds=sleep_time)

            # Fetch results for streamblocks from spirent
            result_dict = template_obj.stc_manager.fetch_streamblock_results(subscribe_result=subscribe_results,
                                                                             streamblock_handle_list=[
                                                                                 good_stream_handle,
                                                                                 pfc_stream_handle],
                                                                             tx_result=True, rx_result=True)

            port_dict = template_obj.stc_manager.fetch_port_results(subscribe_result=subscribe_results,
                                                                    port_handle_list=[port_1], analyzer_result=True)

            new_good_stream_spirent_tx_counter = result_dict[good_stream_handle]['tx_result']['FrameCount']
            new_good_stream_spirent_rx_counter = result_dict[good_stream_handle]['rx_result']['FrameCount']
            new_pfc_stream_spirent_tx_counter = result_dict[pfc_stream_handle]['tx_result']['FrameCount']
            new_pfc_stream_spirent_rx_counter = port_dict[port_1]['analyzer_result']['TotalFrameCount']

            # Fetch results from dut

            dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1, hnu=hnu)
            dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2, hnu=hnu)
            dut_port_1_psw_results = network_controller_obj.peek_psw_port_stats(dut_port_1, hnu=hnu, queue_num=self.queue_num)
            dut_port_2_psw_results = network_controller_obj.peek_psw_port_stats(dut_port_2, hnu=hnu, queue_num=self.queue_num)

            dut_port_1_good_receive = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)
            dut_port_2_good_transmit = get_dut_output_stats_value(dut_port_2_results, FRAMES_TRANSMITTED_OK)

            dut_port_2_pause_receive = get_dut_output_stats_value(dut_port_2_results, CBFC_PAUSE_FRAMES_RECEIVED,
                                                                  tx=False, class_value=CLASS_0)
            dut_port_1_pause_transmit = get_dut_output_stats_value(dut_port_1_results, CBFC_PAUSE_FRAMES_TRANSMITTED,
                                                                  tx=True, class_value=CLASS_0)
            dut_port_1_q00_pg_enqueue_pkts = dut_port_1_psw_results['count']['pg_enq']['pkts']
            dut_port_1_q00_pg_dequeue_pkts = dut_port_1_psw_results['count']['pg_deq']['pkts']
            dut_port_2_q00_q_enqueue_pkts = dut_port_2_psw_results['count']['q_enq']['pkts']
            dut_port_2_q00_q_dequeue_pkts = dut_port_2_psw_results['count']['q_deq']['pkts']

            if i == 0:
                # Fetch counter values
                pass
            else:
                fun_test.log("Values of tx for good stream on spirent are:- Old: %s ; New: %s" %
                             (old_good_stream_spirent_tx_counter, new_good_stream_spirent_tx_counter))
                fun_test.log("Values of rx for good stream on spirent are:- Old: %s ; New: %s" %
                             (old_good_stream_spirent_rx_counter, new_good_stream_spirent_rx_counter))
                fun_test.log("Values of tx for pfc stream on spirent are:- Old: %s ; New: %s" %
                             (old_pfc_stream_spirent_tx_counter, new_pfc_stream_spirent_tx_counter))
                fun_test.log("Values of rx for pfc stream on spirent are:- Old: %s ; New: %s" %
                             (old_pfc_stream_spirent_rx_counter, new_pfc_stream_spirent_rx_counter))

                fun_test.log("Values of tx for good stream on dut are:- Old: %s ; New: %s" %
                             (old_dut_port_1_good_receive, dut_port_1_good_receive))
                fun_test.log("Values of rx for good stream on spirent are:- Old: %s ; New: %s" %
                             (old_dut_port_2_good_transmit, dut_port_2_good_transmit))
                fun_test.log("Values of tx for pfc stream on spirent are:- Old: %s ; New: %s" %
                             (old_dut_port_2_pause_receive, dut_port_2_pause_receive))
                fun_test.log("Values of rx for pfc stream from dut to spirent are:- Old: %s ; New: %s" %
                             (old_dut_port_1_pause_transmit, dut_port_1_pause_transmit))
                fun_test.log("Values of enqueue in q00 of %s port of psw port stats are:- Old: %s ; New: %s" %
                             (dut_port_1, old_dut_port_1_psw_pg_enqueue_pkts, dut_port_1_q00_pg_enqueue_pkts))
                fun_test.log("Values of deque in q00 of %s port of psw port stats are:- Old: %s ; New: %s" %
                             (dut_port_1, old_dut_port_1_psw_pg_dequeue_pkts, dut_port_1_q00_pg_dequeue_pkts))
                fun_test.log("Values of q enque in q00 on %s port of psw port stats are:- Old: %s ; New: %s" %
                             (dut_port_2 ,old_dut_port_2_psw_q_enqueue_pkts, dut_port_2_q00_q_enqueue_pkts))
                fun_test.log("Values of q deque in q00 on %s port of psw port stats are:- Old: %s ; New: %s" %
                             (dut_port_2, old_dut_port_2_psw_q_dequeue_pkts, dut_port_2_q00_q_dequeue_pkts))

                fun_test.test_assert(int(new_good_stream_spirent_tx_counter) > int(old_good_stream_spirent_tx_counter),
                                     message="Ensure tx counter for %s stream has not stopped as its not "
                                             "enabled on spirent" %
                                             good_stream_handle)

                fun_test.test_assert_expected(expected=int(new_good_stream_spirent_rx_counter),
                                              actual=int(old_good_stream_spirent_rx_counter),
                                              message="Ensure rx counter for %s stream has been stopped" %
                                                      good_stream_handle)

                fun_test.test_assert(int(new_pfc_stream_spirent_tx_counter) >
                                     int(old_pfc_stream_spirent_tx_counter),
                                     message="Ensure tx counter for %s stream has not been stopped" %
                                             pfc_stream_handle)

                fun_test.test_assert(int(new_pfc_stream_spirent_rx_counter) >
                                     int(old_pfc_stream_spirent_rx_counter),
                                     message="Ensure tx counter for %s stream has not been stopped" %
                                             pfc_stream_handle)

                fun_test.test_assert(int(dut_port_1_good_receive) > int(old_dut_port_1_good_receive),
                                     message="Ensure tx counter for %s stream is not stopped on dut" %
                                             good_stream_handle)

                fun_test.test_assert_expected(expected=int(dut_port_2_good_transmit),
                                              actual=int(old_dut_port_2_good_transmit),
                                              message="Ensure rx counter for %s stream is stopped on dut" %
                                                      good_stream_handle)

                fun_test.test_assert(int(dut_port_2_pause_receive) > int(old_dut_port_2_pause_receive),
                                     message="Ensure tx counter for %s stream is not stopped on dut" %
                                             pfc_stream_handle)

                fun_test.test_assert(int(dut_port_1_pause_transmit) > int(old_dut_port_1_pause_transmit),
                                     message="Ensure tx of pfc from dut port %s is not stopped" %
                                             pfc_stream_handle)

                fun_test.test_assert(int(dut_port_1_q00_pg_enqueue_pkts) > int(old_dut_port_1_psw_pg_enqueue_pkts),
                                     "Ensure enqueue of packets is happening in q_00")

                fun_test.test_assert_expected(expected=int(old_dut_port_1_psw_pg_dequeue_pkts),
                                              actual=int(dut_port_1_q00_pg_dequeue_pkts),
                                              message="Ensure packets are not getting dequeued when pfc streams "
                                                      "are incoming")

                fun_test.test_assert(int(dut_port_2_q00_q_enqueue_pkts) > int(old_dut_port_2_psw_q_enqueue_pkts),
                                     message="Ensure enqueue of packets is happening in q_00")

                fun_test.test_assert_expected(expected=int(old_dut_port_2_psw_q_dequeue_pkts),
                                              actual=int(dut_port_2_q00_q_dequeue_pkts),
                                              message="Ensure packets are not getting dequeued when pfc streams "
                                                      "are incoming")

            old_good_stream_spirent_tx_counter = new_good_stream_spirent_tx_counter
            old_good_stream_spirent_rx_counter = new_good_stream_spirent_rx_counter
            old_pfc_stream_spirent_tx_counter = new_pfc_stream_spirent_tx_counter
            old_pfc_stream_spirent_rx_counter = new_pfc_stream_spirent_rx_counter
            old_dut_port_1_good_receive = dut_port_1_good_receive
            old_dut_port_2_good_transmit = dut_port_2_good_transmit
            old_dut_port_2_pause_receive = dut_port_2_pause_receive
            old_dut_port_1_pause_transmit = dut_port_1_pause_transmit
            old_dut_port_1_psw_pg_enqueue_pkts = dut_port_1_q00_pg_enqueue_pkts
            old_dut_port_1_psw_pg_dequeue_pkts = dut_port_1_q00_pg_dequeue_pkts
            old_dut_port_2_psw_q_enqueue_pkts = dut_port_2_q00_q_enqueue_pkts
            old_dut_port_2_psw_q_dequeue_pkts = dut_port_2_q00_q_dequeue_pkts

        # Fetch results for port
        port_dict = template_obj.stc_manager.fetch_port_results(subscribe_result=subscribe_results,
                                                                port_handle_list=[port_1, port_2], analyzer_result=True)

        port_2_errors = template_obj.check_non_zero_error_count(port_dict[port_2]['analyzer_result'])
        port_1_errors = template_obj.check_non_zero_error_count(port_dict[port_1]['analyzer_result'])

        fun_test.test_assert(port_2_errors['result'],
                             message="Check error counters on port %s" % port_2)
        fun_test.test_assert(port_1_errors['result'],
                             message="Check error counters on port %s" % port_1)

        fun_test.log("Start new capture on dut port %s to check once pfc is stopped it sends final packet "
                     "with quanta 0" % dut_port_1)
        capture_obj = Capture()
        start_capture = template_obj.stc_manager.start_capture_command(capture_obj=capture_obj, port_handle=port_1)
        fun_test.test_assert(start_capture, "Started capture for quanta 0 on port %s" % port_1)

        # Stop traffic from port 1
        stop = template_obj.disable_generator_configs(generator_configs=generator_dict[port_2])
        fun_test.test_assert(stop, "Stopping pfc on port %s" % port_2)

        fun_test.sleep("Letting pfc get stopped", seconds=sleep_time)

        # SPIRENT OUTPUT
        result = template_obj.stc_manager.fetch_streamblock_results(subscribe_result=subscribe_results,
                                                                         streamblock_handle_list=[
                                                                             good_stream_handle],
                                                                         tx_result=False, rx_result=True)
        current_spirent_good_stream_rx_counter = result[good_stream_handle]['rx_result']['FrameCount']

        # DUT STATS
        current_dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2, hnu=hnu)
        current_dut_port_1_psw_results = network_controller_obj.peek_psw_port_stats(dut_port_1, hnu=hnu, queue_num=self.queue_num)
        current_dut_port_2_psw_results = network_controller_obj.peek_psw_port_stats(dut_port_2, hnu=hnu, queue_num=self.queue_num)

        current_dut_port_2_good_transmit = get_dut_output_stats_value(current_dut_port_2_results, FRAMES_TRANSMITTED_OK)
        current_dut_port_1_q00_pg_enqueue_pkts = current_dut_port_1_psw_results['count']['pg_enq']['pkts']
        current_dut_port_1_q00_pg_dequeue_pkts = current_dut_port_1_psw_results['count']['pg_deq']['pkts']
        current_dut_port_2_q00_q_enqueue_pkts = current_dut_port_2_psw_results['count']['q_enq']['pkts']
        current_dut_port_2_q00_q_dequeue_pkts = current_dut_port_2_psw_results['count']['q_deq']['pkts']

        # Logging counter values
        fun_test.log("Values of spirent rx counter before and after stopping pfc are:- Before: %s ; After: %s"
                     % (new_good_stream_spirent_rx_counter, current_spirent_good_stream_rx_counter))
        fun_test.log("Values of tx from mac stats on port %s before and after stopping pfc are:- Before: %s ; "
                     "After: %s" % (dut_port_2, dut_port_2_good_transmit, current_dut_port_2_good_transmit))
        fun_test.log("Values of pg dequeue before and after stopping pfc are:- Before: %s ; After: %s" %
                     (dut_port_1_q00_pg_dequeue_pkts, current_dut_port_1_q00_pg_dequeue_pkts))
        fun_test.log("Values of pg enqueue before and after stopping pfc are:- Before: %s ; After: %s" %
                     (dut_port_1_q00_pg_enqueue_pkts, current_dut_port_1_q00_pg_enqueue_pkts))
        fun_test.log("Values of q enqueue before and after stopping pfc are:- Before: %s ; After: %s" %
                     (dut_port_2_q00_q_enqueue_pkts, current_dut_port_2_q00_q_enqueue_pkts))
        fun_test.log("Values of q dequeue before and after stopping pfc are:- Before: %s ; After: %s" %
                     (dut_port_2_q00_q_dequeue_pkts, current_dut_port_2_q00_q_dequeue_pkts))


        fun_test.test_assert(int(current_spirent_good_stream_rx_counter) > int(new_good_stream_spirent_rx_counter),
                             message="Ensure spirent has started to receive stopped frames")

        fun_test.test_assert(int(current_dut_port_2_good_transmit) > int(dut_port_2_good_transmit),
                             message="Ensure mac stats shows that tx from %s port has started" % dut_port_2)

        fun_test.test_assert(int(current_dut_port_1_q00_pg_dequeue_pkts) > int(dut_port_1_q00_pg_dequeue_pkts),
                             message="Ensure pg dequeue has started on port %s" % dut_port_1)

        fun_test.test_assert(int(current_dut_port_1_q00_pg_enqueue_pkts) > int(dut_port_1_q00_pg_enqueue_pkts),
                             message="Ensure pg enqueue continues to happen on port %s" % dut_port_1)

        fun_test.test_assert(int(current_dut_port_2_q00_q_enqueue_pkts) > int(dut_port_2_q00_q_enqueue_pkts),
                             message="Ensure q enqueue continues to happen on port %s" % dut_port_2)

        fun_test.test_assert(int(current_dut_port_2_q00_q_dequeue_pkts) > int(dut_port_2_q00_q_dequeue_pkts),
                             message="Ensure q dequeue has started on port %s" % dut_port_2)

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

        first = pcap_parser_1.verify_pfc_header_fields(first_packet=True, time0=self.quanta)
        fun_test.test_assert(first, "Value of quanta %s seen in pfc first packet" % self.quanta)


class TestCase5(FunTestCase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Test DUT with pfc enabled on DUT egress with quanta 56797 for priority 0 and "
                                      "ls octet of class vector set to 00000000",
                              steps="""
                        1. Enable pfc on egress port of DUT
                        2. Start traffic of good frame from port 1 of spirent.
                        3. Send pfc frames from port 2 of spirent with quanta 56797 for priority 0 and ls octet 00000000
                        4. Traffic from port 1 must not be stopped as ls octet is 0.
                        5. Verify stats on spirent:
                           a. Tx counter of good stream does not stop
                           b. Rx counter of good stream does not stop
                           c. Tx counter of pfc frame increases
                        6. Verify stats on DUT.
                           a. Tx counter of good stream does not stop.
                           b. Rx counter of good stream does not stop.
                        """)

    def setup(self):
        disable_1 = network_controller_obj.disable_priority_flow_control(dut_port_1, shape=shape)
        fun_test.test_assert(disable_1, "Disable pfc on port %s" % dut_port_1)

        # enable pfc on dut egress
        enable_1 = network_controller_obj.enable_priority_flow_control(dut_port_2, shape=shape)
        fun_test.test_assert(enable_1, "Enable pfc on port %s" % dut_port_2)

        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1, shape=shape)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2, shape=shape)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

    def cleanup(self):
        # Stop generator traffic on ports
        stop = template_obj.disable_generator_configs(generator_configs=generator_dict[port_1])
        fun_test.test_assert(stop, "Stopping generator config on port %s" % port_1)

        # Stop traffic from port 1
        stop = template_obj.disable_generator_configs(generator_configs=generator_dict[port_2])
        fun_test.test_assert(stop, "Stopping generator config on port %s" % port_2)

        # Clear all subscribed results
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        sleep_time = 5
        check_intervals = 3
        good_stream_obj = streamblock_objs['good_stream_obj']
        good_stream_handle = good_stream_obj.spirent_handle
        pfc_stream_obj = streamblock_objs['pfc_stream_obj']
        pfc_stream_handle = pfc_stream_obj.spirent_handle

        pfc_frame.time0 = '56797'
        ls_octet = '00000000'
        output = template_obj.stc_manager.configure_pfc_header(class_enable_vector=True, update=True,
                                                               stream_block_handle=pfc_stream_handle,
                                                               header_obj=pfc_frame, ls_octet=ls_octet)
        fun_test.test_assert(output, message="Updated %s and %s for pfc stream %s" % (pfc_frame.time0,
                                                                                      ls_octet, pfc_stream_handle))

        # Execute traffic from port 1
        start = template_obj.enable_generator_configs(generator_configs=generator_dict[port_1])
        fun_test.test_assert(start, "Starting generator config on port %s" % port_1)

        fun_test.sleep(message="Letting some good traffic from port %s" % port_1, seconds=sleep_time)

        # Enable pfc from port 2
        start = template_obj.enable_generator_configs(generator_configs=generator_dict[port_2])
        fun_test.test_assert(start, "Starting generator config on port %s" % port_2)

        fun_test.sleep("Letting pfc frames to be sent", seconds=sleep_time)

        result_dict = {}
        for i in range(check_intervals):
            fun_test.sleep("Letting traffic to be executed", seconds=sleep_time)
            if i == 0:
                old_good_stream_spirent_tx_counter = 0
                old_good_stream_spirent_rx_counter = 0
                old_dut_port_1_good_receive = 0
                old_dut_port_2_good_transmit = 0
                old_pfc_stream_spirent_tx_counter = 0
            else:
                old_good_stream_spirent_tx_counter = result_dict[good_stream_handle]['tx_result']['FrameCount']
                old_good_stream_spirent_rx_counter = result_dict[good_stream_handle]['rx_result']['FrameCount']
                old_dut_port_1_good_receive = dut_port_1_good_receive
                old_dut_port_2_good_transmit = dut_port_2_good_transmit
                old_pfc_stream_spirent_tx_counter = result_dict[pfc_stream_handle]['tx_result']['FrameCount']

            # Fetch results for streamblocks
            result_dict = template_obj.stc_manager.fetch_streamblock_results(subscribe_result=subscribe_results,
                                                                             streamblock_handle_list=[
                                                                                 good_stream_handle,
                                                                                 pfc_stream_handle],
                                                                             tx_result=True, rx_result=True)
            fun_test.log("Value of transmit for good frame are:- Old: %s ; New: %s" %
                         (old_good_stream_spirent_tx_counter,
                          result_dict[good_stream_handle]['tx_result']['FrameCount']))
            fun_test.log("Value of receive for good frame are:- Old: %s ; New: %s" %
                         (old_good_stream_spirent_rx_counter,
                          result_dict[good_stream_handle]['rx_result']['FrameCount']))
            fun_test.log("Old value of transmit for pfc frame are:- Old: %s ; New: %s" %
                         (old_pfc_stream_spirent_tx_counter,
                          result_dict[pfc_stream_handle]['tx_result']['FrameCount']))

            fun_test.test_assert(int(result_dict[good_stream_handle]['tx_result']['FrameCount']) >
                                 int(old_good_stream_spirent_tx_counter),
                                 message="Ensure tx counter for %s stream has not been stopped" % good_stream_handle)

            fun_test.test_assert(int(result_dict[good_stream_handle]['rx_result']['FrameCount']) >
                                 int(old_good_stream_spirent_rx_counter),
                                 message="Ensure rx counter for %s stream has not been stopped" % good_stream_handle)

            fun_test.test_assert(int(result_dict[pfc_stream_handle]['tx_result']['FrameCount']) >
                                 int(old_pfc_stream_spirent_tx_counter),
                                 message="Ensure pfc frames are being sent via spirent")

            # Fetch results from dut

            dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1, hnu=hnu)
            dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2, hnu=hnu)

            dut_port_1_good_receive = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)
            dut_port_2_good_transmit = get_dut_output_stats_value(dut_port_2_results, FRAMES_TRANSMITTED_OK)

            fun_test.log("Value of transmit for good stream on dut are:- Old: %s ; New: %s" %
                         (old_dut_port_1_good_receive,
                          dut_port_1_good_receive))
            fun_test.log("Value of receive for good frame on dut are:- Old: %s ; New: %s" %
                         (old_dut_port_2_good_transmit,
                          dut_port_2_good_transmit))

            fun_test.test_assert(int(dut_port_1_good_receive) > int(old_dut_port_1_good_receive),
                                 message="Ensure rx counter for %s stream is not stopped on dut from port %s" %
                                         (good_stream_handle, dut_port_1))

            fun_test.test_assert(int(dut_port_2_good_transmit) > int(old_dut_port_2_good_transmit),
                                 message="Ensure tx counter for %s stream is not stopped on dut from port %s" %
                                         (good_stream_handle, dut_port_2))

        # Fetch results for port
        port_dict = template_obj.stc_manager.fetch_port_results(subscribe_result=subscribe_results,
                                                                port_handle_list=[port_1, port_2], analyzer_result=True)

        port_2_errors = template_obj.check_non_zero_error_count(port_dict[port_2]['analyzer_result'])
        port_1_errors = template_obj.check_non_zero_error_count(port_dict[port_1]['analyzer_result'])

        fun_test.test_assert(port_2_errors['result'],
                             message="Check error counters on port %s" % port_2)
        fun_test.test_assert(port_1_errors['result'],
                             message="Check error counters on port %s" % port_1)


if __name__ == "__main__":
    local_settings = nu_config_obj.get_local_settings_parameters(flow_direction=True, ip_version=True)
    flow_direction = local_settings[nu_config_obj.FLOW_DIRECTION]
    ts = SpirentSetup()
    ts.add_test_case(TestCase1())
    ts.add_test_case(TestCase2())
    ts.add_test_case(TestCase3())
    ts.add_test_case(TestCase4())
    ts.add_test_case(TestCase5())
    ts.run()