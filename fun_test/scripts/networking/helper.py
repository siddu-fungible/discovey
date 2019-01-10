from lib.system.fun_test import *
import re

FRAMES_RECEIVED_OK = "aFramesReceivedOK"
FRAMES_TRANSMITTED_OK = "aFramesTransmittedOK"
OCTETS_RECEIVED_OK = "OctetsReceivedOK"
OCTETS_TRANSMITTED_OK = "OctetsTransmittedOK"
FRAME_TOO_LONG_ERRORS = "aFrameTooLongErrors"
ETHER_STATS_JABBERS = "etherStatsJabbers"
ETHER_STATS_PKTS = "etherStatsPkts"
ETHER_STATS_OVERSIZE_PKTS = "etherStatsOversizePkts"
ETHER_STATS_UNDERSIZE_PKTS = "etherStatsUndersizePkts"
ETHER_STATS_OCTETS = "etherStatsOctets"
ETHER_STATS_PKTS_64_OCTETS = "etherStatsPkts64Octets"
ETHER_STATS_PKTS_65_TO_127_OCTETS = "etherStatsPkts65to127Octets"
ETHER_STATS_PKTS_128_TO_255_OCTETS = "etherStatsPkts128to255Octets"
ETHER_STATS_PKTS_256_TO_511_OCTETS = "etherStatsPkts256to511Octets"
ETHER_STATS_PKTS_512_TO_1023_OCTETS = "etherStatsPkts512to1023Octets"
ETHER_STATS_PKTS_1024_TO_1518_OCTETS = "etherStatsPkts1024to1518Octets"
ETHER_STATS_PKTS_1519_TO_MAX_OCTETS = "etherStatsPkts1519toMaxOctets"
IF_IN_ERRORS = "ifInErrors"
IF_IN_UCAST_PKTS = "ifInUcastPkts"
IF_OUT_ERRORS = "ifOutErrors"
IF_OUT_UCAST_PKTS = "ifOutUcastPkts"
IF_IN_BROADCAST_PKTS = "ifInBroadcastPkts"
CBFC_PAUSE_FRAMES_RECEIVED = "CBFCPAUSEFramesReceived"
CBFC_PAUSE_FRAMES_TRANSMITTED = "CBFCPAUSEFramesTransmitted"
PAUSE_MAC_CONTROL_FRAMES_TRANSMITTED = "aPAUSEMACCtrlFramesTransmitted"
PAUSE_MAC_CONTROL_FRAMES_RECEIVED = "aPAUSEMACCtrlFramesReceived"
FRAME_CHECK_SEQUENCE_ERROR = "aFrameCheckSequenceErrors"
CLASS_0 = "0"
CLASS_1 = "1"
CLASS_2 = "2"
VP_PACKETS_TOTAL_IN = "vp_packets_total_in"
VP_PACKETS_TOTAL_OUT = "vp_packets_total_out"
VP_PACKETS_OUT_HU = "vp_packets_out_hu"
VP_PACKETS_FORWARDING_NU_LE = "vp_packets_forwarding_nu_le"
VP_PACKETS_FORWARDING_NU_DIRECT = "vp_packets_forwarding_nu_direct"
VP_PACKETS_NU_OUT_ETP = "vp_packets_out_nu_etp"
VP_FAE_REQUESTS_SENT = "vp_fae_requests_sent"
VP_FAE_RESPONSES_RECEIVED = "vp_fae_responses_received"
VP_PACKETS_CONTROL_T2C_COUNT = "vp_packets_control_t2c"
VP_PACKETS_CC_OUT = "vp_packets_out_cc"
ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED = "count_for_all_non_fcp_packets_received"
ERP_COUNT_FOR_EFP_WQM_DECREMENT_PULSE = "count_for_efp_to_wqm_decrement_pulse"
ERP_COUNT_FOR_EFP_WRO_DESCRIPTORS_SENT = "count_for_efp_to_wro_descriptors_sent"
ERP_COUNT_FOR_ERP0_EFP_ERROR_INTERFACE_FLITS = "count_for_erp0_to_efp_error_interface_flits"
ERP_COUNT_FOR_EFP_FCP_VLD = "count_for_efp_to_fcb_vld"
ERP_COUNT_PACKETS_INNER_LAYER4_CS_ERROR = "count_for_packets_with_inner_layer4_cs_error"
ERP_COUNT_PACKETS_OUTER_LAYER4_CS_ERROR = "count_for_packets_with_outer_layer4_cs_error"
ERP_COUNT_PACKETS_INNER_IP_LEN_ERROR = "count_for_packets_with_inner_ip_len_error"
ERP_COUNT_PACKETS_OUTER_IP_LEN_ERROR = "count_for_packets_with_outer_ip_len_error"
WRO_IN_NFCP_PKTS = "wroin_nfcp_pkts"
WRO_IN_PKTS = "wroin_pkts"
WRO_OUT_WUS = "wroout_wus"
WRO_WU_COUNT_VPP = "wrowu_cnt_vpp"
PSW_SAMPLED_PACKET_COUNT = 'sampled_pkt'
PSW_FRV_ERROR_COUNT = "frv_error"
SFG_IN_FFE_DESC = "IN_FFE_DESC"
SFG_OUT_FFE_DESC = "OUT_FFE_DESC"
SFG_OUT_PSW_DESC = "OUT_PSW_DESC"
SFG_SAMPLER_COPY = "SAMPLER_COPY"

