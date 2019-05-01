from lib.system.fun_test import *
from collections import OrderedDict
import pickle
import json
from web.fun_test.analytics_models_helper import ModelHelper


TCP_PERFORMANCE_MODEL_NAME = "TeraMarkFunTcpThroughputPerformance"


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

def use_model_helper(model_name, data_dict, unit_dict):
    result = False
    try:
        generic_helper = ModelHelper(model_name=model_name)
        status = fun_test.PASSED
        generic_helper.set_units(**unit_dict)
        generic_helper.add_entry(**data_dict)
        generic_helper.set_status(status)
        result = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return result

def populate_performance_json_file(flow_type, model_name, frame_size, num_flows, throughput_n2t, pps_n2t,
                                   timestamp, filename, protocol="TCP", mode="100G"):
    results = []
    output = False
    try:
        output_dict = {"mode": mode,
                       "flow_type": flow_type,
                       "frame_size": frame_size,
                       "num_flows": num_flows,
                       "pps": pps_n2t,
                       "protocol": protocol,
                       "throughput": throughput_n2t,
                       "timestamp": str(timestamp),
                       "version": fun_test.get_version()
                       }
        fun_test.log("FunOS version is %s" % output_dict['version'])
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

        unit_dict = {}
        unit_dict["pps_unit"] = "pps"
        unit_dict["throughput_unit"] = "Mbps"
        add_entry = use_model_helper(model_name=model_name, data_dict=output_dict, unit_dict=unit_dict)
        fun_test.simple_assert(add_entry, "Entry added to model %s" % model_name)
        fun_test.add_checkpoint("Entry added to model %s" % model_name)
        output = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return output

def get_pps_from_mbps(mbps, byte_frame_size):
    return (float(mbps) * 1000000) / (byte_frame_size * 8)

def execute_shell_file(linux_obj, target_file, output_file=None):
    output = {}
    output['result'] = False
    try:
        check = linux_obj.check_file_directory_exists(target_file)
        fun_test.simple_assert(check, "Check file %s exists in %s" % (target_file, linux_obj.host_ip))
        cmd = "sh %s" % target_file
        if output_file:
            cmd = "sh %s > %s" % (target_file, output_file)
        out = linux_obj.command(command=cmd)
        output['output'] = out
        output['result'] = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return output

def get_total_throughput(output, num_conns):
    result = {}
    result['connections'] = False
    result['throughput'] = 0.0
    try:
        stat_counter = 0
        throughput_out_lines = output.split("\n")
        for line in throughput_out_lines:
            throughput = float(line.split("=")[1])
            result['throughput'] += throughput
            stat_counter += 1
        #fun_test.test_assert_expected(expected=num_conns, actual=stat_counter,
        #                              message="Ensure all netstat clients are started")
        result['connections'] = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return result

def run_mpstat_command(linux_obj, decimal_place=2, interval=5, json_output=False, output_file=None, bg=False):
    try:
        cmd = "mpstat -A %s %s" % (decimal_place, interval)
        if json_output:
            cmd += " -o JSON"
        if output_file:
            cmd += " > %s" % output_file
        if bg:
            cmd += " &"
        fun_test.log("mpstat command formed is %s" % cmd)
        out = linux_obj.command(command=cmd)
    except Exception as ex:
        fun_test.critical(str(ex))
    return out


def read_and_dump_output(linux_obj, read_filename, dump_filename):
    result = False
    try:
        out = None
        out = linux_obj.read_file(file_name=read_filename, include_last_line=True)
        fun_test.simple_assert(out, "File %s has no contents" % read_filename)
        out1 = json.loads(out)

        file = open(dump_filename, "w")
        pickle.dump(out, file)
        file.close()
        result = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return result

def _parse_list_to_dict(list1):
    out_dict = {}
    for item in list1:
        if item[0].isalpha():
            current_key  = item
            out_dict[current_key] = []
        else:
            out_dict[current_key].append(item)

    return out_dict


def _convert_output_to_dict(out_dict):
    output = {}
    try:
        for key, val in out_dict.iteritems():
            current_key = key[:-2]
            output[current_key] = {}
            for value in val:
                current_val = str(value[:-1])
                current_val = current_val.strip()
                if ":" in current_val:
                    new_key = current_val.split(": ")[0].strip()
                    new_val = int(current_val.split(": ")[1])
                    output[current_key][new_key] = new_val
                elif current_val[0].isdigit():
                    new_val = int(current_val.split(" ")[0])
                    new_key = current_val.split(" ")[1:]
                    new_key = ' '.join(new_key)
                    output[current_key][new_key] = new_val
    except Exception as ex:
        fun_test.critical(str(ex))
    return output


def get_netstat_output(linux_obj, options=['s','t'], keys=['Tcp','TcpExt']):
    output = {}
    try:
        fun_test.simple_assert(options, "Options must be provieded for netsat")
        opt = ''.join(options)
        cmd = "netstat -%s" % opt
        fun_test.log("Netstat command formed is %s" % cmd)
        out = linux_obj.command(command=cmd)
        out = out.split("\n")

        parsed_keys = _parse_list_to_dict(out)
        for key in parsed_keys.keys():
            current_key = key[:-2]
            if not current_key in keys:
                parsed_keys.pop(key)

        output = _convert_output_to_dict(parsed_keys)
    except Exception as ex:
        fun_test.critical(str(ex))
    return output

def get_diff_stats(old_stats, new_stats):
    result = {}
    try:
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

def populate_netstat_json_file(old_stats, new_stats, filename):
    results = []
    output = False
    try:
        output_dict = get_diff_stats(old_stats=old_stats, new_stats=new_stats)
        results.append(output_dict)
        file_path = LOGS_DIR + "/%s" % filename
        '''
        contents = _parse_file_to_json_in_order(file_name=file_path)
        if contents:
            append_new_results = contents + results
            file_created = create_counters_file(json_file_name=file_path,
                                                     counter_dict=append_new_results)
            fun_test.simple_assert(file_created, "Create netstat JSON file")
        else:
        '''
        file_created = create_counters_file(json_file_name=file_path,
                                                    counter_dict=results)
        fun_test.simple_assert(file_created, "Create netstat JSON file")
        output = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return output


def get_stale_socket_connections(linux_obj, port_value):
    result = 0
    try:
        cmd = "ss -t| grep %s" % port_value
        output = linux_obj.command(command=cmd)
        if output:
            result = len(output.split("\n"))
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def _remove_dict_key(org_dict, remove_key):
    for key, val in org_dict.iteritems():
        if isinstance(val, list) and key == remove_key:
            del org_dict[key]
        elif isinstance(val, list) or isinstance(val, dict):
            return _remove_dict_key(val, remove_key)
    return org_dict

def trim_json_contents(filepath):
    result = False
    try:
        out = parse_file_to_json(filepath)
        try:
            check_list = out['sysstat']['hosts'][0]['statistics']
        except KeyError:
            fun_test.critical("Key statistics not found in %s" % filepath)

        for item in check_list:
            for key in item.keys():
                if key == "individual-interrupts":
                    del item[key]
        #new_data = _remove_dict_key(org_dict=out, remove_key=key)

        with open(filepath, "w") as dfile:
            data = json.dump(out, dfile, indent=4)
        result = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return result
