'''Author : Yajat N Singh'''
from __future__ import division
from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_traffic_generator_template import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import *
from lib.host.network_controller import *
from scripts.networking.nu_config_manager import *
from scripts.networking.helper import *
from lib.utilities.pcap_parser import *
from scripts.networking.snapshot_helper import *


spirent_config = {}
subscribed_results = None
NUM_PORTS = 2
generator_port_obj_dict = {}
analyzer_port_obj_dict = {}
METER_MODE_BPS = 0
METER_MODE_PPS = 1
SrTCM = 0
TrTCM = 1


def is_close(a, b, rel_tol=1e-01, abs_tol=0.0):
    return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


def create_streams(tx_port, dip, dmac, sip="192.168.85.2", s_port=1024, d_port=1024, sync_bit='0', ack_bit='1', ecn_v4=0,
                   ipv6=False, v6_traffic_class=0, load=50, load_type="MEGABITS_PER_SECOND"):
    stream_obj = StreamBlock(fill_type=test_config['fill_type'], insert_signature=test_config['insert_signature'],
                             load=load, load_unit=load_type,
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


def get_meter_dict(nu_config_object):
    result = {"acl_dict": {}, "traffic_dur": 0, "test_config": {}}
    test_config_file = fun_test.get_script_parent_directory() + "/meter_dut_configs.json"
    test_config = nu_config_object.read_test_configs_by_dut_type(config_file=test_config_file)
    dut_type_json = test_config['dut_type']
    meter_json_file = fun_test.get_script_parent_directory() + '/meter.json'
    meter_json_output_all = fun_test.parse_file_to_json(meter_json_file)
    meter_json_out = meter_json_output_all[dut_type_json]
    result['meter_dict'] = meter_json_out
    result['test_config'] = test_config
    result['traffic_dur'] = test_config['traffic_duration']
    return result

class SpirentSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Configure Spirent Ports (No of ports needed 2)
        2. Configure Generator Configs and Get Generator Handle for Tx Port
        3. Subscribed to all types of results
        """)

    def setup(self):
        global spirent_config, subscribed_results, dut_config, template_obj, network_controller_obj, nu_ing_port, \
            nu_eg_port, hnu_ing_port, hnu_eg_port, generator_port_obj_dict, analyzer_port_obj_dict, nu_config_obj,\
            TRAFFIC_DURATION, meter_json_output, test_config, dpc_server_ip, dpc_server_port, generator_config,\
            result_setup
        nu_config_obj = NuConfigManager()
        spirent_config = nu_config_obj.read_traffic_generator_config()

        dut_config = nu_config_obj.read_dut_config(flow_type=NuConfigManager.ACL_FLOW_TYPE,
                                                   flow_direction=NuConfigManager.FLOW_DIRECTION_ALL)

        template_obj = SpirentEthernetTrafficTemplate(session_name="meter", spirent_config=spirent_config,
                                                      chassis_type=nu_config_obj.CHASSIS_TYPE)
        result_setup = template_obj.setup(no_of_ports_needed=NUM_PORTS, flow_type=NuConfigManager.ACL_FLOW_TYPE,
                                    flow_direction=NuConfigManager.FLOW_DIRECTION_ALL)
        fun_test.test_assert(result_setup['result'], "Ensure Setup is done")

        dpc_server_ip = dut_config["dpcsh_tcp_proxy_ip"]
        dpc_server_port = dut_config["dpcsh_tcp_proxy_port"]

        nu_ing_port = result_setup['port_list'][0]
        nu_eg_port = result_setup['port_list'][1]
        meter_dict = get_meter_dict(nu_config_object=nu_config_obj)
        TRAFFIC_DURATION = meter_dict['traffic_dur']
        meter_json_output = meter_dict['meter_dict']
        test_config = meter_dict['test_config']
        generator_config = GeneratorConfig(scheduling_mode=GeneratorConfig.SCHEDULING_MODE_RATE_BASED,
                                           duration=1,
                                           duration_mode=GeneratorConfig.DURATION_MODE_SECONDS,
                                           time_stamp_latch_mode=GeneratorConfig.TIME_STAMP_LATCH_MODE_END_OF_FRAME)

        port = result_setup['port_list'][0]
        checkpoint = "Create Generator Config for %s port" % port
        result = template_obj.configure_generator_config(port_handle=port,
                                                         generator_config_obj=generator_config)
        fun_test.simple_assert(expression=result, message=checkpoint)

        generator_port_obj_dict[port] = template_obj.stc_manager.get_generator(port_handle=port)
        # Subscribe to all results
        project = template_obj.stc_manager.get_project_handle()
        subscribed_results = template_obj.subscribe_to_all_results(parent=project)
        del subscribed_results['result']

        if dut_config['enable_dpcsh']:
            network_controller_obj = NetworkController(dpc_server_ip=dpc_server_ip, dpc_server_port=dpc_server_port)

    def cleanup(self):
        template_obj.cleanup()


class MeterBase(FunTestCase):
    stream_obj = None
    mode = METER_MODE_BPS
    rate_mode = SrTCM
    erp = False
    json_key = "bps_meter"
    def describe(self):
        self.set_test_details(id=1, summary="Test SrTC meter transit for bps",
                              steps="""
                                  1. Create Stream on Tx port with defined kbps
                                  2. Start Traffic 
                                  3. Make sure Rx and Tx framecount are equal
                                  4. Make sure Rx and Tx rate are same
                                  5. Make sure packets are seen in expected meter colors
                                  6. Ensure no errors are seen on spirent ports
                                  """ )

    def setup(self):
        meter_fields = meter_json_output[self.json_key]
        routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
        l3_config = routes_config['l3_config']
        self.stream_obj = create_streams(tx_port=nu_ing_port, dmac=routes_config['routermac'],
                                         dip=l3_config['destination_ip1'], load=meter_fields['load'],
                                         load_type=meter_fields['load_type'], d_port=meter_fields['dport'],
                                         s_port=meter_fields['sport'])

    def run(self):
        meter_fields = meter_json_output[self.json_key]
        tx_port = nu_ing_port
        rx_port = nu_eg_port
        if generator_config.Duration == TRAFFIC_DURATION:
            generator_config.Duration = 1
            port = result_setup['port_list'][0]
            checkpoint = "Update Generator Config for %s port with duration %s" % (port, generator_config.Duration)
            result = template_obj.configure_generator_config(port_handle=port,
                                                             generator_config_obj=generator_config, update=True)
            fun_test.simple_assert(expression=result, message=checkpoint)
            generator_port_obj_dict[port] = template_obj.stc_manager.get_generator(port_handle=port)

        network_controller_obj.disconnect()
        snapshot_obj = SnapshotHelper(dpc_proxy_ip=dpc_server_ip, dpc_proxy_port=dpc_server_port)
        snapshot_obj.setup_snapshot()
        checkpoint = "Start traffic to get meter ID from snapshot"
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)

        fun_test.sleep("Traffic to complete", seconds=2)
        snapshot_output = snapshot_obj.run_snapshot()
        snapshot_obj.exit_snapshot()
        checkpoint = "Clear spirent results"
        result = template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.test_assert(result, checkpoint)
        meter_id = snapshot_obj.get_snapshot_meter_id(snapshot_output=snapshot_output, erp=self.erp)
        fun_test.log("meter ID from snapshot : %s" % meter_id)
        generator_config.Duration = TRAFFIC_DURATION
        port = result_setup['port_list'][0]
        checkpoint = "Update Generator Config for %s port with duration %s" % (port, generator_config.Duration)
        result = template_obj.configure_generator_config(port_handle=port,
                                                         generator_config_obj=generator_config, update=True)
        fun_test.simple_assert(expression=result, message=checkpoint)

        generator_port_obj_dict[port] = template_obj.stc_manager.get_generator(port_handle=port)

        checkpoint = "Clear FPG port stats on DUT"
        c = 0
        for port_num in dut_config['ports']:
            shape = 0
            if c <= 1:
                result = network_controller_obj.clear_port_stats(port_num=port_num, shape=shape)
                fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
            c += 1
        fun_test.add_checkpoint(checkpoint=checkpoint)

        checkpoint = "Configure meter %s" % meter_id

        result = network_controller_obj.update_meter(index=meter_id, interval=meter_fields['meter_interval'],
                                                     crd=meter_fields['meter_credit'],
                                                     commit_rate=meter_fields['commit_rate'],
                                                     pps_mode=self.mode, rate_mode=self.rate_mode,
                                                     commit_burst=meter_fields['commit_burst'],
                                                     excess_burst=meter_fields['excess_burst'])
        fun_test.simple_assert(expression=result, message=checkpoint)

        meter_before = network_controller_obj.peek_meter_stats_by_id(meter_id=meter_id)
        checkpoint = "Start traffic from %s port for %d secs" % (tx_port, TRAFFIC_DURATION)
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)
        checkpoint = "Validate Tx and Rx Rate"
        fun_test.sleep("Waiting for traffic to reach full throughput", seconds=5)
        stream_objs = []
        stream_objs.append(self.stream_obj)
        rate_result = template_obj.get_traffic_rate_comparison(
            rx_summary_subscribe_handle=subscribed_results['rx_summary_subscribe'],
            tx_summary_subscribe_handle=subscribed_results['tx_stream_subscribe'],
            stream_objects=stream_objs, kbps=True, time_for_throughput=int(TRAFFIC_DURATION/3))
        fun_test.simple_assert(expression=rate_result['result'], message=checkpoint)
        pps_in = rate_result['pps_in']
        pps_out = rate_result['pps_out']
        bps_in = rate_result['throughput_count_in']
        bps_out = rate_result['throughput_count_out']
        fun_test.sleep("Waiting for traffic to complete", seconds=TRAFFIC_DURATION)
        stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                            [self.stream_obj.spirent_handle],
                                                                            tx_result=True, rx_result=True)
        tx_stream_result_framecount = int(
            stream_results[self.stream_obj.spirent_handle]["tx_result"]["FrameCount"])
        rx_stream_result_framecount = int(
            stream_results[self.stream_obj.spirent_handle]["rx_result"]["FrameCount"])

        if dut_config['enable_dpcsh']:

            port1_result = network_controller_obj.peek_fpg_port_stats(port_num=dut_config['ports'][0])
            fun_test.log("DUT Port %d Results: %s" % (dut_config['ports'][0], port1_result))
            fun_test.test_assert(port1_result, "Get %d Port FPG Stats" % dut_config['ports'][0])
            port2_result = network_controller_obj.peek_fpg_port_stats(port_num=dut_config['ports'][1])
            fun_test.log("DUT Port %d Results: %s" % (dut_config['ports'][1], port2_result))
            fun_test.test_assert(port2_result, "Get %d Port FPG Stats" % dut_config['ports'][1])

            frames_transmitted = get_dut_output_stats_value(result_stats=port1_result,
                                                            stat_type=FRAMES_RECEIVED_OK, tx=False)
            frames_received = get_dut_output_stats_value(result_stats=port2_result, stat_type=FRAMES_TRANSMITTED_OK)

            fun_test.test_assert_expected(expected=rx_stream_result_framecount, actual=frames_received,
                                          message="Compare DUT stats and Spirent Stream stats ")
            meter_after = network_controller_obj.peek_meter_stats_by_id(meter_id=meter_id)
            fun_test.log(meter_after)
            checkpoint = "Compare green & yellow colored pkts with total forwarded pkts"
            meter_green = (int(meter_after['green']['pkts']) - int(meter_before['green']['pkts']))
            meter_yellow = (int(meter_after['yellow']['pkts']) - int(meter_before['yellow']['pkts']))
            meter_red = (int(meter_after['red']['pkts']) - int(meter_before['red']['pkts']))
            fun_test.test_assert_expected(expected=frames_received, actual=meter_green + meter_yellow,
                                          message=checkpoint)
            fun_test.test_assert_expected(expected=frames_transmitted, actual=meter_green + meter_yellow+meter_red,
                                          message="Comparing frames sent and all colored pkts")
            meter_color_ratio = (meter_red + meter_yellow + meter_green)/(meter_yellow + meter_green)
            fun_test.log("Meter Color Ratio : " + str(meter_color_ratio))
            if self.mode == METER_MODE_BPS:
                bps_ratio = bps_in/bps_out
                fun_test.log("BPS ratio : "+str(bps_ratio))
                fun_test.test_assert_expected(expected=True, actual=is_close(a=bps_ratio, b=meter_color_ratio),
                                              message="Comparing rx rate against pkts color ratio")
            elif self.mode == METER_MODE_PPS:
                pps_ratio = pps_in/pps_out
                fun_test.log("PPS ratio : "+str(pps_ratio))
                fun_test.test_assert_expected(expected=True, actual=is_close(a=pps_ratio, b=meter_color_ratio),
                                              message="Comparing rx rate against pkts color ratio")

    def cleanup(self):
        dut_rx_port = dut_config['ports'][0]

        checkpoint = "Delete the streams"
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)


class MeterPps1Rate(MeterBase):
    stream_obj = None
    mode = METER_MODE_PPS
    rate_mode = SrTCM
    erp = False
    json_key = "pps_meter"

    def describe(self):
        self.set_test_details(id=2, summary="Test SrTC meter transit for pps",
                              steps="""
                                  1. Create Stream on Tx port with defined kbps
                                  2. Start Traffic 
                                  3. Make sure Rx and Tx framecount are equal
                                  4. Make sure Rx and Tx rate are same
                                  5. Make sure packets are seen in expected meter colors
                                  6. Ensure no errors are seen on spirent ports
                                  """)
    def setup(self):
        super(MeterPps1Rate, self).setup()

    def cleanup(self):
        super(MeterPps1Rate, self).cleanup()

    def run(self):
        super(MeterPps1Rate, self).run()


class MeterPps2Rate(MeterBase):
    stream_obj = None
    mode = METER_MODE_PPS
    rate_mode = SrTCM
    erp = False
    json_key = "pps_meter_2_rate"

    def describe(self):
        self.set_test_details(id=3, summary="Test TrTC meter transit for pps",
                              steps="""
                                  1. Create Stream on Tx port with defined kbps
                                  2. Start Traffic 
                                  3. Make sure Rx and Tx framecount are equal
                                  4. Make sure Rx and Tx rate are same
                                  5. Make sure packets are seen in expected meter colors
                                  6. Ensure no errors are seen on spirent ports
                                  """)
    def setup(self):
        super(MeterPps2Rate, self).setup()

    def cleanup(self):
        super(MeterPps2Rate, self).cleanup()

    def run(self):
        super(MeterPps2Rate, self).run()


class MeterBps2Rate(MeterBase):
    load_type = "FRAMES_PER_SECOND"
    mode = METER_MODE_PPS
    rate_mode = TrTCM


if __name__ == '__main__':
    ts = SpirentSetup()
    ts.add_test_case(MeterBase())
    ts.add_test_case(MeterPps1Rate())
    ts.add_test_case(MeterPps2Rate())
    ts.run()
