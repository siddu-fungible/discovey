from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut, DutInterface
from lib.host.traffic_generator import TrafficGenerator
from lib.host.storage_controller import StorageController
from web.fun_test.analytics_models_helper import VolumePerformanceHelper
from lib.fun.f1 import F1
import uuid

'''
Script to track the performance of various read write combination of local thin block volume using FIO
'''
# As of now the dictionary variable containing the setup/testbed info used in this script
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


class BLTVolumePerformanceScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Start POSIM and create a Linux instance
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


class BLTVolumePerformanceTestcase(FunTestCase):
    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__

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

        # Setting the list of block size and IO depth combo
        if 'fio_bs_iodepth' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['fio_bs_iodepth']:
            benchmark_parsing = False
            fun_test.critical("Block size and IO depth combo to be used for this {} testcase is not available in "
                              "the {} file".format(testcase, benchmark_file))

        # Setting expected FIO results
        if 'expected_fio_result' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['expected_fio_result']:
            benchmark_parsing = False
            fun_test.critical("Benchmarking results for the block size and IO depth combo needed for this {} "
                              "testcase is not available in the {} file".format(testcase, benchmark_file))

        if "fio_sizes" in benchmark_dict[testcase]:
            if len(self.fio_sizes) != len(self.expected_fio_result.keys()):
                benchmark_parsing = False
                fun_test.critical("Mismatch in FIO sizes and its benchmarking results")
        elif "fio_bs_iodepth" in benchmark_dict[testcase]:
            if len(self.fio_bs_iodepth) != len(self.expected_fio_result.keys()):
                benchmark_parsing = False
                fun_test.critical("Mismatch in block size and IO depth combo and its benchmarking results")

        # Setting the expected volume level internal stats at the end of every FIO run
        if ('expected_volume_stats' not in benchmark_dict[testcase] or
                not benchmark_dict[testcase]['expected_volume_stats']):
            benchmark_parsing = False
            fun_test.critical("Expected internal volume stats needed for this {} testcase is not available in "
                              "the {} file".format(testcase, benchmark_file))

        if 'fio_pass_threshold' not in benchmark_dict[testcase]:
            self.fio_pass_threshold = .05
            fun_test.log("Setting passing threshold to {} for this {} testcase, because its not set in the {} file".
                         format(self.fio_pass_threshold, testcase, benchmark_file))

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))
        fun_test.log("Block size and IO depth combo going to be used for this {} testcase: {}".
                     format(testcase, self.fio_bs_iodepth))
        fun_test.log("Benchmarking results going to be used for this {} testcase: \n{}".
                     format(testcase, self.expected_fio_result))
        fun_test.log("Expected internal volume stats for this {} testcase: \n{}".
                     format(testcase, self.expected_volume_stats))
        # End of benchmarking json file parsing

        self.topology = fun_test.shared_variables["topology"]
        self.dut_instance = self.topology.get_dut_instance(index=0)
        fun_test.test_assert(self.dut_instance, "Retrieved dut instance 0")

        self.linux_host = self.topology.get_tg_instance(tg_index=0)
        destination_ip = self.dut_instance.data_plane_ip

        self.storage_controller = StorageController(target_ip=self.dut_instance.host_ip,
                                                    target_port=self.dut_instance.external_dpcsh_port)

        if "blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]:
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False

            # Configuring Local thin block volume
            command_result = {}
            command_result = self.storage_controller.command(command="enable_counters", legacy=True)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Enabling counters on DUT Instance 0")

            command_result = {}
            command_result = self.storage_controller.ip_cfg(ip=self.dut_instance.data_plane_ip,
                                                            command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "ip_cfg {} on Dut Instance 0".
                                 format(self.dut_instance.data_plane_ip))

            command_result = {}
            self.thin_uuid = str(uuid.uuid4()).replace("-", "")[:10]
            command_result = self.storage_controller.create_thin_block_volume(
                capacity=self.volume_details["capacity"], block_size=self.volume_details["block_size"],
                name=self.volume_details["name"], uuid=self.thin_uuid, command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Create BLT volume on Dut Instance 0")

            command_result = {}
            command_result = self.storage_controller.volume_attach_remote(
                ns_id=self.volume_details["ns_id"], uuid=self.thin_uuid, remote_ip=self.linux_host.internal_ip,
                command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Attaching BLT volume on Dut Instance 0")

            fun_test.shared_variables["blt"]["setup_created"] = True
            # fun_test.shared_variables["blt"]["storage_controller"] = self.storage_controller
            fun_test.shared_variables["blt"]["thin_uuid"] = self.thin_uuid

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
        test_method = testcase[3:]

        destination_ip = self.dut_instance.data_plane_ip

        # self.storage_controller = fun_test.shared_variables["blt"]["storage_controller"]
        self.thin_uuid = fun_test.shared_variables["blt"]["thin_uuid"]
        storage_props_tree = "{}/{}/{}/{}".format("storage", "volumes", self.volume_details["type"], self.thin_uuid)

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

                fun_test.log("Running FIO {} only test with the block size and IO depth set to {} & {}".
                             format(mode, fio_block_size, fio_iodepth))

                # Pulling the initial volume stats in dictionary format
                command_result = {}
                initial_volume_status[combo][mode] = {}
                command_result = self.storage_controller.peek(storage_props_tree)
                fun_test.simple_assert(command_result["status"], "Initial volume stats of DUT Instance 0")
                initial_volume_status[combo][mode] = command_result["data"]
                fun_test.log("Volume Status at the beginning of the test:")
                fun_test.log(initial_volume_status[combo][mode])

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
                fio_output[combo][mode] = {}
                fio_output[combo][mode] = self.linux_host.remote_fio(destination_ip=destination_ip, rw=mode,
                                                                     bs=fio_block_size, iodepth=fio_iodepth,
                                                                     **self.fio_cmd_args)
                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output[combo][mode])
                # fun_test.simple_assert(fio_output[combo][mode], "Execution of FIO command")
                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)

                # Getting the volume stats after the FIO test
                command_result = {}
                final_volume_status[combo][mode] = {}
                command_result = self.storage_controller.peek(storage_props_tree)
                fun_test.simple_assert(command_result["status"], "Final volume stats of DUT Instance {}".format(0))
                final_volume_status[combo][mode] = command_result["data"]
                fun_test.log("Volume Status at the end of the test:")
                fun_test.log(final_volume_status[combo][mode])

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
                for fkey, fvalue in final_volume_status[combo][mode].items():
                    # Not going to calculate the difference for the value stats which are not in the expected volume
                    # dictionary and also for the fault_injection attribute
                    if fkey not in expected_volume_stats[mode] or fkey == "fault_injection":
                        diff_volume_stats[combo][mode][fkey] = fvalue
                        continue
                    if fkey in initial_volume_status[combo][mode]:
                        ivalue = initial_volume_status[combo][mode][fkey]
                        diff_volume_stats[combo][mode][fkey] = fvalue - ivalue
                fun_test.log("Difference of volume status before and after the test:")
                fun_test.log(diff_volume_stats[combo][mode])

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
                            fun_test.log("{} {} {} got {} than the expected value {}".
                                         format(op, field, actual, elseop, row_data_dict[op + field][1:]))
                        else:
                            fun_test.add_checkpoint("{} {} check {} test for the block size & IO depth combo {}"
                                                    .format(op, field, mode, combo), "PASSED", value, actual)
                            fun_test.log("{} {} {} is within the expected range {}".
                                         format(op, field, actual, row_data_dict[op + field][1:]))

                # Comparing the internal volume stats with the expected value
                for ekey, evalue in expected_volume_stats[mode].items():
                    if ekey in diff_volume_stats[combo][mode]:
                        actual = diff_volume_stats[combo][mode][ekey]
                        # row_data_dict[ekey] = actual
                        if actual != evalue:
                            if (actual < evalue) and ((evalue - actual) <= self.volume_pass_threshold):
                                fun_test.add_checkpoint("{} check for the {} test for the block size & IO depth combo "
                                                        "{}".format(ekey, mode, combo), "PASSED", evalue, actual)
                                fun_test.critical("Final {} value {} is within the expected range {}".
                                                  format(ekey, actual, evalue))
                            elif (actual > evalue) and ((actual - evalue) <= self.volume_pass_threshold):
                                fun_test.add_checkpoint("{} check for the {} test for the block size & IO depth combo "
                                                        "{}".format(ekey, mode, combo), "PASSED", evalue,
                                                        actual)
                                fun_test.critical("Final {} value {} is within the expected range {}".
                                                  format(ekey, actual, evalue))
                            else:
                                internal_result[combo][mode] = False
                                fun_test.add_checkpoint("{} check for the {} test for the block size & IO depth combo "
                                                        "{}".format(ekey, mode, combo), "FAILED", evalue, actual)
                                fun_test.critical("Final {} value {} is not equal to the expected value {}".
                                                  format(ekey, actual, evalue))
                        else:
                            fun_test.add_checkpoint("{} check for the {} test for the block size & IO depth combo "
                                                    "{}".format(ekey, mode, combo), "PASSED", evalue, actual)
                            fun_test.log("Final {} value {} is equal to the expected value {}".
                                         format(ekey, actual, evalue))
                    else:
                        internal_result[combo][mode] = False
                        fun_test.critical("{} is not found in volume status".format(ekey))

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

                # Building the table row for this variation for both the script table and performance dashboard
                row_data_list = []
                for i in table_data_cols:
                    if i not in row_data_dict:
                        row_data_list.append(0)
                    else:
                        row_data_list.append(row_data_dict[i])

                table_data_rows.append(row_data_list)
                post_results("BLT", test_method, *row_data_list)

        table_data = {"headers": table_data_headers, "rows": table_data_rows}
        fun_test.add_table(panel_header="Performance Table", table_name=self.summary, table_data=table_data)

        # Posting the final status of the test result
        test_result = True
        fun_test.log(fio_result)
        fun_test.log(internal_result)
        for combo in self.fio_bs_iodepth:
            for mode in self.fio_modes:
                if not fio_result[combo][mode] or not internal_result[combo][mode]:
                    test_result = False

        fun_test.test_assert(test_result, self.summary)

    def cleanup(self):

        self.storage_controller.disconnect()
        # pass


