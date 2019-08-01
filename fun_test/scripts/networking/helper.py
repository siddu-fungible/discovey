from lib.system.fun_test import *
import re
from lib.system.utils import MultiProcessingTasks
from prettytable import PrettyTable
from datetime import datetime

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
IF_OUT_BROADCAST_PKTS = "ifOutBroadcastPkts"
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
VP_PACKETS_NU_LE_LOOKUP_MISS = "vp_packets_nu/le_lookup_miss_"
VP_PACKETS_FORWARDING_NU_LE = "vp_packets_forwarding_nu_le"
VP_PACKETS_FORWARDING_NU_DIRECT = "vp_packets_forwarding_nu_direct"
VP_PACKETS_OUT_NU_ETP = "vp_packets_out_nu_etp"
VP_PACKETS_OUT_HNU_ETP = "vp_packets_out_hnu_etp"
VP_NO_DROP_PACKETS_TO_HNU_ETP = "vp_no_drop_packets_to_hnu_etp"
VP_FAE_REQUESTS_SENT = "vp_fae_requests_sent"
VP_FAE_RESPONSES_RECEIVED = "vp_fae_responses_received"
VP_PACKETS_CONTROL_T2C_COUNT = "vp_packets_control_t2c"
VP_PACKETS_CC_OUT = "vp_packets_out_cc"
VP_PACKETS_SAMPLE = "vp_packets_sample"
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
SFG_SAMPLE_COPY = "SAMPLE_COPY"
FCB_TDP0_NONFCP = "tdp0_nonfcp"
FCB_TDP1_NONFCP = "tdp1_nonfcp"
FCB_TDP2_NONFCP = "tdp2_nonfcp"
FCB_TDP0_DATA = "tdp0_data"
FCB_TDP1_DATA = "tdp1_data"
FCB_TDP2_DATA = "tdp2_data"
FCB_TDP0_GNT = "tdp0_gnt"
FCB_TDP1_GNT = "tdp1_gnt"
FCB_TDP2_GNT = "tdp2_gnt"
FCB_TDP0_REQ = "tdp0_req"
FCB_TDP1_REQ = "tdp1_req"
FCB_TDP2_REQ = "tdp2_req"
FCB_DST_FCP_PKT_RCVD = "FCB_DST_FCP_PKT_RCVD"
FCB_DST_REQ_MSG_RCVD = "FCB_DST_REQ_MSG_RCVD"
FCB_SRC_GNT_MSG_RCVD = "FCB_SRC_GNT_MSG_RCVD"
FCB_SRC_REQ_MSG_XMTD = "FCB_SRC_REQ_MSG_XMTD"

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
        if result < 0:
            result = 0
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


def validate_parser_stats(parser_result, compare_value, check_list_keys=[], parser_old_result=None, match_values=True):
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

                if match_values:
                    fun_test.test_assert_expected(expected=compare_value, actual=actual,
                                                  message="Check %s stats for %s in parser nu stats" % (counter, key))
                else:
                    fun_test.test_assert(compare_value <= actual,
                                         message="Check %s stats for %s in parser nu stats. "
                                                 "Expected %s, Actual %s" % (counter, key, compare_value, actual))
        result = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def get_vp_per_pkts_stats_values(network_controller_obj, cluster_id):
    result = None
    try:
        output = network_controller_obj.peek_per_vppkts_stats(cluster_id=cluster_id)
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


def _get_psw_stat_diff_from_results(stat_1, stat_2, stat_type, stat_name):
    new_val = stat_2[stat_type][stat_name]
    old_val = stat_1[stat_type][stat_name]
    if not new_val:
        new_val = 0
    if not old_val:
        old_val = 0
    return int(new_val) - int(old_val)


