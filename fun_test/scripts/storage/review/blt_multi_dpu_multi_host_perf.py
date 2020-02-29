from lib.system.fun_test import *
fun_test.enable_storage_api()
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_operations_template import BltVolumeOperationsTemplate
from swagger_client.models.volume_types import VolumeTypes
from lib.system import utils
from lib.templates.storage.storage_fs_template import *
from scripts.storage.storage_helper import *
from scripts.networking.helper import *
from lib.templates.storage.storage_controller_api import *
import copy


class BringupSetup(FunTestScript):
    topology = None
    testbed_type = fun_test.get_job_environment_variable("test_bed_type")

    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. Bringup FS1600 
        2. Configure Linux Host instance and make it available for test case
        """)

    def setup(self):
        job_inputs = {}
        job_inputs = fun_test.get_job_inputs()

        already_deployed = False
        if "already_deployed" in job_inputs:
            already_deployed = job_inputs["already_deployed"]
        format_drives = True
        if "format_drives" in job_inputs:
            format_drives = job_inputs["format_drives"]

        num_f1 = 2
        dpu_indexes = [x for x in range(num_f1)]
        fun_test.shared_variables["num_f1"] = num_f1

        topology_helper = TopologyHelper()
        self.topology = topology_helper.deploy(already_deployed=already_deployed)
        fun_test.test_assert(self.topology, "Topology deployed")
        fun_test.shared_variables["topology"] = self.topology

        self.sc_template = BltVolumeOperationsTemplate(topology=self.topology)
        self.sc_template.initialize(already_deployed=already_deployed, dpu_indexes=dpu_indexes,
                                    format_drives=format_drives)
        fun_test.shared_variables["storage_controller_template"] = self.sc_template

        # Below lines are needed so that we create/attach volumes only once and other testcases use the same volumes
        fun_test.shared_variables["blt"] = {}
        fun_test.shared_variables["blt"]["setup_created"] = False
        fun_test.shared_variables["blt"]["warmup_done"] = False

    def cleanup(self):
        self.sc_template.cleanup()
        self.topology.cleanup()


class MultiHostFioRandRead(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              test_rail_case_ids=["C37018"],
                              summary="Random read performance for muiltple hosts on TCP "
                                      "with different levels of numjobs & iodepth & block size 4K",
                              steps='''
        1. Create 24 BLT volumes across both DPU
        2. Create a storage controller for TCP and attach above volumes to this controller   
        3. Connect to this volume from remote host
        4. Run the FIO Random read test(without verify) for various block size and IO depth from the 
        remote host and check the performance are inline with the expected threshold. 
        ''')

    def setup(self):
        fun_test.shared_variables["fio"] = {}
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

        # Setting the list of numjobs and IO depth combo
        if 'fio_jobs_iodepth' not in benchmark_dict[testcase] or not benchmark_dict[testcase]['fio_jobs_iodepth']:
            benchmark_parsing = False
            fun_test.critical("Numjobs and IO depth combo to be used for this {} testcase is not available in "
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
        elif "fio_jobs_iodepth" in benchmark_dict[testcase]:
            if len(self.fio_jobs_iodepth) != len(self.expected_fio_result.keys()):
                benchmark_parsing = False
                fun_test.critical("Mismatch in numjobs and IO depth combo and its benchmarking results")

        if 'fio_pass_threshold' not in benchmark_dict[testcase]:
            self.fio_pass_threshold = .05
            fun_test.log("Setting passing threshold to {} for this {} testcase, because its not set in the {} file".
                         format(self.fio_pass_threshold, testcase, benchmark_file))

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 24
        if not hasattr(self, "blt_count"):
            self.blt_count = 24

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))
        fun_test.log("Block size and IO depth combo going to be used for this {} testcase: {}".
                     format(testcase, self.fio_jobs_iodepth))
        fun_test.log("Benchmarking results going to be used for this {} testcase: \n{}".
                     format(testcase, self.expected_fio_result))
        # End of benchmarking json file parsing

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        fun_test.log("Provided job inputs: {}".format(job_inputs))
        if "blt_count" in job_inputs:
            self.blt_count = job_inputs["blt_count"]
        if "capacity" in job_inputs:
            self.blt_details["capacity"] = job_inputs["capacity"]
        if "nvme_io_queues" in job_inputs:
            self.nvme_io_queues = job_inputs["nvme_io_queues"]
        if "warm_up_traffic" in job_inputs:
            self.warm_up_traffic = job_inputs["warm_up_traffic"]
        if "runtime" in job_inputs:
            self.fio_cmd_args["runtime"] = job_inputs["runtime"]
            self.fio_cmd_args["timeout"] = self.fio_cmd_args["runtime"] + 15
        if "full_runtime" in job_inputs:
            self.fio_full_run_time = job_inputs["full_runtime"]
            self.fio_full_run_timeout = self.fio_full_run_time + 15
        if "post_results" in job_inputs:
            self.post_results = job_inputs["post_results"]
        else:
            self.post_results = False
        if "csi_perf_iodepth" in job_inputs:
            self.csi_perf_iodepth = job_inputs["csi_perf_iodepth"]
            self.full_run_iodepth = self.csi_perf_iodepth
        if not isinstance(self.csi_perf_iodepth, list):
            self.csi_perf_iodepth = [self.csi_perf_iodepth]
            self.full_run_iodepth = self.csi_perf_iodepth

        if (not fun_test.shared_variables["blt"]["setup_created"]):

            self.topology = fun_test.shared_variables["topology"]
            self.sc_template = fun_test.shared_variables["storage_controller_template"]

            fs_obj_list = []
            for dut_index in self.topology.get_available_duts().keys():
                fs_obj = self.topology.get_dut_instance(index=dut_index)
                fs_obj_list.append(fs_obj)
            fs_obj = fs_obj_list[0]
            self.sc_dpcsh_obj_f1_0 = fs_obj.get_storage_controller(f1_index=0)
            self.sc_dpcsh_obj_f1_1 = fs_obj.get_storage_controller(f1_index=1)
            self.sc_dpcsh_objs = [self.sc_dpcsh_obj_f1_0, self.sc_dpcsh_obj_f1_1]
            self.hosts = self.topology.get_available_host_instances()

            # Finding the usable capacity of the drives which will be used as the BLT volume capacity, in case
            # the capacity is not overridden while starting the script
            min_drive_capacity_f1_0 = find_min_drive_capacity(self.sc_dpcsh_obj_f1_0)
            min_drive_capacity_f1_1 = find_min_drive_capacity(self.sc_dpcsh_obj_f1_1)
            min_drive_capacity = min_drive_capacity_f1_0 if \
                min_drive_capacity_f1_1 >= min_drive_capacity_f1_0 else min_drive_capacity_f1_1
            if min_drive_capacity:
                self.blt_details["capacity"] = min_drive_capacity
                # Reducing the volume capacity by drive margin as a workaround for the bug SWOS-6862
                self.blt_details["capacity"] -= self.drive_margin
            else:
                fun_test.critical("Unable to find the drive with minimum capacity...So going to use the BLT capacity"
                                  "given in the script config file or capacity passed at the runtime...")

            if "capacity" in job_inputs:
                fun_test.critical("Original Volume size {} is overriden by the size {} given while running the "
                                  "script".format(self.blt_details["capacity"], job_inputs["capacity"]))
                self.blt_details["capacity"] = job_inputs["capacity"]

            self.create_volume_list = []
            f1_0_volume_list = []
            f1_1_volume_list = []
            f1_0_drive_id_list = []
            f1_1_drive_id_list = []

            use_unique_drives = True
            if "use_unique_drives" in job_inputs:
                use_unique_drives = job_inputs["use_unique_drives"]
            fun_test.add_checkpoint(
                checkpoint="Check if volumes are to be created in unique drives:{}".format(str(use_unique_drives)))

            for i in range(self.blt_count):
                suffix = utils.generate_uuid(length=4)
                name = "blt_vol_{}_{}".format(suffix, i + 1)
                body_volume_intent_create = BodyVolumeIntentCreate(name=name,
                                                                   vol_type=self.sc_template.vol_type,
                                                                   capacity=self.blt_details["capacity"],
                                                                   compression_effort=self.blt_details["compression_effort"],
                                                                   encrypt=self.blt_details["encrypt"],
                                                                   data_protection={})

                vol_uuid_list = self.sc_template.create_volume(fs_obj=fs_obj_list,
                                                               body_volume_intent_create=
                                                               body_volume_intent_create)
                current_vol_uuid = vol_uuid_list[0]
                fun_test.test_assert(expression=vol_uuid_list,
                                     message="Created Volume {} Successfully".format(current_vol_uuid))

                # Check if drive id is unique
                current_dpu_index = 0
                current_vol_list = f1_0_volume_list
                current_drive_list = f1_0_drive_id_list
                props_tree = "{}/{}/{}".format("storage", "volumes", self.sc_template.vol_type)
                dpu_op = self.sc_dpcsh_obj_f1_0.peek(props_tree=props_tree)
                if not current_vol_uuid in dpu_op["data"]:
                    current_dpu_index = 1
                    current_vol_list = f1_1_volume_list
                    current_drive_list = f1_1_drive_id_list
                    dpu_op = self.sc_dpcsh_obj_f1_1.peek(props_tree=props_tree)
                drive_id = dpu_op["data"][current_vol_uuid]["stats"]["drive_uuid"]
                if use_unique_drives:
                    fun_test.test_assert(drive_id not in current_drive_list,
                                         message="Volume with uuid {} id created on DPU:{} having unique drive "
                                                 "uuid {}".format(current_vol_uuid, current_dpu_index, drive_id))
                else:
                    fun_test.add_checkpoint(
                        checkpoint="Volume {} created on DPU:{} in drive with uuid {}".format(current_vol_uuid,
                                                                                              current_dpu_index,
                                                                                              drive_id))
                current_vol_list.append(current_vol_uuid)
                current_drive_list.append(drive_id)

            # Printing vol list from both F1s
            fun_test.log("Volumes created on DPU 0 are: {}".format(f1_0_volume_list))
            fun_test.log("Volumes created on DPU 1 are: {}".format(f1_1_volume_list))
            self.create_volume_list.extend(f1_0_volume_list)
            self.create_volume_list.extend(f1_1_volume_list)

            fun_test.test_assert_expected(expected=self.blt_count, actual=len(self.create_volume_list),
                                          message="Created {} number of volumes".format(self.blt_count))

            # Attach volumes to hosts and do nvme connect
            self.attach_vol_result = self.sc_template.attach_m_vol_n_host(fs_obj=fs_obj,
                                                                          volume_uuid_list=self.create_volume_list,
                                                                          host_obj_list=self.hosts,
                                                                          volume_is_shared=False,
                                                                          raw_api_call=self.raw_api_call,
                                                                          validate_nvme_connect=False)
            fun_test.test_assert(expression=self.attach_vol_result, message="Attached volumes to hosts")
            fun_test.shared_variables["volumes_list"] = self.create_volume_list
            fun_test.shared_variables["attach_volumes_list"] = self.attach_vol_result

            for host in self.hosts:
                host.nvme_connect_info = {}
                for result in self.attach_vol_result[host]:
                    if self.raw_api_call:
                        # fun_test.test_assert(expression=result["status"], message="Attach volume {} to {} host".
                        #                     format(i, host.name))
                        subsys_nqn = result["data"]["subsys_nqn"]
                        host_nqn = result["data"]["host_nqn"]
                        dataplane_ip = result["data"]["ip"]
                    else:
                        subsys_nqn = result.subsys_nqn
                        host_nqn = result.host_nqn
                        dataplane_ip = result.ip

                    if subsys_nqn not in host.nvme_connect_info:
                        host.nvme_connect_info[subsys_nqn] = []
                    host_nqn_ip = (host_nqn, dataplane_ip)
                    if host_nqn_ip not in host.nvme_connect_info[subsys_nqn]:
                        host.nvme_connect_info[subsys_nqn].append(host_nqn_ip)

            for host in self.hosts:
                for subsys_nqn in host.nvme_connect_info:
                    for host_nqn_ip in host.nvme_connect_info[subsys_nqn]:
                        host_nqn, dataplane_ip = host_nqn_ip
                        fun_test.test_assert(
                            expression=self.sc_template.nvme_connect_from_host(host_obj=host, subsys_nqn=subsys_nqn,
                                                                                host_nqn=host_nqn,
                                                                                dataplane_ip=dataplane_ip),
                            message="NVMe connect from host: {}".format(host.name))
                        nvme_filename = self.sc_template.get_host_nvme_device(host_obj=host, subsys_nqn=subsys_nqn)
                        fun_test.test_assert(expression=nvme_filename,
                                             message="Get NVMe drive from Host {} using lsblk".format(host.name))


            # Setting the fcp scheduler bandwidth
            for current_dpcsh_obj in self.sc_dpcsh_objs:
                if hasattr(self, "config_fcp_scheduler"):
                    set_fcp_scheduler(storage_controller=current_dpcsh_obj,
                                      config_fcp_scheduler=self.config_fcp_scheduler,
                                      command_timeout=5)

            # Fetch testcase numa cpus to be used
            numa_node_to_use = get_device_numa_node(self.hosts[0].instance, self.ethernet_adapter)
            if self.override_numa_node["override"]:
                numa_node_to_use = self.override_numa_node["override_node"]
            for host in self.hosts:
                if host.name.startswith("cab0"):
                    host.host_numa_cpus = ",".join(host.spec["cpus"]["numa_node_ranges"])
                else:
                    host.host_numa_cpus = host.spec["cpus"]["numa_node_ranges"][numa_node_to_use]

            # Check number of volumes and devices found from hosts
            for host, nvme_device_list in self.sc_template.host_nvme_device.iteritems():
                index = self.hosts.index(host)
                self.hosts[index].nvme_block_device_list = nvme_device_list
                fun_test.test_assert_expected(expected=len(self.attach_vol_result[host]),
                                              actual=len(self.hosts[index].nvme_block_device_list),
                                              message="Check number of nvme block devices found "
                                                      "on host {} matches with attached ".format(host.name))

            # Create fio filename on host for warmup
            for host in self.hosts:
                host.fio_filename = ":".join(host.nvme_block_device_list)

            fun_test.shared_variables["blt"]["setup_created"] = True
            fun_test.shared_variables["hosts"] = self.hosts
            fun_test.shared_variables["sc_dpcsh_objs"] = self.sc_dpcsh_objs

        if not fun_test.shared_variables["blt"]["warmup_done"]:
            thread_id = {}
            end_host_thread = {}

            # Pre-conditioning the volume (one time task)
            if self.warm_up_traffic:
                fio_output = {}
                for index, host in enumerate(self.hosts):
                    fun_test.log("Initial Write IO to volume, this might take long time depending on fio --size "
                                 "provided")
                    warm_up_fio_cmd_args = {}
                    jobs = ""
                    fio_output[index] = {}
                    end_host_thread[index] = host.instance.clone()
                    wait_time = len(self.hosts) - index
                    if "multiple_jobs" in self.warm_up_fio_cmd_args:
                        fio_cpus_allowed_args = " --cpus_allowed={}".format(host.host_numa_cpus)
                        for id, device in enumerate(host.nvme_block_device_list):
                            jobs += " --name=pre-cond-job-{} --filename={}".format(id + 1, device)
                        warm_up_fio_cmd_args["multiple_jobs"] = self.warm_up_fio_cmd_args["multiple_jobs"] + str(
                            fio_cpus_allowed_args) + str(jobs)
                        warm_up_fio_cmd_args["timeout"] = self.warm_up_fio_cmd_args["timeout"]
                        thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                         func=fio_parser,
                                                                         arg1=end_host_thread[index],
                                                                         host_index=index,
                                                                         filename="nofile",
                                                                         **warm_up_fio_cmd_args)
                    else:
                        # Adding the allowed CPUs into the fio warmup command
                        self.warm_up_fio_cmd_args["cpus_allowed"] = host.host_numa_cpus
                        filename = host.fio_filename
                        thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                         func=fio_parser,
                                                                         arg1=end_host_thread[index],
                                                                         host_index=index,
                                                                         filename=filename,
                                                                         **self.warm_up_fio_cmd_args)

                    fun_test.sleep("Fio threadzz", seconds=1)

                fun_test.sleep("Fio threads started", 10)
                try:
                    for index, host in enumerate(self.hosts):
                        fun_test.log("Joining fio thread {}".format(index))
                        fun_test.join_thread(fun_test_thread_id=thread_id[index])
                        fun_test.log("FIO Command Output:")
                        fun_test.log(fun_test.shared_variables["fio"][index])
                        fun_test.test_assert(fun_test.shared_variables["fio"][index], "Volume warmup on host {}".
                                             format(host.name))
                        fio_output[index] = {}
                        fio_output[index] = fun_test.shared_variables["fio"][index]
                        fun_test.shared_variables["blt"]["warmup_done"] = True
                except Exception as ex:
                    fun_test.log("Fio warmup failed")
                    fun_test.critical(str(ex))

                fun_test.sleep("Sleeping for 2 seconds before actual test", seconds=2)
            fun_test.test_assert(fun_test.shared_variables["blt"]["warmup_done"], message="Warmup done successfully")

    def run(self):
        testcase = self.__class__.__name__
        test_method = testcase[3:]
        self.test_mode = testcase[12:]

        # Going to run the FIO test for the block size and iodepth combo listed in fio_jobs_iodepth in both write only
        # & read only modes
        fio_result = {}
        fio_output = {}
        internal_result = {}

        table_data_headers = ["Block Size", "IO Depth", "Size", "Operation", "Write IOPS", "Read IOPS",
                              "Write Throughput in MB/s", "Read Throughput in MB/s", "Write Latency in uSecs",
                              "Write Latency 90 Percentile in uSecs", "Write Latency 95 Percentile in uSecs",
                              "Write Latency 99 Percentile in uSecs", "Write Latency 99.99 Percentile in uSecs",
                              "Read Latency in uSecs", "Read Latency 90 Percentile in uSecs",
                              "Read Latency 95 Percentile in uSecs", "Read Latency 99 Percentile in uSecs",
                              "Read Latency 99.99 Percentile in uSecs", "fio_job_name"]
        table_data_cols = ["block_size", "iodepth", "size", "mode", "writeiops", "readiops", "writebw", "readbw",
                           "writeclatency", "writelatency90", "writelatency95", "writelatency99", "writelatency9999",
                           "readclatency", "readlatency90", "readlatency95", "readlatency99", "readlatency9999",
                           "fio_job_name"]
        table_data_rows = []

        self.hosts = fun_test.shared_variables["hosts"]
        self.sc_dpcsh_objs = fun_test.shared_variables["sc_dpcsh_objs"]

        # Preparing the volume details list containing the list of dictionaries
        vol_details = []
        vol_group = {}
        vol_group[BltVolumeOperationsTemplate.vol_type] = fun_test.shared_variables["volumes_list"]
        vol_details.append(vol_group)

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        if "test_bs" in job_inputs:
            self.fio_bs = job_inputs["test_bs"]
        if "io_depth" in job_inputs:
            self.fio_jobs_iodepth = job_inputs["io_depth"]
            fun_test.log("Overrided fio_jobs_iodepth: {}".format(self.fio_jobs_iodepth))
        if "collect_stats" in job_inputs:
            self.collect_stats = job_inputs["collect_stats"]

        if not isinstance(self.fio_jobs_iodepth, list):
            self.fio_jobs_iodepth = [self.fio_jobs_iodepth]

        for combo in self.fio_jobs_iodepth:
            thread_id = {}
            end_host_thread = {}
            iostat_thread = {}
            final_fio_output = {}
            tmp = combo.split(',')
            fio_numjobs = tmp[0].strip('() ')
            fio_iodepth = tmp[1].strip('() ')

            if self.collect_stats:
                stats_obj_list = []
                for current_dpcsh_obj in self.sc_dpcsh_objs:
                    file_suffix = "{}_iodepth_{}_f1_{}.txt".format(self.test_mode, (int(fio_iodepth) * int(fio_numjobs)),
                                                                   self.sc_dpcsh_objs.index(current_dpcsh_obj))
                    for index, stat_detail in enumerate(self.stats_collect_details):
                        func = stat_detail.keys()[0]
                        self.stats_collect_details[index][func]["count"] = int(
                            self.fio_cmd_args["runtime"] / self.stats_collect_details[index][func]["interval"])
                        if func == "vol_stats":
                            self.stats_collect_details[index][func]["vol_details"] = vol_details
                    fun_test.log("Different stats collection thread details for the current IO depth {} before starting "
                                 "them:\n{}".format((int(fio_iodepth) * int(fio_numjobs)), self.stats_collect_details))
                    current_dpcsh_obj.verbose = False
                    stats_obj = CollectStats(current_dpcsh_obj)
                    stats_obj_list.append(stats_obj)
                    stats_obj.start(file_suffix, self.stats_collect_details)
                    fun_test.log("Different stats collection thread details for f1 {} the current IO depth {} "
                                 "after starting them:\n{}".format(self.sc_dpcsh_objs.index(current_dpcsh_obj),
                                                                   (int(fio_iodepth) * int(fio_numjobs)),
                                                                   self.stats_collect_details))

            for i, host in enumerate(self.hosts):
                fio_result[combo] = {}
                fio_output[combo] = {}
                final_fio_output[combo] = {}
                internal_result[combo] = {}

                end_host_thread[i] = host.instance.clone()

                for mode in self.fio_modes:
                    fio_block_size = self.fio_bs
                    fio_result[combo][mode] = True
                    internal_result[combo][mode] = True
                    row_data_dict = {}
                    row_data_dict["mode"] = mode
                    row_data_dict["block_size"] = fio_block_size
                    row_data_dict["iodepth"] = int(fio_iodepth) * int(fio_numjobs)
                    row_data_dict["num_jobs"] = fio_numjobs
                    file_size_in_gb = self.blt_details["capacity"] / 1073741824
                    row_data_dict["size"] = str(file_size_in_gb) + "GB"

                    fun_test.log("Running FIO {} only test for block size: {} using num_jobs: {}, IO depth: {}".
                                 format(mode, fio_block_size, fio_numjobs, fio_iodepth))

                    starting_core = int(host.host_numa_cpus.split(',')[0].split('-')[0]) + 1
                    if int(fio_numjobs) == 1:
                        cpus_allowed = str(starting_core)
                    elif int(fio_numjobs) == 4:
                        cpus_allowed = "{}-4".format(starting_core)
                    elif int(fio_numjobs) > 4:
                        cpus_allowed = "{}-{}".format(starting_core, host.host_numa_cpus[2:])

                    fun_test.log("Running FIO...")
                    fio_job_name = "fio_tcp_{}_blt_{}_{}_vol_{}".format(mode, fio_numjobs, fio_iodepth, self.blt_count)
                    # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                    fio_output[combo][mode] = {}
                    final_fio_output[combo][mode] = {}
                    wait_time = len(self.hosts) - i
                    # Deciding the FIO runtime based on the current IO depth
                    if row_data_dict["iodepth"] in self.full_run_iodepth:
                        fio_runtime = self.fio_full_run_time
                        fio_timeout = self.fio_full_run_timeout
                    else:
                        fio_runtime = self.fio_cmd_args["runtime"]
                        fio_timeout = self.fio_cmd_args["timeout"]
                    # Building the FIO command
                    fio_cmd_args = {}

                    runtime_global_args = " --runtime={} --cpus_allowed={} --bs={} --rw={} --numjobs={} --iodepth={}".\
                        format(fio_runtime, cpus_allowed, fio_block_size, mode, fio_numjobs, fio_iodepth)
                    jobs = ""
                    for id, device in enumerate(host.nvme_block_device_list):
                        jobs += " --name=vol{} --filename={}".format(id + 1, device)

                    fio_cmd_args["multiple_jobs"] = self.fio_cmd_args["multiple_jobs"] + runtime_global_args + jobs
                    fio_cmd_args["timeout"] = fio_timeout

                    thread_id[i] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                 func=fio_parser, arg1=end_host_thread[i],
                                                                 host_index=i, filename="nofile", **fio_cmd_args)

                    fun_test.sleep("Fio threadzz", seconds=1)

            fun_test.sleep("Fio threads started", 10)

            try:
                for i, host in enumerate(self.hosts):
                    fun_test.log("Joining fio thread {}".format(i))
                    fun_test.join_thread(fun_test_thread_id=thread_id[i])
                    fun_test.log("FIO Command Output:")
                    fun_test.log(fun_test.shared_variables["fio"][i])
                    fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                         "Fio {} test with IO depth {} in host {}".
                                         format(mode, int(fio_iodepth) * int(fio_numjobs), host.name))
                    fio_output[combo][mode][i] = {}
                    fio_output[combo][mode][i] = fun_test.shared_variables["fio"][i]
                final_fio_output[combo][mode] = fio_output[combo][mode][0]
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("FIO Command Output for volume {}:\n {}".format(i, fio_output[combo][mode][i]))
            finally:
                if self.collect_stats:
                    for stats_obj in stats_obj_list:
                        stats_obj.stop(self.stats_collect_details)
                        stats_obj.verbose = True

            if self.collect_stats:
                for stats_obj in stats_obj_list:
                    job_string = "{} - IO depth {} - F1 - {}".format(mode, row_data_dict["iodepth"],
                                                                     stats_obj_list.index(stats_obj))
                    stats_obj.populate_stats_to_file(self.stats_collect_details, job_string)

            fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval), self.iter_interval)

            for i in range(1, len(self.hosts)):
                fun_test.simple_assert(fio_output[combo][mode][i], "Fio threaded test")
                # Boosting the fio output with the testbed performance multiplier
                multiplier = 1
                for op, stats in self.expected_fio_result[combo][mode].items():
                    for field, value in stats.items():
                        if field == "latency":
                            fio_output[combo][mode][i][op][field] = \
                                int(round(fio_output[combo][mode][i][op][field] / multiplier))
                        final_fio_output[combo][mode][op][field] += fio_output[combo][mode][i][op][field]
                fun_test.sleep("Sleeping for {} seconds between iterations".format(self.iter_interval))

            # Comparing the FIO results with the expected value for the current block size and IO depth combo
            for op, stats in self.expected_fio_result[combo][mode].items():
                for field, value in stats.items():
                    # fun_test.log("op is: {} and field is: {} ".format(op, field))
                    actual = final_fio_output[combo][mode][op][field]
                    if "latency" in str(field):
                        actual = int(round(actual / self.blt_count))
                    row_data_dict[op + field] = (actual, int(round((value * (1 - self.fio_pass_threshold)))),
                                                 int((value * (1 + self.fio_pass_threshold))))

            row_data_dict["fio_job_name"] = fio_job_name

            # Building the table row for this variation for both the script table and performance dashboard
            row_data_list = []
            for i in table_data_cols:
                if i not in row_data_dict:
                    row_data_list.append(-1)
                else:
                    row_data_list.append(row_data_dict[i])

            table_data_list = copy.deepcopy(row_data_list)
            table_data_rows.append(table_data_list)

            row_data_list.insert(0, self.blt_count)
            row_data_list.insert(0, self.num_ssd)
            row_data_list.insert(0, get_data_collection_time())
            if self.post_results:
                fun_test.log("Posting results on dashboard")
                post_results("Multi_host_TCP", test_method, *row_data_list)

            table_data = {"headers": table_data_headers, "rows": table_data_rows}
            fun_test.add_table(panel_header="Multiple hosts over TCP Perf Table", table_name=self.summary,
                               table_data=table_data)

        # Posting the final status of the test result
        post_final_test_results(fio_result=fio_result, internal_result=internal_result,
                                fio_jobs_iodepth=self.fio_jobs_iodepth, fio_modes=self.fio_modes)

    def cleanup(self):
        pass


class MultiHostFioRandWrite(MultiHostFioRandRead):

    def describe(self):
        self.set_test_details(id=2,
                              summary="Random write performance for multiple hosts on TCP "
                                      "with different levels of numjobs & iodepth & block size 4K",
                              steps='''
        1. Create 1 BLT volumes on F1 attached
        2. Create a storage controller for TCP and attach above volumes to this controller   
        3. Connect to this volume from remote host
        4. Run the FIO Random write test(without verify) for various block size and IO depth from the 
        remote host and check the performance are inline with the expected threshold. 
        ''')

    def setup(self):
        super(MultiHostFioRandWrite, self).setup()

    def run(self):
        super(MultiHostFioRandWrite, self).run()

    def cleanup(self):
        super(MultiHostFioRandWrite, self).cleanup()


class PreCommitSanity(MultiHostFioRandRead):

    def describe(self):
        self.set_test_details(id=3,
                              summary="Pre-commit Sanity. Create BLT - Attach - IO (Write & Read) - Detach - Delete",
                              steps='''
        1. Bring-up F1 with latest image and configure Dataplane IP 
        2. Create 1 BLT volume with SC API
        2. Attach volume to Remote host
        4. Run the FIO Sequential write and Sequentail Read test from remote host
        5. Detach and Delete the BLT volume
        ''')

    def setup(self):
        super(PreCommitSanity, self).setup()

    def run(self):
        super(PreCommitSanity, self).run()

    def cleanup(self):
        super(PreCommitSanity, self).cleanup()


if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(MultiHostFioRandRead())
    setup_bringup.add_test_case(MultiHostFioRandWrite())
    setup_bringup.add_test_case(PreCommitSanity())
    setup_bringup.run()