# Meter IDs got from copp_static.h file under funcp/networking/asicd/libnu/copp
ETH_COPP_ARP_REQ_METER_ID = 1
ETH_COPP_ARP_RESP_METER_ID = 2
ETH_COPP_ISIS_1_METER_ID = 4
ETH_COPP_ISIS_2_METER_ID = 5
ETH_COPP_LLDP_METER_ID = 6
ETH_COPP_PTP_METER_ID = 7
IPV4_COPP_ICMP_METER_ID = 8
IPV4_COPP_OSPF_1_METER_ID = 9
IPV4_COPP_OSPF_2_METER_ID = 10
IPV4_COPP_DHCP_METER_ID = 11
IPV4_COPP_PIM_METER_ID = 12
IPV4_COPP_BGP_METER_ID = 13
IPV4_COPP_IGMP_METER_ID = 14
IPV4_COPP_PTP_1_METER_ID = 15
IPV4_COPP_PTP_2_METER_ID = 16
IPV4_COPP_PTP_3_METER_ID = 17
IPV4_COPP_PTP_4_METER_ID = 18
IPV4_COPP_TTL_ERR_METER_ID = 19
IPV4_COPP_OPTS_METER_ID = 20
IPV4_COPP_FOR_US_METER_ID = 21
ERR_TRAP_COPP_FSF_METER_ID = 40
ERR_TRAP_COPP_OUTER_CKSUM_ERR_METER_ID = 41
ERR_TRAP_COPP_INNER_CKSUM_ERR_METER_ID = 42
ERR_TRAP_COPP_PRSR_V4_VER_METER_ID = 51
ERR_TRAP_COPP_PRSR_V6_VER_METER_ID = 52
ERR_TRAP_COPP_PRSR_IHL_METER_ID = 53
ERR_TRAP_COPP_PRSR_OL_V4_VER_METER_ID = 54
ERR_TRAP_COPP_PRSR_OL_V6_VER_METER_ID = 55
ERR_TRAP_COPP_PRSR_OL_IHL_METER_ID = 56
ERR_TRAP_COPP_PRSR_IP_FLAG_ZERO_METER_ID = 57


