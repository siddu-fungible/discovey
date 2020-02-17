from lib.system.fun_test import *
fun_test.enable_storage_api()
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_operations_template import EcVolumeOperationsTemplate
from lib.system import utils
from scripts.storage.storage_helper import *
from scripts.networking.helper import *
from collections import Counter
from lib.templates.storage.storage_controller_api import *
import copy


def get_dataplane_ip(self, dut_index, dpu_index):
    dataplane_ip = None
    dut = self.topology.get_dut(index=dut_index)
    bond_interfaces = dut.get_bond_interfaces(f1_index=dpu_index)
    first_bond_interface = bond_interfaces[0]
    dataplane_ip = str(first_bond_interface.ip).split('/')[0]
    return dataplane_ip


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

        dpu_index = None if not "num_f1" in job_inputs else range(job_inputs["num_f1"])

        # TODO: Check workload=storage in deploy(), set dut params
        topology_helper = TopologyHelper()
        self.topology = topology_helper.deploy(already_deployed=already_deployed)
        fun_test.test_assert(self.topology, "Topology deployed")
        fun_test.shared_variables["topology"] = self.topology

        fs_obj_list = []
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            fs_obj_list.append(fs_obj)
        fs_obj = fs_obj_list[0]

        self.sc_template = EcVolumeOperationsTemplate(topology=self.topology)
        self.sc_template.initialize(already_deployed=already_deployed, dpu_indexes=dpu_index)
        fun_test.shared_variables["storage_controller_template"] = self.sc_template

        # Below lines are needed so that we create/attach volumes only once and other testcases use the same volumes
        fun_test.shared_variables["ec"] = {}
        fun_test.shared_variables["ec"]["setup_created"] = False
        fun_test.shared_variables["ec"]["warmup_done"] = False
        fun_test.shared_variables["dpu_index"] = dpu_index

    def cleanup(self):
        self.sc_template.cleanup()
        self.topology.cleanup()


