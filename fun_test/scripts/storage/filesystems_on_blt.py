from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut, DutInterface
from lib.fun.f1 import F1
from lib.host.storage_controller import StorageController
from lib.orchestration.simulation_orchestrator import DockerContainerOrchestrator
import re
import copy

'''
Script to do functional verification of for different file systems mounted on BLT volume
'''
import os
os.environ["DOCKER_HOSTS_SPEC_FILE"] = fun_test.get_script_parent_directory() + "/../scratch/remote_docker_host_with_storage.json"

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
        # TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()


class FSOnBLTTestcase(FunTestCase):

    def describe(self):
        pass

    def do_write_test(self):

        # Deriving dd command 'count' argument based on input file size
        self.input_file_size_in_bytes = utils.convert_to_bytes(self.input_file_size)
        self.dd_write_args["count"] = self.input_file_size_in_bytes / self.dd_write_args["block_size"]
        cmd_timeout = self.dd_write_args["count"] / self.test_timeout_ratio

        # Write a file into the EC volume of size self.input_file_size bytes
        return_size = self.host.dd(timeout=cmd_timeout, **self.dd_write_args)
        fun_test.test_assert_expected(self.input_file_size_in_bytes, return_size,
                                      "Writing {} bytes file into the EC volume".format(self.input_file_size))
        self.input_md5sum = self.host.md5sum(file_name=self.dd_write_args["output_file"])
        fun_test.test_assert(self.input_md5sum, "Finding md5sum of input file {}".
                             format(self.dd_write_args["output_file"]))

    def do_read_test(self):

        self.dd_read_args["count"] = self.input_file_size_in_bytes / self.dd_read_args["block_size"]
        cmd_timeout = self.dd_read_args["count"] / self.test_timeout_ratio

        # Read the previously written file from the EC volume and calculate the md5sum of the same
        return_size = self.host.dd(timeout=cmd_timeout, **self.dd_read_args)
        fun_test.test_assert_expected(self.input_file_size_in_bytes, return_size, "Reading {} bytes file into the EC volume".
                                      format(self.input_file_size_in_bytes))
        self.output_md5sum = self.host.md5sum(file_name=self.dd_read_args["output_file"])
        fun_test.test_assert(self.output_md5sum, "Finding md5sum of ouptut file {}".
                             format(self.dd_read_args["output_file"]))
        fun_test.test_assert_expected(self.input_md5sum, self.output_md5sum, "Comparing md5sum of input & output file")

    def setup(self):

        testcase = self.__class__.__name__

        # Start of benchmarking json file parsing and initializing various variables to run this testcase
        config_parsing = True
        config_file = ""
        config_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Benchmark file being used: {}".format(config_file))

        benchmark_dict = {}
        benchmark_dict = utils.parse_file_to_json(config_file)

        if testcase not in benchmark_dict or not benchmark_dict[testcase]:
            config_parsing = False
            fun_test.critical("Benchmarking is not available for the current testcase {} in {} file".
                              format(testcase, config_file))
            fun_test.test_assert(config_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))

        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)
        # End of benchmarking json file parsing

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

        # TODO: Should we add check for minimum volume capacity for filetypes? for eg. btrfs requires min 40 MB

        '''if self.fs_type == "btrfs":
            fun_test.test_assert(utils.convert_to_bytes(self.volume_params["volume_capacity"]["blt"]) < 41943040,
                                 "Volume /NVME device capacity Size should be minimum 40MB")'''

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

        # Attaching BLT volume to the external server
        command_result = self.storage_controller.volume_attach_pcie(
            ns_id=self.ns_id, uuid=self.this_uuid, command_duration=self.command_timeout)
        fun_test.log(command_result)
        fun_test.simple_assert(command_result["status"], "Attaching BLT volume on DUT instance")

        # Reloading the nvme driver before checking the disk
        if self.reload_after_config:
            command_result = self.host.nvme_restart()
            fun_test.simple_assert(command_result, "Reloading nvme driver")

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
        fs_status = self.host.create_filesystem(self.fs_type, self.nvme_block_device)
        fun_test.test_assert(fs_status, "Creating {} filesystem on BLT volume {}".format(self.fs_type,
                                                                                        self.volume_name))
        command_result = self.host.create_directory(self.mount_point)
        fun_test.test_assert(command_result, "Creating mount point directory {}".format(self.mount_point))
        command_result = self.host.mount_volume(self.nvme_block_device, self.mount_point)
        fun_test.simple_assert(command_result, "Mounting BLT volume {} on {}".format(self.nvme_block_device,
                                                                                    self.mount_point))
        lsblk_output = self.host.lsblk("-b")
        fun_test.test_assert_expected(expected=self.mount_point,
                                      actual=lsblk_output[self.volume_name]["mount_point"],
                                      message="Mounting BLT volume {} on {}".format(self.nvme_block_device,
                                                                                   self.mount_point))
        # Write and read a file into the newly mounted EC volume
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
                              summary="Building EXT2 filesystem on BLT volume and creating file in it of the volume's "
                                      "capacity size",
                              steps="""
        1. Create BLT volume
        2. Attach BLT volume
        3. Create EXT2 filesystem on the BLT volume and mount it
        4. Create a file using dd command
        5. Check that the file is created successfully and find checksum of file 
        6. Read the same file once again and find its checksum.
        7. Compare the checksum obtained in previous two steps
        8. Unmount the BLT volume
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
                              summary="Building EXT3 filesystem on BLT volume and creating file in it of the volume's "
                                      "capacity size",
                              steps="""
          1. Create BLT volume
          2. Attach BLT volume
          3. Create EXT3 filesystem on the BLT volume and mount it
          4. Create a file using dd command
          5. Check that the file is created successfully and find checksum of file 
          6. Read the same file once again and find its checksum.
          7. Compare the checksum obtained in previous two steps
          8. Unmount the BLT volume
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
                              summary="Building EXT4 filesystem on BLT volume and creating file in it of the volume's "
                                      "capacity size",
                              steps="""
          1. Create BLT volume
          2. Attach BLT volume
          3. Create EXT4 filesystem on the BLT volume and mount it
          4. Create a file using dd command
          5. Check that the file is created successfully and find checksum of file 
          6. Read the same file once again and find its checksum.
          7. Compare the checksum obtained in previous two steps
          8. Unmount the BLT volume
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
                              summary="Building XFS filesystem on BLT volume and creating file in it of the volume's "
                                      "capacity size",
                              steps="""
          1. Create BLT volume
          2. Attach BLT volume
          3. Check if Qemu host has 'xfsprogs' package installed, if not install it
          4. Create XFS filesystem on the BLT volume and mount it
          5. Create a file using dd command
          6. Check that the file is created successfully and find checksum of file 
          7. Read the same file once again and find its checksum.
          8. Compare the checksum obtained in previous two steps
          9. Unmount the BLT volume
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
                              summary="Building BTRFS filesystem on BLT volume and creating file in it of the volume's "
                                      "capacity size",
                              steps="""
          1. Create BLT volume
          2. Attach BLT volume
          3. Check if Qemu host has 'btrfs-tools' package installed, if not install it
          4. Create BTRF filesystem on the BLT volume and mount it
          5. Create a file using dd command
          6. Check that the file is created successfully and find checksum of file 
          7. Read the same file once again and find its checksum.
          8. Compare the checksum obtained in previous two steps
          9. Unmount the BLT volume
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
                              summary="Building F2FS filesystem on BLT volume and creating file in it of the volume's "
                                      "capacity size",
                              steps="""
          1. Create BLT volume
          2. Attach BLT volume
          3. Check if Qemu host has 'f2fs-tools' package installed, if not install it
          4. Create F2FS filesystem on the BLT volume and mount it
          5. Create a file using dd command
          6. Check that the file is created successfully and find checksum of file 
          7. Read the same file once again and find its checksum.
          8. Compare the checksum obtained in previous two steps
          9. Unmount the BLT volume
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
                              summary="Building NTFS filesystem on BLT volume and creating file in it of the volume's "
                                      "capacity size",
                              steps="""
        1. Create BLT volume
        2. Attach BLT volume
        3. Create NTFS filesystem on the BLT volume and mount it
        4. Create a file using dd command
        5. Check that the file is created successfully and find checksum of file 
        6. Read the same file once again and find its checksum.
        7. Compare the checksum obtained in previous two steps
        8. Unmount the BLT volume
        9. Detach the BLT volume from DUT
        10. Unconfigure all the BLT volumes
        """)

    def setup(self):
        super(NTFSOnBLT, self).setup()

    def run(self):
        super(NTFSOnBLT, self).run()

    def cleanup(self):
        super(NTFSOnBLT, self).cleanup()


if __name__ == "__main__":

    fsonblt_script = FSOnBLTScript()
    fsonblt_script.add_test_case(Ext2OnBLT())
    fsonblt_script.add_test_case(Ext3OnBLT())
    fsonblt_script.add_test_case(Ext4OnBLT())
    fsonblt_script.add_test_case(XFSOnBLT())
    fsonblt_script.add_test_case(BTRFSOnBLT())
    fsonblt_script.add_test_case(F2FSOnBLT())
    fsonblt_script.add_test_case(NTFSOnBLT())
    fsonblt_script.run()
