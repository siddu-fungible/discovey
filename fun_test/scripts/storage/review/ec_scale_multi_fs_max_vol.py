from lib.system.fun_test import *
fun_test.enable_storage_api()
from lib.system import utils
from lib.fun.fs import Fs
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_operations_template import EcVolumeOperationsTemplate
from swagger_client.models.volume_types import VolumeTypes
from scripts.storage.storage_helper import *
from scripts.networking.helper import *
from lib.host.linux import Linux
from lib.templates.storage.storage_controller_api import *

'''
Script for C18036: Multi DPU: Maximum number(n*128) of volumes supported(expected 32 * 128)
'''


class ECBlockScaleScript(FunTestScript):
    topology = None
    testbed_type = fun_test.get_job_environment_variable("test_bed_type")

    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. Bring up F1 with funos 
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

        self.sc_template = EcVolumeOperationsTemplate(topology=self.topology)
        self.sc_template.initialize(already_deployed=already_deployed, dpu_indexes=dpu_index)
        fun_test.shared_variables["ec_template"] = self.sc_template

        self.fs_obj_list = []
        for dut_index in self.topology.get_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            self.fs_obj_list.append(fs_obj)
        fun_test.shared_variables["fs_obj_list"] = self.fs_obj_list
        
    def cleanup(self):
        self.sc_template.cleanup()
        self.topology.cleanup()