class RandReadWrite8kBlocks(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Inspur TC 8.11.1.1: 8k data block random read/write IOPS performance of Multiple"
                                      " EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using FIO
        8. Run the Performance for 8k transfer size Random read/write IOPS
        """)

    def setup(self):
        fun_test.shared_variables["fio"] = {}
        testcase = self.__class__.__name__
        self.sc_lock = Lock()

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

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))

        if not hasattr(self, "num_ssd"):
            self.num_ssd = 12

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}

        if "num_volumes" in job_inputs:
            self.ec_info["num_volumes"] = job_inputs["num_volumes"]
        if "vol_size" in job_inputs:
            self.ec_info["capacity"] = job_inputs["vol_size"]
        if "nvme_io_queues" in job_inputs:
            self.nvme_io_queues = job_inputs["nvme_io_queues"]
        if "warmup_bs" in job_inputs:
            self.warm_up_fio_cmd_args["bs"] = job_inputs["warmup_bs"]
        if "warmup_io_depth" in job_inputs:
            self.warm_up_fio_cmd_args["iodepth"] = job_inputs["warmup_io_depth"]
        if "warmup_size" in job_inputs:
            self.warm_up_fio_cmd_args["io_size"] = job_inputs["warmup_size"]
        if "csi_perf_iodepth" in job_inputs:
            self.csi_perf_iodepth = job_inputs["csi_perf_iodepth"]
            if not isinstance(self.csi_perf_iodepth, list):
                self.csi_perf_iodepth = [self.csi_perf_iodepth]
            self.full_run_iodepth = self.csi_perf_iodepth
        if "post_results" in job_inputs:
            self.post_results = job_inputs["post_results"]
        else:
            self.post_results = False

        if not fun_test.shared_variables["ec"]["setup_created"]:

            for k, v in self.ec_info.items():
                fun_test.log("{}: {}".format(k, v))

            self.topology = fun_test.shared_variables["topology"]
            self.sc_template = fun_test.shared_variables["storage_controller_template"]

            fs_obj_list = []
            for dut_index in self.topology.get_available_duts().keys():
                fs_obj = self.topology.get_dut_instance(index=dut_index)
                fs_obj_list.append(fs_obj)
            fs_obj = fs_obj_list[0]
            self.storage_controller_dpcsh_obj = fs_obj.get_storage_controller(f1_index=0)
            self.hosts = self.topology.get_available_host_instances()

            self.create_volume_list = []
            for i in range(self.ec_info["num_volumes"]):
                suffix = utils.generate_uuid(length=4)
                name = "ec_vol_{}_{}".format(suffix, i + 1)
                body_volume_intent_create = BodyVolumeIntentCreate(name=name,
                                                                   vol_type=self.sc_template.vol_type,
                                                                   capacity=self.ec_info["capacity"],
                                                                   compression_effort=self.ec_info["compression_effort"],
                                                                   encrypt=self.ec_info["encrypt"],
                                                                   data_protection=self.ec_info["data_protection"])

                vol_uuid_list = self.sc_template.create_volume(fs_obj=fs_obj_list,
                                                               body_volume_intent_create=
                                                               body_volume_intent_create)
                fun_test.test_assert(expression=vol_uuid_list,
                                     message="Created Volume {} Successful".format(vol_uuid_list[0]))
                self.create_volume_list.append(vol_uuid_list[0])

            fun_test.test_assert_expected(expected=self.ec_info["num_volumes"], actual=len(self.create_volume_list),
                                          message="Created {} number of volumes".format(self.ec_info["num_volumes"]))

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
                        nvme_filename = self.sc_template.get_host_nvme_device(host_obj=host)
                        fun_test.test_assert(expression=nvme_filename,
                                             message="Get NVMe drive from Host {} using lsblk".format(host.name))

            # Setting the fcp scheduler bandwidth
            if hasattr(self, "config_fcp_scheduler"):
                set_fcp_scheduler(storage_controller=self.storage_controller_dpcsh_obj,
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
            for host in self.hosts:
                host.nvme_block_device_list = []
                nvme_devices = self.sc_template.get_host_nvme_device(host_obj=host)

                if nvme_devices:
                    if isinstance(nvme_devices, list):
                        for nvme_device in nvme_devices:
                            current_device = "/dev/" + nvme_device
                            host.nvme_block_device_list.append(current_device)
                    else:
                        current_device = "/dev/" + nvme_devices
                        host.nvme_block_device_list.append(current_device)
                fun_test.test_assert_expected(expected=len(self.attach_vol_result[host]),
                                              actual=len(host.nvme_block_device_list),
                                              message="Check number of nvme block devices found "
                                                      "on host {} matches with attached ".format(host.name))

            # Create fio filename on host for warmup
            for host in self.hosts:
                host.fio_filename = ":".join(host.nvme_block_device_list)

            fun_test.shared_variables["ec"]["setup_created"] = True
            fun_test.shared_variables["hosts"] = self.hosts
            fun_test.shared_variables["dpcsh_obj"] = self.storage_controller_dpcsh_obj

        if not fun_test.shared_variables["ec"]["warmup_done"]:
            server_written_total_bytes = 0
            total_bytes_pushed_to_disk = 0
            try:
                self.sc_lock.acquire()
                initial_vol_stats = self.storage_controller_dpcsh_obj.peek(
                    props_tree="storage/volumes", legacy=False, chunk=8192, command_duration=self.command_timeout)
                self.sc_lock.release()
                fun_test.test_assert(initial_vol_stats["status"], "Volume stats collected before warmup")
                fun_test.debug("Volume stats before warmup: {}".format(initial_vol_stats))
            except Exception as ex:
                fun_test.critical(str(ex))

            dpu_index = fun_test.shared_variables["dpu_index"]
            if not dpu_index:
                dpu_index = [0]
            dataplane_ip = get_dataplane_ip(dut_index=0, dpu_index=dpu_index[0])

            # Continuous pings from host to F1 IP
            if getattr(self, "ping_during_warmup", False):
                ping_check_filename = {}
                for host in self.hosts:
                    host_handle = host.instance
                    ping_cmd = "sudo ping {} -i 1 -s 56".format(dataplane_ip)
                    self.ping_status_outfile = "/tmp/{}_ping_status_during_warmup.txt".format(host.name)
                    if host_handle.check_file_directory_exists(path=self.ping_status_outfile):
                        rm_file = host_handle.remove_file(file_name=self.ping_status_outfile)
                        fun_test.log("{} File removal status: {}".format(self.ping_status_outfile, rm_file))
                    self.ping_artifact_file = "{}_ping_status_during_warmup.txt".format(host.name)
                    ping_check_filename[host.name] = fun_test.get_test_case_artifact_file_name(
                        post_fix_name=self.ping_artifact_file)
                    ping_pid = host_handle.start_bg_process(command=ping_cmd, output_file=self.ping_status_outfile,
                                                            timeout=self.fio_cmd_args["timeout"])
                    host.warmup_ping_pid = ping_pid
                    fun_test.log("Ping started from {} to {}".format(host.name, dataplane_ip))

            if self.parallel_warm_up:
                host_clone = {}
                warmup_thread_id = {}
                actual_block_size = int(self.warm_up_fio_cmd_args["bs"].strip("k"))
                aligned_block_size = int((int(actual_block_size / self.num_hosts) + 3) / 4) * 4
                self.warm_up_fio_cmd_args["bs"] = str(aligned_block_size) + "k"
                for index, host in enumerate(self.hosts):
                    wait_time = self.num_hosts - index
                    host_clone[host.name] = host.instance.clone()
                    warmup_thread_id[index] = fun_test.execute_thread_after(
                        time_in_seconds=wait_time, func=fio_parser, arg1=host_clone[host.name], host_index=index,
                        filename=host.fio_filename,
                        cpus_allowed=host.host_numa_cpus, **self.warm_up_fio_cmd_args)

                    fun_test.log("Started FIO command to perform sequential write on {}".format(host.name))
                    fun_test.sleep("to start next thread", 1)

                fun_test.sleep("Fio threads started", 10)
                try:
                    for index, host in enumerate(self.hosts):
                        fun_test.log("Joining fio thread {}".format(index))
                        fun_test.join_thread(fun_test_thread_id=warmup_thread_id[index], sleep_time=1)
                        fun_test.log("FIO Command Output: \n{}".format(fun_test.shared_variables["fio"][index]))
                except Exception as ex:
                    fun_test.critical(str(ex))

                for index, host in enumerate(self.hosts):
                    fun_test.test_assert(fun_test.shared_variables["fio"][index], "Volume warmup on host {}".
                                         format(host.name))
                    fun_test.shared_variables["ec"][host.name]["warmup"] = True
                    server_written_total_bytes += fun_test.shared_variables["fio"][index]["write"]["io_bytes"]
            else:
                for index, host in enumerate(self.hosts):
                    host_handle = host.instance
                    fio_output = host_handle.pcie_fio(filename=host.fio_filename,
                                                      cpus_allowed=host.host_numa_cpus,
                                                      **self.warm_up_fio_cmd_args)
                    fun_test.log("FIO Command Output:\n{}".format(fio_output))
                    fun_test.test_assert(fio_output, "Volume warmup on host {}".format(host.name))
                    server_written_total_bytes += fio_output["write"]["io_bytes"]

            # Stopping ping status check on hosts
            if getattr(self, "ping_during_warmup", False):
                for index, host in enumerate(self.hosts):
                    # Killing with "SIGQUIT" to print the aggregated ping status
                    host_handle.kill_process(process_id=host.warmup_ping_pid,
                                             signal="SIGQUIT")
                    # Killing the process forcefully
                    host_handle.kill_process(process_id=host.warmup_ping_pid)
                    # Saving the ping status output to file
                    fun_test.scp(source_port=host_handle.ssh_port, source_username=host_handle.ssh_username,
                                 source_password=host_handle.ssh_password, source_ip=host_handle.host_ip,
                                 source_file_path=self.ping_status_outfile,
                                 target_file_path=ping_check_filename[host.name])
                    fun_test.add_auxillary_file(description="Ping_status_{}_to_{}".
                                                format(host.name, dataplane_ip),
                                                filename=ping_check_filename[host.name])

            fun_test.sleep("before actual test", self.iter_interval)
            fun_test.shared_variables["ec"]["warmup_done"] = True

            try:
                self.sc_lock.acquire()
                final_vol_stats = self.storage_controller_dpcsh_obj.peek(
                    props_tree="storage/volumes", legacy=False, chunk=8192, command_duration=self.command_timeout)
                self.sc_lock.release()
                fun_test.test_assert(final_vol_stats["status"], "Volume stats collected after warmup")
                fun_test.debug("Volume stats after warmup: {}".format(final_vol_stats))
            except Exception as ex:
                fun_test.critical(str(ex))

            fun_test.test_assert(fun_test.shared_variables["ec"]["warmup_done"], message="Warmup done successfully")

    def run(self):
        testcase = self.__class__.__name__
        test_method = testcase[4:]

        table_data_headers = ["Num Hosts", "Block Size", "IO Depth", "Size", "Operation", "Write IOPS", "Read IOPS",
                              "Write Throughput in KB/s", "Read Throughput in KB/s", "Write Latency in uSecs",
                              "Write Latency 90 Percentile in uSecs", "Write Latency 95 Percentile in uSecs",
                              "Write Latency 99 Percentile in uSecs", "Write Latency 99.99 Percentile in uSecs",
                              "Read Latency in uSecs", "Read Latency 90 Percentile in uSecs",
                              "Read Latency 95 Percentile in uSecs", "Read Latency 99 Percentile in uSecs",
                              "Read Latency 99.99 Percentile in uSecs", "fio_job_name"]
        table_data_cols = ["num_hosts", "block_size", "iodepth", "size", "mode", "writeiops", "readiops", "writebw",
                           "readbw", "writeclatency", "writelatency90", "writelatency95", "writelatency99",
                           "writelatency9999", "readclatency", "readlatency90", "readlatency95", "readlatency99",
                           "readlatency9999", "fio_job_name"]
        table_data_rows = []

        self.hosts = fun_test.shared_variables["hosts"]
        self.storage_controller_dpcsh_obj = fun_test.shared_variables["dpcsh_obj"]
        self.num_f1s = 2
        if fun_test.shared_variables["dpu_index"]:
            self.num_f1s = len(fun_test.shared_variables["dpu_index"])

        # Checking whether the job's inputs argument is having the list of io_depths to be used in this test.
        # If so, override the script default with the user provided config
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        if "io_depth" in job_inputs:
            self.fio_iodepth = job_inputs["io_depth"]

        if not isinstance(self.fio_iodepth, list):
            self.fio_iodepth = [self.fio_iodepth]

        # Going to run the FIO test for the block size and iodepth combo listed in fio_iodepth
        fio_result = {}
        fio_output = {}
        aggr_fio_output = {}

        start_stats = True

        for iodepth in self.fio_iodepth:
            fio_result[iodepth] = True
            fio_output[iodepth] = {}
            aggr_fio_output[iodepth] = {}
            fio_job_args = ""
            fio_cmd_args = {}
            mpstat_pid = {}
            mpstat_artifact_file = {}

            test_thread_id = {}
            host_clone = {}

            row_data_dict = {}
            size = (self.ec_info["capacity"] * self.ec_info["num_volumes"]) / (1024 ** 3)
            row_data_dict["size"] = str(size) + "G"
            self.num_hosts = len(self.hosts)
            row_data_dict["num_hosts"] = self.num_hosts

            # Deciding whether the fio command has to run for the entire volume size or for a certain period of time,
            # based on if the current IO depth is in self.full_run_iodepth
            if iodepth not in self.full_run_iodepth:
                if "runtime" not in self.fio_cmd_args["multiple_jobs"]:
                    self.fio_cmd_args["multiple_jobs"] += " --time_based --runtime={}".format(self.fio_runtime)
                    self.fio_cmd_args["timeout"] = self.fio_run_timeout
            else:
                self.fio_cmd_args["multiple_jobs"] = re.sub(r"--runtime=\d+", "", self.fio_cmd_args["multiple_jobs"])
                self.fio_cmd_args["multiple_jobs"] = re.sub(r"--time_based", "", self.fio_cmd_args["multiple_jobs"])
                self.fio_cmd_args["timeout"] = self.fio_size_timeout

            # Computing the interval and duration that the mpstat/vp_util stats needs to be collected
            if "runtime" not in self.fio_cmd_args:
                mpstat_count = self.fio_cmd_args["timeout"] / self.mpstat_args["interval"]
            elif "runtime" in self.fio_cmd_args and "ramp_time" in self.fio_cmd_args:
                mpstat_count = ((self.fio_cmd_args["runtime"] + self.fio_cmd_args["ramp_time"]) /
                                self.mpstat_args["interval"])
            elif "multiple_jobs" in self.fio_cmd_args:
                match = re.search("--ramp_time=(\d+).*--runtime=(\d+)|--runtime=(\d+).*--ramp_time=(\d+)",
                                  self.fio_cmd_args["multiple_jobs"])
                if match:
                    if match.group(1) != None:
                        ramp_time = match.group(1)
                    if match.group(2) != None:
                        runtime = match.group(2)
                    if match.group(3) != None:
                        runtime = match.group(3)
                    if match.group(4) != None:
                        ramp_time = match.group(4)
                    mpstat_count = (int(runtime) + int(ramp_time)) / self.mpstat_args["interval"]
                else:
                    start_stats = False
            else:
                start_stats = False

            if "bs" in self.fio_cmd_args:
                fio_block_size = self.fio_cmd_args["bs"]
            else:
                fio_block_size = "Mixed"

            if "rw" in self.fio_cmd_args:
                row_data_dict["mode"] = self.fio_cmd_args["rw"]
            else:
                row_data_dict["mode"] = "Combined"

            row_data_dict["block_size"] = fio_block_size

            for index, host in enumerate(self.hosts):
                fio_job_args = ""
                nvme_block_device_list = host.nvme_block_device_list
                host_numa_cpus = host.host_numa_cpus
                total_numa_cpus = get_total_numa_cpus(host_numa_cpus)
                fio_num_jobs = len(nvme_block_device_list)

                wait_time = self.num_hosts - index
                host_clone[host.name] = host.instance.clone()

                for vindex, volume_name in enumerate(nvme_block_device_list):
                    fio_job_args += " --name=job{} --filename={}".format(vindex, volume_name)

                if "multiple_jobs" in self.fio_cmd_args and self.fio_cmd_args["multiple_jobs"].count("name") > 0:
                    global_num_jobs = self.fio_cmd_args["multiple_jobs"].count("name")
                    fio_num_jobs = fio_num_jobs / global_num_jobs
                else:
                    if iodepth <= total_numa_cpus:
                        global_num_jobs = iodepth / len(nvme_block_device_list)
                        fio_iodepth = 1
                    else:
                        io_factor = 2
                        while True:
                            if (iodepth / io_factor) <= total_numa_cpus:
                                global_num_jobs = (iodepth / len(nvme_block_device_list)) / io_factor
                                fio_iodepth = io_factor
                                break
                            else:
                                io_factor += 1

                row_data_dict["iodepth"] = int(fio_iodepth) * int(global_num_jobs) * int(fio_num_jobs)
                fun_test.sleep("Waiting in between iterations", self.iter_interval)

                # Calling the mpstat method to collect the mpstats for the current iteration in all the hosts used in
                # the test
                mpstat_cpu_list = self.mpstat_args["cpu_list"]  # To collect mpstat for all CPU's: recommended
                fun_test.log("Collecting mpstat in {}".format(host.name))
                if start_stats:
                    mpstat_post_fix_name = "{}_mpstat_iodepth_{}.txt".format(host.name, row_data_dict["iodepth"])
                    mpstat_artifact_file[host.name] = fun_test.get_test_case_artifact_file_name(
                        post_fix_name=mpstat_post_fix_name)
                    mpstat_pid[host.name] = host.instance.mpstat(cpu_list=mpstat_cpu_list,
                                                               output_file=self.mpstat_args["output_file"],
                                                               interval=self.mpstat_args["interval"],
                                                               count=int(mpstat_count))
                else:
                    fun_test.critical("Not starting the mpstats collection because of lack of interval and count "
                                      "details")

                # Executing the FIO command for the current mode, parsing its out and saving it as dictionary
                fun_test.log("Running FIO {} test with the block size: {} and IO depth: {} Num jobs: {} for the EC".
                             format(row_data_dict["mode"], fio_block_size, fio_iodepth, fio_num_jobs * global_num_jobs))
                if hasattr(self, "hosting_f1_indexes") and self.hosting_f1_indexes != "all":
                    fio_job_name = "{}_iodepth_{}_f1_{}_vol_{}_hostf1_{}".format(self.fio_job_name,
                                                                                 row_data_dict["iodepth"],
                                                                                 self.num_f1s,
                                                                                 self.ec_info["num_volumes"],
                                                                                 len(self.hosting_f1_indexes))
                else:
                    fio_job_name = "{}_iodepth_{}_f1_{}_vol_{}".format(self.fio_job_name, row_data_dict["iodepth"],
                                                                       self.num_f1s, self.ec_info["num_volumes"])
                fun_test.log("fio_job_name used for current iteration: {}".format(fio_job_name))
                if "multiple_jobs" in self.fio_cmd_args:
                    fio_cmd_args["multiple_jobs"] = self.fio_cmd_args["multiple_jobs"].format(
                        host_numa_cpus, global_num_jobs, fio_iodepth, self.ec_info["capacity"] / global_num_jobs)
                    fio_cmd_args["multiple_jobs"] += fio_job_args
                    fun_test.log("Current FIO args to be used: {}".format(fio_cmd_args))
                    test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                          func=fio_parser,
                                                                          arg1=host_clone[host.name],
                                                                          host_index=index,
                                                                          filename="nofile",
                                                                          timeout=self.fio_cmd_args["timeout"],
                                                                          **fio_cmd_args)
                else:
                    test_thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                          func=fio_parser,
                                                                          arg1=host_clone[host.name],
                                                                          host_index=index,
                                                                          numjobs=fio_num_jobs,
                                                                          iodepth=fio_iodepth, name=fio_job_name,
                                                                          cpus_allowed=host_numa_cpus,
                                                                          **self.fio_cmd_args)
            # Waiting for all the FIO test threads to complete
            try:
                fun_test.log("Test Thread IDs: {}".format(test_thread_id))
                for index, host in enumerate(self.hosts):
                    fio_output[iodepth][host.name] = {}
                    fun_test.log("Joining fio thread {}".format(index))
                    fun_test.join_thread(fun_test_thread_id=test_thread_id[index], sleep_time=1)
                    fun_test.log("FIO Command Output from {}:\n {}".format(host.name,
                                                                           fun_test.shared_variables["fio"][index]))
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("FIO Command Output from {}:\n {}".format(host.name,
                                                                       fun_test.shared_variables["fio"][index]))

            # Summing up the FIO stats from all the hosts
            for index, host in enumerate(self.hosts):
                fun_test.test_assert(fun_test.shared_variables["fio"][index],
                                     "FIO {} test with the Block Size {} IO depth {} and Numjobs {} on {}"
                                     .format(row_data_dict["mode"], fio_block_size, fio_iodepth,
                                             fio_num_jobs * global_num_jobs, host.name))
                for op, stats in fun_test.shared_variables["fio"][index].items():
                    if op not in aggr_fio_output[iodepth]:
                        aggr_fio_output[iodepth][op] = {}
                    aggr_fio_output[iodepth][op] = Counter(aggr_fio_output[iodepth][op]) + \
                                                   Counter(fun_test.shared_variables["fio"][index][op])

            fun_test.log("Aggregated FIO Command Output:\n{}".format(aggr_fio_output[iodepth]))

            for op, stats in aggr_fio_output[iodepth].items():
                for field, value in stats.items():
                    if field == "iops":
                        aggr_fio_output[iodepth][op][field] = int(round(value))
                    if field == "bw":
                        # Converting the KBps to MBps
                        aggr_fio_output[iodepth][op][field] = int(round(value / 1000))
                    if "latency" in field:
                        aggr_fio_output[iodepth][op][field] = int(round(value) / self.num_hosts)
                    row_data_dict[op + field] = aggr_fio_output[iodepth][op][field]

            fun_test.log("Processed Aggregated FIO Command Output:\n{}".format(aggr_fio_output[iodepth]))

            if not aggr_fio_output[iodepth]:
                fio_result[iodepth] = False
                fun_test.critical("No output from FIO test, hence moving to the next variation")
                continue

            row_data_dict["fio_job_name"] = fio_job_name

            # Building the table raw for this variation
            row_data_list = []
            for i in table_data_cols:
                if i not in row_data_dict:
                    row_data_list.append(-1)
                else:
                    row_data_list.append(row_data_dict[i])

            table_data_rows.append(row_data_list)

            table_data_list = copy.deepcopy(row_data_list)
            table_data_rows.append(table_data_list)

            row_data_list.insert(0, self.ec_info["num_volumes"])
            row_data_list.insert(0, self.num_ssd)
            row_data_list.insert(0, get_data_collection_time())

            if self.post_results:
                fun_test.log("Posting results on dashboard")
                post_results("Inspur Performance Test", test_method, *row_data_list)

            table_data = {"headers": table_data_headers, "rows": table_data_rows}
            fun_test.add_table(panel_header="Performance Table", table_name=self.summary, table_data=table_data)

            # Checking if mpstat process is still running...If so killing it...
            for host in self.hosts:
                mpstat_pid_check = host.instance.get_process_id("mpstat")
                if mpstat_pid_check and int(mpstat_pid_check) == int(mpstat_pid[host.name]):
                    host.instance.kill_process(process_id=int(mpstat_pid_check))
                # Saving the mpstat output to the mpstat_artifact_file file
                fun_test.scp(source_port=host.instance.ssh_port, source_username=host.instance.ssh_username,
                             source_password=host.instance.ssh_password, source_ip=host.instance.host_ip,
                             source_file_path=self.mpstat_args["output_file"],
                             target_file_path=mpstat_artifact_file[host.name])
                fun_test.add_auxillary_file(description="Host {} CPU Usage - IO depth {}".
                                            format(host.name, row_data_dict["iodepth"]),
                                            filename=mpstat_artifact_file[host.name])

    def cleanup(self):
        pass


class RandRead8kBlocks(RandReadWrite8kBlocks):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Inspur TC 8.11.1.2: 8k data block random read IOPS performance of Multiple"
                                      " EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using FIO
        8. Run the Performance for 8k transfer size Random read IOPS
        """)

    def setup(self):
        super(RandRead8kBlocks, self).setup()

    def run(self):
        super(RandRead8kBlocks, self).run()

    def cleanup(self):
        super(RandRead8kBlocks, self).cleanup()


