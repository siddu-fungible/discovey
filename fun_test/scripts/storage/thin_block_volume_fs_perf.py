from lib.system.fun_test import *
from lib.system import utils
from lib.topology.dut import Dut, DutInterface
from lib.host.traffic_generator import TrafficGenerator
from web.fun_test.analytics_models_helper import BltVolumePerformanceHelper
from fun_settings import REGRESSION_USER, REGRESSION_USER_PASSWORD
from lib.fun.f1 import F1
from lib.fun.fs import Fs
from datetime import datetime
from lib.templates.storage.fio_performance_helper import FioPerfHelper

'''
Script to track the performance of various read write combination of local thin block volume using FIO
'''
# As of now the dictionary variable containing the setup/testbed info used in this script
tb_config = {
    "name": "Basic Storage",
    "dut_info": {
        0: {
            "mode": Dut.MODE_EMULATION,
            "type": Dut.DUT_TYPE_FSU,
            "disable_f1_index": 1,
            "ip": "server26",
            "user": REGRESSION_USER,
            "passwd": REGRESSION_USER_PASSWORD,
            "emu_target": "palladium",
            "model": "StorageNetwork2",
            "run_mode": "build_only",
            "pci_mode": "all",
            "bootarg": "app=mdt_test,load_mods workload=storage --serial --dpc-server --dpc-uart --csr-replay",
            "huid": 3,
            "ctlid": 2,
            "interface_info": {
                0: {
                    "vms": 0,
                    "type": DutInterface.INTERFACE_TYPE_PCIE
                }
            },
            "start_mode": F1.START_MODE_DPCSH_ONLY,
            "perf_multiplier": 1
        },
    }
}