class BLTFioSeqWriteSeqReadOnly(BLTVolumePerformanceTestcase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Sequential Write & Read only performance of Thin Provisioned local block volume "
                                      "over RDS",
                              steps='''
        1. Create a local thin block volume in dut instances 0.
        2. Export (Attach) this local thin volume to the external Linux instance/container. 
        3. Run the FIO sequential write and read only test(without verify) for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold. 
        ''')

    def setup(self):
        super(BLTFioSeqWriteSeqReadOnly, self).setup()

    def run(self):
        super(BLTFioSeqWriteSeqReadOnly, self).run()

    def cleanup(self):
        super(BLTFioSeqWriteSeqReadOnly, self).cleanup()


class BLTFioRandWriteRandReadOnly(BLTVolumePerformanceTestcase):
    def describe(self):
        self.set_test_details(id=2,
                              summary='Random Write & Read only performance of Thin Provisioned local block volume over'
                                      ' RDS',
                              steps='''
        1. Create a local thin block volume in dut instances 0.
        2. Export (Attach) this local thin volume to the external Linux instance/container. 
        3. Run the FIO random write and read only test(without verify) for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold. 
        ''')

    def setup(self):
        super(BLTFioRandWriteRandReadOnly, self).setup()

    def run(self):
        super(BLTFioRandWriteRandReadOnly, self).run()

    def cleanup(self):
        super(BLTFioRandWriteRandReadOnly, self).cleanup()


