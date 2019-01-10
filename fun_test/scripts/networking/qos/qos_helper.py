from lib.system.fun_test import *
from lib.utilities.pcap_parser import PcapParser
import copy

qos_json_file = fun_test.get_script_parent_directory() + '/qos.json'
qos_json_output = fun_test.parse_file_to_json(qos_json_file)
QOS_PROFILE_WRED = "wred"
QOS_PROFILE_ECN = "ecn"
q_depth = 'avg_q_integ'
wred_q_drop = 'wred_q_drop'
ecn_count = 'ecn_count'
ECN_BITS_00 = 00
ECN_BITS_10 = 10
ECN_BITS_01 = 01
NON_ECN_BITS = 00
CONGESTION_BITS = 11
CONGESTION_BITS_DECIMAL = 3

def get_load_value_from_load_percent(load_percent, max_egress_load):
    result = None
    try:
        if load_percent == 0:
            result = 0
        else:
            result = (load_percent * max_egress_load) / 100.0
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def verify_load_output(actual_value, expected_value, accept_range=0.2, compare=False):
    result = False
    try:
        fun_test.log("Actual load output seen is %s" % actual_value)
        if not compare:
            fun_test.log("Expected load output is %s" % expected_value)
        else:
            fun_test.log("Actual load output seen for comparing stream is %s" % expected_value)
        if actual_value < expected_value:
            diff = expected_value - actual_value
        else:
            diff = actual_value - expected_value

        if diff < accept_range:
            result = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def reset_queue_scheduler_config(network_controller_obj, dut_port, queue_list=[]):
    result = False
    try:
        if not queue_list:
            queue_list = [x for x in range(16)]
        for queue in queue_list:
            strict_priority = 0
            extra_bandwidth = 0
            if queue in [0, 8]:
                strict_priority = 1
                extra_bandwidth = 1
            strict = network_controller_obj.set_qos_scheduler_config(port_num=dut_port, queue_num=queue,
                                                                     scheduler_type=network_controller_obj.SCHEDULER_TYPE_STRICT_PRIORITY,
                                                                     strict_priority_enable=strict_priority,
                                                                     extra_bandwidth=extra_bandwidth)
            fun_test.test_assert(strict,"Set strict priority of %s on queue %s" % (strict_priority, queue),
                                 ignore_on_success=True)

            shaper = network_controller_obj.set_qos_scheduler_config(port_num=dut_port, queue_num=queue,
                                                                     scheduler_type=network_controller_obj.SCHEDULER_TYPE_SHAPER,
                                                                     shaper_enable=False,
                                                                     min_rate=qos_json_output['shaper']['default_cir'],
                                                                     shaper_threshold=qos_json_output['shaper'][
                                                                         'default_threshold'])
            fun_test.test_assert(shaper, "Reset shaper cir and threshold to default values for queue %s" % queue,
                                 ignore_on_success=True)

            dwrr = network_controller_obj.set_qos_scheduler_config(port_num=dut_port, queue_num=queue,
                                                                   scheduler_type=network_controller_obj.SCHEDULER_TYPE_WEIGHTED_ROUND_ROBIN,
                                                                   weight=qos_json_output['dwrr']['default_weight'])
            fun_test.test_assert(dwrr, "Reset dwrr to default values for queue %s" % queue,
                                 ignore_on_success=True)
            result = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def set_default_qos_probability(network_controller_obj, profile_type):
    result = False
    default_probabilities = {"0": 16, "1": 32, "2": 64, "3": 128, "4": 256, "5": 512,
                             "6": 1023, "7": 2047}
    try:
        for key, value in default_probabilities.iteritems():
            if profile_type == QOS_PROFILE_WRED:
                network_controller_obj.set_qos_wred_probability(prob_index=int(key), probability=value)
            elif profile_type == QOS_PROFILE_ECN:
                network_controller_obj.set_qos_ecn_probability(prob_index=int(key), probability=value)
            else:
                raise Exception("QOS profile %s not found" % profile_type)
        result = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def get_ecn11_packet_src_ip(pcap_filename, source_ip_list=[]):
    result = {}
    result['not_found_source_ip'] = []
    result['found_source_ip'] = []
    try:
        if not source_ip_list:
            raise Exception("Source ip list is empty")
        copied_list = copy.deepcopy(source_ip_list)
        pcap_obj = PcapParser(filename=pcap_filename)
        out = pcap_obj.get_filter_captures()
        fun_test.simple_assert(out is not None, "Ensure packets are seen in pcap capture")
        for packet in out:
            if not copied_list:
                break
            ip_layer = pcap_obj.get_all_header_fields(packet=packet, header_layer=pcap_obj.LAYER_IP)
            fun_test.simple_assert(ip_layer, "Ensure ip layer fields are found")
            if ip_layer['ip_dsfield_tree']['ip_dsfield_ecn'] == str(CONGESTION_BITS_DECIMAL):
                src_ip = ip_layer['ip_src']
                if src_ip in source_ip_list:
                    if src_ip not in result['found_source_ip']:
                        result['found_source_ip'].append(src_ip)
                        copied_list.remove(src_ip)
        result['not_found_source_ip'] = result['not_found_source_ip']+ copied_list
    except Exception as ex:
        fun_test.critical(str(ex))
    return result

