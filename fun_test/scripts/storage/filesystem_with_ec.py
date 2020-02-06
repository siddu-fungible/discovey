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
from lib.templates.storage.storage_controller_api import *

'''
Script to test single drive failure scenarios for 4:2 EC config
'''


def fio_parser(arg1, host_index, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    fun_test.shared_variables["fio"][host_index] = fio_output
    fun_test.simple_assert(fio_output, "Fio test for thread {}".format(host_index))
    arg1.disconnect()


class DurableVolScript(FunTestScript):
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
        fun_test.shared_variables["ip_cfg"] = False

    def cleanup(self):
        fun_test.log("Handled in Test case level cleanup section")


class DurableVolumeTestcase(FunTestCase):

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
        '''
        # As ec_info is being modified with new key additions, retaining the pervious case info
        if "ec" in fun_test.shared_variables:
            fun_test.log("Overriding EC info from existing shared variables")
            self.ec_info = fun_test.shared_variables["ec_info"]
        '''

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

            if not fun_test.shared_variables["ip_cfg"]:
                command_result = self.storage_controller.ip_cfg(ip=self.test_network["f1_loopback_ip"])
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "ip_cfg configured on DUT instance")
                fun_test.shared_variables["ip_cfg"] = True

            # Checking if test case is with back-pressure; if so creating additional volume for back-pressure
            if hasattr(self, "back_pressure") and self.back_pressure:
                fun_test.log("Creating Additional EC volume for back-pressure")
                self.ec_info["num_volumes"] += 1

            (ec_config_status, self.ec_info) = self.storage_controller.configure_ec_volume(self.ec_info,
                                                                                           self.command_timeout)
            fun_test.simple_assert(ec_config_status, "Configuring EC/LSV volume")
            fun_test.log("EC details after configuring EC Volume:")
            for k, v in self.ec_info.items():
                fun_test.log("{}: {}".format(k, v))
            self.spare_vol_uuid = []

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

                    nvme_disk = fetch_nvme_list(host_obj=host_handle)
                    temp_nvme_list = nvme_disk["nvme_device"].split(":")
                    temp_filesys_list = self.filesystem_list

                    # If filesystem size is less then expand it based on first filesystem
                    if len(temp_filesys_list) < len(temp_nvme_list):
                        temp_filesys_list = [temp_filesys_list[0]] * len(temp_nvme_list)

                    # Map filesystem to a disk
                    nvme_disk_dict = dict(zip(temp_nvme_list, temp_filesys_list))

                    host_handle.sudo_command("rm -rf /tmp/mount_point*")
                    mount_path = "/tmp/mount_point_"
                    # Format the disk, create a mount point and mount it
                    test_file = []
                    path_list = []
                    for vol_name, filesys_name in nvme_disk_dict.items():
                        count = 1
                        command_result = host_handle.create_filesystem(fs_type=filesys_name, device=vol_name)
                        fun_test.simple_assert(command_result, "{} : Format on {} with type {}".
                                               format(host_name, vol_name, filesys_name))
                        dir_name = mount_path + str(count)
                        command_result = host_handle.create_directory(dir_name="{}{}".format(mount_path, count))
                        fun_test.simple_assert(command_result, "{} : Mount point {} creation".
                                               format(host_name, count))
                        command_result = host_handle.mount_volume(volume=vol_name, directory=dir_name)
                        fun_test.simple_assert(command_result, "{} : Mount of disk {} to dir {}".
                                               format(host_name, vol_name, dir_name))
                        path_list.append("/tmp/mount_point_{}".format(count))
                        test_file.append("/tmp/mount_point_{}/testfile.dat".format(count))
                        count += 1
                    self.nvme_test_file = test_file
                    # self.nvme_test_file = str(":".join(test_file))
                    self.host_info[host_name]["nvme_test_file"] = self.nvme_test_file
                    self.host_info[host_name]["nvme_mount_path"] = path_list

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
        test_method = testcase[4:]

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
                    blt_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LOCAL_THIN", blt_uuid,
                                                             "stats")
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

        fio_output = {}
        test_thread_id = {}
        host_clone = {}

        initial_vol_stats = {}
        initial_vol_stats["blt"] = {}
        initial_vol_stats["ec"] = {}
        for blt_uuid in self.ec_info["uuids"][num]["blt"]:
            blt_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LOCAL_THIN", blt_uuid, "stats")
            initial_vol_stats["blt"][blt_uuid] = self.storage_controller.peek(blt_props_tree)
        ec_uuid = self.ec_info["uuids"][num]["ec"][0]
        ec_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_EC",
                                                ec_uuid, "stats")
        initial_vol_stats["ec"][ec_uuid] = self.storage_controller.peek(ec_props_tree)

        # Writing the disk with a pattern from a file and use same for read operation
        for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
            for index, host_name in enumerate(self.host_info):
                start_time = time.time()
                host_handle = self.host_info[host_name]["handle"]
                nvme_test_file = self.host_info[host_name]["nvme_test_file"]
                self.fio_write_cmd_args["filename"] = nvme_test_file[num]
                wait_time = self.num_hosts - index
                # Generate a file which will be used for write & read. __NOT__ using binary file
                host_handle.sudo_command("rm -rf  /tmp/writefile.txt && "
                                         "dd if=/dev/urandom bs=1MB count=1 | base64 > /tmp/writefile.txt")
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
                                                                      buffer_pattern="\\\'/tmp/writefile.txt\\\'",
                                                                      **self.fio_write_cmd_args)
                end_time = time.time()
                time_taken = end_time - start_time
                fun_test.log("Time taken to start an FIO job on a host {}: {}".format(host_name, time_taken))

        fun_test.sleep("Waiting for fio to start", 10)
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
                                 "FIO Mode: {}, BS: {}, IOdepth: {}, Numjobs: {}, Size: {} on {}"
                                 .format(self.fio_write_cmd_args["rw"], self.fio_write_cmd_args["bs"],
                                         self.fio_write_cmd_args["iodepth"],
                                         self.fio_write_cmd_args["numjobs"], self.fio_write_cmd_args["size"],
                                         host_name))
        fun_test.sleep("Before starting read with data integrity")

        initial_write_blt_vol_stats = {}
        for blt_uuid in self.ec_info["uuids"][num]["blt"]:
            blt_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LOCAL_THIN", blt_uuid, "stats")
            initial_write_blt_vol_stats[blt_uuid] = self.storage_controller.peek(blt_props_tree)
        initial_write_ec_vol_stats = self.storage_controller.peek(ec_props_tree)

        # Diff after initial write
        for blt_uuid in self.ec_info["uuids"][num]["blt"]:
            diff_write_stats = initial_write_blt_vol_stats[blt_uuid]["data"]["num_writes"] - initial_vol_stats["blt"][blt_uuid]["data"]["num_writes"]
            diff_read_stats = initial_write_blt_vol_stats[blt_uuid]["data"]["num_reads"] - initial_vol_stats["blt"][blt_uuid]["data"]["num_reads"]
            fun_test.log("BLT {} write diff : {}".format(blt_uuid, diff_write_stats))
            fun_test.log("BLT {} read diff : {}".format(blt_uuid, diff_read_stats))

        diff_write_stats = initial_write_ec_vol_stats["data"]["num_writes"] - initial_vol_stats["ec"][ec_uuid]["data"]["num_writes"]
        diff_read_stats = initial_write_ec_vol_stats["data"]["num_reads"] - initial_vol_stats["ec"][ec_uuid]["data"]["num_reads"]
        fun_test.log("EC {} write diff : {}".format(ec_uuid, diff_write_stats))
        fun_test.log("EC {} read diff : {}".format(ec_uuid, diff_read_stats))

        # Read once write is complete
        for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
            for index, host_name in enumerate(self.host_info):
                start_time = time.time()
                host_handle = self.host_info[host_name]["handle"]
                nvme_test_file = self.host_info[host_name]["nvme_test_file"]
                self.fio_verify_cmd_args["filename"] = nvme_test_file[num]
                wait_time = self.num_hosts - index
                host_clone[host_name] = self.host_info[host_name]["handle"].clone()
                fun_test.log("Running FIO {} test with the block size: {} and IO depth: {} for the EC".
                             format(self.fio_verify_cmd_args["rw"], self.fio_verify_cmd_args["bs"],
                                    self.fio_verify_cmd_args["iodepth"]))

                test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                      func=fio_parser,
                                                                      arg1=host_clone[host_name],
                                                                      host_index=index,
                                                                      name="{}_{}".format(
                                                                          host_name,
                                                                          self.fio_verify_cmd_args["rw"]),
                                                                      verify_pattern="\\\'/tmp/writefile.txt\\\'",
                                                                      **self.fio_verify_cmd_args)
                end_time = time.time()
                time_taken = end_time - start_time
                fun_test.log("Time taken to start an FIO job on a host {}: {}".format(host_name, time_taken))

        fun_test.sleep("Waiting for fio to start", 10)
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
                                 "FIO Mode: {}, BS: {}, IOdepth: {}, Numjobs: {}, Size: {} on {}"
                                 .format(self.fio_verify_cmd_args["rw"], self.fio_verify_cmd_args["bs"],
                                         self.fio_verify_cmd_args["iodepth"],
                                         self.fio_verify_cmd_args["numjobs"], self.fio_verify_cmd_args["size"],
                                         host_name))

        initial_read_blt_vol_stats = {}
        for blt_uuid in self.ec_info["uuids"][num]["blt"]:
            blt_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LOCAL_THIN", blt_uuid, "stats")
            initial_read_blt_vol_stats[blt_uuid] = self.storage_controller.peek(blt_props_tree)

        if hasattr(self, "trigger_failure") and self.trigger_failure:
            wait_time = 10
            # Check whether the drive index to be failed is given or not. If not pick a random one
            if self.failure_mode == "random" or not hasattr(self, "failure_drive_index"):
                self.failure_drive_index = []
                for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                    self.failure_drive_index.append(random.sample(
                        xrange(0, self.ec_info["ndata"] + self.ec_info["nparity"] - 1), self.plex_failure_count))
            # Triggering the drive failure
            if hasattr(self, "fail_all") and self.fail_all:
                for i in xrange(self.plex_failure_count):
                    for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                        fail_device = self.ec_info["device_id"][num][
                            self.failure_drive_index[num - self.test_volume_start_index][i]]
                        # ## ''' Marking drive as off ''' ## #
                        fun_test.log("Initiating drive power off")
                        device_fail_status = self.storage_controller.power_toggle_ssd(
                            device_id=fail_device, action="off", command_duration=self.command_timeout)
                        fun_test.test_assert(device_fail_status["status"], "PowerOff drive on slot {}".
                                             format(fail_device))
                        # Validate if Device is marked as Failed
                        device_props_tree = "{}/{}/{}/{}/{}".format("storage", "devices", "nvme", "ssds", fail_device)
                        device_stats = self.storage_controller.peek(device_props_tree)
                        fun_test.simple_assert(not device_stats["status"], "Drive on slot {} not offline".
                                               format(fail_device))
                        # ## ''' Marking drive as off ''' ## #

                # Verifying data integrity after drive power off
                for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                    for index, host_name in enumerate(self.host_info):
                        start_time = time.time()
                        host_handle = self.host_info[host_name]["handle"]
                        nvme_test_file = self.host_info[host_name]["nvme_test_file"]
                        self.fio_verify_cmd_args["filename"] = nvme_test_file[num]
                        host_clone[host_name] = self.host_info[host_name]["handle"].clone()
                        wait_time = self.num_hosts - index
                        # Verifying Data Integrity against the file used for input
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
                                                                              verify_pattern="\\\'/tmp/writefile.txt\\\'",
                                                                              **self.fio_verify_cmd_args)
                        end_time = time.time()
                        time_taken = end_time - start_time
                        fun_test.log("Time taken to start an FIO job on a host {}: {}".
                                     format(host_name, time_taken))
                fun_test.sleep("Waiting for fio to start", 10)
                # Waiting for all the FIO test threads to complete
                try:
                    fun_test.log("Test Thread IDs: {}".format(test_thread_id))
                    for index, host_name in enumerate(self.host_info):
                        fio_output[host_name] = {}
                        fun_test.log("Joining fio thread {}".format(index))
                        fun_test.join_thread(fun_test_thread_id=test_thread_id[index], sleep_time=1)
                        fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                               fun_test.shared_variables[
                                                                                   "fio"][
                                                                                   index]))
                except Exception as ex:
                    fun_test.critical(str(ex))
                    fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                           fun_test.shared_variables[
                                                                               "fio"][index]))
                for index, host_name in enumerate(self.host_info):
                    fun_test.test_assert(fun_test.shared_variables["fio"][index],
                                         "FIO Mode: {}, BS: {}, IOdepth: {}, Numjobs: {}, "
                                         "Size: {} on {}"
                                         .format(self.fio_verify_cmd_args["rw"],
                                                 self.fio_verify_cmd_args["bs"],
                                                 self.fio_verify_cmd_args["iodepth"],
                                                 self.fio_verify_cmd_args["numjobs"],
                                                 self.fio_verify_cmd_args["size"],
                                                 host_name))
            else:
                for i in xrange(self.plex_failure_count):
                    for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                        fail_device = self.ec_info["device_id"][num][
                            self.failure_drive_index[num - self.test_volume_start_index][i]]
                        fun_test.log("Initiating drive power off")
                        device_fail_status = self.storage_controller.power_toggle_ssd(
                            device_id=fail_device, action="off", command_duration=self.command_timeout)
                        fun_test.test_assert(device_fail_status["status"], "PowerOff drive on slot {}".
                                             format(fail_device))
                        # Validate if Device is marked as Failed
                        device_power_status = self.storage_controller.get_ssd_power_status(device_id=fail_device,
                                                                                           command_duration=self.command_timeout)
                        fun_test.simple_assert(device_power_status["status"], "Got power status for device {}".
                                               format(fail_device))
                        device_props_tree = "{}/{}/{}/{}/{}".format("storage", "devices", "nvme", "ssds", fail_device)
                        device_stats = self.storage_controller.peek(device_props_tree)
                        fun_test.simple_assert(not device_stats["status"], "Drive on slot {} not offline".
                                               format(fail_device))

                        # Verifying data integrity after each drive is powered off
                        for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                            for index, host_name in enumerate(self.host_info):
                                start_time = time.time()
                                host_handle = self.host_info[host_name]["handle"]
                                nvme_test_file = self.host_info[host_name]["nvme_test_file"]
                                self.fio_verify_cmd_args["filename"] = nvme_test_file[num]
                                host_clone[host_name] = self.host_info[host_name]["handle"].clone()
                                wait_time = self.num_hosts - index
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
                                                                                      verify_pattern="\\\'/tmp/writefile.txt\\\'",
                                                                                      **self.fio_verify_cmd_args)
                                end_time = time.time()
                                time_taken = end_time - start_time
                                fun_test.log("Time taken to start an FIO job on a host {}: {}".
                                             format(host_name, time_taken))

                        fun_test.sleep("Waiting for fio to start", 10)
                        # Waiting for all the FIO test threads to complete
                        try:
                            fun_test.log("Test Thread IDs: {}".format(test_thread_id))
                            for index, host_name in enumerate(self.host_info):
                                fio_output[host_name] = {}
                                fun_test.log("Joining fio thread {}".format(index))
                                fun_test.join_thread(fun_test_thread_id=test_thread_id[index], sleep_time=1)
                                fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                                       fun_test.shared_variables[
                                                                                           "fio"][index]))
                        except Exception as ex:
                            fun_test.critical(str(ex))
                            fun_test.log("FIO Command Output from {}:\n {}".format(host_name,
                                                                                   fun_test.shared_variables[
                                                                                       "fio"][index]))
                        for index, host_name in enumerate(self.host_info):
                            fun_test.test_assert(fun_test.shared_variables["fio"][index],
                                                 "FIO Mode: {}, BS: {}, IOdepth: {}, Numjobs: {}, "
                                                 "Size: {} on {}"
                                                 .format(self.fio_verify_cmd_args["rw"],
                                                         self.fio_verify_cmd_args["bs"],
                                                         self.fio_verify_cmd_args["iodepth"],
                                                         self.fio_verify_cmd_args["numjobs"],
                                                         self.fio_verify_cmd_args["size"],
                                                         host_name))

    def cleanup(self):
        if fun_test.shared_variables["ec"]["setup_created"]:
            # Power on all drives
            if hasattr(self, "fail_driver") and self.fail_drive:
                for i in xrange(self.plex_failure_count):
                    for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                        fail_device = self.ec_info["device_id"][num][
                            self.failure_drive_index[num - self.test_volume_start_index][i]]
                        if self.fail_drive:
                            device_up_status = self.storage_controller.power_toggle_ssd(
                                device_id=fail_device, action="on", command_duration=self.command_timeout)
                            fun_test.test_assert(device_up_status["status"],
                                                 "PowerOn Device ID {}".format(fail_device))

                            device_props_tree = "{}/{}/{}/{}/{}".format("storage", "devices", "nvme", "ssds",
                                                                        fail_device)
                            device_stats = self.storage_controller.peek(device_props_tree)
                            fun_test.simple_assert(not device_stats["status"], "Device {} not offline".
                                                   format(fail_device))
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

                # # Unmount all nvme disks on host & execute NVMe disconnect from all the hosts
                nvme_disconnect_cmd = "nvme disconnect -n {}".format(self.nvme_subsystem)
                for host_name in self.host_info:
                    host_handle = self.host_info[host_name]["handle"]
                    for mount_path in self.host_info[host_name]["nvme_mount_path"]:
                        command_result = host_handle.unmount_volume(directory=mount_path)
                        fun_test.simple_assert(command_result, "Unmount of {} on {}".format(mount_path, host_name))
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


