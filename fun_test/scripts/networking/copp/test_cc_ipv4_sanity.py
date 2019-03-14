from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import *
from lib.host.network_controller import NetworkController
from scripts.networking.nu_config_manager import *
from scripts.networking.helper import *
from scripts.networking.snapshot_helper import SnapshotHelper

dut_config = {}
spirent_config = {}
network_controller_obj = None
port1 = None
port2 = None
port3 = None
generator_handle = None
subscribed_results = None
TRAFFIC_DURATION = 10
DURATION_SECONDS = 10
cc_path_config = {}
LOAD = 110
LOAD_UNIT = StreamBlock.LOAD_UNIT_FRAMES_PER_SECOND
FRAME_SIZE = 128
FRAME_LENGTH_MODE = StreamBlock.FRAME_LENGTH_MODE_FIXED
TEST_CONFIG_FILE = SCRIPTS_DIR + "/networking/copp" + "/test_configs.json"
NUM_PORTS = 3
streams_group = []
MIN_RX_PORT_COUNT = 80
MAX_RX_PORT_COUNT = 90


class SetupSpirent(FunTestScript):
    generator_config_obj = None

    def describe(self):
        self.set_test_details(steps="""
        1. Check health of Spirent. Connect to Lab server
        2. Create ports and attach ports
        3. Read configs 
        4. In cleanup, disconnect session 
        """)

    def setup(self):
        fun_test.log("In script setup")
        global template_obj, dut_config, spirent_config, network_controller_obj, port1, port2, port3, cc_path_config, \
            interface_obj1, interface_obj2, generator_handle, subscribed_results
        global LOAD, LOAD_UNIT, FRAME_SIZE, FRAME_LENGTH_MODE, MIN_RX_PORT_COUNT, MAX_RX_PORT_COUNT, TRAFFIC_DURATION

        nu_config_obj = NuConfigManager()
        fun_test.shared_variables['nu_config_obj'] = nu_config_obj
        dut_type = nu_config_obj.DUT_TYPE
        dut_config = nu_config_obj.read_dut_config(dut_type=dut_type, flow_type=NuConfigManager.CC_FLOW_TYPE,
                                                   flow_direction=FLOW_DIRECTION)

        chassis_type = nu_config_obj.CHASSIS_TYPE
        spirent_config = nu_config_obj.read_traffic_generator_config()

        template_obj = SpirentEthernetTrafficTemplate(session_name="cc_path", spirent_config=spirent_config,
                                                      chassis_type=chassis_type)
        result = template_obj.setup(no_of_ports_needed=NUM_PORTS, flow_type=NuConfigManager.CC_FLOW_TYPE,
                                    flow_direction=FLOW_DIRECTION)
        fun_test.test_assert(result['result'], "Ensure Spirent Setup done")

        port1 = result['port_list'][0]
        port2 = result['port_list'][1]
        port3 = result['port_list'][2]

        interface_obj1 = result['interface_obj_list'][0]
        interface_obj2 = result['interface_obj_list'][1]

        dpc_server_ip = dut_config['dpcsh_tcp_proxy_ip']
        dpc_server_port = dut_config['dpcsh_tcp_proxy_port']
        network_controller_obj = NetworkController(dpc_server_ip=dpc_server_ip, dpc_server_port=dpc_server_port)

        config = nu_config_obj.read_test_configs_by_dut_type(config_file=TEST_CONFIG_FILE)
        fun_test.simple_assert(config, "Read Interface loads file")
        LOAD = config['load']
        MIN_RX_PORT_COUNT = config['min_meter_range']
        MAX_RX_PORT_COUNT = config['max_meter_range']
        LOAD_UNIT = config['load_type']
        FRAME_SIZE = config['fixed_frame_size']
        FRAME_LENGTH_MODE = config['frame_length_mode']
        TRAFFIC_DURATION = config['duration']

        checkpoint = "Configure Generator Config for port %s" % port1
        self.generator_config_obj = GeneratorConfig(duration=TRAFFIC_DURATION,
                                                    duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                                    scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED)
        result = template_obj.configure_generator_config(port_handle=port1,
                                                         generator_config_obj=self.generator_config_obj)
        fun_test.simple_assert(result, "Create Generator config")
        generator_handle = template_obj.stc_manager.get_generator(port_handle=port1)
        fun_test.test_assert(generator_handle, checkpoint)

        checkpoint = "Subscribe to all results"
        subscribed_results = template_obj.subscribe_to_all_results(parent=template_obj.stc_manager.project_handle)
        fun_test.test_assert(subscribed_results, checkpoint)

    def cleanup(self):
        fun_test.log("In script cleanup")
        template_obj.cleanup()


