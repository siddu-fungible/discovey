from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut, DutInterface
from lib.fun.f1 import F1
from lib.host.storage_controller import StorageController
from lib.templates.storage.qemu_storage_template import QemuStorageTemplate
from lib.orchestration.simulation_orchestrator import DockerContainerOrchestrator
import re

'''
Script to test nvme writes and reads with compression enabled EC/LSV in NVME over PCIe scenario 
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
                    "vm_start_mode": "VM_START_MODE_NORMAL",
                    "vm_host_os": "fungible_yocto"
                }
            },
            "start_mode": F1.START_MODE_NORMAL
        }
    }
}


class ECinQemuScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Start 1 POSIXs and allocate a Linux instance 
        2. Make the Linux instance available for the testcase
        """)

    def setup(self):
        topology_obj_helper = TopologyHelper(spec=topology_dict)
        topology = topology_obj_helper.deploy()
        fun_test.test_assert(topology, "Ensure deploy is successful")
        fun_test.shared_variables["topology"] = topology

    def cleanup(self):
        TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()
        # pass


class ECinQemuTestcase(FunTestCase):

    def describe(self):
        pass

    def check_num_dpcsh_cmds(self):

        self.num_dpcsh_cmds += 1
        fun_test.log("DPCsh command executed: {}".format(self.num_dpcsh_cmds))
        if self.track_num_cmds:
            if self.num_dpcsh_cmds >= self.max_dpcsh_cmds:
                self.qemu.start_dpcsh_proxy()
                self.num_dpcsh_cmds = 0
                self.storage_controller.disconnect()

    def setup_ec_volume(self, ndata, nparity):

        if self.need_dpc_server_start:
            self.qemu.start_dpc_server()
            self.storage_controller.disconnect()
            self.need_dpc_server_start = False

        self.ec_ratio = str(ndata) + str(nparity)
        if self.ec_ratio not in fun_test.shared_variables:
            fun_test.shared_variables[self.ec_ratio] = {}

        # self.volumes = ["ndata", "nparity", "ec", "lsv"]
        self.num_volumes = {}
        self.num_volumes["ndata"] = ndata
        self.num_volumes["nparity"] = nparity
        # self.num_volumes["ec"] = 1
        # self.num_volumes["lsv"] = 1

        self.uuids = {}
        self.uuids["blt"] = []
        self.uuids["ec"] = []
        self.uuids["jvol"] = []
        self.uuids["lsv"] = []

        self.calc_volume_capacity = {}
        # LS volume capacity is the ndata times of the BLT volume capacity
        self.calc_volume_capacity["lsv"] = self.volume_capacity["ndata"] * ndata
        if self.use_lsv:

            fun_test.log("LS volume needs to be configured. So increasing the BLT volume's capacity by 30% and "
                         "rounding that to the nearest 8MB value")
            eight_mb = 1024 * 1024 * 8
            for vtype in ["ndata", "nparity"]:
                tmp = self.volume_capacity[vtype] * (1 + self.lsv_pct)
                self.calc_volume_capacity[vtype] = int(tmp + (eight_mb - (tmp % eight_mb)))

            # Setting the EC volume capacity also to same as the one of ndata volume capacity
            self.calc_volume_capacity["ec"] = self.calc_volume_capacity["ndata"] * self.num_volumes["ndata"]
        else:
            self.calc_volume_capacity.update(self.volume_capacity)

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
                fun_test.simple_assert(command_result["status"], "Create {} {} BLT volume on DUT instance".
                                       format(i, vtype))
                self.check_num_dpcsh_cmds()  # Calling this as a workaround for the bug SWOS-1434

        # Configuring EC volume on top of BLT volumes
        this_uuid = utils.generate_uuid()
        self.uuids["ec"].append(this_uuid)
        try:
            command_result = self.storage_controller.create_volume(
                type=self.volume_types["ec"], capacity=self.calc_volume_capacity["ec"],
                block_size=self.volume_block["ec"], name="ec1", uuid=this_uuid, ndata=self.num_volumes["ndata"],
                nparity=self.num_volumes["nparity"], pvol_id=self.uuids["blt"], command_duration=self.command_timeout)
        except Exception as e:
            # EC command creation didn't received any response. So going to check whether the command actually failed
            # or the command got executed properly, but it didn't received the response only
            self.qemu.start_dpcsh_proxy()
            self.num_dpcsh_cmds = 0
            self.storage_controller.disconnect()
            fun_test.log("EC volume creation command didn't received any response. So checking the whether the volume "
                         "is actually created or not")
            storage_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", self.volume_types["ec"], this_uuid,
                                                         "stats")
            command_result = self.storage_controller.peek(storage_props_tree)
            if command_result["status"]:
                fun_test.log("EC volume created successfully, but the command returned no output")
            else:
                fun_test.simple_assert(command_result["status"], "Create EC volume on DUT instance")
        self.check_num_dpcsh_cmds()  # Calling this as a workaround for the bug SWOS-1434
        attach_uuid = this_uuid

        # Configuring LS volume and its associated journal volume based on the script config setting
        if self.use_lsv:
            self.uuids["jvol"] = utils.generate_uuid()
            command_result = self.storage_controller.create_volume(
                type=self.volume_types["jvol"], capacity=self.volume_capacity["jvol"],
                block_size=self.volume_block["jvol"], name="jvol1", uuid=self.uuids["jvol"],
                command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Create Journal volume on DUT instance")

            this_uuid = utils.generate_uuid()
            self.uuids["lsv"].append(this_uuid)
            command_result = self.storage_controller.create_volume(
                type=self.volume_types["lsv"], capacity=self.calc_volume_capacity["lsv"],
                block_size=self.volume_block["lsv"], name="lsv1", uuid=this_uuid, group=self.num_volumes["ndata"],
                compress=self.compress,
                zip_effort=self.zip_effort,
                zip_filter=self.zfilter,
                jvol_uuid=self.uuids["jvol"], pvol_id=self.uuids["ec"], command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.simple_assert(command_result["status"], "Create LS volume on DUT instance")
            self.check_num_dpcsh_cmds()  # Calling this as a workaround for the bug SWOS-1434
            attach_uuid = this_uuid

        # Attaching/Exporting the EC/LS volume to the external server
        if not self.volume_attached:
            command_result = self.storage_controller.volume_attach_pcie(
                ns_id=self.ns_id, uuid=attach_uuid, command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.simple_assert(command_result["status"], "Attaching EC/LS volume on DUT instance")
            self.check_num_dpcsh_cmds()  # Calling this as a workaround for the bug SWOS-1434
            self.volume_attached = True

        fun_test.add_checkpoint("Created {}:{} EC Volume".format(ndata, nparity), "PASSED", True,
                                command_result["status"])

        # disabling the error_injection for the EC volume
        command_result = {}
        command_result = self.storage_controller.poke("params/ecvol/error_inject 0")
        fun_test.log(command_result)
        fun_test.simple_assert(command_result["status"], "Disabling error_injection for EC volume on DUT instance")
        self.check_num_dpcsh_cmds()  # Calling this as a workaround for the bug SWOS-1434

        # Ensuring that the error_injection got disabled properly
        fun_test.sleep("Sleeping for a second to disable the error_injection", 1)
        command_result = {}
        command_result = self.storage_controller.peek("params/ecvol")
        fun_test.log(command_result)
        fun_test.simple_assert(command_result["status"], "Retrieving error_injection status on DUT instance")
        fun_test.test_assert_expected(actual=int(command_result["data"]["error_inject"]), expected=0,
                                      message="Ensuring error_injection got disabled")
        self.check_num_dpcsh_cmds()  # Calling this as a workaround for the bug SWOS-1434

        # Rebooting the qemu host before checking the disk as a workaround to the bug swos-1331
        if self.reboot_after_config:
            fun_test.simple_assert(self.qemu.reboot(timeout=self.command_timeout, retries=12), "Qemu Host Rebooted")
            self.need_dpc_server_start = True

        # Checking that the volume is accessible to the host
        lsblk_output = self.host.lsblk()
        fun_test.test_assert(self.volume_name in lsblk_output, "{} device available".format(self.volume_name))
        fun_test.test_assert_expected(expected="disk", actual=lsblk_output[self.volume_name]["type"],
                                      message="{} device type check".format(self.volume_name))

        fun_test.shared_variables[self.ec_ratio]["uuids"] = self.uuids

    def cleanup_ec_volume(self, data, parity):

        if self.need_dpc_server_start:
            self.qemu.start_dpc_server()
            self.storage_controller.disconnect()
            self.need_dpc_server_start = False

        self.ec_ratio = str(data) + str(parity)
        if self.ec_ratio not in fun_test.shared_variables:
            fun_test.shared_variables[self.ec_ratio] = {}

        attach_uuid = ""
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
            self.check_num_dpcsh_cmds()  # Calling this as a workaround for the bug SWOS-1434
            attach_uuid = this_uuid

            this_uuid = self.uuids["jvol"]
            command_result = self.storage_controller.delete_volume(
                type=self.volume_types["jvol"], capacity=self.volume_capacity["jvol"],
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
        fun_test.simple_assert(command_result["status"], "Delete EC volume on DUT instance")
        self.check_num_dpcsh_cmds()  # Calling this as a workaround for the bug SWOS-1434
        if not attach_uuid:
            attach_uuid = this_uuid

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
                fun_test.simple_assert(command_result["status"], "Delete {} {} BLT volume on DUT instance".
                                       format(i, vtype))
                self.check_num_dpcsh_cmds()  # Calling this as a workaround for the bug SWOS-1434

        self.volume_attached = False

    def setup(self):

        testcase = self.__class__.__name__

        self.need_dpc_server_start = True

        self.my_shared_variables = {}

        # Start of benchmarking json file parsing and initializing various variables to run this testcase
        benchmark_parsing = True
        benchmark_file = ""
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Benchmark file being used: {}".format(benchmark_file))

        benchmark_dict = {}
        benchmark_dict = utils.parse_file_to_json(benchmark_file)

        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

        # End of benchmarking json file parsing

        self.topology = fun_test.shared_variables["topology"]
        self.dut = self.topology.get_dut_instance(index=0)
        fun_test.test_assert(self.dut, "Retrieved dut instance 0")
        self.host = self.topology.get_host_instance(dut_index=0, interface_index=0, host_index=0)
        self.qemu = QemuStorageTemplate(host=self.host, dut=self.dut)
        self.funos_running = True

        # Preserving the funos-posix and qemu commandline
        self.funos_cmdline = self.qemu.get_process_cmdline(F1.FUN_OS_SIMULATION_PROCESS_NAME)
        fun_test.log("\nfunos-posix commandline: {}".format(self.funos_cmdline))
        self.qemu_cmdline = self.qemu.get_process_cmdline(DockerContainerOrchestrator.QEMU_PROCESS)
        fun_test.log("\nQemu commandline: {}".format(self.qemu_cmdline))
        self.qemu_cmdline = re.sub(r'(.*append)\s+(root.*mem=\d+M)(.*)', r'\1 "\2"\3', self.qemu_cmdline)
        fun_test.log("\nProcessed Qemu commandline: {}".format(self.qemu_cmdline))

        # Starting the dpc server in the qemu host
        if self.need_dpc_server_start:
            self.qemu.start_dpc_server()
            fun_test.sleep("Waiting for the DPC server and DPCSH TCP proxy to settle down", self.iter_interval)
            self.need_dpc_server_start = False

        self.storage_controller = StorageController(target_ip=self.dut.host_ip,
                                                    target_port=self.dut.external_dpcsh_port)
        self.num_dpcsh_cmds = 0

        # Configuring the controller
        command_result = self.storage_controller.command(command="enable_counters", legacy=True)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Enabling counters on DUT instance")
        self.num_dpcsh_cmds += 1

        self.volume_name = self.nvme_device.replace("/dev/", "") + "n" + str(self.ns_id)
        self.nvme_block_device = self.nvme_device + "n" + str(self.ns_id)
        self.volume_attached = False

    def do_write_test(self, ndata, nparity):
        '''
        command_result = self. qemu.smartctl(arg1=1, arg2=2)
        fun_test.log(command_result)
        '''
        # Creating input data file containing (data volume block size * ndata volume) bytes of random data
        self.input_size = self.volume_block["ndata"] * ndata
        return_size = self.qemu.create_compressible_file(output_file=self.input_data,
                                                         size=self.input_size,
                                                         compression_pct=self.compression_pct)

        fun_test.test_assert_expected(self.input_size, return_size, "Input data creation")
        self.input_md5sum = self.qemu.md5sum(file_name=self.input_data)
        fun_test.simple_assert(self.input_md5sum, "Finding md5sum for input data")
        # Starting the write test
        num_writes = self.dataset_size / self.input_size
        for blk in range(1, num_writes + 2):
            blk_write_result = ""
            if blk != 1:
                blk = blk * ndata - 1
            else:
                begin = blk
            end = begin + self.input_size - 1

            # Dump stats before writes
            if self.need_dpc_server_start:
                self.qemu.start_dpc_server()
                self.storage_controller.disconnect()
                self.need_dpc_server_start = False

            fun_test.log("IN do_write_test , STATS BBEFORE {} WRITE:".format(self.input_size))
            props_tree = "{}/{}/{}/{}".format("storage", "volumes", self.volume_types["lsv"],
                                                 self.uuids["lsv"][0])
            command_result = self.storage_controller.peek(props_tree, command_duration=5)
            fun_test.log(command_result)

            blk_write_result = self.qemu.nvme_write(device=self.nvme_block_device, start=blk, count=ndata - 1,
                                                    size=self.input_size, data=self.input_data)
            if blk_write_result != "Success":
                self.write_result[ndata][nparity] = False
                fun_test.critical("Write failed for {} to {} bytes".format(begin, end))
            else:
                fun_test.log("Write succeeded for {} to {} bytes".format(begin, end))
                fun_test.log("IN do_write_test , STATS AFTER {} WRITE:".format(self.input_size))
                #command_result = self.storage_controller.peek(props_tree, command_duration=5)
                command_result = self.storage_controller.peek("storage", command_duration=5)
                fun_test.log(command_result)

            begin = end + 1
        if self.write_result[ndata][nparity]:
            fun_test.add_checkpoint("Write operation for {} bytes".format(self.dataset_size), "PASSED", True,
                                    self.write_result[ndata][nparity])
        else:
            fun_test.add_checkpoint("Write operation for {} bytes".format(self.dataset_size), "FAILED", True,
                                    self.write_result[ndata][nparity])
        # fun_test.test_assert(self.write_result[ndata][nparity], "Write operation for {} bytes".
        #                      format(self.dataset_size))

    def do_read_test(self, ndata, nparity, index):

        # Starting the read test
        num_reads = self.dataset_size / self.input_size
        for blk in range(1, num_reads + 1):
            blk_read_result = ""
            output_md5sum = ""
            if blk != 1:
                blk = blk * ndata - 1
            else:
                begin = blk
            end = begin + self.input_size - 1
            output_file = self.output_data + "_" + str(blk)

            fun_test.log("IN do_read_test , STATS BBEFORE {} READ:".format(self.input_size))
            props_tree = "{}/{}/{}/{}".format("storage", "volumes", self.volume_types["lsv"],
                                              self.uuids["lsv"][0])
            command_result = self.storage_controller.peek(props_tree, command_duration=5)
            fun_test.log(command_result)

            blk_read_result = self.qemu.nvme_read(device=self.nvme_block_device, start=blk, count=ndata - 1,
                                                  size=self.input_size, data=output_file)
            if blk_read_result != "Success":
                self.read_result[ndata][nparity][index] = False
                fun_test.critical("Read failed for {} to {} bytes".format(begin, end))
            else:
                fun_test.log("Read succeeded for {} to {} bytes".format(begin, end))
                fun_test.log("IN do_read_test , STATS AFTER {} READ:".format(self.input_size))
                command_result = self.storage_controller.peek(props_tree, command_duration=5)
                fun_test.log(command_result)

            output_md5sum = self.qemu.md5sum(file_name=output_file)
            if output_md5sum == self.input_md5sum:
                fun_test.log("md5sum for {} to {} bytes {} matches with input md5sum {}".
                             format(begin, end, output_md5sum, self.input_md5sum))
            else:
                self.read_result[ndata][nparity][index] = False
                fun_test.critical("md5sum for {} to {} bytes {} is not matching with input md5sum {}".
                                  format(begin, end, output_md5sum, self.input_md5sum))
            begin = end + 1
        if self.read_result[ndata][nparity][index]:
            fun_test.add_checkpoint("Read operation for {} bytes after failing {} data volume(s)".
                                    format(self.dataset_size, index + 1), "PASSED", True,
                                    self.read_result[ndata][nparity][index])
        else:
            fun_test.add_checkpoint("Read operation for {} bytes after failing {} data volume(s)".
                                    format(self.dataset_size, index + 1), "FAILED", True,
                                    self.read_result[ndata][nparity][index])
        # fun_test.test_assert(self.read_result[ndata][nparity][index],
        #                      "Read operation for {} bytes after failing {} data volumes".
        #                      format(self.dataset_size, index + 1))

    def run(self):

        pass

    def cleanup(self):

        self.qemu.stop_dpc_server()
        self.storage_controller.disconnect()


class RndDataWriteAndRead25PctWithDataVolumeFailure(ECinQemuTestcase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Sequential write and then read of 25 % uncompressible data by failing m number "
                                      "of data volumes in n = k+m EC volume eg. n = 8, m = 4",
                              steps="""
        1. Run the outer loop from ndata_partition_start_range to ndata_partition_end_range. Say it as k
        2. Run the inner loop from nparity_start_range = min(int(ndata / 4) + 1, self.max_parity) to 
        nparity_end_range = min(ndata - 1, self.max_parity) + 1. Say it as m
        3. Configure k data and m parity BLT volumes.
        4. Configure k:m EC volume.
        5. Create a compression enabled LS volume on top of the EC volume
        6. Export (Attach) the above LS volume to PCIe controller. 
        7. Write 25% of dataset_size bytes of random data into the LSV and remaining 0 filled data in sequential manner
        8. Start a loop to run 0 to m-1 and inside it fail the data volume in that index and read back the previously
        written data   
        """)

    def setup(self):
        super(RndDataWriteAndRead25PctWithDataVolumeFailure, self).setup()

    def run(self):

        testcase = self.__class__.__name__

        self.unconfig_result = {}
        self.write_result = {}
        self.read_result = {}
        test_result = True

        per_volume_zip_stats = {"accumulated_out_bytes", "compress_done", "compress_fails",
                                "compress_reqs", "uncompress_done", "uncompress_fails",
                                "uncompress_reqs", "uncompressible"}



        for ndata in range(self.ndata_partition_start_range, self.ndata_partition_end_range + 1):

            self.unconfig_result[ndata] = {}
            self.write_result[ndata] = {}
            self.read_result[ndata] = {}

            if not hasattr(self, "nparity_start_range"):
                self.nparity_start_range = min(int(ndata / 4) + 1, self.max_parity)
            if not hasattr(self, "nparity_end_range"):
                self.nparity_end_range = min(ndata - 1, self.max_parity)

            for nparity in range(self.nparity_start_range, self.nparity_end_range + 1):

                self.unconfig_result[ndata][nparity] = True
                self.write_result[ndata][nparity] = True
                self.read_result[ndata][nparity] = {}

                # Take attach specific stats (before attach)
                for key in self.params_to_monitor_per_attach:
                    initial_value = 0
                    prop_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", str(key))
                    command_result = self.storage_controller.peek(prop_tree, command_duration=5)
                    fun_test.log(command_result["data"])
                    if command_result["data"]:
                        initial_value = command_result["data"]
                    self.my_shared_variables["initial_" + str(key)] = initial_value

                # Creating ndata:npartiy EC volume
                self.setup_ec_volume(ndata, nparity)

                if self.need_dpc_server_start:
                    self.qemu.start_dpc_server()
                    self.storage_controller.disconnect()
                    self.need_dpc_server_start = False

                # Take the counters before the test
                fun_test.log("TAKE COUNTERS BEFORE WRITING")
                for key in self.zip_params_to_monitor:
                    initial_value = 0
                    if key not in per_volume_zip_stats:
                        prop_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", str(key))
                    else:
                        prop_tree = "{}/{}/{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LSV",
                                                               self.uuids["lsv"][0], "compression",
                                                               str(key))
                    command_result = self.storage_controller.peek(prop_tree, command_duration=5)
                    fun_test.log(command_result["data"])
                    if command_result["data"]:
                        initial_value = command_result["data"]
                    self.my_shared_variables["initial_" + str(key)] = initial_value

                for key in self.enc_params_to_monitor:
                    initial_value = 0
                    prop_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", str(key))
                    command_result = self.storage_controller.peek(prop_tree, command_duration=5)
                    fun_test.log(command_result["data"])
                    if command_result["data"]:
                        initial_value = command_result["data"]
                    self.my_shared_variables["initial_" + str(key)] = initial_value


                # Performing Write Test
                self.do_write_test(ndata, nparity)
                props_tree = "{}/{}/{}/{}".format("storage", "volumes", self.volume_types["lsv"],
                                                     self.uuids["lsv"][0])
                fun_test.log("FINALLY STATS AFTER CALLING do_write_test:")
                command_result = self.storage_controller.peek(props_tree, command_duration=5)
                fun_test.log(command_result)

                # Disabling the nparity number of data BLT volumes one after the other and trying to read the
                # previously written data back
                for index in range(-1, nparity):
                    self.read_result[ndata][nparity][index] = True

                    if index != -1:

                        # Start the dpc server to inject error into the data BLT volumes
                        if self.need_dpc_server_start:
                            self.qemu.start_dpc_server()
                            self.storage_controller.disconnect()
                            self.need_dpc_server_start = False

                        command_result = self.storage_controller.fail_volume(uuid=self.uuids["ndata"][index],
                                                                             command_duration=self.command_timeout)
                        fun_test.log(command_result)
                        fun_test.test_assert(command_result["status"], "Inject failure to the ndata BLT volume having "
                                                                       "the UUID {}".format(self.uuids["ndata"][index]))
                        self.check_num_dpcsh_cmds()  # Calling this as a workaround for the bug SWOS-1434
                        fun_test.sleep("to enable the fault_injection", 1)
                        props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", self.volume_types["ndata"],
                                                          self.uuids["ndata"][index], "stats")
                        command_result = self.storage_controller.peek(props_tree)
                        fun_test.log(command_result)
                        fun_test.test_assert_expected(actual=int(command_result["data"]["fault_injection"]),
                                                      expected=1, message="Ensuring fault_injection got enabled",
                                                      ignore_on_success=True)
                        self.check_num_dpcsh_cmds()  # Calling this as a workaround for the bug SWOS-1434

                        # Rebooting the qemu host as a workaround for the bug #swos-1332
                        if self.reboot_after_config:
                            self.qemu.reboot()
                            self.need_dpc_server_start = True

                    if self.need_dpc_server_start:
                        self.qemu.start_dpc_server()
                        self.storage_controller.disconnect()
                        self.need_dpc_server_start = False
                    # Performing read test
                    self.do_read_test(ndata, nparity, index)

                if self.need_dpc_server_start:
                    self.qemu.start_dpc_server()
                    self.storage_controller.disconnect()
                    self.need_dpc_server_start = False
                # verify the stats
                fun_test.log("VERIFY THE RESULTS AFTER WRITE")
                for key, value in self.params_to_monitor_per_attach.items():
                    final_value = 0
                    prop_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", str(key))
                    command_result = self.storage_controller.peek(prop_tree, command_duration=5)
                    fun_test.log(command_result["data"])
                    if command_result["data"]:
                        final_value = command_result["data"]
                    if final_value - self.my_shared_variables["initial_" + str(key)] == value:
                        fun_test.add_checkpoint("attach specific stats match: " + str(key).format(self),
                                                "PASSED",
                                                value,
                                                final_value - self.my_shared_variables["initial_" + str(key)])
                    else:
                        fun_test.add_checkpoint("attach specific stats dont match: " + str(key).format(self),
                                                "Failed",
                                                value,
                                                final_value - self.my_shared_variables["initial_" + str(key)])
                        test_result = False

                for key, value in self.zip_params_to_monitor.items():
                    final_value = 0
                    if key not in per_volume_zip_stats:
                        prop_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", str(key))
                    else:
                        prop_tree = "{}/{}/{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LSV",
                                                               self.uuids["lsv"][0], "compression",
                                                               str(key))
                    command_result = self.storage_controller.peek(prop_tree, command_duration=5)
                    fun_test.log(command_result["data"])
                    if command_result["data"]:
                        final_value = command_result["data"]

                    if key == "accumulated_out_bytes":
                        if (final_value - self.my_shared_variables["initial_" + str(key)]) - \
                                self.expected_compressed_bytes < 200:
                            fun_test.add_checkpoint(
                                "zip RATIO: " + str(key) + " :0.005 x input ".format(self),
                                "PASSED",
                                self.expected_compressed_bytes,
                                final_value - self.my_shared_variables["initial_" + str(key)])
                        else:
                            fun_test.add_checkpoint(
                                "zip ratio " + str(key) + " not 0.005 x input ".format(self),
                                "Failed",
                                self.expected_compressed_bytes,
                                final_value - self.my_shared_variables["initial_" + str(key)])
                            test_result = False
                    elif final_value - self.my_shared_variables["initial_" + str(key)] == value:
                        fun_test.add_checkpoint("zip stats match: " + str(key).format(self),
                                                "PASSED",
                                                value,
                                                final_value - self.my_shared_variables[
                                                    "initial_" + str(key)])
                    else:
                        fun_test.add_checkpoint("zip stats dont match: " + str(key).format(self),
                                                "Failed",
                                                value,
                                                final_value - self.my_shared_variables[
                                                    "initial_" + str(key)])
                        test_result = False
                if self.encrypt:
                    final_value = 0
                    for key, value in self.enc_params_to_monitor.items():
                        prop_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", str(key))
                        command_result = self.storage_controller.peek(prop_tree, command_duration=5)
                        fun_test.log(command_result["data"])
                        if command_result["data"]:
                            final_value = command_result["data"]
                        if final_value - self.my_shared_variables["initial_" + str(key)] == value:
                            fun_test.add_checkpoint("enc stats match: " + str(key).format(self),
                                                    "PASSED",
                                                    value,
                                                    final_value - self.my_shared_variables[
                                                        "initial_" + str(key)])
                        else:
                            fun_test.add_checkpoint("enc stats dont match: " + str(key).format(self),
                                                    "Failed",
                                                    value,
                                                    final_value - self.my_shared_variables[
                                                        "initial_" + str(key)])
                            test_result = False

                # Unconfiguring everything to move to next variation
                # Commented the below section because of the bug SWOS-1418
                # Starting the dpc server in the qemu host
                if self.need_dpc_server_start:
                    self.qemu.start_dpc_server()
                    fun_test.sleep("Breathing...", 10)
                    self.storage_controller.disconnect()
                    self.need_dpc_server_start = False
                self.cleanup_ec_volume(ndata, nparity)

                if self.reboot_after_config:
                    self.qemu.reboot()
                    self.need_dpc_server_start = True

                # Checking whether the funos-posix is running after unconfiguration
                funos_pid = self.dut.get_process_id(F1.FUN_OS_SIMULATION_PROCESS_NAME)
                if not funos_pid:
                    self.unconfig_result[ndata][nparity] = False
                    self.funos_running = False
                    fun_test.critical("funos-posix is not running")
                    if self.funos_cmdline:
                        fun_test.log("Restarting the funos-posix")
                        new_funos_pid = self.qemu.start_funos(self.funos_cmdline, self.command_timeout)
                        fun_test.test_assert(new_funos_pid, "Restarting the funos-posix")
                        fun_test.log("Restarting the Qemu")
                        new_qemu_pid = self.qemu.start_qemu(qemu_cmdline=self.qemu_cmdline,
                                                            timeout=self.command_timeout)
                        fun_test.log("New Qemu Process ID: {}".format(new_qemu_pid))
                        fun_test.test_assert(new_qemu_pid, "Restarting the Qemu")
                        self.host.disconnect()
                        self.funos_running = True
                        self.need_dpc_server_start = True

                test_variation_result = self.write_result[ndata][nparity] and self.read_result[ndata][nparity] and \
                    self.unconfig_result[ndata][nparity]
                if test_variation_result:
                    fun_test.add_checkpoint("Sequential write and then read of random data by failing {} number of "
                                            "data volumes in {}:{} EC volume".format(nparity, ndata, nparity),
                                            "PASSED", True, test_variation_result)
                else:
                    fun_test.add_checkpoint("Sequential write and then read of random data by failing {} number of "
                                            "data volumes in {}:{} EC volume".format(nparity, ndata, nparity),
                                            "FAILED", True, test_variation_result)

                if not self.funos_running:
                    fun_test.critical("Unable to get the funos-posix commandline...So aborting the test for further "
                                      "EC combinations")
                    break

        for ndata in range(self.ndata_partition_start_range, self.ndata_partition_end_range + 1):
            for nparity in range(self.nparity_start_range, self.nparity_end_range + 1):
                if not self.write_result[ndata][nparity] or not self.read_result[ndata][nparity] or \
                        not self.unconfig_result[ndata][nparity]:
                    test_result = False

        fun_test.test_assert(test_result, self.summary)

    def cleanup(self):
        super(RndDataWriteAndRead25PctWithDataVolumeFailure, self).cleanup()


class ZeroDataWriteAndReadWithDataVolumeFailure(ECinQemuTestcase):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Sequential write and then read of 100 % compressible data by failing m number "
                                      "of data volumes in n = k+m EC volume",
                              steps="""
        1. Run the outer loop from ndata_partition_start_range to ndata_partition_end_range. Say it as k
        2. Run the inner loop from nparity_start_range = min(int(ndata / 4) + 1, self.max_parity) to 
        nparity_end_range = min(ndata - 1, self.max_parity) + 1. Say it as m
        3. Configure k data and m parity BLT volumes.
        4. Configure k:m EC volume.
        5. Create a LS volume on top of the EC volume.
        6. Export (Attach) the above LS volume to PCIe controller. 
        7. Write dataset_size bytes of zero-filled data into the LSV in a sequential manner.
        8. Start a loop to run 0 to m-1 and inside it fail the data volume in that index and read back the previously
        written data   
        """)

    def setup(self):
        super(ZeroDataWriteAndReadWithDataVolumeFailure, self).setup()

    def run(self):

        testcase = self.__class__.__name__

        self.unconfig_result = {}
        self.write_result = {}
        self.read_result = {}
        test_result = True
        per_volume_zip_stats = {"accumulated_out_bytes", "compress_done", "compress_fails",
                                "compress_reqs", "uncompress_done", "uncompress_fails",
                                "uncompress_reqs", "uncompressible"}

        for ndata in range(self.ndata_partition_start_range, self.ndata_partition_end_range + 1):

            self.unconfig_result[ndata] = {}
            self.write_result[ndata] = {}
            self.read_result[ndata] = {}

            if not hasattr(self, "nparity_start_range"):
                self.nparity_start_range = min(int(ndata / 4) + 1, self.max_parity)
            if not hasattr(self, "nparity_end_range"):
                self.nparity_end_range = min(ndata - 1, self.max_parity)

            for nparity in range(self.nparity_start_range, self.nparity_end_range + 1):

                self.unconfig_result[ndata][nparity] = True
                self.write_result[ndata][nparity] = True
                self.read_result[ndata][nparity] = {}

                # Take attach specific stats (before attach)
                for key in self.params_to_monitor_per_attach:
                    initial_value = 0
                    prop_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", str(key))
                    command_result = self.storage_controller.peek(prop_tree, command_duration=5)
                    fun_test.log(command_result["data"])
                    if command_result["data"]:
                        initial_value = command_result["data"]
                    self.my_shared_variables["initial_" + str(key)] = initial_value

                # Creating ndata:npartiy EC volume
                self.setup_ec_volume(ndata, nparity)

                if self.need_dpc_server_start:
                    self.qemu.start_dpc_server()
                    self.storage_controller.disconnect()
                    self.need_dpc_server_start = False

                # Take the counters before the test
                fun_test.log("TAKE COUNTERS BEFORE WRITING")
                for key in self.zip_params_to_monitor:
                    initial_value = 0
                    if key not in per_volume_zip_stats:
                        prop_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", str(key))
                    else:
                        prop_tree = "{}/{}/{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LSV",
                                                               self.uuids["lsv"][0], "compression",
                                                               str(key))
                    command_result = self.storage_controller.peek(prop_tree, command_duration=5)
                    fun_test.log(command_result["data"])
                    if command_result["data"]:
                        initial_value = command_result["data"]
                    self.my_shared_variables["initial_" + str(key)] = initial_value

                for key in self.enc_params_to_monitor:
                    initial_value = 0
                    prop_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", str(key))
                    command_result = self.storage_controller.peek(prop_tree, command_duration=5)
                    fun_test.log(command_result["data"])
                    if command_result["data"]:
                        initial_value = command_result["data"]
                    self.my_shared_variables["initial_" + str(key)] = initial_value

                # Performing Write Test
                self.do_write_test(ndata, nparity)

                props_tree = "{}/{}/{}/{}".format("storage", "volumes", self.volume_types["lsv"],
                                                  self.uuids["lsv"][0])
                fun_test.log("FINALLY STATS AFTER CALLING do_write_test:")
                command_result = self.storage_controller.peek(props_tree, command_duration=5)
                fun_test.log(command_result)

                # Disabling the nparity number of data BLT volumes one after the other and trying to read the
                # previously written data back
                for index in range(-1, nparity):
                    self.read_result[ndata][nparity][index] = True

                    if index != -1:

                        # Start the dpc server to inject error into the data BLT volumes
                        if self.need_dpc_server_start:
                            self.qemu.start_dpc_server()
                            self.storage_controller.disconnect()
                            self.need_dpc_server_start = False

                        command_result = self.storage_controller.fail_volume(uuid=self.uuids["ndata"][index],
                                                                             command_duration=self.command_timeout)
                        fun_test.log(command_result)
                        fun_test.test_assert(command_result["status"], "Inject failure to the ndata BLT volume having "
                                                                       "the UUID {}".format(self.uuids["ndata"][index]))
                        self.check_num_dpcsh_cmds()  # Calling this as a workaround for the bug SWOS-1434
                        fun_test.sleep("to enable the fault_injection", 1)
                        props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", self.volume_types["ndata"],
                                                          self.uuids["ndata"][index], "stats")
                        command_result = self.storage_controller.peek(props_tree)
                        fun_test.log(command_result)
                        fun_test.test_assert_expected(actual=int(command_result["data"]["fault_injection"]),
                                                      expected=1, message="Ensuring fault_injection got enabled",
                                                      ignore_on_success=True)
                        self.check_num_dpcsh_cmds()  # Calling this as a workaround for the bug SWOS-1434

                        # Rebooting the qemu host as a workaround for the bug #swos-1332
                        if self.reboot_after_config:
                            self.qemu.reboot()
                            self.need_dpc_server_start = True

                    if self.need_dpc_server_start:
                        self.qemu.start_dpc_server()
                        self.storage_controller.disconnect()
                        self.need_dpc_server_start = False

                    # Performing read test
                    self.do_read_test(ndata, nparity, index)

                if self.need_dpc_server_start:
                    self.qemu.start_dpc_server()
                    self.storage_controller.disconnect()
                    self.need_dpc_server_start = False

                # verify the stats
                fun_test.log("VERIFY THE RESULTS AFTER WRITE")
                for key, value in self.params_to_monitor_per_attach.items():
                    final_value = 0
                    prop_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", str(key))
                    command_result = self.storage_controller.peek(prop_tree, command_duration=5)
                    fun_test.log(command_result["data"])
                    if command_result["data"]:
                        final_value = command_result["data"]
                    if final_value - self.my_shared_variables["initial_" + str(key)] == value:
                        fun_test.add_checkpoint("attach specific stats match: " + str(key).format(self),
                                                "PASSED",
                                                value,
                                                final_value - self.my_shared_variables["initial_" + str(key)])
                    else:
                        fun_test.add_checkpoint("attach specific stats dont match: " + str(key).format(self),
                                                "Failed",
                                                value,
                                                final_value - self.my_shared_variables["initial_" + str(key)])
                        test_result = False

                for key, value in self.zip_params_to_monitor.items():
                    final_value = 0
                    if key not in per_volume_zip_stats:
                        prop_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", str(key))
                    else:
                        prop_tree = "{}/{}/{}/{}/{}/{}".format("storage", "volumes", "VOL_TYPE_BLK_LSV",
                                                               self.uuids["lsv"][0], "compression",
                                                               str(key))
                    command_result = self.storage_controller.peek(prop_tree, command_duration=5)
                    fun_test.log(command_result["data"])
                    if command_result["data"]:
                        final_value = command_result["data"]

                    if key == "accumulated_out_bytes":
                        if (final_value - self.my_shared_variables["initial_" + str(key)]) - \
                                self.expected_compressed_bytes < 200:
                            fun_test.add_checkpoint(
                                "zip RATIO: " + str(key) + " :0.005 x input ".format(self),
                                "PASSED",
                                self.expected_compressed_bytes,
                                final_value - self.my_shared_variables["initial_" + str(key)])
                        else:
                            fun_test.add_checkpoint(
                                "zip ratio " + str(key) + " not 0.005 x input ".format(self),
                                "Failed",
                                self.expected_compressed_bytes,
                                final_value - self.my_shared_variables["initial_" + str(key)])

                            test_result = False
                    elif final_value - self.my_shared_variables["initial_" + str(key)] == value:
                        fun_test.add_checkpoint("zip stats match: " + str(key).format(self),
                                                "PASSED",
                                                value,
                                                final_value - self.my_shared_variables[
                                                    "initial_" + str(key)])
                    else:
                        fun_test.add_checkpoint("zip stats dont match: " + str(key).format(self),
                                                "Failed",
                                                value,
                                                final_value - self.my_shared_variables[
                                                    "initial_" + str(key)])
                        test_result = False

                if self.encrypt:
                    final_value = 0
                    for key, value in self.enc_params_to_monitor.items():
                        prop_tree = "{}/{}/{}/{}".format("stats", "wus", "counts", str(key))
                        command_result = self.storage_controller.peek(prop_tree, command_duration=5)
                        fun_test.log(command_result["data"])
                        if command_result["data"]:
                            final_value = command_result["data"]
                        if final_value - self.my_shared_variables["initial_" + str(key)] == value:
                            fun_test.add_checkpoint("enc stats match: " + str(key).format(self),
                                                    "PASSED",
                                                    value,
                                                    final_value - self.my_shared_variables[
                                                        "initial_" + str(key)])
                        else:
                            fun_test.add_checkpoint("enc stats dont match: " + str(key).format(self),
                                                    "Failed",
                                                    value,
                                                    final_value - self.my_shared_variables[
                                                        "initial_" + str(key)])
                            test_result = False

                # Unconfiguring everything to move to next variation
                # Commented the below section because of the bug SWOS-1418
                # Starting the dpc server in the qemu host
                if self.need_dpc_server_start:
                    self.qemu.start_dpc_server()
                    fun_test.sleep("Breathing...", 10)
                    self.storage_controller.disconnect()
                    self.need_dpc_server_start = False
                self.cleanup_ec_volume(ndata, nparity)

                if self.reboot_after_config:
                    self.qemu.reboot()
                    self.need_dpc_server_start = True

                # Checking whether the funos-posix is running after unconfiguration
                funos_pid = self.dut.get_process_id(F1.FUN_OS_SIMULATION_PROCESS_NAME)
                if not funos_pid:
                    self.unconfig_result[ndata][nparity] = False
                    self.funos_running = False
                    fun_test.critical("funos-posix is not running")
                    if self.funos_cmdline:
                        fun_test.log("Restarting the funos-posix")
                        new_funos_pid = self.qemu.start_funos(self.funos_cmdline, self.command_timeout)
                        fun_test.test_assert(new_funos_pid, "Restarting the funos-posix")
                        fun_test.log("Restarting the Qemu")
                        new_qemu_pid = self.qemu.start_qemu(qemu_cmdline=self.qemu_cmdline,
                                                            timeout=self.command_timeout)
                        fun_test.log("New Qemu Process ID: {}".format(new_qemu_pid))
                        fun_test.test_assert(new_qemu_pid, "Restarting the Qemu")
                        self.host.disconnect()
                        self.funos_running = True
                        self.need_dpc_server_start = True

                test_variation_result = self.write_result[ndata][nparity] and self.read_result[ndata][nparity] and \
                    self.unconfig_result[ndata][nparity]
                if test_variation_result:
                    fun_test.add_checkpoint("Sequential write and then read of random data by failing {} number of "
                                            "data volumes in {}:{} EC volume".format(nparity, ndata, nparity),
                                            "PASSED", True, test_variation_result)
                else:
                    fun_test.add_checkpoint("Sequential write and then read of random data by failing {} number of "
                                            "data volumes in {}:{} EC volume".format(nparity, ndata, nparity),
                                            "FAILED", True, test_variation_result)

                if not self.funos_running:
                    fun_test.critical("Unable to get the funos-posix commandline...So aborting the test for further "
                                      "EC combinations")
                    break

        for ndata in range(self.ndata_partition_start_range, self.ndata_partition_end_range + 1):
            for nparity in range(self.nparity_start_range, self.nparity_end_range + 1):
                if not self.write_result[ndata][nparity] or not self.read_result[ndata][nparity] or \
                        not self.unconfig_result[ndata][nparity]:
                    test_result = False

        fun_test.test_assert(test_result, self.summary)

    def cleanup(self):
        super(ZeroDataWriteAndReadWithDataVolumeFailure, self).cleanup()


if __name__ == "__main__":

    ecscript = ECinQemuScript()
    ecscript.add_test_case(RndDataWriteAndRead25PctWithDataVolumeFailure())
    ecscript.add_test_case(ZeroDataWriteAndReadWithDataVolumeFailure())
    ecscript.run()
