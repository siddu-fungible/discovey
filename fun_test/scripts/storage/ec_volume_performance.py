from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut, DutInterface
from lib.fun.f1 import F1
from lib.host.storage_controller import StorageController
from lib.host.traffic_generator import TrafficGenerator
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


def post_results(volume, test, block_size, io_depth, size, operation, write_iops, read_iops, write_bw, read_bw,
                 write_latency, read_latency):
    for i in ["write_iops", "read_iops", "write_bw", "read_bw", "write_latency", "read_latency"]:
        if eval("type({}) is tuple".format(i)):
            exec ("{0} = {0}[0]".format(i))

    VolumePerformanceHelper().add_entry(key=fun_test.get_version(),
                                        volume=volume,
                                        test=test,
                                        block_size=block_size,
                                        io_depth=int(io_depth),
                                        size=size,
                                        operation=operation,
                                        write_iops=write_iops,
                                        read_iops=read_iops,
                                        write_bw=write_bw,
                                        read_bw=read_bw,
                                        write_latency=write_latency,
                                        read_latency=read_latency)
    result = []
    arg_list = post_results.func_code.co_varnames[:12]
    for arg in arg_list:
        result.append(str(eval(arg)))
    result = ",".join(result)
    fun_test.log("Result: {}".format(result))


