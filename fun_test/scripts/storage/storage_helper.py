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


def collect_vp_utils_stats(storage_controller, output_file, interval=10, count=3, non_zero_stats_only=True,
                           threaded=False, command_timeout=DPCSH_COMMAND_TIMEOUT):
    output = False
    column_headers = ["VP", "Utilization"]

    # If threaded is enabled
    if threaded:
        global vp_stats_thread_stop_status
        vp_stats_thread_stop_status[storage_controller] = False
    try:
        with open(output_file, 'a') as f:
            timer = FunTimer(max_time=interval * count)
            while not timer.is_expired():
                lines = []
                dpcsh_result = storage_controller.debug_vp_util(command_timeout=command_timeout)
                # fun_test.simple_assert(dpcsh_result["status"], "Pulling VP Utilization")
                if dpcsh_result["status"] and dpcsh_result["data"] is not None:
                    vp_util = dpcsh_result["data"]
                else:
                    vp_util = {}

                if non_zero_stats_only:
                    filtered_vp_util = OrderedDict()
                    for key, value in sorted(vp_util.iteritems()):
                        if value != 0.0 or value != 0:
                            filtered_vp_util[key] = value
                    vp_util = filtered_vp_util

                table_data = build_simple_table(data=vp_util, column_headers=column_headers)
                lines.append("\n########################  {} ########################\n".format(time.ctime()))
                lines.append(table_data.get_string())
                lines.append("\n\n")
                f.writelines(lines)
                if threaded and vp_stats_thread_stop_status[storage_controller]:
                    fun_test.log("I was asked to stop....So I'm exiting now...")
                    break
                fun_test.sleep("for the next iteration", seconds=interval)
        output = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return output


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


def collect_resource_bam_stats(storage_controller, output_file, interval=10, count=3, threaded=False,
                               command_timeout=DPCSH_COMMAND_TIMEOUT):
    output = False
    column_headers = ["Field Name", "Counters"]

    # If threaded is enabled
    if threaded:
        global resource_bam_stats_thread_stop_status
        resource_bam_stats_thread_stop_status[storage_controller] = False
    try:
        with open(output_file, 'a') as f:
            timer = FunTimer(max_time=interval * count)
            while not timer.is_expired():
                lines = []
                dpcsh_result = storage_controller.peek_resource_bam_stats(command_timeout=command_timeout)
                if dpcsh_result["status"] and dpcsh_result["data"] is not None:
                    resource_bam_stats = dpcsh_result["data"]
                else:
                    resource_bam_stats = {}

                table_data = build_simple_table(data=resource_bam_stats, column_headers=column_headers)
                lines.append("\n########################  {} ########################\n".format(time.ctime()))
                lines.append(table_data.get_string())
                lines.append("\n\n")
                f.writelines(lines)
                if threaded and resource_bam_stats_thread_stop_status[storage_controller]:
                    fun_test.log("Resource BAM stats collection was asked to stop....So exiting now...")
                    break
                fun_test.sleep("for the next iteration - Resource BAM stats collection", seconds=interval)
        output = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return output


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


class CollectStats(object):
    def __init__(self, storage_controller):
        self.storage_controller = storage_controller
        self.socket_lock = Lock()
        self.stop_all = False
        self.stop_vp_utils = False
        self.stop_per_vp_stats = False
        self.stop_resource_bam = False
        self.stop_vol_stats = False

    def collect_vp_utils_stats(self, output_file, interval=10, count=3, non_zero_stats_only=True, threaded=False,
                               command_timeout=DPCSH_COMMAND_TIMEOUT):
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
                    vp_utils_result = self.storage_controller.debug_vp_util(command_timeout=command_timeout)
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

    def collect_per_vp_stats(self, output_file, interval=10, count=3, threaded=False, include_cc=False,
                             display_diff=True, command_timeout=DPCSH_COMMAND_TIMEOUT):
        output = False
        per_vp_stats_key = ["wus_received", "vp_wu_qdepth", "wus_sent"]
        per_vp_stats_header = ["rx", "qd", "tx"]
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
                    initial_per_vp_output = self.storage_controller.peek_per_vp_stats(command_timeout=command_timeout)
                    if display_diff:
                        fun_test.sleep("to get one more per_vp stats to find the diff", 1)
                        final_per_vp_output = self.storage_controller.peek_per_vp_stats(command_timeout=command_timeout)
                    self.socket_lock.release()

                    if initial_per_vp_output["status"] and initial_per_vp_output["data"] is not None:
                        initial_per_vp_stats = initial_per_vp_output["data"]
                    else:
                        initial_per_vp_stats = {}

                    if display_diff:
                        if final_per_vp_output["status"] and final_per_vp_output["data"] is not None:
                            final_per_vp_stats = final_per_vp_output["data"]
                        else:
                            final_per_vp_stats = {}

                    # Removing the Central Cluster(if needed) and the redundant entries
                    filtered_initial_per_vp_stats = OrderedDict()
                    filtered_final_per_vp_stats = OrderedDict()
                    for key in sorted(initial_per_vp_stats):
                        if not include_cc:
                            if not key.split(":")[0][2] == '8' and not key.split(":")[2][0] == '1':
                                filtered_initial_per_vp_stats[key] = initial_per_vp_stats[key]
                                if display_diff and key in final_per_vp_stats:
                                    filtered_final_per_vp_stats[key] = final_per_vp_stats[key]
                        else:
                            if not key.split(":")[2][0] == '1':
                                filtered_initial_per_vp_stats[key] = initial_per_vp_stats[key]
                                if display_diff and key in final_per_vp_stats:
                                    filtered_final_per_vp_stats[key] = final_per_vp_stats[key]

                    processed_per_vp_stats = OrderedDict()
                    # Sorting the keys using the cluster ID(FA*0*:10:0[VP]) as the primary key and the
                    # core ID(FA0:*10*:0[VP]) as the secondary key
                    for key in sorted(filtered_initial_per_vp_stats, key= lambda key: (int(key.split(":")[0][2]),
                                                                                       int(key.split(":")[1]))):
                        cluster_id = key.split(":")[0][2]
                        core_id = (int(key.split(":")[1]) / 4) - 2
                        thread_id = int(key.split(":")[1]) % 4
                        new_key = "{}/{}".format(cluster_id, core_id)
                        if new_key not in processed_per_vp_stats:
                            processed_per_vp_stats[new_key] = []
                        for subkey in per_vp_stats_key:
                            if display_diff:
                                if key in filtered_final_per_vp_stats:
                                    processed_per_vp_stats[new_key].append(filtered_final_per_vp_stats[key][subkey])
                                    processed_per_vp_stats[new_key].append(filtered_final_per_vp_stats[key][subkey] -
                                                                           filtered_initial_per_vp_stats[key][subkey])
                            else:
                                processed_per_vp_stats[new_key].append(filtered_initial_per_vp_stats[key][subkey])

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

    def collect_resource_bam_stats(self, output_file, interval=10, count=3, threaded=False,
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
                          threaded=False, command_timeout=DPCSH_COMMAND_TIMEOUT):
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
                                                                    chunk=8192, command_duration=command_timeout)
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
    stats_exclude_list = ["drive_uuid", "extent_size", "fault_injection", "flvm_block_size", "flvm_vol_size_blocks", "se_size"]
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
                        total_diff[vol_type][stats_field] = total_diff[vol_type][stats_field] + stats_diff[i][vol_type][vol_uuid][stats_field]

        result["status"] = True
        result["stats_diff"] = stats_diff
        result["total_diff"] = total_diff
    except Exception as ex:
        fun_test.critical(str(ex))
        result["status"] = False

    return result