psw_global_stats_counter_names = {'orm_drop': 'orm_drop', 'grm_sx_drop': 'grm_sx_drop',
                                          'grm_sampled_pkt_drop': 'grm_sampled_pkt_drop', 'ct_pkt': 'ct_pkt',
                                          'grm_drop': 'grm_drop', 'grm_fcp_drop': 'grm_fcp_drop',
                                          'irm_drop': 'irm_drop', 'grm_dx_drop': 'grm_dx_drop',
                                          'grm_df_drop': 'grm_df_drop', 'grm_nonfcp_drop': 'grm_nonfcp_drop',
                                          'wred_drop': 'wred_drop', 'grm_sf_drop': 'grm_sf_drop',
                                          'prm_drop': 'prm_drop','cpr_sop_drop_pkt': 'cpr_sop_drop_pkt', 'fwd_frv': 'fwd_frv',
                                            'frv_error': 'frv_error', 'epg1_pkt': 'epg1_pkt',
                                            'ifpg5_pkt': 'ifpg5_pkt', 'ifpg2_pkt': 'ifpg2_pkt',
                                            'main_pkt_drop_eop': 'main_pkt_drop_eop',
                                            'cpr_feop_pkt': 'cpr_feop_pkt', 'ifpg4_pkt': 'ifpg4_pkt',
                                            'epg2_pkt': 'epg2_pkt', 'sampled_pkt': 'sampled_pkt',
                                            'ifpg0_pkt': 'ifpg0_pkt', 'fwd_main_pkt_drop': 'fwd_main_pkt_drop',
                                            'sampled_pkt_drop': 'sampled_pkt_drop', 'ifpg3_pkt': 'ifpg3_pkt',
                                            'epg0_pkt': 'epg0_pkt', 'ifpg1_pkt': 'ifpg1_pkt','fpg3_err_pkt': 'fpg3_err_pkt', 'fpg1_pkt': 'fpg1_pkt',
                                             'fpg5_pkt': 'fpg5_pkt', 'fpg4_err_pkt': 'fpg4_err_pkt',
                                             'fpg3_pkt': 'fpg3_pkt', 'fpg0_err_pkt': 'fpg0_err_pkt',
                                             'purge_pkt': 'purge_pkt', 'fpg2_err_pkt': 'fpg2_err_pkt',
                                             'fpg1_err_pkt': 'fpg1_err_pkt', 'fpg4_pkt': 'fpg4_pkt',
                                             'epg2_pkt': 'epg2_pkt', 'epg1_pkt': 'epg1_pkt', 'fpg2_pkt': 'fpg2_pkt',
                                             'fpg5_err_pkt': 'fpg5_err_pkt', 'fpg0_pkt': 'fpg0_pkt',
                                             'epg0_pkt': 'epg0_pkt'}


def __get_class_based_counter_stats_value(result_stats, stat_type, tx, class_value):
    result = None
    output = result_stats[0]
    for key in output.iterkeys():
        if len(key.split('_')) > 5:
            if stat_type == key.split('_')[4] and str(class_value) == key.split('_')[5]:
                if tx:
                    if not 'TX' == key.split('_')[3]:
                        continue
                    result = output[key]
                    break
                elif 'RX' == key.split('_')[3]:
                    result = output[key]
                    break
    return result


def get_dut_output_stats_value(result_stats, stat_type, tx=True, class_value=None):
    result = None
    try:
        if stat_type == CBFC_PAUSE_FRAMES_RECEIVED or stat_type == CBFC_PAUSE_FRAMES_TRANSMITTED:
            result = __get_class_based_counter_stats_value(result_stats, stat_type, tx, class_value)
            return result
        output = result_stats[0]
        for key in output.iterkeys():
            if len(key.split('_')) > 4:
                if stat_type == key.split('_')[4]:
                    if tx:
                        if not 'TX' == key.split('_')[3]:
                            continue
                        result = output[key]
                        break
                    elif 'RX' == key.split('_')[3]:
                        result = output[key]
                        break
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def get_dut_fpg_port_stats(network_controller_obj, dut_port_list=[], hnu=False):
    result_dict = {}
    try:
        for port in dut_port_list:
            result_dict[port] = network_controller_obj.peek_fpg_port_stats(port, hnu=hnu)
    except Exception as ex:
        fun_test.critical(str(ex))
    return result_dict