class C18013(DurableVolumeTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Creating a Linux file system - EXT4 on volume",
                              test_rail_case_ids=["C18013"],
                              steps="""
        1. Bring up F1 in FS1600
        2. Reboot network connected host and ensure connectivity with F1        
        3. Configure a LSV (on 4:2 EC volume2 on top of the 6 BLT volumes) for actual test        
        4. Export (Attach) the above volume to the Remote Host
        5. Execute nvme-connect from the network host and ensure that the above volume is accessible from the host.
        6. Create a EXT4 filesystem on the volume
        7. Create a 1MB data file and write a file with buffern pattern from data file
        8. After Write is completed, fail one of the plex.
        9. Perform read operation now using the data file for pattern match
        """)


class C18372(DurableVolumeTestcase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Creating a Linux file system - EXT3 on volume",
                              test_rail_case_ids=["C18372"],
                              steps="""
        1. Bring up F1 in FS1600
        2. Reboot network connected host and ensure connectivity with F1        
        3. Configure a LSV (on 4:2 EC volume2 on top of the 6 BLT volumes) for actual test        
        4. Export (Attach) the above volume to the Remote Host
        5. Execute nvme-connect from the network host and ensure that the above volume is accessible from the host.
        6. Create a EXT3 filesystem on the volume
        7. Create a 1MB data file and write a file with buffern pattern from data file
        8. After Write is completed, fail one of the plex.
        9. Perform read operation now using the data file for pattern match
        """)


