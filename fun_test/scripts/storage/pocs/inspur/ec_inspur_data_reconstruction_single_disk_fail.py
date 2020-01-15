from lib.system.fun_test import *
from lib.system import utils
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper, ModelHelper, get_data_collection_time
from lib.fun.fs import Fs
import re
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_fs_template import *
from scripts.storage.storage_helper import *
from scripts.networking.helper import *
from collections import OrderedDict, Counter
from fun_global import PerfUnit, FunPlatform
from lib.templates.storage.storage_controller_api import *

'''
Script for Inspur Functional Testing of Data Reconstruction With Disk Disk Failure and monitor Performance impact
'''


def fio_parser(arg1, host_index, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    fun_test.shared_variables["fio"][host_index] = fio_output
    fun_test.simple_assert(fio_output, "Fio test for thread {}".format(host_index))
    arg1.disconnect()


def post_results(volume, test, num_host, block_size, io_depth, size, operation, write_iops, read_iops, write_bw,
                 read_bw, write_latency, write_90_latency, write_95_latency, write_99_latency, write_99_99_latency,
                 read_latency, read_90_latency, read_95_latency, read_99_latency, read_99_99_latency, plex_rebuild_time,
                 fio_job_name):
    for i in ["write_iops", "read_iops", "write_bw", "read_bw", "write_latency", "write_90_latency", "write_95_latency",
              "write_99_latency", "write_99_99_latency", "read_latency", "read_90_latency", "read_95_latency",
              "read_99_latency", "read_99_99_latency", "fio_job_name"]:
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


def add_to_data_base(value_dict):
    unit_dict = {
        "write_iops_unit": PerfUnit.UNIT_OPS, "read_iops_unit": PerfUnit.UNIT_OPS,
        "write_throughput_unit": PerfUnit.UNIT_MBYTES_PER_SEC, "read_throughput_unit": PerfUnit.UNIT_MBYTES_PER_SEC,
        "write_avg_latency_unit": PerfUnit.UNIT_USECS, "write_90_latency_unit": PerfUnit.UNIT_USECS,
        "write_95_latency_unit": PerfUnit.UNIT_USECS, "write_99_99_latency_unit": PerfUnit.UNIT_USECS,
        "write_99_latency_unit": PerfUnit.UNIT_USECS, "read_avg_latency_unit": PerfUnit.UNIT_USECS,
        "read_90_latency_unit": PerfUnit.UNIT_USECS, "read_95_latency_unit": PerfUnit.UNIT_USECS,
        "read_99_99_latency_unit": PerfUnit.UNIT_USECS, "read_99_latency_unit": PerfUnit.UNIT_USECS,
        "plex_rebuild_time_unit": PerfUnit.UNIT_SECS
    }

    model_name = "InspurDataReconstructionPerformance"
    status = fun_test.PASSED
    try:
        generic_helper = ModelHelper(model_name=model_name)
        generic_helper.set_units(validate=True, **unit_dict)
        generic_helper.add_entry(**value_dict)
        generic_helper.set_status(status)
    except Exception as ex:
        fun_test.critical(str(ex))


class DataReconstructOnDiskFailScript(FunTestScript):
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
            self.syslog_level = 2
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
        fun_test.shared_variables["syslog_level"] = self.syslog_level
        fun_test.shared_variables["db_log_time"] = self.db_log_time
        fun_test.shared_variables["host_info"] = self.host_info

        # for host_name in self.host_info:
        #     host_handle = self.host_info[host_name]["handle"]
        #     # Ensure all hosts are up after reboot
        #     fun_test.test_assert(host_handle.ensure_host_is_up(max_wait_time=self.reboot_timeout),
        #                          message="Ensure Host {} is reachable after reboot".format(host_name))
        #     # Ensure required modules are loaded on host server, if not load it
        #     for module in self.load_modules:
        #         module_check = host_handle.lsmod(module)
        #         if not module_check:
        #             host_handle.modprobe(module)
        #             module_check = host_handle.lsmod(module)
        #             fun_test.sleep("Loading {} module".format(module))
        #         fun_test.simple_assert(module_check, "{} module is loaded".format(module))
        #
        # # Ensuring connectivity from Host to F1's
        # for host_name in self.host_info:
        #     host_handle = self.host_info[host_name]["handle"]
        #     for index, ip in enumerate(self.f1_ips):
        #         ping_status = host_handle.ping(dst=ip, max_percentage_loss=80)
        #         fun_test.test_assert(ping_status, "Host {} is able to ping to {}'s bond interface IP {}".
        #                              format(host_name, self.funcp_spec[0]["container_names"][index], ip))

    def cleanup(self):
        come_reboot = False
        if fun_test.shared_variables["ec"]["setup_created"]:
            self.fs = self.fs_objs[0]
            self.storage_controller = fun_test.shared_variables["sc_obj"][self.f1_in_use]
            try:
                self.ec_info = fun_test.shared_variables["ec_info"]
                self.attach_transport = fun_test.shared_variables["attach_transport"]
                self.ctrlr_uuid = fun_test.shared_variables["ctrlr_uuid"]
                self.nvme_subsystem = fun_test.shared_variables["nvme_subsystem"]

                # Saving the pcap file captured during the nvme connect to the pcap_artifact_file file
                for host_name in self.host_info:
                    host_handle = self.host_info[host_name]["handle"]
                    pcap_post_fix_name = "{}_nvme_connect.pcap".format(host_name)
                    pcap_artifact_file = fun_test.get_test_case_artifact_file_name(post_fix_name=pcap_post_fix_name)

                    fun_test.scp(source_port=host_handle.ssh_port, source_username=host_handle.ssh_username,
                                 source_password=host_handle.ssh_password, source_ip=host_handle.host_ip,
                                 source_file_path="/tmp/nvme_connect.pcap", target_file_path=pcap_artifact_file)
                    fun_test.add_auxillary_file(description="Host {} NVME connect pcap".format(host_name),
                                                filename=pcap_artifact_file)

                # Executing NVMe disconnect from all the hosts
                nvme_disconnect_cmd = "nvme disconnect -n {}".format(self.nvme_subsystem)
                for host_name in self.host_info:
                    host_handle = self.host_info[host_name]["handle"]
                    nvme_disconnect_output = host_handle.sudo_command(command=nvme_disconnect_cmd, timeout=60)
                    nvme_disconnect_exit_status = host_handle.exit_status()
                    fun_test.test_assert_expected(expected=0, actual=nvme_disconnect_exit_status,
                                                  message="{} - NVME Disconnect Status".format(host_name))
                # Detaching all the EC/LS volumes to the external server
                for num in xrange(self.ec_info["num_volumes"]):
                    command_result = self.storage_controller.detach_volume_from_controller(
                        ctrlr_uuid=self.ctrlr_uuid[num], ns_id=num + 1, command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Detaching {} EC/LS volume from DUT".format(num))

                # Unconfiguring all the LSV/EC and it's plex volumes
                self.storage_controller.unconfigure_ec_volume(ec_info=self.ec_info,
                                                              command_timeout=self.command_timeout)
                # Deleting all the storage controller
                for index in xrange(len(self.host_info)):
                    command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid,
                                                                               command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Deleting Storage Controller {}".
                                         format(self.ctrlr_uuid[index]))
                self.storage_controller.disconnect()
            except Exception as ex:
                fun_test.critical(str(ex))
                come_reboot = True


class DataReconstructOnDiskFailTestcase(FunTestCase):

    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__

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
        self.syslog_level = fun_test.shared_variables["syslog_level"]
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
        if "warmup_bs" in job_inputs:
            self.warm_up_fio_cmd_args["bs"] = job_inputs["warmup_bs"]
        self.f1_in_use = fun_test.shared_variables["f1_in_use"]
        self.fs_obj = fun_test.shared_variables["fs_obj"]
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
        self.db_log_time = fun_test.shared_variables["db_log_time"]

        if "ec" not in fun_test.shared_variables or not fun_test.shared_variables["ec"]["setup_created"]:
            fun_test.shared_variables["ec"] = {}
            fun_test.shared_variables["ec"]["setup_created"] = False
            fun_test.shared_variables["ec"]["nvme_connect"] = False
            fun_test.shared_variables["ec"]["warmup_io_completed"] = False
            fun_test.shared_variables["ec_info"] = self.ec_info
            fun_test.shared_variables["num_volumes"] = self.ec_info["num_volumes"]

            command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg configured on DUT instance")

            (ec_config_status, self.ec_info) = self.storage_controller.configure_ec_volume(self.ec_info,
                                                                                           self.command_timeout)
            fun_test.simple_assert(ec_config_status, "Configuring EC/LSV volume")

            fun_test.log("EC details after configuring EC Volume:")
            for k, v in self.ec_info.items():
                fun_test.log("{}: {}".format(k, v))

            if self.rebuild_on_spare_volume:
                num = self.test_volume_start_index
                vtype = "ndata"
                self.spare_vol_uuid = utils.generate_uuid()
                self.ec_info["uuids"][num][vtype].append(self.spare_vol_uuid)
                self.ec_info["uuids"][num]["blt"].append(self.spare_vol_uuid)
                command_result = self.storage_controller.create_volume(
                    type=self.ec_info["volume_types"][vtype], capacity=self.ec_info["volume_capacity"][num][vtype],
                    block_size=self.ec_info["volume_block"][vtype], name=vtype + "_" + self.spare_vol_uuid[-4:],
                    uuid=self.spare_vol_uuid, group_id=num + 1, command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(
                    command_result["status"], "Creating Spare Volume {} {} {} {} bytes volume on DUT instance".
                        format(num, vtype, self.ec_info["volume_types"][vtype],
                               self.ec_info["volume_capacity"][num][vtype]))
                fun_test.log("EC details after Creating Spare Plex for rebuild:")
                for k, v in self.ec_info.items():
                    fun_test.log("{}: {}".format(k, v))

            # Attaching/Exporting all the EC/LS volumes to the external server
            self.ctrlr_uuid = []
            for host_name in self.host_info:
                self.ctrlr_uuid.append(utils.generate_uuid())
                command_result = self.storage_controller.create_controller(ctrlr_id=0,
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

            fun_test.shared_variables["ec"]["setup_created"] = True
            fun_test.shared_variables["ctrlr_uuid"] = self.ctrlr_uuid

            # disabling the error_injection for the EC volume
            command_result = {}
            command_result = self.storage_controller.poke("params/ecvol/error_inject 0",
                                                          command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Disabling error_injection for EC volume on DUT")

            # Ensuring that the error_injection got disabled properly
            fun_test.sleep("Sleeping for a second to disable the error_injection", 1)
            command_result = {}
            command_result = self.storage_controller.peek("params/ecvol", command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Retrieving error_injection status on DUT")
            fun_test.test_assert_expected(actual=int(command_result["data"]["error_inject"]), expected=0,
                                          message="Ensuring error_injection got disabled")

            # Starting packet capture in all the hosts
            pcap_started = {}
            pcap_stopped = {}
            pcap_pid = {}
            for host_name in self.host_info:
                host_handle = self.host_info[host_name]["handle"]
                test_interface = self.host_info[host_name]["test_interface"].name
                pcap_started[host_name] = False
                pcap_stopped[host_name] = True
                pcap_pid[host_name] = {}
                pcap_pid[host_name] = host_handle.tcpdump_capture_start(interface=test_interface,
                                                                        tcpdump_filename="/tmp/nvme_connect.pcap")
                if pcap_pid[host_name]:
                    fun_test.log("Started packet capture in {}".format(host_name))
                    pcap_started[host_name] = True
                    pcap_stopped[host_name] = False
                else:
                    fun_test.critical("Unable to start packet capture in {}".format(host_name))

            fun_test.shared_variables["fio"] = {}
            for host_name in self.host_info:
                fun_test.shared_variables["ec"][host_name] = {}
                host_handle = self.host_info[host_name]["handle"]
                if not fun_test.shared_variables["ec"]["nvme_connect"]:
                    # Checking nvme-connect status
                    if not hasattr(self, "io_queues") or (hasattr(self, "io_queues") and self.io_queues == 0):
                        nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -q {}". \
                            format(self.attach_transport.lower(), self.test_network["f1_loopback_ip"],
                                   str(self.transport_port), self.nvme_subsystem,
                                   self.host_info[host_name]["ip"])
                    else:
                        nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}". \
                            format(self.attach_transport.lower(), self.test_network["f1_loopback_ip"],
                                   str(self.transport_port), self.nvme_subsystem, str(self.io_queues),
                                   self.host_info[host_name]["ip"])
                    try:
                        nvme_connect_output = host_handle.sudo_command(command=nvme_connect_cmd, timeout=60)
                        nvme_connect_exit_status = host_handle.exit_status()
                        fun_test.log("nvme_connect_output output is: {}".format(nvme_connect_output))
                        if nvme_connect_exit_status and pcap_started[host_name]:
                            host_handle.tcpdump_capture_stop(process_id=pcap_pid[host_name])
                            pcap_stopped[host_name] = True
                    except Exception as ex:
                        # Stopping the packet capture if it is started
                        if pcap_started[host_name]:
                            host_handle.tcpdump_capture_stop(process_id=pcap_pid[host_name])
                            pcap_stopped[host_name] = True

                    fun_test.test_assert_expected(expected=0, actual=nvme_connect_exit_status,
                                                  message="{} - NVME Connect Status".format(host_name))

                    lsblk_output = host_handle.lsblk("-b")
                    fun_test.simple_assert(lsblk_output, "Listing available volumes")

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
                    fun_test.shared_variables["ec"][host_name]["nvme_connect"] = True

                    self.host_info[host_name]["nvme_block_device_list"].sort()
                    self.host_info[host_name]["fio_filename"] = \
                        ":".join(self.host_info[host_name]["nvme_block_device_list"])
                    fun_test.shared_variables["host_info"] = self.host_info
                    fun_test.log("Hosts info: {}".format(self.host_info))

            # Stopping the packet capture
            for host_name in self.host_info:
                host_handle = self.host_info[host_name]["handle"]
                if pcap_started[host_name]:
                    host_handle.tcpdump_capture_stop(process_id=pcap_pid[host_name])
                    pcap_stopped[host_name] = True

            # Setting the syslog level
            command_result = self.storage_controller.poke(props_tree=["params/syslog/level", self.syslog_level],
                                                          legacy=False, command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"],
                                 "Setting syslog level to {}".format(self.syslog_level))

            command_result = self.storage_controller.peek(props_tree="params/syslog/level", legacy=False,
                                                          command_duration=self.command_timeout)
            fun_test.test_assert_expected(expected=self.syslog_level, actual=command_result["data"],
                                          message="Checking syslog level")

            # Executing the FIO command to fill the volume to it's capacity
            if not fun_test.shared_variables["ec"]["warmup_io_completed"] and self.warm_up_traffic:
                if self.parallel_warm_up:
                    host_clone = {}
                    warmup_thread_id = {}
                    actual_block_size = int(self.warm_up_fio_cmd_args["bs"].strip("k"))
                    aligned_block_size = int((int(actual_block_size / self.num_hosts) + 3) / 4) * 4
                    self.warm_up_fio_cmd_args["bs"] = str(aligned_block_size) + "k"
                    for index, host_name in enumerate(self.host_info):
                        wait_time = self.num_hosts - index
                        host_clone[host_name] = self.host_info[host_name]["handle"].clone()
                        warmup_thread_id[index] = fun_test.execute_thread_after(
                            time_in_seconds=wait_time, func=fio_parser, arg1=host_clone[host_name], host_index=index,
                            filename=self.host_info[host_name]["fio_filename"],
                            cpus_allowed=self.host_info[host_name]["host_numa_cpus"], **self.warm_up_fio_cmd_args)

                        fun_test.log("Started FIO command to perform sequential write on {}".format(host_name))
                        fun_test.sleep("to start next thread", 1)

                    fun_test.sleep("Fio threads started", 10)
                    try:
                        for index, host_name in enumerate(self.host_info):
                            fun_test.log("Joining fio thread {}".format(index))
                            fun_test.join_thread(fun_test_thread_id=warmup_thread_id[index], sleep_time=1)
                            fun_test.log("FIO Command Output: \n{}".format(fun_test.shared_variables["fio"][index]))
                    except Exception as ex:
                        fun_test.critical(str(ex))

                    for index, host_name in enumerate(self.host_info):
                        fun_test.test_assert(fun_test.shared_variables["fio"][index], "Volume warmup on host {}".
                                             format(host_name))
                        fun_test.shared_variables["ec"][host_name]["warmup"] = True
                else:
                    for index, host_name in enumerate(self.host_info):
                        host_handle = self.host_info[host_name]["handle"]
                        fio_output = host_handle.pcie_fio(filename=self.host_info[host_name]["fio_filename"],
                                                          cpus_allowed=self.host_info[host_name]["host_numa_cpus"],
                                                          **self.warm_up_fio_cmd_args)
                        fun_test.log("FIO Command Output:\n{}".format(fio_output))
                        fun_test.test_assert(fio_output, "Volume warmup on host {}".format(host_name))

                fun_test.sleep("before actual test", self.iter_interval)
                fun_test.shared_variables["ec"]["warmup_io_completed"] = True

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[4:]

        table_data_headers = ["Num Hosts", "Block Size", "IO Depth", "Size", "Operation", "Write IOPS", "Read IOPS",
                              "Write Throughput in KB/s", "Read Throughput in KB/s", "Write Latency in uSecs",
                              "Write Latency 90 Percentile in uSecs", "Write Latency 95 Percentile in uSecs",
                              "Write Latency 99 Percentile in uSecs", "Write Latency 99.99 Percentile in uSecs",
                              "Read Latency in uSecs", "Read Latency 90 Percentile in uSecs",
                              "Read Latency 95 Percentile in uSecs", "Read Latency 99 Percentile in uSecs",
                              "Read Latency 99.99 Percentile in uSecs", "Plex Rebuild Time in sec", "fio_job_name"]
        table_data_cols = ["num_hosts", "block_size", "iodepth", "size", "mode", "writeiops", "readiops", "writebw",
                           "readbw", "writeclatency", "writelatency90", "writelatency95", "writelatency99",
                           "writelatency9999", "readclatency", "readlatency90", "readlatency95", "readlatency99",
                           "readlatency9999", "plex_rebuild_time", "fio_job_name"]
        table_data_rows = []

        # Checking whether the job's inputs argument is having the list of io_depths to be used in this test.
        # If so, override the script default with the user provided config
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        if "io_depth" in job_inputs:
            self.fio_iodepth = job_inputs["io_depth"]

        if not isinstance(self.fio_iodepth, list):
            self.fio_iodepth = [self.fio_iodepth]

        # Test Preparation
        # Checking whether the ec_info is having the drive and device ID for the EC's plex volumes
        # Else going to extract the same
        if "device_id" not in self.ec_info:
            fun_test.log("Drive and Device ID of the EC volume's plex volumes are not available in the ec_info..."
                         "So going to pull that info")
            self.ec_info["drive_uuid"] = {}
            self.ec_info["device_id"] = {}
            for num in xrange(self.ec_info["num_volumes"]):
                self.ec_info["drive_uuid"][num] = []
                self.ec_info["device_id"][num] = []
                for blt_uuid in self.ec_info["uuids"][num]["blt"]:
                    blt_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LOCAL_THIN",
                                                             blt_uuid, "stats")
                    blt_stats = self.storage_controller.peek(blt_props_tree)
                    fun_test.simple_assert(blt_stats["status"], "Stats of BLT Volume {}".format(blt_uuid))
                    if "drive_uuid" in blt_stats["data"]:
                        self.ec_info["drive_uuid"][num].append(blt_stats["data"]["drive_uuid"])
                    else:
                        fun_test.simple_assert(blt_stats["data"].get("drive_uuid"), "Drive UUID of BLT volume {}".
                                               format(blt_uuid))
                    drive_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LOCAL_THIN",
                                                               "drives", blt_stats["data"]["drive_uuid"])
                    drive_stats = self.storage_controller.peek(drive_props_tree)
                    fun_test.simple_assert(drive_stats["status"], "Stats of the drive {}".
                                           format(blt_stats["data"]["drive_uuid"]))
                    if "drive_id" in drive_stats["data"]:
                        self.ec_info["device_id"][num].append(drive_stats["data"]["drive_id"])
                    else:
                        fun_test.simple_assert(drive_stats["data"].get("drive_id"), "Device ID of the drive {}".
                                               format(blt_stats["data"]["drive_uuid"]))

        fun_test.log("EC plex volumes UUID      : {}".
                     format(self.ec_info["uuids"][self.test_volume_start_index]["blt"]))
        fun_test.log("EC plex volumes drive UUID: {}".
                     format(self.ec_info["drive_uuid"][self.test_volume_start_index]))
        fun_test.log("EC plex volumes device ID : {}".
                     format(self.ec_info["device_id"][self.test_volume_start_index]))

        # Going to run the FIO test for the block size and iodepth combo listed in fio_iodepth
        fio_result = {}
        fio_output = {}
        aggr_fio_output = {}
        initial_stats = {}
        final_stats = {}
        resultant_stats = {}
        aggregate_resultant_stats = {}

        start_stats = True

        for iodepth in self.fio_iodepth:
            fio_result[iodepth] = True
            fio_output[iodepth] = {}
            aggr_fio_output[iodepth] = {}
            fio_job_args = ""
            fio_cmd_args = {}
            mpstat_pid = {}
            mpstat_artifact_file = {}
            iostat_pid = {}
            iostat_artifact_file = {}
            initial_stats[iodepth] = {}
            final_stats[iodepth] = {}
            resultant_stats[iodepth] = {}
            aggregate_resultant_stats[iodepth] = {}

            test_thread_id = {}
            host_clone = {}

            row_data_dict = {}
            size = (self.ec_info["capacity"] * self.ec_info["num_volumes"]) / (1024 ** 3)
            row_data_dict["size"] = str(size) + "G"
            row_data_dict["num_hosts"] = self.num_hosts

            # Deciding whether the fio command has to run for the entire volume size or for a certain period of time,
            # based on if the current IO depth is in self.full_run_iodepth
            if iodepth not in self.full_run_iodepth:
                if "runtime" not in self.fio_cmd_args["multiple_jobs"]:
                    self.fio_cmd_args["multiple_jobs"] += " --time_based --runtime={}".format(self.fio_runtime)
                    self.fio_cmd_args["timeout"] = self.fio_run_timeout
            else:
                self.fio_cmd_args["multiple_jobs"] = re.sub(r"--runtime=\d+", "", self.fio_cmd_args["multiple_jobs"])
                self.fio_cmd_args["multiple_jobs"] = re.sub(r"--time_based", "", self.fio_cmd_args["multiple_jobs"])
                self.fio_cmd_args["timeout"] = self.fio_size_timeout

            # Computing the interval and duration that the mpstat/vp_util stats needs to be collected
            if "runtime" not in self.fio_cmd_args:
                mpstat_count = self.fio_cmd_args["timeout"] / self.mpstat_args["interval"]
                iostat_count = self.fio_cmd_args["timeout"] / self.iostat_args["interval"]
            elif "runtime" in self.fio_cmd_args and "ramp_time" in self.fio_cmd_args:
                mpstat_count = ((self.fio_cmd_args["runtime"] + self.fio_cmd_args["ramp_time"]) /
                                self.mpstat_args["interval"])
                iostat_count = ((self.fio_cmd_args["runtime"] + self.fio_cmd_args["ramp_time"]) /
                                self.iostat_args["interval"])
            elif "multiple_jobs" in self.fio_cmd_args:
                match = re.search("--ramp_time=(\d+).*--runtime=(\d+)|--runtime=(\d+).*--ramp_time=(\d+)",
                                  self.fio_cmd_args["multiple_jobs"])
                if match:
                    if match.group(1) != None:
                        ramp_time = match.group(1)
                    if match.group(2) != None:
                        runtime = match.group(2)
                    if match.group(3) != None:
                        runtime = match.group(3)
                    if match.group(4) != None:
                        ramp_time = match.group(4)
                    mpstat_count = (int(runtime) + int(ramp_time)) / self.mpstat_args["interval"]
                    iostat_count = (int(runtime) + int(ramp_time)) / self.iostat_args["interval"]
                else:
                    start_stats = False
            else:
                start_stats = False

            if "bs" in self.fio_cmd_args:
                fio_block_size = self.fio_cmd_args["bs"]
            elif "multiple_jobs" in self.fio_cmd_args:
                match = re.search("--bs=(\w+)", self.fio_cmd_args["multiple_jobs"])
                if match:
                    fio_block_size = match.group(1)
                else:
                    match = re.search("--bssplit=((\w+/\w+:*)+)", self.fio_cmd_args["multiple_jobs"])
                    if match:
                        fio_block_size = "Mixed"

            if "rw" in self.fio_cmd_args:
                row_data_dict["mode"] = self.fio_cmd_args["rw"]
            elif "multiple_jobs" in self.fio_cmd_args:
                match = re.search("--rw=(\w+)", self.fio_cmd_args["multiple_jobs"])
                if match:
                    row_data_dict["mode"] = match.group(1)
            else:
                row_data_dict["mode"] = "Combined"

            row_data_dict["block_size"] = fio_block_size

            # Collecting initial network stats
            if self.collect_network_stats:
                try:
                    initial_stats[iodepth]["peek_psw_global_stats"] = self.storage_controller.peek_psw_global_stats()
                    initial_stats[iodepth]["peek_vp_packets"] = self.storage_controller.peek_vp_packets()
                    initial_stats[iodepth]["cdu"] = self.storage_controller.peek_cdu_stats()
                    initial_stats[iodepth]["ca"] = self.storage_controller.peek_ca_stats()
                    command_result = self.storage_controller.peek(props_tree="stats/eqm", legacy=False,
                                                                  command_duration=self.command_timeout)
                    # fun_test.test_assert(command_result["status"], "Collecting eqm stats for iodepth {}".format(iodepth))
                    if "status" in command_result and command_result["status"]:
                        initial_stats[iodepth]["eqm_stats"] = command_result["data"]
                    else:
                        initial_stats[iodepth]["eqm_stats"] = {}
                    fun_test.log("\nInitial stats collected for iodepth {} after iteration: \n{}\n".format(
                        iodepth, initial_stats[iodepth]))
                except Exception as ex:
                    fun_test.critical(str(ex))

            # Starting the thread to collect the vp_utils stats and resource_bam stats for the current iteration
            if start_stats:
                stats_obj = CollectStats(self.storage_controller)
                vp_util_post_fix_name = "vp_util_iodepth_{}.txt".format(iodepth)
                vp_util_artifact_file = fun_test.get_test_case_artifact_file_name(post_fix_name=vp_util_post_fix_name)
                stats_thread_id = fun_test.execute_thread_after(time_in_seconds=1,
                                                                func=stats_obj.collect_vp_utils_stats,
                                                                output_file=vp_util_artifact_file,
                                                                interval=self.vp_util_args["interval"],
                                                                count=int(mpstat_count), threaded=True)
                resource_bam_post_fix_name = "resource_bam_iodepth_{}.txt".format(iodepth)
                resource_bam_artifact_file = fun_test.get_test_case_artifact_file_name(
                    post_fix_name=resource_bam_post_fix_name)
                stats_rbam_thread_id = fun_test.execute_thread_after(time_in_seconds=10,
                                                                     func=stats_obj.collect_resource_bam_stats,
                                                                     output_file=resource_bam_artifact_file,
                                                                     interval=self.resource_bam_args["interval"],
                                                                     count=int(mpstat_count), threaded=True)
            else:
                fun_test.critical("Not starting the vp_utils and resource_bam stats collection because of lack of "
                                  "interval and count details")

            for index, host_name in enumerate(self.host_info):
                start_time = time.time()
                fio_job_args = ""
                host_handle = self.host_info[host_name]["handle"]
                nvme_block_device_list = self.host_info[host_name]["nvme_block_device_list"]
                host_numa_cpus = self.host_info[host_name]["host_numa_cpus"]
                total_numa_cpus = self.host_info[host_name]["total_numa_cpus"]
                fio_num_jobs = len(nvme_block_device_list)

                wait_time = self.num_hosts - index
                host_clone[host_name] = self.host_info[host_name]["handle"].clone()

                for vindex, volume_name in enumerate(nvme_block_device_list):
                    fio_job_args += " --name=job{} --filename={}".format(vindex, volume_name)

                if "multiple_jobs" in self.fio_cmd_args and self.fio_cmd_args["multiple_jobs"].count("name") > 0:
                    global_num_jobs = self.fio_cmd_args["multiple_jobs"].count("name")
                    fio_num_jobs = fio_num_jobs / global_num_jobs
                else:
                    if iodepth <= total_numa_cpus:
                        global_num_jobs = iodepth / len(nvme_block_device_list)
                        fio_iodepth = 1
                    else:
                        io_factor = 2
                        while True:
                            if (iodepth / io_factor) <= total_numa_cpus:
                                global_num_jobs = (iodepth / len(nvme_block_device_list)) / io_factor
                                fio_iodepth = io_factor
                                break
                            else:
                                io_factor += 1

                row_data_dict["iodepth"] = int(fio_iodepth) * int(global_num_jobs) * int(fio_num_jobs)

                # Calling the mpstat method to collect the mpstats for the current iteration in all the hosts used in
                # the test
                mpstat_cpu_list = self.mpstat_args["cpu_list"]  # To collect mpstat for all CPU's: recommended
                if start_stats:
                    fun_test.log("Collecting mpstat in {}".format(host_name))
                    mpstat_post_fix_name = "{}_mpstat_iodepth_{}.txt".format(host_name, row_data_dict["iodepth"])
                    mpstat_artifact_file[host_name] = fun_test.get_test_case_artifact_file_name(
                        post_fix_name=mpstat_post_fix_name)
                    mpstat_pid[host_name] = host_handle.mpstat(cpu_list=mpstat_cpu_list,
                                                               output_file=self.mpstat_args["output_file"],
                                                               interval=self.mpstat_args["interval"],
                                                               count=int(mpstat_count))

                    # Calling the iostat method to collect the iostat for the while performing IO (copying file)
                    fun_test.log("Collecting iostat on {}".format(host_name))
                    iostat_post_fix_name = "{}_iostat_iodepth_{}.txt".format(host_name, row_data_dict["iodepth"])
                    iostat_artifact_file[host_name] = fun_test.get_test_case_artifact_file_name(
                        post_fix_name=iostat_post_fix_name)
                    iostat_pid[host_name] = host_handle.iostat(
                        device=",".join(self.host_info[host_name]["nvme_block_device_list"]),
                        output_file=self.iostat_args["output_file"], interval=self.iostat_args["interval"],
                        count=int(iostat_count))
                else:
                    fun_test.critical("Not starting the mpstats & iostat collection because of lack of interval and"
                                      "count details")

                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fun_test.log("Running FIO {} test with the block size: {} and IO depth: {} Num jobs: {} for the EC".
                             format(row_data_dict["mode"], fio_block_size, fio_iodepth, fio_num_jobs * global_num_jobs))
                try:
                    fio_job_name = "{}_iodepth_{}_vol_{}_host_{}_f1_{}".\
                        format(self.fio_job_name, row_data_dict["iodepth"],
                               self.ec_info["num_volumes"], self.num_hosts, self.num_f1s)
                except Exception as ex:
                    fun_test.critical(str(ex))
                fun_test.log("fio_job_name used for current iteration: {}".format(fio_job_name))
                fun_test.log("\nStarting FIO at: {}\n".format(time.ctime()))
                if "multiple_jobs" in self.fio_cmd_args:
                    fio_cmd_args["multiple_jobs"] = self.fio_cmd_args["multiple_jobs"].format(
                        host_numa_cpus, global_num_jobs, fio_iodepth, self.ec_info["capacity"] / global_num_jobs)
                    fio_cmd_args["multiple_jobs"] += fio_job_args
                    fun_test.log("Current FIO args to be used: {}".format(fio_cmd_args))
                    test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                          func=fio_parser,
                                                                          arg1=host_clone[host_name],
                                                                          host_index=index,
                                                                          filename="nofile",
                                                                          timeout=self.fio_cmd_args["timeout"],
                                                                          **fio_cmd_args)
                else:
                    test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                          func=fio_parser,
                                                                          arg1=host_clone[host_name],
                                                                          host_index=index,
                                                                          numjobs=fio_num_jobs,
                                                                          iodepth=fio_iodepth, name=fio_job_name,
                                                                          cpus_allowed=host_numa_cpus,
                                                                          **self.fio_cmd_args)
                end_time = time.time()
                time_taken = end_time - start_time
                fun_test.log("Time taken to start an FIO job on a host {}: {}".format(host_name, time_taken))

            ''' Trigger Plex / Drive failure & Rebuild operation here '''
            # Check whether the drive failure needs to be triggered
            if hasattr(self, "trigger_failure") and self.trigger_failure:
                # Sleep for sometime before triggering the drive failure
                wait_time = self.trigger_failure_wait_time
                '''
                if hasattr(self, "failure_start_time_ratio"):
                    wait_time = int(round(self.fio_cmd_args["timeout"] * self.failure_start_time_ratio))
                '''
                fun_test.sleep(message="Sleeping for {} seconds before inducing a drive failure".format(wait_time),
                               seconds=wait_time)
                # Check whether the drive index to be failed is given or not. If not pick a random one
                if self.failure_mode == "random" or not hasattr(self, "failure_drive_index"):
                    self.failure_drive_index = []
                    for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                        self.failure_drive_index.append(random.randint(0, self.ec_info["ndata"] +
                                                                       self.ec_info["nparity"] - 1))
                # Triggering the drive failure
                for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                    fail_uuid = self.ec_info["uuids"][num]["blt"][self.failure_drive_index[num - self.test_volume_start_index]]
                    fail_device = self.ec_info["device_id"][num][self.failure_drive_index[num - self.test_volume_start_index]]
                    if self.fail_drive:
                        ''' Marking drive as failed '''
                        fun_test.log("Initiating drive failure")
                        device_fail_status = self.storage_controller.disable_device(
                            device_id=fail_device, command_duration=self.command_timeout)
                        fun_test.test_assert(device_fail_status["status"], "Disabling Device ID {}".format(fail_device))
                        # Validate if Device is marked as Failed
                        device_props_tree = "{}/{}/{}/{}/{}".format("storage", "devices", "nvme", "ssds", fail_device)
                        device_stats = self.storage_controller.peek(device_props_tree)
                        fun_test.simple_assert(device_stats["status"], "Device {} stats command".format(fail_device))
                        fun_test.test_assert_expected(expected="DEV_ERR_INJECT_ENABLED",
                                                      actual=device_stats["data"]["device state"],
                                                      message="Device ID {} is marked as Failed".format(fail_device))
                        ''' Marking drive as failed '''
                    else:
                        ''' Marking Plex as failed '''
                        fun_test.log("Initiating Plex failure")
                        volume_fail_status = self.storage_controller.fail_volume(uuid=fail_uuid)
                        fun_test.test_assert(volume_fail_status["status"], "Disabling Plex UUID {}".format(fail_uuid))
                        # Validate if volume is marked as Failed
                        device_props_tree = "{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LOCAL_THIN",
                                                                 fail_uuid)
                        volume_stats = self.storage_controller.peek(device_props_tree)
                        fun_test.test_assert_expected(
                            expected=1, actual=volume_stats["data"]["stats"]["fault_injection"],
                            message="Plex is marked as Failed")
                        ''' Marking Plex as failed '''

                    fun_test.log("\nPlex/Drive Failure is injected at: {}\n".format(time.ctime()))
                    fun_test.sleep("After injecting failure in drive/plex & wait before initiating rebuild",
                                   self.trigger_rebuild_wait_time)
                    if not self.rebuild_on_spare_volume:
                        if self.fail_drive:
                            ''' Marking drive as online '''
                            device_up_status = self.storage_controller.enable_device(
                                device_id=fail_device, command_duration=self.command_timeout)
                            fun_test.test_assert(device_up_status["status"],
                                                 "Enabling Device ID {}".format(fail_device))
                            device_props_tree = "{}/{}/{}/{}/{}".format("storage", "devices", "nvme", "ssds",
                                                                        fail_device)
                            device_stats = self.storage_controller.peek(device_props_tree)
                            fun_test.simple_assert(device_stats["status"],
                                                   "Device {} stats command".format(fail_device))
                            fun_test.test_assert_expected(
                                expected="DEV_ONLINE", actual=device_stats["data"]["device state"],
                                message="Device ID {} is Enabled again".format(fail_device))
                            ''' Marking drive as online '''
                        else:
                            ''' Marking Plex as online '''
                            volume_fail_status = self.storage_controller.fail_volume(uuid=fail_uuid)
                            fun_test.test_assert(volume_fail_status["status"], "Re-enabling Volume UUID {}".
                                                 format(fail_uuid))
                            # Validate if Volume is enabled again
                            device_props_tree = "{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LOCAL_THIN",
                                                                     fail_uuid)
                            volume_stats = self.storage_controller.peek(device_props_tree)
                            fun_test.test_assert_expected(expected=0,
                                                          actual=volume_stats["data"]["stats"]["fault_injection"],
                                                          message="Plex is marked as online")
                            ''' Marking Plex as online '''
                    # Rebuild failed plex
                    if self.rebuild_on_spare_volume:
                        spare_uuid = self.spare_vol_uuid
                        fun_test.log("Rebuilding on spare volume: {}".format(spare_uuid))
                    else:
                        spare_uuid = fail_uuid
                        fun_test.log("Rebuilding on failed volume: {}".format(spare_uuid))
                    rebuild_device = self.storage_controller.plex_rebuild(
                        subcmd="ISSUE", type=self.ec_info["volume_types"]["ec"],
                        uuid=self.ec_info["uuids"][num]["ec"][num - self.test_volume_start_index],
                        failed_uuid=fail_uuid, spare_uuid=spare_uuid, rate=self.rebuild_rate)
                    fun_test.test_assert(rebuild_device["status"], "Rebuilding Plex {}".format(fail_uuid))
                    fun_test.log("\nPlex/Drive Rebuild is started at: {}\n".format(time.ctime()))
            ''' Triggering plex failure and reconstruct'''
            # Waiting for all the FIO test threads to complete
            try:
                fun_test.log("Test Thread IDs: {}".format(test_thread_id))
                for index, host_name in enumerate(self.host_info):
                    fio_output[iodepth][host_name] = {}
                    fun_test.log("Joining fio thread {}".format(index))
                    fun_test.join_thread(fun_test_thread_id=test_thread_id[index], sleep_time=1)
                    fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                           fun_test.shared_variables["fio"][index]))
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                       fun_test.shared_variables["fio"][index]))
            finally:
                # Checking whether the vp_util stats collection thread is still running...If so stopping it...
                if fun_test.fun_test_threads[stats_thread_id]["thread"].is_alive():
                    fun_test.critical("VP utilization stats collection thread is still running...Stopping it now")
                    stats_obj.stop_all = True
                    stats_obj.stop_vp_utils = True
                    # fun_test.fun_test_threads[stats_thread_id]["thread"]._Thread__stop()
                # Checking whether the resource bam stats collection thread is still running...If so stopping it...
                if fun_test.fun_test_threads[stats_rbam_thread_id]["thread"].is_alive():
                    fun_test.critical("Resource bam stats collection thread is still running...Stopping it now")
                    stats_obj.stop_all = True
                    stats_obj.stop_resource_bam = True
                    # fun_test.fun_test_threads[stats_rbam_thread_id]["thread"]._Thread__stop()
                fun_test.join_thread(fun_test_thread_id=stats_thread_id, sleep_time=1)
                fun_test.join_thread(fun_test_thread_id=stats_rbam_thread_id, sleep_time=1)

                # Collecting final network stats and finding diff between final and initial stats
                if self.collect_network_stats:
                    try:
                        final_stats[iodepth]["peek_psw_global_stats"] = self.storage_controller.peek_psw_global_stats()
                        final_stats[iodepth]["peek_vp_packets"] = self.storage_controller.peek_vp_packets()
                        final_stats[iodepth]["cdu"] = self.storage_controller.peek_cdu_stats()
                        final_stats[iodepth]["ca"] = self.storage_controller.peek_ca_stats()
                        command_result = self.storage_controller.peek(props_tree="stats/eqm", legacy=False,
                                                                      command_duration=self.command_timeout)
                        if "status" in command_result and command_result["status"]:
                            final_stats[iodepth]["eqm_stats"] = command_result["data"]
                        else:
                            final_stats[iodepth]["eqm_stats"] = {}
                        fun_test.log("\nFinal stats collected for iodepth {} after IO: \n{}\n".format(
                            iodepth, initial_stats[iodepth]))
                    except Exception as ex:
                        fun_test.critical(str(ex))

                    # Stats diff between final stats and initial stats
                    resultant_stats[iodepth]["peek_psw_global_stats"] = {}
                    if final_stats[iodepth]["peek_psw_global_stats"] and initial_stats[iodepth][
                        "peek_psw_global_stats"]:
                        resultant_stats[iodepth]["peek_psw_global_stats"] = get_diff_stats(
                            new_stats=final_stats[iodepth]["peek_psw_global_stats"],
                            old_stats=initial_stats[iodepth]["peek_psw_global_stats"])
                    fun_test.log("\nStat difference for peek_psw_global_stats at the end iteration for iodepth {} is: "
                                 "\n{}\n".format(iodepth, json.dumps(resultant_stats[iodepth]["peek_psw_global_stats"],
                                                                     indent=2)))

                    resultant_stats[iodepth]["peek_vp_packets"] = {}
                    if final_stats[iodepth]["peek_vp_packets"] and initial_stats[iodepth]["peek_vp_packets"]:
                        resultant_stats[iodepth]["peek_vp_packets"] = get_diff_stats(
                            new_stats=final_stats[iodepth]["peek_vp_packets"],
                            old_stats=initial_stats[iodepth]["peek_vp_packets"])
                    fun_test.log(
                        "\nStat difference for peek_vp_packets at the end iteration for iodepth {} is: \n{}\n".format(
                            iodepth, json.dumps(resultant_stats[iodepth]["peek_vp_packets"], indent=2)))

                    resultant_stats[iodepth]["cdu"] = {}
                    if final_stats[iodepth]["cdu"] and initial_stats[iodepth]["cdu"]:
                        resultant_stats[iodepth]["cdu"] = get_diff_stats(
                            new_stats=final_stats[iodepth]["cdu"], old_stats=initial_stats[iodepth]["cdu"])
                    fun_test.log("\nStat difference for cdu at the end iteration for iodepth {} is: \n{}\n".format(
                        iodepth, json.dumps(resultant_stats[iodepth]["cdu"], indent=2)))

                    resultant_stats[iodepth]["ca"] = {}
                    if final_stats[iodepth]["ca"] and initial_stats[iodepth]["ca"]:
                        resultant_stats[iodepth]["ca"] = get_diff_stats(
                            new_stats=final_stats[iodepth]["ca"], old_stats=initial_stats[iodepth]["ca"])
                    fun_test.log("\nStat difference for ca at the end iteration for iodepth {} is: \n{}\n".format(
                        iodepth, json.dumps(resultant_stats[iodepth]["ca"], indent=2)))

                    resultant_stats[iodepth]["eqm_stats"] = {}
                    if final_stats[iodepth]["eqm_stats"] and initial_stats[iodepth]["eqm_stats"]:
                        resultant_stats[iodepth]["eqm_stats"] = get_diff_stats(
                            new_stats=final_stats[iodepth]["eqm_stats"], old_stats=initial_stats[iodepth]["eqm_stats"])
                    fun_test.log("\nStat difference for eqm_stats at the end iteration for iodepth {}: \n{}\n".format(
                        iodepth, json.dumps(resultant_stats[iodepth]["eqm_stats"], indent=2)))
                    '''
                    aggregate_resultant_stats[iodepth] = get_diff_stats(
                        new_stats=final_stats[iodepth], old_stats=initial_stats[iodepth])
                    fun_test.log("\nAggregate Stats diff: \n{}\n".format(json.dumps(aggregate_resultant_stats[iodepth],
                                                                                    indent=2)))
                    '''

            fun_test.log("\nFIO run is completed at: {}\n".format(time.ctime()))
            # Summing up the FIO stats from all the hosts
            for index, host_name in enumerate(self.host_info):
                fun_test.test_assert(fun_test.shared_variables["fio"][index],
                                     "FIO {} test with the Block Size {} IO depth {} and Numjobs {} on {}"
                                     .format(row_data_dict["mode"], fio_block_size, fio_iodepth,
                                             fio_num_jobs * global_num_jobs, host_name))
                for op, stats in fun_test.shared_variables["fio"][index].items():
                    if op not in aggr_fio_output[iodepth]:
                        aggr_fio_output[iodepth][op] = {}
                    aggr_fio_output[iodepth][op] = Counter(aggr_fio_output[iodepth][op]) + \
                                                   Counter(fun_test.shared_variables["fio"][index][op])

            fun_test.log("Aggregated FIO Command Output:\n{}".format(aggr_fio_output[iodepth]))

            # Parsing f1 uart log file to search rebuild start and finish time
            '''
            log file output:
            [2537.762236 2.2.3] CRIT ecvol "UUID: 98cc5a18ea501fb0 plex: 5 under rebuild total failed:1"
            [2774.291395 2.2.3] ALERT ecvol "storage/flvm/ecvol/ecvol.c:3312:ecvol_rebuild_done_process_push() Rebuild operation complete for plex:5"
            [2774.292149 2.2.3] CRIT ecvol "UUID: 98cc5a18ea501fb0 plex: 5 marked active total failed:0"
            '''
            try:
                bmc_handle = self.fs_obj[0].get_bmc()
                uart_log_file = self.fs_obj[0].get_bmc().get_f1_uart_log_file_name(f1_index=self.f1_in_use)
                # uart_log_file = self.fs_obj[0].get_uart_log_file(f1_index=self.f1_in_use)
                fun_test.log("F1 UART Log file used to check Rebuild operation status: {}".format(uart_log_file))
                search_pattern = "'under rebuild total failed'"
                output = bmc_handle.command("grep -c {} {}".format(search_pattern, uart_log_file,
                                                                   timeout=self.command_timeout))
                fun_test.test_assert_expected(expected=1, actual=int(output.rstrip()),
                                              message="Rebuild operation is started")
                rebuild_start_time = bmc_handle.command("grep {} {} | cut -d ' ' -f 1 | cut -d '[' -f 2".format(
                    search_pattern, uart_log_file, timeout=self.command_timeout))
                rebuild_start_time = int(round(float(rebuild_start_time.rstrip())))
                fun_test.log("Rebuild operation started at : {}".format(rebuild_start_time))

                timer = FunTimer(max_time=self.rebuild_timeout)
                while not timer.is_expired():
                    search_pattern = "'Rebuild operation complete for plex'"
                    fun_test.sleep("Waiting for plex rebuild to complete", seconds=self.status_interval)
                    output = bmc_handle.command("grep -c {} {}".format(search_pattern, uart_log_file,
                                                                       timeout=self.command_timeout))
                    if int(output.rstrip()) == 1:
                        rebuild_stop_time = bmc_handle.command("grep {} {} | cut -d ' ' -f 1 | cut -d '[' -f 2".
                                                               format(search_pattern, uart_log_file,
                                                                      timeout=self.command_timeout))
                        rebuild_stop_time = int(round(float(rebuild_stop_time.rstrip())))
                        fun_test.log("Rebuild operation completed at: {}".format(rebuild_stop_time))
                        fun_test.log("Rebuild operation on plex {} is completed".format(spare_uuid))
                        break
                else:
                    fun_test.test_assert(False, "Rebuild operation on plex {} completed".format(spare_uuid))
                rebuild_time = rebuild_stop_time - rebuild_start_time
                fun_test.log("Time taken to rebuild plex: {}".format(rebuild_time))
                row_data_dict["plex_rebuild_time"] = rebuild_time
            except Exception as ex:
                fun_test.critical(str(ex))

            for op, stats in aggr_fio_output[iodepth].items():
                for field, value in stats.items():
                    if field == "iops":
                        aggr_fio_output[iodepth][op][field] = int(round(value))
                    if field == "bw":
                        # Converting the KBps to MBps
                        aggr_fio_output[iodepth][op][field] = int(round(value / 1000))
                    if "latency" in field:
                        aggr_fio_output[iodepth][op][field] = int(round(value) / self.num_hosts)
                    row_data_dict[op + field] = aggr_fio_output[iodepth][op][field]

            fun_test.log("Processed Aggregated FIO Command Output:\n{}".format(aggr_fio_output[iodepth]))

            if not aggr_fio_output[iodepth]:
                fio_result[iodepth] = False
                fun_test.critical("No output from FIO test, hence moving to the next variation")
                continue

            row_data_dict["fio_job_name"] = fio_job_name

            # Building the table raw for this variation
            row_data_list = []
            for i in table_data_cols:
                if i not in row_data_dict:
                    row_data_list.append(-1)
                else:
                    row_data_list.append(row_data_dict[i])
            table_data_rows.append(row_data_list)
            post_results("Inspur Performance Test", test_method, *row_data_list)

            value_dict = {
                "date_time": self.db_log_time,
                "platform": FunPlatform.F1,
                "version": fun_test.get_version(),
                "num_hosts": self.num_hosts,
                "block_size": row_data_dict["block_size"],
                "operation": row_data_dict["mode"],
                "write_iops": row_data_dict["writeiops"],
                "read_iops": row_data_dict["readiops"],
                "write_throughput": row_data_dict["writebw"],
                "read_throughput": row_data_dict["readbw"],
                "write_avg_latency": row_data_dict["writeclatency"],
                "write_90_latency": row_data_dict["writelatency90"],
                "write_95_latency": row_data_dict["writelatency95"],
                "write_99_99_latency": row_data_dict["writelatency9999"],
                "write_99_latency": row_data_dict["writelatency99"],
                "read_avg_latency": row_data_dict["readclatency"],
                "read_90_latency": row_data_dict["readlatency90"],
                "read_95_latency": row_data_dict["readlatency95"],
                "read_99_99_latency": row_data_dict["readlatency9999"],
                "read_99_latency": row_data_dict["readlatency99"],
                "plex_rebuild_time": row_data_dict["plex_rebuild_time"]
            }
            add_to_data_base(value_dict)

            # Checking if mpstat process is still running...If so killing it...
            for host_name in self.host_info:
                host_handle = self.host_info[host_name]["handle"]
                mpstat_pid_check = host_handle.get_process_id("mpstat")
                if mpstat_pid_check and int(mpstat_pid_check) == int(mpstat_pid[host_name]):
                    host_handle.kill_process(process_id=int(mpstat_pid_check))
                # Saving the mpstat output to the mpstat_artifact_file file
                fun_test.scp(source_port=host_handle.ssh_port, source_username=host_handle.ssh_username,
                             source_password=host_handle.ssh_password, source_ip=host_handle.host_ip,
                             source_file_path=self.mpstat_args["output_file"],
                             target_file_path=mpstat_artifact_file[host_name])
                fun_test.add_auxillary_file(description="Host {} CPU Usage - IO depth {}".
                                            format(host_name, row_data_dict["iodepth"]),
                                            filename=mpstat_artifact_file[host_name])

                # Checking if iostat process is still running...If so killing it...
                iostat_pid_check = host_handle.get_process_id("iostat")
                if iostat_pid_check and int(iostat_pid_check) == int(iostat_pid[host_name]):
                    host_handle.kill_process(process_id=int(iostat_pid_check))
                # Saving the iostat output to the iostat_artifact_file file
                fun_test.scp(source_port=host_handle.ssh_port, source_username=host_handle.ssh_username,
                             source_password=host_handle.ssh_password, source_ip=host_handle.host_ip,
                             source_file_path=self.iostat_args["output_file"],
                             target_file_path=iostat_artifact_file[host_name])
                fun_test.add_auxillary_file(description="Host {} IOStat Usage - IO depth {}".
                                            format(host_name, row_data_dict["iodepth"]),
                                            filename=iostat_artifact_file[host_name])

            fun_test.add_auxillary_file(description="F1 VP Utilization - IO depth {}".format(row_data_dict["iodepth"]),
                                        filename=vp_util_artifact_file)
            fun_test.add_auxillary_file(
                description="F1 Resource bam stats - IO depth {}".format(row_data_dict["iodepth"]),
                filename=resource_bam_artifact_file)

            fun_test.sleep("Waiting in between iterations", self.iter_interval)

        table_data = {"headers": table_data_headers, "rows": table_data_rows}
        fun_test.add_table(panel_header="Performance Table", table_name=self.summary, table_data=table_data)

        # Posting the final status of the test result
        fun_test.log(fio_result)
        test_result = True
        for iodepth in self.fio_iodepth:
            if not fio_result[iodepth]:
                test_result = False

        fun_test.test_assert(test_result, self.summary)

    def cleanup(self):
        pass


