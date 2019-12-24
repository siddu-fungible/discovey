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
        if self.testbed_type != "suite-based":
            self.topology_helper = TopologyHelper()
        elif self.testbed_type == "suite-based":
            self.topology_helper = TopologyHelper()
            self.available_dut_indexes = self.topology_helper.get_available_duts().keys()
            fun_test.log("Available DUT Indexes: {}".format(self.available_dut_indexes))
            self.required_hosts = self.topology_helper.get_available_hosts()
            self.testbed_config = self.topology_helper.spec
            self.total_available_duts = len(self.available_dut_indexes)

        # fun_test.test_assert(expression=self.num_duts <= self.total_available_duts,
        #                      message="Testbed has enough DUTs")

        fpg_interfaces = self.topology_helper.get_expanded_topology().get_dut(index=0).get_fpg_interfaces(f1_index=0)
        bond_interfaces = self.topology_helper.get_expanded_topology().get_dut(index=0).get_bond_interfaces(
            f1_index=0)

        if not bond_interfaces:
            fun_test.shared_variables["f1_ips"] = [fpg_interfaces[0].ip]

        else:
            bond_interfaces = self.topology_helper.get_expanded_topology().get_dut(index=0).get_bond_interfaces(
                f1_index=0)
            fun_test.shared_variables["f1_ips"] = [bond_interfaces[0].ip.split("/")[0]]

        self.tftp_image_path = fun_test.get_job_environment_variable("tftp_image_path")
        self.bundle_image_parameters = fun_test.get_job_environment_variable("bundle_image_parameters")

        for i in range(len(self.bootargs)):
            self.bootargs[i] += " --mgmt"
            if self.disable_wu_watchdog:
                self.bootargs[i] += " --disable-wu-watchdog"

        # Deploying of DUTs
        self.available_dut_indexes = self.topology_helper.get_available_duts()
        for dut_index in self.available_dut_indexes:
            self.topology_helper.set_dut_parameters(dut_index=dut_index,
                                                    f1_parameters={0: {"boot_args": self.bootargs[0]},
                                                                   1: {"boot_args": self.bootargs[1]}},
                                                    fs_parameters={"already_deployed": False})
        self.topology = self.topology_helper.deploy()
        fun_test.test_assert(self.topology, "Topology deployed")
        fun_test.sleep(seconds=120, message="Waiting for storage controller API to start")

        # Datetime required for daily Dashboard data filter
        self.db_log_time = get_data_collection_time()
        fun_test.log("Data collection time: {}".format(self.db_log_time))

        hosts = self.topology.get_hosts()
        fun_test.log("Available hosts are: {}".format(hosts))
        required_host_index = []
        self.required_hosts = OrderedDict()
        for i in xrange(self.host_start_index, self.host_start_index + self.num_hosts):
            required_host_index.append(i)
        fun_test.debug("Host index required for scripts: {}".format(required_host_index))
        for j, host_name in enumerate(sorted(hosts)):
            if j in required_host_index:
                self.required_hosts[host_name] = hosts[host_name]
        fun_test.log("Hosts that will be used for current test: {}".format(self.required_hosts.keys()))

        self.host_info = OrderedDict()
        self.hosts_test_interfaces = {}
        self.host_handles = {}
        self.host_ips = []
        self.host_numa_cpus = {}
        self.total_numa_cpus = {}
        for host_name, host_obj in self.required_hosts.items():
            if host_name not in self.host_info:
                self.host_info[host_name] = {}
            # Retrieving host ips
            if host_name not in self.hosts_test_interfaces:
                self.hosts_test_interfaces[host_name] = []
            test_interface = host_obj.get_test_interface(index=0)
            self.hosts_test_interfaces[host_name].append(test_interface)
            self.host_info[host_name]["test_interface"] = test_interface
            host_ip = self.hosts_test_interfaces[host_name][-1].ip.split('/')[0]
            self.host_ips.append(host_ip)
            self.host_info[host_name]["ip"] = host_ip
            fun_test.log("Host-IP: {}".format(host_ip))
            # Retrieving host handles
            host_instance = host_obj.get_instance()
            self.host_handles[host_ip] = host_instance
            self.host_info[host_name]["handle"] = host_instance

        fun_test.log("Hosts info: {}".format(self.host_info))

        # Getting FS, F1 and COMe objects, Storage Controller objects, F1 IPs
        # for all the DUTs going to be used in the test
        self.fs_objs = []
        self.fs_spec = []
        self.come_obj = []
        self.f1_objs = {}
        self.sc_objs = []
        self.f1_ips = []
        self.gateway_ips = []
        for curr_index, dut_index in enumerate(self.available_dut_indexes):
            self.fs_objs.append(self.topology.get_dut_instance(index=dut_index))
            self.fs_spec.append(self.topology.get_dut(index=dut_index))
            self.come_obj.append(self.fs_objs[curr_index].get_come())
            self.f1_objs[curr_index] = []
            for j in xrange(self.num_f1_per_fs):
                self.f1_objs[curr_index].append(self.fs_objs[curr_index].get_f1(index=j))
                self.sc_objs.append(self.f1_objs[curr_index][j].get_dpc_storage_controller())



        """
        # Bringing up of FunCP docker container if it is needed
        self.funcp_obj = {}
        self.funcp_spec = {}
        for index in xrange(self.num_duts):
            self.funcp_obj[index] = StorageFsTemplate(self.come_obj[index])
            if self.tftp_image_path:
                self.funcp_spec[index] = self.funcp_obj[index].deploy_funcp_container(
                    update_deploy_script=self.update_deploy_script, update_workspace=self.update_workspace,
                    mode=self.funcp_mode)
                fun_test.test_assert(self.funcp_spec[index]["status"],
                                     "Starting FunCP docker container in DUT {}".format(index))
                # self.funcp_spec[index]["container_names"].sort()
            else:
                self.funcp_spec[index] = self.funcp_obj[index].get_container_objs()


            self.funcp_spec[index]["container_names"].sort()
            for f1_index, container_name in enumerate(self.funcp_spec[index]["container_names"]):
                if container_name == "run_sc":
                    continue
                bond_interfaces = self.fs_spec[index].get_bond_interfaces(f1_index=f1_index)
                bond_name = "bond0"
                bond_ip = bond_interfaces[0].ip
                self.f1_ips.append(bond_ip.split('/')[0])
                slave_interface_list = bond_interfaces[0].fpg_slaves
                slave_interface_list = [self.fpg_int_prefix + str(i) for i in slave_interface_list]
                self.funcp_obj[index].configure_bond_interface(container_name=container_name,
                                                               name=bond_name,
                                                               ip=bond_ip,
                                                               slave_interface_list=slave_interface_list)
                # Configuring route
                route = self.fs_spec[index].spec["bond_interface_info"][str(f1_index)][str(0)]["route"][0]
                # self.funcp_obj[index].container_info[container_name].command("hostname")
                cmd = "sudo ip route add {} via {} dev {}".format(route["network"], route["gateway"], bond_name)
                route_add_status = self.funcp_obj[index].container_info[container_name].command(cmd)
                fun_test.test_assert_expected(expected=0,
                                              actual=self.funcp_obj[index].container_info[
                                                  container_name].exit_status(),
                                              message="Configure Static route")

        """
        # Forming shared variables for defined parameters
        fun_test.shared_variables["topology"] = self.topology
        fun_test.shared_variables["fs_objs"] = self.fs_objs
        fun_test.shared_variables["come_obj"] = self.come_obj
        fun_test.shared_variables["f1_objs"] = self.f1_objs
        fun_test.shared_variables["sc_obj"] = self.sc_objs
        # fun_test.shared_variables["f1_ips"] = self.f1_ips
        fun_test.shared_variables["host_info"] = self.host_info
        fun_test.shared_variables["host_handles"] = self.host_handles
        fun_test.shared_variables["host_ips"] = self.host_ips
        fun_test.shared_variables["numa_cpus"] = self.host_numa_cpus
        fun_test.shared_variables["total_numa_cpus"] = self.total_numa_cpus
        fun_test.shared_variables["num_f1s"] = self.num_f1s
        fun_test.shared_variables["num_duts"] = self.num_duts
        fun_test.shared_variables["syslog"] = self.syslog
        fun_test.shared_variables["db_log_time"] = self.db_log_time

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

            """
            # Ensure required modules are loaded on host server, if not load it
            for module in self.load_modules:
                module_check = self.host_handles[key].lsmod(module)
                if not module_check:
                    self.host_handles[key].modprobe(module)
                    module_check = self.host_handles[key].lsmod(module)
                    fun_test.sleep("Loading {} module".format(module))
                fun_test.simple_assert(module_check, "{} module is loaded".format(module))
            """

        # Ensuring connectivity from Host to F1's
        """
        for key in self.host_handles:
            for index, ip in enumerate(self.f1_ips):
                ping_status = self.host_handles[key].ping(dst=ip)
                fun_test.test_assert(ping_status, "Host {} is able to ping to {}'s bond interface IP {}".
                                     format(key, self.funcp_spec[0]["container_names"][index], ip))
        """
        # Ensuring perf_host is able to ping F1 IP


        # fun_test.shared_variables["testbed_config"] = self.testbed_config
        fun_test.shared_variables["blt"] = {}
        fun_test.shared_variables["blt"]["setup_created"] = False
        fun_test.shared_variables["blt"]["warmup_done"] = False

    def cleanup(self):
        come_reboot = False
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


