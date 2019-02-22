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
        TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()


class FSOnECTestcase(FunTestCase):

    def describe(self):
        pass

    def configure_ec_volume(self, ec_info):

        result = True
        if "ndata" not in ec_info or "nparity" not in ec_info or "capacity" not in ec_info:
            result = False
            fun_test.critical("Mandatory attributes needed for the EC volume creation is missing in ec_info dictionary")
            return result

        ec_info["uuids"] = {}
        ec_info["uuids"]["blt"] = []
        ec_info["uuids"]["ec"] = []
        ec_info["uuids"]["jvol"] = []
        ec_info["uuids"]["lsv"] = []

        # Calculating the sizes of all the volumes together creates the EC or LSV on top EC volume
        ec_info["volume_capacity"] = {}
        ec_info["volume_capacity"]["lsv"] = ec_info["capacity"]
        ec_info["volume_capacity"]["ndata"] = int(round(float(ec_info["capacity"]) / ec_info["ndata"]))
        ec_info["volume_capacity"]["nparity"] = ec_info["volume_capacity"]["ndata"]
        ec_info["volume_capacity"]["ec"] = ec_info["volume_capacity"]["ndata"] * ec_info["ndata"]

        if "use_lsv" in ec_info and ec_info["use_lsv"]:
            fun_test.log("LS volume needs to be configured. So increasing the BLT volume's capacity by 30% and "
                         "rounding that to the nearest 8KB value")
            ec_info["volume_capacity"]["jvol"] = ec_info["lsv_chunk_size"] * ec_info["volume_block"]["lsv"] * \
                                                 ec_info["jvol_size_multiplier"]

            for vtype in ["ndata", "nparity"]:
                tmp = int(round(ec_info["volume_capacity"][vtype] * (1 + ec_info["lsv_pct"])))
                # Aligning the capacity the nearest nKB(volume block size) boundary
                ec_info["volume_capacity"][vtype] = ((tmp + (ec_info["volume_block"][vtype] - 1)) /
                                                     ec_info["volume_block"][vtype]) * \
                                                    ec_info["volume_block"][vtype]

            # Setting the EC volume capacity also to same as the one of ndata volume capacity
            ec_info["volume_capacity"]["ec"] = ec_info["volume_capacity"]["ndata"] * ec_info["ndata"]

        # Configuring ndata and nparity number of BLT volumes
        for vtype in ["ndata", "nparity"]:
            ec_info["uuids"][vtype] = []
            for i in range(ec_info[vtype]):
                this_uuid = utils.generate_uuid()
                ec_info["uuids"][vtype].append(this_uuid)
                ec_info["uuids"]["blt"].append(this_uuid)
                command_result = self.storage_controller.create_volume(
                    type=ec_info["volume_types"][vtype], capacity=ec_info["volume_capacity"][vtype],
                    block_size=ec_info["volume_block"][vtype], name=vtype+"_"+this_uuid[-4:], uuid=this_uuid,
                    command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Creating {} {} {} {} bytes volume on DUT instance".
                                     format(i, vtype, ec_info["volume_types"][vtype], ec_info["volume_capacity"][vtype]))

        # Configuring EC volume on top of BLT volumes
        this_uuid = utils.generate_uuid()
        ec_info["uuids"]["ec"].append(this_uuid)
        command_result = self.storage_controller.create_volume(
            type=ec_info["volume_types"]["ec"], capacity=ec_info["volume_capacity"]["ec"],
            block_size=ec_info["volume_block"]["ec"], name="ec_"+this_uuid[-4:], uuid=this_uuid,
            ndata=ec_info["ndata"], nparity=ec_info["nparity"], pvol_id=ec_info["uuids"]["blt"],
            command_duration=self.command_timeout)
        fun_test.test_assert(command_result["status"], "Creating {}:{} {} bytes EC volume on DUT instance".
                             format(ec_info["ndata"], ec_info["nparity"], ec_info["volume_capacity"]["ec"]))
        ec_info["attach_uuid"] = this_uuid
        ec_info["attach_size"] = ec_info["volume_capacity"]["ec"]

        # Configuring LS volume and its associated journal volume based on the script config setting
        if "use_lsv" in ec_info and ec_info["use_lsv"]:
            ec_info["uuids"]["jvol"] = utils.generate_uuid()
            command_result = self.storage_controller.create_volume(
                type=ec_info["volume_types"]["jvol"], capacity=ec_info["volume_capacity"]["jvol"],
                block_size=ec_info["volume_block"]["jvol"], name="jvol_"+this_uuid[-4:], uuid=ec_info["uuids"]["jvol"],
                command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Creating {} bytes Journal volume on DUT instance".
                                 format(ec_info["volume_capacity"]["jvol"]))

            this_uuid = utils.generate_uuid()
            ec_info["uuids"]["lsv"].append(this_uuid)
            command_result = self.storage_controller.create_volume(
                type=ec_info["volume_types"]["lsv"], capacity=ec_info["volume_capacity"]["lsv"],
                block_size=ec_info["volume_block"]["lsv"], name="lsv_"+this_uuid[-4:], uuid=this_uuid,
                group=ec_info["ndata"], jvol_uuid=ec_info["uuids"]["jvol"], pvol_id=ec_info["uuids"]["ec"],
                command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Creating {} bytes LS volume on DUT instance".
                                 format(ec_info["volume_capacity"]["lsv"]))
            ec_info["attach_uuid"] = this_uuid
            ec_info["attach_size"] = ec_info["volume_capacity"]["lsv"]

    def unconfigure_ec_volume(self, ec_info):

        # Unconfiguring LS volume based on the script config settting
        if "use_lsv" in ec_info and ec_info["use_lsv"]:
            this_uuid = ec_info["uuids"]["lsv"][0]
            command_result = self.storage_controller.delete_volume(
                type=ec_info["volume_types"]["lsv"], capacity=ec_info["volume_capacity"]["lsv"],
                block_size=ec_info["volume_block"]["lsv"], name="lsv_"+this_uuid[-4:], uuid=this_uuid,
                command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.simple_assert(command_result["status"], "Deleting {} bytes LS volume on DUT instance".
                                   format(ec_info["volume_capacity"]["lsv"]))

            this_uuid = ec_info["uuids"]["jvol"]
            command_result = self.storage_controller.delete_volume(
                type=ec_info["volume_types"]["jvol"], capacity=ec_info["volume_capacity"]["jvol"],
                block_size=ec_info["volume_block"]["jvol"], name="jvol_"+this_uuid[-4:], uuid=this_uuid,
                command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Deleting {} bytes Journal volume on DUT instance".
                                 format(ec_info["volume_capacity"]["jvol"]))

        # Unconfiguring EC volume configured on top of BLT volumes
        this_uuid = ec_info["uuids"]["ec"][0]
        command_result = self.storage_controller.delete_volume(
            type=ec_info["volume_types"]["ec"], capacity=ec_info["volume_capacity"]["ec"],
            block_size=ec_info["volume_block"]["ec"], name="ec_"+this_uuid[-4:], uuid=this_uuid,
            command_duration=self.command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Deleting {}:{} {} bytes EC volume on DUT instance".
                             format(ec_info["ndata"], ec_info["nparity"], ec_info["volume_capacity"]["ec"]))

        # Unconfiguring ndata and nparity number of BLT volumes
        for vtype in ["ndata", "nparity"]:
            for i in range(ec_info[vtype]):
                this_uuid = ec_info["uuids"][vtype][i]
                command_result = self.storage_controller.delete_volume(
                    type=ec_info["volume_types"][vtype], capacity=ec_info["volume_capacity"][vtype],
                    block_size=ec_info["volume_block"][vtype], name=vtype+"_"+this_uuid[-4:], uuid=this_uuid,
                    command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Deleting {} {} {} {} bytes volume on DUT instance".
                                     format(i, vtype, ec_info["volume_types"][vtype], ec_info["volume_capacity"][vtype]))

    def do_write_test(self, ndata, nparity):

        # Compute the size of the file based on self.dataset_size_pct % of the total volume size
        self.lsv_chunk_size_in_bytes = self.ec_info["lsv_chunk_size"] * self.ec_info["volume_block"]["lsv"]
        tmp = int(round(self.ec_info["attach_size"] * self.dataset_size_pct))
        self.input_file_size = ((tmp + self.lsv_chunk_size_in_bytes - 1) / self.lsv_chunk_size_in_bytes) * \
                               self.lsv_chunk_size_in_bytes

        # Calculate the block size and count options of dd command based on the stripe size(number of data volumes)
        # and the total file size
        self.dd_write_args["block_size"] = self.ec_info["volume_block"]["ndata"] * self.ec_info["ndata"]
        self.dd_write_args["count"] = self.input_file_size / self.dd_write_args["block_size"]
        io_timeout = self.dd_write_args["count"] / self.test_timeout_ratio
        if io_timeout < 60:
            io_timeout = 60

        # Write a file into the EC volume of size self.input_file_size bytes
        return_size = self.host.dd(timeout=io_timeout, **self.dd_write_args)
        fun_test.test_assert_expected(self.input_file_size, return_size, "Writing {} bytes file into the EC volume".
                                      format(self.input_file_size))
        self.input_md5sum = self.host.md5sum(file_name=self.dd_write_args["output_file"], timeout=io_timeout)
        fun_test.test_assert(self.input_md5sum, "Finding md5sum of input file {}".
                             format(self.dd_write_args["output_file"]))
        # If the testcase is a buffered I/O then flush the kernel buffers/pages after the write operation, so that
        # the entire file will be flushed to the underlying volume
        if "oflag" not in self.dd_write_args:
            self.host.sudo_command("sync", timeout=io_timeout)
            self.host.sudo_command("echo 3 >/proc/sys/vm/drop_caches", timeout=io_timeout)

    def do_read_test(self, ndata, nparity):

        # Calculate the block size and count options of dd command based on the stripe size(number of data volumes)
        # and the total file size
        self.dd_read_args["block_size"] = self.ec_info["volume_block"]["ndata"] * self.ec_info["ndata"]
        self.dd_read_args["count"] = self.input_file_size / self.dd_read_args["block_size"]
        io_timeout = self.dd_read_args["count"] / self.test_timeout_ratio
        if io_timeout < 60:
            io_timeout = 60

        # If the testcase is a buffered I/O then flush the kernel buffers/pages before the readoperation, so that
        # the entire file will be read from the underlying volume
        if "iflag" not in self.dd_read_args:
            self.host.sudo_command("sync", timeout=io_timeout)
            self.host.sudo_command("echo 3 >/proc/sys/vm/drop_caches", timeout=io_timeout)

        # Read the previously written file from the EC volume and calculate the md5sum of the same
        return_size = self.host.dd(timeout=io_timeout, **self.dd_read_args)
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

        # Getting handles to the DUT and the qemu host and preserving their start commands
        self.topology = fun_test.shared_variables["topology"]
        self.dut = self.topology.get_dut_instance(index=0)
        fun_test.test_assert(self.dut, "Retrieved DUT instance")
        self.host = self.topology.get_host_instance(dut_index=0, interface_index=0, host_index=0)
        fun_test.test_assert(self.dut, "Retrieved Qemu Host instance")

        self.storage_controller = fun_test.shared_variables["storage_controller"]
        self.funos_cmdline = fun_test.shared_variables["funos_cmdline"]
        self.qemu_cmdline = fun_test.shared_variables["qemu_cmdline"]

        self.nvme_block_device = self.nvme_device + "n" + str(self.ns_id)
        self.volume_name = self.nvme_block_device.replace("/dev/", "")
        self.volume_attached = False

        # Increasing the nvme driver timeouts for posix platform
        timeout_config = ""
        for key, value in self.nvme_timeouts.items():
            timeout_config += 'options nvme {}="{}"\n'.format(key, value)
        self.host.create_file(file_name=r"/etc/modprobe.d/nvme_core.conf", contents=timeout_config)
        self.host.command("cat /etc/modprobe.d/nvme_core.conf")

        # Configuring the controller
        command_result = self.storage_controller.command(command="enable_counters", legacy=True)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Enabling counters on DUT instance")

    def run(self):

        testcase = self.__class__.__name__
        for combo in self.ec_list:

            combo = eval(combo)
            ndata, nparity = combo

            for size in self.volume_capacity_list:

                # Check whether the current capacity is sufficient enough to create the ndata:nparity EC volume
                # The minimum size of the each individual plex participating in making m:n EC volume is 128 blocks
                min_ec_plex_size = self.min_ec_plex_blocks * self.ec_info["volume_block"]["ec"]
                if int(round(float(size) / ndata)) < min_ec_plex_size:
                    fun_test.critical("Skipping the current capacity {}, because its not sufficient enough to create "
                                      "{}:{} EC volume".format(size, ndata, nparity))
                    continue

                self.ec_info["ndata"] = ndata
                self.ec_info["nparity"] = nparity
                self.ec_info["capacity"] = size

                fun_test.log("EC details before configuring EC Volume:")
                for k, v in self.ec_info.items():
                    fun_test.log("{}: {}".format(k, v))

                # Creating ndata:npartiy EC volume
                self.configure_ec_volume(self.ec_info)

                fun_test.log("EC details after configuring EC Volume:")
                for k, v in self.ec_info.items():
                    fun_test.log("{}: {}".format(k, v))

                # Attaching/Exporting the EC/LS volume to the external server
                command_result = self.storage_controller.volume_attach_pcie(
                    ns_id=self.ns_id, uuid=self.ec_info["attach_uuid"], command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.simple_assert(command_result["status"], "Attaching EC/LS volume on DUT instance")

                # disabling the error_injection for the EC volume
                command_result = {}
                command_result = self.storage_controller.poke("params/ecvol/error_inject 0")
                fun_test.log(command_result)
                fun_test.simple_assert(command_result["status"],
                                       "Disabling error_injection for EC volume on DUT instance")

                # Ensuring that the error_injection got disabled properly
                fun_test.sleep("Sleeping for a second to disable the error_injection", 1)
                command_result = {}
                command_result = self.storage_controller.peek("params/ecvol")
                fun_test.log(command_result)
                fun_test.simple_assert(command_result["status"],
                                       "Retrieving error_injection status on DUT instance")
                fun_test.test_assert_expected(actual=int(command_result["data"]["error_inject"]), expected=0,
                                              message="Ensuring error_injection got disabled")

                # Reloading the nvme driver before checking the disk and decrease the queue length
                if self.reload_after_config:
                    command_result = self.host.nvme_restart()
                    fun_test.simple_assert(command_result, "Reloading nvme driver")
                    fun_test.sleep("Waiting for the nvme driver reload to complete", 5)
                    self.host.sudo_command("echo 4 >/sys/block/nvme0n1/queue/nr_requests")

                # Checking that the volume is accessible to the host
                lsblk_output = self.host.lsblk("-b")
                fun_test.simple_assert(self.volume_name in lsblk_output, "{} device available".format(self.volume_name))
                fun_test.test_assert_expected(expected="disk", actual=lsblk_output[self.volume_name]["type"],
                                              message="{} volume type check".format(self.volume_name))
                fun_test.test_assert_expected(expected=self.ec_info["attach_size"],
                                              actual=lsblk_output[self.volume_name]["size"],
                                              message="{} volume size check".format(self.volume_name))

                # Creating self.fs_type filesystem in EC volume and mount the same
                # Checking if the filesystem type is XFS, if so at first ensure the xfs is installed in the qemu host
                if self.fs_type == "xfs":
                    install_status = self.host.install_package("xfsprogs")
                    fun_test.test_assert(install_status, "Installing XFS Package")
                # Set the timeout for the filesystem create command based on its size
                fs_create_timeout = (size / 1073741824) * 180
                if not fs_create_timeout:
                    fs_create_timeout = 120
                fs_status = self.host.create_filesystem(self.fs_type, self.nvme_block_device, timeout=fs_create_timeout)
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
                    this_uuid = self.ec_info["uuids"]["ec"][0]
                    command_result = self.storage_controller.delete_volume(
                        type=self.ec_info["volume_types"]["ec"], capacity=self.ec_info["volume_capacity"]["ec"],
                        block_size=self.ec_info["volume_block"]["ec"], name="ec_"+this_uuid[-4:], uuid=this_uuid,
                        command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert_expected(expected=False, actual=command_result["status"],
                                                  message="Deleting EC volume without detaching & deleting the LSV in "
                                                          "first from DUT instance")
                    if self.use_lsv:
                        this_uuid = self.ec_info["uuids"]["lsv"][0]
                        command_result = self.storage_controller.delete_volume(
                            type=self.ec_info["volume_types"]["lsv"], capacity=self.ec_info["volume_capacity"]["lsv"],
                            block_size=self.ec_info["volume_block"]["lsv"], name="lsv_"+this_uuid[-4:], uuid=this_uuid,
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
                # Detaching and Unconfiguring all the volumes
                command_result = self.storage_controller.volume_detach_pcie(
                    ns_id=self.ns_id, uuid=self.ec_info["attach_uuid"], command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Detaching LS/EC volume on DUT")

                self.unconfigure_ec_volume(self.ec_info)

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


class ECVolumeCreateDeleteInBatch(FSOnECTestcase):
    def describe(self):
        self.set_test_details(id=9,
                              summary="Configuring and UnConfiguring EC volume in a batch without attaching them to an "
                                      "end host",
                              steps="""
        1. Run the outer loop for the given list of k:m EC volumes.
        2. Run the inner loop for the different capacity.
        3. Configure k:m EC volume of size N bytes and on top of it create a LSV as well.
        4. Unconfigure all the BLT, EC, Journal and LS volumes.
        5. Repeat #1 - #5 for loop number of times.
        """)

    def setup(self):
        super(ECVolumeCreateDeleteInBatch, self).setup()

    def run(self):
        testcase = self.__class__.__name__

        for i in range(self.loop):
            for combo in self.ec_list:
                combo = eval(combo)
                ndata, nparity = combo
                self.cur_ec_info = {}
                for index, size in enumerate(self.volume_capacity_list):
                    # Check whether the current capacity is sufficient enough to create the ndata:nparity EC volume
                    # The minimum size of the each individual plex participating in making m:n EC volume is 128 blocks
                    min_ec_plex_size = self.min_ec_plex_blocks * self.ec_info["volume_block"]["ec"]
                    if int(round(float(size) / ndata)) < min_ec_plex_size:
                        fun_test.critical("Skipping the current capacity {}, because its not sufficient enough to "
                                          "create {}:{} EC volume".format(size, ndata, nparity))
                        continue
                    self.cur_ec_info[index] = {}
                    self.cur_ec_info[index] = copy.deepcopy(self.ec_info)
                    self.cur_ec_info[index]["ndata"] = ndata
                    self.cur_ec_info[index]["nparity"] = nparity
                    self.cur_ec_info[index]["capacity"] = size
                    # Creating ndata:npartiy EC volume
                    self.configure_ec_volume(self.cur_ec_info[index])
                for index, size in enumerate(self.volume_capacity_list):
                    # Check whether the current capacity is sufficient enough to create the ndata:nparity EC volume
                    # The minimum size of the each individual plex participating in making m:n EC volume is 128 blocks
                    min_ec_plex_size = self.min_ec_plex_blocks * self.ec_info["volume_block"]["ec"]
                    if int(round(float(size) / ndata)) < min_ec_plex_size:
                        fun_test.critical("Skipping the current capacity {}, because its not sufficient enough to "
                                          "create {}:{} EC volume".format(size, ndata, nparity))
                        continue
                    # Creating ndata:npartiy EC volume
                    self.unconfigure_ec_volume(self.cur_ec_info[index])

    def cleanup(self):
        super(ECVolumeCreateDeleteInBatch, self).cleanup()


if __name__ == "__main__":

    fsonec_script = FSOnECScript()
    fsonec_script.add_test_case(Ext2OnECBufferedWriteDetachFirst())
    fsonec_script.add_test_case(Ext2OnECDirectWriteDeleteFirst())
    fsonec_script.add_test_case(Ext3OnECBufferedWriteDetachFirst())
    fsonec_script.add_test_case(Ext3OnECDirectWriteDeleteFirst())
    fsonec_script.add_test_case(Ext4OnECBufferedWriteDetachFirst())
    fsonec_script.add_test_case(Ext4OnECDirectWriteDeleteFirst())
    fsonec_script.add_test_case(XFSOnECBufferedWriteDetachFirst())
    fsonec_script.add_test_case(XFSOnECDirectWriteDeleteFirst())
    fsonec_script.add_test_case(ECVolumeCreateDeleteInBatch())
    fsonec_script.run()