def get_psw_diff_counters(hnu_1, hnu_2, input_list=[], output_list=[],
                          psw_stats_nu_1=None, psw_stats_nu_2=None, psw_stats_hnu_1=None,
                          psw_stats_hnu_2=None):
    result = {}
    parsed_psw_stats_1 = None
    parsed_psw_stats_2 = None
    parsed_psw_stats_3 = None
    parsed_psw_stats_4 = None
    if input_list:
        result["input"] = {}
    if output_list:
        result["output"] = {}

    for key in input_list:
        result["input"][key] = 0
    for key in output_list:
        result["output"][key] = 0
    try:
        if hnu_1 and hnu_2:
            parsed_psw_stats_1 = get_psw_global_stats_values(psw_stats_output=psw_stats_hnu_1, input=True,
                                                             input_key_list=input_list, output=True,
                                                             output_key_list=output_list)
            parsed_psw_stats_2 = get_psw_global_stats_values(psw_stats_output=psw_stats_hnu_2, input=True,
                                                             input_key_list=input_list, output=True,
                                                             output_key_list=output_list)
        elif not hnu_1 and not hnu_2:
            parsed_psw_stats_1 = get_psw_global_stats_values(psw_stats_output=psw_stats_nu_1, input=True,
                                                             input_key_list=input_list, output=True,
                                                             output_key_list=output_list)
            parsed_psw_stats_2 = get_psw_global_stats_values(psw_stats_output=psw_stats_nu_2, input=True,
                                                             input_key_list=input_list, output=True,
                                                             output_key_list=output_list)
        elif not hnu_1 and hnu_2:
            parsed_psw_stats_1 = get_psw_global_stats_values(psw_stats_output=psw_stats_nu_1, input=True,
                                                             input_key_list=input_list, output=True,
                                                             output_key_list=output_list)
            parsed_psw_stats_2 = get_psw_global_stats_values(psw_stats_output=psw_stats_nu_2, input=True,
                                                             input_key_list=input_list, output=True,
                                                             output_key_list=output_list)
            parsed_psw_stats_3 = get_psw_global_stats_values(psw_stats_output=psw_stats_hnu_1, output=True,
                                                             output_key_list=output_list, input=True,
                                                             input_key_list=input_list)
            parsed_psw_stats_4 = get_psw_global_stats_values(psw_stats_output=psw_stats_hnu_2,output=True,
                                                             output_key_list=output_list, input=True,
                                                             input_key_list=input_list)
        else:
            parsed_psw_stats_1 = get_psw_global_stats_values(psw_stats_output=psw_stats_hnu_1, input=True,
                                                             input_key_list=input_list, output=True,
                                                             output_key_list=output_list)
            parsed_psw_stats_2 = get_psw_global_stats_values(psw_stats_output=psw_stats_hnu_2, input=True,
                                                             input_key_list=input_list, output=True,
                                                             output_key_list=output_list)
            parsed_psw_stats_3 = get_psw_global_stats_values(psw_stats_output=psw_stats_nu_1, output=True,
                                                             output_key_list=output_list, input=True,
                                                             input_key_list=input_list)
            parsed_psw_stats_4 = get_psw_global_stats_values(psw_stats_output=psw_stats_nu_2, output=True,
                                                             output_key_list=output_list, input=True,
                                                             input_key_list=input_list)

        if parsed_psw_stats_3 and parsed_psw_stats_4:
            # As epg output apeears towards ingress port type and input epg in at egress
            # we need to take appropriate results
            for key in output_list:
                if "epg" in key:
                    result["output"][key] = _get_psw_stat_diff_from_results(parsed_psw_stats_1, parsed_psw_stats_2,
                                                                           stat_type="output", stat_name=key)
                else:
                    result["output"][key] = _get_psw_stat_diff_from_results(parsed_psw_stats_3, parsed_psw_stats_4,
                                                                            stat_type="output", stat_name=key)

            for key in input_list:
                if "epg" in key:
                    result["input"][key] = _get_psw_stat_diff_from_results(parsed_psw_stats_3, parsed_psw_stats_4,
                                                                            stat_type="input", stat_name=key)
                else:
                    result["input"][key] = _get_psw_stat_diff_from_results(parsed_psw_stats_1, parsed_psw_stats_2,
                                                                            stat_type="input", stat_name=key)

        else:
            for key in output_list:
                new_val = parsed_psw_stats_2['output'][key]
                old_val = parsed_psw_stats_1['output'][key]
                if not new_val:
                    new_val = 0
                if not old_val:
                    old_val = 0
                result["output"][key] = int(new_val) - int(old_val)

            for key in input_list:
                new_val = parsed_psw_stats_2['input'][key]
                old_val = parsed_psw_stats_1['input'][key]
                if not new_val:
                    new_val = 0
                if not old_val:
                    old_val = 0
                result["input"][key] = int(new_val) - int(old_val)
        fun_test.log("Counters diff is %s" % result)
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def compare_spray_values(reference_value, actual_value, threshold_percent=10):
    result = False
    threshold_value = int((threshold_percent / 100.0) * reference_value)
    lower_limit = reference_value - threshold_value
    upper_limit = reference_value + threshold_value
    if int(lower_limit) <= int(actual_value) <= (upper_limit):
        result = True
    return result