class MultiHostVolumePerformanceTestcase(FunTestCase):
    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__

        # self.testbed_config = fun_test.shared_variables["testbed_config"]
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
        if 'fio_jobs_iodepth' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['fio_jobs_iodepth']:
            benchmark_parsing = False
            fun_test.critical("Numjobs and IO depth combo to be used for this {} testcase is not available in "
                              "the {} file".format(testcase, benchmark_file))

        # Setting expected FIO results
        if 'expected_fio_result' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['expected_fio_result']:
            benchmark_parsing = False
            fun_test.critical("Benchmarking results for the block size and IO depth combo needed for this {} "
                              "testcase is not available in the {} file".format(testcase, benchmark_file))

        if "fio_sizes" in benchmark_dict[testcase]:
            if len(self.fio_sizes) != len(self.expected_fio_result.keys()):
                benchmark_parsing = False
                fun_test.critical("Mismatch in FIO sizes and its benchmarking results")
        elif "fio_jobs_iodepth" in benchmark_dict[testcase]:
            if len(self.fio_jobs_iodepth) != len(self.expected_fio_result.keys()):
                benchmark_parsing = False
                fun_test.critical("Mismatch in numjobs and IO depth combo and its benchmarking results")

        if 'fio_pass_threshold' not in benchmark_dict[testcase]:
            self.fio_pass_threshold = .05
            fun_test.log("Setting passing threshold to {} for this {} testcase, because its not set in the {} file".
                         format(self.fio_pass_threshold, testcase, benchmark_file))

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 12
        if not hasattr(self, "blt_count"):
            self.blt_count = 12

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))
        fun_test.log("Block size and IO depth combo going to be used for this {} testcase: {}".
                     format(testcase, self.fio_jobs_iodepth))
        fun_test.log("Benchmarking results going to be used for this {} testcase: \n{}".
                     format(testcase, self.expected_fio_result))
        # End of benchmarking json file parsing

        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
        fun_test.shared_variables["blt_count"] = self.blt_count

        # New changes
        fun_test.shared_variables["transport_type"] = self.transport_type

        self.nvme_block_device = self.nvme_device + "0n" + str(self.blt_details["ns_id"])
        self.volume_name = self.nvme_block_device.replace("/dev/", "")

        self.fs = fun_test.shared_variables["fs_objs"]
        self.fs[0].register_statistics(statistics_type=Fs.StatisticsType.BAM)
        self.fs[0].start_statistics_collection(statistics_type=Fs.StatisticsType.BAM)

        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1 = fun_test.shared_variables["f1_objs"][0][0]
        self.storage_controller = fun_test.shared_variables["sc_obj"][0]
        self.f1_ips = fun_test.shared_variables["f1_ips"][0]
        self.host_info = fun_test.shared_variables["host_info"]
        self.host_handles = fun_test.shared_variables["host_handles"]
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
        # --inputs = {\"num_host\":1,\"blt_count\":1,\"capacity\":468844544}

        job_inputs = {"num_host": 1, "blt_count": 1, "capacity": 468844544}
        if not job_inputs:
            job_inputs = {}
        fun_test.log("Provided job inputs: {}".format(job_inputs))
        if "blt_count" in job_inputs:
            self.blt_count = job_inputs["blt_count"]
        if "capacity" in job_inputs:
            self.blt_details["capacity"] = job_inputs["capacity"]
        if "nvme_io_queues" in job_inputs:
            self.nvme_io_queues = job_inputs["nvme_io_queues"]
        if "warm_up_traffic" in job_inputs:
            self.warm_up_traffic = job_inputs["warm_up_traffic"]
        if "runtime" in job_inputs:
            self.fio_cmd_args["runtime"] = job_inputs["runtime"]
            self.fio_cmd_args["timeout"] = self.fio_cmd_args["runtime"] + 60
        if "post_results" in job_inputs:
            self.post_results = job_inputs["post_results"]
        else:
            self.post_results = False
        if "csi_perf_iodepth" in job_inputs:
            self.csi_perf_iodepth = job_inputs["csi_perf_iodepth"]
        if not isinstance(self.csi_perf_iodepth, list):
            self.csi_perf_iodepth = [self.csi_perf_iodepth]

        if ("blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]) \
                and (not fun_test.shared_variables["blt"]["warmup_done"]):
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
                self.blt_details["capacity"] = min_drive_capacity
                # Reducing the volume capacity by drive margin as a workaround for the bug SWOS-6862
                self.blt_details["capacity"] -= self.drive_margin
            else:
                fun_test.critical("Unable to find the drive with minimum capacity...So going to use the BLT capacity"
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
                                                                       name="thin_block" + str(i + 1), group_id=i+1,
                                                                       uuid=cur_uuid,
                                                                       command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Create BLT {} with uuid {} on DUT".format(i + 1,
                                                                                                          cur_uuid))

            fun_test.shared_variables["thin_uuid"] = self.thin_uuid_list

            # Create one TCP controller per host
            self.nvme_block_device = []
            self.ctrlr_uuid = []
            self.nqn_list = []
            for i in range(0, self.num_hosts):
                cur_uuid = utils.generate_uuid()
                self.ctrlr_uuid.append(cur_uuid)
                nqn = "nqn" + str(i + 1)
                self.nqn_list.append(nqn)
                command_result = self.storage_controller.create_controller(ctrlr_id=i,
                                                                           ctrlr_uuid=cur_uuid,
                                                                           ctrlr_type="BLOCK",
                                                                           transport=self.transport_type.upper(),
                                                                           remote_ip=self.host_ips[i], subsys_nqn=nqn,
                                                                           host_nqn=self.host_ips[i],
                                                                           port=self.transport_port,
                                                                           command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Creating TCP controller for {} with uuid {} on DUT".
                                     format(self.host_ips[i], cur_uuid))

            fun_test.shared_variables["ctrlr_uuid"] = self.ctrlr_uuid
            fun_test.shared_variables["nqn_list"] = self.nqn_list

            # Attach controller to BLTs
            for i in range(self.blt_count):
                ctrlr_index = i % self.num_hosts
                ns_id = (i / self.num_hosts) + 1
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


                # host_handle.start_bg_process(command="sudo tcpdump -i enp216s0 -w nvme_connect_auto.pcap")
                for i in range(2):
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
                        fun_test.sleep("Wait for retry nvme connect", seconds=20)
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

            thread_id = {}
            end_host_thread = {}

            # Pre-conditioning the volume (one time task)
            if self.warm_up_traffic:
                # self.nvme_block_device_str = ':'.join(self.nvme_block_device)
                # fun_test.shared_variables["nvme_block_device_str"] = self.nvme_block_device_str
                fio_output = {}
                for index, host_name in enumerate(self.host_info):
                    fun_test.log("Initial Write IO to volume, this might take long time depending on fio --size "
                                 "provided")
                    warm_up_fio_cmd_args = {}
                    jobs = ""
                    fio_output[index] = {}
                    end_host_thread[index] = self.host_info[host_name]["handle"].clone()
                    wait_time = self.num_hosts - index
                    if "multiple_jobs" in self.warm_up_fio_cmd_args:
                        # Adding the allowed CPUs into the fio warmup command
                        # self.warm_up_fio_cmd_args["multiple_jobs"] += "  --cpus_allowed={}".\
                        #    format(self.host_info[host_name]["host_numa_cpus"])
                        # fio_cpus_allowed_args = " --cpus_allowed={}".format(self.host_info[host_name]["host_numa_cpus"])
                        fio_cpus_allowed_args = ""
                        for id, device in enumerate(self.host_info[host_name]["nvme_block_device_list"]):
                            jobs += " --name=pre-cond-job-{} --filename={}".format(id + 1, device)
                        warm_up_fio_cmd_args["multiple_jobs"] = self.warm_up_fio_cmd_args["multiple_jobs"] + str(
                            fio_cpus_allowed_args) + str(jobs)
                        warm_up_fio_cmd_args["timeout"] = self.warm_up_fio_cmd_args["timeout"]
                        # fio_output = self.host_handles[key].pcie_fio(filename="nofile", timeout=self.warm_up_fio_cmd_args["timeout"],
                        #                                    **warm_up_fio_cmd_args)
                        thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                         func=fio_parser,
                                                                         arg1=end_host_thread[index],
                                                                         host_index=index,
                                                                         filename="nofile",
                                                                         **warm_up_fio_cmd_args)
                    else:
                        # Adding the allowed CPUs into the fio warmup command
                        self.warm_up_fio_cmd_args["cpus_allowed"] = self.host_info[host_name]["host_numa_cpus"]
                        # fio_output = self.host_handles[key].pcie_fio(filename=self.nvme_block_device_str, **self.warm_up_fio_cmd_args)
                        filename = self.host_info[host_name]["fio_filename"]
                        thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                         func=fio_parser,
                                                                         arg1=end_host_thread[index],
                                                                         host_index=index,
                                                                         filename=filename,
                                                                         **self.warm_up_fio_cmd_args)

                    fun_test.sleep("Fio threadzz", seconds=1)

                fun_test.sleep("Fio threads started", 10)
                try:
                    for index, host_name in enumerate(self.host_info):
                        fun_test.log("Joining fio thread {}".format(index))
                        fun_test.join_thread(fun_test_thread_id=thread_id[index])
                        fun_test.log("FIO Command Output:")
                        fun_test.log(fun_test.shared_variables["fio"][index])
                        fun_test.test_assert(fun_test.shared_variables["fio"][index], "Volume warmup on host {}".
                                             format(host_name))
                        fio_output[index] = {}
                        fio_output[index] = fun_test.shared_variables["fio"][index]
                        fun_test.shared_variables["blt"]["warmup_done"] = True
                except Exception as ex:
                    fun_test.log("Fio warmup failed")
                    fun_test.critical(str(ex))

                fun_test.sleep("Sleeping for {} seconds before actual test".format(self.iter_interval),
                               self.iter_interval)

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[3:]
        self.test_mode = testcase[12:]

        # Going to run the FIO test for the block size and iodepth combo listed in fio_jobs_iodepth in both write only
        # & read only modes
        fio_result = {}
        fio_output = {}
        internal_result = {}

        table_data_headers = ["Block Size", "IO Depth", "Size", "Operation", "Write IOPS", "Read IOPS",
                              "Write Throughput in MB/s", "Read Throughput in MB/s", "Write Latency in uSecs",
                              "Write Latency 90 Percentile in uSecs", "Write Latency 95 Percentile in uSecs",
                              "Write Latency 99 Percentile in uSecs", "Write Latency 99.99 Percentile in uSecs",
                              "Read Latency in uSecs", "Read Latency 90 Percentile in uSecs",
                              "Read Latency 95 Percentile in uSecs", "Read Latency 99 Percentile in uSecs",
                              "Read Latency 99.99 Percentile in uSecs", "fio_job_name"]
        table_data_cols = ["block_size", "iodepth", "size", "mode", "writeiops", "readiops", "writebw", "readbw",
                           "writeclatency", "writelatency90", "writelatency95", "writelatency99", "writelatency9999",
                           "readclatency", "readlatency90", "readlatency95", "readlatency99", "readlatency9999",
                           "fio_job_name"]
        table_data_rows = []

        # Preparing the volume details list containing the list of dictionaries
        vol_details = []
        vol_group = {}
        vol_group[self.blt_details["type"]] = fun_test.shared_variables["thin_uuid"]
        vol_details.append(vol_group)

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        if "io_depth" in job_inputs:
            self.fio_jobs_iodepth = job_inputs["io_depth"]
            fun_test.log("Overrided fio_jobs_iodepth: {}".format(self.fio_jobs_iodepth))

        if not isinstance(self.fio_jobs_iodepth, list):
            self.fio_jobs_iodepth = [self.fio_jobs_iodepth]

        for combo in self.fio_jobs_iodepth:
            thread_id = {}
            end_host_thread = {}
            iostat_thread = {}
            final_fio_output = {}
            tmp = combo.split(',')
            fio_numjobs = tmp[0].strip('() ')
            fio_iodepth = tmp[1].strip('() ')

            """

            file_suffix = "{}_iodepth_{}.txt".format(self.test_mode, (int(fio_iodepth) * int(fio_numjobs)))
            for index, stat_detail in enumerate(self.stats_collect_details):
                func = stat_detail.keys()[0]
                self.stats_collect_details[index][func]["count"] = int(
                    self.fio_cmd_args["runtime"] / self.stats_collect_details[index][func]["interval"])
                if func == "vol_stats":
                    self.stats_collect_details[index][func]["vol_details"] = vol_details
            fun_test.log("Different stats collection thread details for the current IO depth {} before starting "
                         "them:\n{}".format((int(fio_iodepth) * int(fio_numjobs)), self.stats_collect_details))
            self.storage_controller.verbose = False
            stats_obj = CollectStats(self.storage_controller)
            stats_obj.start(file_suffix, self.stats_collect_details)
            fun_test.log("Different stats collection thread details for the current IO depth {} after starting "
                         "them:\n{}".format((int(fio_iodepth) * int(fio_numjobs)), self.stats_collect_details))
            """
            for i, host_name in enumerate(self.host_info):
                fio_result[combo] = {}
                fio_output[combo] = {}
                final_fio_output[combo] = {}
                internal_result[combo] = {}

                end_host_thread[i] = self.host_info[host_name]["handle"].clone()

                for mode in self.fio_modes:
                    fio_block_size = self.fio_bs
                    fio_result[combo][mode] = True
                    internal_result[combo][mode] = True
                    row_data_dict = {}
                    row_data_dict["mode"] = mode
                    row_data_dict["block_size"] = fio_block_size
                    row_data_dict["iodepth"] = int(fio_iodepth) * int(fio_numjobs)
                    row_data_dict["num_jobs"] = fio_numjobs
                    file_size_in_gb = self.blt_details["capacity"] / 1073741824
                    row_data_dict["size"] = str(file_size_in_gb) + "GB"

                    fun_test.log("Running FIO {} only test for block size: {} using num_jobs: {}, IO depth: {}".
                                 format(mode, fio_block_size, fio_numjobs, fio_iodepth))


                    """
                    starting_core = int(self.host_info[host_name]["host_numa_cpus"].split(',')[0].split('-')[0]) + 1
                    if int(fio_numjobs) == 1:
                        cpus_allowed = str(starting_core)
                    elif int(fio_numjobs) == 4:
                        cpus_allowed = "{}-4".format(starting_core)
                    elif int(fio_numjobs) > 4:
                        cpus_allowed = "{}-{}".format(starting_core, self.host_info[host_name]["host_numa_cpus"][2:])
                    """


                    """
                    # Flush cache before read test
                    self.end_host.sudo_command("sync")
                    self.end_host.sudo_command("echo 3 > /proc/sys/vm/drop_caches")
                    """

                    fun_test.log("Running FIO...")
                    # fio_job_name = "fio_tcp_" + mode + "_" + "blt" + "_" + fio_numjobs + "_" + fio_iodepth + "_vol_" + str(self.blt_count)
                    fio_job_name = "fio_tcp_{}_blt_{}_{}_vol_{}".format(mode, fio_numjobs, fio_iodepth, self.blt_count)
                    # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                    fio_output[combo][mode] = {}
                    final_fio_output[combo][mode] = {}
                    """
                    if hasattr(self, "test_blt_count") and self.test_blt_count == 1:
                        fio_filename = fun_test.shared_variables["nvme_block_device_list"][0]
                    else:
                        fio_filename = fun_test.shared_variables["nvme_block_device_str"]
                    """
                    # fio_filename = str(fun_test.shared_variables["vol_list"][i]["vol_name"])
                    wait_time = self.num_hosts - i
                    """
                    fio_output[combo][mode] = self.end_host.pcie_fio(filename=fio_filename,
                                                                    numjobs=fio_numjobs,
                                                                    rw=mode,
                                                                    bs=fio_block_size,
                                                                    iodepth=fio_iodepth,
                                                                    name=fio_job_name,
                                                                    cpus_allowed=cpus_allowed,
                                                                    **self.fio_cmd_args)
                    """
                    # Deciding the FIO runtime based on the current IO depth
                    if row_data_dict["iodepth"] in self.full_run_iodepth:
                        fio_runtime = self.fio_full_run_time
                        fio_timeout = self.fio_full_run_timeout
                    else:
                        fio_runtime = self.fio_cmd_args["runtime"]
                        fio_timeout = self.fio_cmd_args["timeout"]
                    # Building the FIO command
                    fio_cmd_args = {}

                    runtime_global_args = " --runtime={} --cpus_allowed={} --bs={} --rw={} --numjobs={} --iodepth={}".\
                        format(fio_runtime, 2, fio_block_size, mode, fio_numjobs, fio_iodepth)
                    jobs = ""
                    for id, device in enumerate(self.host_info[host_name]["nvme_block_device_list"]):
                        jobs += " --name=vol{} --filename={}".format(id + 1, device)

                    fio_cmd_args["multiple_jobs"] = self.fio_cmd_args["multiple_jobs"] + runtime_global_args + jobs
                    fio_cmd_args["timeout"] = fio_timeout

                    thread_id[i] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                 func=fio_parser, arg1=end_host_thread[i],
                                                                 host_index=i, filename="nofile", **fio_cmd_args)

                    fun_test.sleep("Fio threadzz", seconds=1)

            fun_test.sleep("Fio threads started", 10)
            # Starting csi perf stats collection if it's set


            try:
                for i, host_name in enumerate(self.host_info):
                    fun_test.log("Joining fio thread {}".format(i))
                    fun_test.join_thread(fun_test_thread_id=thread_id[i])
                    fun_test.log("FIO Command Output:")
                    fun_test.log(fun_test.shared_variables["fio"][i])
                    fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                         "Fio {} test with IO depth {} in host {}".
                                         format(mode, int(fio_iodepth) * int(fio_numjobs), host_name))
                    fio_output[combo][mode][i] = {}
                    fio_output[combo][mode][i] = fun_test.shared_variables["fio"][i]
                final_fio_output[combo][mode] = fio_output[combo][mode][0]
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("FIO Command Output for volume {}:\n {}".format(i, fio_output[combo][mode][i]))
            finally:
                # stats_obj.stop(self.stats_collect_details)
                self.storage_controller.verbose = True


            fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval), self.iter_interval)

            for i in range(1, len(self.host_info)):
                fun_test.test_assert(fio_output[combo][mode][i], "Fio threaded test")
                # Boosting the fio output with the testbed performance multiplier
                multiplier = 1
                for op, stats in self.expected_fio_result[combo][mode].items():
                    for field, value in stats.items():
                        if field == "latency":
                            fio_output[combo][mode][i][op][field] = int(round(value / multiplier))
                        final_fio_output[combo][mode][op][field] += fio_output[combo][mode][i][op][field]
                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval))

            # Comparing the FIO results with the expected value for the current block size and IO depth combo
            for op, stats in self.expected_fio_result[combo][mode].items():
                for field, value in stats.items():
                    # fun_test.log("op is: {} and field is: {} ".format(op, field))
                    actual = final_fio_output[combo][mode][op][field]
                    if "latency" in str(field):
                        actual = int(round(actual / self.blt_count))
                    row_data_dict[op + field] = (actual, int(round((value * (1 - self.fio_pass_threshold)))),
                                                 int((value * (1 + self.fio_pass_threshold))))

            row_data_dict["fio_job_name"] = fio_job_name

            # Building the table row for this variation for both the script table and performance dashboard
            row_data_list = []
            for i in table_data_cols:
                if i not in row_data_dict:
                    row_data_list.append(-1)
                else:
                    row_data_list.append(row_data_dict[i])

            table_data_rows.append(row_data_list)
            if self.post_results:
                fun_test.log("Posting results on dashboard")
                post_results("Multi_host_TCP", test_method, *row_data_list)

            table_data = {"headers": table_data_headers, "rows": table_data_rows}
            fun_test.add_table(panel_header="Multiple hosts over TCP Perf Table", table_name=self.summary,
                               table_data=table_data)

        # Posting the final status of the test result
        test_result = True
        fun_test.log(fio_result)
        fun_test.log(internal_result)
        for combo in self.fio_jobs_iodepth:
            for mode in self.fio_modes:
                if not fio_result[combo][mode] or not internal_result[combo][mode]:
                    test_result = False

        fun_test.log("Test Result: {}".format(test_result))

    def cleanup(self):
        pass


class MultiHostFioRandRead(MultiHostVolumePerformanceTestcase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Random read performance for muiltple hosts on TCP "
                                      "with different levels of numjobs & iodepth & block size 4K",
                              steps='''
        1. Create 1 BLT volumes on F1 attached
        2. Create a storage controller for TCP and attach above volumes to this controller   
        3. Connect to this volume from remote host
        4. Run the FIO Random read test(without verify) for various block size and IO depth from the 
        remote host and check the performance are inline with the expected threshold. 
        ''')

    def setup(self):
        super(MultiHostFioRandRead, self).setup()

    def run(self):
        super(MultiHostFioRandRead, self).run()

    def cleanup(self):
        super(MultiHostFioRandRead, self).cleanup()




if __name__ == "__main__":

    bltscript = MultiHostVolumePerformanceScript()
    bltscript.add_test_case(MultiHostFioRandRead())
    # bltscript.add_test_case(MultiHostFioRandWrite())
    bltscript.run()