def get_fpg_port_value(dut_port_number):
    result = None
    try:
        operator_value = 4
        if (int(dut_port_number) % operator_value) == 0:
            result = (int(dut_port_number) / operator_value) - 1
        else:
            result = int(dut_port_number) / operator_value
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def get_psw_global_stats_values(psw_stats_output={}, input=False, input_key_list=[], output=False, output_key_list=[],
                                prm=False, prm_key_list=[]):
    result = {}
    try:
        if input:
            result['input'] = {}
            for key in input_key_list:
                result['input'][key] = None
                if psw_global_stats_counter_names.has_key(key):
                    parsed_psw_stats_output = psw_stats_output['global']['input']
                    for key1, val1 in parsed_psw_stats_output.iteritems():
                            if key1 == key:
                                result['input'][key] = val1
                                break
                else:
                    fun_test.log("Key %s not found input section in psw_stats_counter_name" % key)

        if output:
            result['output'] = {}
            for key in output_key_list:
                result['output'][key] = None
                if psw_global_stats_counter_names.has_key(key):
                    parsed_psw_stats_output = psw_stats_output['global']['output']
                    for key1, val1 in parsed_psw_stats_output.iteritems():
                            if key1 == key:
                                result['output'][key] = val1
                                break
                else:
                    fun_test.log("Key %s not found output section in psw_stats_counter_name" % key)
        if prm:
            result['prm'] = {}
            for key in prm_key_list:
                result['prm'][key] = None
                if psw_global_stats_counter_names.has_key(key):
                    parsed_psw_stats_output = psw_stats_output['global']['prm']
                    for key1, val1 in parsed_psw_stats_output.iteritems():
                            if key1 == key:
                                result['prm'][key] = val1
                                break
                else:
                    fun_test.log("Key %s not found prm section in psw_stats_counter_name" % key)

    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def parse_result_dict(result_dict):
    result = {}
    try:
        for key, val in result_dict.iteritems():
            if isinstance(val, dict):
                result[key] = parse_result_dict(val)
            else:
                new_key = re.sub('[()]', '', key)
                new_key = new_key.replace(' ', '_').lower()
                result[new_key] = val
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def get_vp_pkts_stats_values(network_controller_obj):
    result = None
    try:
        output = network_controller_obj.peek_vp_packets()
        fun_test.simple_assert(output, "Ensure vp packet stats are grepped")
        result = parse_result_dict(output)
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def get_bam_stats_values(network_controller_obj):
    result = None
    try:
        output = network_controller_obj.peek_bam_stats()
        fun_test.simple_assert(output, "Ensure bam stats are grepped")
        result = parse_result_dict(output)
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def get_erp_stats_values(network_controller_obj, hnu=False, flex=False):
    result = None
    try:
        output = network_controller_obj.peek_erp_global_stats(hnu=hnu, flex=flex)
        fun_test.simple_assert(output, "Ensure bam stats are grepped")
        result = parse_result_dict(output)
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def get_wro_global_stats_values(network_controller_obj):
    result = None
    try:
        wro_stats = network_controller_obj.peek_wro_global_stats()
        fun_test.simple_assert(wro_stats, "Ensure WRO Global stats fetched")
        result = parse_result_dict(wro_stats)
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def validate_parser_stats(parser_result, compare_value, check_list_keys=[], parser_old_result=None):
    result = False
    try:
        stat_counter_list = ['prv_sent', 'eop_cnt', 'sop_cnt']
        for key in check_list_keys:
            current_dict = parser_result['global'][key]
            for counter in stat_counter_list:
                actual = int(current_dict[counter])
                if parser_old_result:
                    old_dict = parser_old_result['global'][key]
                    if counter in old_dict:
                        actual = int(current_dict[counter]) - int(old_dict[counter])
                    else:
                        actual = int(current_dict[counter])
                fun_test.test_assert_expected(expected=compare_value, actual=actual,
                                              message="Check %s stats for %s in parser nu stats" % (counter, key))
        result = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def get_vp_per_pkts_stats_values(network_controller_obj):
    result = None
    try:
        output = network_controller_obj.peek_per_vppkts_stats()
        fun_test.simple_assert(output, "Ensure vp per packet stats are grepped")
        result = parse_result_dict(output)
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def get_diff_stats(old_stats, new_stats, stats_list=[]):
    result = {}
    try:
        if stats_list:
            for stat in stats_list:
                fun_test.simple_assert(stat in new_stats, "Stat %s not present in new stats" % stat)
                if (stat in old_stats) and (old_stats[stat] is not None):
                    result[stat] = int(new_stats[stat]) - int(old_stats[stat])
                else:
                    result[stat] = int(new_stats[stat])
        else:
            for key, val in new_stats.iteritems():
                if isinstance(val, dict):
                    result[key] = get_diff_stats(old_stats=old_stats[key], new_stats=new_stats[key])
                elif key in old_stats:
                    try:
                        result[key] = int(new_stats[key]) - int(old_stats[key])
                    except TypeError:
                        result[key] = None
                else:
                    try:
                        result[key] = int(new_stats[key])
                    except TypeError:
                        result[key] = None
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def verify_spirent_stats(result_dict):
    for stream_key in result_dict.iterkeys():
        fun_test.test_assert_expected(expected=result_dict[stream_key]['tx_result']['FrameCount'],
                                      actual=result_dict[stream_key]['rx_result']['FrameCount'],
                                      message="Check results for %s" % stream_key)
    result = True
    return result


