from lib.system.fun_test import *
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper
import re
from prettytable import PrettyTable
import time
from collections import OrderedDict
from lib.host.storage_controller import StorageController
from lib.system import utils
from threading import Lock

DPCSH_COMMAND_TIMEOUT = 30

fio_perf_table_header = ["Block Size", "IO Depth", "Size", "Operation", "Write IOPS", "Read IOPS",
                         "Write Throughput in KB/s", "Read Throughput in KB/s", "Write Latency in uSecs",
                         "Write Latency 90 Percentile in uSecs", "Write Latency 95 Percentile in uSecs",
                         "Write Latency 99 Percentile in uSecs", "Write Latency 99.99 Percentile in uSecs",
                         "Read Latency in uSecs", "Read Latency 90 Percentile in uSecs",
                         "Read Latency 95 Percentile in uSecs", "Read Latency 99 Percentile in uSecs",
                         "Read Latency 99.99 Percentile in uSecs", "fio_job_name"]
fio_perf_table_cols = ["block_size", "iodepth", "size", "mode", "writeiops", "readiops", "writebw", "readbw",
                       "writeclatency", "writelatency90", "writelatency95", "writelatency99", "writelatency9999",
                       "readclatency", "readlatency90", "readlatency95", "readlatency99", "readlatency9999",
                       "fio_job_name"]

vp_stats_thread_stop_status = {}
resource_bam_stats_thread_stop_status = {}
unpacked_stats = {}


class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def post_results(volume, test, log_time, num_ssd, num_volumes, block_size, io_depth, size, operation, write_iops,
                 read_iops,
                 write_bw, read_bw, write_latency, write_90_latency, write_95_latency, write_99_latency,
                 write_99_99_latency, read_latency, read_90_latency, read_95_latency, read_99_latency,
                 read_99_99_latency, fio_job_name):
    for i in ["write_iops", "read_iops", "write_bw", "read_bw", "write_latency", "write_90_latency", "write_95_latency",
              "write_99_latency", "write_99_99_latency", "read_latency", "read_90_latency", "read_95_latency",
              "read_99_latency", "read_99_99_latency", "fio_job_name"]:
        if eval("type({}) is tuple".format(i)):
            exec ("{0} = {0}[0]".format(i))

    blt = BltVolumePerformanceHelper()
    blt.add_entry(date_time=log_time,
                  volume=volume,
                  test=test,
                  block_size=block_size,
                  io_depth=int(io_depth),
                  size=size,
                  operation=operation,
                  num_ssd=num_ssd,
                  num_volume=num_volumes,
                  fio_job_name=fio_job_name,
                  write_iops=write_iops,
                  read_iops=read_iops,
                  write_throughput=write_bw,
                  read_throughput=read_bw,
                  write_avg_latency=write_latency,
                  read_avg_latency=read_latency,
                  write_90_latency=write_90_latency,
                  write_95_latency=write_95_latency, write_99_latency=write_99_latency,
                  write_99_99_latency=write_99_99_latency, read_90_latency=read_90_latency,
                  read_95_latency=read_95_latency, read_99_latency=read_99_latency,
                  read_99_99_latency=read_99_99_latency, write_iops_unit="ops",
                  read_iops_unit="ops", write_throughput_unit="MBps", read_throughput_unit="MBps",
                  write_avg_latency_unit="usecs", read_avg_latency_unit="usecs", write_90_latency_unit="usecs",
                  write_95_latency_unit="usecs", write_99_latency_unit="usecs", write_99_99_latency_unit="usecs",
                  read_90_latency_unit="usecs", read_95_latency_unit="usecs", read_99_latency_unit="usecs",
                  read_99_99_latency_unit="usecs")

    result = []
    arg_list = post_results.func_code.co_varnames[:12]
    for arg in arg_list:
        result.append(str(eval(arg)))
    result = ",".join(result)
    fun_test.log("Result: {}".format(result))


def compare(actual, expected, threshold, operation):
    if operation == "lesser":
        return actual < (expected * (1 - threshold)) and ((expected - actual) > 2)
    else:
        return actual > (expected * (1 + threshold)) and ((actual - expected) > 2)


def fetch_nvme_device(end_host, nsid, size=None):
    lsblk_output = end_host.lsblk("-b")
    fun_test.simple_assert(lsblk_output, "Listing available volumes")
    result = {'status': False}
    if size:
        for volume_name in lsblk_output:
            if int(lsblk_output[volume_name]["size"]) == size:
                result['volume_name'] = volume_name
                result['nvme_device'] = "/dev/{}".format(result['volume_name'])
                result['status'] = True
                break
    else:
        for volume_name in lsblk_output:
            match = re.search(r'nvme\dn{}'.format(nsid), volume_name, re.I)
            if match:
                result['volume_name'] = match.group()
                result['nvme_device'] = "/dev/{}".format(result['volume_name'])
                result['status'] = True
                break
    return result


def fetch_numa_cpus(end_host, ethernet_adapter):
    numa_cpus = None
    lspci_output = end_host.lspci(grep_filter=ethernet_adapter)
    fun_test.simple_assert(lspci_output, "Ethernet Adapter Detected")
    adapter_id = lspci_output[0]['id']
    fun_test.simple_assert(adapter_id, "Retrieve Ethernet Adapter Bus ID")
    lspci_verbose_output = end_host.lspci(slot=adapter_id, verbose=True)
    numa_node = lspci_verbose_output[0]['numa_node']
    fun_test.test_assert(numa_node, "Ethernet Adapter NUMA Node Retrieved")

    # Fetching NUMA CPUs for above fetched NUMA Node
    lscpu_output = end_host.lscpu(grep_filter="node{}".format(numa_node))
    fun_test.simple_assert(lscpu_output, "CPU associated to Ethernet Adapter NUMA")

    numa_cpus = lscpu_output.values()[0]
    fun_test.test_assert(numa_cpus, "CPU associated to Ethernet Adapter NUMA")
    fun_test.log("Ethernet Adapter: {}, NUMA Node: {}, NUMA CPU: {}".format(ethernet_adapter, numa_node, numa_cpus))
    return numa_cpus


def enable_counters(storage_controller, timeout=30):
    fun_test.test_assert(storage_controller.command(command="enable_counters",
                                                    legacy=True,
                                                    command_duration=timeout)["status"],
                         message="Enabling counters on DUT")


def configure_fs_ip(storage_controller, ip):
    command_result = storage_controller.ip_cfg(ip=ip)
    fun_test.test_assert(command_result["status"], "ip_cfg configured on DUT instance")


def disable_error_inject(storage_controller, timeout=30):
    command_result = storage_controller.poke("params/ecvol/error_inject 0",
                                             command_duration=timeout)
    fun_test.test_assert(command_result["status"], "Disabling error_injection for EC volume on DUT")

    # Ensuring that the error_injection got disabled properly
    fun_test.sleep("Sleeping for a second to disable the error_injection", 1)
    command_result = storage_controller.peek("params/ecvol", command_duration=timeout)
    fun_test.test_assert(command_result["status"], "Retrieving error_injection status on DUT")
    fun_test.test_assert_expected(actual=int(command_result["data"]["error_inject"]),
                                  expected=0,
                                  message="Ensuring error_injection got disabled")


def set_syslog_level(storage_controller, log_level, timeout=30):
    command_result = storage_controller.poke(props_tree=["params/syslog/level", log_level],
                                             legacy=False,
                                             command_duration=timeout)
    fun_test.test_assert(command_result["status"], "Setting syslog level to {}".format(log_level))

    command_result = storage_controller.peek(props_tree="params/syslog/level",
                                             legacy=False,
                                             command_duration=timeout)
    fun_test.test_assert_expected(expected=log_level,
                                  actual=command_result["data"],
                                  message="Checking syslog level")


def load_nvme_module(end_host):
    end_host.modprobe(module="nvme")
    fun_test.sleep("Loading nvme module", 2)
    command_result = end_host.lsmod(module="nvme")
    fun_test.test_assert_expected(expected="nvme", actual=command_result['name'], message="Loading nvme module")


def load_nvme_tcp_module(end_host):
    end_host.modprobe(module="nvme_tcp")
    fun_test.sleep("Loading nvme_tcp module", 2)
    command_result = end_host.lsmod(module="nvme_tcp")
    fun_test.simple_assert(command_result, "Loading nvme_tcp module")
    fun_test.test_assert_expected(expected="nvme_tcp",
                                  actual=command_result['name'],
                                  message="Loading nvme_tcp module")