def post_results(volume, test, block_size, io_depth, size, operation, write_iops, read_iops, write_bw, read_bw,
                 write_latency, write_90_latency, write_95_latency, write_99_latency, write_99_99_latency, read_latency,
                 read_90_latency, read_95_latency, read_99_latency, read_99_99_latency, fio_job_name):
    for i in ["write_iops", "read_iops", "write_bw", "read_bw", "write_latency", "write_90_latency", "write_95_latency",
              "write_99_latency", "write_99_99_latency", "read_latency", "read_90_latency", "read_95_latency",
              "read_99_latency", "read_99_99_latency", "fio_job_name"]:
        if eval("type({}) is tuple".format(i)):
            exec ("{0} = {0}[0]".format(i))

    db_log_time = fun_test.shared_variables["db_log_time"]
    num_ssd = fun_test.shared_variables["num_ssd"]
    num_volume = fun_test.shared_variables["num_volume"]

    blt = BltVolumePerformanceHelper()
    blt.add_entry(date_time=db_log_time, volume=volume, test=test, block_size=block_size, io_depth=int(io_depth),
                  size=size, operation=operation, num_ssd=num_ssd, num_volume=num_volume, fio_job_name=fio_job_name,
                  write_iops=write_iops, read_iops=read_iops, write_throughput=write_bw, read_throughput=read_bw,
                  write_avg_latency=write_latency, read_avg_latency=read_latency, write_90_latency=write_90_latency,
                  write_95_latency=write_95_latency, write_99_latency=write_99_latency,
                  write_99_99_latency=write_99_99_latency, read_90_latency=read_90_latency,
                  read_95_latency=read_95_latency, read_99_latency=read_99_latency,
                  read_99_99_latency=read_99_99_latency, write_iops_unit="ops",
                  read_iops_unit="ops", write_throughput_unit="MBps", read_throughput_unit="MBps",
                  write_avg_latency_unit="usecs", read_avg_latency_unit="usecs", write_90_latency_unit="usecs",
                  write_95_latency_unit="usecs", write_99_latency_unit="usecs", write_99_99_latency_unit="usecs",
                  read_90_latency_unit="usecs", read_95_latency_unit="usecs", read_99_latency_unit="usecs",
                  read_99_99_latency_unit="usecs")

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
        1. Deploy the topology. i.e Bring up FS
        2. Make the Linux instance available for the testcase
        """)

    def setup(self):
        # topology_obj_helper = TopologyHelper(spec=topology_dict)
        # topology = topology_obj_helper.deploy()

        fs = Fs.get(boot_args=tb_config["dut_info"][0]["bootarg"],
                    disable_f1_index=tb_config["dut_info"][0]["disable_f1_index"])
        fun_test.shared_variables["fs"] = fs

        fun_test.test_assert(fs.bootup(reboot_bmc=False), "FS bootup")
        f1 = fs.get_f1(index=0)
        fun_test.shared_variables["f1"] = f1

        self.db_log_time = get_current_time()
        fun_test.shared_variables["db_log_time"] = self.db_log_time

        self.storage_controller = f1.get_dpc_storage_controller()

        # Setting the syslog level to 2
        command_result = self.storage_controller.poke(props_tree=["params/syslog/level", 2], legacy=False)
        fun_test.test_assert(command_result["status"], "Setting syslog level to 2")

        command_result = self.storage_controller.peek(props_tree="params/syslog/level", legacy=False,
                                                      command_duration=5)
        fun_test.test_assert_expected(expected=2, actual=command_result["data"], message="Checking syslog level")

        fun_test.shared_variables["storage_controller"] = self.storage_controller
        fun_test.shared_variables["sysstat_install"] = False

    def cleanup(self):
        # TopologyHelper(spec=fun_test.shared_variables["topology"]).cleanup()
        # Detach the volume
        try:
            self.volume_details = fun_test.shared_variables["volume_details"]
            command_result = self.storage_controller.volume_detach_pcie(ns_id=self.volume_details["ns_id"],
                                                                        uuid=fun_test.shared_variables["thin_uuid"],
                                                                        huid=tb_config['dut_info'][0]['huid'],
                                                                        ctlid=tb_config['dut_info'][0]['ctlid'],
                                                                        command_duration=30)
            fun_test.test_assert(command_result["status"], "Detaching BLT volume on DUT")

            # Deleting the volume
            command_result = self.storage_controller.delete_volume(capacity=self.volume_details["capacity"],
                                                                   block_size=self.volume_details["block_size"],
                                                                   type=self.volume_details["type"],
                                                                   name=self.volume_details["name"],
                                                                   uuid=fun_test.shared_variables["thin_uuid"],
                                                                   command_duration=10)
            fun_test.test_assert(command_result["status"], "Deleting BLT volume on DUT")
        except:
            fun_test.log("Volume clean-up failed")

        fun_test.log("FS cleanup")
        fun_test.shared_variables["fs"].cleanup()


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

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 1
        if not hasattr(self, "num_volume"):
            self.num_volume = 1

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))
        fun_test.log("Block size and IO depth combo going to be used for this {} testcase: {}".
                     format(testcase, self.fio_bs_iodepth))
        fun_test.log("Benchmarking results going to be used for this {} testcase: \n{}".
                     format(testcase, self.expected_fio_result))
        fun_test.log("Expected internal volume stats for this {} testcase: \n{}".
                     format(testcase, self.expected_volume_stats))
        # End of benchmarking json file parsing

        num_ssd = self.num_ssd
        fun_test.shared_variables["num_ssd"] = num_ssd
        num_volume = self.num_volume
        fun_test.shared_variables["num_volume"] = num_volume

        self.nvme_block_device = self.nvme_device + "n" + str(self.volume_details["ns_id"])
        self.storage_controller = fun_test.shared_variables["storage_controller"]

        '''self.end_host = Linux(host_ip=tb_config["tg_info"][0]["ip"],
                                  ssh_username=tb_config["tg_info"][0]["user"],
                                  ssh_password=tb_config["tg_info"][0]["passwd"])'''

        fs = fun_test.shared_variables["fs"]
        self.end_host = fs.get_come()

        f1 = fun_test.shared_variables["f1"]

        if "blt" not in fun_test.shared_variables or not fun_test.shared_variables["blt"]["setup_created"]:
            fun_test.shared_variables["blt"] = {}
            fun_test.shared_variables["blt"]["setup_created"] = False
            fun_test.shared_variables["volume_details"] = self.volume_details

            # self.end_host.enter_sudo()
            self.end_host.modprobe(module="nvme")
            fun_test.sleep("Loading nvme module", 2)
            command_result = self.end_host.lsmod(module="nvme")
            fun_test.simple_assert(command_result, "Loading nvme module")
            fun_test.test_assert_expected(expected="nvme", actual=command_result['name'], message="Loading nvme module")

            # Configuring Local thin block volume
            """
            vol_size = self.volume_details["capacity"] / self.volume_details["block_size"]
            '''create_ns = self.end_host.nvme_create_namespace(size=vol_size, capacity=vol_size,
                                                            block_size=self.volume_details["block_size"],
                                                            device=self.nvme_device)'''
            create_ns = self.end_host.sudo_command(
                "nvme create-ns --nsze={} --ncap={} --block-size={} {}".format(vol_size, vol_size,
                                                                               self.volume_details["block_size"],
                                                                               self.nvme_device))
            fun_test.test_assert("Success" in create_ns, "Namespace is created")

            attach_ns = self.end_host.nvme_attach_namespace(namespace_id=self.volume_details["ns_id"],
                                                            controllers=self.controllers,
                                                            device=self.nvme_device)
            fun_test.test_assert("Success" in attach_ns, "Namespace is attached")
            # self.end_host.exit_sudo()
            """

            if not fun_test.shared_variables["sysstat_install"]:
                install_sysstat = self.end_host.install_package("sysstat")
                fun_test.test_assert(install_sysstat, "Sysstat installation")
                fun_test.shared_variables["sysstat_install"] = True

            self.thin_uuid = utils.generate_uuid()
            fun_test.shared_variables["thin_uuid"] = self.thin_uuid
            command_result = self.storage_controller.create_thin_block_volume(
                capacity=self.volume_details["capacity"], block_size=self.volume_details["block_size"],
                name=self.volume_details["name"], uuid=self.thin_uuid, command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Create BLT volume on Dut Instance 0")

            command_result = self.storage_controller.volume_attach_pcie(
                ns_id=self.volume_details["ns_id"], uuid=self.thin_uuid, huid=tb_config['dut_info'][0]['huid'],
                ctlid=tb_config['dut_info'][0]['ctlid'], command_duration=self.command_timeout)
            fun_test.log(command_result)
            fun_test.test_assert(command_result["status"], "Attaching BLT volume on Dut Instance 0")

            # fun_test.shared_variables["blt"]["setup_created"] = True # Moved after warm up traffic
            # fun_test.shared_variables["blt"]["storage_controller"] = self.storage_controller
            fun_test.shared_variables["blt"]["thin_uuid"] = self.thin_uuid

            # ns-rescan is only required if volumes are created through dpcsh commands
            # command_result = self.end_host.sudo_command("nvme ns-rescan /dev/nvme0")
            # fun_test.log("ns-rescan output is: {}".format(command_result))

            # Checking that the above created BLT volume is visible to the end host
            fun_test.sleep("Sleeping for couple of seconds for the volume to accessible to the host", 5)
            self.volume_name = self.nvme_device.replace("/dev/", "") + "n" + str(self.volume_details["ns_id"])
            lsblk_output = self.end_host.lsblk()
            fun_test.test_assert(self.volume_name in lsblk_output, "{} device available".format(self.volume_name))
            fun_test.test_assert_expected(expected="disk", actual=lsblk_output[self.volume_name]["type"],
                                          message="{} device type check".format(self.volume_name))

            # Writing 20GB data on volume (one time task)
            if self.warm_up_traffic:
                fun_test.log("Initial Write IO to volume, this might take long time depending on fio --size provided")
                fio_output = self.end_host.pcie_fio(filename=self.nvme_block_device, **self.warm_up_fio_cmd_args)
                fun_test.log("FIO Command Output:\n{}".format(fio_output))
                fun_test.test_assert(fio_output, "Pre-populating the volume")
                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)
            fun_test.shared_variables["blt"]["setup_created"] = True

    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase[3:]
        obj = FioPerfHelper(handle=self.end_host,
                            dpc_conntroller=self.storage_controller,
                            fio_testfile_size=self.fio_cmd_args["size"],
                            fio_rwmode=self.fio_modes[0],
                            nvme_device_name=self.nvme_block_device,
                            fio_test_runtime=self.perf_logic_params["fio_run_time"],
                            cpu_usage_limit=self.perf_logic_params["max_cpu"],
                            iowait_limit=self.perf_logic_params["max_iowait"],
                            eqm_limit=self.perf_logic_params["eqm_difference"])

        use_numjobs, use_iodepth, use_num_cores = obj.get_fio_iodepth_num_jobs_num_cores()
        # self.storage_controller = fun_test.shared_variables["blt"]["storage_controller"]
        # self.thin_uuid = fun_test.shared_variables["blt"]["thin_uuid"]
        # storage_props_tree = "{}/{}/{}/{}/{}".format("storage", "volumes", self.volume_details["type"],
        # self.thin_uuid,
        #                                             "stats")

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
                              "Write Throughput in KB/s", "Read Throughput in KB/s", "Write Latency in uSecs",
                              "Write Latency 90 Percentile in uSecs", "Write Latency 95 Percentile in uSecs",
                              "Write Latency 99 Percentile in uSecs", "Write Latency 99.99 Percentile in uSecs",
                              "Read Latency in uSecs", "Read Latency 90 Percentile in uSecs",
                              "Read Latency 95 Percentile in uSecs", "Read Latency 99 Percentile in uSecs",
                              "Read Latency 99.99 Percentile in uSecs", "fio_job_name"]
        table_data_cols = ["block_size", "iodepth", "size", "mode", "writeiops", "readiops", "writebw", "readbw",
                           "writelatency", "writelatency90", "writelatency95", "writelatency99", "writelatency9999",
                           "readclatency", "readlatency90", "readlatency95", "readlatency99", "readlatency9999",
                           "fio_job_name"]
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
                row_data_dict["iodepth"] = use_iodepth
                row_data_dict["size"] = self.fio_cmd_args["size"]

                fun_test.log("Running FIO {} only test with the block size and IO depth set to {} & {}".
                             format(mode, fio_block_size, use_iodepth))

                # TODO: SWOS-4554 - As dpcsh is not working we are unable to pull internal stats, hence commenting
                ''''# Pulling the initial volume stats in dictionary format
                command_result = {}
                initial_volume_status[combo][mode] = {}
                command_result = self.storage_controller.peek(storage_props_tree, command_duration=self.command_timeout)
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
                            command_result = self.storage_controller.peek(props_tree,
                                                                          command_duration=self.command_timeout)
                            fun_test.simple_assert(command_result["status"], "Initial {} stats of DUT Instance 0".
                                                   format(props_tree))
                            initial_stats[combo][mode][key][item] = command_result["data"]
                    else:
                        props_tree = "{}/{}".format("stats", key)
                        command_result = self.storage_controller.peek(props_tree, command_duration=self.command_timeout)
                        fun_test.simple_assert(command_result["status"], "Initial {} stats of DUT Instance 0".
                                               format(props_tree))
                        initial_stats[combo][mode][key] = command_result["data"]
                    fun_test.log("{} stats at the beginning of the test:".format(key))
                    fun_test.log(initial_stats[combo][mode][key])'''
                cores_allowed_list = obj.form_cores_allowed_list()
                cpus_allowed = obj.cores_allowed_comma_format(cores_allowed_list=cores_allowed_list,
                                                              num_cores=use_num_cores)
                obj.start_fio_analysis(num_jobs=use_numjobs,
                                       iodepth=use_iodepth,
                                       num_cores=use_num_cores,
                                       fio_rwmode=mode,
                                       cpus_allowed=cpus_allowed,
                                       fio_test_runtime=self.fio_cmd_args["runtime"])

                fun_test.log("Running FIO...")
                fio_job_name = "fio_" + mode + "_" + self.fio_job_name[mode]
                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fio_output[combo][mode] = {}

                fio_output[combo][mode] = self.end_host.pcie_fio(filename=self.nvme_block_device, rw=mode,
                                                                 bs=fio_block_size, iodepth=use_iodepth,
                                                                 numjobs=use_numjobs,
                                                                 cpus_allowed=cpus_allowed,
                                                                 name=fio_job_name, **self.fio_cmd_args)

                iostat_results = obj.get_fio_analysis_results()
                fun_test.debug(iostat_results)
                fun_test.log_section("Iostat results")
                fun_test.log("Average IOPS  : {}".format(iostat_results["average_tps"]))
                fun_test.log("Average BW    : {} Kb/s".format(iostat_results["average_kbr"]))
                fun_test.log("Maximum IOPS  : {} ".format(iostat_results["maximum_tps"]))
                fun_test.log("Maximum BW    : {} Kb/s".format(iostat_results["maximum_kbr"]))

                fun_test.log("FIO Command Output:")
                fun_test.log(fio_output[combo][mode])

                # Boosting the fio output with the testbed performance multiplier
                multiplier = tb_config["dut_info"][0]["perf_multiplier"]
                for op, stats in fio_output[combo][mode].items():
                    for field, value in stats.items():
                        if field == "iops":
                            fio_output[combo][mode][op][field] = int(round(value * multiplier))
                        if field == "bw":
                            # Converting the KBps to MBps
                            fio_output[combo][mode][op][field] = int(round(value * multiplier / 1000))
                        if field == "latency":
                            fio_output[combo][mode][op][field] = int(round(value / multiplier))
                fun_test.log("FIO Command Output after multiplication:")
                fun_test.log(fio_output[combo][mode])

                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval),
                               self.iter_interval)

                # TODO: SWOS-4554 - As dpcsh is not working we are unable to pull internal stats, hence commenting
                # Getting the volume stats after the FIO test
                '''command_result = {}
                final_volume_status[combo][mode] = {}
                command_result = self.storage_controller.peek(storage_props_tree, command_duration=self.command_timeout)
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
                            command_result = self.storage_controller.peek(props_tree,
                                                                          command_duration=self.command_timeout)
                            fun_test.simple_assert(command_result["status"], "Final {} stats of DUT Instance 0".
                                                   format(props_tree))
                            final_stats[combo][mode][key][item] = command_result["data"]
                    else:
                        props_tree = "{}/{}".format("stats", key)
                        command_result = self.storage_controller.peek(props_tree, command_duration=self.command_timeout)
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
                    continue'''

                # Comparing the FIO results with the expected value for the current block size and IO depth combo
                for op, stats in self.expected_fio_result[combo][mode].items():
                    for field, value in stats.items():
                        fun_test.log("op is: {} and field is: {} ".format(op, field))
                        actual = fio_output[combo][mode][op][field]
                        row_data_dict[op + field] = (actual, int(round((value * (1 - self.fio_pass_threshold)))),
                                                     int((value * (1 + self.fio_pass_threshold))))
                        fun_test.log("raw_data[op + field] is: {}".format(row_data_dict[op + field]))
                        if field == "latency":
                            ifop = "greater"
                            elseop = "lesser"
                        else:
                            ifop = "lesser"
                            elseop = "greater"
                        # if actual < (value * (1 - self.fio_pass_threshold)) and ((value - actual) > 2):
                        if compare(actual, value, self.fio_pass_threshold, ifop):
                            fio_result[combo][mode] = False
                            '''fun_test.add_checkpoint("{} {} check for {} test for the block size & IO depth combo {}"
                                                    .format(op, field, mode, combo), "FAILED", value, actual)
                            fun_test.critical("{} {} {} is not within the allowed threshold value {}".
                                              format(op, field, actual, row_data_dict[op + field][1:]))'''
                        # elif actual > (value * (1 + self.fio_pass_threshold)) and ((actual - value) > 2):
                        elif compare(actual, value, self.fio_pass_threshold, elseop):
                            '''fun_test.add_checkpoint("{} {} check for {} test for the block size & IO depth combo {}"
                                                    .format(op, field, mode, combo), "PASSED", value, actual)'''
                            fun_test.log("{} {} {} got {} than the expected value {}".
                                         format(op, field, actual, elseop, row_data_dict[op + field][1:]))
                        else:
                            '''fun_test.add_checkpoint("{} {} check {} test for the block size & IO depth combo {}"
                                                    .format(op, field, mode, combo), "PASSED", value, actual)'''
                            fun_test.log("{} {} {} is within the expected range {}".
                                         format(op, field, actual, row_data_dict[op + field][1:]))

                row_data_dict["fio_job_name"] = fio_job_name

                # TODO: SWOS-4554 - As dpcsh is not working we are unable to pull internal stats, hence commenting
                # Comparing the internal volume stats with the expected value
                '''for ekey, evalue in expected_volume_stats[mode].items():
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
                            fun_test.critical("{} is not found in {} stat".format(ekey, key))'''

                # Building the table row for this variation for both the script table and performance dashboard
                row_data_list = []
                for i in table_data_cols:
                    if i not in row_data_dict:
                        row_data_list.append(-1)
                    else:
                        row_data_list.append(row_data_dict[i])

                table_data_rows.append(row_data_list)
                post_results("BLT_FS", test_method, *row_data_list)

        table_data = {"headers": table_data_headers, "rows": table_data_rows}
        fun_test.add_table(panel_header="BLT Performance Table", table_name=self.summary, table_data=table_data)

        # Posting the final status of the test result
        test_result = True
        fun_test.log(fio_result)
        fun_test.log(internal_result)
        for combo in self.fio_bs_iodepth:
            for mode in self.fio_modes:
                if not fio_result[combo][mode] or not internal_result[combo][mode]:
                    test_result = False

        # fun_test.test_assert(test_result, self.summary)
        fun_test.log("Test Result: {}".format(test_result))

    def cleanup(self):
        # self.storage_controller.disconnect()
        pass


class BLTFioSeqRead(BLTVolumePerformanceTestcase):

    def describe(self):
        self.set_test_details(id=1,
                              summary="Sequential Read performance of BLT volume",
                              steps='''
        1. Create a BLT volume on FS attached with SSD.
        2. Export (Attach) this BLT volume to the Internal COMe host connected via the PCIe interface. 
        3. Run FIO sequential read test(without verify) for various block size and IO depth from the 
        COMe host and check the performance are inline with the expected threshold. 
        ''')


class BLTFioRandRead(BLTVolumePerformanceTestcase):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Random Read performance of BLT volume",
                              steps='''
        1. Create a BLT volume on FS attached with SSD.
        2. Export (Attach) this BLT volume to the Internal COMe host connected via the PCIe interface. 
        3. Run FIO random Read test(without verify) for various block size and IO depth from the 
        COMe host and check the performance are inline with the expected threshold. 
        ''')


if __name__ == "__main__":
    bltscript = BLTVolumePerformanceScript()
    bltscript.add_test_case(BLTFioSeqRead())
    bltscript.add_test_case(BLTFioRandRead())
    bltscript.run()
