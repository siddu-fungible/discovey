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
        fun_test.shared_variables["already_deployed"] = already_deployed

    def cleanup(self):
        self.topology.cleanup()

class CreateDeleteVolume(FunTestCase):
    topology = None
    already_deployed = True
    storage_controller_template = None
    body_volume_intent_create = None
    fs_obj_list = []
    capacity = []
    vol_uuid_list = []
    no_of_volumes = 0
    vol_type = VolumeTypes().LOCAL_THIN
    compression_effort = False
    encrypt = False
    come_handle = None

    def describe(self):
        self.set_test_details(id=1,
                              summary="Create Volume and Delete Volume",
                              steps='''
                              1. Make sure API server is up and running
                              2. Create a Volumes using API Call
                              3. Check weather volumes are created or not
                              4. Delete the Volumes Using API call
                              5. Check weather volumes are deleted or not
                              6. Clean up 
                              ''')

    def setup(self):
        self.topology = fun_test.shared_variables["topology"]
        self.already_deployed = fun_test.shared_variables["already_deployed"]
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            self.fs_obj_list.append(fs_obj)
            self.come_handle = fs_obj.get_come()

    def create_volumes(self):
        total_capacity = 0
        remaining_capacity = 0
        max_no_of_volumes = 0
        min_volume_capacity = 1073741824
        max_volume_capacity = 0
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            storage_controller = fs_obj.get_storage_controller()
            raw_sc_api = StorageControllerApi(api_server_ip=storage_controller.target_ip)
            response = raw_sc_api.get_pools()
            pool_uuid = str(response['data'].keys()[0])
            loc_capacity = str(response['data'][pool_uuid]['capacity'])
            total_capacity = total_capacity + int(loc_capacity)
            max_volume_capacity = find_min_drive_capacity(storage_controller,30) - (3*4096)

        max_no_of_volumes = total_capacity/min_volume_capacity
        if total_capacity-min_volume_capacity >= max_volume_capacity:
            random_capacity = random.randint(min_volume_capacity,max_volume_capacity)
        else:
            random_capacity = total_capacity
        random_capacity = random_capacity - (random_capacity%4096)
        remaining_capacity = total_capacity - random_capacity
        for volume in range(max_no_of_volumes):
            self.capacity.append(random_capacity)
            self.no_of_volumes = self.no_of_volumes + 1
            if remaining_capacity == 0:
                break
            else:
                if remaining_capacity-min_volume_capacity >= max_volume_capacity:
                    random_capacity = random.randint(min_volume_capacity,max_volume_capacity)
                else:
                    random_capacity = remaining_capacity
                random_capacity = random_capacity - (random_capacity % 4096)
                remaining_capacity = remaining_capacity - random_capacity

        self.storage_controller_template = BltVolumeOperationsTemplate(topology=self.topology)
        self.storage_controller_template.initialize(already_deployed=self.already_deployed)
        for volume in range(self.no_of_volumes):
            name = "blt_vol_" + str(volume + 1)
            self.body_volume_intent_create = BodyVolumeIntentCreate(name=name, vol_type=self.vol_type, capacity=self.capacity[volume],
                                                                    compression_effort=self.compression_effort,
                                                                    encrypt=self.encrypt, data_protection={})
            vol_uuid = self.storage_controller_template.create_volume(fs_obj=self.fs_obj_list,
                                                                      body_volume_intent_create=self.body_volume_intent_create)
            fun_test.test_assert(expression=vol_uuid, message="Create Volume Successful")
            self.vol_uuid_list.append(vol_uuid[0])

    def attach_volumes(self):
        hosts = self.topology.get_available_hosts()
        required_hosts_available = True if (self.topology.get_available_host_instances() != None) else False
        fun_test.test_assert( required_hosts_available, "Required hosts available" )

        # for fs_obj in vol_uuid_dict:
        for host_id in hosts:
            host_obj = hosts[host_id]
            for volume in range(self.no_of_volumes):
                self.attach_vol_result = self.storage_controller_template.attach_volume(host_obj=host_obj, fs_obj=self.fs_obj_list,
                                                                                        volume_uuid=self.vol_uuid_list[volume][0],
                                                                                        validate_nvme_connect=False,
                                                                                        raw_api_call=True )
                fun_test.test_assert(expression=self.attach_vol_result, message="Attach Volume with uuid {} Successful"
                                     .format(self.vol_uuid_list[volume][0]))

    def detach_volumes(self):
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            storage_controller = fs_obj.get_storage_controller()
            # volumes = storage_controller.storage_api.get_volumes()
            # WORKAROUND : get_volumes errors out.
            raw_sc_api = StorageControllerApi(api_server_ip=storage_controller.target_ip)
            get_volume_result = raw_sc_api.get_volumes()
            fun_test.test_assert(message="Get Volume Details", expression=get_volume_result["status"])
            for volume in get_volume_result["data"]:
                for port in get_volume_result["data"][volume]["ports"]:
                    detach_volume = None
                    detach_result = False
                    detach_volume = storage_controller.storage_api.delete_port(port_uuid=port)
                    if detach_volume:
                        detach_result = detach_volume.status
                    fun_test.add_checkpoint(expected=True, actual=detach_result,
                                            checkpoint="Detach Volume {} from host with host_nqn {}".format(volume,
                                                    get_volume_result["data"][volume]['ports'][port]['host_nqn']))

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

    def volumes_persistent_check(self):
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            storage_controller = fs_obj.get_storage_controller()
            raw_sc_api = StorageControllerApi(api_server_ip=storage_controller.target_ip)
            for volume_num in range(self.no_of_volumes):
                vol_db_status = raw_sc_api.is_raw_vol_in_db(vol_uuid=self.vol_uuid_list[volume_num],come_handle=self.come_handle,
                                                            capacity=self.capacity[volume_num],stripe_count=0,
                                                            vol_type=self.vol_type,encrypt=self.encrypt)
                fun_test.test_assert(expression=vol_db_status["status"], message="Volume Persistent Check {}".format(vol_db_status))

    def volumes_deletion_check(self):
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            storage_controller = fs_obj.get_storage_controller()
            raw_sc_api = StorageControllerApi(api_server_ip=storage_controller.target_ip)
            for volume_uuid in self.vol_uuid_list:
                vol_db_status = raw_sc_api.is_delete_in_db(come_handle=self.come_handle,vol_uuid=volume_uuid)
                fun_test.test_assert(expression=vol_db_status["status"], message="Volume Deletion Check {}".format(vol_db_status))

    def run(self):
        self.delete_volumes() #Delete Volumes from Previous run
        self.create_volumes()
        self.volumes_persistent_check()
        self.attach_volumes()
        self.detach_volumes()
        self.delete_volumes()
        self.volumes_deletion_check()

    def cleanup(self):
        pass
        #self.storage_controller_template.cleanup()


if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(CreateDeleteVolume())
    setup_bringup.run()
