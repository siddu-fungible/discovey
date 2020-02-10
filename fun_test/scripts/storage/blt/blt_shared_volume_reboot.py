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
import string, random
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

        if "already_deployed" in job_inputs:
            self.already_deployed = job_inputs["already_deployed"]
        else:
            self.already_deployed = False

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
        self.blt_template.initialize(dpu_indexes=[0], already_deployed=self.already_deployed)
        fun_test.shared_variables["blt_template"] = self.blt_template
        self.fs_obj_list = []
        for dut_index in self.topology.get_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            self.fs_obj_list.append(fs_obj)

        fun_test.shared_variables["fs_obj_list"] = self.fs_obj_list

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
        if "capacity" in job_inputs:
            self.capacity = job_inputs["capacity"]
        if "blt_count" in job_inputs:
            self.blt_count = job_inputs["blt_count"]
        if "num_hosts" in job_inputs:
            self.num_host = job_inputs["num_hosts"]

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

        self.available_hosts = self.topology.get_available_hosts()
        self.host_objs = self.available_hosts.values()

        self.host_info = {}
        # Populating the linux handles of the hosts
        for host_name, host_obj in self.available_hosts.items():
            self.host_info[host_name] = {}
            self.host_info[host_name]["test_interface"] = host_obj.get_test_interface(index=0)
            self.host_info[host_name]["ip"] = host_obj.get_test_interface(index=0).ip.split('/')[0]
            self.host_info[host_name]["handle"] = host_obj.get_instance()

        # chars = string.ascii_uppercase + string.ascii_lowercase
        for i in range(self.blt_count):
            suffix = utils.generate_uuid(length=4)
            body_volume_intent_create = BodyVolumeIntentCreate(name=self.name + suffix + str(i), vol_type=vol_type,
                                                               capacity=self.capacity, compression_effort=False,
                                                               encrypt=False, data_protection={})
            vol_uuid = self.blt_template.create_volume(self.fs_obj_list, body_volume_intent_create)
            fun_test.test_assert(expression=vol_uuid[0], message="Create Volume Successful")
            self.vol_uuid_list.append(vol_uuid[0])

        for i in range(self.blt_count):
            attach_vol_result = self.blt_template.attach_volume(self.fs_obj_list[0],
                                                                self.vol_uuid_list[i],
                                                                self.host_objs,
                                                                validate_nvme_connect=True,
                                                                raw_api_call=True)
            fun_test.test_assert(expression=attach_vol_result, message="Attach Volume Successful")

        for host_name in self.host_info:
            self.host_info[host_name]["num_volumes"] = self.blt_count

        # Populating the NVMe devices available to the hosts
        for host_name in self.host_info:
            host_obj = self.available_hosts[host_name]
            self.host_info[host_name]["nvme_block_device_list"] = []
            for namespace in self.blt_template.host_nvme_device[host_obj]:
                self.host_info[host_name]["nvme_block_device_list"].append("/dev/{}".format(namespace))
            fun_test.log("Available NVMe devices: {}".format(self.host_info[host_name]["nvme_block_device_list"]))
            fun_test.test_assert_expected(expected=self.host_info[host_name]["num_volumes"],
                                          actual=len(self.host_info[host_name]["nvme_block_device_list"]),
                                          message="Expected NVMe devices are available")
            self.host_info[host_name]["nvme_block_device_list"].sort()
            self.host_info[host_name]["fio_filename"] = ":".join(self.host_info[host_name]["nvme_block_device_list"])

        # Extracting the host CPUs
        for host_name in self.host_info:
            host_handle = self.host_info[host_name]["handle"]
            if host_name.startswith("cab0"):
                if self.override_numa_node["override"]:
                    host_numa_cpus_filter = host_handle.lscpu("node[01]")
                    self.host_info[host_name]["host_numa_cpus"] = ",".join(host_numa_cpus_filter.values())
            else:
                if self.override_numa_node["override"]:
                    host_numa_cpus_filter = host_handle.lscpu(self.override_numa_node["override_node"])
                    self.host_info[host_name]["host_numa_cpus"] = host_numa_cpus_filter[
                        self.override_numa_node["override_node"]]
                else:
                    self.host_info[host_name]["host_numa_cpus"] = fetch_numa_cpus(host_handle, self.ethernet_adapter)

        fun_test.shared_variables["host_info"] = self.host_info
        fun_test.log("Hosts info: {}".format(self.host_info))
        fun_test.shared_variables["host_info"] = self.host_info

    def run(self):


        for mode in self.fio_cmds[2]:
            #  ["write,4k,0","read,4k,1"]

            param, bs, data_integrity = mode.split(",")
            self.fio_io_size = 100 / len(self.host_info)
            # self.offsets = ["1%", "26%", "51%", "76%"]

            thread_id = {}
            end_host_thread = {}
            fio_output = {}
            fio_offset = 1

            fun_test.shared_variables["fio"] = {}
            for index, host_name in enumerate(self.host_info):
                fun_test.log("Initial {} IO to volume, this might take long time depending on fio --size "
                             "provided".format(param))
                fio_output[index] = {}
                end_host_thread[index] = self.host_info[host_name]["handle"].clone()
                wait_time = len(self.host_info) - index
                if "multiple_jobs" in self.warm_up_fio_cmd_args:
                    warm_up_fio_cmd_args = {}
                    # Adding the allowed CPUs into the fio warmup command
                    fio_cpus_allowed_args = " --cpus_allowed={}".format(self.host_info[host_name]["host_numa_cpus"])
                    jobs = ""
                    for id, device in enumerate(self.host_info[host_name]["nvme_block_device_list"]):
                        jobs += " --name=vol{} --filename={}".format(id + 1, device)
                    fio_bs = " --bs={}".format(bs)
                    fio_param = " --rw={}".format(param)
                    fio_data_integrity = " --do_verify={} --verify=md5".format(data_integrity)
                    offset = " --offset={}%".format(fio_offset - 1 if fio_offset - 1 else fio_offset)
                    size = " --size={}%".format(self.fio_io_size)
                    warm_up_fio_cmd_args["multiple_jobs"] = fio_param + fio_bs + self.warm_up_fio_cmd_args["multiple_jobs"] + \
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
                for i, host_name in enumerate(self.host_info):
                    fun_test.log("Joining fio thread {}".format(i))
                    fun_test.join_thread(fun_test_thread_id=thread_id[i])
                    fun_test.log("FIO Command Output:")
                    fun_test.log(fun_test.shared_variables["fio"][i])
                    fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                         "FIO randwrite test with IO depth 16 in host {}".format(host_name))
                    fio_output[i] = fun_test.shared_variables["fio"][i]
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("FIO Command Output from host {}:\n {}".format(host_name, fio_output[i]))

            aggr_fio_output = {}
            for index, host_name in enumerate(self.host_info):
                fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                     "FIO randwrite test with IO depth 16 in host {}".format(host_name))
                for op, stats in fun_test.shared_variables["fio"][index].items():
                    if op not in aggr_fio_output:
                        aggr_fio_output[op] = {}
                    aggr_fio_output[op] = Counter(aggr_fio_output[op]) + Counter(fio_output[i][op])

            fun_test.log("Aggregated FIO Command Output:\n{}".format(aggr_fio_output))

            for op, stats in aggr_fio_output.items():
                for field, value in stats.items():
                    if field == "iops":
                        aggr_fio_output[op][field] = int(round(value))
                    if field == "bw":
                        # Converting the KBps to MBps
                        aggr_fio_output[op][field] = int(round(value / 1000))
                    if "latency" in field:
                        aggr_fio_output[op][field] = int(round(value) / len(self.host_info))
                    # Converting the runtime from milliseconds to seconds and taking the average out of it
                    if field == "runtime":
                        aggr_fio_output[op][field] = int(round(value / 1000) / len(self.host_info))

            fun_test.log("Aggregated FIO Command Output:\n{}".format(aggr_fio_output))

    def cleanup(self):
        pass