def check_per_vp_pkt_spray(old_per_vppkt_output_dict, per_vppkt_output_dict, dut_ingress_frame_count, monitor_stats_list):
    result = False
    try:
        output = {}
        ref_val = "ref_val"
        total_pkts_sent = int(dut_ingress_frame_count)
        fun_test.log("Total packets sent %s on ingress" % total_pkts_sent)
        total_vps = len(per_vppkt_output_dict)
        fun_test.log("Total vps present %s" % total_vps)
        reference_value = int(total_pkts_sent / total_vps)
        fun_test.log("Reference value calculated %s" % reference_value)
        for key, val in per_vppkt_output_dict.iteritems():
            vp_number = str(key.split(":")[1])
            output[vp_number] = {}
            fun_test.log("=========== Capturing stats for vp number %s ===========")
            fun_test.log("Refference value is %s" % reference_value)
            output[vp_number][ref_val] = reference_value

            for stat in monitor_stats_list:
                if stat in val:
                    total_count = int(val[stat])
                    if stat in old_per_vppkt_output_dict[key]:
                        total_count = int(val[stat]) - int(old_per_vppkt_output_dict[key][stat])
                    output[vp_number][stat] = total_count
                    fun_test.log("Value seen for %s is %s" % (stat, total_count))
                else:
                    fun_test.critical("Stat %s not seen in per vp pkts stats" % stat)

        for key, val in output.iteritems():
            fun_test.log("xxxxxxxxxxx Checks on vp number %s xxxxxxxxxx" % str(key))
            for stat in monitor_stats_list:

                fun_test.test_assert(compare_spray_values(output[key][ref_val], output[key][stat]),
                                     "Check counter for %s. Expected value: %s Actual value %s for vp %s" %
                                     (stat, reference_value, output[key][stat], key))
        result = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def ensure_dpcsh_ready(network_controller_obj, max_time=180):
    status = False
    try:
        timer = FunTimer(max_time=max_time)
        while not timer.is_expired():
            fun_test.sleep("DPCsh to come up", seconds=30)
            mtu = network_controller_obj.get_port_mtu(port_num=1, shape=0)
            if mtu:
                fun_test.log("MTU set on port 1: %s" % mtu)
                level_changed = network_controller_obj.set_syslog_level(level=3)
                fun_test.simple_assert(level_changed, "Changed Syslog level to 3")
                status = True
                break
    except Exception as ex:
        fun_test.critical(str(ex))
    return status


def get_flex_counter_values(network_controller_obj, counter_id, erp=False):
    counter_value = 0
    try:
        if erp:
            counterstats = network_controller_obj.peek_erp_flex_stats(counter_num=counter_id)
            fun_test.log("counterstat value : %s " % counterstats)
            counter_value = int(counterstats['bank1']['pkts'])
            fun_test.log("Counter %s value : %s" % (counter_id, counter_value))
        else:
            counterstats = network_controller_obj.peek_fwd_flex_stats(counter_num=counter_id)
            fun_test.log("counterstat value : %s " % counterstats)
            counter_value = int(counterstats['bank2']['pkts'])
            fun_test.log("Counter %s value : %s" % (counter_id, counter_value))
    except Exception as ex:
        fun_test.critical(str(ex))
    return counter_value


def get_qos_stats(network_controller_obj, queue_no, dut_port, queue_type='pg_deq', hnu=False):
    qos_val = 0
    try:
        if queue_no<10:
            queue_num = "0"+str(queue_no)
        else:
            queue_num=str(queue_no)
        stats = network_controller_obj.peek_psw_port_stats(port_num=dut_port, hnu=hnu, queue_num=queue_num)
        fun_test.simple_assert(stats, "Ensure psw command is executed on port %s" % dut_port)
        if stats:
            qos_val = int(stats['count'][queue_type]['pkts'])
        else:
            qos_val = 0
    except Exception as ex:
        fun_test.critical(str(ex))
    return qos_val

