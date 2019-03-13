from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut, DutInterface
from lib.fun.f1 import F1
from lib.host.storage_controller import StorageController
from lib.orchestration.simulation_orchestrator import DockerContainerOrchestrator
import re

'''
Script to do functional verification of for different file systems mounted on BLT volume
'''

topology_dict = {
    "name": "Basic Storage",
    "dut_info": {
        0: {
            "mode": Dut.MODE_SIMULATION,
            "type": Dut.DUT_TYPE_FSU,
            "interface_info": {
                0: {
                    "vms": 1,
                    "type": DutInterface.INTERFACE_TYPE_PCIE,
                    "vm_start_mode": "VM_START_MODE_QEMU_PLUS_DPCSH",
                    "vm_host_os": "fungible_ubuntu"
                }
            },
            "start_mode": F1.START_MODE_QEMU_PLUS_DPCSH
        }
    }
}


class FSOnBLTScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Start 1 POSIXs and allocate a Linux instance 
        2. Make the Linux instance available for the testcase
        """)

    def setup(self):
        self.topology_obj_helper = TopologyHelper(spec=topology_dict)
        self.topology = self.topology_obj_helper.deploy()
        fun_test.test_assert(self.topology, "Ensure deploy is successful")
        self.dut = self.topology.get_dut_instance(index=0)
        fun_test.test_assert(self.dut, "Retrieved DUT instance")
        self.storage_controller = StorageController(target_ip=self.dut.host_ip,
                                                    target_port=self.dut.external_dpcsh_port)

        # Preserving the funos-posix and qemu commandline
        self.funos_cmdline = self.dut.get_process_cmdline(F1.FUN_OS_SIMULATION_PROCESS_NAME)
        fun_test.log("\nfunos-posix commandline: {}".format(self.funos_cmdline))
        self.qemu_cmdline = self.dut.get_process_cmdline(DockerContainerOrchestrator.QEMU_PROCESS)
        fun_test.log("\nQemu commandline: {}".format(self.qemu_cmdline))
        self.qemu_cmdline = re.sub(r'(.*append)\s+(root.*mem=\d+M)(.*)', r'\1 "\2"\3', self.qemu_cmdline)
        fun_test.log("\nProcessed Qemu commandline: {}".format(self.qemu_cmdline))

        fun_test.shared_variables["topology"] = self.topology
        fun_test.shared_variables["storage_controller"] = self.storage_controller
        fun_test.shared_variables["funos_cmdline"] = self.funos_cmdline
        fun_test.shared_variables["qemu_cmdline"] = self.qemu_cmdline

    def cleanup(self):
        self.storage_controller.disconnect()
        TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()


class FSOnBLTTestcase(FunTestCase):

    def describe(self):
        pass

    def do_write_test(self):

        # Calculating filesize based on dataset_size_pct factor, if there is fraction factor after division adjusting
        # it nearest value which is divisible by block_size value
        temp = int(self.volume_params["volume_capacity"]["blt"] * self.dataset_size_pct)
        self.input_file_size = temp - (temp % self.dd_write_args["block_size"])

        # If data_size_pct of volume capacity exceeds 100MB, setting it to 100MB
        if self.input_file_size > self.file_size_limit:
            fun_test.log("50% of volume capacity exceeds the IO filesize limit,"
                         "hence limiting IO filesize to {}".format(self.file_size_limit))
            self.input_file_size = self.file_size_limit

        # Deriving dd command 'count' argument based on input file size
        self.dd_write_args["count"] = self.input_file_size / self.dd_write_args["block_size"]
        self.io_timeout = self.dd_write_args["count"] / self.test_timeout_ratio

        # Write a file into the BLT volume of size self.input_file_size bytes
        return_size = self.host.dd(timeout=self.io_timeout, sudo=True, **self.dd_write_args)
        if not self.readonly_filesystem:
            fun_test.test_assert_expected(self.input_file_size, return_size,
                                          "Writing {} bytes file into the BLT volume".format(self.input_file_size))
            self.input_md5sum = self.host.md5sum(file_name=self.dd_write_args["output_file"])
            fun_test.test_assert(self.input_md5sum, "Finding md5sum of input file {}".
                                 format(self.dd_write_args["output_file"]))
        else:
            # If filesystem is mounted as Read-only filesystem, write will fail
            fun_test.test_assert(not return_size, "Expected failure, write can't be performed on Read-only file system")

        # If the testcase is a buffered I/O then flush the kernel buffers/pages after the write operation, so that
        # the entire file will be flushed to the underlying volume
        if "oflag" not in self.dd_write_args:
            self.host.sudo_command("sync", timeout=self.io_timeout)
            self.host.sudo_command("echo 3 >/proc/sys/vm/drop_caches", timeout=self.io_timeout)

    def do_read_test(self):

        self.dd_read_args["count"] = self.input_file_size / self.dd_read_args["block_size"]
        self.io_timeout = self.dd_read_args["count"] / self.test_timeout_ratio

        # If the test case is a buffered I/O then flush the kernel buffers/pages before the read operation, so that
        # the entire file will be read from the underlying volume
        if "iflag" not in self.dd_read_args:
            self.host.sudo_command("sync", timeout=self.io_timeout)
            self.host.sudo_command("echo 3 >/proc/sys/vm/drop_caches", timeout=self.io_timeout)

        # Read the previously written file from the BLT volume and calculate the md5sum of the same
        return_size = self.host.dd(timeout=self.io_timeout, sudo=True, **self.dd_read_args)
        if not self.readonly_filesystem or self.remount_as_readonly:
            fun_test.test_assert_expected(
                self.input_file_size, return_size,
                "Reading {} bytes file into the BLT volume".format(self.input_file_size))
            self.output_md5sum = self.host.md5sum(file_name=self.dd_read_args["output_file"])
            fun_test.test_assert(self.output_md5sum, "Finding md5sum of output file {}".
                                 format(self.dd_read_args["output_file"]))
            fun_test.test_assert_expected(self.input_md5sum, self.output_md5sum,
                                          "Comparing md5sum of input & output file")
        else:
            fun_test.test_assert(not return_size, "Expected failure, write can't be performed on Read-only file system")

    def setup(self):

        testcase = self.__class__.__name__

        # Start of config json file parsing and initializing various variables to run this testcase
        config_parsing = True
        config_file = ""
        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Config file being used: {}".format(config_file))

        config_dict = {}
        config_dict = utils.parse_file_to_json(config_file)

        if testcase not in config_dict or not config_dict[testcase]:
            config_parsing = False
            fun_test.critical("Config is not available for the current testcase {} in {} file".
                              format(testcase, config_file))
            fun_test.test_assert(config_parsing, "Parsing Config json file for this {} testcase".format(testcase))

        for k, v in config_dict[testcase].iteritems():
            setattr(self, k, v)
        # End of config json file parsing

        # If test case doesn't have required parameter defined in config, setting it to default values
        if not hasattr(self, "remount_filesystem"):
            self.remount_filesystem = False
        if not hasattr(self, "readonly_filesystem"):
            self.readonly_filesystem = False
        if not hasattr(self, "remount_as_readonly"):
            self.remount_as_readonly = False
        if not hasattr(self, "create_fs_timeout"):
            self.create_fs_timeout = 300
        if not hasattr(self, "max_retries"):
            self.max_retries = 10
        if not hasattr(self, "wait_time"):
            self.wait_time = 1

        self.topology = fun_test.shared_variables["topology"]
        self.dut = self.topology.get_dut_instance(index=0)
        fun_test.test_assert(self.dut, "Retrieved DUT instance")
        self.host = self.topology.get_host_instance(dut_index=0, interface_index=0, host_index=0)
        fun_test.test_assert(self.dut, "Retrieved Qemu Host instance")

        self.storage_controller = fun_test.shared_variables["storage_controller"]
        self.funos_cmdline = fun_test.shared_variables["funos_cmdline"]
        self.qemu_cmdline = fun_test.shared_variables["qemu_cmdline"]

        # Configuring the controller
        command_result = self.storage_controller.command(command="enable_counters", legacy=True)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Enabling counters on DUT instance")

        self.nvme_block_device = self.nvme_device + "n" + str(self.ns_id)
        self.volume_name = self.nvme_block_device.replace("/dev/", "")
        self.volume_attached = False

        # Increasing the nvme driver timeouts for posix platform
        timeout_config = ""
        for key, value in self.nvme_timeouts.items():
            timeout_config += 'options nvme {}="{}"\n'.format(key, value)

        self.host.enter_sudo()
        self.host.create_file(file_name=r"/etc/modprobe.d/nvme_core.conf", contents=timeout_config)
        self.host.command("cat /etc/modprobe.d/nvme_core.conf")
        self.host.exit_sudo()

        # Creating BLT volumes
        self.this_uuid = utils.generate_uuid()
        command_result = self.storage_controller.create_volume(
            type=self.volume_params["volume_types"]["blt"],
            capacity=self.volume_params["volume_capacity"]["blt"],
            block_size=self.volume_params["volume_block"]["blt"],
            name="blt" + "_" + self.this_uuid[-4:], uuid=self.this_uuid,
            command_duration=self.command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Creating {} {} {} bytes volume on DUT instance".
                             format("blt", self.volume_params["volume_types"]["blt"],
                                    self.volume_params["volume_capacity"]["blt"]))

        # Attaching BLT volume to the host
        command_result = self.storage_controller.volume_attach_pcie(
            ns_id=self.ns_id, uuid=self.this_uuid, command_duration=self.command_timeout)
        fun_test.log(command_result)
        fun_test.simple_assert(command_result["status"], "Attaching BLT volume on DUT instance")

        # Reloading the nvme driver before checking the disk
        if self.reload_after_config:
            command_result = self.host.nvme_restart()
            fun_test.simple_assert(command_result, "Reloading nvme driver")

        # Additional sleep after nvme reload, required due to changes in lib to avoid #SWOS-3822
        self.attempt = 0
        while self.attempt < self.max_retries:
            fun_test.log("Current Attempt: {}, Max Attempts: {}".format(self.attempt + 1, self.max_retries))
            fun_test.sleep("Waiting after nvme driver reload..", self.wait_time)
            fun_test.log("Checking if device is available")
            lsblk_output = self.host.lsblk("-b")
            if self.volume_name in lsblk_output:
                fun_test.log("Device is accessible, setting the queue_length to {} and continuing with "
                             "test".format(self.queue_length))
                # Setting queue_length
                self.host.sudo_command("echo " + str(self.queue_length) + " >/sys/block/" + self.volume_name +
                                  "/queue/nr_requests")
                break
            self.attempt += 1

        # Checking that the volume is accessible to the host
        lsblk_output = self.host.lsblk("-b")
        fun_test.simple_assert(self.volume_name in lsblk_output, "{} device available".format(self.volume_name))
        fun_test.test_assert_expected(expected="disk", actual=lsblk_output[self.volume_name]["type"],
                                      message="{} volume type check".format(self.volume_name))
        fun_test.test_assert_expected(expected=self.volume_params["volume_capacity"]["blt"],
                                      actual=lsblk_output[self.volume_name]["size"],
                                      message="{} volume size check".format(self.volume_name))

    def run(self):

        testcase = self.__class__.__name__

        # Creating self.fs_type filesystem on BLT volume and mounting it
        # Checking if the filesystem type is XFS/btrfs/f2fs, to install respective packages in the qemu host
        if self.fs_type == "xfs":
            install_status = self.host.install_package("xfsprogs")
            fun_test.test_assert(install_status, "Installing XFS Package")
        if self.fs_type == "btrfs":
            install_status = self.host.install_package("btrfs-tools")
            fun_test.test_assert(install_status, "Installed btrfs-tools Package")
            fun_test.log("Enabling the Kernel module for btrfs")
            self.host.modprobe("btrfs")
        if self.fs_type == "f2fs":
            install_status = self.host.install_package("f2fs-tools")
            fun_test.test_assert(install_status, "Installed f2fs-tools Package")

        # Formatting block device with filesystem
        fs_status = self.host.create_filesystem(self.fs_type, self.nvme_block_device, timeout=self.create_fs_timeout)
        fun_test.test_assert(fs_status, "Creating {} filesystem on BLT volume {}".format(self.fs_type,
                                                                                         self.volume_name))
        # Creating a directory for mount point
        command_result = self.host.create_directory(self.mount_point)
        fun_test.test_assert(command_result, "Creating mount point directory {}".format(self.mount_point))

        # Mounting the volume on mount point
        command_result = self.host.mount_volume(self.nvme_block_device, self.mount_point,
                                                readonly=self.readonly_filesystem)
        fun_test.simple_assert(command_result, "Mounting BLT volume {} on {}".format(self.nvme_block_device,
                                                                                     self.mount_point))
        # Verifying if device is mounted
        lsblk_output = self.host.lsblk("-b")
        fun_test.test_assert_expected(expected=self.mount_point,
                                      actual=lsblk_output[self.volume_name]["mount_point"],
                                      message="Mounting BLT volume {} on {}".format(self.nvme_block_device,
                                                                                    self.mount_point))
        # Verification if device is mounted as read-only
        if self.readonly_filesystem:
            check_fs_ro = self.host.is_mount_ro(self.mount_point)
            fun_test.test_assert_expected(True, check_fs_ro, "File system is mounted as read only filesystem")

        # Write and read a file into the newly mounted BLT volume
        self.do_write_test()
        self.do_read_test()

        # Now unmount the BLT volume
        command_result = self.host.unmount_volume(volume=self.nvme_block_device)
        fun_test.simple_assert(command_result, "Unmounting BLT volume {} from {}".format(self.nvme_block_device,
                                                                                         self.mount_point))
        lsblk_output = self.host.lsblk("-b")
        fun_test.test_assert_expected(expected=None,
                                      actual=lsblk_output[self.volume_name]["mount_point"],
                                      message="Unmounting BLT volume {} from {}".format(self.nvme_block_device,
                                                                                        self.mount_point))
        # Remount file system on host and verify file contents
        if self.remount_filesystem:
            if self.remount_as_readonly:
                self.readonly_filesystem = True
            fun_test.log("\n===== Remounting file system: {} with Read-only flag: {} =====".format(
                self.fs_type, self.readonly_filesystem))
            command_result = self.host.mount_volume(self.nvme_block_device, self.mount_point,
                                                    readonly=self.readonly_filesystem)
            fun_test.simple_assert(command_result, "Mounting BLT volume {} on {}".format(self.nvme_block_device,
                                                                                         self.mount_point))
            if self.readonly_filesystem:
                check_fs_ro = self.host.is_mount_ro(self.mount_point)
                fun_test.test_assert_expected(True, check_fs_ro, "File system is remounted as read only filesystem")
            lsblk_output = self.host.lsblk("-b")
            fun_test.test_assert_expected(expected=self.mount_point,
                                          actual=lsblk_output[self.volume_name]["mount_point"],
                                          message="Mounting BLT volume {} on {}".format(self.nvme_block_device,
                                                                                        self.mount_point))
            # Check if existing file retains the file contents
            self.do_read_test()
            self.output_md5sum = self.host.md5sum(file_name=self.dd_read_args["output_file"])
            fun_test.test_assert(self.output_md5sum, "Finding md5sum of existing ouptut file {} after remount".
                                 format(self.dd_read_args["output_file"]))
            fun_test.test_assert_expected(self.input_md5sum, self.output_md5sum,
                                          "md5sum of input & output file matches after remount")

            # Performing new write and read after remounting
            if not self.remount_as_readonly:
                # Cleaning up old files
                del_input_file = self.host.remove_file(self.dd_read_args["input_file"])
                fun_test.test_assert_expected(True, del_input_file, "Input file is deleted")
                del_output_file = self.host.remove_file(self.dd_read_args["output_file"])
                fun_test.test_assert_expected(True, del_output_file, "Output file is deleted")

                # Write new data in files and re-verify
                self.do_write_test()
                self.do_read_test()

            # unmounting the BLT volume
            command_result = self.host.unmount_volume(volume=self.nvme_block_device)
            fun_test.simple_assert(command_result, "Unmounting BLT volume {} from {}".format(self.nvme_block_device,
                                                                                             self.mount_point))
            lsblk_output = self.host.lsblk("-b")
            fun_test.test_assert_expected(expected=None,
                                          actual=lsblk_output[self.volume_name]["mount_point"],
                                          message="Unmounting BLT volume {} from {}".format(self.nvme_block_device,
                                                                                            self.mount_point))

        # Detaching and Unconfiguring volumes
        command_result = self.storage_controller.volume_detach_pcie(
            ns_id=self.ns_id, uuid=self.this_uuid, command_duration=self.command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Detaching BLT volume on DUT")

    def cleanup(self):
        pass


class Ext2OnBLT(FSOnBLTTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Building EXT2 filesystem on BLT volume and creating file in it",
                              steps="""
        1. Create BLT volume
        2. Attach BLT volume
        3. Create EXT2 filesystem on the BLT volume and mount it
        4. Create a file using dd command
        5. Check that the file is created successfully and find checksum of file 
        6. Read the same file once again and find its checksum.
        7. Compare the checksum obtained in previous two steps
        8. Unmount the file system
        9. Detach the BLT volume from DUT
        10. Unconfigure all the BLT volumes
        """)

    def setup(self):
        super(Ext2OnBLT, self).setup()

    def run(self):
        super(Ext2OnBLT, self).run()

    def cleanup(self):
        super(Ext2OnBLT, self).cleanup()


class Ext3OnBLT(FSOnBLTTestcase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Building EXT3 filesystem on BLT volume and creating file in it",
                              steps="""
          1. Create BLT volume
          2. Attach BLT volume
          3. Create EXT3 filesystem on the BLT volume and mount it
          4. Create a file using dd command
          5. Check that the file is created successfully and find checksum of file 
          6. Read the same file once again and find its checksum.
          7. Compare the checksum obtained in previous two steps
          8. Unmount the file system
          9. Detach the BLT volume from DUT
          10. Unconfigure all the BLT volumes
        """)

    def setup(self):
        super(Ext3OnBLT, self).setup()

    def run(self):
        super(Ext3OnBLT, self).run()

    def cleanup(self):
        super(Ext3OnBLT, self).cleanup()


class Ext4OnBLT(FSOnBLTTestcase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Building EXT4 filesystem on BLT volume and creating file in it",
                              steps="""
          1. Create BLT volume
          2. Attach BLT volume
          3. Create EXT4 filesystem on the BLT volume and mount it
          4. Create a file using dd command
          5. Check that the file is created successfully and find checksum of file 
          6. Read the same file once again and find its checksum.
          7. Compare the checksum obtained in previous two steps
          8. Unmount the file system
          9. Detach the BLT volume from DUT
          10. Unconfigure all the BLT volumes
        """)

    def setup(self):
        super(Ext4OnBLT, self).setup()

    def run(self):
        super(Ext4OnBLT, self).run()

    def cleanup(self):
        super(Ext4OnBLT, self).cleanup()


class XFSOnBLT(FSOnBLTTestcase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Building XFS filesystem on BLT volume and creating file in it",
                              steps="""
          1. Create BLT volume
          2. Attach BLT volume
          3. Check if Qemu host has 'xfsprogs' package installed, if not install it
          4. Create XFS filesystem on the BLT volume and mount it
          5. Create a file using dd command
          6. Check that the file is created successfully and find checksum of file 
          7. Read the same file once again and find its checksum.
          8. Compare the checksum obtained in previous two steps
          9. Unmount the file system
          10. Detach the BLT volume from DUT
          11. Unconfigure all the BLT volumes
        """)

    def setup(self):
        super(XFSOnBLT, self).setup()

    def run(self):
        super(XFSOnBLT, self).run()

    def cleanup(self):
        super(XFSOnBLT, self).cleanup()


class BTRFSOnBLT(FSOnBLTTestcase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Building BTRFS filesystem on BLT volume and creating file in it",
                              steps="""
          1. Create BLT volume
          2. Attach BLT volume
          3. Check if Qemu host has 'btrfs-tools' package installed, if not install it
          4. Create BTRF filesystem on the BLT volume and mount it
          5. Create a file using dd command
          6. Check that the file is created successfully and find checksum of file 
          7. Read the same file once again and find its checksum.
          8. Compare the checksum obtained in previous two steps
          9. Unmount the file system
          10. Detach the BLT volume from DUT
          11. Unconfigure all the BLT volumes
        """)

    def setup(self):
        super(BTRFSOnBLT, self).setup()

    def run(self):
        super(BTRFSOnBLT, self).run()

    def cleanup(self):
        super(BTRFSOnBLT, self).cleanup()


class F2FSOnBLT(FSOnBLTTestcase):
    def describe(self):
        self.set_test_details(id=6,
                              summary="Building F2FS filesystem on BLT volume and creating file in it",
                              steps="""
          1. Create BLT volume
          2. Attach BLT volume
          3. Check if Qemu host has 'f2fs-tools' package installed, if not install it
          4. Create F2FS filesystem on the BLT volume and mount it
          5. Create a file using dd command
          6. Check that the file is created successfully and find checksum of file 
          7. Read the same file once again and find its checksum.
          8. Compare the checksum obtained in previous two steps
          9. Unmount the file system
          10. Detach the BLT volume from DUT
          11. Unconfigure all the BLT volumes
        """)

    def setup(self):
        super(F2FSOnBLT, self).setup()

    def run(self):
        super(F2FSOnBLT, self).run()

    def cleanup(self):
        super(F2FSOnBLT, self).cleanup()


class NTFSOnBLT(FSOnBLTTestcase):
    def describe(self):
        self.set_test_details(id=7,
                              summary="Building NTFS filesystem on BLT volume and creating file in it",
                              steps="""
        1. Create BLT volume
        2. Attach BLT volume
        3. Create NTFS filesystem on the BLT volume and mount it
        4. Create a file using dd command
        5. Check that the file is created successfully and find checksum of file 
        6. Read the same file once again and find its checksum.
        7. Compare the checksum obtained in previous two steps
        8. Unmount the file system
        9. Detach the BLT volume from DUT
        10. Unconfigure all the BLT volumes
        """)

    def setup(self):
        super(NTFSOnBLT, self).setup()

    def run(self):
        super(NTFSOnBLT, self).run()

    def cleanup(self):
        super(NTFSOnBLT, self).cleanup()


class Ext4OnBLTWithRemount(FSOnBLTTestcase):
    def describe(self):
        self.set_test_details(id=9,
                              summary="Building EXT4 filesystem on BLT volume, Create File in it and verifying md5sum "
                                      "of write and read file, remount filesystem and verify contents after remount",
                              steps="""
          1. Create BLT volume
          2. Attach BLT volume
          3. Create EXT4 filesystem on the BLT volume and mount it
          4. Create a file using dd command
          5. Check that the file is created successfully and find checksum of file 
          6. Read the same file once again and find its checksum.
          7. Compare the checksum obtained in previous two steps
          8. Unmount the File system
          9. Remount the File system
          10. Check the existing output file contents
          11. Clean up existing files
          12. Write file with new content and verify
          13. Detach the BLT volume from DUT
          14. Unconfigure all the BLT volumes
        """)

    def setup(self):
        super(Ext4OnBLTWithRemount, self).setup()

    def run(self):
        super(Ext4OnBLTWithRemount, self).run()

    def cleanup(self):
        super(Ext4OnBLTWithRemount, self).cleanup()


class Ext4OnBLTWithReadOnlyFS(FSOnBLTTestcase):
    def describe(self):
        self.set_test_details(id=10,
                              summary="Building EXT4 filesystem as Read-only filesystem on BLT volume, Verifying "
                                      "Write on Read-only filesystem fails",
                              steps="""
          1. Create BLT volume
          2. Attach BLT volume
          3. Create Read only EXT4 filesystem on the BLT volume and mount it
          4. Try to create a file using dd command
          5. Check that the file creation fails on Read-only filesystem 
          6. Detach the BLT volume from DUT
          7. Unconfigure all the BLT volumes
        """)

    def setup(self):
        super(Ext4OnBLTWithReadOnlyFS, self).setup()

    def run(self):
        super(Ext4OnBLTWithReadOnlyFS, self).run()

    def cleanup(self):
        super(Ext4OnBLTWithReadOnlyFS, self).cleanup()

class XFSOnBLTWithRemountAsReadOnlyFS(FSOnBLTTestcase):
    def describe(self):
        self.set_test_details(id=8,
                              summary="Building XFS filesystem on BLT volume, Create a file and verify write and read,"
                                      " Remount XFS file system as Read-only filesystem. File read should succeed",
                              steps="""
          1. Create BLT volume
          2. Attach BLT volume
          3. Create XFS filesystem on the BLT volume and mount it
          4. Create a file using dd command
          5. Check that the file is created successfully and find checksum of file 
          6. Read the same file once again and find its checksum.
          7. Compare the checksum obtained in previous two steps
          8. Unmount the File system
          9. Remount the File system as Read-only Filesystem
          10. Check the existing output file contents
          11. Clean up existing files
          13. Detach the BLT volume from DUT
          14. Unconfigure all the BLT volumes
        """)

    def setup(self):
        super(XFSOnBLTWithRemountAsReadOnlyFS, self).setup()

    def run(self):
        super(XFSOnBLTWithRemountAsReadOnlyFS, self).run()

    def cleanup(self):
        super(XFSOnBLTWithRemountAsReadOnlyFS, self).cleanup()


if __name__ == "__main__":

    fsonblt_script = FSOnBLTScript()
    fsonblt_script.add_test_case(Ext2OnBLT())
    fsonblt_script.add_test_case(Ext3OnBLT())
    fsonblt_script.add_test_case(Ext4OnBLT())
    fsonblt_script.add_test_case(XFSOnBLT())
    fsonblt_script.add_test_case(BTRFSOnBLT())
    fsonblt_script.add_test_case(F2FSOnBLT())
    fsonblt_script.add_test_case(NTFSOnBLT())
    fsonblt_script.add_test_case(XFSOnBLTWithRemountAsReadOnlyFS())
    ##########
    # Commenting out below two TCs as it's filesystems specific verification and not contributing to storage IO
    # fsonblt_script.add_test_case(Ext4OnBLTWithRemount())
    # fsonblt_script.add_test_case(Ext4OnBLTWithReadOnlyFS())
    ##########
    fsonblt_script.run()
