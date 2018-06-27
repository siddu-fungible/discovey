from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, GeneratorConfig, Ethernet2Header
from lib.host.network_controller import NetworkController
from helper import *
from nu_config_manager import *


num_ports = 2
loads_file = "interface_loads.json"
min_frame_length_ipv4 = 64
min_frame_length_ipv6 = 78
max_frame_length = 9000
mtu = max_frame_length
generator_step_ipv4 = max_frame_length - min_frame_length_ipv4
generator_step_ipv6 = max_frame_length - min_frame_length_ipv6
duration_seconds = 240
step_size = 1


def get_nearest_key(dict, max_frame_length):
    nearest_small_key = 0
    for key in dict.keys():

        if key != 'max' and int(key) < max_frame_length:
            current_difference = max_frame_length - int(key)
            if current_difference < max_frame_length - nearest_small_key:
                nearest_small_key = int(key)
    return nearest_small_key


def get_modified_dictionary(dict, nearest_key, max_frame_length):
    output_dict = {}
    if nearest_key == 1518:
        output_dict = dict
        output_dict['max'] = max_frame_length - 1518
    else:
        for key, val in dict.iteritems():
            if key == 'max':
                pass
            elif int(key) < nearest_key:
                output_dict[key] = val
            elif int(key) == nearest_key:
                new_val = max_frame_length - int(key)
                output_dict[key] = new_val
    return output_dict