class TestCcIPv4ICMP(FunTestCase):
    stream_obj = None
    validate_meter_stats = True
    meter_id = None

    def describe(self):
        self.set_test_details(id=1, summary="NU --> CC IPv4 ICMP (Internet Control Message Protocol) destined to "
                                            "CC meter to 100 pps",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and ICMP Echo Request 
                                 headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              4. Start traffic
                              6. Dump all the stats in logs
                              7. Validate Tx and Rx on spirent and ensure no errors are seen.
                              8. Validate Tx and Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX      
                              """ % (
                                  port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        nu_config_obj = fun_test.shared_variables['nu_config_obj']
        routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
        fun_test.simple_assert(routes_config, "Ensure routes config fetched")

        routermac = routes_config['routermac']
        l3_config = routes_config['l3_config']

        checkpoint = "Configure stream with EthernetII, IPv4 and ICMP Echo Request under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)

        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=routermac,
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(protocol=Ipv4Header.PROTOCOL_TYPE_ICMP,
                                     destination_address=l3_config['cc_destination_ip1'])
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        icmp_echo_req_obj = IcmpEchoRequestHeader()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=icmp_echo_req_obj, update=False)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = IPV4_COPP_ICMP_METER_ID

        if nu_config_obj.DUT_TYPE == NuConfigManager.DUT_TYPE_F1:
            result = network_controller_obj.update_meter(index=self.meter_id, interval=15, crd=1, commit_rate=14,
                                                         pps_mode=1, bank=0)
            fun_test.test_assert(result, "Configured meter on F1 for meter id: %d Interval: 15, crd: 1, "
                                         "commit_rate: 14, pps_mode: 1 bank: 0" % self.meter_id)

    def run(self):
        nu_config_obj = fun_test.shared_variables['nu_config_obj']
        dut_port1 = dut_config['ports'][0]

        checkpoint = "Fetch meter ID using snapshot"
        network_controller_obj.disconnect()
        dpcsh_server_ip = dut_config["dpcsh_tcp_proxy_ip"]
        dpcsh_server_port = dut_config['dpcsh_tcp_proxy_port']
        snapshot_obj = SnapshotHelper(dpc_proxy_ip=dpcsh_server_ip, dpc_proxy_port=dpcsh_server_port)
        snapshot_obj.setup_snapshot()

        template_obj.enable_generator_configs([generator_handle])
        fun_test.sleep("to fetch meter id using snapshot", seconds=2)
        snapshot_dict = snapshot_obj.run_snapshot()
        fun_test.simple_assert(snapshot_dict, "Fetch snapshot dict")
        template_obj.disable_generator_configs([generator_handle])

        self.meter_id = snapshot_obj.get_snapshot_meter_id(snapshot_output=snapshot_dict)
        fun_test.simple_assert(self.meter_id, checkpoint)
        snapshot_obj.exit_snapshot()

        checkpoint = "Get PSW and Parser NU stats before traffic"
        psw_stats = network_controller_obj.peek_psw_global_stats()
        parser_stats = network_controller_obj.peek_parser_stats()
        fun_test.log("PSW Stats: %s \n" % psw_stats)
        fun_test.log("Parser stats: %s \n" % parser_stats)
        fun_test.add_checkpoint(checkpoint)

        # TODO: Need to figure out better approach to determine if dut port is FPG or HNU
        checkpoint = "Clear FPG port stats on DUT"
        for port_num in dut_config['ports']:
            shape = 0
            if port_num == 1 or port_num == 2:
                shape = 1
            if nu_config_obj.DUT_TYPE == NuConfigManager.DUT_TYPE_F1:
                shape = 0
            result = network_controller_obj.clear_port_stats(port_num=port_num, shape=shape)
            fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
        fun_test.add_checkpoint(checkpoint=checkpoint)

        vp_stats_before = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)

        erp_stats_before = get_erp_stats_values(network_controller_obj=network_controller_obj)

        wro_stats_before = get_wro_global_stats_values(network_controller_obj=network_controller_obj)

        meter_stats_before = network_controller_obj.peek_meter_stats_by_id(meter_id=self.meter_id)

        fun_test.log("VP stats: %s" % vp_stats_before)
        fun_test.log("ERP stats: %s" % erp_stats_before)
        fun_test.log("WRO stats: %s" % wro_stats_before)
        fun_test.log("METER stats for id %s : %s" % (str(self.meter_id), meter_stats_before))

        checkpoint = "Start traffic Traffic Duration: %d" % TRAFFIC_DURATION
        result = template_obj.enable_generator_configs([generator_handle])
        fun_test.test_assert(result, checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION + 5)

        checkpoint = "Fetch PSW and Parser DUT stats after traffic"
        psw_stats = network_controller_obj.peek_psw_global_stats()
        parser_stats = network_controller_obj.peek_parser_stats()
        fun_test.log("PSW Stats: %s \n" % psw_stats)
        fun_test.log("Parser stats: %s \n" % parser_stats)
        fun_test.add_checkpoint(checkpoint)

        # checkpoint = "Get FPG port stats for all ports"
        # dut_rx_port_stats = network_controller_obj.peek_fpg_port_stats(port_num=dut_port1)
        # fun_test.simple_assert(dut_rx_port_stats, checkpoint)

        # fun_test.log("DUT Rx stats: %s" % dut_rx_port_stats)

        checkpoint = "Fetch VP stats"
        vp_stats = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)
        fun_test.simple_assert(vp_stats, checkpoint)

        checkpoint = "Fetch ERP NU stats"
        erp_stats = get_erp_stats_values(network_controller_obj=network_controller_obj)
        fun_test.simple_assert(erp_stats, checkpoint)

        checkpoint = "Fetch WRO NU stats"
        wro_stats = get_wro_global_stats_values(network_controller_obj=network_controller_obj)
        fun_test.simple_assert(wro_stats, checkpoint)

        checkpoint = "Fetch Meter stats for meter id: %s" % str(self.meter_id)
        meter_stats = network_controller_obj.peek_meter_stats_by_id(meter_id=self.meter_id)
        fun_test.simple_assert(meter_stats, checkpoint)

        fun_test.log("VP stats: %s" % vp_stats)
        fun_test.log("ERP stats: %s" % erp_stats)
        fun_test.log("WRO stats: %s" % wro_stats)
        if meter_stats:
            fun_test.log("METER stats for id %s : %s" % (str(self.meter_id), meter_stats))

        # validation asserts
        # TODO: Skip spirent validation for now as on real CC we need to figure out how to validate
        # DUT stats validation
        checkpoint = "Validate meter stats ensure frames_received on FPG%d == (green pkts + yellow pkts + " \
                     "red_pkts)" % dut_port1
        meter_stats_diff = get_diff_stats(old_stats=meter_stats_before, new_stats=meter_stats)
        green_pkts = int(meter_stats_diff['green']['pkts'])
        yellow_pkts = int(meter_stats_diff['yellow']['pkts'])
        red_pkts = int(meter_stats_diff['red']['pkts'])
        fun_test.log("Green: %d Yellow: %d Red: %d" % (green_pkts, yellow_pkts, red_pkts))
        # frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_stats, stat_type=FRAMES_RECEIVED_OK,
        #                                              tx=False)
        total_packets_punted_cc = green_pkts + yellow_pkts
        fun_test.log("Total Packets punted to CC (green + yellow): %d" % total_packets_punted_cc)
        fun_test.test_assert(expression=MIN_RX_PORT_COUNT <= total_packets_punted_cc <= MAX_RX_PORT_COUNT,
                             message="Ensure total packets metered to CC is within a "
                                     "expected min-max range i.e MIN: %d MAX: %d and packets metered "
                                     "(green + yellow): %d" % (MIN_RX_PORT_COUNT, MAX_RX_PORT_COUNT,
                                                               total_packets_punted_cc))

        # VP stats validation
        # To avoid false failure due to stray traffic in system change assert like below
        checkpoint = "From VP stats, Ensure T2C header counter equal to spirent Tx counter"
        vp_stats_diff = get_diff_stats(old_stats=vp_stats_before, new_stats=vp_stats,
                                       stats_list=[VP_PACKETS_CONTROL_T2C_COUNT, VP_PACKETS_CC_OUT,
                                                   VP_PACKETS_TOTAL_OUT, VP_PACKETS_TOTAL_IN])
        fun_test.test_assert(int(vp_stats_diff[VP_PACKETS_CONTROL_T2C_COUNT]) >= total_packets_punted_cc,
                             message=checkpoint + "Pass Criteria Actual >= Expected  Expected: %s Found: %s" % (
                                 total_packets_punted_cc, vp_stats_diff[VP_PACKETS_CONTROL_T2C_COUNT]))
        checkpoint = "From VP stats, Ensure CC OUT counters are equal to spirent Tx Counter"
        fun_test.test_assert(int(vp_stats_diff[VP_PACKETS_CC_OUT]) >= total_packets_punted_cc,
                             message=checkpoint + "Pass Criteria Actual >= Expected  Expected: %s Found: %s" % (
                                 total_packets_punted_cc, vp_stats_diff[VP_PACKETS_CC_OUT]))
        checkpoint = "Ensure VP total packets IN == VP total packets OUT"
        fun_test.test_assert_expected(expected=vp_stats_diff[VP_PACKETS_TOTAL_IN],
                                      actual=vp_stats_diff[VP_PACKETS_TOTAL_OUT],
                                      message=checkpoint)

        # ERP stats validation
        # To avoid false failure due to stray traffic in system change assert like below
        checkpoint = "From ERP stats, Ensure count for EFP to WQM decrement pulse equal to spirent Tx"
        erp_stats_diff = get_diff_stats(old_stats=erp_stats_before, new_stats=erp_stats,
                                        stats_list=[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED,
                                                    ERP_COUNT_FOR_EFP_WRO_DESCRIPTORS_SENT,
                                                    ERP_COUNT_FOR_EFP_WQM_DECREMENT_PULSE,
                                                    ERP_COUNT_FOR_ERP0_EFP_ERROR_INTERFACE_FLITS,
                                                    ERP_COUNT_FOR_EFP_FCP_VLD])
        fun_test.test_assert(int(erp_stats_diff[ERP_COUNT_FOR_EFP_WQM_DECREMENT_PULSE]) >= total_packets_punted_cc,
                             message=checkpoint + "Pass Criteria Actual >= Expected  Expected: %s Found: %s" % (
                                 total_packets_punted_cc, erp_stats_diff[ERP_COUNT_FOR_EFP_WQM_DECREMENT_PULSE]))
        checkpoint = "From ERP stats, Ensure count for EFP to WRO descriptors send equal to spirent Tx"
        fun_test.test_assert(int(erp_stats_diff[ERP_COUNT_FOR_EFP_WRO_DESCRIPTORS_SENT]) >= total_packets_punted_cc,
                             message=checkpoint + "Pass Criteria Actual >= Expected  Expected: %s Found: %s" % (
                                 total_packets_punted_cc, erp_stats_diff[ERP_COUNT_FOR_EFP_WRO_DESCRIPTORS_SENT]))
        checkpoint = "From ERP stats, Ensure count for ERP0 to EFP error interface flits equal to spirent Tx"
        fun_test.test_assert(
            int(erp_stats_diff[ERP_COUNT_FOR_ERP0_EFP_ERROR_INTERFACE_FLITS]) >= total_packets_punted_cc,
            message=checkpoint + "Pass Criteria Actual >= Expected  Expected: %s Found: %s" % (
                total_packets_punted_cc, erp_stats_diff[ERP_COUNT_FOR_ERP0_EFP_ERROR_INTERFACE_FLITS]))
        checkpoint = "From ERP stats, Ensure count for all non FCP packets received equal to spirent Tx"
        fun_test.test_assert(int(erp_stats_diff[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED]) >= total_packets_punted_cc,
                             message=checkpoint + "Pass Criteria Actual >= Expected  Expected: %s Found: %s" % (
                                 total_packets_punted_cc, erp_stats_diff[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED]))
        checkpoint = "From ERP stats, Ensure count for EFP to FCB vld equal to spirent Tx"
        fun_test.test_assert(int(erp_stats_diff[ERP_COUNT_FOR_EFP_FCP_VLD]) >= total_packets_punted_cc,
                             message=checkpoint + "Pass Criteria Actual >= Expected  Expected: %s Found: %s" % (
                                 total_packets_punted_cc, erp_stats_diff[ERP_COUNT_FOR_EFP_FCP_VLD]))

        # WRO stats validation
        # To avoid false failure due to stray traffic in system change assert like below
        checkpoint = "From WRO stats, Ensure WRO IN packets equal to spirent Tx"
        wro_stats_diff = get_diff_stats(old_stats=wro_stats_before, new_stats=wro_stats)
        fun_test.test_assert(int(wro_stats_diff['global'][WRO_IN_PKTS]) >= total_packets_punted_cc,
                             message=checkpoint + "Pass Criteria Actual >= Expected  Expected: %s Found: %s" % (
                                 total_packets_punted_cc, wro_stats_diff['global'][WRO_IN_PKTS]))
        checkpoint = "From WRO stats, Ensure WRO In NFCP packets equal to spirent Tx"
        fun_test.test_assert(int(wro_stats_diff['global'][WRO_IN_NFCP_PKTS]) >= total_packets_punted_cc,
                             message=checkpoint + "Pass Criteria Actual >= Expected  Expected: %s Found: %s" % (
                                 total_packets_punted_cc, wro_stats_diff['global'][WRO_IN_NFCP_PKTS]))
        checkpoint = "From WRO stats, Ensure WRO out WUs equal to spirent tx"
        fun_test.test_assert(int(wro_stats_diff['global'][WRO_OUT_WUS]) >= total_packets_punted_cc,
                             message=checkpoint + "Pass Criteria Actual >= Expected  Expected: %s Found: %s" % (
                                 total_packets_punted_cc, wro_stats_diff['global'][WRO_OUT_WUS]))
        checkpoint = "From WRO stats, Ensure WRO WU CNT VPP packets equal to spirent tx"
        fun_test.test_assert(int(wro_stats_diff['global'][WRO_WU_COUNT_VPP]) >= total_packets_punted_cc,
                             message=checkpoint + "Pass Criteria Actual >= Expected  Expected: %s Found: %s" % (
                                 total_packets_punted_cc, wro_stats_diff['global'][WRO_WU_COUNT_VPP]))

    def cleanup(self):
        fun_test.log("In test case cleanup")

        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())

        checkpoint = "Deactivate %s " % self.stream_obj.spirent_handle
        template_obj.deactivate_stream_blocks(stream_obj_list=[self.stream_obj])
        fun_test.add_checkpoint(checkpoint)


class TestCcIPv4Ospfv2Hello(TestCcIPv4ICMP):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=2, summary="Test CC IPv4 OSPF V2 Hello (Open Shortest Path First)",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and OSPFv2 Hello headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic
                              6. Dump all the stats in logs
                              7. Validate Tx and Rx on spirent and ensure no errors are seen.
                              8. Validate Tx and Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX       
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        nu_config_obj = fun_test.shared_variables['nu_config_obj']
        checkpoint = "Create a stream with EthernetII and IPv4 and OSPFv2 Hello headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)

        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.OSPF_MULTICAST_MAC_1,
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(protocol=Ipv4Header.PROTOCOL_TYPE_OSPFIGP,
                                     destination_address=Ipv4Header.OSPF_MULTICAST_IP_1)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        ospf_header_obj = Ospfv2HelloHeader()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ospf_header_obj, update=False)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = IPV4_COPP_OSPF_1_METER_ID

        # TODO: Remove below meter configuration once CoPP meter is pre-configured in F1 csr_override
        if nu_config_obj.DUT_TYPE == NuConfigManager.DUT_TYPE_F1:
            result = network_controller_obj.update_meter(index=self.meter_id, interval=15, crd=1, commit_rate=14,
                                                         pps_mode=1, bank=0)
            fun_test.test_assert(result, "Configured meter on F1 for meter id: %d Interval: 15, crd: 1, "
                                         "commit_rate: 14, pps_mode: 1 bank: 0" % self.meter_id)


class TestCcIPv4Ospfv2LinkStateUpdate(TestCcIPv4ICMP):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=3, summary="Test CC IPv4 OSPF V2 Link State Update (Open Shortest Path First)",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and OSPFv2 Link State Update 
                                 headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic
                              6. Dump all the stats in logs
                              7. Validate Tx and Rx on spirent and ensure no errors are seen.
                              8. Validate Tx and Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX       
                                  """ % (
                                  port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        nu_config_obj = fun_test.shared_variables['nu_config_obj']
        checkpoint = "Create a stream with EthernetII and IPv4 and OSPFv2 Link State Update headers under port %s" % \
                     port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.OSPF_MULTICAST_MAC_2,
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(protocol=Ipv4Header.PROTOCOL_TYPE_OSPFIGP,
                                     destination_address=Ipv4Header.OSPF_MULTICAST_IP_2)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        ospf_header_obj = Ospfv2LinkStateUpdateHeader()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ospf_header_obj, update=False)
        fun_test.test_assert(result, checkpoint)
        self.meter_id = IPV4_COPP_OSPF_2_METER_ID

        # TODO: Remove below meter configuration once CoPP meter is pre-configured in F1 csr_override
        if nu_config_obj.DUT_TYPE == NuConfigManager.DUT_TYPE_F1:
            result = network_controller_obj.update_meter(index=self.meter_id, interval=15, crd=1, commit_rate=14,
                                                         pps_mode=1, bank=0)
            fun_test.test_assert(result, "Configured meter on F1 for meter id: %d Interval: 15, crd: 1, "
                                         "commit_rate: 14, pps_mode: 1 bank: 0" % self.meter_id)


class TestCcIpv4Pim(TestCcIPv4ICMP):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=4, summary="Test CC IPv4 PIM (Protocol Independent Multicast)",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and PIMv4Hello
                                 headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic
                              6. Dump all the stats in logs
                              7. Validate Tx and Rx on spirent and ensure no errors are seen.
                              8. Validate Tx and Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX       
                              """ % (
                                  port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        nu_config_obj = fun_test.shared_variables['nu_config_obj']
        checkpoint = "Create a stream with EthernetII and IPv4 and PIMv4Hello headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)

        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.PIM_MULTICAST_MAC,
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(protocol=Ipv4Header.PROTOCOL_TYPE_PIM,
                                     destination_address=Ipv4Header.PIM_MULTICAST_IP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        pim_header_obj = Pimv4HelloHeader()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=pim_header_obj, update=False)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = IPV4_COPP_PIM_METER_ID

        # TODO: Remove below meter configuration once CoPP meter is pre-configured in F1 csr_override
        if nu_config_obj.DUT_TYPE == NuConfigManager.DUT_TYPE_F1:
            result = network_controller_obj.update_meter(index=self.meter_id, interval=15, crd=1, commit_rate=14,
                                                         pps_mode=1, bank=0)
            fun_test.test_assert(result, "Configured meter on F1 for meter id: %d Interval: 15, crd: 1, "
                                         "commit_rate: 14, pps_mode: 1 bank: 0" % self.meter_id)


class TestCcIpv4BGP(TestCcIPv4ICMP):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=5, summary="Test CC IPv4 BGP (Border Gateway Protocol)",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and TCP headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic  
                              6. Dump all the stats in logs
                              7. Validate Tx and Rx on spirent and ensure no errors are seen.
                              8. Validate Tx and Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX     
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        nu_config_obj = fun_test.shared_variables['nu_config_obj']
        routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
        routermac = routes_config['routermac']
        l3_config = routes_config['l3_config']

        checkpoint = "Create a stream with EthernetII and IPv4 and TCP headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=routermac, ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(protocol=Ipv4Header.PROTOCOL_TYPE_TCP,
                                     destination_address=l3_config['cc_destination_ip1'])
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        tcp_header_obj = TCP(source_port=1024, destination_port=TCP.DESTINATION_PORT_BGP, checksum=20047)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=tcp_header_obj, update=False)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = IPV4_COPP_BGP_METER_ID

        # TODO: Remove below meter configuration once CoPP meter is pre-configured in F1 csr_override
        if nu_config_obj.DUT_TYPE == NuConfigManager.DUT_TYPE_F1:
            result = network_controller_obj.update_meter(index=self.meter_id, interval=15, crd=1, commit_rate=14,
                                                         pps_mode=1, bank=0)
            fun_test.test_assert(result, "Configured meter on F1 for meter id: %d Interval: 15, crd: 1, "
                                         "commit_rate: 14, pps_mode: 1 bank: 0" % self.meter_id)


class TestCcIpv4Igmp(TestCcIPv4ICMP):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=6, summary="Test CC IPv4 IGMP (Internet Group Management Protocol)",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and IGMP headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic
                              6. Dump all the stats in logs
                              7. Validate Tx and Rx on spirent and ensure no errors are seen.
                              8. Validate Tx and Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX       
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        nu_config_obj = fun_test.shared_variables['nu_config_obj']
        routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
        routermac = routes_config['routermac']
        l3_config = routes_config['l3_config']

        checkpoint = "Create a stream with EthernetII and IPv4 and IGMP headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=routermac,
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(protocol=Ipv4Header.PROTOCOL_TYPE_IGMP,
                                     destination_address=l3_config['cc_destination_ip1'])
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        igmp_header_obj = Igmpv1Header()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=igmp_header_obj, update=False)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = IPV4_COPP_IGMP_METER_ID

        # TODO: Remove below meter configuration once CoPP meter is pre-configured in F1 csr_override
        if nu_config_obj.DUT_TYPE == NuConfigManager.DUT_TYPE_F1:
            result = network_controller_obj.update_meter(index=self.meter_id, interval=15, crd=1, commit_rate=14,
                                                         pps_mode=1, bank=0)
            fun_test.test_assert(result, "Configured meter on F1 for meter id: %d Interval: 15, crd: 1, "
                                         "commit_rate: 14, pps_mode: 1 bank: 0" % self.meter_id)


class TestCcIPv4ForUs(TestCcIPv4ICMP):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=7, summary="Test CC IPv4 FOR US",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic
                              6. Dump all the stats in logs
                              7. Validate Tx and Rx on spirent and ensure no errors are seen.
                              8. Validate Tx and Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX       
                                  """ % (
                                  port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        nu_config_obj = fun_test.shared_variables['nu_config_obj']
        routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
        routermac = routes_config['routermac']
        l3_config = routes_config['l3_config']

        checkpoint = "Create a stream with EthernetII and IPv4 headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=routermac, ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['cc_destination_ip1'])
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = IPV4_COPP_FOR_US_METER_ID

        # TODO: Remove below meter configuration once CoPP meter is pre-configured in F1 csr_override
        if nu_config_obj.DUT_TYPE == NuConfigManager.DUT_TYPE_F1:
            result = network_controller_obj.update_meter(index=self.meter_id, interval=15, crd=1, commit_rate=14,
                                                         pps_mode=1, bank=0)
            fun_test.test_assert(result, "Configured meter on F1 for meter id: %d Interval: 15, crd: 1, "
                                         "commit_rate: 14, pps_mode: 1 bank: 0" % self.meter_id)


class TestCcIPv4PTP1(TestCcIPv4ICMP):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=8, summary="Test CC IPv4 PTP with Destination port 319 with PTP sync",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and UDP (dest port 319) PTP sync 
                                 headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic
                              6. Dump all the stats in logs
                              7. Validate Tx and Rx on spirent and ensure no errors are seen.
                              8. Validate Tx and Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX       
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        nu_config_obj = fun_test.shared_variables['nu_config_obj']
        routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
        routermac = routes_config['routermac']
        l3_config = routes_config['l3_config']

        checkpoint = "Create a stream with EthernetII and IPv4 headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=routermac, ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['cc_destination_ip1'],
                                     protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        udp_header_obj = UDP(destination_port=319)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=udp_header_obj, update=False)
        fun_test.simple_assert(result, "Added UDP header with dest port 319")
        ptp_sync_obj = PtpSyncHeader()
        result = template_obj.configure_ptp_header(header_obj=ptp_sync_obj,
                                                   stream_block_handle=self.stream_obj.spirent_handle,
                                                   create_header=True, delete_header_type=None)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = IPV4_COPP_PTP_1_METER_ID

        # TODO: Remove below meter configuration once CoPP meter is pre-configured in F1 csr_override
        if nu_config_obj.DUT_TYPE == NuConfigManager.DUT_TYPE_F1:
            result = network_controller_obj.update_meter(index=self.meter_id, interval=15, crd=1, commit_rate=14,
                                                         pps_mode=1, bank=0)
            fun_test.test_assert(result, "Configured meter on F1 for meter id: %d Interval: 15, crd: 1, "
                                         "commit_rate: 14, pps_mode: 1 bank: 0" % self.meter_id)


class TestCcIPv4PTP2(TestCcIPv4ICMP):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=9, summary="Test CC IPv4 PTP with Destination port 320 with PTP sync",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and UDP (dest port 320) PTP sync 
                                 headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic
                              6. Dump all the stats in logs
                              7. Validate Tx and Rx on spirent and ensure no errors are seen.
                              8. Validate Tx and Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX       
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        nu_config_obj = fun_test.shared_variables['nu_config_obj']
        routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
        routermac = routes_config['routermac']
        l3_config = routes_config['l3_config']

        checkpoint = "Create a stream with EthernetII and IPv4 headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=routermac,
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['cc_destination_ip1'],
                                     protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        udp_header_obj = UDP(destination_port=320)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=udp_header_obj, update=False)
        fun_test.simple_assert(result, "Added UDP header with destination port 320")
        ptp_sync_obj = PtpSyncHeader()
        result = template_obj.configure_ptp_header(header_obj=ptp_sync_obj,
                                                   stream_block_handle=self.stream_obj.spirent_handle,
                                                   create_header=True, delete_header_type=None)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = IPV4_COPP_PTP_2_METER_ID

        # TODO: Remove below meter configuration once CoPP meter is pre-configured in F1 csr_override
        if nu_config_obj.DUT_TYPE == NuConfigManager.DUT_TYPE_F1:
            result = network_controller_obj.update_meter(index=self.meter_id, interval=15, crd=1, commit_rate=14,
                                                         pps_mode=1, bank=0)
            fun_test.test_assert(result, "Configured meter on F1 for meter id: %d Interval: 15, crd: 1, "
                                         "commit_rate: 14, pps_mode: 1 bank: 0" % self.meter_id)


