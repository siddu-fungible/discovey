from lib.system.fun_test import *
from lib.system import utils
from lib.topology.topology_helper import TopologyHelper
from lib.topology.dut import Dut, DutInterface
from lib.fun.f1 import F1
from lib.host.storage_controller import StorageController
from lib.host.traffic_generator import TrafficGenerator
from web.fun_test.analytics_models_helper import VolumePerformanceHelper
import uuid, re

'''
Script to track the performance of various read write combination of Erasure Coded volume using FIO
'''


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


def generate_uuid(length=16):

    this_uuid = str(uuid.uuid4()).replace("-", "")[length:]
    # this_uuid = this_uuid[:3] + '-' + this_uuid[3:6] + '-' + this_uuid[6:9] + '-' + this_uuid[9:]
    return this_uuid


class ECDPULevelScript(FunTestScript):
    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. i.e Start ndata + nparity number of POSIXs and allocate a Linux instance. 
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
            self.ec_coding["ndata"] = 2
            self.ec_coding["nparity"] = 1
        else:
            for k, v in benchmark_dict["GlobalSetup"].items():
                setattr(self, k, v)

        if 'ec_coding' not in benchmark_dict['GlobalSetup'] or not benchmark_dict['GlobalSetup']['ec_coding']:
            fun_test.critical("EC coding is not available in the {} config file".format(benchmark_file))
            fun_test.log("Going to use the script level defaults")
            self.ec_coding["ndata"] = 2
            self.ec_coding["nparity"] = 1

        # Computing number DPUs needed and constructing the dut_info attribute of the topology_dict accordingly
        if hasattr(self, "ec_in_sep_dpu") and self.ec_in_sep_dpu:
            self.num_dpu = self.ec_coding["ndata"] + self.ec_coding["nparity"] + 1
        else:
            self.ec_in_sep_dpu = 0
            self.num_dpu = self.ec_coding["ndata"] + self.ec_coding["nparity"]

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

        # Saving the dut handles in a dictionary by using its EC role as the inded
        self.duts = {}
        start = 0
        for type in sorted(self.ec_coding):
            self.duts[type] = []
            for index in range(start, start + self.ec_coding[type]):
                self.duts[type].append(topology.get_dut_instance(index=index))
            start = index + 1
        self.duts["ec"] = topology.get_dut_instance(index=self.num_dpu - 1)

        # for index in range(self.number_of_dpu):
        #    self.duts.append(topology.get_dut_instance(index=index))
        #    fun_test.test_assert(self.duts[index], "Retrieved dut instance {}".format(index))

        global_setup = self.__dict__

        fun_test.shared_variables["topology"] = topology
        fun_test.shared_variables["global_setup"] = global_setup

    def cleanup(self):
        TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()
        # pass