class SpirentSetup(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
                1. Create Spirent template
                2. Connect chassis, labserver and licenseserver
                3. Attach Ports
                4. Create two streamblocks with frame mode as incremental from min size 64B to 16380B and step as 1 on 
                   each port.
                5. Configure generator that runs traffic for specified amount.
                6. Subscribe to tx, rx and analyzer results
                """)

    def setup(self):
        global template_obj, port_1, port_2, interface_1_obj, interface_2_obj, \
            gen_obj_1, gen_obj_2, duration_seconds, subscribe_results, dut_port_2, dut_port_1, network_controller_obj, \
            dut_config, spirent_config, gen_config_obj

        dut_type = fun_test.get_local_setting(setting="dut_type")
        dut_config = nu_config_obj.read_dut_config(dut_type=dut_type)

        chassis_type = fun_test.get_local_setting(setting="chassis_type")
        spirent_config = nu_config_obj.read_traffic_generator_config()

        fun_test.log("Creating Template object")
        template_obj = SpirentEthernetTrafficTemplate(session_name="mac-sanity", spirent_config=spirent_config,
                                                      chassis_type=chassis_type)
        fun_test.test_assert(template_obj, "Create template object")

        # Create network controller object
        dpcsh_server_ip = dut_config["dpcsh_tcp_proxy_ip"]
        dpcsh_server_port = dut_config['dpcsh_tcp_proxy_port']
        network_controller_obj = NetworkController(dpc_server_ip=dpcsh_server_ip, dpc_server_port=dpcsh_server_port)

        result = template_obj.setup(no_of_ports_needed=num_ports)
        fun_test.test_assert(result['result'], "Configure setup")

        port_1 = result['port_list'][0]
        port_2 = result['port_list'][1]

        dut_port_1 = dut_config['ports'][0]
        dut_port_2 = dut_config['ports'][1]

        '''
        srcMac = template_obj.stc_manager.dut_config['source_mac1']
        destMac = template_obj.stc_manager.dut_config['destination_mac1']
        srcIp = template_obj.stc_manager.dut_config['source_ip1']
        destIp = template_obj.stc_manager.dut_config['destination_ip1']
        destIp2 = template_obj.stc_manager.dut_config['destination_ip2']
        dut_port_1 = template_obj.stc_manager.dut_config['port_nos'][0]
        dut_port_2 = template_obj.stc_manager.dut_config['port_nos'][1]
        gateway = template_obj.stc_manager.dut_config['gateway1']
        interface_mode = template_obj.stc_manager.interface_mode
        '''

        # Set Mtu
        interface_1_obj = result['interface_obj_list'][0]
        interface_2_obj = result['interface_obj_list'][1]
        interface_1_obj.Mtu = mtu
        interface_2_obj.Mtu = mtu

        set_mtu_1 = template_obj.configure_physical_interface(interface_1_obj)
        fun_test.test_assert(set_mtu_1, "Set mtu on %s " % interface_1_obj)
        set_mtu_2 = template_obj.configure_physical_interface(interface_2_obj)
        fun_test.test_assert(set_mtu_2, "Set mtu on %s " % interface_2_obj)

        # Set mtu on DUT
        mtu_1 = network_controller_obj.set_port_mtu(port_num=dut_port_1, mtu_value=mtu)
        fun_test.test_assert(mtu_1, " Set mtu on DUT port %s" % dut_port_1)
        mtu_2 = network_controller_obj.set_port_mtu(port_num=dut_port_2, mtu_value=mtu)
        fun_test.test_assert(mtu_2, " Set mtu on DUT port %s" % dut_port_2)

        # Configure Generator
        gen_config_obj = GeneratorConfig()
        gen_config_obj.SchedulingMode = gen_config_obj.SCHEDULING_MODE_RATE_BASED
        gen_config_obj.DurationMode = gen_config_obj.DURATION_MODE_STEP
        gen_config_obj.AdvancedInterleaving = True
        gen_config_obj.StepSize = generator_step_ipv4

        # Apply generator config on port 1
        gen_obj_1 = template_obj.stc_manager.get_generator(port_handle=port_1)
        config_obj = template_obj.configure_generator_config(port_handle=port_1,
                                                             generator_config_obj=gen_config_obj)
        fun_test.test_assert(config_obj, "Creating generator config on port %s" % port_1)

        # Apply generator config on port 2
        gen_obj_2 = template_obj.stc_manager.get_generator(port_handle=port_2)
        config_obj = template_obj.configure_generator_config(port_handle=port_2,
                                                             generator_config_obj=gen_config_obj)
        fun_test.test_assert(config_obj, "Creating generator config on port %s" % port_2)

        # Applying configuration
        apply = template_obj.stc_manager.apply_configuration()
        fun_test.test_assert(apply, "Applying Generator config")

        # Subscribe to results
        project = template_obj.stc_manager.get_project_handle()
        subscribe_results = template_obj.subscribe_to_all_results(parent=project)
        fun_test.test_assert(subscribe_results['result'], "Subscribing to results")
        del subscribe_results['result']

    def cleanup(self):
        fun_test.test_assert(template_obj.cleanup(), "Cleaning up session")


class IPv4IncrementalTestCase1(FunTestCase):
    streamblock_obj_1 = None
    streamblock_obj_2 = None
    min_frame_size = min_frame_length_ipv4
    generator_step_size = generator_step_ipv4

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test all frame size in incremental way (IPv4)",
                              steps="""
                        1. Start traffic and subscribe to tx and rx results
                        2. Compare Tx and Rx results for frame count
                        3. Check for error counters. there must be no error counter
                        4. Check dut ingress and egress frame count match
                        5. Check OctetStats from dut and spirent
                        6. Check EtherOctets from dut and spirent.
                        7. Check Counter for each octet range
                        """)

    def setup(self):
        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

        #  Read loads from file
        file_path = fun_test.get_script_parent_directory() + "/" + loads_file
        output = fun_test.parse_file_to_json(file_path)
        load = output[dut_config['interface_mode']]["incremental_load_mbps"]
        l2_config = spirent_config["l2_config"]
        l3_config = spirent_config["l3_config"]["ipv4"]
        ether_type = Ethernet2Header.INTERNET_IP_ETHERTYPE

        # Create streamblock 1
        self.streamblock_obj_1 = StreamBlock()
        self.streamblock_obj_1.LoadUnit = StreamBlock.LOAD_UNIT_MEGABITS_PER_SECOND
        self.streamblock_obj_1.Load = load
        self.streamblock_obj_1.FillType = StreamBlock.FILL_TYPE_PRBS
        self.streamblock_obj_1.InsertSig = True
        self.streamblock_obj_1.FrameLengthMode = StreamBlock.FRAME_LENGTH_MODE_INCR
        self.streamblock_obj_1.MinFrameLength = min_frame_length_ipv4
        self.streamblock_obj_1.MaxFrameLength = max_frame_length
        self.streamblock_obj_1.StepFrameLength = step_size

        streamblock1 = template_obj.configure_stream_block(self.streamblock_obj_1, port_1)
        fun_test.test_assert(streamblock1, "Creating streamblock on port %s" % port_1)

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=self.streamblock_obj_1.spirent_handle,
                                                               source_mac=l2_config['source_mac'],
                                                               destination_mac=l2_config['destination_mac'],
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Adding source and destination mac")

        # Adding Ip address and gateway
        ip = template_obj.stc_manager.configure_ip_address(streamblock=self.streamblock_obj_1.spirent_handle,
                                                           source=l3_config['source_ip1'],
                                                           destination=l3_config['destination_ip1'],
                                                           gateway=l3_config['gateway'])
        fun_test.test_assert(ip, "Adding source ip, dest ip and gateway")

        # Create streamblock 2
        self.streamblock_obj_2 = StreamBlock()
        self.streamblock_obj_2.LoadUnit = StreamBlock.LOAD_UNIT_MEGABITS_PER_SECOND
        self.streamblock_obj_2.Load = load
        self.streamblock_obj_2.FillType = StreamBlock.FILL_TYPE_PRBS
        self.streamblock_obj_2.InsertSig = True
        self.streamblock_obj_2.FrameLengthMode = StreamBlock.FRAME_LENGTH_MODE_INCR
        self.streamblock_obj_2.MinFrameLength = min_frame_length_ipv4
        self.streamblock_obj_2.MaxFrameLength = max_frame_length
        self.streamblock_obj_2.StepFrameLength = step_size

        streamblock2 = template_obj.configure_stream_block(self.streamblock_obj_2, port_2)
        fun_test.test_assert(streamblock2, "Creating streamblock on port %s" % port_2)

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=self.streamblock_obj_2.spirent_handle,
                                                               source_mac=l2_config['source_mac'],
                                                               destination_mac=l2_config['destination_mac'],
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Adding source and destination mac")

        # Adding Ip address and gateway
        ip = template_obj.stc_manager.configure_ip_address(streamblock=self.streamblock_obj_2.spirent_handle,
                                                           source=l3_config['source_ip2'],
                                                           destination=l3_config['destination_ip2'],
                                                           gateway=l3_config['gateway'])
        fun_test.test_assert(ip, "Adding source ip, dest ip and gateway")

    def cleanup(self):
        fun_test.log("In testcase cleanup")

        fun_test.log("Deleting streamblock %s and %s" % (self.streamblock_obj_1.spirent_handle,
                                                         self.streamblock_obj_2.spirent_handle))
        template_obj.delete_streamblocks(streamblock_handle_list=[self.streamblock_obj_1.spirent_handle,
                                                                  self.streamblock_obj_2.spirent_handle])

        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        psw_stats = network_controller_obj.peek_psw_global_stats()

        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=[gen_obj_1, gen_obj_2])
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic for %s seconds" % duration_seconds, seconds=duration_seconds)

        # Get results for streamblock 1
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            self.streamblock_obj_1.spirent_handle))
        tx_results_1 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=self.streamblock_obj_1.spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            self.streamblock_obj_1.spirent_handle))
        rx_results_1 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=self.streamblock_obj_1.spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        # Get streambllock 2 results
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            self.streamblock_obj_2.spirent_handle))
        tx_results_2 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=self.streamblock_obj_2.spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            self.streamblock_obj_2.spirent_handle))
        rx_results_2 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=self.streamblock_obj_2.spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        fun_test.log("Fetching rx port results for subscribed object %s" % subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results_2 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_2, subscribe_handle=subscribe_results['analyzer_subscribe'])

        fun_test.log("Fetching rx port results for subscribed object %s" % subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results_1 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_1, subscribe_handle=subscribe_results['analyzer_subscribe'])

        dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1)
        dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2)

        psw_stats = network_controller_obj.peek_psw_global_stats()

        fun_test.log("Tx 1 Results %s " % tx_results_1)
        fun_test.log("Rx 1 Results %s" % rx_results_1)
        fun_test.log("Tx 2 Results %s " % tx_results_2)
        fun_test.log("Rx 2 Results %s" % rx_results_2)
        fun_test.log("Rx Port Analyzer Results %s" % rx_port_analyzer_results_1)
        fun_test.log("Rx Port Analyzer Results %s" % rx_port_analyzer_results_2)
        fun_test.log("DUT Port 1 Results: %s" % dut_port_1_results)
        fun_test.log("DUT Port 2 Results: %s" % dut_port_2_results)

        fun_test.test_assert(dut_port_1_results, message="Ensure stats are obtained for %s" % dut_port_1)
        fun_test.test_assert(dut_port_2_results, message="Ensure stats are obtained for %s" % dut_port_2)

        dut_port_1_transmit = get_dut_output_stats_value(dut_port_1_results, FRAMES_TRANSMITTED_OK)
        dut_port_2_transmit = get_dut_output_stats_value(dut_port_2_results, FRAMES_TRANSMITTED_OK)
        dut_port_1_receive = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)
        dut_port_2_receive = get_dut_output_stats_value(dut_port_2_results, FRAMES_RECEIVED_OK, tx=False)

        # ether stats pkts
        dut_port_1_rx_eth_stats_pkts = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_PKTS, tx=False)
        dut_port_2_rx_eth_stats_pkts = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_PKTS, tx=False)
        dut_port_1_tx_eth_stats_pkts = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_PKTS)
        dut_port_2_tx_eth_stats_pkts = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_PKTS)

        # Octet count
        dut_port_1_rx_octet_stats = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_OCTETS, tx=False)
        dut_port_1_tx_octet_stats = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_OCTETS)
        dut_port_2_rx_octet_stats = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_OCTETS, tx=False)
        dut_port_2_tx_octet_stats = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_OCTETS)

        # Get rx octet range
        dut_port_1_rx_octet_64 = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_PKTS_64_OCTETS, tx=False)
        dut_port_1_rx_octet_65_127 = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_PKTS_65_TO_127_OCTETS,
                                                                tx=False)
        dut_port_1_rx_octet_128_255 = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_PKTS_128_TO_255_OCTETS,
                                                                 tx=False)
        dut_port_1_rx_octet_256_511 = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_PKTS_256_TO_511_OCTETS,
                                                                 tx=False)
        dut_port_1_rx_octet_512_1023 = get_dut_output_stats_value(dut_port_1_results,
                                                                  ETHER_STATS_PKTS_512_TO_1023_OCTETS,
                                                                  tx=False)
        dut_port_1_rx_octet_1024_1518 = get_dut_output_stats_value(dut_port_1_results,
                                                                   ETHER_STATS_PKTS_1024_TO_1518_OCTETS,
                                                                   tx=False)
        dut_port_1_rx_octet_1519_max = get_dut_output_stats_value(dut_port_1_results,
                                                                  ETHER_STATS_PKTS_1519_TO_MAX_OCTETS,
                                                                  tx=False)

        dut_port_2_rx_octet_64 = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_PKTS_64_OCTETS, tx=False)
        dut_port_2_rx_octet_65_127 = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_PKTS_65_TO_127_OCTETS,
                                                                tx=False)
        dut_port_2_rx_octet_128_255 = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_PKTS_128_TO_255_OCTETS,
                                                                 tx=False)
        dut_port_2_rx_octet_256_511 = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_PKTS_256_TO_511_OCTETS,
                                                                 tx=False)
        dut_port_2_rx_octet_512_1023 = get_dut_output_stats_value(dut_port_2_results,
                                                                  ETHER_STATS_PKTS_512_TO_1023_OCTETS,
                                                                  tx=False)
        dut_port_2_rx_octet_1024_1518 = get_dut_output_stats_value(dut_port_2_results,
                                                                   ETHER_STATS_PKTS_1024_TO_1518_OCTETS,
                                                                   tx=False)
        dut_port_2_rx_octet_1519_max = get_dut_output_stats_value(dut_port_2_results,
                                                                  ETHER_STATS_PKTS_1519_TO_MAX_OCTETS,
                                                                  tx=False)

        # Get tx octet range
        dut_port_1_tx_octet_64 = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_PKTS_64_OCTETS)
        dut_port_1_tx_octet_65_127 = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_PKTS_65_TO_127_OCTETS)
        dut_port_1_tx_octet_128_255 = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_PKTS_128_TO_255_OCTETS)
        dut_port_1_tx_octet_256_511 = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_PKTS_256_TO_511_OCTETS)
        dut_port_1_tx_octet_512_1023 = get_dut_output_stats_value(dut_port_1_results,
                                                                  ETHER_STATS_PKTS_512_TO_1023_OCTETS)
        dut_port_1_tx_octet_1024_1518 = get_dut_output_stats_value(dut_port_1_results,
                                                                   ETHER_STATS_PKTS_1024_TO_1518_OCTETS)
        dut_port_1_tx_octet_1519_max = get_dut_output_stats_value(dut_port_1_results,
                                                                  ETHER_STATS_PKTS_1519_TO_MAX_OCTETS)

        dut_port_2_tx_octet_64 = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_PKTS_64_OCTETS)
        dut_port_2_tx_octet_65_127 = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_PKTS_65_TO_127_OCTETS)
        dut_port_2_tx_octet_128_255 = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_PKTS_128_TO_255_OCTETS)
        dut_port_2_tx_octet_256_511 = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_PKTS_256_TO_511_OCTETS)
        dut_port_2_tx_octet_512_1023 = get_dut_output_stats_value(dut_port_2_results,
                                                                  ETHER_STATS_PKTS_512_TO_1023_OCTETS)
        dut_port_2_tx_octet_1024_1518 = get_dut_output_stats_value(dut_port_2_results,
                                                                   ETHER_STATS_PKTS_1024_TO_1518_OCTETS)
        dut_port_2_tx_octet_1519_max = get_dut_output_stats_value(dut_port_2_results,
                                                                  ETHER_STATS_PKTS_1519_TO_MAX_OCTETS)

        dut_octet_range_stats = {dut_port_1:
                                     {'RX': {'64': dut_port_1_rx_octet_64,
                                             '127': dut_port_1_rx_octet_65_127,
                                             '255': dut_port_1_rx_octet_128_255,
                                             '511': dut_port_1_rx_octet_256_511,
                                             '1023': dut_port_1_rx_octet_512_1023,
                                             '1518': dut_port_1_rx_octet_1024_1518,
                                             'max': dut_port_1_rx_octet_1519_max},
                                      'TX': {'64': dut_port_1_tx_octet_64,
                                             '127': dut_port_1_tx_octet_65_127,
                                             '255': dut_port_1_tx_octet_128_255,
                                             '511': dut_port_1_tx_octet_256_511,
                                             '1023': dut_port_1_tx_octet_512_1023,
                                             '1518': dut_port_1_tx_octet_1024_1518,
                                             'max': dut_port_1_tx_octet_1519_max}},
                                 dut_port_2:
                                     {'RX': {'64': dut_port_2_rx_octet_64,
                                             '127': dut_port_2_rx_octet_65_127,
                                             '255': dut_port_2_rx_octet_128_255,
                                             '511': dut_port_2_rx_octet_256_511,
                                             '1023': dut_port_2_rx_octet_512_1023,
                                             '1518': dut_port_2_rx_octet_1024_1518,
                                             'max': dut_port_2_rx_octet_1519_max},
                                      'TX': {'64': dut_port_2_tx_octet_64,
                                             '127': dut_port_2_tx_octet_65_127,
                                             '255': dut_port_2_tx_octet_128_255,
                                             '511': dut_port_2_tx_octet_256_511,
                                             '1023': dut_port_2_tx_octet_512_1023,
                                             '1518': dut_port_2_tx_octet_1024_1518,
                                             'max': dut_port_2_tx_octet_1519_max}}
                                 }

        second_last_counter = 1519
        max_counter_value = max_frame_length - second_last_counter
        expected_octet_counters = {'64': 1, '127': 63, '255': 128, '511': 256, '1023': 512, '1518': 495,
                                   'max': max_counter_value}

        fun_test.test_assert(template_obj.compare_result_attribute(tx_results_1, rx_results_1),
                             "Check FrameCount for streamblock %s" % self.streamblock_obj_1.spirent_handle)
        fun_test.test_assert(template_obj.compare_result_attribute(tx_results_2, rx_results_2),
                             "Check FrameCount for streamblock %s" % self.streamblock_obj_2.spirent_handle)

        fun_test.test_assert_expected(expected=int(dut_port_1_receive), actual=int(dut_port_2_transmit),
                                      message="Ensure frames received on DUT port %s are transmitted from DUT port %s"
                                              % (dut_port_1, dut_port_2))

        fun_test.test_assert_expected(expected=int(dut_port_2_receive), actual=int(dut_port_1_transmit),
                                      message="Ensure frames received on DUT port %s are transmitted from DUT port %s"
                                              % (dut_port_2, dut_port_1))

        fun_test.test_assert_expected(expected=int(dut_port_2_transmit), actual=int(rx_results_1['FrameCount']),
                                      message="Ensure frames transmitted from DUT and counter on spirent match")

        fun_test.test_assert_expected(expected=int(dut_port_1_transmit), actual=int(rx_results_2['FrameCount']),
                                      message="Ensure frames transmitted from DUT and counter on spirent match")

        # Check ether stats pkts
        fun_test.test_assert_expected(expected=int(dut_port_1_rx_eth_stats_pkts),
                                      actual=int(dut_port_2_tx_eth_stats_pkts),
                                      message="Ensure eth stat pkts received by DUT port %s are transmitted "
                                              "by DUT port %s" % (dut_port_1, dut_port_2))

        fun_test.test_assert_expected(expected=int(dut_port_2_tx_eth_stats_pkts),
                                      actual=int(rx_results_1['FrameCount']),
                                      message="Ensure eth stat pkts transmitted from DUT and counter on spirent match")

        fun_test.test_assert_expected(expected=int(dut_port_2_rx_eth_stats_pkts),
                                      actual=int(dut_port_1_tx_eth_stats_pkts),
                                      message="Ensure eth stat pkts received by DUT port %s are transmitted "
                                              "by DUT port %s" % (dut_port_2, dut_port_1))

        fun_test.test_assert_expected(expected=int(dut_port_1_tx_eth_stats_pkts),
                                      actual=int(rx_results_2['FrameCount']),
                                      message="Ensure eth stat pkts transmitted from DUT and counter on spirent match")

        # Check octet counts
        fun_test.test_assert_expected(expected=int(dut_port_1_rx_octet_stats), actual=int(dut_port_2_tx_octet_stats),
                                      message="Ensure correct ether stats octets are seen on both DUT ports")

        fun_test.test_assert_expected(expected=int(tx_results_1['OctetCount']), actual=int(rx_results_1['OctetCount']),
                                      message="Ensure octet counts match on spirent rx and tx")

        fun_test.test_assert_expected(expected=int(rx_results_1['OctetCount']), actual=int(dut_port_2_tx_octet_stats),
                                      message="Ensure octets hsown on tx port of DUT matches rx of spirent")

        fun_test.test_assert_expected(expected=int(dut_port_2_rx_octet_stats), actual=int(dut_port_1_tx_octet_stats),
                                      message="Ensure correct ether stats octets are seen on both DUT ports")

        fun_test.test_assert_expected(expected=int(tx_results_2['OctetCount']), actual=int(rx_results_2['OctetCount']),
                                      message="Ensure octet counts match on spirent rx and tx")

        fun_test.test_assert_expected(expected=int(rx_results_2['OctetCount']), actual=int(dut_port_1_tx_octet_stats),
                                      message="Ensure octets hsown on tx port of DUT matches rx of spirent")

        for key, val in dut_octet_range_stats.iteritems():    # DUT level
            for key1, val1 in val.iteritems():                # RX, TX level
                for key2, val2 in val1.iteritems():           # Octet level
                    fun_test.test_assert_expected(expected=expected_octet_counters[key2], actual=int(val2),
                                                  message="Ensure correct value is seen for %s octet in %s of "
                                                          "dut port %s" % (key2, key1, key))

        zero_counter_seen = template_obj.check_non_zero_error_count(rx_port_analyzer_results_1)
        fun_test.test_assert(zero_counter_seen['result'], "Check for error counters on port2")

        zero_counter_seen = template_obj.check_non_zero_error_count(rx_port_analyzer_results_2)
        fun_test.test_assert(zero_counter_seen['result'], "Check for error counters on port1")


class IPv6IncrementalTestCase1(IPv4IncrementalTestCase1):
    min_frame_size = min_frame_length_ipv6
    generator_step_size = generator_step_ipv6

    def describe(self):
        self.set_test_details(id=1,
                              summary="Test all frame size in incremental way (IPv6)",
                              steps="""
                              1. Create Streams with following settings
                                 a. Load: 5 Mbps
                                 b. Payload Fill Type: PRBS
                                 c. Insert Signature True
                                 d. Frame Size Mode: Incremental Min: %d Max: %d
                              2. Start traffic for %d secs 
                              3. Compare Tx and Rx results for frame count
                              4. Check for error counters. there must be no error counter
                              5. Check dut ingress and egress frame count match
                              6. Check OctetStats from dut and spirent
                              7. Check EtherOctets from dut and spirent.
                              8. Check Counter for each octet range
                              """ % (78, max_frame_length, duration_seconds))

    def setup(self):
        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

        #  Read loads from file
        file_path = fun_test.get_script_parent_directory() + "/" + loads_file
        output = fun_test.parse_file_to_json(file_path)
        load = output[dut_config['interface_mode']]["incremental_load_mbps"]
        l2_config = spirent_config["l2_config"]
        l3_config = spirent_config["l3_config"]["ipv6"]
        ether_type = Ethernet2Header.INTERNET_IPV6_ETHERTYPE

        # Create streamblock 1
        self.streamblock_obj_1 = StreamBlock()
        self.streamblock_obj_1.LoadUnit = StreamBlock.LOAD_UNIT_MEGABITS_PER_SECOND
        self.streamblock_obj_1.Load = load
        self.streamblock_obj_1.FillType = StreamBlock.FILL_TYPE_PRBS
        self.streamblock_obj_1.InsertSig = True
        self.streamblock_obj_1.FrameLengthMode = StreamBlock.FRAME_LENGTH_MODE_INCR
        self.streamblock_obj_1.MinFrameLength = min_frame_length_ipv6
        self.streamblock_obj_1.MaxFrameLength = max_frame_length
        self.streamblock_obj_1.StepFrameLength = step_size

        streamblock1 = template_obj.configure_stream_block(stream_block_obj=self.streamblock_obj_1,
                                                           port_handle=port_1, ip_header_version=6)
        fun_test.test_assert(streamblock1, "Creating streamblock on port %s" % port_1)

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=self.streamblock_obj_1.spirent_handle,
                                                               source_mac=l2_config['source_mac'],
                                                               destination_mac=l2_config['destination_mac'],
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Adding source and destination mac")

        # Adding Ip address and gateway
        ip = template_obj.stc_manager.configure_ip_address(streamblock=self.streamblock_obj_1.spirent_handle,
                                                           source=l3_config['source_ip1'],
                                                           destination=l3_config['destination_ip1'])
        fun_test.test_assert(ip, "Adding source ip, dest ip and gateway")

        # Create streamblock 2
        self.streamblock_obj_2 = StreamBlock()
        self.streamblock_obj_2.LoadUnit = StreamBlock.LOAD_UNIT_MEGABITS_PER_SECOND
        self.streamblock_obj_2.Load = load
        self.streamblock_obj_2.FillType = StreamBlock.FILL_TYPE_PRBS
        self.streamblock_obj_2.InsertSig = True
        self.streamblock_obj_2.FrameLengthMode = StreamBlock.FRAME_LENGTH_MODE_INCR
        self.streamblock_obj_2.MinFrameLength = min_frame_length_ipv6
        self.streamblock_obj_2.MaxFrameLength = max_frame_length
        self.streamblock_obj_2.StepFrameLength = step_size

        streamblock2 = template_obj.configure_stream_block(stream_block_obj=self.streamblock_obj_2,
                                                           port_handle=port_2, ip_header_version=6)
        fun_test.test_assert(streamblock2, "Creating streamblock on port %s" % port_2)

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=self.streamblock_obj_2.spirent_handle,
                                                               source_mac=l2_config['source_mac'],
                                                               destination_mac=l2_config['destination_mac'],
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Adding source and destination mac")

        # Adding Ip address and gateway
        ip = template_obj.stc_manager.configure_ip_address(streamblock=self.streamblock_obj_2.spirent_handle,
                                                           source=l3_config['source_ip2'],
                                                           destination=l3_config['destination_ip2'])
        fun_test.test_assert(ip, "Adding source ip, dest ip and gateway")

        # Setting generator config
        gen_config_obj.StepSize = self.generator_step_size
        config_obj = template_obj.configure_generator_config(port_handle=port_1,
                                                             generator_config_obj=gen_config_obj)
        fun_test.test_assert(config_obj,
                             "Updating generator config step to %s on port %s" % (self.generator_step_size, port_1))

        config_obj = template_obj.configure_generator_config(port_handle=port_2,
                                                             generator_config_obj=gen_config_obj)
        fun_test.test_assert(config_obj,
                             "Updating generator config step to %s on port %s" % (self.generator_step_size, port_2))

    def run(self):
        super(IPv6IncrementalTestCase1, self).run()

    def cleanup(self):
        super(IPv6IncrementalTestCase1, self).cleanup()


class IPv4RandomTestCase2(FunTestCase):
    streamblock_obj_1 = None
    streamblock_obj_2 = None
    min_frame_size = min_frame_length_ipv4
    generator_step_size = generator_step_ipv4

    def describe(self):
        self.set_test_details(id=2,
                              summary="Test large random frame size (IPv4)",
                              steps="""
                        1. Create Streams with following settings
                           a. Load: 5 Mbps
                           b. Payload Fill Type: PRBS
                           c. Insert signature True
                           d. Frame Size Mode: Random min: %d max: %d step: %d
                        2. Start traffic for %d secs 
                        3. Compare Tx and Rx results for frame count for each stream
                        4. Check for error counters. there must be no error counter
                        5. Check ok frames on dut ingress and egress counter match and spirent
                        6. Check psw stats for fwd_frv, ct_pkt, ifpg_pkt, fpg_pkt 
                        """ % (min_frame_length_ipv4, max_frame_length, step_size, duration_seconds))

    def setup(self):
        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

        #  Read loads from file
        file_path = fun_test.get_script_parent_directory() + "/" + loads_file
        output = fun_test.parse_file_to_json(file_path)
        load = output[dut_config['interface_mode']]["incremental_load_mbps"]
        l2_config = spirent_config["l2_config"]
        l3_config = spirent_config["l3_config"]["ipv4"]
        ether_type = Ethernet2Header.INTERNET_IP_ETHERTYPE

        # Create streamblock 1
        self.streamblock_obj_1 = StreamBlock()
        self.streamblock_obj_1.LoadUnit = StreamBlock.LOAD_UNIT_MEGABITS_PER_SECOND
        self.streamblock_obj_1.Load = load
        self.streamblock_obj_1.FillType = StreamBlock.FILL_TYPE_PRBS
        self.streamblock_obj_1.InsertSig = True
        self.streamblock_obj_1.FrameLengthMode = StreamBlock.FRAME_LENGTH_MODE_RANDOM
        self.streamblock_obj_1.MinFrameLength = min_frame_length_ipv4
        self.streamblock_obj_1.MaxFrameLength = max_frame_length
        self.streamblock_obj_1.StepFrameLength = step_size

        streamblock1 = template_obj.configure_stream_block(self.streamblock_obj_1, port_1)
        fun_test.test_assert(streamblock1, "Creating streamblock on port %s" % port_1)

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=self.streamblock_obj_1.spirent_handle,
                                                               source_mac=l2_config['source_mac'],
                                                               destination_mac=l2_config['destination_mac'],
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Adding source and destination mac")

        # Adding Ip address and gateway
        ip = template_obj.stc_manager.configure_ip_address(streamblock=self.streamblock_obj_1.spirent_handle,
                                                           source=l3_config['source_ip1'],
                                                           destination=l3_config['destination_ip1'],
                                                           gateway=l3_config['gateway'])
        fun_test.test_assert(ip, "Adding source ip, dest ip and gateway")

        # Create streamblock 2
        self.streamblock_obj_2 = StreamBlock()
        self.streamblock_obj_2.LoadUnit = StreamBlock.LOAD_UNIT_MEGABITS_PER_SECOND
        self.streamblock_obj_2.Load = load
        self.streamblock_obj_2.FillType = StreamBlock.FILL_TYPE_PRBS
        self.streamblock_obj_2.InsertSig = True
        self.streamblock_obj_2.FrameLengthMode = StreamBlock.FRAME_LENGTH_MODE_RANDOM
        self.streamblock_obj_2.MinFrameLength = min_frame_length_ipv4
        self.streamblock_obj_2.MaxFrameLength = max_frame_length
        self.streamblock_obj_2.StepFrameLength = step_size

        streamblock2 = template_obj.configure_stream_block(self.streamblock_obj_2, port_2)
        fun_test.test_assert(streamblock2, "Creating streamblock on port %s" % port_2)

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=self.streamblock_obj_2.spirent_handle,
                                                               source_mac=l2_config['source_mac'],
                                                               destination_mac=l2_config['destination_mac'],
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Adding source and destination mac")

        # Adding Ip address and gateway
        ip = template_obj.stc_manager.configure_ip_address(streamblock=self.streamblock_obj_2.spirent_handle,
                                                           source=l3_config['source_ip2'],
                                                           destination=l3_config['destination_ip2'],
                                                           gateway=l3_config['gateway'])
        fun_test.test_assert(ip, "Adding source ip, dest ip and gateway")

        # Setting generator config
        gen_config_obj.StepSize = self.generator_step_size
        config_obj = template_obj.configure_generator_config(port_handle=port_1,
                                                             generator_config_obj=gen_config_obj)
        fun_test.test_assert(config_obj,
                             "Updating generator config step to %s on port %s" % (self.generator_step_size, port_1))

        config_obj = template_obj.configure_generator_config(port_handle=port_2,
                                                             generator_config_obj=gen_config_obj)
        fun_test.test_assert(config_obj,
                             "Updating generator config step to %s on port %s" % (self.generator_step_size, port_1))

    def cleanup(self):
        fun_test.log("In testcase cleanup")

        fun_test.log("Deleting streamblock %s and %s" % (self.streamblock_obj_1.spirent_handle,
                                                         self.streamblock_obj_2.spirent_handle))
        template_obj.delete_streamblocks(streamblock_handle_list=[self.streamblock_obj_1.spirent_handle,
                                                                  self.streamblock_obj_2.spirent_handle])

        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

    def run(self):
        # Execute traffic
        psw_stats = network_controller_obj.peek_psw_global_stats()

        start = template_obj.enable_generator_configs(generator_configs=[gen_obj_1, gen_obj_2])
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic for %s seconds" % duration_seconds, seconds=duration_seconds)

        # Get results for streamblock 1
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            self.streamblock_obj_1.spirent_handle))
        tx_results_1 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=self.streamblock_obj_1.spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            self.streamblock_obj_1.spirent_handle))
        rx_results_1 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=self.streamblock_obj_1.spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        # Get streambllock 2 results
        fun_test.log(
            "Fetching tx results for subscribed object %s for stream %s" % (subscribe_results['tx_subscribe'],
                                                                            self.streamblock_obj_2.spirent_handle))
        tx_results_2 = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=self.streamblock_obj_2.spirent_handle,
            subscribe_handle=subscribe_results['tx_subscribe'])

        fun_test.log(
            "Fetching rx results for subscribed object %s for stream %s" % (subscribe_results['rx_subscribe'],
                                                                            self.streamblock_obj_2.spirent_handle))
        rx_results_2 = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=self.streamblock_obj_2.spirent_handle,
            subscribe_handle=subscribe_results['rx_subscribe'])

        fun_test.log("Fetching rx port results for subscribed object %s" % subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results_2 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_2, subscribe_handle=subscribe_results['analyzer_subscribe'])

        fun_test.log("Fetching rx port results for subscribed object %s" % subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results_1 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_1, subscribe_handle=subscribe_results['analyzer_subscribe'])

        dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1)
        dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2)

        # Fetch psw global stats
        psw_stats = network_controller_obj.peek_psw_global_stats()

        fun_test.log("Tx 1 Results %s " % tx_results_1)
        fun_test.log("Rx 1 Results %s" % rx_results_1)
        fun_test.log("Tx 2 Results %s " % tx_results_2)
        fun_test.log("Rx 2 Results %s" % rx_results_2)
        fun_test.log("Rx Port Analyzer Results %s" % rx_port_analyzer_results_1)
        fun_test.log("Rx Port Analyzer Results %s" % rx_port_analyzer_results_2)
        fun_test.log("DUT Port 1 Results: %s" % dut_port_1_results)
        fun_test.log("DUT Port 2 Results: %s" % dut_port_2_results)

        fun_test.test_assert(dut_port_1_results, message="Ensure stats are obtained for %s" % dut_port_1)
        fun_test.test_assert(dut_port_2_results, message="Ensure stats are obtained for %s" % dut_port_2)

        dut_port_1_transmit = get_dut_output_stats_value(dut_port_1_results, FRAMES_TRANSMITTED_OK)
        dut_port_2_transmit = get_dut_output_stats_value(dut_port_2_results, FRAMES_TRANSMITTED_OK)
        dut_port_1_receive = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)
        dut_port_2_receive = get_dut_output_stats_value(dut_port_2_results, FRAMES_RECEIVED_OK, tx=False)

        fun_test.test_assert(template_obj.compare_result_attribute(tx_results_1, rx_results_1),
                             "Check FrameCount for streamblock %s" % self.streamblock_obj_1.spirent_handle)
        fun_test.test_assert(template_obj.compare_result_attribute(tx_results_2, rx_results_2),
                             "Check FrameCount for streamblock %s" % self.streamblock_obj_2.spirent_handle)

        fun_test.test_assert_expected(expected=int(dut_port_1_receive), actual=int(dut_port_2_transmit),
                                      message="Ensure frames received on DUT port %s are transmitted from DUT port %s"
                                              % (dut_port_1, dut_port_2))

        fun_test.test_assert_expected(expected=int(dut_port_2_receive), actual=int(dut_port_1_transmit),
                                      message="Ensure frames received on DUT port %s are transmitted from DUT port %s"
                                              % (dut_port_2, dut_port_1))

        fun_test.test_assert_expected(expected=int(dut_port_2_transmit), actual=int(rx_results_1['FrameCount']),
                                      message="Ensure frames transmitted from DUT and counter on spirent match")

        fun_test.test_assert_expected(expected=int(dut_port_1_transmit), actual=int(rx_results_2['FrameCount']),
                                      message="Ensure frames transmitted from DUT and counter on spirent match")

        zero_counter_seen = template_obj.check_non_zero_error_count(rx_port_analyzer_results_1)
        fun_test.test_assert(zero_counter_seen['result'], "Check for error counters on port2")

        zero_counter_seen = template_obj.check_non_zero_error_count(rx_port_analyzer_results_2)
        fun_test.test_assert(zero_counter_seen['result'], "Check for error counters on port1")
        '''
        fetch_list = []
        different = False
        fwd_frv = 'fwd_frv'
        ct_pkt = 'ct_pkt'
        fetch_list = [fwd_frv, ct_pkt]
        dut_port_1_fpg_value = get_fpg_port_value(dut_port_1)
        dut_port_2_fpg_value = get_fpg_port_value(dut_port_2)
        if not dut_port_1_fpg_value == dut_port_2_fpg_value:
            different = True
            ifpg1 = 'ifpg' + str(dut_port_1_fpg_value) + '_pkt'
            fpg1 = 'fpg' + str(dut_port_1_fpg_value) + '_pkt'
            ifpg2 = 'ifpg' + str(dut_port_2_fpg_value) + '_pkt'
            fpg2 = 'fpg' + str(dut_port_2_fpg_value) + '_pkt'
            fetch_list_1 = [ifpg1, fpg1, ifpg2, fpg2]
            fetch_list.extend(fetch_list_1)
        else:
            fetch_list.append('ifpg' + str(dut_port_1_fpg_value) + '_pkt')
            fetch_list.append('fpg' + str(dut_port_1_fpg_value) + '_pkt')

        psw_fetched_output = get_psw_global_stats_values(psw_stats, fetch_list)
        if different:
            ifpg = int(psw_fetched_output[ifpg1]) + int(psw_fetched_output[ifpg2])
            del psw_fetched_output[ifpg1]
            del psw_fetched_output[ifpg2]
            fpg = int(psw_fetched_output[fpg1]) + int(psw_fetched_output[fpg2])
            del psw_fetched_output[fpg1]
            del psw_fetched_output[fpg2]
            psw_fetched_output['ifpg'] = ifpg
            psw_fetched_output['fpg'] = fpg

        for key in fetch_list:
            fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']) + int(tx_results_2['FrameCount']),
                                          actual=psw_fetched_output[key],
                                          message="Check counter %s in psw global stats" % key)
        '''


class IPv6RandomTestCase2(IPv4RandomTestCase2):
    min_frame_size = min_frame_length_ipv6
    generator_step_size = generator_step_ipv6

    def describe(self):
        self.set_test_details(id=2,
                              summary="Test large random frame size (IPv6)",
                              steps="""
                              1. Create Streams with following settings
                                 a. Load: 5 Mbps
                                 b. Payload Fill Type: PRBS
                                 c. Insert signature True
                                 d. Frame Size Mode: Random min: %d max: %d step: %d
                              2. Start traffic for %d secs 
                              3. Compare Tx and Rx results for frame count for each stream
                              4. Check for error counters. there must be no error counter
                              5. Check ok frames on dut ingress and egress counter match and spirent
                              6. Check psw stats for fwd_frv, ct_pkt, ifpg_pkt, fpg_pkt 
                              """ % (78, max_frame_length, step_size, duration_seconds))

    def setup(self):
        # Clear port results on DUT
        clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
        fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

        clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
        fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

        #  Read loads from file
        file_path = fun_test.get_script_parent_directory() + "/" + loads_file
        output = fun_test.parse_file_to_json(file_path)
        load = output[dut_config['interface_mode']]["incremental_load_mbps"]
        l2_config = spirent_config["l2_config"]
        l3_config = spirent_config["l3_config"]["ipv6"]
        ether_type = Ethernet2Header.INTERNET_IPV6_ETHERTYPE

        # Create streamblock 1
        self.streamblock_obj_1 = StreamBlock()
        self.streamblock_obj_1.LoadUnit = StreamBlock.LOAD_UNIT_MEGABITS_PER_SECOND
        self.streamblock_obj_1.Load = load
        self.streamblock_obj_1.FillType = StreamBlock.FILL_TYPE_PRBS
        self.streamblock_obj_1.InsertSig = True
        self.streamblock_obj_1.FrameLengthMode = StreamBlock.FRAME_LENGTH_MODE_RANDOM
        self.streamblock_obj_1.MinFrameLength = min_frame_length_ipv6
        self.streamblock_obj_1.MaxFrameLength = max_frame_length
        self.streamblock_obj_1.StepFrameLength = step_size

        streamblock1 = template_obj.configure_stream_block(stream_block_obj=self.streamblock_obj_1,
                                                           port_handle=port_1, ip_header_version=6)
        fun_test.test_assert(streamblock1, "Creating streamblock on port %s" % port_1)

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=self.streamblock_obj_1.spirent_handle,
                                                               source_mac=l2_config['source_mac'],
                                                               destination_mac=l2_config['destination_mac'],
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Adding source and destination mac")

        # Adding Ip address and gateway
        ip = template_obj.stc_manager.configure_ip_address(streamblock=self.streamblock_obj_1.spirent_handle,
                                                           source=l3_config['source_ip1'],
                                                           destination=l3_config['destination_ip1'])
        fun_test.test_assert(ip, "Adding source ip, dest ip and gateway")

        # Create streamblock 2
        self.streamblock_obj_2 = StreamBlock()
        self.streamblock_obj_2.LoadUnit = StreamBlock.LOAD_UNIT_MEGABITS_PER_SECOND
        self.streamblock_obj_2.Load = load
        self.streamblock_obj_2.FillType = StreamBlock.FILL_TYPE_PRBS
        self.streamblock_obj_2.InsertSig = True
        self.streamblock_obj_2.FrameLengthMode = StreamBlock.FRAME_LENGTH_MODE_RANDOM
        self.streamblock_obj_2.MinFrameLength = min_frame_length_ipv6
        self.streamblock_obj_2.MaxFrameLength = max_frame_length
        self.streamblock_obj_2.StepFrameLength = step_size

        streamblock2 = template_obj.configure_stream_block(stream_block_obj=self.streamblock_obj_2,
                                                           port_handle=port_2, ip_header_version=6)
        fun_test.test_assert(streamblock2, "Creating streamblock on port %s" % port_2)

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=self.streamblock_obj_2.spirent_handle,
                                                               source_mac=l2_config['source_mac'],
                                                               destination_mac=l2_config['destination_mac'],
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Adding source and destination mac")

        # Adding Ip address and gateway
        ip = template_obj.stc_manager.configure_ip_address(streamblock=self.streamblock_obj_2.spirent_handle,
                                                           source=l3_config['source_ip2'],
                                                           destination=l3_config['destination_ip2'])
        fun_test.test_assert(ip, "Adding source ip, dest ip and gateway")

        # Setting generator config
        gen_config_obj.StepSize = self.generator_step_size
        config_obj = template_obj.configure_generator_config(port_handle=port_1,
                                                             generator_config_obj=gen_config_obj)
        fun_test.test_assert(config_obj,
                             "Updating generator config step to %s on port %s" % (self.generator_step_size, port_1))

        config_obj = template_obj.configure_generator_config(port_handle=port_2,
                                                             generator_config_obj=gen_config_obj)
        fun_test.test_assert(config_obj,
                             "Updating generator config step to %s on port %s" % (self.generator_step_size, port_2))

    def run(self):
        super(IPv6RandomTestCase2, self).run()

    def cleanup(self):
        super(IPv6RandomTestCase2, self).cleanup()


if __name__ == "__main__":
    test_case_mode = fun_test.get_local_setting(setting='ip_version')
    ts = SpirentSetup()
    test_case_mode = test_case_mode if test_case_mode else 6
    if test_case_mode == 6:
        ts.add_test_case(IPv6IncrementalTestCase1())
        ts.add_test_case(IPv6RandomTestCase2())
    elif test_case_mode == 4:
        ts.add_test_case(IPv4IncrementalTestCase1())
        ts.add_test_case(IPv4RandomTestCase2())
    else:
        ts.add_test_case(IPv4IncrementalTestCase1())
        ts.add_test_case(IPv4RandomTestCase2())
        ts.add_test_case(IPv6IncrementalTestCase1())
        ts.add_test_case(IPv6RandomTestCase2())
    ts.run()