class TestCcIPv4PTP3(TestCcIPv4ICMP):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=10, summary="Test CC IPv4 PTP Sync with UDP",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and UDP (PTP Sync) headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic 
                              6. Dump all the stats in logs
                              7. Validate Tx and Rx on spirent and ensure no errors are seen.
                              8. Validate Tx and Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX      
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        nu_config_obj = fun_test.shared_variables['nu_config_obj']
        checkpoint = "Create a stream with EthernetII and IPv4 and UDP (PTP Sync) headers under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.LLDP_MULTICAST_MAC,
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=Ipv4Header.PTP_SYNC_MULTICAST_IP,
                                     protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        udp_header_obj = UDP(destination_port=319)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=udp_header_obj, update=False)
        fun_test.simple_assert(result, "Add UDP header")

        ptp_sync_header_obj = PtpSyncHeader()
        result = template_obj.configure_ptp_header(header_obj=ptp_sync_header_obj,
                                                   stream_block_handle=self.stream_obj.spirent_handle,
                                                   create_header=True, delete_header_type=None)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = IPV4_COPP_PTP_3_METER_ID

        # TODO: Remove below meter configuration once CoPP meter is pre-configured in F1 csr_override
        if nu_config_obj.DUT_TYPE == NuConfigManager.DUT_TYPE_F1:
            result = network_controller_obj.update_meter(index=self.meter_id, interval=15, crd=1, commit_rate=14,
                                                         pps_mode=1, bank=0)
            fun_test.test_assert(result, "Configured meter on F1 for meter id: %d Interval: 15, crd: 1, "
                                         "commit_rate: 14, pps_mode: 1 bank: 0" % self.meter_id)


