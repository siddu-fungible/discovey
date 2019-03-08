'''Author : Yajat N Singh'''
from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_traffic_generator_template import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import *
from lib.host.network_controller import *
from scripts.networking.nu_config_manager import *
from scripts.networking.helper import *
from scripts.networking.snapshot_helper import *

spirent_config = {}
subscribed_results = None
NUM_PORTS = 4
generator_port_obj_dict = {}
analyzer_port_obj_dict = {}
prev_traffic_success = 0
ACL_ACTION_COLOR = 0
ACL_ACTION_LOG = 1


def get_acl_dict(nu_config_object):
    result = {"acl_dict": {}, "traffic_dur": 0, "test_config": {}}
    test_config_file = fun_test.get_script_parent_directory() + "/dut_configs.json"
    test_config = nu_config_object.read_test_configs_by_dut_type(config_file=test_config_file)
    dut_type_json = test_config['dut_type']
    acl_json_file = fun_test.get_script_parent_directory() + '/acl.json'
    acl_json_output_all = fun_test.parse_file_to_json(acl_json_file)
    acl_json_out = acl_json_output_all[dut_type_json]
    result['acl_dict'] = acl_json_out
    result['test_config'] = test_config
    result['traffic_dur'] = test_config['traffic_duration']
    return result


def create_streams(tx_port, dip, sip, dmac, s_port=1024, d_port=1024, sync_bit='0', ack_bit='1', ecn_v4=0,
                   ipv6=False, v6_traffic_class=0):
    stream_obj = StreamBlock(fill_type=test_config['fill_type'], insert_signature=test_config['insert_signature'],
                             load = test_config['load'], load_unit=test_config['load_type'],
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


def compare_acl_stream(active_stream, send_port, receive_port, acl_action, send_port_no, receive_port_no,
                       hnu_ing=False, hnu_eg=False, all_streams=[]):

    checkpoint = "Clear FPG port stats on DUT"
    shape = 0
    if send_port_no == 2 or send_port_no == 3:
        shape = 1
    result = network_controller_obj.clear_port_stats(port_num=send_port_no, shape=shape)
    fun_test.simple_assert(result, "Clear FPG stats for port %d" % send_port_no)
    shape = 0
    if receive_port_no == 2 or receive_port_no == 3:
        shape = 1
    result = network_controller_obj.clear_port_stats(port_num=receive_port_no, shape=shape)
    fun_test.simple_assert(result, "Clear FPG stats for port %d" % receive_port_no)

    fun_test.add_checkpoint(checkpoint=checkpoint)

    template_obj.deactivate_stream_blocks(stream_obj_list=all_streams)
    obj_list = []
    obj_list.append(active_stream)
    template_obj.activate_stream_blocks(stream_obj_list=obj_list)
    network_controller_obj.disconnect()
    setup_snapshot(smac=None, psw_stream=None, stream=None, unit=None, dpc_tcp_proxy_ip=dpc_server_ip,
                   dpc_tcp_proxy_port=dpc_server_port)
    checkpoint = "Start traffic from %s port for %d secs stream" % (send_port, TRAFFIC_DURATION)
    result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[send_port]])
    fun_test.simple_assert(expression=result, message=checkpoint)

    fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION + 2)
    checkpoint = "Ensure tx and rx frame count matches on Spirent for NU NU traffic"
    snapshot_output = run_snapshot()
    exit_snapshot()
    ing_port_results = network_controller_obj.peek_fpg_port_stats(send_port_no, hnu=hnu_ing)
    fun_test.simple_assert(ing_port_results, "Fetch DUT Rx port results. FPG%d" % send_port_no)

    eg_port_results = network_controller_obj.peek_fpg_port_stats(receive_port_no, hnu=hnu_eg)
    fun_test.simple_assert(eg_port_results, "Fetch DUT Tx port results. FPG%d" % receive_port_no)

    checkpoint = "Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count"
    frames_received = get_dut_output_stats_value(result_stats=ing_port_results, stat_type=FRAMES_RECEIVED_OK,
                                                 tx=False)
    frames_transmitted = get_dut_output_stats_value(result_stats=eg_port_results,
                                                       stat_type=FRAMES_TRANSMITTED_OK)
    fun_test.log("Frames Received on FPG%s: %s, Frames Transmitted on FPG%s: %s"
                 % (send_port, frames_received, receive_port, frames_transmitted))
    fun_test.test_assert_expected(expected=frames_received, actual=frames_transmitted, message=checkpoint)

    stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                        [active_stream.spirent_handle],
                                                                        tx_result=True, rx_result=True)
    tx_stream_result_framecount = int(
        stream_results[active_stream.spirent_handle]["tx_result"]["FrameCount"])
    rx_stream_result_framecount = int(
        stream_results[active_stream.spirent_handle]["rx_result"]["FrameCount"])
    fun_test.test_assert_expected(expected=tx_stream_result_framecount,
                                  actual=rx_stream_result_framecount,
                                  message=checkpoint)
    if acl_action == ACL_ACTION_COLOR:
        fun_test.log(get_pkt_color_from_snapshot(snapshot_output=snapshot_output))
    elif acl_action == ACL_ACTION_LOG:
        print get_log_from_snapshot(snapshot_output=snapshot_output)


class SpirentSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Configure Spirent Ports (No of ports needed 4)
        2. Configure Generator Configs and Get Generator Handle for Tx Port
        3. Subscribed to all types of results
        """)

    def setup(self):
        global spirent_config, subscribed_results, dut_config, template_obj, network_controller_obj, nu_ing_port, \
            nu_eg_port, hnu_ing_port, hnu_eg_port, generator_port_obj_dict, analyzer_port_obj_dict, nu_config_obj,\
            TRAFFIC_DURATION, acl_json_output, test_config, dpc_server_ip, dpc_server_port

        nu_config_obj = NuConfigManager()
        spirent_config = nu_config_obj.read_traffic_generator_config()

        dut_config = nu_config_obj.read_dut_config(flow_type=NuConfigManager.ACL_FLOW_TYPE,
                                                   flow_direction=NuConfigManager.FLOW_DIRECTION_ALL)

        template_obj = SpirentEthernetTrafficTemplate(session_name="acl", spirent_config=spirent_config,
                                                      chassis_type=nu_config_obj.CHASSIS_TYPE)
        result = template_obj.setup(no_of_ports_needed=NUM_PORTS, flow_type=NuConfigManager.ACL_FLOW_TYPE,
                                    flow_direction=NuConfigManager.FLOW_DIRECTION_ALL)
        fun_test.test_assert(result['result'], "Ensure Setup is done")

        dpc_server_ip = dut_config["dpcsh_tcp_proxy_ip"]
        dpc_server_port = dut_config["dpcsh_tcp_proxy_port"]

        nu_ing_port = result['port_list'][0]
        nu_eg_port = result['port_list'][1]
        hnu_ing_port = result['port_list'][2]
        hnu_eg_port = result['port_list'][3]
        acl_dict = get_acl_dict(nu_config_object=nu_config_obj)
        TRAFFIC_DURATION = acl_dict['traffic_dur']
        acl_json_output = acl_dict['acl_dict']
        test_config = acl_dict['test_config']
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


class AclQosColor(FunTestCase):
    l2_config = None
    l3_config = None
    load = 10
    routes_config = None
    stream_obj_nu_nu = None
    stream_obj_nu_hnu = None
    stream_obj_hnu_hnu = None
    stream_obj_hnu_nu = None
    capture_results = None
    acl_fields_dict_qos = {}
    acl_action = ACL_ACTION_COLOR

    def describe(self):
        self.set_test_details(id=1, summary=" Test QoS ACL for color action for all directions",
                              steps="""
                              1. Create TCP frame streams on Tx Port to match the log ACL
                              2. Start Traffic for stream matching ACL
                              3. Ensure on spirent Tx port frames must be equal to Rx port frames
                              4. Ensure counter value on ACL equals Rx port frames count
                              5. Check Color value according to the ACL rule using Snapshot
                              """)

    def setup(self):
        self.routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
        self.l3_config = self.routes_config['l3_config']
        self.acl_fields_dict_qos = acl_json_output['qos_color']
        checkpoint = "Creating multiple streams on port"
        self.stream_obj_nu_nu = create_streams(tx_port=nu_ing_port,
                                               dmac=self.routes_config['routermac'],
                                               dip=self.l3_config['destination_ip1'],
                                               sip=self.acl_fields_dict_qos['source_ip'],
                                               d_port=self.acl_fields_dict_qos['dest_port_ing_nu'])
        self.stream_obj_nu_hnu = create_streams(tx_port=nu_ing_port,
                                                dmac=self.routes_config['routermac'],
                                                dip=self.l3_config['hnu_destination_ip1'],
                                                sip=self.acl_fields_dict_qos['source_ip'],
                                                s_port=self.acl_fields_dict_qos['source_port_eg_hnu'],
                                                d_port=self.acl_fields_dict_qos['dest_port_eg_hnu'])
        self.stream_obj_hnu_hnu = create_streams(tx_port=nu_ing_port,
                                                 dmac=self.routes_config['routermac'],
                                                 dip=self.l3_config['hnu_destination_ip1'],
                                                 sip=self.acl_fields_dict_qos['source_ip'],
                                                 d_port=self.acl_fields_dict_qos['dest_port_ing_hnu'])
        self.stream_obj_hnu_nu = create_streams(tx_port=hnu_ing_port,
                                                dmac=self.routes_config['routermac'],
                                                dip=self.l3_config['destination_ip1'],
                                                sip=self.acl_fields_dict_qos['source_ip'],
                                                d_port=self.acl_fields_dict_qos['dest_port_eg_nu'])

    def run(self):
        all_streams = []
        all_streams.append(self.stream_obj_nu_nu)
        all_streams.append(self.stream_obj_nu_hnu)
        all_streams.append(self.stream_obj_hnu_hnu)
        all_streams.append(self.stream_obj_hnu_nu)
        compare_acl_stream(active_stream=self.stream_obj_nu_nu, send_port=nu_ing_port, receive_port=nu_eg_port,
                           all_streams=all_streams, acl_action=self.acl_action, send_port_no=dut_config['ports'][0],
                           receive_port_no=dut_config['ports'][1])
        compare_acl_stream(active_stream=self.stream_obj_nu_hnu, send_port=nu_ing_port, receive_port=hnu_eg_port,
                           send_port_no=dut_config['ports'][0], receive_port_no=dut_config['ports'][3], hnu_ing=False,
                           hnu_eg=True, all_streams=all_streams, acl_action=self.acl_action)
        compare_acl_stream(active_stream=self.stream_obj_hnu_hnu, send_port=hnu_ing_port, receive_port=hnu_eg_port,
                           send_port_no=dut_config['ports'][2], receive_port_no=dut_config['ports'][3], hnu_ing=True,
                           hnu_eg=True, all_streams=all_streams, acl_action=self.acl_action)
        compare_acl_stream(active_stream=self.stream_obj_hnu_nu, send_port=hnu_ing_port, receive_port=nu_eg_port,
                           send_port_no=dut_config['ports'][2], receive_port_no=dut_config['ports'][1], hnu_ing=True,
                           hnu_eg=False, all_streams=all_streams, acl_action=self.acl_action)

    def cleanup(self):

        checkpoint = "Delete the streams"
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_nu_nu.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_nu_hnu.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_hnu_hnu.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_hnu_nu.spirent_handle])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)


class AclQosLog(AclQosColor):
    l2_config = None
    l3_config = None
    load = 10
    routes_config = None
    stream_obj_nu_nu = None
    stream_obj_nu_hnu = None
    stream_obj_hnu_hnu = None
    stream_obj_hnu_nu = None
    capture_results = None
    # acl_fields_dict_qos = acl_json_output['qos_log']
    acl_action = ACL_ACTION_LOG

    def describe(self):
        self.set_test_details(id=2, summary="Test QoS ACL for log action for all directions",
                              steps="""
                                  1. Create Stream on Tx port with defined kbps
                                  2. Start Traffic for %d secs
                                  3. Make sure Rx and Tx framecount are equal
                                  4. Make sure Rx and Tx rate are same
                                  5. Make sure packets are seen in expected meter colors
                                  6. Ensure no errors are seen on spirent ports
                                  """ % TRAFFIC_DURATION)

    def setup(self):
        super(AclQosLog, self).setup()

    def cleanup(self):
        super(AclQosLog, self).cleanup()

    def run(self):
        super(AclQosLog, self).run()


if __name__ == '__main__':
    ts = SpirentSetup()
    ts.add_test_case(AclQosColor())
    ts.run()
