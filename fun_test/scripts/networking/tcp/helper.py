from lib.system.fun_test import *
from collections import OrderedDict
from prettytable import PrettyTable
from datetime import datetime
import pickle
import json
import re
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


def run_mpstat_command(linux_obj, count=2, interval=5, output_file=None, bg=False):
    out = None
    try:
        cmd = "mpstat -A -o JSON %s %s" % (interval, count)
        fun_test.log("mpstat command formed is %s" % cmd)
        if bg:
            out = linux_obj.start_bg_process(command=cmd, output_file=output_file)
        else:
            out = linux_obj.command(command=cmd)
    except Exception as ex:
        fun_test.critical(str(ex))
    return out


def create_nested_table(stat, key_name):
    table_obj = None
    try:
        table_obj = PrettyTable(stat[key_name][0].keys())
        for record in stat[key_name]:
            table_obj.add_row(record.values())
    except Exception as ex:
        fun_test.critical(str(ex))
    return table_obj


def create_interrupts_table(stat, key_name):
    table_obj = None
    try:
        table_obj = PrettyTable(stat[key_name][0].keys())
        for record in stat[key_name]:
            rows = []
            for key in record:
                if type(record[key]) == list:
                    inner_table = PrettyTable(record[key][0].keys())
                    inner_table.align = 'l'
                    for _record in record[key]:
                        inner_table.add_row(_record.values())
                    rows.append(inner_table)
                else:
                    rows.append(record[key])
            table_obj.add_row(rows)
    except Exception as ex:
        fun_test.critical(str(ex))
    return table_obj


def populate_mpstat_output_file(output_file, linux_obj, dump_filename):
    mpstat_dump_filepath = None
    try:
        contents = linux_obj.read_file(file_name=output_file, include_last_line=False)
        n_c = re.sub(r'.*Done.*', "", contents)
        mpstat_dict = json.loads(n_c)
        hosts_table = PrettyTable(['Date', 'Machine', 'Node Name', 'No of CPUs', 'release', 'sysname'])

        for host in mpstat_dict['sysstat']['hosts']:
            hosts_table.add_row(
                [host['date'], host['machine'], host['nodename'], host['number-of-cpus'], host['release'],
                 host['sysname']])

        stats_table = PrettyTable(['timestamp', 'cpu-load', 'node-load'])
        interrupts_table = PrettyTable(['timestamp', 'sum-interrupts', 'soft-interrupts'])

        for host in mpstat_dict['sysstat']['hosts']:
            for stat in host['statistics']:
                cpu_load_table = create_nested_table(stat=stat, key_name='cpu-load')
                node_load_table = create_nested_table(stat=stat, key_name='node-load')
                sum_interrupts_table = create_interrupts_table(stat=stat, key_name='sum-interrupts')
                soft_interrupts_table = create_interrupts_table(stat=stat, key_name='soft-interrupts')

                stats_table.add_row([stat['timestamp'], cpu_load_table, node_load_table])
                interrupts_table.add_row([stat['timestamp'], sum_interrupts_table, soft_interrupts_table])

        mpstat_dump_filepath = LOGS_DIR + "/%s" % dump_filename
        lines = ['<=======> Mpstat output <=======>\n', '\n<=======> Hosts MetaData <=======>\n',
                 hosts_table.get_string(), '\n<=======> Statistics <=======>\n', stats_table.get_string(),
                 '\n<=======> Interrupts <=======>\n', interrupts_table.get_string()]
        with open(mpstat_dump_filepath, 'w') as f:
            f.writelines(lines)

    except Exception as ex:
        fun_test.critical(str(ex))
    return mpstat_dump_filepath


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


def populate_netstat_output_file(diff_stats, filename):
    output = False
    try:
        file_path = LOGS_DIR + "/%s" % filename
        netstat_table = PrettyTable(diff_stats.keys())
        rows = []
        for key in diff_stats:
            inner_table = PrettyTable(['Name', 'Value'])
            inner_table.align = 'l'
            inner_table.border = False
            inner_table.header = False
            for _key, _val in diff_stats[key].iteritems():
                inner_table.add_row([_key, _val])
            rows.append(inner_table)
        netstat_table.add_row(rows)

        lines = ['<=======> Netstat output <=======>\n', netstat_table.get_string()]
        with open(file_path, 'w') as f:
            f.writelines(lines)
        output = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return output


