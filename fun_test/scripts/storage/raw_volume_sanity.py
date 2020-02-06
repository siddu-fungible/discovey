

from lib.system.fun_test import *

fun_test.enable_storage_api()
from lib.system import utils
from lib.host.linux import Linux
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_operations_template import BltVolumeOperationsTemplate
from swagger_client.models.volume_types import VolumeTypes
from scripts.storage.storage_helper import *


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
        online_dpu_count = 1
        already_deployed = True
        topology_helper = TopologyHelper()
        self.topology = topology_helper.deploy(already_deployed=already_deployed)
        fun_test.test_assert(self.topology, "Topology deployed")
        fun_test.shared_variables["topology"] = self.topology
        self.storage_controller_template = BltVolumeOperationsTemplate(topology=self.topology)
        self.storage_controller_template.initialize(online_dpu_count=online_dpu_count,
                                                    already_deployed=already_deployed)
        fun_test.shared_variables["storage_controller_template"] = self.storage_controller_template


    def cleanup(self):
        self.topology.cleanup()


class BltApiStorageTest (FunTestCase):
    topology = None
    storage_controller_template = None

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
        self.storage_controller_template = fun_test.shared_variables["storage_controller_template"]
        self.fs_obj_list = []
        for dut_index in self.topology.get_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            self.fs_obj_list.append(fs_obj)

        print("fs_obj list is ",self.fs_obj_list)



        benchmark_parsing = True
        benchmark_file = fun_test.get_script_name_without_ext() + ".json"
        fun_test.log("Benchmark file being used: {}".format(benchmark_file))

        benchmark_dict = {}
        benchmark_dict = utils.parse_file_to_json(benchmark_file)

        if testcase not in benchmark_dict or not benchmark_dict[testcase]:
            benchmark_parsing = False
            fun_test.critical("Benchmarking is not available for the current testcase {} in {} file".
                              format(testcase, benchmark_file))
            fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))
        fun_test.test_assert(benchmark_parsing, "Parsing Benchmark json file for this {} testcase".format(testcase))

        for k, v in benchmark_dict[testcase].iteritems():
            setattr(self, k, v)
        vol_uuid_list = []
        fun_test.shared_variables["blt_count"] = self.blt_count
        vol_type = VolumeTypes().LOCAL_THIN
        if self.DUT == 1:
            self.fs_obj = self.fs_obj_list[0]
        hosts = self.topology.get_available_host_instances()
        for i in range(self.blt_count):
            body_volume_intent_create = BodyVolumeIntentCreate(name=self.name + str(i), vol_type=vol_type,
                                                               capacity=self.capacity,
                                                               compression_effort=False,
                                                               encrypt=False, data_protection={})
            vol_uuid = self.storage_controller_template.create_volume(fs_obj=self.fs_obj_list,
                                                                      body_volume_intent_create=body_volume_intent_create)
            vol_uuid_list.append(vol_uuid)
            attach_vol_result = self.storage_controller_template.attach_volume(host_obj=hosts, fs_obj=fs_obj,
                                                                               volume_uuid=vol_uuid_list[i],
                                                                               validate_nvme_connect=True,
                                                                               raw_api_call=True)
            fun_test.test_assert(expression=attach_vol_result, message="Attach Volume Successful")
            if vol_uuid[0] != attach_vol_result["data"]["uuid"]:
                fun_test.test_assert(expression=attach_vol_result, message="created volume is not attached")

    def run(self):

        obj = single_fs_setup(self, set_dataplane_ips=False)
        obj.offsets = ["1%", "26%", "51%", "76%"]
        thread_id = {}
        end_host_thread = {}
        fio_output = {}
        for index, host_name in enumerate(obj.host_info):
            fun_test.log("Initial Write IO to volume, this might take long time depending on fio --size "
                         "provided")

            jobs = ""
            fio_output[index] = {}
            end_host_thread[index] = obj.host_info[host_name]["handle"].clone()
            wait_time = obj.num_hosts - index
            if "multiple_jobs" in obj.warm_up_fio_cmd_args:
                # Adding the allowed CPUs into the fio warmup command
                # self.warm_up_fio_cmd_args["multiple_jobs"] += "  --cpus_allowed={}".\
                #    format(self.host_info[host_name]["host_numa_cpus"])
                fio_cpus_allowed_args = " --cpus_allowed={}".format(obj.host_info[host_name]["host_numa_cpus"])
                for id, device in enumerate(obj.host_info[host_name]["nvme_block_device_list"]):
                    jobs += " --name=vol{} --filename={}".format(id + 1, device)
                obj.warm_up_fio_cmd_args["multiple_jobs"] = obj.warm_up_fio_cmd_args["multiple_jobs"] + obj.offsets[
                    index] + str(
                    fio_cpus_allowed_args) + str(jobs)
                obj.warm_up_fio_cmd_args["timeout"] = obj.warm_up_fio_cmd_args["timeout"]
                # fio_output = self.host_handles[key].pcie_fio(filename="nofile", timeout=self.warm_up_fio_cmd_args["timeout"],
                #                                    **warm_up_fio_cmd_args)
                thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                 func=fio_parser,
                                                                 arg1=end_host_thread[index],
                                                                 host_index=index,
                                                                 filename="nofile",
                                                                 **warm_up_fio_cmd_args)


    def cleanup(self):
        fun_test.shared_variables["storage_controller_template"] = self.storage_controller_template


