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
from collections import OrderedDict
from lib.templates.csi_perf.csi_perf_template import CsiPerfTemplate
from lib.templates.storage.storage_controller_api import *
from swagger_client.rest import ApiException
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
        self.job_inputs = {}
        self.job_inputs = fun_test.get_job_inputs()
        fun_test.shared_variables["job_inputs"] = self.job_inputs

        already_deployed = False
        #format_drives = False
        if "already_deployed" in self.job_inputs:
            already_deployed = self.job_inputs["already_deployed"]

        topology_helper = TopologyHelper()
        self.topology = topology_helper.deploy(already_deployed=already_deployed)
        fun_test.test_assert(self.topology, "Topology deployed")
        fun_test.shared_variables["topology"] = self.topology

        self.sc_template = BltVolumeOperationsTemplate(topology=self.topology)
        self.sc_template.initialize(already_deployed=already_deployed)
        fun_test.shared_variables["storage_controller_template"] = self.sc_template

        # Below lines are needed so that we create/attach volumes only once and other testcases use the same volumes
        fun_test.shared_variables["blt"] = {}
        fun_test.shared_variables["blt"]["setup_created"] = False
        fun_test.shared_variables["blt"]["warmup_done"] = False

    def cleanup(self):
        self.sc_template.cleanup()
        self.topology.cleanup()


