from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut, DutInterface
from lib.fun.f1 import F1
from lib.host.storage_controller import StorageController
from lib.templates.storage.qemu_storage_template import QemuStorageTemplate
from web.fun_test.analytics_models_helper import VolumePerformanceHelper
import uuid
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
                    "type": DutInterface.INTERFACE_TYPE_PCIE
                }
            },
            "start_mode": F1.START_MODE_NORMAL
        }
    }
}


def compare(actual, expected, threshold, operation):
    if operation == "lesser":
        return (actual < (expected * (1 - threshold)) and ((expected - actual) > 2))
    else:
        return (actual > (expected * (1 + threshold)) and ((actual - expected) > 2))


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
        # TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()
        pass


class ECinQemuTestcase(FunTestCase):

    def describe(self):
        pass

    def check_num_dpcsh_cmds(self):

        self.num_dpcsh_cmds += 1
        fun_test.log("DPCsh command executed: {}".format(self.num_dpcsh_cmds))
        """
        if self.num_dpcsh_cmds >= self.max_dpcsh_cmds:
            self.qemu.start_dpcsh_proxy()
            self.num_dpcsh_cmds = 0
            self.storage_controller.disconnect()
            self.storage_controller = StorageController(target_ip=self.dut.host_ip,
                                                        target_port=self.dut.external_dpcsh_port)
        """

    def setup_ec_volume(self, ndata, nparity):

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
        self.uuids["lsv"] = []

        if self.use_lsv:
            # LS volume capacity is the ndata times of the BLT volume capacity
            self.volume_capacity["lsv"] = self.volume_capacity["ndata"] * ndata

            fun_test.log("LS volume needs to be configured. So increasing the BLT volume's capacity by 30% and "
                         "rounding that to the nearest 8MB value")
            eight_mb = 1024 * 1024 * 8
            for vtype in ["ndata", "nparity"]:
                tmp = self.volume_capacity[vtype] * (1 + self.lsv_pct)
                self.volume_capacity[vtype] = int(tmp + (eight_mb - (tmp % eight_mb)))

            # Setting the EC volume capacity also to same as the one of ndata volume capacity
            self.volume_capacity["ec"] = self.volume_capacity["ndata"]

        # Configuring ndata and nparity number of BLT volumes
        for vtype in ["ndata", "nparity"]:
            self.uuids[vtype] = []
            for i in range(self.num_volumes[vtype]):
                this_uuid = str(uuid.uuid4()).replace("-", "")[:10]
                self.uuids[vtype].append(this_uuid)
                self.uuids["blt"].append(this_uuid)
                try:
                    command_result = self.storage_controller.create_volume(
                        type=self.volume_types[vtype], capacity=self.volume_capacity[vtype],
                        block_size=self.volume_block[vtype], name=vtype+str(i), uuid=this_uuid,
                        command_duration=self.command_timeout)
                except Exception as ex:
                    pass
                fun_test.log(command_result)
                # fun_test.test_assert(command_result["status"], "Create {} {} BLT volume on DUT instance".
                #                     format(i, vtype))
                self.check_num_dpcsh_cmds()  # Calling this as a workaround for the bug SWOS-1434

        # Configuring EC volume on top of BLT volumes
        this_uuid = str(uuid.uuid4()).replace("-", "")[:10]
        self.uuids["ec"].append(this_uuid)
        command_result = self.storage_controller.create_volume(
            type=self.volume_types["ec"], capacity=self.volume_capacity["ec"], block_size=self.volume_block["ec"],
            name="ec1", uuid=this_uuid, ndata=self.num_volumes["ndata"], nparity=self.num_volumes["nparity"],
            pvol_id=self.uuids["blt"], command_duration=self.command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Create EC volume on DUT instance")
        self.check_num_dpcsh_cmds()  # Calling this as a workaround for the bug SWOS-1434
        attach_uuid = this_uuid

        # Configuring LS volume based on the script config settting
        if self.use_lsv:
            this_uuid = str(uuid.uuid4()).replace("-", "")[:10]
            self.uuids["lsv"].append(this_uuid)
            command_result = self.storage_controller.create_volume(
                type=self.volume_types["lsv"], capacity=self.volume_capacity["lsv"],
                block_size=self.volume_block["lsv"], name="lsv1", uuid=this_uuid, group=self.num_volumes["ndata"],
                pvol_id=self.uuids["ec"], command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Create LS volume on DUT instance")
            self.check_num_dpcsh_cmds()  # Calling this as a workaround for the bug SWOS-1434
            attach_uuid = this_uuid

        # Attaching/Exporting the EC/LS volume to the external server
        if not self.volume_attached:
            command_result = self.storage_controller.volume_attach_pcie(
                ns_id=self.ns_id, uuid=attach_uuid, command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Attaching EC/LS volume on DUT instance")
            self.check_num_dpcsh_cmds()  # Calling this as a workaround for the bug SWOS-1434
            self.volume_attached = True

        # disabling the error_injection for the EC volume
        command_result = {}
        command_result = self.storage_controller.poke("params/ecvol/error_inject 0")
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Disabling error_injection for EC volume on DUT instance")
        self.check_num_dpcsh_cmds()  # Calling this as a workaround for the bug SWOS-1434

        # Ensuring that the error_injection got disabled properly
        fun_test.sleep("Sleeping for a second to disable the error_injection", 1)
        command_result = {}
        command_result = self.storage_controller.peek("params/ecvol")
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Retrieving error_injection status on DUT instance")
        fun_test.test_assert_expected(actual=int(command_result["data"]["error_inject"]), expected=0,
                                      message="Ensuring error_injection got disabled")
        self.check_num_dpcsh_cmds()  # Calling this as a workaround for the bug SWOS-1434

        # Rebooting the qemu host before checking the disk as a workaround to the bug swos-1331
        fun_test.test_assert(self.qemu.reboot(timeout=self.command_timeout, retries=12), "Qemu Host Rebooted")

        # Checking that the volume is accessible to the host
        lsblk_output = self.host.lsblk()
        fun_test.test_assert(self.volume_name in lsblk_output, "{} device available".format(self.volume_name))
        fun_test.test_assert_expected(expected="disk", actual=lsblk_output[self.volume_name]["type"],
                                      message="{} device type check".format(self.volume_name))

        fun_test.shared_variables[self.ec_ratio]["uuids"] = self.uuids

    def cleanup_ec_volume(self, data, parity):

        self.ec_ratio = str(data) + str(parity)
        if self.ec_ratio not in fun_test.shared_variables:
            fun_test.shared_variables[self.ec_ratio] = {}

        attach_uuid = ""
        # Unconfiguring LS volume based on the script config settting
        if self.use_lsv:
            this_uuid = self.uuids["lsv"][0]
            command_result = self.storage_controller.delete_volume(
                type=self.volume_types["lsv"], capacity=self.volume_capacity["lsv"],
                block_size=self.volume_block["lsv"], name="lsv1", uuid=this_uuid, command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Delete LS volume on DUT instance")
            self.check_num_dpcsh_cmds()  # Calling this as a workaround for the bug SWOS-1434
            attach_uuid = this_uuid

        # Unconfiguring EC volume configured on top of BLT volumes
        this_uuid = self.uuids["ec"][0]
        command_result = self.storage_controller.delete_volume(
            type=self.volume_types["ec"], capacity=self.volume_capacity["ec"], block_size=self.volume_block["ec"],
            name="ec1", uuid=this_uuid, command_duration=self.command_timeout)
        fun_test.log(command_result)
        fun_test.test_assert(command_result["status"], "Delete EC volume on DUT instance")
        self.check_num_dpcsh_cmds()  # Calling this as a workaround for the bug SWOS-1434
        if not attach_uuid:
            attach_uuid = this_uuid

        # Unconfiguring ndata and nparity number of BLT volumes
        for vtype in ["ndata", "nparity"]:
            for i in range(self.num_volumes[vtype]):
                this_uuid = self.uuids[vtype][i]
                self.uuids["blt"].append(this_uuid)
                command_result = self.storage_controller.delete_volume(
                    type=self.volume_types[vtype], capacity=self.volume_capacity[vtype],
                    block_size=self.volume_block[vtype], name=vtype+str(i), uuid=this_uuid,
                    command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Delete {} {} BLT volume on DUT instance".
                                     format(i, vtype))
                self.check_num_dpcsh_cmds()  # Calling this as a workaround for the bug SWOS-1434

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

        # fio_bs_iodepth variable is a list of tuples in which the first element of the tuple refers the
        # block size & second one refers the iodepth going to used for that block size
        # Checking the block size and IO depth combo list availability
        if 'fio_bs_iodepth' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['fio_bs_iodepth']:
            benchmark_parsing = False
            fun_test.critical("Block size and IO depth combo to be used for this {} testcase is not available in "
                              "the {} file".format(testcase, benchmark_file))

        # Checking the availability of expected FIO results
        if 'expected_fio_result' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['expected_fio_result']:
            benchmark_parsing = False
            fun_test.critical("Benchmarking results for the block size and IO depth combo needed for this {} "
                              "testcase is not available in the {} file".format(testcase, benchmark_file))

        if len(self.fio_bs_iodepth) != len(self.expected_fio_result.keys()):
            benchmark_parsing = False
            fun_test.critical("Mismatch in block size and IO depth combo and its benchmarking results")

        # Checking the availability of expected volume level internal stats at the end of every FIO run
        if ('expected_volume_stats' not in benchmark_dict[testcase] or
                not benchmark_dict[testcase]['expected_volume_stats']):
            benchmark_parsing = False
            fun_test.critical("Expected internal volume stats needed for this {} testcase is not available in "
                              "the {} file".format(testcase, benchmark_file))

        if 'fio_pass_threshold' not in benchmark_dict[testcase]:
            self.fio_pass_threshold = .05
            fun_test.log("Setting FIO passing threshold percentage to {} for this {} testcase, because its not set in "
                         "the {} file".format(self.fio_pass_threshold, testcase, benchmark_file))

        if 'volume_pass_threshold' not in benchmark_dict[testcase]:
            self.volume_pass_threshold = 20
            fun_test.log("Setting volume passing threshold number to {} for this {} testcase, because its not set in "
                         "the {} file".format(self.volume_pass_threshold, testcase, benchmark_file))

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))
        fun_test.log("Block size and IO depth combo going to be used for this {} testcase: {}".
                     format(testcase, self.fio_bs_iodepth))
        fun_test.log("Benchmarking results going to be used for this {} testcase: \n{}".
                     format(testcase, self.expected_fio_result))
        fun_test.log("Expected internal volume stats for this {} testcase: \n{}".
                     format(testcase, self.expected_volume_stats))

        # End of benchmarking json file parsing

        self.topology = fun_test.shared_variables["topology"]
        self.dut = self.topology.get_dut_instance(index=0)
        fun_test.test_assert(self.dut, "Retrieved dut instance 0")
        self.host = self.topology.get_host_instance(dut_index=0, interface_index=0, host_index=0)
        self.qemu = QemuStorageTemplate(host=self.host, dut=self.dut)

        # Starting the dpc server in the qemu host
        self.qemu.start_dpc_server()
        fun_test.sleep("Waiting for the DPC server and DPCSH TCP proxy to settle down", self.iter_interval)
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

        # Creating input data file containing (data volume block size * ndata volume) bytes of random data
        self.input_size = self.volume_block["ndata"] * ndata
        return_size = self.qemu.dd(input_file=self.data_pattern, output_file=self.input_data,
                                   block_size=self.volume_block["ndata"], count=ndata)
        fun_test.test_assert_expected(self.input_size, return_size, "Input data creation")
        self.input_md5sum = self.qemu.md5sum(file_name=self.input_data)
        fun_test.test_assert(self.input_md5sum, "Finding md5sum for input data")

        # Starting the write test
        num_writes = self.dataset_size / self.input_size
        for blk in range(1, num_writes + 2):
            blk_write_result = ""
            if blk != 1:
                blk = blk * ndata - 1
            else:
                begin = blk
            end = begin + self.input_size - 1
            blk_write_result = self.qemu.nvme_write(device=self.nvme_block_device, start=blk, count=ndata - 1,
                                                    size=self.input_size, data=self.input_data)
            if blk_write_result != "Success":
                self.write_result[ndata][nparity] = False
                fun_test.critical("Write failed for {} to {} bytes".format(begin, end))
            else:
                fun_test.log("Write succeeded for {} to {} bytes".format(begin, end))
            begin = end + 1
        fun_test.test_assert(self.write_result[ndata][nparity], "Write operation for {} bytes".
                             format(self.dataset_size))

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
            blk_read_result = self.qemu.nvme_read(device=self.nvme_block_device, start=blk, count=ndata - 1,
                                                  size=self.input_size, data=output_file)
            if blk_read_result != "Success":
                self.read_result[ndata][nparity][index] = False
                fun_test.critical("Read failed for {} to {} bytes".format(begin, end))
            else:
                fun_test.log("Read succeeded for {} to {} bytes".format(begin, end))

            output_md5sum = self.qemu.md5sum(file_name=output_file)
            if output_md5sum == self.input_md5sum:
                fun_test.log("md5sum for {} to {} bytes {} matches with input md5sum {}".
                             format(begin, end, output_md5sum, self.input_md5sum))
            else:
                self.read_result[ndata][nparity][index] = False
                fun_test.critical("md5sum for {} to {} bytes {} is not matching with input md5sum {}".
                                  format(begin, end, output_md5sum, self.input_md5sum))
            begin = end + 1
        fun_test.test_assert(self.read_result[ndata][nparity][index],
                             "Read operation for {} bytes after failing {} data volumes".
                             format(self.dataset_size, index + 1))

    def run(self):

        pass

    def cleanup(self):

        # Check any plex needs to be re-enabled from failure_injection condition
        if hasattr(self, "trigger_plex_failure") and self.trigger_plex_failure:
            for index in self.failure_plex_indices:
                command_result = self.storage_controller.fail_volume(uuid=self.uuids["ndata"][index],
                                                                     command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Disable fault_injection from the ndata BLT volume "
                                                               "having the UUID {}".format(self.uuids["ndata"][index]))
                fun_test.sleep("Sleeping for a second to disable the fault_injection", 1)
                props_tree = "{}/{}/{}/{}".format("storage", "volumes", self.volume_types["ndata"],
                                                  self.uuids["ndata"][index])
                command_result = self.storage_controller.peek(props_tree)
                fun_test.log(command_result)
                fun_test.test_assert_expected(actual=int(command_result["data"]["fault_injection"]), expected=0,
                                              message="Ensuring fault_injection got disabled")

        self.storage_controller.disconnect()


class RndDataWriteAndReadWithDataVolumeFailure(ECinQemuTestcase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Sequential write and then read by failing m number of data volumes in n = k+m "
                                      "EC volume",
                              steps="""
        1. Run the outer loop from ndata_partition_start_range to ndata_partition_end_range. Say it as k
        2. Run the inner loop from nparity_start_range = min(int(ndata / 4) + 1, self.max_parity) to 
        nparity_end_range = min(ndata - 1, self.max_parity) + 1. Say it as m
        3. Configure k data and m parity BLT volumes.
        4. Configure k:m EC volume.
        5. Create a LS volume on top of the EC volume.
        6. Export (Attach) the above LS volume to PCIe controller. 
        7. Write dataset_size bytes of random data into the LSV in a sequential manner.
        8. Start a loop to run 0 to m-1 and inside it fail the data volume in that index and read back the previously
        written data   
        """)

    def setup(self):
        super(RndDataWriteAndReadWithDataVolumeFailure, self).setup()

    def run(self):

        testcase = self.__class__.__name__

        self.write_result = {}
        self.read_result = {}
        for ndata in range(self.ndata_partition_start_range, self.ndata_partition_end_range + 1):

            self.write_result[ndata] = {}
            self.read_result[ndata] = {}
            if not hasattr(self, "nparity_start_range"):
                self.nparity_start_range = min(int(ndata / 4) + 1, self.max_parity)
            if not hasattr(self, "nparity_end_range"):
                self.nparity_end_range = min(ndata - 1, self.max_parity)

            for nparity in range(self.nparity_start_range, self.nparity_end_range + 1):

                self.write_result[ndata][nparity] = True
                self.read_result[ndata][nparity] = {}

                # Creating ndata:npartiy EC volume
                self.setup_ec_volume(ndata, nparity)

                # Performing Write Test
                self.do_write_test(ndata, nparity)

                # Disabling the nparity number of data BLT volumes one after the other and trying to read the
                # previously written data back
                for index in range(nparity):
                    self.read_result[ndata][nparity][index] = True
                    # Start the dpc server to inject error into the data BLT volumes
                    self.qemu.start_dpc_server()
                    self.storage_controller.disconnect()
                    command_result = self.storage_controller.fail_volume(uuid=self.uuids["ndata"][index],
                                                                         command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Inject failure to the ndata BLT volume having the "
                                                                   "UUID {}".format(self.uuids["ndata"][index]))
                    self.check_num_dpcsh_cmds()  # Calling this as a workaround for the bug SWOS-1434
                    fun_test.sleep("to enable the fault_injection", 1)
                    props_tree = "{}/{}/{}/{}".format("storage", "volumes", self.volume_types["ndata"],
                                                      self.uuids["ndata"][index])
                    command_result = self.storage_controller.peek(props_tree)
                    fun_test.log(command_result)
                    fun_test.test_assert_expected(actual=int(command_result["data"]["fault_injection"]), expected=1,
                                                  message="Ensuring fault_injection got enabled",
                                                  ignore_on_success=True)
                    self.check_num_dpcsh_cmds()  # Calling this as a workaround for the bug SWOS-1434

                    # Rebooting the qemu host as a workaround for the bug #swos-1332
                    self.qemu.reboot()

                    # Performing read test
                    self.do_read_test(ndata, nparity, index)

                # Commented the below section because of the bug SWOS-1418
                # Starting the dpc server in the qemu host
                # self.qemu.start_dpc_server()
                # fun_test.sleep("Breathing...", 10)
                # self.storage_controller.disconnect()
                # self.storage_controller = StorageController(target_ip=self.dut.host_ip,
                #                                            target_port=self.dut.external_dpcsh_port)
                # self.cleanup_ec_volume(ndata, nparity)

    def cleanup(self):
        super(RndDataWriteAndReadWithDataVolumeFailure, self).cleanup()


class ZeroDataWriteAndReadWithDataVolumeFailure(ECinQemuTestcase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Sequential write and then read by failing m number of data volumes in n = k+m "
                                      "EC volume",
                              steps="""
        1. Run the outer loop from ndata_partition_start_range to ndata_partition_end_range. Say it as k
        2. Run the inner loop from nparity_start_range = min(int(ndata / 4) + 1, self.max_parity) to 
        nparity_end_range = min(ndata - 1, self.max_parity) + 1. Say it as m
        3. Configure k data and m parity BLT volumes.
        4. Configure k:m EC volume.
        5. Create a LS volume on top of the EC volume.
        6. Export (Attach) the above LS volume to PCIe controller. 
        7. Write dataset_size bytes of random data into the LSV in a sequential manner.
        8. Start a loop to run 0 to m-1 and inside it fail the data volume in that index and read back the previously
        written data   
        """)

    def setup(self):
        super(ZeroDataWriteAndReadWithDataVolumeFailure, self).setup()

    def run(self):

        testcase = self.__class__.__name__

        self.write_result = {}
        self.read_result = {}
        for ndata in range(self.ndata_partition_start_range, self.ndata_partition_end_range + 1):

            self.write_result[ndata] = {}
            self.read_result[ndata] = {}
            if not hasattr(self, "nparity_start_range"):
                self.nparity_start_range = min(int(ndata / 4) + 1, self.max_parity)
            if not hasattr(self, "nparity_end_range"):
                self.nparity_end_range = min(ndata - 1, self.max_parity)

            for nparity in range(self.nparity_start_range, self.nparity_end_range + 1):

                self.write_result[ndata][nparity] = True
                self.read_result[ndata][nparity] = {}

                # Creating ndata:npartiy EC volume
                self.setup_ec_volume(ndata, nparity)

                # Performing Write Test
                self.do_write_test(ndata, nparity)

                # Disabling the nparity number of data BLT volumes one after the other and trying to read the
                # previously written data back
                for index in range(nparity):
                    self.read_result[ndata][nparity][index] = True
                    # Start the dpc server to inject error into the data BLT volumes
                    self.qemu.start_dpc_server()
                    self.storage_controller.disconnect()
                    command_result = self.storage_controller.fail_volume(uuid=self.uuids["ndata"][index],
                                                                         command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Inject failure to the ndata BLT volume having the "
                                                                   "UUID {}".format(self.uuids["ndata"][index]))
                    self.check_num_dpcsh_cmds()  # Calling this as a workaround for the bug SWOS-1434
                    fun_test.sleep("to enable the fault_injection", 1)
                    props_tree = "{}/{}/{}/{}".format("storage", "volumes", self.volume_types["ndata"],
                                                      self.uuids["ndata"][index])
                    command_result = self.storage_controller.peek(props_tree)
                    fun_test.log(command_result)
                    fun_test.test_assert_expected(actual=int(command_result["data"]["fault_injection"]), expected=1,
                                                  message="Ensuring fault_injection got enabled",
                                                  ignore_on_success=True)
                    self.check_num_dpcsh_cmds()  # Calling this as a workaround for the bug SWOS-1434

                    # Rebooting the qemu host as a workaround for the bug #swos-1332
                    self.qemu.reboot()

                    # Performing read test
                    self.do_read_test(ndata, nparity, index)

                # Commented the below section because of the bug SWOS-1418
                # Starting the dpc server in the qemu host
                # self.qemu.start_dpc_server()
                # fun_test.sleep("Breathing...", 10)
                # self.storage_controller.disconnect()
                # self.storage_controller = StorageController(target_ip=self.dut.host_ip,
                #                                            target_port=self.dut.external_dpcsh_port)
                # self.cleanup_ec_volume(ndata, nparity)

    def cleanup(self):
        super(ZeroDataWriteAndReadWithDataVolumeFailure, self).cleanup()


if __name__ == "__main__":

    ecscript = ECinQemuScript()
    # ecscript.add_test_case(RndDataWriteAndReadWithDataVolumeFailure())
    ecscript.add_test_case(ZeroDataWriteAndReadWithDataVolumeFailure())
    ecscript.run()