def configure_endhost_interface(end_host, test_network, interface_name, timeout=30):
    interface_ip_unconfig = "ip addr del {} dev {}".format(test_network["test_interface_ip"],
                                                           interface_name)
    interface_ip_config = "ip addr add {} dev {}".format(test_network["test_interface_ip"],
                                                         interface_name)
    interface_mac_config = "ip link set {} address {}".format(interface_name,
                                                              test_network["test_interface_mac"])
    link_up_cmd = "ip link set {} up".format(interface_name)
    static_arp_cmd = "arp -s {} {}".format(test_network["test_net_route"]["gw"],
                                           test_network["test_net_route"]["arp"])

    end_host.sudo_command(command=interface_ip_unconfig, timeout=timeout)
    end_host.sudo_command(command=interface_ip_config, timeout=timeout)
    fun_test.test_assert_expected(expected=0,
                                  actual=end_host.exit_status(),
                                  message="Configuring test interface IP address")

    end_host.sudo_command(command=interface_mac_config)
    fun_test.test_assert_expected(expected=0,
                                  actual=end_host.exit_status(),
                                  message="Assigning MAC to test interface")

    end_host.sudo_command(command=link_up_cmd,
                          timeout=timeout)
    fun_test.test_assert_expected(expected=0,
                                  actual=end_host.exit_status(),
                                  message="Bringing up test link")

    fun_test.test_assert(end_host.ifconfig_up_down(interface=interface_name,
                                                   action="up"), "Bringing up test interface")

    end_host.ip_route_add(network=test_network["test_net_route"]["net"],
                          gateway=test_network["test_net_route"]["gw"],
                          outbound_interface=interface_name,
                          timeout=timeout)
    fun_test.test_assert_expected(expected=0,
                                  actual=end_host.exit_status(),
                                  message="Adding route to F1")

    end_host.sudo_command(command=static_arp_cmd,
                          timeout=timeout)
    fun_test.test_assert_expected(expected=0,
                                  actual=end_host.exit_status(),
                                  message="Adding static ARP to F1 route")


def build_simple_table(data, column_headers=[], split_values_to_columns=False):
    simple_table = PrettyTable(column_headers)
    simple_table.align = 'l'
    simple_table.border = True
    simple_table.header = True
    try:
        for key in sorted(data):
            row_data = []
            if type(data[key]) is list and split_values_to_columns:
                row_data.append(key)
                row_data.extend(data[key])
            else:
                row_data = [key, data[key]]
            simple_table.add_row(row_data)
    except Exception as ex:
        fun_test.critical(str(ex))
    return simple_table


def check_come_health(storage_controller):
    blt_vol_info = {
        "type": "VOL_TYPE_BLK_LOCAL_THIN",
        "capacity": 10485760,
        "block_size": 4096,
        "name": "thin-block1"}
    result = False
    try:
        blt_uuid = utils.generate_uuid()
        response = storage_controller.create_thin_block_volume(capacity=blt_vol_info["capacity"],
                                                               block_size=blt_vol_info["block_size"],
                                                               name=blt_vol_info['name'],
                                                               uuid=blt_uuid,
                                                               command_duration=30)
        if response["status"]:
            result = True
    except Exception as ex:
        fun_test.critical(ex.message)
    return result


def _convert_vp_util(value):
    value = "{:.0f}".format(value * 100)
    """
    if int(value) >= 50:
        value = colors.WARNING + str(value) + colors.ENDC
    elif int(value) >= 75:
        value = colors.BOLD + colors.WARNING + str(value) + colors.ENDC
    elif int(value) >= 90:
        value = colors.BOLD + colors.FAIL + str(value) + colors.ENDC
    """
    return value


def get_ec_vol_uuids(ec_info):
    ec_details = []
    for num in range(ec_info["num_volumes"]):
        vol_group = {ec_info["volume_types"]["ndata"]: ec_info["uuids"][num]["blt"],
                     ec_info["volume_types"]["ec"]: ec_info["uuids"][num]["ec"],
                     ec_info["volume_types"]["jvol"]: [ec_info["uuids"][num]["jvol"]],
                     ec_info["volume_types"]["lsv"]: ec_info["uuids"][num]["lsv"]}
        ec_details.append(vol_group)
    return ec_details


def initiate_stats_collection(storage_controller, interval, count, vp_util_artifact_file=None,
                              vol_stats_artifact_file=None, bam_stats_articat_file=None, vol_details=None):
    stats_collector = CollectStats(storage_controller=storage_controller)
    result = {'status': False,
              'vp_util_thread_id': None,
              'vol_stats_thread_id': None,
              'bam_stats_thread_id': None}
    if vp_util_artifact_file:
        result['vp_util_thread_id'] = fun_test.execute_thread_after(time_in_seconds=0.5,
                                                                    func=stats_collector.collect_vp_utils_stats,
                                                                    output_file=vp_util_artifact_file,
                                                                    interval=interval,
                                                                    count=count,
                                                                    threaded=True)
    if vol_stats_artifact_file:
        result['vol_stats_thread_id'] = fun_test.execute_thread_after(time_in_seconds=interval / 3,
                                                                      func=stats_collector.collect_vol_stats,
                                                                      output_file=vol_stats_artifact_file,
                                                                      vol_details=vol_details,
                                                                      interval=interval,
                                                                      count=count,
                                                                      threaded=True)
    if bam_stats_articat_file:
        result['bam_stats_thread_id'] = fun_test.execute_thread_after(time_in_seconds=(interval * 2) / 3,
                                                                      func=stats_collector.collect_resource_bam_stats,
                                                                      output_file=bam_stats_articat_file,
                                                                      interval=interval,
                                                                      count=count,
                                                                      threaded=True)
    result['status'] = True
    return result


def terminate_stats_collection(stats_ollector_obj, thread_list):
    for thread in thread_list:
        fun_test.join_thread(fun_test_thread_id=thread, sleep_time=1)

    reset_collector = False
    for thread in thread_list:
        if fun_test.fun_test_threads[thread]["thread"].is_alive():
            reset_collector = True
    if reset_collector:
        stats_ollector_obj.stop_all = True
        stats_ollector_obj.stop_vol_stats = True
        stats_ollector_obj.stop_vp_utils = True
        stats_ollector_obj.stop_resource_bam = True


def vol_stats_diff(initial_vol_stats, final_vol_stats, vol_details):
    """
    :param initial_vol_stats: volume stats collected at the start of test
    :param final_vol_stats: volume stats collected at the end of test
    :param vol_details: list of dictionary containing volume details, type, uuid
    :return: dictionary, with status, stats_diff and total_diff
    """
    result = {"status": False, "stats_diff": None, "total_diff": None}
    dict_vol_details = {}
    stats_diff = {}
    # blt_combined_stat = {}
    total_diff = {}
    stats_exclude_list = ["drive_uuid", "extent_size", "fault_injection", "flvm_block_size", "flvm_vol_size_blocks",
                          "se_size"]
    aggregated_diff_stats_list = ["write_bytes", "read_bytes"]
    try:
        # Forming a dictionary for provided vol_details
        for x in range(len(vol_details)):
            dict_vol_details[x] = vol_details[x]
        for i, vol_group in dict_vol_details.iteritems():
            stats_diff[i] = {}
            # blt_combined_stat[i] = {}
            for vol_type, vol_uuids in sorted(vol_group.iteritems()):
                if vol_type not in stats_diff:
                    stats_diff[i][vol_type] = {}
                for vol_uuid in vol_uuids:
                    if vol_uuid not in stats_diff[i][vol_type]:
                        stats_diff[i][vol_type][vol_uuid] = {}
                    if (vol_type in final_vol_stats and vol_uuid in final_vol_stats[vol_type]) and (
                            vol_type in initial_vol_stats and vol_uuid in initial_vol_stats[vol_type]):
                        for stats_field in set(final_vol_stats[vol_type][vol_uuid]["stats"]) - set(stats_exclude_list):
                            # if stats_field not in blt_combined_stat[i]:
                            #    blt_combined_stat[i][stats_field] = 0
                            stats_diff[i][vol_type][vol_uuid][stats_field] = \
                                final_vol_stats[vol_type][vol_uuid]["stats"][stats_field] - initial_vol_stats[
                                    vol_type][vol_uuid]["stats"][stats_field]
                            # To have agrregated BLT stats under each EC volume,
                            # all volumes BLT stats are collected in total_diff
                            #
                            # if vol_type == "VOL_TYPE_BLK_LOCAL_THIN":
                            #    if blt_combined_stat[i][stats_field] == 0:
                            #        stats_diff[i][vol_type]['blt_combined'] = {}
                            #        stats_diff[i][vol_type]['blt_combined'][stats_field] = {}
                            #    blt_combined_stat[i][stats_field] = blt_combined_stat[i][stats_field] + \
                            #                                        stats_diff[i][vol_type][vol_uuid][stats_field]
                            #    stats_diff[i][vol_type]['blt_combined'][stats_field] = blt_combined_stat[i][
                            #        stats_field]

        for i, vol_group in stats_diff.iteritems():
            for vol_type, vol_uuids in sorted(vol_group.iteritems()):
                if vol_type not in total_diff:
                    total_diff[vol_type] = {}
                for vol_uuid in vol_uuids:
                    # if vol_uuid != "blt_combined":
                    for stats_field in aggregated_diff_stats_list:
                        if stats_field not in total_diff[vol_type]:
                            total_diff[vol_type][stats_field] = 0
                        total_diff[vol_type][stats_field] = total_diff[vol_type][stats_field] + \
                                                            stats_diff[i][vol_type][vol_uuid][stats_field]
        result["status"] = True
        result["stats_diff"] = stats_diff
        result["total_diff"] = total_diff
    except Exception as ex:
        fun_test.critical(str(ex))
        result["status"] = False

    return result


