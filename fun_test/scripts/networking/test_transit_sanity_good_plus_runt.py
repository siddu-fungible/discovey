from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import SpirentEthernetTrafficTemplate, \
    StreamBlock, GeneratorConfig, Ethernet2Header, ARP
from lib.host.network_controller import NetworkController
from helper import *
from nu_config_manager import *

num_ports = 2


class SpirentSetup(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
                1. Create Spirent template
                2. Connect chassis, lab server and license server
                3. Attach Ports
                """)

    def setup(self):
        global template_obj, port_1, port_2, gen_obj, \
            gen_config_obj, network_controller_obj, dut_port_1, dut_port_2, dut_config, spirent_config, chassis_type

        dut_type = fun_test.get_local_setting(setting="dut_type")
        dut_config = nu_config_obj.read_dut_config(dut_type=dut_type)

        chassis_type = fun_test.get_local_setting(setting="chassis_type")
        spirent_config = nu_config_obj.read_traffic_generator_config()

        fun_test.log("Creating Template object")
        template_obj = SpirentEthernetTrafficTemplate(session_name="mac-sanity", spirent_config=spirent_config,
                                                      chassis_type=chassis_type)
        fun_test.test_assert(template_obj, "Create template object")

        result = template_obj.setup(no_of_ports_needed=num_ports)
        fun_test.test_assert(result['result'], "Configure setup")

        port_1 = result['port_list'][0]
        port_2 = result['port_list'][1]

        # Create network controller object
        dpcsh_server_ip = dut_config["dpcsh_tcp_proxy_ip"]
        dpcsh_server_port = dut_config['dpcsh_tcp_proxy_port']
        if dut_config['enable_dpcsh']:
            network_controller_obj = NetworkController(dpc_server_ip=dpcsh_server_ip, dpc_server_port=dpcsh_server_port)
        dut_port_1 = dut_config["ports"][0]
        dut_port_2 = dut_config['ports'][1]

        # Configure Generator
        gen_config_obj = GeneratorConfig()
        gen_config_obj.Duration = 30
        gen_config_obj.SchedulingMode = gen_config_obj.SCHEDULING_MODE_RATE_BASED
        gen_config_obj.DurationMode = gen_config_obj.DURATION_MODE_SECONDS
        gen_config_obj.AdvancedInterleaving = True

        gen_obj = template_obj.stc_manager.get_generator(port_handle=port_1)

        config_obj = template_obj.configure_generator_config(port_handle=port_1,
                                                             generator_config_obj=gen_config_obj)
        fun_test.test_assert(config_obj, "Creating generator config")

        # Applying configuration
        apply = template_obj.stc_manager.apply_configuration()
        fun_test.test_assert(apply, "Applying Generator config")

    def cleanup(self):
        fun_test.test_assert(template_obj.cleanup(), "Cleaning up session")


class IPv4GoodRuntTestCase3(FunTestCase):
    streamblock_obj = None
    subscribe_results = None
    duration_seconds = 30

    def describe(self):
        self.set_test_details(id=1,
                              summary="Creating good and runt IPv4 streamblock",
                              steps="""
                        1. Create streamblock with following settings
                           a. Load: 17000 fps
                           b. Payload Fill Type: PRBS
                           c. Insert signature
                           d. Frame Size Mode: Random Min: 40 Max: 70
                        2. Start traffic for 30 secs 
                        3. Runts must be dropped and good frames must be received
                        4. Ensure count of good frames + undersize generated match tx of stream.
                        5. Ensure runts are not transmitted from dut egress.
                        6. Ensure dut egress receives undersize frames
                        """)

    def setup(self):
        # Clear port results on DUT
        if dut_config['enable_dpcsh']:
            clear_1 = network_controller_obj.clear_port_stats(port_num=dut_port_1)
            fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

            clear_2 = network_controller_obj.clear_port_stats(port_num=dut_port_2)
            fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

        load = 17000
        self.streamblock_obj = StreamBlock()
        self.streamblock_obj.LoadUnit = self.streamblock_obj.LOAD_UNIT_FRAMES_PER_SECOND
        self.streamblock_obj.Load = load
        self.streamblock_obj.FillType = self.streamblock_obj.FILL_TYPE_PRBS
        self.streamblock_obj.InsertSig = False
        self.streamblock_obj.FrameLengthMode = self.streamblock_obj.FRAME_LENGTH_MODE_RANDOM
        self.streamblock_obj.MinFrameLength = 40
        self.streamblock_obj.MaxFrameLength = 70

        # Change generator config parameters
        gen_config_obj.Duration = self.duration_seconds
        config_obj = template_obj.configure_generator_config(port_handle=port_1,
                                                             generator_config_obj=gen_config_obj)
        fun_test.test_assert(config_obj, "Creating generator config")

        l2_config = spirent_config["l2_config"]
        l3_config = spirent_config["l3_config"]["ipv4"]
        ether_type = Ethernet2Header.INTERNET_IP_ETHERTYPE

        # Create streamblock
        streamblock1 = template_obj.configure_stream_block(self.streamblock_obj, port_1)
        fun_test.test_assert(streamblock1, "Creating streamblock on port %s" % port_1)

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=self.streamblock_obj.spirent_handle,
                                                               source_mac=l2_config['source_mac'],
                                                               destination_mac=l2_config['destination_mac'],
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Adding source and destination mac")

        # Adding Ip address and gateway
        ip = template_obj.stc_manager.configure_ip_address(streamblock=self.streamblock_obj.spirent_handle,
                                                           source=l3_config['source_ip1'],
                                                           destination=l3_config['destination_ip1'],
                                                           gateway=l3_config['gateway'])
        fun_test.test_assert(ip, "Adding source ip, dest ip and gateway")

    def cleanup(self):
        fun_test.log("In testcase cleanup")
        fun_test.log("Deleting streamblock %s " % self.streamblock_obj.spirent_handle)
        template_obj.delete_streamblocks(streamblock_handle_list=[self.streamblock_obj.spirent_handle])
        if self.subscribe_results:
            # clear port results
            port_results = template_obj.stc_manager.clear_all_port_results(port_list=[port_1, port_2])
            fun_test.simple_assert(port_results, "Clear port results")

    def run(self):
        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=gen_obj)
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=self.duration_seconds)

        # Subscribe to results
        project = template_obj.stc_manager.get_project_handle()
        self.subscribe_results = template_obj.subscribe_to_all_results(parent=project)
        fun_test.test_assert(self.subscribe_results['result'], "Subscribing to results")

        fun_test.log("Fetching tx results for subscribed object %s" % self.subscribe_results['tx_subscribe'])
        tx_results = template_obj.stc_manager.get_tx_stream_block_results(
            stream_block_handle=self.streamblock_obj.spirent_handle,
            subscribe_handle=self.subscribe_results['tx_subscribe'])

        fun_test.log("Fetching rx results for subscribed object %s" % self.subscribe_results['rx_subscribe'])
        rx_results = template_obj.stc_manager.get_rx_stream_block_results(
            stream_block_handle=self.streamblock_obj.spirent_handle,
            subscribe_handle=self.subscribe_results['rx_subscribe'])

        fun_test.log("Fetching rx port results for subscribed object %s" % self.subscribe_results['generator_subscribe'])
        tx_port_generator_results = template_obj.stc_manager.get_generator_port_results(
            port_handle=port_1, subscribe_handle=self.subscribe_results['generator_subscribe'])

        fun_test.log("Fetching tx port results for subscribed object %s" % self.subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=port_2, subscribe_handle=self.subscribe_results['analyzer_subscribe'])
        dut_port_2_results = None
        dut_port_1_results = None
        dut_port_2_transmit = None
        dut_port_1_undersize_pkts = None
        if dut_config['enable_dpcsh']:
            dut_port_2_results = network_controller_obj.peek_fpg_port_stats(dut_port_2)
            dut_port_1_results = network_controller_obj.peek_fpg_port_stats(dut_port_1)
            dut_port_2_transmit = get_dut_output_stats_value(dut_port_2_results, FRAMES_TRANSMITTED_OK)
            dut_port_1_undersize_pkts = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_UNDERSIZE_PKTS,
                                                                   tx=False)
            fun_test.log("DUT Port 1 Results: %s" % dut_port_1_results)
            fun_test.log("DUT Port 2 Results: %s" % dut_port_2_results)

        fun_test.log("Tx Results %s " % tx_results)
        fun_test.log("Rx Results %s " % rx_results)
        fun_test.log("Tx Generator resukts %s" % tx_port_generator_results)
        fun_test.log("Rx Port Analyzer Results %s" % rx_port_analyzer_results)

        fun_test.test_assert_expected(expected=int(tx_results['FrameCount']),
                                      actual=int(tx_port_generator_results['GeneratorUndersizeFrameCount']) + int(
                                          rx_port_analyzer_results['TotalFrameCount']),
                                      message="Ensure transmitted match with undersize + received")

        fun_test.test_assert_expected(expected=0, actual=int(rx_port_analyzer_results['FcsErrorFrameCount']),
                                      message="Ensure no FCS errors are seen")
        if dut_config['enable_dpcsh']:
            fun_test.test_assert(dut_port_2_results, message="Ensure stats are obtained for %s" % dut_port_2)

            fun_test.test_assert_expected(actual=int(dut_port_2_transmit),
                                          expected=int(rx_port_analyzer_results['TotalFrameCount']),
                                          message="Ensure frames transmitted is None")

            fun_test.test_assert(dut_port_1_results, message="Ensure stats are obtained for %s" % dut_port_1)

            fun_test.test_assert_expected(expected=int(tx_port_generator_results['GeneratorUndersizeFrameCount']),
                                          actual=int(dut_port_1_undersize_pkts),
                                          message="Ensure packets are marked undersize on rx port of dut")


if __name__ == "__main__":
    ts = SpirentSetup()

    ts.add_test_case(IPv4GoodRuntTestCase3())
    ts.run()