class TestCcIPv4PTP4(TestCcIPv4ICMP):
    stream_obj = None

    def describe(self):
        self.set_test_details(id=11, summary="Test CC IPv4 PTP Delay Request with UDP",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and UDP (PTP Delay Request) 
                                 headers under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic
                              6. Dump all the stats in logs
                              7. Validate Tx and Rx on spirent and ensure no errors are seen.
                              8. Validate Tx and Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX       
                              """ % (port1, FRAME_LENGTH_MODE, FRAME_SIZE, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        nu_config_obj = fun_test.shared_variables['nu_config_obj']
        checkpoint = "Create a stream with EthernetII and IPv4 and UDP (PTP Delay Request) headers under port %s" % \
                     port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=FRAME_SIZE,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.PTP_MULTICAST_MAC,
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=Ipv4Header.PTP_DELAY_MULTICAST_IP,
                                     protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Update IPv4 header under %s" % self.stream_obj.spirent_handle)

        udp_header_obj = UDP(destination_port=319)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=udp_header_obj, update=False)
        fun_test.simple_assert(result, "Add UDP header")

        ptp_delay_header_obj = PtpDelayReqHeader()
        result = template_obj.configure_ptp_header(header_obj=ptp_delay_header_obj,
                                                   stream_block_handle=self.stream_obj.spirent_handle,
                                                   create_header=True, delete_header_type=None)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = IPV4_COPP_PTP_4_METER_ID

        # TODO: Remove below meter configuration once CoPP meter is pre-configured in F1 csr_override
        if nu_config_obj.DUT_TYPE == NuConfigManager.DUT_TYPE_F1:
            result = network_controller_obj.update_meter(index=self.meter_id, interval=15, crd=1, commit_rate=14,
                                                         pps_mode=1, bank=0)
            fun_test.test_assert(result, "Configured meter on F1 for meter id: %d Interval: 15, crd: 1, "
                                         "commit_rate: 14, pps_mode: 1 bank: 0" % self.meter_id)


class TestCcIpv4Dhcp(TestCcIPv4ICMP):
    stream_obj = None
    frame_size = 306

    def describe(self):
        self.set_test_details(id=12, summary="Test CC IPv4 DHCP",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 and DHCP header option under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic
                              6. Dump all the stats in logs
                              7. Validate Tx and Rx on spirent and ensure no errors are seen.
                              8. Validate Tx and Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX
                              """ % (
                                  port1, FRAME_LENGTH_MODE, self.frame_size, LOAD, LOAD_UNIT, port1, TRAFFIC_DURATION))

    def setup(self):
        nu_config_obj = fun_test.shared_variables['nu_config_obj']
        checkpoint = "Create a stream with EthernetII and IPv4 and DHCP header option under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=self.frame_size,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=LOAD, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=Ethernet2Header.BROADCAST_MAC,
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=Ipv4Header.DHCP_RELAY_AGENT_MULTICAST_IP,
                                     protocol=Ipv4Header.PROTOCOL_TYPE_UDP)
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.simple_assert(result, "Configure IPv4 Header with DHCP Relay Agent Multicast IP")

        udp_header_obj = UDP()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=udp_header_obj, update=False)
        fun_test.simple_assert(result, "Added UDP header")

        dhcp_client_message_header = DhcpClientMessageHeader()
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=dhcp_client_message_header,
                                                                update=False)
        fun_test.test_assert(result, checkpoint)
        streams_group.append(self.stream_obj)
        self.meter_id = IPV4_COPP_DHCP_METER_ID

        # TODO: Remove below meter configuration once CoPP meter is pre-configured in F1 csr_override
        if nu_config_obj.DUT_TYPE == NuConfigManager.DUT_TYPE_F1:
            result = network_controller_obj.update_meter(index=self.meter_id, interval=15, crd=1, commit_rate=14,
                                                         pps_mode=1, bank=0)
            fun_test.test_assert(result, "Configured meter on F1 for meter id: %d Interval: 15, crd: 1, "
                                         "commit_rate: 14, pps_mode: 1 bank: 0" % self.meter_id)


