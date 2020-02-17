from lib.system.fun_test import *
from lib.system import utils
from web.fun_test.analytics_models_helper import ModelHelper, get_data_collection_time
from lib.fun.fs import Fs
import re
import random
from lib.topology.topology_helper import TopologyHelper
from collections import OrderedDict
from scripts.storage.storage_helper import *
from lib.templates.storage.storage_fs_template import *
from fun_global import PerfUnit, FunPlatform
from lib.templates.storage.storage_controller_api import *

'''
Script to test single drive failure scenarios for 4:2 EC config
'''


def fio_parser(arg1, host_index, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    fun_test.shared_variables["fio"][host_index] = fio_output
    fun_test.simple_assert(fio_output, "Fio test for thread {}".format(host_index))
    arg1.disconnect()


def add_to_data_base(value_dict):
    unit_dict = {"base_file_copy_time_unit": PerfUnit.UNIT_SECS, "copy_time_during_plex_fail_unit": PerfUnit.UNIT_SECS,
                 "file_copy_time_during_rebuild_unit": PerfUnit.UNIT_SECS, "plex_rebuild_time_unit": PerfUnit.UNIT_SECS}

    model_name = "InspurSingleDiskFailurePerformance"
    status = fun_test.PASSED
    try:
        generic_helper = ModelHelper(model_name=model_name)
        generic_helper.set_units(validate=True, **unit_dict)
        generic_helper.add_entry(**value_dict)
        generic_helper.set_status(status)
    except Exception as ex:
        fun_test.critical(str(ex))


class ECVolScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Start 1 POSIXs and allocate a Linux instance 
        2. Make the Linux instance available for the testcase
        """)

    def setup(self):
        # Parsing the global config and assign them as object members
        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))
        script_config = utils.parse_file_to_json(config_file)

        if "GlobalSetup" not in script_config or not script_config["GlobalSetup"]:
            fun_test.critical("Global setup config is not available in the {} config file".format(config_file))
            fun_test.log("Going to use the script level defaults")
            self.bootargs = Fs.DEFAULT_BOOT_ARGS
            self.disable_f1_index = None
            self.f1_in_use = 0
            self.syslog = "default"
            self.command_timeout = 5
            self.retries = 24
        else:
            for k, v in script_config["GlobalSetup"].items():
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
        if "already_deployed" in job_inputs:
            self.already_deployed = job_inputs["already_deployed"]

        # Deploying of DUTs
        self.num_duts = int(round(float(self.num_f1s) / self.num_f1_per_fs))
        fun_test.log("Num DUTs for current test: {}".format(self.num_duts))

        # Pulling test bed specific configuration if script is not submitted with testbed-type suite-based
        self.testbed_type = fun_test.get_job_environment_variable("test_bed_type")
        self = single_fs_setup(self)
        # Forming shared variables for defined parameters
        fun_test.shared_variables["topology"] = self.topology
        fun_test.shared_variables["fs_obj"] = self.fs_objs
        fun_test.shared_variables["f1_in_use"] = self.f1_in_use
        fun_test.shared_variables["come_obj"] = self.come_obj
        fun_test.shared_variables["f1_obj"] = self.f1_objs
        fun_test.shared_variables["sc_obj"] = self.sc_objs
        fun_test.shared_variables["f1_ips"] = self.f1_ips
        fun_test.shared_variables["num_f1s"] = self.num_f1s
        fun_test.shared_variables["num_duts"] = self.num_duts
        fun_test.shared_variables["syslog"] = self.syslog
        fun_test.shared_variables["db_log_time"] = self.db_log_time
        fun_test.shared_variables["host_info"] = self.host_info

    def cleanup(self):
        # Cleaning up host
        for host_name in self.host_info:
            host_handle = self.host_info[host_name]["handle"]
            host_cleanup = cleanup_host(host_obj=host_handle)
            host_cleanup = cleanup_host(host_obj=host_handle)
            fun_test.test_assert_expected(expected=True, actual=host_cleanup["nvme_list"],
                                          message="Host {} cleanup: Fetch NVMe list".format(host_name))
            fun_test.test_assert_expected(expected=True, actual=host_cleanup["nvme_disconnect"],
                                          message="Host {} cleanup: NVMe disconnect".format(host_name))
            fun_test.test_assert_expected(expected=True, actual=host_cleanup["load_nvme_modules"],
                                          message="Host {} cleanup: Load NVMe modules".format(host_name))
            fun_test.test_assert_expected(expected=True, actual=host_cleanup["umount"],
                                          message="Host {} cleanup: Umount".format(host_name))
            fun_test.test_assert_expected(expected=True, actual=host_cleanup["unload_nvme_modules"],
                                          message="Host {} cleanup: Unload NVMe modules".format(host_name))
        fun_test.log("Rest is Handled in Test case level cleanup section")


class ECVolumeTestcase(FunTestCase):

    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__
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
        # End of benchmarking json file parsing

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
        if "post_results" in job_inputs:
            self.post_results = job_inputs["post_results"]
        else:
            self.post_results = False
        if "test_bs" in job_inputs:
            self.fio_write_cmd_args["bs"] = job_inputs["test_bs"]
            self.fio_verify_cmd_args["bs"] = job_inputs["test_bs"]

        self.nvme_block_device = self.nvme_device + "0n" + str(self.ns_id)
        self.volume_name = self.nvme_block_device.replace("/dev/", "")
        self.fs_obj = fun_test.shared_variables["fs_obj"]
        self.f1_in_use = fun_test.shared_variables["f1_in_use"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1 = fun_test.shared_variables["f1_obj"][0][0]
        self.storage_controller = fun_test.shared_variables["sc_obj"][0]
        self.f1_ips = fun_test.shared_variables["f1_ips"][0]
        self.host_info = fun_test.shared_variables["host_info"]
        self.num_f1s = fun_test.shared_variables["num_f1s"]
        self.test_network = {}
        self.test_network["f1_loopback_ip"] = self.f1_ips
        self.num_duts = fun_test.shared_variables["num_duts"]
        self.db_log_time = fun_test.shared_variables["db_log_time"]
        self.num_hosts = len(self.host_info)

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

            # Checking if test case is with back-pressure; if so creating additional volume for back-pressure
            if self.back_pressure:
                fun_test.log("Creating Additional EC volume for back-pressure")
                self.ec_info["num_volumes"] += 1

            (ec_config_status, self.ec_info) = self.storage_controller.configure_ec_volume(self.ec_info,
                                                                                           self.command_timeout)
            fun_test.simple_assert(ec_config_status, "Configuring EC/LSV volume")
            fun_test.log("EC details after configuring EC Volume:")
            for k, v in self.ec_info.items():
                fun_test.log("{}: {}".format(k, v))
            self.spare_vol_uuid = []
            if self.rebuild_on_spare_volume:
                num = self.test_volume_start_index
                vtype = "ndata"
                for i in xrange(self.plex_failure_count):
                    spare_vol_uuid = utils.generate_uuid()
                    self.spare_vol_uuid.append(spare_vol_uuid)
                    self.ec_info["uuids"][num][vtype].append(spare_vol_uuid)
                    self.ec_info["uuids"][num]["blt"].append(spare_vol_uuid)
                    command_result = self.storage_controller.create_volume(
                        type=self.ec_info["volume_types"][vtype], capacity=self.ec_info["volume_capacity"][num][vtype],
                        block_size=self.ec_info["volume_block"][vtype], name=vtype + "_" + spare_vol_uuid[-4:],
                        uuid=spare_vol_uuid, group_id=num + 1, command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(
                        command_result["status"], "Creating Spare Volume {} {} {} {} {} bytes volume on DUT instance".
                            format(i, num, vtype, self.ec_info["volume_types"][vtype],
                                   self.ec_info["volume_capacity"][num][vtype]))

                fun_test.log("EC details after configuring Spare plex Volume:")
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

            for host_name in self.host_info:
                fun_test.shared_variables["ec"][host_name] = {}
                host_handle = self.host_info[host_name]["handle"]
                if not fun_test.shared_variables["ec"]["nvme_connect"]:

                    # Checking nvme-connect status
                    if hasattr(self, "nvme_io_queues") and self.nvme_io_queues != 0:
                        nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -i {} -q {}". \
                            format(self.attach_transport.lower(), self.test_network["f1_loopback_ip"],
                                   str(self.transport_port), self.nvme_subsystem, str(self.nvme_io_queues),
                                   self.host_info[host_name]["ip"])
                    else:
                        nvme_connect_cmd = "nvme connect -t {} -a {} -s {} -n {} -q {}". \
                            format(self.attach_transport.lower(), self.test_network["f1_loopback_ip"],
                                   str(self.transport_port), self.nvme_subsystem,
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

                    # Checking that the above created EC volume is visible to the end host after NVME connect
                    volume_pattern = self.nvme_device.replace("/dev/", "") + r"(\d+)n(\d+)"
                    self.host_info[host_name]["nvme_block_device_list"] = []
                    self.host_info[host_name]["volume_name_list"] = []
                    for volume_name in lsblk_output:
                        match = re.search(volume_pattern, volume_name)
                        if match:
                            ctlr_id = match.group(1)
                            ns_id = match.group(2)
                            self.host_info[host_name]["nvme_block_device_list"].append(
                                self.nvme_device + ctlr_id + "n" + ns_id)
                            self.host_info[host_name]["volume_name_list"].append(
                                self.nvme_block_device.replace("/dev/", ""))

                    # Total number of volumes available should be equal to the ec_info["num_volumes"]
                    self.host_info[host_name]["nvme_block_device_list"].sort()
                    self.host_info[host_name]["volume_name_list"].sort()
                    fun_test.test_assert_expected(expected=self.ec_info["num_volumes"],
                                                  actual=len(self.host_info[host_name]["volume_name_list"]),
                                                  message="Number of volumes available")
                    fun_test.shared_variables["host_info"] = self.host_info
                    fun_test.log("Hosts info: {}".format(self.host_info))

            # Stopping the packet capture and Disable the udev daemon which will skew the read stats of the volume
            # during the test
            udev_services = ["systemd-udevd-control.socket", "systemd-udevd-kernel.socket", "systemd-udevd"]
            for host_name in self.host_info:
                host_handle = self.host_info[host_name]["handle"]
                if pcap_started[host_name]:
                    host_handle.tcpdump_capture_stop(process_id=pcap_pid[host_name])
                    pcap_stopped[host_name] = True
                for service in udev_services:
                    service_status = host_handle.systemctl(service_name=service, action="stop")
                    fun_test.test_assert(service_status, "Stopping {} service in host: {}".format(service, host_name))

            # Setting the syslog level
            if self.syslog != "default":
                command_result = self.storage_controller.poke(
                    props_tree=["params/syslog/level", self.syslog],
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

        # Test Preparation
        # Checking whether the ec_info is having the drive and device ID for the EC's plex volumes
        # Else going to extract the same
        self.ec_info = get_plex_device_id(self.ec_info, self.storage_controller)
        fun_test.log(
            "EC plex volumes UUID      : {}".format(self.ec_info["uuids"][self.test_volume_start_index]["blt"]))
        fun_test.log("EC plex volumes drive UUID: {}".format(self.ec_info["drive_uuid"][self.test_volume_start_index]))
        fun_test.log("EC plex volumes device ID : {}".format(self.ec_info["device_id"][self.test_volume_start_index]))

        fun_test.shared_variables["fio"] = {}
        row_data_dict = {}
        row_data_dict["num_hosts"] = self.num_hosts

        for index, host_name in enumerate(self.host_info):
            host_handle = self.host_info[host_name]["handle"]
            nvme_block_device_list = self.host_info[host_name]["nvme_block_device_list"]
            volume_name_list = self.host_info[host_name]["volume_name_list"]

            # Start background load on other volume
            if hasattr(self, "back_pressure") and self.back_pressure:
                try:
                    # Start the fio here to produce the back pressure
                    fio_pid = None
                    check_pid = None
                    self.back_pressure_io["fio_cmd_args"] += "--filename={}". \
                        format(nvme_block_device_list[self.test_volume_start_index - 1])
                    fio_pid = host_handle.start_bg_process(command=self.back_pressure_io["fio_cmd_args"],
                                                           timeout=self.back_pressure_io["timeout"])
                    fun_test.test_assert(expression=fio_pid is not None, message="Back pressure is started")
                    fun_test.sleep("Allowing FIO to warmup", 10)
                    # Re-checking if FIO processes are not died due to any issue
                    check_pid = host_handle.get_process_id(process_name="fio")
                    fun_test.test_assert(expression=check_pid is not None, message="Back pressure is active")
                    fun_test.log("Back pressure is still running pid/s: {}".format(fio_pid))
                except Exception as ex:
                    fun_test.critical(str(ex))

        fio_output = {}
        test_thread_id = {}
        host_clone = {}

        # If FIO block size is not provided by user, setting FIO block size to the stripe length
        if "bs" not in self.fio_write_cmd_args:
            self.fio_write_cmd_args["bs"] = str(self.ec_info["ndata"] * 4) + "k"
            self.fio_verify_cmd_args["bs"] = str(self.ec_info["ndata"] * 4) + "k"

        # Writing first 50% of volume with --verify=md5
        for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
            for index, host_name in enumerate(self.host_info):
                start_time = time.time()
                host_handle = self.host_info[host_name]["handle"]
                nvme_block_device_list = self.host_info[host_name]["nvme_block_device_list"]
                self.fio_write_cmd_args["offset"] = "0%"
                self.fio_write_cmd_args["filename"] = nvme_block_device_list[num]
                wait_time = self.num_hosts - index
                host_clone[host_name] = self.host_info[host_name]["handle"].clone()
                fun_test.log("Running FIO {} test with the block size: {} and IO depth: {} for the EC".
                             format(self.fio_write_cmd_args["rw"], self.fio_write_cmd_args["bs"],
                                    self.fio_write_cmd_args["iodepth"]))

                test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                      func=fio_parser,
                                                                      arg1=host_clone[host_name],
                                                                      host_index=index,
                                                                      name="{}_{}".format(
                                                                          host_name,
                                                                          self.fio_write_cmd_args["rw"]),
                                                                      **self.fio_write_cmd_args)
                end_time = time.time()
                time_taken = end_time - start_time
                fun_test.log("Time taken to start an FIO job on a host {}: {}".format(host_name, time_taken))

        # Triggering drive failure
        if hasattr(self, "trigger_failure") and self.trigger_failure:
            # Sleep for sometime before triggering the drive failure
            wait_time = 20
            fun_test.sleep(message="Sleeping for {} seconds before inducing a drive failure".format(wait_time),
                           seconds=wait_time)
            # Check whether the drive index to be failed is given or not. If not pick a random one
            if self.failure_mode == "random" or not hasattr(self, "failure_drive_index"):
                self.failure_drive_index = []
                for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                    self.failure_drive_index.append(random.sample(
                        xrange(0, self.ec_info["ndata"] + self.ec_info["nparity"] - 1), self.plex_failure_count))
            # Triggering the drive failure
            for i in xrange(self.plex_failure_count):
                for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                    fail_uuid = self.ec_info["uuids"][num]["blt"][
                        self.failure_drive_index[num - self.test_volume_start_index][i]]
                    fail_device = self.ec_info["device_id"][num][
                        self.failure_drive_index[num - self.test_volume_start_index][i]]
                    if self.fail_drive:
                        # ## ''' Marking drive as failed ''' ## #
                        # Inducing failure in drive
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
                        # ## ''' Marking drive as failed ''' ## #
                    else:
                        # ## ''' Marking plex as failed ''' ## #
                        # Inducing failure in one of the Plex of the volume
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
                        # ## ''' Marking plex as failed ''' ## #

        # Waiting for all the FIO test threads to complete
        try:
            fun_test.log("Test Thread IDs: {}".format(test_thread_id))
            for index, host_name in enumerate(self.host_info):
                fio_output[host_name] = {}
                fun_test.log("Joining fio thread {}".format(index))
                fun_test.join_thread(fun_test_thread_id=test_thread_id[index], sleep_time=1)
                fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                       fun_test.shared_variables["fio"][
                                                                           index]))
        except Exception as ex:
            fun_test.critical(str(ex))
            fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                   fun_test.shared_variables["fio"][index]))

        for index, host_name in enumerate(self.host_info):
            fun_test.test_assert(fun_test.shared_variables["fio"][index],
                                 "FIO Mode: {}, BS: {}, Offset: {}, IOdepth: {}, Numjobs: {}, Size: {} on {}"
                                 .format(self.fio_write_cmd_args["rw"], self.fio_write_cmd_args["bs"],
                                         self.fio_write_cmd_args["offset"], self.fio_write_cmd_args["iodepth"],
                                         self.fio_write_cmd_args["numjobs"], self.fio_write_cmd_args["size"],
                                         host_name))
        fun_test.sleep("before starting read with data integrity", 15)
        # Verifying data integrity after Write is complete
        for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
            for index, host_name in enumerate(self.host_info):
                start_time = time.time()
                host_handle = self.host_info[host_name]["handle"]
                nvme_block_device_list = self.host_info[host_name]["nvme_block_device_list"]
                host_clone[host_name] = self.host_info[host_name]["handle"].clone()
                wait_time = self.num_hosts - index
                # Verifying Data Integrity for 50% data written to the volume with --verify=md5
                self.fio_verify_cmd_args["offset"] = "0%"
                self.fio_verify_cmd_args["filename"] = nvme_block_device_list[num]
                fun_test.log("Running FIO {} test with the block size: {} and IO depth: {} for the EC".
                             format(self.fio_verify_cmd_args["rw"], self.fio_verify_cmd_args["bs"],
                                    self.fio_verify_cmd_args["iodepth"]))

                test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                      func=fio_parser,
                                                                      arg1=host_clone[host_name],
                                                                      host_index=index,
                                                                      name="{}_{}".format(host_name,
                                                                                          self.fio_verify_cmd_args[
                                                                                              "rw"]),
                                                                      **self.fio_verify_cmd_args)
                end_time = time.time()
                time_taken = end_time - start_time
                fun_test.log("Time taken to start an FIO job on a host {}: {}".format(host_name, time_taken))

        # Waiting for all the FIO test threads to complete
        try:
            fun_test.log("Test Thread IDs: {}".format(test_thread_id))
            for index, host_name in enumerate(self.host_info):
                fio_output[host_name] = {}
                fun_test.log("Joining fio thread {}".format(index))
                fun_test.join_thread(fun_test_thread_id=test_thread_id[index], sleep_time=1)
                fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                       fun_test.shared_variables["fio"][
                                                                           index]))
        except Exception as ex:
            fun_test.critical(str(ex))
            fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                   fun_test.shared_variables["fio"][index]))
        for index, host_name in enumerate(self.host_info):
            fun_test.test_assert(fun_test.shared_variables["fio"][index],
                                 "FIO Mode: {}, BS: {}, Offset: {}, IOdepth: {}, Numjobs: {}, Size: {} on {}"
                                 .format(self.fio_verify_cmd_args["rw"], self.fio_verify_cmd_args["bs"],
                                         self.fio_verify_cmd_args["offset"], self.fio_verify_cmd_args["iodepth"],
                                         self.fio_verify_cmd_args["numjobs"], self.fio_verify_cmd_args["size"],
                                         host_name))

        fun_test.sleep("before starting write for remaining 50% size", 15)
        # Writing remaining 50% of volume with --verify=md5
        for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
            for index, host_name in enumerate(self.host_info):
                start_time = time.time()
                host_handle = self.host_info[host_name]["handle"]
                host_clone[host_name] = self.host_info[host_name]["handle"].clone()
                nvme_block_device_list = self.host_info[host_name]["nvme_block_device_list"]
                wait_time = self.num_hosts - index
                self.fio_write_cmd_args["offset"] = "50%"
                self.fio_write_cmd_args["filename"] = nvme_block_device_list[num]
                fun_test.log("Running FIO {} test with the block size: {} and IO depth: {} for the EC".
                             format(self.fio_write_cmd_args["rw"], self.fio_write_cmd_args["bs"],
                                    self.fio_write_cmd_args["iodepth"]))

                test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                      func=fio_parser,
                                                                      arg1=host_clone[host_name],
                                                                      host_index=index,
                                                                      name="{}_{}".format(host_name,
                                                                                          self.fio_write_cmd_args[
                                                                                              "rw"]),
                                                                      **self.fio_write_cmd_args)
                end_time = time.time()
                time_taken = end_time - start_time
                fun_test.log("Time taken to start an FIO job on a host {}: {}".format(host_name, time_taken))

        bmc_handle = self.fs_obj[0].get_bmc()
        uart_log_file = self.fs_obj[0].get_bmc().get_f1_uart_log_file_name(f1_index=self.f1_in_use)
        fun_test.log("F1 UART Log file used to check Rebuild operation status: {}".format(uart_log_file))
        rebuild_time = {}
        rebuild_time["start"] = {}
        rebuild_time["complete"] = {}
        rebuild_time["rebuild_time"] = {}

        fun_test.sleep(message="Sleeping for {} seconds before before bringing up the failed device(s) & "
                               "plex rebuild".format(wait_time), seconds=15)
        for i in xrange(self.plex_failure_count):
            for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                fail_uuid = self.ec_info["uuids"][num]["blt"][
                    self.failure_drive_index[num - self.test_volume_start_index][i]]
                fail_device = self.ec_info["device_id"][num][
                    self.failure_drive_index[num - self.test_volume_start_index][i]]

                if not self.rebuild_on_spare_volume:
                    if self.fail_drive:
                        # ## ''' Marking drive as online ''' ## #
                        device_up_status = self.storage_controller.enable_device(device_id=fail_device,
                                                                                 command_duration=self.command_timeout)
                        fun_test.test_assert(device_up_status["status"], "Enabling Device ID {}".format(fail_device))

                        device_props_tree = "{}/{}/{}/{}/{}".format("storage", "devices", "nvme", "ssds", fail_device)
                        device_stats = self.storage_controller.peek(device_props_tree)
                        fun_test.simple_assert(device_stats["status"], "Device {} stats command".format(fail_device))
                        fun_test.test_assert_expected(expected="DEV_ONLINE",
                                                      actual=device_stats["data"]["device state"],
                                                      message="Device ID {} is Enabled again".format(fail_device))
                        # ## ''' Marking drive as online ''' ## #
                    else:
                        # ## ''' Marking plex as online ''' ## #
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
                        # ## ''' Marking plex as online ''' ## #
                # Rebuild failed plex
                if self.rebuild_on_spare_volume:
                    spare_uuid = self.spare_vol_uuid[i]
                    fun_test.log("Rebuilding on spare volume: {}".format(spare_uuid))
                else:
                    spare_uuid = fail_uuid
                    fun_test.log("Rebuilding on failed volume: {}".format(spare_uuid))
                rebuild_device = self.storage_controller.plex_rebuild(
                    subcmd="ISSUE", type=self.ec_info["volume_types"]["ec"],
                    uuid=self.ec_info["uuids"][num]["ec"][num - self.test_volume_start_index],
                    failed_uuid=fail_uuid, spare_uuid=spare_uuid, rate=self.rebuild_rate)
                fun_test.test_assert(rebuild_device["status"], "Rebuild failed Plex {}".format(fail_uuid))
                fun_test.log("Rebuild failed Plex {} status {}".format(fail_uuid, rebuild_device["status"]))

            #  TODO: Bring the plex rebuild time check logic here
            # Parsing f1 uart log file to search rebuild start and finish time
            for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                rebuild_time["start"][num] = {}
                rebuild_time["complete"][num] = {}
                rebuild_time["rebuild_time"][num] = {}
                rebuild_time["start"][num][i] = []
                rebuild_time["complete"][num][i] = []
                rebuild_time["rebuild_time"][num][i] = []
                ec_uuid = self.ec_info["uuids"][num]["ec"][num - self.test_volume_start_index]
                rebuild_start_time = get_plex_operation_time(
                    bmc_linux_handle=bmc_handle, log_file=uart_log_file,
                    ec_uuid=ec_uuid, get_start_time=True, get_plex_number=True, plex_count=self.plex_failure_count,
                    status_interval=self.status_interval * 5)
                fun_test.log("Rebuild start time for EC UUID: {} is: {}".format(ec_uuid, rebuild_start_time))
                fun_test.test_assert(rebuild_start_time["status"], "EC UUID: {} started at: {}".format(
                    ec_uuid, rebuild_start_time))
                rebuild_time["start"][num][i] = rebuild_start_time
                rebuild_completion_time = get_plex_operation_time(
                    bmc_linux_handle=bmc_handle, log_file=uart_log_file, ec_uuid=ec_uuid,
                    get_completion_time=True, plex_number=rebuild_start_time["plex_number"],
                    status_interval=self.status_interval * 5, rebuild_wait_time=self.rebuild_timeout)
                fun_test.log(
                    "Rebuild completion time for EC UUID: {} is: {}".format(ec_uuid, rebuild_completion_time))
                fun_test.test_assert(rebuild_completion_time["status"], "EC UUID: {} completed at: {}".format(
                    ec_uuid, rebuild_completion_time))
                rebuild_time["complete"][num][i] = rebuild_completion_time

                plex_rebuild_time = rebuild_completion_time["time"] - rebuild_start_time["time"]
                fun_test.log("Time taken to rebuild plex: {}".format(plex_rebuild_time))
                fun_test.test_assert(plex_rebuild_time, "EC UUID: {} Rebuild time: {}".format(
                    ec_uuid, plex_rebuild_time))
                row_data_dict["plex_rebuild_time"] = plex_rebuild_time
                rebuild_time["rebuild_time"][num][i] = plex_rebuild_time

        # Waiting for all the FIO test threads to complete
        try:
            fun_test.log("Test Thread IDs: {}".format(test_thread_id))
            for index, host_name in enumerate(self.host_info):
                fio_output[host_name] = {}
                fun_test.log("Joining fio thread {}".format(index))
                fun_test.join_thread(fun_test_thread_id=test_thread_id[index], sleep_time=1)
                fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                       fun_test.shared_variables["fio"][index]))
        except Exception as ex:
            fun_test.critical(str(ex))
            fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                   fun_test.shared_variables["fio"][index]))
        for index, host_name in enumerate(self.host_info):
            fun_test.test_assert(fun_test.shared_variables["fio"][index],
                                 "FIO Mode: {}, BS: {}, Offset: {}, IOdepth: {}, Numjobs: {}, Size: {} on {}"
                                 .format(self.fio_write_cmd_args["rw"], self.fio_write_cmd_args["bs"],
                                         self.fio_write_cmd_args["offset"], self.fio_write_cmd_args["iodepth"],
                                         self.fio_write_cmd_args["numjobs"], self.fio_write_cmd_args["size"],
                                         host_name))

        fun_test.sleep("before starting read with data integrity for remaining 50% size", 15)
        # Verifying data integrity after Write is complete
        for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
            for index, host_name in enumerate(self.host_info):
                start_time = time.time()
                host_handle = self.host_info[host_name]["handle"]
                host_clone[host_name] = self.host_info[host_name]["handle"].clone()
                nvme_block_device_list = self.host_info[host_name]["nvme_block_device_list"]
                wait_time = self.num_hosts - index
                self.fio_verify_cmd_args["offset"] = "50%"
                self.fio_verify_cmd_args["filename"] = nvme_block_device_list[num]
                # Writing 50% of volume with --verify=md5
                fun_test.log("Running FIO {} test with the block size: {} and IO depth: {} for the EC".
                             format(self.fio_verify_cmd_args["rw"], self.fio_verify_cmd_args["bs"],
                                    self.fio_verify_cmd_args["iodepth"]))

                test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                      func=fio_parser,
                                                                      arg1=host_clone[host_name],
                                                                      host_index=index,
                                                                      name="{}_{}".format(host_name,
                                                                                          self.fio_verify_cmd_args[
                                                                                              "rw"]),
                                                                      **self.fio_verify_cmd_args)
                end_time = time.time()
                time_taken = end_time - start_time
                fun_test.log("Time taken to start an FIO job on a host {}: {}".format(host_name, time_taken))

        # Waiting for all the FIO test threads to complete
        try:
            fun_test.log("Test Thread IDs: {}".format(test_thread_id))
            for index, host_name in enumerate(self.host_info):
                fio_output[host_name] = {}
                fun_test.log("Joining fio thread {}".format(index))
                fun_test.join_thread(fun_test_thread_id=test_thread_id[index], sleep_time=1)
                fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                       fun_test.shared_variables["fio"][index]))
        except Exception as ex:
            fun_test.critical(str(ex))
            fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                   fun_test.shared_variables["fio"][index]))
        for index, host_name in enumerate(self.host_info):
            fun_test.test_assert(fun_test.shared_variables["fio"][index],
                                 "FIO Mode: {}, BS: {}, Offset: {}, IOdepth: {}, Numjobs: {}, Size: {} on {}"
                                 .format(self.fio_verify_cmd_args["rw"], self.fio_verify_cmd_args["bs"],
                                         self.fio_verify_cmd_args["offset"], self.fio_verify_cmd_args["iodepth"],
                                         self.fio_verify_cmd_args["numjobs"], self.fio_verify_cmd_args["size"],
                                         host_name))

        # After Data Reconstruction is completed, verifying 100% data integrity
        for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
            for index, host_name in enumerate(self.host_info):
                start_time = time.time()
                host_handle = self.host_info[host_name]["handle"]
                host_clone[host_name] = self.host_info[host_name]["handle"].clone()
                nvme_block_device_list = self.host_info[host_name]["nvme_block_device_list"]
                wait_time = self.num_hosts - index
                self.fio_verify_cmd_args["size"] = "100%"
                self.fio_verify_cmd_args["offset"] = "0%"
                self.fio_verify_cmd_args["filename"] = nvme_block_device_list[num]
                # After Data Reconstruction is completed, verifying 100% data integrity
                fun_test.log("Running FIO {} test with the block size: {} and IO depth: {} for the EC".
                             format(self.fio_verify_cmd_args["rw"], self.fio_verify_cmd_args["bs"],
                                    self.fio_verify_cmd_args["iodepth"]))

                test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                      func=fio_parser,
                                                                      arg1=host_clone[host_name],
                                                                      host_index=index,
                                                                      name="{}_{}".format(host_name,
                                                                                          self.fio_verify_cmd_args[
                                                                                              "rw"]),
                                                                      **self.fio_verify_cmd_args)
                end_time = time.time()
                time_taken = end_time - start_time
                fun_test.log("Time taken to start an FIO job on a host {}: {}".format(host_name, time_taken))

        fun_test.sleep("before starting read with data integrity for whole volume", 15)
        # Waiting for all the FIO test threads to complete
        try:
            fun_test.log("Test Thread IDs: {}".format(test_thread_id))
            for index, host_name in enumerate(self.host_info):
                fio_output[host_name] = {}
                fun_test.log("Joining fio thread {}".format(index))
                fun_test.join_thread(fun_test_thread_id=test_thread_id[index], sleep_time=1)
                fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                       fun_test.shared_variables["fio"][index]))
        except Exception as ex:
            fun_test.critical(str(ex))
            fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                   fun_test.shared_variables["fio"][index]))
        for index, host_name in enumerate(self.host_info):
            fun_test.test_assert(fun_test.shared_variables["fio"][index],
                                 "FIO Mode: {}, BS: {}, Offset: {}, IOdepth: {}, Numjobs: {}, Size: {} on {}"
                                 .format(self.fio_verify_cmd_args["rw"], self.fio_verify_cmd_args["bs"],
                                         self.fio_verify_cmd_args["offset"], self.fio_verify_cmd_args["iodepth"],
                                         self.fio_verify_cmd_args["numjobs"], self.fio_verify_cmd_args["size"],
                                         host_name))

        try:
            if hasattr(self, "back_pressure") and self.back_pressure:
                # Check if back pressure is still running, if yes, stop it
                check_pid = host_handle.get_process_id(process_name="fio")
                if check_pid:
                    fun_test.log("Back pressure is still running, stopping it")
                    host_handle.pkill(process_name="fio")
                    fun_test.log("Back pressure is stopped")
        except Exception as ex:
            fun_test.critical(str(ex))

    def cleanup(self):
        if fun_test.shared_variables["ec"]["setup_created"]:
            # Marking failure injected drive as online
            for i in xrange(self.plex_failure_count):
                for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                    fail_uuid = self.ec_info["uuids"][num]["blt"][
                        self.failure_drive_index[num - self.test_volume_start_index][i]]
                    fail_device = self.ec_info["device_id"][num][
                        self.failure_drive_index[num - self.test_volume_start_index][i]]
                    if self.fail_drive:
                        # ## ''' Marking drive as online ''' ## #
                        device_up_status = self.storage_controller.enable_device(
                            device_id=fail_device, command_duration=self.command_timeout)
                        fun_test.test_assert(device_up_status["status"],
                                             "Enabling Device ID {}".format(fail_device))

                        device_props_tree = "{}/{}/{}/{}/{}".format("storage", "devices", "nvme", "ssds",
                                                                    fail_device)
                        device_stats = self.storage_controller.peek(device_props_tree)
                        fun_test.simple_assert(device_stats["status"],
                                               "Device {} stats command".format(fail_device))
                        fun_test.test_assert_expected(expected="DEV_ONLINE",
                                                      actual=device_stats["data"]["device state"],
                                                      message="Device ID {} is Enabled again".format(fail_device))
                        # ## ''' Marking drive as online ''' ## #

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
                    command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ctrlr_uuid[index],
                                                                               command_duration=self.command_timeout)
                    fun_test.test_assert(command_result["status"], "Deleting Storage Controller {}".
                                         format(self.ctrlr_uuid[index]))

                # Setting setup_created shared variable as False
                fun_test.shared_variables["ec"]["setup_created"] = False
            except Exception as ex:
                fun_test.critical(str(ex))


class ECVolSingleDriveFailRebuild(ECVolumeTestcase, ECVolScript):
    def __init__(self):
        testcase = self.__class__.__name__
        # Start of benchmarking json file parsing and initializing various variables to run this testcase
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        benchmark_dict = utils.parse_file_to_json(benchmark_file)
        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

    def describe(self):
        self.set_test_details(id=1,
                              summary="Data reconstruction of Single Drive Failure in k:m EC volume",
                              test_rail_case_ids=self.test_rail_case_id,
                              steps="""
        1. Bring up F1 in FS1600
        2. Reboot network connected host and ensure connectivity with F1
        3. Configure a LSV (on 4:2 EC volume1 on top of the 6 BLT volumes) for back-pressure (If enabled)
        4. Configure a LSV (on 4:2 EC volume2 on top of the 6 BLT volumes) for actual test
        5. Configure spare BLT volume/s to use it as spare volume during rebuild
        6. Export (Attach) the above volume to the Remote Host
        7. Execute nvme-connect from the network host and ensure that the above volume is accessible from the host.
        8. Perform 50% write on test volume with --verify=md5 option & during write trigger Single Plex failure
        9. After Write is completed, verify data integrity with read mode IO and with --verify=md5
        10. Perform remaining 50% write on test volume with --verify option & during write trigger Rebuild on spare plex
        11. After Write is completed, verify data integrity with read mode IO and with --verify=md5 of write done in #10
        12. After data reconstruction is completed, verify data integrity for 100% volume size
        """)

    def setup(self):
        super(ECVolSingleDriveFailRebuild, self).setup()

    def run(self):
        super(ECVolSingleDriveFailRebuild, self).run()

    def cleanup(self):
        super(ECVolSingleDriveFailRebuild, self).cleanup()


class ECVolmDriveFailRebuild(ECVolumeTestcase, ECVolScript):
    def __init__(self):
        testcase = self.__class__.__name__

        # Start of benchmarking json file parsing and initializing various variables to run this testcase
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        benchmark_dict = utils.parse_file_to_json(benchmark_file)
        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

    def describe(self):
        self.set_test_details(id=2,
                              summary="Data reconstruction of m Drive Failure in k:m EC volume",
                              test_rail_case_ids=self.test_rail_case_id,
                              steps="""
        1. Bring up F1 in FS1600
        2. Reboot network connected host and ensure connectivity with F1
        3. Configure a LSV (on 4:2 EC volume1 on top of the 6 BLT volumes) for back-pressure (If enabled)
        4. Configure a LSV (on 4:2 EC volume2 on top of the 6 BLT volumes) for actual test
        5. Configure spare BLT volume/s to use it as spare volume during rebuild
        6. Export (Attach) the above volume to the Remote Host
        7. Execute nvme-connect from the network host and ensure that the above volume is accessible from the host.
        8. Perform 50% write on test volume with --verify=md5 option & during write trigger m Plex failures
        9. After Write is completed, verify data integrity with read mode IO and with --verify=md5
        10. Perform remaining 50% write on test volume with --verify option & during write trigger Rebuild on spare plex
        11. After Write is completed, verify data integrity with read mode IO and with --verify=md5 of write done in #10
        12. After data reconstruction is completed, verify data integrity for 100% volume size
        """)

    def setup(self):
        super(ECVolmDriveFailRebuild, self).setup()

    def run(self):
        super(ECVolmDriveFailRebuild, self).run()

    def cleanup(self):
        super(ECVolmDriveFailRebuild, self).cleanup()


class ECVolmPlusOneDriveFailRebuild(ECVolumeTestcase, ECVolScript):
    def __init__(self):
        testcase = self.__class__.__name__

        # Start of benchmarking json file parsing and initializing various variables to run this testcase
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        benchmark_dict = utils.parse_file_to_json(benchmark_file)
        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

    def describe(self):
        self.set_test_details(id=3,
                              summary="Data reconstruction of m+1 Drive Failure in k:m EC volume",
                              test_rail_case_ids=self.test_rail_case_id,
                              steps="""
        1. Bring up F1 in FS1600
        2. Reboot network connected host and ensure connectivity with F1
        3. Configure a LSV (on 4:2 EC volume1 on top of the 6 BLT volumes) for back-pressure (If enabled)
        4. Configure a LSV (on 4:2 EC volume2 on top of the 6 BLT volumes) for actual test
        5. Configure spare BLT volume/s to use it as spare volume during rebuild
        6. Export (Attach) the above volume to the Remote Host
        7. Execute nvme-connect from the network host and ensure that the above volume is accessible from the host.
        8. Perform 50% write on test volume with --verify=md5 option & during write trigger m+1 Plex failure
        9. After Write is completed, verify data integrity with read mode IO and with --verify=md5
        10. Perform remaining 50% write on test volume with --verify option & during write trigger Rebuild on spare plex
        11. After Write is completed, verify data integrity with read mode IO and with --verify=md5 of write done in #10
        12. After data reconstruction is completed, verify data integrity for 100% volume size
        """)

    def setup(self):
        super(ECVolmPlusOneDriveFailRebuild, self).setup()

    def run(self):
        super(ECVolmPlusOneDriveFailRebuild, self).run()

    def cleanup(self):
        super(ECVolmPlusOneDriveFailRebuild, self).cleanup()


class ECVolSingleDriveFailReSync(ECVolumeTestcase, ECVolScript):
    def __init__(self):
        testcase = self.__class__.__name__

        # Start of benchmarking json file parsing and initializing various variables to run this testcase
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        benchmark_dict = utils.parse_file_to_json(benchmark_file)
        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

    def describe(self):
        self.set_test_details(id=4,
                              summary="Data reconstruction of Single Drive Failure in k:m EC volume",
                              test_rail_case_ids=self.test_rail_case_id,
                              steps="""
        1. Bring up F1 in FS1600
        2. Reboot network connected host and ensure connectivity with F1
        3. Configure a LSV (on 4:2 EC volume1 on top of the 6 BLT volumes) for back-pressure (If enabled)
        4. Configure a LSV (on 4:2 EC volume2 on top of the 6 BLT volumes) for actual test
        5. -
        6. Export (Attach) the above volume to the Remote Host
        7. Execute nvme-connect from the network host and ensure that the above volume is accessible from the host.
        8. Perform 50% write on test volume with --verify=md5 option & during write trigger Single Plex failure
        9. After Write is completed, verify data integrity with read mode IO and with --verify=md5
        10. Perform remaining 50% write on test volume with --verify option & Recover the failed plex and 
        during write trigger Rebuild on recovered plex
        11. After Write is completed, verify data integrity with read mode IO and with --verify=md5 of write done in #10
        12. After data reconstruction is completed, verify data integrity for 100% volume size
        """)

    def setup(self):
        super(ECVolSingleDriveFailReSync, self).setup()

    def run(self):
        super(ECVolSingleDriveFailReSync, self).run()

    def cleanup(self):
        super(ECVolSingleDriveFailReSync, self).cleanup()


class ECVolmDriveFailReSync(ECVolumeTestcase, ECVolScript):
    def __init__(self):
        testcase = self.__class__.__name__

        # Start of benchmarking json file parsing and initializing various variables to run this testcase
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        benchmark_dict = utils.parse_file_to_json(benchmark_file)
        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

    def describe(self):
        self.set_test_details(id=5,
                              summary="Data reconstruction of m Drive Failure in k:m EC volume",
                              test_rail_case_ids=self.test_rail_case_id,
                              steps="""
        1. Bring up F1 in FS1600
        2. Reboot network connected host and ensure connectivity with F1
        3. Configure a LSV (on 4:2 EC volume1 on top of the 6 BLT volumes) for back-pressure (If enabled)
        4. Configure a LSV (on 4:2 EC volume2 on top of the 6 BLT volumes) for actual test
        5. -
        6. Export (Attach) the above volume to the Remote Host
        7. Execute nvme-connect from the network host and ensure that the above volume is accessible from the host.
        8. Perform 50% write on test volume with --verify=md5 option & during write trigger m Plex failures
        9. After Write is completed, verify data integrity with read mode IO and with --verify=md5
        10. Perform remaining 50% write on test volume with --verify option  & Recover the failed plex and 
        during write trigger Rebuild on recovered plex
        11. After Write is completed, verify data integrity with read mode IO and with --verify=md5 of write done in #10
        12. After data reconstruction is completed, verify data integrity for 100% volume size
        """)

    def setup(self):
        super(ECVolmDriveFailReSync, self).setup()

    def run(self):
        super(ECVolmDriveFailReSync, self).run()

    def cleanup(self):
        super(ECVolmDriveFailReSync, self).cleanup()


class ECVolmPlusOneDriveFailReSync(ECVolumeTestcase, ECVolScript):
    def __init__(self):
        testcase = self.__class__.__name__

        # Start of benchmarking json file parsing and initializing various variables to run this testcase
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        benchmark_dict = utils.parse_file_to_json(benchmark_file)
        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

    def describe(self):
        self.set_test_details(id=6,
                              summary="Data reconstruction of m+1 Drive Failure in k:m EC volume",
                              test_rail_case_ids=self.test_rail_case_id,
                              steps="""
        1. Bring up F1 in FS1600
        2. Reboot network connected host and ensure connectivity with F1
        3. Configure a LSV (on 4:2 EC volume1 on top of the 6 BLT volumes) for back-pressure (If enabled)
        4. Configure a LSV (on 4:2 EC volume2 on top of the 6 BLT volumes) for actual test
        5. -
        6. Export (Attach) the above volume to the Remote Host
        7. Execute nvme-connect from the network host and ensure that the above volume is accessible from the host.
        8. Perform 50% write on test volume with --verify=md5 option & during write trigger m+1 Plex failure
        9. After Write is completed, verify data integrity with read mode IO and with --verify=md5
        10. Perform remaining 50% write on test volume with --verify option  & Recover the failed plex and 
        during write trigger Rebuild on recovered plex
        11. After Write is completed, verify data integrity with read mode IO and with --verify=md5 of write done in #10
        12. After data reconstruction is completed, verify data integrity for 100% volume size
        """)

    def setup(self):
        super(ECVolmPlusOneDriveFailReSync, self).setup()

    def run(self):
        super(ECVolmPlusOneDriveFailReSync, self).run()

    def cleanup(self):
        super(ECVolmPlusOneDriveFailReSync, self).cleanup()


class ECVolSingleDriveFailRebuildMultiWriter(ECVolumeTestcase):
    def __init__(self):
        super(ECVolSingleDriveFailRebuildMultiWriter, self).__init__()
        testcase = self.__class__.__name__
        # Start of benchmarking json file parsing and initializing various variables to run this testcase
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        benchmark_dict = utils.parse_file_to_json(benchmark_file)
        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

    def describe(self):
        self.set_test_details(id=7,
                              summary="Data reconstruction of Single Drive Failure in k:m EC volume",
                              test_rail_case_ids=self.test_rail_case_id,
                              steps="""
        1. Bring up F1 in FS1600
        2. Reboot network connected host and ensure connectivity with F1
        3. Configure a LSV (on 4:2 EC volume1 on top of the 6 BLT volumes) for back-pressure (If enabled)
        4. Configure a LSV (on 4:2 EC volume2 on top of the 6 BLT volumes) for actual test
        5. Configure spare BLT volume/s to use it as spare volume during rebuild
        6. Export (Attach) the above volume to the Remote Host
        7. Execute nvme-connect from the network host and ensure that the above volume is accessible from the host.
        8. Perform 50% write with multiple threads (FIO numjobs > 1) on test volume with --verify=md5 option & during 
        write trigger Single Plex failure
        9. After Write is completed, verify data integrity with read mode IO and with --verify=md5
        10. Perform remaining 50% write (FIO numjobs > 1) on test volume with --verify option & during write trigger
        Rebuild on spare plex
        11. After Write is completed, verify data integrity with read mode IO and with --verify=md5 of write done in #10
        12. After data reconstruction is completed, verify data integrity for 100% volume size
        """)

    def setup(self):
        super(ECVolSingleDriveFailRebuildMultiWriter, self).setup()

    def run(self):
        super(ECVolSingleDriveFailRebuildMultiWriter, self).run()

    def cleanup(self):
        super(ECVolSingleDriveFailRebuildMultiWriter, self).cleanup()


if __name__ == "__main__":
    ecscript = ECVolScript()
    ecscript.add_test_case(ECVolSingleDriveFailRebuild())
    ecscript.add_test_case(ECVolmDriveFailRebuild())
    ecscript.add_test_case(ECVolmPlusOneDriveFailRebuild())
    ecscript.add_test_case(ECVolSingleDriveFailReSync())
    ecscript.add_test_case(ECVolmDriveFailReSync())
    ecscript.add_test_case(ECVolmPlusOneDriveFailReSync())
    ecscript.add_test_case(ECVolSingleDriveFailRebuildMultiWriter())
    ecscript.run()