def get_timestamp():
    ts = time.time()
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def get_nested_dict_stats(result):
    master_table_obj = PrettyTable()
    master_table_obj.align = 'l'
    master_table_obj.border = False
    master_table_obj.header = False
    try:
        for key in sorted(result):
            table_obj = PrettyTable(['Field Name', 'Counter'])
            table_obj.align = 'l'
            for _key in sorted(result[key]):
                if isinstance(result[key][_key], dict):
                    table_obj = PrettyTable()
                    table_obj.align = 'l'
                    inner_table_obj = PrettyTable(['Field Name', 'Counter'])
                    inner_table_obj.align = 'l'
                    for _key1 in sorted(result[key][_key]):
                        inner_table_obj.add_row([_key1, result[key][_key][_key1]])
                    table_obj.add_row([_key, inner_table_obj])
                table_obj.add_row([_key, result[key][_key]])
            master_table_obj.add_row([key, table_obj])
    except Exception as ex:
        fun_test.critical(str(ex))
    return master_table_obj


def get_single_dict_stats(result):
    master_table_obj = PrettyTable(['Field Name', 'Counter'])
    master_table_obj.align = 'l'
    master_table_obj.border = True
    master_table_obj.header = True
    try:
        for key in sorted(result):
            master_table_obj.add_row([key, result[key]])
    except Exception as ex:
        fun_test.critical(str(ex))
    return master_table_obj


def populate_pc_resource_output_file(network_controller_obj, filename, pc_id, display_output=False):
    output = False
    try:
        lines = list()

        result = network_controller_obj.peek_resource_pc_stats(pc_id=pc_id)
        master_table_obj = get_nested_dict_stats(result=result)
        lines.append("\n########################  %s ########################\n" % str(get_timestamp()))
        lines.append(master_table_obj.get_string())
        lines.append('\n\n\n')

        with open(filename, 'a') as f:
            f.writelines(lines)

        description = "Resource pc %s" % pc_id
        fun_test.add_auxillary_file(description=description, filename=filename)

        if display_output:
            fun_test.log_disable_timestamps()
            fun_test.log_section("PC Resource result for id: %d" % pc_id)
            for line in lines:
                fun_test.log(line)
            fun_test.log_enable_timestamps()
        output = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return output

def populate_vp_util_output_file(network_controller_obj, filename, display_output=False):
    output = False
    try:
        filtered_dict = {}
        lines = list()

        result = network_controller_obj.debug_vp_util()
        for key, val in sorted(result.iteritems()):
            if "CCV1" in key or "CCV2" in key:
                filtered_dict[key] = val
        master_table_obj = get_single_dict_stats(result=filtered_dict)
        lines.append("\n########################  %s ########################\n" % str(get_timestamp()))
        lines.append(master_table_obj.get_string())
        lines.append('\n\n\n')

        with open(filename, 'a') as f:
            f.writelines(lines)

        description = "Vp util"
        fun_test.add_auxillary_file(description=description, filename=filename)

        if display_output:
            fun_test.log_disable_timestamps()
            fun_test.log_section("VP util output")
            for line in lines:
                fun_test.log(line)
            fun_test.log_enable_timestamps()
        output = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return output


def populate_per_vp_output_file(network_controller_obj, filename, display_output=False):
    output = False
    try:
        filtered_dict = {}
        lines = list()

        result = network_controller_obj.peek_per_vp_stats()
        for key, val in sorted(result.iteritems()):
            if "FA1" in key or "FA2" in key:
                filtered_dict[key] = val
        master_table_obj = get_nested_dict_stats(result=filtered_dict)
        lines.append("\n########################  %s ########################\n" % str(get_timestamp()))
        lines.append(master_table_obj.get_string())
        lines.append('\n\n\n')

        with open(filename, 'a') as f:
            f.writelines(lines)

        description = "Per vp"
        fun_test.add_auxillary_file(description=description, filename=filename)

        if display_output:
            fun_test.log_disable_timestamps()
            fun_test.log_section("VP util output")
            for line in lines:
                fun_test.log(line)
            fun_test.log_enable_timestamps()
        output = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return output