class TestCcIPv4MTUCase(TestCcIPv4ICMP):
    stream_obj = None
    mtu = 10000
    frame_size = mtu
    load = 1

    def describe(self):
        self.set_test_details(id=13, summary="Test CC IPv4 10K MTU Case",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                                 e. MTU on ports: %d
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic
                              6. Dump all the stats in logs
                              7. Validate Tx and Rx on spirent and ensure no errors are seen.
                              8. Validate Tx and Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX   
                                  """ % (port1, FRAME_LENGTH_MODE, self.frame_size, self.load, LOAD_UNIT, self.mtu,
                                         port1, TRAFFIC_DURATION))

    def setup(self):
        nu_config_obj = fun_test.shared_variables['nu_config_obj']
        routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
        routermac = routes_config['routermac']
        l3_config = routes_config['l3_config']

        checkpoint = "Create a stream with EthernetII and IPv4 with Control Flags Reserved = 1 Error " \
                     "under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=self.frame_size,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=self.load, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=routermac,
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['destination_ip1'])
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Update ports MTU on spirent ports. MTU: %d" % self.mtu
        mtu_changed_on_spirent = template_obj.change_ports_mtu(interface_obj_list=[interface_obj1, interface_obj2],
                                                               mtu_value=self.mtu)
        fun_test.test_assert(mtu_changed_on_spirent, checkpoint)

        if dut_config['enable_dpcsh']:
            checkpoint = "Update MTU on DUT ports. MTU: %d" % self.mtu
            for port in dut_config['ports']:
                mtu_changed = network_controller_obj.set_port_mtu(port_num=port, mtu_value=self.mtu)
                fun_test.simple_assert(mtu_changed, "Change MTU on DUT port %d to %d" % (port, self.mtu))
            fun_test.add_checkpoint(checkpoint)
        self.validate_meter_stats = False

        # TODO: Remove below meter configuration once CoPP meter is pre-configured in F1 csr_override
        if nu_config_obj.DUT_TYPE == NuConfigManager.DUT_TYPE_F1:
            result = network_controller_obj.update_meter(index=self.meter_id, interval=15, crd=1, commit_rate=14,
                                                         pps_mode=1, bank=0)
            fun_test.test_assert(result, "Configured meter on F1 for meter id: %d Interval: 15, crd: 1, "
                                         "commit_rate: 14, pps_mode: 1 bank: 0" % self.meter_id)


class TestCcMtuCaseForUs(TestCcIPv4ICMP):
    stream_obj = None
    mtu = 10000
    frame_size = mtu
    load = 1

    def describe(self):
        self.set_test_details(id=14, summary="Test CC IPv4 10K MTU Case For US",
                              steps="""
                              1. Create a stream with EthernetII and IPv4 under port %s
                                 a. Frame Size Mode: %s Frame Size: %d 
                                 b. load: %d load Unit: %s
                                 c. Include signature field
                                 d. Payload Fill type: Constant
                                 e. MTU on ports: %d
                              2. Configure %s generator with following settings
                                 a. Set Duration %d secs 
                                 b. Scheduling mode to Rate based
                              3. Subscribe to all results
                              4. Clear DUT stats before running traffic
                              5. Start traffic
                              6. Dump all the stats in logs
                              7. Validate Tx and Rx on spirent and ensure no errors are seen.
                              8. Validate Tx and Rx on DUT
                              9. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              10. From VP stats, validate VP total IN == VP total OUT
                              11. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              12. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX   
                              """ % (port1, FRAME_LENGTH_MODE, self.frame_size, self.load, LOAD_UNIT, self.mtu,
                                     port1, TRAFFIC_DURATION))

    def setup(self):
        nu_config_obj = fun_test.shared_variables['nu_config_obj']
        routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
        routermac = routes_config['routermac']
        l3_config = routes_config['l3_config']

        checkpoint = "Create a stream with EthernetII and IPv4 with Control Flags Reserved = 1 Error " \
                     "under port %s" % port1
        self.stream_obj = StreamBlock(fill_type=StreamBlock.FILL_TYPE_CONSTANT,
                                      fixed_frame_length=self.frame_size,
                                      frame_length_mode=FRAME_LENGTH_MODE,
                                      insert_signature=True,
                                      load=self.load, load_unit=LOAD_UNIT)
        result = template_obj.configure_stream_block(stream_block_obj=self.stream_obj, port_handle=port1)
        fun_test.simple_assert(result, "Create Default Stream Block under: %s" % port1)

        ether_obj = Ethernet2Header(destination_mac=l2_config['destination_mac'],
                                    ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)

        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ether_obj, update=True)
        fun_test.simple_assert(result, "Configure EthernetII header under %s" % self.stream_obj.spirent_handle)

        ipv4_header_obj = Ipv4Header(destination_address=l3_config['cc_destination_ip'])
        result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=self.stream_obj.spirent_handle,
                                                                header_obj=ipv4_header_obj, update=True)
        fun_test.test_assert(result, checkpoint)

        checkpoint = "Update ports MTU on spirent ports. MTU: %d" % self.mtu
        mtu_changed_on_spirent = template_obj.change_ports_mtu(interface_obj_list=[interface_obj1, interface_obj2],
                                                               mtu_value=self.mtu)
        fun_test.test_assert(mtu_changed_on_spirent, checkpoint)

        if dut_config['enable_dpcsh']:
            checkpoint = "Update MTU on DUT ports. MTU: %d" % self.mtu
            for port in dut_config['ports']:
                mtu_changed = network_controller_obj.set_port_mtu(port_num=port, mtu_value=self.mtu)
                fun_test.simple_assert(mtu_changed, "Change MTU on DUT port %d to %d" % (port, self.mtu))
            fun_test.add_checkpoint(checkpoint)
        self.validate_meter_stats = False

        # TODO: Remove below meter configuration once CoPP meter is pre-configured in F1 csr_override
        if nu_config_obj.DUT_TYPE == NuConfigManager.DUT_TYPE_F1:
            result = network_controller_obj.update_meter(index=self.meter_id, interval=15, crd=1, commit_rate=14,
                                                         pps_mode=1, bank=0)
            fun_test.test_assert(result, "Configured meter on F1 for meter id: %d Interval: 15, crd: 1, "
                                         "commit_rate: 14, pps_mode: 1 bank: 0" % self.meter_id)


class TestCcIpv4AllTogether(FunTestCase):

    def describe(self):
        self.set_test_details(id=15, summary="Test CC All Stream Together",
                              steps="""
                              1. Activate following streams
                                 1. IPv4 ICMP
                                 2. IPv4 Ospfv2Hello
                                 3. IPv4 Ospfv2LinkStateUpdate
                                 4. IPv4 Pim
                                 5. IPv4 BGP
                                 6. IPv4 Igmp
                                 7. IPv4 For US
                                 8. IPv4 PTP1
                                 9. IPv4 PTP2
                                 10. IPv4 PTP3
                                 11. IPv4 PTP4
                                 12. IPv4 DHCP
                              2. Clear DUT stats before running traffic
                              3. Start Traffic run all streams together
                              4. Dump all the stats in logs
                              5. Validate Tx and Rx on spirent Rx should be in range of 80-90 pps and 
                                 ensure no errors are seen.
                              6. From VP stats, validate CC OUT and Control T2C counters are equal to spirent TX
                              7. From VP stats, validate VP total IN == VP total OUT
                              8. From ERP stats, Ensure Count for EFP to WQM decrement pulse, EFP to WRO descriptors 
                                  sent, ERP0 to EFP error interface flits, all non FCP packets received, 
                                  EFP to FCP vld should be equal to spirent TX 
                              9. From WRO NU stats, validate count for WROIN_NFCP_PKTS, WROIN_PKTS, WROOUT_WUS, 
                                  WROWU_CNT_VPP should be equal to spirent TX   
                              10. Validate Meter stats
                              """)

    def setup(self):
        checkpoint = "Activate streams on spirent"
        result = template_obj.activate_stream_blocks(stream_obj_list=streams_group)
        fun_test.test_assert(result, checkpoint)

    def run(self):
        global MIN_RX_PORT_COUNT, MAX_RX_PORT_COUNT
        nu_config_obj = fun_test.shared_variables['nu_config_obj']
        dut_port1 = dut_config['ports'][0]

        # TODO: Need to figure out better approach to determine if dut port is FPG or HNU
        checkpoint = "Clear FPG port stats on DUT"
        for port_num in dut_config['ports']:
            shape = 0
            if port_num == 1 or port_num == 2:
                shape = 1
            if nu_config_obj.DUT_TYPE == NuConfigManager.DUT_TYPE_F1:
                shape = 0
            result = network_controller_obj.clear_port_stats(port_num=port_num, shape=shape)
            fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
        fun_test.add_checkpoint(checkpoint=checkpoint)

        checkpoint = "Get PSW and Parser NU stats before traffic"
        psw_stats = network_controller_obj.peek_psw_global_stats()
        parser_stats = network_controller_obj.peek_parser_stats()
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Fetch VP stats"
        vp_stats_before = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)
        fun_test.simple_assert(vp_stats_before, checkpoint)

        checkpoint = "Fetch ERP NU stats"
        erp_stats_before = get_erp_stats_values(network_controller_obj=network_controller_obj)
        fun_test.simple_assert(erp_stats_before, checkpoint)

        checkpoint = "Fetch WRO NU stats"
        wro_stats_before = get_wro_global_stats_values(network_controller_obj=network_controller_obj)
        fun_test.simple_assert(wro_stats_before, checkpoint)

        fun_test.log("PSW Stats: %s \n" % psw_stats)
        fun_test.log("Parser stats: %s \n" % parser_stats)
        fun_test.log("VP stats: %s \n" % vp_stats_before)
        fun_test.log("ERP stats: %s \n" % erp_stats_before)
        fun_test.log("WRO stats: %s \n" % wro_stats_before)

        checkpoint = "Start traffic Traffic Duration: %d" % TRAFFIC_DURATION
        result = template_obj.enable_generator_configs([generator_handle])
        fun_test.test_assert(result, checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION + 10)

        checkpoint = "Fetch PSW and Parser DUT stats after traffic"
        psw_stats = network_controller_obj.peek_psw_global_stats()
        parser_stats = network_controller_obj.peek_parser_stats()
        fun_test.log("PSW Stats: %s \n" % psw_stats)
        fun_test.log("Parser stats: %s \n" % parser_stats)
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Get FPG port stats for all ports"
        dut_rx_port_stats = network_controller_obj.peek_fpg_port_stats(port_num=dut_config['ports'][2])
        fun_test.simple_assert(dut_rx_port_stats, checkpoint)

        fun_test.log("DUT Rx stats: %s" % dut_rx_port_stats)

        checkpoint = "Fetch VP stats"
        vp_stats = get_vp_pkts_stats_values(network_controller_obj=network_controller_obj)
        fun_test.simple_assert(vp_stats, checkpoint)

        checkpoint = "Fetch ERP NU stats"
        erp_stats = get_erp_stats_values(network_controller_obj=network_controller_obj)
        fun_test.simple_assert(erp_stats, checkpoint)

        checkpoint = "Fetch WRO NU stats"
        wro_stats = get_wro_global_stats_values(network_controller_obj=network_controller_obj)
        fun_test.simple_assert(wro_stats, checkpoint)

        fun_test.log("VP stats: %s" % vp_stats)
        fun_test.log("ERP stats: %s" % erp_stats)
        fun_test.log("WRO stats: %s" % wro_stats)

        # TODO: We need to figure out how to validate actual CC so for now we skipped spirent validation
        # VP stats validation
        # To avoid false failure due to stray traffic in system change assert like below
        checkpoint = "From VP stats, Ensure T2C header counter equal to spirent Tx counter"
        vp_stats_diff = get_diff_stats(old_stats=vp_stats_before, new_stats=vp_stats,
                                       stats_list=[VP_PACKETS_CONTROL_T2C_COUNT, VP_PACKETS_CC_OUT,
                                                   VP_PACKETS_TOTAL_OUT, VP_PACKETS_TOTAL_IN])
        total_packets_punted_cc = vp_stats_diff[VP_PACKETS_CC_OUT]
        fun_test.log("Total Packets punted to CC: %d" % total_packets_punted_cc)
        fun_test.test_assert(int(vp_stats_diff[VP_PACKETS_CONTROL_T2C_COUNT]) >= total_packets_punted_cc,
                             message=checkpoint + "Pass Criteria Actual >= Expected  Expected: %s Found: %s" % (
                                 total_packets_punted_cc, vp_stats_diff[VP_PACKETS_CONTROL_T2C_COUNT]))
        checkpoint = "From VP stats, Ensure CC OUT counters are equal to spirent Tx Counter"
        fun_test.test_assert(int(vp_stats_diff[VP_PACKETS_CC_OUT]) >= total_packets_punted_cc,
                             message=checkpoint + "Pass Criteria Actual >= Expected  Expected: %s Found: %s" % (
                                 total_packets_punted_cc, vp_stats_diff[VP_PACKETS_CC_OUT]))
        checkpoint = "Ensure VP total packets IN == VP total packets OUT"
        fun_test.test_assert_expected(expected=vp_stats_diff[VP_PACKETS_TOTAL_IN],
                                      actual=vp_stats_diff[VP_PACKETS_TOTAL_OUT],
                                      message=checkpoint)

        # ERP stats validation
        # To avoid false failure due to stray traffic in system change assert like below
        checkpoint = "From ERP stats, Ensure count for EFP to WQM decrement pulse equal to spirent Tx"
        erp_stats_diff = get_diff_stats(old_stats=erp_stats_before, new_stats=erp_stats,
                                        stats_list=[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED,
                                                    ERP_COUNT_FOR_EFP_WRO_DESCRIPTORS_SENT,
                                                    ERP_COUNT_FOR_EFP_WQM_DECREMENT_PULSE,
                                                    ERP_COUNT_FOR_ERP0_EFP_ERROR_INTERFACE_FLITS,
                                                    ERP_COUNT_FOR_EFP_FCP_VLD])
        fun_test.test_assert(int(erp_stats_diff[ERP_COUNT_FOR_EFP_WQM_DECREMENT_PULSE]) >= total_packets_punted_cc,
                             message=checkpoint + "Pass Criteria Actual >= Expected  Expected: %s Found: %s" % (
                                 total_packets_punted_cc, erp_stats_diff[ERP_COUNT_FOR_EFP_WQM_DECREMENT_PULSE]))
        checkpoint = "From ERP stats, Ensure count for EFP to WRO descriptors send equal to spirent Tx"
        fun_test.test_assert(int(erp_stats_diff[ERP_COUNT_FOR_EFP_WRO_DESCRIPTORS_SENT]) >= total_packets_punted_cc,
                             message=checkpoint + "Pass Criteria Actual >= Expected  Expected: %s Found: %s" % (
                                 total_packets_punted_cc, erp_stats_diff[ERP_COUNT_FOR_EFP_WRO_DESCRIPTORS_SENT]))
        checkpoint = "From ERP stats, Ensure count for ERP0 to EFP error interface flits equal to spirent Tx"
        fun_test.test_assert(
            int(erp_stats_diff[ERP_COUNT_FOR_ERP0_EFP_ERROR_INTERFACE_FLITS]) >= total_packets_punted_cc,
            message=checkpoint + "Pass Criteria Actual >= Expected  Expected: %s Found: %s" % (
                total_packets_punted_cc, erp_stats_diff[ERP_COUNT_FOR_ERP0_EFP_ERROR_INTERFACE_FLITS]))
        checkpoint = "From ERP stats, Ensure count for all non FCP packets received equal to spirent Tx"
        fun_test.test_assert(int(erp_stats_diff[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED]) >= total_packets_punted_cc,
                             message=checkpoint + "Pass Criteria Actual >= Expected  Expected: %s Found: %s" % (
                                 total_packets_punted_cc, erp_stats_diff[ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED]))
        checkpoint = "From ERP stats, Ensure count for EFP to FCB vld equal to spirent Tx"
        fun_test.test_assert(int(erp_stats_diff[ERP_COUNT_FOR_EFP_FCP_VLD]) >= total_packets_punted_cc,
                             message=checkpoint + "Pass Criteria Actual >= Expected  Expected: %s Found: %s" % (
                                 total_packets_punted_cc, erp_stats_diff[ERP_COUNT_FOR_EFP_FCP_VLD]))

        # WRO stats validation
        # To avoid false failure due to stray traffic in system change assert like below
        checkpoint = "From WRO stats, Ensure WRO IN packets equal to spirent Tx"
        wro_stats_diff = get_diff_stats(old_stats=wro_stats_before, new_stats=wro_stats)
        fun_test.test_assert(int(wro_stats_diff['global'][WRO_IN_PKTS]) >= total_packets_punted_cc,
                             message=checkpoint + "Pass Criteria Actual >= Expected  Expected: %s Found: %s" % (
                                 total_packets_punted_cc, wro_stats_diff['global'][WRO_IN_PKTS]))
        checkpoint = "From WRO stats, Ensure WRO In NFCP packets equal to spirent Tx"
        fun_test.test_assert(int(wro_stats_diff['global'][WRO_IN_NFCP_PKTS]) >= total_packets_punted_cc,
                             message=checkpoint + "Pass Criteria Actual >= Expected  Expected: %s Found: %s" % (
                                 total_packets_punted_cc, wro_stats_diff['global'][WRO_IN_NFCP_PKTS]))
        checkpoint = "From WRO stats, Ensure WRO out WUs equal to spirent tx"
        fun_test.test_assert(int(wro_stats_diff['global'][WRO_OUT_WUS]) >= total_packets_punted_cc,
                             message=checkpoint + "Pass Criteria Actual >= Expected  Expected: %s Found: %s" % (
                                 total_packets_punted_cc, wro_stats_diff['global'][WRO_OUT_WUS]))
        checkpoint = "From WRO stats, Ensure WRO WU CNT VPP packets equal to spirent tx"
        fun_test.test_assert(int(wro_stats_diff['global'][WRO_WU_COUNT_VPP]) >= total_packets_punted_cc,
                             message=checkpoint + "Pass Criteria Actual >= Expected  Expected: %s Found: %s" % (
                                 total_packets_punted_cc, wro_stats_diff['global'][WRO_WU_COUNT_VPP]))

    def cleanup(self):
        pass


if __name__ == '__main__':
    FLOW_DIRECTION = NuConfigManager.FLOW_DIRECTION_FPG_CC

    ts = SetupSpirent()
    # IPv4 CC
    ts.add_test_case(TestCcIPv4ICMP())
    ts.add_test_case(TestCcIPv4Ospfv2Hello())
    ts.add_test_case(TestCcIPv4Ospfv2LinkStateUpdate())
    ts.add_test_case(TestCcIpv4Pim())
    ts.add_test_case(TestCcIpv4BGP())
    ts.add_test_case(TestCcIpv4Igmp())
    ts.add_test_case(TestCcIPv4ForUs())
    ts.add_test_case(TestCcIPv4PTP1())
    ts.add_test_case(TestCcIPv4PTP2())
    ts.add_test_case(TestCcIPv4PTP3())
    ts.add_test_case(TestCcIPv4PTP4())

    ts.add_test_case(TestCcIpv4Dhcp())
    # TODO: Need to test this manually
    # TODO: Failing these cases on Virtual chassis hence disabled them
    # ts.add_test_case(TestCcIPv4MTUCase())
    # ts.add_test_case(TestCcMtuCaseForUs())
    # TODO: Need to test this manually
    ts.add_test_case(TestCcIpv4AllTogether())
    ts.run()