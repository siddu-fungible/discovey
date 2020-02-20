from lib.system.fun_test import *

fun_test.enable_storage_api()
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_operations_template import BltVolumeOperationsTemplate
from swagger_client.models.volume_types import VolumeTypes
from scripts.storage.storage_helper import *
from random import seed
from random import randint


class BringupSetup(FunTestScript):
    topology = None
    testbed_type = fun_test.get_job_environment_variable("test_bed_type")

    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. Bringup FS1600 
        2. Configure Linux Host instance and make it available for test case
        """)

    def setup(self):
        already_deployed = True
        topology_helper = TopologyHelper()
        self.topology = topology_helper.deploy(already_deployed=already_deployed)
        fun_test.test_assert(self.topology, "Topology deployed")
        fun_test.shared_variables["topology"] = self.topology

    def cleanup(self):
        self.topology.cleanup()

class CreateDeleteVolume(FunTestCase):
    topology = None
    storage_controller_template = None
    body_volume_intent_create = None
    fs_obj_list = []

    def describe(self):
        self.set_test_details(id=1,
                              summary="Create Volume and Delete Volume",
                              steps='''
                              1. Make sure API server is up and running
                              2. Create a Volume using API Call
                              3. Delete the Volume Using API call
                              4. Clean up 
                              ''')

    def setup(self):
        self.topology = fun_test.shared_variables["topology"]
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            self.fs_obj_list.append(fs_obj)

    def create_volumes(self):
        capacity = []
        total_capacity = 0
        remaining_capacity = 0
        max_no_of_volumes = 0
        no_of_volumes = 0
        min_volume_capacity = 1073741824
        max_volume_capacity = 0
        vol_type = VolumeTypes().LOCAL_THIN
        compression_effort = False
        encrypt = False
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            storage_controller = fs_obj.get_storage_controller()
            raw_sc_api = StorageControllerApi(api_server_ip=storage_controller.target_ip)
            response = raw_sc_api.get_pools()
            pool_uuid = str(response["data"].keys()[0])
            total_capacity = total_capacity + response["data"][pool_uuid]["capacity"]
            max_volume_capacity = find_min_drive_capacity(storage_controller,30)

        max_no_of_volumes = total_capacity/min_volume_capacity
        if total_capacity-min_volume_capacity >= max_volume_capacity:
            random_capacity = random.randint(min_volume_capacity,max_volume_capacity)
        else:
            random_capacity = total_capacity
        remaining_capacity = total_capacity - random_capacity
        for volume in range(max_no_of_volumes):
            capacity.append(random_capacity)
            no_of_volumes = no_of_volumes + 1
            if remaining_capacity == 0:
                break
            else:
                if remaining_capacity-min_volume_capacity >= max_volume_capacity:
                    random_capacity = random.randint(min_volume_capacity,max_volume_capacity)
                else:
                    random_capacity = remaining_capacity
                remaining_capacity = remaining_capacity - random_capacity

        self.storage_controller_template = BltVolumeOperationsTemplate(topology=self.topology)
        self.storage_controller_template.initialize(already_deployed=False)
        for volume in range(no_of_volumes):
            name = "blt_vol_" + str(volume + 1)
            self.body_volume_intent_create = BodyVolumeIntentCreate(name=name, vol_type=vol_type, capacity=capacity[volume],
                                                                    compression_effort=compression_effort,
                                                                    encrypt=encrypt, data_protection={})
            vol_uuid_list = self.storage_controller_template.create_volume(fs_obj=self.fs_obj_list,
                                                                           body_volume_intent_create=self.body_volume_intent_create)
            fun_test.test_assert(expression=vol_uuid_list, message="Create Volume Successful")

    def delete_volumes(self):
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            storage_controller = fs_obj.get_storage_controller()
            raw_sc_api = StorageControllerApi(api_server_ip=storage_controller.target_ip)
            get_volume_result = raw_sc_api.get_volumes()
            fun_test.test_assert(message="Get Volume Details", expression=get_volume_result["status"])
            for volume in get_volume_result["data"]:
                delete_volume = storage_controller.storage_api.delete_volume(volume_uuid=volume)
                fun_test.test_assert(expression=delete_volume.status, message="Delete Volume {}".format(volume))

    def run(self):
        self.create_volumes()
        self.delete_volumes()

    def cleanup(self):
        self.storage_controller_template.cleanup()


if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(CreateDeleteVolume())
    setup_bringup.run()
