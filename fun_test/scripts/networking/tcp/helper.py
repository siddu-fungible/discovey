from lib.system.fun_test import *
from scripts.networking.helper import *
from lib.system.utils import MultiProcessingTasks
from collections import OrderedDict
from prettytable import PrettyTable
from datetime import datetime
import pickle
import json
import re
from web.fun_test.analytics_models_helper import ModelHelper
from fun_global import PerfUnit


TCP_PERFORMANCE_MODEL_NAME = "TeraMarkFunTcpThroughputPerformance"
TCP_CPS_PERFORMANCE_MODEL_NAME = "TeraMarkFunTcpConnectionsPerSecondPerformance"


def _parse_file_to_json_in_order(file_name):
    result = None
    try:
        with open(file_name, "r") as infile:
            contents = infile.read()
            result = json.loads(contents, object_pairs_hook=OrderedDict)
    except Exception as ex:
        scheduler_logger.critical(str(ex))
    return result


def get_nu_lab_host(file_path, host_name):
    result = None
    try:
        hosts = fun_test.parse_file_to_json(file_name=file_path)
        if host_name in hosts:
            result = hosts[host_name]
        else:
            raise Exception("%s host entry not found in asset hosts.json")
    except Exception as ex:
        fun_test.critical(str(ex))
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
                                   timestamp, filename, mode="100G"):
    results = []
    output = False
    try:
        output_dict = {"mode": mode,
                       "flow_type": flow_type,
                       "frame_size": frame_size,
                       "num_flows": num_flows,
                       "pps": pps_n2t,
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
        unit_dict["pps_unit"] = PerfUnit.UNIT_PPS
        unit_dict["throughput_unit"] = PerfUnit.UNIT_MBITS_PER_SEC
        add_entry = use_model_helper(model_name=model_name, data_dict=output_dict, unit_dict=unit_dict)
        fun_test.simple_assert(add_entry, "Entry added to model %s" % model_name)
        fun_test.add_checkpoint("Entry added to model %s" % model_name)
        output = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return output


def populate_cps_performance_json_file(flow_type, model_name, frame_size, cps_type, max_cps, max_latency, avg_latency,
                                       timestamp, filename, mode="100G"):
    results = []
    output = False
    try:
        output_dict = {"mode": mode,
                       "flow_type": flow_type,
                       "frame_size": frame_size,
                       "cps_type": cps_type,
                       "max_cps": max_cps,
                       "max_latency": max_latency,
                       "avg_latency": avg_latency,
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
        unit_dict["max_cps_unit"] = PerfUnit.UNIT_CPS
        unit_dict["max_latency_unit"] = PerfUnit.UNIT_USECS
        unit_dict["avg_latency_unit"] = PerfUnit.UNIT_USECS
        add_entry = use_model_helper(model_name=model_name, data_dict=output_dict, unit_dict=unit_dict)
        fun_test.simple_assert(add_entry, "Entry added to model %s" % model_name)
        fun_test.add_checkpoint("Entry added to model %s" % model_name)
        output = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return output


def get_pps_from_mbps(mbps, byte_frame_size):
    return (float(mbps) * 1000000) / (byte_frame_size * 8)


def execute_shell_file(linux_obj, target_file, output_file=None, sudo=False):
    output = {}
    output['result'] = False
    try:
        check = linux_obj.check_file_directory_exists(target_file)
        fun_test.simple_assert(check, "Check file %s exists in %s" % (target_file, linux_obj.host_ip))
        cmd = "sh %s" % target_file
        if output_file:
            cmd = "sh %s > %s" % (target_file, output_file)
        if sudo:
            out = linux_obj.sudo_command(command=cmd)
        else:
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

        lines = ['<=======> Mpstat output <=======>\n', '\n<=======> Hosts MetaData <=======>\n',
                 hosts_table.get_string(), '\n<=======> Statistics <=======>\n', stats_table.get_string(),
                 '\n<=======> Interrupts <=======>\n', interrupts_table.get_string()]

        mpstat_dump_filepath = fun_test.get_test_case_artifact_file_name(dump_filename)

        with open(mpstat_dump_filepath, 'w') as f:
            f.writelines(lines)

        fun_test.add_auxillary_file(description=dump_filename, filename=mpstat_dump_filepath)

        fun_test.log_disable_timestamps()
        fun_test.log_section('Mpstats output')
        for line in lines:
            fun_test.log(line)
        fun_test.log_enable_timestamps()

    except Exception as ex:
        fun_test.critical(str(ex))
    return mpstat_dump_filepath


def populate_tcpdump_redirect_file(dump_filename, source_file_path, host_obj, host_name, version, num_flows):
    mpstat_dump_filepath = None
    try:
        target_file_name = fun_test.get_test_case_artifact_file_name(dump_filename)
        file_transfer = fun_test.scp(source_file_path=source_file_path, source_ip=host_obj.host_ip,
                                     source_username=host_obj.ssh_username, source_password=host_obj.ssh_password,
                                     target_file_path=target_file_name, timeout=300)
        fun_test.simple_assert(file_transfer, "scp pcap file from linux host to logs dir")
        fun_test.sleep("Letting file to be scp", seconds=2)

        fun_test.add_auxillary_file(description='FunOS Version: %s Num Flows: %s Host: %s tcpdump log' % (
            version, num_flows, host_name), filename=target_file_name)
    except Exception as ex:
        fun_test.critical(str(ex))
    finally:
        host_obj.sudo_command(command="rm -rf %s" % source_file_path)
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

        file_path = fun_test.get_test_case_artifact_file_name(filename)

        with open(file_path, 'w') as f:
            f.writelines(lines)

        fun_test.add_auxillary_file(description=filename, filename=file_path)

        fun_test.log_disable_timestamps()
        fun_test.log_section('Netstat diff output')
        for line in lines:
            fun_test.log(line)
        fun_test.log_enable_timestamps()

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


def populate_flow_list_output_file(network_controller_obj, filename, max_time=10, display_output=True,
                                   iteration=False):
    output = False
    try:
        master_table_obj = PrettyTable()
        master_table_obj.align = 'l'
        master_table_obj.header = False
        timer = FunTimer(max_time=max_time)
        lines = list()
        while not timer.is_expired():
            fun_test.sleep('Get flow list', seconds=1)
            result = network_controller_obj.get_flow_list()['data']
            if result:
                for key in sorted(result):
                    table_obj = inner_table_obj(result=result[key])
                    master_table_obj.add_row([key, table_obj])

                lines.append(master_table_obj.get_string())
                lines.append("\n########################  %s ########################\n" % str(get_timestamp()))

                if not iteration:
                    break

        file_path = fun_test.get_test_case_artifact_file_name(filename)
        with open(file_path, 'w') as f:
            f.writelines(lines)

        fun_test.add_auxillary_file(description=filename, filename=file_path)

        if display_output:
            fun_test.log_disable_timestamps()
            fun_test.log_section('Flow List output')
            for line in lines:
                fun_test.log(line)
            fun_test.log_enable_timestamps()
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


def populate_pc_resource_output_file(network_controller_obj, filename, pc_id, max_time=10, display_output=True,
                                     iteration=False):
    output = False
    try:
        lines = list()
        timer = FunTimer(max_time=max_time)
        while not timer.is_expired():
            fun_test.sleep(message="Peek stats resource pc %d" % pc_id, seconds=1)

            result = network_controller_obj.peek_resource_pc_stats(pc_id=pc_id)
            master_table_obj = get_nested_dict_stats(result=result)
            lines.append("\n########################  %s ########################\n" % str(get_timestamp()))
            lines.append(master_table_obj.get_string())
            lines.append('\n\n\n')

            if not iteration:
                break

        file_path = fun_test.get_test_case_artifact_file_name(filename)

        with open(file_path, 'a') as f:
            f.writelines(lines)

        fun_test.add_auxillary_file(description=filename, filename=file_path)

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

'''
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
'''
def _get_max_reference_keys(result, reference_cluster):
    reference_keys = reference_cluster.keys()
    num_keys = len(reference_keys)
    for key, val in result.iteritems():
        if len(val) > num_keys:
            reference_keys = val.keys()
    return reference_keys

def get_resource_bam_table(result):

    while True:
        try:
            cmd = "stats/resource/bam"
            if not result:
                break
            reference_keys = _get_max_reference_keys(result['bm_usage_per_cluster'],
                                                          result['bm_usage_per_cluster']['cluster_0'])
            gloabl_result = result['bm_usage_global']
            per_cluster_result = result['bm_usage_per_cluster']

            # Global table object
            global_table_obj = PrettyTable(['Field Name', 'Counter'])
            global_table_obj.align = 'l'
            for key, val in gloabl_result.iteritems():
                global_table_obj.add_row([key, val])

            # Per cluster table
            row_list = ['key names']
            for key in sorted(per_cluster_result.keys()):
                row_list.append(key[0].upper() + key[-1] + ":" + "%")
                row_list.append(key[0].upper() + key[-1] + ":" + "col")
            per_cluster_table_obj = PrettyTable()

            output = OrderedDict()
            for col_name in row_list:
                output[col_name] = []
                if col_name == 'key names':
                    output[col_name].extend(sorted(reference_keys))
                else:
                    cname = col_name.replace('C', 'cluster_')
                    cluster_name = cname.split(":")[0]
                    key_name = cname.split(":")[1]
                    if key_name == '%':
                        key_name = 'usage_percent'
                    elif key_name == 'col':
                        key_name = 'color'
                    cls_output = per_cluster_result[cluster_name]
                    for display_key in sorted(reference_keys):
                        if display_key in cls_output:
                            if key_name in cls_output[display_key]:
                                output[col_name].append(cls_output[display_key][key_name])
                            else:
                                output[col_name].append(0)
                        else:
                            output[col_name].append(0)
            print_keys = output.keys()
            print_values = output.values()
            for col_name, col_values in zip(print_keys, print_values):
                per_cluster_table_obj.add_column(col_name, col_values)

        except Exception as ex:
            fun_test.critical(str(ex))
        return global_table_obj, per_cluster_table_obj


def populate_resource_bam_output_file(network_controller_obj, filename, max_time=10, display_output=False):
    output = False
    try:
        lines = list()
        timer = FunTimer(max_time=max_time)
        while not timer.is_expired():
            fun_test.sleep(message="Peek stats resource BAM", seconds=1)

            result = network_controller_obj.peek_resource_bam_stats()
            master_table_obj1, master_table_obj2 = get_resource_bam_table(result=result)
            tab_obj = [master_table_obj1, master_table_obj2]
            for i in tab_obj:
                lines.append("\n########################  %s ########################\n" % str(get_timestamp()))
                lines.append(i.get_string())
                lines.append('\n\n\n')

        file_path = fun_test.get_test_case_artifact_file_name(filename)

        with open(file_path, 'a') as f:
            f.writelines(lines)

        fun_test.add_auxillary_file(description='DPC Resource BAM stats', filename=file_path)

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


def populate_vp_util_output_file(network_controller_obj, filename, display_output=True, max_time=10, iteration=True):
    output = False
    try:
        lines = list()
        timer = FunTimer(max_time=max_time)
        while not timer.is_expired():
            output = network_controller_obj.debug_vp_util()
            result = get_vp_util_filtered_dict(output=output)
            complete_dict = get_vp_util_parsed_data_dict(result=result)

            master_table_obj = get_vp_util_table_obj(complete_dict=complete_dict)

            # print normalized data
            normalized_value = get_normalized_data_vp_data(complete_dict=complete_dict)

            # print histogram
            histogram_table_obj = get_vp_util_histogram_table_obj(complete_dict=complete_dict)

            lines.append("\n########################  %s ########################\n" % str(get_timestamp()))
            lines.append("Normalized VP Util: {}".format(normalized_value))
            lines.append("\n\nHistogram table: Num of VPs in util range\n")
            lines.append(histogram_table_obj.get_string())
            lines.append('\n\nVP util table obj\n')
            lines.append(master_table_obj.get_string())
            lines.append('\n\n\n')
            if not iteration:
                break

        file_path = fun_test.get_test_case_artifact_file_name(filename)

        with open(file_path, 'a') as f:
            f.writelines(lines)

        fun_test.add_auxillary_file(description=filename, filename=file_path)

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


def run_netperf_concurrently(cmd_dict, network_controller_obj, display_output=False, num_flows=1,
                             collect_dpc_stats=True):
    result = {}
    try:
        version = fun_test.get_version()
        multi_task_obj = MultiProcessingTasks()
        index = 1
        total_netperf_processes = 0
        for linux_obj, cmd_list in cmd_dict.iteritems():
            duration = len(cmd_list) * 60
            total_netperf_processes = total_netperf_processes + len(cmd_list)
            for cmd in cmd_list:
                multi_task_obj.add_task(func=run_netperf,
                                        func_args=(linux_obj, cmd, duration),
                                        task_key="conn_%d" % index)
                index += 1

        flow_list_file = str(version) + "_" + str(num_flows) + '_flowlist.txt'
        resource_pc_file = str(version) + "_" + str(num_flows) + '_resource_pc.txt'
        resource_bam_file = str(version) + "_" + str(num_flows) + '_resource_bam.txt'
        vp_utils_file = str(version) + "_" + str(num_flows) + '_vp_utils.txt'

        # No need to add more task for dpcsh command instead start a thread after few secs of traffic to collect
        # dpcsh output
        '''
        multi_task_obj.add_task(func=run_dpcsh_commands,
                                func_args=(network_controller_obj, flow_list_file, resource_bam_file,
                                           resource_pc_file, display_output),
                                task_key='')
        '''
        thread_id = None
        if collect_dpc_stats:
            thread_id = fun_test.execute_thread_after(time_in_seconds=10, func=run_dpcsh_commands,
                                                      network_controller_obj=network_controller_obj,
                                                      flow_list_file=flow_list_file,
                                                      resource_bam_file=resource_bam_file,
                                                      vp_utils_file=vp_utils_file,
                                                      resource_pc_file=resource_pc_file,
                                                      display_output=display_output)

        run_started = multi_task_obj.run(max_parallel_processes=total_netperf_processes, parallel=True)
        fun_test.test_assert(run_started, "Ensure netperf commands started")
        if thread_id:
            fun_test.join_thread(fun_test_thread_id=thread_id, sleep_time=5)

        for index in range(1, total_netperf_processes + 1):
            task_key = 'conn_%d' % index
            res = multi_task_obj.get_result(task_key=task_key)
            result[task_key] = res

        all_throughputs = []
        for conn, val in result.iteritems():
            all_throughputs.append(val['throughput'])
        result['total_throughput'] = sum(all_throughputs)
    except Exception as ex:
        for linux_obj in cmd_dict:
            get_stale_socket_connections(linux_obj=linux_obj, port_value=4555)
        fun_test.critical(str(ex))
    return result


def run_dpcsh_commands(network_controller_obj, flow_list_file, resource_bam_file, resource_pc_file, vp_utils_file,
                       display_output=False, iteration=True):
    try:
        fun_test.add_checkpoint('Get flow list')
        populate_flow_list_output_file(network_controller_obj=network_controller_obj, filename=flow_list_file,
                                       display_output=display_output, iteration=iteration)

        fun_test.add_checkpoint('Get Resource pc id 1')
        populate_pc_resource_output_file(network_controller_obj=network_controller_obj,
                                         filename=resource_pc_file, pc_id=1, display_output=display_output,
                                         iteration=iteration)

        fun_test.add_checkpoint('Get Resource pc id 2')
        populate_pc_resource_output_file(network_controller_obj=network_controller_obj,
                                         filename=resource_pc_file, pc_id=2, display_output=display_output,
                                         iteration=iteration)

        fun_test.add_checkpoint('Get VP utils')
        populate_vp_util_output_file(network_controller_obj=network_controller_obj,
                                     filename=vp_utils_file, display_output=display_output, iteration=iteration)

        fun_test.add_checkpoint('Get Resource BAM')
        populate_resource_bam_output_file(network_controller_obj=network_controller_obj, filename=resource_bam_file,
                                          display_output=display_output)
    except Exception as ex:
        fun_test.critical(str(ex))
    return True


def run_tcpdump_command(linux_obj, tcp_dump_file, interface, snaplen=80, filecount=1, count=2000000, sudo=False):
    result = None
    try:
        cmd = "sudo tcpdump -leni %s tcp -w %s -s %d -W %d -c %d" % (interface, tcp_dump_file, snaplen,
                                                                     filecount, count)
        fun_test.log("tcpdump command formed: %s" % cmd)
        if sudo:
            cmd = "nohup tcpdump -leni %s tcp -w %s -s %d -W %d -c %d >/dev/null 2>&1 &" % (
                interface, tcp_dump_file, snaplen, filecount, count)
            linux_obj.sudo_command(command=cmd)
            process_id = linux_obj.get_process_id_by_pattern(process_pat="tcpdump")
        else:
            process_id = linux_obj.start_bg_process(command=cmd)
        fun_test.log("tcpdump started process id: %s" % process_id)
        if process_id:
            result = process_id
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def get_interface_name(file_path):
    interface_name = None
    try:
        with open(file_path, 'r') as f:
            contents = f.read()
            m = re.search(r'sudo\s+ifconfig\s+(\w+).*', contents, re.IGNORECASE)
            if m:
                interface_name = m.group(1)
        fun_test.log("Interface used: %s" % interface_name)
    except Exception as ex:
        fun_test.critical(str(ex))
    return interface_name


def run_netperf(linux_obj, cmd, duration=60):
    result = {"throughput": -1}
    try:
        pat = r'THROUGHPUT=(\d+)'
        output = linux_obj.command(cmd, timeout=duration + 30)
        match = re.search(pat, output, re.DOTALL)
        if match:
            throughput = float(match.group(1))
            result.update({'throughput': round(throughput, 3)})
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def get_netperf_cmd_list(dip, protocol='tcp', duration=60, num_flows=1, send_size="128K",
                         port1=1000, port2=4555, start_core_id=8, end_core_id=15):
    cmd_list = []
    try:
        if protocol.lower() == 'udp':
            t = 'UDP_STREAM'
        else:
            t = 'TCP_STREAM'

        cpu = start_core_id
        for conn in range(0, num_flows):
            if cpu > end_core_id:
                cpu = start_core_id
            cmd = "taskset -c %d netperf -t %s -H %s -l %s -f m -j -N -P 0 -- -k \"THROUGHPUT\" -s %s -P %d,%d " % (
                cpu, t, dip, duration, send_size, port1, port2
            )
            fun_test.log("Netperf cmd formed: %s\n" % cmd)
            cmd_list.append(cmd)
            cpu += 1
    except Exception as ex:
        fun_test.critical(str(ex))
    return cmd_list


def create_performance_table(total_throughput, num_flows, total_pps, no_of_runs=5):
    table_created = False
    try:
        headers = ['# of connections', 'Avg. Throughput of %d runs in Mbps' % no_of_runs,
                   'Avg PPS of %d runs' % no_of_runs]
        rows = []
        rows.append([num_flows, total_throughput, total_pps])
        table_name = 'Aggregate throughput and pps for %d of connections' % num_flows
        table_data = {'headers': headers, 'rows': rows}
        fun_test.add_table(panel_header="FunTCP server throughput",
                           table_name=table_name,
                           table_data=table_data)
        table_created = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return table_created


def find_max_cps_using_trex(network_controller_obj, trex_obj, astf_profile, base_cps, increment_count,
                            cpu=1, duration=60, end_cps=None):
    result = {'max_cps': -1, 'max_latency': -1, 'avg_latency': -1, 'status': False, 'summary_dict': None}
    output_file_path = fun_test.get_temp_file_path(file_name=fun_test.get_temp_file_name()) + ".txt"
    try:
        count = 1
        max_cps_found = False
        version = fun_test.get_version()
        profile_name = astf_profile.split('/')[1].split('.')[0]
        flow_list_file = str(version) + "_" + profile_name + '_flowlist.txt'
        resource_pc_file = str(version) + "_" + profile_name + '_resource_pc.txt'
        resource_bam_file = str(version) + "_" + profile_name + '_resource_bam.txt'
        vp_utils_file = str(version) + "_" + profile_name + '_vp_utils.txt'
        cps = base_cps
        while True:
            if end_cps and cps >= end_cps:
                break
            if max_cps_found:
                break
            if count == 1:
                cps = base_cps
            else:
                cps += increment_count

            fun_test.log_section("Find Max CPS and latency for %s. Base CPS Given: %d "
                                 "Current iteration count: %d Current CPS value: %d" % (profile_name,
                                                                                        base_cps, count, cps))
            cmd = trex_obj.get_trex_cmd(astf_profile=astf_profile, astf=True, duration=duration, latency=True,
                                        warmup_time=5, latency_packet_rate=100, cps_rate=cps, cpu=cpu,
                                        output_file=output_file_path, bg=True)
            fun_test.simple_assert(cmd, "Get TRex cps command")

            checkpoint = "Execute TRex command"
            output = trex_obj.execute_trex_command(cmd=cmd, timeout=duration)
            fun_test.test_assert(output, checkpoint)

            checkpoint = "Running dpcsh commands to capture stats during run"
            output = run_dpcsh_commands(network_controller_obj=network_controller_obj,
                                        flow_list_file=flow_list_file,
                                        resource_bam_file=resource_bam_file, resource_pc_file=resource_pc_file,
                                        iteration=True, display_output=False, vp_utils_file=vp_utils_file)
            fun_test.simple_assert(output, checkpoint)

            fun_test.simple_assert(trex_obj.poll_for_trex_process(max_time=duration), "Ensure TRex process finish")

            checkpoint = "Parse TRex output file"
            summary = trex_obj.read_trex_output_summary(file_path=output_file_path)
            fun_test.simple_assert(summary, checkpoint)

            checkpoint = "Collect summary stats for %d iteration" % count
            summary_dict = trex_obj.get_trex_summary_stats(summary_contents=summary)
            fun_test.simple_assert(summary_dict, checkpoint)

            checkpoint = "Summary Table for Iteration: %d CPS: %d Profile: %s" % (count, cps, profile_name)
            trex_obj.pretty_print_summary_dict(summary_dict=summary_dict, table_header=checkpoint)
            fun_test.add_checkpoint(checkpoint)

            checkpoint = "Validate summary stats"
            validate_stats = validate_summary_stats(summary_dict=summary_dict)
            if validate_stats:
                result['max_cps'] = cps
                result['max_latency'] = summary_dict['max_latency']
                result['avg_latency'] = summary_dict['avg_latency']
                result['status'] = True
                result['summary_dict'] = summary_dict
            else:
                if cps != base_cps and 'max_cps' in result:
                    fun_test.log(
                        "<=======> FAILED Iteration: %d CPS: %d Profile: %s <=======>" % (count, cps, profile_name),
                        fun_test.LOG_LEVEL_CRITICAL)
                    fun_test.log("<=======> Last Successful CPS was %d in iteration %d <=======>" % (result['max_cps'],
                                                                                                     count - 1))
                    max_cps_found = True
                else:
                    fun_test.log(
                        "<=======> FAILED Iteration: %d Base CPS: %d Profile: %s <=======>" % (count, cps,
                                                                                               profile_name),
                        fun_test.LOG_LEVEL_CRITICAL)
                    result['status'] = True
                    result['summary_dict'] = summary_dict
                    break
            fun_test.add_checkpoint(checkpoint)
            count += 1
    except Exception as ex:
        fun_test.critical(str(ex))
    finally:
        trex_obj.sudo_command(command="rm -rf %s" % output_file_path)
    return result


def validate_summary_stats(summary_dict):
    result = False
    try:
        if 'tcps_conn_attempt' in summary_dict['client'] and 'tcps_connects' in summary_dict['client']:
            fun_test.test_assert_expected(expected=summary_dict['client']['tcps_conn_attempt'],
                                          actual=summary_dict['client']['tcps_connects'],
                                          message='Ensure TCP connections attempted equal to connections established.',
                                          ignore_on_success=True)

        fun_test.simple_assert('embryonic_tcp_conn_drops' not in summary_dict['client'],
                               "check for embryonic connections dropped")
        fun_test.simple_assert('tcps_retransmit_syn_timeouts' not in summary_dict['client'],
                               "check for retransmit SYN timeouts")
        fun_test.simple_assert('tcps_keepalive_timeouts' not in summary_dict['client'], "check for keepalive timeouts")
        fun_test.simple_assert('tcps_conn_keepalive_drops' not in summary_dict['client'],
                               "check for connections dropped in keepalive")
        fun_test.simple_assert('max_latency' in summary_dict, "check for max latency")
        fun_test.simple_assert('avg_latency' in summary_dict, "check for avg latency")
        result = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


if __name__ == '__main__':
    from lib.host.network_controller import NetworkController
    nw = NetworkController(dpc_server_ip="fs48-come", dpc_server_port=40220)
    populate_vp_util_output_file(network_controller_obj=nw, filename='output_vp_util.txt')