class RandWrite8kBlocks(RandReadWrite8kBlocks):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Inspur TC 8.11.1.3: 8k data block random write IOPS performance of Multiple"
                                      " EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using FIO
        8. Run the Performance for 8k transfer size Random write IOPS
        """)

    def setup(self):
        super(RandWrite8kBlocks, self).setup()

    def run(self):
        super(RandWrite8kBlocks, self).run()

    def cleanup(self):
        super(RandWrite8kBlocks, self).cleanup()


class SequentialReadWrite1024kBlocks(RandReadWrite8kBlocks):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Inspur TC 8.11.2: 1024k data block sequential write IOPS performance"
                                      "of Multiple EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using FIO
        8. Run the Performance for 1024k transfer size Sequential write IOPS
        """)

    def setup(self):
        super(SequentialReadWrite1024kBlocks, self).setup()

    def run(self):
        super(SequentialReadWrite1024kBlocks, self).run()

    def cleanup(self):
        super(SequentialReadWrite1024kBlocks, self).cleanup()


class MixedRandReadWriteIOPS(RandReadWrite8kBlocks):
    def describe(self):
        self.set_test_details(id=5,
                              summary="Inspur TC 8.11.3: Integrated model read/write IOPS performance of Multiple"
                                      " EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using FIO
        8. Run the Performance for Integrated Model read/write IOPS
        """)

    def setup(self):
        super(MixedRandReadWriteIOPS, self).setup()

    def run(self):
        super(MixedRandReadWriteIOPS, self).run()

    def cleanup(self):
        super(MixedRandReadWriteIOPS, self).cleanup()


class OLTPModelReadWriteIOPS(RandReadWrite8kBlocks):
    def describe(self):
        self.set_test_details(id=6,
                              summary="Inspur TC 8.11.4: OLTP Model read/read IOPS performance of Multiple EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using FIO
        8. Run the Performance for OLTP model read/write IOPS
        """)

    def setup(self):
        super(OLTPModelReadWriteIOPS, self).setup()

    def run(self):
        super(OLTPModelReadWriteIOPS, self).run()

    def cleanup(self):
        super(OLTPModelReadWriteIOPS, self).cleanup()