def inner_table_obj(result):
    table_obj = PrettyTable(['Field Name', 'Counter'])
    table_obj.align = 'l'
    table_obj.sortby = 'Field Name'
    try:
        for key in sorted(result):
            if key == 'cookie':
                table_obj.add_row([key, result[key]])
            elif type(result[key]) == list:
                for record in sorted(result[key]):
                    if type(record) == dict:
                        inner_table = PrettyTable()
                        inner_table.align = 'l'
                        for _key, val in record.iteritems():
                            if type(val) == dict:
                                if 'packets' in val or 'bytes' in val:
                                    _table_obj = PrettyTable(['Field Name', 'Counter'])
                                    _table_obj.sortby = 'Field Name'
                                else:
                                    _table_obj = PrettyTable()
                                _table_obj.align = 'l'
                                for inner_key in val:
                                    _table_obj.add_row([inner_key, val[inner_key]])
                                inner_table.add_row([_key, _table_obj])
                            else:
                                inner_table.add_row([_key, val])
                        table_obj.add_row([key, inner_table])
    except Exception as ex:
        fun_test.critical(str(ex))
    return table_obj


def populate_flow_list_output_file(result, filename):
    output = False
    try:
        file_path = LOGS_DIR + "/%s" % filename
        master_table_obj = PrettyTable()
        master_table_obj.align = 'l'
        master_table_obj.header = False
        if result:
            for key in sorted(result):
                table_obj = inner_table_obj(result=result[key])
                master_table_obj.add_row([key, table_obj])

            lines = ['<=======> Flowlist output <=======>\n', master_table_obj.get_string()]
            with open(file_path, 'w') as f:
                f.writelines(lines)
        output = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return output


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
        print master_table_obj
    except Exception as ex:
        fun_test.critical(str(ex))
    return master_table_obj


def dma_resource_table(result):
    table_obj = PrettyTable(['color', 'qdepth'])
    try:
        for record in result:
            table_obj.add_row(record.values())
    except Exception as ex:
        fun_test.critical(str(ex))
    return table_obj


def populate_pc_resource_output_file(network_controller_obj, filename, pc_id):
    output = False
    try:
        file_path = LOGS_DIR + "/%s" % filename

        result = network_controller_obj.peek_resource_pc_stats(pc_id=pc_id)
        master_table_obj = get_nested_dict_stats(result=result)
        lines = ['<=======> Peek Stats Resource PC %d output <=======>\n' % pc_id, master_table_obj.get_string(),
                 '\n\n\n']

        result = network_controller_obj.peek_resource_dma_stats(pc_id=pc_id)
        master_table_obj = dma_resource_table(result=result)
        lines.append('<=======> Peek Stats Resource DMA %d output <=======>\n' % pc_id)
        lines.append(master_table_obj.get_string())

        for index in range(0, 4):
            fun_test.sleep(message="Peek stats resource pc/dma %d" % pc_id, seconds=1)

            result = network_controller_obj.peek_resource_pc_stats(pc_id=pc_id)
            master_table_obj = get_nested_dict_stats(result=result)
            lines.append("\n########################  %s ########################\n" % str(get_timestamp()))
            lines.append(master_table_obj.get_string())
            lines.append('\n\n\n')

            result = network_controller_obj.peek_resource_dma_stats(pc_id=pc_id)
            master_table_obj = dma_resource_table(result=result)
            lines.append("\n########################  %s ########################\n" % str(get_timestamp()))
            lines.append(master_table_obj.get_string())
            lines.append('\n\n\n')

        with open(file_path, 'a') as f:
            f.writelines(lines)
        output = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return output


def get_timestamp():
    ts = time.time()
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


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
