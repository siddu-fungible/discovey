from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, GeneratorConfig, Ethernet2Header, Ipv4Header
from lib.host.network_controller import NetworkController
from helper import *


num_ports = 2
generator_list = []


class SpirentSetup(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
                1. Create Spirent template
                2. Connect chassis, labserver and licenseserver
                3. Attach Ports
                4. Configure all required streamblock on both ports
                5. Configure generator that runs traffic for specified amount.
                6. Subscribe to tx, rx and analyzer results
                """)

    def setup(self):
        global template_obj, port_1, port_2, subscribe_results, network_controller_obj, dut_port_1, dut_port_2, \
            ethernet, ipv4, source_mac1, destination_mac1, destination_ip1, streamblock_1, duration_seconds

        fun_test.log("Creating Template object")
        template_obj = SpirentEthernetTrafficTemplate(session_name="test_good_bad_frames2")
        fun_test.test_assert(template_obj, "Create template object")

        # Create network controller object
        dpcsh_server_ip = template_obj.stc_manager.dpcsh_server_config['dpcsh_server_ip']
        dpcsh_server_port = int(template_obj.stc_manager.dpcsh_server_config['dpcsh_server_port'])
        network_controller_obj = NetworkController(dpc_server_ip=dpcsh_server_ip, dpc_server_port=dpcsh_server_port)

        result = template_obj.setup(no_of_ports_needed=num_ports)
        fun_test.test_assert(result['result'], "Configure setup")

        port_obj_list = result['port_list']
        port_1 = port_obj_list[0]
        port_2 = port_obj_list[1]

        source_mac1 = template_obj.stc_manager.dut_config['source_mac1']
        destination_mac1 = template_obj.stc_manager.dut_config['destination_mac1']
        destination_ip1 = template_obj.stc_manager.dut_config['destination_ip1']
        dut_port_1 = template_obj.stc_manager.dut_config['port_nos'][0]
        dut_port_2 = template_obj.stc_manager.dut_config['port_nos'][1]

        streamblock_1 = StreamBlock(load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND, load=100)
        create_streamblock_1 = template_obj.configure_stream_block(streamblock_1, port_handle=port_1)
        fun_test.test_assert(create_streamblock_1, " Creating streamblock on port %s" % port_1)

        # Configure mac and ip on the stream
        ethernet = Ethernet2Header(destination_mac=destination_mac1)
        frame_stack = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=streamblock_1._spirent_handle, header_obj=ethernet)
        fun_test.test_assert(frame_stack, "Added ethernet header to stream %s" % streamblock_1._spirent_handle)

        ipv4 = Ipv4Header(destination_address=destination_ip1)
        frame_stack = template_obj.stc_manager.configure_frame_stack(
            stream_block_handle=streamblock_1._spirent_handle, header_obj=ipv4)
        fun_test.test_assert(frame_stack, "Added ipv4 header to stream %s" % streamblock_1._spirent_handle)

        duration_seconds = 10
        gen_config_obj = GeneratorConfig()
        gen_config_obj.Duration = duration_seconds
        gen_config_obj.SchedulingMode = gen_config_obj.SCHEDULING_MODE_RATE_BASED
        gen_config_obj.DurationMode = gen_config_obj.DURATION_MODE_SECONDS
        gen_config_obj.AdvancedInterleaving = True
        config_obj = template_obj.configure_generator_config(port_handle=port_1,
                                                             generator_config_obj=gen_config_obj)
        fun_test.test_assert(config_obj, "Creating generator config on port %s" % port_1)

        generator_list.append(template_obj.stc_manager.get_generator(port_1))

        # Subscribe to results
        project = template_obj.stc_manager.get_project_handle()
        subscribe_results = template_obj.subscribe_to_all_results(parent=project)
        fun_test.test_assert(subscribe_results['result'], "Subscribing to results")
        del subscribe_results['result']


class TestCase1(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Test bad dest ipv4 address",
                              steps="""
                        1. Modify destination ip to bad one.
                        2. Start traffic from spirent
                        3. ensure there is no rx on spirent
                        4. Ensure no rx on dut
                        5. Check psw global stats frv_error, fwd_frv, fwd_main_pkt_drop, main_pkt_drop_eop, ifpg_pkt
                        """)

    def setup(self):
        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

    def cleanup(self):
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

        ipv4.destAddr = destination_ip1
        fun_test.log("Modifying destination ip to correct destination ip")
        output = template_obj.stc_manager.configure_frame_stack(stream_block_handle=streamblock_1._spirent_handle,
                                                                header_obj=ipv4, update=True)
        fun_test.test_assert(output, message="Changed destination ip to correct ip")

    def run(self):
        bad_destination_ip = '99.1.1.99'

        # Modify destination ip to bad destination ip
        ipv4.destAddr = bad_destination_ip

        fun_test.log("Modifying destination ip to bad destination ip")
        output = template_obj.stc_manager.configure_frame_stack(stream_block_handle=streamblock_1._spirent_handle,
                                                                header_obj=ipv4, update=True)
        fun_test.test_assert(output, message="Changed destination ip to bad ip")

        start = template_obj.enable_generator_configs(generator_configs=generator_list)
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=duration_seconds)

        # Fetch spirent results
        result_dict = template_obj.stc_manager.fetch_streamblock_results(subscribe_result=subscribe_results,
                                                                         streamblock_handle_list=[
                                                                             streamblock_1._spirent_handle],
                                                                         tx_result=True, rx_result=True)

        spirent_tx_counter = int(result_dict[streamblock_1._spirent_handle]['tx_result']['FrameCount'])
        spirent_rx_counter = int(result_dict[streamblock_1._spirent_handle]['tx_result']['FrameCount'])

        # Fetch dut results
        dut_results = get_dut_fpg_port_stats(network_controller_obj=network_controller_obj, dut_port_list=[dut_port_1,
                                                                                                           dut_port_2])
        dut_port_1_receive = get_dut_output_stats_value(dut_results[dut_port_1], FRAMES_RECEIVED_OK, tx=False)
        dut_port_2_transmit = get_dut_output_stats_value(dut_results[dut_port_2], FRAMES_TRANSMITTED_OK)

        # Fetch psw global stats
        psw_stats = network_controller_obj.peek_psw_global_stats()
        dut_port_1_fpg_value = get_fpg_port_value(dut_port_1)
        ifpg_pkt = 'ifpg' + str(dut_port_1_fpg_value) + '_pkt'
        frv_error = 'frv_error'
        fwd_frv = 'fwd_frv'
        fwd_main_pkt_drop ='fwd_main_pkt_drop'
        main_pkt_drop_eop = 'main_pkt_drop_eop'
        fetch_list = [frv_error, fwd_frv, fwd_main_pkt_drop, main_pkt_drop_eop, ifpg_pkt]

        psw_fetched_output = get_psw_global_stats_values(psw_stats, fetch_list)

        expected_rx_count = 0
        fun_test.test_assert_expected(expected=expected_rx_count, actual=spirent_rx_counter,
                                      message="Ensure frames are not received when wrong destination ip is "
                                              "present in packet")

        fun_test.test_assert_expected(actual=int(dut_port_1_receive), expected=spirent_tx_counter,
                                      message="Ensure frames are received in dut stats")

        fun_test.test_assert(not dut_port_2_transmit, message=" Ensure no frames are transmitted by dut port %s" %
                                                              dut_port_2)

        for key in fetch_list:
            fun_test.test_assert_expected(expected=int(spirent_tx_counter), actual=psw_fetched_output[key],
                                          message="Check counter %s in psw global stats" % key)


class TestCase2(FunTestCase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Test bad dest mac address",
                              steps="""
                        1. Modify destination mac to bad one.
                        2. Start traffic from spirent
                        3. ensure there is no rx on spirent
                        4. Ensure no rx on dut
                        5. Check psw global stats ifpg, fwd_frv, frv_error, main_pkt_drop_eop, fwd_main_pkt_drop
                        """)

    def setup(self):
        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

    def cleanup(self):
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

        ethernet.dstMac = destination_mac1
        fun_test.log("Modifying destination mac to correct destination mac")
        output = template_obj.stc_manager.configure_frame_stack(stream_block_handle=streamblock_1._spirent_handle,
                                                                header_obj=ethernet, update=True)
        fun_test.test_assert(output, message="Changed destination mac to correct mac")

    def run(self):
        bad_destination_mac = '00:DE:AD:BE:EF:01'

        # Modify destination ip to bad destination ip
        ethernet.dstMac = bad_destination_mac

        fun_test.log("Modifying destination mac to bad destination mac")
        output = template_obj.stc_manager.configure_frame_stack(stream_block_handle=streamblock_1._spirent_handle,
                                                                header_obj=ethernet, update=True)
        fun_test.test_assert(output, message="Changed destination mac to bad mac")

        start = template_obj.enable_generator_configs(generator_configs=generator_list)
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=duration_seconds)

        # Fetch spirent results
        result_dict = template_obj.stc_manager.fetch_streamblock_results(subscribe_result=subscribe_results,
                                                                         streamblock_handle_list=[
                                                                             streamblock_1._spirent_handle],
                                                                         tx_result=True, rx_result=True)

        spirent_tx_counter = int(result_dict[streamblock_1._spirent_handle]['tx_result']['FrameCount'])
        spirent_rx_counter = int(result_dict[streamblock_1._spirent_handle]['tx_result']['FrameCount'])

        # Fetch dut results
        dut_results = get_dut_fpg_port_stats(network_controller_obj=network_controller_obj, dut_port_list=[dut_port_1,
                                                                                                           dut_port_2])
        dut_port_1_receive = get_dut_output_stats_value(dut_results[dut_port_1], FRAMES_RECEIVED_OK, tx=False)
        dut_port_2_transmit = get_dut_output_stats_value(dut_results[dut_port_2], FRAMES_TRANSMITTED_OK)

        # Fetch psw global stats
        psw_stats = network_controller_obj.peek_psw_global_stats()
        dut_port_1_fpg_value = get_fpg_port_value(dut_port_1)
        ifpg_pkt = 'ifpg' + str(dut_port_1_fpg_value) + '_pkt'
        frv_error = 'frv_error'
        fwd_frv = 'fwd_frv'
        fwd_main_pkt_drop = 'fwd_main_pkt_drop'
        main_pkt_drop_eop = 'main_pkt_drop_eop'
        fetch_list = [frv_error, fwd_frv, fwd_main_pkt_drop, main_pkt_drop_eop, ifpg_pkt]

        psw_fetched_output = get_psw_global_stats_values(psw_stats, fetch_list)

        expected_rx_count = 0
        fun_test.test_assert_expected(expected=expected_rx_count, actual=spirent_rx_counter,
                                      message="Ensure frames are not received when wrong destination ip is "
                                              "present in packet")

        fun_test.test_assert_expected(actual=int(dut_port_1_receive), expected=spirent_tx_counter,
                                      message="Ensure frames are received in dut stats")

        fun_test.test_assert(not dut_port_2_transmit, message=" Ensure no frames are transmitted by dut port %s" %
                                                              dut_port_2)

        for key in fetch_list:
            fun_test.test_assert_expected(expected=int(spirent_tx_counter), actual=psw_fetched_output[key],
                                          message="Check counter %s in psw global stats" % key)


class TestCase3(FunTestCase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Test bad source mac address",
                              steps="""
                        1. Modify source mac to bad one.
                        2. Start traffic from spirent
                        3. ensure there is no rx on spirent
                        4. Ensure no rx on dut
                        5. Check psw global stats ct_pkt, fwd_frv, ifpg_pkt, fpg_pkt
                        """)

    def setup(self):
        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

    def cleanup(self):
        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

        ethernet.srcMac = source_mac1
        fun_test.log("Modifying source mac to correct source mac")
        output = template_obj.stc_manager.configure_frame_stack(stream_block_handle=streamblock_1._spirent_handle,
                                                                header_obj=ethernet, update=True)
        fun_test.test_assert(output, message="Changed source mac to source mac")

    def run(self):
        bad_source_mac = '01:DE:AD:BE:EF:00'

        # Modify destination ip to bad destination ip
        ethernet.preamble = bad_source_mac

        fun_test.log("Modifying source mac to bad source mac")
        output = template_obj.stc_manager.configure_frame_stack(stream_block_handle=streamblock_1._spirent_handle,
                                                                header_obj=ethernet, update=True)
        fun_test.test_assert(output, message="Changed source mac to bad source mac")

        start = template_obj.enable_generator_configs(generator_configs=generator_list)
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=duration_seconds)

        # Fetch spirent results
        result_dict = template_obj.stc_manager.fetch_streamblock_results(subscribe_result=subscribe_results,
                                                                         streamblock_handle_list=[
                                                                             streamblock_1._spirent_handle],
                                                                         tx_result=True, rx_result=True)

        spirent_tx_counter = int(result_dict[streamblock_1._spirent_handle]['tx_result']['FrameCount'])
        spirent_rx_counter = int(result_dict[streamblock_1._spirent_handle]['tx_result']['FrameCount'])

        # Fetch dut results
        dut_results = get_dut_fpg_port_stats(network_controller_obj=network_controller_obj, dut_port_list=[dut_port_1,
                                                                                                           dut_port_2])
        dut_port_1_receive = get_dut_output_stats_value(dut_results[dut_port_1], FRAMES_RECEIVED_OK, tx=False)
        dut_port_2_transmit = get_dut_output_stats_value(dut_results[dut_port_2], FRAMES_TRANSMITTED_OK)

        # Fetch psw global stats
        psw_stats = network_controller_obj.peek_psw_global_stats()
        dut_port_1_fpg_value = get_fpg_port_value(dut_port_1)
        ifpg_pkt = 'ifpg' + str(dut_port_1_fpg_value) + '_pkt'
        fpg_pkt = 'fpg' + str(dut_port_1_fpg_value) + '_pkt'
        fwd_frv = 'fwd_frv'
        ct_pkt = 'ct_pkt'
        fetch_list = [fwd_frv, fpg_pkt, ct_pkt, ifpg_pkt]

        psw_fetched_output = get_psw_global_stats_values(psw_stats, fetch_list)

        expected_rx_count = 0
        fun_test.test_assert_expected(expected=expected_rx_count, actual=spirent_rx_counter,
                                      message="Ensure frames are not received when wrong destination ip is "
                                              "present in packet")

        fun_test.test_assert_expected(actual=int(dut_port_1_receive), expected=spirent_tx_counter,
                                      message="Ensure frames are received in dut stats")

        fun_test.test_assert(not dut_port_2_transmit, message=" Ensure no frames are transmitted by dut port %s" %
                                                              dut_port_2)

        for key in fetch_list:
            fun_test.test_assert_expected(expected=int(spirent_tx_counter), actual=psw_fetched_output[key],
                                          message="Check counter %s in psw global stats" % key)


if __name__ == "__main__":
    ts = SpirentSetup()
    ts.add_test_case(TestCase1())
    ts.add_test_case(TestCase2())
    ts.add_test_case(TestCase3())
    ts.run()