class ECDPULevelTestcase(FunTestCase):

    def describe(self):
        pass

    def setup(self):

        testcase = self.__class__.__name__

        # Importing global setup
        self.topology = fun_test.shared_variables["topology"]
        self.global_setup = fun_test.shared_variables["global_setup"]
        self.linux_host = self.topology.get_tg_instance(tg_index=0)
        destination_ip = self.global_setup["duts"]["ec"].data_plane_ip

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

        self.ec_ratio = str(self.global_setup["ec_coding"]["ndata"]) + str(self.global_setup["ec_coding"]["nparity"])

        if self.use_lsv:
            # LS volume capacity is the ndata times of the BLT volume capacity
            self.volume_capacity["lsv"] = self.volume_capacity["ndata"] * self.ec_coding["ndata"]

            fun_test.log("LS volume needs to be configured. So increasing the BLT volume's capacity by 30% and "
                         "rounding that to the nearest 8MB value")
            eight_mb = 1024 * 1024 * 8
            for type in sorted(self.global_setup["ec_coding"]):
                tmp = self.volume_capacity[type] * (1 + self.lsv_pct)
                self.volume_capacity[type] = int(tmp + (eight_mb - (tmp % eight_mb)))

            # Setting the RDS & EC volume capacity also to same as the one of ndata volume capacity
            self.volume_capacity["rds"] = self.volume_capacity["ndata"]
            self.volume_capacity["ec"] = self.volume_capacity["ndata"]

        # Initializing the storage controller handle
        self.storage_controller = {}
        ec_dut = self.global_setup["duts"]["ec"]
        self.storage_controller["ec"] = [StorageController(target_ip=ec_dut.host_ip,
                                                           target_port=ec_dut.external_dpcsh_port)]
        for type in sorted(self.global_setup["ec_coding"]):
            self.storage_controller[type] = []
            for i in range(self.global_setup["ec_coding"][type]):
                dut = self.global_setup["duts"][type][i]
                self.storage_controller[type].append(StorageController(target_ip=dut.host_ip,
                                                                       target_port=dut.external_dpcsh_port))

        if self.ec_ratio not in fun_test.shared_variables or \
                not fun_test.shared_variables[self.ec_ratio]["setup_created"]:
            fun_test.shared_variables[self.ec_ratio] = {}
            fun_test.shared_variables[self.ec_ratio]["setup_created"] = False
            self.uuids = {}
            self.uuids["blt"] = []
            self.uuids["rds"] = []
            self.uuids["ec"] = []
            self.uuids["lsv"] = []

            # Configuring ndata and nparity number of BLT volumes in their appropriate DPU
            for type in sorted(self.global_setup["ec_coding"]):
                self.uuids[type] = []
                for i in range(self.global_setup["ec_coding"][type]):

                    # Configuring the controller
                    dut = self.global_setup["duts"][type][i]
                    command_result = self.storage_controller[type][i].command(command="enable_counters", legacy=True)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Enabling counters on {} {} DUT instance"
                                         .format(type, i))

                    command_result = self.storage_controller[type][i].ip_cfg(
                        ip=dut.data_plane_ip, command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"],
                                         "ip_cfg {} on {} {} DUT instance".format(dut.data_plane_ip, type, i))

                    # Configuring the BLT volume
                    this_uuid = generate_uuid()
                    self.uuids[type].append(this_uuid)
                    self.uuids["blt"].append(this_uuid)
                    command_result = self.storage_controller[type][i].create_volume(
                        type=self.volume_types[type], capacity=self.volume_capacity[type],
                        block_size=self.volume_block[type], name=type+"-"+str(i), uuid=this_uuid,
                        command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Create BLT volume on {} {} DUT instance".
                                         format(type, i))

                    # Attaching the BLT to the DPU in the which the EC volume going to be configured
                    command_result = self.storage_controller[type][i].volume_attach_remote(
                        ns_id=self.ns_id[type], uuid=this_uuid, remote_ip=ec_dut.data_plane_ip,
                        command_duration=self.command_timeout)
                    fun_test.log(command_result)
                    fun_test.test_assert(command_result["status"], "Attaching BLT volume of {} {} DUT instance to the "
                                                                   "last DUT instance".format(type, i))

            # Configuring RDS, EC & LSV(if needed) volume in the last DUT defined in the topplogy dict
            # Configuring the controller in the DUT in case if the EC volume needs to configured in a separate DPU
            if self.global_setup["ec_in_sep_dpu"]:
                # Configuring the controller
                command_result = self.storage_controller["ec"][0].command(command="enable_counters", legacy=True)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Enabling counters in the last DUT instance")

                command_result = self.storage_controller["ec"][0].ip_cfg(ip=ec_dut.data_plane_ip,
                                                                         command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"],
                                     "ip_cfg {} on last DUT instance".format(ec_dut.data_plane_ip))

            # Configuring the required number of RDS based on whether the EC volume needs to configured in a separate
            # DPU. If the EC dpu DUT instance is equal to the last blt instance(i.,e the instance in the nparity blt
            # falls), then don't configure the RDS in that DUT instance, because the EC volume need not to be in a
            # separate volume

            for type in sorted(self.global_setup["ec_coding"]):
                for i in range(self.global_setup["ec_coding"][type]):
                    dut = self.global_setup["duts"][type][i]
                    if ec_dut != dut:
                        this_uuid = generate_uuid()
                        self.uuids["rds"].append(this_uuid)
                        command_result = self.storage_controller["ec"][0].create_volume(
                            type=self.volume_types["rds"], capacity=self.volume_capacity["rds"],
                            block_size=self.volume_block["rds"], name=type+str(i)+"-rds", uuid=this_uuid,
                            remote_nsid=self.ns_id[type], remote_ip=dut.data_plane_ip,
                            command_duration=self.command_timeout)
                        fun_test.log(command_result)
                        fun_test.test_assert(command_result["status"], "Create RDS volume for {} {} DUT instance".
                                             format(type, i))

            if len(self.uuids["rds"]) == len(self.uuids["blt"]):
                ec_pvol_id = self.uuids["rds"]
            else:
                ec_pvol_id = self.uuids["rds"] + list(self.uuids["blt"][-1])

            # Configuring EC volume on top of BLT volumes
            this_uuid = generate_uuid()
            self.uuids["ec"].append(this_uuid)
            command_result = self.storage_controller["ec"][0].create_volume(
                type=self.volume_types["ec"], capacity=self.volume_capacity["ec"], block_size=self.volume_block["ec"],
                name="ec-1", uuid=this_uuid, ndata=self.global_setup["ec_coding"]["ndata"],
                nparity=self.global_setup["ec_coding"]["nparity"], pvol_id=ec_pvol_id,
                command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Create EC volume on last DUT instance")
            attach_uuid = this_uuid
            ns_id = self.ns_id["ec"]

            # Configuring LS volume based on the script config settting
            if self.use_lsv:
                this_uuid = generate_uuid()
                self.uuids["lsv"].append(this_uuid)
                command_result = self.storage_controller["ec"][0].create_volume(
                    type=self.volume_types["lsv"], capacity=self.volume_capacity["lsv"],
                    block_size=self.volume_block["lsv"], name="lsv-1", uuid=this_uuid,
                    group=self.global_setup["ec_coding"]["ndata"], pvol_id=self.uuids["ec"],
                    command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Create LS volume on the last DUT instance")
                attach_uuid = this_uuid
                ns_id = self.ns_id["lsv"]

            # Attaching/Exporting the EC/LS volume to the external server
            command_result = self.storage_controller["ec"][0].volume_attach_remote(
                ns_id=ns_id, uuid=attach_uuid, remote_ip=self.linux_host.internal_ip,
                command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Attaching EC/LS volume in the last DUT instance")

            # disabling the error_injection for the EC volume
            command_result = {}
            command_result = self.storage_controller["ec"][0].poke("params/ecvol/error_inject 0")
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Disabling error_injection for EC volume in the last DUT "
                                                           "instance")

            # Ensuring that the error_injection got disabled properly
            fun_test.sleep("Sleeping for a second to disable the error_injection", 1)
            command_result = {}
            command_result = self.storage_controller["ec"][0].peek("params/ecvol")
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Retrieving error_injection status from the last DUT "
                                                           "instance")
            fun_test.test_assert_expected(actual=int(command_result["data"]["error_inject"]), expected=0,
                                          message="Ensuring error_injection got disabled")

            fun_test.shared_variables[self.ec_ratio]["uuids"] = self.uuids
            # fun_test.shared_variables[self.ec_ratio]["storage_controller"] = self.storage_controller
            fun_test.shared_variables[self.ec_ratio]["setup_created"] = True

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

        self.uuids = fun_test.shared_variables[self.ec_ratio]["uuids"]
        # self.storage_controller = fun_test.shared_variables[self.ec_ratio]["storage_controller"]
        destination_ip = self.global_setup["duts"]["ec"].data_plane_ip

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

        volumes = sorted(self.global_setup["ec_coding"])
        volumes.append("ec")
        if self.use_lsv and self.check_lsv_stats:
            volumes.append("lsv")

        # Check any plex needs to be induced to fail and if so do the same
        if hasattr(self, "trigger_plex_failure") and self.trigger_plex_failure:
            for index in self.failure_plex_indices:
                command_result = self.storage_controller["ndata"][index].fail_volume(
                    uuid=self.uuids["ndata"][index], command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Inject failure to the ndata BLT volume having the "
                                                               "UUID {}".format(self.uuids["ndata"][index]))
                fun_test.sleep("Sleeping for a second to enable the fault_injection", 1)
                props_tree = "{}/{}/{}/{}".format("storage", "volumes", self.volume_types["ndata"],
                                                  self.uuids["ndata"][index])
                command_result = self.storage_controller["ndata"][index].peek(props_tree)
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

                # Pulling initial volume stats of all the volumes from the DUT in dictionary format
                fun_test.log("Pulling initial stats of the all the volumes from the DUT in dictionary format before "
                             "the test")
                initial_volume_status[combo][mode] = {}
                for type in volumes:
                    if type == "lsv":
                        sc_type = "ec"
                    else:
                        sc_type = type
                    initial_volume_status[combo][mode][type] = {}
                    for index, uuid in enumerate(self.uuids[type]):
                        initial_volume_status[combo][mode][type][index] = {}
                        storage_props_tree = "{}/{}/{}/{}".format("storage", "volumes", self.volume_types[type], uuid)
                        command_result = {}
                        command_result = self.storage_controller[sc_type][index].peek(storage_props_tree)
                        fun_test.simple_assert(command_result["status"], "Initial {} {} volume stats".
                                               format(type, index))
                        initial_volume_status[combo][mode][type][index] = command_result["data"]
                        fun_test.log("{} {} volume Status at the beginning of the test:".format(type, index))
                        fun_test.log(initial_volume_status[combo][mode][type][index])

                # Pulling the initial stats in dictionary format
                initial_stats[combo][mode] = {}
                for type in volumes:
                    if type == "lsv":
                        continue
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
                fun_test.log("Running FIO {} only test with the block size and IO depth set to {} & {} for the EC "
                             "coding {}".format(mode, fio_block_size, fio_iodepth, self.ec_ratio))
                fio_output[combo][mode] = {}
                fio_output[combo][mode] = self.linux_host.remote_fio(
                    destination_ip=destination_ip, rw=mode, bs=fio_block_size, iodepth=fio_iodepth, **self.fio_cmd_args)
                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output[combo][mode])
                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)

                # Pulling volume stats of all the volumes from the DUT in dictionary format after the test
                fun_test.log("Pulling volume stats of all volumes after the FIO test")
                final_volume_status[combo][mode] = {}
                for type in volumes:
                    if type == "lsv":
                        sc_type = "ec"
                    else:
                        sc_type = type
                    final_volume_status[combo][mode][type] = {}
                    for index, uuid in enumerate(self.uuids[type]):
                        final_volume_status[combo][mode][type][index] = {}
                        storage_props_tree = "{}/{}/{}/{}".format("storage", "volumes", self.volume_types[type], uuid)
                        command_result = {}
                        command_result = self.storage_controller[sc_type][index].peek(storage_props_tree)
                        fun_test.simple_assert(command_result["status"], "Initial {} {} volume stats".
                                               format(type, index))
                        final_volume_status[combo][mode][type][index] = command_result["data"]
                        fun_test.log("{} {} volume Status at the end of the test:".format(type, index))
                        fun_test.log(final_volume_status[combo][mode][type][index])

                # Pulling the final stats in dictionary format
                final_stats[combo][mode] = {}
                for type in volumes:
                    if type == "lsv":
                        continue
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
                post_results("EC with DPU level failure domain", test_method, *row_data_list)

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
                command_result = self.storage_controller["ndata"][index].fail_volume(
                    uuid=self.uuids["ndata"][index], command_duration=self.command_timeout)
                fun_test.log(command_result)
                fun_test.test_assert(command_result["status"], "Disable fault_injection from the ndata BLT volume "
                                                               "having the UUID {}".format(self.uuids["ndata"][index]))
                fun_test.sleep("Sleeping for a second to disable the fault_injection", 1)
                props_tree = "{}/{}/{}/{}".format("storage", "volumes", self.volume_types["ndata"],
                                                  self.uuids["ndata"][index])
                command_result = self.storage_controller["ndata"][index].peek(props_tree)
                fun_test.log(command_result)
                fun_test.test_assert_expected(actual=int(command_result["data"]["fault_injection"]), expected=0,
                                              message="Ensuring fault_injection got enabled")

        # Initializing the storage controller handle
        for type in sorted(self.global_setup["ec_coding"]):
            for i in range(self.global_setup["ec_coding"][type]):
                self.storage_controller[type][i].disconnect()
        self.storage_controller["ec"][0].disconnect()


