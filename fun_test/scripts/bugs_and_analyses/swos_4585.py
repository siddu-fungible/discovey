from lib.system.fun_test import *
from lib.system import utils
from lib.topology.dut import Dut
from lib.host.traffic_generator import TrafficGenerator
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper
from lib.host.linux import Linux
from lib.fun.fs import Fs
from datetime import datetime
import re
import random
from lib.topology.topology_helper import TopologyHelper
from lib.host.storage_controller import StorageController

'''
Script to test single drive failure scenarios for 4:2 EC config
'''

class ECVolumeLevelScript(FunTestScript):
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
            self.syslog_level = "default"
            self.command_timeout = 5
            self.retries = 24
        else:
            for k, v in script_config["GlobalSetup"].items():
                setattr(self, k, v)

        fun_test.log("Global Config: {}".format(self.__dict__))

        # Pulling the testbed type and its config
        self.testbed_type = fun_test.get_job_environment_variable("test_bed_type")
        fun_test.log("Testbed-type: {}".format(self.testbed_type))
        self.fs_spec = fun_test.get_asset_manager().get_fs_spec(self.testbed_type)
        self.testbed_config = fun_test.get_asset_manager().get_test_bed_spec(self.testbed_type)
        fun_test.log("{} FS Spec: {}".format(self.testbed_type, self.fs_spec))
        fun_test.log("{} Testbed Config: {}".format(self.testbed_type, self.testbed_config))
        fun_test.simple_assert(self.fs_spec, "FS Spec for {}".format(self.testbed_type))
        fun_test.simple_assert(self.testbed_config, "Testbed Config for {}".format(self.testbed_type))

        self.topology_helper = TopologyHelper()
        self.topology_helper.set_dut_parameters(dut_index=0, custom_boot_args=self.bootargs,
                                                disable_f1_index=self.disable_f1_index)
        self.topology = self.topology_helper.deploy()
        fun_test.test_assert(self.topology, "Topology deployed")

        self.fs = self.topology.get_dut_instance(index=self.f1_in_use)
        self.f1 = self.fs.get_f1(index=self.f1_in_use)
        self.storage_controller = self.f1.get_dpc_storage_controller()

        # Fetching Linux host
        self.end_host = self.fs.get_come()

        fun_test.shared_variables["testbed_type"] = self.testbed_type
        fun_test.shared_variables["topology"] = self.topology
        fun_test.shared_variables["fs_spec"] = self.fs_spec
        fun_test.shared_variables["testbed_config"] = self.testbed_config
        fun_test.shared_variables["f1_in_use"] = self.f1_in_use
        fun_test.shared_variables["attach"] = self.attach
        fun_test.shared_variables["fs"] = self.fs
        fun_test.shared_variables["f1"] = self.f1
        fun_test.shared_variables["end_host"] = self.end_host
        fun_test.shared_variables["storage_controller"] = self.storage_controller

        # Setting the syslog level
        if self.syslog_level != "default":
            command_result = self.storage_controller.poke(props_tree=["params/syslog/level", self.syslog_level],
                                                          legacy=False, command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Setting syslog level to {}".format(self.syslog_level))

            command_result = self.storage_controller.peek(props_tree="params/syslog/level", legacy=False,
                                                          command_duration=self.command_timeout)
            fun_test.test_assert_expected(expected=self.syslog_level, actual=command_result["data"],
                                          message="Checking syslog level")
        else:
            fun_test.log("Default syslog level is requested...So not going to modify the syslog settings")

    def cleanup(self):
        self.storage_controller.disconnect()
        fun_test.sleep("Allowing buffer time before calling fs clean-up", 60)
        self.fs.cleanup()


class ECVolumeLevelTestcase(FunTestCase):

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
        # End of benchmarking json file parsing

        self.fs = fun_test.shared_variables["fs"]
        self.f1 = fun_test.shared_variables["f1"]

        self.testbed_type = fun_test.shared_variables["testbed_type"]
        self.fs_spec = fun_test.shared_variables["fs_spec"]
        self.testbed_config = fun_test.shared_variables["testbed_config"]
        self.f1_in_use = fun_test.shared_variables["f1_in_use"]
        self.attach = fun_test.shared_variables["attach"]
        self.storage_controller = fun_test.shared_variables["storage_controller"]
        self.end_host = fun_test.shared_variables["end_host"]

        self.nvme_block_device = self.nvme_device + "0n" + str(self.ns_id)
        self.volume_name = self.nvme_block_device.replace("/dev/", "")
        self.volume_configured = False
        self.volume_attached = False

        # Proceeding to configure the EC volume
        # Configuring the controller
        command_result = {}
        command_result = self.storage_controller.command(command="enable_counters", legacy=True,
                                                         command_duration=self.command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Enabling counters on DUT")

        self.ec_info["cntrlr_uuid"] = utils.generate_uuid()
        command_result = self.storage_controller.create_controller(ctrlr_id=0,
                                                                   ctrlr_uuid=self.ec_info["cntrlr_uuid"],
                                                                   ctrlr_type="BLOCK",
                                                                   transport=self.attach["transport"],
                                                                   huid=self.attach["huid"],
                                                                   ctlid=self.attach["ctlid"],
                                                                   fnid=self.attach["fnid"],
                                                                   command_duration=self.command_timeout)

        fun_test.test_assert(command_result['status'], message="Create Controller with UUID: {}".
                             format(self.ec_info['cntrlr_uuid']))

        (ec_config_status, self.ec_info) = self.storage_controller.configure_ec_volume(self.ec_info,
                                                                                       self.command_timeout)
        fun_test.simple_assert(ec_config_status, "Configuring EC/LSV volume")

        self.volume_configured = True
        fun_test.log("EC details after configuring EC Volume:")
        for k, v in self.ec_info.items():
            fun_test.log("{}: {}".format(k, v))

        # Attaching/Exporting all the EC/LS volumes to the external server
        for num in xrange(self.ec_info["num_volumes"]):
            command_result = self.storage_controller.attach_volume_to_controller(
                ctrlr_uuid=self.ec_info["cntrlr_uuid"], ns_id=num+1, vol_uuid=self.ec_info["attach_uuid"][num],
                command_duration=self.command_timeout)
            fun_test.test_assert(command_result['status'],
                                 message="Attach LSV Volume {0} to the Controller with uuid: {1}".format(
                                     self.ec_info["attach_uuid"][num],self.ec_info["cntrlr_uuid"]))

        self.volume_attached = True
        fun_test.shared_variables["ec_info"] = self.ec_info

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

        lsblk_output = self.end_host.lsblk("-b")
        fun_test.simple_assert(lsblk_output, "Listing available volumes")

        # Checking that the above created EC volume is visible to the end host after NVME connect
        volume_pattern = self.nvme_device.replace("/dev/", "") + r"(\d+)n(\d+)"
        self.nvme_block_device_list = []
        self.volume_name_list = []
        for volume_name in lsblk_output:
            match = re.search(volume_pattern, volume_name)
            if match:
                ctlr_id = match.group(1)
                ns_id = match.group(2)
                self.nvme_block_device_list.append(self.nvme_device + ctlr_id + "n" + ns_id)
                self.volume_name_list.append(self.nvme_block_device_list[-1].replace("/dev/", ""))
                fun_test.test_assert_expected(expected=self.volume_name_list[-1],
                                              actual=lsblk_output[volume_name]["name"],
                                              message="{} device available".format(self.volume_name_list[-1]))
                fun_test.test_assert_expected(expected="disk", actual=lsblk_output[volume_name]["type"],
                                              message="{} device type check".format(self.volume_name_list[-1]))
                fun_test.test_assert_expected(expected=self.ec_info["attach_size"][int(ns_id) - 1],
                                              actual=lsblk_output[volume_name]["size"],
                                              message="{} volume size check".format(self.volume_name_list[-1]))

        # Total number of volumes available should be equal to the ec_info["num_volumes"]
        self.nvme_block_device_list.sort()
        self.volume_name_list.sort()
        fun_test.test_assert_expected(expected=self.ec_info["num_volumes"], actual=len(self.nvme_block_device_list),
                                      message="Number of volumes available")

        fun_test.shared_variables["nvme_block_device_list"] = self.nvme_block_device_list
        fun_test.shared_variables["volume_name_list"] = self.volume_name_list

        # Disable the udev daemon which will skew the read stats of the volume during the test
        udev_services = ["systemd-udevd-control.socket", "systemd-udevd-kernel.socket", "systemd-udevd"]
        for service in udev_services:
            service_status = self.end_host.systemctl(service_name=service, action="stop")
            fun_test.test_assert(service_status, "Stopping {} service".format(service))

    def run(self):

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

        fun_test.log("EC plex volumes UUID      : {}".format(self.ec_info["uuids"][0]["blt"]))
        fun_test.log("EC plex volumes drive UUID: {}".format(self.ec_info["drive_uuid"][0]))
        fun_test.log("EC plex volumes device ID : {}".format(self.ec_info["device_id"][0]))

        # Creating the filesystem in the volumes configured and available to the host
        if self.fs_type == "xfs":
            install_status = self.end_host.install_package("xfsprogs")
            fun_test.test_assert(install_status, "Installing XFS Package")

        for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
            size = self.ec_info["attach_size"][num]
            # Set the timeout for the filesystem create command based on its size
            fs_create_timeout = (size / self.f1_fs_timeout_ratio[0]) * self.f1_fs_timeout_ratio[1]
            if fs_create_timeout < self.min_timeout:
                fs_create_timeout = self.min_timeout
            fs_status = self.end_host.create_filesystem(self.fs_type, self.nvme_block_device_list[num],
                                                        timeout=fs_create_timeout)
            fun_test.test_assert(fs_status, "Creating {} filesystem on EC volume {}".
                                 format(self.fs_type, self.volume_name_list[num]))
            # Creating mount point
            mount_point = self.mount_path + str(num + 1)
            command_result = self.end_host.create_directory(mount_point)
            fun_test.test_assert(command_result, "Creating mount point directory {}".format(mount_point))
            # Mounting the volume into the mount point
            command_result = self.end_host.mount_volume(self.nvme_block_device_list[num], mount_point)
            fun_test.simple_assert(command_result, "Mounting EC volume {} on {}".
                                   format(self.nvme_block_device_list[num], mount_point))
            lsblk_output = self.end_host.lsblk("-b")
            fun_test.test_assert_expected(expected=mount_point,
                                          actual=lsblk_output[self.volume_name_list[num]]["mount_point"],
                                          message="Mounting EC volume {} on {}".format(self.nvme_block_device_list[num],
                                                                                       mount_point))

        # Creating input file
        self.dd_create_file["count"] = self.test_file_size / self.dd_create_file["block_size"]

        # Write a file into the EC volume of size self.test_file_size bytes
        return_size = self.end_host.dd(timeout=self.dd_create_file["count"], sudo=True, **self.dd_create_file)
        fun_test.test_assert_expected(self.test_file_size, return_size, "Creating {} bytes test input file".
                                      format(self.test_file_size))
        self.src_md5sum = self.end_host.md5sum(file_name=self.dd_create_file["output_file"],
                                             timeout=self.dd_create_file["count"])
        fun_test.test_assert(self.src_md5sum, "Finding md5sum of source file {}".
                             format(self.dd_create_file["output_file"]))


        # Test Preparation Done
        # Starting the test
        cp_timeout = (self.test_file_size / self.fs_cp_timeout_ratio[0]) * self.fs_cp_timeout_ratio[1]
        if cp_timeout < self.min_timeout:
            cp_timeout = self.min_timeout

        if hasattr(self, "back_pressure") and self.back_pressure:
            # Start the vdbench here to produce the back pressure
            pass

        # Copying the file into the all the test volumes
        source_file = self.dd_create_file["output_file"]
        dst_file1 = []
        for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
            dst_file1.append(self.mount_path + str(num + 1) + "/file1")
            cp_cmd = "sudo cp {} {}".format(source_file, dst_file1[-1])
            self.end_host.start_bg_process(command=cp_cmd)

        # Check whether the drive failure needs to be triggered
        if hasattr(self, "trigger_drive_failure") and self.trigger_drive_failure:
            # Check whether the drive index to be failed is given or not. If not pick a random one
            if self.failure_mode == "random" or not hasattr(self, "failure_drive_indicies"):
                self.failure_drive_indicies = {}
                for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                    self.failure_drive_indicies[num] = []
                    while True:
                        index = random.randint(0, self.ec_info["ndata"] + self.ec_info["nparity"] - 1)
                        if index not in self.failure_drive_indicies[num]:
                            self.failure_drive_indicies[num].append(index)
                        if len(self.failure_drive_indicies[num]) >= 2:
                            break
            # Sleep for sometime before triggering the drive failure
            fun_test.log("Drives needs to be disabled: {}".format(self.failure_drive_indicies))
            wait_time = 2
            if hasattr(self, "failure_start_time_ratio"):
                wait_time = int(round(cp_timeout * self.failure_start_time_ratio))
            fun_test.sleep(message="Sleeping for {} seconds before inducing a drive failure".format(wait_time),
                           seconds=wait_time)

            # Triggering the drive failure
            for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                fail_uuid = self.ec_info["uuids"][num]["blt"][self.failure_drive_indicies[num][0]]
                fail_device = self.ec_info["device_id"][num][self.failure_drive_indicies[num][0]]
                device_fail_status = self.storage_controller.disable_device(device_id=fail_device,
                                                                            command_duration=self.command_timeout)
                fun_test.test_assert(device_fail_status["status"], "Disabling Device ID {}".format(fail_device))

        timer = FunTimer(max_time=cp_timeout)
        while not timer.is_expired():
            fun_test.sleep("Waiting for the copy to complete", seconds=self.status_interval)
            output = self.end_host.get_process_id_by_pattern(process_pat=cp_cmd, multiple=True)
            if not output:
                fun_test.log("Copying file {} to {} got completed".format(source_file, dst_file1))
                break
        else:
            fun_test.test_assert(False, "Copying {} bytes file into {}".format(self.test_file_size, dst_file1))

        self.end_host.sudo_command("sync", timeout=cp_timeout / 2)
        self.end_host.sudo_command("echo 3 >/proc/sys/vm/drop_caches", timeout=cp_timeout / 2)

        for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
            cur_dst_file = dst_file1[num - self.test_volume_start_index]
            dst_file_info = self.end_host.ls(cur_dst_file)
            fun_test.simple_assert(dst_file_info, "Copied file {} exists".format(cur_dst_file))
            fun_test.test_assert_expected(expected=self.test_file_size, actual=dst_file_info["size"],
                                          message="Copying {} bytes file into {}".format(self.test_file_size,
                                                                                         cur_dst_file))
            self.dst_md5sum = self.end_host.md5sum(file_name=cur_dst_file, timeout=cp_timeout)
            fun_test.test_assert(self.dst_md5sum, "Finding md5sum of copied file {}".format(cur_dst_file))
            fun_test.test_assert_expected(expected=self.src_md5sum, actual=self.dst_md5sum,
                                          message="Comparing md5sum of source & destination file")

        # Creating another input file
        self.dd_create_file["count"] = self.test_file_size / self.dd_create_file["block_size"]

        # Write a file into the EC volume of size self.test_file_size bytes
        return_size = self.end_host.dd(timeout=self.dd_create_file["count"], sudo=True, **self.dd_create_file)
        fun_test.test_assert_expected(self.test_file_size, return_size, "Creating {} bytes test input file".
                                      format(self.test_file_size))
        self.src_md5sum = self.end_host.md5sum(file_name=self.dd_create_file["output_file"],
                                               timeout=self.dd_create_file["count"])
        fun_test.test_assert(self.src_md5sum, "Finding md5sum of source file {}".
                             format(self.dd_create_file["output_file"]))

        # Copying the file into the volume
        source_file = self.dd_create_file["output_file"]
        dst_file2 = []
        for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
            dst_file2.append(self.mount_path + str(num + 1) + "/file2")
            cp_cmd = "sudo cp {} {}".format(source_file, dst_file2[-1])
            self.end_host.start_bg_process(command=cp_cmd)

        # Check whether the drive failure needs to be triggered
        if hasattr(self, "trigger_drive_failure") and self.trigger_drive_failure:
            # Sleep for sometime before triggering the drive failure
            wait_time = 2
            if hasattr(self, "failure_start_time_ratio"):
                wait_time = int(round(cp_timeout * self.failure_start_time_ratio))
            fun_test.sleep(message="Sleeping for {} seconds before inducing a drive failure".format(wait_time),
                           seconds=wait_time)
            # Triggering the drive failure
            for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
                fail_uuid = self.ec_info["uuids"][num]["blt"][self.failure_drive_index[num][1]]
                fail_device = self.ec_info["device_id"][num][self.failure_drive_index[num][1]]
                device_fail_status = self.storage_controller.disable_device(device_id=fail_device,
                                                                            command_duration=self.command_timeout)
                fun_test.test_assert(device_fail_status["status"], "Disabling Device ID {}".format(fail_device))

        timer = FunTimer(max_time=cp_timeout)
        while not timer.is_expired():
            fun_test.sleep("Waiting for the copy to complete", seconds=self.status_interval)
            output = self.end_host.get_process_id_by_pattern(process_pat=cp_cmd, multiple=True)
            if not output:
                fun_test.log("Copying file {} to {} got completed".format(source_file, dst_file2))
                break
        else:
            fun_test.test_assert(False, "Copying {} bytes file into {}".format(self.test_file_size, dst_file2))

        self.end_host.sudo_command("sync", timeout=cp_timeout / 2)
        self.end_host.sudo_command("echo 3 >/proc/sys/vm/drop_caches", timeout=cp_timeout / 2)

        for num in xrange(self.test_volume_start_index, self.ec_info["num_volumes"]):
            cur_dst_file = dst_file2[num - self.test_volume_start_index]
            dst_file_info = self.end_host.ls(cur_dst_file)
            fun_test.simple_assert(dst_file_info, "Copied file {} exists".format(cur_dst_file))
            fun_test.test_assert_expected(expected=self.test_file_size, actual=dst_file_info["size"],
                                          message="Copying {} bytes file into {}".format(self.test_file_size,
                                                                                         cur_dst_file))
            self.dst_md5sum = self.end_host.md5sum(file_name=cur_dst_file, timeout=cp_timeout)
            fun_test.test_assert(self.dst_md5sum, "Finding md5sum of copied file {}".format(cur_dst_file))
            fun_test.test_assert_expected(expected=self.src_md5sum, actual=self.dst_md5sum,
                                          message="Comparing md5sum of source & destination file")

    def cleanup(self):

        if self.volume_attached:
            # Detaching all the EC/LS volumes to the external server
            for num in xrange(self.ec_info["num_volumes"]):
                command_result = self.storage_controller.detach_volume_from_controller(
                    ctrlr_uuid=self.ec_info["cntrlr_uuid"], ns_id=num+1, command_duration=self.command_timeout)
                fun_test.test_assert(command_result["status"], message="Detach nsid: {} from controller: {}".
                                     format(num+1, self.ec_info["cntrlr_uuid"]))

            command_result = self.storage_controller.delete_controller(ctrlr_uuid=self.ec_info["cntrlr_uuid"],
                                                                       command_duration=self.command_timeout),
            fun_test.test_assert(command_result["status"], message="Delete Controller uuid: {}".
                                 format(self.ec_info["cntrlr_uuid"]))

        if self.volume_configured:
            # Unconfiguring all the LSV/EC and it's plex volumes
            self.storage_controller.unconfigure_ec_volume(ec_info=self.ec_info, command_timeout=self.command_timeout)


class SingleVolumeMultiDriveFailureWithoutBP(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Inspur: 8.7.1.0: Multi Drive Failure Testing without rebuild",
                              steps="""
        1. Bring up F1 in FS1600.
        2. Reboot network connected hosted and configure its test interface to establish connectivity with F1.
        3. Configure 6 BLT volumes in F1.
        4. Configure a 4:2 EC volume on top of the 6 BLT volumes.
        5. Configure a LS volume on top of the EC volume based on use_lsv config along with its associative journal 
        volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Execute NVME connect from the network host and ensure that the above volume is accessible from the host.
        8. Create ext3 filesystem in the above volume and mount the same under /mnt/ssd<volume_num>.
        9. Create test_file_size bytes file and copy the same into the above mount point.
        10. While the copy is in progress, simulate drive failure in one of the drives hosting the above 6 BLT volumes.
        11. Ensure that the file is copied successfully and the md5sum between the source and destination is matching.
        12. Create another test_file_size bytes file and copy the same into the above mount point.
        13. While the copy is in progress, simulate one more drive failure in one of the drives hosting the above 6 BLT 
        volumes.
        14. Ensure that the file is copied successfully and the md5sum between the source and destination is matching.
        """)

    def setup(self):
        super(SingleVolumeMultiDriveFailureWithoutBP, self).setup()

    def run(self):
        super(SingleVolumeMultiDriveFailureWithoutBP, self).run()

    def cleanup(self):
        super(SingleVolumeMultiDriveFailureWithoutBP, self).cleanup()

if __name__ == "__main__":

    ecscript = ECVolumeLevelScript()
    ecscript.add_test_case(SingleVolumeMultiDriveFailureWithoutBP())
    ecscript.run()
