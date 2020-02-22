from lib.system.fun_test import *
from lib.system import utils
fun_test.enable_storage_api()
from lib.system import utils
from lib.host.linux import Linux
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_operations_template import EcVolumeOperationsTemplate
from swagger_client.models.volume_types import VolumeTypes
from scripts.storage.storage_helper import *
import string, random,re
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

        topology_helper = TopologyHelper()
        self.topology = topology_helper.deploy(already_deployed=self.already_deployed)
        fun_test.test_assert(self.topology, "Topology deployed")
        fun_test.shared_variables["topology"] = self.topology
        self.ec_template = EcVolumeOperationsTemplate(topology=self.topology)
        self.ec_template.initialize(dpu_indexes=[0], already_deployed=self.already_deployed,format_drives=format_drives)
        fun_test.shared_variables["ec_template"] = self.ec_template
        self.fs_obj_list = []
        for dut_index in self.topology.get_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            self.fs_obj_list.append(fs_obj)

        fun_test.shared_variables["fs_obj_list"] = self.fs_obj_list
        fs_obj = self.fs_obj_list[0]
        self.storage_controller_dpcsh_obj = fs_obj.get_storage_controller(f1_index=0)
        fun_test.shared_variables["dpcsh_obj"] = self.storage_controller_dpcsh_obj


    def cleanup(self):

        self.ec_template.cleanup()
        self.topology.cleanup()