class EC21FioSeqWriteSeqReadOnly(ECDPULevelTestcase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Sequential Write & Read only performance of EC volume",
                              steps="""
        1. Create a BLT volumes on DUT instance 0-2.
        2. Export these BLT volumes to the last DUT instance.
        3. On the last Dut instance, import the above BLT volumes (Create RDS volume) from the DUT instance 0-2.
        4. Create a 2:1 EC volume on top of the 3 BLT volumes.
        5. Create a LS volume on top of the EC volume.
        6. Export (Attach) the above LS volume to external Linux instance/container. 
        7. Run the FIO sequential write and read only test(without verify) for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold.
        """)

    def setup(self):
        super(EC21FioSeqWriteSeqReadOnly, self).setup()

    def run(self):
        super(EC21FioSeqWriteSeqReadOnly, self).run()

    def cleanup(self):
        super(EC21FioSeqWriteSeqReadOnly, self).cleanup()


class EC21FioRandWriteRandReadOnly(ECDPULevelTestcase):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Random Write & Read only performance of EC volume",
                              steps="""
        1. Create a BLT volumes on DUT instance 0-2.
        2. Export these BLT volumes to the last DUT instance.
        3. On the last Dut instance, import the above BLT volumes (Create RDS volume) from the DUT instance 0-2.
        4. Create a 2:1 EC volume on top of the 3 BLT volumes.
        5. Create a LS volume on top of the EC volume.
        6. Export (Attach) the above LS volume to external Linux instance/container.
        7. Run the FIO random write and read only test(without verify) for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold.
        """)

    def setup(self):
        super(EC21FioRandWriteRandReadOnly, self).setup()

    def run(self):
        super(EC21FioRandWriteRandReadOnly, self).run()

    def cleanup(self):
        super(EC21FioRandWriteRandReadOnly, self).cleanup()


