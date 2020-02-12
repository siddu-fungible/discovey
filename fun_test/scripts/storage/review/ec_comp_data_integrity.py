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


        topology_helper = TopologyHelper()
        self.topology = topology_helper.deploy(already_deployed=self.already_deployed)
        fun_test.test_assert(self.topology, "Topology deployed")
        fun_test.shared_variables["topology"] = self.topology
        self.ec_template = EcVolumeOperationsTemplate(topology=self.topology)
        self.ec_template.initialize(dpu_indexes=[0], already_deployed=self.already_deployed)
        fun_test.shared_variables["ec_template"] = self.ec_template
        self.fs_obj_list = []
        for dut_index in self.topology.get_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            self.fs_obj_list.append(fs_obj)

        fun_test.shared_variables["fs_obj_list"] = self.fs_obj_list

        # self.fs_obj_list = fun_test.shared_variables["fs_obj_list"]


    def cleanup(self):

        self.ec_template.cleanup()
        self.topology.cleanup()


class DataIntegrityTest(FunTestCase):

    def describe(self):

        self.set_test_details(id=1,
                              summary="Create Volume using API and run IO from host",
                              steps='''
                              1. Make sure API server is up and running
                              2. Create EC Volume using API Call
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
            self.num_host = job_inputs["num_hosts"]

        self.vol_uuid_list = []
        fun_test.shared_variables["ec_count"] = self.ec_count
        vol_type = VolumeTypes().EC
        
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
        self.ec_count = len(self.effort_levels)
        for i,e in zip(range(self.ec_count), self.effort_levels):
            suffix = utils.generate_uuid(length=4)
            body_volume_intent_create = BodyVolumeIntentCreate(name=self.name + suffix + str(i), vol_type=vol_type,
                                                               capacity=self.capacity, compression_effort=e,
                                                               encrypt=False, data_protection={"num_redundant_dpus": 0,
                                                                                               "num_failed_disks": 2})
            vol_uuid = self.ec_template.create_volume(self.fs_obj_list, body_volume_intent_create)
            fun_test.test_assert(expression=vol_uuid[0], message="Create Volume Successful")
            self.vol_uuid_list.append(vol_uuid[0])

        for i in range(self.ec_count):
            attach_vol_result = self.ec_template.attach_volume(self.fs_obj_list[0],
                                                                self.vol_uuid_list[i],
                                                                self.host_objs,
                                                                validate_nvme_connect=True,
                                                                raw_api_call=True)
            fun_test.test_assert(expression=attach_vol_result, message="Attach Volume Successful")

        for host_name in self.host_info:
            self.host_info[host_name]["num_volumes"] = self.ec_count

        # Populating the NVMe devices available to the hosts
        for host_name in self.host_info:
            host_obj = self.available_hosts[host_name]
            self.host_info[host_name]["nvme_block_device_list"] = []
            for namespace in self.ec_template.host_nvme_device[host_obj]:
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

    def run(self):

        self.fio_io_size = 100
        # FIO Write
        thread_id = {}
        end_host_thread = {}
        fio_output = {}

        fun_test.shared_variables["fio"] = {}
        for index, host_name in enumerate(self.host_info):
            fun_test.log("Initial Write IO to volume, this might take long time depending on fio --size "
                         "provided")
            fio_output[index] = {}
            end_host_thread[index] = self.host_info[host_name]["handle"].clone()
            wait_time = len(self.host_info) - index
            if "multiple_jobs" in self.fio_write_cmd_args:
                fio_cmd_args = {}
                # Adding the allowed CPUs into the fio command
                fio_cpus_allowed_args = " --cpus_allowed={}".format(self.host_info[host_name]["host_numa_cpus"])
                jobs = ""
                for id, device in enumerate(self.host_info[host_name]["nvme_block_device_list"]):
                    jobs += " --name=vol{} --filename={}".format(id + 1, device)
                size = " --size={}%".format(self.fio_io_size)
                fio_cmd_args["multiple_jobs"] = self.fio_write_cmd_args["multiple_jobs"] + \
                                                        fio_cpus_allowed_args + size + jobs
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
            for i, host_name in enumerate(self.host_info):
                fun_test.log("Joining fio thread {}".format(i))
                fun_test.join_thread(fun_test_thread_id=thread_id[i])
                fun_test.log("FIO write Command Output:")
                fun_test.log(fun_test.shared_variables["fio"][i])
                fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                     "FIO write test with verify=md5 in host {}".format(host_name))
                fio_output[i] = fun_test.shared_variables["fio"][i]
        except Exception as ex:
            fun_test.critical(str(ex))
            fun_test.log("FIO Write Command Output from host {}:\n {}".format(host_name, fio_output[i]))

        aggr_fio_output = {}
        for index, host_name in enumerate(self.host_info):
            for op, stats in fun_test.shared_variables["fio"][index].items():
                if op not in aggr_fio_output:
                    aggr_fio_output[op] = {}
                aggr_fio_output[op] = Counter(aggr_fio_output[op]) + Counter(fio_output[i][op])

        fun_test.log("Aggregated FIO Write Command Output:\n{}".format(aggr_fio_output))

        # FIO Read
        thread_id = {}
        end_host_thread = {}
        fio_output = {}
        fio_offset = 1

        fun_test.shared_variables["fio"] = {}
        for index, host_name in enumerate(self.host_info):
            fun_test.log("Initial Read IO to volume")
            fio_output[index] = {}
            end_host_thread[index] = self.host_info[host_name]["handle"].clone()
            wait_time = len(self.host_info) - index
            if "multiple_jobs" in self.fio_read_cmd_args:
                fio_cmd_args = {}
                # Adding the allowed CPUs into the fio command
                fio_cpus_allowed_args = " --cpus_allowed={}".format(self.host_info[host_name]["host_numa_cpus"])
                jobs = ""
                for id, device in enumerate(self.host_info[host_name]["nvme_block_device_list"]):
                    jobs += " --name=vol{} --filename={}".format(id + 1, device)
                size = " --size={}%".format(self.fio_io_size)
                fio_cmd_args["multiple_jobs"] = self.fio_read_cmd_args["multiple_jobs"] + \
                                                        fio_cpus_allowed_args + size + jobs
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
            for i, host_name in enumerate(self.host_info):
                fun_test.log("Joining fio thread {}".format(i))
                fun_test.join_thread(fun_test_thread_id=thread_id[i])
                fun_test.log("FIO read Command Output:")
                fun_test.log(fun_test.shared_variables["fio"][i])
                fun_test.test_assert(fun_test.shared_variables["fio"][i],
                                     "FIO read test with do_verify in host {}".format(host_name))
                fio_output[i] = fun_test.shared_variables["fio"][i]
        except Exception as ex:
            fun_test.critical(str(ex))
            fun_test.log("FIO Command Output from host {}:\n {}".format(host_name, fio_output[i]))

        aggr_fio_output = {}
        for index, host_name in enumerate(self.host_info):
            for op, stats in fun_test.shared_variables["fio"][index].items():
                if op not in aggr_fio_output:
                    aggr_fio_output[op] = {}
                aggr_fio_output[op] = Counter(aggr_fio_output[op]) + Counter(fio_output[i][op])

        fun_test.log("Aggregated FIO Read Command Output:\n{}".format(aggr_fio_output))


    def cleanup(self):
        fun_test.shared_variables["storage_controller_template"] = self.ec_template


if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(DataIntegrityTest())
    setup_bringup.run()