class DateIntegrityCheck(FunTestCase):

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
        self.ec_template = fun_test.shared_variables["ec_template"]
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
        if "capacity" in job_inputs:
            self.capacity = job_inputs["capacity"]
        if "ec_count" in job_inputs:
            self.ec_count = job_inputs["ec_count"]
        if "num_hosts" in job_inputs:
            self.num_hosts = job_inputs["num_hosts"]
        if "test_bs" in job_inputs:
            self.fio_bs = job_inputs["test_bs"]
        if "fio_modes" in job_inputs:
            self.fio_modes = job_inputs["fio_modes"]


        self.vol_uuid_list = []
        self.ec_count = len(self.effort_levels)
        fun_test.shared_variables["ec_count"] = self.ec_count
        vol_type = VolumeTypes().EC

        self.hosts = self.topology.get_available_host_instances()

        # chars = string.ascii_uppercase + string.ascii_lowercase
        for effort in self.effort_levels:
            suffix = utils.generate_uuid(length=4)
            body_volume_intent_create = BodyVolumeIntentCreate(name=self.name + suffix + str(effort), vol_type=vol_type,
                                                               capacity=self.capacity, compression_effort=effort,
                                                               encrypt=False, data_protection={"num_redundant_dpus": 0,
                                                                                               "num_failed_disks": 2})
            vol_uuid = self.ec_template.create_volume(self.fs_obj_list, body_volume_intent_create)
            fun_test.test_assert(expression=vol_uuid[0], message="Create Volume Successful")
            self.vol_uuid_list.append(vol_uuid[0])

        fun_test.shared_variables["vol_uuid_list"] = self.vol_uuid_list
        for host in self.hosts:
            host.nvme_connect_info = {}

        attach_vol_result = {}
        for i in range(self.ec_count):
            attach_vol_result[i] = self.ec_template.attach_volume(self.fs_obj_list[0],
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
                        expression=self.ec_template.nvme_connect_from_host(host_obj=host, subsys_nqn=subsys_nqn,
                                                                            host_nqn=host_nqn,
                                                                            dataplane_ip=dataplane_ip),
                        message="NVMe connect from host: {}".format(host.name))
                    nvme_filename = self.ec_template.get_host_nvme_device(host_obj=host, subsys_nqn=subsys_nqn)
                    fun_test.test_assert(expression=nvme_filename,
                                         message="Get NVMe drive from Host {} using lsblk".format(host.name))

        for host in self.hosts:
            host.num_volumes = self.ec_count

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
        '''
        numa_node_to_use = get_device_numa_node(self.hosts[0].instance, self.ethernet_adapter)
        if self.override_numa_node["override"]:
            numa_node_to_use = self.override_numa_node["override_node"]
        for host in self.hosts:
            if host.name.startswith("cab0"):
                host.host_numa_cpus = ",".join(host.spec["cpus"]["numa_node_ranges"])
            else:
                host.host_numa_cpus = host.spec["cpus"]["numa_node_ranges"][numa_node_to_use]
        '''
        fun_test.shared_variables["host_info"] = self.hosts
        fun_test.log("Hosts info: {}".format(dir(self.hosts)))
        fun_test.shared_variables["hosts"] = self.hosts



    def run(self):

        testcase = self.__class__.__name__
        test_method = testcase
        self.fio_io_size = 100
        block_sizes = ["4k", "8k", "16k", "32k", "64k"]
        wr_modes =["write", "randwrite", "write", "randwrite"]
        rd_modes = ["read", "randread", "randread", "read"]

        for bs in block_sizes:
            for wr_mode, rd_mode in zip(wr_modes, rd_modes):
                # FIO write
                thread_id = {}
                end_host_thread = {}
                fio_output = {}

                fun_test.shared_variables["fio"] = {}
                for index, host in enumerate(self.hosts):
                    host.instance.sudo_command("dmesg -C") # cleaning the dmesg output of the previous runs
                    fun_test.log("Write IO to volume")
                    fio_output[index] = {}
                    end_host_thread[index] = host.instance.clone()
                    wait_time = len(self.hosts) - index
                    if "multiple_jobs" in self.fio_write_cmd_args:
                        fio_cmd_args = {}
                        # Adding the allowed CPUs into the fio command
                        # fio_cpus_allowed_args = " --cpus_allowed={}".format(host.host_numa_cpus) 
                        jobs = ""
                        for id, device in enumerate(host.nvme_block_device_list):
                            jobs += " --name=vol{} --filename={}".format(id + 1, device)
                        size = " --size={}%".format(self.fio_io_size)
                        operation = " --rw={}".format(wr_mode)
                        blk_size = " --bs={}".format(bs)

                        fio_cmd_args["multiple_jobs"] = self.fio_write_cmd_args["multiple_jobs"] + \
                                                                operation + blk_size + \
                                                                size + jobs
                        fio_cmd_args["timeout"] = self.fio_write_cmd_args["timeout"]

                        thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                         func=fio_parser,
                                                                         arg1=end_host_thread[index],
                                                                         host_index=index,
                                                                         filename="nofile",
                                                                         **fio_cmd_args)
                        fun_test.sleep("Fio write threadzz", seconds=1)

                fun_test.sleep("Fio write threads started", 10)
                try:
                    for i, host in enumerate(self.hosts):
                        fun_test.log("Joining fio write thread {}".format(i))
                        fun_test.join_thread(fun_test_thread_id=thread_id[i])
                        fun_test.log("FIO write command Output:")
                        fun_test.log(fun_test.shared_variables["fio"][i])
                        fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                             "FIO write test with host {}".format(host.name))
                        fio_output[i] = fun_test.shared_variables["fio"][i]
                except Exception as ex:
                    fun_test.critical(str(ex))
                    fun_test.log("FIO write command output from host {}:\n {}".format(host.name, fio_output[i]))
                    # Run dmesg to check the FIO failures
                    host.instance.sudo_command("dmesg")

                aggr_fio_output = {}
                for index, host in enumerate(self.hosts):
                    fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                         "FIO write test in host {}".format(host.name))
                    for op, stats in fun_test.shared_variables["fio"][index].items():
                        if op not in aggr_fio_output:
                            aggr_fio_output[op] = {}
                        aggr_fio_output[op] = Counter(aggr_fio_output[op]) + Counter(fio_output[i][op])

                fun_test.log("Aggregated FIO write command output after computation :\n{}".format(aggr_fio_output))

                # FIO read
                thread_id = {}
                end_host_thread = {}
                fio_output = {}

                fun_test.shared_variables["fio"] = {}
                for index, host in enumerate(self.hosts):
                    host.instance.sudo_command("dmesg -C") # cleaning the dmesg output of the previous runs
                    fun_test.log("Read IO to volume")
                    fio_output[index] = {}
                    end_host_thread[index] = host.instance.clone()
                    wait_time = len(self.hosts) - index
                    if "multiple_jobs" in self.fio_read_cmd_args:
                        fio_cmd_args = {}
                        # Adding the allowed CPUs into the fio command
                        # fio_cpus_allowed_args = " --cpus_allowed={}".format(host.host_numa_cpus)
                        jobs = ""
                        for id, device in enumerate(host.nvme_block_device_list):
                            jobs += " --name=vol{} --filename={}".format(id + 1, device)
                        size = " --size={}%".format(self.fio_io_size)
                        operation = " --rw={}".format(rd_mode)
                        blk_size = " --bs={}".format(bs)

                        fio_cmd_args["multiple_jobs"] = self.fio_read_cmd_args["multiple_jobs"] + \
                                                                operation + blk_size + \
                                                                size + jobs
                        fio_cmd_args["timeout"] = self.fio_read_cmd_args["timeout"]

                        thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                         func=fio_parser,
                                                                         arg1=end_host_thread[index],
                                                                         host_index=index,
                                                                         filename="nofile",
                                                                         **fio_cmd_args)
                        fun_test.sleep("Fio read threadzz", seconds=1)

                fun_test.sleep("Fio read threads started", 10)
                try:
                    for i, host in enumerate(self.hosts):
                        fun_test.log("Joining fio read thread {}".format(i))
                        fun_test.join_thread(fun_test_thread_id=thread_id[i])
                        fun_test.log("FIO read command Output:")
                        fun_test.log(fun_test.shared_variables["fio"][i])
                        fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                             "FIO read test with in host {}".format(host.name))
                        fio_output[i] = fun_test.shared_variables["fio"][i]
                except Exception as ex:
                    fun_test.critical(str(ex))
                    fun_test.log("FIO read command output from host {}:\n {}".format(host.name, fio_output[i]))
                    # Run dmesg to check the FIO failures
                    host.instance.sudo_command("dmesg")

                aggr_fio_output = {}
                for index, host in enumerate(self.hosts):
                    fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                         "FIO read test in host {}".format(host.name))
                    for op, stats in fun_test.shared_variables["fio"][index].items():
                        if op not in aggr_fio_output:
                            aggr_fio_output[op] = {}
                        aggr_fio_output[op] = Counter(aggr_fio_output[op]) + Counter(fio_output[i][op])

                fun_test.log("Aggregated FIO read command output after computation :\n{}".format(aggr_fio_output))


    def cleanup(self):
        pass


