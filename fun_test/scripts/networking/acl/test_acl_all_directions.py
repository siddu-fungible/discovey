'''Author : Yajat N Singh'''
from lib.system.fun_test import *
from lib.templates.traffic_generator.spirent_traffic_generator_template import *
from lib.templates.traffic_generator.spirent_ethernet_traffic_template import *
from lib.host.network_controller import *
from scripts.networking.nu_config_manager import *
from scripts.networking.helper import *
from lib.utilities.pcap_parser import *


spirent_config = {}
nu_config_obj = NuConfigManager()
TEST_CONFIG_FILE = fun_test.get_script_parent_directory() + "/dut_configs.json"
test_config = nu_config_obj.read_test_configs_by_dut_type(config_file=TEST_CONFIG_FILE)
subscribed_results = None
TRAFFIC_DURATION = test_config['traffic_duration']
NUM_PORTS = 4
generator_port_obj_dict = {}
analyzer_port_obj_dict = {}
prev_traffic_success = 0
acl_json_file = fun_test.get_script_parent_directory() + '/acl.json'
acl_json_output = fun_test.parse_file_to_json(acl_json_file)
acl_fields_dict_sanity_eg_nu_hnu = acl_json_output['nu_hnu_egress_drop_test']
acl_fields_dict_sanity_nu_nu = acl_json_output["sanity_test_nu_nu"]
acl_fields_dict_ipv6_nu_nu = acl_json_output["nu_nu_v6_test"]
acl_fields_dict_qos_nu_nu = acl_json_output['qos_nu_nu']
acl_fields_dict_sanity_ing_hnu_hnu = acl_json_output['hnu_hnu_drop_test']
acl_fields_dict_sanity_eg_hnu_nu = acl_json_output['hnu_nu_drop_test']
acl_fields_dict_sanity_v6_nu_hnu = acl_json_output['v6_nu_hnu_test']
acl_fields_dict_ipv6_hnu_hnu = acl_json_output['hnu_hnu_v6_drop']
acl_fields_dict_ipv6_hnu_nu = acl_json_output['hnu_nu_v6_drop']


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