def run_dpcsh_commands(template_obj, sequencer_handle, network_controller_obj, single_flow, half_load_latency,test_time,
                       test_type=None, display_output=False):
    try:
        sequencer_passed = False
        version = fun_test.get_version()
        flow = "multi_flow"
        if single_flow:
            flow = "single_flow"
        latency = "full_load_latency"
        if half_load_latency:
            latency = "half_load_latency"
        flow_latency = "%s_%s" % (flow, latency)
        time_delta = 10
        sleep_time = int(test_time/time_delta)
        total_stream_runs = 3
        total_trails = 6
        max_loop_count = total_stream_runs * total_trails * time_delta

        common_file_name = str(version) + "_" + flow_latency
        if test_type:
            str(version) + "_" + str(test_type) + "_" + flow_latency
        resource_pc_1_file = common_file_name + '_resource_pc_1.txt'
        resource_pc_2_file = common_file_name + '_resource_pc_2.txt'
        bam_stats_file = common_file_name + '_bam.txt'
        vp_util_file = common_file_name + "_vp_util.txt"
        per_vp_file = common_file_name + "_per_vp.txt"
        ddr_stats_file = common_file_name + "_ddr.txt"
        cdu_stats_file = common_file_name + "_cdu.txt"
        ca_stats_file = common_file_name + "_ca.txt"

        artifact_resource_pc_1_file = fun_test.get_test_case_artifact_file_name(post_fix_name=resource_pc_1_file)
        artifact_resource_pc_2_file = fun_test.get_test_case_artifact_file_name(post_fix_name=resource_pc_2_file)
        artifact_bam_stats_file = fun_test.get_test_case_artifact_file_name(post_fix_name=bam_stats_file)
        artifact_vp_util_file = fun_test.get_test_case_artifact_file_name(post_fix_name=vp_util_file)
        artifact_per_vp_file = fun_test.get_test_case_artifact_file_name(post_fix_name=per_vp_file)
        artifact_ddr_file = fun_test.get_test_case_artifact_file_name(post_fix_name=ddr_stats_file)
        artifact_cdu_file = fun_test.get_test_case_artifact_file_name(post_fix_name=cdu_stats_file)
        artifact_ca_file = fun_test.get_test_case_artifact_file_name(post_fix_name=ca_stats_file)

        start_counter = 0
        while not sequencer_passed:
            fun_test.log_module_filter("random_module")
            populate_pc_resource_output_file(network_controller_obj=network_controller_obj,
                                             filename=artifact_resource_pc_1_file, pc_id=1, display_output=display_output)
            populate_pc_resource_output_file(network_controller_obj=network_controller_obj,
                                             filename=artifact_resource_pc_2_file, pc_id=2, display_output=display_output)
            populate_resource_bam_output_file(network_controller_obj=network_controller_obj, filename=artifact_bam_stats_file)
            populate_vp_util_output_file(network_controller_obj=network_controller_obj, filename=artifact_vp_util_file)
            populate_per_vp_output_file(network_controller_obj=network_controller_obj, filename=artifact_per_vp_file)
            populate_ddr_output_file(network_controller_obj=network_controller_obj, filename=artifact_ddr_file)
            populate_cdu_output_file(network_controller_obj=network_controller_obj, filename=artifact_cdu_file)
            populate_ca_output_file(network_controller_obj=network_controller_obj, filename=artifact_ca_file)
            fun_test.log_module_filter_disable()

            fun_test.sleep("Sleep for %s secs before next iteration of populating dpcsh stats" % sleep_time, seconds=sleep_time)

            state = template_obj.get_sequencer_state(sequencer_handle=sequencer_handle)
            if state.lower() == template_obj.PASSED.lower():
                sequencer_passed = True
                fun_test.log("Sequencer passed. Stopping dpcsh commands")
            elif start_counter >= max_loop_count:
                sequencer_passed = True
                fun_test.log("Sequencer did not stop in expected time. Forcefully looping out")
            start_counter += 1

    except Exception as ex:
        fun_test.critical(str(ex))
    return True