def get_ecn11_packet_dscp(pcap_filename, dscp_list=[]):
    """
    :param pcap_filename: filepath of the pcap file
    :param dscp_list: dscp values to be tested for having ecn 11
    :return: dict containing one list of all dscp values seen having ecn 11 and
    other list with dscp values not having ecn 11
    """
    result = {}
    result['not_found_dscp'] = []
    result['found_dscp'] = []
    out = None
    try:
        if not dscp_list:
            raise Exception("DSCP list is empty")
        copied_list = copy.deepcopy(dscp_list)
        pcap_obj = PcapParser(filename=pcap_filename)
        out = pcap_obj.get_filter_captures()
        fun_test.simple_assert(out is not None, "Ensure packets are seen in pcap capture")
        for packet in out:
            if not copied_list:
                break
            ip_layer = pcap_obj.get_all_header_fields(packet=packet, header_layer=pcap_obj.LAYER_IP)
            fun_test.simple_assert(ip_layer, "Ensure ip layer fields are found")
            if ip_layer['ip_dsfield_tree']['ip_dsfield_ecn'] == str(CONGESTION_BITS_DECIMAL):
                dscp_val = int(ip_layer['ip_dsfield_tree']['ip_dsfield_dscp'])
                if dscp_val in dscp_list:
                    if dscp_val not in result['found_dscp']:
                        result['found_dscp'].append(dscp_val)
                        copied_list.remove(dscp_val)
        result['not_found_dscp'] = result['not_found_dscp']+ copied_list
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def capture_wred_ecn_stats_n_times(network_controller_obj, port_num, queue_num, iterations, stats_list):
    result = {}
    result['result'] = False
    try:
        for i in range(iterations):
            output_1 = network_controller_obj.get_qos_wred_ecn_stats(port_num=port_num, queue_num=queue_num)
            fun_test.simple_assert(output_1, "Get wred ecn stats once")

            fun_test.sleep("Letting stats to be updated")

            output_2 = network_controller_obj.get_qos_wred_ecn_stats(port_num=port_num, queue_num=queue_num)
            fun_test.simple_assert(output_2, "Get wred ecn stats twice")

            for stat in stats_list:
                fun_test.simple_assert(stat in output_1, "Stat %s not found" % stat)
                if stat not in result:
                    result[stat] = []
                if stat == q_depth:
                    result[stat].append(output_2[stat])
                else:
                    result[stat].append(output_2[stat] - output_1[stat])
        result['result'] = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def get_ecn_qos_binary(qos_binary, ecn_bits=CONGESTION_BITS):
    return qos_binary + str(ecn_bits) + 'b'


def get_load_pps_for_each_queue(max_egress_load_mbps, packet_size, total_queues=None):
    max_load_bits = max_egress_load_mbps * 1000000
    bit_packet_size = packet_size * 8
    if not total_queues:
        total_queues = 16
    return int(max_load_bits / (bit_packet_size * total_queues))


def reset_pfc_configs(network_controller_obj, dut_port_list, queue_list=[], quanta=False, threshold=False, shared_configs=False, shared_config_port_list=[]):
    result = False
    default_quanta = 0
    default_threshold = 0
    default_min_thr = 16383
    default_shr_thr = 16383
    default_hdr_thr = 16383
    default_xoff_enable = 0
    default_shared_xon_thr = 100
    try:
        fun_test.simple_assert(network_controller_obj.disable_qos_pfc(), "Disable QOS pfc")

        for dut_port in dut_port_list:
            fun_test.simple_assert(network_controller_obj.disable_priority_flow_control(port_num=dut_port),
                                   "Disable PFC on %s" % dut_port)

            if quanta or threshold:
                for queue in queue_list:
                    if quanta:
                        fun_test.simple_assert(network_controller_obj.set_priority_flow_control_quanta(
                            port_num=dut_port, quanta=default_quanta, class_num=queue),
                            "Reset default quanta of %s on queue %s" % (default_quanta, dut_port))
                    if threshold:
                        fun_test.simple_assert(network_controller_obj.set_priority_flow_control_threshold(
                            port_num=dut_port, threshold=default_threshold, class_num=queue),
                            "Reset default threshold of %s on queue %s" % (default_threshold, dut_port))

        if shared_configs:
            for dut_port in shared_config_port_list:
                for queue in queue_list:
                    fun_test.simple_assert(network_controller_obj.
                                           set_qos_ingress_priority_group(port_num=dut_port,
                                                                          priority_group_num=queue,
                                                                          min_threshold=default_min_thr,
                                                                          shared_threshold=default_shr_thr,
                                                                          headroom_threshold=default_hdr_thr,
                                                                          xoff_enable=default_xoff_enable,
                                                                          shared_xon_threshold=default_shared_xon_thr),
                                           "Ensure shared configs are reset on queue %s of port %s" % (queue, dut_port))
        result = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def reset_link_pause_configs(network_controller_obj, dut_port_list, quanta=True, threshold=True):
    result = False
    default_quanta = 0
    default_threshold = 0
    try:
        for dut_port in dut_port_list:
            fun_test.simple_assert(network_controller_obj.disable_link_pause(port_num=dut_port),
                                   message="Disable link pause on port %s" % dut_port)
            if quanta:
                fun_test.simple_assert(network_controller_obj.set_link_pause_quanta(port_num=dut_port_list,
                                                                                    quanta=default_quanta),
                                       message="Set pause quanta to 0 on port %s" % default_quanta)
            if threshold:
                fun_test.simple_assert(network_controller_obj.set_link_pause_threshold(port_num=dut_port_list,
                                                                                       threshold=default_threshold),
                                       message="Set pause threshold to 0 on port %s" % default_threshold)
        result = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return result