class SpirentSetup(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Configure Spirent Ports (No of ports needed 4)
        2. Configure Generator Configs and Get Generator Handle for Tx Port
        3. Subscribed to all types of results
        """)

    def setup(self):
        global spirent_config, subscribed_results, dut_config, template_obj, network_controller_obj, nu_ing_port, \
            nu_eg_port, hnu_ing_port, hnu_eg_port, generator_port_obj_dict, analyzer_port_obj_dict

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


class AclIngressDropNUtoNU(FunTestCase):
    l2_config = None
    l3_config = None
    stream_obj_sport = None
    stream_obj_dport = None
    stream_obj_sip = None
    stream_obj_dip = None
    stream_obj_ecn = None
    stream_obj_drop = None
    stream_obj_tcpflag = None
    capture_results = None

    def describe(self):
        self.set_test_details(id=1, summary="Test ACL Drop FPG to FPG",
                              steps="""
                                  1. Create Multiple streams on Tx port, make sure 1 matches the ACL for drop
                                  2. Start Traffic for %d secs
                                  3. Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count for 
                                  all streams but the drop stream
                                  4. Make sure no packets are transmitted for drop stream
                                  5. Make sure counter value equals sent packets on drop stream
                                  6. Ensure no errors are seen on spirent ports
                                  """ % TRAFFIC_DURATION)

    def setup(self):
        global dut_rx_port, dut_tx_port
        self.routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
        self.l3_config = self.routes_config['l3_config']
        # Multiple streams for seding packets with different fields
        checkpoint = "Creating multiple streams on %s port" % nu_ing_port
        self.stream_obj_sport = create_streams(tx_port=nu_ing_port,
                                               dmac=self.routes_config['routermac'],
                                               dip=self.l3_config['destination_ip1'],
                                               sip=acl_fields_dict_sanity_nu_nu['source_ip'],
                                               d_port=acl_fields_dict_sanity_nu_nu['dest_port'],
                                               sync_bit=acl_fields_dict_sanity_nu_nu['tcp_sync_bit'],
                                               ack_bit=acl_fields_dict_sanity_nu_nu['tcp_ack_bit'])

        self.stream_obj_dport = create_streams(tx_port=nu_ing_port,
                                               dmac=self.routes_config['routermac'],
                                               dip=self.l3_config['destination_ip1'],
                                               sip=acl_fields_dict_sanity_nu_nu['source_ip'],
                                               s_port=acl_fields_dict_sanity_nu_nu['source_port'],
                                               sync_bit=acl_fields_dict_sanity_nu_nu['tcp_sync_bit'],
                                               ack_bit=acl_fields_dict_sanity_nu_nu['tcp_ack_bit'])

        self.stream_obj_sip = create_streams(tx_port=nu_ing_port,
                                              dmac=self.routes_config['routermac'],
                                              dip=self.l3_config['destination_ip1'], sip="192.168.2.10",
                                              s_port=acl_fields_dict_sanity_nu_nu['source_port'],
                                              d_port=acl_fields_dict_sanity_nu_nu['dest_port'],
                                              sync_bit=acl_fields_dict_sanity_nu_nu['tcp_sync_bit'],
                                              ack_bit=acl_fields_dict_sanity_nu_nu['tcp_ack_bit'])

        self.stream_obj_dip = create_streams(tx_port=nu_ing_port,
                                             dmac=self.routes_config['routermac'],
                                             dip=acl_fields_dict_sanity_nu_nu['wrong_dip'],
                                             sip=acl_fields_dict_sanity_nu_nu['source_ip'],
                                             s_port=acl_fields_dict_sanity_nu_nu['source_port'],
                                             d_port=acl_fields_dict_sanity_nu_nu['dest_port'],
                                             sync_bit=acl_fields_dict_sanity_nu_nu['tcp_sync_bit'],
                                             ack_bit=acl_fields_dict_sanity_nu_nu['tcp_ack_bit'])

        self.stream_obj_ecn = create_streams(tx_port=nu_ing_port,
                                             dmac=self.routes_config['routermac'],
                                             dip=self.l3_config['destination_ip1'],
                                             sip=acl_fields_dict_sanity_nu_nu['source_ip'],
                                             s_port=acl_fields_dict_sanity_nu_nu['source_port'],
                                             d_port=acl_fields_dict_sanity_nu_nu['dest_port'],
                                             sync_bit=acl_fields_dict_sanity_nu_nu['tcp_sync_bit'],
                                             ack_bit=acl_fields_dict_sanity_nu_nu['tcp_ack_bit'])

        self.stream_obj_tcpflag = create_streams(tx_port=nu_ing_port,
                                                 dmac=self.routes_config['routermac'],
                                                 dip=self.l3_config['destination_ip1'],
                                                 sip=acl_fields_dict_sanity_nu_nu['source_ip'],
                                                 s_port=acl_fields_dict_sanity_nu_nu['source_port'],
                                                 d_port=acl_fields_dict_sanity_nu_nu['dest_port'],
                                                 ecn_v4=acl_fields_dict_sanity_nu_nu['ecn_bits'])

        self.stream_obj_drop = create_streams(tx_port=nu_ing_port,
                                              dmac=self.routes_config['routermac'],
                                              dip=self.l3_config['destination_ip1'],
                                              sip=acl_fields_dict_sanity_nu_nu['source_ip'],
                                              s_port=acl_fields_dict_sanity_nu_nu['source_port'],
                                              d_port=acl_fields_dict_sanity_nu_nu['dest_port'],
                                              sync_bit=acl_fields_dict_sanity_nu_nu['tcp_sync_bit'],
                                              ack_bit=acl_fields_dict_sanity_nu_nu['tcp_ack_bit'],
                                              ecn_v4=acl_fields_dict_sanity_nu_nu['ecn_bits'])

        dut_rx_port = dut_config['ports'][0]
        dut_tx_port = dut_config['ports'][1]

    def run(self):
        '''
        Made the variables global
        dut_rx_port = dut_config['ports'][0]
        dut_tx_port = dut_config['ports'][1]
        '''
        tx_port=nu_ing_port
        rx_port=nu_eg_port
        checkpoint = "Clear FPG port stats on DUT"
        c = 0
        for port_num in dut_config['ports']:
            shape = 0
            if c <= 1:
                result = network_controller_obj.clear_port_stats(port_num=port_num, shape=shape)
                fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
            c += 1
        fun_test.add_checkpoint(checkpoint=checkpoint)

        checkpoint = "Deactivate not required stream blocks"
        obj_list = []
        obj_list.append(self.stream_obj_dip)
        obj_list.append(self.stream_obj_dport)
        obj_list.append(self.stream_obj_sip)
        obj_list.append(self.stream_obj_ecn)
        obj_list.append(self.stream_obj_tcpflag)
        obj_list.append(self.stream_obj_drop)
        template_obj.deactivate_stream_blocks(stream_obj_list=obj_list)

        checkpoint = "Start traffic from %s port for %d secs" % (tx_port, TRAFFIC_DURATION)
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION+1)
        # Getting Spirent results - only when analyzer/generator is subscribed

        checkpoint = "Fetch Rx Port Results for %s" % rx_port
        rx_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=rx_port_result, message=checkpoint)

        dut_rx_port_results = network_controller_obj.peek_fpg_port_stats(dut_rx_port)
        fun_test.simple_assert(dut_rx_port_results, "Fetch DUT Rx port results. FPG%d" % dut_rx_port)

        dut_tx_port_results = network_controller_obj.peek_fpg_port_stats(dut_tx_port)
        fun_test.simple_assert(dut_tx_port_results, "Fetch DUT Tx port results. FPG%d" % dut_tx_port)

        fun_test.log("DUT Rx Port %d Results: %s" % (dut_rx_port, dut_rx_port_results))
        fun_test.log("DUT Tx Port %d Results: %s" % (dut_tx_port, dut_tx_port_results))
        checkpoint = "Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count"
        frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_results, stat_type=FRAMES_RECEIVED_OK,
                                                     tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%s: %s and Frames Transmitted on FPG%s: %s" % (
            dut_rx_port, frames_received, dut_tx_port, frames_transmitted))

        fun_test.test_assert_expected(expected=frames_received, actual=frames_transmitted, message=checkpoint)

        stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                            [self.stream_obj_sport.spirent_handle],
                                                                            tx_result=True, rx_result=True)
        tx_stream_result_framecount = int(
            stream_results[self.stream_obj_sport.spirent_handle]["tx_result"]["FrameCount"])
        rx_stream_result_framecount = int(
            stream_results[self.stream_obj_sport.spirent_handle]["rx_result"]["FrameCount"])
        fun_test.test_assert_expected(expected=tx_stream_result_framecount,
                                      actual=rx_stream_result_framecount,
                                      message="Comparing tx and rx frame count on Spirent for stream sip")

        checkpoint = "Ensure no errors are seen on Rx spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        if frames_received == frames_transmitted:
            del obj_list[:]
            obj_list.append(self.stream_obj_sport)
            obj_list.append(self.stream_obj_drop)
            template_obj.deactivate_stream_blocks(stream_obj_list=obj_list)

            del obj_list[:]
            obj_list.append(self.stream_obj_dport)
            obj_list.append(self.stream_obj_sip)
            obj_list.append(self.stream_obj_dip)
            obj_list.append(self.stream_obj_ecn)
            obj_list.append(self.stream_obj_tcpflag)
            template_obj.activate_stream_blocks(stream_obj_list=obj_list)

            checkpoint = "Start traffic from %s port for %d secs streams dport,sip,dip,ecn,tcpflag"\
                         % (tx_port, TRAFFIC_DURATION)
            result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
            fun_test.simple_assert(expression=result, message=checkpoint)

            fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION + 1)
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_dport.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_dport = int(
                stream_results[self.stream_obj_dport.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_dport = int(
                stream_results[self.stream_obj_dport.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_dport,
                                          actual=rx_stream_result_framecount_dport,
                                          message="Comparing tx and rx frame count on Spirent for stream dport")
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_sip.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_sip = int(
                stream_results[self.stream_obj_sip.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_sip = int(
                stream_results[self.stream_obj_sip.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_sip,
                                          actual=rx_stream_result_framecount_sip,
                                          message="Comparing tx and rx frame count on Spirent for stream sip")
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_dip.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_dip = int(
                stream_results[self.stream_obj_dip.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_dip = int(
                stream_results[self.stream_obj_dip.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_dip,
                                          actual=rx_stream_result_framecount_dip,
                                          message="Comparing tx and rx frame count on Spirent for stream dip")
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_ecn.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_ecn = int(
                stream_results[self.stream_obj_ecn.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_ecn = int(
                stream_results[self.stream_obj_ecn.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_ecn,
                                          actual=rx_stream_result_framecount_ecn,
                                          message="Comparing tx and rx frame count on Spirent for stream ecn")

            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_tcpflag.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_tcpflag = int(
                stream_results[self.stream_obj_tcpflag.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_tcpflag = int(
                stream_results[self.stream_obj_tcpflag.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_tcpflag,
                                          actual=rx_stream_result_framecount_tcpflag,
                                          message="Comparing tx and rx frame count on Spirent for stream tcpflag")

            acl_stats_tx_before = network_controller_obj.peek_fpg_port_stats(dut_tx_port)
            acl_stats_rx_before = network_controller_obj.peek_fpg_port_stats(dut_rx_port)
            fun_test.log("Port DPC results : ")
            fun_test.log(acl_stats_tx_before)
            fun_test.log(acl_stats_rx_before)
            # Send drop traffic which matches all the fields below
            obj_list.append(self.stream_obj_sport)
            template_obj.deactivate_stream_blocks(stream_obj_list=obj_list)

            del obj_list[:]
            obj_list.append(self.stream_obj_drop)
            template_obj.activate_stream_blocks(stream_obj_list=obj_list)

            counter_bef = get_flex_counter_values(network_controller_obj=network_controller_obj,
                                             counter_id=acl_fields_dict_sanity_nu_nu['counter_id'])

            checkpoint = "Start traffic from %s port for %d secs stream sip" % (tx_port, TRAFFIC_DURATION)
            result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
            fun_test.simple_assert(expression=result, message=checkpoint)

            fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION + 2)
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_drop.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_drop = int(
                stream_results[self.stream_obj_drop.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_drop = int(
                stream_results[self.stream_obj_drop.spirent_handle]["rx_result"]["FrameCount"])

            counter_after = get_flex_counter_values(network_controller_obj=network_controller_obj,
                                               counter_id=acl_fields_dict_sanity_nu_nu['counter_id'])

            fun_test.log("tx_streamcount"+str(tx_stream_result_framecount_drop))
            fun_test.test_assert_expected(expected=0, actual=rx_stream_result_framecount_drop,
                                          message="Comparing tx and rx frame count on Spirent for stream drop. No pkt shuold be transmitted")
            # add counter values with the stream value using : peek_fwd_flex_stats
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_drop,
                                          actual=(counter_after - counter_bef),
                                          message="Packets dropped should be equal to counter value")
            rx_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
                port_handle=rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
            checkpoint = "Ensure no errors are seen on Rx spirent port"
            result = template_obj.check_non_zero_error_count(rx_results=rx_port_result)
            fun_test.test_assert(result['result'], checkpoint)

    def cleanup(self):
        dut_rx_port = dut_config['ports'][0]

        checkpoint = "Delete the streams"
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_sport.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_dport.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_sip.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_dip.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_ecn.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_drop.spirent_handle])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)


class AclIPv6NUtoNU(FunTestCase):
    l2_config = None
    l3_config = None
    load = 10
    routes_config = None
    stream_obj_sport = None
    stream_obj_dport = None
    stream_obj_sip = None
    stream_obj_dip = None
    stream_obj_drop = None
    stream_obj_tcpflag = None
    stream_obj_ecn = None
    capture_results = None

    def describe(self):
        self.set_test_details(id=2, summary="Test IPv6 ACL FPG to FPG",
                              steps="""
                                 1. Create TCP frame stream on Tx Port
                                 2. Start Traffic for %d secs
                                 3. Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count 
                                 4. Ensure on spirent Tx port frames must be equal to Rx port frames
                                 5. Ensure no errors are seen on spirent ports
                                 """ % TRAFFIC_DURATION)

    def setup(self):
        global dut_rx_port, dut_tx_port
        self.routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config,
                                                                              ip_version="ipv6")
        self.l3_config = self.routes_config['l3_config']
        # Multiple streams for seding packets with different fields
        checkpoint = "Creating multiple streams on %s port" % nu_ing_port,

        self.stream_obj_sport = create_streams(tx_port=nu_ing_port,  ipv6=True,
                                               dip=self.l3_config['destination_ip1'],
                                               sip=acl_fields_dict_ipv6_nu_nu['source_ip'],
                                               dmac=self.routes_config['routermac'],
                                               s_port=1024, d_port=acl_fields_dict_ipv6_nu_nu['dest_port'])

        self.stream_obj_dport = create_streams(tx_port=nu_ing_port,  ipv6=True,
                                               dip=self.l3_config['destination_ip1'],
                                               sip=acl_fields_dict_ipv6_nu_nu['source_ip'],
                                               dmac=self.routes_config['routermac'],
                                               s_port=acl_fields_dict_ipv6_nu_nu['source_port'], d_port=1024)

        self.stream_obj_sip = create_streams(tx_port=nu_ing_port,  ipv6=True,
                                             dip=self.l3_config['destination_ip1'],
                                             sip="3001::1", dmac=self.routes_config['routermac'],
                                             s_port=acl_fields_dict_ipv6_nu_nu['source_port'],
                                             d_port=acl_fields_dict_ipv6_nu_nu['dest_port'])

        self.stream_obj_dip = create_streams(tx_port=nu_ing_port,  ipv6=True,
                                             dip=acl_fields_dict_ipv6_nu_nu['wrong_dip'],
                                             sip=acl_fields_dict_ipv6_nu_nu['source_ip'],
                                             dmac=self.routes_config['routermac'],
                                             s_port=acl_fields_dict_ipv6_nu_nu['source_port'],
                                             d_port=acl_fields_dict_ipv6_nu_nu['dest_port'])

        self.stream_obj_tcpflag = create_streams(tx_port=nu_ing_port,
                                                 ipv6=True, dip=self.l3_config['destination_ip1'],
                                                 sip=acl_fields_dict_ipv6_nu_nu['source_ip'],
                                                 dmac=self.routes_config['routermac'],
                                                 s_port=acl_fields_dict_ipv6_nu_nu['source_port'],
                                                 d_port=acl_fields_dict_ipv6_nu_nu['dest_port'],
                                                 sync_bit=acl_fields_dict_ipv6_nu_nu['tcp_sync_bit'])

        self.stream_obj_ecn = create_streams(tx_port=nu_ing_port,  ipv6=True,
                                                 dip=self.l3_config['destination_ip1'],
                                                 sip=acl_fields_dict_ipv6_nu_nu['source_ip'],
                                                 dmac=self.routes_config['routermac'],
                                                 s_port=acl_fields_dict_ipv6_nu_nu['source_port'],
                                                 d_port=acl_fields_dict_ipv6_nu_nu['dest_port'],
                                                 sync_bit=acl_fields_dict_ipv6_nu_nu['tcp_sync_bit'],
                                                 ack_bit=acl_fields_dict_ipv6_nu_nu['tcp_ack_bit'])

        self.stream_obj_drop = create_streams(tx_port=nu_ing_port,  ipv6=True,
                                              dip=self.l3_config['destination_ip1'],
                                              sip=acl_fields_dict_ipv6_nu_nu['source_ip'],
                                              dmac=self.routes_config['routermac'],
                                              s_port=acl_fields_dict_ipv6_nu_nu['source_port'],
                                              d_port=acl_fields_dict_ipv6_nu_nu['dest_port'],
                                              sync_bit=acl_fields_dict_ipv6_nu_nu['tcp_sync_bit'],
                                              ack_bit=acl_fields_dict_ipv6_nu_nu['tcp_ack_bit'],
                                              v6_traffic_class=2)

        dut_rx_port = dut_config['ports'][0]
        dut_tx_port = dut_config['ports'][1]

    def run(self):
        checkpoint = "Clear FPG port stats on DUT"
        c = 0
        for port_num in dut_config['ports']:
            shape = 0
            result = network_controller_obj.clear_port_stats(port_num=port_num, shape=shape)
            fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
            c += 1
            if c>2:
                break
        fun_test.add_checkpoint(checkpoint=checkpoint)
        tx_port = nu_ing_port
        rx_port = nu_eg_port
        checkpoint = "Deactivate not required stream blocks"
        obj_list = []
        obj_list.append(self.stream_obj_dip)
        obj_list.append(self.stream_obj_dport)
        obj_list.append(self.stream_obj_sip)
        obj_list.append(self.stream_obj_tcpflag)
        obj_list.append(self.stream_obj_drop)
        obj_list.append(self.stream_obj_ecn)
        template_obj.deactivate_stream_blocks(stream_obj_list=obj_list)
        del obj_list[:]
        obj_list.append(self.stream_obj_sport)
        template_obj.activate_stream_blocks(stream_obj_list=obj_list)

        checkpoint = "Start traffic from %s port for %d secs" % (tx_port, TRAFFIC_DURATION)
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION + 1)

        checkpoint = "Fetch Rx Port Results for %s" % rx_port
        rx_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=rx_port_result, message=checkpoint)

        dut_rx_port_results = network_controller_obj.peek_fpg_port_stats(dut_rx_port)
        fun_test.simple_assert(dut_rx_port_results, "Fetch DUT Rx port results. FPG%d" % dut_rx_port)

        dut_tx_port_results = network_controller_obj.peek_fpg_port_stats(dut_tx_port)
        fun_test.simple_assert(dut_tx_port_results, "Fetch DUT Tx port results. FPG%d" % dut_tx_port)

        fun_test.log("DUT Rx Port %d Results: %s" % (dut_rx_port, dut_rx_port_results))
        fun_test.log("DUT Tx Port %d Results: %s" % (dut_tx_port, dut_tx_port_results))

        checkpoint = "Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count"
        frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_results, stat_type=FRAMES_RECEIVED_OK,
                                                     tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%s: %s and Frames Transmitted on FPG%s: %s" % (
            dut_rx_port, frames_received, dut_tx_port, frames_transmitted))

        fun_test.test_assert_expected(expected=frames_received, actual=frames_transmitted, message=checkpoint)

        # Validate Spirent stats
        stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                            [self.stream_obj_sport.spirent_handle],
                                                                            tx_result=True, rx_result=True)
        tx_stream_result_framecount_sport = int(
            stream_results[self.stream_obj_sport.spirent_handle]["tx_result"]["FrameCount"])
        rx_stream_result_framecount_sport = int(
            stream_results[self.stream_obj_sport.spirent_handle]["rx_result"]["FrameCount"])
        fun_test.test_assert_expected(expected=tx_stream_result_framecount_sport,
                                      actual=rx_stream_result_framecount_sport,
                                      message="Comparing tx and rx frame count on Spirent for stream sip")

        checkpoint = "Ensure no errors are seen on Rx spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        if frames_received == frames_transmitted:
            del obj_list[:]
            obj_list.append(self.stream_obj_sport)
            obj_list.append(self.stream_obj_drop)
            template_obj.deactivate_stream_blocks(stream_obj_list=obj_list)

            del obj_list[:]
            obj_list.append(self.stream_obj_dport)
            obj_list.append(self.stream_obj_sip)
            obj_list.append(self.stream_obj_dip)
            obj_list.append(self.stream_obj_tcpflag)
            obj_list.append(self.stream_obj_ecn)
            template_obj.activate_stream_blocks(stream_obj_list=obj_list)

            checkpoint = "Start traffic from %s port for %d secs streams dport,sip,dip,ecn,tcpflag" % (
            tx_port, TRAFFIC_DURATION)
            result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
            fun_test.simple_assert(expression=result, message=checkpoint)

            fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION + 1)
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_dport.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_dport = int(
                stream_results[self.stream_obj_dport.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_dport = int(
                stream_results[self.stream_obj_dport.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_dport,
                                          actual=rx_stream_result_framecount_dport,
                                          message="Comparing tx and rx frame count on Spirent for stream dport")
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_sip.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_sip = int(
                stream_results[self.stream_obj_sip.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_sip = int(
                stream_results[self.stream_obj_sip.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_sip,
                                          actual=rx_stream_result_framecount_sip,
                                          message="Comparing tx and rx frame count on Spirent for stream sip")
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_dip.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_dip = int(
                stream_results[self.stream_obj_dip.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_dip = int(
                stream_results[self.stream_obj_dip.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_dip,
                                          actual=rx_stream_result_framecount_dip,
                                          message="Comparing tx and rx frame count on Spirent for stream dip")

            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_tcpflag.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_tcpflag = int(
                stream_results[self.stream_obj_tcpflag.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_tcpflag = int(
                stream_results[self.stream_obj_tcpflag.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_tcpflag,
                                          actual=rx_stream_result_framecount_tcpflag,
                                          message="Comparing tx and rx frame count on Spirent for stream tcpflag")

            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_ecn.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_ecn = int(
                stream_results[self.stream_obj_ecn.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_ecn = int(
                stream_results[self.stream_obj_ecn.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_ecn,
                                          actual=rx_stream_result_framecount_ecn,
                                          message="Comparing tx and rx frame count on Spirent for stream tcpflag")

            acl_stats_tx_before = network_controller_obj.peek_fpg_port_stats(dut_tx_port)
            acl_stats_rx_before = network_controller_obj.peek_fpg_port_stats(dut_rx_port)
            fun_test.log("Port DPC results : ")
            fun_test.log(acl_stats_tx_before)
            fun_test.log(acl_stats_rx_before)
            # Send drop traffic which matches all the fields below
            obj_list.append(self.stream_obj_sport)
            template_obj.deactivate_stream_blocks(stream_obj_list=obj_list)

            del obj_list[:]
            obj_list.append(self.stream_obj_drop)
            template_obj.activate_stream_blocks(stream_obj_list=obj_list)

            counter_bef = get_flex_counter_values(network_controller_obj=network_controller_obj,
                                             counter_id=acl_fields_dict_ipv6_nu_nu['counter_id'])

            checkpoint = "Start traffic from %s port for %d secs stream sip" % (tx_port, TRAFFIC_DURATION)
            result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
            fun_test.simple_assert(expression=result, message=checkpoint)

            fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION + 1)
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_drop.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_drop = int(
                stream_results[self.stream_obj_drop.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_drop = int(
                stream_results[self.stream_obj_drop.spirent_handle]["rx_result"]["FrameCount"])

            counter_after = get_flex_counter_values(network_controller_obj=network_controller_obj,
                                               counter_id=acl_fields_dict_ipv6_nu_nu['counter_id'])

            fun_test.log("tx_streamcount" + str(tx_stream_result_framecount_drop))
            checkpoint="Comparing tx and rx frame count on Spirent for stream drop. No pkt shuold be transmitted"
            fun_test.test_assert_expected(expected=0, actual=rx_stream_result_framecount_drop,
                                          message=checkpoint)
            # add counter values with the stream value using : peek_fwd_flex_stats
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_drop,
                                          actual=(counter_after - counter_bef),
                                          message="Packets dropped should be equal to counter value")
            rx_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
                port_handle=rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
            checkpoint = "Ensure no errors are seen on Rx spirent port"
            result = template_obj.check_non_zero_error_count(rx_results=rx_port_result)
            fun_test.test_assert(result['result'], checkpoint)

    def cleanup(self):
        dut_rx_port = dut_config['ports'][0]

        checkpoint = "Delete the streams"
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_sport.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_dport.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_sip.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_dip.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_drop.spirent_handle])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)


class AclQosTCNuNu(FunTestCase):
    l2_config = None
    l3_config = None
    load = 10
    routes_config = None
    stream_obj = None
    capture_results = None

    def describe(self):
        self.set_test_details(id=3, summary=" Test QoS ACL for set_tc action",
                              steps="""
                              1. Create TCP frame streams on Tx Port to match the log ACL
                              2. Start Traffic for stream matching ACL
                              3. Ensure on spirent Tx port frames must be equal to Rx port frames
                              4. Ensure counter value on ACL equals Rx port frames count
                              5. Check QoS queue according to the ACL rule
                              """)

    def setup(self):
        self.routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
        self.l3_config = self.routes_config['l3_config']

        checkpoint = "Creating multiple streams on %s port" % nu_ing_port
        self.stream_obj = create_streams(tx_port=nu_ing_port,
                                               dmac=self.routes_config['routermac'],
                                               dip=self.l3_config['destination_ip1'],
                                               sip=acl_fields_dict_sanity_nu_nu['source_ip'],
                                               d_port=acl_fields_dict_qos_nu_nu['dest_port'],
                                               ecn_v4=acl_fields_dict_qos_nu_nu['ecn_bits'])


    def run(self):
        checkpoint = "Clear FPG port stats on DUT"
        c = 0
        for port_num in dut_config['ports']:
            shape = 0
            result = network_controller_obj.clear_port_stats(port_num=port_num, shape=shape)
            fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
            c += 1
            if c > 1:
                break
        fun_test.add_checkpoint(checkpoint=checkpoint)
        tx_port = nu_ing_port
        dut_rx_port = dut_config['ports'][0]
        # set ingress priority to pg map list
        k_list = [x for x in range(0, 16)]
        k_list.reverse()
        set_ingress_priority_map = network_controller_obj.set_qos_priority_to_pg_map(port_num=dut_rx_port,
                                                                                     map_list=k_list)
        fun_test.test_assert(set_ingress_priority_map, message="Set priority to pg map")

        # set egress priority to pg map list
        '''
        set_egress_priority_map = network_controller_obj.set_qos_queue_to_priority_map(port_num=dut_port_2,
                                                                                       map_list=k_list)
        fun_test.test_assert(set_egress_priority_map, "Set queue to priority map")
        '''
        pg_queue_counters_dict = get_psw_port_enqueue_dequeue_counters(network_controller_obj=network_controller_obj,
                                                  dut_port=dut_rx_port, pg=True, hnu=False)
        qos_count_bef = get_qos_stats(network_controller_obj=network_controller_obj,
                                      queue_no=acl_fields_dict_qos_nu_nu['queue_id'],
                                      dut_port=dut_rx_port, queue_type='pg_deq')

        ecn_qos_count_bef = get_qos_stats(network_controller_obj=network_controller_obj,
                                            queue_no=acl_fields_dict_qos_nu_nu['ecn_tc'],
                                            dut_port=dut_rx_port, queue_type='pg_deq')
        counter_bef = get_flex_counter_values(network_controller_obj=network_controller_obj,
                                         counter_id=acl_fields_dict_qos_nu_nu['counter_id'])

        checkpoint = "Start traffic from %s port for %d secs stream" % (tx_port, TRAFFIC_DURATION)
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION + 2)

        stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                            [self.stream_obj.spirent_handle],
                                                                            tx_result=True, rx_result=True)
        tx_stream_result_framecount = int(
            stream_results[self.stream_obj.spirent_handle]["tx_result"]["FrameCount"])
        rx_stream_result_framecount = int(
            stream_results[self.stream_obj.spirent_handle]["rx_result"]["FrameCount"])
        fun_test.test_assert_expected(expected=tx_stream_result_framecount,
                                      actual=rx_stream_result_framecount,
                                      message="Ensure tx and rx framecount matches")

        checkpoint = "Make sure packets transmitted equals ACL counter value"

        counter_after = get_flex_counter_values(network_controller_obj=network_controller_obj,
                                           counter_id=acl_fields_dict_qos_nu_nu['counter_id'])
        fun_test.test_assert_expected(expected=rx_stream_result_framecount, actual=counter_after - counter_bef,
                                      message=checkpoint)

        qos_count_after = get_qos_stats(network_controller_obj=network_controller_obj,
                                        queue_no=acl_fields_dict_qos_nu_nu['queue_id'],
                                        dut_port=dut_rx_port, queue_type='pg_deq')
        fun_test.test_assert_expected(expected=tx_stream_result_framecount,actual=(qos_count_after-qos_count_bef),
                                      message="Ensure Queue %s has the frames after matching the ACL" % acl_fields_dict_qos_nu_nu['queue_id'])
        ecn_qos_count_after = get_qos_stats(network_controller_obj=network_controller_obj,
                                      queue_no=acl_fields_dict_qos_nu_nu['ecn_tc'],
                                      dut_port=dut_rx_port, queue_type='pg_deq')
        fun_test.test_assert_expected(expected=0,actual=ecn_qos_count_after-ecn_qos_count_bef,
                                      message="Ensure Queue %s has no packets" % acl_fields_dict_qos_nu_nu['ecn_tc'])

    def cleanup(self):

        checkpoint = "Delete the stream"
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj.spirent_handle])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)


class AclEgressDropNUtoHNU(FunTestCase):
    l2_config = None
    l3_config = None
    load = 10
    routes_config = None
    stream_obj_sport = None
    stream_obj_dport = None
    stream_obj_sip = None
    stream_obj_dip = None
    stream_obj_ecn = None
    stream_obj_drop = None
    stream_obj_tcpflag = None
    capture_results = None

    def describe(self):
        self.set_test_details(id=4, summary="Test Traffic FPG to HNU",
                              steps="""
                              1. Create TCP frame stream on Tx Port
                              2. Start Traffic for %d secs
                              3. Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count 
                              4. Ensure on spirent Tx port frames must be equal to Rx port frames
                              5. Ensure no errors are seen on spirent ports
                              """ % TRAFFIC_DURATION)

    def setup(self):
        global dut_rx_port,dut_tx_port
        self.routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
        self.l3_config = self.routes_config['l3_config']
        #Multiple streams for seding packets with different fields
        checkpoint = "Creating multiple streams on %s port" % nu_ing_port

        self.stream_obj_sport = create_streams(tx_port=nu_ing_port,
                                                    dmac=self.routes_config['routermac'],
                                                    dip=self.l3_config['hnu_destination_ip2'],
                                                    sip=acl_fields_dict_sanity_eg_nu_hnu['source_ip'],
                                                    d_port=acl_fields_dict_sanity_eg_nu_hnu['dest_port'],
                                                    sync_bit=acl_fields_dict_sanity_eg_nu_hnu['tcp_sync_bit'],
                                                    ack_bit=acl_fields_dict_sanity_eg_nu_hnu['tcp_ack_bit'])

        self.stream_obj_dport = create_streams(tx_port=nu_ing_port,
                                               dmac=self.routes_config['routermac'],
                                               dip=self.l3_config['hnu_destination_ip2'],
                                               sip=acl_fields_dict_sanity_eg_nu_hnu['source_ip'],
                                               s_port=acl_fields_dict_sanity_eg_nu_hnu['source_port'],
                                               sync_bit=acl_fields_dict_sanity_eg_nu_hnu['tcp_sync_bit'],
                                               ack_bit=acl_fields_dict_sanity_eg_nu_hnu['tcp_ack_bit'])

        self.stream_obj_sip = create_streams(tx_port=nu_ing_port,
                                             dmac=self.routes_config['routermac'],
                                             dip=self.l3_config['hnu_destination_ip2'], sip="192.168.2.10",
                                             s_port=acl_fields_dict_sanity_eg_nu_hnu['source_port'],
                                             d_port=acl_fields_dict_sanity_eg_nu_hnu['dest_port'],
                                             sync_bit=acl_fields_dict_sanity_eg_nu_hnu['tcp_sync_bit'],
                                             ack_bit=acl_fields_dict_sanity_eg_nu_hnu['tcp_ack_bit'])

        self.stream_obj_dip = create_streams(tx_port=nu_ing_port,
                                             dmac=self.routes_config['routermac'],
                                             dip=acl_fields_dict_sanity_eg_nu_hnu['wrong_dip'],
                                             sip=acl_fields_dict_sanity_eg_nu_hnu['source_ip'],
                                             s_port=acl_fields_dict_sanity_eg_nu_hnu['source_port'],
                                             d_port=acl_fields_dict_sanity_eg_nu_hnu['dest_port'],
                                             sync_bit=acl_fields_dict_sanity_eg_nu_hnu['tcp_sync_bit'],
                                             ack_bit=acl_fields_dict_sanity_eg_nu_hnu['tcp_ack_bit'])

        self.stream_obj_ecn = create_streams(tx_port=nu_ing_port,
                                             dmac=self.routes_config['routermac'],
                                             dip=self.l3_config['hnu_destination_ip2'],
                                             sip=acl_fields_dict_sanity_eg_nu_hnu['source_ip'],
                                             s_port=acl_fields_dict_sanity_eg_nu_hnu['source_port'],
                                             d_port=acl_fields_dict_sanity_eg_nu_hnu['dest_port'],
                                             sync_bit=acl_fields_dict_sanity_eg_nu_hnu['tcp_sync_bit'],
                                             ack_bit=acl_fields_dict_sanity_eg_nu_hnu['tcp_ack_bit'])

        self.stream_obj_tcpflag = create_streams(tx_port=nu_ing_port,
                                                 dmac=self.routes_config['routermac'],
                                                 dip=self.l3_config['hnu_destination_ip2'],
                                                 sip=acl_fields_dict_sanity_eg_nu_hnu['source_ip'],
                                                 s_port=acl_fields_dict_sanity_eg_nu_hnu['source_port'],
                                                 d_port=acl_fields_dict_sanity_eg_nu_hnu['dest_port'],
                                                 ecn_v4=acl_fields_dict_sanity_eg_nu_hnu['ecn_bits'])

        self.stream_obj_drop = create_streams(tx_port=nu_ing_port,
                                              dmac=self.routes_config['routermac'],
                                              dip=self.l3_config['hnu_destination_ip2'],
                                              sip=acl_fields_dict_sanity_eg_nu_hnu['source_ip'],
                                              s_port=acl_fields_dict_sanity_eg_nu_hnu['source_port'],
                                              d_port=acl_fields_dict_sanity_eg_nu_hnu['dest_port'],
                                              sync_bit=acl_fields_dict_sanity_eg_nu_hnu['tcp_sync_bit'],
                                              ack_bit=acl_fields_dict_sanity_eg_nu_hnu['tcp_ack_bit'],
                                              ecn_v4=acl_fields_dict_sanity_eg_nu_hnu['ecn_bits'])

        dut_rx_port = dut_config['ports'][0]
        dut_tx_port = dut_config['ports'][3]

    def run(self):

        tx_port = nu_ing_port
        rx_port = hnu_eg_port
        checkpoint = "Clear FPG port stats on DUT"
        c = 0
        for port_num in dut_config['ports']:
            if c == 0:
                shape = 0
                result = network_controller_obj.clear_port_stats(port_num=port_num, shape=shape)
                fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
            elif c == 3:
                shape = 1
                result = network_controller_obj.clear_port_stats(port_num=port_num, shape=shape)
                fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
            c += 1
        fun_test.add_checkpoint(checkpoint=checkpoint)

        checkpoint = "Deactivate not required stream blocks"
        obj_list = []
        obj_list.append(self.stream_obj_dip)
        obj_list.append(self.stream_obj_dport)
        obj_list.append(self.stream_obj_sip)
        obj_list.append(self.stream_obj_ecn)
        obj_list.append(self.stream_obj_tcpflag)
        obj_list.append(self.stream_obj_drop)
        template_obj.deactivate_stream_blocks(stream_obj_list=obj_list)

        checkpoint = "Start traffic from %s port for %d secs" % (tx_port, TRAFFIC_DURATION)
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION+3)
        # Getting Spirent results - only when analyzer/generator is subscribed

        checkpoint = "Fetch Tx Port Results for %s" % tx_port
        tx_port_result = template_obj.stc_manager.get_generator_port_results(
            port_handle=tx_port, subscribe_handle=subscribed_results['generator_subscribe'])
        fun_test.simple_assert(expression=tx_port_result, message=checkpoint)

        checkpoint = "Fetch Rx Port Results for %s" % rx_port
        rx_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=rx_port_result, message=checkpoint)

        fun_test.log("Tx Port: %s" % tx_port_result)
        fun_test.log("Rx Port: %s" % rx_port_result)

        dut_rx_port_results = network_controller_obj.peek_fpg_port_stats(dut_rx_port)
        fun_test.simple_assert(dut_rx_port_results, "Fetch DUT Rx port results. FPG%d" % dut_rx_port)

        dut_tx_port_results = network_controller_obj.peek_fpg_port_stats(dut_tx_port,hnu=True)
        fun_test.simple_assert(dut_tx_port_results, "Fetch DUT Tx port results. FPG%d" % dut_tx_port)

        fun_test.log("DUT Rx Port %d Results: %s" % (dut_rx_port, dut_rx_port_results))
        fun_test.log("DUT Tx Port %d Results: %s" % (dut_tx_port, dut_tx_port_results))

        checkpoint = "Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count | S_Port Stream"
        frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_results, stat_type=FRAMES_RECEIVED_OK,
                                                     tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%s: %s and Frames Transmitted on FPG%s: %s" % (
            dut_rx_port, frames_received, dut_tx_port, frames_transmitted))

        fun_test.test_assert_expected(expected=frames_received, actual=frames_transmitted, message=checkpoint)

        stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                            [self.stream_obj_sport.spirent_handle],
                                                                            tx_result=True, rx_result=True)
        tx_stream_result_framecount_sport = int(
            stream_results[self.stream_obj_sport.spirent_handle]["tx_result"]["FrameCount"])
        rx_stream_result_framecount_sport = int(
            stream_results[self.stream_obj_sport.spirent_handle]["rx_result"]["FrameCount"])
        fun_test.test_assert_expected(expected=tx_stream_result_framecount_sport,
                                      actual=rx_stream_result_framecount_sport,
                                      message="Comparing tx and rx frame count on Spirent for stream dport")

        # Validate Spirent stats
        checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Rx spirent port FrameCount"
        fun_test.test_assert_expected(expected=tx_port_result['GeneratorFrameCount'],
                                      actual=rx_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure no errors are seen on Rx spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        if frames_received == frames_transmitted:
            del obj_list[:]
            obj_list.append(self.stream_obj_sport)
            obj_list.append(self.stream_obj_drop)
            template_obj.deactivate_stream_blocks(stream_obj_list=obj_list)

            del obj_list[:]
            obj_list.append(self.stream_obj_dport)
            obj_list.append(self.stream_obj_sip)
            obj_list.append(self.stream_obj_dip)
            obj_list.append(self.stream_obj_ecn)
            obj_list.append(self.stream_obj_tcpflag)
            template_obj.activate_stream_blocks(stream_obj_list=obj_list)

            checkpoint = "Start traffic from %s port for %d secs streams dport,sip,dip,ecn,tcpflag" % (tx_port, TRAFFIC_DURATION)
            result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
            fun_test.simple_assert(expression=result, message=checkpoint)

            fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION + 2)
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_dport.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_dport = int(
                stream_results[self.stream_obj_dport.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_dport = int(
                stream_results[self.stream_obj_dport.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_dport, actual=rx_stream_result_framecount_dport,
                                          message="Comparing tx and rx frame count on Spirent for stream dport")
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_sip.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_sip = int(
                stream_results[self.stream_obj_sip.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_sip = int(
                stream_results[self.stream_obj_sip.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_sip, actual=rx_stream_result_framecount_sip,
                                      message="Comparing tx and rx frame count on Spirent for stream sip")
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_dip.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_dip = int(
                stream_results[self.stream_obj_dip.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_dip = int(
                stream_results[self.stream_obj_dip.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_dip, actual=rx_stream_result_framecount_dip,
                                      message="Comparing tx and rx frame count on Spirent for stream dip")
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_ecn.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_ecn = int(
                stream_results[self.stream_obj_ecn.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_ecn = int(
                stream_results[self.stream_obj_ecn.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_ecn,
                                          actual=rx_stream_result_framecount_ecn,
                                          message="Comparing tx and rx frame count on Spirent for stream ecn")

            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_tcpflag.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_tcpflag = int(
                stream_results[self.stream_obj_tcpflag.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_tcpflag = int(
                stream_results[self.stream_obj_tcpflag.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_tcpflag,
                                          actual=rx_stream_result_framecount_tcpflag,
                                          message="Comparing tx and rx frame count on Spirent for stream tcpflag")

            acl_stats_tx_before = network_controller_obj.peek_fpg_port_stats(dut_tx_port)
            acl_stats_rx_before = network_controller_obj.peek_fpg_port_stats(dut_rx_port)
            fun_test.log("Port DPC results : ")
            fun_test.log(acl_stats_tx_before)
            fun_test.log(acl_stats_rx_before)
            # Send drop traffic which matches all the fields below
            obj_list.append(self.stream_obj_sport)
            template_obj.deactivate_stream_blocks(stream_obj_list=obj_list)

            del obj_list[:]
            obj_list.append(self.stream_obj_drop)
            template_obj.activate_stream_blocks(stream_obj_list=obj_list)
            counterstats_before = network_controller_obj.peek_erp_flex_stats(acl_fields_dict_sanity_eg_nu_hnu['counter_id'])
            fun_test.log("counterstats Before: ")
            #fun_test.log(counterstats_before)
            counter_bef = int(counterstats_before['bank1']['pkts'])
            fun_test.log(counter_bef)
            checkpoint = "Start traffic from %s port for %d secs stream sip" % (tx_port, TRAFFIC_DURATION)
            result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
            fun_test.simple_assert(expression=result, message=checkpoint)

            fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION + 2)
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_drop.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_drop = int(
                stream_results[self.stream_obj_drop.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_drop = int(
                stream_results[self.stream_obj_drop.spirent_handle]["rx_result"]["FrameCount"])
            counterstats_after = network_controller_obj.peek_erp_flex_stats(acl_fields_dict_sanity_eg_nu_hnu['counter_id'])
            fun_test.log("counterstats after: ")
            counter_after = int(counterstats_after['bank1']['pkts'])
            fun_test.log(counter_after)
            fun_test.log("tx_streamcount"+str(tx_stream_result_framecount_drop))
            fun_test.test_assert_expected(expected=0, actual=rx_stream_result_framecount_drop,
                                          message="Comparing tx and rx frame count on Spirent for stream drop. No pkt shuold be transmitted")
            # add counter values with the stream value using : peek_erp_flex_stats
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_drop, actual=(counter_after - counter_bef),
                                          message="Packets dropped should be equal to counter value")
            rx_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
                port_handle=rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
            checkpoint = "Ensure no errors are seen on Rx spirent port"
            result = template_obj.check_non_zero_error_count(rx_results=rx_port_result)
            fun_test.test_assert(result['result'], checkpoint)

    def cleanup(self):
        dut_rx_port = dut_config['ports'][0]

        checkpoint = "Delete the streams"
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_sport.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_dport.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_sip.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_dip.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_ecn.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_drop.spirent_handle])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)


class AclIngressDropHNUtoHNU(FunTestCase):
    l2_config = None
    l3_config = None
    load = 10
    routes_config = None
    stream_obj_sport = None
    stream_obj_dport = None
    stream_obj_sip = None
    stream_obj_dip = None
    stream_obj_ecn = None
    stream_obj_drop = None
    stream_obj_tcpflag = None
    capture_results = None

    def describe(self):
        self.set_test_details(id=5, summary="Test ACL HNU to HNU",
                              steps="""
                              1. Create TCP frame stream on Tx Port
                              2. Start Traffic for %d secs
                              3. Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count 
                              4. Ensure on spirent Tx port frames must be equal to Rx port frames
                              5. Ensure no errors are seen on spirent ports
                              """ % TRAFFIC_DURATION)

    def setup(self):
        global dut_rx_port,dut_tx_port
        self.routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
        self.l3_config = self.routes_config['l3_config']
        checkpoint = "Creating multiple streams on %s port" % hnu_ing_port

        self.stream_obj_sport = create_streams(tx_port=hnu_ing_port,
                                               dmac=self.routes_config['routermac'],
                                               dip=self.l3_config['hnu_destination_ip2'],
                                               sip=acl_fields_dict_sanity_ing_hnu_hnu['source_ip'],
                                               d_port=acl_fields_dict_sanity_ing_hnu_hnu['dest_port'],
                                               sync_bit=acl_fields_dict_sanity_ing_hnu_hnu['tcp_sync_bit'],
                                               ack_bit=acl_fields_dict_sanity_ing_hnu_hnu['tcp_ack_bit'])

        self.stream_obj_dport = create_streams(tx_port=hnu_ing_port,
                                               dmac=self.routes_config['routermac'],
                                               dip=self.l3_config['hnu_destination_ip2'],
                                               sip=acl_fields_dict_sanity_ing_hnu_hnu['source_ip'],
                                               s_port=acl_fields_dict_sanity_ing_hnu_hnu['source_port'],
                                               sync_bit=acl_fields_dict_sanity_ing_hnu_hnu['tcp_sync_bit'],
                                               ack_bit=acl_fields_dict_sanity_ing_hnu_hnu['tcp_ack_bit'])

        self.stream_obj_sip = create_streams(tx_port=hnu_ing_port,
                                             dmac=self.routes_config['routermac'],
                                             dip=self.l3_config['hnu_destination_ip2'], sip="192.168.2.10",
                                             s_port=acl_fields_dict_sanity_ing_hnu_hnu['source_port'],
                                             d_port=acl_fields_dict_sanity_ing_hnu_hnu['dest_port'],
                                             sync_bit=acl_fields_dict_sanity_ing_hnu_hnu['tcp_sync_bit'],
                                             ack_bit=acl_fields_dict_sanity_ing_hnu_hnu['tcp_ack_bit'])

        self.stream_obj_dip = create_streams(tx_port=hnu_ing_port,
                                             dmac=self.routes_config['routermac'],
                                             dip=acl_fields_dict_sanity_ing_hnu_hnu['wrong_dip'],
                                             sip=acl_fields_dict_sanity_ing_hnu_hnu['source_ip'],
                                             s_port=acl_fields_dict_sanity_ing_hnu_hnu['source_port'],
                                             d_port=acl_fields_dict_sanity_ing_hnu_hnu['dest_port'],
                                             sync_bit=acl_fields_dict_sanity_ing_hnu_hnu['tcp_sync_bit'],
                                             ack_bit=acl_fields_dict_sanity_ing_hnu_hnu['tcp_ack_bit'])

        self.stream_obj_ecn = create_streams(tx_port=hnu_ing_port,
                                             dmac=self.routes_config['routermac'],
                                             dip=self.l3_config['hnu_destination_ip2'],
                                             sip=acl_fields_dict_sanity_ing_hnu_hnu['source_ip'],
                                             s_port=acl_fields_dict_sanity_ing_hnu_hnu['source_port'],
                                             d_port=acl_fields_dict_sanity_ing_hnu_hnu['dest_port'],
                                             sync_bit=acl_fields_dict_sanity_ing_hnu_hnu['tcp_sync_bit'],
                                             ack_bit=acl_fields_dict_sanity_ing_hnu_hnu['tcp_ack_bit'])

        self.stream_obj_tcpflag = create_streams(tx_port=hnu_ing_port,
                                                 dmac=self.routes_config['routermac'],
                                                 dip=self.l3_config['hnu_destination_ip2'],
                                                 sip=acl_fields_dict_sanity_ing_hnu_hnu['source_ip'],
                                                 s_port=acl_fields_dict_sanity_ing_hnu_hnu['source_port'],
                                                 d_port=acl_fields_dict_sanity_ing_hnu_hnu['dest_port'],
                                                 ecn_v4=acl_fields_dict_sanity_ing_hnu_hnu['ecn_bits'])

        self.stream_obj_drop = create_streams(tx_port=hnu_ing_port,
                                              dmac=self.routes_config['routermac'],
                                              dip=self.l3_config['hnu_destination_ip2'],
                                              sip=acl_fields_dict_sanity_ing_hnu_hnu['source_ip'],
                                              s_port=acl_fields_dict_sanity_ing_hnu_hnu['source_port'],
                                              d_port=acl_fields_dict_sanity_ing_hnu_hnu['dest_port'],
                                              sync_bit=acl_fields_dict_sanity_ing_hnu_hnu['tcp_sync_bit'],
                                              ack_bit=acl_fields_dict_sanity_ing_hnu_hnu['tcp_ack_bit'],
                                              ecn_v4=acl_fields_dict_sanity_ing_hnu_hnu['ecn_bits'])

        dut_rx_port = dut_config['ports'][2]
        dut_tx_port = dut_config['ports'][3]

    def run(self):
        tx_port = hnu_ing_port
        rx_port = hnu_eg_port
        checkpoint = "Clear FPG port stats on DUT"
        c = 0
        for port_num in dut_config['ports']:
            if c == 2 or c == 3:
                shape = 1
                result = network_controller_obj.clear_port_stats(port_num=port_num, shape=shape)
                fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
            c += 1
        fun_test.add_checkpoint(checkpoint=checkpoint)

        checkpoint = "Deactivate not required stream blocks"
        obj_list = []
        obj_list.append(self.stream_obj_dip)
        obj_list.append(self.stream_obj_dport)
        obj_list.append(self.stream_obj_sip)
        obj_list.append(self.stream_obj_ecn)
        obj_list.append(self.stream_obj_tcpflag)
        obj_list.append(self.stream_obj_drop)
        template_obj.deactivate_stream_blocks(stream_obj_list=obj_list)

        checkpoint = "Start traffic from %s port for %d secs" % (tx_port, TRAFFIC_DURATION)
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION+2)
        # Getting Spirent results - only when analyzer/generator is subscribed

        checkpoint = "Fetch Tx Port Results for %s" % tx_port
        tx_port_result = template_obj.stc_manager.get_generator_port_results(
            port_handle=tx_port, subscribe_handle=subscribed_results['generator_subscribe'])
        fun_test.simple_assert(expression=tx_port_result, message=checkpoint)

        checkpoint = "Fetch Rx Port Results for %s" % rx_port
        rx_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=rx_port_result, message=checkpoint)

        fun_test.log("Tx Port: %s" % tx_port_result)
        fun_test.log("Rx Port: %s" % rx_port_result)

        dut_rx_port_results = network_controller_obj.peek_fpg_port_stats(dut_rx_port, hnu=True)
        fun_test.simple_assert(dut_rx_port_results, "Fetch DUT Rx port results. FPG%d" % dut_rx_port)

        dut_tx_port_results = network_controller_obj.peek_fpg_port_stats(dut_tx_port, hnu=True)
        fun_test.simple_assert(dut_tx_port_results, "Fetch DUT Tx port results. FPG%d" % dut_tx_port)
        fun_test.log("DUT Rx Port %d Results: %s" % (dut_rx_port, dut_rx_port_results))
        fun_test.log("DUT Tx Port %d Results: %s" % (dut_tx_port, dut_tx_port_results))

        checkpoint = "Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count"
        frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_results, stat_type=FRAMES_RECEIVED_OK,
                                                     tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%s: %s and Frames Transmitted on FPG%s: %s" % (
            dut_rx_port, frames_received, dut_tx_port, frames_transmitted))

        fun_test.test_assert_expected(expected=frames_received, actual=frames_transmitted, message=checkpoint)

        # Validate Spirent stats
        # checkpoint = "Ensure Tx spirent Port FrameCount must be equal to Rx spirent port FrameCount"
        # fun_test.test_assert_expected(expected=tx_port_result['GeneratorFrameCount'],
        #                               actual=rx_port_result['TotalFrameCount'], message=checkpoint)

        checkpoint = "Ensure no errors are seen on Rx spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        if frames_received == frames_transmitted:
            del obj_list[:]
            obj_list.append(self.stream_obj_sport)
            obj_list.append(self.stream_obj_drop)
            template_obj.deactivate_stream_blocks(stream_obj_list=obj_list)

            del obj_list[:]
            obj_list.append(self.stream_obj_dport)
            obj_list.append(self.stream_obj_sip)
            obj_list.append(self.stream_obj_dip)
            obj_list.append(self.stream_obj_ecn)
            obj_list.append(self.stream_obj_tcpflag)
            template_obj.activate_stream_blocks(stream_obj_list=obj_list)

            checkpoint = "Start traffic from %s port for %d secs streams dport,sip,dip,ecn,tcpflag" % (tx_port, TRAFFIC_DURATION)
            result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
            fun_test.simple_assert(expression=result, message=checkpoint)

            fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION + 2)
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_dport.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_dport = int(
                stream_results[self.stream_obj_dport.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_dport = int(
                stream_results[self.stream_obj_dport.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_dport, actual=rx_stream_result_framecount_dport,
                                          message="Comparing tx and rx frame count on Spirent for stream dport")
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_sip.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_sip = int(
                stream_results[self.stream_obj_sip.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_sip = int(
                stream_results[self.stream_obj_sip.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_sip, actual=rx_stream_result_framecount_sip,
                                      message="Comparing tx and rx frame count on Spirent for stream sip")
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_dip.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_dip = int(
                stream_results[self.stream_obj_dip.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_dip = int(
                stream_results[self.stream_obj_dip.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_dip, actual=rx_stream_result_framecount_dip,
                                      message="Comparing tx and rx frame count on Spirent for stream dip")
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_ecn.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_ecn = int(
                stream_results[self.stream_obj_ecn.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_ecn = int(
                stream_results[self.stream_obj_ecn.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_ecn,
                                          actual=rx_stream_result_framecount_ecn,
                                          message="Comparing tx and rx frame count on Spirent for stream ecn")

            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_tcpflag.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_tcpflag = int(
                stream_results[self.stream_obj_tcpflag.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_tcpflag = int(
                stream_results[self.stream_obj_tcpflag.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_tcpflag,
                                          actual=rx_stream_result_framecount_tcpflag,
                                          message="Comparing tx and rx frame count on Spirent for stream tcpflag")

            acl_stats_tx_before = network_controller_obj.peek_fpg_port_stats(dut_tx_port)
            acl_stats_rx_before = network_controller_obj.peek_fpg_port_stats(dut_rx_port)
            fun_test.log("Port DPC results : ")
            fun_test.log(acl_stats_tx_before)
            fun_test.log(acl_stats_rx_before)
            # Send drop traffic which matches all the fields below
            obj_list.append(self.stream_obj_sport)
            template_obj.deactivate_stream_blocks(stream_obj_list=obj_list)

            del obj_list[:]
            obj_list.append(self.stream_obj_drop)
            template_obj.activate_stream_blocks(stream_obj_list=obj_list)

            counter_bef = get_flex_counter_values(network_controller_obj=network_controller_obj,
                                               counter_id=acl_fields_dict_sanity_ing_hnu_hnu['counter_id'])
            checkpoint = "Start traffic from %s port for %d secs stream sip" % (tx_port, TRAFFIC_DURATION)
            result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
            fun_test.simple_assert(expression=result, message=checkpoint)

            fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION + 2)
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_drop.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_drop = int(
                stream_results[self.stream_obj_drop.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_drop = int(
                stream_results[self.stream_obj_drop.spirent_handle]["rx_result"]["FrameCount"])
            counter_after = get_flex_counter_values(network_controller_obj=network_controller_obj,
                                               counter_id=acl_fields_dict_sanity_ing_hnu_hnu['counter_id'])
            fun_test.log("tx_streamcount"+str(tx_stream_result_framecount_drop))
            fun_test.test_assert_expected(expected=0, actual=rx_stream_result_framecount_drop,
                                          message="Comparing tx and rx frame count on Spirent for stream drop. No pkt shuold be transmitted")
            # add counter values with the stream value using : peek_erp_flex_stats
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_drop, actual=(counter_after - counter_bef),
                                          message="Packets dropped should be equal to counter value")
            rx_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
                port_handle=rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
            checkpoint = "Ensure no errors are seen on Rx spirent port"
            result = template_obj.check_non_zero_error_count(rx_results=rx_port_result)
            fun_test.test_assert(result['result'], checkpoint)

    def cleanup(self):
        dut_rx_port = dut_config['ports'][0]

        checkpoint = "Delete the streams"
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_sport.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_dport.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_sip.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_dip.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_ecn.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_drop.spirent_handle])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)


class AclEgressDropHNUtoNU(FunTestCase):
    l2_config = None
    l3_config = None
    load = 10
    routes_config = None
    stream_obj_sport = None
    stream_obj_dport = None
    stream_obj_sip = None
    stream_obj_dip = None
    stream_obj_ecn = None
    stream_obj_drop = None
    stream_obj_tcpflag = None
    capture_results = None

    def describe(self):
        self.set_test_details(id=6, summary="Test ACL HNU to NU",
                              steps="""
                              1. Create TCP frame stream on Tx Port
                              2. Start Traffic for %d secs
                              3. Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count 
                              4. Ensure on spirent Tx port frames must be equal to Rx port frames
                              5. Ensure no errors are seen on spirent ports
                              """ % TRAFFIC_DURATION)

    def setup(self):
        global dut_rx_port,dut_tx_port
        self.routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config)
        self.l3_config = self.routes_config['l3_config']
        #Multiple streams for seding packets with different fields
        checkpoint = "Creating multiple streams on %s port" % hnu_ing_port
        self.stream_obj_sport = create_streams(tx_port=hnu_ing_port,
                                               dmac=self.routes_config['routermac'],
                                               dip=self.l3_config['destination_ip1'],
                                               sip=acl_fields_dict_sanity_eg_hnu_nu['source_ip'],
                                               d_port=acl_fields_dict_sanity_eg_hnu_nu['dest_port'],
                                               sync_bit=acl_fields_dict_sanity_eg_hnu_nu['tcp_sync_bit'],
                                               ack_bit=acl_fields_dict_sanity_eg_hnu_nu['tcp_ack_bit'])

        self.stream_obj_dport = create_streams(tx_port=hnu_ing_port,
                                               dmac=self.routes_config['routermac'],
                                               dip=self.l3_config['destination_ip1'],
                                               sip=acl_fields_dict_sanity_eg_hnu_nu['source_ip'],
                                               s_port=acl_fields_dict_sanity_eg_hnu_nu['source_port'],
                                               sync_bit=acl_fields_dict_sanity_eg_hnu_nu['tcp_sync_bit'],
                                               ack_bit=acl_fields_dict_sanity_eg_hnu_nu['tcp_ack_bit'])

        self.stream_obj_sip = create_streams(tx_port=hnu_ing_port,
                                             dmac=self.routes_config['routermac'],
                                             dip=self.l3_config['destination_ip1'], sip="192.168.2.10",
                                             s_port=acl_fields_dict_sanity_eg_hnu_nu['source_port'],
                                             d_port=acl_fields_dict_sanity_eg_hnu_nu['dest_port'],
                                             sync_bit=acl_fields_dict_sanity_eg_hnu_nu['tcp_sync_bit'],
                                             ack_bit=acl_fields_dict_sanity_eg_hnu_nu['tcp_ack_bit'])

        self.stream_obj_dip = create_streams(tx_port=hnu_ing_port,
                                             dmac=self.routes_config['routermac'],
                                             dip=acl_fields_dict_sanity_eg_hnu_nu['wrong_dip'],
                                             sip=acl_fields_dict_sanity_eg_hnu_nu['source_ip'],
                                             s_port=acl_fields_dict_sanity_eg_hnu_nu['source_port'],
                                             d_port=acl_fields_dict_sanity_eg_hnu_nu['dest_port'],
                                             sync_bit=acl_fields_dict_sanity_eg_hnu_nu['tcp_sync_bit'],
                                             ack_bit=acl_fields_dict_sanity_eg_hnu_nu['tcp_ack_bit'])

        self.stream_obj_ecn = create_streams(tx_port=hnu_ing_port,
                                             dmac=self.routes_config['routermac'],
                                             dip=self.l3_config['destination_ip1'],
                                             sip=acl_fields_dict_sanity_eg_hnu_nu['source_ip'],
                                             s_port=acl_fields_dict_sanity_eg_hnu_nu['source_port'],
                                             d_port=acl_fields_dict_sanity_eg_hnu_nu['dest_port'],
                                             sync_bit=acl_fields_dict_sanity_eg_hnu_nu['tcp_sync_bit'],
                                             ack_bit=acl_fields_dict_sanity_eg_hnu_nu['tcp_ack_bit'])

        self.stream_obj_tcpflag = create_streams(tx_port=hnu_ing_port,
                                                 dmac=self.routes_config['routermac'],
                                                 dip=self.l3_config['destination_ip1'],
                                                 sip=acl_fields_dict_sanity_eg_hnu_nu['source_ip'],
                                                 s_port=acl_fields_dict_sanity_eg_hnu_nu['source_port'],
                                                 d_port=acl_fields_dict_sanity_eg_hnu_nu['dest_port'],
                                                 ecn_v4=acl_fields_dict_sanity_eg_hnu_nu['ecn_bits'])

        self.stream_obj_drop = create_streams(tx_port=hnu_ing_port,
                                              dmac=self.routes_config['routermac'],
                                              dip=self.l3_config['destination_ip1'],
                                              sip=acl_fields_dict_sanity_eg_hnu_nu['source_ip'],
                                              s_port=acl_fields_dict_sanity_eg_hnu_nu['source_port'],
                                              d_port=acl_fields_dict_sanity_eg_hnu_nu['dest_port'],
                                              sync_bit=acl_fields_dict_sanity_eg_hnu_nu['tcp_sync_bit'],
                                              ack_bit=acl_fields_dict_sanity_eg_hnu_nu['tcp_ack_bit'],
                                              ecn_v4=acl_fields_dict_sanity_eg_hnu_nu['ecn_bits'])

        dut_rx_port = dut_config['ports'][2]
        dut_tx_port = dut_config['ports'][1]

    def run(self):
        tx_port = hnu_ing_port
        rx_port = nu_eg_port
        checkpoint = "Clear FPG port stats on DUT"
        c = 0
        for port_num in dut_config['ports']:
            if c == 1:
                shape = 0
                result = network_controller_obj.clear_port_stats(port_num=port_num, shape=shape)
                fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
            elif c == 2:
                shape = 1
                result = network_controller_obj.clear_port_stats(port_num=port_num, shape=shape)
                fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
            c += 1
        fun_test.add_checkpoint(checkpoint=checkpoint)

        checkpoint = "Deactivate not required stream blocks"
        obj_list = []
        obj_list.append(self.stream_obj_dip)
        obj_list.append(self.stream_obj_dport)
        obj_list.append(self.stream_obj_sip)
        obj_list.append(self.stream_obj_ecn)
        obj_list.append(self.stream_obj_tcpflag)
        obj_list.append(self.stream_obj_drop)
        template_obj.deactivate_stream_blocks(stream_obj_list=obj_list)
        del obj_list[:]
        obj_list.append(self.stream_obj_sport)
        template_obj.activate_stream_blocks(stream_obj_list=obj_list)
        checkpoint = "Start traffic from %s port for %d secs" % (tx_port, TRAFFIC_DURATION)
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION+2)
        # Getting Spirent results - only when analyzer/generator is subscribed

        checkpoint = "Fetch Tx Port Results for %s" % tx_port
        tx_port_result = template_obj.stc_manager.get_generator_port_results(
            port_handle=tx_port, subscribe_handle=subscribed_results['generator_subscribe'])
        fun_test.simple_assert(expression=tx_port_result, message=checkpoint)

        checkpoint = "Fetch Rx Port Results for %s" % rx_port
        rx_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=rx_port_result, message=checkpoint)

        fun_test.log("Tx Port: %s" % tx_port_result)
        fun_test.log("Rx Port: %s" % rx_port_result)

        dut_rx_port_results = network_controller_obj.peek_fpg_port_stats(dut_rx_port, hnu=True)
        fun_test.simple_assert(dut_rx_port_results, "Fetch DUT Rx port results. FPG%d" % dut_rx_port)

        dut_tx_port_results = network_controller_obj.peek_fpg_port_stats(dut_tx_port)
        fun_test.simple_assert(dut_tx_port_results, "Fetch DUT Tx port results. FPG%d" % dut_tx_port)

        fun_test.log("DUT Rx Port %d Results: %s" % (dut_rx_port, dut_rx_port_results))
        fun_test.log("DUT Tx Port %d Results: %s" % (dut_tx_port, dut_tx_port_results))

        checkpoint = "Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count"
        frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_results, stat_type=FRAMES_RECEIVED_OK,
                                                     tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%s: %s and Frames Transmitted on FPG%s: %s" % (
            dut_rx_port, frames_received, dut_tx_port, frames_transmitted))

        fun_test.test_assert_expected(expected=frames_received, actual=frames_transmitted, message=checkpoint)

        checkpoint = "Ensure no errors are seen on Rx spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        if frames_received == frames_transmitted:
            del obj_list[:]
            obj_list.append(self.stream_obj_sport)
            obj_list.append(self.stream_obj_drop)
            template_obj.deactivate_stream_blocks(stream_obj_list=obj_list)

            del obj_list[:]
            obj_list.append(self.stream_obj_dport)
            obj_list.append(self.stream_obj_sip)
            obj_list.append(self.stream_obj_dip)
            obj_list.append(self.stream_obj_ecn)
            obj_list.append(self.stream_obj_tcpflag)
            template_obj.activate_stream_blocks(stream_obj_list=obj_list)

            checkpoint = "Start traffic from %s port for %d secs streams dport,sip,dip,ecn,tcpflag" % (tx_port, TRAFFIC_DURATION)
            result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
            fun_test.simple_assert(expression=result, message=checkpoint)

            fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION + 2)
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_dport.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_dport = int(
                stream_results[self.stream_obj_dport.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_dport = int(
                stream_results[self.stream_obj_dport.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_dport, actual=rx_stream_result_framecount_dport,
                                          message="Comparing tx and rx frame count on Spirent for stream dport")
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_sip.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_sip = int(
                stream_results[self.stream_obj_sip.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_sip = int(
                stream_results[self.stream_obj_sip.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_sip, actual=rx_stream_result_framecount_sip,
                                      message="Comparing tx and rx frame count on Spirent for stream sip")
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_dip.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_dip = int(
                stream_results[self.stream_obj_dip.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_dip = int(
                stream_results[self.stream_obj_dip.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_dip, actual=rx_stream_result_framecount_dip,
                                      message="Comparing tx and rx frame count on Spirent for stream dip")
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_ecn.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_ecn = int(
                stream_results[self.stream_obj_ecn.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_ecn = int(
                stream_results[self.stream_obj_ecn.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_ecn,
                                          actual=rx_stream_result_framecount_ecn,
                                          message="Comparing tx and rx frame count on Spirent for stream ecn")

            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_tcpflag.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_tcpflag = int(
                stream_results[self.stream_obj_tcpflag.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_tcpflag = int(
                stream_results[self.stream_obj_tcpflag.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_tcpflag,
                                          actual=rx_stream_result_framecount_tcpflag,
                                          message="Comparing tx and rx frame count on Spirent for stream tcpflag")

            acl_stats_tx_before = network_controller_obj.peek_fpg_port_stats(dut_tx_port)
            acl_stats_rx_before = network_controller_obj.peek_fpg_port_stats(dut_rx_port)
            fun_test.log("Port DPC results : ")
            fun_test.log(acl_stats_tx_before)
            fun_test.log(acl_stats_rx_before)
            # Send drop traffic which matches all the fields below
            obj_list.append(self.stream_obj_sport)
            template_obj.deactivate_stream_blocks(stream_obj_list=obj_list)

            del obj_list[:]
            obj_list.append(self.stream_obj_drop)
            template_obj.activate_stream_blocks(stream_obj_list=obj_list)

            checkpoint = "Start traffic from %s port for %d secs stream sip" % (tx_port, TRAFFIC_DURATION)
            result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
            fun_test.simple_assert(expression=result, message=checkpoint)

            fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION + 2)
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_drop.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_drop = int(
                stream_results[self.stream_obj_drop.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_drop = int(
                stream_results[self.stream_obj_drop.spirent_handle]["rx_result"]["FrameCount"])

            fun_test.log("tx_streamcount"+str(tx_stream_result_framecount_drop))
            fun_test.test_assert_expected(expected=0, actual=rx_stream_result_framecount_drop,
                                          message="Comparing tx and rx frame count on Spirent for stream drop. No pkt shuold be transmitted")
            rx_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
                port_handle=rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
            checkpoint = "Ensure no errors are seen on Rx spirent port"
            result = template_obj.check_non_zero_error_count(rx_results=rx_port_result)
            fun_test.test_assert(result['result'], checkpoint)

    def cleanup(self):
        dut_rx_port = dut_config['ports'][0]

        checkpoint = "Delete the streams"
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_sport.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_dport.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_sip.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_dip.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_ecn.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_drop.spirent_handle])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)


class AclIPv6NUtoHNU(FunTestCase):
    l2_config = None
    l3_config = None
    load = 10
    routes_config = None
    stream_obj_sport = None
    stream_obj_dport = None
    stream_obj_sip = None
    stream_obj_dip = None
    stream_obj_drop = None
    stream_obj_ecn = None
    stream_obj_tcpflag = None
    capture_results = None

    def describe(self):
        self.set_test_details(id=7, summary="Test IPv6 ACL FPG to HNU",
                              steps="""
                                 1. Create TCP frame stream on Tx Port
                                 2. Start Traffic for %d secs
                                 3. Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count 
                                 4. Ensure on spirent Tx port frames must be equal to Rx port frames
                                 5. Ensure no errors are seen on spirent ports
                                 """ % TRAFFIC_DURATION)

    def setup(self):
        global dut_rx_port, dut_tx_port
        self.routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config,
                                                                              ip_version="ipv6")
        self.l3_config = self.routes_config['l3_config']
        # Multiple streams for seding packets with different fields
        checkpoint = "Creating multiple streams on %s port" % nu_ing_port

        self.stream_obj_sport = create_streams(tx_port=nu_ing_port,  ipv6=True,
                                               dip=self.l3_config['hnu_destination_ip2'],
                                               sip=acl_fields_dict_sanity_v6_nu_hnu['source_ip'],
                                               dmac=self.routes_config['routermac'],
                                               s_port=1024, d_port=acl_fields_dict_sanity_v6_nu_hnu['dest_port'])

        self.stream_obj_dport = create_streams(tx_port=nu_ing_port,  ipv6=True,
                                               dip=self.l3_config['hnu_destination_ip2'],
                                               sip=acl_fields_dict_sanity_v6_nu_hnu['source_ip'],
                                               dmac=self.routes_config['routermac'],
                                               s_port=acl_fields_dict_sanity_v6_nu_hnu['source_port'], d_port=1024)

        self.stream_obj_sip = create_streams(tx_port=nu_ing_port,  ipv6=True,
                                             dip=self.l3_config['hnu_destination_ip2'],
                                             sip="3001::1", dmac=self.routes_config['routermac'],
                                             s_port=acl_fields_dict_sanity_v6_nu_hnu['source_port'],
                                             d_port=acl_fields_dict_sanity_v6_nu_hnu['dest_port'])

        self.stream_obj_dip = create_streams(tx_port=nu_ing_port,  ipv6=True,
                                             dip=self.l3_config['hnu_destination_ip2'],
                                             sip=acl_fields_dict_sanity_v6_nu_hnu['source_ip'],
                                             dmac=self.routes_config['routermac'],
                                             s_port=acl_fields_dict_sanity_v6_nu_hnu['source_port'],
                                             d_port=acl_fields_dict_sanity_v6_nu_hnu['dest_port'])

        self.stream_obj_tcpflag = create_streams(tx_port=nu_ing_port,
                                                 ipv6=True, dip=self.l3_config['hnu_destination_ip2'],
                                                 sip=acl_fields_dict_sanity_v6_nu_hnu['source_ip'],
                                                 dmac=self.routes_config['routermac'],
                                                 s_port=acl_fields_dict_sanity_v6_nu_hnu['source_port'],
                                                 d_port=acl_fields_dict_sanity_v6_nu_hnu['dest_port'],
                                                 sync_bit=acl_fields_dict_sanity_v6_nu_hnu['tcp_sync_bit'])

        self.stream_obj_ecn = create_streams(tx_port=nu_ing_port,  ipv6=True,
                                             dip=self.l3_config['hnu_destination_ip2'],
                                             sip=acl_fields_dict_sanity_v6_nu_hnu['source_ip'],
                                             dmac=self.routes_config['routermac'],
                                             s_port=acl_fields_dict_sanity_v6_nu_hnu['source_port'],
                                             d_port=acl_fields_dict_sanity_v6_nu_hnu['dest_port'],
                                             sync_bit=acl_fields_dict_sanity_v6_nu_hnu['tcp_sync_bit'],
                                             ack_bit=acl_fields_dict_sanity_v6_nu_hnu['tcp_ack_bit'])

        self.stream_obj_drop = create_streams(tx_port=nu_ing_port,  ipv6=True,
                                              dip=self.l3_config['hnu_destination_ip2'],
                                              sip=acl_fields_dict_sanity_v6_nu_hnu['source_ip'],
                                              dmac=self.routes_config['routermac'],
                                              s_port=acl_fields_dict_sanity_v6_nu_hnu['source_port'],
                                              d_port=acl_fields_dict_sanity_v6_nu_hnu['dest_port'],
                                              sync_bit=acl_fields_dict_sanity_v6_nu_hnu['tcp_sync_bit'],
                                              ack_bit=acl_fields_dict_sanity_v6_nu_hnu['tcp_ack_bit'],
                                              v6_traffic_class=2)

        dut_rx_port = dut_config['ports'][0]
        dut_tx_port = dut_config['ports'][3]

    def run(self):
        tx_port = nu_ing_port
        rx_port = hnu_eg_port
        checkpoint = "Clear FPG port stats on DUT"
        c = 0
        for port_num in dut_config['ports']:
            if c == 0:
                shape = 0
                result = network_controller_obj.clear_port_stats(port_num=port_num, shape=shape)
                fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
            elif c == 3:
                shape = 1
                result = network_controller_obj.clear_port_stats(port_num=port_num, shape=shape)
                fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
            c += 1
        fun_test.add_checkpoint(checkpoint=checkpoint)

        checkpoint = "Deactivate not required stream blocks"
        obj_list = []
        obj_list.append(self.stream_obj_dip)
        obj_list.append(self.stream_obj_dport)
        obj_list.append(self.stream_obj_sip)
        obj_list.append(self.stream_obj_tcpflag)
        obj_list.append(self.stream_obj_drop)
        obj_list.append(self.stream_obj_ecn)
        template_obj.deactivate_stream_blocks(stream_obj_list=obj_list)
        del obj_list[:]
        obj_list.append(self.stream_obj_sport)
        template_obj.activate_stream_blocks(stream_obj_list=obj_list)

        checkpoint = "Start traffic from %s port for %d secs" % (tx_port, TRAFFIC_DURATION)
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION + 2)
        # Getting Spirent results - only when analyzer/generator is subscribed

        checkpoint = "Fetch Tx Port Results for %s" % tx_port
        tx_port_result = template_obj.stc_manager.get_generator_port_results(
            port_handle=tx_port, subscribe_handle=subscribed_results['generator_subscribe'])
        fun_test.simple_assert(expression=tx_port_result, message=checkpoint)

        checkpoint = "Fetch Rx Port Results for %s" % rx_port
        rx_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=rx_port_result, message=checkpoint)

        fun_test.log("Tx Port: %s" % tx_port_result)
        fun_test.log("Rx Port: %s" % rx_port_result)

        dut_rx_port_results = network_controller_obj.peek_fpg_port_stats(dut_rx_port)
        fun_test.simple_assert(dut_rx_port_results, "Fetch DUT Rx port results. FPG%d" % dut_rx_port)

        dut_tx_port_results = network_controller_obj.peek_fpg_port_stats(dut_tx_port, hnu=True)
        fun_test.simple_assert(dut_tx_port_results, "Fetch DUT Tx port results. FPG%d" % dut_tx_port)

        fun_test.log("DUT Rx Port %d Results: %s" % (dut_rx_port, dut_rx_port_results))
        fun_test.log("DUT Tx Port %d Results: %s" % (dut_tx_port, dut_tx_port_results))

        frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_results, stat_type=FRAMES_RECEIVED_OK,
                                                     tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%s: %s and Frames Transmitted on FPG%s: %s" % (
            dut_rx_port, frames_received, dut_tx_port, frames_transmitted))

        fun_test.test_assert_expected(expected=frames_received, actual=frames_transmitted, message=checkpoint)

        stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                            [self.stream_obj_sport.spirent_handle],
                                                                            tx_result=True, rx_result=True)
        tx_stream_result_framecount_sport = int(
            stream_results[self.stream_obj_sport.spirent_handle]["tx_result"]["FrameCount"])
        rx_stream_result_framecount_sport = int(
            stream_results[self.stream_obj_sport.spirent_handle]["rx_result"]["FrameCount"])
        fun_test.test_assert_expected(expected=tx_stream_result_framecount_sport,
                                      actual=rx_stream_result_framecount_sport,
                                      message="Comparing tx and rx frame count on Spirent for stream dport")

        checkpoint = "Ensure no errors are seen on Rx spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        del obj_list[:]
        obj_list.append(self.stream_obj_sport)
        obj_list.append(self.stream_obj_drop)
        template_obj.deactivate_stream_blocks(stream_obj_list=obj_list)

        del obj_list[:]
        obj_list.append(self.stream_obj_dport)
        obj_list.append(self.stream_obj_sip)
        obj_list.append(self.stream_obj_dip)
        obj_list.append(self.stream_obj_tcpflag)
        #obj_list.append(self.stream_obj_ecn)
        template_obj.activate_stream_blocks(stream_obj_list=obj_list)

        checkpoint = "Start traffic from %s port for %d secs streams dport,sip,dip,ecn,tcpflag" % (
        tx_port, TRAFFIC_DURATION)
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION + 2)
        stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                            [self.stream_obj_dport.spirent_handle],
                                                                            tx_result=True, rx_result=True)
        tx_stream_result_framecount_dport = int(
            stream_results[self.stream_obj_dport.spirent_handle]["tx_result"]["FrameCount"])
        rx_stream_result_framecount_dport = int(
            stream_results[self.stream_obj_dport.spirent_handle]["rx_result"]["FrameCount"])
        fun_test.test_assert_expected(expected=tx_stream_result_framecount_dport,
                                      actual=rx_stream_result_framecount_dport,
                                      message="Comparing tx and rx frame count on Spirent for stream dport")
        stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                            [self.stream_obj_sip.spirent_handle],
                                                                            tx_result=True, rx_result=True)
        tx_stream_result_framecount_sip = int(
            stream_results[self.stream_obj_sip.spirent_handle]["tx_result"]["FrameCount"])
        rx_stream_result_framecount_sip = int(
            stream_results[self.stream_obj_sip.spirent_handle]["rx_result"]["FrameCount"])
        fun_test.test_assert_expected(expected=tx_stream_result_framecount_sip,
                                      actual=rx_stream_result_framecount_sip,
                                      message="Comparing tx and rx frame count on Spirent for stream sip")
        stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                            [self.stream_obj_dip.spirent_handle],
                                                                            tx_result=True, rx_result=True)
        tx_stream_result_framecount_dip = int(
            stream_results[self.stream_obj_dip.spirent_handle]["tx_result"]["FrameCount"])
        rx_stream_result_framecount_dip = int(
            stream_results[self.stream_obj_dip.spirent_handle]["rx_result"]["FrameCount"])
        fun_test.test_assert_expected(expected=tx_stream_result_framecount_dip,
                                      actual=rx_stream_result_framecount_dip,
                                      message="Comparing tx and rx frame count on Spirent for stream dip")

        stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                            [self.stream_obj_tcpflag.spirent_handle],
                                                                            tx_result=True, rx_result=True)
        tx_stream_result_framecount_tcpflag = int(
            stream_results[self.stream_obj_tcpflag.spirent_handle]["tx_result"]["FrameCount"])
        rx_stream_result_framecount_tcpflag = int(
            stream_results[self.stream_obj_tcpflag.spirent_handle]["rx_result"]["FrameCount"])
        fun_test.test_assert_expected(expected=tx_stream_result_framecount_tcpflag,
                                      actual=rx_stream_result_framecount_tcpflag,
                                      message="Comparing tx and rx frame count on Spirent for stream tcpflag")
        #enable ecn after bug fix is complete for ECN on ERP
        # stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
        #                                                                     [self.stream_obj_ecn.spirent_handle],
        #                                                                     tx_result=True, rx_result=True)
        # # tx_stream_result_framecount_ecn = int(
        #     stream_results[self.stream_obj_ecn.spirent_handle]["tx_result"]["FrameCount"])
        # rx_stream_result_framecount_ecn = int(
        #     stream_results[self.stream_obj_ecn.spirent_handle]["rx_result"]["FrameCount"])
        # fun_test.test_assert_expected(expected=tx_stream_result_framecount_ecn,
        #                               actual=rx_stream_result_framecount_ecn,
        #                               message="Comparing tx and rx frame count on Spirent for stream tcpflag")

        acl_stats_tx_before = network_controller_obj.peek_fpg_port_stats(dut_tx_port)
        acl_stats_rx_before = network_controller_obj.peek_fpg_port_stats(dut_rx_port,hnu=True)
        fun_test.log("Port DPC results : ")
        fun_test.log(acl_stats_tx_before)
        fun_test.log(acl_stats_rx_before)
        # Send drop traffic which matches all the fields below
        obj_list.append(self.stream_obj_sport)
        template_obj.deactivate_stream_blocks(stream_obj_list=obj_list)

        del obj_list[:]
        obj_list.append(self.stream_obj_drop)
        template_obj.activate_stream_blocks(stream_obj_list=obj_list)

        counter_bef = get_flex_counter_values(network_controller_obj=network_controller_obj,
                                         counter_id=acl_fields_dict_sanity_v6_nu_hnu['counter_id'],erp=True)

        checkpoint = "Start traffic from %s port for %d secs stream sip" % (tx_port, TRAFFIC_DURATION)
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION + 2)
        stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                            [self.stream_obj_drop.spirent_handle],
                                                                            tx_result=True, rx_result=True)
        tx_stream_result_framecount_drop = int(
            stream_results[self.stream_obj_drop.spirent_handle]["tx_result"]["FrameCount"])
        rx_stream_result_framecount_drop = int(
            stream_results[self.stream_obj_drop.spirent_handle]["rx_result"]["FrameCount"])

        counter_after = get_flex_counter_values(network_controller_obj=network_controller_obj,
                                           counter_id=acl_fields_dict_sanity_v6_nu_hnu['counter_id'],erp=True)

        fun_test.log("tx_streamcount" + str(tx_stream_result_framecount_drop))
        checkpoint="Comparing tx and rx frame count on Spirent for stream drop. No pkt shuold be transmitted"
        fun_test.test_assert_expected(expected=0, actual=rx_stream_result_framecount_drop,
                                      message=checkpoint)
        # add counter values with the stream value using : peek_fwd_flex_stats
        fun_test.test_assert_expected(expected=tx_stream_result_framecount_drop,
                                      actual=(counter_after - counter_bef),
                                      message="Packets dropped should be equal to counter value")
        rx_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        checkpoint = "Ensure no errors are seen on Rx spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_result)
        fun_test.test_assert(result['result'], checkpoint)

    def cleanup(self):
        dut_rx_port = dut_config['ports'][0]

        checkpoint = "Delete the streams"
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_sport.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_dport.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_sip.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_dip.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_drop.spirent_handle])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)


class AclIPv6HNUtoHNU(FunTestCase):
    l2_config = None
    l3_config = None
    load = 10
    routes_config = None
    stream_obj_sport = None
    stream_obj_dport = None
    stream_obj_sip = None
    stream_obj_dip = None
    stream_obj_drop = None
    stream_obj_tcpflag = None
    stream_obj_ecn = None
    capture_results = None

    def describe(self):
        self.set_test_details(id=8, summary="Test IPv6 ACL HNU to HNU",
                              steps="""
                                 1. Create TCP frame stream on Tx Port
                                 2. Start Traffic for %d secs
                                 3. Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count 
                                 4. Ensure on spirent Tx port frames must be equal to Rx port frames
                                 5. Ensure no errors are seen on spirent ports
                                 """ % TRAFFIC_DURATION)

    def setup(self):
        global dut_rx_port, dut_tx_port
        self.routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config,
                                                                              ip_version="ipv6")
        self.l3_config = self.routes_config['l3_config']
        # Multiple streams for seding packets with different fields
        checkpoint = "Creating multiple streams on %s port" % hnu_ing_port

        self.stream_obj_sport = create_streams(tx_port=hnu_ing_port,
                                               ipv6=True, dip=self.l3_config['hnu_destination_ip2'],
                                               sip=acl_fields_dict_ipv6_hnu_hnu['source_ip'],
                                               dmac=self.routes_config['routermac'],
                                               s_port=1024, d_port=acl_fields_dict_ipv6_hnu_hnu['dest_port'])

        self.stream_obj_dport = create_streams(tx_port=hnu_ing_port,
                                               ipv6=True, dip=self.l3_config['hnu_destination_ip2'],
                                               sip=acl_fields_dict_ipv6_hnu_hnu['source_ip'],
                                               dmac=self.routes_config['routermac'],
                                               s_port=acl_fields_dict_ipv6_hnu_hnu['source_port'], d_port=1024)

        self.stream_obj_sip = create_streams(tx_port=hnu_ing_port,  ipv6=True,
                                             dip=self.l3_config['hnu_destination_ip2'],
                                             sip="3001::1", dmac=self.routes_config['routermac'],
                                             s_port=acl_fields_dict_ipv6_hnu_hnu['source_port'],
                                             d_port=acl_fields_dict_ipv6_hnu_hnu['dest_port'])

        self.stream_obj_dip = create_streams(tx_port=hnu_ing_port,  ipv6=True,
                                             dip=acl_fields_dict_ipv6_hnu_hnu['wrong_dip'],
                                             sip=acl_fields_dict_ipv6_hnu_hnu['source_ip'],
                                             dmac=self.routes_config['routermac'],
                                             s_port=acl_fields_dict_ipv6_hnu_hnu['source_port'],
                                             d_port=acl_fields_dict_ipv6_hnu_hnu['dest_port'])

        self.stream_obj_tcpflag = create_streams(tx_port=hnu_ing_port,
                                                 ipv6=True, dip=self.l3_config['hnu_destination_ip2'],
                                                 sip=acl_fields_dict_ipv6_hnu_hnu['source_ip'],
                                                 dmac=self.routes_config['routermac'],
                                                 s_port=acl_fields_dict_ipv6_hnu_hnu['source_port'],
                                                 d_port=acl_fields_dict_ipv6_hnu_hnu['dest_port'],
                                                 sync_bit=acl_fields_dict_ipv6_hnu_hnu['tcp_sync_bit'])

        self.stream_obj_ecn = create_streams(tx_port=hnu_ing_port,  ipv6=True,
                                             dip=self.l3_config['hnu_destination_ip2'],
                                             sip=acl_fields_dict_ipv6_hnu_hnu['source_ip'],
                                             dmac=self.routes_config['routermac'],
                                             s_port=acl_fields_dict_ipv6_hnu_hnu['source_port'],
                                             d_port=acl_fields_dict_ipv6_hnu_hnu['dest_port'],
                                             sync_bit=acl_fields_dict_ipv6_hnu_hnu['tcp_sync_bit'],
                                             ack_bit=acl_fields_dict_ipv6_hnu_hnu['tcp_ack_bit'])

        self.stream_obj_drop = create_streams(tx_port=hnu_ing_port,  ipv6=True,
                                              dip=self.l3_config['hnu_destination_ip2'],
                                              sip=acl_fields_dict_ipv6_hnu_hnu['source_ip'],
                                              dmac=self.routes_config['routermac'],
                                              s_port=acl_fields_dict_ipv6_hnu_hnu['source_port'],
                                              d_port=acl_fields_dict_ipv6_hnu_hnu['dest_port'],
                                              sync_bit=acl_fields_dict_ipv6_hnu_hnu['tcp_sync_bit'],
                                              ack_bit=acl_fields_dict_ipv6_hnu_hnu['tcp_ack_bit'],
                                              v6_traffic_class=2)

        dut_rx_port = dut_config['ports'][2]
        dut_tx_port = dut_config['ports'][3]

    def run(self):
        tx_port = hnu_ing_port
        rx_port = hnu_eg_port
        checkpoint = "Clear FPG port stats on DUT"
        c = 0
        for port_num in dut_config['ports']:
            if c == 2 or c == 3:
                shape = 1
                result = network_controller_obj.clear_port_stats(port_num=port_num, shape=shape)
                fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
            c += 1
        fun_test.add_checkpoint(checkpoint=checkpoint)

        checkpoint = "Deactivate not required stream blocks"
        obj_list = []
        obj_list.append(self.stream_obj_dip)
        obj_list.append(self.stream_obj_dport)
        obj_list.append(self.stream_obj_sip)
        obj_list.append(self.stream_obj_tcpflag)
        obj_list.append(self.stream_obj_drop)
        obj_list.append(self.stream_obj_ecn)
        template_obj.deactivate_stream_blocks(stream_obj_list=obj_list)
        del obj_list[:]
        obj_list.append(self.stream_obj_sport)
        template_obj.activate_stream_blocks(stream_obj_list=obj_list)

        checkpoint = "Start traffic from %s port for %d secs" % (tx_port, TRAFFIC_DURATION)
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION + 3)

        checkpoint = "Fetch Rx Port Results for %s" % rx_port
        rx_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=rx_port_result, message=checkpoint)

        dut_rx_port_results = network_controller_obj.peek_fpg_port_stats(dut_rx_port, hnu=True)
        fun_test.simple_assert(dut_rx_port_results, "Fetch DUT Rx port results. FPG%d" % dut_rx_port)

        dut_tx_port_results = network_controller_obj.peek_fpg_port_stats(dut_tx_port, hnu=True)
        fun_test.simple_assert(dut_tx_port_results, "Fetch DUT Tx port results. FPG%d" % dut_tx_port)

        fun_test.log("DUT Rx Port %d Results: %s" % (dut_rx_port, dut_rx_port_results))
        fun_test.log("DUT Tx Port %d Results: %s" % (dut_tx_port, dut_tx_port_results))

        checkpoint = "Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count"
        frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_results, stat_type=FRAMES_RECEIVED_OK,
                                                     tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%s: %s and Frames Transmitted on FPG%s: %s" % (
            dut_rx_port, frames_received, dut_tx_port, frames_transmitted))

        fun_test.test_assert_expected(expected=frames_received, actual=frames_transmitted, message=checkpoint)

        # Validate Spirent stats
        stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                            [self.stream_obj_sport.spirent_handle],
                                                                            tx_result=True, rx_result=True)
        tx_stream_result_framecount_sport = int(
            stream_results[self.stream_obj_sport.spirent_handle]["tx_result"]["FrameCount"])
        rx_stream_result_framecount_sport = int(
            stream_results[self.stream_obj_sport.spirent_handle]["rx_result"]["FrameCount"])
        fun_test.test_assert_expected(expected=tx_stream_result_framecount_sport,
                                      actual=rx_stream_result_framecount_sport,
                                      message="Comparing tx and rx frame count on Spirent for stream sip")

        checkpoint = "Ensure no errors are seen on Rx spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        if frames_received == frames_transmitted:
            del obj_list[:]
            obj_list.append(self.stream_obj_sport)
            obj_list.append(self.stream_obj_drop)
            template_obj.deactivate_stream_blocks(stream_obj_list=obj_list)

            del obj_list[:]
            obj_list.append(self.stream_obj_dport)
            obj_list.append(self.stream_obj_sip)
            obj_list.append(self.stream_obj_dip)
            obj_list.append(self.stream_obj_tcpflag)
            obj_list.append(self.stream_obj_ecn)
            template_obj.activate_stream_blocks(stream_obj_list=obj_list)

            checkpoint = "Start traffic from %s port for %d secs streams dport,sip,dip,ecn,tcpflag" % (
            tx_port, TRAFFIC_DURATION)
            result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
            fun_test.simple_assert(expression=result, message=checkpoint)

            fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION + 5)
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_dport.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_dport = int(
                stream_results[self.stream_obj_dport.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_dport = int(
                stream_results[self.stream_obj_dport.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_dport,
                                          actual=rx_stream_result_framecount_dport,
                                          message="Comparing tx and rx frame count on Spirent for stream dport")
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_sip.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_sip = int(
                stream_results[self.stream_obj_sip.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_sip = int(
                stream_results[self.stream_obj_sip.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_sip,
                                          actual=rx_stream_result_framecount_sip,
                                          message="Comparing tx and rx frame count on Spirent for stream sip")
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_dip.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_dip = int(
                stream_results[self.stream_obj_dip.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_dip = int(
                stream_results[self.stream_obj_dip.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_dip,
                                          actual=rx_stream_result_framecount_dip,
                                          message="Comparing tx and rx frame count on Spirent for stream dip")

            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_tcpflag.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_tcpflag = int(
                stream_results[self.stream_obj_tcpflag.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_tcpflag = int(
                stream_results[self.stream_obj_tcpflag.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_tcpflag,
                                          actual=rx_stream_result_framecount_tcpflag,
                                          message="Comparing tx and rx frame count on Spirent for stream tcpflag")

            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_ecn.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_ecn = int(
                stream_results[self.stream_obj_ecn.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_ecn = int(
                stream_results[self.stream_obj_ecn.spirent_handle]["rx_result"]["FrameCount"])
            # fun_test.test_assert_expected(expected=tx_stream_result_framecount_ecn,
            #                               actual=rx_stream_result_framecount_ecn,
            #                               message="Comparing tx and rx frame count on Spirent for stream ecn")

            acl_stats_tx_before = network_controller_obj.peek_fpg_port_stats(dut_tx_port)
            acl_stats_rx_before = network_controller_obj.peek_fpg_port_stats(dut_rx_port)
            fun_test.log("Port DPC results : ")
            fun_test.log(acl_stats_tx_before)
            fun_test.log(acl_stats_rx_before)
            # Send drop traffic which matches all the fields below
            obj_list.append(self.stream_obj_sport)
            template_obj.deactivate_stream_blocks(stream_obj_list=obj_list)

            del obj_list[:]
            obj_list.append(self.stream_obj_drop)
            template_obj.activate_stream_blocks(stream_obj_list=obj_list)

            counter_bef = get_flex_counter_values(network_controller_obj=network_controller_obj,
                                             counter_id=acl_fields_dict_ipv6_hnu_hnu['counter_id'])

            checkpoint = "Start traffic from %s port for %d secs stream sip" % (tx_port, TRAFFIC_DURATION)
            result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
            fun_test.simple_assert(expression=result, message=checkpoint)

            fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION + 2)
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_drop.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_drop = int(
                stream_results[self.stream_obj_drop.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_drop = int(
                stream_results[self.stream_obj_drop.spirent_handle]["rx_result"]["FrameCount"])

            counter_after = get_flex_counter_values(network_controller_obj=network_controller_obj,
                                               counter_id=acl_fields_dict_ipv6_hnu_hnu['counter_id'])

            fun_test.log("tx_streamcount" + str(tx_stream_result_framecount_drop))
            checkpoint="Comparing tx and rx frame count on Spirent for stream drop. No pkt shuold be transmitted"
            fun_test.test_assert_expected(expected=0, actual=rx_stream_result_framecount_drop,
                                          message=checkpoint)
            # add counter values with the stream value using : peek_fwd_flex_stats
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_drop,
                                          actual=(counter_after - counter_bef),
                                          message="Packets dropped should be equal to counter value")
            rx_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
                port_handle=rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
            checkpoint = "Ensure no errors are seen on Rx spirent port"
            result = template_obj.check_non_zero_error_count(rx_results=rx_port_result)
            fun_test.test_assert(result['result'], checkpoint)

    def cleanup(self):
        dut_rx_port = dut_config['ports'][0]

        checkpoint = "Delete the streams"
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_sport.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_dport.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_sip.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_dip.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_drop.spirent_handle])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)


class AclIPv6HNUtoNU(FunTestCase):
    l2_config = None
    l3_config = None
    routes_config = None
    stream_obj_sport = None
    stream_obj_dport = None
    stream_obj_sip = None
    stream_obj_dip = None
    stream_obj_drop = None
    stream_obj_tcpflag = None
    stream_obj_ecn = None
    capture_results = None

    def describe(self):
        self.set_test_details(id=9, summary="Test IPv6 ACL HNU to HNU",
                              steps="""
                                 1. Create TCP frame stream on Tx Port
                                 2. Start Traffic for %d secs
                                 3. Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count 
                                 4. Ensure on spirent Tx port frames must be equal to Rx port frames
                                 5. Ensure no errors are seen on spirent ports
                                 """ % TRAFFIC_DURATION)

    def setup(self):
        global dut_rx_port, dut_tx_port
        self.routes_config = nu_config_obj.get_traffic_routes_by_chassis_type(spirent_config=spirent_config,
                                                                              ip_version="ipv6")
        fun_test.simple_assert(self.routes_config, "Ensure routes config fetched")
        self.l3_config = self.routes_config['l3_config']
        # Multiple streams for seding packets with different fields
        checkpoint = "Creating multiple streams on %s port" % hnu_ing_port

        self.stream_obj_sport = create_streams(tx_port=hnu_ing_port, ipv6=True, dip=self.l3_config['destination_ip1'],
                                               sip=acl_fields_dict_ipv6_hnu_nu['source_ip'],
                                               dmac=self.routes_config['routermac'],
                                               s_port=1024, d_port=acl_fields_dict_ipv6_hnu_nu['dest_port'])

        self.stream_obj_dport = create_streams(tx_port=hnu_ing_port, ipv6=True, dip=self.l3_config['destination_ip1'],
                                               sip=acl_fields_dict_ipv6_hnu_nu['source_ip'],
                                               dmac=self.routes_config['routermac'],
                                               s_port=acl_fields_dict_ipv6_hnu_nu['source_port'], d_port=1024)

        self.stream_obj_sip = create_streams(tx_port=hnu_ing_port, ipv6=True, dip=self.l3_config['destination_ip1'],
                                             sip="3001::1", dmac=self.routes_config['routermac'],
                                             s_port=acl_fields_dict_ipv6_hnu_nu['source_port'],
                                             d_port=acl_fields_dict_ipv6_hnu_nu['dest_port'])

        self.stream_obj_dip = create_streams(tx_port=hnu_ing_port, ipv6=True,
                                             dip=acl_fields_dict_ipv6_hnu_nu['wrong_dip'],
                                             sip=acl_fields_dict_ipv6_hnu_nu['source_ip'],
                                             dmac=self.routes_config['routermac'],
                                             s_port=acl_fields_dict_ipv6_hnu_nu['source_port'],
                                             d_port=acl_fields_dict_ipv6_hnu_nu['dest_port'])

        self.stream_obj_tcpflag = create_streams(tx_port=hnu_ing_port, ipv6=True, dip=self.l3_config['destination_ip1'],
                                                 sip=acl_fields_dict_ipv6_hnu_nu['source_ip'],
                                                 dmac=self.routes_config['routermac'],
                                                 s_port=acl_fields_dict_ipv6_hnu_nu['source_port'],
                                                 d_port=acl_fields_dict_ipv6_hnu_nu['dest_port'],
                                                 sync_bit=acl_fields_dict_ipv6_hnu_nu['tcp_sync_bit'])

        self.stream_obj_ecn = create_streams(tx_port=hnu_ing_port, ipv6=True,
                                             dip=self.l3_config['destination_ip1'],
                                             sip=acl_fields_dict_ipv6_hnu_nu['source_ip'],
                                             dmac=self.routes_config['routermac'],
                                             s_port=acl_fields_dict_ipv6_hnu_nu['source_port'],
                                             d_port=acl_fields_dict_ipv6_hnu_nu['dest_port'],
                                             sync_bit=acl_fields_dict_ipv6_hnu_nu['tcp_sync_bit'],
                                             ack_bit=acl_fields_dict_ipv6_hnu_nu['tcp_ack_bit'], v6_traffic_class=4)

        self.stream_obj_drop = create_streams(tx_port=hnu_ing_port, ipv6=True,
                                              dip=self.l3_config['destination_ip1'],
                                              sip=acl_fields_dict_ipv6_hnu_nu['source_ip'],
                                              dmac=self.routes_config['routermac'],
                                              s_port=acl_fields_dict_ipv6_hnu_nu['source_port'],
                                              d_port=acl_fields_dict_ipv6_hnu_nu['dest_port'],
                                              sync_bit=acl_fields_dict_ipv6_hnu_nu['tcp_sync_bit'],
                                              ack_bit=acl_fields_dict_ipv6_hnu_nu['tcp_ack_bit'],
                                              v6_traffic_class=2)

        dut_rx_port = dut_config['ports'][2]
        dut_tx_port = dut_config['ports'][1]

    def run(self):
        tx_port = hnu_ing_port
        rx_port = nu_eg_port
        checkpoint = "Clear FPG port stats on DUT"
        c = 0
        for port_num in dut_config['ports']:
            if c == 1:
                shape = 0
                result = network_controller_obj.clear_port_stats(port_num=port_num, shape=shape)
                fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
            elif c == 2:
                shape = 1
                result = network_controller_obj.clear_port_stats(port_num=port_num, shape=shape)
                fun_test.simple_assert(result, "Clear FPG stats for port %d" % port_num)
            c += 1
        fun_test.add_checkpoint(checkpoint=checkpoint)

        checkpoint = "Deactivate not required stream blocks"
        obj_list = []
        obj_list.append(self.stream_obj_dip)
        obj_list.append(self.stream_obj_dport)
        obj_list.append(self.stream_obj_sip)
        obj_list.append(self.stream_obj_tcpflag)
        obj_list.append(self.stream_obj_drop)
        obj_list.append(self.stream_obj_ecn)
        template_obj.deactivate_stream_blocks(stream_obj_list=obj_list)
        del obj_list[:]
        obj_list.append(self.stream_obj_sport)
        template_obj.activate_stream_blocks(stream_obj_list=obj_list)

        checkpoint = "Start traffic from %s port for %d secs" % (tx_port, TRAFFIC_DURATION)
        result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
        fun_test.simple_assert(expression=result, message=checkpoint)

        fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION + 2)

        checkpoint = "Fetch Rx Port Results for %s" % rx_port
        rx_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
            port_handle=rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
        fun_test.simple_assert(expression=rx_port_result, message=checkpoint)

        dut_rx_port_results = network_controller_obj.peek_fpg_port_stats(dut_rx_port, hnu=True)
        fun_test.simple_assert(dut_rx_port_results, "Fetch DUT Rx port results. FPG%d" % dut_rx_port)

        dut_tx_port_results = network_controller_obj.peek_fpg_port_stats(dut_tx_port)
        fun_test.simple_assert(dut_tx_port_results, "Fetch DUT Tx port results. FPG%d" % dut_tx_port)

        fun_test.log("DUT Rx Port %d Results: %s" % (dut_rx_port, dut_rx_port_results))
        fun_test.log("DUT Tx Port %d Results: %s" % (dut_tx_port, dut_tx_port_results))

        checkpoint = "Validate FPG ports stats ensure Tx frame count must be equal to Rx frame count"
        frames_received = get_dut_output_stats_value(result_stats=dut_rx_port_results, stat_type=FRAMES_RECEIVED_OK,
                                                     tx=False)
        frames_transmitted = get_dut_output_stats_value(result_stats=dut_tx_port_results,
                                                        stat_type=FRAMES_TRANSMITTED_OK)
        fun_test.log("Frames Received on FPG%s: %s and Frames Transmitted on FPG%s: %s" % (
            dut_rx_port, frames_received, dut_tx_port, frames_transmitted))

        fun_test.test_assert_expected(expected=frames_received, actual=frames_transmitted, message=checkpoint)

        # Validate Spirent stats
        stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                            [self.stream_obj_sport.spirent_handle],
                                                                            tx_result=True, rx_result=True)
        tx_stream_result_framecount_sport = int(
            stream_results[self.stream_obj_sport.spirent_handle]["tx_result"]["FrameCount"])
        rx_stream_result_framecount_sport = int(
            stream_results[self.stream_obj_sport.spirent_handle]["rx_result"]["FrameCount"])
        fun_test.test_assert_expected(expected=tx_stream_result_framecount_sport,
                                      actual=rx_stream_result_framecount_sport,
                                      message="Comparing tx and rx frame count on Spirent for stream sip")

        checkpoint = "Ensure no errors are seen on Rx spirent port"
        result = template_obj.check_non_zero_error_count(rx_results=rx_port_result)
        fun_test.test_assert(result['result'], checkpoint)

        if frames_received == frames_transmitted:
            del obj_list[:]
            obj_list.append(self.stream_obj_sport)
            obj_list.append(self.stream_obj_drop)
            template_obj.deactivate_stream_blocks(stream_obj_list=obj_list)

            del obj_list[:]
            obj_list.append(self.stream_obj_dport)
            obj_list.append(self.stream_obj_sip)
            obj_list.append(self.stream_obj_dip)
            obj_list.append(self.stream_obj_tcpflag)
            obj_list.append(self.stream_obj_ecn)
            template_obj.activate_stream_blocks(stream_obj_list=obj_list)

            checkpoint = "Start traffic from %s port for %d secs streams dport,sip,dip,ecn,tcpflag" % (
            tx_port, TRAFFIC_DURATION)
            result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
            fun_test.simple_assert(expression=result, message=checkpoint)

            fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION + 5)
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_dport.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_dport = int(
                stream_results[self.stream_obj_dport.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_dport = int(
                stream_results[self.stream_obj_dport.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_dport,
                                          actual=rx_stream_result_framecount_dport,
                                          message="Comparing tx and rx frame count on Spirent for stream dport")
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_sip.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_sip = int(
                stream_results[self.stream_obj_sip.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_sip = int(
                stream_results[self.stream_obj_sip.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_sip,
                                          actual=rx_stream_result_framecount_sip,
                                          message="Comparing tx and rx frame count on Spirent for stream sip")
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_dip.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_dip = int(
                stream_results[self.stream_obj_dip.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_dip = int(
                stream_results[self.stream_obj_dip.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_dip,
                                          actual=rx_stream_result_framecount_dip,
                                          message="Comparing tx and rx frame count on Spirent for stream dip")

            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_tcpflag.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_tcpflag = int(
                stream_results[self.stream_obj_tcpflag.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_tcpflag = int(
                stream_results[self.stream_obj_tcpflag.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_tcpflag,
                                          actual=rx_stream_result_framecount_tcpflag,
                                          message="Comparing tx and rx frame count on Spirent for stream tcpflag")

            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_ecn.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_ecn = int(
                stream_results[self.stream_obj_ecn.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_ecn = int(
                stream_results[self.stream_obj_ecn.spirent_handle]["rx_result"]["FrameCount"])
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_ecn,
                                          actual=rx_stream_result_framecount_ecn,
                                          message="Comparing tx and rx frame count on Spirent for stream tcpflag")

            acl_stats_tx_before = network_controller_obj.peek_fpg_port_stats(dut_tx_port)
            acl_stats_rx_before = network_controller_obj.peek_fpg_port_stats(dut_rx_port)
            fun_test.log("Port DPC results : ")
            fun_test.log(acl_stats_tx_before)
            fun_test.log(acl_stats_rx_before)
            # Send drop traffic which matches all the fields below
            obj_list.append(self.stream_obj_sport)
            template_obj.deactivate_stream_blocks(stream_obj_list=obj_list)

            del obj_list[:]
            obj_list.append(self.stream_obj_drop)
            template_obj.activate_stream_blocks(stream_obj_list=obj_list)

            counter_bef = get_flex_counter_values(network_controller_obj=network_controller_obj,
                                             counter_id=acl_fields_dict_ipv6_hnu_nu['counter_id'])

            checkpoint = "Start traffic from %s port for %d secs stream sip" % (tx_port, TRAFFIC_DURATION)
            result = template_obj.enable_generator_configs(generator_configs=[generator_port_obj_dict[tx_port]])
            fun_test.simple_assert(expression=result, message=checkpoint)

            fun_test.sleep("Traffic to complete", seconds=TRAFFIC_DURATION + 2)
            stream_results = template_obj.stc_manager.fetch_streamblock_results(subscribed_results,
                                                                                [self.stream_obj_drop.spirent_handle],
                                                                                tx_result=True, rx_result=True)
            tx_stream_result_framecount_drop = int(
                stream_results[self.stream_obj_drop.spirent_handle]["tx_result"]["FrameCount"])
            rx_stream_result_framecount_drop = int(
                stream_results[self.stream_obj_drop.spirent_handle]["rx_result"]["FrameCount"])

            counter_after = get_flex_counter_values(network_controller_obj=network_controller_obj,
                                                    counter_id=acl_fields_dict_ipv6_hnu_nu['counter_id'])

            fun_test.log("tx_streamcount" + str(tx_stream_result_framecount_drop))
            checkpoint="Comparing tx and rx frame count on Spirent for stream drop. No pkt shuold be transmitted"
            fun_test.test_assert_expected(expected=0, actual=rx_stream_result_framecount_drop,
                                          message=checkpoint)
            # add counter values with the stream value using : peek_fwd_flex_stats
            fun_test.test_assert_expected(expected=tx_stream_result_framecount_drop,
                                          actual=(counter_after - counter_bef),
                                          message="Packets dropped should be equal to counter value")
            rx_port_result = template_obj.stc_manager.get_rx_port_analyzer_results(
                port_handle=rx_port, subscribe_handle=subscribed_results['analyzer_subscribe'])
            checkpoint = "Ensure no errors are seen on Rx spirent port"
            result = template_obj.check_non_zero_error_count(rx_results=rx_port_result)
            fun_test.test_assert(result['result'], checkpoint)

    def cleanup(self):
        dut_rx_port = dut_config['ports'][0]

        checkpoint = "Delete the streams"
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_sport.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_dport.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_sip.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_dip.spirent_handle])
        template_obj.delete_streamblocks(streamblock_handle_list=[self.stream_obj_drop.spirent_handle])
        fun_test.add_checkpoint(checkpoint)

        checkpoint = "Clear subscribed results"
        template_obj.clear_subscribed_results(subscribe_handle_list=subscribed_results.values())
        fun_test.add_checkpoint(checkpoint)


if __name__ == '__main__':
    ts = SpirentSetup()
    ts.add_test_case(AclIngressDropNUtoNU())
    ts.add_test_case(AclIPv6NUtoNU())
    ts.add_test_case(AclQosTCNuNu())
    ts.add_test_case(AclEgressDropNUtoHNU())
    ts.add_test_case(AclIngressDropHNUtoHNU())
    ts.add_test_case(AclEgressDropHNUtoNU())
    ts.add_test_case(AclIPv6NUtoHNU())
    ts.add_test_case(AclIPv6HNUtoHNU())
    ts.add_test_case(AclIPv6HNUtoNU())
    ts.run()