class ConfigPeristenceAfterReset(FunTestCase):
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
        self.topology = fun_test.shared_variables["topology"]
        self.storage_controller_template = fun_test.shared_variables["storage_controller_template"]
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
        obj = single_fs_setup(self, set_dataplane_ips=False)
        obj.offsets = ["1%", "26%", "51%", "76%"]
        thread_id = {}
        end_host_thread = {}
        fio_output = {}
        for index, host_name in enumerate(obj.host_info):
            fun_test.log("Initial Write IO to volume, this might take long time depending on fio --size "
                         "provided")

            jobs = ""
            fio_output[index] = {}
            end_host_thread[index] = obj.host_info[host_name]["handle"].clone()
            wait_time = obj.num_hosts - index
            if "multiple_jobs" in obj.warm_up_fio_cmd_args:
                # Adding the allowed CPUs into the fio warmup command
                # self.warm_up_fio_cmd_args["multiple_jobs"] += "  --cpus_allowed={}".\
                #    format(self.host_info[host_name]["host_numa_cpus"])
                fio_cpus_allowed_args = " --cpus_allowed={}".format(obj.host_info[host_name]["host_numa_cpus"])
                for id, device in enumerate(obj.host_info[host_name]["nvme_block_device_list"]):
                    jobs += " --name=vol{} --filename={}".format(id + 1, device)
                obj.warm_up_fio_cmd_args["multiple_jobs"] = obj.warm_up_fio_cmd_args["multiple_jobs"] + obj.offsets[
                    index] + str(
                    fio_cpus_allowed_args) + str(jobs)
                obj.warm_up_fio_cmd_args["timeout"] = obj.warm_up_fio_cmd_args["timeout"]
                # fio_output = self.host_handles[key].pcie_fio(filename="nofile", timeout=self.warm_up_fio_cmd_args["timeout"],
                #                                    **warm_up_fio_cmd_args)
                thread_id[index] = fun_test.execute_thread_after(time_in_seconds=wait_time,
                                                                 func=fio_parser,
                                                                 arg1=end_host_thread[index],
                                                                 host_index=index,
                                                                 filename="nofile",
                                                                 **warm_up_fio_cmd_args)

    def cleanup(self):
        # self.storage_controller_template.cleanup()
        pass

    def reset_and_health_check(self, fs_obj):
        fs_obj.reset()
        fs_obj.come.ensure_expected_containers_running()
        fun_test.test_assert(expression=self.storage_controller_template.get_health(
            storage_controller=fs_obj.get_storage_controller()),
            message="{}: API server health".format(fs_obj))


if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(BltApiStorageTest())
    #setup_bringup.add_test_case(ConfigPeristenceAfterReset())
    setup_bringup.run()
