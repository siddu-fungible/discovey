'''Author : Yajat N Singh'''
from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_traffic_generator_template import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import *
from lib.host.network_controller import *
from scripts.networking.nu_config_manager import *
from scripts.networking.helper import *
from lib.utilities.pcap_parser import *

spirent_config = {}
TEST_CONFIG_FILE = fun_test.get_script_parent_directory() + "/meter_dut_configs.json"
test_config = nu_config_obj.read_test_configs_by_dut_type(config_file=TEST_CONFIG_FILE)
TRAFFIC_DURATION = test_config['traffic_duration']
subscribed_results = None
NUM_PORTS = 2
generator_port_obj_dict = {}
analyzer_port_obj_dict = {}
meter_json_file = fun_test.get_script_parent_directory() + '/meter.json'
meter_json_output = fun_test.parse_file_to_json(meter_json_file)
meter_bps = meter_json_output[0]['bps_meter']
meter_pps = meter_json_output[0]['pps_meter']
METER_MODE_BPS=0
METER_MODE_PPS=1
TWO_COLOR_METER=0
THREE_COLOR_METER=1


def create_streams(tx_port, dip, dmac, load=test_config['load_pps'], load_type = test_config['fill_type'], sip="192.168.1.2", s_port=1024, d_port=1024, sync_bit='0', ack_bit='1', ecn_v4=0,
                   ipv6=False, v6_traffic_class=0):
    stream_obj = StreamBlock(fill_type=test_config['fill_type'], insert_signature=test_config['insert_signature'],
                             load = load, load_unit=load_type,
                             frame_length_mode= test_config['frame_length_mode'],
                             fixed_frame_length=test_config['fixed_frame_size'])

    if ipv6:
        stream_created = template_obj.configure_stream_block(stream_block_obj=stream_obj,
                                                             port_handle=tx_port, ip_header_version=6)
        ethernet_obj = Ethernet2Header(destination_mac=dmac, ether_type=Ethernet2Header.INTERNET_IPV6_ETHERTYPE)
        ip_header_obj = Ipv6Header(destination_address=dip, source_address=sip, traffic_class=v6_traffic_class,
                                   next_header=Ipv4Header.PROTOCOL_TYPE_TCP)

    else:
        ip_header_obj = Ipv4Header(destination_address=dip, source_address=sip, protocol=Ipv4Header.PROTOCOL_TYPE_TCP)
        stream_created = template_obj.configure_stream_block(stream_block_obj=stream_obj,
                                                             port_handle=tx_port)
        ethernet_obj = Ethernet2Header(destination_mac=dmac,
                                       ether_type=Ethernet2Header.INTERNET_IP_ETHERTYPE)
    fun_test.test_assert(stream_created, "Creating stream")

    checkpoint = "Configure Mac address for %s " % stream_obj.spirent_handle
    result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=stream_obj.spirent_handle,
                                                            header_obj=ethernet_obj, update=True)
    fun_test.simple_assert(expression=result, message=checkpoint)

    checkpoint = "Add IP header for %s " % stream_obj.spirent_handle
    result = template_obj.stc_manager.configure_frame_stack(
        stream_block_handle=stream_obj.spirent_handle,
        header_obj=ip_header_obj, update=True)
    fun_test.simple_assert(expression=result, message=checkpoint)

    if ecn_v4 != 0:
        update_ecn = template_obj.configure_diffserv(streamblock_obj=stream_obj, reserved=ecn_v4, update=True)
        fun_test.test_assert(update_ecn, "Update ecn bits in ip header %s" % stream_obj.spirent_handle)

    tcp_header_obj = TCP(source_port=s_port, destination_port=d_port, sync_bit=sync_bit, ack_bit=ack_bit)
    checkpoint = "Add TCP header"
    result = template_obj.stc_manager.configure_frame_stack(stream_block_handle=stream_obj.spirent_handle,
                                                            header_obj=tcp_header_obj, update=False)
    fun_test.simple_assert(result, checkpoint)

    return stream_obj


class SpirentSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Configure Spirent Ports (No of ports needed 2)
        2. Configure Generator Configs and Get Generator Handle for Tx Port
        3. Subscribed to all types of results
        """)

    def setup(self):
        global spirent_config, subscribed_results, dut_config, template_obj, network_controller_obj, nu_ing_port, \
            nu_eg_port, hnu_ing_port, hnu_eg_port, generator_port_obj_dict, analyzer_port_obj_dict

        spirent_config = nu_config_obj.read_traffic_generator_config()

        dut_config = nu_config_obj.read_dut_config(flow_type=NuConfigManager.ACL_FLOW_TYPE,
                                                   flow_direction=NuConfigManager.FLOW_DIRECTION_ALL)

        template_obj = SpirentEthernetTrafficTemplate(session_name="meter", spirent_config=spirent_config,
                                                      chassis_type=nu_config_obj.CHASSIS_TYPE)
        result = template_obj.setup(no_of_ports_needed=NUM_PORTS, flow_type=NuConfigManager.ACL_FLOW_TYPE,
                                    flow_direction=NuConfigManager.FLOW_DIRECTION_ALL)
        fun_test.test_assert(result['result'], "Ensure Setup is done")

        dpc_server_ip = dut_config["dpcsh_tcp_proxy_ip"]
        dpc_server_port = dut_config["dpcsh_tcp_proxy_port"]

        nu_ing_port = result['port_list'][0]
        nu_eg_port = result['port_list'][1]

        generator_config = GeneratorConfig(scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED,
                                           duration=TRAFFIC_DURATION,
                                           duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                           time_stamp_latch_mode=GeneratorConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)

        analyzer_config = AnalyzerConfig(timestamp_latch_mode=AnalyzerConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)
        for port in result['port_list']:
            checkpoint = "Create Generator Config for %s port" % port
            result = template_obj.configure_generator_config(port_handle=port,
                                                             generator_config_obj=generator_config)
            fun_test.simple_assert(expression=result, message=checkpoint)

            checkpoint = "Create Analyzer Config for %s port" % port
            result = template_obj.configure_analyzer_config(port_handle=port,
                                                            analyzer_config_obj=analyzer_config)
            fun_test.simple_assert(result, checkpoint)

            generator_port_obj_dict[port] = template_obj.stc_manager.get_generator(port_handle=port)
            analyzer_port_obj_dict[port] = template_obj.stc_manager.get_analyzer(port_handle=port)
        # Subscribe to all results
        project = template_obj.stc_manager.get_project_handle()
        subscribed_results = template_obj.subscribe_to_all_results(parent=project)
        fun_test.test_assert(subscribed_results['result'], "Subscribing to all results")
        del subscribed_results['result']

        if dut_config['enable_dpcsh']:
            network_controller_obj = NetworkController(dpc_server_ip=dpc_server_ip, dpc_server_port=dpc_server_port)

    def cleanup(self):
        template_obj.cleanup()


class MeterBase(FunTestCase):
    stream_obj = None
    load_type = "MEGABITS_PER_SECOND"
    load = test_config['load_kbps']
    dport = meter_bps['dport']
    meter_id = meter_bps['meter_id']
    meter_interval = meter_bps['meter_interval']
    meter_credit = meter_bps['meter_credit']
    commit_rate = meter_bps['commit_rate']
    mode = METER_MODE_BPS
    rate_mode= TWO_COLOR_METER
    def describe(self):
        self.set_test_details(id=1, summary="Test SrTC meter transit for bps",
                              steps="""
                                  1. Create Stream on Tx port with defined kbps
                                  2. Start Traffic for %d secs
                                  3. Make sure Rx and Tx framecount are equal
                                  4. Make sure Rx and Tx rate are same
                                  5. Make sure packets are seen in expected meter colors
                                  6. Ensure no errors are seen on spirent ports
                                  """ % TRAFFIC_DURATION)

    def setup(self):

        self.routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
        self.l3_config = self.routes_config['l3_config']
        # Multiple streams for seding packets with different fields
        checkpoint = "Creating multiple streams on %s port" % nu_ing_port
        self.stream_obj = create_streams(tx_port=nu_ing_port, load=self.load, load_type=self.load_type,
                                         dmac=self.routes_config['routermac'],
                                         dip=self.l3_config['destination_ip1'],
                                         d_port=self.dport)
        checkpoint = "Clear FPG port stats on DUT"
        c = 0
        for port_num in dut_config['ports']:
            shape = 0
            if c <= 1:
                result = network_controller_obj.clear_port_stats(port_num=port_num, shape=shape)
                fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
            c += 1
        fun_test.add_checkpoint(checkpoint=checkpoint)

    def run(self):
        tx_port = nu_ing_port
        rx_port = nu_eg_port
        result = network_controller_obj.update_meter(index=self.meter_id, interval=self.meter_interval,
                                                     crd=self.meter_credit, commit_rate=self.commit_rate,
                                                     pps_mode=self.mode, rate_mode=rate_mode)

        meter_before =  network_controller_obj.peek_meter_stats_by_id(meter_id=self.meter_id)
        checkpoint = "Start traffic from %s port for %d secs" % (tx_port, TRAFFIC_DURATION)
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)
        checkpoint = "Validate Tx and Rx Rate"
        fun_test.sleep("Waiting for traffic to reach full throughput", seconds=5)
        stream_objs = []
        stream_objs.append(self.stream_obj)
        rate_result = template_obj.validate_traffic_rate_results(
            rx_summary_subscribe_handle=subscribed_results['rx_summary_subscribe'],
            tx_summary_subscribe_handle=subscribed_results['tx_stream_subscribe'],
            stream_objects=stream_objs)
        fun_test.simple_assert(expression=rate_result['result'], message=checkpoint)

        fun_test.sleep("Waiting for traffic to complete", seconds=TRAFFIC_DURATION)

        if dut_config['enable_dpcsh']:
            checkpoint = "Validate FPG FrameCount Tx == Rx for port direction %d --> %d on DUT" % (
                dut_config['ports'][0], dut_config['ports'][1])
            port1_result = network_controller_obj.peek_fpg_port_stats(port_num=dut_config['ports'][0])
            fun_test.log("DUT Port %d Results: %s" % (dut_config['ports'][0], port1_result))
            fun_test.test_assert(port1_result, "Get %d Port FPG Stats" % dut_config['ports'][0])
            port2_result = network_controller_obj.peek_fpg_port_stats(port_num=dut_config['ports'][1])
            fun_test.log("DUT Port %d Results: %s" % (dut_config['ports'][1], port2_result))
            fun_test.test_assert(port2_result, "Get %d Port FPG Stats" % dut_config['ports'][1])

            frames_transmitted = get_dut_output_stats_value(result_stats=port1_result,
                                                            stat_type=FRAMES_TRANSMITTED_OK)
            frames_received = get_dut_output_stats_value(result_stats=port2_result, stat_type=FRAMES_RECEIVED_OK)

            fun_test.test_assert_expected(expected=frames_transmitted, actual=frames_received,
                                          message=checkpoint)
            meter_after = network_controller_obj.peek_meter_stats_by_id(meter_id=self.meter_id)
            fun_test.log(meter_after)


    def cleanup(self):
        dut_rx_port = dut_config['ports'][0]

        checkpoint = "Delete the streams"
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)


class MeterPps2Color(MeterBase):
    load_type = "FRAMES_PER_SECOND"
    load = test_config['load_pps']
    dport = meter_pps['dport']
    meter_id = meter_pps['meter_id']
    meter_interval = meter_pps['meter_interval']
    meter_credit = meter_pps['meter_credit']
    commit_rate = meter_pps['commit_rate']
    mode = METER_MODE_PPS
    rate_mode = TWO_COLOR_METER


class MeterPps3Color(MeterBase):
    load_type = "FRAMES_PER_SECOND"
    load = test_config['load_pps']
    dport = meter_pps['dport']
    meter_id = meter_pps['meter_id']
    meter_interval = meter_pps['meter_interval']
    meter_credit = meter_pps['meter_credit']
    commit_rate = meter_pps['commit_rate']
    mode = METER_MODE_PPS
    rate_mode = THREE_COLOR_METER


if __name__ == '__main__':
    ts = SpirentSetup()
    ts.add_test_case(MeterBase())
    ts.add_test_case(MeterPps2Color())
    ts.add_test_case(MeterPps3Color())
    ts.run()