class OLAPModelReadWriteIOPS(RandReadWrite8kBlocks):
    def describe(self):
        self.set_test_details(id=7,
                              summary="Inspur TC 8.11.5: OLAP Model read/write IOPS performance of Multiple EC volume",
                              steps="""
        1. Bring up F1 in FS1600
        2. Bring up and configure Remote Host
        3. Create 6 BLT volumes on dut instance.
        4. Create a 4:2 EC volume on top of the 6 BLT volumes.
        5. Create a LS volume on top of the EC volume based on use_lsv config along with its associative journal volume.
        6. Export (Attach) the above EC or LS volume based on use_lsv config to the Remote Host 
        7. Run warm-up traffic using FIO
        8. Run the Performance for OLAP model Random read/write IOPS
        """)

    def setup(self):
        super(OLAPModelReadWriteIOPS, self).setup()

    def run(self):
        super(OLAPModelReadWriteIOPS, self).run()

    def cleanup(self):
        super(OLAPModelReadWriteIOPS, self).cleanup()


class RandReadWrite8kBlocksAfterReboot(RandReadWrite8kBlocks):
    def describe(self):
        self.set_test_details(id=8,
                              summary="Bundle sanity. Run fio random read after COMe reboot on the same EC vol attached",
                              steps='''
        1. Do fio warmup on EC/LSV volume.
        2. Run fio reads on the EC/LSV volume
        3. Reboot COMe.
        4. Check docker containers F1-0, F1-1 and run_sc.
        5. Run fio read from the host.
        6. Run fio writes from host
        7. Run fio read for writes in step6
        ''')

    def setup(self):
        super(RandReadWrite8kBlocksAfterReboot, self).setup()
        testcase = self.__class__.__name__
        benchmark_file = ""
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Benchmark file being used: {}".format(benchmark_file))

        benchmark_dict = {}
        benchmark_dict = utils.parse_file_to_json(benchmark_file)

        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)

    def run(self):
        fun_test.log("Running fio reads on EC/LSV before COMe reboot")
        super(RandReadWrite8kBlocksAfterReboot, self).run()

        # fun_test.log("Rebooting COMe")
        # self.post_results = False
        # self.fs = fun_test.shared_variables["fs_objs"]
        # self.come_obj = fun_test.shared_variables["come_obj"]
        # self.host_info = fun_test.shared_variables["host_info"]
        # self.f1_ips = fun_test.shared_variables["f1_ips"]
        #
        # total_reconnect_time = 600
        # add_on_time = 180
        # reboot_timer = FunTimer(max_time=total_reconnect_time + add_on_time)
        #
        # # Reset COMe
        # reset = self.fs[0].reset(hard=False)
        # fun_test.test_assert(reset, "COMe reset successfully done")
        #
        # # Ensure COMe is up
        # ensure_up = self.fs[0].ensure_is_up()
        # fun_test.test_assert(ensure_up, "Ensure COMe is up")
        #
        # # Ensure all containers are up
        # fs_obj = self.fs[0]
        # come = fs_obj.get_come()
        # containers_status = come.ensure_expected_containers_running()
        # fun_test.test_assert(containers_status, "All containers up")
        #
        # # Ensure API server is up
        # self.sc_api = StorageControllerApi(api_server_ip=come.host_ip)
        # fun_test.test_assert(ensure_api_server_is_up(self.sc_api, timeout=self.api_server_timeout),
        #                      "Ensure API server is up")
        #
        # fun_test.log("TOTAL TIME ELAPSED IN REBOOT IS {}".format(reboot_timer.elapsed_time()))
        #
        # volume_found = False
        # nvme_list_found = False
        # vol_uuid = fun_test.shared_variables["volume_uuid_list"][0]
        # host_handle = self.host_info[self.host_info.keys()[0]]['handle']
        # nvme_device = self.host_info[self.host_info.keys()[0]]["nvme_block_device_list"][0]
        # fun_test.log("Nvme device name is {}".format(nvme_device))
        # nvme_device_name = nvme_device.split("/")[-1]
        # docker_f1_handle = come.get_funcp_container(f1_index=0)
        # fun_test.log("Will look for nvme {} on host {}".format(nvme_device_name, host_handle))
        #
        # while not reboot_timer.is_expired():
        #     # Check whether EC vol is listed in storage/volumes
        #     vols = self.sc_api.get_volumes()
        #     if (vols['status'] and vols['data']) and not volume_found:
        #         if vol_uuid in vols['data'].keys():
        #             fun_test.log(vols)
        #             fun_test.test_assert(vols['data'][vol_uuid]['type'] == "durable volume",
        #                                  "EC/LSV Volume {} is persistent".format(vol_uuid))
        #             volume_found = True
        #     if volume_found:
        #         nvme_list_output = host_handle.sudo_command("nvme list")
        #         if nvme_device in nvme_list_output and "FS1600" in nvme_list_output:
        #             nvme_list_found = True
        #             break
        #     fun_test.log("Checking for routes on host and docker containers")
        #     fun_test.log("Routes from docker container {}".format(docker_f1_handle))
        #     docker_f1_handle.command("arp -n")
        #     docker_f1_handle.command("route -n")
        #     docker_f1_handle.command("ifconfig")
        #     fun_test.log("\nRoutes from host {}".format(host_handle))
        #     host_handle.command("arp -n")
        #     host_handle.command("route -n")
        #     host_handle.command("ifconfig")
        #     fun_test.sleep("Letting BLT volume {} be found".format(vol_uuid), seconds=10)
        #
        # if not nvme_list_found:
        #     fun_test.log("Printing dmesg from host {}".format(host_handle))
        #     host_handle.command("dmesg")
        # fun_test.test_assert(nvme_list_found, "Check nvme device {} is found on host {}".format(nvme_device_name,
        #                                                                                         host_handle))
        #
        # # Check host F1 connectivity
        # fun_test.log("Checking host F1 connectivity")
        # for ip in self.f1_ips:
        #     ping_status = host_handle.ping(dst=ip)
        #     if not ping_status:
        #         fun_test.log("Routes from docker container {}".format(docker_f1_handle))
        #         docker_f1_handle.command("arp -n")
        #         docker_f1_handle.command("route -n")
        #         docker_f1_handle.command("ifconfig")
        #         fun_test.log("\nRoutes from host {}".format(host_handle))
        #         host_handle.command("arp -n")
        #         host_handle.command("route -n")
        #         host_handle.command("ifconfig")
        #
        #     fun_test.simple_assert(ping_status, "Host {} is able to ping to bond interface IP {}".
        #                            format(host_handle.host_ip, ip))
        #
        # # Run fio
        # fun_test.log("Running fio reads on EC/LSV after COMe reboot")
        # super(RandReadWrite8kBlocksAfterReboot, self).run()
        #
        # self.fio_cmd_args["multiple_jobs"] = self.fio_cmd_args["multiple_jobs"].replace("--rw=read", "--rw=write")
        # self.fio_cmd_args["multiple_jobs"] = self.fio_cmd_args["multiple_jobs"].replace("--do_verify=1", "--do_verify=0")
        # fun_test.log("Running fio writes on EC/LSV after COMe reboot")
        # super(RandReadWrite8kBlocksAfterReboot, self).run()
        #
        # self.fio_cmd_args["multiple_jobs"] = self.fio_cmd_args["multiple_jobs"].replace("--rw=write", "--rw=read")
        # self.fio_cmd_args["multiple_jobs"] = self.fio_cmd_args["multiple_jobs"].replace("--do_verify=0", "--do_verify=1")
        # fun_test.log("Running fio reads on EC/LSV after COMe reboot")
        # super(RandReadWrite8kBlocksAfterReboot, self).run()


    def cleanup(self):
        super(RandReadWrite8kBlocksAfterReboot, self).cleanup()


if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(RandReadWrite8kBlocks())
    setup_bringup.add_test_case(RandRead8kBlocks())
    setup_bringup.add_test_case(MixedRandReadWriteIOPS())
    setup_bringup.add_test_case(SequentialReadWrite1024kBlocks())
    setup_bringup.add_test_case(RandWrite8kBlocks())
    setup_bringup.add_test_case(OLTPModelReadWriteIOPS())
    setup_bringup.add_test_case(OLAPModelReadWriteIOPS())
    setup_bringup.add_test_case(RandReadWrite8kBlocksAfterReboot())
    setup_bringup.run()