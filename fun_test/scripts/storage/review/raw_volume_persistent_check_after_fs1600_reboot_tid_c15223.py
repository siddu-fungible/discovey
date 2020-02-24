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

class CreateDeleteVolumeRebootFS1600(FunTestCase):
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
                fun_test.test_assert( expression=vol_db_status["status"], message="Volume Deletion Check {}".format(vol_db_status))

    def reboot_fs1600(self):
        fun_test.log("Rebooting FS1600")

        api_server_timeout = 240
        total_reconnect_time = 600
        add_on_time = 180  # Needed for getting through 60 iterations of reconnect from host
        reboot_timer = FunTimer(
            max_time=total_reconnect_time + add_on_time)  # WORKAROUND, why do we need so much time

        # Reset FS1600
        reset = self.fs_obj_list[0].reset(hard=False)
        fun_test.test_assert(reset, "FS1600 reset successfully done")

        # Ensure FS1600 is up
        ensure_up = self.fs_obj_list[0].ensure_is_up()
        fun_test.test_assert(ensure_up, "Ensure FS1600 is up")

        # Ensure all containers are up
        fs_obj = self.fs_obj_list[0]
        come = fs_obj.get_come()
        containers_status = come.ensure_expected_containers_running()
        fun_test.test_assert(containers_status, "All containers up")

        # Ensure API server is up
        sc_api = StorageControllerApi(api_server_ip=come.host_ip)
        fun_test.test_assert(ensure_api_server_is_up(sc_api, timeout=api_server_timeout),
                              "Ensure API server is up")
        fun_test.log("TOTAL TIME ELAPSED IN REBOOT IS {}".format(reboot_timer.elapsed_time()))
        ipmi_details = {
            "username": "admin",
            "password": "admin",
            "host_ip": self.come_handle.host_ip
        }
        come_up = self.come_handle.ensure_host_is_up(max_wait_time=300,ipmi_details=ipmi_details,
                                                     power_cycle=True)

    def run(self):
        self.delete_volumes() #Delete Volumes from Previous run
        self.create_volumes()
        self.volumes_persistent_check()
        self.reboot_fs1600()
        self.delete_volumes()
        self.volumes_deletion_check()

    def cleanup(self):
        pass
        #self.storage_controller_template.cleanup()


if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(CreateDeleteVolumeRebootFS1600())
    setup_bringup.run()