def get_key_to_change(class_dict, priority_val):
    result = None
    for key in class_dict.iterkeys():
        if 'time' in key:
            out = int(filter(str.isdigit, key))
            if out == priority_val:
                result = key
                break
    return result


def find_spirent_rx_counters_stopped(template_obj, subscribe_result, streamblock_handle_list=None, pfc_stream=False,
                                     port_handle=None):
    result_dict = {}
    value_dict = {}
    for i in range(2):        # Get value of rx counter of stream in 2 runs to check if it has stopped or not
        if not pfc_stream:
            value_dict[i] = template_obj.stc_manager.fetch_streamblock_results(subscribe_result=subscribe_result,
                                                                               streamblock_handle_list=streamblock_handle_list,
                                                                               rx_result=True)
        else:
            value_dict[i] = template_obj.stc_manager.fetch_port_results(subscribe_result=subscribe_result,
                                                                               port_handle_list=[port_handle],
                                                                               analyzer_result=True)
        fun_test.sleep("Sleeping 5 seconds", seconds=5)
    if not pfc_stream:
        for stream in streamblock_handle_list:
            result_dict[stream] = None
            old_rx_counter = int(value_dict[0][stream]['rx_result']['FrameCount'])
            new_rx_counter = int(value_dict[1][stream]['rx_result']['FrameCount'])
            fun_test.log("Values of rx counter for stream %s are:- Old: %s ; New: %s" % (stream, old_rx_counter,
                                                                                         new_rx_counter))

            if old_rx_counter < new_rx_counter:
                result_dict[stream] = False
            elif old_rx_counter == new_rx_counter:
                result_dict[stream] = True

    if pfc_stream:
        old_rx_counter = int(value_dict[0][port_handle]['analyzer_result']['TotalFrameCount'])
        new_rx_counter = int(value_dict[1][port_handle]['analyzer_result']['TotalFrameCount'])
        fun_test.log("Values of rx counter for stream %s are:- Old: %s ; New: %s" % (port_handle, old_rx_counter,
                                                                                     new_rx_counter))

        if old_rx_counter < new_rx_counter:
            result_dict[port_handle] = False
        elif old_rx_counter == new_rx_counter:
            result_dict[port_handle] = True

    return result_dict


def get_fpg_port_cbfcpause_counters(network_controller_obj, dut_port, shape, tx=False, hnu=False, priority_list=None):
    output_dict = {}
    if not priority_list:
        priority_list = [x for x in range(16)]
    try:
        stat_type = CBFC_PAUSE_FRAMES_RECEIVED
        if tx:
            stat_type = CBFC_PAUSE_FRAMES_TRANSMITTED
        out = network_controller_obj.clear_port_stats(dut_port, shape=shape)
        fun_test.simple_assert(out, "Clear port stats on dut port %s" % dut_port)
        fun_test.sleep('Stats clear', seconds=2)
        stats = network_controller_obj.peek_fpg_port_stats(dut_port, hnu=hnu)
        fun_test.simple_assert(stats, "Fpg stats on port %s" % dut_port)

        for priority in priority_list:
            output_dict[priority] = False
            value = get_dut_output_stats_value(stats, stat_type=stat_type,
                                               tx=tx, class_value=priority)
            if value:
                fun_test.log("Value seen for priority %s is %s" % (priority, value))
                output_dict[priority] = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return output_dict


def get_fpg_port_pause_mac_ctrl_counters(network_controller_obj, dut_port, shape, tx=False, hnu=False):
    output = False
    try:
        stat_type = PAUSE_MAC_CONTROL_FRAMES_RECEIVED
        if tx:
            stat_type = PAUSE_MAC_CONTROL_FRAMES_TRANSMITTED
        output = False
        out = network_controller_obj.clear_port_stats(dut_port, shape=shape)
        fun_test.simple_assert(out, "Clear port stats on dut port %s" % dut_port)
        fun_test.sleep('Stats clear', seconds=2)
        stats = network_controller_obj.peek_fpg_port_stats(dut_port, hnu=hnu)
        fun_test.simple_assert(stats, "Fpg stats on port %s" % dut_port)

        value = get_dut_output_stats_value(stats, stat_type=stat_type, tx=tx)
        if value:
            fun_test.log("Value seen for type %s is %s" % (stat_type, value))
            output = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return output


