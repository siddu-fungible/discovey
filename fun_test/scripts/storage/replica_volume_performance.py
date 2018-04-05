from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut, DutInterface
from lib.fun.f1 import F1
from lib.host.storage_controller import StorageController
from lib.host.traffic_generator import TrafficGenerator
import uuid

'''
Script to track the performance of various read write combination of replica volume using FIO
'''


def post_results(volume, test, block_size, io_depth, size, operation, write_iops, read_iops, write_bw, read_bw,
                 write_latency, read_latency):
    result = []
    arg_list = post_results.func_code.co_varnames[:-3]
    for arg in arg_list:
        result.append(str(eval(arg)))
    result = ",".join(result)
    fun_test.log("Result: {}".format(result))


def compare(actual, expected, threshold, operation):
    if operation == "lesser":
        return (actual < (expected * (1 - threshold)) and ((expected - actual) > 2))
    else:
        return (actual > (expected * (1 + threshold)) and ((actual - expected) > 2))


class ReplicaDPULevelScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Start num_replica number of posix and allocate a Linux instance. 
        2. Make the Linux instance available for the testcase.
        """)

    def setup(self):

        # Initializing the global config
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Benchmark file being used: {}".format(benchmark_file))

        benchmark_dict = utils.parse_file_to_json(benchmark_file)

        if "GlobalSetup" not in benchmark_dict or not benchmark_dict["GlobalSetup"]:
            fun_test.critical("Global setup config is not available in the {} config file".format(benchmark_file))
            fun_test.log("Going to use the script level defaults")
            self.num_replica = 2
            self.min_replicas_insync = 1
        else:
            for k, v in benchmark_dict["GlobalSetup"].items():
                setattr(self, k, v)

        if 'num_replica' not in benchmark_dict['GlobalSetup']:
            fun_test.critical("Number of BLT needed to build the replica is not available in the {} config file".
                              format(benchmark_file))
            fun_test.log("Going to use the script level defaults")
            self.num_replica = 2
            self.min_replicas_insync = 1

        # Computing number DPUs needed and constructing the dut_info attribute of the topology_dict accordingly
        if hasattr(self, "replica_in_sep_dpu") and self.replica_in_sep_dpu:
            self.num_dpu = self.num_replica + 1
        else:
            self.replica_in_sep_dpu = 0
            self.num_dpu = self.num_replica

        dut_info = {
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

        topology_dict = {
            "name": "Basic Storage",
            "dut_info": {},
            "tg_info": {
                0: {
                    "type": TrafficGenerator.TRAFFIC_GENERATOR_TYPE_LINUX_HOST
                }
            }
        }

        for index in range(self.num_dpu):
            topology_dict["dut_info"][index] = dut_info

        topology_obj_helper = TopologyHelper(spec=topology_dict)
        topology = topology_obj_helper.deploy()
        fun_test.test_assert(topology, "Ensure deploy is successful")
        fun_test.shared_variables["topology"] = topology

        self.duts = {}
        self.duts["blt"] = []
        self.duts["replica"] = []

        for index in range(self.num_replica):
            self.duts["blt"].append(topology.get_dut_instance(index=index))

        self.duts["replica"] = topology.get_dut_instance(index=self.num_dpu - 1)

        global_setup = self.__dict__

        fun_test.shared_variables["topology"] = topology
        fun_test.shared_variables["global_setup"] = global_setup

    def cleanup(self):
        TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()
        # pass


class ReplicaDPULevelTestcase(FunTestCase):

    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__

        # Importing global setup
        self.topology = fun_test.shared_variables["topology"]
        self.global_setup = fun_test.shared_variables["global_setup"]
        self.linux_host = self.topology.get_tg_instance(tg_index=0)
        destination_ip = self.global_setup["duts"]["replica"].data_plane_ip

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

        for k, v in benchmark_dict[testcase].items():
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

        if "fio_sizes" in benchmark_dict[testcase]:
            if len(self.fio_sizes) != len(self.expected_fio_result.keys()):
                benchmark_parsing = False
                fun_test.critical("Mismatch in FIO sizes and its benchmarking results")
        elif "fio_bs_iodepth" in benchmark_dict[testcase]:
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
            self.volume_pass_threshold = 0
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

        stat_uuids = []
        thin_uuids = []
        rds_uuids = []
        volume_details = []

        if "replica" not in fun_test.shared_variables or not fun_test.shared_variables["replica"]["setup_created"]:
            fun_test.shared_variables["replica"] = {}
            fun_test.shared_variables["replica"]["setup_created"] = False
            self.uuids = {}
            self.uuids["blt"] = []
            self.uuids["rds"] = []
            self.uuids["replica"] = []

            # Configuring ndata and nparity number of BLT volumes in their appropriate DPU
            self.storage_controller = {}
            self.storage_controller["blt"] = []
            replica_dut = self.global_setup["duts"]["replica"]
            self.storage_controller["replica"] = [StorageController(target_ip=replica_dut.host_ip,
                                                                    target_port=replica_dut.external_dpcsh_port)]

            for i in range(self.global_setup["num_replica"]):
                # Configuring the controller
                dut = self.global_setup["duts"]["blt"][i]
                self.storage_controller["blt"].append(StorageController(target_ip=dut.host_ip,
                                                                        target_port=dut.external_dpcsh_port))
                command_result = self.storage_controller["blt"][i].command(command="enable_counters", legacy=True)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Enabling counters on BLT {} DUT instance".format(i))

                command_result = self.storage_controller["blt"][i].ip_cfg(
                    ip=dut.data_plane_ip, command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "ip_cfg {} on BLT {} DUT instance".
                                     format(dut.data_plane_ip, i))

                # Configuring the BLT volume
                this_uuid = str(uuid.uuid4()).replace("-", "")[:10]
                self.uuids["blt"].append(this_uuid)
                command_result = self.storage_controller["blt"][i].create_volume(
                    type=self.volume_types["blt"], capacity=self.volume_capacity["blt"],
                    block_size=self.volume_block["blt"], name="blt" + "-" + str(i), uuid=this_uuid,
                    command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Create BLT volume on {} DUT instance".format(i))

                # Attaching the BLT to the DPU in the which the Replica volume going to be configured
                command_result = self.storage_controller["blt"][i].volume_attach_remote(
                    ns_id=self.ns_id["blt"], uuid=this_uuid, remote_ip=replica_dut.data_plane_ip,
                    command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Attaching BLT volume of {} DUT instance to the last "
                                                               "DUT instance".format(i))

            # Configuring RDS & Replica volume in the last DUT defined in the topology dict
            # Configuring the controller in the DUT in case if the Replica volume needs to configured in a separate DPU
            if self.global_setup["replica_in_sep_dpu"]:
                # Configuring the controller
                command_result = self.storage_controller["replica"][0].command(command="enable_counters", legacy=True)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Enabling counters in the Replica DUT instance")

                command_result = self.storage_controller["replica"][0].ip_cfg(
                    ip=replica_dut.data_plane_ip, command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "ip_cfg {} on last DUT instance".
                                     format(replica_dut.data_plane_ip))

            # Configuring the required number of RDS based on whether the replica volume needs to configured in a
            # separate DPU. If the replica dpu DUT instance is equal to the last blt instance, then don't configure
            # the RDS in that DUT instance, because the replica volume need not to be in a separate volume

            for i in range(self.global_setup["num_replica"]):
                dut = self.global_setup["duts"]["blt"][i]
                if replica_dut != dut:
                    this_uuid = str(uuid.uuid4()).replace("-", "")[:10]
                    self.uuids["rds"].append(this_uuid)
                    command_result = self.storage_controller["replica"][0].create_volume(
                        type=self.volume_types["rds"], capacity=self.volume_capacity["rds"],
                        block_size=self.volume_block["rds"], name="blt" + str(i) + "-rds", uuid=this_uuid,
                        remote_nsid=self.ns_id["blt"], remote_ip=dut.data_plane_ip,
                        command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Create RDS volume for BLT {} DUT instance".
                                         format(i))

            if len(self.uuids["rds"]) == len(self.uuids["blt"]):
                replica_pvol_id = self.uuids["rds"]
            else:
                replica_pvol_id = self.uuids["rds"] + list(self.uuids["blt"][-1])

            # Configuring Replica volume on top of RDS volumes
            this_uuid = str(uuid.uuid4()).replace("-", "")[:10]
            self.uuids["replica"].append(this_uuid)
            command_result = self.storage_controller["replica"][0].create_volume(
                type=self.volume_types["replica"], capacity=self.volume_capacity["replica"],
                block_size=self.volume_block["replica"], name="replica-1", uuid=this_uuid, pvol_id=replica_pvol_id,
                pvol_type=self.volume_types["rds"], min_replicas_insync=self.global_setup["min_replicas_insync"],
                command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Create Replica volume on last DUT instance")
            attach_uuid = this_uuid
            ns_id = self.ns_id["replica"]

            # Attaching/Exporting the Replica volume to the external server
            command_result = self.storage_controller["replica"][0].volume_attach_remote(
                ns_id=ns_id, uuid=attach_uuid, remote_ip=self.linux_host.internal_ip,
                command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Attaching Replica volume in the last DUT instance")

            # disabling the error_injection for the replica volume
            command_result = {}
            command_result = self.storage_controller["replica"][0].poke("params/repvol/error_inject 0")
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Disabling error_injection in the last DUT instance")

            # Ensuring that the error_injection got disabled properly
            fun_test.sleep("Sleeping for a second to disable the error_injection", 1)
            command_result = {}
            command_result = self.storage_controller["replica"][0].peek("params/repvol")
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Retrieving error_injection status from the last DUT "
                                                           "instance")
            fun_test.test_assert_expected(actual=int(command_result["data"]["error_inject"]), expected=0,
                                          message="Ensuring error_injection got disabled")

            fun_test.shared_variables["replica"]["uuids"] = self.uuids
            fun_test.shared_variables["replica"]["storage_controller"] = self.storage_controller
            fun_test.shared_variables["replica"]["setup_created"] = True

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
        test_method = testcase

        self.uuids = fun_test.shared_variables["replica"]["uuids"]
        self.storage_controller = fun_test.shared_variables["replica"]["storage_controller"]
        destination_ip = self.global_setup["duts"]["replica"].data_plane_ip

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

        volumes = ["blt", "replica"]

        # Check any plex needs to be induced to fail and if so do the same
        if hasattr(self, "trigger_plex_failure") and self.trigger_plex_failure:
            for index in self.failure_plex_indices:
                command_result = self.storage_controller["blt"][index].fail_volume(
                    uuid=self.uuids["blt"][index], command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Inject failure to the BLT volume having the "
                                                               "UUID {}".format(self.uuids["blt"][index]))
                fun_test.sleep("Sleeping for a second to enable the fault_injection", 1)
                props_tree = "{}/{}/{}/{}".format("storage", "volumes", self.volume_types["blt"],
                                                  self.uuids["blt"][index])
                command_result = self.storage_controller["blt"][index].peek(props_tree)
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

                # Pulling the initial volume stats from all the DUTs in dictionary format
                fun_test.log("Pulling the initial volume stats from all the DUTs in dictionary format before the test")
                initial_volume_status[combo][mode] = {}
                for type in volumes:
                    initial_volume_status[combo][mode][type] = {}
                    for index, uuid in enumerate(self.uuids[type]):
                        initial_volume_status[combo][mode][type][index] = {}
                        storage_props_tree = "{}/{}/{}/{}".format("storage", "volumes", self.volume_types[type], uuid)
                        command_result = self.storage_controller[type][index].peek(storage_props_tree)
                        fun_test.simple_assert(command_result["status"], "Initial volume stats of DUT instance {}".
                                               format(index))
                        initial_volume_status[combo][mode][type][index] = command_result["data"]
                        fun_test.log("{} {} volume Status at the beginning of the test:".format(type, index))
                        fun_test.log(initial_volume_status[combo][mode][type][index])

                # Pulling the initial stats in dictionary format
                initial_stats[combo][mode] = {}
                for type in volumes:
                    initial_stats[combo][mode][type] = {}
                    for index, uuid in enumerate(self.uuids[type]):
                        initial_stats[combo][mode][type][index] = {}
                        for key, value in self.stats_list.items():
                            if key not in initial_stats[combo][mode][type][index]:
                                initial_stats[combo][mode][type][index][key] = {}
                            if value:
                                for item in value:
                                    props_tree = "{}/{}/{}".format("stats", key, item)
                                    command_result = self.storage_controller[type][index].peek(props_tree)
                                    fun_test.simple_assert(
                                        command_result["status"], "Initial {} stats of {} {} DUT "
                                                                  "instance".format(props_tree, type, index))
                                    initial_stats[combo][mode][type][index][key][item] = command_result["data"]
                            else:
                                props_tree = "{}/{}".format("stats", key)
                                command_result = self.storage_controller[type][index].peek(props_tree)
                                fun_test.simple_assert(
                                    command_result["status"], "Initial {} stats of {} {} DUT "
                                                              "instance".format(props_tree, type, index))
                                initial_stats[combo][mode][type][index][key] = command_result["data"]
                            fun_test.log("{} stats of {} {} DUT at the beginning of the test:".format(key, type, index))
                            fun_test.log(initial_stats[combo][mode][type][index][key])

                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fun_test.log("Running FIO {} only test with the block size and IO depth set to {} & {}".
                             format(mode, fio_block_size, fio_iodepth))
                fio_output[combo][mode] = {}
                fio_output[combo][mode] = self.linux_host.remote_fio(
                    destination_ip=destination_ip, rw=mode, bs=fio_block_size, iodepth=fio_iodepth, **self.fio_cmd_args)
                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output[combo][mode])
                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)

                # Pulling volume stats from all the DUTs in dictionary format after the test
                fun_test.log("Pulling the volume stats from all the DUTs after the FIO test")
                final_volume_status[combo][mode] = {}
                for type in volumes:
                    final_volume_status[combo][mode][type] = {}
                    for index, uuid in enumerate(self.uuids[type]):
                        final_volume_status[combo][mode][type][index] = {}
                        storage_props_tree = "{}/{}/{}/{}".format("storage", "volumes", self.volume_types[type], uuid)
                        command_result = self.storage_controller[type][index].peek(storage_props_tree)
                        fun_test.simple_assert(command_result["status"], "Initial {} {} volume stats".
                                               format(type, index))
                        final_volume_status[combo][mode][type][index] = command_result["data"]
                        fun_test.log("{} {} volume Status at the end of the test:".format(type, index))
                        fun_test.log(final_volume_status[combo][mode][type][index])

                # Pulling the final stats in dictionary format
                final_stats[combo][mode] = {}
                for type in volumes:
                    final_stats[combo][mode][type] = {}
                    for index, uuid in enumerate(self.uuids[type]):
                        final_stats[combo][mode][type][index] = {}
                        for key, value in self.stats_list.items():
                            if key not in final_stats[combo][mode][type][index]:
                                final_stats[combo][mode][type][index][key] = {}
                            if value:
                                for item in value:
                                    props_tree = "{}/{}/{}".format("stats", key, item)
                                    command_result = self.storage_controller[type][index].peek(props_tree)
                                    fun_test.simple_assert(
                                        command_result["status"], "Final {} stats of {} {} DUT "
                                                                  "instance".format(props_tree, type, index))
                                    final_stats[combo][mode][type][index][key][item] = command_result["data"]
                            else:
                                props_tree = "{}/{}".format("stats", key)
                                command_result = self.storage_controller[type][index].peek(props_tree)
                                fun_test.simple_assert(command_result["status"], "Final {} stats of {} {} DUT instance".
                                                       format(props_tree, type, index))
                                final_stats[combo][mode][type][index][key] = command_result["data"]
                            fun_test.log("{} stats of {} {} DUT at the end of the test:".format(key, type, index))
                            fun_test.log(final_stats[combo][mode][type][index][key])

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
                        fun_test.log("Difference of {} {} volume status before and after the test:".
                                     format(type, index))
                        fun_test.log(diff_volume_stats[combo][mode][type][index])

                # Finding the difference between the stats before and after the test
                diff_stats[combo][mode] = {}
                for type in volumes:
                    diff_stats[combo][mode][type] = {}
                    for index in range(len(self.uuids[type])):
                        diff_stats[combo][mode][type][index] = {}
                        for key, value in self.stats_list.items():
                            diff_stats[combo][mode][type][index][key] = {}
                            for fkey, fvalue in final_stats[combo][mode][type][index][key].items():
                                ivalue = initial_stats[combo][mode][type][index][key][fkey]
                                diff_stats[combo][mode][type][index][key][fkey] = fvalue - ivalue
                            fun_test.log("Difference of {} stats of {} {} before and after the test:".format(key, type,
                                                                                                             index))
                            fun_test.log(diff_stats[combo][mode][type][index][key])

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
                for type in volumes:
                    for index in range(len(self.uuids[type])):
                        for key, value in expected_stats[mode][type][str(index)].items():
                            for ekey, evalue in expected_stats[mode][type][str(index)][key].items():
                                if ekey in diff_stats[combo][mode][type][index][key]:
                                    actual = diff_stats[combo][mode][type][index][key][ekey]
                                    evalue_list = evalue.strip("()").split(",")
                                    expected = int(evalue_list[0])
                                    threshold = int(evalue_list[1])
                                    if actual != expected:
                                        if actual < expected:
                                            fun_test.add_checkpoint(
                                                "{} check of {} stats for the {} test for the block size & IO depth "
                                                "combo {} in {} {} DUT".format(ekey, key, mode, combo, type, index),
                                                "PASSED", expected, actual)
                                            fun_test.log("Final {} value {} of {} stats is less than the expected "
                                                         "range {} in {} {} DUT".format(ekey, key, actual, expected,
                                                                                        type, index))
                                        elif (actual > expected) and ((actual - expected) <= threshold):
                                            fun_test.add_checkpoint(
                                                "{} check of {} stats for the {} test for the block size & IO depth "
                                                "combo {} in {} {} DUT".format(ekey, key, mode, combo, type, index),
                                                "PASSED", expected, actual)
                                            fun_test.log("Final {} value {} of {} stats is within the expected range "
                                                         "{} in {} {} DUT".format(ekey, key, actual, expected, type,
                                                                                  index))
                                        else:
                                            internal_result[combo][mode] = False
                                            fun_test.add_checkpoint(
                                                "{} check of {} stats for the {} test for the block size & IO depth "
                                                "combo {} in {} {} DUT".format(ekey, key, mode, combo, type, index),
                                                "FAILED", expected, actual)
                                            fun_test.critical("Final {} value of {} stats {} is not equal to the "
                                                              "expected value {} in {} {} DUT".
                                                              format(ekey, key, actual, expected, type, index))
                                    else:
                                        fun_test.add_checkpoint(
                                            "{} check of {} stats for the {} test for the block size & IO depth combo "
                                            "{} in {} {} DUT".format(ekey, key, mode, combo, type, index), "PASSED",
                                            expected, actual)
                                        fun_test.log("Final {} value of {} stats {} is equal to the expected value "
                                                     "{} in {} {} DUT".format(ekey, key, actual, expected, type, index))
                                else:
                                    internal_result[combo][mode] = False
                                    fun_test.critical("{} is not found in {} stat in {} {} DUT".format(ekey, key, type,
                                                                                                       index))

                # Building the table raw for this variation
                row_data_list = []
                for i in table_data_cols:
                    if i not in row_data_dict:
                        row_data_list.append(0)
                    else:
                        row_data_list.append(row_data_dict[i])
                table_data_rows.append(row_data_list)
                post_results("Replica volume with DPU level failure domain", test_method, *row_data_list)

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
                command_result = self.storage_controller["blt"][index].fail_volume(
                    uuid=self.uuids["blt"][index], command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Disable fault_injection from the BLT volume having the "
                                                               "UUID {}".format(self.uuids["ndata"][index]))
                fun_test.sleep("Sleeping for a second to disable the fault_injection", 1)
                props_tree = "{}/{}/{}/{}".format("storage", "volumes", self.volume_types["blt"],
                                                  self.uuids["blt"][index])
                command_result = self.storage_controller["blt"][index].peek(props_tree)
                fun_test.log(command_result)
                fun_test.test_assert_expected(actual=int(command_result["blt"]["fault_injection"]), expected=0,
                                              message="Ensuring fault_injection got enabled")


class FioSeqWriteSeqReadOnly(ReplicaDPULevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Sequential Write & Read only performance of replica volume",
                              steps="""
        1. Create a BLT volume on dut instances 0 and 1
        2. Export (Attach) this local thin volume to dut instance 2 
        3. On Dut instance 2:
           a. Import the above local thin volume (Create RDS volume) from both dut instance 0 and 1
           b. Attach a replica volume using the 2 volumes imported at step a.
        4. Run the FIO sequential write and read only test(without verify) for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold.
        """)

    def setup(self):
        super(FioSeqWriteSeqReadOnly, self).setup()

    def run(self):
        super(FioSeqWriteSeqReadOnly, self).run()

    def cleanup(self):
        super(FioSeqWriteSeqReadOnly, self).cleanup()


class FioRandWriteRandReadOnly(ReplicaDPULevelTestcase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Random Write & Read only performance of replica volume",
                              steps="""
        1. Create a BLT volume on dut instances 0 and 1
        2. Export (Attach) this local thin volume to dut instance 2 
        3. On Dut instance 2:
            a. Import the above local thin volume (Create RDS volume) from both dut instance 0 and 1
            b. Attach a replica volume using the 2 volumes imported at step a.
        4. Run the FIO random write and read only test(without verify) for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold.
        """)

    def setup(self):
        super(FioRandWriteRandReadOnly, self).setup()

    def run(self):
        super(FioRandWriteRandReadOnly, self).run()

    def cleanup(self):
        super(FioRandWriteRandReadOnly, self).cleanup()


class FioSeqAndRandReadOnlyWithFailure(ReplicaDPULevelTestcase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Random Write & Read only performance of replica volume",
                              steps="""
        1. Create a BLT volume on dut instances 0 and 1
        2. Export (Attach) this local thin volume to dut instance 2
        3. On Dut instance 2:
            a. Import the above BLT volume (Create RDS volume) from both dut instance 0 and 1
            b. Attach a replica volume using the 2 volumes imported at step a.
        4. Inject failure in one of the BLT volume
        5. Run the FIO sequential and random read only test(without verify) for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold.
        """)

    def setup(self):
        super(FioSeqAndRandReadOnlyWithFailure, self).setup()

    def run(self):
        super(FioSeqAndRandReadOnlyWithFailure, self).run()

    def cleanup(self):
        super(FioSeqAndRandReadOnlyWithFailure, self).cleanup()


class FioSeqReadWriteMix(ReplicaDPULevelTestcase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Sequential 75% Write & 25% Read performance of replica volume",
                              steps="""
        1. Create a local thin volume on dut instances 0 and 1
        2. Export (Attach) this local thin volume to dut instance 2 
        3. On Dut instance 2:
            a. Import the above local thin volume (Create RDS volume) from both dut instance 0 and 1
            b. Attach a replica volume using the 2 volumes imported at step a.
        4. Run the FIO sequential write and read mix test with 3:1 ratio for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold.
        """)

    def setup(self):
        super(FioSeqReadWriteMix, self).setup()

    def run(self):
        super(FioSeqReadWriteMix, self).run()

    def cleanup(self):
        super(FioSeqReadWriteMix, self).cleanup()


class FioRandReadWriteMix(ReplicaDPULevelTestcase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Random 75% Write & 25% Read performance of replica volume",
                              steps="""
        1. Create a local thin volume on dut instances 0 and 1
        2. Export (Attach) this local thin volume to dut instance 2 
        3. On Dut instance 2:
            a. Import the above local thin volume (Create RDS volume) from both dut instance 0 and 1
            b. Attach a replica volume using the 2 volumes imported at step a.
        4. Run the FIO random write and read mix test with 3:1 ratio for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold.
        """)

    def setup(self):
        super(FioRandReadWriteMix, self).setup()

    def run(self):
        super(FioRandReadWriteMix, self).run()

    def cleanup(self):
        super(FioRandReadWriteMix, self).cleanup()


class FioLargeWriteReadOnly(ReplicaDPULevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Write & Read only performance(for both Sequential and random) for large sizes "
                                      "of replica volume",
                              steps="""
        1. Create a local thin volume on dut instances 0 and 1
        2. Export (Attach) this local thin volume to dut instance 2 
        3. On Dut instance 2:
            a. Import the above local thin volume (Create RDS volume) from both dut instance 0 and 1
            b. Attach a replica volume using the 2 volumes imported at step a.
        4. Run the FIO write and read only test(without verify) for various sizes from the external Linux server and 
        check the performance are inline with the expected threshold.
        """)

    def setup(self):
        super(FioLargeWriteReadOnly, self).setup()

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase

        self.uuids = fun_test.shared_variables["replica"]["uuids"]
        self.storage_controller = fun_test.shared_variables["replica"]["storage_controller"]
        destination_ip = self.global_setup["duts"]["replica"].data_plane_ip

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

        volumes = ["blt", "replica"]

        table_data_headers = ["Block Size", "IO Depth", "Size", "Operation", "Write IOPS", "Read IOPS",
                              "Write Throughput in KiB/s", "Read Throughput in KiB/s", "Write Latency in uSecs",
                              "Read Latency in uSecs"]
        table_data_cols = ["block_size", "iodepth", "size", "mode", "writeiops", "readiops", "writebw", "readbw",
                           "writelatency", "readlatency"]
        table_data_rows = []

        tmp = self.fio_bs_iodepth.split(',')

        fio_block_size = tmp[0].strip('() ') + 'k'
        self.fio_cmd_args["bs"] = fio_block_size

        fio_iodepth = tmp[1].strip('() ')
        self.fio_cmd_args["iodepth"] = fio_iodepth

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

                # Pulling the initial volume stats from all the DUTs in dictionary format
                fun_test.log("Pulling the initial volume stats from all the DUTs in dictionary format before the test")
                initial_volume_status[size][mode] = {}
                for type in volumes:
                    initial_volume_status[size][mode][type] = {}
                    for index, uuid in enumerate(self.uuids[type]):
                        initial_volume_status[size][mode][type][index] = {}

                        props_tree = "{}/{}/{}/{}".format("storage", "volumes", self.volume_types[type], uuid)
                        command_result = {}
                        command_result = self.storage_controller[type][index].peek(props_tree)
                        fun_test.simple_assert(command_result["status"], "Initial volume stats of DUT instance {}".
                                               format(index))
                        initial_volume_status[size][mode][type][index] = command_result["data"]
                        fun_test.log("{} {} volume Status at the beginning of the test:".format(type, index))
                        fun_test.log(initial_volume_status[size][mode][type][index])

                # Pulling the initial stats in dictionary format
                initial_stats[size][mode] = {}
                for type in volumes:
                    initial_stats[size][mode][type] = {}
                    for index, uuid in enumerate(self.uuids[type]):
                        initial_stats[size][mode][type][index] = {}
                        for key, value in self.stats_list.items():
                            if key not in initial_stats[size][mode][type][index]:
                                initial_stats[size][mode][type][index][key] = {}
                            if value:
                                for item in value:
                                    props_tree = "{}/{}/{}".format("stats", key, item)
                                    command_result = self.storage_controller[type][index].peek(props_tree)
                                    fun_test.simple_assert(
                                        command_result["status"], "Initial {} stats of {} {} DUT "
                                                                  "instance".format(props_tree, type, index))
                                    initial_stats[size][mode][type][index][key][item] = command_result["data"]
                            else:
                                props_tree = "{}/{}".format("stats", key)
                                command_result = self.storage_controller[type][index].peek(props_tree)
                                fun_test.simple_assert(
                                    command_result["status"], "Initial {} stats of {} {} DUT "
                                                              "instance".format(props_tree, type, index))
                                initial_stats[size][mode][type][index][key] = command_result["data"]
                            fun_test.log("{} stats of {} {} DUT at the beginning of the test:".format(key, type, index))
                            fun_test.log(initial_stats[size][mode][type][index][key])

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

                # Pulling volume stats from all the DUTs in dictionary format after the test
                fun_test.log("Pulling the volume stats from all the DUTs after the FIO test")
                final_volume_status[size][mode] = {}
                for type in volumes:
                    final_volume_status[size][mode][type] = {}
                    for index, uuid in enumerate(self.uuids[type]):
                        final_volume_status[size][mode][type][index] = {}
                        props_tree = "{}/{}/{}/{}".format("storage", "volumes", self.volume_types[type], uuid)
                        command_result = {}
                        command_result = self.storage_controller[type][index].peek(props_tree)
                        fun_test.simple_assert(command_result["status"], "Initial {} {} volume stats".
                                               format(type, index))
                        final_volume_status[size][mode][type][index] = command_result["data"]
                        fun_test.log("{} {} volume Status at the end of the test:".format(type, index))
                        fun_test.log(final_volume_status[size][mode][type][index])

                # Pulling the final stats in dictionary format
                final_stats[size][mode] = {}
                for type in volumes:
                    final_stats[size][mode][type] = {}
                    for index, uuid in enumerate(self.uuids[type]):
                        final_stats[size][mode][type][index] = {}
                        for key, value in self.stats_list.items():
                            if key not in final_stats[size][mode][type][index]:
                                final_stats[size][mode][type][index][key] = {}
                            if value:
                                for item in value:
                                    props_tree = "{}/{}/{}".format("stats", key, item)
                                    command_result = self.storage_controller[type][index].peek(props_tree)
                                    fun_test.simple_assert(
                                        command_result["status"], "Final {} stats of {} {} DUT "
                                                                  "instance".format(props_tree, type, index))
                                    final_stats[size][mode][type][index][key][item] = command_result["data"]
                            else:
                                props_tree = "{}/{}".format("stats", key)
                                command_result = self.storage_controller[type][index].peek(props_tree)
                                fun_test.simple_assert(command_result["status"], "Final {} stats of {} {} DUT instance".
                                                       format(props_tree, type, index))
                                final_stats[size][mode][type][index][key] = command_result["data"]
                            fun_test.log("{} stats of {} {} DUT at the end of the test:".format(key, type, index))
                            fun_test.log(final_stats[size][mode][type][index][key])

                # Finding the difference between the internal volume stats before and after the test
                diff_volume_stats[size][mode] = {}
                for type in volumes:
                    diff_volume_stats[size][mode][type] = {}
                    for index in range(len(self.uuids[type])):
                        diff_volume_stats[size][mode][type][index] = {}
                        for fkey, fvalue in final_volume_status[size][mode][type][index].items():
                            # Don't compute the difference of stats which is not defined in expected_volume_stats in
                            # the json config file
                            if fkey not in self.expected_volume_stats[size][mode][type][str(index)] \
                                    or fkey == "fault_injection":
                                diff_volume_stats[size][mode][type][index][fkey] = fvalue
                                continue
                            if fkey in initial_volume_status[size][mode][type][index]:
                                ivalue = initial_volume_status[size][mode][type][index][fkey]
                                diff_volume_stats[size][mode][type][index][fkey] = fvalue - ivalue
                        fun_test.log("Difference of {} {} volume status before and after the test:".
                                     format(type, index))
                        fun_test.log(diff_volume_stats[size][mode][type][index])

                # Finding the difference between the stats before and after the test
                diff_stats[size][mode] = {}
                for type in volumes:
                    diff_stats[size][mode][type] = {}
                    for index in range(len(self.uuids[type])):
                        diff_stats[size][mode][type][index] = {}
                        for key, value in self.stats_list.items():
                            diff_stats[size][mode][type][index][key] = {}
                            for fkey, fvalue in final_stats[size][mode][type][index][key].items():
                                ivalue = initial_stats[size][mode][type][index][key][fkey]
                                diff_stats[size][mode][type][index][key][fkey] = fvalue - ivalue
                            fun_test.log("Difference of {} stats of {} {} before and after the test:".format(key, type,
                                                                                                             index))
                            fun_test.log(diff_stats[size][mode][type][index][key])

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
                for type in volumes:
                    for index in range(len(self.uuids[type])):
                        for ekey, evalue in self.expected_volume_stats[size][mode][type][str(index)].items():
                            if evalue == -1:
                                fun_test.log("Ignoring the {}'s key checking for {} {} volume".format(ekey, type,
                                                                                                      index))
                                continue
                            if ekey in diff_volume_stats[size][mode][type][index]:
                                actual = diff_volume_stats[size][mode][type][index][ekey]
                                # row_data_dict[ekey] = actual
                                if actual != evalue:
                                    if (actual < evalue) and ((evalue - actual) <= self.volume_pass_threshold):
                                        fun_test.add_checkpoint(
                                            "{} check for {} {} test for the {} {} volume with the block size & IO "
                                            "depth combo ({}, {})".format(ekey, size, mode, type, index, fio_block_size,
                                                                          fio_iodepth), "PASSED", evalue, actual)
                                        fun_test.critical("Final {} value {} of {} {} volume is within the expected "
                                                          "range {}".format(ekey, actual, type, index, evalue))
                                    elif (actual > evalue) and ((actual - evalue) <= self.volume_pass_threshold):
                                        fun_test.add_checkpoint(
                                            "{} check for {} {} test for the {} {} volume with the block size & IO "
                                            "depth combo ({}, {})".format(ekey, size, mode, type, index, fio_block_size,
                                                                          fio_iodepth), "PASSED", evalue, actual)
                                        fun_test.critical("Final {} value {} of {} {} volume is within the expected "
                                                          "range {}".format(ekey, actual, type, index, evalue))
                                    else:
                                        internal_result[size][mode] = False
                                        fun_test.add_checkpoint(
                                            "{} check for {} {} test for the {} {} volume with the block size & IO "
                                            "depth combo ({}, {})".format(ekey, size, mode, type, index, fio_block_size,
                                                                          fio_iodepth), "PASSED", evalue, actual)
                                        fun_test.critical("Final {} value {} of {} {} volume is not equal to the "
                                                          "expected value {}".format(ekey, actual, type, index, evalue))
                                else:
                                    fun_test.add_checkpoint(
                                        "{} check for {} {} test for the {} {} volume with the block size & IO "
                                        "depth combo ({}, {})".format(ekey, size, mode, type, index, fio_block_size,
                                                                      fio_iodepth), "PASSED", evalue, actual)
                                    fun_test.log("Final {} value {} of {} {} volume is equal to the expected value {}".
                                                 format(ekey, actual, type, index, evalue))
                            else:
                                internal_result[size][mode] = False
                                fun_test.critical("{} is not found in {} {} volume status".format(ekey, type, index))

                # Comparing the internal stats with the expected value
                for type in volumes:
                    for index in range(len(self.uuids[type])):
                        for key, value in self.expected_stats[size][mode][type][str(index)].items():
                            for ekey, evalue in self.expected_stats[size][mode][type][str(index)][key].items():
                                if ekey in diff_stats[size][mode][type][index][key]:
                                    actual = diff_stats[size][mode][type][index][key][ekey]
                                    evalue_list = evalue.strip("()").split(",")
                                    expected = int(evalue_list[0])
                                    threshold = int(evalue_list[1])
                                    if actual != expected:
                                        if actual < expected:
                                            fun_test.add_checkpoint(
                                                "{} check of {} stats for the {} {} test for the block size & IO depth "
                                                "combo ({}, {}) in {} {} DUT".format(ekey, key, size, mode,
                                                                                     fio_block_size, fio_iodepth, type,
                                                                                     index), "PASSED", expected, actual)
                                            fun_test.log("Final {} value {} of {} stats is less than the expected "
                                                         "range {} in {} {} DUT".format(ekey, key, actual, expected,
                                                                                        type, index))
                                        elif (actual > expected) and ((actual - expected) <= threshold):
                                            fun_test.add_checkpoint(
                                                "{} check of {} stats for the {} {} test for the block size & IO depth "
                                                "combo ({}, {}) in {} {} DUT".format(ekey, key, size, mode,
                                                                                     fio_block_size, fio_iodepth, type,
                                                                                     index), "PASSED", expected, actual)
                                            fun_test.log("Final {} value {} of {} stats is within the expected range "
                                                         "{} in {} {} DUT".format(ekey, key, actual, expected, type,
                                                                                  index))
                                        else:
                                            internal_result[size][mode] = False
                                            fun_test.add_checkpoint(
                                                "{} check of {} stats for the {} {} test for the block size & IO depth "
                                                "combo ({}, {}) in {} {} DUT".format(ekey, key, size, mode,
                                                                                     fio_block_size, fio_iodepth, type,
                                                                                     index), "FAILED", expected, actual)
                                            fun_test.critical("Final {} value of {} stats {} is not equal to the "
                                                              "expected value {} in {} {} DUT".
                                                              format(ekey, key, actual, expected, type, index))
                                    else:
                                        fun_test.add_checkpoint(
                                            "{} check of {} stats for the {} {} test for the block size & IO depth "
                                            "combo ({}, {}) in {} {} DUT".format(ekey, key, size, mode, fio_block_size,
                                                                                 fio_iodepth, type, index), "PASSED",
                                            expected, actual)
                                        fun_test.log("Final {} value of {} stats {} is equal to the expected value "
                                                     "{} in {} {} DUT".format(ekey, key, actual, expected, type, index))
                                else:
                                    internal_result[size][mode] = False
                                    fun_test.critical("{} is not found in {} stat in {} {} DUT".format(ekey, key, type,
                                                                                                       index))

                # Building the table raw for this variation
                row_data_list = []
                for i in table_data_cols:
                    if i not in row_data_dict:
                        row_data_list.append(0)
                    else:
                        row_data_list.append(row_data_dict[i])
                table_data_rows.append(row_data_list)
                post_results("Replica volume with DPU level failure domain", test_method, *row_data_list)

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
        super(FioLargeWriteReadOnly, self).cleanup()


if __name__ == "__main__":

    replica_script = ReplicaDPULevelScript()
    replica_script.add_test_case(FioSeqWriteSeqReadOnly())
    replica_script.add_test_case(FioRandWriteRandReadOnly())
    # Commenting this case because of the bug #771
    # replica_script.add_test_case(FioSeqAndRandReadOnlyWithFailure())
    replica_script.add_test_case(FioSeqReadWriteMix())
    replica_script.add_test_case(FioRandReadWriteMix())
    # replica_script.add_test_case(FioLargeWriteReadOnly())
    replica_script.run()
