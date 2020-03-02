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
from swagger_client.rest import ApiException
import string, random
from collections import OrderedDict, Counter


class BringupSetup(FunTestScript):
    topology = None
    testbed_type = fun_test.get_job_environment_variable("test_bed_type")

    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. Bringup FS1600 
        2. Configure Linux Host instance and make it available for test case
        """)

    def setup(self):

        format_drives = True
        job_inputs = fun_test.get_job_inputs()
        if not job_inputs:
            job_inputs = {}
        fun_test.log("Provided job inputs: {}".format(job_inputs))
        if "format_drives" in job_inputs:
            format_drives = job_inputs["format_drives"]

        if "already_deployed" in job_inputs:
            self.already_deployed = job_inputs["already_deployed"]
        else:
            self.already_deployed = False
        num_f1 = 2
        dpu_indexes = [x for x in range(num_f1)]

        topology_helper = TopologyHelper()
        self.topology = topology_helper.deploy(already_deployed=self.already_deployed)
        fun_test.test_assert(self.topology, "Topology deployed")
        fun_test.shared_variables["topology"] = self.topology

        self.blt_template = BltVolumeOperationsTemplate(topology=self.topology, api_logging_level=logging.ERROR)
        self.blt_template.initialize(dpu_indexes=dpu_indexes, already_deployed=self.already_deployed,
                                     format_drives=format_drives)
        fun_test.shared_variables["blt_template"] = self.blt_template
        self.fs_obj_list = []
        for dut_index in self.topology.get_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            self.fs_obj_list.append(fs_obj)

        fun_test.shared_variables["fs_obj_list"] = self.fs_obj_list
        self.sc_dpcsh_obj = self.fs_obj_list[0].get_storage_controller(f1_index=0)
        fun_test.shared_variables["dpcsh_obj"] = self.sc_dpcsh_obj

    def cleanup(self):
        fun_test.log("Performing disconnect/detach/delete cleanup as part of script level cleanup")
        #self.blt_template.cleanup()
        self.topology.cleanup()


class GenericCreateAttachDetachDelete(FunTestCase):

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
        if not job_inputs:
            job_inputs = {}
        if "capacity" in job_inputs:
            self.capacity = job_inputs["capacity"]
        if "blt_per_host" in job_inputs:
            self.blt_per_host = job_inputs["blt_per_host"]
        if "num_hosts" in job_inputs:
            self.num_host = job_inputs["num_hosts"]
        if "test_iteration_count" in job_inputs:
            self.test_iteration_count = job_inputs["test_iteration_count"]

        fun_test.shared_variables["blt_per_host"] = self.blt_per_host
        self.vol_type = VolumeTypes().LOCAL_THIN
        #self.hosts = self.topology.get_available_host_instances()


    def run(self):
        self.blt_count = self.blt_per_host
        for count in range(self.test_iteration_count):
            self.vol_uuid_list = []
            for i in range(self.blt_count):
                suffix = utils.generate_uuid(length=4)
                body_volume_intent_create = BodyVolumeIntentCreate(name=self.name + suffix + str(i),
                                                                   vol_type=self.vol_type,
                                                                   capacity=self.capacity, compression_effort=False,
                                                                   encrypt=self.encrypt, data_protection={})
                vol_uuid = self.blt_template.create_volume(self.fs_obj_list, body_volume_intent_create)
                fun_test.test_assert(expression=vol_uuid and vol_uuid[0], message="Create Volume{} Successful with "
                                                                                  "uuid {}".format(i+1, vol_uuid[0]))
                self.vol_uuid_list.append(vol_uuid[0])
            self.cleanupio()
            fun_test.test_assert(expression=True, message="Test completed {} Iteration".format(count + 1))


    def cleanupio(self):
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            storage_controller = fs_obj.get_storage_controller()
            # volumes = storage_controller.storage_api.get_volumes()
            # WORKAROUND : get_volumes errors out.
            raw_sc_api = StorageControllerApi(api_server_ip=storage_controller.target_ip)
            get_volume_result = raw_sc_api.get_volumes()
            fun_test.test_assert(message="Get Volume Details", expression=get_volume_result["status"])
            for volume in get_volume_result["data"]:
                    delete_volume = None
                    try:
                        delete_volume = storage_controller.storage_api.delete_volume(volume_uuid=volume)
                    except ApiException as e:
                        fun_test.critical("Exception while detaching volume: {}\n".format(e))
                    except Exception as e:
                        fun_test.critical("Exception while detaching volume: {}\n".format(e))
                    delete_volume_result = False
                    if delete_volume:
                        delete_volume_result = delete_volume.status
                    fun_test.test_assert(expression=delete_volume.status, message="Delete Volume {}".format(volume))

    def cleanup(self):
        fun_test.shared_variables["storage_controller_template"] = self.blt_template


class CreateDeleteMaxVolume(GenericCreateAttachDetachDelete):
    def describe(self):
        self.set_test_details(id=1,
                              summary="Create and delete max volumes",
                              test_rail_case_ids=["T31394"],
                              steps='''
                                    1. Create 1000 volumes
                                    2. Delete 1000 volumes
                              ''')

        def setup(self):
            super(CreateDeleteMaxVolume, self).setup()

        def run(self):
            super(CreateDeleteMaxVolume, self).run()

        def cleanup(self):
            super(CreateDeleteMaxVolume, self).cleanup()




if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(CreateDeleteMaxVolume())
    setup_bringup.run()
