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
FRAME_CHECK_SEQUENCE_ERROR = "aFrameCheckSequenceErrors"
CLASS_0 = "0"
VP_PACKETS_TOTAL_IN = "vp_packets_total_in"
VP_PACKETS_TOTAL_OUT = "vp_packets_total_out"
VP_PACKETS_OUT_HU = "vp_packets_out_hu"
VP_PACKETS_FORWARDING_NU_LE = "vp_packets_forwarding_nu_le"
ERP_COUNT_FOR_ALL_NON_FCP_PACKETS_RECEIVED = "count_for_all_non_fcp_packets_received"


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
                if tx and 'TX' == key.split('_')[3]:
                    result = output[key]
                    break
                elif 'RX' == key.split('_')[3]:
                    result = output[key]
                    break
    return result


def get_dut_output_stats_value(result_stats, stat_type, tx=True, class_value=None):
    result = None
    try:
        if stat_type == CBFC_PAUSE_FRAMES_RECEIVED:
            result = __get_class_based_counter_stats_value(result_stats, stat_type, tx, class_value)
            return result
        output = result_stats[0]
        for key in output.iterkeys():
            if len(key.split('_')) > 4:
                if stat_type == key.split('_')[4]:
                    if tx and 'TX' == key.split('_')[3]:
                        result = output[key]
                        break
                    elif 'RX' == key.split('_')[3]:
                        result = output[key]
                        break
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def get_dut_fpg_port_stats(network_controller_obj, dut_port_list=[]):
    result_dict = {}
    try:
        for port in dut_port_list:
            result_dict[port] = network_controller_obj.peek_fpg_port_stats(port)
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


def get_psw_global_stats_values(psw_stats_output={}, key_list=[]):
    result = {}
    try:
        for key in key_list:
            result[key] = None
            if psw_global_stats_counter_names.has_key(key):
                for key1, val1 in psw_stats_output.iteritems():
                    for key2, val2 in val1.iteritems():
                        if key2 == key:
                            result[key] = val2
                            break
            else:
                fun_test.log("Key %s not found in psw_stats_counter_name" % key)
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def parse_result_dict(result_dict):
    result = {}
    try:
        for key, val in result_dict.iteritems():
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


def get_bam_stats_values(network_controller_obj=None):
    result = None
    try:
        output = network_controller_obj.peek_bam_stats()
        fun_test.simple_assert(output, "Ensure bam stats are grepped")
        result = parse_result_dict(output)
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def get_erp_stats_values(network_controller_obj=None, hnu=False, flex=False):
    result = None
    try:
        output = network_controller_obj.peek_erp_global_stats(hnu=hnu, flex=flex)
        fun_test.simple_assert(output, "Ensure bam stats are grepped")
        result = parse_result_dict(output)
    except Exception as ex:
        fun_test.critical(str(ex))
    return result