class BLTFioSeqReadWriteMix(BLTVolumePerformanceTestcase):
    def describe(self):
        self.set_test_details(id=3,
                              summary='Sequential 75% Write & 25% Read performance of Thin Provisioned local block '
                                      'volume over RDS',
                              steps='''
        1. Create a local thin block volume in dut instances 0.
        2. Export (Attach) this local thin volume to the external Linux instance/container. 
        3. Run the FIO sequential write and read mix test with 3:1 ratio for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold. 
        ''')

    def setup(self):
        super(BLTFioSeqReadWriteMix, self).setup()

    def run(self):
        super(BLTFioSeqReadWriteMix, self).run()

    def cleanup(self):
        super(BLTFioSeqReadWriteMix, self).cleanup()


class BLTFioRandReadWriteMix(BLTVolumePerformanceTestcase):
    def describe(self):
        self.set_test_details(id=4,
                              summary='Random 75% Write & 25% Read performance of Thin Provisioned local block '
                                      'volume over RDS',
                              steps='''
        1. Create a local thin block volume in dut instances 0.
        2. Export (Attach) this local thin volume to the external Linux instance/container. 
        3. Run the FIO random write and read mix test with 3:1 ratio for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold. 
        ''')

    def setup(self):
        super(BLTFioRandReadWriteMix, self).setup()

    def run(self):
        super(BLTFioRandReadWriteMix, self).run()

    def cleanup(self):
        super(BLTFioRandReadWriteMix, self).cleanup()


