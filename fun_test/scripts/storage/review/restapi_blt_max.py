from lib.system.fun_test import *
fun_test.enable_storage_api()
from swagger_client.models.body_volume_intent_create import BodyVolumeIntentCreate
from lib.topology.topology_helper import TopologyHelper
from lib.templates.storage.storage_operations_template import BltVolumeOperationsTemplate
from swagger_client.models.volume_types import VolumeTypes
from lib.templates.storage.storage_controller_api import *


class BringupSetup(FunTestScript):
    topology = None
    testbed_type = fun_test.get_job_environment_variable("test_bed_type")

    def describe(self):
        self.set_test_details(steps="""
        1. Deploy the topology. Bringup FS1600 
        2. Configure Linux Host instance and make it available for test case
        """)

    def setup(self):
        already_deployed = False
        topology_helper = TopologyHelper()
        self.topology = topology_helper.deploy(already_deployed=already_deployed)
        fun_test.test_assert(self.topology, "Topology deployed")
        fun_test.shared_variables["topology"] = self.topology

    def cleanup(self):
        self.topology.cleanup()


class CreateMaxBLTVolumes(FunTestCase):
    topology = None
    storage_controller_template = None

    def describe(self):
        self.set_test_details(id=1,
                              summary="Create given number of BLT Volumes with encryption disabled, attach/detach/delete",
                              test_rail_case_ids=["C18571"],
                              steps='''
                              1. Make sure API server is up and running
                              2. Create volumes using API Call
                              3. Attach volumes to a remote host
                              ''')

    def setup(self, enable_encryption = False, skip_initialize=False, stripe_enabled=False):
        self.topology = fun_test.shared_variables["topology"]
        vol_name = "blt_vol"
        count = 0
        vol_type = VolumeTypes().LOCAL_THIN
        capacity = 10737418240
        compression_effort = False
        if enable_encryption:
            encrypt = True
        else:
            encrypt = False

        if stripe_enabled:
            stripe_count = 12
        else:
            stripe_count = 0
        volume_count = 1000
        self.run_traffic = False
        self.storage_controller_template = BltVolumeOperationsTemplate(topology=self.topology)
        if not skip_initialize:
            self.storage_controller_template.initialize()

        fs_obj_list = []
        for dut_index in self.topology.get_available_duts().keys():
            fs_obj = self.topology.get_dut_instance(index=dut_index)
            fs_obj_list.append(fs_obj)

        storage_controller = fs_obj.get_storage_controller()
        vol_uuid_dict = {}
        final_vol_uuid_dict = {}
        for x in range(1, volume_count+1, 1):
            name = vol_name + str(x)
            body_volume_intent_create = BodyVolumeIntentCreate(name=name, vol_type=vol_type, capacity=capacity,
                                                               compression_effort=compression_effort,
                                                               encrypt=encrypt, data_protection={},
                                                               stripe_count=stripe_count)
            vol_uuid_dict = self.storage_controller_template.create_volume(fs_obj=fs_obj,
                                                                           body_volume_intent_create=body_volume_intent_create)
            final_vol_uuid_dict[x] = vol_uuid_dict
            fun_test.test_assert(expression=vol_uuid_dict, message="Create volume{} with uuid {}"
                                 .format(x, final_vol_uuid_dict[x]))

        hosts = self.topology.get_available_hosts()
        # for fs_obj in vol_uuid_dict:
        for host_id in hosts:
            host_obj = hosts[host_id]
            for x in range(1, volume_count + 1, 1):
                attach_vol_result = self.storage_controller_template.attach_volume(host_obj=host_obj, fs_obj=fs_obj,
                                                                                   volume_uuid=final_vol_uuid_dict[x][0],
                                                                                   validate_nvme_connect=False,
                                                                                   raw_api_call=True)
                fun_test.test_assert(expression=attach_vol_result, message="Attach Volume with uuid {} Successful"
                                     .format(final_vol_uuid_dict[x][0]))

    def run(self):
        hosts = self.topology.get_available_hosts()
        if self.run_traffic:
            for host_id in hosts:
                host_obj = hosts[host_id]
                nvme_device_name = self.storage_controller_template.get_host_nvme_device(host_obj=host_obj)
                traffic_result = self.storage_controller_template.traffic_from_host(host_obj=host_obj,
                                                                                    filename="/dev/"+nvme_device_name)
                fun_test.test_assert(expression=traffic_result, message="FIO traffic result")
                fun_test.log(traffic_result)

    def cleanup(self):
        # self.storage_controller_template.cleanup()
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
                    detach_volume = storage_controller.storage_api.delete_port(port_uuid=port)
                    fun_test.test_assert(expression=detach_volume.status,
                                         message="Detach Volume {} from host with remote IP {}".format(
                                             volume, get_volume_result["data"][volume]['ports'][port]['remote_ip']))
                delete_volume = storage_controller.storage_api.delete_volume(volume_uuid=volume)
                fun_test.test_assert(expression=delete_volume.status, message="Delete Volume {}".format(volume))


class MaxBltEncryption(CreateMaxBLTVolumes):
    def describe(self):
        self.set_test_details(id=2,
                              summary="Create given number of BLT Volumes with encryption enabled, attach/detach/delete",
                              test_rail_case_ids=["C20329"],
                              steps='''1. Make sure API server is up and running
                              2. Create a encryption enabled volumes using API Call
                              3. Attach volumes to a remote host
                              ''')

    def setup(self):
        super(MaxBltEncryption, self).setup(enable_encryption=True, skip_initialize=True)

    def run(self):
        super(MaxBltEncryption, self).run()

    def cleanup(self):
        super(MaxBltEncryption, self).cleanup()
        
class MaxStripeVolume(CreateMaxBLTVolumes):
    def describe(self):
        self.set_test_details(id=3,
                              summary="Create given number of stripe Volumes(stripe_count=12), attach/detach/delete",
                              test_rail_case_ids=["C18603"],
                              steps='''1. Make sure API server is up and running
                              2. Create a encryption enabled volumes using API Call
                              3. Attach volumes to a remote host
                              ''')

    def setup(self):
        super(MaxStripeVolume, self).setup(enable_encryption=False, skip_initialize=True, stripe_enabled=True)

    def run(self):
        super(MaxStripeVolume, self).run()

    def cleanup(self):
        super(MaxStripeVolume, self).cleanup()

class MaxStripeVolumeEncryption(CreateMaxBLTVolumes):
    def describe(self):
        self.set_test_details(id=4,
                              summary="Create given number of stripe Volumes(stripe_count=12) with encryption enabled, attach/detach/delete",
                              test_rail_case_ids=["C36678"],
                              steps='''1. Make sure API server is up and running
                              2. Create a encryption enabled volumes using API Call
                              3. Attach volumes to a remote host
                              ''')

    def setup(self):
        super(MaxStripeVolumeEncryption, self).setup(enable_encryption=True, skip_initialize=True, stripe_enabled=True)

    def run(self):
        super(MaxStripeVolumeEncryption, self).run()

    def cleanup(self):
        super(MaxStripeVolumeEncryption, self).cleanup()


if __name__ == "__main__":
    setup_bringup = BringupSetup()
    setup_bringup.add_test_case(CreateMaxBLTVolumes())
    #setup_bringup.add_test_case(MaxBltEncryption())
    #setup_bringup.add_test_case(MaxStripeVolume())
    #setup_bringup.add_test_case(MaxStripeVolumeEncryption())
    setup_bringup.run()
