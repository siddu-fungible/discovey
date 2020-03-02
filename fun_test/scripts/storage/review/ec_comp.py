from lib.system.fun_test import *
fun_test.enable_storage_api()
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_operations_template import EcVolumeOperationsTemplate
from lib.templates.storage.storage_traffic_template import StorageTrafficTemplate
from swagger_client.models.volume_types import VolumeTypes



class BootupSetup(FunTestScript):
    topology = None
    testbed_type = fun_test.get_job_environment_variable("test_bed_type")

    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. Bootup FS1600 
        2. Configure Linux Host instance and make it available for test case
        """)

    def setup(self):
        already_deployed = False
        topology_helper = TopologyHelper()
        self.topology = topology_helper.deploy(already_deployed=already_deployed)
        fun_test.test_assert(self.topology, "Topology deployed")
        fun_test.shared_variables["topology"] = self.topology

        job_inputs = fun_test.get_job_inputs()
        if "num_hosts" in job_inputs:
            self.num_host = job_inputs["num_hosts"]

    def cleanup(self):
        self.topology.cleanup()


class TestDataIntegrity(FunTestCase):
    topology = None
    storage_controller_template = None
    attach_result = None


    def describe(self):
        self.set_test_details(id=1,
                              summary="Create EC volumes with 8 zip levels and run IO from host ",
                              steps='''
                              1. Make sure API server is up and running
                              2. Create a Volume using API Call
                              3. Attach Volume to a remote host
                              4. Run FIO from host
                              ''')

    def setup(self):

        self.topology = fun_test.shared_variables["topology"]
        vol_name = "ec_vol"
        num_vols = 2
        vol_type = VolumeTypes().EC
        capacity = 10*1024*1024*1024
        effort_levels = [1, 2]
        encrypt = True

        self.fs_obj_list = [self.topology.get_dut_instance(index=dut_index)
                       for dut_index in self.topology.get_available_duts().keys()]
        self.host_obj_list = self.topology.get_available_host_instances()
        self.vol_uuid_list = []

        for vol in range(num_vols):
            for effort in effort_levels:
                body_volume_intent_create = BodyVolumeIntentCreate(name=vol_name + str(effort) + str(vol+1),
                                                                   vol_type=vol_type, capacity=capacity,
                                                                   compression_effort=effort, encrypt=encrypt,
                                                                   data_protection={"num_redundant_dpus": 0,
                                                                                    "num_failed_disks": 2})
                self.storage_controller_template = EcVolumeOperationsTemplate(topology=self.topology)
                self.storage_controller_template.initialize(already_deployed=False)

                vol_uuid = self.storage_controller_template.\
                    create_volume(fs_obj=self.fs_obj_list, body_volume_intent_create=body_volume_intent_create)
                fun_test.test_assert(vol_uuid,
                                     message="Create Volume {} Successful. zip level: {}".format(vol_uuid[0], effort))
                self.vol_uuid_list.append(vol_uuid[0])

        self.attach_result = self.storage_controller_template.attach_m_vol_n_host(self.fs_obj_list[0],
                                                             self.vol_uuid_list, self.host_obj_list,
                                                             volume_is_shared=True)
        fun_test.test_assert(expression=self.attach_result, message="Attach Volume(s) Successful")

        fun_test.shared_variables["fs_obj_list"] = self.fs_obj_list
        fun_test.shared_variables["host_obj_list"] = self.host_obj_list
        fun_test.shared_variables["vol_uuid_list"] = self.vol_uuid_list

    def run(self):
        self.nvme_device_list =[]
        for host_obj in self.host_obj_list:
            for idx in range(len(self.attach_result[host_obj])):
                vol_uuid = self.attach_result[host_obj[idx]['data']['uuid']]
                nvme_device_name = self.storage_controller_template.\
                    get_host_nvme_device(host_obj=host_obj,
                                         subsys_nqn=self.attach_result[host_obj][idx]['data']['subsys_nqn'],
                                         nsid=self.attach_result['data']['nsid'])

                storage_traffic_obj = StorageTrafficTemplate(storage_operations_template=
                                                             self.storage_controller_template)
                traffic_result = storage_traffic_obj.fio_with_integrity_check(host_obj=host_obj.get_instance(),
                                                                              filename=nvme_device_name)
                fun_test.test_assert(expression=traffic_result,
                                     message="Host : {}, Vol: {} FIO traffic result".format(host_obj.name, vol_uuid))
                fun_test.log(traffic_result)

    def cleanup(self):
        self.storage_controller_template.cleanup(fun_test.is_current_test_case_failed())


if __name__ == "__main__":
    setup_bringup = BootupSetup()
    setup_bringup.add_test_case(TestDataIntegrity())
    setup_bringup.run()