class BLTFioLargeWriteReadOnly(BLTVolumePerformanceTestcase):
    def describe(self):
        self.set_test_details(id=5,
                              summary='Write & Read only performance(for both Sequential and random) for large sizes '
                                      'of Thin Provisioned local block volume over RDS',
                              steps='''
        1. Create a local thin block volume in dut instances 0.
        2. Export (Attach) this local thin volume to the external Linux instance/container. 
        3. Run the FIO write and read only test(without verify) for various sizes from the external Linux server and 
        check the performance are inline with the expected threshold. 
        ''')

    def setup(self):
        super(BLTFioLargeWriteReadOnly, self).setup()

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[3:]

        destination_ip = self.dut_instance.data_plane_ip

        self.storage_controller = fun_test.shared_variables["blt"]["storage_controller"]
        self.thin_uuid = fun_test.shared_variables["blt"]["thin_uuid"]
        storage_props_tree = "{}/{}/{}/{}".format("storage", "volumes", self.volume_details["type"], self.thin_uuid)

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

        tmp = self.fio_bs_iodepth.split(',')

        fio_block_size = tmp[0].strip('() ') + 'k'
        self.fio_cmd_args["bs"] = fio_block_size

        fio_iodepth = tmp[1].strip('() ')
        self.fio_cmd_args["iodepth"] = fio_iodepth

        table_data_headers = ["Block Size", "IO Depth", "Size", "Operation", "Write IOPS", "Read IOPS",
                              "Write Throughput in KiB/s", "Read Throughput in KiB/s", "Write Latency in uSecs",
                              "Read Latency in uSecs"]
        table_data_cols = ["block_size", "iodepth", "size", "mode", "writeiops", "readiops", "writebw", "readbw",
                           "writelatency", "readlatency"]
        table_data_rows = []

        for size in self.fio_sizes:

            # The below check needs to be removed once the bugs #324 get resolved
            if size == "512m" or size == "896m":
                continue
            fio_result[size] = {}
            fio_output[size] = {}
            internal_result[size] = {}
            initial_volume_status[size] = {}
            final_volume_status[size] = {}
            diff_volume_stats[size] = {}
            initial_stats[size] = {}
            final_stats[size] = {}
            diff_stats[size] = {}

            for mode in self.fio_modes:

                # The below check needs to be removed once the bugs #299 get resolved
                if (size == "256m") and (mode == "write" or mode == "randwrite"):
                    continue

                fio_result[size][mode] = True
                internal_result[size][mode] = True
                row_data_dict = {}
                row_data_dict["mode"] = mode
                row_data_dict["size"] = size
                row_data_dict["block_size"] = fio_block_size
                row_data_dict["iodepth"] = fio_iodepth

                # Pulling in the initial volume stats in dictionary format
                command_result = {}
                initial_volume_status[size][mode] = {}
                command_result = self.storage_controller.peek(storage_props_tree)
                fun_test.simple_assert(command_result["status"], "Initial volume stats of DUT Instance {}".format(0))
                initial_volume_status[size][mode] = command_result["data"]
                fun_test.log("Volume Status at the beginning of the test:")
                fun_test.log(initial_volume_status[size][mode])

                # Pulling the initial stats in dictionary format
                initial_stats[size][mode] = {}
                for key, value in self.stats_list.items():
                    if key not in initial_stats[size][mode]:
                        initial_stats[size][mode][key] = {}
                    if value:
                        for item in value:
                            props_tree = "{}/{}/{}".format("stats", key, item)
                            command_result = self.storage_controller.peek(props_tree)
                            fun_test.simple_assert(command_result["status"], "Initial {} stats of DUT Instance 0".
                                                   format(props_tree))
                            initial_stats[size][mode][key][item] = command_result["data"]
                    else:
                        props_tree = "{}/{}".format("stats", key)
                        command_result = self.storage_controller.peek(props_tree)
                        fun_test.simple_assert(command_result["status"], "Initial {} stats of DUT Instance 0".
                                               format(props_tree))
                        initial_stats[size][mode][key] = command_result["data"]
                    fun_test.log("{} stats at the beginning of the test:".format(key))
                    fun_test.log(initial_stats[size][mode][key])

                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fun_test.log("Running FIO {} only test for the size {} with the block size & IO depth set to {} & {}"
                             .format(mode, size, fio_block_size, fio_iodepth))
                fio_output[size][mode] = {}
                fio_output[size][mode] = self.linux_host.remote_fio(destination_ip=destination_ip, rw=mode, size=size,
                                                                    **self.fio_cmd_args)
                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output[size][mode])
                # fun_test.simple_assert(fio_output[combo][mode], "Execution of FIO command")
                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)

                # Getting the volume stats after the FIO test
                command_result = {}
                final_volume_status[size][mode] = {}
                command_result = self.storage_controller.peek(storage_props_tree)
                fun_test.simple_assert(command_result["status"], "Final volume stats of DUT Instance {}".format(0))
                final_volume_status[size][mode] = command_result["data"]
                fun_test.log("Volume Status at the end of the test:")
                fun_test.log(final_volume_status[size][mode])

                # Pulling the final stats in dictionary format
                final_stats[size][mode] = {}
                for key, value in self.stats_list.items():
                    if key not in final_stats[size][mode]:
                        final_stats[size][mode][key] = {}
                    if value:
                        for item in value:
                            props_tree = "{}/{}/{}".format("stats", key, item)
                            command_result = self.storage_controller.peek(props_tree)
                            fun_test.simple_assert(command_result["status"], "Initial {} stats of DUT Instance 0".
                                                   format(props_tree))
                            final_stats[size][mode][key][item] = command_result["data"]
                    else:
                        props_tree = "{}/{}".format("stats", key)
                        command_result = self.storage_controller.peek(props_tree)
                        fun_test.simple_assert(command_result["status"], "Initial {} stats of DUT Instance 0".
                                               format(props_tree))
                        final_stats[size][mode][key] = command_result["data"]
                    fun_test.log("{} stats at the end of the test:".format(key))
                    fun_test.log(final_stats[size][mode][key])

                # Finding the difference between the internal volume stats before and after the test
                diff_volume_stats[size][mode] = {}
                for fkey, fvalue in final_volume_status[size][mode].items():
                    # Not going to calculate the difference for the value stats which are not in the expected volume
                    # dictionary and also for the fault_injection attribute
                    if fkey not in self.expected_volume_stats[size][mode] or fkey == "fault_injection":
                        diff_volume_stats[size][mode][fkey] = fvalue
                        continue
                    if fkey in initial_volume_status[size][mode]:
                        ivalue = initial_volume_status[size][mode][fkey]
                        diff_volume_stats[size][mode][fkey] = fvalue - ivalue
                fun_test.log("Difference of volume status before and after the test:")
                fun_test.log(diff_volume_stats[size][mode])

                # Finding the difference between the stats before and after the test
                diff_stats[size][mode] = {}
                for key, value in self.stats_list.items():
                    diff_stats[size][mode][key] = {}
                    for fkey, fvalue in final_stats[size][mode][key].items():
                        ivalue = initial_stats[size][mode][key][fkey]
                        diff_stats[size][mode][key][fkey] = fvalue - ivalue
                    fun_test.log("Difference of {} stats before and after the test:".format(key))
                    fun_test.log(diff_stats[size][mode][key])

                if not fio_output[size][mode]:
                    fio_result[size][mode] = False
                    fun_test.critical("No output from FIO test, hence moving to the next variation")
                    continue

                # Comparing the FIO results with the expected value for the current block size and IO depth combo
                for op, stats in self.expected_fio_result[size][mode].items():
                    for field, value in stats.items():
                        actual = fio_output[size][mode][op][field]
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
                            fio_result[size][mode] = False
                            fun_test.add_checkpoint("{} check for {} {} test for the block size & IO depth set to {} "
                                                    "& {}".format(field, size, mode, fio_block_size, fio_iodepth),
                                                    "FAILED", value, actual)
                            fun_test.critical("{} {} {} is not within the allowed threshold value {}".
                                              format(op, field, actual, row_data_dict[op + field][1:]))
                        # elif actual > (value * (1 + self.fio_pass_threshold)) and ((actual - value) > 2):
                        elif compare(actual, value, self.fio_pass_threshold, elseop):
                            fun_test.add_checkpoint("{} check for {} {} test for the block size & IO depth set to {} "
                                                    "& {}".format(field, size, mode, fio_block_size, fio_iodepth),
                                                    "PASSED", value, actual)
                            fun_test.log("{} {} {} got {} than the expected value {}".
                                         format(op, field, actual, elseop, row_data_dict[op + field][1:]))
                        else:
                            fun_test.add_checkpoint("{} check for {} {} test for the block size & IO depth set to {} "
                                                    "& {}".format(field, size, mode, fio_block_size, fio_iodepth),
                                                    "PASSED", value, actual)
                            fun_test.log("{} {} {} is within the expected range {}".
                                         format(op, field, actual, row_data_dict[op + field][1:]))

                # Comparing the internal volume stats with the expected value
                for ekey, evalue in self.expected_volume_stats[size][mode].items():
                    if ekey in diff_volume_stats[size][mode]:
                        actual = diff_volume_stats[size][mode][ekey]
                        # row_data_dict[ekey] = actual
                        if actual != evalue:
                            if (actual < evalue) and ((evalue - actual) <= self.volume_pass_threshold):
                                fun_test.add_checkpoint("{} check for {} {} test for the block size & IO depth combo "
                                                        "{} & {}".format(ekey, size, mode, fio_block_size, fio_iodepth),
                                                        "PASSED", evalue, actual)
                                fun_test.critical("Final {} value {} is within the expected range {}".
                                                  format(ekey, actual, evalue))
                            elif (actual > evalue) and ((actual - evalue) <= self.volume_pass_threshold):
                                fun_test.add_checkpoint("{} check for {} {} test for the block size & IO depth combo "
                                                        "{} & {}".format(ekey, size, mode, fio_block_size, fio_iodepth),
                                                        "PASSED", evalue, actual)
                                fun_test.critical("Final {} value {} is within the expected range {}".
                                                  format(ekey, actual, evalue))
                            internal_result[size][mode] = False
                            fun_test.add_checkpoint("{} check for {} {} test for the block size & IO depth combo "
                                                    "{} & {}".format(ekey, size, mode, fio_block_size, fio_iodepth),
                                                    "FAILED", evalue, actual)
                            fun_test.critical("Final {} value {} is not equal to the expected value {}".
                                              format(ekey, actual, evalue))
                        else:
                            fun_test.add_checkpoint("{} check for {} {} test for the block size & IO depth combo "
                                                    "{} & {}".format(ekey, size, mode, fio_block_size, fio_iodepth),
                                                    "PASSED", evalue, actual)
                            fun_test.log("Final {} value {} is equal to the expected value {}".
                                         format(ekey, actual, evalue))
                    else:
                        internal_result[size][mode] = False
                        fun_test.critical("{} is not found in volume status".format(ekey))

                # Comparing the internal stats with the expected value
                for key, value in self.expected_stats[size].items():
                    for ekey, evalue in self.expected_stats[size][key].items():
                        if ekey in diff_stats[size][mode][key]:
                            actual = diff_stats[size][mode][key][ekey]
                            evalue_list = evalue.strip("()").split(",")
                            expected = int(evalue_list[0])
                            threshold = int(evalue_list[1])
                            if actual != expected:
                                if actual < expected:
                                    fun_test.add_checkpoint(
                                        "{} check of {} stats for {} {} test for the block size & IO depth combo "
                                        "{} & {}".format(ekey, key, size, mode, fio_block_size, fio_iodepth), "PASSED",
                                        expected, actual)
                                    fun_test.log("Final {} value {} of {} stats is less than the expected range "
                                                 "{}".format(ekey, key, actual, expected))
                                elif (actual > expected) and ((actual - expected) <= threshold):
                                    fun_test.add_checkpoint(
                                        "{} check of {} stats for the {} test for the block size & IO depth combo "
                                        "{} & {}".format(ekey, key, size, mode, fio_block_size, fio_iodepth), "PASSED",
                                        expected, actual)
                                    fun_test.log("Final {} value {} of {} stats is within the expected range {}".
                                                 format(ekey, key, actual, expected))
                                else:
                                    internal_result[size][mode] = False
                                    fun_test.add_checkpoint(
                                        "{} check of {} stats for the {} test for the block size & IO depth combo "
                                        "{} & {}".format(ekey, key, size, mode, fio_block_size, fio_iodepth), "FAILED",
                                        expected, actual)
                                    fun_test.critical("Final {} value of {} stats {} is not equal to the expected value"
                                                      " {}".format(ekey, key, actual, expected))
                            else:
                                fun_test.add_checkpoint(
                                    "{} check of {} stats for the {} test for the block size & IO depth combo "
                                    "{} & {}".format(ekey, key, size, mode, fio_block_size, fio_iodepth), "PASSED",
                                    expected, actual)
                                fun_test.log("Final {} value of {} stats is equal to the expected value {}".
                                             format(ekey, key, actual, expected))
                        else:
                            internal_result[size][mode] = False
                            fun_test.critical("{} is not found in {} stat".format(ekey, key))

                # Building the table raw for this variation
                row_data_list = []
                for i in table_data_cols:
                    if i not in row_data_dict:
                        row_data_list.append(0)
                    else:
                        row_data_list.append(row_data_dict[i])
                table_data_rows.append(row_data_list)
                post_results("BLT", test_method, *row_data_list)

        table_data = {"headers": table_data_headers, "rows": table_data_rows}
        fun_test.add_table(panel_header="Performance Table", table_name=self.summary, table_data=table_data)

        # Posting the final status of the test result
        fun_test.log(fio_result)
        fun_test.log(internal_result)
        test_result = True
        for size in self.fio_sizes:
            # The below check needs to be removed once the bugs #324 get resolved
            if size == "512m" or size == "896m":
                continue
            for mode in self.fio_modes:
                # The below check needs to be removed once the bugs #299 get resolved
                if (size == "256m") and (mode == "write" or mode == "randwrite"):
                    continue
                if not fio_result[size][mode] or not internal_result[size][mode]:
                    test_result = False

        fun_test.test_assert(test_result, self.summary)

    def cleanup(self):
        super(BLTFioLargeWriteReadOnly, self).cleanup()


if __name__ == "__main__":

    bltscript = BLTVolumePerformanceScript()
    bltscript.add_test_case(BLTFioSeqWriteSeqReadOnly())
    bltscript.add_test_case(BLTFioRandWriteRandReadOnly())
    bltscript.add_test_case(BLTFioSeqReadWriteMix())
    bltscript.add_test_case(BLTFioRandReadWriteMix())
    bltscript.add_test_case(BLTFioLargeWriteReadOnly())
    bltscript.run()