def populate_stats_file(network_controller_obj, test_time, generic_file_name_part, display_output=False):
    try:
        version = fun_test.get_version()
        sleep_time_factor = 10
        sleep_time = int(test_time/sleep_time_factor)

        resource_pc_1_file = str(version) + "_" + generic_file_name_part + '_resource_pc_1.txt'
        resource_pc_2_file = str(version) + "_" + generic_file_name_part + '_resource_pc_2.txt'
        bam_stats_file = str(version) + "_" + generic_file_name_part + '_bam.txt'
        vp_util_file = str(version) + "_" + generic_file_name_part + "_vp_util.txt"
        per_vp_file = str(version) + "_" + generic_file_name_part + "_per_vp.txt"
        ddr_stats_file = str(version) + "_" + generic_file_name_part + "_ddr.txt"
        cdu_stats_file = str(version) + "_" + generic_file_name_part + "_cdu.txt"
        ca_stats_file = str(version) + "_" + generic_file_name_part + "_ca.txt"

        artifact_resource_pc_1_file = fun_test.get_test_case_artifact_file_name(post_fix_name=resource_pc_1_file)
        artifact_resource_pc_2_file = fun_test.get_test_case_artifact_file_name(post_fix_name=resource_pc_2_file)
        artifact_bam_stats_file = fun_test.get_test_case_artifact_file_name(post_fix_name=bam_stats_file)
        artifact_vp_util_file = fun_test.get_test_case_artifact_file_name(post_fix_name=vp_util_file)
        artifact_per_vp_file = fun_test.get_test_case_artifact_file_name(post_fix_name=per_vp_file)
        artifact_ddr_file = fun_test.get_test_case_artifact_file_name(post_fix_name=ddr_stats_file)
        artifact_cdu_file = fun_test.get_test_case_artifact_file_name(post_fix_name=cdu_stats_file)
        artifact_ca_file = fun_test.get_test_case_artifact_file_name(post_fix_name=ca_stats_file)

        start_counter = 0
        while not start_counter == sleep_time_factor:
            fun_test.log_module_filter("random_module")
            populate_pc_resource_output_file(network_controller_obj=network_controller_obj,
                                             filename=artifact_resource_pc_1_file, pc_id=1, display_output=display_output)
            populate_pc_resource_output_file(network_controller_obj=network_controller_obj,
                                             filename=artifact_resource_pc_2_file, pc_id=2, display_output=display_output)
            populate_resource_bam_output_file(network_controller_obj=network_controller_obj, filename=artifact_bam_stats_file)
            populate_vp_util_output_file(network_controller_obj=network_controller_obj, filename=artifact_vp_util_file)
            populate_per_vp_output_file(network_controller_obj=network_controller_obj, filename=artifact_per_vp_file)
            populate_ddr_output_file(network_controller_obj=network_controller_obj, filename=artifact_ddr_file)
            populate_cdu_output_file(network_controller_obj=network_controller_obj, filename=artifact_cdu_file)
            populate_ca_output_file(network_controller_obj=network_controller_obj, filename=artifact_ca_file)
            fun_test.log_module_filter_disable()

            fun_test.sleep("Sleep for %s secs before next iteration of populating dpcsh stats" % sleep_time, seconds=sleep_time)

            start_counter += 1
        fun_test.log("Population of file stats completed")

    except Exception as ex:
        fun_test.critical(str(ex))
    return True


def get_resource_bam_table(result):
    table_obj = None
    bam_pool_decode_dict = {
        'pool0': 'BM_POOL_FUNOS',
        'pool1': 'BM_POOL_NU_ETP_CMDLIST',
        'pool2': 'BM_POOL_HU_REQ',
        'pool3': 'BM_POOL_SW_PREFETCH',
        'pool4': 'BM_POOL_NU_ERP_FCP',
        'pool19': 'BM_POOL_NU_ERP_CC',
        'pool20': 'BM_POOL_NU_ERP_SAMPLING',
        'pool34': 'BM_POOL_REGEX',
        'pool35': 'BM_POOL_REFBUF',
        'pool49': 'BM_POOL_NU_ERP_NONFCP',
        'pool50': 'BM_POOL_HNU_NONFCP',
        'pool62': 'BM_POOL_HNU_PREFETCH',
        'pool63': 'BM_POOL_NU_PREFETCH', }

    try:
        table_obj = PrettyTable(['Field Name', 'Counters'])
        table_obj.align = 'l'
        for key in result:
            decode_value = ''
            pool_value = key.split(' ')[0]
            if 'usage' in key:
                pool_value = key.split(' ')[1]
            if pool_value in bam_pool_decode_dict:
                decode_value = bam_pool_decode_dict[pool_value]
            table_obj.add_row([decode_value + ' (' + key + ')'.strip(), result[key], ])
    except Exception as ex:
        fun_test.critical(str(ex))
    return table_obj


