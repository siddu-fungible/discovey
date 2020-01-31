from lib.system.fun_test import *
from lib.system import utils
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper, get_data_collection_time
from lib.fun.fs import Fs
import re
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_fs_template import *
from scripts.storage.storage_helper import *
from scripts.networking.helper import *
from collections import OrderedDict, Counter
from lib.templates.csi_perf.csi_perf_template import CsiPerfTemplate
from lib.host.linux import Linux
from threading import Lock
from lib.templates.storage.storage_controller_api import *
import itertools
import random
from copy import deepcopy

'''
Script to track the Inspur Performance Cases of various read write combination of Erasure Coded volume using FIO
'''


def fio_parser(arg1, host_index, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    fun_test.shared_variables["fio"][host_index] = fio_output
    fun_test.simple_assert(fio_output, "Fio test for thread {}".format(host_index))
    arg1.disconnect()


def post_results(volume, test, num_host, block_size, io_depth, size, operation, write_iops, read_iops, write_bw,
                 read_bw,
                 write_latency, write_90_latency, write_95_latency, write_99_latency, write_99_99_latency, read_latency,
                 read_90_latency, read_95_latency, read_99_latency, read_99_99_latency, fio_job_name,
                 write_amp_vol_stats, read_amp_vol_stats, aggr_amp_vol_stats, write_amp_app_stats, read_amp_app_stats,
                 aggr_amp_app_stats, write_amp_rcnvme_stats, read_amp_rcnvme_stats, aggr_amp_rcnvme_stats):
    for i in ["write_iops", "read_iops", "write_bw", "read_bw", "write_latency", "write_90_latency", "write_95_latency",
              "write_99_latency", "write_99_99_latency", "read_latency", "read_90_latency", "read_95_latency",
              "read_99_latency", "read_99_99_latency", "fio_job_name", "write_amp_vol_stats", "read_amp_vol_stats",
              "aggr_amp_vol_stats", "write_amp_app_stats", "read_amp_app_stats", "aggr_amp_app_stats",
              "write_amp_rcnvme_stats", "read_amp_rcnvme_stats", "aggr_amp_rcnvme_stats"]:
        if eval("type({}) is tuple".format(i)):
            exec ("{0} = {0}[0]".format(i))

    db_log_time = fun_test.shared_variables["db_log_time"]
    num_ssd = fun_test.shared_variables["num_ssd"]
    num_volumes = fun_test.shared_variables["num_volumes"]

    blt = BltVolumePerformanceHelper()
    blt.add_entry(date_time=db_log_time, volume=volume, test=test, block_size=block_size, io_depth=int(io_depth),
                  size=size, operation=operation, num_ssd=num_ssd, num_volume=num_volumes, fio_job_name=fio_job_name,
                  write_iops=write_iops, read_iops=read_iops, write_throughput=write_bw, read_throughput=read_bw,
                  write_avg_latency=write_latency, read_avg_latency=read_latency, write_90_latency=write_90_latency,
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


class ECBlockRecoveryScript(FunTestScript):

    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. Bring up F1 with funos 
        2. Configure Linux Host instance and make it available for test case
        """)

    def setup(self):
        # Parsing the global config and assign them as object members
        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))
        config_dict = utils.parse_file_to_json(config_file)

        if "GlobalSetup" not in config_dict or not config_dict["GlobalSetup"]:
            fun_test.critical("Global setup config is not available in the {} config file".format(config_file))
            fun_test.log("Going to use the script level defaults")
            self.bootargs = Fs.DEFAULT_BOOT_ARGS
            self.disable_f1_index = None
            self.f1_in_use = 0
            self.syslog = "default"
            self.command_timeout = 5
            self.reboot_timeout = 600
        else:
            for k, v in config_dict["GlobalSetup"].items():
                setattr(self, k, v)

        fun_test.log("Global Config: {}".format(self.__dict__))

        # Declaring default values if not defined in config files
        if not hasattr(self, "dut_start_index"):
            self.dut_start_index = 0
        if not hasattr(self, "host_start_index"):
            self.host_start_index = 0
        if not hasattr(self, "update_workspace"):
            self.update_workspace = False
        if not hasattr(self, "update_deploy_script"):
            self.update_deploy_script = False

        # Using Parameters passed during execution, this will override global and config parameters
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        fun_test.log("Provided job inputs: {}".format(job_inputs))
        if "dut_start_index" in job_inputs:
            self.dut_start_index = job_inputs["dut_start_index"]
        if "host_start_index" in job_inputs:
            self.host_start_index = job_inputs["host_start_index"]
        if "num_hosts" in job_inputs:
            self.num_hosts = job_inputs["num_hosts"]
        if "update_workspace" in job_inputs:
            self.update_workspace = job_inputs["update_workspace"]
        if "update_deploy_script" in job_inputs:
            self.update_deploy_script = job_inputs["update_deploy_script"]
        if "disable_wu_watchdog" in job_inputs:
            self.disable_wu_watchdog = job_inputs["disable_wu_watchdog"]
        else:
            self.disable_wu_watchdog = True
        if "f1_in_use" in job_inputs:
            self.f1_in_use = job_inputs["f1_in_use"]
        if "syslog" in job_inputs:
            self.syslog = job_inputs["syslog"]

        # Deploying of DUTs
        self.num_duts = int(round(float(self.num_f1s) / self.num_f1_per_fs))
        fun_test.log("Num DUTs for current test: {}".format(self.num_duts))

        # Pulling test bed specific configuration if script is not submitted with testbed-type suite-based
        self.testbed_type = fun_test.get_job_environment_variable("test_bed_type")
        self = single_fs_setup(self)

        # Forming shared variables for defined parameters
        fun_test.shared_variables["f1_in_use"] = self.f1_in_use
        fun_test.shared_variables["topology"] = self.topology
        fun_test.shared_variables["fs_obj"] = self.fs_objs
        fun_test.shared_variables["come_obj"] = self.come_obj
        fun_test.shared_variables["f1_obj"] = self.f1_objs
        fun_test.shared_variables["sc_obj"] = self.sc_objs
        fun_test.shared_variables["f1_ips"] = self.f1_ips
        fun_test.shared_variables["host_handles"] = self.host_handles
        fun_test.shared_variables["host_ips"] = self.host_ips
        fun_test.shared_variables["numa_cpus"] = self.host_numa_cpus
        fun_test.shared_variables["total_numa_cpus"] = self.total_numa_cpus
        fun_test.shared_variables["num_f1s"] = self.num_f1s
        fun_test.shared_variables["num_duts"] = self.num_duts
        fun_test.shared_variables["syslog"] = self.syslog
        fun_test.shared_variables["db_log_time"] = self.db_log_time
        fun_test.shared_variables["host_info"] = self.host_info
        fun_test.shared_variables["csi_perf_enabled"] = self.csi_perf_enabled
        fun_test.shared_variables["csi_cache_miss_enabled"] = self.csi_cache_miss_enabled
        if self.csi_perf_enabled or self.csi_cache_miss_enabled:
            fun_test.shared_variables["perf_listener_host_name"] = self.perf_listener_host_name
            fun_test.shared_variables["perf_listener_ip"] = self.perf_listener_ip

        for host_name in self.host_info:
            host_handle = self.host_info[host_name]["handle"]
            # Ensure all hosts are up after reboot
            fun_test.test_assert(host_handle.ensure_host_is_up(max_wait_time=self.reboot_timeout),
                                 message="Ensure Host {} is reachable after reboot".format(host_name))

            # TODO: enable after mpstat check is added
            """
            # Check and install systat package
            install_sysstat_pkg = host_handle.install_package(pkg="sysstat")
            fun_test.test_assert(expression=install_sysstat_pkg, message="sysstat package available")
            """
            # Ensure required modules are loaded on host server, if not load it
            for module in self.load_modules:
                module_check = host_handle.lsmod(module)
                if not module_check:
                    host_handle.modprobe(module)
                    module_check = host_handle.lsmod(module)
                    fun_test.sleep("Loading {} module".format(module))
                fun_test.simple_assert(module_check, "{} module is loaded".format(module))

        # Ensuring connectivity from Host to F1's
        for host_name in self.host_info:
            host_handle = self.host_info[host_name]["handle"]
            for index, ip in enumerate(self.f1_ips):
                ping_status = host_handle.ping(dst=ip, max_percentage_loss=80)
                fun_test.test_assert(ping_status, "Host {} is able to ping to {}'s bond interface IP {}".
                                     format(host_name, self.funcp_spec[0]["container_names"][index], ip))

        # Ensuring perf_host is able to ping F1 IP
        if self.csi_perf_enabled or self.csi_cache_miss_enabled:
            # csi_perf_host_instance = csi_perf_host_obj.get_instance()  # TODO: Returning as NoneType
            csi_perf_host_instance = Linux(host_ip=self.csi_perf_host_obj.spec["host_ip"],
                                           ssh_username=self.csi_perf_host_obj.spec["ssh_username"],
                                           ssh_password=self.csi_perf_host_obj.spec["ssh_password"])
            ping_status = csi_perf_host_instance.ping(dst=self.csi_f1_ip)
            fun_test.test_assert(ping_status, "Host {} is able to ping to F1 IP {}".
                                 format(self.perf_listener_host_name, self.csi_f1_ip))

    def cleanup(self):
        pass

class RecoveryWithFailures(FunTestCase):

    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__
        self.sc_lock = Lock()
        self.syslog = fun_test.shared_variables["syslog"]

        # Start of benchmarking json file parsing and initializing various variables to run this testcase
        benchmark_parsing = True
        benchmark_file = ""
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Benchmark file being used: {}".format(benchmark_file))

        benchmark_dict = {}
        benchmark_dict = utils.parse_file_to_json(benchmark_file)

        if testcase not in benchmark_dict or not benchmark_dict[testcase]:
            benchmark_parsing = False
            fun_test.critical("Benchmarking is not available for the current testcase {} in {} file".
                              format(testcase, benchmark_file))
            fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))

        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))


        if not hasattr(self, "num_ssd"):
            self.num_ssd = 1
        # End of benchmarking json file parsing

        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
        fun_test.shared_variables["attach_transport"] = self.attach_transport
        fun_test.shared_variables["nvme_subsystem"] = self.nvme_subsystem

        # Checking whether the job's inputs argument is having the number of volumes and/or capacity of each volume
        # to be used in this test. If so, override the script default with the user provided config
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        if "num_volumes" in job_inputs:
            self.ec_info["num_volumes"] = job_inputs["num_volumes"]
        if "vol_size" in job_inputs:
            self.ec_info["capacity"] = job_inputs["vol_size"]
        if "nvme_io_queues" in job_inputs:
            self.nvme_io_queues = job_inputs["nvme_io_queues"]
        if "plex_fail_method" in job_inputs:
            self.plex_fail_method = job_inputs["plex_fail_method"]
        if "plex_failure_combination" in job_inputs:
            self.plex_failure_combination = job_inputs["plex_failure_combination"]
        if "write_bs" in job_inputs:
            self.fio_write_cmd_args["bs"] = str(job_inputs["write_bs"]) + "k"
        if "read_bs" in job_inputs:
            self.fio_read_cmd_args["bs"] = str(job_inputs["read_bs"]) + "k"
        if "csi_perf_iodepth" in job_inputs:
            self.csi_perf_iodepth = job_inputs["csi_perf_iodepth"]
            if not isinstance(self.csi_perf_iodepth, list):
                self.csi_perf_iodepth = [self.csi_perf_iodepth]
            self.full_run_iodepth = self.csi_perf_iodepth
        if "post_results" in job_inputs:
            self.post_results = job_inputs["post_results"]
        else:
            self.post_results = False

        self.f1_in_use = fun_test.shared_variables["f1_in_use"]
        self.fs = fun_test.shared_variables["fs_obj"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1 = fun_test.shared_variables["f1_obj"][0][0]
        self.storage_controller = fun_test.shared_variables["sc_obj"][self.f1_in_use]
        self.f1_ips = fun_test.shared_variables["f1_ips"][self.f1_in_use]
        self.host_info = fun_test.shared_variables["host_info"]
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_loopback_ip"] = self.f1_ips
        self.num_duts = fun_test.shared_variables["num_duts"]
        self.num_hosts = len(self.host_info)
        self.csi_perf_enabled = fun_test.shared_variables["csi_perf_enabled"]
        self.csi_cache_miss_enabled = fun_test.shared_variables["csi_cache_miss_enabled"]
        if self.csi_perf_enabled or self.csi_cache_miss_enabled:
            self.perf_listener_host_name = fun_test.shared_variables["perf_listener_host_name"]
            self.perf_listener_ip = fun_test.shared_variables["perf_listener_ip"]

        #IP_CFG
        command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "ip_cfg configured on DUT instance")

        # Setting the required syslog level
        if self.syslog != "default":
            command_result = self.storage_controller.poke(props_tree=["params/syslog/level", self.syslog],
                                                          legacy=False, command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"],
                                 "Setting syslog level to {}".format(self.syslog))

            command_result = self.storage_controller.peek(props_tree="params/syslog/level", legacy=False,
                                                          command_duration=self.command_timeout)
            fun_test.test_assert_expected(expected=self.syslog, actual=command_result["data"],
                                          message="Checking syslog level")
        else:
            fun_test.log("Default syslog level is requested...So not going to modify the syslog settings")

    def run(self):

        testcase = self.__class__.__name__

        #Create controller
        self.ctrlr_uuid = []
        for index, host_name in enumerate(self.host_info):
            self.ctrlr_uuid.append(utils.generate_uuid())
            command_result = self.storage_controller.create_controller(ctrlr_id=index,
                                                                       ctrlr_uuid=self.ctrlr_uuid[-1],
                                                                       ctrlr_type="BLOCK",
                                                                       transport=self.attach_transport,
                                                                       remote_ip=self.host_info[host_name]["ip"],
                                                                       subsys_nqn=self.nvme_subsystem,
                                                                       host_nqn=self.host_info[host_name]["ip"],
                                                                       port=self.transport_port,
                                                                       command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"],
                                 "Create Storage Controller for {} with controller uuid {} on DUT".
                                 format(self.attach_transport, self.ctrlr_uuid[-1]))

        for combo in self.ec_list:
            self.ec_info["ndata"] = int(combo.split(",")[0])
            self.ec_info["nparity"] = int(combo.split(",")[1])
            plex_fail_comb_list = []
            if self.plex_failure_combination == "all":
                plex_fail_comb_list = list(
                    itertools.combinations(range(self.ec_info["ndata"] + self.ec_info["nparity"]),
                                           self.ec_info["nparity"]))
            elif self.plex_failure_combination == "random":
                plex_fail_comb_list.append(tuple(random.sample(range(self.ec_info["ndata"] + self.ec_info["nparity"]), self.ec_info["nparity"])))
            for plex_fail_pattern in plex_fail_comb_list:

                #configure ec volume
                (ec_config_status, self.ec_info) = self.storage_controller.configure_ec_volume(self.ec_info,self.command_timeout)
                fun_test.simple_assert(ec_config_status, "Configuring EC/LSV volume")

                fun_test.log("EC details after configuring EC Volume with encryption enabled:")
                for k, v in self.ec_info.items():
                    fun_test.log("{}: {}".format(k, v))

                # Attach volume to controller
                for num in xrange(self.ec_info["num_volumes"]):
                    curr_ctrlr_index = num % self.num_hosts
                    curr_host_name = self.host_info.keys()[curr_ctrlr_index]
                    if "num_volumes" not in self.host_info[curr_host_name]:
                        self.host_info[curr_host_name]["num_volumes"] = 0
                    command_result = self.storage_controller.attach_volume_to_controller(
                        ctrlr_uuid=self.ctrlr_uuid[curr_ctrlr_index], ns_id=num + 1,
                        vol_uuid=self.ec_info["attach_uuid"][num], command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Attaching {} EC/LS volume on DUT".format(num))
                    self.host_info[curr_host_name]["num_volumes"] += 1

                # Get the device id for the plexes
                self.ec_info = get_plex_device_id(self.ec_info, self.storage_controller)
                #fun_test.shared_variables["ec_info"] = self.ec_info

                # Do nvme connect, check if host is able to see the volume
                for host_name in self.host_info:
                    #fun_test.shared_variables["ec"][host_name] = {}
                    host_handle = self.host_info[host_name]["handle"]
                    # Checking nvme-connect status
                    if not hasattr(self, "nvme_io_queues") or (
                            hasattr(self, "nvme_io_queues") and self.nvme_io_queues == 0):
                        nvme_connect_status = host_handle.nvme_connect(
                            target_ip=self.test_network["f1_loopback_ip"], nvme_subsystem=self.nvme_subsystem,
                            port=self.transport_port, transport=self.attach_transport,
                            hostnqn=self.host_info[host_name]["ip"])
                    else:
                        nvme_connect_status = host_handle.nvme_connect(
                            target_ip=self.test_network["f1_loopback_ip"], nvme_subsystem=self.nvme_subsystem,
                            port=self.transport_port, transport=self.attach_transport,
                            nvme_io_queues=self.nvme_io_queues,
                            hostnqn=self.host_info[host_name]["ip"])

                    fun_test.test_assert(nvme_connect_status, message="{} - NVME Connect Status".format(host_name))
                    """
                    lsblk_output = host_handle.lsblk("-b")
                    fun_test.simple_assert(lsblk_output, "Listing available volumes")
                    """
                    # Checking if the EC volume is visible to the end host
                    self.host_info[host_name]["nvme_block_device_list"] = host_handle.get_nvme_device_list()
                    """
                    volume_pattern = self.nvme_device.replace("/dev/", "") + r"(\d+)n(\d+)"
                    for volume_name in lsblk_output:
                        match = re.search(volume_pattern, volume_name)
                        if match:
                            self.nvme_block_device = self.nvme_device + str(match.group(1)) + "n" + \
                                                     str(match.group(2))
                            self.host_info[host_name]["nvme_block_device_list"].append(self.nvme_block_device)
                            fun_test.log("NVMe Block Device/s: {}".
                                         format(self.host_info[host_name]["nvme_block_device_list"]))

                    fun_test.test_assert_expected(expected=self.host_info[host_name]["num_volumes"],
                                                  actual=len(self.host_info[host_name]["nvme_block_device_list"]),
                                                  message="Expected NVMe devices are available")
                    """
                    self.host_info[host_name]["nvme_block_device_list"].sort()
                    self.host_info[host_name]["fio_filename"] = \
                        ":".join(self.host_info[host_name]["nvme_block_device_list"])
                    #fun_test.shared_variables["host_info"] = self.host_info
                    fun_test.log("Hosts info: {}".format(self.host_info))

                    # Perform write
                    #self.fio_write_cmd_args["bs"] = str(self.ec_info["ndata"] * 4) + "k"
                    #self.fio_read_cmd_args["bs"] = self.fio_write_cmd_args["bs"]
                    fio_output = host_handle.pcie_fio(filename=self.host_info[host_name]["fio_filename"],
                                                      cpus_allowed=self.host_info[host_name]["host_numa_cpus"],
                                                      **self.fio_write_cmd_args)
                    fun_test.log("FIO Command Output:\n{}".format(fio_output))
                    fun_test.test_assert(fio_output, "Write completed on EC volume from host")
                    write_initial_vol_stats = self.storage_controller.peek(
                        props_tree="storage/volumes/VOL_TYPE_BLK_EC/{}/stats".format(self.ec_info["uuids"][num]["ec"][0]), legacy=False, chunk=8192, command_duration=self.command_timeout)
                    fun_test.log("EC Volume stats:\n{}".format(write_initial_vol_stats))
                    fun_test.test_assert(write_initial_vol_stats, "EC Volume stats after WRITE")
                    fun_test.log("EC volume recovery read count:\n{}".format(write_initial_vol_stats["data"]["recovery_read_count"]))
                    # Perform read
                    fio_output = host_handle.pcie_fio(filename=self.host_info[host_name]["fio_filename"],
                                                      cpus_allowed=self.host_info[host_name]["host_numa_cpus"],
                                                      **self.fio_read_cmd_args)
                    fun_test.log("FIO Command Output:\n{}".format(fio_output))
                    fun_test.test_assert(fio_output,
                                         "READ with verify completed before failing any plex")
                    read_initial_vol_stats = self.storage_controller.peek(
                        props_tree="storage/volumes/VOL_TYPE_BLK_EC/{}/stats".format(self.ec_info["uuids"][num]["ec"][0]), legacy=False, chunk=8192, command_duration=self.command_timeout)
                    fun_test.log("EC Volume stats:\n{}".format(read_initial_vol_stats))
                    fun_test.test_assert(read_initial_vol_stats, "EC Volume stats after WRITE")
                    fun_test.log("EC volume recovery read count:\n{}".format(read_initial_vol_stats["data"]["recovery_read_count"]))

                    # Power OFF device
                    self.device_id_failed = []
                    for index, plex in enumerate(plex_fail_pattern):
                        if self.plex_fail_method == "ssd_power_off":
                            fun_test.log("Initiating drive failure for device id {} by powering off ssd".format(self.ec_info["device_id"][num][plex]))
                            device_fail_status = self.storage_controller.power_toggle_ssd("off",
                                device_id=self.ec_info["device_id"][num][plex], command_duration=self.command_timeout)
                            fun_test.test_assert(device_fail_status["status"],
                                                 "Powering OFF Device ID {}".format(self.ec_info["device_id"][num][plex]))
                            # Validate if Device is marked Failed
                            device_stats = self.storage_controller.get_ssd_power_status(self.ec_info["device_id"][num][plex], command_duration=self.command_timeout)
                            fun_test.simple_assert(device_stats["status"],
                                                   "Device {} stats command".format(self.ec_info["device_id"][num][plex]))
                            fun_test.test_assert_expected(expected=1,
                                                          actual=device_stats["data"]["input"],
                                                          message="Device ID {} is powered OFF".format(
                                                              self.ec_info["device_id"][num][plex]))
                            self.device_id_failed.append(self.ec_info["device_id"][num][plex])
                        elif self.plex_fail_method == "drive_pull":
                            fun_test.log("Initiating drive failure for device id {} by injecting fault".format(self.ec_info["device_id"][num][plex]))
                            device_fail_status = self.storage_controller.disable_device(device_id=self.ec_info["device_id"][num][plex],
                                                                                             command_duration=self.command_timeout)
                            fun_test.test_assert(device_fail_status["status"],
                                                 "Injecting fault on Device ID {}".format(self.ec_info["device_id"][num][plex]))
                            # Validate if Device is marked Failed
                            device_stats = self.storage_controller.get_device_status(device_id=self.ec_info["device_id"][num][plex], command_duration=self.command_timeout)
                            fun_test.simple_assert(device_stats["status"],
                                                   "Device {} stats command".format(self.ec_info["device_id"][num][plex]))
                            fun_test.test_assert_expected(expected="DEV_ERR_INJECT_ENABLED",
                                                          actual=device_stats["data"]["device state"],
                                                          message="Device ID {} is marked as Failed".format(
                                                              self.ec_info["device_id"][num][plex]))
                            self.device_id_failed.append(self.ec_info["device_id"][num][plex])

                        # Perform read if concurrent plex failure is not set
                        if (not hasattr(self, "m_concurrent_failure")) and (not hasattr(self, "m_plus_concurrent_failure")):
                            fio_output = host_handle.pcie_fio(filename=self.host_info[host_name]["fio_filename"],
                                                              cpus_allowed=self.host_info[host_name]["host_numa_cpus"],
                                                              **self.fio_read_cmd_args)
                            fun_test.log("FIO Command Output:\n{}".format(fio_output))
                            fun_test.test_assert(fio_output, "Reading from EC volume with {} plex {} failed".
                                                 format(index + 1, self.device_id_failed))

                    # Perform read if concurrent plex failure is set
                    if (hasattr(self, "m_concurrent_failure") and self.m_concurrent_failure) and (not hasattr(self, "m_plus_concurrent_failure")):
                        fio_output = host_handle.pcie_fio(filename=self.host_info[host_name]["fio_filename"],
                                                          cpus_allowed=self.host_info[host_name]["host_numa_cpus"],
                                                          **self.fio_read_cmd_args)
                        fun_test.log("FIO Command Output:\n{}".format(fio_output))
                        fun_test.test_assert(fio_output, "Reading from EC volume with {} plex {} failed".
                                             format(index + 1, self.device_id_failed))

                    if (hasattr(self, "mplusfailure") and self.mplusfailure) or (hasattr(self, "m_plus_concurrent_failure") and self.m_plus_concurrent_failure) or (hasattr(self, "k_plus_m_concurrent_failure") and self.k_plus_m_concurrent_failure):
                        plex_to_be_failed = []
                        if not hasattr(self, "k_plus_m_concurrent_failure"):
                            # Fail one more plex other than the above ones
                            #while True:
                            plex_to_be_failed.append(random.choice(list(set(self.ec_info["device_id"][num]).difference(set(self.device_id_failed)))))
                                #if plex_to_be_failed[0] not in plex_fail_pattern:
                                    #break
                        elif hasattr(self, "k_plus_m_concurrent_failure") and self.k_plus_m_concurrent_failure:
                            # Fail all the plexes, other than the ones failed already
                            plex_to_be_failed = list(set(self.ec_info["device_id"][num]).difference(set(self.device_id_failed)))
                        for plex in plex_to_be_failed:
                            if self.plex_fail_method == "ssd_power_off":
                                fun_test.log(
                                    "After failing {} drives, initiating drive failure on drive {}".format(
                                        self.device_id_failed, plex))
                                device_fail_status = self.storage_controller.power_toggle_ssd("off",
                                                                                              device_id=plex,
                                                                                              command_duration=self.command_timeout)
                                fun_test.test_assert(device_fail_status["status"],
                                                     "Powering OFF Device ID {}".format(plex))
                                # Validate if Device is marked Failed
                                device_stats = self.storage_controller.get_ssd_power_status(plex,
                                                                                            command_duration=self.command_timeout)
                                fun_test.simple_assert(device_stats["status"],
                                                       "Device {} stats command".format(plex))
                                fun_test.test_assert_expected(expected=1,
                                                              actual=device_stats["data"]["input"],
                                                              message="Device ID {} is powered OFF".format(
                                                                  plex))
                                self.device_id_failed.append(plex)
                            elif self.plex_fail_method == "drive_pull":
                                fun_test.log(
                                    "Initiating drive failure for drive id {} by injecting fault".format(
                                        plex))
                                device_fail_status = self.storage_controller.disable_device(device_id=plex,
                                                                                            command_duration=self.command_timeout)
                                fun_test.test_assert(device_fail_status["status"],
                                                     "Injecting fault on Device ID {}".format(plex))
                                # Validate if Device is marked Failed
                                device_stats = self.storage_controller.get_device_status(device_id=plex,
                                                                                         command_duration=self.command_timeout)
                                fun_test.simple_assert(device_stats["status"],
                                                       "Device {} stats command".format(plex))
                                fun_test.test_assert_expected(expected="DEV_ERR_INJECT_ENABLED",
                                                              actual=device_stats["data"]["device state"],
                                                              message="Device ID {} is marked as Failed".format(
                                                                  plex))
                                self.device_id_failed.append(plex)
                        # Perform read
                        fio_output = host_handle.pcie_fio(
                            filename=self.host_info[host_name]["fio_filename"],
                            cpus_allowed=self.host_info[host_name]["host_numa_cpus"],
                            **self.fio_read_cmd_args)
                        fun_test.log("FIO Command Output:\n{}".format(fio_output))
                        fun_test.test_assert(not(fio_output),
                                             "After failing {} plexes with drive ids {} concurrently, \
                                             unable to read from EC volume as expected".
                                             format(len(self.device_id_failed), self.device_id_failed))

                    # Power ON the devices that were powered OFF
                    self.device_id_clean_up = deepcopy(self.device_id_failed)
                    for plex in self.device_id_clean_up:
                        if self.plex_fail_method == "ssd_power_off":
                            fun_test.log("Initiating power ON for drive {}".format(plex))
                            device_bringup_status = self.storage_controller.power_toggle_ssd("on",
                                device_id=plex, command_duration=self.command_timeout)
                            fun_test.simple_assert(device_bringup_status["status"],
                                                 "Powering ON Device ID {}".format(plex))
                            # Validate if Device is marked Failed
                            device_stats = self.storage_controller.get_ssd_power_status(plex, command_duration=self.command_timeout)
                            fun_test.simple_assert(device_stats["status"],
                                                   "Device {} stats command".format(plex))
                            fun_test.test_assert_expected(expected=0,
                                                          actual=device_stats["data"]["input"],
                                                          message="Device ID {} is powered ON".format(
                                                              plex))
                            self.device_id_failed.remove(plex)
                        elif self.plex_fail_method == "drive_pull":
                            fun_test.log("Clearing the injected fault for device id {}".format(plex))
                            device_bringup_status = self.storage_controller.enable_device(device_id=plex,
                                                                                        command_duration=self.command_timeout)
                            fun_test.test_assert(device_bringup_status["status"],
                                                 "Clearing fault on Device ID {}".format(plex))
                            # Validate if Device is marked Failed
                            device_stats = self.storage_controller.get_device_status(device_id=plex, command_duration=self.command_timeout)
                            fun_test.simple_assert(device_stats["status"],
                                                   "Device {} stats command".format(plex))
                            fun_test.test_assert_expected(expected="DEV_ONLINE",
                                                          actual=device_stats["data"]["device state"],
                                                          message="Cleared fault on Device ID {}".format(
                                                              plex))
                            self.device_id_failed.remove(plex)
                    self.device_id_clean_up = self.device_id_failed
                    # Executing NVMe disconnect from all the hosts
                    nvme_disconnect_cmd = "nvme disconnect -n {}".format(self.nvme_subsystem)
                    nvme_disconnect_output = host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                    nvme_disconnect_exit_status = host_handle.exit_status()
                    fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                                  message="{} - NVME Disconnect Status".format(host_name))

                # Detaching all the EC/LS volumes from the external server
                command_result = self.storage_controller.detach_volume_from_controller(
                    ctrlr_uuid=self.ctrlr_uuid[num], ns_id=num + 1, command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "Detaching {} EC/LS volume from DUT".format(num))

                # Unconfiguring all the LSV/EC and it's plex volumes
                self.storage_controller.unconfigure_ec_volume(ec_info=self.ec_info,
                                                              command_timeout=self.command_timeout)

    def cleanup(self):
        # If the READ fails, Power ON the drives that were powered OFF
        for plex in self.device_id_failed:
            if self.plex_fail_method == "ssd_power_off":
                fun_test.log("After READ failure, initiating power ON for drive {}".format(plex))
                device_bringup_status = self.storage_controller.power_toggle_ssd("on",
                                                                                    device_id=plex,
                                                                                    command_duration=self.command_timeout)
                fun_test.simple_assert(device_bringup_status["status"],
                                       "Powering ON Device ID {}".format(plex))
                # Validate if Device is marked Failed
                device_stats = self.storage_controller.get_ssd_power_status(plex, command_duration=self.command_timeout)
                fun_test.simple_assert(device_stats["status"],
                                       "Device {} stats command".format(plex))
                fun_test.test_assert_expected(expected=0,
                                              actual=device_stats["data"]["input"],
                                              message="Device ID {} is powered ON".format(
                                                  plex))
            elif self.plex_fail_method == "drive_pull":
                fun_test.log("After READ failure, clearing fault for device id {}".format(plex))
                device_bringup_status = self.storage_controller.enable_device(device_id=plex,
                                                                                    command_duration=self.command_timeout)
                fun_test.simple_assert(device_bringup_status["status"],
                                       "Clearing fault on Device ID {}".format(plex))
                # Validate if Device is marked Online
                device_stats = self.storage_controller.get_device_status(device_id=plex, command_duration=self.command_timeout)
                fun_test.simple_assert(device_stats["status"],
                                       "Device {} stats command".format(plex))
                fun_test.test_assert_expected(expected="DEV_ONLINE",
                                              actual=device_stats["data"]["device state"],
                                              message="Cleared fault on Device ID {}".format(
                                                  plex))

        # Deleting all the storage controller
        for index in xrange(len(self.host_info)):
            command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid[index],
                                                                       command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Deleting Storage Controller {}".
                                 format(self.ctrlr_uuid[index]))

class RecoveryWithMFailure(RecoveryWithFailures):
    def describe(self):
        self.set_test_details(id=1,
                              summary="EC recovery with M plex failure",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using FIO
        8. Run the Performance for 8k transfer size Random read/write IOPS
        """)

    def setup(self):
        super(RecoveryWithMFailure, self).setup()

    def run(self):
        super(RecoveryWithMFailure, self).run()

    def cleanup(self):
        super(RecoveryWithMFailure, self).cleanup()

class RecoveryWithMplus1Failure(RecoveryWithFailures):

    def describe(self):
        self.set_test_details(id=2,
                              summary="EC recovery with M+1 plex failure",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using FIO
        8. Run the Performance for 8k transfer size Random read/write IOPS
        """)

    def setup(self):
        super(RecoveryWithMplus1Failure, self).setup()

    def run(self):
        super(RecoveryWithMplus1Failure, self).run()

    def cleanup(self):
        super(RecoveryWithMplus1Failure, self).cleanup()

class RecoveryWithMConcurrentFailure(RecoveryWithFailures):

    def describe(self):
        self.set_test_details(id=3,
                              summary="EC recovery with M concurrent plex failure",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using FIO
        8. Run the Performance for 8k transfer size Random read/write IOPS
        """)

    def setup(self):
        super(RecoveryWithMConcurrentFailure, self).setup()

    def run(self):
        super(RecoveryWithMConcurrentFailure, self).run()

    def cleanup(self):
        super(RecoveryWithMConcurrentFailure, self).cleanup()

class RecoveryWithMplusConcurrentFailure(RecoveryWithFailures):

    def describe(self):
        self.set_test_details(id=4,
                              summary="EC recovery with M plus concurrent plex failure",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using FIO
        8. Run the Performance for 8k transfer size Random read/write IOPS
        """)

    def setup(self):
        super(RecoveryWithMplusConcurrentFailure, self).setup()

    def run(self):
        super(RecoveryWithMplusConcurrentFailure, self).run()

    def cleanup(self):
        super(RecoveryWithMplusConcurrentFailure, self).cleanup()

class RecoveryWithKplusMConcurrentFailure(RecoveryWithFailures):

    def describe(self):
        self.set_test_details(id=5,
                              summary="EC recovery with K plus M plus concurrent plex failure",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using FIO
        8. Run the Performance for 8k transfer size Random read/write IOPS
        """)

    def setup(self):
        super(RecoveryWithKplusMConcurrentFailure, self).setup()

    def run(self):
        super(RecoveryWithKplusMConcurrentFailure, self).run()

    def cleanup(self):
        super(RecoveryWithKplusMConcurrentFailure, self).cleanup()

if __name__ == "__main__":
    ecrecovery = ECBlockRecoveryScript()
    ecrecovery.add_test_case(RecoveryWithMFailure())
    ecrecovery.add_test_case(RecoveryWithMplus1Failure())
    ecrecovery.add_test_case(RecoveryWithMConcurrentFailure())
    ecrecovery.add_test_case(RecoveryWithMplusConcurrentFailure())
    ecrecovery.add_test_case(RecoveryWithKplusMConcurrentFailure())
    ecrecovery.run()