class DataReconstructionSingleDiskFailure(DataReconstructOnDiskFailTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Inspur TC 8.7.5: Data reconstruction on single disk fail on EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Reboot network connected host and ensure connectivity with F1
        3. Configure a LSV (on 4:2 EC volume1 on top of the 6 BLT volumes) for performance test
        4. Configure a LSV (on 4:2 EC volume2 on top of the 6 BLT volumes) for plex failure and rebuild test
        5. Configure one more BLT volume to use it as spare volume during rebuild
        6. Export (Attach) the above volume to the Remote Host
        7. Execute nvme-connect from the network host and ensure that the above volume is accessible from the host.
        8. Create EXT3 filesystem in the volume2 and mount the same under /mnt/ssd<volume_num>.
        9. Start performance test (Inspur 8.11.1) on volume1 using FIO
        10. Create test_file_size bytes file and copy it in volume (mount point) and record base file copy time, 
        record and verify md5sum of file before and after copy
        11. Create another test_file_size1 bytes file, record md5sum and copy it in volume (mount point)
        12. While the copy is in progress, simulate plex/drive failure in one of the drives hosting the above 6 BLT 
        volumes, verify file copy succeeds, record the file copy time. Verify md5sum after copy
        13. Create another test_file_size2 bytes file, record md5sum and copy it in volume (mount point)
        14. Instruct EC to use spare volume to rebuild the content of failed drive
        15. Ensure that the file is copied successfully and the md5sum after copy matches.
        16. Re-verify test_file_size1 md5sum
        17. Record reconstruction time
        18. Note down the Performance numbers during Disk/Plex Failure and check for any performance degradation
        """)

    def setup(self):
        super(DataReconstructionSingleDiskFailure, self).setup()

    def run(self):
        super(DataReconstructionSingleDiskFailure, self).run()

    def cleanup(self):
        super(DataReconstructionSingleDiskFailure, self).cleanup()


if __name__ == "__main__":
    ecscript = DataReconstructOnDiskFailScript()
    ecscript.add_test_case(DataReconstructionSingleDiskFailure())
    ecscript.run()
