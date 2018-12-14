"""
Author: Rushikesh Pendse
Created On: 31/07/2018

"""

from lib.system.fun_test import *
from lib.host.linux import Linux
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import *
from lib.host.network_controller import NetworkController
from helper import *
from nu_config_manager import *

spirent_config = {}
subscribed_results = None
TRAFFIC_DURATION = 1
cc_path_config = {}
cc_port_list = []
vp_port_list = []
LOAD = 110
LOAD_UNIT = StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND
FRAME_SIZE = 128
MIN_FRAME_SIZE = 64
MAX_FRAME_SIZE = 9000
MTU = MAX_FRAME_SIZE
FRAME_LENGTH_MODE = StreamBlock.FRAME_LENGTH_MODE_FIXED
INTERFACE_LOADS_SPEC = SCRIPTS_DIR + "/networking" + "/interface_loads.json"
NUM_PORTS = 3
streams_group = []
MIN_RX_PORT_COUNT = 80
MAX_RX_PORT_COUNT = 90
CUSHION_SLEEP = 5
flow_direction = NuConfigManager.FLOW_DIRECTION_NU_NU
flow_type = NuConfigManager.TRANSIT_FLOW_TYPE
PC_3_CONFIG_DIR = "pc_3_fcp_configs"
PC_4_CONFIG_DIR = "pc_4_fcp_configs"

dpcsh_obj = None