def unpack_nested_dict(input_dict, prefix=''):
    for key, value in sorted(input_dict.items()):
        if isinstance(value, dict):
            unpack_nested_dict(value, '{}{}_'.format(prefix, key))
        else:
            unpacked_stats["{}{}".format(prefix, key)] = value
    return unpacked_stats


def get_diff_results(old_result, new_result):
    result = {}
    try:
        for key, val in new_result.iteritems():
            if isinstance(val, dict):
                result[key] = get_diff_results(old_result=old_result[key], new_result=new_result[key])
            elif isinstance(val, list):
                result[key] = []
                try:
                    result[key].append(map(subtract, val, old_result[key]))
                except Exception as ex:
                    fun_test.critical(str(ex))
            else:
                if not key in old_result:
                    old_result[key] = 0
                result[key] = new_result[key] - old_result[key]
    except Exception as ex:
        fun_test.critical(str(ex))
    return result


def subtract(a, b):
    a = 0 if not a else a
    b = 0 if not b else b
    return a - b


def divide(n, d):
    return n/d if d else 0


class CollectStats(object):
    def __init__(self, storage_controller):
        self.storage_controller = storage_controller
        self.socket_lock = Lock()
        self.stop_all = False
        self.stop_vp_utils = False
        self.stop_per_vp_stats = False
        self.stop_resource_bam = False
        self.stop_vol_stats = False
        self.stop_vppkts_stats = False
        self.stop_psw_stats = False
        self.stop_fcp_stats = False
        self.stop_wro_stats = False
        self.stop_erp_stats = False
        self.stop_etp_stats = False
        self.stop_eqm_stats = False
        self.stop_hu_stats = False
        self.stop_ddr_stats = False
        self.stop_ca_stats = False
        self.stop_cdu_stats = False

    def collect_vp_utils_stats(self, output_file, interval=10, count=3, non_zero_stats_only=True, threaded=True,
                               chunk=8192, command_timeout=DPCSH_COMMAND_TIMEOUT):
        output = False
        column_headers = ["Cluster/Core", "Thread 0", "Thread 1", "Thread 2", "Thread 3"]

        try:
            with open(output_file, 'a') as f:
                timer = FunTimer(max_time=interval * count)
                while not timer.is_expired():
                    lines = []
                    if threaded and (self.stop_vp_utils or self.stop_all):
                        fun_test.log("Stopping VP Utils stats collection thread")
                        break
                    self.socket_lock.acquire()
                    vp_utils_result = self.storage_controller.debug_vp_util(chunk=chunk, command_timeout=command_timeout)
                    self.socket_lock.release()
                    # fun_test.simple_assert(vp_util_result["status"], "Pulling VP Utilization")
                    if vp_utils_result["status"] and vp_utils_result["data"] is not None:
                        vp_util = vp_utils_result["data"]
                    else:
                        vp_util = {}

                    # Grouping the output based on its cluster & core level. That is, all the four hardware threads
                    # utilization will be added into a list and assigned to it attribute having its cluster and core
                    filtered_vp_util = OrderedDict()
                    for key, value in sorted(vp_util.iteritems()):
                        cluster_id = key.split(".")[0][3]
                        core_id = key.split(".")[1]
                        new_key = "{}/{}".format(cluster_id, core_id)
                        if new_key not in filtered_vp_util:
                            filtered_vp_util[new_key] = []
                        filtered_vp_util[new_key].append(_convert_vp_util(value))

                    # Filling the gap for the central cluster which has only 2 threads in a core
                    for core in range(4):
                        for thread in range(2, 4):
                            key = "8/{}".format(core)
                            if key in filtered_vp_util and type(filtered_vp_util[key]) is list:
                                filtered_vp_util[key].append("N/A")

                    # Eliminate the cluster/core whose threads is at 0% utilization
                    if non_zero_stats_only:
                        for key, value in filtered_vp_util.items():
                            delete_key = True
                            for thread_util in value:
                                if thread_util != "0" and thread_util != "N/A":
                                    delete_key = False
                                    break
                            if delete_key:
                                del(filtered_vp_util[key])

                    table_data = build_simple_table(data=filtered_vp_util, column_headers=column_headers,
                                                    split_values_to_columns=True)
                    lines.append("\n########################  {} ########################\n".format(time.ctime()))
                    lines.append(table_data.get_string())
                    lines.append("\n\n")
                    f.writelines(lines)
                    fun_test.sleep("for the next iteration - VP utils stats collection", seconds=interval)
            output = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return output

    def collect_per_vp_stats(self, output_file, interval=10, count=3, threaded=True, include_cc=False, chunk=8192,
                             display_diff=True, command_timeout=DPCSH_COMMAND_TIMEOUT):
        output = False
        per_vp_stats_key = ["wus_received", "vp_wu_qdepth", "wus_sent"]
        per_vp_stats_header = ["rx", "lo_q", "hi_q", "tx"]
        column_headers = ["Cluster/Core"]
        for thread in range(4):
            for header in per_vp_stats_header:
                column_headers.append("{}:{}".format(thread, header))
                if display_diff:
                    column_headers.append("{}:{}_d".format(thread, header))
        try:
            with open(output_file, 'a') as f:
                timer = FunTimer(max_time=interval * count)
                while not timer.is_expired():
                    lines = []
                    # Checking whether to continue/stop this threaded execution
                    if threaded and (self.stop_per_vp_stats or self.stop_all):
                        fun_test.log("Stopping per VP stats collection thread")
                        break

                    # Pulling the per_vp stats once or twice with one second interval based on the display_diff
                    self.socket_lock.acquire()
                    per_vp_result = self.storage_controller.peek(props_tree="stats/per_vp", legacy=False, chunk=chunk,
                                                                 command_duration=command_timeout)
                    self.socket_lock.release()

                    if per_vp_result["status"] and per_vp_result["data"] is not None:
                        self.new_per_vp_stats = per_vp_result["data"]
                    else:
                        self.new_per_vp_stats = {}

                    if display_diff:
                        if not hasattr(self, "old_per_vp_stats"):
                            self.old_per_vp_stats = self.new_per_vp_stats
                        diff_per_vp_stats = get_diff_results(old_result=self.old_per_vp_stats,
                                                             new_result=self.new_per_vp_stats)
                        self.old_per_vp_stats = self.new_per_vp_stats

                    # Removing the Central Cluster(if needed) and the redundant WU received and sent from the high queue
                    filtered_new_per_vp_stats = OrderedDict()
                    filtered_diff_per_vp_stats = OrderedDict()
                    for key in sorted(self.new_per_vp_stats):
                        if key.split(":")[0][2] == '8' and not include_cc:
                            continue
                        filtered_new_per_vp_stats[key] = self.new_per_vp_stats.get(key, {})
                        if display_diff:
                            filtered_diff_per_vp_stats[key] = diff_per_vp_stats.get(key, {})

                    processed_per_vp_stats = OrderedDict()
                    # Sorting the keys using the cluster ID(FA*0*:10:0[VP]) as the primary key and the
                    # core ID(FA0:*10*:0[VP]) as the secondary key
                    for key in sorted(filtered_new_per_vp_stats, key=lambda key: (int(key.split(":")[0][2]),
                                                                                  int(key.split(":")[1]))):
                        cluster_id = key.split(":")[0][2]
                        core_id = (int(key.split(":")[1]) / 4) - 2
                        thread_id = int(key.split(":")[1]) % 4
                        queue_id = int(key.split(":")[2][0])
                        if queue_id == 1:
                            continue
                        new_key = "{}/{}".format(cluster_id, core_id)
                        if new_key not in processed_per_vp_stats:
                            processed_per_vp_stats[new_key] = []
                        for subkey in per_vp_stats_key:
                            processed_per_vp_stats[new_key].append(filtered_new_per_vp_stats[key][subkey])
                            if display_diff:
                                if key in filtered_diff_per_vp_stats:
                                    processed_per_vp_stats[new_key].append(filtered_diff_per_vp_stats[key][subkey])
                                else:
                                    processed_per_vp_stats[new_key].append("N/A")
                            # Add the high queue depth and its difference as well
                            if subkey == "vp_wu_qdepth":
                                nextkey = key.replace("0[VP]", "1[VP]")
                                processed_per_vp_stats[new_key].append(filtered_new_per_vp_stats[nextkey][subkey])
                                if display_diff:
                                    if nextkey in filtered_diff_per_vp_stats:
                                        processed_per_vp_stats[new_key].append(filtered_diff_per_vp_stats[nextkey][subkey])
                                    else:
                                        processed_per_vp_stats[new_key].append("N/A")

                    table_data = build_simple_table(data=processed_per_vp_stats, column_headers=column_headers,
                                                    split_values_to_columns=True)
                    lines.append("\n########################  {} ########################\n".format(time.ctime()))
                    lines.append(table_data.get_string())
                    lines.append("\n\n")
                    f.writelines(lines)
                    fun_test.sleep("for the next iteration - per VP stats collection", seconds=interval)
            output = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return output

    def collect_resource_bam_stats(self, output_file, interval=10, count=3, threaded=True,
                                   command_timeout=DPCSH_COMMAND_TIMEOUT):
        output = False
        column_headers = ["Field Name", "Counters"]

        try:
            with open(output_file, 'a') as f:
                timer = FunTimer(max_time=interval * count)
                while not timer.is_expired():
                    lines = []
                    if threaded and (self.stop_resource_bam or self.stop_all):
                        fun_test.log("Stopping Resource BAM stats collection thread")
                        break
                    self.socket_lock.acquire()
                    bam_result = self.storage_controller.peek_resource_bam_stats(command_timeout=command_timeout)
                    self.socket_lock.release()
                    if bam_result["status"] and bam_result["data"] is not None:
                        resource_bam_stats = bam_result["data"]
                    else:
                        resource_bam_stats = {}

                    table_data = build_simple_table(data=resource_bam_stats, column_headers=column_headers)
                    lines.append("\n########################  {} ########################\n".format(time.ctime()))
                    lines.append(table_data.get_string())
                    lines.append("\n\n")
                    f.writelines(lines)
                    fun_test.sleep("for the next iteration - Resource BAM stats collection", seconds=interval)
            output = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return output

    def collect_vol_stats(self, vol_details, output_file="/dev/null", interval=10, count=3, non_zero_stats_only=True,
                          chunk=8192, threaded=True, command_timeout=DPCSH_COMMAND_TIMEOUT):
        """
        :param output_file: File name in which the volume stats collected at every given interval for given number of
        counts in the table format
        :param vol_details: Takes a list of dictionaries as its value. Each element is a dictionary whose attributes
        will be volumes types and the attribute value the list of volume UUID of that particular volume type.
        The expected format here is:
            vol_details = [{"VOLUME_TYPE1": [UUID1, UUID2, ...], "VOLUME_TYPE2": [UUID1], ...},
                           {"VOLUME_TYPE1": [UUID1, UUID2, ...], "VOLUME_TYPE2": [UUID1], ...}]
        For Example:
            vol_details = [{"VOL_TYPE_BLK_THIN_LOCAL": [UUID1, UUID2, ...], "VOL_TYPE_BLK_EC": [UUID1]},
                           {"VOL_TYPE_BLK_THIN_LOCAL": [UUID1, UUID2, ...], "VOL_TYPE_BLK_EC": [UUID1]}]
        :param interval:
        :param count:
        :param non_zero_stats_only:
        :param threaded:
        :param command_timeout:
        :param chunk:
        :return:
        """
        output = False

        try:
            with open(output_file, 'a') as f:
                timer = FunTimer(max_time=interval * count)
                while not timer.is_expired():
                    if threaded and (self.stop_vol_stats or self.stop_all):
                        fun_test.log("Stopping Volume stats collection thread")
                        break
                    self.socket_lock.acquire()
                    vol_stats_result = self.storage_controller.peek(props_tree="storage/volumes", legacy=False,
                                                                    chunk=chunk, command_duration=command_timeout)
                    self.socket_lock.release()
                    if vol_stats_result["status"] and vol_stats_result["data"] is not None:
                        all_vol_stats = vol_stats_result["data"]
                    else:
                        all_vol_stats = {}

                    lines = "\n########################  {} ########################\n".format(time.ctime())
                    f.writelines(lines)
                    # Extracting the required volume stats from the complete peek storage/volumes output
                    for vol_group in vol_details:
                        lines = []
                        column_headers = ["Stats"]
                        for vol_type, vol_uuids in sorted(vol_group.iteritems()):
                            vol_type = vol_type[13:]
                            for vol_uuid in vol_uuids:
                                column_headers.append(vol_type + "/" + vol_uuid[-8:])

                        vol_stats = {}
                        for vol_type, vol_uuids in sorted(vol_group.iteritems()):
                            if vol_type not in vol_stats:
                                vol_stats[vol_type] = {}
                            for vol_uuid in vol_uuids:
                                if vol_uuid not in vol_stats[vol_type]:
                                    vol_stats[vol_type][vol_uuid] = {}
                                if vol_type in all_vol_stats and vol_uuid in all_vol_stats[vol_type]:
                                    vol_stats[vol_type][vol_uuid] = all_vol_stats[vol_type][vol_uuid]["stats"]

                        all_attributes = set()
                        for vol_type, vol_uuids in sorted(vol_group.iteritems()):
                            for vol_uuid in vol_uuids:
                                all_attributes |= set(sorted(vol_stats[vol_type][vol_uuid]))

                        combined_vol_stats = {}
                        for attribute in all_attributes:
                            if attribute not in combined_vol_stats:
                                combined_vol_stats[attribute] = []
                            for vol_type, vol_uuids in sorted(vol_group.iteritems()):
                                for vol_uuid in vol_uuids:
                                    combined_vol_stats[attribute].append(vol_stats[vol_type][vol_uuid].
                                                                         get(attribute, "-"))
                        table_data = build_simple_table(data=combined_vol_stats, column_headers=column_headers,
                                                        split_values_to_columns=True)
                        lines.append(table_data.get_string())
                        lines.append("\n\n")
                        f.writelines(lines)
                    fun_test.sleep("for the next iteration - Volume stats collection", seconds=interval)
            output = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return output

    def collect_vppkts_stats(self, output_file="/dev/null", interval=10, count=3, threaded=True,
                             non_zero_stats_only=True, display_diff=True, chunk=8192,
                             command_timeout=DPCSH_COMMAND_TIMEOUT):
        output = False
        column_headers = ["VP Pkts Stats", "Counters"]
        if display_diff:
            column_headers.append("Diff Stats")

        try:
            with open(output_file, 'a') as f:
                timer = FunTimer(max_time=interval * count)
                while not timer.is_expired():
                    lines = []
                    if threaded and (self.stop_vppkts_stats or self.stop_all):
                        fun_test.log("Stopping VP Pkts stats collection thread")
                        break
                    self.socket_lock.acquire()
                    vppkts_result = self.storage_controller.peek(props_tree="stats/vppkts", legacy=False,
                                                                 chunk=chunk, command_duration=command_timeout)
                    self.socket_lock.release()

                    self.new_vppkts_stats = {}
                    if vppkts_result["status"] and vppkts_result["data"]:
                        vppkts_stats = vppkts_result["data"]
                        if non_zero_stats_only:
                            for key, value in vppkts_stats.iteritems():
                                if value != 0:
                                    self.new_vppkts_stats[key] = value
                        else:
                            self.new_vppkts_stats = vppkts_stats

                    if display_diff:
                        if not hasattr(self, "old_vppkts_stats"):
                            self.old_vppkts_stats = self.new_vppkts_stats
                        diff_vppkts_stats = get_diff_results(old_result=self.old_vppkts_stats,
                                                             new_result=self.new_vppkts_stats)
                    self.old_vppkts_stats = self.new_vppkts_stats

                    result_vppkts_stats = OrderedDict()
                    for key, value in sorted(self.new_vppkts_stats.iteritems()):
                        if key not in result_vppkts_stats:
                            result_vppkts_stats[key] = []
                        result_vppkts_stats[key].append(value)
                        if display_diff:
                            result_vppkts_stats[key].append(diff_vppkts_stats[key])

                    table_data = build_simple_table(data=result_vppkts_stats, column_headers=column_headers,
                                                    split_values_to_columns=True)
                    lines.append("\n########################  {} ########################\n".format(time.ctime()))
                    lines.append(table_data.get_string())
                    lines.append("\n\n")
                    f.writelines(lines)
                    fun_test.sleep("for the next iteration - VP Pkts stats collection", seconds=interval)
                output = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return output

    def collect_psw_stats(self, output_file="/dev/null", interval=10, count=3, threaded=True,
                          non_zero_stats_only=True, chunk=8192, nu=False, hnu=False, display_diff=True,
                          command_timeout=10):
        output = False
        column_headers = ["PSW HNU/NU Stats", "Value"]

        if display_diff:
            column_headers.append("Diff Stats")

        if nu and not hnu:
            props_tree = "stats/psw/nu"
        elif hnu and not nu:
            props_tree = "stats/psw/hnu"
        else:
            props_tree = "stats/psw"

        try:
            with open(output_file, 'a') as f:
                timer = FunTimer(max_time=interval * count)
                while not timer.is_expired():
                    lines = []
                    if threaded and (self.stop_psw_stats or self.stop_all):
                        fun_test.log("Stopping PSW stats collection thread")
                        break
                    self.socket_lock.acquire()
                    psw_result = self.storage_controller.peek(props_tree=props_tree, legacy=False,
                                                              chunk=chunk, command_duration=command_timeout)
                    self.socket_lock.release()

                    self.new_psw_stats = {}
                    if psw_result["status"] and psw_result["data"]:
                        psw_stats = psw_result["data"]

                        unpacked_psw_stats = unpack_nested_dict(input_dict=psw_stats)
                        if non_zero_stats_only:
                            for key, value in unpacked_psw_stats.iteritems():
                                if value != "0":
                                    self.new_psw_stats[key] = value
                        else:
                            self.new_psw_stats = unpacked_psw_stats

                    if display_diff:
                        if not hasattr(self, "old_psw_stats"):
                            self.old_psw_stats = self.new_psw_stats
                        diff_psw_stats = get_diff_results(old_result=self.old_psw_stats, new_result=self.new_psw_stats)
                    self.old_psw_stats = self.new_psw_stats

                    result_psw_stats = OrderedDict()
                    for key, value in sorted(self.new_psw_stats.iteritems()):
                        if key not in result_psw_stats:
                            result_psw_stats[key] = []
                        result_psw_stats[key].append(value)
                        if display_diff:
                            result_psw_stats[key].append(diff_psw_stats[key])

                    table_data = build_simple_table(data=result_psw_stats, column_headers=column_headers,
                                                    split_values_to_columns=True)
                    lines.append("\n########################  {} ########################\n".format(time.ctime()))
                    lines.append(table_data.get_string())
                    lines.append("\n\n")
                    f.writelines(lines)
                    fun_test.sleep("for the next iteration - PSW stats collection", seconds=interval)
                output = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return output

    def collect_fcp_stats(self, output_file="/dev/null", interval=10, count=3, threaded=True,
                          non_zero_stats_only=True, chunk=8192, nu=False, hnu=False, display_diff=True,
                          command_timeout=10):
        output = False
        column_headers = ["FCP HNU/NU Stats", "Value"]

        if display_diff:
            column_headers.append("Diff Stats")

        if nu and not hnu:
            props_tree = "stats/fcp/nu"
        elif hnu and not nu:
            props_tree = "stats/fcp/hnu"
        else:
            props_tree = "stats/fcp"

        try:
            with open(output_file, 'a') as f:
                timer = FunTimer(max_time=interval * count)
                while not timer.is_expired():
                    lines = []
                    if threaded and (self.stop_fcp_stats or self.stop_all):
                        fun_test.log("Stopping FCP stats collection thread")
                        break
                    self.socket_lock.acquire()
                    fcp_result = self.storage_controller.peek(props_tree=props_tree, legacy=False,
                                                              chunk=chunk, command_duration=command_timeout)
                    self.socket_lock.release()

                    self.new_fcp_stats = {}
                    if fcp_result["status"] and fcp_result["data"]:
                        fcp_stats = fcp_result["data"]

                        unpacked_fcp_stats = unpack_nested_dict(input_dict=fcp_stats)
                        if non_zero_stats_only:
                            for key, value in unpacked_fcp_stats.iteritems():
                                if value != "0":
                                    self.new_fcp_stats[key] = value
                        else:
                            self.new_fcp_stats = unpacked_fcp_stats

                    if display_diff:
                        if not hasattr(self, "old_fcp_stats"):
                            self.old_fcp_stats = self.new_fcp_stats
                        diff_fcp_stats = get_diff_results(old_result=self.old_fcp_stats, new_result=self.new_fcp_stats)
                    self.old_fcp_stats = self.new_fcp_stats

                    result_fcp_stats = OrderedDict()
                    for key, value in sorted(self.new_fcp_stats.iteritems()):
                        if key not in result_fcp_stats:
                            result_fcp_stats[key] = []
                        result_fcp_stats[key].append(value)
                        if display_diff:
                            result_fcp_stats[key].append(diff_fcp_stats[key])

                    table_data = build_simple_table(data=result_fcp_stats, column_headers=column_headers,
                                                    split_values_to_columns=True)
                    lines.append("\n########################  {} ########################\n".format(time.ctime()))
                    lines.append(table_data.get_string())
                    lines.append("\n\n")
                    f.writelines(lines)
                    fun_test.sleep("for the next iteration - FCP stats collection", seconds=interval)
                output = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return output

    def collect_wro_stats(self, output_file="/dev/null", interval=10, count=3, threaded=True,
                          non_zero_stats_only=True, chunk=8192, nu=False, hnu=False, display_diff=True,
                          command_timeout=10):
        output = False
        column_headers = ["WRO HNU/NU Stats", "Value"]

        if display_diff:
            column_headers.append("Diff Stats")

        if nu and not hnu:
            props_tree = "stats/wro/nu"
        elif hnu and not nu:
            props_tree = "stats/wro/hnu"
        else:
            props_tree = "stats/wro"

        try:
            with open(output_file, 'a') as f:
                timer = FunTimer(max_time=interval * count)
                while not timer.is_expired():
                    lines = []
                    if threaded and (self.stop_wro_stats or self.stop_all):
                        fun_test.log("Stopping WRO stats collection thread")
                        break
                    self.socket_lock.acquire()
                    wro_result = self.storage_controller.peek(props_tree=props_tree, legacy=False,
                                                              chunk=chunk, command_duration=command_timeout)
                    self.socket_lock.release()

                    self.new_wro_stats = {}
                    if wro_result["status"] and wro_result["data"]:
                        wro_stats = wro_result["data"]

                        unpacked_wro_stats = unpack_nested_dict(input_dict=wro_stats)
                        if non_zero_stats_only:
                            for key, value in unpacked_wro_stats.iteritems():
                                if value != "0":
                                    self.new_wro_stats[key] = value
                        else:
                            self.new_wro_stats = unpacked_wro_stats

                    if display_diff:
                        if not hasattr(self, "old_wro_stats"):
                            self.old_wro_stats = self.new_wro_stats
                        diff_wro_stats = get_diff_results(old_result=self.old_wro_stats, new_result=self.new_wro_stats)
                    self.old_wro_stats = self.new_wro_stats

                    result_wro_stats = OrderedDict()
                    for key, value in sorted(self.new_wro_stats.iteritems()):
                        if key not in result_wro_stats:
                            result_wro_stats[key] = []
                        result_wro_stats[key].append(value)
                        if display_diff:
                            result_wro_stats[key].append(diff_wro_stats[key])

                    table_data = build_simple_table(data=result_wro_stats, column_headers=column_headers,
                                                    split_values_to_columns=True)
                    lines.append("\n########################  {} ########################\n".format(time.ctime()))
                    lines.append(table_data.get_string())
                    lines.append("\n\n")
                    f.writelines(lines)
                    fun_test.sleep("for the next iteration - WRO stats collection", seconds=interval)
                output = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return output

    def collect_erp_stats(self, output_file="/dev/null", interval=10, count=3, threaded=True,
                          non_zero_stats_only=True, chunk=8192, nu=False, hnu=False, display_diff=True,
                          command_timeout=10):
        output = False
        column_headers = ["ERP HNU/NU Stats", "Value"]

        if display_diff:
            column_headers.append("Diff Stats")

        if nu and not hnu:
            props_tree = "stats/erp/nu"
        elif hnu and not nu:
            props_tree = "stats/erp/hnu"
        else:
            props_tree = "stats/erp"

        try:
            with open(output_file, 'a') as f:
                timer = FunTimer(max_time=interval * count)
                while not timer.is_expired():
                    lines = []
                    if threaded and (self.stop_erp_stats or self.stop_all):
                        fun_test.log("Stopping ERP stats collection thread")
                        break
                    self.socket_lock.acquire()
                    erp_result = self.storage_controller.peek(props_tree=props_tree, legacy=False,
                                                              chunk=chunk, command_duration=command_timeout)
                    self.socket_lock.release()

                    self.new_erp_stats = {}
                    if erp_result["status"] and erp_result["data"]:
                        erp_stats = erp_result["data"]

                        unpacked_erp_stats = unpack_nested_dict(input_dict=erp_stats)
                        if non_zero_stats_only:
                            for key, value in unpacked_erp_stats.iteritems():
                                if value != "0":
                                    self.new_erp_stats[key] = value
                        else:
                            self.new_erp_stats = unpacked_erp_stats

                    if display_diff:
                        if not hasattr(self, "old_erp_stats"):
                            self.old_erp_stats = self.new_erp_stats
                        diff_erp_stats = get_diff_results(old_result=self.old_erp_stats, new_result=self.new_erp_stats)
                    self.old_erp_stats = self.new_erp_stats

                    result_erp_stats = OrderedDict()
                    for key, value in sorted(self.new_erp_stats.iteritems()):
                        if key not in result_erp_stats:
                            result_erp_stats[key] = []
                        result_erp_stats[key].append(value)
                        if display_diff:
                            result_erp_stats[key].append(diff_erp_stats[key])

                    table_data = build_simple_table(data=result_erp_stats, column_headers=column_headers,
                                                    split_values_to_columns=True)
                    lines.append("\n########################  {} ########################\n".format(time.ctime()))
                    lines.append(table_data.get_string())
                    lines.append("\n\n")
                    f.writelines(lines)
                    fun_test.sleep("for the next iteration - ERP stats collection", seconds=interval)
                output = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return output

    def collect_etp_stats(self, output_file="/dev/null", interval=10, count=3, threaded=True,
                          non_zero_stats_only=True, chunk=8192, nu=False, hnu=False, display_diff=True,
                          command_timeout=10):
        output = False
        column_headers = ["ETP HNU/NU Stats", "Value"]

        if display_diff:
            column_headers.append("Diff Stats")

        if nu and not hnu:
            props_tree = "stats/etp/nu"
        elif hnu and not nu:
            props_tree = "stats/etp/hnu"
        else:
            props_tree = "stats/etp"

        try:
            with open(output_file, 'a') as f:
                timer = FunTimer(max_time=interval * count)
                while not timer.is_expired():
                    lines = []
                    if threaded and (self.stop_etp_stats or self.stop_all):
                        fun_test.log("Stopping ETP stats collection thread")
                        break
                    self.socket_lock.acquire()
                    etp_result = self.storage_controller.peek(props_tree=props_tree, legacy=False,
                                                              chunk=chunk, command_duration=command_timeout)
                    self.socket_lock.release()

                    self.new_etp_stats = {}
                    if etp_result["status"] and etp_result["data"]:
                        etp_stats = etp_result["data"]

                        unpacked_etp_stats = unpack_nested_dict(input_dict=etp_stats)
                        if non_zero_stats_only:
                            for key, value in unpacked_etp_stats.iteritems():
                                if value != "0":
                                    self.new_etp_stats[key] = value
                        else:
                            self.new_etp_stats = unpacked_etp_stats

                    if display_diff:
                        if not hasattr(self, "old_etp_stats"):
                            self.old_etp_stats = self.new_etp_stats
                        diff_etp_stats = get_diff_results(old_result=self.old_etp_stats, new_result=self.new_etp_stats)
                    self.old_etp_stats = self.new_etp_stats

                    result_etp_stats = OrderedDict()
                    for key, value in sorted(self.new_etp_stats.iteritems()):
                        if key not in result_etp_stats:
                            result_etp_stats[key] = []
                        result_etp_stats[key].append(value)
                        if display_diff:
                            result_etp_stats[key].append(diff_etp_stats[key])

                    table_data = build_simple_table(data=result_etp_stats, column_headers=column_headers,
                                                    split_values_to_columns=True)
                    lines.append("\n########################  {} ########################\n".format(time.ctime()))
                    lines.append(table_data.get_string())
                    lines.append("\n\n")
                    f.writelines(lines)
                    fun_test.sleep("for the next iteration - ETP stats collection", seconds=interval)
                output = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return output

    def collect_eqm_stats(self, output_file="/dev/null", interval=10, count=3, threaded=True,
                          non_zero_stats_only=True, chunk=8192, display_diff=True, command_timeout=10):
        output = False
        column_headers = ["EQM Stats", "Value"]

        if display_diff:
            column_headers.append("Diff Stats")

        props_tree = "stats/eqm"

        try:
            with open(output_file, 'a') as f:
                timer = FunTimer(max_time=interval * count)
                while not timer.is_expired():
                    lines = []
                    if threaded and (self.stop_eqm_stats or self.stop_all):
                        fun_test.log("Stopping EQM stats collection thread")
                        break
                    self.socket_lock.acquire()
                    eqm_result = self.storage_controller.peek(props_tree=props_tree, legacy=False,
                                                              chunk=chunk, command_duration=command_timeout)
                    self.socket_lock.release()

                    self.new_eqm_stats = {}
                    if eqm_result["status"] and eqm_result["data"]:
                        eqm_stats = eqm_result["data"]

                        unpacked_eqm_stats = unpack_nested_dict(input_dict=eqm_stats)
                        if non_zero_stats_only:
                            for key, value in unpacked_eqm_stats.iteritems():
                                if value != "0":
                                    self.new_eqm_stats[key] = value
                        else:
                            self.new_eqm_stats = unpacked_eqm_stats

                    if display_diff:
                        if not hasattr(self, "old_eqm_stats"):
                            self.old_eqm_stats = self.new_eqm_stats
                        diff_eqm_stats = get_diff_results(old_result=self.old_eqm_stats, new_result=self.new_eqm_stats)
                    self.old_eqm_stats = self.new_eqm_stats

                    result_eqm_stats = OrderedDict()
                    for key, value in sorted(self.new_eqm_stats.iteritems()):
                        if key not in result_eqm_stats:
                            result_eqm_stats[key] = []
                        result_eqm_stats[key].append(value)
                        if display_diff:
                            result_eqm_stats[key].append(diff_eqm_stats[key])

                    table_data = build_simple_table(data=result_eqm_stats, column_headers=column_headers,
                                                    split_values_to_columns=True)
                    lines.append("\n########################  {} ########################\n".format(time.ctime()))
                    lines.append(table_data.get_string())
                    lines.append("\n\n")
                    f.writelines(lines)
                    fun_test.sleep("for the next iteration - EQM stats collection", seconds=interval)
                output = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return output

    def collect_hu_stats(self, output_file="/dev/null", interval=10, count=3, threaded=True,
                         non_zero_stats_only=True, chunk=8192, display_diff=True, command_timeout=10):
        output = False
        column_headers = ["HU Stats", "Value"]

        if display_diff:
            column_headers.append("Diff Stats")

        props_tree = "stats/hu"

        try:
            with open(output_file, 'a') as f:
                timer = FunTimer(max_time=interval * count)
                while not timer.is_expired():
                    lines = []
                    if threaded and (self.stop_hu_stats or self.stop_all):
                        fun_test.log("Stopping HU stats collection thread")
                        break
                    self.socket_lock.acquire()
                    hu_result = self.storage_controller.peek(props_tree=props_tree, legacy=False, chunk=chunk,
                                                             command_duration=command_timeout)
                    self.socket_lock.release()

                    self.new_hu_stats = {}
                    if hu_result["status"] and hu_result["data"]:
                        hu_stats = hu_result["data"]

                        unpacked_hu_stats = unpack_nested_dict(input_dict=hu_stats)
                        if non_zero_stats_only:
                            for key, value in unpacked_hu_stats.iteritems():
                                if value != "0":
                                    self.new_hu_stats[key] = value
                        else:
                            self.new_hu_stats = unpacked_hu_stats

                    if display_diff:
                        if not hasattr(self, "old_hu_stats"):
                            self.old_hu_stats = self.new_hu_stats
                        diff_hu_stats = get_diff_results(old_result=self.old_hu_stats, new_result=self.new_hu_stats)
                    self.old_hu_stats = self.new_hu_stats

                    result_hu_stats = OrderedDict()
                    for key, value in sorted(self.new_hu_stats.iteritems()):
                        if key not in result_hu_stats:
                            result_hu_stats[key] = []
                        result_hu_stats[key].append(value)
                        if display_diff:
                            result_hu_stats[key].append(diff_hu_stats[key])

                    table_data = build_simple_table(data=result_hu_stats, column_headers=column_headers,
                                                    split_values_to_columns=True)
                    lines.append("\n########################  {} ########################\n".format(time.ctime()))
                    lines.append(table_data.get_string())
                    lines.append("\n\n")
                    f.writelines(lines)
                    fun_test.sleep("for the next iteration - HU stats collection", seconds=interval)
                output = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return output

    def collect_ddr_stats(self, output_file="/dev/null", interval=10, count=3, threaded=True,
                          non_zero_stats_only=True, chunk=8192, display_diff=True, command_timeout=10):
        output = False
        column_headers = ["DDR Stats", "Value"]

        if display_diff:
            column_headers.append("Diff Stats")

        props_tree = "stats/ddr"

        try:
            with open(output_file, 'a') as f:
                timer = FunTimer(max_time=interval * count)
                while not timer.is_expired():
                    lines = []
                    if threaded and (self.stop_ddr_stats or self.stop_all):
                        fun_test.log("Stopping DDR stats collection thread")
                        break
                    self.socket_lock.acquire()
                    ddr_result = self.storage_controller.peek(props_tree=props_tree, legacy=False,
                                                              chunk=chunk, command_duration=command_timeout)
                    self.socket_lock.release()

                    self.new_ddr_stats = {}
                    if ddr_result["status"] and ddr_result["data"]:
                        ddr_stats = ddr_result["data"]

                        unpacked_ddr_stats = unpack_nested_dict(input_dict=ddr_stats)
                        if non_zero_stats_only:
                            for key, value in unpacked_ddr_stats.iteritems():
                                if value != "0":
                                    self.new_ddr_stats[key] = value
                        else:
                            self.new_ddr_stats = unpacked_ddr_stats

                    if display_diff:
                        if not hasattr(self, "old_ddr_stats"):
                            self.old_ddr_stats = self.new_ddr_stats
                        diff_ddr_stats = get_diff_results(old_result=self.old_ddr_stats, new_result=self.new_ddr_stats)
                    self.old_ddr_stats = self.new_ddr_stats

                    result_ddr_stats = OrderedDict()
                    for key, value in sorted(self.new_ddr_stats.iteritems()):
                        if key not in result_ddr_stats:
                            result_ddr_stats[key] = []
                        result_ddr_stats[key].append(value)
                        if display_diff:
                            result_ddr_stats[key].append(diff_ddr_stats[key])

                    table_data = build_simple_table(data=result_ddr_stats, column_headers=column_headers,
                                                    split_values_to_columns=True)
                    lines.append("\n########################  {} ########################\n".format(time.ctime()))
                    lines.append(table_data.get_string())
                    lines.append("\n\n")
                    f.writelines(lines)
                    fun_test.sleep("for the next iteration - DDR stats collection", seconds=interval)
                output = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return output

    def collect_ca_stats(self, output_file="/dev/null", interval=10, count=3, threaded=True,
                         non_zero_stats_only=True, chunk=8192, display_diff=True, command_timeout=10):
        output = False
        column_headers = ["CA Stats", "Value"]

        if display_diff:
            column_headers.append("Diff Stats")

        props_tree = "stats/ca"

        try:
            with open(output_file, 'a') as f:
                timer = FunTimer(max_time=interval * count)
                while not timer.is_expired():
                    lines = []
                    if threaded and (self.stop_ca_stats or self.stop_all):
                        fun_test.log("Stopping CA stats collection thread")
                        break
                    self.socket_lock.acquire()
                    ca_result = self.storage_controller.peek(props_tree=props_tree, legacy=False, chunk=chunk,
                                                             command_duration=command_timeout)
                    self.socket_lock.release()

                    self.new_ca_stats = {}
                    if ca_result["status"] and ca_result["data"]:
                        ca_stats = ca_result["data"]

                        unpacked_ca_stats = unpack_nested_dict(input_dict=ca_stats)
                        if non_zero_stats_only:
                            for key, value in unpacked_ca_stats.iteritems():
                                if value != "0":
                                    self.new_ca_stats[key] = value
                        else:
                            self.new_ca_stats = unpacked_ca_stats

                    if display_diff:
                        if not hasattr(self, "old_ca_stats"):
                            self.old_ca_stats = self.new_ca_stats
                        diff_ca_stats = get_diff_results(old_result=self.old_ca_stats, new_result=self.new_ca_stats)
                    self.old_ca_stats = self.new_ca_stats

                    result_ca_stats = OrderedDict()
                    for key, value in sorted(self.new_ca_stats.iteritems()):
                        if key not in result_ca_stats:
                            result_ca_stats[key] = []
                        result_ca_stats[key].append(value)
                        if display_diff:
                            result_ca_stats[key].append(diff_ca_stats[key])

                    table_data = build_simple_table(data=result_ca_stats, column_headers=column_headers,
                                                    split_values_to_columns=True)
                    lines.append("\n########################  {} ########################\n".format(time.ctime()))
                    lines.append(table_data.get_string())
                    lines.append("\n\n")
                    f.writelines(lines)
                    fun_test.sleep("for the next iteration - CA stats collection", seconds=interval)
                output = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return output

    def collect_cdu_stats(self, output_file="/dev/null", interval=10, count=3, threaded=True,
                          non_zero_stats_only=True, chunk=8192, display_diff=True, command_timeout=10):
        output = False
        column_headers = ["CDU Stats", "Value"]

        if display_diff:
            column_headers.append("Diff Stats")

        props_tree = "stats/cdu"

        try:
            with open(output_file, 'a') as f:
                timer = FunTimer(max_time=interval * count)
                while not timer.is_expired():
                    lines = []
                    if threaded and (self.stop_cdu_stats or self.stop_all):
                        fun_test.log("Stopping CDU stats collection thread")
                        break
                    self.socket_lock.acquire()
                    cdu_result = self.storage_controller.peek(props_tree=props_tree, legacy=False,
                                                              chunk=chunk, command_duration=command_timeout)
                    self.socket_lock.release()

                    self.new_cdu_stats = {}
                    if cdu_result["status"] and cdu_result["data"]:
                        cdu_stats = cdu_result["data"]

                        unpacked_cdu_stats = unpack_nested_dict(input_dict=cdu_stats)
                        if non_zero_stats_only:
                            for key, value in unpacked_cdu_stats.iteritems():
                                if value != "0":
                                    self.new_cdu_stats[key] = value
                        else:
                            self.new_cdu_stats = unpacked_cdu_stats

                    if display_diff:
                        if not hasattr(self, "old_cdu_stats"):
                            self.old_cdu_stats = self.new_cdu_stats
                        diff_cdu_stats = get_diff_results(old_result=self.old_cdu_stats, new_result=self.new_cdu_stats)
                    self.old_cdu_stats = self.new_cdu_stats

                    result_cdu_stats = OrderedDict()
                    for key, value in sorted(self.new_cdu_stats.iteritems()):
                        if key not in result_cdu_stats:
                            result_cdu_stats[key] = []
                        result_cdu_stats[key].append(value)
                        if display_diff:
                            result_cdu_stats[key].append(diff_cdu_stats[key])

                    table_data = build_simple_table(data=result_cdu_stats, column_headers=column_headers,
                                                    split_values_to_columns=True)
                    lines.append("\n########################  {} ########################\n".format(time.ctime()))
                    lines.append(table_data.get_string())
                    lines.append("\n\n")
                    f.writelines(lines)
                    fun_test.sleep("for the next iteration - CDU stats collection", seconds=interval)
                output = True
        except Exception as ex:
            fun_test.critical(str(ex))
        return output

    def start(self, file_suffix, stats_collect_details):
        try:
            start_time = 1
            start_dealy = 5
            for index, stat_detail in enumerate(stats_collect_details):
                func = stat_detail.keys()[0]
                arg = stat_detail[func]
                if "thread_id" in arg:
                    del(stats_collect_details[index][func]["thread_id"])
                post_fix_name = "{}_{}".format(func, file_suffix)
                stats_collect_details[index][func]["output_file"] = \
                    fun_test.get_test_case_artifact_file_name(post_fix_name)
                if func == "vp_utils":
                    stats_collect_details[index][func]["thread_id"] = fun_test.execute_thread_after(
                        time_in_seconds=start_time, func=self.collect_vp_utils_stats, **arg)
                    fun_test.log("Started the VP utilization stats collection thread having the ID: {}".
                                 format(stats_collect_details[index][func]["thread_id"]))
                if func == "per_vp":
                    stats_collect_details[index][func]["thread_id"] = fun_test.execute_thread_after(
                        time_in_seconds=start_time, func=self.collect_per_vp_stats, **arg)
                    fun_test.log("Started the per VP utilization stats collection thread having the ID: {}".
                                 format(stats_collect_details[index][func]["thread_id"]))
                if func == "resource_bam_args":
                    stats_collect_details[index][func]["thread_id"] = fun_test.execute_thread_after(
                        time_in_seconds=start_time, func=self.collect_resource_bam_stats, **arg)
                    fun_test.log("Started the BAM stats collection thread having the ID: {}".
                                 format(stats_collect_details[index][func]["thread_id"]))
                if func == "vol_stats":
                    stats_collect_details[index][func]["thread_id"] = fun_test.execute_thread_after(
                        time_in_seconds=start_time, func=self.collect_vol_stats, **arg)
                    fun_test.log("Started the Volume stats collection thread having the ID: {}".
                                 format(stats_collect_details[index][func]["thread_id"]))
                if func == "vppkts_stats":
                    stats_collect_details[index][func]["thread_id"] = fun_test.execute_thread_after(
                        time_in_seconds=start_time, func=self.collect_vppkts_stats, **arg)
                    fun_test.log("Started the VP Pkts stats collection thread having the ID: {}".
                                 format(stats_collect_details[index][func]["thread_id"]))
                if func == "psw_stats":
                    stats_collect_details[index][func]["thread_id"] = fun_test.execute_thread_after(
                        time_in_seconds=start_time, func=self.collect_psw_stats, **arg)
                    fun_test.log("Started the PSW stats collection thread having the ID: {}".
                                 format(stats_collect_details[index][func]["thread_id"]))
                if func == "fcp_stats":
                    stats_collect_details[index][func]["thread_id"] = fun_test.execute_thread_after(
                        time_in_seconds=start_time, func=self.collect_fcp_stats, **arg)
                    fun_test.log("Started the FCP stats collection thread having the ID: {}".
                                 format(stats_collect_details[index][func]["thread_id"]))
                if func == "wro_stats":
                    stats_collect_details[index][func]["thread_id"] = fun_test.execute_thread_after(
                        time_in_seconds=start_time, func=self.collect_wro_stats, **arg)
                    fun_test.log("Started the WRO stats collection thread having the ID: {}".
                                 format(stats_collect_details[index][func]["thread_id"]))
                if func == "erp_stats":
                    stats_collect_details[index][func]["thread_id"] = fun_test.execute_thread_after(
                        time_in_seconds=start_time, func=self.collect_erp_stats, **arg)
                    fun_test.log("Started the ERP stats collection thread having the ID: {}".
                                 format(stats_collect_details[index][func]["thread_id"]))
                if func == "etp_stats":
                    stats_collect_details[index][func]["thread_id"] = fun_test.execute_thread_after(
                        time_in_seconds=start_time, func=self.collect_etp_stats, **arg)
                    fun_test.log("Started the ETP stats collection thread having the ID: {}".
                                 format(stats_collect_details[index][func]["thread_id"]))
                if func == "eqm_stats":
                    stats_collect_details[index][func]["thread_id"] = fun_test.execute_thread_after(
                        time_in_seconds=start_time, func=self.collect_eqm_stats, **arg)
                    fun_test.log("Started the EQM stats collection thread having the ID: {}".
                                 format(stats_collect_details[index][func]["thread_id"]))
                if func == "hu_stats":
                    stats_collect_details[index][func]["thread_id"] = fun_test.execute_thread_after(
                        time_in_seconds=start_time, func=self.collect_hu_stats, **arg)
                    fun_test.log("Started the HU stats collection thread having the ID: {}".
                                 format(stats_collect_details[index][func]["thread_id"]))
                if func == "ddr_stats":
                    stats_collect_details[index][func]["thread_id"] = fun_test.execute_thread_after(
                        time_in_seconds=start_time, func=self.collect_ddr_stats, **arg)
                    fun_test.log("Started the DDR stats collection thread having the ID: {}".
                                 format(stats_collect_details[index][func]["thread_id"]))
                if func == "ca_stats":
                    stats_collect_details[index][func]["thread_id"] = fun_test.execute_thread_after(
                        time_in_seconds=start_time, func=self.collect_ca_stats, **arg)
                    fun_test.log("Started the CA stats collection thread having the ID: {}".
                                 format(stats_collect_details[index][func]["thread_id"]))
                if func == "cdu_stats":
                    stats_collect_details[index][func]["thread_id"] = fun_test.execute_thread_after(
                        time_in_seconds=start_time, func=self.collect_cdu_stats, **arg)
                    fun_test.log("Started the CDU stats collection thread having the ID: {}".
                                 format(stats_collect_details[index][func]["thread_id"]))
                start_time += start_dealy
        except Exception as ex:
            fun_test.critical(str(ex))

    def stop(self, stats_collect_details):

        # If the threads are still running, then set their stop flag
        for index, stat_detail in enumerate(stats_collect_details):
            func = stat_detail.keys()[0]
            arg = stat_detail[func]
            thread_id = arg.get("thread_id")
            if thread_id and fun_test.fun_test_threads[thread_id]["thread"].is_alive():
                if func == "vp_utils":
                    fun_test.log("VP utilization stats collection thread having the ID {} is still running..."
                                 "Stopping it now".format(thread_id))
                    self.stop_vp_utils = True
                if func == "per_vp":
                    fun_test.log("Per VP Stats collection thread having the ID {} is still running...Stopping it "
                                 "now".format(thread_id))
                    self.stop_per_vp_stats = True
                if func == "resource_bam_args":
                    fun_test.log("Resource bam stats collection thread having the ID {} is still running..."
                                 "Stopping it now".format(thread_id))
                    self.stop_resource_bam = True
                if func == "vol_stats":
                    fun_test.log("Volume Stats collection thread having the ID {} is still running...Stopping "
                                 "it now".format(thread_id))
                    self.stop_vol_stats = True
                if func == "vppkts_stats":
                    fun_test.log("VP Pkts Stats collection thread having the ID {} is still running...Stopping "
                                 "it now".format(thread_id))
                    self.stop_vppkts_stats = True
                if func == "psw_stats":
                    fun_test.log("PSW stats collection thread having the ID {} is still running...Stopping "
                                 "it now".format(thread_id))
                    self.stop_psw_stats = True
                if func == "fcp_stats":
                    fun_test.log("FCP stats collection thread having the ID {} is still running...Stopping "
                                 "it now".format(thread_id))
                    self.stop_fcp_stats = True
                if func == "wro_stats":
                    fun_test.log("WRO stats collection thread having the ID {} is still running...Stopping "
                                 "it now".format(thread_id))
                    self.stop_wro_stats = True
                if func == "erp_stats":
                    fun_test.log("ERP stats collection thread having the ID {} is still running...Stopping "
                                 "it now".format(thread_id))
                    self.stop_erp_stats = True
                if func == "etp_stats":
                    fun_test.log("ETP stats collection thread having the ID {} is still running...Stopping "
                                 "it now".format(thread_id))
                    self.stop_etp_stats = True
                if func == "eqm_stats":
                    fun_test.log("EQM stats collection thread having the ID {} is still running...Stopping "
                                 "it now".format(thread_id))
                    self.stop_eqm_stats = True
                if func == "hu_stats":
                    fun_test.log("HU stats collection thread having the ID {} is still running...Stopping "
                                 "it now".format(thread_id))
                    self.stop_hu_stats = True
                if func == "ddr_stats":
                    fun_test.log("DDR stats collection thread having the ID {} is still running...Stopping "
                                 "it now".format(thread_id))
                    self.stop_ddr_stats = True
                if func == "ca_stats":
                    fun_test.log("CA stats collection thread having the ID {} is still running...Stopping "
                                 "it now".format(thread_id))
                    self.stop_ca_stats = True
                if func == "cdu_stats":
                    fun_test.log("CDU stats collection thread having the ID {} is still running...Stopping "
                                 "it now".format(thread_id))
                    self.stop_cdu_stats = True

        # Wait for the threads to complete
        for index, stat_detail in enumerate(stats_collect_details):
            func = stat_detail.keys()[0]
            arg = stat_detail[func]
            thread_id = arg.get("thread_id")
            if thread_id:
                if func == "vp_utils":
                    fun_test.log("Waiting for the VP utilization stats collection thread having the ID {} to "
                                 "complete...".format(thread_id))
                if func == "per_vp":
                    fun_test.log("Waiting for the Per VP Stats collection thread having the ID {} to "
                                 "complete...".format(thread_id))
                if func == "resource_bam_args":
                    fun_test.log("Waiting for the Resource bam stats collection thread having the ID {} to "
                                 "complete...".format(thread_id))
                if func == "vol_stats":
                    fun_test.log("Waiting for the Volume Stats collection thread having the ID {} to "
                                 "complete...".format(thread_id))
                if func == "vppkts_stats":
                    fun_test.log("Waiting for the VP Pkts Stats collection thread having the ID {} to "
                                 "complete...".format(thread_id))
                if func == "psw_stats":
                    fun_test.log("Waiting for the PSW Stats collection thread having the ID {} to "
                                 "complete...".format(thread_id))
                if func == "fcp_stats":
                    fun_test.log("Waiting for the FCP Stats collection thread having the ID {} to "
                                 "complete...".format(thread_id))
                if func == "wro_stats":
                    fun_test.log("Waiting for the WRO Stats collection thread having the ID {} to "
                                 "complete...".format(thread_id))
                if func == "erp_stats":
                    fun_test.log("Waiting for the ERP Stats collection thread having the ID {} to "
                                 "complete...".format(thread_id))
                if func == "etp_stats":
                    fun_test.log("Waiting for the ETP Stats collection thread having the ID {} to "
                                 "complete...".format(thread_id))
                if func == "eqm_stats":
                    fun_test.log("Waiting for the EQM Stats collection thread having the ID {} to "
                                 "complete...".format(thread_id))
                if func == "hu_stats":
                    fun_test.log("Waiting for the HU Stats collection thread having the ID {} to "
                                 "complete...".format(thread_id))
                if func == "ddr_stats":
                    fun_test.log("Waiting for the DDR Stats collection thread having the ID {} to "
                                 "complete...".format(thread_id))
                if func == "ca_stats":
                    fun_test.log("Waiting for the CA Stats collection thread having the ID {} to "
                                 "complete...".format(thread_id))
                if func == "cdu_stats":
                    fun_test.log("Waiting for the CDU Stats collection thread having the ID {} to "
                                 "complete...".format(thread_id))
                fun_test.join_thread(fun_test_thread_id=thread_id, sleep_time=1)