class CreateFullCapacityBltVolume(FunTestCase):
    def describe(self):
        self.set_test_details(id=1,
                              summary="C36952 - To verify correctness of the total capacity given by rest API "
                                      "",
                              steps='''
        1. Bring up FS1600
        2. Bring up DP0 online   
        3. Create 1 full capacity blt volume on all attached SSDs. (e.g. if all 12 ssds connected to 1 DPU, 
           create 12 volumes of "effective available capacity" on each of the 12 ssds)
        4. use dpcsh and issue peek storage command to sum up the "effective capacities"
        5. Verify that the 'Capacity' section under Dashboard shows the collective capacity of the SSDs 
           connected to DPU0 and matches with dpcsh sum.
        6. Bring up DPU1 online, repeat 3,4
        7. verify the 'Capacity' section under Dashboard shows the collective capacity of the SSDs connected to DPU1 
           and DPU0 and matches with dpcsh sum.   
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
        # TODO: Check if block size is not required
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

        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))
        fun_test.log("Block size and IO depth combo going to be used for this {} testcase: {}".
                     format(testcase, self.fio_jobs_iodepth))
        fun_test.log("Benchmarking results going to be used for this {} testcase: \n{}".
                     format(testcase, self.expected_fio_result))
        # End of benchmarking json file parsing



        self.job_inputs = fun_test.shared_variables["job_inputs"]
        self.topology = fun_test.shared_variables["topology"]
        self.sc_template = fun_test.shared_variables["storage_controller_template"]
        self.blt_count = 1
        self.create_volume_list = []

        fs_obj_list = []
        self.create_volume_list = []
        use_unique_drives = 1

        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            fs_obj_list.append(fs_obj)
        #fs_obj = fs_obj_list[0]

        self.sc_ctrl = fs_obj.get_storage_controller()
        self.sc_dpcsh_obj = fs_obj.get_storage_controller(f1_index=0)
        self.hosts = self.topology.get_available_host_instances()
        self.topology_result = None
        self.total_capacity = 0
        self.drive_id_list = []

        #2. Finding the number of online DPUs (num_online_dpus)
        dpu_indexes = None
        if dpu_indexes is None:
            dpu_indexes = [0, 1]
        self.num_online_dpus = self.sc_template.get_online_dpus(dpu_indexes=dpu_indexes)

        #3.Find the number of SSDs per DPU and create 1 BLT volume of full capacity per  SSD

        try:
            topology_result = self.sc_ctrl.topology_api.get_hierarchical_topology()
        except ApiException as e:
            fun_test.critical("Exception while getting topology%s\n" % e)
        self.num_dpu_list = [x.dpus for x in topology_result.data.values()]
        fun_test.test_assert(expression=self.num_dpu_list, message="Fetch num_dpu_list using topology API")
        self.num_dpus = self.num_dpu_list[0]
        if not len(self.num_dpus) == self.num_online_dpus:
            fun_test.critical(message="Number of DPUs got from topology do not match the Number of online DPUs")



        #Verify if the capacity value got is matching the capacity in GUI
        for index in range(len(self.num_dpus)):

            self.num_drives = len(self.num_dpus[index].drives)
            fun_test.log("Number of drives on DPU{} = {}".format(index, self.num_drives))
            self.dpu_capacity = 0
            for kk in range(self.num_drives):
                capacity = self.num_dpus[index].drives[kk].capacity
                self.dpu_capacity += capacity
            fun_test.log("Total capacity of the drives on DPU{} = {}".format(index, self.dpu_capacity))
            self.total_capacity += self.dpu_capacity
        fun_test.log("Total capacity of all the online DPUs = {}".format(self.total_capacity))


        self.total_logical_capacity = 0
        self.total_capacity = 0
        for index in range(len(self.num_dpus)):
            self.num_drives = len(self.num_dpus[index].drives)
            #fs_obj = fs_obj_list[index]
            #fs_obj_list_tmp = [fs_obj_list[index]]
            self.sc_dpcsh_obj = fs_obj.get_storage_controller(f1_index=index)
            self.total_capacity = 0
            for kk in range(self.num_drives):
                capacity = self.num_dpus[index].drives[kk].capacity - (3*4096)
                blt_name = "{}_{}_{}_{}".format("dpu", str(index), "blt_vol", str(kk))
                vol_type = VolumeTypes.LOCAL_THIN
                compression_effort = False
                encrypt = False
                body_volume_intent_create = BodyVolumeIntentCreate(name=blt_name, vol_type=vol_type, capacity=capacity,
                                                                   compression_effort=compression_effort,
                                                                   encrypt=encrypt, data_protection={})
                vol_uuid_list = self.sc_template. \
                    create_volume(fs_obj=fs_obj_list, body_volume_intent_create=body_volume_intent_create)
                fun_test.test_assert(expression=vol_uuid_list, message="Create Volume Successful")
                fun_test.log("Create Volume Successful for {} with capacity {}".format(blt_name, capacity))
                #self.total_logical_capacity += capacity -ASH remove this as capacity now got from peek


                current_vol_uuid = vol_uuid_list[0]
                fun_test.test_assert(expression=vol_uuid_list,
                                     message="Created Volume {} Successful".format(current_vol_uuid))
                self.create_volume_list.append(current_vol_uuid)

                # Check if drive id is unique
                #if use_unique_drives:
                #    props_tree = "{}/{}/{}".format("storage", "volumes", self.sc_template.vol_type)
                #    dpcsh_op = self.sc_ctrl.peek(props_tree=props_tree)
                #    vol_uuid_set = set(dpcsh_op["data"].keys())
                #    drive_id_set = set(dpcsh_op["data"]["drives"].keys())
                #    if(current_vol_uuid not in vol_uuid_set):
                #        fun_test.critical(message="Volume {} not seen in peek storage output".format(current_vol_uuid))
                #    drive_id = dpcsh_op["data"][current_vol_uuid]["stats"]["drive_uuid"]
                #    seen_capacity_bytes = dpcsh_op["data"]["drives"][drive_id]["capacity_bytes"]
                #    fun_test.log("Seen capacity of drive {} in DPU {} = {}".format(kk, index, seen_capacity_bytes))
                #    self.total_capacity += seen_capacity_bytes
                #    if(drive_id not in drive_id_set):
                #        fun_test.critical(message="Volume id {} drive with uuid {} id is not found in drive_id_set"
                #                                 " uuid {}".format(current_vol_uuid, drive_id, drive_id_set))
                #    self.drive_id_list.append(drive_id)

        #Ashwini
        use_unique_drives = 1
        seen_vol_uuid = {}
        seen_drive_id = {}
        for index in range(len(self.num_dpus)):
            self.num_drives = len(self.num_dpus[index].drives)
            self.sc_dpcsh_obj = fs_obj.get_storage_controller(f1_index=index)
            self.total_capacity = 0
            for kk in range(self.num_drives):

                # Check if drive id is unique
                if use_unique_drives:

                    props_tree = "{}/{}/{}".format("storage", "volumes", self.sc_template.vol_type)
                    dpcsh_op = self.sc_ctrl.peek(props_tree=props_tree)
                    vol_uuid_set = set(dpcsh_op["data"].keys())
                    drive_id_set = set(dpcsh_op["data"]["drives"].keys())
                    vol_idx = kk + (self.num_drives*index)
                    vol_uuid_search = self.create_volume_list[vol_idx]
                    if(vol_uuid_search not in vol_uuid_set):
                        fun_test.critical(message="Volume {} not seen in peek storage output".format(vol_uuid_search))
                    else:
                        seen_vol_uuid[vol_uuid_search] += 1
                        if (seen_vol_uuid[vol_uuid_set] > 1):
                            fun_test.critical(
                                    message="Duplicate Volume {} seen while creating Volume {} for DPU {}".format(
                                    , kk, index))
                    drive_id = dpcsh_op["data"][vol_uuid_search]["stats"]["drive_uuid"]
                    seen_capacity_bytes = dpcsh_op["data"]["drives"][drive_id]["capacity_bytes"]
                    fun_test.log("Seen capacity of drive {} in DPU {} = {}".format(kk, index, seen_capacity_bytes))
                    self.total_capacity += seen_capacity_bytes
                    if(drive_id not in drive_id_set):
                        fun_test.critical(message="Volume id {} drive with uuid {} id is not found in drive_id_set"
                                                     " uuid {}".format(vol_uuid_search, drive_id, drive_id_set))
                    else:
                        seen_drive_id[drive_id] += 1
                        if (seen_drive_id[drive_id] > 1):
                            fun_test.critical(message="Duplicate drive_id {} seen for Volume id {}"
                                               "for Volume Number {} for DPU {}".format(drive_id,
                                               vol_uuid_search, kk, index))
                    self.drive_id_list.append(drive_id)

        #EOF_Ashwini

                self.total_logical_capacity += self.total_capacity
                fun_test.log("Total capacity of DPU {} = {}".format(index, self.total_capacity))
            fun_test.log("Total capacity of all the online DPUs = {}".format(self.total_logical_capacity))

        self.raw_sc_api = StorageControllerApi(api_server_ip=self.sc_ctrl.target_ip)
        self.get_pool_data = self.raw_sc_api.get_pools()
        self.api_capacity = 0
        for kk in self.get_pool_data["data"].keys():
            self.api_capacity = self.get_pool_data["data"][kk]["capacity"]
        fun_test.log("DPUs capacity  got from API get_pools{}".format(self.api_capacity))
        #if not self.api_capacity == self.total_logical_capacity:
        #    fun_test.critical(
        #        message="Capacity got from API get_pools does not match the total_capacity calculated for online DPUs")


        self.api_get_volume_volume_list = set(self.get_volume_data["data"].keys())

        for kk in self.create_volume_list:
            if kk not in api_get_volume_volume_list:
                fun_test.critical(message = "FAIL : create_volume_entry {} not found in {}".format(kk, api_get_volume_volume_list))
            else:
                fun_test.log("PASS: create_volume_entry {} found in {}".format(kk, api_get_volume_volume_list))

        self.get_volume_data = self.raw_sc_api.get_volumes()
        self.api_gui_logical_capacity = 0
        for kk in self.get_volume_data["data"].keys():
            self.api_gui_logical_capacity += self.get_volume_data["data"][kk]["physical_capacity"]
        fun_test.log("GUI logical_capacity  got from API get_volumes{}".format(self.api_gui_logical_capacity))
        if not self.api_gui_logical_capacity == self.total_logical_capacity:
               fun_test.critical(
                   message="Capacity got from API get_volumes does not match the total_capacity calculated for online DPUs")


        fun_test.log("Provided job inputs: {}".format(self.job_inputs))


        # Attach volumes to hosts and do nvme connect
        # TODO: Check if nvme connect needs to be only once on host
        #self.raw_api_call = True (or) False //FIXME_ASH: check on this
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

        fun_test.shared_variables["blt"]["setup_created"] = True
        fun_test.shared_variables["hosts"] = self.hosts
        fun_test.shared_variables["dpcsh_obj"] = self.sc_dpcsh_obj

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
                fun_test.sleep("Sleeping for 2 seconds before actual test", seconds=2)
            fun_test.test_assert(fun_test.shared_variables["blt"]["warmup_done"], message="Warmup done successfully")

    def run(self):
        pass




if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(CreateFullCapacityBltVolume())
    #setup_bringup.add_test_case(MultiHostFioRandWrite())
    #setup_bringup.add_test_case(PreCommitSanity())
    setup_bringup.run()