class C18373(DurableVolumeTestcase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Creating a Linux file system - EXT2 on volume",
                              test_rail_case_ids=["C18373"],
                              steps="""
        1. Bring up F1 in FS1600
        2. Reboot network connected host and ensure connectivity with F1        
        3. Configure a LSV (on 4:2 EC volume2 on top of the 6 BLT volumes) for actual test        
        4. Export (Attach) the above volume to the Remote Host
        5. Execute nvme-connect from the network host and ensure that the above volume is accessible from the host.
        6. Create a EXT4 filesystem on the volume
        7. Create a 1MB data file and write a file with buffern pattern from data file
        8. After Write is completed, fail one of the plex.
        9. Perform read operation now using the data file for pattern match
        """)


class C18374(DurableVolumeTestcase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Creating a Linux file system - XFS on volume",
                              test_rail_case_ids=["C18374"],
                              steps="""
        1. Bring up F1 in FS1600
        2. Reboot network connected host and ensure connectivity with F1        
        3. Configure a LSV (on 4:2 EC volume2 on top of the 6 BLT volumes) for actual test        
        4. Export (Attach) the above volume to the Remote Host
        5. Execute nvme-connect from the network host and ensure that the above volume is accessible from the host.
        6. Create a XFS filesystem on the volume
        7. Create a 1MB data file and write a file with buffern pattern from data file
        8. After Write is completed, fail one of the plex.
        9. Perform read operation now using the data file for pattern match
        """)


class C18375(DurableVolumeTestcase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Creating a Linux file system - BTRFS on volume",
                              test_rail_case_ids=["C18375"],
                              steps="""
        1. Bring up F1 in FS1600
        2. Reboot network connected host and ensure connectivity with F1        
        3. Configure a LSV (on 4:2 EC volume2 on top of the 6 BLT volumes) for actual test        
        4. Export (Attach) the above volume to the Remote Host
        5. Execute nvme-connect from the network host and ensure that the above volume is accessible from the host.
        6. Create a BTRFS filesystem on the volume
        7. Create a 1MB data file and write a file with buffern pattern from data file
        8. After Write is completed, fail one of the plex.
        9. Perform read operation now using the data file for pattern match
        """)


if __name__ == "__main__":
    ecscript = DurableVolScript()
    ecscript.add_test_case(C18013())
    ecscript.add_test_case(C18372())
    ecscript.add_test_case(C18373())
    ecscript.add_test_case(C18374())
    ecscript.add_test_case(C18375())
    ecscript.run()
