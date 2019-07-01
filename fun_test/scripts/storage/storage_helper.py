from lib.system.fun_test import *
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper
import re
from prettytable import PrettyTable
import time
from collections import OrderedDict
from lib.host.storage_controller import StorageController
from lib.system import utils

DPCSH_COMMAND_TIMEOUT = 5

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


def build_simple_table(data, column_headers=[]):
    simple_table = PrettyTable(column_headers)
    simple_table.align = 'l'
    simple_table.border = True
    simple_table.header = True
    try:
        for key in sorted(data):
            simple_table.add_row([key, data[key]])
    except Exception as ex:
        fun_test.critical(str(ex))
    return simple_table


def collect_vp_utils_stats(storage_controller, output_file, interval=10, count=3, non_zero_stats_only=True,
                           command_timeout=DPCSH_COMMAND_TIMEOUT):
    output = False
    column_headers = ["VP", "Utilization"]
    try:
        with open(output_file, 'a') as f:
            timer = FunTimer(max_time=interval * count)
            while not timer.is_expired():
                lines = []
                dpcsh_result = storage_controller.debug_vp_util(command_timeout=command_timeout)
                fun_test.simple_assert(dpcsh_result["status"], "Pulling VP Utilization")
                if dpcsh_result["data"] is not None:
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
                fun_test.sleep("for the next iteration", seconds=interval)
        output = True
    except Exception as ex:
        fun_test.critical(str(ex))
    return output


def check_come_health(fs_obj, f1_in_use):
    blt_vol_info = {
        "type": "VOL_TYPE_BLK_LOCAL_THIN",
        "capacity": 10485760,
        "block_size": 4096,
        "name": "thin-block1"}
    result = False
    try:
        come_obj = fs_obj.get_come()
        blt_uuid = utils.generate_uuid()
        dpc_cli = StorageController(target_ip=come_obj.host_ip,
                                    target_port=come_obj.get_dpc_port(f1_in_use))
        response = dpc_cli.create_thin_block_volume(capacity=blt_vol_info["capacity"],
                                                    block_size=blt_vol_info["block_size"],
                                                    name=blt_vol_info['name'],
                                                    uuid=blt_uuid,
                                                    command_duration=30)
        dpc_cli.disconnect()
        if response["status"]:
            result = True
    except Exception as ex:
        fun_test.critical(ex.message)
    return result