def get_psw_port_enqueue_dequeue_counters(network_controller_obj, dut_port, hnu, pg=False, priority_list=None):
    output_dict = {}
    if not priority_list:
        priority_list = [x for x in range(16)]
    dequeue = 'dequeue'
    enqueue = 'enqueue'
    if pg:
        q_type = "pg"
        dequeue_type = 'pg_deq'
        enqueue_type = 'pg_enq'
    else:
        q_type = "q"
        dequeue_type = 'q_deq'
        enqueue_type = 'q_enq'
    try:
        stats_1 = network_controller_obj.peek_psw_port_stats(port_num=dut_port, hnu=hnu)
        fun_test.simple_assert(stats_1, "Ensure psw command is executed for 1st time on port %s" % dut_port)

        fun_test.sleep("Letting queries to be executed", seconds=5)

        stats_2 = network_controller_obj.peek_psw_port_stats(port_num=dut_port, hnu=hnu)
        fun_test.simple_assert(stats_2, "Ensure psw command is executed for 2nd time on port %s" % dut_port)

        for queue_num in priority_list:
            output_dict[queue_num] = {}
            output_dict[queue_num][dequeue] = True
            output_dict[queue_num][enqueue] = False
            if len(str(queue_num)) == 1:
                updated_queue = '0' + str(queue_num)
            else:
                updated_queue = str(queue_num)
            q_no = 'q_' + updated_queue

            old_dequeue_val = int(stats_1[q_no]['count'][dequeue_type]['pkts'])
            new_dequeue_val = int(stats_2[q_no]['count'][dequeue_type]['pkts'])
            old_enqueue_val = int(stats_1[q_no]['count'][enqueue_type]['pkts'])
            new_enqueue_val = int(stats_2[q_no]['count'][enqueue_type]['pkts'])

            fun_test.log("Values of %s dequeue seen on %s for queue %s are:- Old: %s ; New: %s" % (q_type, dut_port, q_no,
                                                                                           old_dequeue_val,
                                                                                           new_dequeue_val))
            fun_test.log("Values of %s enqueue seen on %s for queue %s are:- Old: %s ; New: %s" % (q_type, dut_port, q_no,
                                                                                          old_enqueue_val,
                                                                                          new_enqueue_val))

            if old_dequeue_val < new_dequeue_val:
                output_dict[queue_num][dequeue] = True
            elif old_dequeue_val == new_dequeue_val:
                output_dict[queue_num][dequeue] = False

            if old_enqueue_val < new_enqueue_val:
                output_dict[queue_num][enqueue] = True
            elif old_enqueue_val == new_enqueue_val:
                output_dict[queue_num][enqueue] = False

    except Exception as ex:
        fun_test.critical(str(ex))
    return output_dict


def set_strict_priority_on_queue(network_controller_obj, dut_port, set_queue_list):
    result = False
    try:
        full_list = [x for x in range(16)]
        for queue in full_list:
            if queue in set_queue_list:
                output = network_controller_obj.set_qos_scheduler_config(port_num=dut_port, queue_num=queue,
                                                                         strict_priority_enable=True,
                                                                         scheduler_type=network_controller_obj.SCHEDULER_TYPE_STRICT_PRIORITY)
                fun_test.simple_assert(output, "Set strict priority on queue %s on port %s" % (queue, dut_port))
            else:
                output = network_controller_obj.set_qos_scheduler_config(port_num=dut_port, queue_num=queue,
                                                                         strict_priority_enable=False,
                                                                         scheduler_type=network_controller_obj.SCHEDULER_TYPE_STRICT_PRIORITY)
                fun_test.simple_assert(output, "Remove strict priority on queue %s on port %s" % (queue, dut_port))
        result = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def remove_strict_priority_from_queue(network_controller_obj, dut_port):
    result = False
    try:
        full_list = [x for x in range(16)]
        for queue in full_list:
            output = network_controller_obj.set_qos_scheduler_config(port_num=dut_port, queue_num=queue,
                                                                     strict_priority_enable=False,
                                                                     scheduler_type=network_controller_obj.SCHEDULER_TYPE_STRICT_PRIORITY)
            fun_test.simple_assert(output, "Remove strict priority on queue %s on port %s" % (queue, dut_port))
        result = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def convert_bps_to_mbps(count_in_bps):
    count_in_mbps = count_in_bps / float(1000000)
    return count_in_mbps