class CreateAttachDetachDeleteMultivolMultihost(FunTestCase):

    def describe(self):

        self.set_test_details(id=1,
                              summary="Create/attach/connect/disconnect/detach/delete with I/O",
                              steps='''
                              1. Make sure API server is up and running
                              2. Create a Volume using API Call
                              3. Attach Volume to a remote host
                              4. Run FIO from host 
                              5. Perform nvme disconnect after I/O
                              6. Detach volume
                              7. Delete volume 
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
        if "num_volumes" in job_inputs:
            self.num_volumes = job_inputs["num_volumes"]
        if "test_iteration_count" in job_inputs:
            self.test_iteration_count = job_inputs["test_iteration_count"]

        '''if "warmup_jobs" in job_inputs:
            self.warm_up_fio_cmd_args["multiple_jobs"] = self.warm_up_fio_cmd_args["multiple_jobs"]. \
                replace("numjobs=1", "numjobs={}".format(job_inputs["warmup_jobs"]))'''


        fun_test.shared_variables["num_volumes"] = self.num_volumes

        self.available_hosts = self.topology.get_available_hosts()
        self.host_objs = self.available_hosts.values()

        self.host_info = {}
        # Populating the linux handles of the hosts
        for host_name, host_obj in self.available_hosts.items():
            self.host_info[host_name] = {}
            self.host_info[host_name]["test_interface"] = host_obj.get_test_interface(index=0)
            self.host_info[host_name]["ip"] = host_obj.get_test_interface(index=0).ip.split('/')[0]
            self.host_info[host_name]["handle"] = host_obj.get_instance()

        fun_test.log("test info: capacity: {} ".format(self.ec_info["capacity"]))
        fun_test.log("test info: num_volumes: {} ".format(self.num_volumes))
        fun_test.log("test info: test_iteration_count: {} ".format(self.test_iteration_count))

        # chars = string.ascii_uppercase + string.ascii_lowercase
        for count in range(self.test_iteration_count):
            self.vol_uuid_list = []
            for i in range(self.num_volumes):
                name = "EC_" + testcase + "_" + str(num + 1)
                suffix = utils.generate_uuid(length=4)
                body_volume_intent_create = BodyVolumeIntentCreate(name=name,
                                                                   vol_type=self.ec_template.vol_type,
                                                                   capacity=self.ec_info["capacity"],
                                                                   compression_effort=self.ec_info["compression_effort"],
                                                                   allow_expansion=self.ec_info["allow_expansion"],
                                                                   stripe_count=self.ec_info["stripe_count"],
                                                                   encrypt=self.ec_info["encrypt"],
                                                                   data_protection=self.ec_info["data_protection"])
                
                vol_uuid = self.ec_template.create_volume(self.fs_obj_list, body_volume_intent_create)
                fun_test.test_assert(expression=vol_uuid[0], message="Create Volume{} Successful with uuid {}".format(i+1, vol_uuid[0]))
                self.vol_uuid_list.append(vol_uuid[0])

            # index = 0
            # count = 0
            hosts = self.topology.get_available_host_instances()
            attach_vol_result = self.ec_template.attach_m_vol_n_host(host_obj_list=hosts, fs_obj=fs_obj,
                                                                     volume_uuid_list=self.vol_uuid_list,
                                                                     validate_nvme_connect=False,
                                                                     raw_api_call=True,
                                                                     nvme_io_queues=None,
                                                                     volume_is_shared=False)

            fun_test.test_assert(expression=attach_vol_result, message="Attach Volume Successful")

            for host, data in attach_vol_result.items():
                nvme_connect_result = self.ec_template.nvme_connect_from_host(host_obj=host,
                                                                              subsys_nqn=data[0]["data"]["subsys_nqn"],
                                                                              host_nqn=data[0]["data"]["host_nqn"],
                                                                              dataplane_ip=data[0]["data"]["ip"])
                fun_test.test_assert_expected(expected=True, actual=nvme_connect_result,
                                              message="nvme connect successful")
                #fun_test.sleep(message="Wait for nvme devices to appear on host", seconds=30)
                # Check number of volumes and devices found from hosts
                #for host in hosts:
                host.nvme_block_device_list = []
                nvme_devices = self.ec_template.get_host_nvme_device(host_obj=host)
                if nvme_devices:
                    if isinstance(nvme_devices, list):
                        for nvme_device in nvme_devices:
                            current_device = "/dev/" + nvme_device
                            host.nvme_block_device_list.append(current_device)
                    else:
                        current_device = "/dev/" + nvme_devices
                        host.nvme_block_device_list.append(current_device)
                fun_test.test_assert_expected(expected=len(attach_vol_result[host]),
                                              actual=len(host.nvme_block_device_list),
                                              message="Check number of nvme block devices found "
                                                      "on host {} matches with attached ".format(host.name))

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
                        self.host_info[host_name]["host_numa_cpus"] = fetch_numa_cpus(host_handle,
                                                                                      self.ethernet_adapter)

            fun_test.shared_variables["host_info"] = self.host_info

            fun_test.log("Hosts info: {}".format(self.host_info))

            '''self.fio_io_size = 100 / len(self.host_info)
            # self.offsets = ["1%", "26%", "51%", "76%"]

            thread_id = {}
            end_host_thread = {}
            fio_output = {}
            fio_offset = 1

            fun_test.shared_variables["fio"] = {}
            for index, host_name in enumerate(self.host_info):
                fun_test.log("Initial Write IO to volume, this might take long time depending on fio --size "
                             "provided")
                fio_output[index] = {}
                end_host_thread[index] = self.host_info[host_name]["handle"].clone()
                wait_time = len(self.host_info) - index
                if "multiple_jobs" in self.warm_up_fio_cmd_args:
                    warm_up_fio_cmd_args = {}
                    # Adding the allowed CPUs into the fio warmup command
                    fio_cpus_allowed_args = " --cpus_allowed={}".format(self.host_info[host_name]["host_numa_cpus"])
                    jobs = ""
                    for id, device in enumerate(host.nvme_block_device_list):
                        jobs += " --name=vol{} --filename={}".format(id + 1, device)
                    #offset = " --offset={}%".format(fio_offset - 1 if fio_offset - 1 else fio_offset)
                    size = " --size={}%".format(self.fio_io_size)
                    #warm_up_fio_cmd_args["multiple_jobs"] = self.warm_up_fio_cmd_args["multiple_jobs"] + \
                    #                                        fio_cpus_allowed_args + offset + size + jobs
                    warm_up_fio_cmd_args["multiple_jobs"] = self.warm_up_fio_cmd_args["multiple_jobs"] + \
                                                            fio_cpus_allowed_args  + size + jobs
                    warm_up_fio_cmd_args["timeout"] = self.warm_up_fio_cmd_args["timeout"]

                    thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                     func=fio_parser,
                                                                     arg1=end_host_thread[index],
                                                                     host_index=index,
                                                                     filename="nofile",
                                                                     **warm_up_fio_cmd_args)
                    #fio_offset += self.fio_io_size
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

            fun_test.log("Aggregated FIO Command Output:\n{}".format(aggr_fio_output))'''

            self.ec_template.cleanup()
            fun_test.test_assert(expression=True, message="Iteration {} completed".format(count+1))

    def run(self):
        pass

    def cleanup(self):
        fun_test.shared_variables["storage_controller_template"] = self.ec_template

if __name__ == "__main__":
    script = ECBlockScaleScript()
    script.add_test_case(CreateAttachDetachDeleteMultivolMultihost())
    script.run()
