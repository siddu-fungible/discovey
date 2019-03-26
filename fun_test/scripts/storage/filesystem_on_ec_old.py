from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut, DutInterface
from lib.fun.f1 import F1
from lib.host.storage_controller import StorageController
from lib.templates.storage.qemu_storage_template import QemuStorageTemplate
from lib.orchestration.simulation_orchestrator import DockerContainerOrchestrator
from web.fun_test.analytics_models_helper import VolumePerformanceHelper
import re

'''
Script to track the performance of various read write combination of Erasure Coded volume using FIO
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


class FSOnECScript(FunTestScript):
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
        pass


class FSOnECTestcase(FunTestCase):

    def describe(self):
        pass

    def configure_ec_volume(self, ndata, nparity, capacity):

        self.num_volumes = {}
        self.num_volumes["ndata"] = ndata
        self.num_volumes["nparity"] = nparity

        self.uuids = {}
        self.uuids["blt"] = []
        self.uuids["ec"] = []
        self.uuids["jvol"] = []
        self.uuids["lsv"] = []

        # Calculating the sizes of all the volumes together creates the EC or LSV on top EC volume
        self.calc_volume_capacity = {}
        self.calc_volume_capacity["lsv"] = capacity
        self.calc_volume_capacity["ndata"] = int(round(float(capacity) / ndata))
        self.calc_volume_capacity["nparity"] = int(round(float(capacity) / ndata))
        self.calc_volume_capacity["ec"] = self.calc_volume_capacity["ndata"] * self.num_volumes["ndata"]

        if self.use_lsv:
            fun_test.log("LS volume needs to be configured. So increasing the BLT volume's capacity by 30% and "
                         "rounding that to the nearest 8KB value")
            self.calc_volume_capacity["jvol"] = self.lsv_chunk_size * self.volume_block["lsv"] *\
                                                self.jvol_size_multiplier

            for vtype in ["ndata", "nparity"]:
                tmp = int(round(self.calc_volume_capacity[vtype] * (1 + self.lsv_pct)))
                # Aligning the capacity the nearest nKB(volume block size) boundary
                self.calc_volume_capacity[vtype] = ((tmp + (self.volume_block[vtype] - 1)) / self.volume_block[vtype]) \
                                                   * self.volume_block[vtype]

            # Setting the EC volume capacity also to same as the one of ndata volume capacity
            self.calc_volume_capacity["ec"] = self.calc_volume_capacity["ndata"] * self.num_volumes["ndata"]

        # Configuring ndata and nparity number of BLT volumes
        for vtype in ["ndata", "nparity"]:
            self.uuids[vtype] = []
            for i in range(self.num_volumes[vtype]):
                this_uuid = utils.generate_uuid()
                self.uuids[vtype].append(this_uuid)
                self.uuids["blt"].append(this_uuid)
                command_result = self.storage_controller.create_volume(
                    type=self.volume_types[vtype], capacity=self.calc_volume_capacity[vtype],
                    block_size=self.volume_block[vtype], name=vtype+str(i), uuid=this_uuid,
                    command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Create {} {} {} volume on DUT instance".
                                       format(i, vtype, self.volume_types[vtype]))

        # Configuring EC volume on top of BLT volumes
        this_uuid = utils.generate_uuid()
        self.uuids["ec"].append(this_uuid)
        try:
            command_result = self.storage_controller.create_volume(
                type=self.volume_types["ec"], capacity=self.calc_volume_capacity["ec"],
                block_size=self.volume_block["ec"], name="ec1", uuid=this_uuid, ndata=self.num_volumes["ndata"],
                nparity=self.num_volumes["nparity"], pvol_id=self.uuids["blt"], command_duration=self.command_timeout)
            fun_test.test_assert(command_result["status"], "Create EC volume on DUT instance")
        except Exception as e:
            # EC command creation didn't received any response. So going to check whether the command actually failed
            # or the command got executed properly, but it didn't received the response only
            fun_test.log("EC volume creation command didn't received any response. So checking the whether the volume "
                         "is actually created or not")
            storage_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", self.volume_types["ec"], this_uuid,
                                                         "stats")
            command_result = self.storage_controller.peek(storage_props_tree)
            fun_test.test_assert(command_result["status"], "Create EC volume on DUT instance")
        attach_uuid = this_uuid
        self.attach_size = self.calc_volume_capacity["ec"]

        # Configuring LS volume and its associated journal volume based on the script config setting
        if self.use_lsv:
            self.uuids["jvol"] = utils.generate_uuid()
            command_result = self.storage_controller.create_volume(
                type=self.volume_types["jvol"], capacity=self.calc_volume_capacity["jvol"],
                block_size=self.volume_block["jvol"], name="jvol1", uuid=self.uuids["jvol"],
                command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Create Journal volume on DUT instance")

            this_uuid = utils.generate_uuid()
            self.uuids["lsv"].append(this_uuid)
            command_result = self.storage_controller.create_volume(
                type=self.volume_types["lsv"], capacity=self.calc_volume_capacity["lsv"],
                block_size=self.volume_block["lsv"], name="lsv1", uuid=this_uuid, group=self.num_volumes["ndata"],
                jvol_uuid=self.uuids["jvol"], pvol_id=self.uuids["ec"], command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Create LS volume on DUT instance")
            attach_uuid = this_uuid
            self.attach_size = self.calc_volume_capacity["lsv"]

        # Attaching/Exporting the EC/LS volume to the external server
        command_result = self.storage_controller.volume_attach_pcie(ns_id=self.ns_id, uuid=attach_uuid,
                                                                    command_duration=self.command_timeout)
        fun_test.log(command_result)
        fun_test.simple_assert(command_result["status"], "Attaching EC/LS volume on DUT instance")

        # disabling the error_injection for the EC volume
        command_result = {}
        command_result = self.storage_controller.poke("params/ecvol/error_inject 0")
        fun_test.log(command_result)
        fun_test.simple_assert(command_result["status"], "Disabling error_injection for EC volume on DUT instance")

        # Ensuring that the error_injection got disabled properly
        fun_test.sleep("Sleeping for a second to disable the error_injection", 1)
        command_result = {}
        command_result = self.storage_controller.peek("params/ecvol")
        fun_test.log(command_result)
        fun_test.simple_assert(command_result["status"], "Retrieving error_injection status on DUT instance")
        fun_test.test_assert_expected(actual=int(command_result["data"]["error_inject"]), expected=0,
                                      message="Ensuring error_injection got disabled")

    def unconfigure_ec_volume(self, data, parity):

        # Unconfiguring LS volume based on the script config settting
        if self.use_lsv:
            detach_uid = self.uuids["lsv"][0]
            command_result = self.storage_controller.volume_detach_pcie(
                ns_id=self.ns_id, uuid=detach_uid, command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Detaching LS volume on DUT")

            this_uuid = self.uuids["lsv"][0]
            command_result = self.storage_controller.delete_volume(
                type=self.volume_types["lsv"], capacity=self.calc_volume_capacity["lsv"],
                block_size=self.volume_block["lsv"], name="lsv1", uuid=this_uuid, command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.simple_assert(command_result["status"], "Delete LS volume on DUT instance")

            this_uuid = self.uuids["jvol"]
            command_result = self.storage_controller.delete_volume(
                type=self.volume_types["jvol"], capacity=self.calc_volume_capacity["jvol"],
                block_size=self.volume_block["jvol"], name="jvol1", uuid=this_uuid,
                command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Delete Journal volume on DUT instance")
        else:
            detach_uid = self.uuids["ec"][0]
            command_result = self.storage_controller.volume_detach_pcie(
                ns_id=self.ns_id, uuid=detach_uid, command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Detaching LS volume on DUT")

        # Unconfiguring EC volume configured on top of BLT volumes
        this_uuid = self.uuids["ec"][0]
        command_result = self.storage_controller.delete_volume(
            type=self.volume_types["ec"], capacity=self.calc_volume_capacity["ec"], block_size=self.volume_block["ec"],
            name="ec1", uuid=this_uuid, command_duration=self.command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Delete EC volume on DUT instance")

        # Unconfiguring ndata and nparity number of BLT volumes
        for vtype in ["ndata", "nparity"]:
            for i in range(self.num_volumes[vtype]):
                this_uuid = self.uuids[vtype][i]
                self.uuids["blt"].append(this_uuid)
                command_result = self.storage_controller.delete_volume(
                    type=self.volume_types[vtype], capacity=self.calc_volume_capacity[vtype],
                    block_size=self.volume_block[vtype], name=vtype+str(i), uuid=this_uuid,
                    command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Delete {} {} BLT volume on DUT instance".
                                       format(i, vtype))

    def do_write_test(self, ndata, nparity):

        # Compute the size of the file based on self.dataset_size_pct % of the total volume size
        self.lsv_chunk_size_in_bytes = self.lsv_chunk_size * self.volume_block["lsv"]
        tmp = int(round(self.attach_size * self.dataset_size_pct))
        self.input_file_size = ((tmp + self.lsv_chunk_size_in_bytes - 1) / self.lsv_chunk_size_in_bytes) * \
                               self.lsv_chunk_size_in_bytes

        # Calculate the block size and count options of dd command based on the stripe size(number of data volumes)
        # and the total file size
        self.dd_write_args["block_size"] = self.volume_block["ndata"] * ndata
        count = self.input_file_size / self.dd_write_args["block_size"]
        cmd_timeout = count / self.test_timeout_ratio

        # Write a file into the EC volume of size self.input_file_size bytes
        return_size = self.host.dd(count=count, timeout=cmd_timeout, **self.dd_write_args)
        fun_test.test_assert_expected(self.input_file_size, return_size, "Writing {} bytes file into the EC volume".
                                      format(self.input_file_size))
        self.input_md5sum = self.host.md5sum(file_name=self.dd_write_args["output_file"])
        fun_test.test_assert(self.input_md5sum, "Finding md5sum of input file {}".
                             format(self.dd_write_args["output_file"]))
        # If the testcase is a buffered I/O then flush the kernel buffers/pages after the write operation, so that
        # the entire file will be flushed to the underlying volume
        if "oflag" not in self.dd_write_args:
            self.host.sudo_command("sync")
            self.host.sudo_command("echo 3>/proc/sys/vm/drop_caches")

    def do_read_test(self, ndata, nparity):

        # Calculate the block size and count options of dd command based on the stripe size(number of data volumes)
        # and the total file size
        self.dd_read_args["block_size"] = self.volume_block["ndata"] * ndata
        count = self.input_file_size / self.dd_read_args["block_size"]
        cmd_timeout = count / self.test_timeout_ratio

        # If the testcase is a buffered I/O then flush the kernel buffers/pages before the readoperation, so that
        # the entire file will be read from the underlying volume
        if "iflag" not in self.dd_read_args:
            self.host.sudo_command("sync")
            self.host.sudo_command("echo 3>/proc/sys/vm/drop_caches")

        # Read the previously written file from the EC volume and calculate the md5sum of the same
        return_size = self.host.dd(count=count, timeout=cmd_timeout, **self.dd_read_args)
        fun_test.test_assert_expected(self.input_file_size, return_size, "Reading {} bytes file into the EC volume".
                                      format(self.input_file_size))
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

    def run(self):

        testcase = self.__class__.__name__

        self.unconfig_result = {}
        self.write_result = {}
        self.read_result = {}

        for combo in self.ec_list:

            combo = eval(combo)
            ndata, nparity = combo

            self.unconfig_result[ndata] = {}
            self.write_result[ndata] = {}
            self.read_result[ndata] = {}
            self.unconfig_result[ndata][nparity] = {}
            self.write_result[ndata][nparity] = {}
            self.read_result[ndata][nparity] = {}

            for size in self.volume_capacity_list:
                self.unconfig_result[ndata][nparity][size] = True
                self.write_result[ndata][nparity][size] = True
                self.read_result[ndata][nparity][size] = True

                # Check whether the current capacity is sufficient enough to create the ndata:nparity EC volume
                # The minimum size of the each individual plex participating in making m:n EC volume is 128 blocks
                min_ec_plex_size = self.min_ec_plex_blocks * self.volume_block["ec"]
                if int(round(float(size) / ndata)) < min_ec_plex_size:
                    fun_test.critical("Skipping the current capacity {}, because its not sufficient enough to create "
                                      "{}:{} EC volume".format(size, ndata, nparity))
                    continue

                # Creating ndata:npartiy EC volume
                self.configure_ec_volume(ndata, nparity, size)

                # Reloading the nvme driver before checking the disk
                if self.reload_after_config:
                    command_result = self.host.nvme_restart()
                    fun_test.simple_assert(command_result, "Reloading nvme driver")

                # Checking that the volume is accessible to the host
                lsblk_output = self.host.lsblk("-b")
                fun_test.simple_assert(self.volume_name in lsblk_output, "{} device available".format(self.volume_name))
                fun_test.test_assert_expected(expected="disk", actual=lsblk_output[self.volume_name]["type"],
                                              message="{} volume type check".format(self.volume_name))
                fun_test.test_assert_expected(expected=self.attach_size, actual=lsblk_output[self.volume_name]["size"],
                                              message="{} volume size check".format(self.volume_name))

                # Creating self.fs_type filesystem in EC volume and mount the same
                # Checking if the filesystem type is XFS, if so at first ensure the xfs is installed in the qemu host
                if self.fs_type == "xfs":
                    install_status = self.host.install_package("xfsprogs")
                    fun_test.test_assert(install_status, "Installing XFS Package")
                fs_status = self.host.create_filesystem(self.fs_type, self.nvme_block_device)
                fun_test.test_assert(fs_status, "Creating {} filesystem on EC volume {}".format(self.fs_type,
                                                                                                self.volume_name))
                command_result = self.host.create_directory(self.mount_point)
                fun_test.test_assert(command_result, "Creating mount point directory {}".format(self.mount_point))
                command_result = self.host.mount_volume(self.nvme_block_device, self.mount_point)
                fun_test.simple_assert(command_result, "Mounting EC volume {} on {}".format(self.nvme_block_device,
                                                                                            self.mount_point))
                lsblk_output = self.host.lsblk("-b")
                fun_test.test_assert_expected(expected=self.mount_point,
                                              actual=lsblk_output[self.volume_name]["mount_point"],
                                              message="Mounting EC volume {} on {}".format(self.nvme_block_device,
                                                                                           self.mount_point))
                # Write and read a file into the newly mounted EC volume
                self.do_write_test(ndata, nparity)
                self.do_read_test(ndata, nparity)

                # Try to delete the LSV and the EC volume without detaching the LSV
                # The expectation here is that the below deletes has to fail
                if hasattr(self, "delete_before_detach") and self.delete_before_detach:
                    this_uuid = self.uuids["ec"][0]
                    command_result = self.storage_controller.delete_volume(
                        type=self.volume_types["ec"], capacity=self.calc_volume_capacity["ec"],
                        block_size=self.volume_block["ec"], name="ec1", uuid=this_uuid,
                        command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert_expected(expected=False, actual=command_result["status"],
                                                  message="Deleting EC volume without detaching & deleting the LSV in "
                                                          "first from DUT instance")
                    if self.use_lsv:
                        this_uuid = self.uuids["lsv"][0]
                        command_result = self.storage_controller.delete_volume(
                            type=self.volume_types["lsv"], capacity=self.calc_volume_capacity["lsv"],
                            block_size=self.volume_block["lsv"], name="lsv1", uuid=this_uuid,
                            command_duration=self.command_timeout)
                        fun_test.log(command_result)
                        fun_test.test_assert_expected(expected=False, actual=command_result["status"],
                                                      message="Deleting LS volume without detaching it first from DUT "
                                                              "instance")
                # Now unmount the EC volume
                command_result = self.host.unmount_volume(volume=self.nvme_block_device)
                fun_test.simple_assert(command_result, "Unmounting EC volume {} from {}".format(self.nvme_block_device,
                                                                                                self.mount_point))
                lsblk_output = self.host.lsblk("-b")
                fun_test.test_assert_expected(expected=None,
                                              actual=lsblk_output[self.volume_name]["mount_point"],
                                              message="Unmounting EC volume {} from {}".format(self.nvme_block_device,
                                                                                               self.mount_point))
                # Unconfiguring the current EC volume in the correct order
                self.unconfigure_ec_volume(ndata, nparity)

    def cleanup(self):
        pass


class Ext2OnECBufferedWriteDetachFirst(FSOnECTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Building EXT2 filesystem on different m:n EC volume of varying capacity and "
                                      "creating file in it whose size equal to 50% of the volume's capacity through "
                                      "Buffered I/O",
                              steps="""
        1. Run the outer loop for the given list of k:m EC volumes.
        2. Run the inner loop for the different capacity.
        3. Configure k:m EC volume of size N bytes and on top of it create a LSV as well.
        4. Attach the above LSV to the PCIe connected host.
        5. Create EXT2 filesystem on the LSV volume and mount the same.
        6. Create a file of size N/2 bytes using dd command - Buffered I/O - No oflag set.
        7. Check that the file is created successfully and find its checksum. 
        8. Read the same file once again after flushing the kernel pages and find its checksum.
        9. Compare the checksum obtained in step #6 & #7.
        10. Unmount the LSV.
        11. Detach the LSV from DUT.
        12. Unconfigure all the BLT, EC, Journal and LS volumes.
        """)

    def setup(self):
        super(Ext2OnECBufferedWriteDetachFirst, self).setup()

    def run(self):
        super(Ext2OnECBufferedWriteDetachFirst, self).run()

    def cleanup(self):
        super(Ext2OnECBufferedWriteDetachFirst, self).cleanup()


class Ext2OnECDirectWriteDeleteFirst(FSOnECTestcase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Building EXT2 filesystem on different m:n EC volume of varying capacity and "
                                      "creating file in it whose size equal to 50% of the volume's capacity through "
                                      "Direct I/O",
                              steps="""
        1. Run the outer loop for the given list of k:m EC volumes.
        2. Run the inner loop for the different capacity.
        3. Configure k:m EC volume of size N bytes and on top of it create a LSV as well.
        4. Attach the above LSV to the PCIe connected host.
        5. Create EXT2 filesystem on the LSV volume and mount the same.
        6. Create a file of size N/2 bytes using dd command - Direct I/O - No oflag set.
        7. Check that the file is created successfully and find its checksum. 
        8. Read the same file once again after flushing the kernel pages and find its checksum.
        9. Compare the checksum obtained in step #6 & #7.
        10. Without unmounting the LSV from the host and detaching the same from the DUT, try to delete the LSV and EC.
        11. Unmount the LSV.
        12. Detach the LSV from DUT.
        13. Unconfigure all the BLT, EC, Journal and LS volumes.
        """)

    def setup(self):
        super(Ext2OnECDirectWriteDeleteFirst, self).setup()

    def run(self):
        super(Ext2OnECDirectWriteDeleteFirst, self).run()

    def cleanup(self):
        super(Ext2OnECDirectWriteDeleteFirst, self).cleanup()


class Ext3OnECBufferedWriteDetachFirst(FSOnECTestcase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Building EXT3 filesystem on different m:n EC volume of varying capacity and "
                                      "creating file in it whose size equal to 50% of the volume's capacity through "
                                      "Buffered I/O",
                              steps="""
        1. Run the outer loop for the given list of k:m EC volumes.
        2. Run the inner loop for the different capacity.
        3. Configure k:m EC volume of size N bytes and on top of it create a LSV as well.
        4. Attach the above LSV to the PCIe connected host.
        5. Create EXT3 filesystem on the LSV volume and mount the same.
        6. Create a file of size N/2 bytes using dd command - Buffered I/O - No oflag set.
        7. Check that the file is created successfully and find its checksum. 
        8. Read the same file once again after flushing the kernel pages and find its checksum.
        9. Compare the checksum obtained in step #6 & #7.
        10. Unmount the LSV.
        11. Detach the LSV from DUT.
        12. Unconfigure all the BLT, EC, Journal and LS volumes.
        """)

    def setup(self):
        super(Ext3OnECBufferedWriteDetachFirst, self).setup()

    def run(self):
        super(Ext3OnECBufferedWriteDetachFirst, self).run()

    def cleanup(self):
        super(Ext3OnECBufferedWriteDetachFirst, self).cleanup()


class Ext3OnECDirectWriteDeleteFirst(FSOnECTestcase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Building EXT3 filesystem on different m:n EC volume of varying capacity and "
                                      "creating file in it whose size equal to 50% of the volume's capacity through "
                                      "Direct I/O",
                              steps="""
        1. Run the outer loop for the given list of k:m EC volumes.
        2. Run the inner loop for the different capacity.
        3. Configure k:m EC volume of size N bytes and on top of it create a LSV as well.
        4. Attach the above LSV to the PCIe connected host.
        5. Create EXT3 filesystem on the LSV volume and mount the same.
        6. Create a file of size N/2 bytes using dd command - Direct I/O - No oflag set.
        7. Check that the file is created successfully and find its checksum. 
        8. Read the same file once again after flushing the kernel pages and find its checksum.
        9. Compare the checksum obtained in step #6 & #7.
        10. Without unmounting the LSV from the host and detaching the same from the DUT, try to delete the LSV and EC.
        11. Unmount the LSV.
        12. Detach the LSV from DUT.
        13. Unconfigure all the BLT, EC, Journal and LS volumes.
        """)

    def setup(self):
        super(Ext3OnECDirectWriteDeleteFirst, self).setup()

    def run(self):
        super(Ext3OnECDirectWriteDeleteFirst, self).run()

    def cleanup(self):
        super(Ext3OnECDirectWriteDeleteFirst, self).cleanup()


class Ext4OnECBufferedWriteDetachFirst(FSOnECTestcase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Building EXT4 filesystem on different m:n EC volume of varying capacity and "
                                      "creating file in it whose size equal to 50% of the volume's capacity through "
                                      "Buffered I/O",
                              steps="""
        1. Run the outer loop for the given list of k:m EC volumes.
        2. Run the inner loop for the different capacity.
        3. Configure k:m EC volume of size N bytes and on top of it create a LSV as well.
        4. Attach the above LSV to the PCIe connected host.
        5. Create EXT4 filesystem on the LSV volume and mount the same.
        6. Create a file of size N/2 bytes using dd command - Buffered I/O - No oflag set.
        7. Check that the file is created successfully and find its checksum. 
        8. Read the same file once again after flushing the kernel pages and find its checksum.
        9. Compare the checksum obtained in step #6 & #7.
        10. Unmount the LSV.
        11. Detach the LSV from DUT.
        12. Unconfigure all the BLT, EC, Journal and LS volumes.
        """)

    def setup(self):
        super(Ext4OnECBufferedWriteDetachFirst, self).setup()

    def run(self):
        super(Ext4OnECBufferedWriteDetachFirst, self).run()

    def cleanup(self):
        super(Ext4OnECBufferedWriteDetachFirst, self).cleanup()


class Ext4OnECDirectWriteDeleteFirst(FSOnECTestcase):
    def describe(self):
        self.set_test_details(id=6,
                              summary="Building EXT4 filesystem on different m:n EC volume of varying capacity and "
                                      "creating file in it whose size equal to 50% of the volume's capacity through "
                                      "Direct I/O",
                              steps="""
        1. Run the outer loop for the given list of k:m EC volumes.
        2. Run the inner loop for the different capacity.
        3. Configure k:m EC volume of size N bytes and on top of it create a LSV as well.
        4. Attach the above LSV to the PCIe connected host.
        5. Create EXT4 filesystem on the LSV volume and mount the same.
        6. Create a file of size N/2 bytes using dd command - Direct I/O - No oflag set.
        7. Check that the file is created successfully and find its checksum. 
        8. Read the same file once again after flushing the kernel pages and find its checksum.
        9. Compare the checksum obtained in step #6 & #7.
        10. Without unmounting the LSV from the host and detaching the same from the DUT, try to delete the LSV and EC.
        11. Unmount the LSV.
        12. Detach the LSV from DUT.
        13. Unconfigure all the BLT, EC, Journal and LS volumes.
        """)

    def setup(self):
        super(Ext4OnECDirectWriteDeleteFirst, self).setup()

    def run(self):
        super(Ext4OnECDirectWriteDeleteFirst, self).run()

    def cleanup(self):
        super(Ext4OnECDirectWriteDeleteFirst, self).cleanup()


class XFSOnECBufferedWriteDetachFirst(FSOnECTestcase):
    def describe(self):
        self.set_test_details(id=7,
                              summary="Building XFS filesystem on different m:n EC volume of varying capacity and "
                                      "creating file in it whose size equal to 50% of the volume's capacity through "
                                      "Buffered I/O",
                              steps="""
        1. Run the outer loop for the given list of k:m EC volumes.
        2. Run the inner loop for the different capacity.
        3. Configure k:m EC volume of size N bytes and on top of it create a LSV as well.
        4. Attach the above LSV to the PCIe connected host.
        5. Create XFS filesystem on the LSV volume and mount the same.
        6. Create a file of size N/2 bytes using dd command - Buffered I/O - No oflag set.
        7. Check that the file is created successfully and find its checksum. 
        8. Read the same file once again after flushing the kernel pages and find its checksum.
        9. Compare the checksum obtained in step #6 & #7.
        10. Unmount the LSV.
        11. Detach the LSV from DUT.
        12. Unconfigure all the BLT, EC, Journal and LS volumes.
        """)

    def setup(self):
        super(XFSOnECBufferedWriteDetachFirst, self).setup()

    def run(self):
        super(XFSOnECBufferedWriteDetachFirst, self).run()

    def cleanup(self):
        super(XFSOnECBufferedWriteDetachFirst, self).cleanup()


class XFSOnECDirectWriteDeleteFirst(FSOnECTestcase):
    def describe(self):
        self.set_test_details(id=8,
                              summary="Building XFS filesystem on different m:n EC volume of varying capacity and "
                                      "creating file in it whose size equal to 50% of the volume's capacity through "
                                      "Direct I/O",
                              steps="""
        1. Run the outer loop for the given list of k:m EC volumes.
        2. Run the inner loop for the different capacity.
        3. Configure k:m EC volume of size N bytes and on top of it create a LSV as well.
        4. Attach the above LSV to the PCIe connected host.
        5. Create XFS filesystem on the LSV volume and mount the same.
        6. Create a file of size N/2 bytes using dd command - Direct I/O - No oflag set.
        7. Check that the file is created successfully and find its checksum. 
        8. Read the same file once again after flushing the kernel pages and find its checksum.
        9. Compare the checksum obtained in step #6 & #7.
        10. Without unmounting the LSV from the host and detaching the same from the DUT, try to delete the LSV and EC.
        11. Unmount the LSV.
        12. Detach the LSV from DUT.
        13. Unconfigure all the BLT, EC, Journal and LS volumes.
        """)

    def setup(self):
        super(XFSOnECDirectWriteDeleteFirst, self).setup()

    def run(self):
        super(XFSOnECDirectWriteDeleteFirst, self).run()

    def cleanup(self):
        super(XFSOnECDirectWriteDeleteFirst, self).cleanup()


if __name__ == "__main__":

    fsonec_script = FSOnECScript()
    # fsonec_script.add_test_case(Ext2OnECBufferedWriteDetachFirst())
    #fsonec_script.add_test_case(Ext2OnECDirectWriteDeleteFirst())
    # fsonec_script.add_test_case(Ext3OnECBufferedWriteDetachFirst())
    # fsonec_script.add_test_case(Ext3OnECDirectWriteDeleteFirst())
    # fsonec_script.add_test_case(Ext4OnECBufferedWriteDetachFirst())
    # fsonec_script.add_test_case(Ext4OnECDirectWriteDeleteFirst())
    # fsonec_script.add_test_case(XFSOnECBufferedWriteDetachFirst())
    fsonec_script.add_test_case(XFSOnECDirectWriteDeleteFirst())
    fsonec_script.run()