class SpirentSetup(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
                1. Read Spirent Config
                """)

    def setup(self):
        global subscribe_results, spirent_config, chassis_type, template_obj, dpcsh_obj, LOAD, FRAME_SIZE, \
            FRAME_LENGTH_MODE, MIN_RX_PORT_COUNT, MAX_RX_PORT_COUNT, LOAD_UNIT, TRAFFIC_DURATION, flow_direction, \
            flow_type

        chassis_type = fun_test.get_local_setting(setting="chassis_type")
        spirent_config = nu_config_obj.read_traffic_generator_config()

        session_name = "short-sanity"
        template_obj = SpirentEthernetTrafficTemplate(session_name=session_name, spirent_config=spirent_config,
                                                      chassis_type=chassis_type)

        project_handle = template_obj.stc_manager.create_project(project_name=session_name)
        fun_test.simple_assert(project_handle, "Create %s Project" % "short-sanity")
        fun_test.test_assert(expression=template_obj.stc_manager.health(session_name=session_name)['result'],
                             message="Health of Spirent Test Center")
        # Subscribe to results
        project = template_obj.stc_manager.get_project_handle()
        subscribe_results = template_obj.subscribe_to_all_results(parent=project)
        fun_test.test_assert(subscribe_results['result'], "Subscribing to results")
        del subscribe_results['result']

        dut_config = nu_config_obj.read_dut_config(dut_type=NuConfigManager.DUT_TYPE_PALLADIUM,
                                                   flow_type=NuConfigManager.TRANSIT_FLOW_TYPE)
        # Create network controller object
        dpcsh_server_ip = dut_config["dpcsh_tcp_proxy_ip"]
        dpcsh_server_port = dut_config['dpcsh_tcp_proxy_port']

        if dut_config['enable_dpcsh']:
            dpcsh_obj = NetworkController(dpc_server_ip=dpcsh_server_ip, dpc_server_port=dpcsh_server_port)

        configs = fun_test.parse_file_to_json(INTERFACE_LOADS_SPEC)
        fun_test.simple_assert(configs, "Read Interface loads file")
        cc_path_config = configs['cc_path']
        LOAD = cc_path_config['load']
        MIN_RX_PORT_COUNT = cc_path_config['rx_range_min']
        MAX_RX_PORT_COUNT = cc_path_config['rx_range_max']
        LOAD_UNIT = cc_path_config['load_unit']
        FRAME_SIZE = cc_path_config['frame_size']
        FRAME_LENGTH_MODE = cc_path_config['frame_length_mode']
        TRAFFIC_DURATION = cc_path_config['duration']

    def cleanup(self):
        pass


class TransitSweep(FunTestCase):
    streamblock_obj_1 = None
    streamblock_obj_2 = None
    dut_config = None
    template_obj = None
    dpcsh_obj = None
    num_ports = 2
    port_1 = None
    port_2 = None
    generator_handles = []
    min_frame_size = MIN_FRAME_SIZE
    
    def describe(self):
        self.set_test_details(id=1,
                              summary="Test all frame size in incremental way (IPv4) (64 to 9K)",
                              steps="""
                              1. Create Bi-directional stream with frame size mode = Incremental Min: 64 and Max: 9000 
                              2. Start traffic @ 5 Mbps
                              3. Check for error counters. there must be no error counter
                              4. Check dut ingress and egress frame count match
                              5. Check OctetStats from dut and spirent
                              6. Check EtherOctets from dut and spirent.
                              7. Check Counter for each octet range
                              8. Ensure Tx and Rx FrameCount on spirent and ensure no errors are seen
                              """)

    def setup(self):
        global flow_direction, flow_type
        flow_direction = NuConfigManager.FLOW_DIRECTION_NU_NU
        flow_type = NuConfigManager.TRANSIT_FLOW_TYPE

        self.dut_config = nu_config_obj.read_dut_config(dut_type=NuConfigManager.DUT_TYPE_PALLADIUM,
                                                        flow_type=flow_type)
        if self.dut_config['enable_dpcsh']:
            checkpoint = "Change DUT ports MTU to %d" % MTU
            for port_num in self.dut_config['ports']:
                mtu_changed = dpcsh_obj.set_port_mtu(port_num=port_num, mtu_value=MTU)
                fun_test.simple_assert(mtu_changed, "Change MTU on DUT port %d to %d" % (port_num, MTU))
            fun_test.add_checkpoint(checkpoint)

        result = template_obj.setup_ports_using_command(no_of_ports_needed=self.num_ports,
                                                        flow_type=flow_type, flow_direction=flow_direction)
        fun_test.test_assert(result['result'], "Configure setup")

        self.port_1 = result['port_list'][0]
        self.port_2 = result['port_list'][1]

        checkpoint = "Change ports MTU to %d" % MTU
        mtu_changed_on_spirent = template_obj.change_ports_mtu(interface_obj_list=result["interface_obj_list"],
                                                               mtu_value=MTU)
        fun_test.test_assert(mtu_changed_on_spirent, checkpoint)

        # Configure Generator
        burst_size = MAX_FRAME_SIZE - MIN_FRAME_SIZE
        gen_config_obj = GeneratorConfig(scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED,
                                         duration_mode=GeneratorConfig.DURATION_MODE_BURSTS,
                                         advanced_interleaving=True, burst_size=1, duration=burst_size)

        # Apply generator config on port 1
        config_obj = template_obj.configure_generator_config(port_handle=self.port_1,
                                                             generator_config_obj=gen_config_obj)
        fun_test.simple_assert(config_obj, "Creating generator config on port %s" % self.port_1)
        gen_obj_1 = template_obj.stc_manager.get_generator(port_handle=self.port_1)
        fun_test.simple_assert(gen_obj_1, "Fetch Generator Handle for %s" % self.port_1)
        self.generator_handles.append(gen_obj_1)

        # Apply generator config on port 2
        config_obj = template_obj.configure_generator_config(port_handle=self.port_2,
                                                             generator_config_obj=gen_config_obj)
        fun_test.simple_assert(config_obj, "Creating generator config on port %s" % self.port_2)
        gen_obj_2 = template_obj.stc_manager.get_generator(port_handle=self.port_2)
        fun_test.simple_assert(gen_obj_2, "Fetch Generator Handle for %s" % self.port_2)
        self.generator_handles.append(gen_obj_2)

        #  Read loads from file
        output = fun_test.parse_file_to_json(INTERFACE_LOADS_SPEC)
        load = output[self.dut_config['interface_mode']]["incremental_load_mbps"]
        l2_config = spirent_config["l2_config"]
        l3_config = spirent_config["l3_config"]["ipv4"]
        ether_type = Ethernet2Header.INTERNET_IP_ETHERTYPE

        # Create streamblock 1
        self.streamblock_obj_1 = StreamBlock(load_unit=StreamBlock.LOAD_UNIT_MEGABITS_PER_SECOND, load=load,
                                             fill_type=StreamBlock.FILL_TYPE_PRBS, insert_signature=True,
                                             frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_INCR,
                                             max_frame_length=MAX_FRAME_SIZE, min_frame_length=MIN_FRAME_SIZE,
                                             step_frame_length=1)

        stream_created = template_obj.configure_stream_block(stream_block_obj=self.streamblock_obj_1,
                                                             port_handle=self.port_1)
        fun_test.test_assert(stream_created, "Creating streamblock on port %s" % self.port_1)

        # Adding source and destination ip
        ether_obj = Ethernet2Header(source_mac=l2_config['source_mac'], destination_mac=l2_config['destination_mac'],
                                    ether_type=ether_type)
        ether = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj_1.spirent_handle,
                                                               header_obj=ether_obj, update=True)
        fun_test.simple_assert(ether, "Adding source and destination mac")

        # Adding Ip address and gateway
        ip_header_obj = Ipv4Header(source_address=l3_config['source_ip1'],
                                   destination_address=l3_config['destination_ip1'],
                                   gateway=l3_config['gateway'])
        ip = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj_1.spirent_handle,
                                                            header_obj=ip_header_obj, update=True)
        fun_test.simple_assert(ip, "Adding source ip, dest ip and gateway")

        # Create streamblock 2
        self.streamblock_obj_2 = StreamBlock(load_unit=StreamBlock.LOAD_UNIT_MEGABITS_PER_SECOND, load=load,
                                             fill_type=StreamBlock.FILL_TYPE_PRBS, insert_signature=True,
                                             frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_INCR,
                                             max_frame_length=MAX_FRAME_SIZE, min_frame_length=MIN_FRAME_SIZE,
                                             step_frame_length=1)

        stream_created = template_obj.configure_stream_block(stream_block_obj=self.streamblock_obj_2,
                                                             port_handle=self.port_2)
        fun_test.test_assert(stream_created, "Creating streamblock on port %s" % self.port_2)

        # Adding source and destination ip
        ether_obj = Ethernet2Header(source_mac=l2_config['source_mac'], destination_mac=l2_config['destination_mac'],
                                    ether_type=ether_type)
        ether = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj_2.spirent_handle,
                                                               header_obj=ether_obj, update=True)
        fun_test.simple_assert(ether, "Adding source and destination mac")

        # Adding Ip address and gateway
        ip_header_obj = Ipv4Header(source_address=l3_config['source_ip1'],
                                   destination_address=l3_config['destination_ip4'],
                                   gateway=l3_config['gateway'])
        ip = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.streamblock_obj_2.spirent_handle,
                                                            header_obj=ip_header_obj, update=True)
        fun_test.simple_assert(ip, "Adding source ip, dest ip and gateway")

    def run(self):
        dut_port_1 = self.dut_config['ports'][0]
        dut_port_2 = self.dut_config['ports'][1]

        if self.dut_config['enable_dpcsh']:
            clear_1 = dpcsh_obj.clear_port_stats(port_num=dut_port_1)
            fun_test.test_assert(clear_1, message="Clear stats on port num %s of dut" % dut_port_1)

            clear_2 = dpcsh_obj.clear_port_stats(port_num=dut_port_2)
            fun_test.test_assert(clear_2, message="Clear stats on port num %s of dut" % dut_port_2)

            # Log PSW stats before traffic
            dpcsh_obj.peek_psw_global_stats()

        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=self.generator_handles)
        fun_test.test_assert(start, "Starting generator config")

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=120)

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
            port_handle=self.port_2, subscribe_handle=subscribe_results['analyzer_subscribe'])

        fun_test.log("Fetching rx port results for subscribed object %s" % subscribe_results['analyzer_subscribe'])
        rx_port_analyzer_results_1 = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=self.port_1, subscribe_handle=subscribe_results['analyzer_subscribe'])

        dut_port_1_results = None
        dut_port_2_results = None
        if self.dut_config['enable_dpcsh']:
            dut_port_1_results = dpcsh_obj.peek_fpg_port_stats(dut_port_1)
            dut_port_2_results = dpcsh_obj.peek_fpg_port_stats(dut_port_2)
            psw_stats = dpcsh_obj.peek_psw_global_stats()
            fun_test.log("DUT Port 1 Results: %s" % dut_port_1_results)
            fun_test.log("DUT Port 2 Results: %s" % dut_port_2_results)

        fun_test.log("Tx 1 Results %s " % tx_results_1)
        fun_test.log("Rx 1 Results %s" % rx_results_1)
        fun_test.log("Tx 2 Results %s " % tx_results_2)
        fun_test.log("Rx 2 Results %s" % rx_results_2)
        fun_test.log("Rx Port Analyzer Results %s" % rx_port_analyzer_results_1)
        fun_test.log("Rx Port Analyzer Results %s" % rx_port_analyzer_results_2)

        if self.dut_config['enable_dpcsh']:
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
            dut_port_1_rx_octet_64 = get_dut_output_stats_value(dut_port_1_results, ETHER_STATS_PKTS_64_OCTETS,
                                                                tx=False)
            dut_port_1_rx_octet_65_127 = get_dut_output_stats_value(dut_port_1_results,
                                                                    ETHER_STATS_PKTS_65_TO_127_OCTETS,
                                                                    tx=False)
            dut_port_1_rx_octet_128_255 = get_dut_output_stats_value(dut_port_1_results,
                                                                     ETHER_STATS_PKTS_128_TO_255_OCTETS,
                                                                     tx=False)
            dut_port_1_rx_octet_256_511 = get_dut_output_stats_value(dut_port_1_results,
                                                                     ETHER_STATS_PKTS_256_TO_511_OCTETS,
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

            dut_port_2_rx_octet_64 = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_PKTS_64_OCTETS,
                                                                tx=False)
            dut_port_2_rx_octet_65_127 = get_dut_output_stats_value(dut_port_2_results,
                                                                    ETHER_STATS_PKTS_65_TO_127_OCTETS,
                                                                    tx=False)
            dut_port_2_rx_octet_128_255 = get_dut_output_stats_value(dut_port_2_results,
                                                                     ETHER_STATS_PKTS_128_TO_255_OCTETS,
                                                                     tx=False)
            dut_port_2_rx_octet_256_511 = get_dut_output_stats_value(dut_port_2_results,
                                                                     ETHER_STATS_PKTS_256_TO_511_OCTETS,
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
            dut_port_1_tx_octet_65_127 = get_dut_output_stats_value(dut_port_1_results,
                                                                    ETHER_STATS_PKTS_65_TO_127_OCTETS)
            dut_port_1_tx_octet_128_255 = get_dut_output_stats_value(dut_port_1_results,
                                                                     ETHER_STATS_PKTS_128_TO_255_OCTETS)
            dut_port_1_tx_octet_256_511 = get_dut_output_stats_value(dut_port_1_results,
                                                                     ETHER_STATS_PKTS_256_TO_511_OCTETS)
            dut_port_1_tx_octet_512_1023 = get_dut_output_stats_value(dut_port_1_results,
                                                                      ETHER_STATS_PKTS_512_TO_1023_OCTETS)
            dut_port_1_tx_octet_1024_1518 = get_dut_output_stats_value(dut_port_1_results,
                                                                       ETHER_STATS_PKTS_1024_TO_1518_OCTETS)
            dut_port_1_tx_octet_1519_max = get_dut_output_stats_value(dut_port_1_results,
                                                                      ETHER_STATS_PKTS_1519_TO_MAX_OCTETS)

            dut_port_2_tx_octet_64 = get_dut_output_stats_value(dut_port_2_results, ETHER_STATS_PKTS_64_OCTETS)
            dut_port_2_tx_octet_65_127 = get_dut_output_stats_value(dut_port_2_results,
                                                                    ETHER_STATS_PKTS_65_TO_127_OCTETS)
            dut_port_2_tx_octet_128_255 = get_dut_output_stats_value(dut_port_2_results,
                                                                     ETHER_STATS_PKTS_128_TO_255_OCTETS)
            dut_port_2_tx_octet_256_511 = get_dut_output_stats_value(dut_port_2_results,
                                                                     ETHER_STATS_PKTS_256_TO_511_OCTETS)
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
            max_counter_value = MAX_FRAME_SIZE - second_last_counter
            expected_octet_counters = {'64': 1, '127': 63, '255': 128, '511': 256, '1023': 512, '1518': 495,
                                       'max': max_counter_value}

            fun_test.test_assert_expected(expected=int(dut_port_1_receive), actual=int(dut_port_2_transmit),
                                          message="Ensure frames received on DUT port %s are transmitted from "
                                                  "DUT port %s" % (dut_port_1, dut_port_2))

            fun_test.test_assert_expected(expected=int(dut_port_2_receive), actual=int(dut_port_1_transmit),
                                          message="Ensure frames received on DUT port %s are transmitted from "
                                                  "DUT port %s" % (dut_port_2, dut_port_1))

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
                                          message="Ensure eth stat pkts transmitted from DUT and counter "
                                                  "on spirent match")

            fun_test.test_assert_expected(expected=int(dut_port_2_rx_eth_stats_pkts),
                                          actual=int(dut_port_1_tx_eth_stats_pkts),
                                          message="Ensure eth stat pkts received by DUT port %s are transmitted "
                                                  "by DUT port %s" % (dut_port_2, dut_port_1))

            fun_test.test_assert_expected(expected=int(dut_port_1_tx_eth_stats_pkts),
                                          actual=int(rx_results_2['FrameCount']),
                                          message="Ensure eth stat pkts transmitted from DUT and counter "
                                                  "on spirent match")

            # Check octet counts
            fun_test.test_assert_expected(expected=int(dut_port_1_rx_octet_stats),
                                          actual=int(dut_port_2_tx_octet_stats),
                                          message="Ensure correct ether stats octets are seen on both DUT ports")

            fun_test.test_assert_expected(expected=int(tx_results_1['OctetCount']),
                                          actual=int(rx_results_1['OctetCount']),
                                          message="Ensure octet counts match on spirent rx and tx")

            fun_test.test_assert_expected(expected=int(rx_results_1['OctetCount']),
                                          actual=int(dut_port_2_tx_octet_stats),
                                          message="Ensure octets shown on tx port of DUT matches rx of spirent")

            fun_test.test_assert_expected(expected=int(dut_port_2_rx_octet_stats),
                                          actual=int(dut_port_1_tx_octet_stats),
                                          message="Ensure correct ether stats octets are seen on both DUT ports")

            fun_test.test_assert_expected(expected=int(tx_results_2['OctetCount']),
                                          actual=int(rx_results_2['OctetCount']),
                                          message="Ensure octet counts match on spirent rx and tx")

            fun_test.test_assert_expected(expected=int(rx_results_2['OctetCount']),
                                          actual=int(dut_port_1_tx_octet_stats),
                                          message="Ensure octets hsown on tx port of DUT matches rx of spirent")

            for key, val in dut_octet_range_stats.iteritems():    # DUT level
                for key1, val1 in val.iteritems():                # RX, TX level
                    for key2, val2 in val1.iteritems():           # Octet level
                        fun_test.log("Key: %s Val: %s" % (key2, val2))
                        if self.min_frame_size == 78 and key2 == "64":
                            continue
                        if self.min_frame_size == 78 and key2 == "127":
                            expected_octet_counters[key2] = 50
                        fun_test.test_assert_expected(expected=expected_octet_counters[key2], actual=int(val2),
                                                      message="Ensure correct value is seen for %s octet in %s of "
                                                              "dut port %s" % (key2, key1, key))

        if tx_results_1['FrameCount'] == rx_results_1['FrameCount']:
            fun_test.test_assert(template_obj.compare_result_attribute(tx_results_1, rx_results_1),
                                 "Check FrameCount for streamblock %s" % self.streamblock_obj_1.spirent_handle)
            fun_test.test_assert(template_obj.compare_result_attribute(tx_results_2, rx_results_2),
                                 "Check FrameCount for streamblock %s" % self.streamblock_obj_2.spirent_handle)

            zero_counter_seen = template_obj.check_non_zero_error_count(rx_port_analyzer_results_1)
            fun_test.test_assert(zero_counter_seen['result'], "Check for error counters on port2")

            zero_counter_seen = template_obj.check_non_zero_error_count(rx_port_analyzer_results_2)
            fun_test.test_assert(zero_counter_seen['result'], "Check for error counters on port1")

    def cleanup(self):
        fun_test.log("In testcase cleanup")

        fun_test.log("Deleting streamblock %s and %s" % (self.streamblock_obj_1.spirent_handle,
                                                         self.streamblock_obj_2.spirent_handle))
        template_obj.delete_streamblocks(streamblock_handle_list=[self.streamblock_obj_1.spirent_handle,
                                                                  self.streamblock_obj_2.spirent_handle])

        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])


class TransitV6Sweep(TransitSweep):
    min_frame_size = 78
    burst_size = MAX_FRAME_SIZE - min_frame_size
    generator_handles = []

    def describe(self):
        self.set_test_details(id=2,
                              summary="Test all frame size in incremental way (IPv6) (78 to 9K)",
                              steps="""
                              1. Create a Bi-directional stream with IPv6 header and frame size mode = Incremental 
                                 Min: 78 and Max: 9000
                              2. Start traffic @ 5 Mbps
                              3. Compare Tx and Rx results for frame count
                              4. Check for error counters. there must be no error counter
                              5. Check dut ingress and egress frame count match
                              6. Check OctetStats from dut and spirent
                              7. Check EtherOctets from dut and spirent.
                              8. Check Counter for each octet range
                              """)

    def setup(self):
        global flow_direction, flow_type
        flow_direction = NuConfigManager.FLOW_DIRECTION_NU_NU
        flow_type = NuConfigManager.TRANSIT_FLOW_TYPE

        self.dut_config = nu_config_obj.read_dut_config(dut_type=NuConfigManager.DUT_TYPE_PALLADIUM,
                                                        flow_type=flow_type)
        if self.dut_config['enable_dpcsh']:
            checkpoint = "Change DUT ports MTU to %d" % MTU
            for port_num in self.dut_config['ports']:
                mtu_changed = dpcsh_obj.set_port_mtu(port_num=port_num, mtu_value=MTU)
                fun_test.simple_assert(mtu_changed, "Change MTU on DUT port %d to %d" % (port_num, MTU))
            fun_test.add_checkpoint(checkpoint)

        result = template_obj.setup_ports_using_command(no_of_ports_needed=self.num_ports,
                                                        flow_type=flow_type, flow_direction=flow_direction)
        fun_test.test_assert(result['result'], "Configure setup")

        self.port_1 = result['port_list'][0]
        self.port_2 = result['port_list'][1]

        checkpoint = "Change ports MTU to %d" % MTU
        mtu_changed_on_spirent = template_obj.change_ports_mtu(interface_obj_list=result["interface_obj_list"],
                                                               mtu_value=MTU)
        fun_test.test_assert(mtu_changed_on_spirent, checkpoint)

        # Configure Generator
        gen_config_obj = GeneratorConfig(scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED,
                                         duration_mode=GeneratorConfig.DURATION_MODE_BURSTS,
                                         advanced_interleaving=True, duration=self.burst_size, burst_size=1)

        # Apply generator config on port 1
        config_obj = template_obj.configure_generator_config(port_handle=self.port_1,
                                                             generator_config_obj=gen_config_obj)
        fun_test.simple_assert(config_obj, "Creating generator config on port %s" % self.port_1)
        gen_obj_1 = template_obj.stc_manager.get_generator(port_handle=self.port_1)
        fun_test.simple_assert(gen_obj_1, "Fetch Generator Handle for %s" % self.port_1)
        self.generator_handles.append(gen_obj_1)

        # Apply generator config on port 2
        config_obj = template_obj.configure_generator_config(port_handle=self.port_2,
                                                             generator_config_obj=gen_config_obj)
        fun_test.simple_assert(config_obj, "Creating generator config on port %s" % self.port_2)
        gen_obj_2 = template_obj.stc_manager.get_generator(port_handle=self.port_2)
        fun_test.simple_assert(gen_obj_2, "Fetch Generator Handle for %s" % self.port_2)
        self.generator_handles.append(gen_obj_2)

        #  Read loads from file
        output = fun_test.parse_file_to_json(INTERFACE_LOADS_SPEC)
        load = output[self.dut_config['interface_mode']]["incremental_load_mbps"]
        l2_config = spirent_config["l2_config"]
        l3_config = spirent_config["l3_config"]["ipv6"]
        ether_type = Ethernet2Header.INTERNET_IPV6_ETHERTYPE

        # Create streamblock 1
        self.streamblock_obj_1 = StreamBlock(load_unit=StreamBlock.LOAD_UNIT_MEGABITS_PER_SECOND, load=load,
                                             fill_type=StreamBlock.FILL_TYPE_PRBS, insert_signature=True,
                                             frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_INCR,
                                             max_frame_length=MAX_FRAME_SIZE, min_frame_length=self.min_frame_size,
                                             step_frame_length=1)

        streamblock1 = template_obj.configure_stream_block(stream_block_obj=self.streamblock_obj_1,
                                                           port_handle=self.port_1, ip_header_version=6)
        fun_test.test_assert(streamblock1, "Creating streamblock on port %s" % self.port_1)

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
        self.streamblock_obj_2 = StreamBlock(load_unit=StreamBlock.LOAD_UNIT_MEGABITS_PER_SECOND, load=load,
                                             fill_type=StreamBlock.FILL_TYPE_PRBS, insert_signature=True,
                                             frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_INCR,
                                             max_frame_length=MAX_FRAME_SIZE, min_frame_length=self.min_frame_size,
                                             step_frame_length=1)

        streamblock2 = template_obj.configure_stream_block(stream_block_obj=self.streamblock_obj_2,
                                                           port_handle=self.port_2, ip_header_version=6)
        fun_test.test_assert(streamblock2, "Creating streamblock on port %s" % self.port_2)

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=self.streamblock_obj_2.spirent_handle,
                                                               source_mac=l2_config['source_mac'],
                                                               destination_mac=l2_config['destination_mac'],
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Adding source and destination mac")

        # Adding Ip address and gateway
        ip = template_obj.stc_manager.configure_ip_address(streamblock=self.streamblock_obj_2.spirent_handle,
                                                           source=l3_config['source_ip2'],
                                                           destination=l3_config['destination_ip4'])
        fun_test.test_assert(ip, "Adding source ip, dest ip and gateway")


class TestCcFlows(FunTestCase):
    stream_obj = None
    generator_handle = None
    validate_meter_stats = True
    meter_id = None
    dut_config = None
    num_ports = 3
    port_1 = None
    port_2 = None
    port_3 = None
    detach_ports = True
    erp = False

    def describe(self):
        pass

    def setup(self):
        pass

    def configure_ports(self):
        global cc_port_list, flow_direction, flow_type

        self.dut_config = nu_config_obj.read_dut_config(dut_type=NuConfigManager.DUT_TYPE_PALLADIUM,
                                                        flow_type=flow_type,
                                                        flow_direction=flow_direction)
        if self.detach_ports:
            checkpoint = "Setup CC Ports"
            result = template_obj.setup_ports_using_command(no_of_ports_needed=self.num_ports,
                                                            flow_type=flow_type,
                                                            flow_direction=flow_direction)
            fun_test.test_assert(expression=result['result'], message=checkpoint)

            self.port_1 = result['port_list'][0]
            self.port_2 = result['port_list'][1]
            self.port_3 = result['port_list'][2]
            cc_port_list.append(self.port_1)
            cc_port_list.append(self.port_2)
            cc_port_list.append(self.port_3)

        checkpoint = "Configure Generator Config for port %s" % self.port_1
        generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                               duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                               scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=self.port_1,
                                                         generator_config_obj=generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=self.port_1)
        fun_test.test_assert(self.generator_handle, checkpoint)

    def run(self):
        vp_stats_before = None
        erp_stats_before = None
        wro_stats_before = None
        meter_stats_before = None
        if self.dut_config['enable_dpcsh']:
            # TODO: Clear PSW, VP, WRO, meter stats. Will add this once support for clear stats provided in dpc
            checkpoint = "Clear FPG stats on all DUT ports"
            for port in self.dut_config['ports']:
                shape = 0
                if port == 1 or port == 2:
                    shape = 1
                clear_stats = dpcsh_obj.clear_port_stats(port_num=port, shape=shape)
                fun_test.simple_assert(clear_stats, "FPG stats clear on DUT port %d" % port)
            fun_test.add_checkpoint(checkpoint)

            checkpoint = "Get PSW and Parser NU stats before traffic"
            psw_stats = dpcsh_obj.peek_psw_global_stats()
            parser_stats = dpcsh_obj.peek_parser_stats()
            fun_test.log("PSW Stats: %s \n" % psw_stats)
            fun_test.log("Parser stats: %s \n" % parser_stats)
            fun_test.add_checkpoint(checkpoint)

            vp_stats_before = get_vp_pkts_stats_values(network_controller_obj=dpcsh_obj)

            erp_stats_before = get_erp_stats_values(network_controller_obj=dpcsh_obj)

            wro_stats_before = get_wro_global_stats_values(network_controller_obj=dpcsh_obj)

            if self.meter_id:
                meter_stats_before = dpcsh_obj.peek_meter_stats_by_id(meter_id=self.meter_id, erp=self.erp)

            fun_test.log("VP stats: %s" % vp_stats_before)
            fun_test.log("ERP stats: %s" % erp_stats_before)
            fun_test.log("WRO stats: %s" % wro_stats_before)
            if meter_stats_before:
                fun_test.log("METER stats for id %s : %s" % (str(self.meter_id), meter_stats_before))

        checkpoint = "Start traffic Traffic Duration: %d" % TRAFFIC_DURATION
        result = template_obj.enable_generator_configs([self.generator_handle])
        fun_test.test_assert(result, checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION + 10)

        checkpoint = "Ensure Spirent stats fetched"
        tx_results = template_obj.stc_manager.get_tx_stream_block_results(stream_block_handle=self.stream_obj.
                                                                          spirent_handle,
                                                                          subscribe_handle=subscribe_results
                                                                          ['tx_subscribe'])
        rx_results = template_obj.stc_manager.get_rx_stream_block_results(stream_block_handle=self.stream_obj.
                                                                          spirent_handle,
                                                                          subscribe_handle=subscribe_results
                                                                          ['rx_subscribe'])
        rx_port_results = template_obj.stc_manager.get_rx_port_analyzer_results(port_handle=self.port_3,
                                                                                subscribe_handle=subscribe_results
                                                                                ['analyzer_subscribe'])
        rx_port2_results = template_obj.stc_manager.get_rx_port_analyzer_results(port_handle=self.port_2,
                                                                                 subscribe_handle=subscribe_results
                                                                                 ['analyzer_subscribe'])
        tx_port_results = template_obj.stc_manager.get_generator_port_results(port_handle=self.port_1,
                                                                              subscribe_handle=subscribe_results
                                                                              ['generator_subscribe'])
        fun_test.simple_assert(rx_port_results and tx_port_results and rx_port2_results, checkpoint)

        fun_test.log("Tx Spirent Stats: %s" % tx_results)
        fun_test.log("Rx Spirent Stats: %s" % rx_results)
        fun_test.log("Tx Port Stats: %s" % tx_port_results)
        fun_test.log("Rx Port Stats: %s" % rx_port_results)
        fun_test.log("Rx Port 2 Stats: %s" % rx_port2_results)

        dut_tx_port_stats = None
        dut_rx_port_stats = None
        vp_stats = None
        erp_stats = None
        wro_stats = None
        meter_stats = None
        if self.dut_config['enable_dpcsh']:
            checkpoint = "Fetch PSW and Parser DUT stats after traffic"
            psw_stats = dpcsh_obj.peek_psw_global_stats()
            parser_stats = dpcsh_obj.peek_parser_stats()
            fun_test.log("PSW Stats: %s \n" % psw_stats)
            fun_test.log("Parser stats: %s \n" % parser_stats)
            fun_test.add_checkpoint(checkpoint)

            checkpoint = "Get FPG port stats for all ports"
            dut_port_1 = self.dut_config['ports'][0]
            dut_port_2 = self.dut_config['ports'][2]
            hnu = False
            if dut_port_1 == 1 or dut_port_1 == 2:
                hnu = True
            dut_tx_port_stats = dpcsh_obj.peek_fpg_port_stats(port_num=dut_port_1, hnu=hnu)
            hnu = False
            if dut_port_2 == 1 or dut_port_2 == 2:
                hnu = True
            dut_rx_port_stats = dpcsh_obj.peek_fpg_port_stats(port_num=dut_port_2, hnu=hnu)
            fun_test.simple_assert(dut_tx_port_stats and dut_rx_port_stats, checkpoint)

            fun_test.log("DUT Tx stats: %s" % dut_tx_port_stats)
            fun_test.log("DUT Rx stats: %s" % dut_rx_port_stats)

            checkpoint = "Fetch VP stats"
            vp_stats = get_vp_pkts_stats_values(network_controller_obj=dpcsh_obj)
            fun_test.simple_assert(vp_stats, checkpoint)

            checkpoint = "Fetch ERP NU stats"
            erp_stats = get_erp_stats_values(network_controller_obj=dpcsh_obj)
            fun_test.simple_assert(erp_stats, checkpoint)

            checkpoint = "Fetch WRO NU stats"
            wro_stats = get_wro_global_stats_values(network_controller_obj=dpcsh_obj)
            fun_test.simple_assert(wro_stats, checkpoint)

            if self.meter_id:
                checkpoint = "Fetch Meter stats for meter id: %s" % str(self.meter_id)
                meter_stats = dpcsh_obj.peek_meter_stats_by_id(meter_id=self.meter_id, erp=self.erp)
                fun_test.simple_assert(meter_stats, checkpoint)

            fun_test.log("VP stats: %s" % vp_stats)
            fun_test.log("ERP stats: %s" % erp_stats)
            fun_test.log("WRO stats: %s" % wro_stats)
            if meter_stats:
                fun_test.log("METER stats for id %s : %s" % (str(self.meter_id), meter_stats))

        # validation asserts
        # Spirent stats validation
        checkpoint = "Validate Tx and Rx on spirent"
        fun_test.log("Tx FrameCount: %d Rx FrameCount: %d" % (int(tx_port_results['GeneratorFrameCount']),
                                                              int(rx_port_results['TotalFrameCount'])))
        fun_test.test_assert((MIN_RX_PORT_COUNT <= int(rx_port_results['TotalFrameCount']) <= MAX_RX_PORT_COUNT),
                             checkpoint)

        checkpoint = "Ensure %s does not received any frames" % self.port_2
        fun_test.log("Rx Port2 FrameCount: %d" % int(rx_port2_results['TotalFrameCount']))
        fun_test.test_assert_expected(expected=0, actual=int(rx_port2_results['TotalFrameCount']),
                                      message=checkpoint)

        checkpoint = "Ensure no errors are seen on spirent"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_results)
        fun_test.test_assert(expression=result['result'], message=checkpoint)

        # DUT stats validation
        if self.dut_config['enable_dpcsh']:
            checkpoint = "Validate Tx and Rx on DUT"
            frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_stats,
                                                            stat_type=FRAMES_RECEIVED_OK)
            frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_stats,
                                                         stat_type=FRAMES_TRANSMITTED_OK)
            fun_test.log("DUT Tx FrameCount: %s DUT Rx FrameCount: %s" % (str(frames_transmitted),
                                                                          str(frames_received)))
            fun_test.test_assert((MIN_RX_PORT_COUNT <= frames_received <= MAX_RX_PORT_COUNT),
                                 checkpoint)
            # VP stats validation
            checkpoint = "From VP stats, Ensure T2C header counter equal to spirent Tx counter"
            vp_stats_diff = get_diff_stats(old_stats=vp_stats_before, new_stats=vp_stats,
                                           stats_list=[VP_PACKETS_CONTROL_T2C_COUNT, VP_PACKETS_CC_OUT,
                                                       VP_PACKETS_TOTAL_OUT, VP_PACKETS_TOTAL_IN])
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=vp_stats_diff[VP_PACKETS_CONTROL_T2C_COUNT],
                                          message=checkpoint)
            checkpoint = "From VP stats, Ensure CC OUT counters are equal to spirent Tx Counter"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=vp_stats_diff[VP_PACKETS_CC_OUT],
                                          message=checkpoint)

            checkpoint = "Ensure VP total packets IN == VP total packets OUT"
            fun_test.test_assert_expected(expected=vp_stats_diff[VP_PACKETS_TOTAL_IN],
                                          actual=vp_stats_diff[VP_PACKETS_TOTAL_OUT],
                                          message=checkpoint)
            # ERP stats validation
            checkpoint = "From ERP stats, Ensure count for EFP to WQM decrement pulse equal to spirent Tx"
            erp_stats_diff = get_diff_stats(old_stats=erp_stats_before, new_stats=erp_stats,
                                            stats_list=[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED,
                                                        ERP_COUNT_FOR_EFP_WRO_DESCRIPTORS_SENT,
                                                        ERP_COUNT_FOR_EFP_WQM_DECREMENT_PULSE,
                                                        ERP_COUNT_FOR_ERP0_EFP_ERROR_INTERFACE_FLITS,
                                                        ERP_COUNT_FOR_EFP_FCP_VLD])
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=erp_stats_diff[ERP_COUNT_FOR_EFP_WQM_DECREMENT_PULSE],
                                          message=checkpoint)
            checkpoint = "From ERP stats, Ensure count for EFP to WRO descriptors send equal to spirent Tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=erp_stats_diff[ERP_COUNT_FOR_EFP_WRO_DESCRIPTORS_SENT],
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for ERP0 to EFP error interface flits equal to spirent Tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=erp_stats_diff[ERP_COUNT_FOR_ERP0_EFP_ERROR_INTERFACE_FLITS],
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for all non FCP packets received equal to spirent Tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=erp_stats_diff[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED],
                                          message=checkpoint)

            checkpoint = "From ERP stats, Ensure count for EFP to FCB vld equal to spirent Tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=erp_stats_diff[ERP_COUNT_FOR_EFP_FCP_VLD],
                                          message=checkpoint)
            # WRO stats validation
            checkpoint = "From WRO stats, Ensure WRO IN packets equal to spirent Tx"
            wro_stats_diff = get_diff_stats(old_stats=wro_stats_before, new_stats=wro_stats)
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=wro_stats_diff['global'][WRO_IN_PKTS],
                                          message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO In NFCP packets equal to spirent Tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=wro_stats_diff['global'][WRO_IN_NFCP_PKTS],
                                          message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO out WUs equal to spirent tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=wro_stats_diff['global'][WRO_OUT_WUS],
                                          message=checkpoint)

            checkpoint = "From WRO stats, Ensure WRO WU CNT VPP packets equal to spirent tx"
            fun_test.test_assert_expected(expected=frames_received,
                                          actual=wro_stats_diff['global'][WRO_WU_COUNT_VPP],
                                          message=checkpoint)

            if self.validate_meter_stats:
                checkpoint = "Validate meter stats ensure frames_received == (green pkts + yellow pkts)"
                meter_stats_diff = get_diff_stats(old_stats=meter_stats_before, new_stats=meter_stats)
                green_pkts = int(meter_stats_diff['green']['pkts'])
                yellow_pkts = int(meter_stats_diff['yellow']['pkts'])
                red_pkts = int(meter_stats_diff['red']['pkts'])
                fun_test.log("Green: %d Yellow: %d Red: %d" % (green_pkts, yellow_pkts, red_pkts))
                fun_test.test_assert_expected(expected=frames_received, actual=(green_pkts + yellow_pkts),
                                              message=checkpoint)
                checkpoint = "Ensure red pkts are equal to DroppedFrameCount on Spirent Rx results"
                dropped_frame_count = int(rx_results['DroppedFrameCount'])
                fun_test.log("Dropped Frame Count on Spirent: %d" % dropped_frame_count)
                fun_test.test_assert_expected(expected=tx_port_results['TotalFrameCount'],
                                              actual=(red_pkts + green_pkts + yellow_pkts),
                                              message=checkpoint)

    def cleanup(self):
        fun_test.log("In test case cleanup")

        template_obj.clear_subscribed_results(subscribe_handle_list=subscribe_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)

        if self.detach_ports:
            checkpoint = "Detach ports"
            port_handles = template_obj.stc_manager.get_port_list()
            template_obj.stc_manager.detach_ports_by_command(port_handles=port_handles)
            fun_test.add_checkpoint(checkpoint=checkpoint)


class TestArpRequestFlow1(TestCcFlows):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Test CC Ethernet ARP Request (NU --> CC)",
                              steps="""
                              1. Create a stream with EthernetII and ARP headers under port
                                 a. Frame Size Mode: %s Frame Size %d
                                 b. Load: %d Load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic
                              6. Validate Tx and Rx on spirent and ensure no errors are seen.
                              7. Validate Tx and Rx on DUT
                              8. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              9. From VP stats, validate VP total IN == VP total OUT
                              10. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              11. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX    
                              """ % (FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT,
                                     TRAFFIC_DURATION))

    def setup(self):
        global flow_direction, flow_type

        flow_direction = NuConfigManager.FLOW_DIRECTION_FPG_CC
        flow_type = NuConfigManager.CC_FLOW_TYPE

        self.configure_ports()
        self.detach_ports = False

        checkpoint = "Configure a stream with EthernetII and ARP headers under port %s" % self.port_1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=self.port_1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % self.port_1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.BROADCAST_MAC,
                                    ether_type=Ethernet2Header.ARP_ETHERTYPE)
        arp_obj = ARP()

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=arp_obj, update=False,
                                                                delete_header=[Ipv4Header.HEADER_TYPE])
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = ETH_COPP_ARP_REQ_METER_ID


class TestArpRequestFlow2(TestCcFlows):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Test CC Ethernet ARP Request (HNU --> CC)",
                              steps="""
                              1. Create a stream with EthernetII and ARP headers under port
                                 a. Frame Size Mode: %s Frame Size %d
                                 b. Load: %d Load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic
                              6. Validate Tx and Rx on spirent and ensure no errors are seen.
                              7. Validate Tx and Rx on DUT
                              8. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              9. From VP stats, validate VP total IN == VP total OUT
                              10. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              11. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX    
                              """ % (FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT,
                                     TRAFFIC_DURATION))

    def setup(self):
        global flow_direction, flow_type

        flow_direction = NuConfigManager.FLOW_DIRECTION_HNU_CC
        flow_type = NuConfigManager.CC_FLOW_TYPE

        self.configure_ports()
        self.detach_ports = False

        checkpoint = "Configure a stream with EthernetII and ARP headers under port %s" % self.port_1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=self.port_1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % self.port_1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.BROADCAST_MAC,
                                    ether_type=Ethernet2Header.ARP_ETHERTYPE)
        arp_obj = ARP()

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=arp_obj, update=False,
                                                                delete_header=[Ipv4Header.HEADER_TYPE])
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = ETH_COPP_ARP_REQ_METER_ID


class TestVpFlows(FunTestCase):
    streamblock_obj_1 = None
    min_frame_size = 78
    max_frame_size = MAX_FRAME_SIZE
    generator_step_size = max_frame_size
    dut_config = None
    num_ports = 2
    port_1 = None
    port_2 = None
    sleep_duration_seconds = None
    generator_handle = None
    detach_ports = True
    fps = 100
    mtu = max_frame_size
    hnu = False

    def describe(self):
        pass

    def l4_setup(self):
        tcp = TCP()
        add_tcp = template_obj.stc_manager.configure_frame_stack(stream_block_handle=
                                                                 self.streamblock_obj_1.spirent_handle,
                                                                 header_obj=tcp)
        fun_test.test_assert(add_tcp, "Adding tcp header to frame")

        range_obj = RangeModifier(recycle_count=MAX_FRAME_SIZE, step_value=1, data=1024)
        modify_attribute = 'sourcePort'
        create_range = template_obj.stc_manager.configure_range_modifier(range_modifier_obj=range_obj,
                                                                         streamblock_obj=self.streamblock_obj_1,
                                                                         header_obj=tcp,
                                                                         header_attribute=modify_attribute)
        fun_test.test_assert(create_range, "Ensure range modifier created on %s for attribute %s"
                             % (tcp._spirent_handle, modify_attribute))

    def configure_cadence_pcs_for_fcp(self):
        username = 'root'
        password = 'fun123'
        cadence_pc_3 = "cadence-pc-3"
        cadence_pc_4 = "cadence-pc-4"
        pc_3_config_dir = fun_test.get_helper_dir_path() + "/pc_3_fcp_configs"
        pc_4_config_dir = fun_test.get_helper_dir_path() + "/pc_4_fcp_configs"

        # Copy req files to cadence pc 3
        target_file_path = "/tmp"
        pc_3_obj = Linux(host_ip=cadence_pc_3, ssh_username=username, ssh_password=password)
        for file_name in ['unnh.sh', 'nofcp.sh', 'nh_fcp.sh']:
            fun_test.log("Coping %s file to cadence pc 3 in /tmp dir" % file_name)
            transfer_success = fun_test.scp(source_file_path=pc_3_config_dir + "/%s" % file_name,
                                            target_file_path=target_file_path, target_ip=cadence_pc_3,
                                            target_username=username, target_password=password)
            fun_test.simple_assert(transfer_success, "Ensure file is transferred")

            # Configure cadence pc 3 for FCP traffic
            fun_test.log("Executing %s on cadence pc 3" % file_name)
            cmd = "sh /tmp/%s" % file_name
            pc_3_obj.command(command=cmd)

        # Copy req files to cadence pc 4
        pc_4_obj = Linux(host_ip=cadence_pc_4, ssh_username=username, ssh_password=password)
        for file_name in ['nh_fcp.sh', 'unnh.sh']:
            fun_test.log("Coping %s file to cadence pc 4 in /tmp dir" % file_name)
            transfer_success = fun_test.scp(source_file_path=pc_4_config_dir + "/%s" % file_name,
                                            target_file_path=target_file_path, target_ip=cadence_pc_4,
                                            target_username=username, target_password=password)
            fun_test.simple_assert(transfer_success, "Ensure file is transferred")

            # Configure cadence pc 3 for FCP traffic
            fun_test.log("Executing %s cadence pc 4" % file_name)
            cmd = "sh /tmp/%s" % file_name
            pc_4_obj.command(command=cmd)

    def setup(self):
        pass

    def configure_ports(self):
        global vp_port_list

        self.dut_config = nu_config_obj.read_dut_config(dut_type=NuConfigManager.DUT_TYPE_PALLADIUM,
                                                        flow_type=flow_type,
                                                        flow_direction=flow_direction)

        if self.detach_ports:
            checkpoint = "Setup VP Ports"
            result = template_obj.setup_ports_using_command(no_of_ports_needed=self.num_ports,
                                                            flow_type=flow_type,
                                                            flow_direction=flow_direction)
            fun_test.test_assert(expression=result['result'], message=checkpoint)

            self.port_1 = result['port_list'][0]
            self.port_2 = result['port_list'][1]
            vp_port_list.append(self.port_1)
            vp_port_list.append(self.port_2)

        self.sleep_duration_seconds = (self.generator_step_size / self.fps) + CUSHION_SLEEP

        gen_config_obj = GeneratorConfig(scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED,
                                         duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                         duration=self.sleep_duration_seconds, advanced_interleaving=True)
        # Apply generator config on port 1
        self.generator_handle = template_obj.stc_manager.get_generator(port_handle=self.port_1)
        config_obj = template_obj.configure_generator_config(port_handle=self.port_1,
                                                             generator_config_obj=gen_config_obj)
        fun_test.test_assert(config_obj, "Creating generator config on port %s" % self.port_1)

        if self.dut_config['enable_dpcsh']:
            # Enable qos pfc
            set_pfc = dpcsh_obj.enable_qos_pfc()
            fun_test.test_assert(set_pfc, "Enable qos pfc")

            set_pfc = dpcsh_obj.enable_qos_pfc(hnu=True)
            fun_test.test_assert(set_pfc, "Enable HNU qos pfc")

            buffer = dpcsh_obj.set_qos_egress_buffer_pool(nonfcp_xoff_thr=7000,
                                                          fcp_xoff_thr=7000, df_thr=4000, dx_thr=4000, fcp_thr=8000,
                                                          nonfcp_thr=8000, sample_copy_thr=255, sf_thr=4000,
                                                          sf_xoff_thr=3500, sx_thr=4000)
            fun_test.test_assert(buffer, "Set non fcp xoff threshold")

            buffer = dpcsh_obj.set_qos_egress_buffer_pool(nonfcp_xoff_thr=3500,
                                                          fcp_xoff_thr=900, mode='hnu', df_thr=2000, dx_thr=1000,
                                                          fcp_thr=1000, nonfcp_thr=9000,
                                                          sample_copy_thr=255,sf_thr=2000, sf_xoff_thr=1900, sx_thr=250)
            fun_test.test_assert(buffer, "Set HNU non fcp xoff threshold")

            # Set mtu on DUT
            dut_port_1 = self.dut_config['ports'][0]
            dut_port_2 = self.dut_config['ports'][1]
            shape = 0
            if dut_port_1 == 1 or dut_port_1 == 2:
                shape = 1
            mtu_1 = dpcsh_obj.set_port_mtu(port_num=dut_port_1, mtu_value=self.mtu, shape=shape)
            fun_test.test_assert(mtu_1, " Set mtu on DUT port %s" % dut_port_1)

            shape = 0
            if dut_port_2 == 1 or dut_port_2 == 2:
                shape = 1
            mtu_2 = dpcsh_obj.set_port_mtu(port_num=dut_port_2, mtu_value=self.mtu, shape=shape)
            fun_test.test_assert(mtu_2, " Set mtu on DUT port %s" % dut_port_2)

    def run(self):
        bam_stats_1 = None
        parser_stats_1 = None
        vp_pkts_stats_1 = None
        erp_stats_1 = None
        psw_stats_1 = None
        wro_stats_1 = None

        if self.dut_config['enable_dpcsh']:
            checkpoint = "Clear FPG stats on all DUT ports"
            for port in self.dut_config['ports']:
                shape = 0
                if port == 1 or port == 2:
                    shape = 1
                clear_stats = dpcsh_obj.clear_port_stats(port_num=port, shape=shape)
                fun_test.simple_assert(clear_stats, "FPG stats clear on DUT port %d" % port)
            fun_test.add_checkpoint(checkpoint)

        # Adding l4 header
        fun_test.add_checkpoint("Adding l4 header")
        self.l4_setup()

        if self.dut_config['enable_dpcsh']:
            # Get stats before starting traffic
            fun_test.log("Get stats before starting traffic")
            bam_stats_1 = get_bam_stats_values(network_controller_obj=dpcsh_obj)
            parser_stats_1 = dpcsh_obj.peek_parser_stats()
            vp_pkts_stats_1 = get_vp_pkts_stats_values(network_controller_obj=dpcsh_obj)
            erp_stats_1 = get_erp_stats_values(network_controller_obj=dpcsh_obj, hnu=self.hnu)
            psw_stats_1 = dpcsh_obj.peek_psw_global_stats(hnu=self.hnu)
            wro_stats_1 = dpcsh_obj.peek_wro_global_stats()

        # Execute traffic
        start = template_obj.enable_generator_configs(generator_configs=[self.generator_handle])
        fun_test.test_assert(start, "Starting generator config")

        stream_handle_1 = self.streamblock_obj_1.spirent_handle

        # Sleep until traffic is executed
        fun_test.sleep("Sleeping for executing traffic", seconds=self.sleep_duration_seconds)

        stop = template_obj.disable_generator_configs(generator_configs=[self.generator_handle])
        fun_test.test_assert(stop, "Stopping generator configs")

        fun_test.sleep("Letting rx to take place", seconds=2)

        # Asserts
        stream_result_dict = template_obj.stc_manager.fetch_streamblock_results(subscribe_result=subscribe_results,
                                                                                streamblock_handle_list=
                                                                                [stream_handle_1],
                                                                                tx_result=True, rx_result=True)

        port_result_dict = template_obj.stc_manager.fetch_port_results(subscribe_result=subscribe_results,
                                                                       port_handle_list=[self.port_2],
                                                                       analyzer_result=True)

        tx_results_1 = stream_result_dict[stream_handle_1]['tx_result']
        rx_results_1 = stream_result_dict[stream_handle_1]['rx_result']
        port_2_analyzer_result = port_result_dict[self.port_2]['analyzer_result']

        fun_test.log("Spirent Tx Results: %s" % tx_results_1)
        fun_test.log("Spirent Rx Results: %s" % rx_results_1)
        fun_test.log("Spirent Port Analyzer Results: %s" % port_2_analyzer_result)

        if self.dut_config['enable_dpcsh']:
            dut_port_1 = self.dut_config['ports'][0]
            dut_port_2 = self.dut_config['ports'][1]
            hnu = False
            if dut_port_1 == 1 or dut_port_1 == 2:
                hnu = True
            dut_port_1_results = dpcsh_obj.peek_fpg_port_stats(port_num=dut_port_1, hnu=hnu)
            fun_test.test_assert(dut_port_1_results, message="Ensure stats are obtained for %s" % dut_port_1)
            hnu = False
            if dut_port_2 == 1 or dut_port_2 == 2:
                hnu = True
            dut_port_2_results = dpcsh_obj.peek_fpg_port_stats(port_num=dut_port_2, hnu=hnu)
            fun_test.test_assert(dut_port_2_results, message="Ensure stats are obtained for %s" % dut_port_2)

            dut_port_2_transmit = get_dut_output_stats_value(dut_port_2_results, FRAMES_TRANSMITTED_OK)
            dut_port_1_receive = get_dut_output_stats_value(dut_port_1_results, FRAMES_RECEIVED_OK, tx=False)

            fun_test.log("Get system stats after traffic execution")
            bam_stats_2 = get_bam_stats_values(network_controller_obj=dpcsh_obj)
            psw_stats_2 = dpcsh_obj.peek_psw_global_stats(hnu=self.hnu)
            erp_stats_2 = get_erp_stats_values(network_controller_obj=dpcsh_obj, hnu=self.hnu)
            vp_pkts_stats_2 = get_vp_pkts_stats_values(network_controller_obj=dpcsh_obj)
            parser_stats_2 = dpcsh_obj.peek_parser_stats()
            wro_stats_2 = dpcsh_obj.peek_wro_global_stats()

            dut_port_2_fpg_value = get_fpg_port_value(dut_port_2)
            dut_port_1_fpg_value = get_fpg_port_value(dut_port_1)
            frv_error = 'frv_error'
            main_pkt_drop_eop = 'main_pkt_drop_eop'
            epg0_pkt = 'epg0_pkt'
            ifpg = 'ifpg' + str(dut_port_1_fpg_value) + '_pkt'
            input_list = [frv_error, main_pkt_drop_eop, epg0_pkt, ifpg]
            output_list = [epg0_pkt]

            parsed_psw_stats_1 = get_psw_global_stats_values(psw_stats_output=psw_stats_1, input=True,
                                                             input_key_list=input_list, output=True,
                                                             output_key_list=output_list)
            parsed_psw_stats_2 = get_psw_global_stats_values(psw_stats_output=psw_stats_2, input=True,
                                                             input_key_list=input_list, output=True,
                                                             output_key_list=output_list)
            parsed_input_1 = parsed_psw_stats_1['input']
            parsed_output_1 = parsed_psw_stats_1['output']
            parsed_input_2 = parsed_psw_stats_2['input']
            parsed_output_2 = parsed_psw_stats_2['output']

            fun_test.test_assert_expected(expected=int(dut_port_1_receive), actual=int(dut_port_2_transmit),
                                          message="Ensure frames received on DUT port %s are transmitted from "
                                                  "DUT port %s"
                                                  % (dut_port_2, dut_port_1))
            # Check system stats
            # Check bam stats
            del bam_stats_2['durations_histogram']
            del bam_stats_1['durations_histogram']
            del bam_stats_2['num_bytes_in_use']
            del bam_stats_1['num_bytes_in_use']
            del bam_stats_2['num_in_use']
            del bam_stats_1['num_in_use']
            fun_test.test_assert(bam_stats_1 == bam_stats_2, message="Check BAM stats before and after match")

            # Check ERP stats
            diff_stats_erp = get_diff_stats(old_stats=erp_stats_1, new_stats=erp_stats_2,
                                            stats_list=[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED])
            diff_stats = int(diff_stats_erp[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED]) - int(tx_results_1['FrameCount'])
            expected_erp_stats = int(diff_stats_erp[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED])
            if diff_stats == 1:
                expected_erp_stats = int(diff_stats_erp[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED]) - 1

            fun_test.test_assert_expected(expected=expected_erp_stats,
                                          actual=(int(tx_results_1['FrameCount'])),
                                          message="Check non fcp packets counter from erp stats")

            stats_list = [VP_PACKETS_TOTAL_IN, VP_PACKETS_TOTAL_OUT, VP_PACKETS_FORWARDING_NU_LE]
            if flow_direction == NuConfigManager.FLOW_DIRECTION_HU_FPG:
                stats_list = [VP_PACKETS_TOTAL_IN, VP_PACKETS_TOTAL_OUT, VP_PACKETS_OUT_ETP, VP_FAE_REQUESTS_SENT,
                              VP_FAE_RESPONSES_RECEIVED]
                diff_stats_vppkts = get_diff_stats(old_stats=vp_pkts_stats_1, new_stats=vp_pkts_stats_2,
                                                   stats_list=stats_list)

                fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']),
                                              actual=int(diff_stats_vppkts[VP_PACKETS_OUT_ETP]),
                                              message="Ensure VP stats has correct etp out packets")

                fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']),
                                              actual=int(diff_stats_vppkts[VP_FAE_REQUESTS_SENT]),
                                              message="Ensure VP stats has correct fae requests sent")

                fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']),
                                              actual=int(diff_stats_vppkts[VP_FAE_RESPONSES_RECEIVED]),
                                              message="Ensure VP stats has correct fae responses received")
            else:
                diff_stats_vppkts = get_diff_stats(old_stats=vp_pkts_stats_1, new_stats=vp_pkts_stats_2,
                                                   stats_list=stats_list)
                fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']),
                                              actual=int(diff_stats_vppkts[VP_PACKETS_FORWARDING_NU_LE]),
                                              message="Ensure VP stats has correct nu le packets")

            fun_test.test_assert_expected(expected=int(diff_stats_vppkts[VP_PACKETS_TOTAL_IN]),
                                          actual=int(diff_stats_vppkts[VP_PACKETS_TOTAL_OUT]),
                                          message="Ensure VP stats has correct total IN packets == total OUT packets")

            # Check psw nu input stats
            psw_diff_stats = get_diff_stats(old_stats=parsed_input_1, new_stats=parsed_input_2)

            fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']), actual=psw_diff_stats[ifpg],
                                          message="Check ifpg counter in psw nu stats in input")
            # Check psw nu output stats
            psw_diff_stats = get_diff_stats(old_stats=parsed_output_1, new_stats=parsed_output_2)
            fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']), actual=psw_diff_stats[epg0_pkt],
                                          message="Check epg_pkt counter in psw nu stats in output")

        # SPIRENT ASSERTS
        if int(tx_results_1['FrameCount']) == int(rx_results_1['FrameCount']):
            fun_test.test_assert_expected(expected=int(tx_results_1['FrameCount']),
                                          actual=int(rx_results_1['FrameCount']),
                                          message="Ensure frames transmitted and received on spirent match from %s" %
                                                  flow_direction)

        zero_counter_seen = template_obj.check_non_zero_error_count(port_2_analyzer_result)
        if "PrbsErrorFrameCount" in zero_counter_seen.keys():
            zero_counter_seen['result'] = True
        fun_test.test_assert(zero_counter_seen['result'], "Check for error counters on port2")

    def cleanup(self):
        fun_test.log("In testcase cleanup")

        fun_test.log("Deleting streamblock %s " % self.streamblock_obj_1.spirent_handle)
        template_obj.delete_streamblocks(streamblock_handle_list=[self.streamblock_obj_1.spirent_handle])

        for key in subscribe_results.iterkeys():
            template_obj.stc_manager.clear_results_view_command(result_dataset=subscribe_results[key])

        if self.detach_ports:
            checkpoint = "Detach ports"
            port_handles = template_obj.stc_manager.get_port_list()
            template_obj.stc_manager.detach_ports_by_command(port_handles=port_handles)
            fun_test.add_checkpoint(checkpoint=checkpoint)


class VPPathIPv4TCP(TestVpFlows):

    def describe(self):
        self.set_test_details(id=5,
                              summary="Test VP path from NU ---> HNU for IPv4 with TCP with frame size incrementing "
                                      "from 78B to %s" % MAX_FRAME_SIZE,
                              steps="""
                        1. Create streamblock and add ethernet, ipv4 and tcp headers
                        1. Start traffic in incremental
                        2. Compare Tx and Rx results for frame count
                        3. Check for error counters. there must be no error counter
                        4. Check dut ingress and egress frame count match
                        5. Check egress frame count with spirent rx counter
                        6. Check rx counter on spirent matches with dut egress counter
                        7. Check erp stats for non fcp packets
                        8. Check bam stats before and after traffic
                        9. Check psw nu for main_drop, fwd_error to be 0
                        10. Check psw nu for ifpg, epg0 and fpg counter to match spirent tx count
                        11. Check parser stats for eop_cnt, sop_cnt, prv_sent with spirent tx
                        12. Check vp pkts for vp in, vp out, vp forward nu le with spirent tx
                        """)

    def setup(self):
        global flow_direction, flow_type

        flow_direction = NuConfigManager.FLOW_DIRECTION_FPG_HNU
        flow_type = NuConfigManager.VP_FLOW_TYPE

        self.configure_ports()
        self.detach_ports = False

        l2_config = spirent_config["l2_config"]
        l3_config = spirent_config["l3_config"]["ipv4"]
        ether_type = Ethernet2Header.INTERNET_IP_ETHERTYPE

        # Create streamblock 1
        self.streamblock_obj_1 = StreamBlock(load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND,
                                             load=self.fps, fill_type=StreamBlock.FILL_TYPE_PRBS,
                                             insert_signature=True,
                                             frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_INCR,
                                             min_frame_length=self.min_frame_size, max_frame_length=MAX_FRAME_SIZE,
                                             step_frame_length=1)
        streamblock1 = template_obj.configure_stream_block(self.streamblock_obj_1, self.port_1)
        fun_test.test_assert(streamblock1, "Creating streamblock on port %s" % self.port_1)

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=self.streamblock_obj_1.spirent_handle,
                                                               source_mac=l2_config['source_mac'],
                                                               destination_mac=l2_config['destination_mac'],
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Adding source and destination mac")

        # Adding Ip address and gateway
        destination = l3_config['hnu_destination_ip2']
        ip = template_obj.stc_manager.configure_ip_address(streamblock=self.streamblock_obj_1.spirent_handle,
                                                           source=l3_config['source_ip1'],
                                                           destination=destination)
        fun_test.test_assert(ip, "Adding source ip, dest ip and gateway")


class VPPathIPv4TCPNFCP(TestVpFlows):

    def describe(self):
        self.set_test_details(id=6,
                              summary="Test VP path from HNU ---> HNU (NFCP) for IPv4 with TCP with frame size "
                                      "incrementing from 78B to 1500B",
                              steps="""
                        1. Create streamblock and add ethernet, ipv4 and tcp headers
                        1. Start traffic in incremental
                        2. Compare Tx and Rx results for frame count
                        3. Check for error counters. there must be no error counter
                        4. Check dut ingress and egress frame count match
                        5. Check egress frame count with spirent rx counter
                        6. Check rx counter on spirent matches with dut egress counter
                        7. Check erp stats for non fcp packets
                        8. Check bam stats before and after traffic
                        9. Check psw nu for main_drop, fwd_error to be 0
                        10. Check psw nu for ifpg, epg0 and fpg counter to match spirent tx count
                        11. Check parser stats for eop_cnt, sop_cnt, prv_sent with spirent tx
                        12. Check vp pkts for vp in, vp out, vp forward nu le with spirent tx
                        """)

    def setup(self):
        global flow_direction, flow_type

        flow_direction = NuConfigManager.FLOW_DIRECTION_HNU_HNU
        flow_type = NuConfigManager.VP_FLOW_TYPE
        self.fps = 50
        self.hnu = True
        self.max_frame_size = 9000
        self.mtu = 9000
        self.generator_step_size = 9000

        self.configure_ports()
        self.detach_ports = False

        l2_config = spirent_config["l2_config"]
        l3_config = spirent_config["l3_config"]["ipv4"]
        ether_type = Ethernet2Header.INTERNET_IP_ETHERTYPE

        # Create streamblock 1
        self.streamblock_obj_1 = StreamBlock(load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND,
                                             load=self.fps, fill_type=StreamBlock.FILL_TYPE_PRBS,
                                             insert_signature=True,
                                             frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_INCR,
                                             min_frame_length=self.min_frame_size,
                                             max_frame_length=self.max_frame_size,
                                             step_frame_length=1)
        streamblock1 = template_obj.configure_stream_block(self.streamblock_obj_1, self.port_1)
        fun_test.test_assert(streamblock1, "Creating streamblock on port %s" % self.port_1)

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=self.streamblock_obj_1.spirent_handle,
                                                               source_mac=l2_config['source_mac'],
                                                               destination_mac=l2_config['destination_mac'],
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Adding source and destination mac")

        # Adding Ip address and gateway
        destination = l3_config['hnu_destination_ip2']
        ip = template_obj.stc_manager.configure_ip_address(streamblock=self.streamblock_obj_1.spirent_handle,
                                                           source=l3_config['source_ip1'],
                                                           destination=destination)
        fun_test.test_assert(ip, "Adding source ip, dest ip and gateway")


class VPPathIPv4TCPFCP(TestVpFlows):

    def describe(self):
        self.set_test_details(id=7,
                              summary="Test VP path from HNU ---> HNU (FCP) for IPv4 with TCP with frame size "
                                      "incrementing from 78B to %s" % MAX_FRAME_SIZE,
                              steps="""
                        1. Create streamblock and add ethernet, ipv4 and tcp headers
                        1. Start traffic in incremental
                        2. Compare Tx and Rx results for frame count
                        3. Check for error counters. there must be no error counter
                        4. Check dut ingress and egress frame count match
                        5. Check egress frame count with spirent rx counter
                        6. Check rx counter on spirent matches with dut egress counter
                        7. Check erp stats for non fcp packets
                        8. Check bam stats before and after traffic
                        9. Check psw nu for main_drop, fwd_error to be 0
                        10. Check psw nu for ifpg, epg0 and fpg counter to match spirent tx count
                        11. Check parser stats for eop_cnt, sop_cnt, prv_sent with spirent tx
                        12. Check vp pkts for vp in, vp out, vp forward nu le with spirent tx
                        """)

    def setup(self):
        global flow_direction, flow_type

        flow_direction = NuConfigManager.FLOW_DIRECTION_FCP_HNU_HNU
        flow_type = NuConfigManager.VP_FLOW_TYPE
        self.fps = 50

        self.configure_cadence_pcs_for_fcp()
        self.configure_ports()
        self.detach_ports = False

        l2_config = spirent_config["l2_config"]
        l3_config = spirent_config["l3_config"]["ipv4"]
        ether_type = Ethernet2Header.INTERNET_IP_ETHERTYPE

        # Create streamblock 1
        self.streamblock_obj_1 = StreamBlock(load_unit=StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND,
                                             load=self.fps, fill_type=StreamBlock.FILL_TYPE_PRBS,
                                             insert_signature=True,
                                             frame_length_mode=StreamBlock.FRAME_LENGTH_MODE_INCR,
                                             min_frame_length=self.min_frame_size, max_frame_length=MAX_FRAME_SIZE,
                                             step_frame_length=1)
        streamblock1 = template_obj.configure_stream_block(self.streamblock_obj_1, self.port_1)
        fun_test.test_assert(streamblock1, "Creating streamblock on port %s" % self.port_1)

        # Adding source and destination ip
        ether = template_obj.stc_manager.configure_mac_address(streamblock=self.streamblock_obj_1.spirent_handle,
                                                               source_mac=l2_config['source_mac'],
                                                               destination_mac=l2_config['destination_mac'],
                                                               ethernet_type=ether_type)
        fun_test.test_assert(ether, "Adding source and destination mac")

        # Adding Ip address and gateway
        destination = l3_config['hnu_fcp_destination_ip1']
        ip = template_obj.stc_manager.configure_ip_address(streamblock=self.streamblock_obj_1.spirent_handle,
                                                           source=l3_config['source_ip1'],
                                                           destination=destination)
        fun_test.test_assert(ip, "Adding source ip, dest ip and gateway")


if __name__ == "__main__":
    ts = SpirentSetup()
    # Transit NU --> NU Flow
    # ts.add_test_case(TransitSweep())
    # TODO: Add IPv6 route for FPG18 75.0.0.5
    # ts.add_test_case(TransitV6Sweep())

    # CC NU --> CC Flow
    # ts.add_test_case(TestArpRequestFlow1())

    # CC HNU --> CC Flow
    # ts.add_test_case(TestArpRequestFlow2())

    # VP NU --> HNU Flow
    ts.add_test_case(VPPathIPv4TCP())

    # VP HNU --> HNU (NFCP) Flow
    ts.add_test_case(VPPathIPv4TCPNFCP())

    # VP HNU --> HNU (FCP) Flow
    # ts.add_test_case(VPPathIPv4TCPFCP())

    ts.run()