class ConfigPeristenceAfterReset(FunTestCase):
    topology = None

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

        self.topology = fun_test.shared_variables["topology"]
        # fun_test.shared_variables["blt_template"] = self.blt_template
        self.blt_template = fun_test.shared_variables["blt_template"]
        # self.storage_controller_template = fun_test.shared_variables["storage_controller_template"]
        threads_list = []
        for dut_index in self.topology.get_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            thread_id = fun_test.execute_thread_after(time_in_seconds=2, func=self.reset_and_health_check,
                                                      fs_obj=fs_obj)
            threads_list.append(thread_id)

        for thread_id in threads_list:
            fun_test.join_thread(fun_test_thread_id=thread_id, sleep_time=1)
        fun_test.sleep(message="Wait before firing Dataplane IP commands", seconds=60)
        for dut_index in self.topology.get_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            self.storage_controller_template.verify_dataplane_ip(storage_controller=fs_obj.get_storage_controller(),
                                                                 dut_index=dut_index)

    def run(self):

        self.host_info = fun_test.shared_variables["host_info"]

        for host_name in self.host_info:
            host_obj = self.available_hosts[host_name]
            self.host_info[host_name]["nvme_block_device_list"] = []
            for namespace in self.blt_template.host_nvme_device[host_obj]:
                self.host_info[host_name]["nvme_block_device_list_after_reboot"].append("/dev/{}".format(namespace))
            fun_test.log("Available NVMe devices after reboot: {}".format(self.host_info[host_name]["nvme_block_device_list_after_reboot"]))
            fun_test.test_assert_expected(expected=len(self.host_info[host_name]["nvme_block_device_list_after_reboot"]),
                                          actual=len(self.host_info[host_name]["nvme_block_device_list"]),
                                          message="Expected number of NVMe devices available after reboot")
            res = sorted(self.host_info[host_name]["nvme_block_device_list_after_reboot"]) == sorted(self.host_info[host_name]["nvme_block_device_list"])
                #fun_test.test_assert()
            fun_test.test_assert(res, "nvme devices names are valid {}".format(self.host_name[host_name]["nvme_block_device_list_after_reboot"]))

        for mode in self.fio_cmds[-1]:
                #  ["write,4k,0","read,4k,1"]

            param, bs, data_integrity = mode.split(",")
            self.fio_io_size = 100 / len(self.host_info)
            thread_id = {}
            end_host_thread = {}
            fio_output = {}
            fio_offset = 1

            for index, host_name in enumerate(self.host_info):
                fun_test.log("checking the data integrity after reboot")
                fio_output[index] = {}
                end_host_thread[index] = self.host_info[host_name]["handle"].clone()
                wait_time = len(self.host_info) - index
                if "multiple_jobs" in self.warm_up_fio_cmd_args:
                    warm_up_fio_cmd_args = {}
                    # Adding the allowed CPUs into the fio warmup command
                    fio_cpus_allowed_args = " --cpus_allowed={}".format(self.host_info[host_name]["host_numa_cpus"])
                    jobs = ""
                    for id, device in enumerate(self.host_info[host_name]["nvme_block_device_list"]):
                        jobs += " --name=vol{} --filename={}".format(id + 1, device)
                    offset = " --offset={}%".format(fio_offset)
                    size = " --size={}%".format(self.fio_io_size)
                    fio_bs = " --bs={}".format(bs)
                    fio_param = " --rw={}".format(fio_param)
                    fio_data_integrity = " --do_verify={} --verify=md5".format(data_integrity)

                    warm_up_fio_cmd_args["multiple_jobs"] = self.warm_up_fio_cmd_args["multiple_jobs"] + \
                                                            fio_cpus_allowed_args + offset + size + str(jobs)
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
                for i, host_name in enumerate(self.host_info):
                    fun_test.log("Joining fio thread {}".format(i))
                    fun_test.join_thread(fun_test_thread_id=thread_id[i])
                    fun_test.log("FIO Command Output:")
                    fun_test.log(fun_test.shared_variables["fio"][i])
                    fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                         "FIO randwrite test with IO depth 16 in host {}".format(host_name))
                    fio_output[i] = fun_test.shared_variables["fio"][i]
            except Exception as ex:
                fun_test.critical(str(ex))
                fun_test.log("FIO Command Output from host {}:\n {}".format(host_name, fio_output[i]))

            aggr_fio_output = {}
            for index, host_name in enumerate(self.host_info):
                fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                     "FIO randwrite test with IO depth 16 in host {}".format(host_name))
                for op, stats in fun_test.shared_variables["fio"][index].items():
                    if op not in aggr_fio_output:
                        aggr_fio_output[op] = {}
                    aggr_fio_output[op] = Counter(aggr_fio_output[op]) + Counter(fio_output[i][op])

            fun_test.log("Aggregated FIO Command Output:\n{}".format(aggr_fio_output))

            for op, stats in aggr_fio_output.items():
                for field, value in stats.items():
                    if field == "iops":
                        aggr_fio_output[op][field] = int(round(value))
                    if field == "bw":
                        # Converting the KBps to MBps
                        aggr_fio_output[op][field] = int(round(value / 1000))
                    if "latency" in field:
                        aggr_fio_output[op][field] = int(round(value) / len(self.host_info))
                    # Converting the runtime from milliseconds to seconds and taking the average out of it
                    if field == "runtime":
                        aggr_fio_output[op][field] = int(round(value / 1000) / len(self.host_info))

            fun_test.log("Aggregated FIO Command Output:\n{}".format(aggr_fio_output))

    def cleanup(self):
        self.blt_template.cleanup()

    def reset_and_health_check(self, fs_obj):
        fs_obj.reset()
        fs_obj.come.ensure_expected_containers_running()
        fun_test.test_assert(expression=self.blt_template.get_health(
            storage_controller=fs_obj.get_storage_controller()),
            message="{}: API server health".format(fs_obj))


if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(SharedVolumePerfTest())
    setup_bringup.add_test_case(ConfigPeristenceAfterReset())
    setup_bringup.run()