def populate_resource_bam_output_file(network_controller_obj, filename, display_output=False):
    output = False
    try:
        lines = list()

        result = network_controller_obj.peek_resource_bam_stats()
        master_table_obj = get_resource_bam_table(result=result)
        lines.append("\n########################  %s ########################\n" % str(get_timestamp()))
        lines.append(master_table_obj.get_string())
        lines.append('\n\n\n')

        with open(filename, 'a') as f:
            f.writelines(lines)

        description = "Bam stats"
        fun_test.add_auxillary_file(description=description, filename=filename)

        if display_output:
            fun_test.log_disable_timestamps()
            fun_test.log_section("BAM Resource result")
            for line in lines:
                fun_test.log(line)
            fun_test.log_enable_timestamps()
        output = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return output


def populate_ddr_output_file(network_controller_obj, filename, display_output=False):
    output = False
    try:
        lines = list()

        result_1 = network_controller_obj.peek_ddr_stats()
        fun_test.sleep("Let time go for another second", seconds=1)
        result_2 = network_controller_obj.peek_ddr_stats()
        result = get_diff_results(old_result=result_1, new_result=result_2)
        lines.append("\n########################  %s ########################\n" % str(get_timestamp()))
        for key, val in result.iteritems():

            master_table_obj = get_nested_dict_stats(result=val)
            lines.append(master_table_obj.get_string())

            with open(filename, 'a') as f:
                f.writelines(lines)

            description = "DDR stats"
            fun_test.add_auxillary_file(description=description, filename=filename)

            if display_output:
                fun_test.log_disable_timestamps()
                fun_test.log_section("DDR result")
                for line in lines:
                    fun_test.log(line)
                fun_test.log_enable_timestamps()
        lines.append('\n\n\n')
        output = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return output


def populate_cdu_output_file(network_controller_obj, filename, display_output=False):
    output = False
    try:
        lines = list()

        result = network_controller_obj.peek_cdu_stats()
        fun_test.sleep("Let time go for another second", seconds=1)
        result = network_controller_obj.peek_cdu_stats()
        master_table_obj = get_nested_dict_stats(result=result)
        lines.append("\n########################  %s ########################\n" % str(get_timestamp()))
        lines.append(master_table_obj.get_string())
        lines.append('\n\n\n')

        with open(filename, 'a') as f:
            f.writelines(lines)

        description = "CDU stats"
        fun_test.add_auxillary_file(description=description, filename=filename)

        if display_output:
            fun_test.log_disable_timestamps()
            fun_test.log_section("CDU result")
            for line in lines:
                fun_test.log(line)
            fun_test.log_enable_timestamps()
        output = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return output


def populate_ca_output_file(network_controller_obj, filename, display_output=False):
    output = False
    try:
        lines = list()

        result_1 = network_controller_obj.peek_ca_stats()
        fun_test.sleep("Let time go for another second", seconds=1)
        result_2 = network_controller_obj.peek_ca_stats()
        result = get_diff_results(old_result=result_1, new_result=result_2)
        lines.append("\n########################  %s ########################\n" % str(get_timestamp()))
        for key, val in result.iteritems():

            master_table_obj = get_nested_dict_stats(result=val)
            lines.append(master_table_obj.get_string())

            with open(filename, 'a') as f:
                f.writelines(lines)

            description = "CA stats"
            fun_test.add_auxillary_file(description=description, filename=filename)

            if display_output:
                fun_test.log_disable_timestamps()
                fun_test.log_section("CA result")
                for line in lines:
                    fun_test.log(line)
                fun_test.log_enable_timestamps()
        lines.append('\n\n\n')
        output = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return output


def get_diff_results(old_result, new_result):
    result = {}
    try:
        for key, val in new_result.iteritems():
            if isinstance(val, dict):
                result[key] = get_diff_results(old_result=old_result[key], new_result=new_result[key])
            else:
                if not key in old_result:
                    old_result[key] = 0
                result[key] = new_result[key] - old_result[key]
    except Exception as ex:
        fun_test.critical(str(ex))
    return result