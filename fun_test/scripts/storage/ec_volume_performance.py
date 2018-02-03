from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut, DutInterface
from lib.fun.f1 import F1
from lib.host.storage_controller import StorageController
from lib.host.traffic_generator import TrafficGenerator
import uuid, re

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
                    "vms": 0,
                    "type": DutInterface.INTERFACE_TYPE_PCIE
                }
            },
            "start_mode": F1.START_MODE_DPCSH_ONLY
        }
    },
    "tg_info": {
        0: {
            "type": TrafficGenerator.TRAFFIC_GENERATOR_TYPE_LINUX_HOST
        }
    }
}

fun_test.shared_variables["configured"] = False


class ECVolumeLevelScript(FunTestScript):
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

        topology = fun_test.shared_variables["topology"]
        dut = topology.get_dut_instance(index=0)
        fun_test.test_assert(dut, "Retrieved dut instance 0")
        linux_host = topology.get_tg_instance(tg_index=0)

        self.command_timeout = 5
        self.ec_ratio = str(self.ec_coding["ndata"]) + str(self.ec_coding["nparity"])

        if self.use_lsv:
            # LS volume capacity is the ndata times of the BLT volume capacity
            self.volume_capacity["lsv"] = self.volume_capacity["ndata"] * self.ec_coding["ndata"]

            fun_test.log("LS volume needs to be configured. So increasing the BLT volume's capacity by 30% and "
                         "rounding that to the nearest 8MB value")
            eight_mb = 1024 * 1024 * 8
            for type in sorted(self.ec_coding):
                tmp = self.volume_capacity[type] * (1 + self.lsv_pct)
                self.volume_capacity[type] = int(tmp + (eight_mb - (tmp % eight_mb)))

            # Setting the EC volume capacity also to same as the one of ndata volume capacity
            self.volume_capacity["ec"] = self.volume_capacity["ndata"]

        if self.ec_ratio not in fun_test.shared_variables or \
                not fun_test.shared_variables[self.ec_ratio]["setup_created"]:
            fun_test.shared_variables[self.ec_ratio] = {}
            fun_test.shared_variables[self.ec_ratio]["setup_created"] = False
            self.uuids = {}
            self.uuids["blt"] = []
            self.uuids["ec"] = []
            self.uuids["lsv"] = []

            # Configuring the controller
            storage_controller = StorageController(target_ip=dut.host_ip, target_port=dut.external_dpcsh_port)
            command_result = {}
            command_result = storage_controller.command("enable_counters")
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling counters on DUT instance 0")

            command_result = {}
            command_result = storage_controller.ip_cfg(ip=dut.data_plane_ip,
                                                       expected_command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg {} on DUT instance 0".format(dut.data_plane_ip))

            # Configuring ndata and nparity number of BLT volumes
            for type in sorted(self.ec_coding):
                self.uuids[type] = []
                for i in range(self.ec_coding[type]):
                    this_uuid = str(uuid.uuid4()).replace("-", "")[:10]
                    self.uuids[type].append(this_uuid)
                    self.uuids["blt"].append(this_uuid)
                    command_result = storage_controller.create_volume(type=self.volume_types[type],
                                                                      capacity=self.volume_capacity[type],
                                                                      block_size=self.volume_block[type],
                                                                      name=type+str(i), uuid=this_uuid,
                                                                      expected_command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Create {} {} BLT volume on DUT instance 0".
                                         format(i, type))

            # Configuring EC volume on top of BLT volumes
            this_uuid = str(uuid.uuid4()).replace("-", "")[:10]
            self.uuids["ec"].append(this_uuid)
            command_result = storage_controller.create_volume(type=self.volume_types["ec"],
                                                              capacity=self.volume_capacity["ec"],
                                                              block_size=self.volume_block["ec"], name="ec1",
                                                              uuid=this_uuid, ndata=self.ec_coding["ndata"],
                                                              nparity=self.ec_coding["nparity"],
                                                              pvol_id=self.uuids["blt"],
                                                              expected_command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Create EC volume on DUT instance 0")
            attach_uuid = this_uuid

            # Configuring LS volume based on the script config settting
            if self.use_lsv:
                this_uuid = str(uuid.uuid4()).replace("-", "")[:10]
                self.uuids["lsv"].append(this_uuid)
                command_result = storage_controller.create_volume(type=self.volume_types["lsv"],
                                                                  capacity=self.volume_capacity["lsv"],
                                                                  block_size=self.volume_block["lsv"], name="lsv1",
                                                                  uuid=this_uuid, group=self.ec_coding["ndata"],
                                                                  pvol_id=self.uuids["ec"],
                                                                  expected_command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Create LS volume on DUT instance 0")
                attach_uuid = this_uuid

            # Attaching/Exporting the EC/LS volume to the external server
            command_result = {}
            command_result = storage_controller.attach_volume(ns_id=self.ns_id, uuid=attach_uuid,
                                                              remote_ip=linux_host.internal_ip,
                                                              expected_command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Attaching EC/LS volume on DUT instance 0")

            # disabling the error_injection for the EC volume
            command_result = {}
            command_result = storage_controller.command("poke params/ecvol/error_inject 0")
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Disabling error_injection for EC volume on DUT instance 0")

            # Ensuring that the error_injection got disabled properly
            fun_test.sleep("Sleeping for a second to disable the error_injection", 1)
            command_result = {}
            command_result = storage_controller.peek("params/ecvol")
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Retrieving error_injection status on DUT instance 0")
            fun_test.test_assert_expected(actual=int(command_result["data"]["error_inject"]), expected=0,
                                          message="Ensuring error_injection got disabled")

            fun_test.shared_variables[self.ec_ratio]["uuids"] = self.uuids
            fun_test.shared_variables[self.ec_ratio]["setup_created"] = True

    # def fioseqwriteseqreadonly(self):
    def run(self):

        testcase = self.__class__.__name__

        topology = fun_test.shared_variables["topology"]
        dut = topology.get_dut_instance(index=0)
        fun_test.test_assert(dut, "Retrieved dut instance 0")

        linux_host = topology.get_tg_instance(tg_index=0)
        destination_ip = dut.data_plane_ip

        self.uuids = fun_test.shared_variables[self.ec_ratio]["uuids"]

        # Going to run the FIO test for the block size and iodepth combo listed in fio_bs_iodepth in both write only
        # & read only modes
        fio_result = {}
        internal_result = {}
        initial_volume_status = {}
        fio_output = {}
        final_volume_status = {}
        diff_volume_stats = {}

        volumes = sorted(self.ec_coding)
        volumes.append("ec")
        if self.use_lsv and self.check_lsv_stats:
            volumes.append("lsv")

        # Check any plex needs to be induced to fail and if so do the same
        storage_controller = StorageController(target_ip=dut.host_ip, target_port=dut.external_dpcsh_port)
        if hasattr(self, "trigger_plex_failure") and self.trigger_plex_failure:
            for index in self.failure_plex_indices:
                command_result = storage_controller.fail_volume(uuid=self.uuids["ndata"][index],
                                                                expected_command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Inject failure to the ndata BLT volume having the "
                                                               "UUID {}".format(self.uuids["ndata"][index]))
                fun_test.sleep("Sleeping for a second to enable the fault_injection", 1)
                props_tree = "{}/{}/{}/{}".format("storage", "volumes", self.volume_types["ndata"],
                                                  self.uuids["ndata"][index])
                command_result = storage_controller.peek(props_tree)
                fun_test.log(command_result)
                fun_test.test_assert_expected(actual=int(command_result["data"]["fault_injection"]), expected=1,
                                              message="Ensuring fault_injection got enabled")

        for combo in self.fio_bs_iodepth:
            fio_result[combo] = {}
            internal_result[combo] = {}
            initial_volume_status[combo] = {}
            fio_output[combo] = {}
            final_volume_status[combo] = {}
            diff_volume_stats[combo] = {}

            if combo in self.expected_volume_stats:
                expected_volume_stats = self.expected_volume_stats[combo]
            else:
                expected_volume_stats = self.expected_volume_stats

            for mode in self.fio_modes:

                tmp = combo.split(',')
                fio_block_size = tmp[0].strip('() ') + 'k'
                fio_iodepth = tmp[1].strip('() ')
                fio_result[combo][mode] = True
                internal_result[combo][mode] = True

                # Pulling initial volume stats of all the volumes from the DUT in dictionary format
                fun_test.log("Pulling initial stats of the all the volumes from the DUT in dictionary format before "
                             "the test")
                initial_volume_status[combo][mode] = {}
                for type in volumes:
                    initial_volume_status[combo][mode][type] = {}
                    for index, uuid in enumerate(self.uuids[type]):
                        initial_volume_status[combo][mode][type][index] = {}
                        props_tree = "{}/{}/{}/{}".format("storage", "volumes", self.volume_types[type], uuid)
                        command_result = {}
                        command_result = storage_controller.peek(props_tree)
                        fun_test.simple_assert(command_result["status"], "Initial {} {} volume stats".
                                               format(type, index))
                        initial_volume_status[combo][mode][type][index] = command_result["data"]
                        fun_test.log("{} {} volume Status at the beginning of the test:".format(type, index))
                        fun_test.log(initial_volume_status[combo][mode][type][index])

                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fun_test.log("Running FIO {} only test with the block size and IO depth set to {} & {} for the EC "
                             "coding {}".format(mode, fio_block_size, fio_iodepth, self.ec_ratio))
                fio_output[combo][mode] = {}
                fio_output[combo][mode] = linux_host.fio(destination_ip=destination_ip, rw=mode, bs=fio_block_size,
                                                         iodepth=fio_iodepth, **self.fio_cmd_args)
                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output[combo][mode])
                # fun_test.simple_assert(fio_output[combo][mode], "Execution of FIO command")
                fun_test.sleep("Sleeping for 5 seconds between iterations", 5)

                # Pulling volume stats of all the volumes from the DUT in dictionary format after the test
                fun_test.log("Pulling volume stats of all volumes after the FIO test")
                final_volume_status[combo][mode] = {}
                for type in volumes:
                    final_volume_status[combo][mode][type] = {}
                    for index, uuid in enumerate(self.uuids[type]):
                        final_volume_status[combo][mode][type][index] = {}
                        props_tree = "{}/{}/{}/{}".format("storage", "volumes", self.volume_types[type], uuid)
                        command_result = {}
                        command_result = storage_controller.peek(props_tree)
                        fun_test.simple_assert(command_result["status"], "Initial {} {} volume stats".
                                               format(type, index))
                        final_volume_status[combo][mode][type][index] = command_result["data"]
                        fun_test.log("{} {} volume Status at the end of the test:".format(type, index))
                        fun_test.log(final_volume_status[combo][mode][type][index])

                # Finding the difference between the internal volume stats before and after the test
                diff_volume_stats[combo][mode] = {}
                for type in volumes:
                    diff_volume_stats[combo][mode][type] = {}
                    for index in range(len(self.uuids[type])):
                        diff_volume_stats[combo][mode][type][index] = {}
                        for fkey, fvalue in final_volume_status[combo][mode][type][index].items():
                            # Don't compute the difference of stats which is not defined in expected_volume_stats in
                            # the json config file
                            if fkey not in expected_volume_stats[mode][type][str(index)] \
                                    or fkey == "fault_injection":
                                diff_volume_stats[combo][mode][type][index][fkey] = fvalue
                                continue
                            if fkey in initial_volume_status[combo][mode][type][index]:
                                ivalue = initial_volume_status[combo][mode][type][index][fkey]
                                diff_volume_stats[combo][mode][type][index][fkey] = fvalue - ivalue
                        fun_test.log("Difference of {} {} BLT volume status before and after the test:".
                                     format(type, index))
                        fun_test.log(diff_volume_stats[combo][mode][type][index])

                if not fio_output[combo][mode]:
                    fio_result[combo][mode] = False
                    fun_test.critical("No output from FIO test, hence moving to the next variation")
                    continue

                # Comparing the FIO results with the expected value for the current block size and IO depth combo
                for op, stats in self.expected_fio_result[combo][mode].items():
                    for field, value in stats.items():
                        actual = fio_output[combo][mode][op][field]
                        if actual < (value * (1 - self.fio_pass_threshold)) and ((value - actual) > 2):
                            fio_result[combo][mode] = False
                            fun_test.critical("{} {} {} got dropped more than the allowed threshold value {}".
                                              format(op, field, actual, value))
                        elif actual > (value * (1 + self.fio_pass_threshold)) and ((actual - value) > 2):
                            fun_test.log("{} {} {} got increased more than the expected value {}".format(op, field,
                                                                                                         actual, value))
                        else:
                            fun_test.log("{} {} {} is within the expected range {}".format(op, field, actual, value))

                # Comparing the internal volume stats with the expected value
                for type in volumes:
                    for index in range(len(self.uuids[type])):
                        for ekey, evalue in expected_volume_stats[mode][type][str(index)].items():
                            if evalue == -1:
                                fun_test.log("Ignoring the {}'s key checking for {} {} volume".format(ekey, type,
                                                                                                      index))
                                continue
                            if ekey in diff_volume_stats[combo][mode][type][index]:
                                actual = diff_volume_stats[combo][mode][type][index][ekey]
                                if actual != evalue:
                                    if (actual < evalue) and ((evalue - actual) <= self.volume_pass_threshold):
                                        fun_test.critical("Final {} value {} of {} {} volume is within the expected "
                                                          "range {}".format(ekey, actual, type, index, evalue, type,
                                                                            index))
                                    elif (actual > evalue) and ((actual - evalue) <= self.volume_pass_threshold):
                                        fun_test.critical("Final {} value {} of {} {} volume is within the expected "
                                                          "range {}".format(ekey, actual, type, index, evalue, type,
                                                                            index))
                                    else:
                                        internal_result[combo][mode] = False
                                        fun_test.critical("Final {} value {} of {} {} volume is not equal to the "
                                                          "expected value {}".format(ekey, actual, type, index, evalue,
                                                                                     type, index))
                                else:
                                    fun_test.log("Final {} value {} of {} {} volume is equal to the expected value {}".
                                                 format(ekey, actual, type, index, evalue))
                            else:
                                internal_result[combo][mode] = False
                                fun_test.critical("{} is not found in {} {} volume status".format(ekey, type, index))

        # Posting the final status of the test result
        fun_test.log(fio_result)
        fun_test.log(internal_result)
        for combo in self.fio_bs_iodepth:
            for mode in self.fio_modes:
                fun_test.test_assert(fio_result[combo][mode], "FIO {} performance check for the block size & IO depth "
                                                              "combo {}".format(mode, combo))
                fun_test.test_assert(internal_result[combo][mode], "Volume stats check for the {} test for the block "
                                                                   "size & IO depth combo {}".format(mode, combo))

    def old_run(self):

        testcase = self.__class__.__name__
        method_str = re.split(r"EC\d+", testcase)[1].lower()
        method_name = getattr(self, method_str)
        method_name()

    def cleanup(self):

        topology = fun_test.shared_variables["topology"]
        dut = topology.get_dut_instance(index=0)

        # Check any plex needs to be re-enabled from failure_injection condition
        storage_controller = StorageController(target_ip=dut.host_ip, target_port=dut.external_dpcsh_port)
        if hasattr(self, "trigger_plex_failure") and self.trigger_plex_failure:
            for index in self.failure_plex_indices:
                command_result = storage_controller.fail_volume(uuid=self.uuids["ndata"][index],
                                                                expected_command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Disable fault_injection from the ndata BLT volume "
                                                               "having the UUID {}".format(self.uuids["ndata"][index]))
                fun_test.sleep("Sleeping for a second to disable the fault_injection", 1)
                props_tree = "{}/{}/{}/{}".format("storage", "volumes", self.volume_types["ndata"],
                                                  self.uuids["ndata"][index])
                command_result = storage_controller.peek(props_tree)
                fun_test.log(command_result)
                fun_test.test_assert_expected(actual=int(command_result["data"]["fault_injection"]), expected=0,
                                              message="Ensuring fault_injection got enabled")


class EC21FioSeqWriteSeqReadOnly(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Sequential Write & Read only performance of EC volume",
                              steps="""
        1. Create 3 BLT volumes on dut instance 0.
        2. Create a 2:1 EC volume on top of the 3 BLT volumes.
        3. Create a LS volume on top of the EC volume.
        4. Export (Attach) the above LS volume to external Linux instance/container. 
        5. Run the FIO sequential write and read only test(without verify) for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold.
        """)

    def setup(self):
        super(EC21FioSeqWriteSeqReadOnly, self).setup()

    def run(self):
        super(EC21FioSeqWriteSeqReadOnly, self).run()

    def cleanup(self):
        super(EC21FioSeqWriteSeqReadOnly, self).cleanup()


class EC21FioSeqAndRandReadOnlyWithFailure(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Sequential and Random Read only performance of EC volume with a plex failure",
                              steps="""
        1. Create 3 BLT volumes on dut instance 0.
        2. Create a 2:1 EC volume on top of the 3 BLT volumes.
        3. Create a LS volume on top of the EC volume.
        4. Export (Attach) the above LS volume to external Linux instance/container.
        5. Inject failure in one of the ndata BLT volume
        6. Run the FIO sequential and random read only test(without verify) for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold.
        """)

    def setup(self):
        super(EC21FioSeqAndRandReadOnlyWithFailure, self).setup()

    def run(self):
        super(EC21FioSeqAndRandReadOnlyWithFailure, self).run()

    def cleanup(self):
        super(EC21FioSeqAndRandReadOnlyWithFailure, self).cleanup()


class EC21FioRandWriteRandReadOnly(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Random Write & Read only performance of EC volume",
                              steps="""
        1. Create 3 BLT volumes in dut instance 0.
        2. Create a 2:1 EC volume on top of the 3 BLT volumes.
        3. Create a LS volume on top of the EC volume based on use_lsv config.
        4. Export (Attach) the above EC or LS volume based on use_lsv config to external Linux instance/container.
        5. Run the FIO random write and read only test(without verify) for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold.
        """)

    def setup(self):
        super(EC21FioRandWriteRandReadOnly, self).setup()

    def run(self):
        super(EC21FioRandWriteRandReadOnly, self).run()

    def cleanup(self):
        super(EC21FioRandWriteRandReadOnly, self).cleanup()


class EC21FioSeqReadWriteMix(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Sequential 75% Write & 25% Read performance of EC volume",
                              steps="""
        1. Create 3 BLT volumes in dut instance 0.
        2. Create a 2:1 EC volume on top of the 3 BLT volumes.
        3. Create a LS volume on top of the EC volume based on use_lsv config.
        5. Export (Attach) the above EC or LS volume based on use_lsv config to external Linux instance/container.
        6. Run the FIO sequential write and read mix test with 3:1 ratio for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold.
        """)

    def setup(self):
        super(EC21FioSeqReadWriteMix, self).setup()

    def run(self):
        super(EC21FioSeqReadWriteMix, self).run()

    def cleanup(self):
        super(EC21FioSeqReadWriteMix, self).cleanup()


class EC21FioRandReadWriteMix(ECVolumeLevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Random 75% Write & 25% Read performance of EC volume",
                              steps="""
        1. Create 3 BLT volumes in dut instance 0.
        2. Create a 2:1 EC volume on top of the 3 BLT volumes.
        3. Create a LS volume on top of the EC volume based on use_lsv config.
        5. Export (Attach) the above EC or LS volume based on use_lsv config to external Linux instance/container.
        6. Run the FIO random write and read mix test with 3:1 ratio for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold.
        """)

    def setup(self):
        super(EC21FioRandReadWriteMix, self).setup()

    def run(self):
        super(EC21FioRandReadWriteMix, self).run()

    def cleanup(self):
        super(EC21FioRandReadWriteMix, self).cleanup()


if __name__ == "__main__":

    ecscript = ECVolumeLevelScript()
    ecscript.add_test_case(EC21FioSeqWriteSeqReadOnly())
    ecscript.add_test_case(EC21FioRandWriteRandReadOnly())
    ecscript.add_test_case(EC21FioSeqAndRandReadOnlyWithFailure())
    ecscript.add_test_case(EC21FioSeqReadWriteMix())
    ecscript.add_test_case(EC21FioRandReadWriteMix())
    ecscript.run()
