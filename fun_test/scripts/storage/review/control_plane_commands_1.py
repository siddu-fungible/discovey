from lib.system.fun_test import *
from lib.system import utils
from lib.host.traffic_generator import TrafficGenerator
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper, get_data_collection_time
from lib.fun.fs import Fs
from lib.host.linux import Linux
from scripts.storage.funcp_deploy import FunCpDockerContainer
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_fs_template import *
from scripts.storage.storage_helper import *
from scripts.networking.helper import *
from collections import OrderedDict
from lib.templates.csi_perf.csi_perf_template import CsiPerfTemplate
from lib.templates.storage.storage_controller_api import *

'''
Script to track the performance of various read write combination with multiple (12) local thin block volumes using FIO
'''


def fio_parser(arg1, host_index, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    fun_test.shared_variables["fio"][host_index] = fio_output
    fun_test.test_assert(fio_output, "Fio test for thread {}".format(host_index), ignore_on_success=True)
    arg1.disconnect()


def get_iostat(host_thread, sleep_time, iostat_interval, iostat_iter):
    host_thread.sudo_command("sleep {} ; iostat {} {} -d nvme0n1 > /tmp/iostat.log".
                             format(sleep_time, iostat_interval, iostat_iter), timeout=400)
    host_thread.sudo_command("awk '/^nvme0n1/' <(cat /tmp/iostat.log) | sed 1d > /tmp/iostat_final.log")

    fun_test.shared_variables["avg_tps"] = host_thread.sudo_command(
        "awk '{ total += $2 } END { print total/NR }' /tmp/iostat_final.log")

    fun_test.shared_variables["avg_kbr"] = host_thread.sudo_command(
        "awk '{ total += $3 } END { print total/NR }' /tmp/iostat_final.log")

    host_thread.disconnect()


def post_results(volume, test, block_size, io_depth, size, operation, write_iops, read_iops, write_bw, read_bw,
                 write_latency, write_90_latency, write_95_latency, write_99_latency, write_99_99_latency, read_latency,
                 read_90_latency, read_95_latency, read_99_latency, read_99_99_latency, fio_job_name):

    for i in ["write_iops", "read_iops", "write_bw", "read_bw", "write_latency", "write_90_latency", "write_95_latency",
              "write_99_latency", "write_99_99_latency", "read_latency", "read_90_latency", "read_95_latency",
              "read_99_latency", "read_99_99_latency", "fio_job_name"]:
        if eval("type({}) is tuple".format(i)):
            exec ("{0} = {0}[0]".format(i))

    db_log_time = fun_test.shared_variables["db_log_time"]
    num_ssd = fun_test.shared_variables["num_ssd"]
    num_volume = fun_test.shared_variables["blt_count"]

    blt = BltVolumePerformanceHelper()
    blt.add_entry(date_time=db_log_time, volume=volume, test=test, block_size=block_size, io_depth=int(io_depth),
                  size=size, operation=operation, num_ssd=num_ssd, num_volume=num_volume, fio_job_name=fio_job_name,
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


def compare(actual, expected, threshold, operation):
    if operation == "lesser":
        return (actual < (expected * (1 - threshold)) and ((expected - actual) > 2))
    else:
        return (actual > (expected * (1 + threshold)) and ((actual - expected) > 2))


class MultiHostVolumePerformanceScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Bring up FS
        2. Make the Linux instance available for the testcase
        """)

    def setup(self):

        # Parsing the global config and assign them as object members
        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))
        config_dict = utils.parse_file_to_json(config_file)

        fun_test.shared_variables["fio"] = {}

        if "GlobalSetup" not in config_dict or not config_dict["GlobalSetup"]:
            fun_test.critical("Global setup config is not available in the {} config file".format(config_file))
            fun_test.log("Going to use the script level defaults")
            self.bootargs = Fs.DEFAULT_BOOT_ARGS
            self.disable_f1_index = None
            self.f1_in_use = 0
            self.syslog = 2
            self.command_timeout = 30
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
        if "update_workspace" in job_inputs:
            self.update_workspace = job_inputs["update_workspace"]
        if "update_deploy_script" in job_inputs:
            self.update_deploy_script = job_inputs["update_deploy_script"]
        if "num_hosts" in job_inputs:
            self.num_hosts = job_inputs["num_hosts"]
        if "disable_wu_watchdog" in job_inputs:
            self.disable_wu_watchdog = job_inputs["disable_wu_watchdog"]
        else:
            self.disable_wu_watchdog = False
        if "syslog" in job_inputs:
            self.syslog = job_inputs["syslog"]

        self.num_duts = int(round(float(self.num_f1s) / self.num_f1_per_fs))
        fun_test.log("Num DUTs for current test: {}".format(self.num_duts))

        # Pulling test bed specific configuration if script is not submitted with testbed-type suite-based
        self.testbed_type = fun_test.get_job_environment_variable("test_bed_type")

        self = single_fs_setup(self)

        # Forming shared variables for defined parameters
        fun_test.shared_variables["topology"] = self.topology
        fun_test.shared_variables["fs_objs"] = self.fs_objs
        fun_test.shared_variables["come_obj"] = self.come_obj
        fun_test.shared_variables["f1_objs"] = self.f1_objs
        fun_test.shared_variables["sc_obj"] = self.sc_objs
        fun_test.shared_variables["f1_ips"] = self.f1_ips
        fun_test.shared_variables["host_info"] = self.host_info
        fun_test.shared_variables["host_handles"] = self.host_handles
        fun_test.shared_variables["host_ips"] = self.host_ips
        fun_test.shared_variables["numa_cpus"] = self.host_numa_cpus
        fun_test.shared_variables["total_numa_cpus"] = self.total_numa_cpus
        fun_test.shared_variables["num_f1s"] = self.num_f1s
        fun_test.shared_variables["num_duts"] = self.num_duts
        fun_test.shared_variables["syslog"] = self.syslog
        fun_test.shared_variables["db_log_time"] = self.db_log_time
        fun_test.shared_variables["csi_perf_enabled"] = self.csi_perf_enabled
        fun_test.shared_variables["csi_cache_miss_enabled"] = self.csi_cache_miss_enabled

        if self.csi_perf_enabled or self.csi_cache_miss_enabled:
            fun_test.shared_variables["perf_listener_host_name"] = self.perf_listener_host_name
            fun_test.shared_variables["perf_listener_ip"] = self.perf_listener_ip

        for key in self.host_handles:
            # Ensure all hosts are up after reboot
            fun_test.test_assert(self.host_handles[key].ensure_host_is_up(max_wait_time=self.reboot_timeout),
                                 message="Ensure Host {} is reachable after reboot".format(key))

            # TODO: enable after mpstat check is added
            """
            # Check and install systat package
            install_sysstat_pkg = host_handle.install_package(pkg="sysstat")
            fun_test.test_assert(expression=install_sysstat_pkg, message="sysstat package available")
            """
            # Ensure required modules are loaded on host server, if not load it
            for module in self.load_modules:
                module_check = self.host_handles[key].lsmod(module)
                if not module_check:
                    self.host_handles[key].modprobe(module)
                    module_check = self.host_handles[key].lsmod(module)
                    fun_test.sleep("Loading {} module".format(module))
                fun_test.simple_assert(module_check, "{} module is loaded".format(module))

        # Ensuring connectivity from Host to F1's
        for key in self.host_handles:
            for index, ip in enumerate(self.f1_ips):
                ping_status = self.host_handles[key].ping(dst=ip)
                fun_test.test_assert(ping_status, "Host {} is able to ping to {}'s bond interface IP {}".
                                     format(key, self.funcp_spec[0]["container_names"][index], ip))

        # Ensuring perf_host is able to ping F1 IP
        if self.csi_perf_enabled or self.csi_cache_miss_enabled:
            # csi_perf_host_instance = csi_perf_host_obj.get_instance()  # TODO: Returning as NoneType
            csi_perf_host_instance = Linux(host_ip=self.csi_perf_host_obj.spec["host_ip"],
                                           ssh_username=self.csi_perf_host_obj.spec["ssh_username"],
                                           ssh_password=self.csi_perf_host_obj.spec["ssh_password"])
            ping_status = csi_perf_host_instance.ping(dst=self.csi_f1_ip)
            fun_test.test_assert(ping_status, "Host {} is able to ping to F1 IP {}".
                                 format(self.perf_listener_host_name, self.csi_f1_ip))

        fun_test.shared_variables["testbed_config"] = self.testbed_config
        fun_test.shared_variables["blt"] = {}
        fun_test.shared_variables["blt"]["setup_created"] = False
        fun_test.shared_variables["blt"]["warmup_done"] = False

    def cleanup(self):
        if "blt" in fun_test.shared_variables and fun_test.shared_variables["blt"]["setup_created"]:
            self.fs = self.fs_objs[0]
            self.storage_controller = fun_test.shared_variables["sc_obj"][0]
            try:
                self.blt_details = fun_test.shared_variables["blt_details"]
                self.thin_uuid_list = fun_test.shared_variables["thin_uuid"]
                self.ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]
                self.nqn_list = fun_test.shared_variables["nqn_list"]

                # Setting the syslog level back to 6
                if self.syslog != "default":
                    command_result = self.storage_controller.poke("params/syslog/level 6")
                    fun_test.test_assert(command_result["status"], "Setting syslog level to 6")

                    command_result = self.storage_controller.peek("params/syslog/level")
                    fun_test.test_assert_expected(expected=6, actual=command_result["data"],
                                                  message="Checking syslog level set to 6")

                # Executing NVMe disconnect from all the hosts
                for index, host_name in enumerate(self.host_info):
                    host_handle = self.host_info[host_name]["handle"]
                    nqn = self.nqn_list[index]

                    nvme_disconnect_cmd = "nvme disconnect -n {}".format(nqn)
                    nvme_disconnect_output = host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                    nvme_disconnect_exit_status = host_handle.exit_status()
                    fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                                  message="Host {} - NVME Disconnect Status".format(host_name))

                # Detaching and deleting the volume
                print("thin_uuid_list", self.thin_uuid_list)
                for i, vol_uuid in enumerate(self.thin_uuid_list):
                    num_hosts = len(self.host_info)
                    ctrlr_index = i % num_hosts
                    ns_id = (i / num_hosts) + 1
                    command_result = self.storage_controller.detach_volume_from_controller(
                        ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], ns_id=ns_id, command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Detaching BLT volume {} from controller {}".
                                         format(vol_uuid, self.ctrlr_uuid[ctrlr_index]))

                    command_result = self.storage_controller.delete_volume(uuid=vol_uuid,
                                                                           type=str(self.blt_details['type']),
                                                                           command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Deleting BLT {} with uuid {} on DUT".
                                         format(i + 1, vol_uuid))

                # Deleting the controller
                for index, host_name in enumerate(self.host_info):
                    command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid[index],
                                                                               command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Deleting storage controller {}".
                                         format(self.ctrlr_uuid[index]))
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("Clean-up of volumes failed.")


class MultiHostVolumePerformanceTestcase8(FunTestCase):
    # Create volume with different name but with same uuid
    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__

        self.testbed_config = fun_test.shared_variables["testbed_config"]
        self.syslog = fun_test.shared_variables["syslog"]

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

        # Setting the list of numjobs and IO depth combo
        # TODO: Check if block size is not required

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 12
        if not hasattr(self, "blt_count"):
            self.blt_count = 12

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))

        # End of benchmarking json file parsing

        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
        fun_test.shared_variables["blt_count"] = self.blt_count

        # New changes
        fun_test.shared_variables["transport_type"] = self.transport_type

        self.nvme_block_device = self.nvme_device + "0n" + str(self.blt_details["ns_id"])
        self.volume_name = self.nvme_block_device.replace("/dev/", "")

        self.fs = fun_test.shared_variables["fs_objs"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1 = fun_test.shared_variables["f1_objs"][0][0]
        self.storage_controller = fun_test.shared_variables["sc_obj"][0]
        self.f1_ips = fun_test.shared_variables["f1_ips"][0]
        self.host_info = fun_test.shared_variables["host_info"]
        self.host_handles = fun_test.shared_variables["host_handles"]
        self.csi_perf_enabled = fun_test.shared_variables["csi_perf_enabled"]
        self.csi_cache_miss_enabled = fun_test.shared_variables["csi_cache_miss_enabled"]

        if self.csi_perf_enabled or self.csi_cache_miss_enabled:
            self.perf_listener_host_name = fun_test.shared_variables["perf_listener_host_name"]
            self.perf_listener_ip = fun_test.shared_variables["perf_listener_ip"]
        self.host_ips = fun_test.shared_variables["host_ips"]
        self.num_hosts = len(self.host_ips)
        self.end_host = self.host_handles[self.host_ips[0]]
        # self.numa_cpus = fun_test.shared_variables["numa_cpus"][self.host_ips[0]]
        # self.total_numa_cpus = fun_test.shared_variables["total_numa_cpus"][self.host_ips[0]]
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_loopback_ip"] = self.f1_ips
        self.remote_ip = self.host_ips[0]
        fun_test.shared_variables["remote_ip"] = self.remote_ip
        self.num_duts = fun_test.shared_variables["num_duts"]

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}

        if "csi_perf_iodepth" in job_inputs:
            self.csi_perf_iodepth = job_inputs["csi_perf_iodepth"]
            self.full_run_iodepth = self.csi_perf_iodepth
        if not isinstance(self.csi_perf_iodepth, list):
            self.csi_perf_iodepth = [self.csi_perf_iodepth]
            self.full_run_iodepth = self.csi_perf_iodepth

        if ("blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]):
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False
            fun_test.shared_variables["blt"]["warmup_done"] = False
            fun_test.shared_variables["blt_details"] = self.blt_details

            # Enabling counters
            """
            command_result = self.storage_controller.json_execute(verb="enable_counters",
                                                                  command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling Internal Stats/Counters")
            """

            # Configuring controller IP
            command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg on DUT instance")

            # If the number of hosts is less than the number of volumes then expand the host_ips list to equal to
            # number of volumes by repeating the existing entries for the required number of times
            self.final_host_ips = self.host_ips[:]
            if len(self.host_ips) < self.blt_count:
                for i in range(len(self.host_ips), self.blt_count):
                    self.final_host_ips.append(self.host_ips[i % len(self.host_ips)])

            for host_name in self.host_info:
                self.host_info[host_name]["num_volumes"] = self.final_host_ips.count(self.host_info[host_name]["ip"])

            # Finding the usable capacity of the drives which will be used as the BLT volume capacity, in case
            # the capacity is not overridden while starting the script
            min_drive_capacity = find_min_drive_capacity(self.storage_controller, self.command_timeout)
            if min_drive_capacity:
                self.blt_details["max_capacity"] = min_drive_capacity
                # Reducing the volume capacity by drive margin as a workaround for the bug SWOS-6862
                self.blt_details["max_capacity"] -= self.drive_margin
            else:
                fun_test.critical("Unable to find the drive with minimum capacity...So going to use the BLT capacity"
                                  "given in the script config file or capacity passed at the runtime...")

            if "capacity" in job_inputs:
                fun_test.critical("Original Volume size {} is overriden by the size {} given while running the "
                                  "script".format(self.blt_details["capacity"], job_inputs["capacity"]))
                self.blt_details["capacity"] = job_inputs["capacity"]

            # Create BLT's
            self.thin_uuid_list = []
# Here is 'counter' is the counter for the volumes created
            counter=0

            cur_uuid = utils.generate_uuid()
            self.thin_uuid_list.append(cur_uuid)
            command_result = self.storage_controller.create_volume(type=self.blt_details["type"],
                                                                       capacity=self.blt_details["capacity"],
                                                                       block_size=self.blt_details["block_size"],
                                                                       name="thin_block" + str(counter + 1), group_id=counter+1,
                                                                       uuid=cur_uuid,
                                                                       command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.add_checkpoint("Create BLT {} with uuid {} and capacity{} on DUT".format(counter + 1, cur_uuid,self.blt_details["capacity"]),expected="True", actual=command_result["status"])
            #fun_test.test_assert(command_result["status"], "Create BLT {} with uuid {} on DUT".format(counter + 1,
            #                                                                                              cur_uuid))

            fun_test.shared_variables["thin_uuid"] = self.thin_uuid_list
            counter+=1


            #Reusing the same uuid
            command_result = self.storage_controller.create_volume(type=self.blt_details["type"],
                                                                   capacity=self.blt_details["capacity"],
                                                                   block_size=self.blt_details["block_size"],
                                                                   name="thin_block" + str(counter + 1),
                                                                   group_id=counter + 1,
                                                                   uuid=cur_uuid,
                                                                   command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.add_checkpoint("Create BLT {} with uuid {} and capacity{} on DUT".format(counter + 1, cur_uuid,
                                                                                              self.blt_details[
                                                                                                  "capacity"]),
                                    expected="True", actual=command_result["status"])

            #fun_test.test_assert(command_result["status"], "Create BLT {} with same uuid {} on DUT".format(counter + 1,
            #                                                                                          cur_uuid))

            fun_test.shared_variables["thin_uuid"] = self.thin_uuid_list



            # Create one TCP controller per host\
            self.ctrlr_uuid = []
            for i in range(self.blt_count):
                self.nvme_block_device = []

                self.nqn_list = []
                cur_uuid = utils.generate_uuid()
                self.ctrlr_uuid.append(cur_uuid)
                nqn = "nqn" + str(i + 1)
                self.nqn_list.append(nqn)
                command_result = self.storage_controller.create_controller(ctrlr_id=i,
                                                                           ctrlr_uuid=cur_uuid,
                                                                           ctrlr_type="BLOCK",
                                                                           transport=self.transport_type.upper(),
                                                                           remote_ip=self.host_ips[i],
                                                                           subsys_nqn=nqn,
                                                                           host_nqn=self.host_ips[i],
                                                                           port=self.transport_port,
                                                                           command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Creating TCP controller for {} with uuid {} on DUT".
                                         format(self.host_ips[i], cur_uuid))

            fun_test.shared_variables["ctrlr_uuid"] = self.ctrlr_uuid
            fun_test.shared_variables["nqn_list"] = self.nqn_list

            # Attach controller to BLTs
            print("crtrl uuid",self.ctrlr_uuid)
            for i in range(self.blt_count):
                ctrlr_index = i % self.num_hosts
                ns_id = (i / self.num_hosts) + 1
                print ("ctrlr_index is ", ctrlr_index)
                print("self.ctrlr_uuid[ctrlr_index]", self.ctrlr_uuid[ctrlr_index])
                print("self.thin_uuid_list[i]", self.thin_uuid_list[i])
                ns_id = (i / self.num_hosts) + 1
                print ("i value looping in attaching volume ", i)
                print("self.ctrlr_uuid[ctrlr_index]",self.ctrlr_uuid[ctrlr_index])
                print("self.thin_uuid_list[i]",self.thin_uuid_list[i])
                command_result = self.storage_controller.attach_volume_to_controller(
                    ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], vol_uuid=self.thin_uuid_list[i],
                    ns_id=ns_id, command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Attaching BLT volume {} to the host {} via controller "
                                                               "{}".format(self.thin_uuid_list[i],
                                                                           self.host_ips[ctrlr_index],
                                                                           self.ctrlr_uuid[ctrlr_index]))

            # Setting the fcp scheduler bandwidth
            if hasattr(self, "config_fcp_scheduler"):
                command_result = self.storage_controller.set_fcp_scheduler(fcp_sch_config=self.config_fcp_scheduler,
                                                                           command_timeout=self.command_timeout)
                if not command_result["status"]:
                    fun_test.critical("Unable to set the fcp scheduler bandwidth...So proceeding the test with the "
                                      "default setting")
                elif self.config_fcp_scheduler != command_result["data"]:
                    fun_test.critical("Unable to fetch the applied FCP scheduler config... So proceeding the test "
                                      "with the default setting")
                else:
                    fun_test.log("Successfully set the fcp scheduler bandwidth to: {}".format(command_result["data"]))

            for index, host_name in enumerate(self.host_info):
                host_handle = self.host_info[host_name]["handle"]
                host_ip = self.host_info[host_name]["ip"]
                nqn = self.nqn_list[index]
                host_handle.sudo_command("iptables -F && ip6tables -F && dmesg -c > /dev/null")
                host_handle.sudo_command("/etc/init.d/irqbalance stop")
                irq_bal_stat = host_handle.command("/etc/init.d/irqbalance status")
                if "dead" in irq_bal_stat:
                    fun_test.log("IRQ balance stopped on {}".format(i))
                else:
                    fun_test.log("IRQ balance not stopped on {}".format(i))
                    install_status = host_handle.install_package("tuned")
                    fun_test.test_assert(install_status, "tuned installed successfully")

                    host_handle.sudo_command("tuned-adm profile network-throughput && tuned-adm active")

                command_result = host_handle.command("lsmod | grep -w nvme")
                if "nvme" in command_result:
                    fun_test.log("nvme driver is loaded")
                else:
                    fun_test.log("Loading nvme")
                    host_handle.modprobe("nvme")
                    host_handle.modprobe("nvme_core")
                command_result = host_handle.lsmod("nvme_tcp")
                if "nvme_tcp" in command_result:
                    fun_test.log("nvme_tcp driver is loaded")
                else:
                    fun_test.log("Loading nvme_tcp")
                    host_handle.modprobe("nvme_tcp")
                    host_handle.modprobe("nvme_fabrics")

                host_handle.start_bg_process(command="sudo tcpdump -i enp216s0 -w nvme_connect_auto.pcap")
                if hasattr(self, "nvme_io_queues") and self.nvme_io_queues != 0:
                    command_result = host_handle.sudo_command(
                        "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}".format(unicode.lower(self.transport_type),
                                                                                  self.test_network["f1_loopback_ip"],
                                                                                  self.transport_port, nqn,
                                                                                  self.nvme_io_queues, host_ip))
                    fun_test.log(command_result)
                else:
                    command_result = host_handle.sudo_command(
                        "nvme connect -t {} -a {} -s {} -n {} -q {}".format(unicode.lower(self.transport_type),
                                                                            self.test_network["f1_loopback_ip"],
                                                                            self.transport_port, nqn, host_ip))
                    fun_test.log(command_result)
                fun_test.sleep("Wait for couple of seconds for the volume to be accessible to the host", 5)
                host_handle.sudo_command("for i in `pgrep tcpdump`;do kill -9 $i;done")
                host_handle.sudo_command("dmesg")

                lsblk_output = host_handle.lsblk("-b")
                fun_test.simple_assert(lsblk_output, "Listing available volumes")
                fun_test.log("lsblk Output: \n{}".format(lsblk_output))

                # Checking that the above created BLT volume is visible to the end host
                self.host_info[host_name]["nvme_block_device_list"] = []
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

                self.host_info[host_name]["nvme_block_device_list"].sort()
                self.host_info[host_name]["fio_filename"] = ":".join(
                    self.host_info[host_name]["nvme_block_device_list"])
                fun_test.shared_variables["host_info"] = self.host_info
                fun_test.log("Hosts info: {}".format(self.host_info))

            # Setting the required syslog level
            if self.syslog != "default":
                command_result = self.storage_controller.poke("params/syslog/level {}".format(self.syslog))
                fun_test.test_assert(command_result["status"], "Setting syslog level to {}".format(self.syslog))

                command_result = self.storage_controller.peek("params/syslog/level")
                fun_test.test_assert_expected(expected=self.syslog, actual=command_result["data"],
                                              message="Checking syslog level")
            else:
                fun_test.log("Default syslog level is requested...So not going to modify the syslog settings")

            fun_test.shared_variables["blt"]["setup_created"] = True


            # Pre-conditioning the volume (one time task)


    def run(self):
        print "in run"

    def cleanup(self):
        if "blt" in fun_test.shared_variables and fun_test.shared_variables["blt"]["setup_created"]:
            self.fs = self.fs_objs[0]
            self.storage_controller = fun_test.shared_variables["sc_obj"][0]
            try:
                self.blt_details = fun_test.shared_variables["blt_details"]
                self.thin_uuid_list = fun_test.shared_variables["thin_uuid"]
                self.ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]
                self.nqn_list = fun_test.shared_variables["nqn_list"]

                # Setting the syslog level back to 6

                for index, host_name in enumerate(self.host_info):
                    host_handle = self.host_info[host_name]["handle"]
                    nqn = self.nqn_list[index]

                    nvme_disconnect_cmd = "nvme disconnect -n {}".format(nqn)
                    nvme_disconnect_output = host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                    nvme_disconnect_exit_status = host_handle.exit_status()
                    fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                                  message="Host {} - NVME Disconnect Status".format(host_name))

                # Detaching and deleting the volume
                print("thin_uuid_list",self.thin_uuid_list)
                for i, vol_uuid in enumerate(self.thin_uuid_list):
                    num_hosts = len(self.host_info)
                    ctrlr_index = i % num_hosts
                    ns_id = (i / num_hosts) + 1
                    print ("ctrlr_index is ", ctrlr_index)
                    print("self.ctrlr_uuid[ctrlr_index]", self.ctrlr_uuid[ctrlr_index])
                    print("self.thin_uuid_list[i]", self.thin_uuid_list[i])
                    ns_id = (i / self.num_hosts) + 1
                    print ("i value looping in attaching volume ", i)
                    command_result = self.storage_controller.detach_volume_from_controller(
                        ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], ns_id=ns_id, command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Detaching BLT volume {} from controller {}".
                                         format(vol_uuid, self.ctrlr_uuid[ctrlr_index]))

                    command_result = self.storage_controller.delete_volume(uuid=vol_uuid,
                                                                           type=str(self.blt_details['type']),
                                                                           command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Deleting BLT {} with uuid {} on DUT".
                                         format(i + 1, vol_uuid))

                # Deleting the controller
                for index, host_name in enumerate(self.host_info):
                    command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid[index],
                                                                               command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Deleting storage controller {}".
                                         format(self.ctrlr_uuid[index]))
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("Clean-up of volumes failed.")

            for i in self.thin_uuid_list:
                command_result = self.storage_controller.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN/" + i)
            fun_test.test_assert_expected(expected=False, actual=command_result["Status"],
                                          message="Checking if the volume id is deleted after deleting the volume")


class MultiHostVolumePerformanceTestcase9(FunTestCase):
    # Reusing of volume name and uuid should be allowed
    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__

        self.testbed_config = fun_test.shared_variables["testbed_config"]
        self.syslog = fun_test.shared_variables["syslog"]

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

        # Setting the list of numjobs and IO depth combo
        # TODO: Check if block size is not required

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 12
        if not hasattr(self, "blt_count"):
            self.blt_count = 12

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))

        # End of benchmarking json file parsing

        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
        fun_test.shared_variables["blt_count"] = self.blt_count

        # New changes
        fun_test.shared_variables["transport_type"] = self.transport_type

        self.nvme_block_device = self.nvme_device + "0n" + str(self.blt_details["ns_id"])
        self.volume_name = self.nvme_block_device.replace("/dev/", "")

        self.fs = fun_test.shared_variables["fs_objs"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1 = fun_test.shared_variables["f1_objs"][0][0]
        self.storage_controller = fun_test.shared_variables["sc_obj"][0]
        self.f1_ips = fun_test.shared_variables["f1_ips"][0]
        self.host_info = fun_test.shared_variables["host_info"]
        self.host_handles = fun_test.shared_variables["host_handles"]
        self.csi_perf_enabled = fun_test.shared_variables["csi_perf_enabled"]
        self.csi_cache_miss_enabled = fun_test.shared_variables["csi_cache_miss_enabled"]

        if self.csi_perf_enabled or self.csi_cache_miss_enabled:
            self.perf_listener_host_name = fun_test.shared_variables["perf_listener_host_name"]
            self.perf_listener_ip = fun_test.shared_variables["perf_listener_ip"]
        self.host_ips = fun_test.shared_variables["host_ips"]
        self.num_hosts = len(self.host_ips)
        self.end_host = self.host_handles[self.host_ips[0]]
        # self.numa_cpus = fun_test.shared_variables["numa_cpus"][self.host_ips[0]]
        # self.total_numa_cpus = fun_test.shared_variables["total_numa_cpus"][self.host_ips[0]]
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_loopback_ip"] = self.f1_ips
        self.remote_ip = self.host_ips[0]
        fun_test.shared_variables["remote_ip"] = self.remote_ip
        self.num_duts = fun_test.shared_variables["num_duts"]

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}

        if "csi_perf_iodepth" in job_inputs:
            self.csi_perf_iodepth = job_inputs["csi_perf_iodepth"]
            self.full_run_iodepth = self.csi_perf_iodepth
        if not isinstance(self.csi_perf_iodepth, list):
            self.csi_perf_iodepth = [self.csi_perf_iodepth]
            self.full_run_iodepth = self.csi_perf_iodepth

        if ("blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]):
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False
            fun_test.shared_variables["blt"]["warmup_done"] = False
            fun_test.shared_variables["blt_details"] = self.blt_details

            # Enabling counters
            """
            command_result = self.storage_controller.json_execute(verb="enable_counters",
                                                                  command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling Internal Stats/Counters")
            """

            # Configuring controller IP
            command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg on DUT instance")

            # If the number of hosts is less than the number of volumes then expand the host_ips list to equal to
            # number of volumes by repeating the existing entries for the required number of times
            self.final_host_ips = self.host_ips[:]
            if len(self.host_ips) < self.blt_count:
                for i in range(len(self.host_ips), self.blt_count):
                    self.final_host_ips.append(self.host_ips[i % len(self.host_ips)])

            for host_name in self.host_info:
                self.host_info[host_name]["num_volumes"] = self.final_host_ips.count(self.host_info[host_name]["ip"])

            # Finding the usable capacity of the drives which will be used as the BLT volume capacity, in case
            # the capacity is not overridden while starting the script
            min_drive_capacity = find_min_drive_capacity(self.storage_controller, self.command_timeout)
            if min_drive_capacity:
                self.blt_details["max_capacity"] = min_drive_capacity
                # Reducing the volume capacity by drive margin as a workaround for the bug SWOS-6862
                self.blt_details["max_capacity"] -= self.drive_margin
            else:
                fun_test.critical("Unable to find the drive with minimum capacity...So going to use the BLT capacity"
                                  "given in the script config file or capacity passed at the runtime...")

            if "capacity" in job_inputs:
                fun_test.critical("Original Volume size {} is overriden by the size {} given while running the "
                                  "script".format(self.blt_details["capacity"], job_inputs["capacity"]))
                self.blt_details["capacity"] = job_inputs["capacity"]

            # Create BLT's
            self.thin_uuid_list = []
# Here is 'counter' is the counter for the volumes created
            counter=0
            #Create a volume
            cur_uuid = utils.generate_uuid()
            self.thin_uuid_list.append(cur_uuid)
            command_result = self.storage_controller.create_volume(type=self.blt_details["type"],
                                                                       capacity=self.blt_details["capacity"],
                                                                       block_size=self.blt_details["block_size"],
                                                                       name="thin_block" + str(counter + 1), group_id=counter+1,
                                                                       uuid=cur_uuid,
                                                                       command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Create BLT {} with uuid {} on DUT".format(counter + 1,
                                                                                                          cur_uuid))

            fun_test.shared_variables["thin_uuid"] = self.thin_uuid_list
            counter+=1



            # Create one TCP controller per host\
            self.ctrlr_uuid = []
            for i in range(self.blt_count):
                self.nvme_block_device = []

                self.nqn_list = []
                cur_uuid = utils.generate_uuid()
                self.ctrlr_uuid.append(cur_uuid)
                nqn = "nqn" + str(i + 1)
                self.nqn_list.append(nqn)
                command_result = self.storage_controller.create_controller(ctrlr_id=i,
                                                                           ctrlr_uuid=cur_uuid,
                                                                           ctrlr_type="BLOCK",
                                                                           transport=self.transport_type.upper(),
                                                                           remote_ip=self.host_ips[i],
                                                                           subsys_nqn=nqn,
                                                                           host_nqn=self.host_ips[i],
                                                                           port=self.transport_port,
                                                                           command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Creating TCP controller for {} with uuid {} on DUT".
                                         format(self.host_ips[i], cur_uuid))

            fun_test.shared_variables["ctrlr_uuid"] = self.ctrlr_uuid
            fun_test.shared_variables["nqn_list"] = self.nqn_list

            # Attach controller to BLTs
            print("crtrl uuid", self.ctrlr_uuid)
            for i in range(self.blt_count):
                ctrlr_index = i % self.num_hosts
                ns_id = (i / self.num_hosts) + 1
                print ("ctrlr_index is ", ctrlr_index)
                print("self.ctrlr_uuid[ctrlr_index]", self.ctrlr_uuid[ctrlr_index])
                print("self.thin_uuid_list[i]", self.thin_uuid_list[i])
                ns_id = (i / self.num_hosts) + 1
                print ("i value looping in attaching volume ", i)
                command_result = self.storage_controller.attach_volume_to_controller(
                    ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], vol_uuid=self.thin_uuid_list[i],
                    ns_id=ns_id, command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Attaching BLT volume {} to the host {} via controller "
                                                               "{}".format(self.thin_uuid_list[i],
                                                                           self.host_ips[ctrlr_index],
                                                                           self.ctrlr_uuid[ctrlr_index]))

            # Setting the fcp scheduler bandwidth
            if hasattr(self, "config_fcp_scheduler"):
                command_result = self.storage_controller.set_fcp_scheduler(fcp_sch_config=self.config_fcp_scheduler,
                                                                           command_timeout=self.command_timeout)
                if not command_result["status"]:
                    fun_test.critical("Unable to set the fcp scheduler bandwidth...So proceeding the test with the "
                                      "default setting")
                elif self.config_fcp_scheduler != command_result["data"]:
                    fun_test.critical("Unable to fetch the applied FCP scheduler config... So proceeding the test "
                                      "with the default setting")
                else:
                    fun_test.log("Successfully set the fcp scheduler bandwidth to: {}".format(command_result["data"]))

            for index, host_name in enumerate(self.host_info):
                host_handle = self.host_info[host_name]["handle"]
                host_ip = self.host_info[host_name]["ip"]
                nqn = self.nqn_list[index]
                host_handle.sudo_command("iptables -F && ip6tables -F && dmesg -c > /dev/null")
                host_handle.sudo_command("/etc/init.d/irqbalance stop")
                irq_bal_stat = host_handle.command("/etc/init.d/irqbalance status")
                if "dead" in irq_bal_stat:
                    fun_test.log("IRQ balance stopped on {}".format(i))
                else:
                    fun_test.log("IRQ balance not stopped on {}".format(i))
                    install_status = host_handle.install_package("tuned")
                    fun_test.test_assert(install_status, "tuned installed successfully")

                    host_handle.sudo_command("tuned-adm profile network-throughput && tuned-adm active")

                command_result = host_handle.command("lsmod | grep -w nvme")
                if "nvme" in command_result:
                    fun_test.log("nvme driver is loaded")
                else:
                    fun_test.log("Loading nvme")
                    host_handle.modprobe("nvme")
                    host_handle.modprobe("nvme_core")
                command_result = host_handle.lsmod("nvme_tcp")
                if "nvme_tcp" in command_result:
                    fun_test.log("nvme_tcp driver is loaded")
                else:
                    fun_test.log("Loading nvme_tcp")
                    host_handle.modprobe("nvme_tcp")
                    host_handle.modprobe("nvme_fabrics")

                host_handle.start_bg_process(command="sudo tcpdump -i enp216s0 -w nvme_connect_auto.pcap")
                if hasattr(self, "nvme_io_queues") and self.nvme_io_queues != 0:
                    command_result = host_handle.sudo_command(
                        "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}".format(unicode.lower(self.transport_type),
                                                                                  self.test_network["f1_loopback_ip"],
                                                                                  self.transport_port, nqn,
                                                                                  self.nvme_io_queues, host_ip))
                    fun_test.log(command_result)
                else:
                    command_result = host_handle.sudo_command(
                        "nvme connect -t {} -a {} -s {} -n {} -q {}".format(unicode.lower(self.transport_type),
                                                                            self.test_network["f1_loopback_ip"],
                                                                            self.transport_port, nqn, host_ip))
                    fun_test.log(command_result)
                fun_test.sleep("Wait for couple of seconds for the volume to be accessible to the host", 5)
                host_handle.sudo_command("for i in `pgrep tcpdump`;do kill -9 $i;done")
                host_handle.sudo_command("dmesg")

                lsblk_output = host_handle.lsblk("-b")
                fun_test.simple_assert(lsblk_output, "Listing available volumes")
                fun_test.log("lsblk Output: \n{}".format(lsblk_output))

                # Checking that the above created BLT volume is visible to the end host
                self.host_info[host_name]["nvme_block_device_list"] = []
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

                self.host_info[host_name]["nvme_block_device_list"].sort()
                self.host_info[host_name]["fio_filename"] = ":".join(
                    self.host_info[host_name]["nvme_block_device_list"])
                fun_test.shared_variables["host_info"] = self.host_info
                fun_test.log("Hosts info: {}".format(self.host_info))

            # Setting the required syslog level
            if self.syslog != "default":
                command_result = self.storage_controller.poke("params/syslog/level {}".format(self.syslog))
                fun_test.test_assert(command_result["status"], "Setting syslog level to {}".format(self.syslog))

                command_result = self.storage_controller.peek("params/syslog/level")
                fun_test.test_assert_expected(expected=self.syslog, actual=command_result["data"],
                                              message="Checking syslog level")
            else:
                fun_test.log("Default syslog level is requested...So not going to modify the syslog settings")

            # nvme disconnect

            for index, host_name in enumerate(self.host_info):
                host_handle = self.host_info[host_name]["handle"]
                nqn = self.nqn_list[index]

                nvme_disconnect_cmd = "nvme disconnect -n {}".format(nqn)
                nvme_disconnect_output = host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                nvme_disconnect_exit_status = host_handle.exit_status()
                fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                              message="Host {} - NVME Disconnect Status".format(host_name))

            # Detaching and deleting the volume
            print("thin_uuid_list", self.thin_uuid_list)
            for i, vol_uuid in enumerate(self.thin_uuid_list):
                num_hosts = len(self.host_info)
            ctrlr_index = i % num_hosts
            ns_id = (i / num_hosts) + 1
            command_result = self.storage_controller.detach_volume_from_controller(
                ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], ns_id=ns_id, command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Detaching BLT volume {} from controller {}".
                                 format(vol_uuid, self.ctrlr_uuid[ctrlr_index]))

            command_result = self.storage_controller.delete_volume(uuid=vol_uuid,
                                                                   type=str(self.blt_details['type']),
                                                                   command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Deleting BLT {} with uuid {} on DUT".
                                 format(i + 1, vol_uuid))

            # Deleting the controller
            for index, host_name in enumerate(self.host_info):
                command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid[index],
                                                                           command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Deleting storage controller {}".
                                 format(self.ctrlr_uuid[index]))

            # Pre-conditioning the volume (one time task)


# Reusing the same volume uuid
            command_result = self.storage_controller.create_volume(type=self.blt_details["type"],
                                                                   capacity=self.blt_details["capacity"],
                                                                   block_size=self.blt_details["block_size"],
                                                                   name="thin_block" + str(counter + 1),
                                                                   group_id=counter + 1,
                                                                   uuid=self.thin_uuid_list[0],
                                                                   command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"],
                                 "Create BLT {} with uuid {} on DUT".format(counter + 1,
                                                                            cur_uuid))

            fun_test.shared_variables["thin_uuid"] = self.thin_uuid_list
            counter += 1

            # Create one TCP controller per host\
            self.ctrlr_uuid = []
            for i in range(self.blt_count):
                self.nvme_block_device = []

                self.nqn_list = []
                cur_uuid = utils.generate_uuid()
                self.ctrlr_uuid.append(cur_uuid)
                nqn = "nqn" + str(i + 1)
                self.nqn_list.append(nqn)
                command_result = self.storage_controller.create_controller(ctrlr_id=i,
                                                                           ctrlr_uuid=cur_uuid,
                                                                           ctrlr_type="BLOCK",
                                                                           transport=self.transport_type.upper(),
                                                                           remote_ip=self.host_ips[i],
                                                                           subsys_nqn=nqn,
                                                                           host_nqn=self.host_ips[i],
                                                                           port=self.transport_port,
                                                                           command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "Creating TCP controller for {} with uuid {} on DUT".
                                     format(self.host_ips[i], cur_uuid))

            fun_test.shared_variables["ctrlr_uuid"] = self.ctrlr_uuid
            fun_test.shared_variables["nqn_list"] = self.nqn_list

            # Attach controller to BLTs
            print("crtrl uuid", self.ctrlr_uuid)
            for i in range(self.blt_count):
                ctrlr_index = i % self.num_hosts
                ns_id = (i / self.num_hosts) + 1
                print ("ctrlr_index is ", ctrlr_index)
                print("self.ctrlr_uuid[ctrlr_index]", self.ctrlr_uuid[ctrlr_index])
                print("self.thin_uuid_list[i]", self.thin_uuid_list[i])
                ns_id = (i / self.num_hosts) + 1
                print ("i value looping in attaching volume ", i)
                command_result = self.storage_controller.attach_volume_to_controller(
                    ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], vol_uuid=self.thin_uuid_list[i],
                    ns_id=ns_id, command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "Attaching BLT volume {} to the host {} via controller "
                                     "{}".format(self.thin_uuid_list[i],
                                                 self.host_ips[ctrlr_index],
                                                 self.ctrlr_uuid[ctrlr_index]))


    def run(self):
        print "in run"

    def cleanup(self):
        if "blt" in fun_test.shared_variables and fun_test.shared_variables["blt"]["setup_created"]:
            self.fs = self.fs_objs[0]
            self.storage_controller = fun_test.shared_variables["sc_obj"][0]
            try:
                self.blt_details = fun_test.shared_variables["blt_details"]
                self.thin_uuid_list = fun_test.shared_variables["thin_uuid"]
                self.ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]
                self.nqn_list = fun_test.shared_variables["nqn_list"]

                # Setting the syslog level back to 6

                for index, host_name in enumerate(self.host_info):
                    host_handle = self.host_info[host_name]["handle"]
                    nqn = self.nqn_list[index]

                    nvme_disconnect_cmd = "nvme disconnect -n {}".format(nqn)
                    nvme_disconnect_output = host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                    nvme_disconnect_exit_status = host_handle.exit_status()
                    fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                                  message="Host {} - NVME Disconnect Status".format(host_name))

                # Detaching and deleting the volume
                print("thin_uuid_list", self.thin_uuid_list)
                for i, vol_uuid in enumerate(self.thin_uuid_list):
                    num_hosts = len(self.host_info)
                    ctrlr_index = i % num_hosts
                    ns_id = (i / num_hosts) + 1
                    command_result = self.storage_controller.detach_volume_from_controller(
                        ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], ns_id=ns_id, command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Detaching BLT volume {} from controller {}".
                                         format(vol_uuid, self.ctrlr_uuid[ctrlr_index]))

                    command_result = self.storage_controller.delete_volume(uuid=vol_uuid,
                                                                           type=str(self.blt_details['type']),
                                                                           command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Deleting BLT {} with uuid {} on DUT".
                                         format(i + 1, vol_uuid))

                # Deleting the controller
                for index, host_name in enumerate(self.host_info):
                    command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid[index],
                                                                               command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Deleting storage controller {}".
                                         format(self.ctrlr_uuid[index]))
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("Clean-up of volumes failed.")

            for i in self.thin_uuid_list:
                command_result = self.storage_controller.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN/" + i)
            fun_test.test_assert_expected(expected=False, actual=command_result["Status"],
                                          message="Checking if the volume id is deleted after deleting the volume")


class MultiHostVolumePerformanceTestcase10(FunTestCase):
    # Create shared volume
    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__

        self.testbed_config = fun_test.shared_variables["testbed_config"]
        self.syslog = fun_test.shared_variables["syslog"]

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
            fun_test.test_assert(benchmark_parsing,
                                 "Parsing Benchmark json file for this {} testcase".format(testcase))

        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

        # Setting the list of numjobs and IO depth combo
        # TODO: Check if block size is not required

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 12
        if not hasattr(self, "blt_count"):
            self.blt_count = 12

        fun_test.test_assert(benchmark_parsing,
                             "Parsing Benchmark json file for this {} testcase".format(testcase))

        # End of benchmarking json file parsing

        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
        fun_test.shared_variables["blt_count"] = self.blt_count

        # New changes
        fun_test.shared_variables["transport_type"] = self.transport_type

        self.nvme_block_device = self.nvme_device + "0n" + str(self.blt_details["ns_id"])
        self.volume_name = self.nvme_block_device.replace("/dev/", "")

        self.fs = fun_test.shared_variables["fs_objs"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1 = fun_test.shared_variables["f1_objs"][0][0]
        self.storage_controller = fun_test.shared_variables["sc_obj"][0]
        self.f1_ips = fun_test.shared_variables["f1_ips"][0]
        self.host_info = fun_test.shared_variables["host_info"]
        self.host_handles = fun_test.shared_variables["host_handles"]
        self.csi_perf_enabled = fun_test.shared_variables["csi_perf_enabled"]
        self.csi_cache_miss_enabled = fun_test.shared_variables["csi_cache_miss_enabled"]

        if self.csi_perf_enabled or self.csi_cache_miss_enabled:
            self.perf_listener_host_name = fun_test.shared_variables["perf_listener_host_name"]
            self.perf_listener_ip = fun_test.shared_variables["perf_listener_ip"]
        self.host_ips = fun_test.shared_variables["host_ips"]
        self.num_hosts = len(self.host_ips)
        self.end_host = self.host_handles[self.host_ips[0]]
        # self.numa_cpus = fun_test.shared_variables["numa_cpus"][self.host_ips[0]]
        # self.total_numa_cpus = fun_test.shared_variables["total_numa_cpus"][self.host_ips[0]]
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_loopback_ip"] = self.f1_ips
        self.remote_ip = self.host_ips[0]
        fun_test.shared_variables["remote_ip"] = self.remote_ip
        self.num_duts = fun_test.shared_variables["num_duts"]

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}

        if "csi_perf_iodepth" in job_inputs:
            self.csi_perf_iodepth = job_inputs["csi_perf_iodepth"]
            self.full_run_iodepth = self.csi_perf_iodepth
        if not isinstance(self.csi_perf_iodepth, list):
            self.csi_perf_iodepth = [self.csi_perf_iodepth]
            self.full_run_iodepth = self.csi_perf_iodepth

        if ("blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]):
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False
            fun_test.shared_variables["blt"]["warmup_done"] = False
            fun_test.shared_variables["blt_details"] = self.blt_details

            # Enabling counters
            """
            command_result = self.storage_controller.json_execute(verb="enable_counters",
                                                                  command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling Internal Stats/Counters")
            """

            # Configuring controller IP
            command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg on DUT instance")

            # If the number of hosts is less than the number of volumes then expand the host_ips list to equal to
            # number of volumes by repeating the existing entries for the required number of times
            self.final_host_ips = self.host_ips[:]
            if len(self.host_ips) < self.blt_count:
                for i in range(len(self.host_ips), self.blt_count):
                    self.final_host_ips.append(self.host_ips[i % len(self.host_ips)])

            for host_name in self.host_info:
                self.host_info[host_name]["num_volumes"] = self.final_host_ips.count(
                    self.host_info[host_name]["ip"])

            # Finding the usable capacity of the drives which will be used as the BLT volume capacity, in case
            # the capacity is not overridden while starting the script
            min_drive_capacity = find_min_drive_capacity(self.storage_controller, self.command_timeout)
            if min_drive_capacity:
                self.blt_details["max_capacity"] = min_drive_capacity
                # Reducing the volume capacity by drive margin as a workaround for the bug SWOS-6862
                self.blt_details["max_capacity"] -= self.drive_margin
            else:
                fun_test.critical(
                    "Unable to find the drive with minimum capacity...So going to use the BLT capacity"
                    "given in the script config file or capacity passed at the runtime...")

            if "capacity" in job_inputs:
                fun_test.critical("Original Volume size {} is overriden by the size {} given while running the "
                                  "script".format(self.blt_details["capacity"], job_inputs["capacity"]))
                self.blt_details["capacity"] = job_inputs["capacity"]

            # Create BLT's
            self.thin_uuid_list = []
            # Here is 'counter' is the counter for the volumes created
            counter = 0
            cur_uuid = utils.generate_uuid()
            self.thin_uuid_list.append(cur_uuid)
            command_result = self.storage_controller.create_volume(type=self.blt_details["type"],
                                                                   capacity=self.blt_details["capacity"],
                                                                   block_size=self.blt_details["block_size"],
                                                                   name="thin_block" + str(counter + 1),
                                                                   group_id=counter + 1,
                                                                   uuid=cur_uuid,
                                                                   command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"],
                                 "Create BLT {} with uuid {} on DUT".format(counter + 1,
                                                                            cur_uuid))

            fun_test.shared_variables["thin_uuid"] = self.thin_uuid_list
            counter += 1

            # Create one TCP controller per host\
            self.ctrlr_uuid = []
            for i in range(self.num_hosts):
                self.nvme_block_device = []
                self.nqn_list = []
                cur_uuid = utils.generate_uuid()
                self.ctrlr_uuid.append(cur_uuid)
                nqn = "nqn" + str(i + 1)
                self.nqn_list.append(nqn)
                command_result = self.storage_controller.create_controller(ctrlr_id=i,
                                                                           ctrlr_uuid=cur_uuid,
                                                                           ctrlr_type="BLOCK",
                                                                           transport=self.transport_type.upper(),
                                                                           remote_ip=self.host_ips[i],
                                                                           subsys_nqn=nqn,
                                                                           host_nqn=self.host_ips[i],
                                                                           port=self.transport_port,
                                                                           command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "Creating TCP controller for {} with uuid {} on DUT".
                                     format(self.host_ips[i], cur_uuid))

            fun_test.shared_variables["ctrlr_uuid"] = self.ctrlr_uuid
            fun_test.shared_variables["nqn_list"] = self.nqn_list

            # Attach the same volume to all the hosts
            for i in range(self.num_hosts):
                ctrlr_index = i % self.num_hosts
                print("num of hosts",self.num_hosts)
                print("value of i is",i)
                print("value of ctrlr index is ",ctrlr_index)
                ns_id = (i / self.num_hosts) + 1
                command_result = self.storage_controller.attach_volume_to_controller(
                    ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], vol_uuid=self.thin_uuid_list[0],
                    ns_id=ns_id, command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "Attaching BLT volume {} to the host {} via controller "
                                     "{}".format(self.thin_uuid_list[i],
                                                 self.host_ips[ctrlr_index],
                                                 self.ctrlr_uuid[ctrlr_index]))

            # Setting the fcp scheduler bandwidth
            if hasattr(self, "config_fcp_scheduler"):
                command_result = self.storage_controller.set_fcp_scheduler(
                    fcp_sch_config=self.config_fcp_scheduler,
                    command_timeout=self.command_timeout)
                if not command_result["status"]:
                    fun_test.critical(
                        "Unable to set the fcp scheduler bandwidth...So proceeding the test with the "
                        "default setting")
                elif self.config_fcp_scheduler != command_result["data"]:
                    fun_test.critical(
                        "Unable to fetch the applied FCP scheduler config... So proceeding the test "
                        "with the default setting")
                else:
                    fun_test.log(
                        "Successfully set the fcp scheduler bandwidth to: {}".format(command_result["data"]))

            for index, host_name in enumerate(self.host_info):
                host_handle = self.host_info[host_name]["handle"]
                host_ip = self.host_info[host_name]["ip"]
                nqn = self.nqn_list[index]
                host_handle.sudo_command("iptables -F && ip6tables -F && dmesg -c > /dev/null")
                host_handle.sudo_command("/etc/init.d/irqbalance stop")
                irq_bal_stat = host_handle.command("/etc/init.d/irqbalance status")
                if "dead" in irq_bal_stat:
                    fun_test.log("IRQ balance stopped on {}".format(i))
                else:
                    fun_test.log("IRQ balance not stopped on {}".format(i))
                    install_status = host_handle.install_package("tuned")
                    fun_test.test_assert(install_status, "tuned installed successfully")

                    host_handle.sudo_command("tuned-adm profile network-throughput && tuned-adm active")

                command_result = host_handle.command("lsmod | grep -w nvme")
                if "nvme" in command_result:
                    fun_test.log("nvme driver is loaded")
                else:
                    fun_test.log("Loading nvme")
                    host_handle.modprobe("nvme")
                    host_handle.modprobe("nvme_core")
                command_result = host_handle.lsmod("nvme_tcp")
                if "nvme_tcp" in command_result:
                    fun_test.log("nvme_tcp driver is loaded")
                else:
                    fun_test.log("Loading nvme_tcp")
                    host_handle.modprobe("nvme_tcp")
                    host_handle.modprobe("nvme_fabrics")

                host_handle.start_bg_process(command="sudo tcpdump -i enp216s0 -w nvme_connect_auto.pcap")
                if hasattr(self, "nvme_io_queues") and self.nvme_io_queues != 0:
                    command_result = host_handle.sudo_command(
                        "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}".format(
                            unicode.lower(self.transport_type),
                            self.test_network["f1_loopback_ip"],
                            self.transport_port, nqn,
                            self.nvme_io_queues, host_ip))
                    fun_test.log(command_result)
                else:
                    command_result = host_handle.sudo_command(
                        "nvme connect -t {} -a {} -s {} -n {} -q {}".format(unicode.lower(self.transport_type),
                                                                            self.test_network["f1_loopback_ip"],
                                                                            self.transport_port, nqn, host_ip))
                    fun_test.log(command_result)
                fun_test.sleep("Wait for couple of seconds for the volume to be accessible to the host", 5)
                host_handle.sudo_command("for i in `pgrep tcpdump`;do kill -9 $i;done")
                host_handle.sudo_command("dmesg")

                lsblk_output = host_handle.lsblk("-b")
                fun_test.simple_assert(lsblk_output, "Listing available volumes")
                fun_test.log("lsblk Output: \n{}".format(lsblk_output))

                # Checking that the above created BLT volume is visible to the end host
                self.host_info[host_name]["nvme_block_device_list"] = []
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

                self.host_info[host_name]["nvme_block_device_list"].sort()
                self.host_info[host_name]["fio_filename"] = ":".join(
                    self.host_info[host_name]["nvme_block_device_list"])
                fun_test.shared_variables["host_info"] = self.host_info
                fun_test.log("Hosts info: {}".format(self.host_info))



            def run(self):
                print "in run"

            def cleanup(self):
                if "blt" in fun_test.shared_variables and fun_test.shared_variables["blt"]["setup_created"]:
                    self.fs = self.fs_objs[0]
                    self.storage_controller = fun_test.shared_variables["sc_obj"][0]
                    try:
                        self.blt_details = fun_test.shared_variables["blt_details"]
                        self.thin_uuid_list = fun_test.shared_variables["thin_uuid"]
                        self.ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]
                        self.nqn_list = fun_test.shared_variables["nqn_list"]

                        # Setting the syslog level back to 6

                        for index, host_name in enumerate(self.host_info):
                            host_handle = self.host_info[host_name]["handle"]
                            nqn = self.nqn_list[index]

                            nvme_disconnect_cmd = "nvme disconnect -n {}".format(nqn)
                            nvme_disconnect_output = host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                            nvme_disconnect_exit_status = host_handle.exit_status()
                            fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                                          message="Host {} - NVME Disconnect Status".format(host_name))

                        # Detaching and deleting the volume
                        print("thin_uuid_list", self.thin_uuid_list)
                        for i, vol_uuid in enumerate(self.thin_uuid_list):
                            num_hosts = len(self.host_info)
                            ctrlr_index = i % num_hosts
                            ns_id = (i / num_hosts) + 1
                            command_result = self.storage_controller.detach_volume_from_controller(
                                ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], ns_id=ns_id,
                                command_duration=self.command_timeout)
                            fun_test.test_assert(command_result["status"], "Detaching BLT volume {} from controller {}".
                                                 format(vol_uuid, self.ctrlr_uuid[ctrlr_index]))

                            command_result = self.storage_controller.delete_volume(uuid=vol_uuid,
                                                                                   type=str(self.blt_details['type']),
                                                                                   command_duration=self.command_timeout)
                            fun_test.test_assert(command_result["status"], "Deleting BLT {} with uuid {} on DUT".
                                                 format(i + 1, vol_uuid))

                        # Deleting the controller
                        for index, host_name in enumerate(self.host_info):
                            command_result = self.storage_controller.delete_controller(
                                ctrlr_uuid=self.ctrlr_uuid[index],
                                command_duration=self.command_timeout)
                            fun_test.log(command_result)
                            fun_test.test_assert(command_result["status"], "Deleting storage controller {}".
                                                 format(self.ctrlr_uuid[index]))
                    except Exception as ex:
                        fun_test.critical(str(ex))
                        fun_test.log("Clean-up of volumes failed.")

                    for i in self.thin_uuid_list:
                        command_result = self.storage_controller.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN/" + i)
                        fun_test.log("DPCSH command result")
                        fun_test.log(command_result)
                    fun_test.test_assert_expected(expected=False, actual=command_result["Status"],
                                                  message="Checking if the volume id is deleted after deleting the volume")


class MultiHostVolumePerformanceTestcase11(FunTestCase):
    # Attach non existent volume to a controller
    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__

        self.testbed_config = fun_test.shared_variables["testbed_config"]
        self.syslog = fun_test.shared_variables["syslog"]

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
            fun_test.test_assert(benchmark_parsing,
                                 "Parsing Benchmark json file for this {} testcase".format(testcase))

        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

        # Setting the list of numjobs and IO depth combo
        # TODO: Check if block size is not required

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 12
        if not hasattr(self, "blt_count"):
            self.blt_count = 12

        fun_test.test_assert(benchmark_parsing,
                             "Parsing Benchmark json file for this {} testcase".format(testcase))

        # End of benchmarking json file parsing

        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
        fun_test.shared_variables["blt_count"] = self.blt_count

        # New changes
        fun_test.shared_variables["transport_type"] = self.transport_type

        self.nvme_block_device = self.nvme_device + "0n" + str(self.blt_details["ns_id"])
        self.volume_name = self.nvme_block_device.replace("/dev/", "")

        self.fs = fun_test.shared_variables["fs_objs"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1 = fun_test.shared_variables["f1_objs"][0][0]
        self.storage_controller = fun_test.shared_variables["sc_obj"][0]
        self.f1_ips = fun_test.shared_variables["f1_ips"][0]
        self.host_info = fun_test.shared_variables["host_info"]
        self.host_handles = fun_test.shared_variables["host_handles"]
        self.csi_perf_enabled = fun_test.shared_variables["csi_perf_enabled"]
        self.csi_cache_miss_enabled = fun_test.shared_variables["csi_cache_miss_enabled"]

        if self.csi_perf_enabled or self.csi_cache_miss_enabled:
            self.perf_listener_host_name = fun_test.shared_variables["perf_listener_host_name"]
            self.perf_listener_ip = fun_test.shared_variables["perf_listener_ip"]
        self.host_ips = fun_test.shared_variables["host_ips"]
        self.num_hosts = len(self.host_ips)
        self.end_host = self.host_handles[self.host_ips[0]]
        # self.numa_cpus = fun_test.shared_variables["numa_cpus"][self.host_ips[0]]
        # self.total_numa_cpus = fun_test.shared_variables["total_numa_cpus"][self.host_ips[0]]
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_loopback_ip"] = self.f1_ips
        self.remote_ip = self.host_ips[0]
        fun_test.shared_variables["remote_ip"] = self.remote_ip
        self.num_duts = fun_test.shared_variables["num_duts"]

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}

        if "csi_perf_iodepth" in job_inputs:
            self.csi_perf_iodepth = job_inputs["csi_perf_iodepth"]
            self.full_run_iodepth = self.csi_perf_iodepth
        if not isinstance(self.csi_perf_iodepth, list):
            self.csi_perf_iodepth = [self.csi_perf_iodepth]
            self.full_run_iodepth = self.csi_perf_iodepth

        if ("blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]):
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False
            fun_test.shared_variables["blt"]["warmup_done"] = False
            fun_test.shared_variables["blt_details"] = self.blt_details

            # Enabling counters
            """
            command_result = self.storage_controller.json_execute(verb="enable_counters",
                                                                  command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling Internal Stats/Counters")
            """

            # Configuring controller IP
            command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg on DUT instance")

            # If the number of hosts is less than the number of volumes then expand the host_ips list to equal to
            # number of volumes by repeating the existing entries for the required number of times
            self.final_host_ips = self.host_ips[:]
            if len(self.host_ips) < self.blt_count:
                for i in range(len(self.host_ips), self.blt_count):
                    self.final_host_ips.append(self.host_ips[i % len(self.host_ips)])

            for host_name in self.host_info:
                self.host_info[host_name]["num_volumes"] = self.final_host_ips.count(
                    self.host_info[host_name]["ip"])

            # Finding the usable capacity of the drives which will be used as the BLT volume capacity, in case
            # the capacity is not overridden while starting the script
            min_drive_capacity = find_min_drive_capacity(self.storage_controller, self.command_timeout)
            if min_drive_capacity:
                self.blt_details["max_capacity"] = min_drive_capacity
                # Reducing the volume capacity by drive margin as a workaround for the bug SWOS-6862
                self.blt_details["max_capacity"] -= self.drive_margin
            else:
                fun_test.critical(
                    "Unable to find the drive with minimum capacity...So going to use the BLT capacity"
                    "given in the script config file or capacity passed at the runtime...")

            if "capacity" in job_inputs:
                fun_test.critical("Original Volume size {} is overriden by the size {} given while running the "
                                  "script".format(self.blt_details["capacity"], job_inputs["capacity"]))
                self.blt_details["capacity"] = job_inputs["capacity"]

            # Create BLT's
            self.thin_uuid_list = []
            # a random uuid is generated but the volume is not created .Controller is created and attached to the non existing volume
            counter = 0
            cur_uuid = utils.generate_uuid()
            self.thin_uuid_list.append(cur_uuid)
            fun_test.shared_variables["thin_uuid"] = self.thin_uuid_list
            counter += 1

            # Create one TCP controller per host\
            self.ctrlr_uuid = []
            for i in range(self.num_hosts):
                self.nvme_block_device = []

                self.nqn_list = []
                cur_uuid = utils.generate_uuid()
                self.ctrlr_uuid.append(cur_uuid)
                nqn = "nqn" + str(i + 1)
                self.nqn_list.append(nqn)
                command_result = self.storage_controller.create_controller(ctrlr_id=i,
                                                                           ctrlr_uuid=cur_uuid,
                                                                           ctrlr_type="BLOCK",
                                                                           transport=self.transport_type.upper(),
                                                                           remote_ip=self.host_ips[i],
                                                                           subsys_nqn=nqn,
                                                                           host_nqn=self.host_ips[i],
                                                                           port=self.transport_port,
                                                                           command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "Creating TCP controller for {} with uuid {} on DUT".
                                     format(self.host_ips[i], cur_uuid))

            fun_test.shared_variables["ctrlr_uuid"] = self.ctrlr_uuid
            fun_test.shared_variables["nqn_list"] = self.nqn_list

            # Attach a single controller to all the hosts
            for i in range(self.num_hosts):
                ctrlr_index = i % self.num_hosts
                ns_id = (i / self.num_hosts) + 1
                print("num of hosts", self.num_hosts)
                print("value of i is", i)
                print("value of ctrlr index is ", ctrlr_index)
                command_result = self.storage_controller.attach_volume_to_controller(
                    ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], vol_uuid=self.thin_uuid_list[0],
                    ns_id=ns_id, command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "Attaching BLT volume {} to the host {} via controller "
                                     "{}".format(self.thin_uuid_list[i],
                                                 self.host_ips[ctrlr_index],
                                                 self.ctrlr_uuid[ctrlr_index]))



    def run(self):
                print "in run"

    def cleanup(self):
        if "blt" in fun_test.shared_variables and fun_test.shared_variables["blt"]["setup_created"]:
            self.fs = self.fs_objs[0]
            self.storage_controller = fun_test.shared_variables["sc_obj"][0]
            try:
                self.blt_details = fun_test.shared_variables["blt_details"]
                self.thin_uuid_list = fun_test.shared_variables["thin_uuid"]
                self.ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]
                self.nqn_list = fun_test.shared_variables["nqn_list"]

                # Setting the syslog level back to 6

                for index, host_name in enumerate(self.host_info):
                    host_handle = self.host_info[host_name]["handle"]
                    nqn = self.nqn_list[index]

                    nvme_disconnect_cmd = "nvme disconnect -n {}".format(nqn)
                    nvme_disconnect_output = host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                    nvme_disconnect_exit_status = host_handle.exit_status()
                    fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                                  message="Host {} - NVME Disconnect Status".format(host_name))

                # Detaching and deleting the volume
                print("thin_uuid_list", self.thin_uuid_list)
                for i, vol_uuid in enumerate(self.thin_uuid_list):
                    num_hosts = len(self.host_info)
                    ctrlr_index = i % num_hosts
                    ns_id = (i / num_hosts) + 1
                    print("num of hosts", self.num_hosts)
                    print("value of i is", i)
                    print("value of ctrlr index is ", ctrlr_index)
                    command_result = self.storage_controller.detach_volume_from_controller(
                        ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], ns_id=ns_id, command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Detaching BLT volume {} from controller {}".
                                         format(vol_uuid, self.ctrlr_uuid[ctrlr_index]))

                    command_result = self.storage_controller.delete_volume(uuid=vol_uuid,
                                                                           type=str(self.blt_details['type']),
                                                                           command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Deleting BLT {} with uuid {} on DUT".
                                         format(i + 1, vol_uuid))

                # Deleting the controller
                for index, host_name in enumerate(self.host_info):
                    command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid[index],
                                                                               command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Deleting storage controller {}".
                                         format(self.ctrlr_uuid[index]))
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("Clean-up of volumes failed.")

            for i in self.thin_uuid_list:
                command_result = self.storage_controller.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN/" + i)
            fun_test.test_assert_expected(expected=False, actual=command_result["Status"],
                                          message="Checking if the volume id is deleted after deleting the volume")



class MultiHostVolumePerformanceTestcase12(FunTestCase):
    # Attach same namespace twice
    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__

        self.testbed_config = fun_test.shared_variables["testbed_config"]
        self.syslog = fun_test.shared_variables["syslog"]

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
            fun_test.test_assert(benchmark_parsing,
                                 "Parsing Benchmark json file for this {} testcase".format(testcase))

        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

        # Setting the list of numjobs and IO depth combo
        # TODO: Check if block size is not required

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 12
        if not hasattr(self, "blt_count"):
            self.blt_count = 12

        fun_test.test_assert(benchmark_parsing,
                             "Parsing Benchmark json file for this {} testcase".format(testcase))

        # End of benchmarking json file parsing

        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
        fun_test.shared_variables["blt_count"] = self.blt_count

        # New changes
        fun_test.shared_variables["transport_type"] = self.transport_type

        self.nvme_block_device = self.nvme_device + "0n" + str(self.blt_details["ns_id"])
        self.volume_name = self.nvme_block_device.replace("/dev/", "")

        self.fs = fun_test.shared_variables["fs_objs"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1 = fun_test.shared_variables["f1_objs"][0][0]
        self.storage_controller = fun_test.shared_variables["sc_obj"][0]
        self.f1_ips = fun_test.shared_variables["f1_ips"][0]
        self.host_info = fun_test.shared_variables["host_info"]
        self.host_handles = fun_test.shared_variables["host_handles"]
        self.csi_perf_enabled = fun_test.shared_variables["csi_perf_enabled"]
        self.csi_cache_miss_enabled = fun_test.shared_variables["csi_cache_miss_enabled"]

        if self.csi_perf_enabled or self.csi_cache_miss_enabled:
            self.perf_listener_host_name = fun_test.shared_variables["perf_listener_host_name"]
            self.perf_listener_ip = fun_test.shared_variables["perf_listener_ip"]
        self.host_ips = fun_test.shared_variables["host_ips"]
        self.num_hosts = len(self.host_ips)
        self.end_host = self.host_handles[self.host_ips[0]]
        # self.numa_cpus = fun_test.shared_variables["numa_cpus"][self.host_ips[0]]
        # self.total_numa_cpus = fun_test.shared_variables["total_numa_cpus"][self.host_ips[0]]
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_loopback_ip"] = self.f1_ips
        self.remote_ip = self.host_ips[0]
        fun_test.shared_variables["remote_ip"] = self.remote_ip
        self.num_duts = fun_test.shared_variables["num_duts"]

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}

        if "csi_perf_iodepth" in job_inputs:
            self.csi_perf_iodepth = job_inputs["csi_perf_iodepth"]
            self.full_run_iodepth = self.csi_perf_iodepth
        if not isinstance(self.csi_perf_iodepth, list):
            self.csi_perf_iodepth = [self.csi_perf_iodepth]
            self.full_run_iodepth = self.csi_perf_iodepth

        if ("blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]):
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False
            fun_test.shared_variables["blt"]["warmup_done"] = False
            fun_test.shared_variables["blt_details"] = self.blt_details

            # Enabling counters
            """
            command_result = self.storage_controller.json_execute(verb="enable_counters",
                                                                  command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling Internal Stats/Counters")
            """

            # Configuring controller IP
            command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg on DUT instance")

            # If the number of hosts is less than the number of volumes then expand the host_ips list to equal to
            # number of volumes by repeating the existing entries for the required number of times
            self.final_host_ips = self.host_ips[:]
            if len(self.host_ips) < self.blt_count:
                for i in range(len(self.host_ips), self.blt_count):
                    self.final_host_ips.append(self.host_ips[i % len(self.host_ips)])

            for host_name in self.host_info:
                self.host_info[host_name]["num_volumes"] = self.final_host_ips.count(
                    self.host_info[host_name]["ip"])

            # Finding the usable capacity of the drives which will be used as the BLT volume capacity, in case
            # the capacity is not overridden while starting the script
            min_drive_capacity = find_min_drive_capacity(self.storage_controller, self.command_timeout)
            if min_drive_capacity:
                self.blt_details["max_capacity"] = min_drive_capacity
                # Reducing the volume capacity by drive margin as a workaround for the bug SWOS-6862
                self.blt_details["max_capacity"] -= self.drive_margin
            else:
                fun_test.critical(
                    "Unable to find the drive with minimum capacity...So going to use the BLT capacity"
                    "given in the script config file or capacity passed at the runtime...")

            if "capacity" in job_inputs:
                fun_test.critical("Original Volume size {} is overriden by the size {} given while running the "
                                  "script".format(self.blt_details["capacity"], job_inputs["capacity"]))
                self.blt_details["capacity"] = job_inputs["capacity"]

            # Create BLT's
            self.thin_uuid_list = []
            # a random uuid is generated but the volume is not created .Controller is created and attached to the non existing volume
            for i in range(self.blt_count):
                cur_uuid = utils.generate_uuid()
                self.thin_uuid_list.append(cur_uuid)
                command_result = self.storage_controller.create_volume(type=self.blt_details["type"],
                                                                           capacity=self.blt_details["capacity"],
                                                                           block_size=self.blt_details["block_size"],
                                                                           name="thin_block" + str(i + 1), group_id=i+1,
                                                                           uuid=cur_uuid,
                                                                           command_duration=self.command_timeout)
                fun_test.log(command_result)
                self.thin_uuid_list.append(cur_uuid)
                fun_test.add_checkpoint("Create BLT {} with uuid {} and capacity{} on DUT".format(i + 1, cur_uuid, self.blt_details["capacity"]),expected="True",actual=command_result["status"])

            # Create one TCP controller per host\
            self.ctrlr_uuid = []
            for i in range(self.num_hosts):
                self.nvme_block_device = []

                self.nqn_list = []
                cur_uuid = utils.generate_uuid()
                self.ctrlr_uuid.append(cur_uuid)
                nqn = "nqn" + str(i + 1)
                self.nqn_list.append(nqn)
                command_result = self.storage_controller.create_controller(ctrlr_id=i,
                                                                           ctrlr_uuid=cur_uuid,
                                                                           ctrlr_type="BLOCK",
                                                                           transport=self.transport_type.upper(),
                                                                           remote_ip=self.host_ips[i],
                                                                           subsys_nqn=nqn,
                                                                           host_nqn=self.host_ips[i],
                                                                           port=self.transport_port,
                                                                           command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "Creating TCP controller for {} with uuid {} on DUT".
                                     format(self.host_ips[i], cur_uuid))

            fun_test.shared_variables["ctrlr_uuid"] = self.ctrlr_uuid
            fun_test.shared_variables["nqn_list"] = self.nqn_list

            # Creating controller
            for i in range(self.num_hosts):
                ctrlr_index = i % self.num_hosts
                ns_id = (i / self.num_hosts) + 1
                print("num of hosts", self.num_hosts)
                print("value of i is", i)
                print("value of ctrlr index is ", ctrlr_index)
                command_result = self.storage_controller.attach_volume_to_controller(
                    ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], vol_uuid=self.thin_uuid_list[0],
                    ns_id=ns_id, command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "Attaching BLT volume {} to the host {} via controller "
                                     "{}".format(self.thin_uuid_list[i],
                                                 self.host_ips[ctrlr_index],
                                                 self.ctrlr_uuid[ctrlr_index]))
            # Attach volume to a controller
            for i in range(0, self.blt_count, 1):
                vol_uuid = fun_test.shared_variables["thin_uuid"][i]
                command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                                     vol_uuid=vol_uuid,
                                                                                     ns_id=i + 1,
                                                                                     command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Attaching BLT volume {} to controller {}".
                                     format(vol_uuid, self.ctrlr_uuid))

            # Try to attach second time
            for i in range(0, self.blt_count, 1):
                vol_uuid = fun_test.shared_variables["thin_uuid"][i]
                command_result = self.storage_controller.attach_volume_to_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                                     vol_uuid=vol_uuid,
                                                                                     ns_id=i + 1,
                                                                                     command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Attaching BLT volume {} to controller {}".
                                     format(vol_uuid, self.ctrlr_uuid))
    def run(self):
                print "in run"

    def cleanup(self):
        if "blt" in fun_test.shared_variables and fun_test.shared_variables["blt"]["setup_created"]:
            self.fs = self.fs_objs[0]
            self.storage_controller = fun_test.shared_variables["sc_obj"][0]
            try:
                self.blt_details = fun_test.shared_variables["blt_details"]
                self.thin_uuid_list = fun_test.shared_variables["thin_uuid"]
                self.ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]
                self.nqn_list = fun_test.shared_variables["nqn_list"]

                # Setting the syslog level back to 6

                for index, host_name in enumerate(self.host_info):
                    host_handle = self.host_info[host_name]["handle"]
                    nqn = self.nqn_list[index]

                    nvme_disconnect_cmd = "nvme disconnect -n {}".format(nqn)
                    nvme_disconnect_output = host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                    nvme_disconnect_exit_status = host_handle.exit_status()
                    fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                                  message="Host {} - NVME Disconnect Status".format(host_name))

                # Detaching and deleting the volume
                print("thin_uuid_list", self.thin_uuid_list)
                for i, vol_uuid in enumerate(self.thin_uuid_list):
                    num_hosts = len(self.host_info)
                    ctrlr_index = i % num_hosts
                    ns_id = (i / num_hosts) + 1
                    print("num of hosts", self.num_hosts)
                    print("value of i is", i)
                    print("value of ctrlr index is ", ctrlr_index)
                    command_result = self.storage_controller.detach_volume_from_controller(
                        ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], ns_id=ns_id, command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Detaching BLT volume {} from controller {}".
                                         format(vol_uuid, self.ctrlr_uuid[ctrlr_index]))

                    command_result = self.storage_controller.delete_volume(uuid=vol_uuid,
                                                                           type=str(self.blt_details['type']),
                                                                           command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Deleting BLT {} with uuid {} on DUT".
                                         format(i + 1, vol_uuid))

                # Deleting the controller
                for index, host_name in enumerate(self.host_info):
                    command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid[index],
                                                                               command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Deleting storage controller {}".
                                         format(self.ctrlr_uuid[index]))
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("Clean-up of volumes failed.")

            for i in self.thin_uuid_list:
                command_result = self.storage_controller.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN/" + i)
            fun_test.test_assert_expected(expected=False, actual=command_result["Status"],
                                          message="Checking if the volume id is deleted after deleting the volume")


class MultiHostVolumePerformanceTestcase13(FunTestCase):
    # Detach volume multiple times
    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__

        self.testbed_config = fun_test.shared_variables["testbed_config"]
        self.syslog = fun_test.shared_variables["syslog"]

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
            fun_test.test_assert(benchmark_parsing,
                                 "Parsing Benchmark json file for this {} testcase".format(testcase))

        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

        # Setting the list of numjobs and IO depth combo
        # TODO: Check if block size is not required

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 12
        if not hasattr(self, "blt_count"):
            self.blt_count = 12

        fun_test.test_assert(benchmark_parsing,
                             "Parsing Benchmark json file for this {} testcase".format(testcase))

        # End of benchmarking json file parsing

        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
        fun_test.shared_variables["blt_count"] = self.blt_count

        # New changes
        fun_test.shared_variables["transport_type"] = self.transport_type

        self.nvme_block_device = self.nvme_device + "0n" + str(self.blt_details["ns_id"])
        self.volume_name = self.nvme_block_device.replace("/dev/", "")

        self.fs = fun_test.shared_variables["fs_objs"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1 = fun_test.shared_variables["f1_objs"][0][0]
        self.storage_controller = fun_test.shared_variables["sc_obj"][0]
        self.f1_ips = fun_test.shared_variables["f1_ips"][0]
        self.host_info = fun_test.shared_variables["host_info"]
        self.host_handles = fun_test.shared_variables["host_handles"]
        self.csi_perf_enabled = fun_test.shared_variables["csi_perf_enabled"]
        self.csi_cache_miss_enabled = fun_test.shared_variables["csi_cache_miss_enabled"]

        if self.csi_perf_enabled or self.csi_cache_miss_enabled:
            self.perf_listener_host_name = fun_test.shared_variables["perf_listener_host_name"]
            self.perf_listener_ip = fun_test.shared_variables["perf_listener_ip"]
        self.host_ips = fun_test.shared_variables["host_ips"]
        self.num_hosts = len(self.host_ips)
        self.end_host = self.host_handles[self.host_ips[0]]
        # self.numa_cpus = fun_test.shared_variables["numa_cpus"][self.host_ips[0]]
        # self.total_numa_cpus = fun_test.shared_variables["total_numa_cpus"][self.host_ips[0]]
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_loopback_ip"] = self.f1_ips
        self.remote_ip = self.host_ips[0]
        fun_test.shared_variables["remote_ip"] = self.remote_ip
        self.num_duts = fun_test.shared_variables["num_duts"]

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}

        if "csi_perf_iodepth" in job_inputs:
            self.csi_perf_iodepth = job_inputs["csi_perf_iodepth"]
            self.full_run_iodepth = self.csi_perf_iodepth
        if not isinstance(self.csi_perf_iodepth, list):
            self.csi_perf_iodepth = [self.csi_perf_iodepth]
            self.full_run_iodepth = self.csi_perf_iodepth

        if ("blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]):
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False
            fun_test.shared_variables["blt"]["warmup_done"] = False
            fun_test.shared_variables["blt_details"] = self.blt_details

            # Enabling counters
            """
            command_result = self.storage_controller.json_execute(verb="enable_counters",
                                                                  command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling Internal Stats/Counters")
            """

            # Configuring controller IP
            command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg on DUT instance")

            # If the number of hosts is less than the number of volumes then expand the host_ips list to equal to
            # number of volumes by repeating the existing entries for the required number of times
            self.final_host_ips = self.host_ips[:]
            if len(self.host_ips) < self.blt_count:
                for i in range(len(self.host_ips), self.blt_count):
                    self.final_host_ips.append(self.host_ips[i % len(self.host_ips)])

            for host_name in self.host_info:
                self.host_info[host_name]["num_volumes"] = self.final_host_ips.count(
                    self.host_info[host_name]["ip"])

            # Finding the usable capacity of the drives which will be used as the BLT volume capacity, in case
            # the capacity is not overridden while starting the script
            min_drive_capacity = find_min_drive_capacity(self.storage_controller, self.command_timeout)
            if min_drive_capacity:
                self.blt_details["max_capacity"] = min_drive_capacity
                # Reducing the volume capacity by drive margin as a workaround for the bug SWOS-6862
                self.blt_details["max_capacity"] -= self.drive_margin
            else:
                fun_test.critical(
                    "Unable to find the drive with minimum capacity...So going to use the BLT capacity"
                    "given in the script config file or capacity passed at the runtime...")

            if "capacity" in job_inputs:
                fun_test.critical("Original Volume size {} is overriden by the size {} given while running the "
                                  "script".format(self.blt_details["capacity"], job_inputs["capacity"]))
                self.blt_details["capacity"] = job_inputs["capacity"]

            # Create BLT's
            self.thin_uuid_list = []
            # a random uuid is generated but the volume is not created .Controller is created and attached to the non existing volume
            for i in range(self.blt_count):
                cur_uuid = utils.generate_uuid()
                self.thin_uuid_list.append(cur_uuid)
                command_result = self.storage_controller.create_volume(type=self.blt_details["type"],
                                                                           capacity=self.blt_details["capacity"],
                                                                           block_size=self.blt_details["block_size"],
                                                                           name="thin_block" + str(i + 1), group_id=i+1,
                                                                           uuid=cur_uuid,
                                                                           command_duration=self.command_timeout)
                fun_test.log(command_result)
                self.thin_uuid_list.append(cur_uuid)
                fun_test.test_assert(command_result["status"],
                                     "Create BLT {} with uuid {} and capacity {} on DUT".format(i + 1, cur_uuid,self.blt_details["capacity"]))

            # Create one TCP controller per host\
            self.ctrlr_uuid = []
            for i in range(self.num_hosts):
                self.nvme_block_device = []

                self.nqn_list = []
                cur_uuid = utils.generate_uuid()
                self.ctrlr_uuid.append(cur_uuid)
                nqn = "nqn" + str(i + 1)
                self.nqn_list.append(nqn)
                command_result = self.storage_controller.create_controller(ctrlr_id=i,
                                                                           ctrlr_uuid=cur_uuid,
                                                                           ctrlr_type="BLOCK",
                                                                           transport=self.transport_type.upper(),
                                                                           remote_ip=self.host_ips[i],
                                                                           subsys_nqn=nqn,
                                                                           host_nqn=self.host_ips[i],
                                                                           port=self.transport_port,
                                                                           command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "Creating TCP controller for {} with uuid {} on DUT".
                                     format(self.host_ips[i], cur_uuid))

            fun_test.shared_variables["ctrlr_uuid"] = self.ctrlr_uuid
            fun_test.shared_variables["nqn_list"] = self.nqn_list

            # Attach volume to a controller
            for i in range(self.num_hosts):
                ctrlr_index = i % self.num_hosts
                ns_id = (i / self.num_hosts) + 1
                print("num of hosts", self.num_hosts)
                print("value of i is", i)
                print("value of ctrlr index is ", ctrlr_index)
                command_result = self.storage_controller.attach_volume_to_controller(
                    ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], vol_uuid=self.thin_uuid_list[0],
                    ns_id=ns_id, command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "Attaching BLT volume {} to the host {} via controller "
                                     "{}".format(self.thin_uuid_list[i],
                                                 self.host_ips[ctrlr_index],

                                                 self.ctrlr_uuid[ctrlr_index]))

            # Executing NVMe disconnect from all the hosts
            for index, host_name in enumerate(self.host_info):
                host_handle = self.host_info[host_name]["handle"]
                nqn = self.nqn_list[index]

                nvme_disconnect_cmd = "nvme disconnect -n {}".format(nqn)
                nvme_disconnect_output = host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                nvme_disconnect_exit_status = host_handle.exit_status()
                fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                              message="Host {} - NVME Disconnect Status".format(host_name))

            #Detach the volume created twice
            count=1
            while(count!=2):
                count+=1
                print("thin_uuid_list", self.thin_uuid_list)
                for i, vol_uuid in enumerate(self.thin_uuid_list):
                    num_hosts = len(self.host_info)
                    ctrlr_index = i % num_hosts
                    ns_id = (i / num_hosts) + 1
                    command_result = self.storage_controller.detach_volume_from_controller(
                        ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], ns_id=ns_id, command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Detaching BLT volume {} from controller {}".
                                     format(vol_uuid, self.ctrlr_uuid[ctrlr_index]))

            #Try deleting non existing volume
            count=1
            while(count!=2):
                count+=1
                print("thin_uuid_list", self.thin_uuid_list)
                for i, vol_uuid in enumerate(self.thin_uuid_list):
                    num_hosts = len(self.host_info)
                    ctrlr_index = i % num_hosts
                    command_result = self.storage_controller.delete_volume(uuid=vol_uuid,
                                                                           type=str(self.blt_details['type']),
                                                                           command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Deleting BLT {} with uuid {} on DUT".
                                         format(i + 1, vol_uuid))



    def run(self):
                print "in run"

    def cleanup(self):
        if "blt" in fun_test.shared_variables and fun_test.shared_variables["blt"]["setup_created"]:
            self.fs = self.fs_objs[0]
            self.storage_controller = fun_test.shared_variables["sc_obj"][0]
            try:
                self.blt_details = fun_test.shared_variables["blt_details"]
                self.thin_uuid_list = fun_test.shared_variables["thin_uuid"]
                self.ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]
                self.nqn_list = fun_test.shared_variables["nqn_list"]

                # Setting the syslog level back to 6

                for index, host_name in enumerate(self.host_info):
                    host_handle = self.host_info[host_name]["handle"]
                    nqn = self.nqn_list[index]

                    nvme_disconnect_cmd = "nvme disconnect -n {}".format(nqn)
                    nvme_disconnect_output = host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                    nvme_disconnect_exit_status = host_handle.exit_status()
                    fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                                  message="Host {} - NVME Disconnect Status".format(host_name))

                # Detaching and deleting the volume
                print("thin_uuid_list", self.thin_uuid_list)
                for i, vol_uuid in enumerate(self.thin_uuid_list):
                    num_hosts = len(self.host_info)
                    ctrlr_index = i % num_hosts
                    ns_id = (i / num_hosts) + 1
                    print("num of hosts", self.num_hosts)
                    print("value of i is", i)
                    print("value of ctrlr index is ", ctrlr_index)
                    command_result = self.storage_controller.detach_volume_from_controller(
                        ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], ns_id=ns_id, command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Detaching BLT volume {} from controller {}".
                                         format(vol_uuid, self.ctrlr_uuid[ctrlr_index]))

                    command_result = self.storage_controller.delete_volume(uuid=vol_uuid,
                                                                           type=str(self.blt_details['type']),
                                                                           command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Deleting BLT {} with uuid {} on DUT".
                                         format(i + 1, vol_uuid))

                # Deleting the controller
                for index, host_name in enumerate(self.host_info):
                    command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid[index],
                                                                               command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Deleting storage controller {}".
                                         format(self.ctrlr_uuid[index]))
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("Clean-up of volumes failed.")

            for i in self.thin_uuid_list:
                command_result = self.storage_controller.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN/" + i)
            fun_test.test_assert_expected(expected=False, actual=command_result["Status"],
                                          message="Checking if the volume id is deleted after deleting the volume")



class MultiHostVolumePerformanceTestcase14(FunTestCase):
    # Delete namespace without detach
    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__

        self.testbed_config = fun_test.shared_variables["testbed_config"]
        self.syslog = fun_test.shared_variables["syslog"]

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
            fun_test.test_assert(benchmark_parsing,
                                 "Parsing Benchmark json file for this {} testcase".format(testcase))

        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

        # Setting the list of numjobs and IO depth combo
        # TODO: Check if block size is not required

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 12
        if not hasattr(self, "blt_count"):
            self.blt_count = 12

        fun_test.test_assert(benchmark_parsing,
                             "Parsing Benchmark json file for this {} testcase".format(testcase))

        # End of benchmarking json file parsing

        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
        fun_test.shared_variables["blt_count"] = self.blt_count

        # New changes
        fun_test.shared_variables["transport_type"] = self.transport_type

        self.nvme_block_device = self.nvme_device + "0n" + str(self.blt_details["ns_id"])
        self.volume_name = self.nvme_block_device.replace("/dev/", "")

        self.fs = fun_test.shared_variables["fs_objs"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1 = fun_test.shared_variables["f1_objs"][0][0]
        self.storage_controller = fun_test.shared_variables["sc_obj"][0]
        self.f1_ips = fun_test.shared_variables["f1_ips"][0]
        self.host_info = fun_test.shared_variables["host_info"]
        self.host_handles = fun_test.shared_variables["host_handles"]
        self.csi_perf_enabled = fun_test.shared_variables["csi_perf_enabled"]
        self.csi_cache_miss_enabled = fun_test.shared_variables["csi_cache_miss_enabled"]

        if self.csi_perf_enabled or self.csi_cache_miss_enabled:
            self.perf_listener_host_name = fun_test.shared_variables["perf_listener_host_name"]
            self.perf_listener_ip = fun_test.shared_variables["perf_listener_ip"]
        self.host_ips = fun_test.shared_variables["host_ips"]
        self.num_hosts = len(self.host_ips)
        self.end_host = self.host_handles[self.host_ips[0]]
        # self.numa_cpus = fun_test.shared_variables["numa_cpus"][self.host_ips[0]]
        # self.total_numa_cpus = fun_test.shared_variables["total_numa_cpus"][self.host_ips[0]]
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_loopback_ip"] = self.f1_ips
        self.remote_ip = self.host_ips[0]
        fun_test.shared_variables["remote_ip"] = self.remote_ip
        self.num_duts = fun_test.shared_variables["num_duts"]

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}

        if "csi_perf_iodepth" in job_inputs:
            self.csi_perf_iodepth = job_inputs["csi_perf_iodepth"]
            self.full_run_iodepth = self.csi_perf_iodepth
        if not isinstance(self.csi_perf_iodepth, list):
            self.csi_perf_iodepth = [self.csi_perf_iodepth]
            self.full_run_iodepth = self.csi_perf_iodepth

        if ("blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]):
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False
            fun_test.shared_variables["blt"]["warmup_done"] = False
            fun_test.shared_variables["blt_details"] = self.blt_details

            # Enabling counters
            """
            command_result = self.storage_controller.json_execute(verb="enable_counters",
                                                                  command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling Internal Stats/Counters")
            """

            # Configuring controller IP
            command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg on DUT instance")

            # If the number of hosts is less than the number of volumes then expand the host_ips list to equal to
            # number of volumes by repeating the existing entries for the required number of times
            self.final_host_ips = self.host_ips[:]
            if len(self.host_ips) < self.blt_count:
                for i in range(len(self.host_ips), self.blt_count):
                    self.final_host_ips.append(self.host_ips[i % len(self.host_ips)])

            for host_name in self.host_info:
                self.host_info[host_name]["num_volumes"] = self.final_host_ips.count(
                    self.host_info[host_name]["ip"])

            # Finding the usable capacity of the drives which will be used as the BLT volume capacity, in case
            # the capacity is not overridden while starting the script
            min_drive_capacity = find_min_drive_capacity(self.storage_controller, self.command_timeout)
            if min_drive_capacity:
                self.blt_details["max_capacity"] = min_drive_capacity
                # Reducing the volume capacity by drive margin as a workaround for the bug SWOS-6862
                self.blt_details["max_capacity"] -= self.drive_margin
            else:
                fun_test.critical(
                    "Unable to find the drive with minimum capacity...So going to use the BLT capacity"
                    "given in the script config file or capacity passed at the runtime...")

            if "capacity" in job_inputs:
                fun_test.critical("Original Volume size {} is overriden by the size {} given while running the "
                                  "script".format(self.blt_details["capacity"], job_inputs["capacity"]))
                self.blt_details["capacity"] = job_inputs["capacity"]

            # Create BLT's
            self.thin_uuid_list = []
            # a random uuid is generated but the volume is not created .Controller is created and attached to the non existing volume
            for i in range(self.blt_count):
                cur_uuid = utils.generate_uuid()
                self.thin_uuid_list.append(cur_uuid)
                command_result = self.storage_controller.create_volume(type=self.blt_details["type"],
                                                                           capacity=self.blt_details["capacity"],
                                                                           block_size=self.blt_details["block_size"],
                                                                           name="thin_block" + str(i + 1), group_id=i+1,
                                                                           uuid=cur_uuid,
                                                                           command_duration=self.command_timeout)
                fun_test.log(command_result)
                self.thin_uuid_list.append(cur_uuid)
                fun_test.test_assert(command_result["status"],
                                     "Create BLT {} with uuid {} and capacity {} on DUT".format(i + 1, cur_uuid,self.blt_details["capacity"]))


            # Create one TCP controller per host\
            self.ctrlr_uuid = []
            for i in range(self.num_hosts):
                self.nvme_block_device = []

                self.nqn_list = []
                cur_uuid = utils.generate_uuid()
                self.ctrlr_uuid.append(cur_uuid)
                nqn = "nqn" + str(i + 1)
                self.nqn_list.append(nqn)
                command_result = self.storage_controller.create_controller(ctrlr_id=i,
                                                                           ctrlr_uuid=cur_uuid,
                                                                           ctrlr_type="BLOCK",
                                                                           transport=self.transport_type.upper(),
                                                                           remote_ip=self.host_ips[i],
                                                                           subsys_nqn=nqn,
                                                                           host_nqn=self.host_ips[i],
                                                                           port=self.transport_port,
                                                                           command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "Creating TCP controller for {} with uuid {} on DUT".
                                     format(self.host_ips[i], cur_uuid))

            fun_test.shared_variables["ctrlr_uuid"] = self.ctrlr_uuid
            fun_test.shared_variables["nqn_list"] = self.nqn_list

            # Attach volume to a controller
            for i in range(self.num_hosts):
                ctrlr_index = i % self.num_hosts
                ns_id = (i / self.num_hosts) + 1
                print("num of hosts", self.num_hosts)
                print("value of i is", i)
                print("value of ctrlr index is ", ctrlr_index)
                command_result = self.storage_controller.attach_volume_to_controller(
                    ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], vol_uuid=self.thin_uuid_list[0],
                    ns_id=ns_id, command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "Attaching BLT volume {} to the host {} via controller "
                                     "{}".format(self.thin_uuid_list[i],
                                                 self.host_ips[ctrlr_index],

                                                 self.ctrlr_uuid[ctrlr_index]))


            # Executing NVMe disconnect from all the hosts
            for index, host_name in enumerate(self.host_info):
                host_handle = self.host_info[host_name]["handle"]
                nqn = self.nqn_list[index]

                nvme_disconnect_cmd = "nvme disconnect -n {}".format(nqn)
                nvme_disconnect_output = host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                nvme_disconnect_exit_status = host_handle.exit_status()
                fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                              message="Host {} - NVME Disconnect Status".format(host_name))

            # Delete volume without detach
            print("thin_uuid_list", self.thin_uuid_list)
            for i, vol_uuid in enumerate(self.thin_uuid_list):
                num_hosts = len(self.host_info)
                ctrlr_index = i % num_hosts
                ns_id = (i / num_hosts) + 1
                command_result = self.storage_controller.delete_volume(uuid=vol_uuid,
                                                                       type=str(self.blt_details['type']),
                                                                       command_duration=self.command_timeout)
                fun_test.test_assert(command_result["status"], "Deleting BLT {} with uuid {} on DUT".
                                     format(i + 1, vol_uuid))





    def run(self):
                print "in run"

    def cleanup(self):
        if "blt" in fun_test.shared_variables and fun_test.shared_variables["blt"]["setup_created"]:
            self.fs = self.fs_objs[0]
            self.storage_controller = fun_test.shared_variables["sc_obj"][0]
            try:
                self.blt_details = fun_test.shared_variables["blt_details"]
                self.thin_uuid_list = fun_test.shared_variables["thin_uuid"]
                self.ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]
                self.nqn_list = fun_test.shared_variables["nqn_list"]

                # Setting the syslog level back to 6

                for index, host_name in enumerate(self.host_info):
                    host_handle = self.host_info[host_name]["handle"]
                    nqn = self.nqn_list[index]

                    nvme_disconnect_cmd = "nvme disconnect -n {}".format(nqn)
                    nvme_disconnect_output = host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                    nvme_disconnect_exit_status = host_handle.exit_status()
                    fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                                  message="Host {} - NVME Disconnect Status".format(host_name))

                # Detaching and deleting the volume
                print("thin_uuid_list", self.thin_uuid_list)
                for i, vol_uuid in enumerate(self.thin_uuid_list):
                    num_hosts = len(self.host_info)
                    ctrlr_index = i % num_hosts
                    ns_id = (i / num_hosts) + 1
                    print("num of hosts", self.num_hosts)
                    print("value of i is", i)
                    print("value of ctrlr index is ", ctrlr_index)
                    command_result = self.storage_controller.detach_volume_from_controller(
                        ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], ns_id=ns_id, command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Detaching BLT volume {} from controller {}".
                                         format(vol_uuid, self.ctrlr_uuid[ctrlr_index]))

                    command_result = self.storage_controller.delete_volume(uuid=vol_uuid,
                                                                           type=str(self.blt_details['type']),
                                                                           command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Deleting BLT {} with uuid {} on DUT".
                                         format(i + 1, vol_uuid))

                # Deleting the controller
                for index, host_name in enumerate(self.host_info):
                    command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid[index],
                                                                               command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Deleting storage controller {}".
                                         format(self.ctrlr_uuid[index]))
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("Clean-up of volumes failed.")

            for i in self.thin_uuid_list:
                command_result = self.storage_controller.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN/" + i)
            fun_test.test_assert_expected(expected=False, actual=command_result["Status"],
                                          message="Checking if the volume id is deleted after deleting the volume")


class MultiHostVolumePerformanceTestcase15(FunTestCase):
    # Delete namespace without detach
    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__

        self.testbed_config = fun_test.shared_variables["testbed_config"]
        self.syslog = fun_test.shared_variables["syslog"]

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
            fun_test.test_assert(benchmark_parsing,
                                 "Parsing Benchmark json file for this {} testcase".format(testcase))

        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

        # Setting the list of numjobs and IO depth combo
        # TODO: Check if block size is not required

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 12
        if not hasattr(self, "blt_count"):
            self.blt_count = 12

        fun_test.test_assert(benchmark_parsing,
                             "Parsing Benchmark json file for this {} testcase".format(testcase))

        # End of benchmarking json file parsing

        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
        fun_test.shared_variables["blt_count"] = self.blt_count

        # New changes
        fun_test.shared_variables["transport_type"] = self.transport_type

        self.nvme_block_device = self.nvme_device + "0n" + str(self.blt_details["ns_id"])
        self.volume_name = self.nvme_block_device.replace("/dev/", "")

        self.fs = fun_test.shared_variables["fs_objs"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1 = fun_test.shared_variables["f1_objs"][0][0]
        self.storage_controller = fun_test.shared_variables["sc_obj"][0]
        self.f1_ips = fun_test.shared_variables["f1_ips"][0]
        self.host_info = fun_test.shared_variables["host_info"]
        self.host_handles = fun_test.shared_variables["host_handles"]
        self.csi_perf_enabled = fun_test.shared_variables["csi_perf_enabled"]
        self.csi_cache_miss_enabled = fun_test.shared_variables["csi_cache_miss_enabled"]

        if self.csi_perf_enabled or self.csi_cache_miss_enabled:
            self.perf_listener_host_name = fun_test.shared_variables["perf_listener_host_name"]
            self.perf_listener_ip = fun_test.shared_variables["perf_listener_ip"]
        self.host_ips = fun_test.shared_variables["host_ips"]
        self.num_hosts = len(self.host_ips)
        self.end_host = self.host_handles[self.host_ips[0]]
        # self.numa_cpus = fun_test.shared_variables["numa_cpus"][self.host_ips[0]]
        # self.total_numa_cpus = fun_test.shared_variables["total_numa_cpus"][self.host_ips[0]]
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_loopback_ip"] = self.f1_ips
        self.remote_ip = self.host_ips[0]
        fun_test.shared_variables["remote_ip"] = self.remote_ip
        self.num_duts = fun_test.shared_variables["num_duts"]

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}

        if "csi_perf_iodepth" in job_inputs:
            self.csi_perf_iodepth = job_inputs["csi_perf_iodepth"]
            self.full_run_iodepth = self.csi_perf_iodepth
        if not isinstance(self.csi_perf_iodepth, list):
            self.csi_perf_iodepth = [self.csi_perf_iodepth]
            self.full_run_iodepth = self.csi_perf_iodepth

        if ("blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]):
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False
            fun_test.shared_variables["blt"]["warmup_done"] = False
            fun_test.shared_variables["blt_details"] = self.blt_details

            # Enabling counters
            """
            command_result = self.storage_controller.json_execute(verb="enable_counters",
                                                                  command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling Internal Stats/Counters")
            """

            # Configuring controller IP
            command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg on DUT instance")

            # If the number of hosts is less than the number of volumes then expand the host_ips list to equal to
            # number of volumes by repeating the existing entries for the required number of times
            self.final_host_ips = self.host_ips[:]
            if len(self.host_ips) < self.blt_count:
                for i in range(len(self.host_ips), self.blt_count):
                    self.final_host_ips.append(self.host_ips[i % len(self.host_ips)])

            for host_name in self.host_info:
                self.host_info[host_name]["num_volumes"] = self.final_host_ips.count(
                    self.host_info[host_name]["ip"])

            # Finding the usable capacity of the drives which will be used as the BLT volume capacity, in case
            # the capacity is not overridden while starting the script
            min_drive_capacity = find_min_drive_capacity(self.storage_controller, self.command_timeout)
            if min_drive_capacity:
                self.blt_details["max_capacity"] = min_drive_capacity
                # Reducing the volume capacity by drive margin as a workaround for the bug SWOS-6862
                self.blt_details["max_capacity"] -= self.drive_margin
            else:
                fun_test.critical(
                    "Unable to find the drive with minimum capacity...So going to use the BLT capacity"
                    "given in the script config file or capacity passed at the runtime...")

            if "capacity" in job_inputs:
                fun_test.critical("Original Volume size {} is overriden by the size {} given while running the "
                                  "script".format(self.blt_details["capacity"], job_inputs["capacity"]))
                self.blt_details["capacity"] = job_inputs["capacity"]

            # Create BLT's
            self.thin_uuid_list = []
            # a random uuid is generated but the volume is not created .Controller is created and attached to the non existing volume
            for i in range(self.blt_count):
                cur_uuid = utils.generate_uuid()
                self.thin_uuid_list.append(cur_uuid)
                command_result = self.storage_controller.create_volume(type=self.blt_details["type"],
                                                                           capacity=self.blt_details["capacity"],
                                                                           block_size=self.blt_details["block_size"],
                                                                           name="thin_block" + str(i + 1), group_id=i+1,
                                                                           uuid=cur_uuid,
                                                                           command_duration=self.command_timeout)
                fun_test.log(command_result)
                self.thin_uuid_list.append(cur_uuid)
                fun_test.test_assert(command_result["status"],
                                     "Create BLT {} with uuid {} and capacity {} on DUT".format(i + 1, cur_uuid,self.blt_details["capacity"]))


            # Create one TCP controller per host\
            self.ctrlr_uuid=[]
            for i in range(self.num_hosts):
                self.nvme_block_device = []

                self.nqn_list = []
                cur_uuid = utils.generate_uuid()
                self.ctrlr_uuid.append(cur_uuid)
                nqn = "nqn" + str(i + 1)
                self.nqn_list.append(nqn)
                command_result = self.storage_controller.create_controller(ctrlr_id=i,
                                                                           ctrlr_uuid=cur_uuid,
                                                                           ctrlr_type="BLOCK",
                                                                           transport=self.transport_type.upper(),
                                                                           remote_ip=self.host_ips[i],
                                                                           subsys_nqn=nqn,
                                                                           host_nqn=self.host_ips[i],
                                                                           port=self.transport_port,
                                                                           command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "Creating TCP controller for {} with uuid {} on DUT".
                                     format(self.host_ips[i], cur_uuid))

            fun_test.shared_variables["ctrlr_uuid"] = self.ctrlr_uuid
            fun_test.shared_variables["nqn_list"] = self.nqn_list

            # Attach volume to a controller
            for i in range(self.num_hosts):
                ctrlr_index = i % self.num_hosts
                ns_id = (i / self.num_hosts) + 1
                print("num of hosts", self.num_hosts)
                print("value of i is", i)
                print("value of ctrlr index is ", ctrlr_index)
                command_result = self.storage_controller.attach_volume_to_controller(
                    ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], vol_uuid=self.thin_uuid_list[0],
                    ns_id=ns_id, command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "Attaching BLT volume {} to the host {} via controller "
                                     "{}".format(self.thin_uuid_list[i],
                                                 self.host_ips[ctrlr_index],

                                                 self.ctrlr_uuid[ctrlr_index]))

            #Detach the volume created twice
            count=1
            while(count!=2):
                count+=1
                print("thin_uuid_list", self.thin_uuid_list)
                for i, vol_uuid in enumerate(self.thin_uuid_list):
                    num_hosts = len(self.host_info)
                    ctrlr_index = i % num_hosts
                    ns_id = (i / num_hosts) + 1
                    command_result = self.storage_controller.detach_volume_from_controller(
                        ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], ns_id=ns_id, command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Detaching BLT volume {} from controller {}".
                                     format(vol_uuid, self.ctrlr_uuid[ctrlr_index]))




    def run(self):
                print "in run"

    def cleanup(self):
        if "blt" in fun_test.shared_variables and fun_test.shared_variables["blt"]["setup_created"]:
            self.fs = self.fs_objs[0]
            self.storage_controller = fun_test.shared_variables["sc_obj"][0]
            try:
                self.blt_details = fun_test.shared_variables["blt_details"]
                self.thin_uuid_list = fun_test.shared_variables["thin_uuid"]
                self.ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]
                self.nqn_list = fun_test.shared_variables["nqn_list"]

                # Setting the syslog level back to 6

                for index, host_name in enumerate(self.host_info):
                    host_handle = self.host_info[host_name]["handle"]
                    nqn = self.nqn_list[index]

                    nvme_disconnect_cmd = "nvme disconnect -n {}".format(nqn)
                    nvme_disconnect_output = host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                    nvme_disconnect_exit_status = host_handle.exit_status()
                    fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                                  message="Host {} - NVME Disconnect Status".format(host_name))

                # Detaching and deleting the volume
                print("thin_uuid_list", self.thin_uuid_list)
                for i, vol_uuid in enumerate(self.thin_uuid_list):
                    num_hosts = len(self.host_info)
                    ctrlr_index = i % num_hosts
                    ns_id = (i / num_hosts) + 1
                    print("num of hosts", self.num_hosts)
                    print("value of i is", i)
                    print("value of ctrlr index is ", ctrlr_index)
                    command_result = self.storage_controller.detach_volume_from_controller(
                        ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], ns_id=ns_id, command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Detaching BLT volume {} from controller {}".
                                         format(vol_uuid, self.ctrlr_uuid[ctrlr_index]))

                    command_result = self.storage_controller.delete_volume(uuid=vol_uuid,
                                                                           type=str(self.blt_details['type']),
                                                                           command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Deleting BLT {} with uuid {} on DUT".
                                         format(i + 1, vol_uuid))

                # Deleting the controller
                for index, host_name in enumerate(self.host_info):
                    command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid[index],
                                                                               command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Deleting storage controller {}".
                                         format(self.ctrlr_uuid[index]))
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("Clean-up of volumes failed.")

            for i in self.thin_uuid_list:
                command_result = self.storage_controller.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN/" + i)
            fun_test.test_assert_expected(expected=False, actual=command_result["Status"],
                                          message="Checking if the volume id is deleted after deleting the volume")



class MultiHostVolumePerformanceTestcase16(FunTestCase):
    # Configure a BLT volume with compression enabled
    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__

        self.testbed_config = fun_test.shared_variables["testbed_config"]
        self.syslog = fun_test.shared_variables["syslog"]

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
            fun_test.test_assert(benchmark_parsing,
                                 "Parsing Benchmark json file for this {} testcase".format(testcase))

        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

        # Setting the list of numjobs and IO depth combo
        # TODO: Check if block size is not required

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 12
        if not hasattr(self, "blt_count"):
            self.blt_count = 12

        fun_test.test_assert(benchmark_parsing,
                             "Parsing Benchmark json file for this {} testcase".format(testcase))

        # End of benchmarking json file parsing

        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
        fun_test.shared_variables["blt_count"] = self.blt_count

        # New changes
        fun_test.shared_variables["transport_type"] = self.transport_type

        self.nvme_block_device = self.nvme_device + "0n" + str(self.blt_details["ns_id"])
        self.volume_name = self.nvme_block_device.replace("/dev/", "")

        self.fs = fun_test.shared_variables["fs_objs"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1 = fun_test.shared_variables["f1_objs"][0][0]
        self.storage_controller = fun_test.shared_variables["sc_obj"][0]
        self.f1_ips = fun_test.shared_variables["f1_ips"][0]
        self.host_info = fun_test.shared_variables["host_info"]
        self.host_handles = fun_test.shared_variables["host_handles"]
        self.csi_perf_enabled = fun_test.shared_variables["csi_perf_enabled"]
        self.csi_cache_miss_enabled = fun_test.shared_variables["csi_cache_miss_enabled"]

        if self.csi_perf_enabled or self.csi_cache_miss_enabled:
            self.perf_listener_host_name = fun_test.shared_variables["perf_listener_host_name"]
            self.perf_listener_ip = fun_test.shared_variables["perf_listener_ip"]
        self.host_ips = fun_test.shared_variables["host_ips"]
        self.num_hosts = len(self.host_ips)
        self.end_host = self.host_handles[self.host_ips[0]]
        # self.numa_cpus = fun_test.shared_variables["numa_cpus"][self.host_ips[0]]
        # self.total_numa_cpus = fun_test.shared_variables["total_numa_cpus"][self.host_ips[0]]
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_loopback_ip"] = self.f1_ips
        self.remote_ip = self.host_ips[0]
        fun_test.shared_variables["remote_ip"] = self.remote_ip
        self.num_duts = fun_test.shared_variables["num_duts"]

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}

        if "csi_perf_iodepth" in job_inputs:
            self.csi_perf_iodepth = job_inputs["csi_perf_iodepth"]
            self.full_run_iodepth = self.csi_perf_iodepth
        if not isinstance(self.csi_perf_iodepth, list):
            self.csi_perf_iodepth = [self.csi_perf_iodepth]
            self.full_run_iodepth = self.csi_perf_iodepth

        if ("blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]):
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False
            fun_test.shared_variables["blt"]["warmup_done"] = False
            fun_test.shared_variables["blt_details"] = self.blt_details

            # Enabling counters
            """
            command_result = self.storage_controller.json_execute(verb="enable_counters",
                                                                  command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling Internal Stats/Counters")
            """

            # Configuring controller IP
            command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg on DUT instance")

            # If the number of hosts is less than the number of volumes then expand the host_ips list to equal to
            # number of volumes by repeating the existing entries for the required number of times
            self.final_host_ips = self.host_ips[:]
            if len(self.host_ips) < self.blt_count:
                for i in range(len(self.host_ips), self.blt_count):
                    self.final_host_ips.append(self.host_ips[i % len(self.host_ips)])

            for host_name in self.host_info:
                self.host_info[host_name]["num_volumes"] = self.final_host_ips.count(
                    self.host_info[host_name]["ip"])

            # Finding the usable capacity of the drives which will be used as the BLT volume capacity, in case
            # the capacity is not overridden while starting the script
            min_drive_capacity = find_min_drive_capacity(self.storage_controller, self.command_timeout)
            if min_drive_capacity:
                self.blt_details["max_capacity"] = min_drive_capacity
                # Reducing the volume capacity by drive margin as a workaround for the bug SWOS-6862
                self.blt_details["max_capacity"] -= self.drive_margin
            else:
                fun_test.critical(
                    "Unable to find the drive with minimum capacity...So going to use the BLT capacity"
                    "given in the script config file or capacity passed at the runtime...")

            if "capacity" in job_inputs:
                fun_test.critical("Original Volume size {} is overriden by the size {} given while running the "
                                  "script".format(self.blt_details["capacity"], job_inputs["capacity"]))
                self.blt_details["capacity"] = job_inputs["capacity"]

            # Create BLT's
            self.thin_uuid_list = []
            # a random uuid is generated but the volume is not created .Controller is created and attached to the non existing volume
            for i in range(self.blt_count):
                cur_uuid = utils.generate_uuid()
                self.thin_uuid_list.append(cur_uuid)
                command_result = self.storage_controller.create_volume(type=self.blt_details["type"],
                                                                           capacity=self.blt_details["capacity"],
                                                                           block_size=self.blt_details["block_size"],
                                                                           name="thin_block" + str(i + 1), group_id=i+1,
                                                                           uuid=cur_uuid,encrypt=True,
                                                                           command_duration=self.command_timeout)
                fun_test.log(command_result)
                self.thin_uuid_list.append(cur_uuid)
                fun_test.test_assert(command_result["status"],
                                     "Create BLT {} with uuid {} and capacity {} on DUT".format(i + 1, cur_uuid,self.blt_details["capacity"]))


            # Create one TCP controller per host\
            self.ctrlr_uuid = []
            for i in range(self.num_hosts):
                self.nvme_block_device = []

                self.nqn_list = []
                cur_uuid = utils.generate_uuid()
                self.ctrlr_uuid.append(cur_uuid)
                nqn = "nqn" + str(i + 1)
                self.nqn_list.append(nqn)
                command_result = self.storage_controller.create_controller(ctrlr_id=i,
                                                                           ctrlr_uuid=cur_uuid,
                                                                           ctrlr_type="BLOCK",
                                                                           transport=self.transport_type.upper(),
                                                                           remote_ip=self.host_ips[i],
                                                                           subsys_nqn=nqn,
                                                                           host_nqn=self.host_ips[i],
                                                                           port=self.transport_port,
                                                                           command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "Creating TCP controller for {} with uuid {} on DUT".
                                     format(self.host_ips[i], cur_uuid))

            fun_test.shared_variables["ctrlr_uuid"] = self.ctrlr_uuid
            fun_test.shared_variables["nqn_list"] = self.nqn_list

            # Attach volume to a controller
            for i in range(self.num_hosts):
                ctrlr_index = i % self.num_hosts
                ns_id = (i / self.num_hosts) + 1
                print("num of hosts", self.num_hosts)
                print("value of i is", i)
                print("value of ctrlr index is ", ctrlr_index)
                command_result = self.storage_controller.attach_volume_to_controller(
                    ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], vol_uuid=self.thin_uuid_list[0],
                    ns_id=ns_id, command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "Attaching BLT volume {} to the host {} via controller "
                                     "{}".format(self.thin_uuid_list[i],
                                                 self.host_ips[ctrlr_index],

                                                 self.ctrlr_uuid[ctrlr_index]))


    def cleanup(self):
        if "blt" in fun_test.shared_variables and fun_test.shared_variables["blt"]["setup_created"]:
            self.fs = self.fs_objs[0]
            self.storage_controller = fun_test.shared_variables["sc_obj"][0]
            try:
                self.blt_details = fun_test.shared_variables["blt_details"]
                self.thin_uuid_list = fun_test.shared_variables["thin_uuid"]
                self.ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]
                self.nqn_list = fun_test.shared_variables["nqn_list"]

                # Setting the syslog level back to 6

                for index, host_name in enumerate(self.host_info):
                    host_handle = self.host_info[host_name]["handle"]
                    nqn = self.nqn_list[index]

                    nvme_disconnect_cmd = "nvme disconnect -n {}".format(nqn)
                    nvme_disconnect_output = host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                    nvme_disconnect_exit_status = host_handle.exit_status()
                    fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                                  message="Host {} - NVME Disconnect Status".format(host_name))

                # Detaching and deleting the volume
                print("thin_uuid_list", self.thin_uuid_list)
                for i, vol_uuid in enumerate(self.thin_uuid_list):
                    num_hosts = len(self.host_info)
                    ctrlr_index = i % num_hosts
                    ns_id = (i / num_hosts) + 1
                    command_result = self.storage_controller.detach_volume_from_controller(
                        ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], ns_id=ns_id, command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Detaching BLT volume {} from controller {}".
                                         format(vol_uuid, self.ctrlr_uuid[ctrlr_index]))

                    command_result = self.storage_controller.delete_volume(uuid=vol_uuid,
                                                                           type=str(self.blt_details['type']),
                                                                           command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Deleting BLT {} with uuid {} on DUT".
                                         format(i + 1, vol_uuid))

                # Deleting the controller
                for index, host_name in enumerate(self.host_info):
                    command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid[index],
                                                                               command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Deleting storage controller {}".
                                         format(self.ctrlr_uuid[index]))
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("Clean-up of volumes failed.")

            for i in self.thin_uuid_list:
                command_result = self.storage_controller.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN/" + i)
            fun_test.test_assert_expected(expected=False, actual=command_result["Status"],
                                          message="Checking if the volume id is deleted after deleting the volume")



class MultiHostVolumePerformanceTestcase17(FunTestCase):
    # Create a volume of size equal to drive capacity and later try to expand the same


    def setup(self):

        testcase = self.__class__.__name__

        self.testbed_config = fun_test.shared_variables["testbed_config"]
        self.syslog = fun_test.shared_variables["syslog"]

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
            fun_test.test_assert(benchmark_parsing,
                                 "Parsing Benchmark json file for this {} testcase".format(testcase))

        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

        # Setting the list of numjobs and IO depth combo
        # TODO: Check if block size is not required

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 12
        if not hasattr(self, "blt_count"):
            self.blt_count = 12

        fun_test.test_assert(benchmark_parsing,
                             "Parsing Benchmark json file for this {} testcase".format(testcase))

        # End of benchmarking json file parsing

        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
        fun_test.shared_variables["blt_count"] = self.blt_count

        # New changes
        fun_test.shared_variables["transport_type"] = self.transport_type

        self.nvme_block_device = self.nvme_device + "0n" + str(self.blt_details["ns_id"])
        self.volume_name = self.nvme_block_device.replace("/dev/", "")

        self.fs = fun_test.shared_variables["fs_objs"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1 = fun_test.shared_variables["f1_objs"][0][0]
        self.storage_controller = fun_test.shared_variables["sc_obj"][0]
        self.f1_ips = fun_test.shared_variables["f1_ips"][0]
        self.host_info = fun_test.shared_variables["host_info"]
        self.host_handles = fun_test.shared_variables["host_handles"]
        self.csi_perf_enabled = fun_test.shared_variables["csi_perf_enabled"]
        self.csi_cache_miss_enabled = fun_test.shared_variables["csi_cache_miss_enabled"]

        if self.csi_perf_enabled or self.csi_cache_miss_enabled:
            self.perf_listener_host_name = fun_test.shared_variables["perf_listener_host_name"]
            self.perf_listener_ip = fun_test.shared_variables["perf_listener_ip"]
        self.host_ips = fun_test.shared_variables["host_ips"]
        self.num_hosts = len(self.host_ips)
        self.end_host = self.host_handles[self.host_ips[0]]
        # self.numa_cpus = fun_test.shared_variables["numa_cpus"][self.host_ips[0]]
        # self.total_numa_cpus = fun_test.shared_variables["total_numa_cpus"][self.host_ips[0]]
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_loopback_ip"] = self.f1_ips
        self.remote_ip = self.host_ips[0]
        fun_test.shared_variables["remote_ip"] = self.remote_ip
        self.num_duts = fun_test.shared_variables["num_duts"]

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}

        if "csi_perf_iodepth" in job_inputs:
            self.csi_perf_iodepth = job_inputs["csi_perf_iodepth"]
            self.full_run_iodepth = self.csi_perf_iodepth
        if not isinstance(self.csi_perf_iodepth, list):
            self.csi_perf_iodepth = [self.csi_perf_iodepth]
            self.full_run_iodepth = self.csi_perf_iodepth

        if ("blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]):
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False
            fun_test.shared_variables["blt"]["warmup_done"] = False
            fun_test.shared_variables["blt_details"] = self.blt_details

            # Enabling counters
            """
            command_result = self.storage_controller.json_execute(verb="enable_counters",
                                                                  command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling Internal Stats/Counters")
            """

            # Configuring controller IP
            command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg on DUT instance")

            # If the number of hosts is less than the number of volumes then expand the host_ips list to equal to
            # number of volumes by repeating the existing entries for the required number of times
            self.final_host_ips = self.host_ips[:]
            if len(self.host_ips) < self.blt_count:
                for i in range(len(self.host_ips), self.blt_count):
                    self.final_host_ips.append(self.host_ips[i % len(self.host_ips)])

            for host_name in self.host_info:
                self.host_info[host_name]["num_volumes"] = self.final_host_ips.count(
                    self.host_info[host_name]["ip"])

            # Finding the usable capacity of the drives which will be used as the BLT volume capacity, in case
            # the capacity is not overridden while starting the script
            min_drive_capacity = find_min_drive_capacity(self.storage_controller, self.command_timeout)
            if min_drive_capacity:
                self.blt_details["max_capacity"] = min_drive_capacity
                # Reducing the volume capacity by drive margin as a workaround for the bug SWOS-6862
                self.blt_details["max_capacity"] -= self.drive_margin
            else:
                fun_test.critical(
                    "Unable to find the drive with minimum capacity...So going to use the BLT capacity"
                    "given in the script config file or capacity passed at the runtime...")

            if "capacity" in job_inputs:
                fun_test.critical("Original Volume size {} is overriden by the size {} given while running the "
                                  "script".format(self.blt_details["capacity"], job_inputs["capacity"]))
                self.blt_details["capacity"] = job_inputs["capacity"]

            # Create BLT's
            self.thin_uuid_list = []
            for i in range(self.blt_count):
                cur_uuid = utils.generate_uuid()
                self.thin_uuid_list.append(cur_uuid)
                command_result = self.storage_controller.create_volume(type=self.blt_details["type"],
                                                                       capacity=self.blt_details["capacity"],
                                                                       block_size=self.blt_details["block_size"],
                                                                       name="thin_block" + str(i + 1), group_id=i + 1,
                                                                       uuid=cur_uuid,allow_expansion=True,
                                                                       command_duration=self.command_timeout)
                fun_test.log(command_result)
                self.thin_uuid_list.append(cur_uuid)
                fun_test.test_assert(command_result["status"],
                                     "Create BLT {} with uuid {} and capacity {} on DUT".format(i + 1, cur_uuid,
                                                                                                self.blt_details[
                                                                                                    "capacity"]))

    def cleanup(self):
        if "blt" in fun_test.shared_variables and fun_test.shared_variables["blt"]["setup_created"]:
            self.fs = self.fs_objs[0]
            self.storage_controller = fun_test.shared_variables["sc_obj"][0]
            try:
                self.blt_details = fun_test.shared_variables["blt_details"]
                self.thin_uuid_list = fun_test.shared_variables["thin_uuid"]
                self.ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]
                self.nqn_list = fun_test.shared_variables["nqn_list"]

                # Setting the syslog level back to 6

                for index, host_name in enumerate(self.host_info):
                    host_handle = self.host_info[host_name]["handle"]
                    nqn = self.nqn_list[index]

                    nvme_disconnect_cmd = "nvme disconnect -n {}".format(nqn)
                    nvme_disconnect_output = host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                    nvme_disconnect_exit_status = host_handle.exit_status()
                    fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                                  message="Host {} - NVME Disconnect Status".format(host_name))

                # Detaching and deleting the volume
                print("thin_uuid_list", self.thin_uuid_list)
                for i, vol_uuid in enumerate(self.thin_uuid_list):
                    num_hosts = len(self.host_info)
                    ctrlr_index = i % num_hosts
                    ns_id = (i / num_hosts) + 1
                    command_result = self.storage_controller.detach_volume_from_controller(
                        ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], ns_id=ns_id, command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Detaching BLT volume {} from controller {}".
                                         format(vol_uuid, self.ctrlr_uuid[ctrlr_index]))

                    command_result = self.storage_controller.delete_volume(uuid=vol_uuid,
                                                                           type=str(self.blt_details['type']),
                                                                           command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Deleting BLT {} with uuid {} on DUT".
                                         format(i + 1, vol_uuid))

                # Deleting the controller
                for index, host_name in enumerate(self.host_info):
                    command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid[index],
                                                                               command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Deleting storage controller {}".
                                         format(self.ctrlr_uuid[index]))
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("Clean-up of volumes failed.")

            for i in self.thin_uuid_list:
                command_result = self.storage_controller.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN/" + i)
            fun_test.test_assert_expected(expected=False, actual=command_result["Status"],
                                          message="Checking if the volume id is deleted after deleting the volume")


class MultiHostVolumePerformanceTestcase18(FunTestCase):
    # Try to delete the volume without nvme disconnect

    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__

        self.testbed_config = fun_test.shared_variables["testbed_config"]
        self.syslog = fun_test.shared_variables["syslog"]

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
            fun_test.test_assert(benchmark_parsing,
                                 "Parsing Benchmark json file for this {} testcase".format(testcase))

        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

        # Setting the list of numjobs and IO depth combo
        # TODO: Check if block size is not required

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 12
        if not hasattr(self, "blt_count"):
            self.blt_count = 12

        fun_test.test_assert(benchmark_parsing,
                             "Parsing Benchmark json file for this {} testcase".format(testcase))

        # End of benchmarking json file parsing

        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
        fun_test.shared_variables["blt_count"] = self.blt_count

        # New changes
        fun_test.shared_variables["transport_type"] = self.transport_type

        self.nvme_block_device = self.nvme_device + "0n" + str(self.blt_details["ns_id"])
        self.volume_name = self.nvme_block_device.replace("/dev/", "")

        self.fs = fun_test.shared_variables["fs_objs"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1 = fun_test.shared_variables["f1_objs"][0][0]
        self.storage_controller = fun_test.shared_variables["sc_obj"][0]
        self.f1_ips = fun_test.shared_variables["f1_ips"][0]
        self.host_info = fun_test.shared_variables["host_info"]
        self.host_handles = fun_test.shared_variables["host_handles"]
        self.csi_perf_enabled = fun_test.shared_variables["csi_perf_enabled"]
        self.csi_cache_miss_enabled = fun_test.shared_variables["csi_cache_miss_enabled"]

        if self.csi_perf_enabled or self.csi_cache_miss_enabled:
            self.perf_listener_host_name = fun_test.shared_variables["perf_listener_host_name"]
            self.perf_listener_ip = fun_test.shared_variables["perf_listener_ip"]
        self.host_ips = fun_test.shared_variables["host_ips"]
        self.num_hosts = len(self.host_ips)
        self.end_host = self.host_handles[self.host_ips[0]]
        # self.numa_cpus = fun_test.shared_variables["numa_cpus"][self.host_ips[0]]
        # self.total_numa_cpus = fun_test.shared_variables["total_numa_cpus"][self.host_ips[0]]
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_loopback_ip"] = self.f1_ips
        self.remote_ip = self.host_ips[0]
        fun_test.shared_variables["remote_ip"] = self.remote_ip
        self.num_duts = fun_test.shared_variables["num_duts"]

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}

        if "csi_perf_iodepth" in job_inputs:
            self.csi_perf_iodepth = job_inputs["csi_perf_iodepth"]
            self.full_run_iodepth = self.csi_perf_iodepth
        if not isinstance(self.csi_perf_iodepth, list):
            self.csi_perf_iodepth = [self.csi_perf_iodepth]
            self.full_run_iodepth = self.csi_perf_iodepth

        if ("blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]):
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False
            fun_test.shared_variables["blt"]["warmup_done"] = False
            fun_test.shared_variables["blt_details"] = self.blt_details

            # Enabling counters
            """
            command_result = self.storage_controller.json_execute(verb="enable_counters",
                                                                  command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling Internal Stats/Counters")
            """

            # Configuring controller IP
            command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg on DUT instance")

            # If the number of hosts is less than the number of volumes then expand the host_ips list to equal to
            # number of volumes by repeating the existing entries for the required number of times
            self.final_host_ips = self.host_ips[:]
            if len(self.host_ips) < self.blt_count:
                for i in range(len(self.host_ips), self.blt_count):
                    self.final_host_ips.append(self.host_ips[i % len(self.host_ips)])

            for host_name in self.host_info:
                self.host_info[host_name]["num_volumes"] = self.final_host_ips.count(
                    self.host_info[host_name]["ip"])

            # Finding the usable capacity of the drives which will be used as the BLT volume capacity, in case
            # the capacity is not overridden while starting the script
            min_drive_capacity = find_min_drive_capacity(self.storage_controller, self.command_timeout)
            if min_drive_capacity:
                self.blt_details["max_capacity"] = min_drive_capacity
                # Reducing the volume capacity by drive margin as a workaround for the bug SWOS-6862
                self.blt_details["max_capacity"] -= self.drive_margin
            else:
                fun_test.critical(
                    "Unable to find the drive with minimum capacity...So going to use the BLT capacity"
                    "given in the script config file or capacity passed at the runtime...")

            if "capacity" in job_inputs:
                fun_test.critical("Original Volume size {} is overriden by the size {} given while running the "
                                  "script".format(self.blt_details["capacity"], job_inputs["capacity"]))
                self.blt_details["capacity"] = job_inputs["capacity"]

            # Create BLT's
            self.thin_uuid_list = []
            # a random uuid is generated but the volume is not created .Controller is created and attached to the non existing volume
            for i in range(self.blt_count):
                cur_uuid = utils.generate_uuid()
                self.thin_uuid_list.append(cur_uuid)
                command_result = self.storage_controller.create_volume(type=self.blt_details["type"],
                                                                       capacity=self.blt_details["capacity"],
                                                                       block_size=self.blt_details["block_size"],
                                                                       name="thin_block" + str(i + 1), group_id=i + 1,
                                                                       uuid=cur_uuid,
                                                                       command_duration=self.command_timeout)
                fun_test.log(command_result)
                self.thin_uuid_list.append(cur_uuid)
                fun_test.test_assert(command_result["status"],
                                     "Create BLT {} with uuid {} and capacity {} on DUT".format(i + 1, cur_uuid,
                                                                                                self.blt_details[
                                                                                                    "capacity"]))

            # Create one TCP controller per host\
            self.ctrlr_uuid = []
            for i in range(self.num_hosts):
                self.nvme_block_device = []

                self.nqn_list = []
                cur_uuid = utils.generate_uuid()
                self.ctrlr_uuid.append(cur_uuid)
                nqn = "nqn" + str(i + 1)
                self.nqn_list.append(nqn)
                command_result = self.storage_controller.create_controller(ctrlr_id=i,
                                                                           ctrlr_uuid=cur_uuid,
                                                                           ctrlr_type="BLOCK",
                                                                           transport=self.transport_type.upper(),
                                                                           remote_ip=self.host_ips[i],
                                                                           subsys_nqn=nqn,
                                                                           host_nqn=self.host_ips[i],
                                                                           port=self.transport_port,
                                                                           command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "Creating TCP controller for {} with uuid {} on DUT".
                                     format(self.host_ips[i], cur_uuid))

            fun_test.shared_variables["ctrlr_uuid"] = self.ctrlr_uuid
            fun_test.shared_variables["nqn_list"] = self.nqn_list

            # Attach volume to a controller
            for i in range(self.num_hosts):
                ctrlr_index = i % self.num_hosts
                ns_id = (i / self.num_hosts) + 1
                print("num of hosts", self.num_hosts)
                print("value of i is", i)
                print("value of ctrlr index is ", ctrlr_index)
                command_result = self.storage_controller.attach_volume_to_controller(
                    ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], vol_uuid=self.thin_uuid_list[0],
                    ns_id=ns_id, command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "Attaching BLT volume {} to the host {} via controller "
                                     "{}".format(self.thin_uuid_list[i],
                                                 self.host_ips[ctrlr_index],

                                                 self.ctrlr_uuid[ctrlr_index]))

            # Detaching and deleting the volume
            print("thin_uuid_list", self.thin_uuid_list)
            for i, vol_uuid in enumerate(self.thin_uuid_list):
                num_hosts = len(self.host_info)
                ctrlr_index = i % num_hosts
                ns_id = (i / num_hosts) + 1
                command_result = self.storage_controller.detach_volume_from_controller(
                    ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], ns_id=ns_id, command_duration=self.command_timeout)
                fun_test.test_assert(command_result["status"], "Detaching BLT volume {} from controller {}".
                                     format(vol_uuid, self.ctrlr_uuid[ctrlr_index]))

                command_result = self.storage_controller.delete_volume(uuid=vol_uuid,
                                                                       type=str(self.blt_details['type']),
                                                                       command_duration=self.command_timeout)
                fun_test.test_assert(command_result["status"], "Deleting BLT {} with uuid {} on DUT".
                                     format(i + 1, vol_uuid))

    def run(self):
                print "in run"

    def cleanup(self):
        if "blt" in fun_test.shared_variables and fun_test.shared_variables["blt"]["setup_created"]:
            self.fs = self.fs_objs[0]
            self.storage_controller = fun_test.shared_variables["sc_obj"][0]
            try:
                self.blt_details = fun_test.shared_variables["blt_details"]
                self.thin_uuid_list = fun_test.shared_variables["thin_uuid"]
                self.ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]
                self.nqn_list = fun_test.shared_variables["nqn_list"]

                # Setting the syslog level back to 6

                for index, host_name in enumerate(self.host_info):
                    host_handle = self.host_info[host_name]["handle"]
                    nqn = self.nqn_list[index]

                    nvme_disconnect_cmd = "nvme disconnect -n {}".format(nqn)
                    nvme_disconnect_output = host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                    nvme_disconnect_exit_status = host_handle.exit_status()
                    fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                                  message="Host {} - NVME Disconnect Status".format(host_name))

                # Detaching and deleting the volume
                print("thin_uuid_list", self.thin_uuid_list)
                for i, vol_uuid in enumerate(self.thin_uuid_list):
                    num_hosts = len(self.host_info)
                    ctrlr_index = i % num_hosts
                    ns_id = (i / num_hosts) + 1
                    command_result = self.storage_controller.detach_volume_from_controller(
                        ctrlr_uuid=self.ctrlr_uuid[ctrlr_index], ns_id=ns_id, command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Detaching BLT volume {} from controller {}".
                                         format(vol_uuid, self.ctrlr_uuid[ctrlr_index]))

                    command_result = self.storage_controller.delete_volume(uuid=vol_uuid,
                                                                           type=str(self.blt_details['type']),
                                                                           command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Deleting BLT {} with uuid {} on DUT".
                                         format(i + 1, vol_uuid))

                # Deleting the controller
                for index, host_name in enumerate(self.host_info):
                    command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid[index],
                                                                               command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Deleting storage controller {}".
                                         format(self.ctrlr_uuid[index]))
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("Clean-up of volumes failed.")

            for i in self.thin_uuid_list:
                command_result = self.storage_controller.peek("storage/volumes/VOL_TYPE_BLK_LOCAL_THIN/" + i)
            fun_test.test_assert_expected(expected=False, actual=command_result["Status"],
                                          message="Checking if the volume id is deleted after deleting the volume")


class ControlPlaneTesting8(MultiHostVolumePerformanceTestcase8):

    def describe(self):
        self.set_test_details(id=8,
                          summary="Create volume with different name with same uuid",
                          test_rail_case_ids=["C17793"],
                          steps='''
    1. Create 1 BLT volume
    2.Try to create a second volume with same uuid used for the first volume
    ''')

    def setup(self):
        super(ControlPlaneTesting8, self).setup()

    def run(self):
        super(ControlPlaneTesting8, self).run()

    def cleanup(self):
        super(ControlPlaneTesting8, self).cleanup()

class ControlPlaneTesting9(MultiHostVolumePerformanceTestcase9):

    def describe(self):
        self.set_test_details(id=9,
                              summary="Reusing of volume name and uuid should be allowed",
                              test_rail_case_ids=["C17794"],
                              steps='''
                              1. Create and attach the volume to host
                              2. Write data to it
                              3. Detach and delete volume
                              4. Create an another volume with the uuid and name used for the first volume
       
        ''')

    def setup(self):
        super(ControlPlaneTesting9, self).setup()

    def run(self):
        super(ControlPlaneTesting9, self).run()

    def cleanup(self):
        super(ControlPlaneTesting9, self).cleanup()


class ControlPlaneTesting10(MultiHostVolumePerformanceTestcase10):

    def describe(self):
        self.set_test_details(id=10,
                              summary="Create shared volume",
                              test_rail_case_ids=["C17795"],
                              steps='''

        ''')

    def setup(self):
        super(ControlPlaneTesting10, self).setup()

    def run(self):
        super(ControlPlaneTesting10, self).run()

    def cleanup(self):
        super(ControlPlaneTesting10, self).cleanup()


class ControlPlaneTesting11(MultiHostVolumePerformanceTestcase11):

    def describe(self):
        self.set_test_details(id=11,
                              summary="Attach non existant volume to a controller",
                              test_rail_case_ids=["C17798"],
                              steps='''

        ''')

    def setup(self):
        super(ControlPlaneTesting11, self).setup()

    def run(self):
        super(ControlPlaneTesting11, self).run()

    def cleanup(self):
        super(ControlPlaneTesting11, self).cleanup()


class ControlPlaneTesting12(MultiHostVolumePerformanceTestcase12):

    def describe(self):
        self.set_test_details(id=12,
                              summary="Attach same namespace twice",
                              test_rail_case_ids=["C17799"],
                              steps='''

        ''')

    def setup(self):
        super(ControlPlaneTesting12, self).setup()

    def run(self):
        super(ControlPlaneTesting12, self).run()

    def cleanup(self):
        super(ControlPlaneTesting12, self).cleanup()


class ControlPlaneTesting13(MultiHostVolumePerformanceTestcase13):

    def describe(self):
        self.set_test_details(id=13,
                              summary="Detach volume multiple times",
                              test_rail_case_ids=["C17804","C17807"],
                              steps='''

        ''')

    def setup(self):
        super(ControlPlaneTesting13, self).setup()

    def run(self):
        super(ControlPlaneTesting13, self).run()

    def cleanup(self):
        super(ControlPlaneTesting13, self).cleanup()

class ControlPlaneTesting14(MultiHostVolumePerformanceTestcase14):

    def describe(self):
        self.set_test_details(id=14,
                              summary="Delete name space without detach",
                              test_rail_case_ids=["C17805"],
                              steps='''

        ''')

    def setup(self):
        super(ControlPlaneTesting14, self).setup()

    def run(self):
        super(ControlPlaneTesting14, self).run()

    def cleanup(self):
        super(ControlPlaneTesting14, self).cleanup()





class ControlPlaneTesting16(MultiHostVolumePerformanceTestcase16):

    def describe(self):
        self.set_test_details(id=16,
                              summary="Configure BLT volume with compression enabled",
                              test_rail_case_ids=["C17851"],
                              steps='''

        ''')

    def setup(self):
        super(ControlPlaneTesting16, self).setup()

    def run(self):
        super(ControlPlaneTesting16, self).run()

    def cleanup(self):
        super(ControlPlaneTesting16, self).cleanup()


class ControlPlaneTesting17(MultiHostVolumePerformanceTestcase17):

    def describe(self):
        self.set_test_details(id=17,
                              summary="Create a volume of size equal to drive capacity and later try to expand the same",
                              test_rail_case_ids=["C17851"],
                              steps='''

        ''')

    def setup(self):
        super(ControlPlaneTesting17, self).setup()

    def run(self):
        super(ControlPlaneTesting17, self).run()

    def cleanup(self):
        super(ControlPlaneTesting17, self).cleanup()

class ControlPlaneTesting18(MultiHostVolumePerformanceTestcase18):

    def describe(self):
        self.set_test_details(id=18,
                              summary="Create and attach a volume ,delete the volume without nvme disconnect",
                              test_rail_case_ids=["C35437"],
                              steps='''
                              1. Create and attach the volume to host
                              2. Delete the volume without issuing a nvme disconnect from the host

        ''')

    def setup(self):
        super(ControlPlaneTesting18, self).setup()

    def run(self):
        super(ControlPlaneTesting18, self).run()

    def cleanup(self):
        super(ControlPlaneTesting18, self).cleanup()

if __name__ == "__main__":

    bltscript = MultiHostVolumePerformanceScript()
    bltscript.add_test_case(ControlPlaneTesting8())
    bltscript.add_test_case(ControlPlaneTesting9())
    bltscript.add_test_case(ControlPlaneTesting10())
    bltscript.add_test_case(ControlPlaneTesting11())
    bltscript.add_test_case(ControlPlaneTesting12())
    bltscript.add_test_case(ControlPlaneTesting13())
    bltscript.add_test_case(ControlPlaneTesting14())
    bltscript.add_test_case(ControlPlaneTesting16())
    bltscript.add_test_case(ControlPlaneTesting17())
    bltscript.add_test_case(ControlPlaneTesting18())
    bltscript.run()