class DataIntegrityAfterReset(FunTestCase):

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
        self.ec_template = fun_test.shared_variables["ec_template"]
        self.vol_uuid_list = fun_test.shared_variables["vol_uuid_list"]
        self.fs_obj_list = fun_test.shared_variables["fs_obj_list"]

        fs = self.fs_obj_list[0]
        come = fs.get_come()
        self.sc_api = StorageControllerApi(api_server_ip=come.host_ip)

        # FIO write
        thread_id = {}
        end_host_thread = {}
        fio_output = {}

        fun_test.shared_variables["fio"] = {}
        for index, host in enumerate(self.hosts):
            host.instance.sudo_command("dmesg -C")  # cleaning the dmesg output of the previous runs
            fun_test.log("Write IO to volume")
            fio_output[index] = {}
            end_host_thread[index] = host.instance.clone()
            wait_time = len(self.hosts) - index
            if "multiple_jobs" in self.fio_write_cmd_args:
                fio_cmd_args = {}
                # Adding the allowed CPUs into the fio command
                # fio_cpus_allowed_args = " --cpus_allowed={}".format(host.host_numa_cpus)
                jobs = ""
                for id, device in enumerate(host.nvme_block_device_list):
                    jobs += " --name=vol{} --filename={}".format(id + 1, device)
                size = " --size={}%".format(self.fio_io_size)
                operation = " --rw=write"
                blk_size = " --bs=16k"

                fio_cmd_args["multiple_jobs"] = self.fio_write_cmd_args["multiple_jobs"] + \
                                                operation + blk_size + \
                                                size + jobs
                fio_cmd_args["timeout"] = self.fio_write_cmd_args["timeout"]

                thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                 func=fio_parser,
                                                                 arg1=end_host_thread[index],
                                                                 host_index=index,
                                                                 filename="nofile",
                                                                 **fio_cmd_args)
                fun_test.sleep("Fio write threadzz", seconds=1)

        fun_test.sleep("Fio write threads started", 10)
        try:
            for i, host in enumerate(self.hosts):
                fun_test.log("Joining fio write thread {}".format(i))
                fun_test.join_thread(fun_test_thread_id=thread_id[i])
                fun_test.log("FIO write command Output:")
                fun_test.log(fun_test.shared_variables["fio"][i])
                fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                     "FIO write test with host {}".format(host.name))
                fio_output[i] = fun_test.shared_variables["fio"][i]
        except Exception as ex:
            fun_test.critical(str(ex))
            fun_test.log("FIO write command output from host {}:\n {}".format(host.name, fio_output[i]))
            # Run dmesg to check the FIO failures
            host.instance.sudo_command("dmesg")

        aggr_fio_output = {}
        for index, host in enumerate(self.hosts):
            fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                 "FIO write test in host {}".format(host.name))
            for op, stats in fun_test.shared_variables["fio"][index].items():
                if op not in aggr_fio_output:
                    aggr_fio_output[op] = {}
                aggr_fio_output[op] = Counter(aggr_fio_output[op]) + Counter(fio_output[i][op])

        fun_test.log("Aggregated FIO write command output after computation :\n{}".format(aggr_fio_output))

        # Reset the fs and ensure all containers are up and api server is running
        total_reconnect_time = 600
        add_on_time = 180  # Needed for getting through 60 iterations of reconnect from host
        reboot_timer = FunTimer(max_time=total_reconnect_time + add_on_time)  # WORKAROUND, why do we need so much time
        self.reset_and_health_check(self.fs_obj_list[0])
        fun_test.sleep(message="Wait before checking the state of the DPU's", seconds=60)
        num_dpus = 1
        fun_test.test_assert_expected(expected=1,
                                      actual=self.ec_template.get_online_dpus(dpu_indexes=[0]),
                                      message="Make sure {} DPUs are online".format(num_dpus))

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

        # FIO read
        thread_id = {}
        end_host_thread = {}
        fio_output = {}

        fun_test.shared_variables["fio"] = {}
        for index, host in enumerate(self.hosts):
            host.instance.sudo_command("dmesg -C")  # cleaning the dmesg output of the previous runs
            fun_test.log("Read IO to volume")
            fio_output[index] = {}
            end_host_thread[index] = host.instance.clone()
            wait_time = len(self.hosts) - index
            if "multiple_jobs" in self.fio_read_cmd_args:
                fio_cmd_args = {}
                # Adding the allowed CPUs into the fio command
                # fio_cpus_allowed_args = " --cpus_allowed={}".format(host.host_numa_cpus)
                jobs = ""
                for id, device in enumerate(host.nvme_block_device_list):
                    jobs += " --name=vol{} --filename={}".format(id + 1, device)
                size = " --size={}%".format(self.fio_io_size)
                operation = " --rw=read"
                blk_size = " --bs=16k"

                fio_cmd_args["multiple_jobs"] = self.fio_read_cmd_args["multiple_jobs"] + \
                                                operation + blk_size + \
                                                size + jobs
                fio_cmd_args["timeout"] = self.fio_read_cmd_args["timeout"]

                thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                 func=fio_parser,
                                                                 arg1=end_host_thread[index],
                                                                 host_index=index,
                                                                 filename="nofile",
                                                                 **fio_cmd_args)
                fun_test.sleep("Fio read threadzz", seconds=1)

        fun_test.sleep("Fio read threads started", 10)
        try:
            for i, host in enumerate(self.hosts):
                fun_test.log("Joining fio read thread {}".format(i))
                fun_test.join_thread(fun_test_thread_id=thread_id[i])
                fun_test.log("FIO read command Output:")
                fun_test.log(fun_test.shared_variables["fio"][i])
                fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                     "FIO read test with in host {}".format(host.name))
                fio_output[i] = fun_test.shared_variables["fio"][i]
        except Exception as ex:
            fun_test.critical(str(ex))
            fun_test.log("FIO read command output from host {}:\n {}".format(host.name, fio_output[i]))
            # Run dmesg to check the FIO failures
            host.instance.sudo_command("dmesg")

        aggr_fio_output = {}
        for index, host in enumerate(self.hosts):
            fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                 "FIO read test in host {}".format(host.name))
            for op, stats in fun_test.shared_variables["fio"][index].items():
                if op not in aggr_fio_output:
                    aggr_fio_output[op] = {}
                aggr_fio_output[op] = Counter(aggr_fio_output[op]) + Counter(fio_output[i][op])

        fun_test.log("Aggregated FIO read command output after computation :\n{}".format(aggr_fio_output))

    def cleanup(self):
        pass

    def reset_and_health_check(self, fs_obj):
        fs_obj.reset(hard=False)
        fun_test.test_assert(fs_obj.come.ensure_expected_containers_running(), "All containers are up")
        fun_test.test_assert(expression=self.ec_template.get_health(fs_obj),
                             message="{}: API server health".format(fs_obj))

if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(DateIntegrityCheck())
    setup_bringup.add_test_case(DataIntegrityAfterReset())
    setup_bringup.run()