def compare(actual, expected, threshold, operation):
    if operation == "lesser":
        return (actual < (expected * (1 - threshold)) and ((expected - actual) > 2))
    else:
        return (actual > (expected * (1 + threshold)) and ((actual - expected) > 2))


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
        TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()
        # pass


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

        self.topology = fun_test.shared_variables["topology"]
        self.dut = self.topology.get_dut_instance(index=0)
        fun_test.test_assert(self.dut, "Retrieved dut instance 0")
        self.linux_host = self.topology.get_tg_instance(tg_index=0)
        destination_ip = self.dut.data_plane_ip
        self.storage_controller = StorageController(target_ip=self.dut.host_ip,
                                                    target_port=self.dut.external_dpcsh_port)

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
            command_result = {}
            command_result = self.storage_controller.command(command="enable_counters", legacy=True)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling counters on DUT instance 0")

            command_result = {}
            command_result = self.storage_controller.ip_cfg(ip=self.dut.data_plane_ip,
                                                            command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg {} on DUT instance 0".format(self.dut.data_plane_ip))

            # Configuring ndata and nparity number of BLT volumes
            for type in sorted(self.ec_coding):
                self.uuids[type] = []
                for i in range(self.ec_coding[type]):
                    this_uuid = str(uuid.uuid4()).replace("-", "")[:10]
                    self.uuids[type].append(this_uuid)
                    self.uuids["blt"].append(this_uuid)
                    command_result = self.storage_controller.create_volume(
                        type=self.volume_types[type], capacity=self.volume_capacity[type],
                        block_size=self.volume_block[type], name=type+str(i), uuid=this_uuid,
                        command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Create {} {} BLT volume on DUT instance 0".
                                         format(i, type))

            # Configuring EC volume on top of BLT volumes
            this_uuid = str(uuid.uuid4()).replace("-", "")[:10]
            self.uuids["ec"].append(this_uuid)
            command_result = self.storage_controller.create_volume(
                type=self.volume_types["ec"], capacity=self.volume_capacity["ec"], block_size=self.volume_block["ec"],
                name="ec1", uuid=this_uuid, ndata=self.ec_coding["ndata"], nparity=self.ec_coding["nparity"],
                pvol_id=self.uuids["blt"], command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Create EC volume on DUT instance 0")
            attach_uuid = this_uuid

            # Configuring LS volume based on the script config settting
            if self.use_lsv:
                this_uuid = str(uuid.uuid4()).replace("-", "")[:10]
                self.uuids["lsv"].append(this_uuid)
                command_result = self.storage_controller.create_volume(
                    type=self.volume_types["lsv"], capacity=self.volume_capacity["lsv"],
                    block_size=self.volume_block["lsv"], name="lsv1", uuid=this_uuid, group=self.ec_coding["ndata"],
                    pvol_id=self.uuids["ec"], command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Create LS volume on DUT instance 0")
                attach_uuid = this_uuid

            # Attaching/Exporting the EC/LS volume to the external server
            command_result = {}
            command_result = self.storage_controller.volume_attach_remote(
                ns_id=self.ns_id, uuid=attach_uuid, remote_ip=self.linux_host.internal_ip,
                command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Attaching EC/LS volume on DUT instance 0")

            # disabling the error_injection for the EC volume
            command_result = {}
            command_result = self.storage_controller.poke("params/ecvol/error_inject 0")
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Disabling error_injection for EC volume on DUT instance 0")

            # Ensuring that the error_injection got disabled properly
            fun_test.sleep("Sleeping for a second to disable the error_injection", 1)
            command_result = {}
            command_result = self.storage_controller.peek("params/ecvol")
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Retrieving error_injection status on DUT instance 0")
            fun_test.test_assert_expected(actual=int(command_result["data"]["error_inject"]), expected=0,
                                          message="Ensuring error_injection got disabled")

            fun_test.shared_variables[self.ec_ratio]["setup_created"] = True
            # fun_test.shared_variables[self.ec_ratio]["storage_controller"] = self.storage_controller
            fun_test.shared_variables[self.ec_ratio]["uuids"] = self.uuids

            # Executing the FIO command to warm up the system
            if self.warm_up_traffic:
                fun_test.log("Executing the FIO command to warm up the system")
                fio_output = self.linux_host.remote_fio(destination_ip=destination_ip, **self.warm_up_fio_cmd_args)
                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output)
                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[4:]

        destination_ip = self.dut.data_plane_ip
        self.uuids = fun_test.shared_variables[self.ec_ratio]["uuids"]
        # self.storage_controller = fun_test.shared_variables[self.ec_ratio]["storage_controller"]

        # Going to run the FIO test for the block size and iodepth combo listed in fio_bs_iodepth in both write only
        # & read only modes
        fio_result = {}
        fio_output = {}
        internal_result = {}
        initial_volume_status = {}
        final_volume_status = {}
        diff_volume_stats = {}
        initial_stats = {}
        final_stats = {}
        diff_stats = {}

        volumes = sorted(self.ec_coding)
        volumes.append("ec")
        if self.use_lsv and self.check_lsv_stats:
            volumes.append("lsv")

        # Check any plex needs to be induced to fail and if so do the same
        if hasattr(self, "trigger_plex_failure") and self.trigger_plex_failure:
            for index in self.failure_plex_indices:
                command_result = self.storage_controller.fail_volume(uuid=self.uuids["ndata"][index],
                                                                     command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Inject failure to the ndata BLT volume having the "
                                                               "UUID {}".format(self.uuids["ndata"][index]))
                fun_test.sleep("Sleeping for a second to enable the fault_injection", 1)
                props_tree = "{}/{}/{}/{}".format("storage", "volumes", self.volume_types["ndata"],
                                                  self.uuids["ndata"][index])
                command_result = self.storage_controller.peek(props_tree)
                fun_test.log(command_result)
                fun_test.test_assert_expected(actual=int(command_result["data"]["fault_injection"]), expected=1,
                                              message="Ensuring fault_injection got enabled")

        table_data_headers = ["Block Size", "IO Depth", "Size", "Operation", "Write IOPS", "Read IOPS",
                              "Write Throughput in KiB/s", "Read Throughput in KiB/s", "Write Latency in uSecs",
                              "Read Latency in uSecs"]
        table_data_cols = ["block_size", "iodepth", "size", "mode", "writeiops", "readiops", "writebw", "readbw",
                           "writelatency", "readlatency"]
        table_data_rows = []

        for combo in self.fio_bs_iodepth:
            fio_result[combo] = {}
            fio_output[combo] = {}
            internal_result[combo] = {}
            initial_volume_status[combo] = {}
            final_volume_status[combo] = {}
            diff_volume_stats[combo] = {}
            initial_stats[combo] = {}
            final_stats[combo] = {}
            diff_stats[combo] = {}

            if combo in self.expected_volume_stats:
                expected_volume_stats = self.expected_volume_stats[combo]
            else:
                expected_volume_stats = self.expected_volume_stats

            if combo in self.expected_stats:
                expected_stats = self.expected_stats[combo]
            else:
                expected_stats = self.expected_stats

            for mode in self.fio_modes:

                tmp = combo.split(',')
                fio_block_size = tmp[0].strip('() ') + 'k'
                fio_iodepth = tmp[1].strip('() ')
                fio_result[combo][mode] = True
                internal_result[combo][mode] = True
                row_data_dict = {}
                row_data_dict["mode"] = mode
                row_data_dict["block_size"] = fio_block_size
                row_data_dict["iodepth"] = fio_iodepth
                row_data_dict["size"] = self.fio_cmd_args["size"]

                # Pulling initial volume stats of all the volumes from the DUT in dictionary format
                fun_test.log("Pulling initial stats of the all the volumes from the DUT in dictionary format before "
                             "the test")
                initial_volume_status[combo][mode] = {}
                for type in volumes:
                    initial_volume_status[combo][mode][type] = {}
                    for index, uuid in enumerate(self.uuids[type]):
                        initial_volume_status[combo][mode][type][index] = {}
                        storage_props_tree = "{}/{}/{}/{}".format("storage", "volumes", self.volume_types[type], uuid)
                        command_result = {}
                        command_result = self.storage_controller.peek(storage_props_tree)
                        fun_test.simple_assert(command_result["status"], "Initial {} {} volume stats".
                                               format(type, index))
                        initial_volume_status[combo][mode][type][index] = command_result["data"]
                        fun_test.log("{} {} volume Status at the beginning of the test:".format(type, index))
                        fun_test.log(initial_volume_status[combo][mode][type][index])

                # Pulling the initial stats in dictionary format
                initial_stats[combo][mode] = {}
                for key, value in self.stats_list.items():
                    if key not in initial_stats[combo][mode]:
                        initial_stats[combo][mode][key] = {}
                    if value:
                        for item in value:
                            props_tree = "{}/{}/{}".format("stats", key, item)
                            command_result = self.storage_controller.peek(props_tree)
                            fun_test.simple_assert(command_result["status"], "Initial {} stats of DUT Instance 0".
                                                   format(props_tree))
                            initial_stats[combo][mode][key][item] = command_result["data"]
                    else:
                        props_tree = "{}/{}".format("stats", key)
                        command_result = self.storage_controller.peek(props_tree)
                        fun_test.simple_assert(command_result["status"], "Initial {} stats of DUT Instance 0".
                                               format(props_tree))
                        initial_stats[combo][mode][key] = command_result["data"]
                    fun_test.log("{} stats at the beginning of the test:".format(key))
                    fun_test.log(initial_stats[combo][mode][key])

                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fun_test.log("Running FIO {} only test with the block size and IO depth set to {} & {} for the EC "
                             "coding {}".format(mode, fio_block_size, fio_iodepth, self.ec_ratio))
                fio_output[combo][mode] = {}
                fio_output[combo][mode] = self.linux_host.remote_fio(destination_ip=destination_ip, rw=mode,
                                                                     bs=fio_block_size, iodepth=fio_iodepth,
                                                                     **self.fio_cmd_args)
                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output[combo][mode])
                # fun_test.simple_assert(fio_output[combo][mode], "Execution of FIO command")
                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)

                # Pulling volume stats of all the volumes from the DUT in dictionary format after the test
                fun_test.log("Pulling volume stats of all volumes after the FIO test")
                final_volume_status[combo][mode] = {}
                for type in volumes:
                    final_volume_status[combo][mode][type] = {}
                    for index, uuid in enumerate(self.uuids[type]):
                        final_volume_status[combo][mode][type][index] = {}
                        storage_props_tree = "{}/{}/{}/{}".format("storage", "volumes", self.volume_types[type], uuid)
                        command_result = {}
                        command_result = self.storage_controller.peek(storage_props_tree)
                        fun_test.simple_assert(command_result["status"], "Initial {} {} volume stats".
                                               format(type, index))
                        final_volume_status[combo][mode][type][index] = command_result["data"]
                        fun_test.log("{} {} volume Status at the end of the test:".format(type, index))
                        fun_test.log(final_volume_status[combo][mode][type][index])

                # Pulling the final stats in dictionary format
                final_stats[combo][mode] = {}
                for key, value in self.stats_list.items():
                    if key not in final_stats[combo][mode]:
                        final_stats[combo][mode][key] = {}
                    if value:
                        for item in value:
                            props_tree = "{}/{}/{}".format("stats", key, item)
                            command_result = self.storage_controller.peek(props_tree)
                            fun_test.simple_assert(command_result["status"], "Final {} stats of DUT Instance 0".
                                                   format(props_tree))
                            final_stats[combo][mode][key][item] = command_result["data"]
                    else:
                        props_tree = "{}/{}".format("stats", key)
                        command_result = self.storage_controller.peek(props_tree)
                        fun_test.simple_assert(command_result["status"], "Final {} stats of DUT Instance 0".
                                               format(props_tree))
                        final_stats[combo][mode][key] = command_result["data"]
                    fun_test.log("{} stats at the end of the test:".format(key))
                    fun_test.log(final_stats[combo][mode][key])

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

                # Finding the difference between the stats before and after the test
                diff_stats[combo][mode] = {}
                for key, value in self.stats_list.items():
                    diff_stats[combo][mode][key] = {}
                    for fkey, fvalue in final_stats[combo][mode][key].items():
                        ivalue = initial_stats[combo][mode][key][fkey]
                        diff_stats[combo][mode][key][fkey] = fvalue - ivalue
                    fun_test.log("Difference of {} stats before and after the test:".format(key))
                    fun_test.log(diff_stats[combo][mode][key])

                if not fio_output[combo][mode]:
                    fio_result[combo][mode] = False
                    fun_test.critical("No output from FIO test, hence moving to the next variation")
                    continue

                # Comparing the FIO results with the expected value for the current block size and IO depth combo
                for op, stats in self.expected_fio_result[combo][mode].items():
                    for field, value in stats.items():
                        actual = fio_output[combo][mode][op][field]
                        row_data_dict[op + field] = (actual, int(round((value * (1 - self.fio_pass_threshold)))),
                                                     int((value * (1 + self.fio_pass_threshold))))
                        if field == "latency":
                            ifop = "greater"
                            elseop = "lesser"
                        else:
                            ifop = "lesser"
                            elseop = "greater"
                        # if actual < (value * (1 - self.fio_pass_threshold)) and ((value - actual) > 2):
                        if compare(actual, value, self.fio_pass_threshold, ifop):
                            fio_result[combo][mode] = False
                            fun_test.add_checkpoint("{} {} check for {} test for the block size & IO depth combo {}"
                                                    .format(op, field, mode, combo), "FAILED", value, actual)
                            fun_test.critical("{} {} {} is not within the allowed threshold value {}".
                                              format(op, field, actual, row_data_dict[op + field][1:]))
                        # elif actual > (value * (1 + self.fio_pass_threshold)) and ((actual - value) > 2):
                        elif compare(actual, value, self.fio_pass_threshold, elseop):
                            fun_test.add_checkpoint("{} {} check for {} test for the block size & IO depth combo {}"
                                                    .format(op, field, mode, combo), "PASSED", value, actual)
                            fun_test.log("{} {} {} got {} than the expected range {}".
                                         format(op, field, actual, elseop, row_data_dict[op + field][1:]))
                        else:
                            fun_test.add_checkpoint("{} {} check for {} test for the block size & IO depth combo {}"
                                                    .format(op, field, mode, combo), "PASSED", value, actual)
                            fun_test.log("{} {} {} is within the expected range {}".
                                         format(op, field, actual, row_data_dict[op + field][1:]))

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
                                # row_data_dict[ekey] = actual
                                if actual != evalue:
                                    if (actual < evalue) and ((evalue - actual) <= self.volume_pass_threshold):
                                        fun_test.add_checkpoint("{} check for {} {} volume for {} test for the "
                                                                "block size & IO depth combo {}".
                                                                format(ekey, type, index, mode, combo), "PASSED",
                                                                evalue, actual)
                                        fun_test.critical("Final {} value {} of {} {} volume is within the expected "
                                                          "range {}".format(ekey, actual, type, index, evalue))
                                    elif (actual > evalue) and ((actual - evalue) <= self.volume_pass_threshold):
                                        fun_test.add_checkpoint("{} check for {} {} volume for {} test for the "
                                                                "block size & IO depth combo {}".
                                                                format(ekey, type, index, mode, combo), "PASSED",
                                                                evalue, actual)
                                        fun_test.critical("Final {} value {} of {} {} volume is within the expected "
                                                          "range {}".format(ekey, actual, type, index, evalue))
                                    else:
                                        internal_result[combo][mode] = False
                                        fun_test.add_checkpoint("{} check for {} {} volume for {} test for the "
                                                                "block size & IO depth combo {}".
                                                                format(ekey, type, index, mode, combo), "FAILED",
                                                                evalue, actual)
                                        fun_test.critical("Final {} value {} of {} {} volume is not equal to the "
                                                          "expected value {}".format(ekey, actual, type, index, evalue))
                                else:
                                    fun_test.add_checkpoint("{} check for {} {} volume for {} test for the block "
                                                            "size & IO depth combo {}".
                                                            format(ekey, type, index, mode, combo), "PASSED",
                                                            evalue, actual)
                                    fun_test.log("Final {} value {} of {} {} volume is equal to the expected value {}".
                                                 format(ekey, actual, type, index, evalue))
                            else:
                                internal_result[combo][mode] = False
                                fun_test.critical("{} is not found in {} {} volume status".format(ekey, type, index))

                # Comparing the internal stats with the expected value
                for key, value in expected_stats[mode].items():
                    for ekey, evalue in expected_stats[mode][key].items():
                        if ekey in diff_stats[combo][mode][key]:
                            actual = diff_stats[combo][mode][key][ekey]
                            evalue_list = evalue.strip("()").split(",")
                            expected = int(evalue_list[0])
                            threshold = int(evalue_list[1])
                            if actual != expected:
                                if actual < expected:
                                    fun_test.add_checkpoint(
                                        "{} check of {} stats for the {} test for the block size & IO depth combo "
                                        "{}".format(ekey, key, mode, combo), "PASSED", expected, actual)
                                    fun_test.log("Final {} value {} of {} stats is less than the expected range "
                                                 "{}".format(ekey, key, actual, expected))
                                elif (actual > expected) and ((actual - expected) <= threshold):
                                    fun_test.add_checkpoint(
                                        "{} check of {} stats for the {} test for the block size & IO depth combo "
                                        "{}".format(ekey, key, mode, combo), "PASSED", expected, actual)
                                    fun_test.log("Final {} value {} of {} stats is within the expected range {}".
                                                 format(ekey, key, actual, expected))
                                else:
                                    internal_result[combo][mode] = False
                                    fun_test.add_checkpoint(
                                        "{} check of {} stats for the {} test for the block size & IO depth combo "
                                        "{}".format(ekey, key, mode, combo), "FAILED", expected, actual)
                                    fun_test.critical("Final {} value of {} stats {} is not equal to the expected value"
                                                      " {}".format(ekey, key, actual, expected))
                            else:
                                fun_test.add_checkpoint(
                                    "{} check of {} stats for the {} test for the block size & IO depth combo "
                                    "{}".format(ekey, key, mode, combo), "PASSED", expected, actual)
                                fun_test.log("Final {} value of {} stats is equal to the expected value {}".
                                             format(ekey, key, actual, expected))
                        else:
                            internal_result[combo][mode] = False
                            fun_test.critical("{} is not found in {} stat".format(ekey, key))

                # Building the table raw for this variation
                row_data_list = []
                for i in table_data_cols:
                    if i not in row_data_dict:
                        row_data_list.append(0)
                    else:
                        row_data_list.append(row_data_dict[i])
                table_data_rows.append(row_data_list)
                post_results("EC with volume level failure domain", test_method, *row_data_list)

        table_data = {"headers": table_data_headers, "rows": table_data_rows}
        fun_test.add_table(panel_header="Performance Table", table_name=self.summary, table_data=table_data)

        # Posting the final status of the test result
        fun_test.log(fio_result)
        fun_test.log(internal_result)
        test_result = True
        for combo in self.fio_bs_iodepth:
            for mode in self.fio_modes:
                if not fio_result[combo][mode] or not internal_result[combo][mode]:
                    test_result = False

        fun_test.test_assert(test_result, self.summary)

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
        self.set_test_details(id=2,
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
        self.set_test_details(id=3,
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
        self.set_test_details(id=4,
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
        self.set_test_details(id=5,
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