class EC21FioSeqAndRandReadOnlyWithFailure(ECDPULevelTestcase):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Sequential and Random Read only performance of EC volume with a plex failure",
                              steps="""
        1. Create a BLT volumes on DUT instance 0-2.
        2. Export these BLT volumes to the last DUT instance.
        3. On the last Dut instance, import the above BLT volumes (Create RDS volume) from the DUT instance 0-2.
        4. Create a 2:1 EC volume on top of the 3 BLT volumes.
        5. Create a LS volume on top of the EC volume.
        6. Export (Attach) the above LS volume to external Linux instance/container.
        7. Inject failure in one of the ndata BLT volume
        8. Run the FIO sequential and random read only test(without verify) for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold.
        """)

    def setup(self):
        super(EC21FioSeqAndRandReadOnlyWithFailure, self).setup()

    def run(self):
        super(EC21FioSeqAndRandReadOnlyWithFailure, self).run()

    def cleanup(self):
        super(EC21FioSeqAndRandReadOnlyWithFailure, self).cleanup()


class EC21FioSeqReadWriteMix(ECDPULevelTestcase):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Sequential 75% Write & 25% Read performance of EC volume",
                              steps="""
        1. Create a BLT volumes on DUT instance 0-2.
        2. Export these BLT volumes to the last DUT instance.
        3. On the last Dut instance, import the above BLT volumes (Create RDS volume) from the DUT instance 0-2.
        4. Create a 2:1 EC volume on top of the 3 BLT volumes.
        5. Create a LS volume on top of the EC volume.
        6. Export (Attach) the above LS volume to external Linux instance/container.
        7. Run the FIO sequential write and read mix test with 3:1 ratio for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold.
        """)

    def setup(self):
        super(EC21FioSeqReadWriteMix, self).setup()

    def run(self):
        super(EC21FioSeqReadWriteMix, self).run()

    def cleanup(self):
        super(EC21FioSeqReadWriteMix, self).cleanup()


