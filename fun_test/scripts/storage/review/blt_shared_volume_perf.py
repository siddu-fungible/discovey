from lib.system.fun_test import *
from lib.system import utils
fun_test.enable_storage_api()
from lib.system import utils
from lib.host.linux import Linux
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_operations_template import BltVolumeOperationsTemplate
from swagger_client.models.volume_types import VolumeTypes
from scripts.storage.storage_helper import *
import string, random,re,copy
from collections import OrderedDict, Counter


def fio_parser(arg1, host_index, **kwargs):
    fio_output = arg1.pcie_fio(**kwargs)
    fun_test.shared_variables["fio"][host_index] = fio_output
    fun_test.test_assert(fio_output, "Fio test for thread {}".format(host_index), ignore_on_success=True)
    arg1.disconnect()


class BringupSetup(FunTestScript):
    topology = None
    testbed_type = fun_test.get_job_environment_variable("test_bed_type")

    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. Bringup FS1600 
        2. Configure Linux Host instance and make it available for test case
        """)

    def setup(self):

        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        fun_test.log("Provided job inputs: {}".format(job_inputs))
        format_drives = True
        if "already_deployed" in job_inputs:
            self.already_deployed = job_inputs["already_deployed"]
        else:
            self.already_deployed = False
        if "format_drives" in job_inputs:
            format_drives = job_inputs["format_drives"]

        '''
        self = single_fs_setup(self, set_dataplane_ips=False)

        fun_test.shared_variables["topology"] = self.topology
        fun_test.shared_variables["fs_objs"] = self.fs_objs
        fun_test.shared_variables["come_obj"] = self.come_obj
        fun_test.shared_variables["f1_objs"] = self.f1_objs
        fun_test.shared_variables["sc_obj"] = self.sc_objs
        fun_test.shared_variables["f1_ips"] = self.f1_ips
        fun_test.shared_variables["host_info"] = self.host_info
        
        '''

        topology_helper = TopologyHelper()
        self.topology = topology_helper.deploy(already_deployed=self.already_deployed)
        fun_test.test_assert(self.topology, "Topology deployed")
        fun_test.shared_variables["topology"] = self.topology
        self.blt_template = BltVolumeOperationsTemplate(topology=self.topology)
        self.blt_template.initialize(dpu_indexes=[0], already_deployed=self.already_deployed,format_drives=format_drives)
        fun_test.shared_variables["blt_template"] = self.blt_template
        self.fs_obj_list = []
        for dut_index in self.topology.get_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            self.fs_obj_list.append(fs_obj)

        fun_test.shared_variables["fs_obj_list"] = self.fs_obj_list
        fs_obj = self.fs_obj_list[0]
        self.storage_controller_dpcsh_obj = fs_obj.get_storage_controller(f1_index=0)
        fun_test.shared_variables["dpcsh_obj"] = self.storage_controller_dpcsh_obj

        # self.fs_obj_list = fun_test.shared_variables["fs_obj_list"]

        '''
        fun_test.shared_variables["fs_obj_list"] = fs_obj_list
        hosts = self.topology.get_available_hosts()
        for host_id in hosts:
            host_obj = hosts[host_id]
            host_handle = host_obj.get_instance()
            nvme_list = self.storage_controller_template.get_nvme_namespaces(host_handle=host_handle)
            for ns in nvme_list:
                dev=ns[:-2]
                host_handle.sudo_command("nvme disconnect -d /dev/{}".format(dev))
        '''

    def cleanup(self):

        self.blt_template.cleanup()
        self.topology.cleanup()


class SharedVolumePerfTest(FunTestCase):

    def describe(self):

        self.set_test_details(id=1,
                              summary="Create Volume using API and run IO from host",
                              steps='''
                              1. Make sure API server is up and running
                              2. Create a Volume using API Call
                              3. Attach Volume to a remote host
                              4. Run FIO from host 
                              ''')

    def setup(self):

        testcase = self.__class__.__name__
        self.topology = fun_test.shared_variables["topology"]
        self.blt_template = fun_test.shared_variables["blt_template"]
        self.fs_obj_list = fun_test.shared_variables["fs_obj_list"]

        tc_config = True
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Benchmark file being used: {}".format(benchmark_file))

        tc_config = {}
        tc_config = utils.parse_file_to_json(benchmark_file)

        if testcase not in tc_config or not tc_config[testcase]:
            tc_config = False
            fun_test.critical("Benchmarking is not available for the current testcase {} in {} file".
                              format(testcase, benchmark_file))
            fun_test.test_assert(tc_config, "Parsing Benchmark json file for this {} testcase".format(testcase))
        fun_test.test_assert(tc_config, "Parsing Benchmark json file for this {} testcase".format(testcase))

        for k, v in tc_config[testcase].iteritems():
            setattr(self, k, v)

        job_inputs = fun_test.get_job_inputs()
        if "post_results" in job_inputs:
            self.post_results = job_inputs["post_results"]
        else:
            self.post_results = False
        if "capacity" in job_inputs:
            self.capacity = job_inputs["capacity"]
        if "blt_count" in job_inputs:
            self.blt_count = job_inputs["blt_count"]
        if "num_hosts" in job_inputs:
            self.num_hosts = job_inputs["num_hosts"]
        if "warmup_jobs" in job_inputs:
            self.warm_up_fio_cmd_args["multiple_jobs"] = self.warm_up_fio_cmd_args["multiple_jobs"]. \
                replace("numjobs=1", "numjobs={}".format(job_inputs["warmup_jobs"]))
        fun_test.log("Using the warm_up job value provided in the job inputs")
        fun_test.log(self.warm_up_fio_cmd_args["multiple_jobs"])
        if "warmup_bs" in job_inputs:
            self.warm_up_fio_cmd_args["multiple_jobs"] = self.warm_up_fio_cmd_args["multiple_jobs"]. \
                replace("bs=128k", "bs={}".format(job_inputs["warmup_bs"]))
        if "test_bs" in job_inputs:
            self.fio_bs = job_inputs["test_bs"]
        if "fio_modes" in job_inputs:
            self.fio_modes = job_inputs["fio_modes"]

        res = re.search('--numjobs=(\d+)', str(self.warm_up_fio_cmd_args["multiple_jobs"]))
        fun_test.log("num_jobs for warmup")
        fun_test.log(res.group(1))
        if int(res.group(1)) > 1:
            self.warm_up_fio_cmd_args["multiple_jobs"] += " --time_based --runtime={}". \
                format(int(self.warm_up_fio_cmd_args["timeout"]) - 60)
            fun_test.log("Time based fio when num_jobs > 1")
            fun_test.log(self.warm_up_fio_cmd_args["multiple_jobs"])

        """
        self.topology = fun_test.shared_variables["topology"]
        self.fs_objs = fun_test.shared_variables["fs_objs"]
        self.come_obj = fun_test.shared_variables["come_obj"]
        self.f1_objs = fun_test.shared_variables["f1_objs"]
        self.sc_objs = fun_test.shared_variables["sc_obj"]
        self.f1_ips = fun_test.shared_variables["f1_ips"]
        self.host_info = fun_test.shared_variables["host_info"]
        """

        self.vol_uuid_list = []
        fun_test.shared_variables["blt_count"] = self.blt_count
        vol_type = VolumeTypes().LOCAL_THIN

        self.hosts = self.topology.get_available_host_instances()

        # chars = string.ascii_uppercase + string.ascii_lowercase
        for i in range(self.blt_count):
            suffix = utils.generate_uuid(length=4)
            body_volume_intent_create = BodyVolumeIntentCreate(name=self.name + suffix + str(i), vol_type=vol_type,
                                                               capacity=self.capacity, compression_effort=False,
                                                               encrypt=False, data_protection={})
            vol_uuid = self.blt_template.create_volume(self.fs_obj_list, body_volume_intent_create)
            fun_test.test_assert(expression=vol_uuid[0], message="Create Volume Successful")
            self.vol_uuid_list.append(vol_uuid[0])

        fun_test.shared_variables["vol_uuid_list"] = self.vol_uuid_list
        for host in self.hosts:
            host.nvme_connect_info = {}

        attach_vol_result = {}
        for i in range(self.blt_count):
            attach_vol_result[i] = self.blt_template.attach_volume(self.fs_obj_list[0],
                                                                   self.vol_uuid_list[i],
                                                                   self.hosts,
                                                                   validate_nvme_connect=False,
                                                                   raw_api_call=self.raw_api_call)
            fun_test.simple_assert(expression=attach_vol_result[i], message="Attach Volume {} to {} hosts".
                                   format(i+1, len(self.hosts)))
            for j, result in enumerate(attach_vol_result[i]):
                host = self.hosts[j]
                if self.raw_api_call:
                    fun_test.test_assert(expression=result["status"], message="Attach volume {} to {} host".
                                         format(i+1, host.name))
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
                        expression=self.blt_template.nvme_connect_from_host(host_obj=host, subsys_nqn=subsys_nqn,
                                                                            host_nqn=host_nqn,
                                                                            dataplane_ip=dataplane_ip),
                        message="NVMe connect from host: {}".format(host.name))
                    nvme_filename = self.blt_template.get_host_nvme_device(host_obj=host, subsys_nqn=subsys_nqn)
                    fun_test.test_assert(expression=nvme_filename,
                                         message="Get NVMe drive from Host {} using lsblk".format(host.name))

        for host in self.hosts:
            host.num_volumes = self.blt_count

        # Populating the NVMe devices available to the hosts

        for host in self.hosts:
            host.nvme_block_device_list = []
            results = fetch_nvme_list(host.instance)
            host.nvme_block_device_list = results["nvme_device"].split(":")
            fun_test.test_assert_expected(expected=host.num_volumes,
                                          actual=len(host.nvme_block_device_list),
                                          message="Expected NVMe devices are available - {}".format(host.name))
            host.nvme_block_device_list.sort()
            host.fio_filename = ":".join(host.nvme_block_device_list)

        # Extracting the host CPUs
        # for host in self.hosts:
        #     host_handle = host.instance
        #     if host.name.startswith("cab0"):
        #         if self.override_numa_node["override"]:
        #             host_numa_cpus_filter = host_handle.lscpu("node[01]")
        #             host.host_numa_cpus = ",".join(host_numa_cpus_filter.values())
        #     else:
        #         if self.override_numa_node["override"]:
        #             host_numa_cpus_filter = host_handle.lscpu(self.override_numa_node["override_node"])
        #             host.host_numa_cpus = host_numa_cpus_filter[self.override_numa_node["override_node"]]
        #         else:
        #             host.host_numa_cpus = fetch_numa_cpus(host_handle, self.ethernet_adapter)
        numa_node_to_use = get_device_numa_node(self.hosts[0].instance, self.ethernet_adapter)
        if self.override_numa_node["override"]:
            numa_node_to_use = self.override_numa_node["override_node"]
        for host in self.hosts:
            if host.name.startswith("cab0"):
                host.host_numa_cpus = ",".join(host.spec["cpus"]["numa_node_ranges"])
            else:
                host.host_numa_cpus = host.spec["cpus"]["numa_node_ranges"][numa_node_to_use]

        fun_test.shared_variables["host_info"] = self.hosts
        fun_test.log("Hosts info: {}".format(dir(self.hosts)))
        fun_test.shared_variables["hosts"] = self.hosts

        # Warming up the volumes
        self.fio_io_size = 100 / len(self.hosts)
        # self.offsets = ["1%", "26%", "51%", "76%"]
        thread_id = {}
        end_host_thread = {}
        fio_output = {}
        fio_offset = 1

        fun_test.shared_variables["fio"] = {}
        for index, host in enumerate(self.hosts):
            host.instance.sudo_command("dmesg -C") # cleaning the dmesg output of the previous runs
            fun_test.log("Initial Write IO to volume, this might take long time depending on fio --size "
                         "provided")
            fio_output[index] = {}
            end_host_thread[index] = host.instance.clone()
            wait_time = len(self.hosts) - index
            if "multiple_jobs" in self.warm_up_fio_cmd_args:
                warm_up_fio_cmd_args = {}
                # Adding the allowed CPUs into the fio warmup command
                fio_cpus_allowed_args = " --cpus_allowed={}".format(host.host_numa_cpus)
                jobs = ""
                for id, device in enumerate(host.nvme_block_device_list):
                    jobs += " --name=vol{} --filename={}".format(id + 1, device)
                offset = " --offset={}%".format(fio_offset - 1 if fio_offset - 1 else fio_offset)
                size = " --size={}%".format(self.fio_io_size)
                warm_up_fio_cmd_args["multiple_jobs"] = self.warm_up_fio_cmd_args["multiple_jobs"] + \
                                                        fio_cpus_allowed_args + offset + size + jobs
                warm_up_fio_cmd_args["timeout"] = self.warm_up_fio_cmd_args["timeout"]

                thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                 func=fio_parser,
                                                                 arg1=end_host_thread[index],
                                                                 host_index=index,
                                                                 filename="nofile",
                                                                 **warm_up_fio_cmd_args)
                fio_offset += self.fio_io_size
                fun_test.sleep("Fio threadzz", seconds=1)

        fun_test.sleep("Fio threads started", 10)
        try:
            for i, host in enumerate(self.hosts):
                fun_test.log("Joining fio thread {}".format(i))
                fun_test.join_thread(fun_test_thread_id=thread_id[i])
                fun_test.log("FIO Command Output:")
                fun_test.log(fun_test.shared_variables["fio"][i])
                fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                     "FIO randwrite test with IO depth 16 in host {}".format(host.name))
                fio_output[i] = fun_test.shared_variables["fio"][i]
        except Exception as ex:
            fun_test.critical(str(ex))
            fun_test.log("FIO Command Output from host {}:\n {}".format(host.name, fio_output[i]))
            host.instance.sudo_command("dmesg") # print dmesg output of the host when fio fails

        aggr_fio_output = {}
        for index, host in enumerate(self.hosts):
            fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                 "FIO randwrite test with IO depth 16 in host {}".format(host.name))
            for op, stats in fun_test.shared_variables["fio"][index].items():
                if op not in aggr_fio_output:
                    aggr_fio_output[op] = {}
                aggr_fio_output[op] = Counter(aggr_fio_output[op]) + Counter(fio_output[i][op])

        # fun_test.log("Aggregated FIO Command Output:\n{}".format(aggr_fio_output))

        for op, stats in aggr_fio_output.items():
            for field, value in stats.items():
                if field == "iops":
                    aggr_fio_output[op][field] = int(round(value))
                if field == "bw":
                    # Converting the KBps to MBps
                    aggr_fio_output[op][field] = int(round(value / 1000))
                if "latency" in field:
                    aggr_fio_output[op][field] = int(round(value) / len(self.hosts))
                # Converting the runtime from milliseconds to seconds and taking the average out of it
                if field == "runtime":
                    aggr_fio_output[op][field] = int(round(value / 1000) / len(self.hosts))

        fun_test.log("Aggregated FIO Command Output after Computation :\n{}".format(aggr_fio_output))

    def run(self):
        testcase = self.__class__.__name__
        test_method = testcase
        # self.test_mode = testca

        # Going to run the FIO test for the block size and iodepth combo listed in fio_jobs_iodepth in both write only
        # & read only modes

        fio_result = {}
        internal_result = {}
        self.fio_jobs_iodepth = []

        table_data_headers = ["Block Size", "IO Depth", "Size", "Operation", "Write IOPS", "Read IOPS",
                              "Write Throughput in MB/s", "Read Throughput in MB/s", "Write Latency in uSecs",
                              "Write Latency 90 Percentile in uSecs", "Write Latency 95 Percentile in uSecs",
                              "Write Latency 99 Percentile in uSecs", "Write Latency 99.99 Percentile in uSecs",
                              "Read Latency in uSecs", "Read Latency 90 Percentile in uSecs",
                              "Read Latency 95 Percentile in uSecs", "Read Latency 99 Percentile in uSecs",
                              "Read Latency 99.99 Percentile in uSecs"]
        table_data_cols = ["block_size", "iodepth", "size", "mode", "writeiops", "readiops", "writebw", "readbw",
                           "writeclatency", "writelatency90", "writelatency95", "writelatency99", "writelatency9999",
                           "readclatency", "readlatency90", "readlatency95", "readlatency99", "readlatency9999",
                           ]

        table_data_rows = []
        # Preparing the volume details list containing the list of dictionaries
        vol_details = []
        vol_group = {}
        vol_group[BltVolumeOperationsTemplate.vol_type] = fun_test.shared_variables["vol_uuid_list"]
        vol_details.append(vol_group)
        self.storage_controller_dpcsh_obj = fun_test.shared_variables["dpcsh_obj"]

        for mode in self.fio_modes:
            for io_depth in self.fio_iodepth:
                self.test_mode = mode
                row_data_dict = {}
                row_data_dict["mode"] = mode
                row_data_dict["block_size"] = self.fio_bs
                row_data_dict["iodepth"] = io_depth
                num_jobs = 32 / self.blt_count
                file_size_in_gb = self.capacity / 1073741824
                row_data_dict["size"] = str(file_size_in_gb) + "GB"
                file_suffix = "{}_iodepth_{}.txt".format(self.test_mode, (int(io_depth) * int(num_jobs)))
                for index, stat_detail in enumerate(self.stats_collect_details):
                    func = stat_detail.keys()[0]
                    self.stats_collect_details[index][func]["count"] = int(
                        self.fio_cmd_args["timeout"] / self.stats_collect_details[index][func]["interval"])
                    if func == "vol_stats":
                        self.stats_collect_details[index][func]["vol_details"] = vol_details
                fun_test.log("Different stats collection thread details for the current IO depth {} before starting "
                             "them:\n{}".format((int(io_depth) * int(num_jobs)), self.stats_collect_details))
                self.storage_controller_dpcsh_obj.verbose = False
                stats_obj = CollectStats(self.storage_controller_dpcsh_obj)
                stats_obj.start(file_suffix, self.stats_collect_details)
                fun_test.log("Different stats collection thread details for the current IO depth {} after starting "
                             "them:\n{}".format((int(io_depth) * int(num_jobs)), self.stats_collect_details))

                thread_id = {}
                end_host_thread = {}
                fio_output = {}
                fio_offset = 1
                for index, host in enumerate(self.hosts):
                    fun_test.log("After warmup,{} IO to volume, this might take long time depending on fio --size "
                                 "provided".format(mode))
                    fio_output[index] = {}
                    end_host_thread[index] = host.instance.clone()
                    wait_time = len(self.hosts) - index
                    if "multiple_jobs" in self.fio_cmd_args:
                        fio_cmd_args = {}
                        # Adding the allowed CPUs into the fio command
                        fio_cpus_allowed_args = " --cpus_allowed={}".format(host.host_numa_cpus)
                        jobs = ""
                        for id, device in enumerate(host.nvme_block_device_list):
                            jobs += " --name=vol{} --filename={}".format(id + 1, device)

                        num_jobs_string = " --numjobs={}".format(num_jobs)
                        required_io_depth = io_depth / num_jobs
                        combo = str(num_jobs, required_io_depth)
                        self.fio_jobs_iodepth.append(combo)
                        fio_result[combo] = {}
                        internal_result[combo] = {}
                        fio_result[combo][mode] = True
                        internal_result[combo][mode] = True
                        io_depth_string = " --iodepth={}".format(required_io_depth)
                        io_size = self.capacity / num_jobs
                        io_size_string = " --io_size={}".format(io_size)
                        # offset = " --offset={}%".format(fio_offset - 1 if fio_offset - 1 else fio_offset)
                        # size = " --size={}%".format(self.fio_io_size)
                        rw_string = " --rw={}".format(mode)
                        bs_string = " --bs={}".format(self.fio_bs)
                        fio_cmd_args["multiple_jobs"] = self.fio_cmd_args["multiple_jobs"] + \
                                                        fio_cpus_allowed_args + num_jobs_string + \
                                                        io_depth_string + io_size_string + bs_string + rw_string + jobs
                        fio_cmd_args["timeout"] = self.fio_cmd_args["timeout"]
                        fun_test.log("Fio command used is ")
                        fun_test.log(fio_cmd_args["multiple_jobs"])
                        thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                         func=fio_parser,
                                                                         arg1=end_host_thread[index],
                                                                         host_index=index,
                                                                         filename="nofile",
                                                                         **fio_cmd_args)
                        fio_offset += self.fio_io_size
                        fun_test.sleep("Fio threadzz", seconds=1)

                fun_test.sleep("Fio threads started", 10)
                try:
                    for i, host in enumerate(self.hosts):
                        fun_test.log("Joining fio thread {}".format(i))
                        fun_test.join_thread(fun_test_thread_id=thread_id[i])
                        fun_test.log("FIO Command Output:")
                        fun_test.log(fun_test.shared_variables["fio"][i])
                        fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                             "FIO {} test with IO depth {} in host {}".format(mode, io_depth, host.name))
                        fio_output[i] = fun_test.shared_variables["fio"][i]
                except Exception as ex:
                    fun_test.critical(str(ex))
                    host.instance.sudo_command("dmesg") #print dmesg output of the host when fio fails
                    fun_test.log("FIO Command Output from host {}:\n {}".format(host.name, fio_output[i]))
                finally:
                    stats_obj.stop(self.stats_collect_details)
                    self.storage_controller_dpcsh_obj.verbose = True

                job_string = "{} - IO depth {}".format(mode, row_data_dict["iodepth"])
                stats_obj.populate_stats_to_file(self.stats_collect_details, job_string=job_string)

                aggr_fio_output = {}
                for index, host in enumerate(self.hosts):
                    fun_test.simple_assert(fun_test.shared_variables["fio"][index],
                                           "FIO {} test with IO depth {} in host {}".format(mode, io_depth, host.name))
                    for op, stats in fun_test.shared_variables["fio"][index].items():
                        if op not in aggr_fio_output:
                            aggr_fio_output[op] = {}
                        aggr_fio_output[op] = Counter(aggr_fio_output[op]) + Counter(fio_output[index][op])

                fun_test.log("Aggregated FIO Command Output:\n{}".format(aggr_fio_output))

                for op, stats in aggr_fio_output.items():
                    for field, value in stats.items():
                        if field == "iops":
                            aggr_fio_output[op][field] = int(round(value))
                        if field == "bw":
                            # Converting the KBps to MBps
                            aggr_fio_output[op][field] = int(round(value / 1000))
                        if "latency" in field:
                            aggr_fio_output[op][field] = int(round(value) / len(self.hosts))
                        # Converting the runtime from milliseconds to seconds and taking the average out of it
                        if field == "runtime":
                            aggr_fio_output[op][field] = int(round(value / 1000) / len(self.hosts))
                        row_data_dict[op + field] = aggr_fio_output[op][field]
                fun_test.log("Processed Aggregated FIO Command Output:\n{}".format(aggr_fio_output))

                row_data_list = []
                for i in table_data_cols:
                    if i not in row_data_dict:
                        row_data_list.append(-1)
                    else:
                        row_data_list.append(row_data_dict[i])
                table_data_rows.append(row_data_list)

                table_data_list = copy.deepcopy(row_data_list)
                table_data_rows.append(table_data_list)

                row_data_list.insert(0, self.blt_count)
                row_data_list.insert(0, self.num_ssd)
                row_data_list.insert(0, get_data_collection_time())
                row_data_list.append(self.num_f1)
                row_data_list.append(len(self.hosts))
                row_data_list.append(shared_volume=True)
                if self.post_results:
                    fun_test.log("Posting results on dashboard")
                    post_results("Shared_Volume_Test", test_method, *row_data_list)

                table_data = {"headers": table_data_headers, "rows": table_data_rows}
                fun_test.add_table(panel_header="BLT Shared Volume Performance Table", table_name=self.summary,
                                   table_data=table_data)

                # Posting the final status of the test result
        post_final_test_results(fio_result=fio_result, internal_result=internal_result,
                                fio_jobs_iodepth=self.fio_jobs_iodepth, fio_modes=self.fio_modes)

    def cleanup(self):
        pass


class ConfigPersistenceAfterReset(FunTestCase):
    topology = None
    storage_controller_template = None

    def describe(self):
        self.set_test_details(id=2,
                              summary="Reset FS1600 and Do IO from host",
                              steps='''
                                 1. Reset FS1600 
                                 2. Make sure API server is up and running
                                 3. Make sure Volume is Present
                                 4. Make sure Host sees NVMe device
                                 5. Run FIO from host
                                 ''')

    def setup(self):
        testcase = self.__class__.__name__
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Benchmark file being used: {}".format(benchmark_file))

        tc_config = {}
        tc_config = utils.parse_file_to_json(benchmark_file)

        if testcase not in tc_config or not tc_config[testcase]:
            tc_config = False
            fun_test.critical("Benchmarking is not available for the current testcase {} in {} file".
                              format(testcase, benchmark_file))
            fun_test.test_assert(tc_config, "Parsing Benchmark json file for this {} testcase".format(testcase))
        fun_test.test_assert(tc_config, "Parsing Benchmark json file for this {} testcase".format(testcase))
        for k, v in tc_config[testcase].iteritems():
            setattr(self, k, v)

        self.hosts = fun_test.shared_variables["hosts"]
        self.topology = fun_test.shared_variables["topology"]
        self.blt_template = fun_test.shared_variables["blt_template"]
        self.vol_uuid_list = fun_test.shared_variables["vol_uuid_list"]
        self.fs_obj_list = fun_test.shared_variables["fs_obj_list"]

        fs = self.fs_obj_list[0]
        come = fs.get_come()
        self.sc_api = StorageControllerApi(api_server_ip=come.host_ip)
        # check the data integrity before reboot
        # self.offsets = ["1%", "26%", "51%", "76%"]
        thread_id = {}
        end_host_thread = {}
        fio_output = {}
        fio_offset = 1

        fun_test.shared_variables["fio"] = {}
        for index, host in enumerate(self.hosts):
            fun_test.log("Verifying data integrity before reboot")
            fio_output[index] = {}
            end_host_thread[index] = host.instance.clone()
            wait_time = len(self.hosts) - index
            if "multiple_jobs" in self.warm_up_fio_cmd_args:
                warm_up_fio_cmd_args = {}
                # Adding the allowed CPUs into the fio warmup command
                fio_cpus_allowed_args = " --cpus_allowed={}".format(host.host_numa_cpus)
                jobs = ""
                for id, device in enumerate(host.nvme_block_device_list):
                    jobs += " --name=vol{} --filename={}".format(id + 1, device)
                # offset = " --offset={}%".format(fio_offset - 1 if fio_offset - 1 else fio_offset)
                size = " --size={}%".format(self.fio_io_size)
                warm_up_fio_cmd_args["multiple_jobs"] = self.warm_up_fio_cmd_args["multiple_jobs"] + \
                                                        fio_cpus_allowed_args + size + jobs
                warm_up_fio_cmd_args["timeout"] = self.warm_up_fio_cmd_args["timeout"]

                thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                 func=fio_parser,
                                                                 arg1=end_host_thread[index],
                                                                 host_index=index,
                                                                 filename="nofile",
                                                                 **warm_up_fio_cmd_args)
                # fio_offset += self.fio_io_size
                fun_test.sleep("Fio threadzz", seconds=1)

        fun_test.sleep("Fio threads started", 10)
        try:
            for i, host in enumerate(self.hosts):
                fun_test.log("Joining fio thread {}".format(i))
                fun_test.join_thread(fun_test_thread_id=thread_id[i])
                fun_test.log("FIO Command Output:")
                fun_test.log(fun_test.shared_variables["fio"][i])
                fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                     "FIO read test with IO depth 16 in host {}".format(host.name))
                fio_output[i] = fun_test.shared_variables["fio"][i]
        except Exception as ex:
            fun_test.critical(str(ex))
            fun_test.log("FIO Command Output from host {}:\n {}".format(host.name, fio_output[i]))
            host.instance.sudo_command("dmesg") # print dmesg output of the host when fio fails

        aggr_fio_output = {}
        for index, host in enumerate(self.hosts):
            fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                 "FIO test with IO depth 16 in host {}".format(host.name))
            for op, stats in fun_test.shared_variables["fio"][index].items():
                if op not in aggr_fio_output:
                    aggr_fio_output[op] = {}
                aggr_fio_output[op] = Counter(aggr_fio_output[op]) + Counter(fio_output[i][op])

        # fun_test.log("Aggregated FIO Command Output:\n{}".format(aggr_fio_output))

        for op, stats in aggr_fio_output.items():
            for field, value in stats.items():
                if field == "iops":
                    aggr_fio_output[op][field] = int(round(value))
                if field == "bw":
                    # Converting the KBps to MBps
                    aggr_fio_output[op][field] = int(round(value / 1000))
                if "latency" in field:
                    aggr_fio_output[op][field] = int(round(value) / len(self.hosts))
                # Converting the runtime from milliseconds to seconds and taking the average out of it
                if field == "runtime":
                    aggr_fio_output[op][field] = int(round(value / 1000) / len(self.hosts))

        fun_test.log("Aggregated FIO Command Output after Computation :\n{}".format(aggr_fio_output))



        # Reset the fs and ensure all containers are up and api server is running
        total_reconnect_time = 600
        add_on_time = 180  # Needed for getting through 60 iterations of reconnect from host
        reboot_timer = FunTimer(max_time=total_reconnect_time + add_on_time)  # WORKAROUND, why do we need so much time
        self.reset_and_health_check(self.fs_obj_list[0])
        fun_test.sleep(message="Wait before checking the state of the DPU's", seconds=60)
        num_dpus = 1
        fun_test.test_assert_expected(expected=1,
                                      actual=self.blt_template.get_online_dpus(dpu_indexes=[0]),
                                      message="Make sure {} DPUs are online".format(num_dpus))
        '''
        threads_list = []
        for dut_index in self.topology.get_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            thread_id = fun_test.execute_thread_after(time_in_seconds=2, func=self.reset_an d_health_check,
                                                      fs_obj=fs_obj)
            threads_list.append(thread_id)
        
        for thread_id in threads_list:
            fun_test.join_thread(fun_test_thread_id=thread_id, sleep_time=1)
        '''


        # Check whether volumes are available to the hosts after reboot
        volume_found = False
        while not reboot_timer.is_expired():
            # checking if the volumes are available at fs side
            vols = self.sc_api.get_volumes()
            if (vols['status'] and vols['data']):
                volume_list = vols['data'].keys()
                fun_test.log("volumes listed from api after reboot")
                fun_test.log(volume_list)
                res = sorted(volume_list) == sorted(self.vol_uuid_list)
                fun_test.test_assert(res, "volumes are available at the fs side after reboot")
                volume_found = True
            if volume_found:
                for host in self.hosts:
                    host_handle = host.instance
                    nvme_device_list_after_reboot = fetch_nvme_list(host_handle)
                    nvme_device_list_after_reboot["nvme_device"] = nvme_device_list_after_reboot["nvme_device"]. \
                        split(":")
                    fun_test.log("nvme_device_list_after_reboot")
                    fun_test.log(nvme_device_list_after_reboot)
                    if nvme_device_list_after_reboot["status"]:
                        fun_test.test_assert_expected(
                            expected=len(host.nvme_block_device_list),
                            actual=len(nvme_device_list_after_reboot["nvme_device"]),
                            message="Expected number of NVMe devices available after reboot at host {}".format(host.name))
                        res = sorted(host.nvme_block_device_list) == sorted(nvme_device_list_after_reboot["nvme_device"])
                        fun_test.test_assert(res, "nvme device names are valid {}".format(nvme_device_list_after_reboot["nvme_device"]))
                break

    def run(self):

        thread_id = {}
        end_host_thread = {}
        fio_output = {}
        fio_offset = 1

        fun_test.shared_variables["fio"] = {}
        for index, host in enumerate(self.hosts):
            fun_test.log("Verifying data integrity after reboot")
            fio_output[index] = {}
            end_host_thread[index] = host.instance.clone()
            wait_time = len(self.hosts) - index
            if "multiple_jobs" in self.warm_up_fio_cmd_args:
                warm_up_fio_cmd_args = {}
                # Adding the allowed CPUs into the fio warmup command
                fio_cpus_allowed_args = " --cpus_allowed={}".format(host.host_numa_cpus)
                jobs = ""
                for id, device in enumerate(host.nvme_block_device_list):
                    jobs += " --name=vol{} --filename={}".format(id + 1, device)
                # offset = " --offset={}%".format(fio_offset - 1 if fio_offset - 1 else fio_offset)
                size = " --size={}%".format(self.fio_io_size)
                warm_up_fio_cmd_args["multiple_jobs"] = self.warm_up_fio_cmd_args["multiple_jobs"] + \
                                                        fio_cpus_allowed_args + size + jobs
                warm_up_fio_cmd_args["timeout"] = self.warm_up_fio_cmd_args["timeout"]

                thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                 func=fio_parser,
                                                                 arg1=end_host_thread[index],
                                                                 host_index=index,
                                                                 filename="nofile",
                                                                 **warm_up_fio_cmd_args)
                # fio_offset += self.fio_io_size
                fun_test.sleep("Fio threadzz", seconds=1)

        fun_test.sleep("Fio threads started", 10)
        try:
            for i, host in enumerate(self.hosts):
                fun_test.log("Joining fio thread {}".format(i))
                fun_test.join_thread(fun_test_thread_id=thread_id[i])
                fun_test.log("FIO Command Output:")
                fun_test.log(fun_test.shared_variables["fio"][i])
                fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                     "FIO read test with IO depth 16 in host {}".format(host.name))
                fio_output[i] = fun_test.shared_variables["fio"][i]
        except Exception as ex:
            fun_test.critical(str(ex))
            fun_test.log("FIO Command Output from host {}:\n {}".format(host.name, fio_output[i]))
            host.instance.sudo_command("dmesg")  # print dmesg output of the host when fio fails

        aggr_fio_output = {}
        for index, host in enumerate(self.hosts):
            fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                 "FIO test with IO depth 16 in host {}".format(host.name))
            for op, stats in fun_test.shared_variables["fio"][index].items():
                if op not in aggr_fio_output:
                    aggr_fio_output[op] = {}
                aggr_fio_output[op] = Counter(aggr_fio_output[op]) + Counter(fio_output[i][op])

        # fun_test.log("Aggregated FIO Command Output:\n{}".format(aggr_fio_output))

        for op, stats in aggr_fio_output.items():
            for field, value in stats.items():
                if field == "iops":
                    aggr_fio_output[op][field] = int(round(value))
                if field == "bw":
                    # Converting the KBps to MBps
                    aggr_fio_output[op][field] = int(round(value / 1000))
                if "latency" in field:
                    aggr_fio_output[op][field] = int(round(value) / len(self.hosts))
                # Converting the runtime from milliseconds to seconds and taking the average out of it
                if field == "runtime":
                    aggr_fio_output[op][field] = int(round(value / 1000) / len(self.hosts))

        fun_test.log("Aggregated FIO Command Output after Computation :\n{}".format(aggr_fio_output))

    def cleanup(self):
        pass

    def reset_and_health_check(self, fs_obj):
        fs_obj.reset(hard=False)
        fun_test.test_assert(fs_obj.come.ensure_expected_containers_running(), "All containers are up")
        fun_test.test_assert(expression=self.blt_template.get_health(fs_obj),
                             message="{}: API server health".format(fs_obj))

    """
    def fetch_nvme_list(self, host_obj):
        result = {'status': False}
        nvme_list_raw = host_obj.sudo_command("nvme list -o json")
        fun_test.log("NVME list command results")
        fun_test.log(fetch_nvme_list)
        host_obj.disconnect()
        if nvme_list_raw:
            if "failed to open" in nvme_list_raw.lower():
                nvme_list_raw = nvme_list_raw + "}"
                temp1 = nvme_list_raw.replace('\n', '')
                temp2 = re.search(r'{.*', temp1).group()
                nvme_list_dict = json.loads(temp2, strict=False)
            else:
                try:
                    nvme_list_dict = json.loads(nvme_list_raw)
                except:
                    nvme_list_raw = nvme_list_raw + "}"
                    nvme_list_dict = json.loads(nvme_list_raw, strict=False)
            try:
                nvme_device_list = []
                for device in nvme_list_dict["Devices"]:
                    if "Non-Volatile memory controller: Vendor 0x1dad" in device["ProductName"] or \
                            "fs1600" in device["ModelNumber"].lower():
                        nvme_device_list.append(device["DevicePath"])
                    elif "unknown device" in device["ProductName"].lower() or "null" in device["ProductName"].lower():
                        if not device["ModelNumber"].strip() and not device["SerialNumber"].strip():
                            nvme_device_list.append(device["DevicePath"])
                result = {'status': True, 'nvme_devices': nvme_device_list}
            except:
                result = {'status': False, 'nvme_devices': nvme_device_list}
        else:
            result = {'status': False, 'nvme_devices': None}
        return result
    """


if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(SharedVolumePerfTest())
    setup_bringup.add_test_case(ConfigPersistenceAfterReset())
    setup_bringup.run()
