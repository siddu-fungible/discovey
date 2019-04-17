from lib.system.fun_test import *
from collections import OrderedDict


def _parse_file_to_json_in_order(file_name):
    result = None
    try:
        with open(file_name, "r") as infile:
            contents = infile.read()
            result = json.loads(contents, object_pairs_hook=OrderedDict)
    except Exception as ex:
        scheduler_logger.critical(str(ex))
    return result

def create_counters_file(json_file_name, counter_dict):
    result = False
    try:
        with open(json_file_name, "w") as f:
            json.dump(counter_dict, f, indent=4, default=str)
        result = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return result

def populate_performance_json_file(flow_type, frame_size, num_flows, throughput_n2t, pps_n2t,
                                   timestamp, filename, protocol="TCP", offloads=False):
    results = []
    output = False
    try:
        output_dict = {"flow_type": flow_type,
                       "frame_size": frame_size,
                       "num_flows": num_flows,
                       "offloads": offloads,
                       "pps_n2t": pps_n2t,
                       "protocol": protocol,
                       "throughput_n2t": throughput_n2t,
                       "timestamp": timestamp,
                       "version": fun_test.get_version()
                       }
        results.append(output_dict)
        file_path = LOGS_DIR + "/%s" % filename
        contents = _parse_file_to_json_in_order(file_name=file_path)
        if contents:
            append_new_results = contents + results
            file_created = create_counters_file(json_file_name=file_path,
                                                     counter_dict=append_new_results)
            fun_test.simple_assert(file_created, "Create Performance JSON file")
        else:
            file_created = create_counters_file(json_file_name=file_path,
                                                     counter_dict=results)
            fun_test.simple_assert(file_created, "Create Performance JSON file")
        output = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return output

def get_pps_from_mbps(mbps, byte_frame_size):
    return (float(mbps) * 1000000) / (byte_frame_size * 8)