class EC21FioRandReadWriteMix(ECDPULevelTestcase):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Random 75% Write & 25% Read performance of EC volume",
                              steps="""
        1. Create a BLT volumes on DUT instance 0-2.
        2. Export these BLT volumes to the last DUT instance.
        3. On the last Dut instance, import the above BLT volumes (Create RDS volume) from the DUT instance 0-2.
        4. Create a 2:1 EC volume on top of the 3 BLT volumes.
        5. Create a LS volume on top of the EC volume.
        6. Export (Attach) the above LS volume to external Linux instance/container.
        7. Run the FIO random write and read mix test with 3:1 ratio for various block size and IO depth from the 
        external Linux server and check the performance are inline with the expected threshold.
        """)

    def setup(self):
        super(EC21FioRandReadWriteMix, self).setup()

    def run(self):
        super(EC21FioRandReadWriteMix, self).run()

    def cleanup(self):
        super(EC21FioRandReadWriteMix, self).cleanup()


if __name__ == "__main__":

    ec_dpu_script = ECDPULevelScript()
    ec_dpu_script.add_test_case(EC21FioSeqWriteSeqReadOnly())
    ec_dpu_script.add_test_case(EC21FioRandWriteRandReadOnly())
    # Commenting this case because of the bug #771
    # ec_dpu_script.add_test_case(EC21FioSeqAndRandReadOnlyWithFailure())
    ec_dpu_script.add_test_case(EC21FioSeqReadWriteMix())
    ec_dpu_script.add_test_case(EC21FioRandReadWriteMix())
    ec_dpu_script.run()
